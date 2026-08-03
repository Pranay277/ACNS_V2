"""
tests/ — Backend regression suite.

Run from the backend directory:

    python -m pytest tests -q

Tests that only exercise pure logic (geo, SMS templates, validators) never
touch Firebase. The API-contract test imports the FastAPI app and therefore
requires ``serviceAccountKey.json`` to be present (it is skipped otherwise).
"""

import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
