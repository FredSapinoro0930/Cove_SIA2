import random
import requests

BASE_URL = "https://pokeapi.co/api/v2"

# name shown in the app -> highest Pokedex number included
GENERATIONS = {
    "Gen 1 (1-151)": 151,
    "Gen 1-3 (1-386)": 386,
    "Gen 1-8 (1-898)": 898,
}

_names = []  # [(id, name), ...] downloaded once, then reused (the API asks clients to cache)


def _get_json(url, params=None):
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        raise Exception("Could not reach PokeAPI. Check your internet connection.")
    except ValueError:
        raise Exception("PokeAPI returned an unexpected response.")


def _load_names(upto):
    """Download the Pokemon name list (100 per request) until we have at least `upto` of them."""
    while len(_names) < upto:
        data = _get_json(f"{BASE_URL}/pokemon-species", {"limit": 100, "offset": len(_names)}) 
        results = data.get("results", [])
        if not results:
            break
        for r in results:
            poke_id = int(r["url"].rstrip("/").rsplit("/", 1)[-1])
            _names.append((poke_id, r["name"]))


def pretty_name(raw):
    return raw.replace("-", " ").title()  # "mr-mime" -> "Mr Mime"


def _get_image_url(poke_id):
    data = _get_json(f"{BASE_URL}/pokemon/{poke_id}")
    sprites = data.get("sprites") or {}
    other = sprites.get("other") or {}
    artwork = (other.get("official-artwork") or {}).get("front_default")
    return artwork or sprites.get("front_default")  # fall back to the small sprite


def _download_image(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException:
        raise Exception("Could not download the Pokemon image.")


def make_round(max_id):
    """One question: the mystery Pokemon, 4 name choices, and the image bytes."""
    _load_names(max_id)
    pool = _names[:max_id]

    image_url = None
    for _ in range(5):  # a few tries, in case one Pokemon has no image
        correct = random.choice(pool)
        image_url = _get_image_url(correct[0])
        if image_url:
            break
    if not image_url:
        raise Exception("Could not find an image. Try again.")

    wrong = random.sample([p for p in pool if p[0] != correct[0]], 3)
    choices = [pretty_name(name) for _, name in wrong] + [pretty_name(correct[1])]
    random.shuffle(choices)

    return {
        "id": correct[0],
        "name": pretty_name(correct[1]),
        "choices": choices,
        "image": _download_image(image_url),
    }


if __name__ == "__main__":
    for _ in range(3):
        r = make_round(151)
        is_png = r["image"][:4] == b"\x89PNG"
        print(f"#{r['id']} {r['name']} | choices: {r['choices']}")
        print(f"    image: {len(r['image'])} bytes, PNG: {is_png}")