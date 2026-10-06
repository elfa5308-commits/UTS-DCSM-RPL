import json
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / 'logs'
AUDIT_LOG = LOG_DIR / 'audit.log'
_LOCK = threading.Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def write_audit(action: str, decision: str, *, user: str = 'anonymous', role: str = '',
                filename: str = '', label: str = '', reason: str = '') -> None:
    """Append one structured JSON audit event. Never store passwords or JWT tokens."""
    event = {
        'timestamp': _utc_now(),
        'user': user or 'anonymous',
        'action': action,
        'decision': decision,
    }
    if role:
        event['role'] = role
    if filename:
        event['filename'] = filename
    if label:
        event['label'] = label
    if reason:
        event['reason'] = reason

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, sort_keys=True)
    with _LOCK:
        with AUDIT_LOG.open('a', encoding='utf-8') as handle:
            handle.write(line + '\n')
            handle.flush()
