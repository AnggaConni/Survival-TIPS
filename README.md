# Survival-TIPS — Survival Knowledge Collector

Python-first, source-linked survival knowledge base inspired by rebuilding civilization from first principles.

**Current phase:** source collection, eight-stage knowledge taxonomy, stage filters, and automatic offline PDF export. Frontend remains a later phase.

## Knowledge stages

Each stage is a separate filter and can be exported as its own handbook:

1. **Disaster Risk Reduction (DRR)** — preparedness, first aid, evacuation, shelter, communication.
2. **Biodiversity & Survival Ecology** — species, ecosystems, useful plants, and safe identification.
3. **Water & Sanitation** — water collection and treatment, sanitation, wastewater.
4. **Agriculture & Food Systems** — crops, seeds, soil, irrigation, food preservation.
5. **Energy & Mechanics** — generators, motors, solar, wind, micro-hydro, storage.
6. **Materials & Construction** — clay, brick, lime, shells, mortar, concrete, glass, polymers.
7. **Tools, Chemistry & Manufacturing** — toolmaking, metalworking, chemistry basics, repair.
8. **Infrastructure & Civilization** — community systems, communications, public health, logistics.

Stage definitions live in `config/stages.json`. Tips receive `stage_ids`; the shared classifier in `scripts/stages.py` powers stage filters and PDF exports. A cross-cutting entry may appear in more than one stage.

## Automated data → PDF flow

The intended flow is:

1. The scraper discovers and fetches sources.
2. AI extraction saves source-linked candidate entries to `data/*.json`.
3. The collection workflow validates the JSON and generates all eight PDFs during the same run.
4. A separate `.github/workflows/generate-pdfs.yml` workflow also runs on pushes that change JSON data or the stage/PDF generator files. This covers manual data edits and commits made outside the collection workflow.
5. Generated handbooks are committed to `docs/pdf/`.

**GitHub Actions detail:** commits pushed using GitHub Actions' default `GITHUB_TOKEN` do not normally trigger another `push` workflow. That's why the collection workflow itself also generates PDFs before committing its data and PDF outputs. The separate push-triggered workflow is for direct pushes and other qualifying changes, not the only path for PDF generation.

## Repository layout

- `config/sources.json` — search queries, trusted domains, RSS feeds, GBIF taxon queries.
- `config/stages.json` — stage catalogue, order, descriptions, category and keyword rules.
- `scripts/collect_sources.py` — search, RSS, article fetching.
- `scripts/extract_tips.py` — evidence-first AI extraction with Groq → DeepSeek → OpenRouter fallback; rejects tips whose evidence excerpt is not verbatim in stored source text or that have no practical steps.
- `scripts/audit_tips.py` — deterministic quality audit for missing fields, unsupported evidence, generic advice, duplicate titles, and stage mismatches; optional AI re-extraction repair.
- `scripts/stages.py` — shared stage classification and filtering.
- `scripts/export_pdfs.py` — creates a separate PDF for each stage.
- `scripts/collect_gbif.py` — GBIF occurrence records and license-gated image downloads.
- `scripts/run_pipeline.py` — data collection orchestrator.
- `scripts/validate_data.py` — data-integrity checks.
- `data/sources.json`, `data/tips.json`, `data/species.json` — collected records.
- `docs/pdf/` — generated stage handbooks.
- `.github/workflows/collect-data.yml` — manual and weekly scraper pipeline.
- `.github/workflows/generate-pdfs.yml` — PDF regeneration on qualifying pushes.

## Generate PDFs locally

Install dependencies first:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Generate all eight stage PDFs:

```powershell
python -m scripts.export_pdfs --all
```

Generate just one stage:

```powershell
python -m scripts.export_pdfs --stage 03-water-sanitation
```

PDFs are written to `docs/pdf/` by default. You can set a custom folder with `--output-dir path/to/folder`. A PDF is generated even when a stage has no collected tips yet, so the handbook structure is ready to grow offline.

## Run the data collector (Windows PowerShell)

Copy `.env.example` to `.env`, add your keys locally, and never commit `.env`.

