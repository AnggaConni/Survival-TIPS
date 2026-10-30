from __future__ import annotations
import argparse
import re
from collections import defaultdict

from .common import ROOT, now_iso, read_json, write_json
from .extract_tips import extract
from .stages import get_stages
from .source_quality import duplicate_pairs, possible_conflict_pairs

GENERIC_PHRASES = (
    "be prepared", "improve resilience", "consult guidelines",
    "use appropriate", "plan ahead", "provide safe", "ensure proper",
)
VALID_CONTENT_TYPES = {"identify", "eat", "grow", "build", "make", "repair", "maintain", "treat", "prepare", "plan", "other", "communication_guidance", "planning_guidance", "material_guidance", "shelter_standard", "cold_climate_shelter_guidance", "safety_rule", "heating_reference"}

def norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()

def audit(tips, sources):
    source_by_url = {s.get("url"): s for s in sources if s.get("url")}
    issues = defaultdict(list)
    seen_titles = {}
    valid_stage_ids = {stage["id"] for stage in get_stages()}
    for tip in tips:
        tip_id = tip.get("id", "(missing-id)")
        title_key = norm(tip.get("title"))
        if not tip.get("title"):
            issues[tip_id].append("missing_title")
        if not tip.get("summary"):
            issues[tip_id].append("missing_summary")
        content_type = norm(tip.get("content_type"))
        if content_type not in VALID_CONTENT_TYPES:
            issues[tip_id].append("missing_or_invalid_content_type")
        if content_type == "eat":
            food_fields = ("identification_criteria", "edible_parts", "preparation_requirements", "lookalikes_or_uncertainty")
            if any(not isinstance(tip.get(field), list) or not tip.get(field) for field in food_fields):
                issues[tip_id].append("wild_food_safety_details_missing")
        if content_type in {"build", "make"}:
            if not tip.get("materials"): issues[tip_id].append("build_recipe_missing_materials")
            if not tip.get("tools"): issues[tip_id].append("build_recipe_missing_tools")
            if not tip.get("expected_result"): issues[tip_id].append("build_recipe_missing_expected_result")
        if not isinstance(tip.get("steps"), list) or not tip.get("steps"):
            issues[tip_id].append("no_actionable_steps")
        refs = tip.get("sources", [])
        if not refs:
            issues[tip_id].append("missing_source")
        else:
            evidence = str(tip.get("evidence_excerpt", "")).strip()
            matched = [source_by_url.get(ref.get("url")) for ref in refs if isinstance(ref, dict) and source_by_url.get(ref.get("url"))]
            if not matched:
                issues[tip_id].append("source_text_unavailable_for_audit")
            elif not evidence or not any(evidence.casefold() in str(source.get("text", "")).casefold() for source in matched):
                issues[tip_id].append("evidence_not_found_verbatim_in_any_referenced_source")
        searchable = norm(tip.get("title")) + " " + norm(tip.get("summary"))
        if any(phrase in searchable for phrase in GENERIC_PHRASES):
            issues[tip_id].append("possibly_generic_advice")
        if title_key in seen_titles:
            issues[tip_id].append("duplicate_title_exact:" + seen_titles[title_key])
        else:
            seen_titles[title_key] = tip_id
        current_stages = tip.get("stage_ids", [])
        if not isinstance(current_stages, list) or not current_stages:
            issues[tip_id].append("unclassified_stage")
        elif any(stage_id not in valid_stage_ids for stage_id in current_stages):
            issues[tip_id].append("invalid_stage_id")
        classification = tip.get("stage_classification", {})
        if not classification:
            issues[tip_id].append("stage_classification_not_auditable")
        elif classification.get("review_status") not in {"human_reviewed", "needs_human_review"}:
            issues[tip_id].append("invalid_stage_review_status")
        if tip.get("quality_status") not in {"source_aligned_needs_human_review", "ai_candidate_needs_review"}:
            issues[tip_id].append("missing_quality_status")
    for pair in duplicate_pairs(tips):
        issues[pair["left_id"]].append("possible_near_duplicate:" + str(pair["right_id"]))
        issues[pair["right_id"]].append("possible_near_duplicate:" + str(pair["left_id"]))
    for pair in possible_conflict_pairs(tips):
        issues[pair["left_id"]].append("possible_conflict_review:" + str(pair["right_id"]))
        issues[pair["right_id"]].append("possible_conflict_review:" + str(pair["left_id"]))
    return issues, source_by_url

