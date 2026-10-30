from __future__ import annotations
from pathlib import Path
from .common import ROOT, read_json

VALID_CONTENT_TYPES = {
    "identify", "eat", "grow", "build", "make", "repair", "maintain",
    "treat", "prepare", "plan", "other", "communication_guidance",
    "planning_guidance", "material_guidance", "shelter_standard",
    "cold_climate_shelter_guidance", "safety_rule", "heating_reference",
}
VALID_QUALITY_STATUSES = {"source_aligned_needs_human_review", "ai_candidate_needs_review"}

def validate():
    errors=[]
    data={name:read_json(ROOT/"data"/f"{name}.json",{}) for name in ("sources","tips","species")}
    for name,payload in data.items():
        if not isinstance(payload.get(name),list):
            errors.append(f"data/{name}.json must have '{name}' array")
    optional = {
        "candidate_tips": read_json(ROOT/"data"/"candidate_tips.json", {"tips": []}),
        "tips.quarantine": read_json(ROOT/"data"/"tips.quarantine.json", {"tips": []}),
    }
    active=data["tips"].get("tips",[])
    candidates=optional["candidate_tips"].get("tips",[])
    quarantined=optional["tips.quarantine"].get("tips",[])
    all_groups=(("active",active),("candidate",candidates),("quarantine",quarantined))
    ids=set()
    for group,rows in all_groups:
        if not isinstance(rows,list):
            errors.append(f"{group} tips must be an array")
            continue
        for tip in rows:
            tip_id=tip.get("id")
            if not tip_id or not tip.get("title") or not tip.get("summary"):
                errors.append(f"{group} tip missing id/title/summary: {tip_id}")
            if tip_id in ids:
                errors.append(f"duplicate tip ID across active/candidate/quarantine: {tip_id}")
            ids.add(tip_id)
            if not isinstance(tip.get("sources"),list) or not tip.get("sources"):
                errors.append(f"{group} tip missing non-empty sources: {tip_id}")
            if group == "quarantine":
                if not tip.get("quarantine_reason"):
                    errors.append(f"quarantine tip missing quarantine_reason: {tip_id}")
                continue
            for field in ("steps","stage_ids"):
                if not isinstance(tip.get(field),list) or not tip.get(field):
                    errors.append(f"{group} tip missing non-empty {field}: {tip_id}")
            if not tip.get("content_type") or tip.get("content_type") not in VALID_CONTENT_TYPES:
                errors.append(f"{group} tip has missing/invalid content_type: {tip_id}")
            if tip.get("quality_status") not in VALID_QUALITY_STATUSES:
                errors.append(f"{group} tip has missing/invalid quality_status: {tip_id}")
            verification=tip.get("verification",{})
            if verification.get("status") != "needs_review":
                errors.append(f"{group} tip must remain needs_review until human approval: {tip_id}")
            if verification.get("reviewed_by") or verification.get("reviewed_at"):
                errors.append(f"{group} tip has reviewer metadata without an approval workflow: {tip_id}")
    for row in data["species"].get("species",[]):
        for field in ("image_path","image_license","image_source_url"):
            if not row.get(field): errors.append(f"species missing {field}: {row.get('id')}")
    if errors:
        print("\n".join(errors))
        return False
    print(f"Data OK: {len(data['sources']['sources'])} sources, {len(active)} active tips, {len(candidates)} candidates, {len(quarantined)} quarantined tips, {len(data['species']['species'])} species/images.")
    return True

if __name__=="__main__":
    raise SystemExit(0 if validate() else 1)
