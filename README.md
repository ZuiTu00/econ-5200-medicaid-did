# ECON 5200 Final Project: The Causal Effect of ACA Medicaid Expansion on Uninsured Rates

**Author:** ZuiTu00  
**Course:** ECON 5200 — Consulting Report (Spring 2026)  
**Identification Strategy:** County-level Difference-in-Differences (DiD) with Two-Way Fixed Effects

---

## Research Question

Does Medicaid expansion under the Affordable Care Act cause a reduction in county-level uninsured rates?

## Main Finding

Medicaid expansion reduced county-level uninsured rates by **1.4 to 2.1 percentage points** (population-weighted vs. unweighted TWFE estimates). The naive OLS comparison of −6.8 pp overstates the effect by roughly 3–4x due to selection bias: counties in expansion states already had lower uninsured rates before the ACA.

| Method | Estimate | 95% CI |
|--------|----------|--------|
| Naive OLS | −6.78 pp | [−6.90, −6.66] |
| Simple DiD | −2.06 pp | [−2.27, −1.85] |
| TWFE (unweighted, state-clustered SE) | **−2.06 pp** | **[−3.42, −0.69]** |
| TWFE (population-weighted) | −1.41 pp | [−3.81, 0.99] |

## Repository Structure

econ-5200-medicaid-did/
├── checkpoint_colab.ipynb         # Main analysis notebook
├── proposal.md                    # One-page project proposal
├── README.md                      # This file
└── data/
├── clean_data/
│   └── did_county.csv         # Cleaned balanced panel (2,142 counties × 15 years)
└── raw_data/
└── sahie-*.zip            # Original SAHIE files, 2009–2023
## Reproducibility

Open the notebook directly in Google Colab (no local setup required):

[**→ Open in Colab**](https://colab.research.google.com/github/ZuiTu00/econ-5200-medicaid-did/blob/main/checkpoint_colab.ipynb)

The notebook loads the cleaned dataset from this repo via the GitHub raw URL. All results are reproducible by running `Runtime → Run all` in Colab.

## Data

- **Source:** U.S. Census Bureau, Small Area Health Insurance Estimates (SAHIE), 2009–2023
- **Panel:** 2,142 counties × 15 years = 32,130 observations
- **Treatment group:** 1,172 counties in 25 states that expanded Medicaid by January 2014
- **Control group:** 970 counties in 10 states that had not expanded by 2023
- **Outcome:** Percent uninsured, under 65 (`PCTUI`)

## Methodology

- **Identification:** Difference-in-Differences with county and year fixed effects
- **Standard errors:** Clustered at the state level (treatment is state-assigned)
- **Robustness checks:** (1) drop COVID years 2020–2023; (2) placebo DiD with fake 2012 treatment on pre-ACA data

## Key Assumption

**Parallel trends:** In the absence of Medicaid expansion, expansion and non-expansion counties would have followed the same uninsured-rate trajectory. Supported by visual event study and placebo DiD on the pre-period.
