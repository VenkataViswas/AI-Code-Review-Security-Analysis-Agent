"""Clean example: small functions and explicit validation."""

def calculate_discount(price: float, percentage: float) -> float:
    if price < 0:
        raise ValueError("price cannot be negative")
    if not 0 <= percentage <= 100:
        raise ValueError("percentage must be between 0 and 100")
    return price * (1 - percentage / 100)


def format_username(username: str) -> str:
    cleaned = username.strip()
    if not cleaned:
        raise ValueError("username cannot be empty")
    return cleaned
