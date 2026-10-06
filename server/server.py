import hashlib
import json
import logging
from concurrent import futures
from pathlib import Path

import grpc

from . import file_storage_pb2 as pb2
from . import file_storage_pb2_grpc as pb2_grpc
from .auth import authenticate, validate_token
from .audit import write_audit
from .authorization import can_delete, can_read, can_write, normalize_label

ROOT = Path(__file__).resolve().parent.parent
CERTS = ROOT / 'certificates'
STORAGE = ROOT / 'storage'
STORAGE.mkdir(exist_ok=True)
METADATA_PATH = STORAGE / '.metadata.json'


def load_metadata() -> dict:
    if not METADATA_PATH.exists():
        return {}
    try:
        return json.loads(METADATA_PATH.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return {}


def save_metadata(metadata: dict) -> None:
    METADATA_PATH.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding='utf-8')


def get_file_label(filename: str) -> str:
    metadata = load_metadata()
    return metadata.get(filename, {}).get('label', 'PUBLIC')


def safe_name(name: str) -> str:
    cleaned = Path(name).name
    if not cleaned or cleaned in {'.', '..'}:
        raise ValueError('Invalid filename')
    return cleaned


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FileStorageService(pb2_grpc.FileStorageServicer):
    @staticmethod
    def _identity(claims):
        return (claims.get('sub', 'unknown'), claims.get('role', ''))

    def _require_auth(self, context, action: str):
        metadata = dict(context.invocation_metadata())
        auth_header = metadata.get('authorization', '')
        if not auth_header.startswith('Bearer '):
            write_audit(action, 'DENY', reason='Missing Bearer token')
            context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Missing Bearer token.')
        token = auth_header[7:].strip()
        claims = validate_token(token)
        if not claims:
            write_audit(action, 'DENY', reason='Invalid or expired JWT token')
            context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Invalid or expired JWT token.')
        return claims

    def Login(self, request, context):
        token = authenticate(request.username, request.password)
        if not token:
            write_audit('LOGIN', 'DENY', user=request.username, reason='Invalid username or password')
            return pb2.LoginResponse(success=False, message='Invalid username or password.')
        role = 'ADMIN' if request.username == 'admin' else 'USER'
        write_audit('LOGIN', 'ALLOW', user=request.username, role=role, reason='Authentication successful')
        return pb2.LoginResponse(success=True, token=token, message='Login successful.')

    def Upload(self, request, context):
        claims = self._require_auth(context, 'UPLOAD')
        user, role = self._identity(claims)
        try:
            filename = safe_name(request.filename)
        except ValueError as exc:
            write_audit('UPLOAD', 'DENY', user=user, role=role, reason=str(exc))
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))

        try:
            label = normalize_label(request.label)
        except ValueError as exc:
            write_audit('UPLOAD', 'DENY', user=user, role=role, filename=filename, reason=str(exc))
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        if not can_write(claims, label):
            reason = 'RBAC policy denies writing this security label'
            write_audit('UPLOAD', 'DENY', user=user, role=role, filename=filename, label=label, reason=reason)
            context.abort(grpc.StatusCode.PERMISSION_DENIED, reason + '.')

        calculated = sha256_bytes(request.content)
        if request.sha256 and request.sha256 != calculated:
            reason = 'SHA-256 mismatch in upload request'
            write_audit('UPLOAD', 'DENY', user=user, role=role, filename=filename, label=label, reason=reason)
            return pb2.FileResponse(
                success=False,
                message=reason + '.',
                filename=filename,
                label=label,
                sha256=calculated,
            )

        path = STORAGE / filename
        path.write_bytes(request.content)
        metadata = load_metadata()
        metadata[filename] = {'label': label, 'sha256': calculated}
        save_metadata(metadata)
        write_audit('UPLOAD', 'ALLOW', user=user, role=role, filename=filename, label=label, reason='File uploaded successfully')
        return pb2.FileResponse(
            success=True,
            message='File uploaded successfully.',
            filename=filename,
            label=label,
            sha256=calculated,
        )

    def Download(self, request, context):
        claims = self._require_auth(context, 'DOWNLOAD')
        user, role = self._identity(claims)
        try:
            filename = safe_name(request.filename)
        except ValueError as exc:
            write_audit('DOWNLOAD', 'DENY', user=user, role=role, reason=str(exc))
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))

        path = STORAGE / filename
        if not path.is_file():
            write_audit('DOWNLOAD', 'DENY', user=user, role=role, filename=filename, reason='File not found')
            return pb2.FileResponse(success=False, message='File not found.', filename=filename)

        label = get_file_label(filename)
        if not can_read(claims, label):
            reason = 'Security label policy denies reading this file'
            write_audit('DOWNLOAD', 'DENY', user=user, role=role, filename=filename, label=label, reason=reason)
            context.abort(grpc.StatusCode.PERMISSION_DENIED, reason + '.')

        content = path.read_bytes()
        calculated = sha256_bytes(content)
        expected = load_metadata().get(filename, {}).get('sha256')
        if expected and calculated != expected:
            reason = 'SHA-256 integrity check failed: file may have been tampered with'
            write_audit('DOWNLOAD', 'DENY', user=user, role=role, filename=filename, label=label, reason=reason)
            return pb2.FileResponse(
                success=False,
                message=reason + '.',
                filename=filename,
                label=label,
                sha256=calculated,
            )
        write_audit('DOWNLOAD', 'ALLOW', user=user, role=role, filename=filename, label=label, reason='Integrity verified')
        return pb2.FileResponse(
            success=True,
            message='File downloaded successfully.',
            filename=filename,
            label=label,
            content=content,
            sha256=calculated,
        )

    def List(self, request, context):
        claims = self._require_auth(context, 'LIST')
        user, role = self._identity(claims)
        files = []
        for path in sorted(STORAGE.iterdir()):
            if path.is_file():
                label = get_file_label(path.name)
                if not can_read(claims, label):
                    continue
                content = path.read_bytes()
                files.append(pb2.FileInfo(
                    filename=path.name,
                    label=label,
                    sha256=sha256_bytes(content),
                    size=path.stat().st_size,
                ))
        write_audit('LIST', 'ALLOW', user=user, role=role, reason=f'Listed {len(files)} readable file(s)')
        return pb2.ListResponse(files=files)

    def Delete(self, request, context):
        claims = self._require_auth(context, 'DELETE')
        user, role = self._identity(claims)
        try:
            filename = safe_name(request.filename)
        except ValueError as exc:
            write_audit('DELETE', 'DENY', user=user, role=role, reason=str(exc))
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))

        path = STORAGE / filename
        if not path.is_file():
            write_audit('DELETE', 'DENY', user=user, role=role, filename=filename, reason='File not found')
            return pb2.FileResponse(success=False, message='File not found.', filename=filename)

        label = get_file_label(filename)
        if not can_delete(claims, label):
            reason = 'RBAC/security label policy denies deleting this file'
            write_audit('DELETE', 'DENY', user=user, role=role, filename=filename, label=label, reason=reason)
            context.abort(grpc.StatusCode.PERMISSION_DENIED, reason + '.')

        path.unlink()
        metadata = load_metadata()
        metadata.pop(filename, None)
        save_metadata(metadata)
        write_audit('DELETE', 'ALLOW', user=user, role=role, filename=filename, label=label, reason='File deleted successfully')
        return pb2.FileResponse(success=True, message='File deleted successfully.', filename=filename, label=label)


def build_server() -> grpc.Server:
    server_key = (CERTS / 'server.key').read_bytes()
    server_cert = (CERTS / 'server.crt').read_bytes()
    ca_cert = (CERTS / 'ca.crt').read_bytes()

    credentials = grpc.ssl_server_credentials(
        [(server_key, server_cert)],
        root_certificates=ca_cert,
        require_client_auth=True,
    )

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_FileStorageServicer_to_server(FileStorageService(), server)
    server.add_secure_port('[::]:50051', credentials)
    return server


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    server = build_server()
    server.start()
    logging.info('Secure gRPC mTLS server listening on 0.0.0.0:50051')
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=1)


if __name__ == '__main__':
    main()
