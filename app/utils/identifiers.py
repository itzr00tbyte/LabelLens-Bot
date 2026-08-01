import secrets


def generate_error_reference() -> str:
    return f"ERR-{secrets.token_hex(3).upper()}"