def main():
    parser = argparse.ArgumentParser(description="Audit survival tips and optionally re-extract questionable source pages.")
    parser.add_argument("--repair", action="store_true", help="Re-extract flagged source pages into the selected unapproved dataset; never auto-approve candidates.")
    parser.add_argument("--dataset", choices=("tips", "candidates", "approved"), default="tips",
                        help="Dataset to audit: active review backlog, AI candidates, or approved tips.")
    parser.add_argument("--candidates", action="store_true", help="Backward-compatible alias for --dataset candidates.")
    parser.add_argument("--report-file", default="quality_report.json", help="Report filename under data/.")
    args = parser.parse_args()

    dataset = "candidates" if args.candidates else args.dataset
    if args.repair and dataset == "approved":
        parser.error("--repair cannot modify the approved dataset.")
    filenames = {
        "tips": "tips.json",
        "candidates": "candidate_tips.json",
        "approved": "approved_tips.json",
    }
    tip_path = ROOT / "data" / filenames[dataset]
    source_path = ROOT / "data" / "sources.json"
    tip_data = read_json(tip_path, {"schema_version": "1.0", "tips": []})
    source_data = read_json(source_path, {"sources": []})
    tips = tip_data.get("tips", [])
    sources = source_data.get("sources", [])
    issues, source_by_url = audit(tips, sources)

    duplicates = duplicate_pairs(tips)
    conflicts = possible_conflict_pairs(tips)
    print(f"[audit] Checked {len(tips)} tips; flagged {len(issues)} tip(s).")
    print(f"[audit] Similarity screening: {len(duplicates)} possible duplicate pair(s); lexical conflict screening: {len(conflicts)} possible conflict pair(s).")
    for pair in duplicates:
        print(f"[duplicate-review] {pair['left_id']} <-> {pair['right_id']} (similarity={pair['similarity']})")
    for pair in conflicts:
        print(f"[conflict-review] {pair['left_id']} <-> {pair['right_id']} signals={','.join(pair['signals'])}")
    source_tiers = defaultdict(int)
    for source in sources:
        assessment = source.get("quality_assessment", {})
        source_tiers[assessment.get("authority_tier", "unassessed")] += 1
    report = {
        "generated_at": now_iso(),
        "dataset": tip_path.name,
        "tip_count": len(tips),
        "flagged_tip_count": len(issues),
        "flagged_issues": {tip_id: sorted(set(items)) for tip_id, items in issues.items()},
        "possible_duplicate_pairs": duplicates,
        "possible_conflict_pairs": conflicts,
        "source_tier_counts": dict(source_tiers),
        "review_note": "Similarity and lexical conflict signals are triage leads only; they do not prove duplication or factual contradiction."
    }
    report_path = ROOT / "data" / args.report_file
    write_json(report_path, report)
    print(f"[audit] Wrote {report_path.relative_to(ROOT)}")
    for tip in tips:
        problems = issues.get(tip.get("id", "(missing-id)"))
        if problems:
            print(f"[audit] {tip.get('id')} | {tip.get('title', '(untitled)')}: {', '.join(problems)}")

    if not args.repair or not issues:
        return

    flagged_ids = set(issues)
    bad_tips = [tip for tip in tips if tip.get("id", "(missing-id)") in flagged_ids]
    urls_to_repair = sorted({
        source_ref.get("url")
        for tip in bad_tips
        for source_ref in tip.get("sources", [])
        if source_ref.get("url") in source_by_url and source_by_url[source_ref.get("url")].get("text")
    })
    if not urls_to_repair:
        print("[repair] No flagged source has stored source text; nothing changed.")
        return

    updated_tips = list(tips)
    repaired = 0
    for url in urls_to_repair:
        source = source_by_url[url]
        source_tips = [
            tip for tip in updated_tips
            if any(ref.get("url") == url for ref in tip.get("sources", []))
        ]
        feedback_lines = []
        for tip in source_tips:
            tip_issues = issues.get(tip.get("id", "(missing-id)"), [])
            if tip_issues:
                feedback_lines.append(f"- {tip.get('title', '(untitled)')}: {', '.join(tip_issues)}")
        repair_source = dict(source)
        repair_source["repair_feedback"] = (
            "Flagged existing entries and their issues:\\n"
            + "\\n".join(feedback_lines)
            + "\\nProduce only distinct, source-supported, actionable replacements. "
              "Do not preserve a weak title by merely rephrasing it; return no tip if evidence is insufficient."
        )
        replacements, provider = extract(repair_source)
        if not replacements:
            print(f"[repair] Kept existing tips for {url}: no replacement passed validation (provider={provider}).")
            continue
        replacement_issues, _ = audit(replacements, [source])
        severe = {
            "evidence_not_found_verbatim_in_any_referenced_source",
            "source_text_unavailable_for_audit",
            "no_actionable_steps", "missing_title", "missing_summary",
            "missing_source", "possibly_generic_advice", "unclassified_stage",
            "missing_or_invalid_content_type", "wild_food_safety_details_missing",
            "build_recipe_missing_materials", "build_recipe_missing_tools",
            "build_recipe_missing_expected_result", "missing_quality_status",
            "invalid_stage_id", "stage_classification_not_auditable",
            "invalid_stage_review_status",
        }
        rejected = {
            tip.get("id"): sorted(set(replacement_issues.get(tip.get("id"), [])) & severe)
            for tip in replacements
            if set(replacement_issues.get(tip.get("id"), [])) & severe
        }
        if rejected:
            print(f"[repair] Kept existing tips for {url}: replacement candidates still failed quality checks: {rejected}")
            continue
        flagged_for_url = {
            tip.get("id") for tip in source_tips
            if issues.get(tip.get("id", "(missing-id)"))
        }
        old_count = len(flagged_for_url)
        # Preserve unflagged records from the same source; only replace records
        # that the audit actually identified as problematic.
        updated_tips = [tip for tip in updated_tips if tip.get("id") not in flagged_for_url]
        for replacement in replacements:
            replacement["quality_status"] = "ai_candidate_needs_review"
            replacement["quality_notes"] = "AI repair candidate. Not human-reviewed or approved for operational use."
        updated_tips.extend(replacements)
        repaired += 1
        print(f"[repair] Replaced {old_count} flagged tip(s) for {url} with {len(replacements)} candidate(s) from {provider}.")

    if repaired:
        write_json(tip_path, {
            "schema_version": tip_data.get("schema_version", "1.0"),
            "generated_at": now_iso(),
            "tips": updated_tips[-5000:],
        })
        print(f"[repair] Saved updated {tip_path.name} after re-extracting {repaired} source page(s).")
    else:
        print("[repair] No source was replaced; tips.json left unchanged.")

if __name__ == "__main__":
    main()
