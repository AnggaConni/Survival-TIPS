# Survival-TIPS — JSON-first Field Knowledge Library

A static, modular survival and resilience knowledge library. **JSON files are the source of truth.** The browser reads catalogues from `data/index.json`, renders articles, images and references, and offers on-demand document exports.

## Publishing workflow

1. Add or edit a JSON content file in `data/`.
2. Add its path to `data/index.json`.
3. Put images in static folders such as `thumb/` and reference them with paths such as `thumb/galon.png`.
4. Commit and push. Once the static site is published, the new JSON appears in the library.
5. Open an article in JSON Explorer and export it to Word or print-to-PDF.

No crawler, AI extraction, autonomous approval, scheduled collection, push-triggered tests or push-triggered PDF generation runs. GitHub Pages may still publish the static website if enabled; that only hosts the files.

## Article JSON model

```json
{
  "schema_version": "2.0",
  "catalogue": "water-survival",
  "title": "Water Survival & Purification",
  "articles": [{
    "id": "WAT-001",
    "title": "Emergency Water Storage at Home",
    "category": "water_storage",
    "stage_ids": ["01-drr", "03-water-sanitation"],
    "status": "review_required",
    "summary": "Short summary.",
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
      {"url": "thumb/galon.png", "alt": "Sealed water gallon", "caption": "Water storage", "role": "hero"},
      {"url": "thumb/water-jerrycan.png", "alt": "Portable water container"}
    ],
    "sources": [{"title": "Public-health authority", "url": "https://example.org/"}],
    "review": {"status": "review_required", "reviewed_by": null, "reviewed_at": null}
  }]
}
```

## Add a catalogue

Create `data/food.json` with a top-level `articles` array, then add an entry to `data/index.json`:
```json
{"path":"data/food.json","dataset":"approved"}
```

The `dataset` property is a grouping label for the explorer. Each article's own `status` and `review` fields remain visible. Do not mark safety-critical content approved until its evidence has been reviewed.

## Images

- Store images in `thumb/`, `images/` or another static folder.
- Use repository-relative paths; do not use paths on your local computer.
- Multiple image objects per article are supported.
- Include `alt`, captions and attribution/licence details where appropriate.
- Confirm rights for redistribution before committing images.

## Export

- **PDF:** Open an article → Print / Save PDF → browser print dialog → Save as PDF.
- **Word:** Open an article → Download Word. This produces a Word-compatible `.doc` HTML file.
- These are on-demand browser exports, not committed binary files. A true `.docx` generator would require a separate explicitly invoked toolchain.

## Quality and safety

A JSON status is editorial metadata, not a safety certification. Keep unverified records marked `review_required`. Water treatment, food safety, toxicology, first aid, chemical handling and engineering instructions require authoritative sources and domain review.

## Repository structure

- `data/index.json` — catalogue manifest.
- `data/*.json` — structured content.
- `thumb/` — article images.
- `assets/js/app.js` — JSON reader, search, article viewer and exports.
- `assets/css/site.css` — Macintosh-inspired interface.
- `dashboard.html` — topic browser.
- `data-explorer.html` — JSON explorer.
- `pdf-library.html` — export desk.
