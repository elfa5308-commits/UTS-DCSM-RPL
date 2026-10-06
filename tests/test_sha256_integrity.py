import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from client.client import create_mtls_channel, sha256_bytes
from server import file_storage_pb2 as pb2
from server import file_storage_pb2_grpc as pb2_grpc


def login(stub, username, password):
    result = stub.Login(pb2.LoginRequest(username=username, password=password), timeout=5)
    assert result.success and result.token
    return (('authorization', f'Bearer {result.token}'),)


def test_upload_rejects_wrong_sha256():
    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)
        md = login(stub, 'mahasiswa', 'mhs123')
        content = b'integrity test'
        response = stub.Upload(pb2.UploadRequest(
            filename='sha_wrong.txt', label='PUBLIC', content=content,
            sha256='0' * 64), metadata=md, timeout=5)
        assert not response.success
        assert 'mismatch' in response.message.lower()
        assert not (ROOT / 'storage' / 'sha_wrong.txt').exists()


def test_tampered_file_is_detected_on_download():
    storage_file = ROOT / 'storage' / 'sha_tamper.txt'
    try:
        with create_mtls_channel() as channel:
            stub = pb2_grpc.FileStorageStub(channel)
            md = login(stub, 'admin', 'admin123')
            original = b'original trusted content'
            uploaded = stub.Upload(pb2.UploadRequest(
                filename=storage_file.name, label='SECRET', content=original,
                sha256=sha256_bytes(original)), metadata=md, timeout=5)
            assert uploaded.success
            assert uploaded.sha256 == sha256_bytes(original)

            # Simulate an illegal manual modification directly on server disk.
            storage_file.write_bytes(b'ILLEGAL MODIFICATION')

            downloaded = stub.Download(pb2.DownloadRequest(filename=storage_file.name), metadata=md, timeout=5)
            assert not downloaded.success
            assert 'integrity check failed' in downloaded.message.lower()
            assert downloaded.sha256 == sha256_bytes(b'ILLEGAL MODIFICATION')
            assert downloaded.content == b''
    finally:
        storage_file.unlink(missing_ok=True)


def test_valid_file_download_passes_integrity_check():
    storage_file = ROOT / 'storage' / 'sha_valid.txt'
    try:
        with create_mtls_channel() as channel:
            stub = pb2_grpc.FileStorageStub(channel)
            md = login(stub, 'admin', 'admin123')
            content = b'valid trusted content'
            uploaded = stub.Upload(pb2.UploadRequest(
                filename=storage_file.name, label='SECRET', content=content,
                sha256=sha256_bytes(content)), metadata=md, timeout=5)
            assert uploaded.success
            downloaded = stub.Download(pb2.DownloadRequest(filename=storage_file.name), metadata=md, timeout=5)
            assert downloaded.success
            assert downloaded.content == content
            assert downloaded.sha256 == sha256_bytes(content)
    finally:
        storage_file.unlink(missing_ok=True)
