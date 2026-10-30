from __future__ import annotations

import argparse
import json
from pathlib import Path

from .common import ROOT, read_json
from .review_tips import apply_decisions


def list_candidates():
    payload = read_json(ROOT / "data" / "candidate_tips.json", {"tips": []})
    tips = payload.get("tips", [])
    if not tips:
        print("No candidate tips are currently queued.")
        return
    for tip in tips:
        sources = tip.get("sources", [])
        print(f"{tip.get('id')} | {tip.get('title')}")
        print(f"  stages: {', '.join(tip.get('stage_ids', [])) or 'unassigned'}")
        print(f"  steps: {len(tip.get('steps', []))} | sources: {len(sources)}")
        for source in sources:
            print(f"  source: {source.get('url', '')}")


def write_template(tip_ids: list[str]):
    payload = read_json(ROOT / "data" / "candidate_tips.json", {"tips": []})
    index = {tip.get("id"): tip for tip in payload.get("tips", [])}
    decisions = []
    for tip_id in tip_ids:
        tip = index.get(tip_id)
        if not tip:
            raise SystemExit(f"Candidate not found: {tip_id}")
        sources = tip.get("sources", [])
        default_url = sources[0].get("url", "") if sources else ""
        decisions.append({
            "tip_id": tip_id,
            "decision": "approve",
            "reviewer": "REPLACE_WITH_REVIEWER",
            "reviewed_at": "",
            "notes": "REPLACE_WITH_REVIEW_NOTES",
            "stage_ids": tip.get("stage_ids", []),
            "stage_review_notes": "REPLACE_WITH_STAGE_REVIEW_NOTES",
            "step_reviews": [
                {"evidence_excerpt": "REPLACE_WITH_EXACT_SOURCE_QUOTE", "source_url": default_url}
                for _ in tip.get("steps", [])
            ],
        })
    print(json.dumps({"schema_version": "1.0", "decisions": decisions}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="List candidate tips, create a review template, or apply completed human approvals."
    )
    parser.add_argument("--list", action="store_true", help="List candidates with IDs, stages, steps, and sources.")
    parser.add_argument("--template", nargs="+", metavar="TIP_ID", help="Print a decision JSON template for selected candidates.")
    parser.add_argument("--apply", action="store_true", help="Apply completed decisions and move approved candidates.")
    parser.add_argument("--decisions-file", default=str(ROOT / "data" / "review_decisions.json"))
    args = parser.parse_args()

    if args.list:
        list_candidates()
    elif args.template:
        write_template(args.template)
    elif args.apply:
        apply_decisions(Path(args.decisions_file), candidates_only=True)
    else:
        parser.error("Choose --list, --template TIP_ID [TIP_ID ...], or --apply.")


if __name__ == "__main__":
    main()
