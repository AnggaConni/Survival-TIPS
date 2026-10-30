from __future__ import annotations
import hashlib
import re
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from urllib.parse import urlparse

OFFICIAL_DOMAINS = {
    "cdc.gov", "who.int", "fao.org", "unhcr.org", "ready.gov", "fema.gov",
    "usda.gov", "nifa.usda.gov", "weather.gov", "noaa.gov", "usgs.gov",
    "gov.uk", "ec.europa.eu", "nps.gov", "epa.gov",
}
TECHNICAL_ORGANIZATIONS = {
    "ifrc.org", "redcross.org", "practicalaction.org", "extension.oregonstate.edu",
    "reliefweb.int",
}
NEWS_TERMS = ("news", "press release", "announcement", "statement", "launches", "announces")
DOC_PATTERNS = (
    ("standard", ("standard", "minimum requirements", "specification")),
    ("technical_manual", ("technical manual", "field manual", "manual")),
    ("technical_guide", ("technical guide", "field guide", "how to", "guideline", "guide")),
    ("factsheet", ("fact sheet", "factsheet", "fact-sheet")),
    ("toolkit", ("toolkit", "tool box", "toolbox")),
    ("policy_or_framework", ("policy", "framework", "strategy", "action plan")),
    ("news_or_announcement", NEWS_TERMS),
)

def normalized_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()

def content_hash(text):
    return hashlib.sha256(normalized_text(text).encode("utf-8")).hexdigest()


def evidence_matches(evidence, source_text):
    """Match verbatim evidence, allowing explicit ellipses between quoted fragments."""
    def normalize(value):
        value = unicodedata.normalize("NFKC", str(value or ""))
        return re.sub(r"\s+", " ", value).strip().casefold()

    source = normalize(source_text)
    raw = unicodedata.normalize("NFKC", str(evidence or ""))
    fragments = [normalize(part) for part in re.split(r"\.{3,}|…+", raw)]
    fragments = [part for part in fragments if part]
    if not fragments:
        return False
    cursor = 0
    for fragment in fragments:
        if len(fragment) < 8:
            return False
        position = source.find(fragment, cursor)
        if position < 0:
            return False
        cursor = position + len(fragment)
    return True

def _domain_matches(host, domains):
    return any(host == d or host.endswith("." + d) for d in domains)

def extract_publication_date(source):
    body = str(source.get("text", ""))
    patterns = (
        r"(?:last reviewed|last updated|updated|published|publication date)\s*[:\-]?\s*((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})",
        r"(?:last reviewed|last updated|updated|published|publication date)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})",
        r"(?:last reviewed|last updated|updated|published|publication date)\s*[:\-]?\s*((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})",
    )
    for pattern in patterns:
        match = re.search(pattern, body, re.I)
        if match:
            raw = match.group(1)
            for fmt in ("%B %d, %Y", "%B %d %Y", "%Y-%m-%d", "%B %Y"):
                try:
                    return datetime.strptime(raw.replace(",", ""), fmt).date().isoformat()
                except ValueError:
                    pass
    return None

def assess_source(source):
    """Transparent heuristic triage. This is not a certification of factual quality."""
    url = str(source.get("url", ""))
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    title = normalized_text(source.get("title"))
    body = normalized_text(source.get("text"))
    if _domain_matches(host, OFFICIAL_DOMAINS):
        tier, authority_points = "A_official_public_authority", 40
    elif _domain_matches(host, TECHNICAL_ORGANIZATIONS):
        tier, authority_points = "B_technical_or_humanitarian_organization", 30
    elif host.endswith(".edu") or ".edu." in host:
        tier, authority_points = "B_academic_or_extension", 30
    else:
        tier, authority_points = "C_or_unassessed", 15
    document_type = "web_article"
    for label, terms in DOC_PATTERNS:
        if any(term in title for term in terms):
            document_type = label
            break
    if document_type == "news_or_announcement":
        authority_points = min(authority_points, 10)
    technical_terms = ("procedure", "temperature", "dosage", "standard", "specification",
                       "measurement", "step", "treatment", "maintenance", "construction",
                       "disinfection", "cultivation", "safety", "equipment")
    technical_hits = sum(body.count(term) for term in technical_terms)
    depth = 0 if len(body) < 500 else 1 if len(body) < 1800 else 2 if technical_hits < 5 else 3
    depth_points = depth * 10
    date = extract_publication_date(source)
    score = min(100, authority_points + depth_points + (10 if date else 0))
    rationale = [
        "domain tier is a heuristic based on the host name",
        "document type is inferred from title keywords",
        "technical depth is estimated from text length and technical vocabulary",
        "publication date is included only when explicitly found in page text",
    ]
    return {
        "authority_tier": tier,
        "document_type": document_type,
        "publication_date": date,
        "last_updated": date,
        "jurisdiction": "not_stated",
        "technical_depth": depth,
        "quality_score": score,
        "score_components": {"authority": authority_points, "technical_depth": depth_points, "date_present": 10 if date else 0},
        "classification_method": "heuristic_v1",
        "review_status": "needs_human_review",
        "rationale": rationale,
    }

