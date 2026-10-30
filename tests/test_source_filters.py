import json

from scripts.collect_sources import filter_candidates
from scripts import extract_tips


def test_source_discovery_rejects_untrusted_and_off_topic_pages():
    rows = [
        {"url": "https://www.ready.gov/water", "title": "Water | Ready.gov"},
        {"url": "https://dictionary.cambridge.org/dictionary/english/technical", "title": "Technical meaning"},
        {"url": "https://doyouremember.com/158561/emergency-cast-then-now", "title": "The Emergency Cast: Then and Now"},
        {"url": "https://www.who.int/news/item/example", "title": "WHO announces a new partnership"},
    ]
    accepted = filter_candidates(rows)
    assert [row["url"] for row in accepted] == ["https://www.ready.gov/water"]


def test_source_discovery_keeps_relevant_official_technical_guidance():
    rows = [
        {"url": "https://emergency.unhcr.org/shelter", "title": "Emergency Shelter Solutions and Standards"},
        {"url": "https://www.fao.org/guide", "title": "Improving nutrition through home gardening"},
        {"url": "https://www.who.int/news/item/statement", "title": "WHO statement on global priorities"},
    ]
    accepted = filter_candidates(rows)
    assert len(accepted) == 2
    assert all("who.int/news/item/statement" not in row["url"] for row in accepted)


def test_extraction_relevance_uses_trusted_domain_and_title(monkeypatch, tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "sources.json").write_text(json.dumps({
        "trusted_domains": ["ready.gov", "who.int"]
    }), encoding="utf-8")
    monkeypatch.setattr(extract_tips, "ROOT", tmp_path)

    assert extract_tips.source_is_relevant({
        "url": "https://www.ready.gov/water",
        "title": "Water | Ready.gov",
    })
    assert not extract_tips.source_is_relevant({
        "url": "https://example.com/water",
        "title": "Water guide",
    })
    assert not extract_tips.source_is_relevant({
        "url": "https://www.who.int/news/item/partnership",
        "title": "WHO announces a new partnership",
    })
