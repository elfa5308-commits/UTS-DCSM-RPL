from pathlib import Path
import grpc

from client.client import create_mtls_channel
from server import file_storage_pb2 as pb2
from server import file_storage_pb2_grpc as pb2_grpc

ROOT = Path(__file__).resolve().parent.parent
CERTS = ROOT / 'certificates'


def test_valid_client_certificate():
    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)
        response = stub.Login(pb2.LoginRequest(username='mahasiswa', password='mhs123'), timeout=5)
        assert response.success and response.token


def test_missing_client_certificate_is_rejected():
    ca_cert = (CERTS / 'ca.crt').read_bytes()
    credentials = grpc.ssl_channel_credentials(root_certificates=ca_cert)
    with grpc.secure_channel('localhost:50051', credentials) as channel:
        stub = pb2_grpc.FileStorageStub(channel)
        try:
            stub.Login(pb2.LoginRequest(username='demo', password='demo'), timeout=5)
        except grpc.RpcError as exc:
            assert exc.code() in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.UNKNOWN)
        else:
            raise AssertionError('Connection without client certificate was unexpectedly accepted.')
