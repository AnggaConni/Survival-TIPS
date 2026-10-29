from scripts.collect_gbif import license_allowed
from scripts.extract_tips import normalize_tip

def test_license_allowlist():
    assert license_allowed("https://creativecommons.org/licenses/by/4.0/")
    assert license_allowed("https://creativecommons.org/licenses/by-sa/4.0/")
    assert license_allowed("https://creativecommons.org/publicdomain/zero/1.0/")
    assert not license_allowed("https://creativecommons.org/licenses/by-nc/4.0/")
    assert not license_allowed("https://creativecommons.org/licenses/by-nd/4.0/")
    assert not license_allowed("")
    assert not license_allowed("All rights reserved")

def test_tip_requires_source():
    src={"url":"https://example.org/guide","title":"Guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00","text":"Follow current public health guidance."}
    tip=normalize_tip({"title":"Keep water safe","content_type":"treat","category":"water","summary":"Follow current public health guidance." ,"steps":["Check official guidance"],"warnings":[],"evidence_excerpt":"Follow current public health guidance.","confidence":"medium"},src,"test")
    assert tip and tip["verification"]["status"]=="needs_review"
    assert tip["sources"][0]["url"]==src["url"]
    assert "03-water-sanitation" in tip["stage_ids"]
    assert normalize_tip({"title":"No source"},{}, "test") is None


def test_prompt_rejects_heading_only_and_requires_verbatim_evidence():
    from scripts.extract_tips import PROMPT
    assert "navigation headings" in PROMPT
    assert "verbatim excerpt" in PROMPT
    assert "return no tip" in PROMPT
    assert "Never invent thresholds" in PROMPT

def test_normalize_tip_keeps_unreviewed_status_and_rejects_empty_steps_shape():
    src={"url":"https://example.org/water","title":"Water guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00","text":"Boil water before drinking."}
    tip=normalize_tip({
        "title":"Treat drinking water","content_type":"treat","category":"water",
        "summary":"Use the source-supported water treatment method.",
        "steps":["Follow the stated procedure."],"warnings":[],
        "evidence_excerpt":"Boil water before drinking.","confidence":"high"
    },src,"test")
    assert tip["verification"]["status"] == "needs_review"
    assert tip["verification"]["confidence"] == "high"
    assert tip["evidence_excerpt"] == "Boil water before drinking."


def test_normalize_tip_rejects_non_verbatim_evidence():
    src={"url":"https://example.org/guide","title":"Guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00","text":"Boil water for one minute before drinking."}
    raw={"title":"Treat water","content_type":"treat","category":"water","summary":"Treat drinking water.","steps":["Boil the water."],"warnings":[],"evidence_excerpt":"Boiling water kills all chemicals.","confidence":"high"}
    assert normalize_tip(raw,src,"test") is None

def test_normalize_tip_rejects_heading_only_without_steps():
    src={"url":"https://example.org/guide","title":"Guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00","text":"Emergency water storage"}
    raw={"title":"Emergency water storage","content_type":"other","category":"water","summary":"Store water for emergencies.","steps":[],"warnings":[],"evidence_excerpt":"Emergency water storage","confidence":"high"}
    assert normalize_tip(raw,src,"test") is None

def test_normalize_tip_accepts_verbatim_evidence_and_steps():
    src={"url":"https://example.org/guide","title":"Guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00","text":"Boil water for one minute before drinking."}
    raw={"title":"Boil water before drinking","content_type":"treat","category":"water","summary":"Boil water before use.","steps":["Bring water to a boil for one minute."],"warnings":[],"evidence_excerpt":"Boil water for one minute before drinking.","confidence":"medium"}
    tip=normalize_tip(raw,src,"test")
    assert tip is not None
    assert tip["evidence_excerpt"] in src["text"]


def test_extract_falls_back_when_first_provider_fails_validation(monkeypatch):
    import scripts.extract_tips as extractor
    source={"url":"https://example.org/guide","title":"Guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00","text":"Boil water for one minute before drinking."}
    bad={"tips":[{"title":"Treat water","category":"water","summary":"Boil water.","steps":["Boil water."],"warnings":[],"evidence_excerpt":"Boiling water removes every contaminant.","confidence":"high"}]}
    good={"tips":[{"title":"Boil water before drinking","category":"water","summary":"Boil water before use.","steps":["Bring water to a boil for one minute."],"warnings":[],"evidence_excerpt":"Boil water for one minute before drinking.","confidence":"medium"}]}
    monkeypatch.setattr(extractor, "call_groq", lambda source: bad)
    monkeypatch.setattr(extractor, "call_deepseek", lambda source: good)
    monkeypatch.setattr(extractor, "call_openrouter", lambda source: {"tips":[]})
    tips, provider = extractor.extract(source)
    assert provider == "deepseek"
    assert len(tips) == 1
    assert tips[0]["evidence_excerpt"] in source["text"]


