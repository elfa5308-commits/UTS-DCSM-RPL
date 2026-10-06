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
    print("TC-RPL-02 - RBAC + SECURITY LABEL")
    print("=" * 60)

    with create_mtls_channel() as channel:
        stub = pb2_grpc.FileStorageStub(channel)

        # ==========================================
        # 1. ADMIN LOGIN
        # ==========================================
        print("\n[1] Login sebagai ADMIN")

        admin_login = stub.Login(
            pb2.LoginRequest(
                username="admin",
                password="admin123"
            ),
            timeout=5
        )

        print(f"Login ADMIN : {admin_login.success}")
        print(f"Message     : {admin_login.message}")

        admin_metadata = (
            ("authorization", f"Bearer {admin_login.token}"),
        )

        # ==========================================
        # 2. ADMIN UPLOAD SECRET
        # ==========================================
        print("\n[2] ADMIN upload file SECRET")

        upload = stub.Upload(
            pb2.UploadRequest(
                filename="demo_secret.txt",
                label="SECRET",
                content=b"Data rahasia DCSM RPL",
            ),
            timeout=5,
            metadata=admin_metadata
        )

        print(f"Upload SECRET : {upload.success}")
        print(f"Message       : {upload.message}")

        # ==========================================
        # 3. USER LOGIN
        # ==========================================
        print("\n[3] Login sebagai USER")

        user_login = stub.Login(
            pb2.LoginRequest(
                username="mahasiswa",
                password="mhs123"
            ),
            timeout=5
        )

        print(f"Login USER : {user_login.success}")
        print(f"Message    : {user_login.message}")

        user_metadata = (
            ("authorization", f"Bearer {user_login.token}"),
        )

        # ==========================================
        # 4. USER DOWNLOAD SECRET
        # ==========================================
        print("\n[4] USER mencoba Download SECRET")

        try:
            download = stub.Download(
                pb2.DownloadRequest(
                    filename="demo_secret.txt"
                ),
                timeout=5,
                metadata=user_metadata
            )

            print(f"Download : {download.success}")
            print(f"Message  : {download.message}")

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.PERMISSION_DENIED:
                print("Result   : DENIED")
                print("Status   : PASS")
                print("Reason   : Security label policy denies reading this file.")
            else:
                print("Result   : ERROR")
                print("Status   : FAIL")
                print("Reason   :", e.details())

        # ==========================================
        # 5. CLEANUP
        # ==========================================
        print("\n[5] ADMIN menghapus file demo")

        delete = stub.Delete(
            pb2.DeleteRequest(
                filename="demo_secret.txt"
            ),
            timeout=5,
            metadata=admin_metadata
        )

        print(f"Delete : {delete.success}")
        print(f"Message: {delete.message}")

        print("\n" + "=" * 60)
        print("TC-RPL-02 SELESAI")
        print("=" * 60)


if __name__ == "__main__":
    main()