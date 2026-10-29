from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from .common import ROOT, read_json
from .stages import get_stages, tips_for_stage

OUT_DIR = ROOT / "docs" / "pdf"

def safe(value):
    return escape(str(value or "")).replace("\\n", "<br/>")

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(18 * mm, 12 * mm, "Survival-TIPS • Educational knowledge base • Verify local guidance")
    canvas.drawRightString(192 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()

def build_pdf(stage, tips, output_path):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontSize=25, leading=30, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="StageHeading", parent=styles["Heading1"], fontSize=17, leading=21, spaceBefore=12, spaceAfter=8))
    styles.add(ParagraphStyle(name="TipTitle", parent=styles["Heading2"], fontSize=12, leading=15, spaceBefore=9, spaceAfter=4))
    styles.add(ParagraphStyle(name="SmallNote", parent=styles["BodyText"], fontSize=8, leading=11, textColor=colors.HexColor("#555555")))
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=20*mm, title=f"Survival-TIPS — {stage['name']}", author="Survival-TIPS")
    story = [
        Spacer(1, 35*mm),
        Paragraph("SURVIVAL-TIPS", styles["CoverTitle"]),
        Paragraph(safe(stage["name"]), styles["Heading1"]),
        Spacer(1, 6*mm),
        Paragraph(safe(stage.get("description", "")), styles["BodyText"]),
        Spacer(1, 8*mm),
        Paragraph(f"Stage {stage['order']:02d} • Generated {datetime.now().strftime('%Y-%m-%d')} • {len(tips)} knowledge entries", styles["SmallNote"]),
        Spacer(1, 10*mm),
        Paragraph("How to use this handbook", styles["Heading2"]),
        Paragraph("Use this guide as a learning aid, not as a substitute for official emergency instructions or expert assessment. Every AI-extracted tip must be reviewed before it is treated as verified guidance. Never infer that a wild plant, mushroom, water source, or improvised material is safe based on appearance alone.", styles["BodyText"]),
        PageBreak(),
    ]
    if not tips:
        story.extend([Paragraph("No entries yet", styles["StageHeading"]), Paragraph("This stage is ready for content. Run the collection pipeline, review candidate entries, then regenerate this PDF.", styles["BodyText"])])
    for index, tip in enumerate(tips, 1):
        block = [Paragraph(f"{index}. {safe(tip.get('title', 'Untitled'))}", styles["TipTitle"])]
        if tip.get("summary"):
            block.append(Paragraph(safe(tip["summary"]), styles["BodyText"]))
        if tip.get("content_type"):
            block.append(Paragraph("Action type: " + safe(tip["content_type"]), styles["SmallNote"]))
        for field, label in (("materials", "Materials / ingredients"), ("tools", "Tools / equipment"), ("prerequisites", "Prerequisites")):
            values = tip.get(field, [])
            if values:
                block.append(Paragraph("<b>" + label + "</b>", styles["BodyText"]))
                for value in values:
                    block.append(Paragraph("• " + safe(value), styles["BodyText"]))
        if tip.get("steps"):
            block.append(Paragraph("<b>Steps</b>", styles["BodyText"]))
            for step_num, step in enumerate(tip["steps"], 1):
                block.append(Paragraph(f"{step_num}. {safe(step)}", styles["BodyText"]))
        if tip.get("expected_result"):
            block.append(Paragraph("<b>Expected result</b>: " + safe(tip["expected_result"]), styles["BodyText"]))
        for field, label in (("failure_modes", "Failure modes / limitations"), ("safety_notes", "Safety notes"), ("identification_criteria", "Identification criteria"), ("edible_parts", "Edible parts stated by source"), ("preparation_requirements", "Preparation requirements"), ("lookalikes_or_uncertainty", "Look-alikes / uncertainty")):
            values = tip.get(field, [])
            if values:
                block.append(Paragraph("<b>" + label + "</b>", styles["BodyText"]))
                for value in values:
                    block.append(Paragraph("• " + safe(value), styles["BodyText"]))
        if tip.get("warnings"):
            block.append(Paragraph("<b>Warnings</b>", styles["BodyText"]))
            for warning in tip["warnings"]:
                block.append(Paragraph("• " + safe(warning), styles["BodyText"]))
        verification = tip.get("verification", {})
        block.append(Paragraph(f"Review status: {safe(verification.get('status', 'needs_review'))} • Category: {safe(tip.get('category', 'other'))}", styles["SmallNote"]))
        for source in tip.get("sources", []):
            url = str(source.get("url", ""))
            if url.startswith(("https://", "http://")):
                block.append(Paragraph("Source: " + safe(source.get("title") or url) + " — " + safe(url), styles["SmallNote"]))
        block.append(Spacer(1, 3*mm))
        story.append(KeepTogether(block))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

def main():
    parser = argparse.ArgumentParser(description="Generate a separate offline PDF handbook for each Survival-TIPS stage.")
    parser.add_argument("--stage", help="Stage ID (for example 03-water-sanitation).")
    parser.add_argument("--all", action="store_true", help="Generate a PDF for every stage.")
    parser.add_argument("--output-dir", default=str(OUT_DIR), help="Output directory for PDFs.")
    args = parser.parse_args()
    stages = get_stages()
    if not stages:
        parser.error("No stages configured in config/stages.json")
    if not args.all and not args.stage:
        parser.error("Choose --all or --stage STAGE_ID")
    selected = stages if args.all else [s for s in stages if s["id"] == args.stage]
    if not selected:
        parser.error(f"Unknown stage ID: {args.stage}. Available: " + ", ".join(s["id"] for s in stages))
    tips_payload = read_json(ROOT / "data" / "tips.json", {"tips": []})
    tips = tips_payload.get("tips", [])
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stage in selected:
        stage_tips = tips_for_stage(tips, stage["id"])
        path = out_dir / f"{stage['id']}.pdf"
        build_pdf(stage, stage_tips, path)
        print(f"[pdf] {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}: {len(stage_tips)} entries")
    print(f"Generated {len(selected)} PDF handbook(s).")

if __name__ == "__main__":
    main()
