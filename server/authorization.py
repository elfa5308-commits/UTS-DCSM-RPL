LABEL_LEVELS = {
    'PUBLIC': 0,
    'SECRET': 1,
}

ALLOWED_LABELS = set(LABEL_LEVELS)


def normalize_label(label: str) -> str:
    value = (label or 'PUBLIC').strip().upper()
    if value not in ALLOWED_LABELS:
        raise ValueError(f'Invalid security label: {value}. Use PUBLIC or SECRET.')
    return value


def can_read(claims: dict, file_label: str) -> bool:
    """Simple Bell-LaPadula-style no-read-up rule using user clearance label."""
    user_label = normalize_label(claims.get('label', 'PUBLIC'))
    target_label = normalize_label(file_label)
    return LABEL_LEVELS[user_label] >= LABEL_LEVELS[target_label]


def can_write(claims: dict, target_label: str) -> bool:
    """RBAC/write policy: ADMIN may write any label; USER may write PUBLIC only."""
    role = str(claims.get('role', '')).upper()
    target = normalize_label(target_label)
    if role == 'ADMIN':
        return True
    return role == 'USER' and target == 'PUBLIC'


def can_delete(claims: dict, file_label: str) -> bool:
    """Deletion follows the same clearance rule plus RBAC role policy."""
    role = str(claims.get('role', '')).upper()
    if role == 'ADMIN':
        return True
    return role == 'USER' and can_read(claims, file_label) and normalize_label(file_label) == 'PUBLIC'
