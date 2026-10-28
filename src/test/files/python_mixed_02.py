"""Mixed: hardcoded password and poor configuration design."""

DATABASE_PASSWORD = "demo-password-123"


def connect(database_driver):
    # Credentials should come from a secret manager or environment configuration.
    return database_driver.connect(
        host="db.internal",
        user="app_user",
        password=DATABASE_PASSWORD,
    )
