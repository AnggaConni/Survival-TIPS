# Phase 3 — Technical Knowledge

Phase 3 establishes four source-traceable knowledge catalogues:

1. **Recipes** — reproducible build, make, repair, and maintenance procedures.
2. **Materials** — material classes, properties, production methods, applications, hazards, and environmental considerations.
3. **Biodiversity profiles** — taxonomy, identification, habitat, distribution, ecological role, documented uses, look-alikes, and conservation notes.
4. **Agriculture profiles** — crop identity, regional applicability, propagation, planting, water and nutrient management, pest/disease management, harvest, storage, and failure modes.

## Data boundaries

The catalogues are deliberately separate from the GBIF occurrence/image dataset. A GBIF record or photograph is evidence that an observation was recorded; it is not evidence of edibility, medicinal efficacy, toxicity, or practical use.

The initial catalogue files are empty by design. No example or synthetic knowledge record is published as factual content. A record should be added only after a source has been collected and its relevant text is available in `data/sources.json`.

## Evidence model

Each technical record has:
- a stable `id`, title, summary, and one or more valid `stage_ids`;
- one or more source references that resolve to stored source records;
- field-level `evidence` entries with `field`, `source_url`, and an exact excerpt copied from stored source text;
- a `verification.status` of `needs_review` until a human reviewer has actually reviewed it.

The validator checks source linkage, stage IDs, field-level verbatim evidence, required domain fields, and reviewer metadata for approved records. Exact text matching is a mechanical traceability check, not proof that the excerpt supports the claim in context.

## Domain safeguards

### Recipes
A procedure must preserve source-stated materials, tools, prerequisites, steps, measurements, expected result, failure modes, and safety notes. Do not invent missing quantities, temperatures, tolerances, or steps. Missing information stays missing and limits reproducibility.

### Materials
Properties and manufacturing methods must be source-backed. Hazards and environmental considerations are separate fields; an application claim does not establish that a material is safe to handle or produce.

### Biodiversity
Taxonomic identity, identification traits, habitat, distribution, and ecological context must be sourced. The catalogue does not permit blanket fields such as `safe_to_eat`, `edible_certified`, or `medicinally_safe`. Food-use status defaults to `not_assessed`; a source mention is not a safety certification. Documented uses require an explicit expert-review status.

### Agriculture
Cultivation guidance must retain its stated climate, soil, variety, region, season, and other applicability limits. Do not generalize a technique to all climates or cultivars when the source is narrower.

## Validation

Run:

```powershell
python -m scripts.knowledge_validation
python -m pytest -q
python -m scripts.validate_data
```

The main test workflow runs the technical catalogue validator. The catalogues start empty and will grow only through source-backed research and human review.
