# Implementation Guide: From Report to Configured System

This is general background for whoever configures Salesforce/Pardot based on the output of `generate_pardot_config.py`. The generated `implementation_spec.md` is specific to one run's data; this doc is the standing reference for how that spec maps to actual setup steps.

## Where multi-touch weighting actually lives in Salesforce

Salesforce ships three built-in Campaign Influence models:
- **Salesforce Influence Model** (default): 100% credit to the Primary Campaign Source, 0% to everything else. Simple, but exactly the single-touch problem this skill exists to fix.
- **First Touch / Last Touch**: single-touch models, same caveats as covered in `attribution_frameworks.md`.
- **Even Touch**: equal credit across all influencing campaigns, equivalent to the Linear model this skill computes.

None of the built-ins support W-shaped, time-decay, or full-path weighting natively. To get there, enable **Customizable Campaign Influence** (Setup > Campaign Influence > Campaign Influence Setup), which lets an admin define engagement-based or position-based weighting rules. This is where the per-campaign or per-campaign-type percentages from `implementation_spec.md` get translated into actual configuration, typically as a set of rules keyed off engagement type, timing relative to opportunity creation, or campaign member status, since Salesforce does not offer a raw "set this campaign to exactly 23.8%" input.

## Practical sequencing

1. Confirm Customizable Campaign Influence is available on the org's edition (varies by Salesforce edition and whether B2B Marketing Analytics is licensed).
2. Start with the campaign-type roll-up (section 2 of the generated spec) rather than the full per-campaign table. It's easier to configure and validate a handful of type-level rules than dozens of campaign-level ones, and campaign-level weights will drift every time a new campaign launches anyway.
3. Validate against a holdout: after configuring, pull a Campaigns with Influenced Opportunities report and sanity-check it against the attribution_report.csv the skill produced. They won't match exactly (Salesforce's engine and this skill's math aren't identical), but the relative ranking of top campaigns should be directionally consistent.
4. Re-run this skill quarterly (or after each cohort of ~10+ new closed-won deals) and diff the new implementation_spec.md against the configured rules. Update the Salesforce configuration when the drift is meaningful, not on every minor shift.

## If Pardot's platform status is a concern

Salesforce has signaled Account Engagement (Pardot) is not an active roadmap priority (certification retirement, no significant recent feature investment). That doesn't require an immediate migration, but it's worth designing the reporting layer (dashboards, saved reports referencing these weights) so they'd survive a future move to Marketing Cloud Engagement or another MAP: keep the attribution logic and weight computation in this skill (platform-agnostic), and treat the Salesforce/Pardot configuration as the swappable last-mile layer.
