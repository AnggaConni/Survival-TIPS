from __future__ import annotations
import argparse
from .common import ROOT, read_json, write_json, now_iso

def main():
    parser = argparse.ArgumentParser(description="Apply human review decisions to Survival-TIPS candidates.")
    parser.add_argument("--apply", action="store_true", help="Apply data/review_decisions.json.")
    args = parser.parse_args()
    if not args.apply:
        parser.error("Use --apply after editing data/review_decisions.json.")
    decisions = read_json(ROOT / "data" / "review_decisions.json", {"decisions": []}).get("decisions", [])
    if not decisions:
        parser.error("No review decisions found.")
    sources = read_json(ROOT / "data" / "sources.json", {"sources": []}).get("sources", [])
    source_text = {s.get("url"): s.get("text", "") for s in sources if s.get("url")}
    approved_payload = read_json(ROOT / "data" / "approved_tips.json", {"schema_version": "1.0", "tips": []})
    approved = {t["id"]: t for t in approved_payload.get("tips", [])}
    index = {}
    for filename in ("tips.json", "candidate_tips.json"):
        payload = read_json(ROOT / "data" / filename, {"tips": []})
        for tip in payload.get("tips", []):
            index[tip.get("id")] = tip
    changed = 0
    for decision in decisions:
        if decision.get("decision") != "approve":
            continue
        tip_id = decision.get("tip_id")
        if tip_id in approved:
            continue
        if tip_id not in index:
            raise SystemExit(f"Unknown tip_id: {tip_id}")
        reviewer, notes = decision.get("reviewer"), decision.get("notes")
        if not reviewer or not notes:
            raise SystemExit(f"{tip_id}: reviewer and notes are required")
        original = index[tip_id]
        reviews, steps = decision.get("step_reviews", []), original.get("steps", [])
        if len(reviews) != len(steps):
            raise SystemExit(f"{tip_id}: provide exactly one step_review per step")
        refs = {s.get("url") for s in original.get("sources", []) if isinstance(s, dict)}
        reviewed_steps = []
        for number, (step, review) in enumerate(zip(steps, reviews), 1):
            instruction = step.get("instruction", "") if isinstance(step, dict) else str(step)
            excerpt, url = review.get("evidence_excerpt", ""), review.get("source_url", "")
            if not instruction or url not in refs or not excerpt or excerpt not in source_text.get(url, ""):
                raise SystemExit(f"{tip_id} step {number}: evidence must be a verbatim excerpt from one of this tip's stored sources")
            reviewed_steps.append({"instruction": instruction, "evidence_excerpt": excerpt, "source_url": url})
        tip = dict(original)
        tip["steps"] = reviewed_steps
        tip["quality_status"] = "human_verified"
        tip["verification"] = {
            "status": "approved",
            "confidence": original.get("verification", {}).get("confidence", "not_assessed"),
            "reviewed_by": reviewer,
            "reviewed_at": decision.get("reviewed_at") or now_iso(),
            "review_notes": notes
        }
        approved[tip_id] = tip
        changed += 1
    approved_payload["tips"] = list(approved.values())
    approved_payload["generated_at"] = now_iso()
    write_json(ROOT / "data" / "approved_tips.json", approved_payload)
    print(f"Applied {changed} approval(s); {len(approved)} approved tip(s) available for PDF export.")
    print("Review decisions are retained for audit history.")

if __name__ == "__main__":
    main()
