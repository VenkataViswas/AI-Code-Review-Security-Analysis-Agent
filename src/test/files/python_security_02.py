"""Security issue: hardcoded credential."""

API_TOKEN = "sk_test_EXAMPLE_DO_NOT_USE_123456"


def call_service(client):
    return client.get("/profile", headers={"Authorization": f"Bearer {API_TOKEN}"})
