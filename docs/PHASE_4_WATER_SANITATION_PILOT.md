# Phase 4 — Water & Sanitation Pilot

## Purpose

Use the Water & Sanitation stage as the first end-to-end pilot for evidence-backed knowledge development. The pilot tests the existing source collection, candidate extraction, review, technical catalogue, validation, and publication process before it is expanded to the other seven civilization stages.

This phase does not lower existing evidence or safety requirements. It does not publish operational instructions merely because an AI model generated them.

## Existing baseline

- The technical knowledge catalogues are intentionally empty until source-backed records are researched and reviewed.
- The repository already contains water-related source material, including a CDC drinking-water advisory communications toolkit. This is useful for public communication and incident coordination, but it is not a substitute for technical guidance on treatment, testing, or sanitation.
- Existing tips and candidates remain subject to their current review status. Do not silently promote them as part of this pilot.
- GBIF occurrence data must not be used to infer water safety, edibility, or medicinal use.

Re-run the repository validators and inspect the current data files before each collection/review cycle; counts can change as the repository evolves.

## Pilot scope

1. **Water preparedness and assessment** — emergency planning, demand estimation, recognizing/reporting suspected contamination, and limits of visual/taste/odor observations.
2. **Water sourcing and collection** — source selection, local contamination risks, rainwater collection, and protecting collection points.
3. **Water treatment and testing** — officially documented methods and limitations, testing interpretation, escalation, and contaminant-specific warnings.
4. **Safe storage and distribution** — container selection, cleaning, covering, labeling, handling, and preventing recontamination.
5. **Hygiene and sanitation** — hand/household hygiene, excreta and wastewater management, menstrual hygiene, and accessible sanitation.
6. **Public-health communication** — boil-water / do-not-drink / do-not-use advisory distinctions, accessible messages, translation, and trusted local channels.

## Source strategy

Prioritize primary and authoritative sources:

- WHO drinking-water quality and emergency WASH guidance.
- UNICEF emergency WASH technical guidance.
- Sphere Handbook WASH standards.
- National and local public-health, water utility, disaster-management, and environmental-health authorities.
- Peer-reviewed technical literature only where official operational guidance is unavailable or where it provides essential supporting evidence.

For every collected source, retain its canonical URL, publisher, document type, publication/update date where available, jurisdiction, retrieval date, and the exact extracted text used as evidence. Prefer current primary sources over secondary summaries. Record geographic, climate, infrastructure, population, and incident-specific limits.

## Risk and review policy

The following topics are high-risk and must remain in the human-review queue. They are not eligible for autonomous approval:

- Water disinfection, dosing, treatment, and chemical handling.
- Water testing and interpretation that could affect a health decision.
- Suspected chemical, industrial, radiological, or biological contamination.
- Sewage, fecal sludge, wastewater, and pathogen exposure.
- Advice for infants, immunocompromised people, or other vulnerable groups.

AI may help discover sources, extract candidate claims, map evidence, and identify missing context. It must not certify water as potable or safe. Never infer safety from clear appearance, taste, smell, a single indicator, or an unverified field observation.

Where a source does not specify a dose, contact time, temperature, equipment, test threshold, or limitation, do not invent one. Preserve uncertainty and refer users to local public-health or water authorities when appropriate.

## Data model and publication

Use the existing repository schemas and review workflow:

- data/sources.json for source metadata and stored source text.
- data/tips.json and data/candidate_tips.json for tip records and review queues.
- data/recipes.json only for genuinely reproducible procedures with source-backed prerequisites, materials, tools, steps, measurements, expected results, failure modes, and safety notes.
- data/materials.json for materials and their documented properties, applications, hazards, and environmental considerations.

Do not create a recipe merely to fill a catalogue. A procedure with missing quantities or critical steps must remain incomplete and must not be presented as reproducible. Every technical record must use field-level evidence linked to stored source text. Exact excerpt matching is a traceability check, not proof of correctness. Human reviewers must check the source in context and assess applicability.

Only records that pass the existing review and validation workflow may be included in approved exports. High-risk water and sanitation records require human review even if an AI reviewer expresses high confidence.

## Pilot workflow

1. Run the current validators and inventory existing Water & Sanitation sources, tips, candidates, and catalogue records.
2. Build a topic-to-source coverage matrix and identify evidence gaps.
3. Collect a small, diverse set of authoritative sources for the scoped domains.
4. Extract a limited batch of candidate records with exact source excerpts.
5. Audit source authority, recency, jurisdiction, evidence fit, duplicate/conflict signals, and risk classification.
6. Human-review candidates and technical records; keep unsupported or ambiguous records quarantined.
7. Run tests, data validation, knowledge validation, and approved-only PDF export.
8. Review pilot quality and revise the workflow before expanding to other stages.

## Pilot success criteria

- Each in-scope domain has an explicit coverage status: covered, partial, or gap.
- Every candidate links to a stored source and exact excerpt.
- No record is marked approved without the required review metadata.
- No high-risk water/sanitation record is autonomously approved.
- No invented dose, threshold, treatment claim, or universal safety claim is introduced.
- Duplicate/conflict checks and all existing validators pass.
- Published exports contain approved records only.
- The team can identify remaining evidence gaps and the next source-collection priorities.

## Out of scope

- Automatically certifying water as safe to drink.
- Replacing local water-quality authorities, laboratories, or public-health instructions.
- Publishing unreviewed treatment, disinfection, or sanitation procedures.
- Filling empty catalogues with synthetic examples.
- Expanding all eight stages before the Water & Sanitation pilot has been evaluated.
