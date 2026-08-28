# Marketing Attribution Model Builder (Claude Skill)

A Claude Skill that builds a multi-touch marketing attribution model from Salesforce Opportunity data and Pardot (Salesforce Marketing Cloud Account Engagement) campaign/engagement data. Built for B2B sellers with long, multi-stakeholder sales cycles, where simple first-touch or last-touch attribution is known to misrepresent which marketing activity actually drives revenue.

**Current version runs entirely on bundled synthetic sample data**, so you can see the full pipeline work immediately with no setup. It can also be pointed at real exports, but that must be run locally (see below), and a direct, no-export Salesforce connector is on the roadmap as the longer-term secure path.

## What it does

1. Ingests Salesforce Opportunity, Opportunity Contact Role, and Campaign Influence exports, plus Pardot Campaign and Prospect Engagement exports (CSV, no live connector required yet)
2. Joins them into a per-opportunity marketing touchpoint journey
3. Runs a win-versus-loss driver analysis: which campaigns and touch volumes actually differ between deals won and deals lost
4. Computes attribution weights under seven rule-based frameworks (first-touch, last-touch, linear, time-decay, U-shaped, W-shaped, full-path)
5. Generates a concrete implementation spec for configuring Salesforce Campaign Influence / Customizable Campaign Influence and Pardot campaign structure
6. Writes every result as CSV, Markdown, and PDF into a new timestamped folder under `Analysis Outcomes/`

## Quick start: run it on the sample data

Just say one of these to Claude (with this skill available), or run the command yourself:

- **"Run the sample data and show me how the attribution model works."**
- **"Walk me through this attribution tool using the bundled sample data."**
- **"Compare all the attribution models on the sample data."**

Or from the command line:

```bash
cd scripts
python run_full_analysis.py
```

That single command runs the entire pipeline (validate → join → win/loss analysis → attribution modeling → implementation spec → PDF conversion) against `assets/sample_data/` and writes everything to a new folder under `Analysis Outcomes/`, for example:

```
Analysis Outcomes/run_20260827_231353_sample_data/
├── run_manifest.md              what was run, when, opportunity counts
├── journeys.csv                 the joined touchpoint-per-opportunity table
├── win_loss_drivers.csv/.md/.pdf     campaigns and touch volume, won vs. lost
├── attribution_report.csv/.md/.pdf   attributed dollars per campaign, per model
└── implementation_spec.md/.pdf       Salesforce/Pardot configuration recommendations
```

To compare all seven models instead of just the default (W-shaped):

```bash
python run_full_analysis.py --model all
```

## Natural language flow (what to expect if you ask Claude to do this)

1. You ask something like *"run the marketing attribution analysis on the sample data"*
2. Claude runs `run_full_analysis.py` against the bundled sample data
3. Claude walks you through the results in this order: win/loss drivers first (what actually differs between won and lost deals), then the attribution model output (how credit splits across campaigns), then the implementation spec (what to configure in Salesforce/Pardot)
4. Claude points you to the new folder under `Analysis Outcomes/` and offers the PDF versions as the files to share with a manager or marketing ops
5. If you want a different model, say so, e.g. *"redo that with time-decay instead"* or *"show me all the models side by side"*
6. If you're ready to try it on real data, see the next section

## Running against real data (must be local)

This skill does not connect live to Salesforce or Pardot. To use your own data:

1. Pull the CSV exports described in `references/salesforce_data_requirements.md` and `references/pardot_data_requirements.md`
2. Put them in a local folder, **on your own machine or a private environment you control**, never in a shared or public Claude session, and never inside this repository's tracked files
3. Run:
   ```bash
   python scripts/run_full_analysis.py --data-dir /path/to/your/local/exports --model w_shaped
   ```
4. Results land in `Analysis Outcomes/run_<timestamp>_local_data/`, in the same file formats as the sample run

**This has to be a local run.** A CSV export of real Opportunity and prospect data is sensitive by nature (deal values, contact names, account details); it should never be uploaded through a shared session, pasted into chat, or committed to a public repository, this one or any fork of it. `.gitignore` in this repo excludes `Analysis Outcomes/` and any non-sample CSV as a backstop, but treat that as a safety net, not a substitute for care.

## Roadmap: direct Salesforce connector

The file-export-then-upload pattern above works, but it means a flat file of sensitive CRM data exists outside Salesforce's access controls for the duration of the analysis, even if it never leaves your machine. The next planned iteration is a **direct Salesforce MCP connector** that pulls Opportunity, Contact Role, and Campaign Influence data straight from the org for this analysis, with no manual export step at all. That's a data-security improvement, not just a convenience one: it removes the window where sensitive pipeline data exists as a portable file. Until that connector ships, local file-based runs (as described above) are the recommended approach for real data.

## Important: data privacy

**This repository ships only synthetic, fabricated sample data** in `assets/sample_data/`. It exists so you can see the tool work before pointing it at anything real. Never commit a real Salesforce or Pardot export, or any output generated from one, to this repository or any fork of it. The `.gitignore` excludes non-sample CSVs and the entire `Analysis Outcomes/` folder as a backstop.

## Using this as a Claude Skill

Point Claude (Claude.ai, Claude Code, or the API with the Skills feature) at this repository, or copy the contents into your skills directory. See `SKILL.md` for the workflow Claude follows once the skill is active.

## Repo layout

```
SKILL.md                            Main workflow Claude follows
scripts/
  run_full_analysis.py              Orchestrator: runs the full pipeline and organizes outputs
  ingest_validate.py                Load, validate, and join the CSV exports
  win_loss_driver_analysis.py       Compare touch patterns between won and lost deals
  run_attribution_models.py         Compute weights under each attribution framework
  generate_pardot_config.py         Turn results into a Salesforce/Pardot implementation spec
  generate_pdf_reports.py           Convert markdown/CSV outputs into formatted PDFs
  generate_synthetic_data.py        Regenerate the synthetic sample dataset
references/
  salesforce_data_requirements.md   Field-level schema for the Salesforce exports
  pardot_data_requirements.md       Field-level schema for the Pardot exports
  attribution_frameworks.md         How each model works, when to use it
  implementation_guide.md           General guidance for configuring Salesforce/Pardot
assets/sample_data/                 Synthetic sample CSVs (safe to commit, not real data)
Analysis Outcomes/                  Generated at run time, one folder per run (gitignored)
tests/eval_cases.json               Test prompts for validating the skill's behavior
```

## Status

**v1.1-alpha (current):** rule-based attribution models (first-touch through full-path), file-upload only, runs on bundled sample data out of the box, PDF + Markdown + CSV outputs organized into `Analysis Outcomes/`. Not yet validated against a live org; see RELEASE_NOTES.md.

**Planned:**
- Direct Salesforce MCP connector, replacing manual CSV export for data-security reasons (see Roadmap above)
- Data-driven/algorithmic attribution (regression or Markov-chain removal-effect), once there's a large enough closed-won sample to fit it reliably (see `references/attribution_frameworks.md`)
- Validation of the documented field schema against a live org

Field names in `references/*_data_requirements.md` are built from the documented Salesforce/Pardot object model and have not yet been validated against a live org. Confirm against your actual export before the first real run and open an issue/PR if field names differ.

## License

See LICENSE.
