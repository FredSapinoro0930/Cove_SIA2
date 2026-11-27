import sqlite3
import hashlib
import hmac
import os
import secrets
import time

# next to this file, so the app finds the same database no matter where it is run from
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music.db")
SESSION_DAYS = 30
OLD_PLAYLIST_NAME = "My Playlist"
# "Stay logged in" token: kept in the home folder, outside the project, so git never sees it
SESSION_FILE = os.path.join(os.path.expanduser("~"), ".cove_session")


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            salt BLOB NOT NULL,
            password_hash BLOB NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playlist_songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            track_id TEXT NOT NULL,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            duration INTEGER NOT NULL,
            stream_url TEXT NOT NULL,
            UNIQUE (user_id, track_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS game_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            played_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            track_id TEXT NOT NULL,
            UNIQUE (user_id, source, track_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE (user_id, name)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playlist_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            track_id TEXT NOT NULL,
            UNIQUE (playlist_id, source, track_id)
        )
    """)
    _migrate_old_playlists(conn)
    conn.commit()
    conn.close()


def _migrate_old_playlists(conn):
    """Runs once: copies songs from the old one-playlist table into the new tables.

    The old table is left untouched as a backup.
    """
    if conn.execute("PRAGMA user_version").fetchone()[0] >= 1:
        return  # already done, so a playlist the user deleted never comes back
    rows = conn.execute(
        "SELECT user_id, track_id FROM playlist_songs ORDER BY id").fetchall()
    for user_id, track_id in rows:
        conn.execute("INSERT OR IGNORE INTO playlists (user_id, name) VALUES (?, ?)",
                     (user_id, OLD_PLAYLIST_NAME))
        playlist_id = conn.execute(
            "SELECT id FROM playlists WHERE user_id = ? AND name = ?",
            (user_id, OLD_PLAYLIST_NAME)).fetchone()[0]
        conn.execute(
            "INSERT OR IGNORE INTO playlist_tracks (playlist_id, source, track_id) "
            "VALUES (?, 'jamendo', ?)", (playlist_id, track_id))
    conn.execute("PRAGMA user_version = 1")


def _execute(sql, params=()):
    """Run one change. Returns the number of rows it affected."""
    conn = get_connection()
    try:
        with conn:  # commits, or rolls back on an error
            return conn.execute(sql, params).rowcount
    finally:
        conn.close()


def _query(sql, params=()):
    conn = get_connection()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)  # random salt, unique per user
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt, pw_hash


def register_user(username, password):
    if not username or not password:
        return False, "Username and password are required"
    salt, pw_hash = hash_password(password)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)",
            (username, salt, pw_hash),
        )
        conn.commit()
        return True, "Registered"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()


def login_user(username, password):
    conn = get_connection()
    row = conn.execute(
        "SELECT id, salt, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    user_id, salt, stored_hash = row
    _, new_hash = hash_password(password, salt)
    if hmac.compare_digest(new_hash, stored_hash):
        return user_id
    return None


# ---------- "stay logged in" sessions ----------
def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user_id):
    """Returns a random token. Only its hash is stored, never the password or the token."""
    token = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + SESSION_DAYS * 24 * 60 * 60
    _execute("DELETE FROM sessions WHERE expires_at <= ?", (int(time.time()),))
    _execute("INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
             (_hash_token(token), user_id, expires_at))
    return token


def get_session_user(token):
    """(user_id, username) for a valid token, otherwise None."""
    rows = _query(
        "SELECT u.id, u.username FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token_hash = ? AND s.expires_at > ?",
        (_hash_token(token), int(time.time())))
    return rows[0] if rows else None


def delete_session(token):
    _execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))


def _read_token():
    try:
        with open(SESSION_FILE, encoding="utf-8") as f:
            return f.read().strip()
    except (OSError, UnicodeDecodeError):
        return ""


def remember_login(user_id):
    forget_login()  # only one saved login per computer account
    token = create_session(user_id)
    try:
        # 0o600: readable only by this user (Windows ignores this and uses folder permissions)
        fd = os.open(SESSION_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(token)
    except OSError:
        delete_session(token)  # couldn't save it, so the user just logs in next time


def restore_login():
    """(user_id, username) if a saved login is still valid, otherwise None."""
    token = _read_token()
    if not token:
        return None
    user = get_session_user(token)
    if user is None:
        forget_login()
    return user


def forget_login():
    token = _read_token()
    if token:
        delete_session(token)
    try:
        os.remove(SESSION_FILE)
    except OSError:
        pass


# ---------- favorites ----------
def add_favorite(user_id, source, track_id):
    """Returns True if added, False if it was already a favorite."""
    return _execute(
        "INSERT OR IGNORE INTO favorites (user_id, source, track_id) VALUES (?, ?, ?)",
        (user_id, source, str(track_id))) == 1


def remove_favorite(user_id, source, track_id):
    _execute("DELETE FROM favorites WHERE user_id = ? AND source = ? AND track_id = ?",
             (user_id, source, str(track_id)))


def get_favorites(user_id):
    """A list of (source, track_id), oldest first."""
    return _query("SELECT source, track_id FROM favorites WHERE user_id = ? ORDER BY id",
                  (user_id,))


# ---------- playlists ----------
def create_playlist(user_id, name):
    """Returns the new playlist's id, or None if the name is empty or already used."""
    name = name.strip()
    if not name:
        return None
    conn = get_connection()
    try:
        with conn:
            return conn.execute("INSERT INTO playlists (user_id, name) VALUES (?, ?)",
                                (user_id, name)).lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_playlists(user_id):
    """A list of (playlist_id, name)."""
    return _query("SELECT id, name FROM playlists WHERE user_id = ? ORDER BY id", (user_id,))


def _owns_playlist(user_id, playlist_id):
    return bool(_query("SELECT 1 FROM playlists WHERE id = ? AND user_id = ?",
                       (playlist_id, user_id)))


def delete_playlist(user_id, playlist_id):
    if _owns_playlist(user_id, playlist_id):
        _execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
        _execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))


