import uuid
import secrets
import string


def generate_unique_id(prefix: str = "", length: int = 32) -> str | uuid.UUID:
    if not prefix:
        return uuid.uuid4()

    hex_chars = secrets.token_hex(max(length, 16))
    unique_part = hex_chars[:length]
    return f"{prefix}_{unique_part}"
