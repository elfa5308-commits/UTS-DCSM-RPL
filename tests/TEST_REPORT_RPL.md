# RPL UTS — Final Test Report

## Environment
- Language: Python
- RPC: gRPC
- Transport Security: TLS/mTLS
- Authentication: JWT
- Authorization: RBAC + Security Label (PUBLIC/SECRET)
- Integrity: SHA-256
- Audit: JSON Lines
- Server: `localhost:50051`

## Official RPL Test Cases

| Test Case | Test | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| TC-RPL-01 | Upload & Download File with TLS | File can be uploaded and downloaded through authenticated mTLS gRPC channel | Upload succeeded; download succeeded; content and SHA-256 matched | PASS |
| TC-RPL-02 | RBAC & Security Label | USER cannot access SECRET; denied request recorded as `DENY` | `PERMISSION_DENIED`; audit event recorded with `DOWNLOAD` + `DENY` + `SECRET` | PASS |
| TC-RPL-03 | Invalid Client Certificate | Connection without valid client certificate is rejected during TLS handshake | gRPC connection rejected with `UNAVAILABLE`/`UNKNOWN` | PASS |
| TC-RPL-04 | File Tampering / SHA-256 | Modified server-side file must be detected | SHA-256 mismatch detected; content not returned | PASS |

## Regression Test Result

Command:

```text
PYTHONPATH=. pytest -q tests/test_rpl_tc_suite.py tests/test_mtls.py tests/test_jwt_auth.py tests/test_rbac_labels.py tests/test_sha256_integrity.py tests/test_audit_log.py
```

Result:

```text
17 passed in 0.41s
```

## Security Evidence

1. mTLS requires a client certificate signed by the configured CA.
2. JWT is required for protected file operations.
3. RBAC enforces the PUBLIC/SECRET security-label policy.
4. SHA-256 is stored as file metadata and verified before a download is returned.
5. Audit logs record security decisions as structured JSON without storing passwords or JWT tokens.

## Conclusion

All four mandatory RPL UTS test cases passed. The current implementation satisfies the functional security test requirements for mTLS, token authentication, RBAC/security labels, SHA-256 integrity checking, and audit logging.