def test_audit_flags_missing_verbatim_evidence():
    from scripts.audit_tips import audit
    source={"url":"https://example.org/water","text":"Boil water before drinking."}
    tip={
        "id":"tip-1","title":"Boil drinking water","content_type":"treat","category":"water",
        "summary":"Boil water before drinking.","steps":["Boil water."],
        "evidence_excerpt":"Boiling removes every contaminant.",
        "sources":[{"url":"https://example.org/water"}],
        "stage_ids":["03-water-sanitation"]
    }
    issues, _ = audit([tip], [source])
    assert "evidence_not_found_verbatim_in_source" in issues["tip-1"]

def test_audit_accepts_tip_with_verbatim_evidence_and_stage():
    from scripts.audit_tips import audit
    source={"url":"https://example.org/water","text":"Boil water before drinking."}
    tip={
        "id":"tip-2","title":"Boil drinking water","content_type":"treat","category":"water",
        "summary":"Boil water before drinking.","steps":["Boil water."],
        "evidence_excerpt":"Boil water before drinking.",
        "sources":[{"url":"https://example.org/water"}],
        "stage_ids":["03-water-sanitation"]
    }
    issues, _ = audit([tip], [source])
    assert "tip-2" not in issues


def test_normalize_tip_rejects_wild_food_without_safety_details():
    src={"url":"https://example.org/plant","title":"Plant guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00","text":"The leaves of Example plant are eaten after thorough cooking."}
    raw={
        "title":"Eat Example plant leaves","content_type":"eat","category":"food",
        "summary":"The source mentions cooked leaves.","steps":["Cook the leaves."],
        "warnings":[],"evidence_excerpt":"The leaves of Example plant are eaten after thorough cooking.",
        "confidence":"high"
    }
    assert normalize_tip(raw,src,"test") is None


def test_normalize_tip_accepts_eat_only_with_required_source_fields():
    src={"url":"https://example.org/plant","title":"Plant guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00","text":"The leaves of Example plant are eaten after thorough cooking."}
    raw={
        "title":"Eat Example plant leaves","content_type":"eat","category":"food",
        "summary":"The source mentions cooked leaves.","steps":["Cook the leaves."],
        "materials":["Example plant leaves"],"tools":[],"prerequisites":[],
        "expected_result":"Cooked leaves","failure_modes":[],"safety_notes":[],
        "identification_criteria":["Use only the plant identified in the source."],
        "edible_parts":["Leaves"],"preparation_requirements":["Thorough cooking"],
        "lookalikes_or_uncertainty":["The source does not describe look-alikes; identification needs expert confirmation."],
        "warnings":[],"evidence_excerpt":"The leaves of Example plant are eaten after thorough cooking.",
        "confidence":"medium"
    }
    tip=normalize_tip(raw,src,"test")
    assert tip is not None
    assert tip["content_type"] == "eat"
    assert tip["edible_parts"] == ["Leaves"]


def test_audit_flags_build_tip_missing_recipe_details():
    from scripts.audit_tips import audit
    source={"url":"https://example.org/build","text":"Build a brick stove for cooking."}
    tip={
        "id":"tip-build","title":"Build a brick stove","content_type":"build","category":"other",
        "summary":"Build a brick stove.","steps":["Arrange bricks."],
        "evidence_excerpt":"Build a brick stove for cooking.",
        "sources":[{"url":"https://example.org/build"}],"stage_ids":["07-manufacturing"],
        "materials":[],"tools":[],"expected_result":""
    }
    issues,_=audit([tip],[source])
    assert "build_recipe_missing_materials" in issues["tip-build"]
    assert "build_recipe_missing_tools" in issues["tip-build"]
    assert "build_recipe_missing_expected_result" in issues["tip-build"]


def test_normalize_tip_rejects_missing_content_type():
    src={"url":"https://example.org/guide","title":"Guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00","text":"Boil water before drinking."}
    raw={"title":"Boil drinking water","category":"water","summary":"Boil water.","steps":["Boil water."],"warnings":[],"evidence_excerpt":"Boil water before drinking.","confidence":"high"}
    assert normalize_tip(raw,src,"test") is None


def test_normalize_tip_rejects_generic_slogan():
    src={"url":"https://example.org/guide","title":"Guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00","text":"Be prepared for emergencies."}
    raw={"title":"Be prepared","content_type":"prepare","category":"planning","summary":"Be prepared for emergencies.","steps":["Be prepared."],"warnings":[],"evidence_excerpt":"Be prepared for emergencies.","confidence":"high"}
    assert normalize_tip(raw,src,"test") is None


def test_normalize_tip_rejects_incomplete_build_recipe():
    src={"url":"https://example.org/build","title":"Build guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00","text":"Build a simple stove from local materials."}
    raw={"title":"Build a simple stove","content_type":"build","category":"other","summary":"Build a stove.","steps":["Arrange the materials."],"materials":["Local materials"],"tools":[],"expected_result":"A stove","warnings":[],"evidence_excerpt":"Build a simple stove from local materials.","confidence":"medium"}
    assert normalize_tip(raw,src,"test") is None
