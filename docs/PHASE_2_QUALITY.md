# Phase 2 — evidence quality, deduplication, conflicts, and versioning

## Source quality triage

Each stored source receives a transparent heuristic assessment in `quality_assessment`:

- authority tier based on the host domain;
- document type inferred from title terms;
- technical-depth estimate based on text length and vocabulary;
- publication/last-updated date only when an explicit date is found in the page text;
- jurisdiction remains `not_stated` unless the source itself states it;
- a score with visible components and a short rationale.

These fields prioritize human review; they do **not** certify that a source is accurate, current, unbiased, applicable in Indonesia, or safe. Heuristic assessments remain marked `needs_human_review`.

## Duplicate and contradiction screening

`python -m scripts.audit_tips` and `python -m scripts.audit_tips --candidates` now emit:

- exact and near-duplicate title/summary signals;
- possible conflict signals from opposite terms or differing explicit numeric values on overlapping topics;
- a machine-readable `data/quality_report.json`.

Similarity is not proof that two tips are duplicates. Lexical opposition or different numbers are not proof of a factual contradiction: contexts, units, populations, climate, jurisdiction, and source dates may differ. Review the original sources and retain both items when the apparent disagreement is explainable.

## Source version history

Source text is hashed after whitespace normalization. Each source records a version number, content hash, first-seen time, last-checked time, and last content-change time. The collector rechecks sources after `SOURCE_REFRESH_DAYS` (default 30). Changed text creates an event in `data/source_versions.json`; unchanged text updates the check timestamp without incrementing the version.

This records changes in the extracted page text, not a complete archival copy of every historic page. The source page may change between checks. Set `SOURCE_REFRESH_DAYS` to change the default 30-day refresh interval.

## Extraction and stage classification versions

New tips record `prompt_version`, `extractor_version`, source version, and source content hash. Legacy tips are marked `legacy_unversioned`; their historic prompts cannot be reconstructed. To deliberately rerun the current extractor on previously processed sources, use `python -m scripts.extract_tips --reprocess --limit 5`. This replaces only candidate entries for a source when the new extraction returns candidates; if no candidates are returned, existing candidates are preserved. Active, quarantined, and approved records are never rewritten by this command.

Stage classification records the suggested IDs, method, reason, and review status. The reviewer may supply `stage_ids` and `stage_review_notes` in the approval decision. Approved entries must have a human-reviewed stage assignment, reviewer, and timestamp. The keyword/category classifier remains a suggestion engine, not a semantic authority.

## Local commands

```bash
python -m scripts.enrich_sources
python -m scripts.audit_tips
python -m scripts.audit_tips --candidates
python -m scripts.validate_data
python -m pytest -q
```

Do not automatically approve, delete, or rewrite a tip based only on a duplicate/conflict signal or a source score.
