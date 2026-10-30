from __future__ import annotations

import argparse
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, ListFlowable, ListItem
from reportlab.pdfbase.pdfmetrics import stringWidth

from .common import ROOT, read_json
from .knowledge_validation import CATALOGUES

LABELS = {
    "material_class": "Material class",
    "properties": "Properties",
    "production_methods": "Production methods",
    "applications": "Applications",
    "hazards": "Hazards",
    "environmental_considerations": "Environmental considerations",
    "scientific_name": "Scientific name",
    "common_names": "Common names",
    "identification": "Identification",
    "habitat_ecology": "Habitat & ecology",
    "distribution": "Distribution",
    "ecological_role": "Ecological role",
    "uses": "Documented uses (reviewed)",
    "toxicity_or_lookalikes": "Toxicity & look-alikes",
    "conservation_notes": "Conservation notes",
    "food_use_status": "Food-use status",
    "crop_name": "Crop",
    "variety_or_cultivar": "Variety / cultivar",
    "regional_applicability": "Regional applicability",
    "climate": "Climate",
    "soil": "Soil",
    "propagation": "Propagation",
    "planting": "Planting",
    "water_management": "Water management",
    "nutrient_management": "Nutrient management",
    "pest_disease_management": "Pest & disease management",
    "harvest": "Harvest",
    "storage": "Storage",
    "failure_modes": "Failure modes",
    "safety_notes": "Safety notes",
    "materials": "Materials",
    "tools": "Tools",
    "prerequisites": "Prerequisites",
    "steps": "Procedure",
    "measurements": "Measurements (source-stated)",
    "expected_result": "Expected result",
}


def _plain(value):
    if isinstance(value, list):
        return "; ".join(_plain(item) for item in value)
    if isinstance(value, dict):
        return "; ".join(f"{key}: {_plain(item)}" for key, item in value.items())
    return str(value)


def build_catalogue_pdf(filename: str, output: Path):
    spec = CATALOGUES[filename]
    payload = read_json(ROOT / "data" / filename, {spec["key"]: []})
    records = [
        row for row in payload.get(spec["key"], [])
        if row.get("verification", {}).get("status") == "approved"
    ]
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CatalogTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=19, leading=23))
    styles.add(ParagraphStyle(name="CatalogHeading", parent=styles["Heading2"], spaceBefore=8, spaceAfter=5))
    styles.add(ParagraphStyle(name="CatalogBody", parent=styles["BodyText"], leading=14, spaceAfter=4))
    styles.add(ParagraphStyle(name="CatalogSmall", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.darkgrey))
    story = [
        Paragraph(escape(filename.replace(".json", "").replace("_", " ").title()), styles["CatalogTitle"]),
        Spacer(1, 4 * mm),
        Paragraph("Survival-TIPS · Phase 3 Technical Knowledge", styles["CatalogSmall"]),
        Paragraph(f"Human-approved records: {len(records)}", styles["CatalogSmall"]),
        Spacer(1, 6 * mm),
    ]
    if not records:
        story.append(Paragraph("No human-approved records are available yet. Candidate and unreviewed records are intentionally excluded.", styles["CatalogBody"]))
    for index, record in enumerate(records):
        story.append(Paragraph(escape(record.get("title", "Untitled")), styles["CatalogHeading"]))
        story.append(Paragraph(escape(record.get("summary", "")), styles["CatalogBody"]))
        for field, value in record.items():
            if field in {"id", "title", "summary", "sources", "evidence", "verification", "stage_ids", "generated_at"}:
                continue
            if value in (None, "", []):
                continue
            label = LABELS.get(field, field.replace("_", " ").title())
            story.append(Paragraph(f"<b>{escape(label)}:</b> {escape(_plain(value))}", styles["CatalogBody"]))
        story.append(Paragraph(
            f"Reviewed by: {escape(str(record['verification'].get('reviewed_by', '')))} · "
            f"Reviewed at: {escape(str(record['verification'].get('reviewed_at', '')))}",
            styles["CatalogSmall"]
        ))
        for source in record.get("sources", []):
            url = source.get("url", "")
            if url.startswith(("https://", "http://")):
                story.append(Paragraph(f"Source: <link href=\"{escape(url)}\" color=\"blue\">{escape(url)}</link>", styles["CatalogSmall"]))
        story.append(Spacer(1, 5 * mm))
        if index < len(records) - 1:
            story.append(PageBreak())

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    doc.build(story)
    print(f"[knowledge-pdf] {output}: {len(records)} approved record(s)")


def main():
    parser = argparse.ArgumentParser(description="Export only human-approved Phase 3 knowledge records.")
    parser.add_argument("--output-dir", default=str(ROOT / "docs" / "knowledge-pdf"))
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    for filename in CATALOGUES:
        build_catalogue_pdf(filename, output_dir / filename.replace(".json", ".pdf"))


if __name__ == "__main__":
    main()
