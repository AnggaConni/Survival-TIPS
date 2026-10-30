import json

from scripts.autonomous_approval import run_autonomous_approval


def save(root, name, payload):
    path = root / "data" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def read(root, name):
    return json.loads((root / "data" / name).read_text(encoding="utf-8"))


def source():
    return {
        "url": "https://www.ready.gov/example",
        "title": "Official community communication guide",
        "text": "Use a designated communication channel to share verified community updates.",
        "quality_assessment": {
            "authority_tier": "A_official_public_authority",
            "quality_score": 80,
        },
    }


def safe_candidate(tip_id="candidate-plan"):
    return {
        "id": tip_id,
        "title": "Share verified community updates through a designated channel",
        "summary": "A planning and communication practice supported by the cited guide.",
        "content_type": "communication_guidance",
        "category": "communication",
        "steps": ["Use a designated communication channel to share verified community updates."],
        "sources": [{"url": "https://www.ready.gov/example"}],
        "stage_ids": ["08-infrastructure"],
        "stage_classification": {"suggested_stage_ids": ["08-infrastructure"]},
        "verification": {"status": "needs_review", "confidence": "high"},
        "quality_status": "ai_candidate_needs_review",
    }


def test_low_risk_candidate_is_auto_approved_with_exact_step_evidence(tmp_path):
    save(tmp_path, "sources.json", {"sources": [source()]})
    save(tmp_path, "candidate_tips.json", {"schema_version": "1.0", "tips": [safe_candidate()]})
    save(tmp_path, "approved_tips.json", {"schema_version": "1.0", "tips": []})

    def reviewer(tip, sources, model):
        return {
            "decision": "approve",
            "risk_level": "low",
            "confidence": 0.97,
            "stage_ids": ["08-infrastructure"],
            "reason": "Every step is directly supported by the stored official source.",
            "step_reviews": [{
                "step_index": 1,
                "evidence_excerpt": "Use a designated communication channel to share verified community updates.",
                "source_url": "https://www.ready.gov/example",
            }],
        }

    result = run_autonomous_approval(tmp_path, reviewer=reviewer)
    assert result["auto_approved"] == 1
    assert read(tmp_path, "candidate_tips.json")["tips"] == []
    approved = read(tmp_path, "approved_tips.json")["tips"][0]
    assert approved["quality_status"] == "ai_verified"
    assert approved["verification"]["review_type"] == "automated_low_risk_only"
    assert approved["steps"][0]["evidence_excerpt"] == source()["text"]
    assert read(tmp_path, "autonomous_review_log.json")["reviews"][0]["decision"] == "auto_approved"


def test_high_risk_candidate_stays_in_manual_queue_without_calling_model(tmp_path):
    risky = safe_candidate("candidate-water")
    risky["content_type"] = "treat"
    risky["category"] = "water"
    save(tmp_path, "sources.json", {"sources": [source()]})
    save(tmp_path, "candidate_tips.json", {"tips": [risky]})
    save(tmp_path, "approved_tips.json", {"tips": []})

    def must_not_run(*args):
        raise AssertionError("High-risk candidate must not be sent for autonomous approval")

    result = run_autonomous_approval(tmp_path, reviewer=must_not_run)
    assert result["auto_approved"] == 0
    assert len(read(tmp_path, "candidate_tips.json")["tips"]) == 1
    assert read(tmp_path, "approved_tips.json")["tips"] == []
    assert read(tmp_path, "autonomous_review_log.json")["reviews"][0]["decision"] == "needs_human_review"


def test_fabricated_or_nonverbatim_step_evidence_cannot_be_approved(tmp_path):
    save(tmp_path, "sources.json", {"sources": [source()]})
    save(tmp_path, "candidate_tips.json", {"tips": [safe_candidate()]})
    save(tmp_path, "approved_tips.json", {"tips": []})

    def reviewer(tip, sources, model):
        return {
            "decision": "approve", "risk_level": "low", "confidence": 0.99,
            "stage_ids": ["08-infrastructure"], "reason": "Looks good.",
            "step_reviews": [{
                "step_index": 1, "evidence_excerpt": "Invented source quotation.",
                "source_url": "https://www.ready.gov/example",
            }],
        }

    result = run_autonomous_approval(tmp_path, reviewer=reviewer)
    assert result["auto_approved"] == 0
    assert len(read(tmp_path, "candidate_tips.json")["tips"]) == 1
    assert read(tmp_path, "approved_tips.json")["tips"] == []


def test_existing_approved_id_is_removed_from_stale_candidate_queue(tmp_path):
    tip = safe_candidate()
    approved = {
        **tip,
        "quality_status": "ai_verified",
        "verification": {"status": "approved", "review_type": "automated_low_risk_only"},
    }
    save(tmp_path, "sources.json", {"sources": [source()]})
    save(tmp_path, "candidate_tips.json", {"tips": [tip]})
    save(tmp_path, "approved_tips.json", {"tips": [approved]})

    result = run_autonomous_approval(tmp_path, reviewer=lambda *args: None)
    assert result["auto_approved"] == 0
    assert read(tmp_path, "candidate_tips.json")["tips"] == []
    assert read(tmp_path, "approved_tips.json")["tips"][0]["id"] == tip["id"]


def test_review_limit_leaves_unprocessed_candidates_in_queue(tmp_path):
    tips = [safe_candidate("candidate-" + str(i)) for i in range(3)]
    save(tmp_path, "sources.json", {"sources": [source()]})
    save(tmp_path, "candidate_tips.json", {"tips": tips})
    save(tmp_path, "approved_tips.json", {"tips": []})

    calls = []
    def reviewer(tip, sources, model):
        calls.append(tip["id"])
        return {
            "decision": "needs_human_review", "risk_level": "low", "confidence": 0.5,
            "stage_ids": ["08-infrastructure"], "reason": "Needs a person to check context.",
            "step_reviews": [],
        }

    result = run_autonomous_approval(tmp_path, reviewer=reviewer, limit=1)
    assert len(calls) == 1
    assert result["remaining_candidates"] == 3
    assert len(read(tmp_path, "candidate_tips.json")["tips"]) == 3
