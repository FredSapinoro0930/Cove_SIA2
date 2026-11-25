import sqlite3
import hashlib
import hmac
import os

DB_NAME = "music.db"


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
    conn.commit()
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


# ---------- playlist ----------
def add_to_playlist(user_id, track):
    """Returns True if added, False if the song is already in this user's playlist."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO playlist_songs "
            "(user_id, track_id, title, artist, duration, stream_url) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, str(track["id"]), track["title"], track["artist"],
             track["duration"], track["stream_url"]),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_from_playlist(user_id, track_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM playlist_songs WHERE user_id = ? AND track_id = ?",
        (user_id, str(track_id)),
    )
    conn.commit()
    conn.close()


def get_playlist(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT track_id, title, artist, duration, stream_url "
        "FROM playlist_songs WHERE user_id = ? ORDER BY id",
        (user_id,),
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "title": r[1], "artist": r[2], "duration": r[3], "stream_url": r[4]}
        for r in rows
    ]


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