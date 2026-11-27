import random
import requests

CLIENT_ID = "a18eaf22"
BASE_URL = "https://api.jamendo.com/v3.0"
RANDOM_POOL = 500  # random picks come from about this many of the most popular songs


def _to_seconds(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _request_tracks(extra_params):
    """Ask Jamendo for tracks. Raises Exception with a readable message on failure."""
    params = {
        "client_id": CLIENT_ID,
        "format": "json",
        "audioformat": "mp32",
    }
    params.update(extra_params)
    try:
        response = requests.get(f"{BASE_URL}/tracks/", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        raise Exception("Could not reach Jamendo. Check your internet connection.")
    except ValueError:
        raise Exception("Jamendo returned an unexpected response.")

    headers = data.get("headers", {})
    if headers.get("status") != "success":
        raise Exception(headers.get("error_message") or "Jamendo returned an error.")

    tracks = []
    for item in data.get("results", []):
        if not item.get("audio"):
            continue  # skip tracks with no stream URL
        tracks.append({
            "source": "jamendo",
            "id": str(item.get("id")),
            "title": item.get("name", "Unknown"),
            "artist": item.get("artist_name", "Unknown"),
            "album": item.get("album_name", ""),
            "duration": _to_seconds(item.get("duration")),
            "stream_url": item["audio"],
        })
    return tracks


def search_tracks(query, limit=20):
    return _request_tracks({"search": query, "limit": limit})


def random_tracks(limit=20):
    """A different set of popular songs each time (Jamendo has no "random" sort)."""
    params = {"order": "popularity_total", "limit": limit}
    offset = random.randrange(0, RANDOM_POOL, limit)
    tracks = _request_tracks({**params, "offset": offset})
    if not tracks:
        tracks = _request_tracks(params)  # fall back to the top of the list
    random.shuffle(tracks)
    return tracks


def get_tracks(track_ids):
    """Look up many tracks in as few requests as possible. Returns {id: track}."""
    ids = [str(i) for i in track_ids]
    found = {}
    for start in range(0, len(ids), 50):
        batch = ids[start:start + 50]
        try:
            for track in _request_tracks({"id[]": batch, "limit": len(batch)}):
                found[track["id"]] = track
        except Exception:
            pass  # anything missed is tried one at a time below
    for track_id in ids:
        if track_id not in found:
            track = get_track(track_id)
            if track:
                found[track_id] = track
    return found


def get_track(track_id):
    """Fetch one track by id to get a fresh stream link. Returns None on any failure."""
    try:
        tracks = _request_tracks({"id": track_id, "limit": 1})
    except Exception:
        return None
    return tracks[0] if tracks else None


if __name__ == "__main__":
    for t in search_tracks("chill", limit=5):
        print(t["title"], "-", t["artist"], "-", t["duration"], "seconds")
        print("   ", t["stream_url"])