def annotate_source(source):
    row = dict(source)
    row.setdefault("first_seen_at", row.get("retrieved_at"))
    row.setdefault("version", 1)
    row.setdefault("content_hash", content_hash(row.get("text", "")))
    row.setdefault("last_checked_at", row.get("retrieved_at"))
    row.setdefault("content_changed_at", row.get("retrieved_at"))
    if not isinstance(row.get("quality_assessment"), dict):
        row["quality_assessment"] = assess_source(row)
    return row

def _tokens(value):
    return {x for x in re.findall(r"[a-z0-9]{3,}", normalized_text(value)) if x not in {
        "the", "and", "for", "with", "from", "this", "that", "when", "then",
        "into", "your", "use", "using", "how", "are", "can", "should", "must",
    }}

def duplicate_pairs(tips):
    pairs = []
    for i, left in enumerate(tips):
        for right in tips[i + 1:]:
            a, b = normalized_text(left.get("title")), normalized_text(right.get("title"))
            if not a or not b:
                continue
            title_ratio = SequenceMatcher(None, a, b).ratio()
            ta, tb = _tokens(a), _tokens(b)
            jaccard = len(ta & tb) / max(1, len(ta | tb))
            summary_a, summary_b = _tokens(left.get("summary")), _tokens(right.get("summary"))
            summary_overlap = len(summary_a & summary_b) / max(1, len(summary_a | summary_b))
            if title_ratio >= 0.88 or (jaccard >= 0.78 and summary_overlap >= 0.55):
                pairs.append({"left_id": left.get("id"), "right_id": right.get("id"),
                              "similarity": round(max(title_ratio, jaccard), 3),
                              "signal": "near_duplicate_title_or_summary"})
    return pairs

OPPOSITE_PAIRS = (
    ("safe", "unsafe"), ("edible", "inedible"), ("potable", "nonpotable"),
    ("increase", "decrease"), ("increases", "decreases"),
    ("add", "remove"), ("wet", "dry"), ("boil", "do not boil"),
    ("recommended", "not recommended"),
)

def _contains_phrase(text, phrase):
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", text))

def possible_conflict_pairs(tips):
    """Lexical screening only: emit review signals, never resolve or label a true contradiction."""
    pairs = []
    for i, left in enumerate(tips):
        left_text = normalized_text(" ".join([str(left.get("title", "")), str(left.get("summary", ""))] + [str(x) for x in left.get("steps", [])]))
        left_tokens = _tokens(left_text)
        for right in tips[i + 1:]:
            right_text = normalized_text(" ".join([str(right.get("title", "")), str(right.get("summary", ""))] + [str(x) for x in right.get("steps", [])]))
            right_tokens = _tokens(right_text)
            shared = left_tokens & right_tokens
            if len(shared) < 3:
                continue
            opposite = []
            for a, b in OPPOSITE_PAIRS:
                if (_contains_phrase(left_text, a) and _contains_phrase(right_text, b)) or (_contains_phrase(left_text, b) and _contains_phrase(right_text, a)):
                    opposite.append(f"{a}/{b}")
            # Compare numeric values only when both records use the same explicit unit.
            # This avoids treating unrelated dimensions (e.g. floor area, height, and kW)
            # as contradictions merely because their numbers differ.
            def numeric_values(text):
                pattern = r"\b(\d+(?:\.\d+)?)\s*(°\s*[cf]|km²|km2|m²|m2|cm|mm|kw|w|minutes?|hours?|days?|lit(?:re|er)s?|mg|kg|g|%)"
                values = {}
                for value, unit in re.findall(pattern, text):
                    key = re.sub(r"\s+", "", unit).casefold()
                    values.setdefault(key, set()).add(float(value))
                return values

            nums_left, nums_right = numeric_values(left_text), numeric_values(right_text)
            shared_units = set(nums_left) & set(nums_right)
            numeric_signal = bool(
                len(shared) >= 5
                and any(nums_left[unit] != nums_right[unit] for unit in shared_units)
            )
            if opposite or numeric_signal:
                pairs.append({"left_id": left.get("id"), "right_id": right.get("id"),
                              "shared_topic_terms": sorted(shared)[:12],
                              "signals": opposite + (["different_numeric_values"] if numeric_signal else []),
                              "status": "human_review_required"})
    return pairs
