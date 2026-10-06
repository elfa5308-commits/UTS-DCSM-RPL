from datetime import datetime, timedelta, timezone
import os
import jwt

JWT_SECRET = os.getenv('DCSM_JWT_SECRET', 'DCSM-UTS-RPL-DEMO-SECRET-KEY-2026')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRE_MINUTES = 30

USERS = {
    'admin': {'password': 'admin123', 'role': 'ADMIN', 'label': 'SECRET'},
    'mahasiswa': {'password': 'mhs123', 'role': 'USER', 'label': 'PUBLIC'},
}


def authenticate(username: str, password: str):
    user = USERS.get(username)
    if not user or user['password'] != password:
        return None
    now = datetime.now(timezone.utc)
    payload = {
        'sub': username,
        'role': user['role'],
        'label': user['label'],
        'iat': now,
        'exp': now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def validate_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
