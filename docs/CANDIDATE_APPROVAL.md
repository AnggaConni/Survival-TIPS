# Candidate review and approval

AI-generated entries remain unpublished candidates until a human reviewer checks the original source in context and confirms every actionable step.

## Local review helper

List the current queue:

```powershell
python -m scripts.approve_candidates --list
```

Create a decision template for one or more candidate IDs:

```powershell
python -m scripts.approve_candidates --template tip-id-1 tip-id-2
```

Copy the generated JSON into a file, then replace every placeholder. For every step, provide one exact excerpt copied from the stored text of one of that tip's own sources. Confirm the stage assignment and write meaningful reviewer notes.

Apply locally:

```powershell
python -m scripts.approve_candidates --apply --decisions-file path\to\completed-decisions.json
python -m scripts.validate_data
python -m pytest -q
python -m scripts.export_pdfs --all
```

## GitHub Actions review

1. Open **Actions → Review and approve candidate tips → Run workflow**.
2. Paste the completed JSON object into the `decisions_json` input.
3. Run the workflow and inspect its validation and test results.

The action checks that every selected ID exists in `data/candidate_tips.json`, requires reviewer metadata and one source-verbatim evidence excerpt per step, checks stage IDs, runs the complete data validation and test suite, regenerates the PDFs, and commits the publication dataset plus the reduced candidate queue to `main`.

## Safety and audit guarantees

- This workflow is candidate-only; it cannot approve entries from the legacy `tips.json` review backlog.
- A candidate is removed from `candidate_tips.json` only after all approval checks pass and it is present in `approved_tips.json`.
- Existing approved entries are not duplicated on reruns.
- The GitHub Action persists the submitted decision manifest to `data/review_decisions.json` and commits it alongside the publication changes, preserving reviewer attribution and evidence for later audit.
- Exact text matching is a mechanical check, not a judgment that the evidence truly supports the instruction. The reviewer must read the source in context and assess scope, local applicability, completeness, and safety.
- Only `data/approved_tips.json` is used by PDF export.
