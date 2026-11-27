"""Remembers who is logged in on this computer ("Stay logged in").

A random token is saved in the user's home folder, outside the project, so it can't be
committed to git by accident. The database only keeps a hash of it. No password is saved.
"""
import os
import db

SESSION_FILE = os.path.join(os.path.expanduser("~"), ".cove_session")


def _read_token():
    try:
        with open(SESSION_FILE, encoding="utf-8") as f:
            return f.read().strip()
    except (OSError, UnicodeDecodeError):
        return ""


def remember(user_id):
    forget()  # only one saved login per computer account
    token = db.create_session(user_id)
    try:
        # 0o600: readable only by this user (Windows ignores this and uses folder permissions)
        fd = os.open(SESSION_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(token)
    except OSError:
        db.delete_session(token)  # couldn't save it, so the user just logs in next time


def restore():
    """(user_id, username) if a saved login is still valid, otherwise None."""
    token = _read_token()
    if not token:
        return None
    user = db.get_session_user(token)
    if user is None:
        forget()
    return user


def forget():
    token = _read_token()
    if token:
        db.delete_session(token)
    try:
        os.remove(SESSION_FILE)
    except OSError:
        pass
