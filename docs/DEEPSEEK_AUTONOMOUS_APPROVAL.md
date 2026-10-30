# DeepSeek autonomous approval policy

## What can be published automatically?

The collector runs `python -m scripts.autonomous_approval` after the candidate audit. DeepSeek is an independent reviewer, not an unrestricted publisher.

Automatic publication is deliberately limited to:
- `content_type`: `plan`, `planning_guidance`, or `communication_guidance`
- `category`: `planning` or `communication`
- a referenced source with stored text and an A/B authority tier plus a heuristic quality score of at least 60
- DeepSeek decision `approve`, risk `low`, confidence at least 0.90
- one exact, contiguous, source-verbatim excerpt for every actionable step
- valid configured stage IDs and a non-empty explanation
- no duplicate/conflict triage signal and no deterministic safety-sensitive wording

Only five candidates are sent to DeepSeek per collection run by default. Override locally with `python -m scripts.autonomous_approval --limit N`. This cap helps control API usage.

## What must remain manual?

Food and wild-species use/identification, water treatment, first aid, health, sanitation, chemicals, electricity, combustion, construction, tools, agriculture, and other operational safety advice are not eligible for autonomous approval. The script also defers candidates with weak source metadata, missing source text, duplicate/conflict signals, invalid quotations, uncertain decisions, low confidence, or API errors.

The deterministic risk checks are intentionally conservative but are not a complete hazard classifier. Human review remains necessary for all high-risk content.

## Publication and audit trail

- AI-approved records are labelled `quality_status = ai_verified`, `verification.review_type = automated_low_risk_only`, and `stage_classification.review_status = ai_reviewed`.
- Human-approved records retain their existing `human_verified` and `human_reviewed` labels.
- Candidates are removed from the queue only when all gates pass and the approved record is written.
- Deferred candidates stay in `data/candidate_tips.json`.
- Each decision is appended to `data/autonomous_review_log.json`, including the model, prompt version, decision, confidence, reason, and evidence quotes where applicable.
- PDFs continue to be generated only from `data/approved_tips.json`.

A verbatim quote only proves that the text exists in the stored source. It does not independently prove that the source is correct, that advice is safe in every location, or that every operational detail is complete. The autonomous path is restricted accordingly.
