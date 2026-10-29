from __future__ import annotations
import json
import re
from functools import lru_cache
from .common import ROOT, read_json

@lru_cache(maxsize=1)
def get_stages():
    payload = read_json(ROOT / "config" / "stages.json", {"stages": []})
    return sorted(payload.get("stages", []), key=lambda item: item.get("order", 999))

def classify_tip(tip):
    """Return stage IDs using explicit assignment first, then transparent keyword/category rules."""
    valid = {stage["id"] for stage in get_stages()}
    explicit = tip.get("stage_ids")
    if isinstance(explicit, list):
        chosen = [stage_id for stage_id in explicit if stage_id in valid]
        if chosen:
            return chosen
    category = str(tip.get("category", "other")).lower()
    text = " ".join(str(tip.get(key, "")) for key in ("title", "summary", "evidence_excerpt"))
    text = re.sub(r"\s+", " ", text).casefold()
    scored = []
    for stage in get_stages():
        score = sum(1 for keyword in stage.get("keywords", []) if keyword.casefold() in text)
        if category in stage.get("categories", []):
            score += 1
        if score:
            scored.append((score, -stage.get("order", 999), stage["id"]))
    if not scored:
        return []
    best = max(score for score, _, _ in scored)
    # Keep all tied best matches, allowing cross-cutting guides to appear in multiple filters.
    return [stage_id for score, _, stage_id in scored if score == best]

def tips_for_stage(tips, stage_id):
    return [tip for tip in tips if stage_id in classify_tip(tip)]
