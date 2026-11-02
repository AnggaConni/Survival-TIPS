# Survival-TIPS — Field Knowledge Intelligence System

Survival-TIPS is a static, JSON-first survival and resilience knowledge library. JSON is the source of truth; the browser reads the manifest, merges the configured catalogues, classifies records into thematic filters, and displays a live coverage/gap dashboard.

## Publishing content

1. Add or edit a JSON file in `data/`.
2. Add the file path to `data/index.json` under `files`.
3. Put images in `thumb/` or another static directory and reference them in article image objects, e.g. `thumb/galon.png`.
4. Commit and push. When the static site is published, the browser reads the new JSON.
5. The homepage dashboard recalculates theme counts and the thematic map identifies missing subject areas.

No crawler, AI extraction, autonomous approval, scheduled collection, or push-triggered PDF generation is used. GitHub Pages may publish the static site if configured; that is hosting, not content generation.

## How the reader works

The approach is adapted from a multi-JSON Node.js reader: multiple files are loaded, their collections merged, categories/themes derived from data, and records rendered as cards. A browser cannot list repository directories by itself, so `data/index.json` is the explicit manifest.

Thematic assignment uses:
- `stage_ids` / `stages` (preferred, explicit classification)
- `category`, `type`, tags and text keywords (automatic fallback)
- `dataset` metadata from the manifest (e.g. species records map to biodiversity)

The filter facets for `environment`, `climate` and `season` are populated from values actually present in the JSON.

## Manifest example

```json
{
  "schema_version": "2.1",
  "files": [
    {"path": "data/water.json", "dataset": "water", "kind": "content"},
    {"path": "data/agriculture.json", "dataset": "agriculture", "kind": "content"},
    {"path": "data/species.json", "dataset": "species", "kind": "evidence"}
  ],
  "reference_files": [
    {"path": "data/sources.json", "dataset": "sources"}
  ]
}
```

## Article model

```json
{
  "id": "WAT-010",
  "title": "Emergency Water Storage",
  "category": "water_storage",
  "stage_ids": ["03-water-sanitation"],
  "status": "review_required",
  "summary": "Short article summary.",
  "body": "Full article text.",
  "environment": ["urban", "coastal"],
  "climate": ["tropical"],
  "season": ["rainy", "dry"],
  "materials": ["Food-grade container"],
  "tools": ["Funnel"],
  "steps": ["Step one", "Step two"],
  "safety": ["Safety warning"],
  "limitations": ["Known limitation"],
  "images": [
    {"url": "thumb/galon.png", "alt": "Water gallon", "caption": "Storage container"},
    {"url": "thumb/jerrycan.png", "alt": "Portable water container"}
  ],
  "sources": [
    {"title": "Public-health authority", "url": "https://example.org/guidance"}
  ],
  "review": {"status": "review_required", "reviewed_by": null, "reviewed_at": null}
}
```

## Theme taxonomy

| Theme ID | Domain |
|---|---|
| 01-drr | Disaster Risk & Response |
| 02-biodiversity | Biodiversity & Ecology |
| 03-water-sanitation | Water & Sanitation |
| 04-agriculture | Agriculture & Food Production |
| 05-energy | Energy & Power |
| 06-materials | Shelter & Materials |
| 07-manufacturing | Tools & Manufacturing |
| 08-infrastructure | Infrastructure & Logistics |

Use `stage_ids` to classify a record reliably. Keyword classification is a convenience fallback and should not replace explicit tags for important content.

## Coverage dashboard

The homepage displays loaded record counts, reference-source count, species records, and review-needed records. The thematic map compares current records with an initial editorial checklist. This is a heuristic inventory, not a validated assessment of real-world preparedness or technical completeness.

## Images and exports

- Multiple image objects per article are supported.
- Use relative repository paths and include alt text, caption and licence/credit where relevant.
- PDF: open an article → Print / PDF → browser print dialog → Save as PDF.
- Word: open an article → Word .doc. This is Word-compatible HTML in a `.doc` wrapper, not a native `.docx`.

## Safety and quality

Editorial status is not a safety certification. Water treatment, food safety, toxicology, first aid, chemical handling and engineering instructions require authoritative sources and domain review. Species occurrence records and photographs do not prove edibility, medicinal use or safe handling.
