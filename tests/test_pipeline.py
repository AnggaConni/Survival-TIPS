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
    bad={"tips":[{"title":"Treat water","content_type":"treat","category":"water","summary":"Boil water.","steps":["Boil water."],"warnings":[],"evidence_excerpt":"Boiling water removes every contaminant.","confidence":"high"}]}
    good={"tips":[{"title":"Boil water before drinking","content_type":"treat","category":"water","summary":"Boil water before use.","steps":["Bring water to a boil for one minute."],"warnings":[],"evidence_excerpt":"Boil water for one minute before drinking.","confidence":"medium"}]}
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
        "stage_ids":["03-water-sanitation"],
        "quality_status":"source_aligned_needs_human_review"
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


def test_normalize_tip_marks_new_output_as_unreviewed_candidate():
    src={"url":"https://example.org/guide","title":"Guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00","text":"Use several channels to communicate an emergency notice."}
    raw={"title":"Use several channels","content_type":"communication_guidance","category":"communication","summary":"Consider more than one channel.","steps":["Consider more than one channel."],"warnings":[],"evidence_excerpt":"Use several channels to communicate an emergency notice.","confidence":"medium"}
    tip=normalize_tip(raw,src,"test")
    assert tip is not None
    assert tip["quality_status"] == "ai_candidate_needs_review"
    assert tip["verification"]["status"] == "needs_review"


def test_quarantine_ids_are_not_reintroduced_as_candidates(monkeypatch, tmp_path):
    import scripts.extract_tips as extractor
    from scripts.common import ROOT
    # This regression is covered by the process function's protected-ID/source set;
    # the queue must not be merged into active tips.json.
    assert "tips.quarantine.json" in extractor.process_saved_sources.__code__.co_consts
    assert "candidate_tips.json" in extractor.process_saved_sources.__code__.co_consts


def test_pdf_export_uses_only_approved_dataset(monkeypatch, tmp_path):
    import scripts.export_pdfs as exporter
    payload = {"tips": [
        {"id":"draft","title":"Draft","summary":"Not approved","steps":["Do not publish"],"stage_ids":["01-drr"],"verification":{"status":"needs_review"},"quality_status":"source_aligned_needs_human_review"},
        {"id":"approved","title":"Approved","summary":"Reviewed","steps":[{"instruction":"Do it","evidence_excerpt":"Supported text","source_url":"https://example.org"}],"stage_ids":["01-drr"],"verification":{"status":"approved","reviewed_by":"Reviewer","reviewed_at":"2026-10-30","review_notes":"Checked"},"quality_status":"human_verified"}
    ]}
    monkeypatch.setattr(exporter, "read_json", lambda path, default: payload if path.name == "approved_tips.json" else default)
    selected = [tip for tip in payload["tips"] if tip.get("verification", {}).get("status") == "approved" and tip.get("quality_status") == "human_verified"]
    assert [tip["id"] for tip in selected] == ["approved"]


def test_approved_tip_requires_step_level_verbatim_evidence(monkeypatch):
    import scripts.validate_data as validator
    payloads = {
        "sources": {"sources":[{"url":"https://example.org/guide","text":"Boil water for one minute."}]},
        "tips": {"tips":[]}, "species":{"species":[]},
        "candidate_tips":{"tips":[]}, "tips.quarantine":{"tips":[]},
        "approved_tips":{"tips":[{
            "id":"approved-1","title":"Boil water","summary":"Boil water.",
            "stage_ids":["01-drr"],"primary_stage_id":"01-drr","secondary_stage_ids":[],
            "stage_classification":{"suggested_stage_ids":["01-drr"],"approved_stage_ids":["01-drr"],"review_status":"human_reviewed","reviewed_by":"Reviewer"},
            "sources":[{"url":"https://example.org/guide"}],
            "steps":[{"instruction":"Boil water.","evidence_excerpt":"Boil water for one minute.","source_url":"https://example.org/guide"}],
            "verification":{"status":"approved","reviewed_by":"Reviewer","reviewed_at":"2026-10-30","review_notes":"Checked"},
            "quality_status":"human_verified"
        }]}
    }
    monkeypatch.setattr(validator, "read_json", lambda path, default: payloads.get(path.stem, default))
    monkeypatch.setattr(validator, "get_stages", lambda: [{"id":"01-drr"}])
    assert validator.validate()
    payloads["approved_tips"]["tips"][0]["steps"][0]["evidence_excerpt"] = "Invented evidence."
    assert not validator.validate()


