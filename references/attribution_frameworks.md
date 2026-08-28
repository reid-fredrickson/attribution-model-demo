# Attribution Frameworks Reference

Each model answers a slightly different question. Run more than one and compare before committing to a default; the goal is a model that matches how your buyers actually move through a ~6-month, multi-stakeholder cycle, not the model that is simplest to explain.

## Single-touch models (diagnostic, not recommended as the primary model)

**First-touch**: 100% of credit to the first touchpoint. Answers "what starts a journey." Use it as a top-of-funnel diagnostic, never as the primary model for a cycle this long, since it ignores everything that actually moved the deal forward.

**Last-touch**: 100% of credit to the final touchpoint before close. Answers "what triggers the close." Same caveat: useful as a diagnostic, misleading as a budget-allocation model, since it systematically overcredits bottom-funnel activity like demo requests.

## Multi-touch, rule-based models

**Linear**: Equal credit across every touch. The honest baseline. If your other models diverge wildly from linear, that is a signal the weighting assumptions are doing a lot of work, worth a sanity check before trusting them.

**Time-decay**: Credit increases exponentially the closer a touch is to the close date. Tunable via a half-life parameter (default 14 days in the reference implementation). Good fit if you believe recency dominates, e.g. a prospect that goes cold for months and then re-engages hard right before signing.

**U-shaped (position-based)**: 40% to first touch, 40% to the touch nearest opportunity creation, remaining 20% split across the middle. Simpler two-anchor version of W-shaped; use if you don't need to isolate the close itself as a distinct moment.

**W-shaped (recommended default for a ~6-month sales cycle)**: 30% first touch, 30% touch nearest opportunity creation, 30% touch nearest close, remaining 10% split across whatever happens in between. This is the standard model recommended for long, staged B2B cycles because it credits three distinct jobs marketing does: creating awareness, qualifying/progressing the deal into pipeline, and reinforcing the decision at the end.

**Full-path**: W-shaped plus an explicit added weight on the close-adjacent touch, useful if you suspect a specific late-cycle asset (a fresh case study, a reference call, an ROI calculator revisit) is what actually revives a stalling deal rather than just being coincidentally present near the end.

## Data-driven / algorithmic (v2, not yet implemented)

Regression-based or Markov-chain removal-effect attribution: instead of assuming a weighting rule, the model learns which touch sequences statistically precede wins versus losses, and assigns credit based on each touchpoint's measured incremental contribution. This is the more defensible long-run approach, but needs enough closed-won volume to fit reliably; most teams start with a rule-based model like W-shaped and graduate to data-driven once they have on the order of 100+ closed-won deals with clean touch histories to train on. Treat this as a v2 milestone once the rule-based pipeline has been validated against a full year of real closed-won data.

## Choosing a model in practice

1. Run `run_attribution_models.py --model all` and compare the top-5 campaigns under each model. If the ranking is stable across models, you have a robust signal. If it swings wildly, investigate before trusting any single model, likely a data quality or small-sample-size issue.
2. Cross-check against `win_loss_driver_analysis.py` output. A campaign that ranks high in attributed dollars but shows a negative or flat won-vs-lost presence gap is a flag: it may be well-timed relative to close (time-decay rewards it) without actually being a differentiator between winning and losing.
3. Default to W-shaped unless the comparison in step 1 gives a clear reason to prefer another model.
