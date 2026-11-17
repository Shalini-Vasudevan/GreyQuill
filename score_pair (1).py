from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from itertools import permutations


@dataclass
class FieldComparison:

    attribute: str
    method: str
    weight: float


@dataclass
class MatchResult:
    confidence: float
    algorithm: str
    field_scores: dict[str, float]


PLAN = [
    FieldComparison("name", "phonetic", 0.25),
    FieldComparison("email", "edit_distance", 0.20),
    FieldComparison("phone", "normalized_phone", 0.20),
    FieldComparison("date_of_birth", "date", 0.20),
    FieldComparison("pin_code", "exact", 0.10),
    FieldComparison("city", "exact", 0.05),
]


def clean(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def levenshtein(s, t):
    previous = list(range(len(t) + 1))
    for i, a in enumerate(s, start=1):
        current = [i]
        for j, b in enumerate(t, start=1):
            cost = 0 if a == b else 1
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost))
        previous = current
    return previous[-1]


def similarity(s, t):
    longest = max(len(s), len(t))
    if longest == 0:
        return 1.0
    return 1 - levenshtein(s, t) / longest


def email_score(a, b):
    return similarity(a.lower(), b.lower())


def sound_key(word):
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return ""
    for old, new in [("sh", "s"), ("ph", "f"), ("th", "t"), ("dh", "d"), ("bh", "b"),
                     ("ee", "i"), ("oo", "u"), ("w", "v"), ("y", "i"), ("z", "s")]:
        word = word.replace(old, new)
    word = re.sub(r"(.)\1+", r"\1", word)

    return word[0] + re.sub(r"[aeiouh]", "", word[1:])


def word_score(a, b):
    if a == b:
        return 1.0
    if len(a) == 1 or len(b) == 1:
        return 0.85 if a[0] == b[0] else 0.0
    by_spelling = similarity(a, b)
    key_a, key_b = sound_key(a), sound_key(b)
    if key_a == key_b:
        by_sound = 0.95
    else:
        by_sound = similarity(key_a, key_b)
    return max(by_spelling, by_sound)


def name_words(name):

    words = [re.sub(r"[^a-z]", "", w) for w in re.split(r"[\s,]+", name.lower())]
    return [w for w in words if w]


def name_score(a, b):
    words_a, words_b = name_words(a), name_words(b)
    if not words_a or not words_b:
        return 0.0
    short, long = sorted([words_a, words_b], key=len)

    best = 0.0
    for order in permutations(long, len(short)):
        total = sum(word_score(x, y) for x, y in zip(short, order))
        best = max(best, total)

    score = best / len(short)
    score -= 0.05 * (len(long) - len(short))
    return max(0.0, score)


def normalize_phone(phone):
    phone = re.sub(r"[\s\-]", "", phone)
    if phone.startswith("+91"):
        phone = phone[3:]
    elif phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]
    if phone.startswith("0"):
        phone = phone[1:]
    return phone


DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d.%m.%y", "%d.%m.%Y", "%d-%b-%Y"]


def parse_date(text):
    for fmt in DATE_FORMATS:
        try:
            d = datetime.strptime(text, fmt).date()
        except ValueError:
            continue

        if d > date.today():
            d = d.replace(year=d.year - 100)
        return d
    return None


def compare(method, x, y):
    if method == "phonetic":
        return name_score(x, y)
    if method == "edit_distance":
        return email_score(x, y)
    if method == "normalized_phone":
        return 1.0 if normalize_phone(x) == normalize_phone(y) else 0.0
    if method == "date":
        dx, dy = parse_date(x), parse_date(y)
        if dx is None or dy is None:
            return None
        return 1.0 if dx == dy else 0.0
    if method == "exact":
        return 1.0 if x.lower() == y.lower() else 0.0
    raise ValueError("unknown method: " + method)


def score_pair(a: dict[str, object], b: dict[str, object], plan: list[FieldComparison]) -> MatchResult:

    field_scores = {}
    methods = []
    total = 0.0
    weights = 0.0

    for item in plan:
        x = clean(a.get(item.attribute))
        y = clean(b.get(item.attribute))
        if x is None or y is None:
            continue

        score = compare(item.method, x, y)
        if score is None:
            continue
        score = min(1.0, max(0.0, score))

        field_scores[item.attribute] = score
        if item.method not in methods:
            methods.append(item.method)
        total += item.weight * score
        weights += item.weight

    confidence = total / weights if weights else 0.0
    return MatchResult(confidence, "+".join(methods), field_scores)
