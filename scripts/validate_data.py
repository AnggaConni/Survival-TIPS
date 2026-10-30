from __future__ import annotations
from .common import ROOT, read_json, is_http_url
from .stages import get_stages

VALID_CONTENT_TYPES = {
    "identify", "eat", "grow", "build", "make", "repair", "maintain",
    "treat", "prepare", "plan", "other", "communication_guidance",
    "planning_guidance", "material_guidance", "shelter_standard",
    "cold_climate_shelter_guidance", "safety_rule", "heating_reference",
}
VALID_QUALITY_STATUSES = {"source_aligned_needs_human_review", "ai_candidate_needs_review"}

def validate():
    errors = []
    data = {name: read_json(ROOT / "data" / f"{name}.json", {}) for name in ("sources", "tips", "species")}
    for name, payload in data.items():
        if not isinstance(payload.get(name), list):
            errors.append(f"data/{name}.json must have '{name}' array")
    active = data["tips"].get("tips", []) if isinstance(data["tips"].get("tips"), list) else []
    candidates = read_json(ROOT / "data" / "candidate_tips.json", {"tips": []}).get("tips", [])
    quarantined = read_json(ROOT / "data" / "tips.quarantine.json", {"tips": []}).get("tips", [])
    approved = read_json(ROOT / "data" / "approved_tips.json", {"tips": []}).get("tips", [])
    sources = data["sources"].get("sources", [])
    source_text = {s.get("url"): s.get("text", "") for s in sources if s.get("url")}
    version_events = read_json(ROOT / "data" / "source_versions.json", {"events": []}).get("events", [])
    version_keys = {(event.get("source_url"), event.get("version")) for event in version_events}
    for source in sources:
        if (source.get("url"), source.get("version", 1)) not in version_keys:
            errors.append(f"source version missing from history: {source.get('url')}")
    for source in sources:
        assessment = source.get("quality_assessment", {})
        if not source.get("content_hash") or not source.get("version"):
            errors.append(f"source missing content version metadata: {source.get('url')}")
        for field in ("authority_tier", "document_type", "technical_depth", "quality_score", "review_status"):
            if field not in assessment:
                errors.append(f"source missing quality assessment {field}: {source.get('url')}")
        if assessment.get("review_status") != "needs_human_review":
            errors.append(f"source heuristic assessment must remain unreviewed: {source.get('url')}")
    valid_stages = {s.get("id") for s in get_stages()}
    ids = set()
    for group, rows in (("active", active), ("candidate", candidates), ("quarantine", quarantined)):
        if not isinstance(rows, list):
            errors.append(f"{group} tips must be an array")
            continue
        for tip in rows:
            if not isinstance(tip, dict):
                errors.append(f"{group} contains a non-object tip")
                continue
            tip_id = tip.get("id")
            if not tip_id or not tip.get("title") or not tip.get("summary"):
                errors.append(f"{group} tip missing id/title/summary: {tip_id}")
            if tip_id in ids:
                errors.append(f"duplicate tip ID across active/candidate/quarantine: {tip_id}")
            ids.add(tip_id)
            refs = tip.get("sources")
            if not isinstance(refs, list) or not refs:
                errors.append(f"{group} tip missing non-empty sources: {tip_id}")
            elif any(not isinstance(s, dict) or not is_http_url(s.get("url", "")) for s in refs):
                errors.append(f"{group} tip has invalid source URL: {tip_id}")
            if group == "quarantine":
                if not tip.get("quarantine_reason"):
                    errors.append(f"quarantine tip missing quarantine_reason: {tip_id}")
                continue
            for field in ("steps", "stage_ids"):
                if not isinstance(tip.get(field), list) or not tip.get(field):
                    errors.append(f"{group} tip missing non-empty {field}: {tip_id}")
            if tip.get("content_type") not in VALID_CONTENT_TYPES:
                errors.append(f"{group} tip has missing/invalid content_type: {tip_id}")
            if tip.get("quality_status") not in VALID_QUALITY_STATUSES:
                errors.append(f"{group} tip has missing/invalid quality_status: {tip_id}")
            if any(stage_id not in valid_stages for stage_id in tip.get("stage_ids", [])):
                errors.append(f"{group} tip has unknown stage ID: {tip_id}")
            verification = tip.get("verification", {})
            if verification.get("status") != "needs_review":
                errors.append(f"{group} tip must remain needs_review until human approval: {tip_id}")
            if verification.get("reviewed_by") or verification.get("reviewed_at"):
                errors.append(f"{group} tip has reviewer metadata without approval: {tip_id}")
    approved_ids = set()
    for tip in approved:
        if not isinstance(tip, dict):
            errors.append("approved dataset contains a non-object tip")
            continue
        tip_id = tip.get("id")
        if not tip_id or tip_id in approved_ids:
            errors.append(f"approved dataset has missing/duplicate ID: {tip_id}")
        approved_ids.add(tip_id)
        verification = tip.get("verification", {})
        if verification.get("status") != "approved" or tip.get("quality_status") != "human_verified":
            errors.append(f"approved tip lacks approved/human_verified status: {tip_id}")
        stage_review = tip.get("stage_classification", {})
        if stage_review.get("review_status") != "human_reviewed" or not stage_review.get("reviewed_by") or not stage_review.get("reviewed_at"):
            errors.append(f"approved tip lacks human-reviewed stage classification: {tip_id}")
        if not tip.get("primary_stage_id") or tip.get("primary_stage_id") not in valid_stages:
            errors.append(f"approved tip has invalid primary stage: {tip_id}")
        if tip.get("primary_stage_id") != (tip.get("stage_ids") or [None])[0]:
            errors.append(f"approved tip primary stage does not match stage_ids: {tip_id}")
        if stage_review.get("approved_stage_ids") != tip.get("stage_ids"):
            errors.append(f"approved tip stage review does not match published stage_ids: {tip_id}")
        if not verification.get("reviewed_by") or not verification.get("reviewed_at") or not verification.get("review_notes"):
            errors.append(f"approved tip missing reviewer, date, or review notes: {tip_id}")
        refs = {s.get("url") for s in tip.get("sources", []) if isinstance(s, dict)}
        if not refs or any(not is_http_url(url or "") for url in refs):
            errors.append(f"approved tip has invalid sources: {tip_id}")
        steps = tip.get("steps", [])
        if not isinstance(steps, list) or not steps:
            errors.append(f"approved tip has no steps: {tip_id}")
            continue
        for number, step in enumerate(steps, 1):
            if not isinstance(step, dict):
                errors.append(f"approved tip step {number} must have structured evidence: {tip_id}")
                continue
            excerpt, url = step.get("evidence_excerpt", ""), step.get("source_url", "")
            if not step.get("instruction") or not excerpt or url not in refs:
                errors.append(f"approved tip step {number} missing instruction/evidence/source: {tip_id}")
            elif excerpt not in source_text.get(url, ""):
                errors.append(f"approved tip step {number} evidence not found verbatim in stored source: {tip_id}")
    for row in data["species"].get("species", []):
        for field in ("image_path", "image_license", "image_source_url"):
            if not row.get(field):
                errors.append(f"species missing {field}: {row.get('id')}")
    if errors:
        print("\n".join(errors))
        return False
    print(f"Data OK: {len(sources)} sources, {len(active)} active review items, {len(candidates)} candidates, {len(quarantined)} quarantined, {len(approved)} approved tips, {len(data['species']['species'])} species/images.")
    return True

if __name__ == "__main__":
    raise SystemExit(0 if validate() else 1)
