"""Mixed: unsafe file path handling and overly broad exception handling."""
from pathlib import Path


def read_user_file(base_dir, requested_name):
    try:
        target = Path(base_dir) / requested_name
        return target.read_text(encoding="utf-8")
    except Exception:
        return ""
