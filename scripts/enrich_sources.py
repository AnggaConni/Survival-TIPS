from __future__ import annotations
from .common import ROOT, now_iso, read_json, write_json
from .source_quality import annotate_source

def main():
    payload = read_json(ROOT / "data" / "sources.json", {"schema_version": "1.0", "sources": []})
    sources = [annotate_source(source) for source in payload.get("sources", [])]
    payload["schema_version"] = "1.1"
    payload["generated_at"] = now_iso()
    payload["sources"] = sources
    write_json(ROOT / "data" / "sources.json", payload)

    versions = read_json(ROOT / "data" / "source_versions.json", {"schema_version": "1.0", "events": []})
    versions["schema_version"] = "1.0"
    versions["generated_at"] = now_iso()
    known = {(event.get("source_url"), event.get("version")) for event in versions.get("events", [])}
    for source in sources:
        key = (source.get("url"), source.get("version", 1))
        if key not in known:
            versions.setdefault("events", []).append({
                "source_url": source.get("url"), "version": source.get("version", 1),
                "content_hash": source.get("content_hash"), "changed_at": source.get("first_seen_at"),
                "event": "baseline_snapshot"
            })
    versions["events"] = versions.get("events", [])[-5000:]
    write_json(ROOT / "data" / "source_versions.json", versions)

    for filename in ("tips.json", "candidate_tips.json"):
        tip_path = ROOT / "data" / filename
        tip_payload = read_json(tip_path, {"schema_version": "1.0", "tips": []})
        for tip in tip_payload.get("tips", []):
            if not tip.get("stage_classification"):
                stages = list(tip.get("stage_ids", []))
                tip["stage_classification"] = {
                    "suggested_stage_ids": stages,
                    "method": "legacy_existing_assignment",
                    "review_status": "needs_human_review",
                    "reason": "Backfilled from previously stored stage_ids; a reviewer has not confirmed this classification."
                }
                if stages:
                    tip["primary_stage_id"] = stages[0]
                    tip["secondary_stage_ids"] = stages[1:]
            tip.setdefault("prompt_version", "legacy_unversioned")
            tip.setdefault("extractor_version", "legacy_unversioned")
        write_json(tip_path, tip_payload)
    print(f"Enriched {len(sources)} source records; backfilled legacy stage metadata and source baselines.")

if __name__ == "__main__":
    main()
