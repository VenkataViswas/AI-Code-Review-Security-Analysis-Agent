"""Code quality issue: broad exception handling hides failures."""

def load_settings(path):
    try:
        with open(path, encoding="utf-8") as settings_file:
            return settings_file.read()
    except Exception:
        return None
