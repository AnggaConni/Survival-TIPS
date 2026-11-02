# JSON Catalogue Schema (v2.1)

Every catalogue is UTF-8 JSON and is listed in `data/index.json`.

## Manifest

- `files[]`: content/evidence JSON files with `path`, `dataset`, and optional `kind`.
- `reference_files[]`: reference collections kept separate from practical article cards.
- A browser cannot list repository directories, so the manifest is the explicit index.

## Article fields

Required/recommended:
- `id`, `title`, `status`
- `category`, `stage_ids`, `tags`
- `summary`, `body`
- `environment[]`, `climate[]`, `season[]`
- `materials[]`, `tools[]`, `steps[]`
- `safety[]`, `limitations[]`, `sources[]`, `review{}`

## Automatic thematic assignment

Use `stage_ids` as the authoritative taxonomy link. The browser also checks category, type, tags and text keywords as a fallback. Available themes:

1. `01-drr` — Disaster Risk & Response
2. `02-biodiversity` — Biodiversity & Ecology
3. `03-water-sanitation` — Water & Sanitation
4. `04-agriculture` — Agriculture & Food Production
5. `05-energy` — Energy & Power
6. `06-materials` — Shelter & Materials
7. `07-manufacturing` — Tools & Manufacturing
8. `08-infrastructure` — Infrastructure & Logistics

Filters for environment, climate and season are generated from the values found in the loaded JSON.

## Images

`images[]` accepts objects with `url`, `alt`, `caption`, `credit`, and `role`. Example: `{"url":"thumb/galon.png","alt":"Water gallon","caption":"Emergency water storage"}`.

## Review status

Use values such as `review_required`, `needs_review`, and `approved`. The status is editorial metadata, not a safety certification.
