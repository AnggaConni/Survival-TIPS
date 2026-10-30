import json

import pytest

from scripts import approve_candidates, review_tips


def _save(root, name, payload):
    path = root / "data" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _read(root, name):
    return json.loads((root / "data" / name).read_text(encoding="utf-8"))


def _candidate(tip_id="candidate-1"):
    return {
        "id": tip_id,
        "title": "Boil water before drinking",
        "summary": "Treat water using the source-supported method.",
        "steps": ["Bring water to a boil for one minute."],
        "sources": [{"url": "https://example.org/guide"}],
        "stage_ids": ["03-water-sanitation"],
        "verification": {"status": "needs_review", "confidence": "medium"},
        "quality_status": "ai_candidate_needs_review",
    }


def _decision(tip_id="candidate-1"):
    return {
        "tip_id": tip_id,
        "decision": "approve",
        "reviewer": "Human reviewer",
        "notes": "Read the source in context and checked applicability.",
        "stage_ids": ["03-water-sanitation"],
        "stage_review_notes": "Confirmed water and sanitation classification.",
        "step_reviews": [{
            "evidence_excerpt": "Boil water for one minute before drinking.",
            "source_url": "https://example.org/guide",
        }],
    }


def test_candidate_approval_moves_tip_and_removes_it_from_queue(monkeypatch, tmp_path):
    monkeypatch.setattr(review_tips, "ROOT", tmp_path)
    _save(tmp_path, "sources.json", {"sources": [{
        "url": "https://example.org/guide",
        "text": "Boil water for one minute before drinking.",
    }]})
    _save(tmp_path, "candidate_tips.json", {"schema_version": "1.0", "tips": [_candidate()]})
    _save(tmp_path, "approved_tips.json", {"schema_version": "1.0", "tips": []})
    decisions = tmp_path / "submitted.json"
    decisions.write_text(json.dumps({"decisions": [_decision()]}), encoding="utf-8")

    review_tips.apply_decisions(decisions, candidates_only=True)

    assert _read(tmp_path, "candidate_tips.json")["tips"] == []
    approved = _read(tmp_path, "approved_tips.json")["tips"]
    assert len(approved) == 1
    assert approved[0]["id"] == "candidate-1"
    assert approved[0]["verification"]["status"] == "approved"
    assert approved[0]["steps"][0]["evidence_excerpt"] == "Boil water for one minute before drinking."


def test_candidate_only_approval_refuses_legacy_backlog(monkeypatch, tmp_path):
    monkeypatch.setattr(review_tips, "ROOT", tmp_path)
    _save(tmp_path, "sources.json", {"sources": [{
        "url": "https://example.org/guide",
        "text": "Boil water for one minute before drinking.",
    }]})
    _save(tmp_path, "tips.json", {"tips": [_candidate("legacy-tip")]})
    _save(tmp_path, "candidate_tips.json", {"tips": []})
    _save(tmp_path, "approved_tips.json", {"tips": []})
    decisions = tmp_path / "submitted.json"
    decisions.write_text(json.dumps({"decisions": [_decision("legacy-tip")]}), encoding="utf-8")

    with pytest.raises(SystemExit, match="candidate_tips.json"):
        review_tips.apply_decisions(decisions, candidates_only=True)


def test_candidate_is_not_removed_when_evidence_validation_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(review_tips, "ROOT", tmp_path)
    _save(tmp_path, "sources.json", {"sources": [{
        "url": "https://example.org/guide",
        "text": "Boil water for one minute before drinking.",
    }]})
    _save(tmp_path, "candidate_tips.json", {"tips": [_candidate()]})
    _save(tmp_path, "approved_tips.json", {"tips": []})
    bad = _decision()
    bad["step_reviews"][0]["evidence_excerpt"] = "Unsupported claim."
    decisions = tmp_path / "submitted.json"
    decisions.write_text(json.dumps({"decisions": [bad]}), encoding="utf-8")

    with pytest.raises(SystemExit, match="verbatim excerpt"):
        review_tips.apply_decisions(decisions, candidates_only=True)

    assert len(_read(tmp_path, "candidate_tips.json")["tips"]) == 1
    assert _read(tmp_path, "approved_tips.json")["tips"] == []


def test_candidate_template_only_accepts_existing_candidate_ids(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(approve_candidates, "ROOT", tmp_path)
    _save(tmp_path, "candidate_tips.json", {"tips": [_candidate()]})

    approve_candidates.write_template(["candidate-1"])
    output = json.loads(capsys.readouterr().out)
    assert output["decisions"][0]["tip_id"] == "candidate-1"
    assert len(output["decisions"][0]["step_reviews"]) == 1
    assert output["decisions"][0]["step_reviews"][0]["evidence_excerpt"] == "REPLACE_WITH_EXACT_SOURCE_QUOTE"

    with pytest.raises(SystemExit, match="Candidate not found"):
        approve_candidates.write_template(["not-a-candidate"])
