from __future__ import annotations
import argparse
import re
from collections import defaultdict

from .common import ROOT, now_iso, read_json, write_json
from .extract_tips import extract
from .stages import classify_tip

GENERIC_PHRASES = (
    "be prepared", "improve resilience", "consult guidelines",
    "use appropriate", "plan ahead", "provide safe", "ensure proper",
)
VALID_CONTENT_TYPES = {"identify", "eat", "grow", "build", "make", "repair", "maintain", "treat", "prepare", "plan", "other"}

def norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()

def audit(tips, sources):
    source_by_url = {s.get("url"): s for s in sources if s.get("url")}
    issues = defaultdict(list)
    seen_titles = {}
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
            if not tip.get("materials"):
                issues[tip_id].append("build_recipe_missing_materials")
            if not tip.get("tools"):
                issues[tip_id].append("build_recipe_missing_tools")
            if not tip.get("expected_result"):
                issues[tip_id].append("build_recipe_missing_expected_result")
        if not isinstance(tip.get("steps"), list) or not tip.get("steps"):
            issues[tip_id].append("no_actionable_steps")
        if not tip.get("sources"):
            issues[tip_id].append("missing_source")
        else:
            matched_source = None
            for source_ref in tip.get("sources", []):
                source = source_by_url.get(source_ref.get("url"))
                if source:
                    matched_source = source
                    break
            if matched_source:
                evidence = str(tip.get("evidence_excerpt", "")).strip()
                body = str(matched_source.get("text", ""))
                if not evidence or evidence.casefold() not in body.casefold():
                    issues[tip_id].append("evidence_not_found_verbatim_in_source")
            else:
                issues[tip_id].append("source_text_unavailable_for_audit")
        searchable = norm(tip.get("title")) + " " + norm(tip.get("summary"))
        if any(phrase in searchable for phrase in GENERIC_PHRASES):
            issues[tip_id].append("possibly_generic_advice")
        if title_key in seen_titles:
            issues[tip_id].append("duplicate_title:" + seen_titles[title_key])
        else:
            seen_titles[title_key] = tip_id
        expected_stages = classify_tip({**tip, "stage_ids": []})
        current_stages = tip.get("stage_ids", [])
        if expected_stages and set(expected_stages) != set(current_stages):
            issues[tip_id].append("stage_assignment_mismatch")
        if not current_stages:
            issues[tip_id].append("unclassified_stage")
    return issues, source_by_url

def main():
    parser = argparse.ArgumentParser(description="Audit survival tips and optionally re-extract questionable source pages.")
    parser.add_argument("--repair", action="store_true", help="Re-extract source pages associated with questionable tips; replace old tips only when valid replacements are found.")
    args = parser.parse_args()

    tip_path = ROOT / "data" / "tips.json"
    source_path = ROOT / "data" / "sources.json"
    tip_data = read_json(tip_path, {"schema_version": "1.0", "tips": []})
    source_data = read_json(source_path, {"sources": []})
    tips = tip_data.get("tips", [])
    sources = source_data.get("sources", [])
    issues, source_by_url = audit(tips, sources)

    print(f"[audit] Checked {len(tips)} tips; flagged {len(issues)} tip(s).")
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
            "evidence_not_found_verbatim_in_source", "no_actionable_steps",
            "missing_title", "missing_summary", "missing_source",
            "possibly_generic_advice", "unclassified_stage",
            "missing_or_invalid_content_type", "wild_food_safety_details_missing",
            "build_recipe_missing_materials", "build_recipe_missing_tools",
            "build_recipe_missing_expected_result",
        }
        rejected = {
            tip.get("id"): sorted(set(replacement_issues.get(tip.get("id"), [])) & severe)
            for tip in replacements
            if set(replacement_issues.get(tip.get("id"), [])) & severe
        }
        if rejected:
            print(f"[repair] Kept existing tips for {url}: replacement candidates still failed quality checks: {rejected}")
            continue
        before = len(updated_tips)
        old_count = len(source_tips)
        updated_tips = [
            tip for tip in updated_tips
            if not any(ref.get("url") == url for ref in tip.get("sources", []))
        ]
        updated_tips.extend(replacements)
        repaired += 1
        print(f"[repair] Replaced source tips for {url}: {old_count} old candidate(s) -> {len(replacements)} new candidate(s) from {provider}.")

    if repaired:
        write_json(tip_path, {
            "schema_version": tip_data.get("schema_version", "1.0"),
            "generated_at": now_iso(),
            "tips": updated_tips[-5000:],
        })
        print(f"[repair] Saved updated tips.json after re-extracting {repaired} source page(s).")
    else:
        print("[repair] No source was replaced; tips.json left unchanged.")

if __name__ == "__main__":
    main()
