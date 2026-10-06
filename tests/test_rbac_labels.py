import sys
from pathlib import Path

import grpc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from client.client import create_mtls_channel, sha256_bytes
from server import file_storage_pb2 as pb2
from server import file_storage_pb2_grpc as pb2_grpc


def login(stub, username, password):
    result = stub.Login(pb2.LoginRequest(username=username, password=password), timeout=5)
    assert result.success and result.token
    return (('authorization', f'Bearer {result.token}'),)


def test_user_can_upload_public_but_not_secret():
    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)
        md = login(stub, 'mahasiswa', 'mhs123')

        public = b'public rbac test'
        ok = stub.Upload(pb2.UploadRequest(
            filename='rbac_public.txt', label='PUBLIC', content=public,
            sha256=sha256_bytes(public)), metadata=md, timeout=5)
        assert ok.success

        try:
            stub.Upload(pb2.UploadRequest(
                filename='rbac_secret_user.txt', label='SECRET', content=b'secret',
                sha256=sha256_bytes(b'secret')), metadata=md, timeout=5)
        except grpc.RpcError as exc:
            assert exc.code() == grpc.StatusCode.PERMISSION_DENIED
        else:
            raise AssertionError('USER should not be allowed to upload SECRET files')


def test_public_user_cannot_download_secret_file():
    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)
        admin_md = login(stub, 'admin', 'admin123')
        secret = b'secret rbac test'
        uploaded = stub.Upload(pb2.UploadRequest(
            filename='rbac_secret.txt', label='SECRET', content=secret,
            sha256=sha256_bytes(secret)), metadata=admin_md, timeout=5)
        assert uploaded.success

        public_md = login(stub, 'mahasiswa', 'mhs123')
        try:
            stub.Download(pb2.DownloadRequest(filename='rbac_secret.txt'), metadata=public_md, timeout=5)
        except grpc.RpcError as exc:
            assert exc.code() == grpc.StatusCode.PERMISSION_DENIED
        else:
            raise AssertionError('PUBLIC user should not read SECRET file')

        listing = stub.List(pb2.ListRequest(), metadata=public_md, timeout=5)
        assert 'rbac_secret.txt' not in [f.filename for f in listing.files]


def test_admin_can_read_secret():
    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)
        md = login(stub, 'admin', 'admin123')
        response = stub.Download(pb2.DownloadRequest(filename='rbac_secret.txt'), metadata=md, timeout=5)
        assert response.success
        assert response.label == 'SECRET'


def test_public_user_cannot_delete_secret():
    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)
        md = login(stub, 'mahasiswa', 'mhs123')
        try:
            stub.Delete(pb2.DeleteRequest(filename='rbac_secret.txt'), metadata=md, timeout=5)
        except grpc.RpcError as exc:
            assert exc.code() == grpc.StatusCode.PERMISSION_DENIED
        else:
            raise AssertionError('PUBLIC user should not delete SECRET file')
