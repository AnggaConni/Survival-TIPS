# JSON schema overview

## data/sources.json
Root fields: `schema_version`, `generated_at`, `sources[]`.

Each source stores a stable ID, canonical URL, title, domain, extracted readable text, short search/RSS snippet, source type, retrieval time, and discovery metadata. Source text is retained for later extraction; review site terms before public redistribution.

## data/tips.json
Root fields: `schema_version`, `generated_at`, `tips[]`.

Each candidate tip stores: `id`, `title`, `category`, `summary`, `steps[]`, `warnings[]`, short `evidence_excerpt`, source URL/domain, retrieval timestamp, AI provider, and verification status. AI-generated content starts at `needs_review`.

## data/species.json
Root fields: `schema_version`, `generated_at`, `species[]`.

Each image record stores scientific/common names when present, GBIF occurrence/taxon keys, country/locality metadata, image file path, original image URL, license, creator/publisher/rights-holder attribution, GBIF record URL, review state, and an explicit statement that GBIF observation data does not establish edibility or safety.
