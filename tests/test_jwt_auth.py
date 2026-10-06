import sys
from pathlib import Path

import grpc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from client.client import create_mtls_channel
from server import file_storage_pb2 as pb2
from server import file_storage_pb2_grpc as pb2_grpc


def test_login_success_and_protected_request():
    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)
        login = stub.Login(pb2.LoginRequest(username='mahasiswa', password='mhs123'), timeout=5)
        assert login.success and login.token
        md = (('authorization', f'Bearer {login.token}'),)
        response = stub.List(pb2.ListRequest(), timeout=5, metadata=md)
        assert response is not None


def test_login_invalid_credentials():
    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)
        login = stub.Login(pb2.LoginRequest(username='mahasiswa', password='salah'), timeout=5)
        assert not login.success
        assert not login.token


def test_protected_request_without_jwt_is_rejected():
    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)
        try:
            stub.List(pb2.ListRequest(), timeout=5)
            assert False, 'Request without JWT should be rejected'
        except grpc.RpcError as exc:
            assert exc.code() == grpc.StatusCode.UNAUTHENTICATED
