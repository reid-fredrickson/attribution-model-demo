# Attribution Implementation Spec: w_shaped

Generated from 14 campaigns across the analyzed closed-won opportunities, totaling $808,500 in attributed pipeline value.

## 1. Salesforce: Customizable Campaign Influence weights

Set up in Setup > Campaign Influence > Campaign Influence Setup. Enable Customizable Campaign Influence (if not already active) and define a weighting rule that approximates the w_shaped split below. Salesforce's engine applies weights at the model-configuration level (typically by touch position or engagement type), so translate the per-campaign dollar split below into the closest equivalent position-based rule your org's edition supports; exact per-campaign percentages are the target to validate against once configured, not a literal field-by-field mapping.

| Campaign | Campaign Type | Attributed % of analyzed pipeline | Attributed $ |
|---|---|---|---|
| On-Demand Warehousing ROI Calculator | Interactive Tool | 23.8% | $192,775 |
| Demo Request Landing Page | Demo Request | 17.6% | $141,992 |
| Flexible Warehousing 101 Webinar | Webinar | 17.6% | $141,989 |
| Google Search - Warehousing Non-Brand | Paid Search | 10.7% | $86,489 |
| Case Study: Enterprise Overflow Program | Case Study | 6.7% | $54,536 |
| Analyst Report Syndication (Gartner) | Content Syndication | 6.3% | $51,236 |
| ABM Direct Mail - Enterprise DTC | ABM Direct Mail | 5.9% | $47,942 |
| MODEX Trade Show | Trade Show | 4.4% | $35,921 |
| Partner Referral - 3PL Network | Referral | 2.7% | $21,664 |
| Q3 Email Nurture - Overflow Storage | Email Nurture | 2.5% | $20,571 |
| Google Search - Warehousing Brand | Paid Search | 0.5% | $4,286 |
| Peak Season Playbook Download | Content Syndication | 0.5% | $3,775 |
| Spot Warehousing Index Report | Content Syndication | 0.3% | $2,786 |
| LinkedIn ABM Retargeting | Paid Social | 0.3% | $2,538 |

## 2. Roll-up by campaign type

Use this to sanity-check the model at the channel-strategy level, and as the basis for a Pardot campaign folder/tagging convention so future campaigns of the same type inherit a sensible starting weight.

| Campaign Type | Share of attributed pipeline |
|---|---|
| Interactive Tool | 23.8% |
| Demo Request | 17.6% |
| Webinar | 17.6% |
| Paid Search | 11.2% |
| Content Syndication | 7.1% |
| Case Study | 6.7% |
| ABM Direct Mail | 5.9% |
| Trade Show | 4.4% |
| Referral | 2.7% |
| Email Nurture | 2.5% |
| Paid Social | 0.3% |

## 3. Pardot-side changes to support ongoing measurement

- Confirm Connected Campaigns is enabled so every Pardot asset maps to a Salesforce Campaign the influence model can read.
- Standardize a Campaign_Type custom field/picklist matching the taxonomy used here, so future campaigns roll into this reporting structure without manual remapping.
- Turn on completion actions for the touchpoint types that scored highest in the win/loss driver analysis (see win_loss_drivers.csv), so those specific actions reliably create Campaign Member records rather than being tracked as anonymous activity only.
- Re-run this analysis on a fixed cadence (recommended: quarterly, given the ~6 month sales cycle means each new closed-won cohort meaningfully shifts the data) and diff the weights against this spec to catch drift.

## 4. Caveats before implementing

- This spec reflects the model and data available at generation time. Validate the underlying journeys.csv join rate (see ingest_validate.py console output for unmatched-engagement warnings) before treating these percentages as final; a high unmatched rate means real engagement is missing from this picture.
- Multi-touch weighting in Salesforce Customizable Campaign Influence has edition and configuration limits; confirm what's actually supported in the org before assuming a literal per-campaign percentage is settable.
- Sample sizes on closed-won cohorts under ~20-30 deals should be treated as directional, not final; expect the weights to shift as more closed-won data accumulates.