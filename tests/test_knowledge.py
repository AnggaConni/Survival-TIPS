import json

from scripts.knowledge_validation import validate_catalogues


def _write(root, name, payload):
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "data" / name).write_text(json.dumps(payload), encoding="utf-8")


def _source():
    return {"sources": [{
        "url": "https://example.org/guide",
        "text": "Use dry, clean sand for this demonstration material.",
    }]}


def _recipe():
    return {
        "id": "recipe-1",
        "title": "Prepare a demonstration mix",
        "summary": "A source-documented demonstration recipe.",
        "stage_ids": ["06-materials"],
        "materials": ["Dry, clean sand"],
        "tools": ["Mixing container"],
        "prerequisites": [],
        "steps": ["Use dry, clean sand for this demonstration material."],
        "measurements": [],
        "expected_result": "A prepared demonstration mix",
        "failure_modes": [],
        "safety_notes": [],
        "sources": [{"url": "https://example.org/guide"}],
        "evidence": [{
            "field": "materials",
            "source_url": "https://example.org/guide",
            "excerpt": "Use dry, clean sand for this demonstration material.",
        }],
        "verification": {"status": "needs_review"},
    }


def _catalogues(root, recipe_rows=None):
    _write(root, "sources.json", _source())
    _write(root, "recipes.json", {"recipes": recipe_rows or []})
    _write(root, "materials.json", {"materials": []})
    _write(root, "biodiversity_profiles.json", {"profiles": []})
    _write(root, "agriculture_profiles.json", {"profiles": []})


def test_empty_phase3_catalogues_are_valid(tmp_path):
    _catalogues(tmp_path)
    errors, counts = validate_catalogues(tmp_path)
    assert errors == []
    assert counts["recipes.json"] == 0


def test_recipe_requires_verbatim_field_level_evidence(tmp_path):
    row = _recipe()
    _catalogues(tmp_path, [row])
    errors, _ = validate_catalogues(tmp_path)
    assert errors == []

    row["evidence"][0]["excerpt"] = "This is not in the source."
    _catalogues(tmp_path, [row])
    errors, _ = validate_catalogues(tmp_path)
    assert any("not verbatim" in error for error in errors)


def test_recipe_rejects_unknown_stage_and_missing_required_materials(tmp_path):
    row = _recipe()
    row["stage_ids"] = ["99-fiction"]
    row["materials"] = []
    _catalogues(tmp_path, [row])
    errors, _ = validate_catalogues(tmp_path)
    assert any("invalid stage_ids" in error for error in errors)
    assert any("missing required field: materials" in error for error in errors)


def test_approved_knowledge_requires_reviewer_metadata(tmp_path):
    row = _recipe()
    row["verification"] = {"status": "approved"}
    _catalogues(tmp_path, [row])
    errors, _ = validate_catalogues(tmp_path)
    assert any("missing verification.reviewed_by" in error for error in errors)


def test_biodiversity_catalogue_rejects_blanket_edibility_certification(tmp_path):
    _write(tmp_path, "sources.json", _source())
    _write(tmp_path, "recipes.json", {"recipes": []})
    _write(tmp_path, "materials.json", {"materials": []})
    _write(tmp_path, "agriculture_profiles.json", {"profiles": []})
    profile = {
        "id": "species-1",
        "title": "Example species",
        "summary": "Research profile only.",
        "stage_ids": ["02-biodiversity"],
        "scientific_name": "Example species",
        "identification": ["Source-supported identifying trait"],
        "habitat_ecology": ["Source-supported habitat"],
        "distribution": ["Source-stated distribution"],
        "sources": [{"url": "https://example.org/guide"}],
        "evidence": [
            {"field": "scientific_name", "source_url": "https://example.org/guide", "excerpt": "Use dry, clean sand for this demonstration material."},
            {"field": "identification", "source_url": "https://example.org/guide", "excerpt": "Use dry, clean sand for this demonstration material."},
            {"field": "habitat_ecology", "source_url": "https://example.org/guide", "excerpt": "Use dry, clean sand for this demonstration material."},
            {"field": "distribution", "source_url": "https://example.org/guide", "excerpt": "Use dry, clean sand for this demonstration material."},
        ],
        "verification": {"status": "needs_review"},
        "food_use_status": "not_assessed",
        "safe_to_eat": True,
    }
    _write(tmp_path, "biodiversity_profiles.json", {"profiles": [profile]})
    errors, _ = validate_catalogues(tmp_path)
    assert any("blanket food/medicine safety assertion" in error for error in errors)
