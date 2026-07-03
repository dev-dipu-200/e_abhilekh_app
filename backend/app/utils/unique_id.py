import uuid
import secrets


def generate_unique_id(prefix: str = "", total_length: int = 10) -> str | uuid.UUID:
    if not prefix:
        return uuid.uuid4()

    hex_length = max(total_length - len(prefix) - 1, 2)
    hex_chars = secrets.token_hex(16)
    unique_part = hex_chars[:hex_length]
    return f"{prefix}_{unique_part}"
