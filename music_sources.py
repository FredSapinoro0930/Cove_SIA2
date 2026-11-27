"""One place that knows about both music services."""
import deezer
import jamendo

SOURCES = {"jamendo": jamendo, "deezer": deezer}
LABELS = {"jamendo": "Jamendo", "deezer": "Deezer 30s"}


def get_fresh_track(source, track_id):
    """The track with a new stream link, or None if it can't be fetched."""
    service = SOURCES.get(source)
    return service.get_track(track_id) if service else None


def lookup(refs, cache):
    """Turn saved (source, track_id) pairs into track details. Run on a background thread.

    `cache` is {(source, id): track}. Returns only the newly fetched entries.
    """
    found = {}
    for name, service in SOURCES.items():
        missing = [tid for src, tid in refs if src == name and (src, tid) not in cache]
        if missing:
            for tid, track in service.get_tracks(missing).items():
                found[(name, tid)] = track
    return found
