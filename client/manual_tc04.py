import sys
from pathlib import Path

import grpc

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import file_storage_pb2 as pb2
from server import file_storage_pb2_grpc as pb2_grpc
from client.client import create_mtls_channel


def main():
    print("=" * 60)
    print("TC-RPL-04 - SHA-256 FILE TAMPERING")
    print("=" * 60)

    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)

        print("\n[1] Login sebagai ADMIN")

        login = stub.Login(
            pb2.LoginRequest(
                username="admin",
                password="admin123"
            ),
            timeout=5
        )

        print(f"Login : {login.success}")
        print(f"Message: {login.message}")

        metadata = (
            ("authorization", f"Bearer {login.token}"),
        )

        print("\n[2] ADMIN mencoba Download demo_secret.txt")

        download = stub.Download(
            pb2.DownloadRequest(
                filename="demo_secret.txt"
            ),
            timeout=5,
            metadata=metadata
        )

        print(f"Success : {download.success}")
        print(f"Message : {download.message}")
        print(f"SHA-256 : {download.sha256}")

        print("\n" + "=" * 60)
        print("TC-RPL-04 SELESAI")
        print("=" * 60)


if __name__ == "__main__":
    main()