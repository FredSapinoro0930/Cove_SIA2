import re
import requests
from urllib.parse import quote

SEARCH_URL = "https://archive.org/advancedsearch.php"
METADATA_URL = "https://archive.org/metadata"
DOWNLOAD_URL = "https://archive.org/download"

# name shown in the app -> archive.org collection name
COLLECTIONS = {
    "Feature films": "feature_films",
    "Classic TV": "classic_tv",
    "Vintage & educational films": "prelinger",
}

# crude filter: titles containing these whole words are hidden from the results
BLOCKED_WORDS = ["sex", "sexy", "nude", "nudist", "naked", "erotic", "porn", "xxx"]
_BLOCKED = re.compile(r"\b(" + "|".join(BLOCKED_WORDS) + r")\b", re.IGNORECASE)


def _get_json(url, params=None):
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        raise Exception("Could not reach the Internet Archive. Check your internet connection.")
    except ValueError:
        raise Exception("The Internet Archive returned an unexpected response.")


def _first(value, default=""):
    """Some fields come back as a list, some as plain text, some missing."""
    if isinstance(value, list):
        return value[0] if value else default
    return default if value is None else value


def search_videos(collection, keyword="", rows=25):
    """Returns a list of {'id', 'title', 'year'} for videos in a collection."""
    # keep letters, numbers and spaces only, so odd characters can't break the query
    keyword = "".join(ch for ch in keyword if ch.isalnum() or ch.isspace()).strip()

    query = f"collection:({collection}) AND mediatype:(movies)"
    if keyword:
        query += f" AND ({keyword})"

    params = {
        "q": query,
        "fl[]": ["identifier", "title", "year"],
        "sort[]": "downloads desc",
        "rows": rows,
        "page": 1,
        "output": "json",
    }
    data = _get_json(SEARCH_URL, params)
    docs = data.get("response", {}).get("docs", [])

    videos = []
    for d in docs:
        if not d.get("identifier"):
            continue
        title = str(_first(d.get("title"), "Untitled"))
        if _BLOCKED.search(title):
            continue
        videos.append({
            "id": d["identifier"],
            "title": title,
            "year": str(_first(d.get("year"), "")),
        })
    return videos


def get_playable_files(identifier):
    """All streamable mp4 files in an item. A movie has one, a TV series may have many."""
    data = _get_json(f"{METADATA_URL}/{identifier}")
    files = data.get("files", [])

    mp4s = [f for f in files if str(f.get("name", "")).lower().endswith(".mp4")]
    # prefer the h.264 versions (the ones Windows plays best), otherwise any mp4
    h264 = [f for f in mp4s if str(f.get("format", "")).lower() == "h.264"]
    chosen = h264 or mp4s

    results = []
    for f in sorted(chosen, key=lambda f: f["name"]):
        try:
            size_mb = round(int(f.get("size", 0)) / 1_000_000)
        except (TypeError, ValueError):
            size_mb = 0
        short_name = f["name"].rsplit("/", 1)[-1].rsplit(".", 1)[0]
        results.append({
            "label": str(f.get("title") or short_name),
            "size_mb": size_mb,
            "url": f"{DOWNLOAD_URL}/{identifier}/{quote(f['name'])}",
        })
    return results


if __name__ == "__main__":
    for label, collection in COLLECTIONS.items():
        videos = search_videos(collection, rows=3)
        print(f"{label}: {len(videos)} results")
        for v in videos:
            files = get_playable_files(v["id"])
            print("    ", v["title"], "->", len(files), "playable file(s)")