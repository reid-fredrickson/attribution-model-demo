# Release Notes

## v1.1-alpha

**Status: alpha.** This release is a general rule-based attribution framework, not yet validated against a live Salesforce/Pardot org and **not intended for production use**. Treat output as directional until the documented field schema (`references/salesforce_data_requirements.md`, `references/pardot_data_requirements.md`) has been confirmed against a real org and the pipeline has been run against real closed-won data.

### Scope of the model

A Claude Skill and standalone script pipeline that builds a **multi-touch marketing attribution model** from Salesforce Opportunity data and Pardot (Account Engagement) campaign/engagement data. It targets B2B sellers with long (multi-month), multi-stakeholder sales cycles, where single-touch attribution (first-click or last-click) is known to misrepresent which marketing activity actually drives revenue.

The pipeline:

1. Ingests Salesforce Opportunity, Opportunity Contact Role, and Campaign Influence exports, plus Pardot Campaign and Prospect Engagement exports (CSV; no live connector yet).
2. Joins them into a per-opportunity marketing touchpoint journey.
3. Runs a win-versus-loss driver analysis — which campaigns and touch volumes actually differ between deals won and deals lost.
4. Computes attribution weights under seven rule-based frameworks: first-touch, last-touch, linear, time-decay, U-shaped, W-shaped (recommended default for ~6-month cycles), and full-path.
5. Generates a concrete implementation spec for configuring Salesforce Campaign Influence / Customizable Campaign Influence and Pardot campaign structure.
6. Writes every result as CSV, Markdown, and PDF into a timestamped folder under `Analysis Outcomes/`.

Data-driven/algorithmic attribution (regression or Markov-chain removal-effect) is scoped as a future milestone, once there's enough closed-won volume (100+ deals with clean touch histories) to fit reliably. A direct, no-export Salesforce MCP connector is also on the roadmap, to remove the manual CSV export/upload step entirely.

### Intended usage

- **Out of the box**: runs entirely on bundled synthetic sample data (`assets/sample_data/`), so the full pipeline — ingest, win/loss analysis, attribution modeling, implementation spec, PDF output — can be seen working immediately with no setup and no real data required.
- **Against real data**: supported via `run_full_analysis.py --data-dir /path/to/your/local/exports`, but **must be run locally**, on the user's own machine or a private environment. Real Salesforce/Pardot exports (deal values, contact names, account details) should never be uploaded through a shared or public Claude session, pasted into chat, or committed to this repository or any fork of it.
- **As a Claude Skill**: point Claude (Claude.ai, Claude Code, or the API with the Skills feature) at this repository, or copy its contents into a skills directory, to drive the pipeline conversationally (see `SKILL.md`).
- **Not intended for**: production use of any kind at this stage (this is a general rule-based framework, not yet validated against a live org), production/live Salesforce or Pardot connectivity (file-upload only in this version), or as the sole basis for budget decisions without cross-checking model output against the win/loss driver analysis (see `references/attribution_frameworks.md` for guidance on choosing and validating a model).
