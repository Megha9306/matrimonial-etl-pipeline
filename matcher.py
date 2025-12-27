"""Explainable, configurable fuzzy matching utilities.

This module prefers `rapidfuzz` when available and falls back to `difflib`.
It returns scores in 0-100 range and includes details for explainability.
"""
from __future__ import annotations

from typing import Iterable, Optional, Tuple, Dict

try:
    from rapidfuzz import process, fuzz  # type: ignore
    _HAS_RAPIDFUZZ = True
except Exception:  # pragma: no cover - optional dependency
    _HAS_RAPIDFUZZ = False

import difflib


def _difflib_score(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio() * 100.0


def match_one(query: str, choices: Iterable[str], scorer: str = "auto", threshold: float = 80.0) -> Tuple[Optional[str], float, Dict]:
    """Match `query` to the best value in `choices`.

    Returns (match, score, details). Score is 0-100.
    If no match meets `threshold`, returns (None, best_score, details).

    scorer: 'auto' (prefer rapidfuzz), 'rapidfuzz', or 'difflib'.
    """
    q = (query or "").strip()
    if not q:
        return None, 0.0, {"reason": "empty query"}
    choices_list = list(choices)
    best_match = None
    best_score = 0.0
    details: Dict = {"method": None, "matcher": scorer}
    if scorer in ("auto", "rapidfuzz") and _HAS_RAPIDFUZZ:
        # rapidfuzz returns score in 0-100
        details["method"] = "rapidfuzz"
        res = process.extractOne(q, choices_list, scorer=fuzz.WRatio)
        if res:
            best_match, best_score = res[0], float(res[1])
    else:
        details["method"] = "difflib"
        for c in choices_list:
            s = _difflib_score(q.lower(), c.lower())
            if s > best_score:
                best_score = s
                best_match = c
    details["best_score"] = best_score
    details["threshold"] = threshold
    if best_score >= float(threshold):
        return best_match, best_score, details
    return None, best_score, details
