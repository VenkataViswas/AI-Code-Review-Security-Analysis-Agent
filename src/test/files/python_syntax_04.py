# Intentional syntax error: assignment used where a comparison was intended.
def is_admin(role):
    if role = "admin":
        return True
    return False
