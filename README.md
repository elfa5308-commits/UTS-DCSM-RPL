# UTS DCSM RPL — Secure File Storage System

Project UTS untuk spesifikasi **Kelas RPL**.

## Scope
- 100% Python
- gRPC
- 2-tier Client → Secure Server / Storage Service
- mTLS untuk secure transport
- JWT untuk authentication
- RBAC + Security Label (PUBLIC / SECRET) — fase berikutnya
- SHA-256 checksum
- Structured JSON audit log (`logs/audit.log`)
- Docker / Docker Compose

## Progress
- [x] Fase 1 — Project structure
- [x] Fase 2 — TLS/mTLS
- [x] Fase 3 — gRPC Upload/Download/List/Delete
- [x] Fase 4 — JWT Authentication
- [x] Fase 5 — RBAC + Security Label
- [x] Fase 6 — SHA-256 tamper verification enhancement
- [x] Fase 7 — JSON Audit Log
- [x] Fase 8 — TC-RPL-01 s/d TC-RPL-04 final test suite
- [x] Fase 9 — Docker
- [ ] Fase 10 — Design Document
- [ ] Fase 11 — Video Demo
- [ ] Fase 12 — Slide Presentasi

## Demo users
- `mahasiswa` / `mhs123` — USER / PUBLIC
- `admin` / `admin123` — ADMIN / SECRET

> Credentials di atas hanya untuk demonstrasi lokal UTS.

## Menjalankan server
```bash
python -m server.server
```

## Menjalankan client
```bash
python client/client.py
```

## Testing
```bash
pytest -q tests/test_mtls.py tests/test_jwt_auth.py
```

## Fase 4 result
Semua test autentikasi dan proteksi request berhasil: **5 passed**.

## Fase 5 result
RBAC dan Security Label `PUBLIC/SECRET` berhasil diterapkan. `ADMIN/SECRET` dapat mengakses kedua label, sedangkan `USER/PUBLIC` hanya dapat membaca/menulis/menghapus `PUBLIC`. File `SECRET` disembunyikan dari listing user PUBLIC dan akses langsung ditolak dengan `PERMISSION_DENIED`. Full regression suite: **9 passed**.

## Fase 6 result
SHA-256 checksum sekarang disimpan bersama metadata file saat upload dan diverifikasi kembali saat download. Upload dengan hash yang salah ditolak, file yang diubah langsung pada storage terdeteksi sebagai tampering, dan file yang tidak berubah lolos integrity check. Full regression suite: **12 passed**.


## Fase 9 result
Dockerfile dan Docker Compose telah di-hardening dan divalidasi secara statis. Private key sertifikat tidak lagi masuk ke Docker image karena `certificates/*.key` dikecualikan melalui `.dockerignore`; server/client menggunakan sertifikat melalui volume mount. Client container menggunakan `DCSM_SERVER_TARGET=server:50051` agar dapat terhubung ke service server melalui jaringan Compose.

Runtime `docker build` / `docker compose up` belum dapat dijalankan pada environment pengembangan ini karena Docker CLI tidak tersedia. Validasi runtime harus dilakukan pada mesin yang memiliki Docker Engine/Desktop.

Perintah validasi runtime:
```bash
docker compose build
docker compose up -d server
docker compose run --rm client
docker compose logs server
docker compose down
```

## Generative AI Usage
Penggunaan Generative AI dicantumkan secara eksplisit pada dokumentasi project. AI digunakan sebagai alat bantu pada tahap perancangan struktur, review kode, debugging, dan dokumentasi; keputusan implementasi, pengujian, dan verifikasi hasil dilakukan oleh mahasiswa.

## Fase 7 result
Structured JSON audit log sudah diterapkan menggunakan JSON Lines (`logs/audit.log`). Setiap event mencatat `timestamp`, `user`, `action`, dan `decision` (`ALLOW`/`DENY`), serta konteks `role`, `filename`, `label`, dan `reason` bila diperlukan. Password dan JWT token tidak pernah ditulis ke audit log. Audit mencakup LOGIN, UPLOAD, DOWNLOAD, LIST, DELETE, termasuk penolakan autentikasi, RBAC/security label, dan kegagalan integrity check. Full regression suite: **13 passed**.


## Fase 8 — Final Test Suite

Empat test case wajib RPL telah diuji dan seluruhnya PASS:

- **TC-RPL-01** — Upload & Download File with TLS: PASS
- **TC-RPL-02** — RBAC & Security Label + Audit DENY: PASS
- **TC-RPL-03** — Invalid Client Certificate Rejected: PASS
- **TC-RPL-04** — File Tampering Detected by SHA-256: PASS

Regression test gabungan menghasilkan **17 passed**. Detail tersedia pada `tests/TEST_REPORT_RPL.md` dan implementasi test pada `tests/test_rpl_tc_suite.py`.
