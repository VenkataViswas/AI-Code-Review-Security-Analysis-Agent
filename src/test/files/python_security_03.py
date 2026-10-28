"""Security issue: unsafe deserialization of untrusted data."""
import pickle


def load_uploaded_object(upload_bytes):
    # Unsafe if upload_bytes comes from an untrusted user.
    return pickle.loads(upload_bytes)
