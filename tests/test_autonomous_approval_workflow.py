from pathlib import Path


def test_collection_workflow_runs_deepseek_review_before_approved_audit():
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "collect-data.yml").read_text()
    review = workflow.index("python -m scripts.autonomous_approval")
    approved_audit = workflow.index("python -m scripts.audit_tips --dataset approved")
    assert review < approved_audit
    assert "DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}" in workflow
    assert "data/autonomous_review_log.json" in workflow


def test_validator_keeps_ai_approval_distinct_from_human_approval():
    validator = (Path(__file__).resolve().parents[1] / "scripts" / "validate_data.py").read_text()
    assert '"human_verified", "ai_verified"' in validator
    assert 'verification.get("review_type") == "automated_low_risk_only"' in validator
