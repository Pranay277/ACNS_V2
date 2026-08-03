"""
core/ — Global infrastructure.

Modules here are importable by every feature:
    config.py   — centralized configuration (constants + env settings).
    firebase.py — Firebase Admin SDK initialization (single Firestore handle).
    logging.py  — optional root logging configuration.

Nothing in core/ imports from features/ or shared/.
"""
