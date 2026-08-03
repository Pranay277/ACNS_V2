"""
core/firebase.py — Firebase SDK initialization.

Single place where the Firebase Admin SDK is bootstrapped and the Firestore
client handle is created. Every feature service imports ``db`` from here.

The service account key is read from ``backend/serviceAccountKey.json``
(gitignored) so the path stays valid regardless of the module's location.
"""

import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

_KEY_PATH = Path(__file__).resolve().parents[1] / "serviceAccountKey.json"

cred = credentials.Certificate(os.fspath(_KEY_PATH))
firebase_admin.initialize_app(cred)

db = firestore.client()