```powershell
python -m scripts.run_pipeline --limit 8 --gbif-limit 3
python -m scripts.audit_tips
python -m scripts.audit_tips --repair
python -m scripts.validate_data
python -m scripts.export_pdfs --all
python -m pytest -q
```

GitHub Actions can run the pipeline manually: Actions → **Collect survival data** → Run workflow. The workflow audits tip quality each run. Enable the `repair_tips` input to re-extract flagged source pages with the configured AI providers (this may consume API credits). Repair replaces existing tips from a source only when new candidates pass evidence/step validation; if no replacement passes, existing data is kept. The pipeline exports and commits stage PDFs alongside updated JSON and licensed assets.

The extractor falls back from Groq to DeepSeek to OpenRouter when a provider errors or all its candidate tips fail local validation. A valid empty response is treated as the model finding no sufficiently supported tips, not as an API failure. The audit is a screening aid, not a substitute for human review.

## GitHub Actions secrets

Configure repository secrets in **Settings → Secrets and variables → Actions → Repository secrets**:

- `GROQ_API_KEY`
- `DEEPSEEK_API_KEY`
- `OPENROUTER_API_KEY`

Optional: `TAVILY_API_KEY` for dedicated web search. Model overrides may be configured as Actions variables (`GROQ_MODEL`, `DEEPSEEK_MODEL`, `OPENROUTER_MODEL`). Safe defaults are used when model variables are empty.

## Quality and safety

- AI-extracted content is a candidate, not verified advice. New tips start at `verification.status = "needs_review"`.
- Each tip should preserve source URLs and review status in the PDF.
- Search results are discovery leads, not proof of trustworthiness. Curated/trusted domains are prioritized.
- GBIF occurrence records and photos do not establish that a species is edible, medicinal, non-toxic, or suitable for survival.
- Images are downloaded only when license metadata explicitly permits redistribution (CC0/public domain, CC BY, or CC BY-SA); attribution is retained.
- Site terms and robots rules still apply. The collector avoids copying whole articles into tips.
- Practical content involving drinking water, wild foods, chemicals, electricity, lime kilns, or construction must be reviewed for local conditions and safety before being treated as instructions.

## Download the eight stage handbooks

The latest generated PDFs are stored in [`docs/pdf/`](docs/pdf/). Click a handbook to download or read it online:

1. [`01-drr.pdf` — Disaster Risk Reduction](docs/pdf/01-drr.pdf)
2. [`02-biodiversity.pdf` — Biodiversity & Survival Ecology](docs/pdf/02-biodiversity.pdf)
3. [`03-water-sanitation.pdf` — Water & Sanitation](docs/pdf/03-water-sanitation.pdf)
4. [`04-agriculture.pdf` — Agriculture & Food Systems](docs/pdf/04-agriculture.pdf)
5. [`05-energy.pdf` — Energy & Mechanics](docs/pdf/05-energy.pdf)
6. [`06-materials.pdf` — Materials & Construction](docs/pdf/06-materials.pdf)
7. [`07-manufacturing.pdf` — Tools, Chemistry & Manufacturing](docs/pdf/07-manufacturing.pdf)
8. [`08-infrastructure.pdf` — Infrastructure & Civilization](docs/pdf/08-infrastructure.pdf)

## Is the data accurate? What can be eaten or made?

**Treat the current corpus as a research collection, not a field-verified survival manual.** Every stored tip is currently marked `needs_review`. The AI's `confidence` field expresses the model's estimate of how directly the source supports a tip; it is not independent verification that the advice is true, safe, locally applicable, or complete.

A review of the current `data/tips.json` snapshot found **40 tips, all `needs_review`**. Some have useful water, sanitation, emergency-shelter, preparedness, and home-gardening content. However, a number of entries focus on communicating public advisories or applying humanitarian guidance rather than giving a direct, reproducible survival procedure. Eight tips also have no assigned stage in this snapshot. The dataset is still small and uneven: categories such as `other` dominate, while several stages have no or very little content. Do not infer that a stage PDF is complete just because the file exists.

