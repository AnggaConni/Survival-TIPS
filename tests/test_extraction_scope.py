from scripts import extract_tips


def test_public_notice_is_not_a_technical_extraction_source(monkeypatch, tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "sources.json").write_text(
        '{"trusted_domains":["cdc.gov"]}', encoding="utf-8"
    )
    monkeypatch.setattr(extract_tips, "ROOT", tmp_path)

    assert not extract_tips.source_is_relevant({
        "url": "https://www.cdc.gov/example",
        "title": "Include All 10 Required Elements in a Public Notice",
    })


def test_household_water_treatment_source_is_relevant(monkeypatch, tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "sources.json").write_text(
        '{"trusted_domains":["cdc.gov"]}', encoding="utf-8"
    )
    monkeypatch.setattr(extract_tips, "ROOT", tmp_path)

    assert extract_tips.source_is_relevant({
        "url": "https://www.cdc.gov/example",
        "title": "Household Water Treatment",
    })


def test_communication_guidance_cannot_enter_practical_tip_dataset():
    source = {
        "url": "https://www.cdc.gov/example",
        "title": "Public Notice Guidance",
        "domain": "cdc.gov",
        "text": "A public notice must include this required information.",
    }
    raw = {
        "title": "Include Required Elements in a Public Notice",
        "content_type": "communication_guidance",
        "category": "water",
        "summary": "Prepare a public notice about drinking water.",
        "steps": ["Include the required information in the notice."],
        "evidence_excerpt": "A public notice must include this required information.",
        "confidence": "high",
    }

    assert extract_tips.normalize_tip(raw, source, "test") is None


def test_practical_water_treatment_type_remains_allowed():
    assert "treat" in extract_tips.PRACTICAL_CONTENT_TYPES
    assert "build" in extract_tips.PRACTICAL_CONTENT_TYPES
    assert "make" in extract_tips.PRACTICAL_CONTENT_TYPES
    assert "communication_guidance" not in extract_tips.PRACTICAL_CONTENT_TYPES
    assert "planning_guidance" not in extract_tips.PRACTICAL_CONTENT_TYPES
