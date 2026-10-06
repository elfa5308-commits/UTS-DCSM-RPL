"""Official RPL UTS test mapping: TC-RPL-01 .. TC-RPL-04."""

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

CERTS = ROOT / "certificates"
STORAGE = ROOT / "storage"


def login(stub, username, password):
    response = stub.Login(pb2.LoginRequest(username=username, password=password), timeout=5)
    assert response.success and response.token
    return (("authorization", f"Bearer {response.token}"),)


def audit_events():
    if not AUDIT_LOG.exists():
        return []
    return [json.loads(line) for line in AUDIT_LOG.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_tc_rpl_01_upload_download_file_with_tls():
    """TC-RPL-01: File upload/download over the mutual-TLS gRPC channel."""
    filename = "tc_rpl_01_tls.txt"
    content = b"TC-RPL-01 secure file transfer"
    try:
        with create_mtls_channel() as channel:
            stub = pb2_grpc.FileStorageStub(channel)
            md = login(stub, "mahasiswa", "mhs123")
            uploaded = stub.Upload(
                pb2.UploadRequest(filename=filename, label="PUBLIC", content=content, sha256=sha256_bytes(content)),
                metadata=md,
                timeout=5,
            )
            assert uploaded.success
            downloaded = stub.Download(pb2.DownloadRequest(filename=filename), metadata=md, timeout=5)
            assert downloaded.success
            assert downloaded.content == content
            assert downloaded.sha256 == sha256_bytes(content)
    finally:
        storage_file = STORAGE / filename
        storage_file.unlink(missing_ok=True)
        metadata = json.loads((STORAGE / ".metadata.json").read_text(encoding="utf-8")) if (STORAGE / ".metadata.json").exists() else {}
        metadata.pop(filename, None)
        (STORAGE / ".metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")


def test_tc_rpl_02_rbac_security_label_and_audit_deny():
    """TC-RPL-02: Lower-clearance user is denied SECRET file access and DENY is audited."""
    filename = "tc_rpl_02_secret.txt"
    content = b"TC-RPL-02 secret data"
    try:
        with create_mtls_channel() as channel:
            stub = pb2_grpc.FileStorageStub(channel)
            admin_md = login(stub, "admin", "admin123")
            uploaded = stub.Upload(
                pb2.UploadRequest(filename=filename, label="SECRET", content=content, sha256=sha256_bytes(content)),
                metadata=admin_md,
                timeout=5,
            )
            assert uploaded.success

            user_md = login(stub, "mahasiswa", "mhs123")
            try:
                stub.Download(pb2.DownloadRequest(filename=filename), metadata=user_md, timeout=5)
            except grpc.RpcError as exc:
                assert exc.code() == grpc.StatusCode.PERMISSION_DENIED
            else:
                raise AssertionError("USER unexpectedly read a SECRET file")

        events = audit_events()
        assert any(
            e.get("action") == "DOWNLOAD"
            and e.get("decision") == "DENY"
            and e.get("filename") == filename
            and e.get("label") == "SECRET"
            for e in events
        )
    finally:
        (STORAGE / filename).unlink(missing_ok=True)
        metadata = json.loads((STORAGE / ".metadata.json").read_text(encoding="utf-8")) if (STORAGE / ".metadata.json").exists() else {}
        metadata.pop(filename, None)
        (STORAGE / ".metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")


def test_tc_rpl_03_invalid_client_certificate_rejected():
    """TC-RPL-03: TLS handshake rejects a client without a valid certificate."""
    ca_cert = (CERTS / "ca.crt").read_bytes()
    credentials = grpc.ssl_channel_credentials(root_certificates=ca_cert)
    with grpc.secure_channel("localhost:50051", credentials) as channel:
        stub = pb2_grpc.FileStorageStub(channel)
        try:
            stub.Login(pb2.LoginRequest(username="mahasiswa", password="mhs123"), timeout=5)
        except grpc.RpcError as exc:
            assert exc.code() in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.UNKNOWN)
        else:
            raise AssertionError("Connection without client certificate was unexpectedly accepted")


def test_tc_rpl_04_sha256_tampering_detected():
    """TC-RPL-04: Server-side file modification is detected by SHA-256 mismatch."""
    filename = "tc_rpl_04_tamper.txt"
    content = b"TC-RPL-04 trusted original"
    storage_file = STORAGE / filename
    try:
        with create_mtls_channel() as channel:
            stub = pb2_grpc.FileStorageStub(channel)
            admin_md = login(stub, "admin", "admin123")
            uploaded = stub.Upload(
                pb2.UploadRequest(filename=filename, label="SECRET", content=content, sha256=sha256_bytes(content)),
                metadata=admin_md,
                timeout=5,
            )
            assert uploaded.success
            assert uploaded.sha256 == sha256_bytes(content)

            storage_file.write_bytes(b"ILLEGAL TAMPERING")
            downloaded = stub.Download(pb2.DownloadRequest(filename=filename), metadata=admin_md, timeout=5)
            assert not downloaded.success
            assert "integrity check failed" in downloaded.message.lower()
            assert downloaded.content == b""
            assert downloaded.sha256 == sha256_bytes(b"ILLEGAL TAMPERING")
    finally:
        storage_file.unlink(missing_ok=True)
        metadata = json.loads((STORAGE / ".metadata.json").read_text(encoding="utf-8")) if (STORAGE / ".metadata.json").exists() else {}
        metadata.pop(filename, None)
        (STORAGE / ".metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
