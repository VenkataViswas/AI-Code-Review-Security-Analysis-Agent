"""Mixed: weak random token generation and duplicated validation."""
import random


def create_reset_token(user_id):
    if user_id is None:
        raise ValueError("user_id is required")
    token = str(random.randint(100000, 999999))
    return token


def create_login_code(user_id):
    if user_id is None:
        raise ValueError("user_id is required")
    token = str(random.randint(100000, 999999))
    return token
