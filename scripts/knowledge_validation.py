from __future__ import annotations

import argparse
from pathlib import Path

from .common import ROOT, read_json, is_http_url
from .stages import get_stages

# Separate, typed catalogues keep domain-specific knowledge structured.
CATALOGUES = {
    "recipes.json": {
        "key": "recipes",
        "required": ("title", "summary", "stage_ids", "materials", "tools", "steps", "expected_result"),
        "list_fields": ("materials", "tools", "prerequisites", "steps", "measurements", "failure_modes", "safety_notes"),
    },
    "materials.json": {
        "key": "materials",
        "required": ("title", "summary", "stage_ids", "material_class", "properties", "hazards"),
        "list_fields": ("properties", "production_methods", "applications", "hazards", "environmental_considerations"),
    },
    "biodiversity_profiles.json": {
        "key": "profiles",
        "required": ("title", "summary", "stage_ids", "scientific_name", "identification", "habitat_ecology", "distribution"),
        "list_fields": ("common_names", "identification", "habitat_ecology", "distribution", "ecological_role", "uses", "toxicity_or_lookalikes", "conservation_notes"),
    },
    "agriculture_profiles.json": {
        "key": "profiles",
        "required": ("title", "summary", "stage_ids", "crop_name", "regional_applicability"),
        "list_fields": ("propagation", "planting", "water_management", "nutrient_management", "pest_disease_management", "harvest", "storage", "failure_modes", "safety_notes"),
    },
}

VALID_STATUSES = {"needs_review", "approved"}
VALID_FOOD_USE_STATUSES = {
    "not_assessed",
    "source_reports_food_use_not_verified",
    "requires_expert_identification",
}


def validate_catalogues(root: Path = ROOT):
    errors = []
    counts = {}
    source_payload = read_json(root / "data" / "sources.json", {"sources": []})
    source_rows = source_payload.get("sources", [])
    source_text = {
        source.get("url"): source.get("text", "")
        for source in source_rows
        if isinstance(source, dict) and source.get("url")
    }
    valid_stages = {stage.get("id") for stage in get_stages()}
    all_ids = set()

    for filename, spec in CATALOGUES.items():
        payload = read_json(root / "data" / filename, {})
        key = spec["key"]
        rows = payload.get(key) if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            errors.append(f"data/{filename} must contain a '{key}' array")
            counts[filename] = 0
            continue
        counts[filename] = len(rows)

        for row in rows:
            if not isinstance(row, dict):
                errors.append(f"{filename} contains a non-object record")
                continue
            record_id = row.get("id")
            label = f"{filename}:{record_id or '(missing-id)'}"
            if not record_id:
                errors.append(f"{label} missing id")
            elif record_id in all_ids:
                errors.append(f"{label} duplicate ID across technical knowledge catalogues")
            else:
                all_ids.add(record_id)

            for field in spec["required"]:
                value = row.get(field)
                if value is None or value == "" or value == []:
                    errors.append(f"{label} missing required field: {field}")

            stage_ids = row.get("stage_ids", [])
            if not isinstance(stage_ids, list) or not stage_ids or any(stage not in valid_stages for stage in stage_ids):
                errors.append(f"{label} has empty or invalid stage_ids")

            sources = row.get("sources", [])
            if not isinstance(sources, list) or not sources:
                errors.append(f"{label} must cite at least one source")
                source_urls = set()
            else:
                source_urls = set()
                for source in sources:
                    url = source.get("url") if isinstance(source, dict) else None
                    if not is_http_url(url or "") or url not in source_text:
                        errors.append(f"{label} has a source URL not present in stored sources: {url}")
                    else:
                        source_urls.add(url)

            evidence = row.get("evidence", [])
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{label} must include field-level evidence")
                evidence = []
            evidence_fields = set()
            for item in evidence:
                if not isinstance(item, dict):
                    errors.append(f"{label} contains a malformed evidence item")
                    continue
                field = item.get("field")
                url = item.get("source_url")
                excerpt = item.get("excerpt")
                if not field or field not in row:
                    errors.append(f"{label} evidence references an unknown field: {field}")
                    continue
                if url not in source_urls:
                    errors.append(f"{label} evidence source is not among the record's sources: {url}")
                    continue
                if not isinstance(excerpt, str) or not excerpt.strip() or excerpt not in source_text.get(url, ""):
                    errors.append(f"{label} evidence for {field} is not verbatim in stored source text")
                    continue
                evidence_fields.add(field)

            for field in spec["required"]:
                if field not in {"title", "summary", "stage_ids"} and row.get(field) not in (None, "", []):
                    if field not in evidence_fields:
                        errors.append(f"{label} required field lacks field-level evidence: {field}")

            for field in spec["list_fields"]:
                value = row.get(field, [])
                if value is not None and not isinstance(value, list):
                    errors.append(f"{label} field '{field}' must be an array")
                    continue
                if value and field not in evidence_fields:
                    errors.append(f"{label} populated field lacks field-level evidence: {field}")
                if field == "steps":
                    for number, step in enumerate(value or [], 1):
                        if not isinstance(step, (str, dict)) or not (step.get("instruction") if isinstance(step, dict) else step.strip()):
                            errors.append(f"{label} step {number} is empty or malformed")

            verification = row.get("verification", {})
            status = verification.get("status") if isinstance(verification, dict) else None
            if status not in VALID_STATUSES:
                errors.append(f"{label} has invalid verification.status")
            elif status == "approved":
                for field in ("reviewed_by", "reviewed_at", "review_notes"):
                    if not verification.get(field):
                        errors.append(f"{label} approved record missing verification.{field}")

            if filename == "biodiversity_profiles.json":
                food_status = row.get("food_use_status", "not_assessed")
                if food_status not in VALID_FOOD_USE_STATUSES:
                    errors.append(
                        f"{label} has invalid food_use_status; this catalogue cannot certify a species as safe to eat"
                    )
                if row.get("uses") and row.get("use_claim_review_status") not in {
                    "requires_expert_review", "qualified_review_completed"
                }:
                    errors.append(
                        f"{label} has use claims without an explicit expert-review status"
                    )
                # Do not permit a field that turns a profile into a blanket edibility/safety certification.
                if any(field in row for field in ("safe_to_eat", "edible_certified", "medicinally_safe")):
                    errors.append(f"{label} contains a prohibited blanket food/medicine safety assertion")

    return errors, counts


def main():
    errors, counts = validate_catalogues()
    if errors:
        print("\\n".join(errors))
        raise SystemExit(1)
    summary = ", ".join(f"{name}: {count}" for name, count in counts.items())
    print(f"Technical knowledge catalogues OK — {summary}")


if __name__ == "__main__":
    main()
