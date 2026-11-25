import html
import random
import requests

BASE_URL = "https://opentdb.com"


def _get_json(path, params=None):
    try:
        response = requests.get(f"{BASE_URL}/{path}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        raise Exception("Could not reach Open Trivia DB. Check your internet connection.")
    except ValueError:
        raise Exception("Open Trivia DB returned an unexpected response.")


def get_categories():
    """Returns a list like [{'id': 9, 'name': 'General Knowledge'}, ...]"""
    data = _get_json("api_category.php")
    categories = []
    for c in data.get("trivia_categories", []):
        categories.append({"id": c["id"], "name": html.unescape(c["name"])})
    return categories


def get_questions(amount=10, category=None, difficulty=None):
    """Returns a list of question dicts. Empty list if there are no matching questions."""
    params = {"amount": amount, "type": "multiple"}  # multiple choice = 4 answers
    if category:
        params["category"] = category
    if difficulty:
        params["difficulty"] = difficulty

    data = _get_json("api.php", params)
    code = data.get("response_code")
    if code == 5:
        raise Exception("Too many requests. Wait a few seconds and try again.")
    if code != 0:
        return []  # for example: not enough questions for that category and difficulty

    questions = []
    for item in data.get("results", []):
        # the API sends special characters as HTML codes (like &quot;), so decode them
        correct = html.unescape(item["correct_answer"]).strip()
        answers = [html.unescape(a).strip() for a in item["incorrect_answers"]] + [correct]
        
        random.shuffle(answers)
        questions.append({
            "question": html.unescape(item["question"]),
            "correct": correct,
            "answers": answers,
            "category": html.unescape(item.get("category", "")),
            "difficulty": item.get("difficulty", ""),
        })
    return questions


if __name__ == "__main__":
    for q in get_questions(3):
        print(q["question"])
        print("   answers:", q["answers"], "| correct:", q["correct"])