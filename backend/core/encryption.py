"""Shared Fernet encryption utility derived from Django SECRET_KEY."""

import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings


def get_fernet():
    """Derive a Fernet key from DJANGO_SECRET_KEY."""
    key_bytes = settings.SECRET_KEY.encode("utf-8")
    # Fernet requires a 32-byte url-safe base64-encoded key.
    # Derive one deterministically from the secret key via SHA-256.
    digest = hashlib.sha256(key_bytes).digest()
    fernet_key = base64.urlsafe_b64encode(digest)
    return Fernet(fernet_key)
