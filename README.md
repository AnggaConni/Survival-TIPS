# Survival-TIPS — Survival Knowledge Collector

Python-first data collection pipeline for a source-linked, global emergency preparedness knowledge base.

**Current phase:** data ingestion only. No frontend or PDF generation yet.

## What it does

1. Finds candidate articles through configured RSS feeds and a web-search adapter.
2. Fetches readable article text conservatively, with timeouts, size limits, a user agent, and robots.txt checks.
3. Uses **Groq first**, then **OpenRouter** as AI extraction fallback (both configured via GitHub Actions secrets); if both are unavailable, stores source records without inventing tips.
4. Stores append-only, deduplicated JSON records with source URLs, retrieval dates, AI provider, and a `needs_review` status.
5. Collects GBIF occurrence metadata and downloads images only when the media has a recognized, explicit redistributable license.
6. Runs manually or weekly through GitHub Actions.

## Repository layout

- `config/sources.json` — approved domains, search queries, RSS feeds, and GBIF taxon queries.
- `scripts/collect_sources.py` — search, RSS, article fetching.
- `scripts/extract_tips.py` — Groq/OpenRouter extraction adapter.
- `scripts/collect_gbif.py` — GBIF occurrences and license-gated image downloads.
- `scripts/run_pipeline.py` — command-line orchestrator.
- `scripts/validate_data.py` — basic data-integrity checks.
- `data/sources.json` — fetched source records.
- `data/tips.json` — candidate tips extracted from source content.
- `data/species.json` — GBIF occurrence and image-attribution metadata.
- `.github/workflows/collect-data.yml` — manual and weekly workflow.

## GitHub secrets

In **Settings → Secrets and variables → Actions → Repository secrets**, configure the keys you already have:

- `GROQ_API_KEY`
- `OPENROUTER_API_KEY`

Optional:
- `TAVILY_API_KEY` — dedicated web search. Without it, the collector tries DuckDuckGo search; RSS collection is independent of search availability.

No secrets are needed for the GBIF public API. Never put keys in source files or commit them to Git.

## Run locally (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and add your API keys; never commit .env
python -m scripts.run_pipeline --limit 8 --gbif-limit 3
python -m scripts.validate_data
```

For search-only collection without AI processing:

```powershell
python -m scripts.run_pipeline --search-only --limit 8
```

For just GBIF:

```powershell
python -m scripts.collect_gbif --query "Quercus" --limit 5
```

## Workflow

Actions → **Collect survival data** → Run workflow. It also runs weekly.

The workflow commits updated JSON and licensed images when there are changes. Search limits are intentionally low in the MVP to be polite to upstream sites and manage API quotas.

## Important quality and safety controls

- AI output is **candidate content**, not verified advice. Every generated tip starts with `verification.status = "needs_review"`.
- Source text is treated as untrusted input; prompts explicitly ignore instructions embedded in scraped pages.
- Search results are discovery leads, not proof of trustworthiness. Curated/trusted domains are prioritized.
- The GBIF API is used for occurrence records. A photo or occurrence record does **not** establish that a species is edible, medicinal, non-toxic, or suitable for survival.
- Images are downloaded only with explicit CC0/public-domain, CC BY, or CC BY-SA license metadata. Unknown, absent, NC, ND, and all-rights-reserved media are skipped. Attribution and original media URLs are preserved.
- Site-specific terms still apply. Robots checks are a baseline, not a substitute for reading terms of use.
- The collector avoids copying whole articles into tip records. It stores limited evidence excerpts and references original pages.

## Next phase

Once source collection runs reliably, add reviewed-source curation and broader coverage. Frontend, offline handbook and PDF generation are deliberately deferred until the collection pipeline is stable.
