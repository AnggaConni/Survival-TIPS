from pathlib import Path


def test_collection_workflow_is_manual_and_ai_extraction_is_opt_in():
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "collect-data.yml").read_text()
    assert "run_ai_extraction" in workflow
    assert "default: false" in workflow
    assert "${{ inputs.run_ai_extraction }}" in workflow
    assert "python -m scripts.autonomous_approval" not in workflow
    assert "schedule:" not in workflow
    assert "data/autonomous_review_log.json" in workflow

def test_validator_keeps_ai_approval_distinct_from_human_approval():
    validator = (Path(__file__).resolve().parents[1] / "scripts" / "validate_data.py").read_text()
    assert '"human_verified", "ai_verified"' in validator
    assert 'verification.get("review_type") == "automated_low_risk_only"' in validator
