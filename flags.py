import random
import requests

CODES_URL = "https://flagcdn.com/en/codes.json"
IMAGE_URL = "https://flagcdn.com/w320/{code}.png"
_cache = []  # the country list is downloaded once, then reused


def get_countries():
    """Returns a list like [{'name': 'Japan', 'flag_url': 'https://...png'}, ...]"""
    global _cache
    if _cache:
        return _cache
    try:
        response = requests.get(CODES_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        raise Exception("Could not reach FlagCDN. Check your internet connection.")
    except ValueError:
        raise Exception("FlagCDN returned an unexpected response.")

    if not isinstance(data, dict):
        raise Exception(f"FlagCDN error: {str(data)[:120]}")

    countries = []
    for code, name in data.items():
        # keep only real countries: 2-letter codes (skips regions like us-ca or gb-eng)
        # and skip the EU and UN flags, which are not countries
        if len(code) != 2 or code in ("eu", "un"):
            continue
        if isinstance(name, str) and name:
            countries.append({"name": name, "flag_url": IMAGE_URL.format(code=code)})
    if len(countries) < 4:
        raise Exception("Not enough countries were returned. Try again later.")
    _cache = countries
    return _cache


def make_question(countries):
    """Picks a random flag and 3 wrong answers."""
    correct = random.choice(countries)
    others = [c for c in countries if c["name"] != correct["name"]]
    wrong = random.sample(others, 3)
    answers = [c["name"] for c in wrong] + [correct["name"]]
    random.shuffle(answers)
    return {"flag_url": correct["flag_url"], "correct": correct["name"], "answers": answers}


def get_flag_image(url):
    """Downloads the flag picture and returns the raw bytes."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException:
        raise Exception("Could not load the flag image. Check your internet connection.")


if __name__ == "__main__":
    q = make_question(get_countries())
    print(q["flag_url"])
    print("   answers:", q["answers"], "| correct:", q["correct"])