### Can I eat it?

Use the **Biodiversity & Survival Ecology** and **Agriculture & Food Systems** sections to investigate species, food production, and preservation. In the current snapshot, there is no sufficient basis to treat the corpus as a reliable wild-food identification guide. A species record, photograph, AI-generated description, or keyword match is **not** proof that a plant, mushroom, or animal is edible. Do not eat an unidentified wild organism on the strength of this repository; some toxic species look very similar to edible ones, and safe identification can depend on location and plant part.

Useful food-related knowledge should be specific and source-backed: a reliably identified species and region, the edible part, preparation requirements, known toxic look-alikes, and clear limits/contraindications. If these details are absent, label the item **research needed** instead of publishing it as an edible-food recommendation.

### What can I make or build?

Look first in these stages:
- **Agriculture & Food Systems:** crop cultivation, seed saving, soil improvement, composting, irrigation, and food preservation.
- **Energy & Mechanics:** simple mechanical power, repair, energy generation and storage.
- **Materials & Construction:** clay, bricks, lime, mortar, concrete, glass and other construction materials.
- **Tools, Chemistry & Manufacturing:** tools, repair, metalworking, soap/adhesives and basic manufacturing.
- **Water & Sanitation:** safe collection, treatment and storage of water, toilets, and hygiene facilities.
- **Disaster Risk Reduction:** emergency shelters, kits, evacuation and first-aid preparedness.

These are **target categories for building the knowledge base**, not a claim that the current dataset already contains complete how-to recipes for each. For a build/make guide, require a bill of materials, tools, step-by-step method, critical temperatures/measurements where source-backed, expected result, failure modes, and safety warnings. Avoid synthesizing operational instructions from unrelated sources when key details are missing.

## Is the filter good enough?

The current filter is useful as a **first-pass organizer**, but it is not a semantic fact-checker. In `scripts/stages.py`, stage assignment prioritizes an existing `stage_ids` value; if absent, it uses keyword and category matches. That is transparent and fast, but can still produce false positives (a keyword mention is not proof that the tip belongs in a stage) and missed matches when a different word is used. The extraction path already rejects candidates whose evidence excerpt is not found verbatim in stored source text, that have no practical steps, or that cannot be classified into a stage. `scripts/audit_tips.py` adds deterministic checks for missing fields, source evidence, generic advice, duplicates and stage mismatches.

These checks improve consistency but **do not validate the source's authority, scientific correctness, regional applicability, completeness, or safety**. A verbatim excerpt proves only that the wording occurs in the stored page; it does not automatically prove that the AI's summary or steps are a faithful interpretation.

Recommended quality gates before content is promoted from `needs_review`:
1. **Source quality:** prefer primary sources and recognized technical agencies; keep source date, region/jurisdiction, and document version where available.
2. **Evidence match:** exact excerpt is stored; each actionable step can be traced to the source (not just the general topic).
3. **Practicality:** enough detail to reproduce the procedure; no generic slogans or missing critical steps.
4. **Safety-critical review:** qualified human review for wild foods, water treatment, first aid, chemicals, electricity, combustion, construction and food preservation.
5. **Classification:** explicit reviewed stage assignment and a distinct content type such as `identify`, `eat`, `grow`, `build`, `make`, `repair`, or `maintain`.
6. **Status discipline:** keep new AI items at `needs_review`; change status only after an actual review, with reviewer, date and review notes.

### Audit and repair commands

```powershell
python -m scripts.audit_tips
python -m scripts.audit_tips --repair
python -m scripts.validate_data
python -m pytest -q
```

Audit mode only reports flags. Repair mode may call AI providers and consume API credits; it re-extracts flagged source pages and replaces tips only when new candidates pass the configured checks. A passing automatic check is not the same as human approval.

## PDF output

The exporter selects content using explicit `stage_ids` or transparent category/keyword rules. It includes warnings, review status, and source links. A PDF can exist while its stage contains few or zero tips. PDF generation is a formatting/export step, not an accuracy or safety certification.
