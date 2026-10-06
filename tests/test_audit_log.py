import json
import sys
from pathlib import Path

import grpc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from client.client import create_mtls_channel, sha256_bytes
from server import file_storage_pb2 as pb2
from server import file_storage_pb2_grpc as pb2_grpc
from server.audit import AUDIT_LOG


def login(stub, username, password):
    result = stub.Login(pb2.LoginRequest(username=username, password=password), timeout=5)
    assert result.success and result.token
    return (('authorization', f'Bearer {result.token}'),)


def read_events():
    if not AUDIT_LOG.exists():
        return []
    return [json.loads(line) for line in AUDIT_LOG.read_text(encoding='utf-8').splitlines() if line.strip()]


def test_audit_log_records_allow_and_deny():
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_LOG.write_text('', encoding='utf-8')

    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)

        # Successful login must be logged without exposing the password/token.
        md = login(stub, 'mahasiswa', 'mhs123')
        content = b'audit log public test'
        uploaded = stub.Upload(pb2.UploadRequest(
            filename='audit_public.txt', label='PUBLIC', content=content,
            sha256=sha256_bytes(content)), metadata=md, timeout=5)
        assert uploaded.success

        # Successful read is ALLOW.
        downloaded = stub.Download(pb2.DownloadRequest(filename='audit_public.txt'), metadata=md, timeout=5)
        assert downloaded.success

        # USER attempting SECRET must be denied and logged as DENY.
        admin_md = login(stub, 'admin', 'admin123')
        secret = b'audit secret test'
        secret_upload = stub.Upload(pb2.UploadRequest(
            filename='audit_secret.txt', label='SECRET', content=secret,
            sha256=sha256_bytes(secret)), metadata=admin_md, timeout=5)
        assert secret_upload.success
        try:
            stub.Download(pb2.DownloadRequest(filename='audit_secret.txt'), metadata=md, timeout=5)
        except grpc.RpcError as exc:
            assert exc.code() == grpc.StatusCode.PERMISSION_DENIED
        else:
            raise AssertionError('USER should not read SECRET file')

        # Clean up using ADMIN.
        assert stub.Delete(pb2.DeleteRequest(filename='audit_public.txt'), metadata=admin_md, timeout=5).success
        assert stub.Delete(pb2.DeleteRequest(filename='audit_secret.txt'), metadata=admin_md, timeout=5).success

    events = read_events()
    assert events
    for event in events:
        assert {'timestamp', 'user', 'action', 'decision'} <= event.keys()
        assert event['decision'] in {'ALLOW', 'DENY'}
        raw = json.dumps(event)
        assert 'mhs123' not in raw
        assert 'admin123' not in raw

    assert any(e['action'] == 'UPLOAD' and e['decision'] == 'ALLOW' and e.get('filename') == 'audit_public.txt' for e in events)
    assert any(e['action'] == 'DOWNLOAD' and e['decision'] == 'DENY' and e.get('filename') == 'audit_secret.txt' for e in events)
