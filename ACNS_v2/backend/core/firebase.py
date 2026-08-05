"""
core/firebase.py — Firebase SDK initialization.

Single place where the Firebase Admin SDK is bootstrapped and the Firestore
client handle is created. Every feature service imports ``db`` from here.

Credentials are resolved in this priority order:

1. ``FIREBASE_SERVICE_ACCOUNT_JSON`` — the full service-account JSON document
   as an environment variable (used on Railway / container platforms where
   secrets are injected as strings and writing files is discouraged). The
   JSON is parsed in memory and passed straight to the Admin SDK; no
   temporary file is ever written.
2. ``backend/serviceAccountKey.json`` — local development (gitignored), so
   the path stays valid regardless of the module's location.

If neither credential source is present, a clear ``RuntimeError`` is raised
so a misconfigured deployment fails fast at import time.
"""

import json
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

_KEY_PATH = Path(__file__).resolve().parents[1] / "serviceAccountKey.json"


def _load_credentials():
    """Return Admin SDK credentials, preferring the env var over the key file."""
    env_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if env_json:
        try:
            return credentials.Certificate(json.loads(env_json))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_JSON is set but could not be parsed as "
                "a valid Firebase service-account JSON document."
            ) from exc

    if _KEY_PATH.exists():
        return credentials.Certificate(os.fspath(_KEY_PATH))

    raise RuntimeError(
        "Firebase credentials are missing. Set the FIREBASE_SERVICE_ACCOUNT_JSON "
        f"environment variable or place the service account file at {_KEY_PATH}."
    )


cred = _load_credentials()
firebase_admin.initialize_app(cred)

db = firestore.client()
