import json

import pytest

from scripts import review_knowledge


def _save(root, name, payload):
    path = root / "data" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _recipe():
    excerpt = "Source states the complete procedure."
    return {
        "id": "recipe-review-1",
        "title": "A reviewed demonstration procedure",
        "summary": "A test record.",
        "stage_ids": ["06-materials"],
        "materials": ["Material A"],
        "tools": ["Tool A"],
        "steps": ["Perform the source-stated procedure."],
        "expected_result": "The stated result.",
        "sources": [{"url": "https://example.org/source"}],
        "evidence": [
            {"field": field, "source_url": "https://example.org/source", "excerpt": excerpt}
            for field in ("materials", "tools", "steps", "expected_result")
        ],
        "verification": {"status": "needs_review"},
    }


def _setup(root, record=None):
    _save(root, "sources.json", {"sources": [{
        "url": "https://example.org/source",
        "text": "Source states the complete procedure.",
    }]})
    _save(root, "recipes.json", {"recipes": [record or _recipe()]})
    _save(root, "materials.json", {"materials": []})
    _save(root, "biodiversity_profiles.json", {"profiles": []})
    _save(root, "agriculture_profiles.json", {"profiles": []})


def test_knowledge_review_approves_record_with_source_evidence(monkeypatch, tmp_path):
    monkeypatch.setattr(review_knowledge, "ROOT", tmp_path)
    _setup(tmp_path)
    decisions = tmp_path / "decisions.json"
    decisions.write_text(json.dumps({"decisions": [{
        "catalogue": "recipes.json",
        "record_id": "recipe-review-1",
        "decision": "approve",
        "reviewer": "Reviewer",
        "review_notes": "Checked the source and technical limits.",
    }]}), encoding="utf-8")

    assert review_knowledge.apply_decisions(decisions) == 1
    approved = json.loads((tmp_path / "data" / "recipes.json").read_text())["recipes"][0]
    assert approved["verification"]["status"] == "approved"
    assert approved["verification"]["reviewed_by"] == "Reviewer"


def test_knowledge_review_refuses_non_verbatim_evidence(monkeypatch, tmp_path):
    monkeypatch.setattr(review_knowledge, "ROOT", tmp_path)
    row = _recipe()
    row["evidence"][0]["excerpt"] = "Unsupported claim."
    _setup(tmp_path, row)
    decisions = tmp_path / "decisions.json"
    decisions.write_text(json.dumps({"decisions": [{
        "catalogue": "recipes.json",
        "record_id": "recipe-review-1",
        "decision": "approve",
        "reviewer": "Reviewer",
        "review_notes": "Checked.",
    }]}), encoding="utf-8")

    with pytest.raises(SystemExit, match="verbatim"):
        review_knowledge.apply_decisions(decisions)
    pending = json.loads((tmp_path / "data" / "recipes.json").read_text())["recipes"][0]
    assert pending["verification"]["status"] == "needs_review"


def test_knowledge_review_template_requires_catalogue_and_record_id(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(review_knowledge, "ROOT", tmp_path)
    _setup(tmp_path)
    review_knowledge.write_template(["recipes.json:recipe-review-1"])
    result = json.loads(capsys.readouterr().out)
    assert result["decisions"][0]["catalogue"] == "recipes.json"
    assert result["decisions"][0]["record_id"] == "recipe-review-1"
    with pytest.raises(SystemExit, match="Record not found"):
        review_knowledge.write_template(["recipes.json:not-found"])
