# Human review and publication workflow

AI extraction and automated audits produce **candidates**, not verified advice. Nothing is published merely because it passes an automated check.

## Review sequence

1. Open the original source page and read the relevant surrounding section, not only the saved excerpt.
2. Check the tip's claim, audience, jurisdiction, date, practical completeness, limitations, and safety implications.
3. For every step, identify a verbatim excerpt in one of the tip's stored sources that supports that specific instruction. If a step is not supported, revise or remove it before approval; do not stretch an excerpt to justify unrelated instructions.
4. Add a decision to `data/review_decisions.json`.
5. Run `python -m scripts.review_tips --apply`, then `python -m scripts.validate_data`.
6. Generate PDFs with `python -m scripts.export_pdfs --all`. Only approved entries in `data/approved_tips.json` can appear.

## Decision format

The `step_reviews` array must have exactly one entry per step, in the same order. The source URL must already be listed under the tip's `sources`; the excerpt must occur verbatim in the stored source text.

```json
{
  "schema_version": "1.0",
  "decisions": [
    {
      "tip_id": "tip-example",
      "decision": "approve",
      "reviewer": "Reviewer name or role",
      "reviewed_at": "2026-10-30T09:00:00+07:00",
      "notes": "Read the source in context; checked scope, limitations, and local applicability.",
      "step_reviews": [
        {
          "evidence_excerpt": "Exact sentence copied from the stored source text.",
          "source_url": "https://example.org/technical-guide"
        }
      ]
    }
  ]
}
```

Do not copy this example as an approval. Replace the ID, reviewer, notes, and evidence with a real completed review. The command validates that each excerpt exists verbatim in the stored source and that the URL belongs to the tip; a human must still judge whether the evidence genuinely supports the instruction and whether the advice is safe and applicable.

## Publication rule

Approval records include reviewer, timestamp, notes, and evidence for every step. The generated PDFs show the review attribution, step evidence, and clickable source links. Keep the publication dataset empty when no item has completed review. A passing test or exact text match is not a scientific, legal, or safety certification.