def add_to_playlist(user_id, playlist_id, source, track_id):
    """Returns True if added, False if it was already there."""
    if not _owns_playlist(user_id, playlist_id):
        return False
    return _execute(
        "INSERT OR IGNORE INTO playlist_tracks (playlist_id, source, track_id) "
        "VALUES (?, ?, ?)", (playlist_id, source, str(track_id))) == 1


def remove_from_playlist(user_id, playlist_id, source, track_id):
    if _owns_playlist(user_id, playlist_id):
        _execute("DELETE FROM playlist_tracks "
                 "WHERE playlist_id = ? AND source = ? AND track_id = ?",
                 (playlist_id, source, str(track_id)))


def get_playlist_tracks(user_id, playlist_id):
    """A list of (source, track_id) in the order they were added."""
    return _query(
        "SELECT t.source, t.track_id FROM playlist_tracks t "
        "JOIN playlists p ON p.id = t.playlist_id "
        "WHERE p.id = ? AND p.user_id = ? ORDER BY t.id", (playlist_id, user_id))


# ---------- game scores ----------
def save_score(user_id, game, score, total):
    conn = get_connection()
    conn.execute(
        "INSERT INTO game_scores (user_id, game, score, total) VALUES (?, ?, ?, ?)",
        (user_id, game, score, total),
    )
    conn.commit()
    conn.close()


def get_best_score(user_id, game):
    """This user's best score for a game, or None if they never played it."""
    conn = get_connection()
    row = conn.execute(
        "SELECT MAX(score) FROM game_scores WHERE user_id = ? AND game = ?",
        (user_id, game),
    ).fetchone()
    conn.close()
    return row[0]


def get_leaderboard(game, limit=5):
    """Top players for a game: a list of (username, best_score)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT u.username, MAX(g.score) AS best "
        "FROM game_scores g JOIN users u ON u.id = g.user_id "
        "WHERE g.game = ? GROUP BY g.user_id "
        "ORDER BY best DESC, u.username LIMIT ?",
        (game, limit),
    ).fetchall()
    conn.close()
    return [(r[0], r[1]) for r in rows]


if __name__ == "__main__":
    init_db()
    print(register_user("test", "pass123"))
    print(register_user("test", "pass123"))
    print(login_user("test", "pass123"))
    print(login_user("test", "wrong"))