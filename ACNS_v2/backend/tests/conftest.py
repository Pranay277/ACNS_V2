"""
tests/ — Backend regression suite.

Run from the backend directory:

    python -m pytest tests -q

Tests that only exercise pure logic (geo, SMS templates, validators) never
touch Firebase. The API-contract test imports the FastAPI app and therefore
requires ``serviceAccountKey.json`` to be present (it is skipped otherwise).

Credential-less environments (e.g. GitHub Actions, which intentionally has no
``serviceAccountKey.json`` and no ``FIREBASE_SERVICE_ACCOUNT_JSON`` secret):
``core.firebase`` resolves credentials at import time and raises a
``RuntimeError`` when both sources are missing, which aborts pytest collection
for every module that transitively imports it. To keep the suite runnable there,
a structurally-valid but fake service account is injected into the environment
when no real credentials exist, so imports succeed. The auth/API-contract tests
still skip (their guards check for the real ``serviceAccountKey.json`` file) and
the pure-logic tests never call Firestore, so the fake credentials are never
used for anything.
"""

import json
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Test-only synthetic service account (throwaway RSA key — never used for any
# request, never deployed). Only set when no real credential source exists.
_SYNTHETIC_SERVICE_ACCOUNT = {
    "type": "service_account",
    "project_id": "ci-test-project",
    "private_key_id": "ci-test-key-id",
    "private_key": (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEAy7VHnxIVD1/qodeHBplha8nXYF93sPiz6vxsGX3ZaN+kUsGF\n"
        "SgsoeW1sRh8lWH75TeE4jUPOHDLjhIkJ+oFSwo/kfDT4VhQIfVWuogqIwXkPMKv2\n"
        "AJcUebB4OGpBD5vCILd05aSNF1exzyOjWHJxGMBVgfVOEEGe6vBzdAQkJRVuxIym\n"
        "NtvQwhm/QJKKu1FMztd67W0gi3aY9ajYiKtYY/w6ugB6FY2aloJKnmMVfD7cnUGl\n"
        "M6X6uzI1oLDFvciyIKxE7ooW0HV44oE3XyzxWEGiaPBT4Qph+Ats5+FjXqkSahdZ\n"
        "s61LcfPTO8fQ0CTQsCkf6mWi+gFaU/Oq6eP66wIDAQABAoIBAGKT8rlZNETQ60fv\n"
        "dyGr5teVAPtbp53F9Lch+SPq4WNdWnVLvfdDaA4+9BcI6nclVvqno0jFR8AgpjZU\n"
        "ZLZLj+OkY3Lx5T0ui58vcAdtZpmNvlqU1MKbWea7janrTVnCy9IuRUz98OMbZmnx\n"
        "epIKK43JQXfW4DSAtOlHe+9oM5+Xnny37y9zctB9KAdxXAMC7k7JvuZ9hD0E/9Yw\n"
        "gPa4Z6H+ycSmg3Wx928XLn6VUA1aSUg9nqvQAHKTumzJxLwagR+9XEHqPtPSo9pk\n"
        "ynKKUHgV1Pe3wVU+ifUJmz0uQXop5X3cnoK+DA9ZGOd8HIL6Hh11gdND/R1Pa+6P\n"
        "5QKx5hkCgYEA9ZJvBd+OqijBUMezUypaR3Fyt5fi2dF4Dwh1YqvOHroAc1C+1v1D\n"
        "2u12kqcMGDVn61tV8gPo9WaUkK5svcKDPbvaH9T19qaqQrz9HziOZ1SNQ1IcQ3TC\n"
        "048FVraoOxOCDSYN132T5WXT+1vSb2KOMkp75W8no1GQx4yjH32TDEMCgYEA1FvA\n"
        "d8vT84o7FvA6z4PVDBty5k7r+FW4xgNdMQXUqXp33Slledhdylr0xfHcRweHLoUV\n"
        "r/AjNeEJAp0pMQhmBPYxqkgtqFFFL7RuDhMFuUCyxtvMyWzwPFE07zff6XILX2Zd\n"
        "1YDpAzPLBT0pdQzprM4bf3ucZ+nqZfiPMvP8wDkCgYEAwdjuxM8dGdsEBpUtTCfx\n"
        "jdXS/XPrAZAlWpCNwO7nzT98XYrOqnzP1ICAifFNTcrSlmnJ5ToK6bQo8DCP7Bcg\n"
        "bFneLCR6aFJVskrm8H8/gfevbwXhA6qmpEOQrkuPbtrOXTy9zm31ki6YcCGicoR0\n"
        "xOQg+xKMUpJvW+X7Wj9RFWsCgYBft8uVM8aha5keycF4b8/D2Ut9C+3IzbqvZizH\n"
        "P/2PNqh4g4Q924zK/Rx/bHkBex8vlMUlvHPigUBycSxz8Xkqm13fhxEtYRRyYD2L\n"
        "En/t9H+gqsovsG7IgUH+4YyHyOPfaGC7L5PX4ayM+/iHzf416eDzIWBqZkFFHThO\n"
        "mzM94QKBgHNYPpqB1Qbysc/owlkTW/ej7/Smub9rX21CTjPCRQwB3pSsDEkBfVTX\n"
        "mijjgE1xGDqCSeuqlvpISUa0z3gUFWE3dnDczflG4/UKsiwEVM1kqYrSRVwlozWV\n"
        "fv1rFkC6OUeAZy7rrgWj9+VkRmSw8gcv/ac67exRy2z7dq3sRRNi\n"
        "-----END RSA PRIVATE KEY-----\n"
    ),
    "client_email": "ci-test@ci-test-project.iam.gserviceaccount.com",
    "client_id": "0",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": (
        "https://www.googleapis.com/robot/v1/metadata/x509/"
        "ci-test%40ci-test-project.iam.gserviceaccount.com"
    ),
}

if (
    not os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    and not os.path.exists(os.path.join(BACKEND_DIR, "serviceAccountKey.json"))
):
    os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"] = json.dumps(_SYNTHETIC_SERVICE_ACCOUNT)
