import hashlib
import os
import sys
from pathlib import Path

import grpc

from server import file_storage_pb2 as pb2
from server import file_storage_pb2_grpc as pb2_grpc

ROOT = Path(__file__).resolve().parent.parent
CERTS = ROOT / 'certificates'


def create_mtls_channel(target=None):
    target = target or os.getenv('DCSM_SERVER_TARGET', 'localhost:50051')
    ca_cert = (CERTS / 'ca.crt').read_bytes()
    client_cert = (CERTS / 'client.crt').read_bytes()
    client_key = (CERTS / 'client.key').read_bytes()
    credentials = grpc.ssl_channel_credentials(
        root_certificates=ca_cert,
        private_key=client_key,
        certificate_chain=client_cert,
    )
    return grpc.secure_channel(target, credentials)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    print('DCSM RPL - Secure gRPC Client')
    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)
        login = stub.Login(pb2.LoginRequest(username='mahasiswa', password='mhs123'), timeout=5)
        print(f'Login    : {login.success} - {login.message}')
        if not login.success:
            return
        metadata = (('authorization', f'Bearer {login.token}'),)

        sample = b'DCSM RPL JWT test file'
        upload = stub.Upload(pb2.UploadRequest(
            filename='demo.txt', label='PUBLIC', content=sample,
            sha256=sha256_bytes(sample)), timeout=5, metadata=metadata)
        print(f'Upload   : {upload.success} - {upload.message}')

        listing = stub.List(pb2.ListRequest(), timeout=5, metadata=metadata)
        print('List     :', [f.filename for f in listing.files])

        download = stub.Download(pb2.DownloadRequest(filename='demo.txt'), timeout=5, metadata=metadata)
        print(f'Download : {download.success} - {download.message}')
        print(f'Integrity: {sha256_bytes(download.content) == download.sha256}')

        delete = stub.Delete(pb2.DeleteRequest(filename='demo.txt'), timeout=5, metadata=metadata)
        print(f'Delete   : {delete.success} - {delete.message}')


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT))
    main()
