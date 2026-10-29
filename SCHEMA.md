# Data JSON contracts
- `data/sources.json`: `schema_version`, `generated_at`, `sources[]` with title, canonical URL, domain, extracted text, short snippet, discovery type, retrieval time and discovery metadata.
- `data/tips.json`: `tips[]` with stable ID, category, summary, steps, warnings, short evidence excerpt, source URL, AI provider, retrieval date and `verification.status=needs_review` until human review.
- `data/species.json`: `species[]` with GBIF taxon/occurrence keys, image path, original media URL, explicit media license, creator/publisher attribution, GBIF record URL and review status.
