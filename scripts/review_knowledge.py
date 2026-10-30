from __future__ import annotations

import argparse
import json
from pathlib import Path

from .common import ROOT, read_json, write_json, now_iso
from .knowledge_validation import CATALOGUES


def _catalogue_path(name: str) -> Path:
    if name not in CATALOGUES:
        raise SystemExit(f"Unknown catalogue: {name}. Choose one of: {', '.join(CATALOGUES)}")
    return ROOT / "data" / name


def list_pending():
    for filename, spec in CATALOGUES.items():
        payload = read_json(ROOT / "data" / filename, {spec["key"]: []})
        for row in payload.get(spec["key"], []):
            status = row.get("verification", {}).get("status", "missing")
            if status == "needs_review":
                print(f"{filename} | {row.get('id')} | {row.get('title')}")


def write_template(items: list[str]):
    decisions = []
    for item in items:
        if ":" not in item:
            raise SystemExit(f"Use catalogue.json:record-id, received: {item}")
        filename, record_id = item.split(":", 1)
        path = _catalogue_path(filename)
        spec = CATALOGUES[filename]
        payload = read_json(path, {spec["key"]: []})
        if not any(row.get("id") == record_id for row in payload.get(spec["key"], [])):
            raise SystemExit(f"Record not found: {item}")
        decisions.append({
            "catalogue": filename,
            "record_id": record_id,
            "decision": "approve",
            "reviewer": "REPLACE_WITH_REVIEWER",
            "reviewed_at": "",
            "review_notes": "REPLACE_WITH_REVIEW_NOTES",
        })
    print(json.dumps({"schema_version": "1.0", "decisions": decisions}, ensure_ascii=False, indent=2))


def apply_decisions(decisions_path: Path) -> int:
    manifest = read_json(decisions_path, {"decisions": []})
    decisions = manifest.get("decisions", [])
    if not isinstance(decisions, list) or not decisions:
        raise SystemExit("No knowledge review decisions supplied.")

    sources_payload = read_json(ROOT / "data" / "sources.json", {"sources": []})
    source_text = {
        row.get("url"): row.get("text", "")
        for row in sources_payload.get("sources", [])
        if isinstance(row, dict) and row.get("url")
    }
    loaded = {}
    changed = 0
    for decision in decisions:
        if decision.get("decision") != "approve":
            continue
        filename = decision.get("catalogue")
        path = _catalogue_path(filename)
        spec = CATALOGUES[filename]
        if filename not in loaded:
            loaded[filename] = read_json(path, {spec["key"]: []})
        payload = loaded[filename]
        rows = payload.get(spec["key"], [])
        record = next((row for row in rows if row.get("id") == decision.get("record_id")), None)
        if record is None:
            raise SystemExit(f"{filename}: record not found: {decision.get('record_id')}")
        if record.get("verification", {}).get("status") == "approved":
            continue

        reviewer = str(decision.get("reviewer", "")).strip()
        notes = str(decision.get("review_notes", "")).strip()
        if not reviewer or not notes:
            raise SystemExit(f"{filename}:{record.get('id')} requires reviewer and review_notes.")

        refs = {
            source.get("url")
            for source in record.get("sources", [])
            if isinstance(source, dict) and source.get("url")
        }
        evidence_fields = set()
        evidence = record.get("evidence", [])
        if not isinstance(evidence, list) or not evidence:
            raise SystemExit(f"{filename}:{record.get('id')} has no field-level evidence.")
        for item in evidence:
            if not isinstance(item, dict):
                raise SystemExit(f"{filename}:{record.get('id')} has malformed evidence.")
            field, url, excerpt = item.get("field"), item.get("source_url"), item.get("excerpt")
            if not field or field not in record or url not in refs or not excerpt or excerpt not in source_text.get(url, ""):
                raise SystemExit(
                    f"{filename}:{record.get('id')} evidence must be verbatim and linked to one of its stored sources."
                )
            evidence_fields.add(field)

        required_fields = set(spec["required"]) - {"title", "summary", "stage_ids"}
        for field in required_fields:
            if record.get(field) not in (None, "", []) and field not in evidence_fields:
                raise SystemExit(f"{filename}:{record.get('id')} required field lacks evidence: {field}")
        metadata_fields = {
            "id", "title", "summary", "stage_ids", "sources", "evidence",
            "verification", "food_use_status", "use_claim_review_status",
            "qualified_reviewer", "qualification_basis", "generated_at",
        }
        for field, value in record.items():
            if field in metadata_fields or value in (None, "", []):
                continue
            if field not in evidence_fields:
                raise SystemExit(f"{filename}:{record.get('id')} populated claim field lacks evidence: {field}")
        if filename == "biodiversity_profiles.json":
            food_status = record.get("food_use_status", "not_assessed")
            if food_status != "not_assessed" and "food_use_status" not in evidence_fields:
                raise SystemExit(f"{filename}:{record.get('id')} food_use_status requires source evidence")

        if filename == "biodiversity_profiles.json" and record.get("uses"):
            if record.get("use_claim_review_status") != "qualified_review_completed":
                raise SystemExit(
                    f"{filename}:{record.get('id')} use claims require qualified review before approval."
                )
            if not record.get("qualified_reviewer") or not record.get("qualification_basis"):
                raise SystemExit(
                    f"{filename}:{record.get('id')} must record the qualified reviewer and qualification basis."
                )

        record["verification"] = {
            "status": "approved",
            "reviewed_by": reviewer,
            "reviewed_at": decision.get("reviewed_at") or now_iso(),
            "review_notes": notes,
        }
        changed += 1

    for filename, payload in loaded.items():
        spec = CATALOGUES[filename]
        payload["generated_at"] = now_iso()
        write_json(ROOT / "data" / filename, payload)

    print(f"Approved {changed} technical knowledge record(s).")
    return changed


def main():
    parser = argparse.ArgumentParser(description="Human review for Phase 3 technical knowledge catalogues.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List records awaiting human review.")
    group.add_argument("--template", nargs="+", metavar="CATALOGUE:ID", help="Create a review decision template.")
    group.add_argument("--apply", action="store_true", help="Apply completed human review decisions.")
    parser.add_argument("--decisions-file", default=str(ROOT / "data" / "knowledge_review_decisions.json"))
    args = parser.parse_args()
    if args.list:
        list_pending()
    elif args.template:
        write_template(args.template)
    else:
        apply_decisions(Path(args.decisions_file))


if __name__ == "__main__":
    main()
