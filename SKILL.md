---
name: marketing-attribution-builder
description: Build a marketing attribution model from Salesforce Opportunity data and Pardot (Account Engagement) campaign/engagement data, for B2B sellers with long sales cycles and multiple stakeholders. Use this whenever the user wants to analyze which marketing campaigns and touchpoints actually drove closed-won deals, compare attribution models (first-touch, last-touch, linear, time-decay, U-shaped, W-shaped, full-path), run a win-versus-loss driver analysis on marketing engagement, or generate an implementation spec for Salesforce Campaign Influence / Pardot. Also trigger this to demo or walk through the tool using its bundled synthetic sample data. Trigger on requests like "analyze our marketing attribution," "which campaigns influenced our closed-won deals," "build an attribution model from our Salesforce/Pardot data," "run the sample data," "what marketing touches drove this pipeline," or any request that pairs Opportunity data with Campaign/engagement data and asks what worked.
---

# Marketing Attribution Model Builder

Builds a multi-touch marketing attribution model from Salesforce Opportunity/Campaign Influence exports and Pardot campaign/engagement exports. Designed for B2B sellers with long (multi-month), multi-stakeholder sales cycles, where single-touch (first/last click) attribution is known to be misleading.

**This version of the skill runs on the bundled synthetic sample data by default.** It is a working demo of the full pipeline, not yet validated against a real Salesforce/Pardot org. See "Running against real data" below before pointing it at anything real.

## Workflow (default: sample data)

The whole pipeline is one command. When a user asks to see how this works, run the sample data, or build an attribution model without specifying their own files, use this:

```
python scripts/run_full_analysis.py
```

This runs ingest/validate, win/loss driver analysis, attribution modeling (W-shaped by default), and implementation spec generation in sequence, against `assets/sample_data/`, and writes every output, CSV, markdown, and PDF, into a new timestamped folder under `Analysis Outcomes/` (e.g. `Analysis Outcomes/run_20260827_231353_sample_data/`). Nothing needs to be run manually or assembled by hand.

To compare all seven attribution models instead of just the default:

```
python scripts/run_full_analysis.py --model all
```

After it runs, open the new folder under `Analysis Outcomes/` and walk the user through:
- `run_manifest.md`: what was run, when, against what data, opportunity counts
- `win_loss_drivers.md` / `.pdf`: which campaigns and touch volumes differ between won and lost deals (present this one first, it's often more actionable than the weighted dollars)
- `attribution_report.md` / `.pdf`: top campaigns by attributed pipeline dollars, per model
- `implementation_spec.md` / `.pdf`: concrete Salesforce/Pardot configuration recommendations

Present the PDF versions as the primary shareable deliverable (they're what a user would forward to a manager or marketing ops); the markdown and CSV versions exist alongside them for anyone who wants to read the raw data or diff runs over time.

## Running against real data

The bundled orchestrator also accepts a real local data folder:

```
python scripts/run_full_analysis.py --data-dir /path/to/your/local/exports --model w_shaped
```

This must be run **locally**, on the user's own machine or a private environment, never uploaded through a shared or public Claude session and never committed to this (or any) public repository. See `references/salesforce_data_requirements.md` and `references/pardot_data_requirements.md` for the exact CSV export format required. If the user doesn't have these exports yet, those two files double as a checklist for a Salesforce/Pardot admin to pull them.

If the user asks to run this against real Salesforce/Pardot data inside a shared or non-local session, or asks to add real data to this repository, decline and explain why (see "Data privacy" in README.md), then offer to walk them through running it locally instead.

## Roadmap: direct Salesforce connector

This version is file-upload only by design. A live Salesforce MCP connector (pulling Opportunity, Contact Role, and Campaign Influence data directly, without a manual CSV export ever touching disk) is a planned follow-up, specifically for data-security reasons: it removes the export/upload step entirely, so sensitive pipeline data never leaves Salesforce's access-controlled environment as a flat file. Until that connector exists, the file-upload-plus-local-run pattern above is the recommended secure path. If the user asks about this, explain it's on the roadmap, not available yet, and that local file-based runs remain the current best practice for real data.

## Manual step-by-step (for debugging or partial runs)

The orchestrator wraps these individually runnable scripts, useful if a user wants to inspect an intermediate step or rerun just one stage:

1. `scripts/ingest_validate.py --data-dir <dir> --out <journeys.csv>` — validates required columns and joins everything into a touchpoint-per-row journey table. Read the console output for the unmatched-engagement warning; a high count means real prospect engagement isn't linking to any Opportunity Contact Role, worth surfacing before trusting downstream results.
2. `scripts/win_loss_driver_analysis.py --journeys <journeys.csv> --out <win_loss_drivers.csv>`
3. `scripts/run_attribution_models.py --journeys <journeys.csv> --out <attribution_report.csv> --model <model or 'all'>`
4. `scripts/generate_pardot_config.py --report <attribution_report.csv> --model <model> --out <implementation_spec.md>`
5. `scripts/generate_pdf_reports.py --md <file.md> --out <file.pdf>` (or `--csv <file.csv> --title "..."` for a raw table) — converts any markdown or CSV output into a formatted PDF

## Choosing a model

See `references/attribution_frameworks.md` for the full menu and tradeoffs. Given a sales cycle around 6 months, **W-shaped** is the recommended default unless the user has a specific reason to prefer another (e.g. time-decay if they believe recency dominates). If unsure, run `--model all` and compare rankings; stable rankings across models are a good sign, wide swings mean the sample size or data quality needs a look first.

## Notes on data-driven (algorithmic) attribution

Not implemented in this version. `references/attribution_frameworks.md` explains the rationale: rule-based models (especially W-shaped) are the right starting point until there's a large enough closed-won sample (roughly 100+ deals with clean touch histories) to fit a regression or Markov-chain model reliably. If the user asks for this, explain the tradeoff and suggest the rule-based comparison (`--model all`) as the current alternative.

## Common failure modes to watch for

- **Low join rate between Pardot engagement and Salesforce Opportunity Contact Roles.** The most common real-world problem (unsynced prospects, missing contact roles). `ingest_validate.py` surfaces this as a warning; don't ignore it when summarizing results.
- **Very small closed-won sample.** Under ~15-20 closed-won deals, treat any model's output as directional, say so explicitly rather than presenting percentages as precise. The bundled sample data itself only has 11 closed-won opportunities, call this out if walking someone through the demo.
- **Confusing "attributed dollars" with "caused the deal."** Attribution models describe correlation/credit-splitting under an assumed weighting scheme, not proven causation. Phrase results accordingly ("credited under the W-shaped model," not "responsible for").
- **Committing real data.** Never write real uploaded data into this repository's tracked files, and never place real exports anywhere that could end up in `Analysis Outcomes/` if that folder is later committed. See the `.gitignore` and README.md.
