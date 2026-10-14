from datetime import datetime, timedelta, timezone

from app.services.matching import time_score
from app.services.similarity import text_similarity


def test_similar_descriptions_score_high():
    assert text_similarity("black Dell laptop with stickers", "Dell laptop black, has stickers") > 0.6


def test_unrelated_descriptions_score_low():
    assert text_similarity("red umbrella", "calculus textbook") < 0.15


def test_typos_still_match():
    assert text_similarity("wallet", "walet") > 0.3


def test_time_score_decays_and_rejects_impossible_order():
    t = datetime(2026, 1, 10, tzinfo=timezone.utc)
    assert time_score(t, t + timedelta(hours=2)) > 0.95
    assert 0.4 < time_score(t, t + timedelta(days=7)) < 0.6
    assert time_score(t, t + timedelta(days=20)) == 0.0
    assert time_score(t, t - timedelta(days=3)) == 0.0