def test_review_command_promotes_only_with_verbatim_evidence(monkeypatch, tmp_path):
    import json, sys
    import scripts.review_tips as reviewer
    monkeypatch.setattr(reviewer, "ROOT", tmp_path)
    (tmp_path / "data").mkdir()
    def save(name, payload):
        (tmp_path / "data" / name).write_text(json.dumps(payload), encoding="utf-8")
    save("sources.json", {"sources":[{"url":"https://example.org/guide","text":"Boil water for one minute."}]})
    save("tips.json", {"tips":[{"id":"tip-1","title":"Boil water","summary":"Boil water safely.","steps":["Bring water to a boil."],"sources":[{"url":"https://example.org/guide"}],"verification":{"status":"needs_review","confidence":"medium"},"quality_status":"source_aligned_needs_human_review"}]})
    save("candidate_tips.json", {"tips":[]})
    save("approved_tips.json", {"tips":[]})
    save("review_decisions.json", {"decisions":[{
        "tip_id":"tip-1","decision":"approve","reviewer":"Human reviewer","notes":"Checked against source.",
        "step_reviews":[{"evidence_excerpt":"Boil water for one minute.","source_url":"https://example.org/guide"}]
    }]})
    monkeypatch.setattr(sys, "argv", ["review_tips", "--apply"])
    reviewer.main()
    approved = json.loads((tmp_path / "data" / "approved_tips.json").read_text(encoding="utf-8"))["tips"]
    assert len(approved) == 1
    assert approved[0]["verification"]["status"] == "approved"
    assert approved[0]["steps"][0]["evidence_excerpt"] == "Boil water for one minute."


def test_review_command_rejects_non_verbatim_step_evidence(monkeypatch, tmp_path):
    import json, sys, pytest
    import scripts.review_tips as reviewer
    monkeypatch.setattr(reviewer, "ROOT", tmp_path)
    (tmp_path / "data").mkdir()
    def save(name, payload):
        (tmp_path / "data" / name).write_text(json.dumps(payload), encoding="utf-8")
    save("sources.json", {"sources":[{"url":"https://example.org/guide","text":"Boil water for one minute."}]})
    save("tips.json", {"tips":[{"id":"tip-2","title":"Boil water","summary":"Boil water.","steps":["Boil water."],"sources":[{"url":"https://example.org/guide"}],"verification":{"status":"needs_review"},"quality_status":"source_aligned_needs_human_review"}]})
    save("candidate_tips.json", {"tips":[]})
    save("approved_tips.json", {"tips":[]})
    save("review_decisions.json", {"decisions":[{
        "tip_id":"tip-2","decision":"approve","reviewer":"Human reviewer","notes":"Checked.",
        "step_reviews":[{"evidence_excerpt":"Boiling water removes all toxins.","source_url":"https://example.org/guide"}]
    }]})
    monkeypatch.setattr(sys, "argv", ["review_tips", "--apply"])
    with pytest.raises(SystemExit):
        reviewer.main()


def test_source_quality_assessment_is_explicitly_heuristic():
    from scripts.source_quality import assess_source, content_hash, annotate_source
    source = {
        "url":"https://www.cdc.gov/water/emergency.html",
        "title":"Emergency Drinking Water Technical Guide",
        "text":"Last Reviewed: June 30, 2025. " + ("Water treatment procedure and safety equipment. " * 80),
        "retrieved_at":"2026-10-30T00:00:00+00:00"
    }
    assessment = assess_source(source)
    assert assessment["authority_tier"] == "A_official_public_authority"
    assert assessment["document_type"] == "technical_guide"
    assert assessment["review_status"] == "needs_human_review"
    assert assessment["classification_method"] == "heuristic_v1"
    annotated = annotate_source(source)
    assert annotated["version"] == 1
    assert annotated["content_hash"] == content_hash(source["text"])


def test_duplicate_detector_flags_near_duplicate_titles():
    from scripts.source_quality import duplicate_pairs
    tips = [
        {"id":"a","title":"Boil drinking water safely","summary":"Boil water before drinking."},
        {"id":"b","title":"Boil drinking water safely!","summary":"Boil water before drinking."},
        {"id":"c","title":"Build a raised garden bed","summary":"Prepare a garden bed."}
    ]
    pairs = duplicate_pairs(tips)
    assert len(pairs) == 1
    assert {pairs[0]["left_id"], pairs[0]["right_id"]} == {"a","b"}


def test_conflict_detector_only_emits_human_review_signals():
    from scripts.source_quality import possible_conflict_pairs
    tips = [
        {"id":"a","title":"Water is safe to drink","summary":"The tested water is safe after treatment."},
        {"id":"b","title":"Water is unsafe to drink","summary":"The tested water is unsafe after treatment."}
    ]
    pairs = possible_conflict_pairs(tips)
    assert pairs
    assert pairs[0]["status"] == "human_review_required"
    assert "safe/unsafe" in pairs[0]["signals"]


def test_audit_checks_evidence_across_all_referenced_sources():
    from scripts.audit_tips import audit
    sources = [
        {"url":"https://example.org/first","text":"An unrelated overview."},
        {"url":"https://example.org/second","text":"Boil water for one minute."}
    ]
    tip = {
        "id":"multi-source","title":"Boil water","content_type":"treat","category":"water",
        "summary":"Boil water before drinking.","steps":["Boil water."],
        "evidence_excerpt":"Boil water for one minute.",
        "sources":[{"url":"https://example.org/first"},{"url":"https://example.org/second"}],
        "stage_ids":["03-water-sanitation"],
        "stage_classification":{"review_status":"needs_human_review"}
    }
    issues, _ = audit([tip], sources)
    assert "evidence_not_found_verbatim_in_any_referenced_source" not in issues["multi-source"]
