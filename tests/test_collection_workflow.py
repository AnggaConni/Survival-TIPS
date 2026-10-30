from pathlib import Path

def test_collection_workflow_commits_every_generated_dataset():
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "collect-data.yml").read_text()
    staging_line = next(line for line in workflow.splitlines() if line.strip().startswith("git add "))
    for path in (
        "data/sources.json",
        "data/source_versions.json",
        "data/tips.json",
        "data/candidate_tips.json",
        "data/approved_tips.json",
        "data/tips.quarantine.json",
        "data/species.json",
        "data/quality_report*.json",
    ):
        assert path in staging_line, f"Generated dataset is not committed: {path}"


def test_repair_gate_uses_the_auditors_exact_evidence_issue_names():
    source = (Path(__file__).resolve().parents[1] / "scripts" / "audit_tips.py").read_text()
    assert '"evidence_not_found_verbatim_in_any_referenced_source"' in source
    assert '"source_text_unavailable_for_audit"' in source
