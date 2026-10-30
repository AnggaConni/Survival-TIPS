from __future__ import annotations

import argparse
from pathlib import Path

from .common import ROOT, read_json, write_json, now_iso
from .stages import get_stages


def apply_decisions(decisions_path: Path, candidates_only: bool = False) -> int:
    decisions = read_json(decisions_path, {"decisions": []}).get("decisions", [])
    if not decisions:
        raise SystemExit("No review decisions found.")

    sources = read_json(ROOT / "data" / "sources.json", {"sources": []}).get("sources", [])
    source_text = {s.get("url"): s.get("text", "") for s in sources if s.get("url")}
    approved_path = ROOT / "data" / "approved_tips.json"
    approved_payload = read_json(approved_path, {"schema_version": "1.0", "tips": []})
    approved = {t["id"]: t for t in approved_payload.get("tips", [])}

    candidate_path = ROOT / "data" / "candidate_tips.json"
    candidate_payload = read_json(candidate_path, {"schema_version": "1.0", "tips": []})
    candidates = candidate_payload.get("tips", [])
    candidate_index = {tip.get("id"): tip for tip in candidates if tip.get("id")}

    index = {}
    if not candidates_only:
        active_payload = read_json(ROOT / "data" / "tips.json", {"tips": []})
        index.update({tip.get("id"): tip for tip in active_payload.get("tips", []) if tip.get("id")})
    index.update(candidate_index)

    valid_stage_ids = {stage["id"] for stage in get_stages()}
    changed = 0
    approved_candidate_ids = set()

    for decision in decisions:
        if decision.get("decision") != "approve":
            continue
        tip_id = decision.get("tip_id")
        if not tip_id:
            raise SystemExit("Approval decision is missing tip_id.")
        if candidates_only and tip_id not in candidate_index and tip_id not in approved:
            raise SystemExit(f"{tip_id}: not found in data/candidate_tips.json; candidate-only approval refused.")
        if tip_id in approved:
            # Idempotent reruns must not duplicate an already-published record.
            if tip_id in candidate_index:
                approved_candidate_ids.add(tip_id)
            continue
        if tip_id not in index:
            raise SystemExit(f"Unknown tip_id: {tip_id}")

        reviewer, notes = decision.get("reviewer"), decision.get("notes")
        if not reviewer or not notes:
            raise SystemExit(f"{tip_id}: reviewer and notes are required.")
        original = index[tip_id]
        reviews, steps = decision.get("step_reviews", []), original.get("steps", [])
        if not isinstance(reviews, list) or len(reviews) != len(steps):
            raise SystemExit(f"{tip_id}: provide exactly one step_review per step.")

        refs = {s.get("url") for s in original.get("sources", []) if isinstance(s, dict)}
        reviewed_steps = []
        for number, (step, review) in enumerate(zip(steps, reviews), 1):
            instruction = step.get("instruction", "") if isinstance(step, dict) else str(step)
            excerpt = review.get("evidence_excerpt", "") if isinstance(review, dict) else ""
            url = review.get("source_url", "") if isinstance(review, dict) else ""
            if not instruction or url not in refs or not excerpt or excerpt not in source_text.get(url, ""):
                raise SystemExit(
                    f"{tip_id} step {number}: evidence must be a verbatim excerpt from one of this tip's stored sources."
                )
            reviewed_steps.append({
                "instruction": instruction,
                "evidence_excerpt": excerpt,
                "source_url": url,
            })

        requested_stages = decision.get("stage_ids") or original.get("stage_ids", [])
        if (
            not isinstance(requested_stages, list)
            or not requested_stages
            or any(stage_id not in valid_stage_ids for stage_id in requested_stages)
        ):
            raise SystemExit(f"{tip_id}: stage_ids must contain valid configured stage IDs.")

        tip = dict(original)
        tip["steps"] = reviewed_steps
        tip["stage_ids"] = list(dict.fromkeys(requested_stages))
        tip["primary_stage_id"] = tip["stage_ids"][0]
        tip["secondary_stage_ids"] = tip["stage_ids"][1:]
        tip["stage_classification"] = {
            "suggested_stage_ids": original.get("stage_classification", {}).get(
                "suggested_stage_ids", original.get("stage_ids", [])
            ),
            "approved_stage_ids": tip["stage_ids"],
            "method": original.get("stage_classification", {}).get("method", "legacy_or_human_supplied"),
            "review_status": "human_reviewed",
            "reviewed_by": reviewer,
            "reviewed_at": decision.get("reviewed_at") or now_iso(),
            "reason": decision.get("stage_review_notes", "Reviewer confirmed or adjusted stage classification."),
        }
        tip["quality_status"] = "human_verified"
        tip["verification"] = {
            "status": "approved",
            "confidence": original.get("verification", {}).get("confidence", "not_assessed"),
            "reviewed_by": reviewer,
            "reviewed_at": decision.get("reviewed_at") or now_iso(),
            "review_notes": notes,
        }
        approved[tip_id] = tip
        if tip_id in candidate_index:
            approved_candidate_ids.add(tip_id)
        changed += 1

    # A candidate is moved, not copied: remove it from the queue only after
    # every approval check has passed and it exists in the publication dataset.
    if approved_candidate_ids:
        candidate_payload["tips"] = [
            tip for tip in candidates if tip.get("id") not in approved_candidate_ids
        ]
        candidate_payload["generated_at"] = now_iso()
        write_json(candidate_path, candidate_payload)

    approved_payload["tips"] = list(approved.values())
    approved_payload["generated_at"] = now_iso()
    write_json(approved_path, approved_payload)
    print(
        f"Applied {changed} approval(s); {len(approved)} approved tip(s) available for PDF export; "
        f"{len(candidate_payload.get('tips', []))} candidate(s) remain."
    )
    print("Review decisions are retained for audit history.")
    return changed


def main():
    parser = argparse.ArgumentParser(description="Apply human review decisions to Survival-TIPS.")
    parser.add_argument("--apply", action="store_true", help="Apply the supplied review decision JSON.")
    parser.add_argument(
        "--decisions-file",
        default=str(ROOT / "data" / "review_decisions.json"),
        help="Path to the review decision JSON file.",
    )
    parser.add_argument(
        "--candidates-only",
        action="store_true",
        help="Refuse approvals unless each tip is in candidate_tips.json.",
    )
    args = parser.parse_args()
    if not args.apply:
        parser.error("Use --apply after completing the human review decisions.")
    apply_decisions(Path(args.decisions_file), candidates_only=args.candidates_only)


if __name__ == "__main__":
    main()
