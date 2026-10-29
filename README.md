# Survival-TIPS — Survival Knowledge Collector

Python-first, source-linked survival knowledge base inspired by rebuilding civilization from first principles.

**Current phase:** source collection, eight-stage knowledge taxonomy, stage filters, and offline PDF export. Frontend remains a later phase.

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

## Repository layout

- `config/sources.json` — search queries, trusted domains, RSS feeds, GBIF taxon queries.
- `config/stages.json` — stage catalogue, order, descriptions, category and keyword rules.
- `scripts/collect_sources.py` — search, RSS, article fetching.
- `scripts/extract_tips.py` — AI extraction with Groq → DeepSeek → OpenRouter fallback; assigns stage IDs.
- `scripts/stages.py` — shared stage classification and filtering.
- `scripts/export_pdfs.py` — creates a separate PDF for each stage.
- `scripts/collect_gbif.py` — GBIF occurrence records and license-gated image downloads.
- `scripts/run_pipeline.py` — data collection orchestrator.
- `scripts/validate_data.py` — data-integrity checks.
- `data/sources.json`, `data/tips.json`, `data/species.json` — collected records.
- `docs/pdf/` — generated stage handbooks.
- `.github/workflows/collect-data.yml` — manual and weekly pipeline.

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
python -m scripts.validate_data
python -m scripts.export_pdfs --all
pytest -q
```

GitHub Actions can also run the pipeline manually: Actions → **Collect survival data** → Run workflow. The workflow exports and commits stage PDFs alongside updated JSON and licensed assets.

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

## PDF output

The exporter is deterministic in content selection: stage membership comes from explicit `stage_ids` or transparent category/keyword rules. It includes warnings, review status, and source links. It does not mark AI output as verified.
