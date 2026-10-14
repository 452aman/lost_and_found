"""Dependency-free text similarity: TF-IDF-style cosine over word and char n-grams.

Kept pure Python so the matcher is deterministic and unit-testable; the
`Embedder` protocol in matching.py lets a neural model replace it later.
"""
import math
import re
from collections import Counter

_STOP = {
    "a", "an", "the", "and", "or", "of", "in", "on", "at", "my", "i", "it", "is", "was",
    "with", "to", "for", "near", "left", "lost", "found", "has", "have", "this", "that",
}
_WORD = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    words = [w for w in _WORD.findall(text.lower()) if w not in _STOP]
    grams: list[str] = []
    for w in words:
        padded = f"#{w}#"
        grams.extend(padded[i : i + 3] for i in range(len(padded) - 2))  # char trigrams tolerate typos
    return words + grams


def vectorize(text: str) -> Counter:
    return Counter(tokens(text))


def cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def text_similarity(a: str, b: str) -> float:
    return cosine(vectorize(a), vectorize(b))
