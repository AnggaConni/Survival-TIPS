from scripts.collect_gbif import license_allowed
from scripts.extract_tips import normalize_tip
from scripts.collect_sources import collect_candidates


def test_image_license_allowlist():
    assert license_allowed("https://creativecommons.org/licenses/by/4.0/")
    assert license_allowed("https://creativecommons.org/licenses/by-sa/4.0/")
    assert license_allowed("https://creativecommons.org/publicdomain/zero/1.0/")
    assert not license_allowed("https://creativecommons.org/licenses/by-nc/4.0/")
    assert not license_allowed("https://creativecommons.org/licenses/by-nd/4.0/")
    assert not license_allowed("")
    assert not license_allowed("All rights reserved")


def test_tip_normalization_requires_source():
    source = {
        "url": "https://example.org/preparedness",
        "title": "Preparedness",
        "domain": "example.org",
        "retrieved_at": "2026-10-29T00:00:00+00:00",
    }
    tip = normalize_tip({
        "title": "Keep water safe",
        "category": "water",
        "summary": "Follow public health guidance for emergency water treatment.",
        "steps": ["Consult current official guidance"],
        "warnings": ["Water treatment does not remove every contaminant."],
        "confidence": "medium",
    }, source, "test")
    assert tip is not None
    assert tip["verification"]["status"] == "needs_review"
    assert tip["sources"][0]["url"] == source["url"]
    assert normalize_tip({"title": "No source"}, {}, "test") is None
