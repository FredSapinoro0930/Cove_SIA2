"""Deezer's public API: popular chart and search. No key needed.

The API only gives 30-second MP3 previews. Preview links expire, so the app asks for
a fresh one every time a song is played, and never saves them.
"""
import time
import requests

BASE_URL = "https://api.deezer.com"
PREVIEW_SECONDS = 30
QUOTA_ERROR = 4  # Deezer allows only a limited number of requests every few seconds


def _get_json(path, params=None):
    for attempt in range(3):
        try:
            response = requests.get(f"{BASE_URL}/{path}", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException:
            raise Exception("Could not reach Deezer. Check your internet connection.")
        except ValueError:
            raise Exception("Deezer returned an unexpected response.")

        error = data.get("error")  # Deezer reports errors inside a normal response
        if not error:
            return data
        if error.get("code") == QUOTA_ERROR and attempt < 2:
            time.sleep(5)  # only ever runs on a background thread
            continue
        raise Exception(f"Deezer: {error.get('message') or 'request failed'}")


def _to_track(item):
    return {
        "source": "deezer",
        "id": str(item.get("id")),
        "title": item.get("title") or "Unknown",
        "artist": (item.get("artist") or {}).get("name") or "Unknown",
        "album": (item.get("album") or {}).get("title") or "",
        "duration": PREVIEW_SECONDS,
        "stream_url": item.get("preview") or "",
    }


def _playable(data):
    return [_to_track(i) for i in data.get("data", []) if i.get("preview")]


def chart_tracks(limit=50):
    return _playable(_get_json("chart/0/tracks", {"limit": limit}))


def search_tracks(query, limit=30):
    return _playable(_get_json("search", {"q": query, "limit": limit}))


def get_track(track_id):
    """One track with a fresh preview link. Returns None on any failure."""
    try:
        track = _to_track(_get_json(f"track/{int(track_id)}"))
    except Exception:
        return None
    return track if track["stream_url"] else None


def get_tracks(track_ids):
    """Returns {id: track}. Deezer has no bulk lookup, so this asks one at a time."""
    found = {}
    for track_id in track_ids:
        track = get_track(track_id)
        if track:
            found[str(track_id)] = track
    return found


if __name__ == "__main__":
    for t in chart_tracks(limit=5):
        print(t["title"], "-", t["artist"])
        print("   ", t["stream_url"])
