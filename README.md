# ECON 5200 Final Project: The Causal Effect of ACA Medicaid Expansion on Uninsured Rates

**Author:** ZuiTu00  
**Course:** ECON 5200 — Consulting Report (Spring 2026)  
**Identification Strategy:** County-level Difference-in-Differences (DiD) with Two-Way Fixed Effects

---

## TL;DR

Medicaid expansion under the ACA caused a **1.4–2.1 percentage point** reduction in county-level uninsured rates. The naive OLS comparison of −6.78 pp overstates the effect by roughly threefold due to selection bias.

| Method | Estimate | 95% CI |
|--------|----------|--------|
| Naive OLS | −6.78 pp | [−6.90, −6.66] |
| Simple DiD | −2.06 pp | [−2.27, −1.85] |
| **TWFE (unweighted, state-clustered SE) — preferred** | **−2.06 pp** | **[−3.42, −0.69]** |
| TWFE (population-weighted) | −1.41 pp | [−3.81, +0.99] |

---

## Live Deliverables

- 📊 **Streamlit Dashboard:** [econ-5200-medicaid-did.streamlit.app](https://econ-5200-medicaid-did-zpe5tcg3rugqpijqjxw25p.streamlit.app/)  
  Interactive what-if scenarios with parameter sliders, dynamic confidence intervals, and counterfactual analysis.

- 📓 **Open Notebook in Colab:** [Run the analysis live](https://colab.research.google.com/github/ZuiTu00/econ-5200-medicaid-did/blob/main/checkpoint_colab.ipynb)  
  No local setup required. Loads data directly from this repo.

---

## Repository Structure

```
econ-5200-medicaid-did/
├── checkpoint_colab.ipynb         # Main analysis notebook
├── medicaid_did.py                # Reusable Python module (data cleaning + estimation)
├── app.py                         # Streamlit dashboard source
├── proposal.md                    # One-page project proposal
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── deliverables/                  # Final report PDFs and DOCXs
│   ├── executive_summary.docx
│   ├── technical_report.docx
│   ├── threats_to_identification.docx
│   └── ai_methodology_appendix.docx
└── data/
    ├── clean_data/
    │   └── did_county.csv         # Cleaned balanced panel
    └── raw_data/
        └── sahie-*.zip            # Original SAHIE files, 2009–2023
```

---

## Reproducibility

**Quick start (Colab, no install):** Open the notebook via the Colab link above and `Runtime → Run all`.

**Local install:**

```bash
git clone https://github.com/ZuiTu00/econ-5200-medicaid-did.git
cd econ-5200-medicaid-did
pip install -r requirements.txt
jupyter notebook checkpoint_colab.ipynb
```

**Run the dashboard locally:**

```bash
streamlit run app.py
```

All numerical results in the notebook can be regenerated from the cleaned dataset in `data/clean_data/did_county.csv`. The full pipeline from raw SAHIE files is also documented and reproducible via the `medicaid_did.py` module.

---

## Methodology

- **Design:** Difference-in-Differences with county and year fixed effects
- **Sample:** Balanced panel of 2,142 counties × 15 years (N = 32,130 observations)
- **Treatment group:** 1,172 counties in 25 states that expanded Medicaid by January 2014
- **Control group:** 970 counties in 10 states that have not expanded as of 2023
- **Excluded:** 15 late-adopting states (avoids Goodman-Bacon 2021 staggered-DiD bias)
- **Inference:** Standard errors clustered at the state level (35 clusters)
- **Robustness:** Pre-COVID subsample (2009–2019); placebo DiD with fake 2012 treatment

## Data Source

U.S. Census Bureau, Small Area Health Insurance Estimates (SAHIE), 2009–2023.  
[https://www.census.gov/programs-surveys/sahie.html](https://www.census.gov/programs-surveys/sahie.html)

## Key Assumption

**Parallel trends:** Absent the policy, expansion and non-expansion counties would have followed the same uninsured-rate trajectory. Supported by an event study showing pre-2014 coefficients statistically indistinguishable from zero, and a placebo DiD with fake 2012 treatment returning a null (β = 0.25, p = 0.21).

## Limitations

The full discussion is in `deliverables/threats_to_identification.docx`. In brief: (i) the parallel-trends assumption cannot be tested in the post-period; (ii) ACA Medicaid expansion is bundled with state marketplace exchanges and outreach; (iii) external validity to remaining non-expansion states (which are systematically poorer and more rural than 2014 expanders) is limited.

---

## License

This project is released for educational use under the MIT License.
