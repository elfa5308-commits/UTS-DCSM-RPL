# UTS DCSM RPL - Testing

## Phase 5: RBAC + Security Label

Policy:
- `ADMIN / SECRET`: may read/write/delete `PUBLIC` and `SECRET`.
- `USER / PUBLIC`: may read/write/delete `PUBLIC` only.
- `USER / PUBLIC` cannot read, write, list, or delete `SECRET` files.
- File labels are persisted in `storage/.metadata.json`.

Test:
```bash
python -m pytest -q tests/test_rbac_labels.py
```

The tests directly cover the core behavior required by TC-RPL-02.
