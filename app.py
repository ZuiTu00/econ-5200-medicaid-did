"""
ECON 5200 Final Project: Medicaid Expansion Causal Dashboard
Author: ZuiTu00
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ============================================================
# Page configuration
# ============================================================
st.set_page_config(
    page_title="Medicaid Expansion Causal Dashboard",
    page_icon="🏥",
    layout="wide"
)

# ============================================================
# Header
# ============================================================
st.title("🏥 Medicaid Expansion: Causal Effect on Uninsured Rates")
st.markdown(
    "*A consulting dashboard for the ECON 5200 Final Project. "
    "County-level Difference-in-Differences using SAHIE data, 2009–2023.*"
)
st.markdown("---")

# ============================================================
# Load data from GitHub
# ============================================================
DATA_URL = (
    "https://raw.githubusercontent.com/ZuiTu00/econ-5200-medicaid-did/"
    "main/data/clean_data/did_county.csv"
)

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)
    df["county_id"] = df["county_id"].astype(int)
    df["statefips"] = df["statefips"].astype(int)
    return df

df = load_data()

# ============================================================
# Baseline causal estimates (from TWFE DiD in main notebook)
# ============================================================
BASELINE_ATE_UNWEIGHTED = -2.06   # pp reduction
BASELINE_SE_UNWEIGHTED = 0.70

BASELINE_ATE_WEIGHTED = -1.41
BASELINE_SE_WEIGHTED = 1.22

# ============================================================
# Sidebar: What-If Controls
# ============================================================
st.sidebar.header("⚙️ What-If Scenarios")

specification = st.sidebar.radio(
    "Specification",
    ["Population-Weighted (effect on average person)",
     "Unweighted (effect on average county)"],
    help=("Population-weighted gives equal weight to each person; "
          "unweighted gives equal weight to each county.")
)

if "Unweighted" in specification:
    BASELINE_ATE = BASELINE_ATE_UNWEIGHTED
    BASELINE_SE = BASELINE_SE_UNWEIGHTED
else:
    BASELINE_ATE = BASELINE_ATE_WEIGHTED
    BASELINE_SE = BASELINE_SE_WEIGHTED

st.sidebar.markdown("---")

takeup_rate = st.sidebar.slider(
    "Eligibility take-up rate (%)",
    min_value=50, max_value=100, value=85, step=5,
    help=("Share of newly eligible adults who actually enroll. "
          "Baseline TWFE estimate assumes ~85% take-up "
          "based on observed enrollment in 2014 expanders.")
)

coverage_scale = st.sidebar.slider(
    "Generalizability multiplier",
    min_value=0.5, max_value=1.5, value=1.0, step=0.1,
    help=("Adjusts for external validity to non-expansion states. "
          "Use < 1.0 if non-expansion states are likely to have weaker "
          "outreach infrastructure or lower take-up than 2014 expanders.")
)

pop_nonexpansion = st.sidebar.number_input(
    "Population under 65 in non-expansion states (millions)",
    min_value=10.0, max_value=80.0, value=55.0, step=1.0,
    help="Approximate under-65 population across the 10 non-expansion states."
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Methodology:** Two-Way Fixed Effects DiD on 2,142 counties × 15 years. "
    "Standard errors clustered at state level (35 clusters)."
)

# ============================================================
# Compute What-If Estimate
# ============================================================
adjusted_ate = BASELINE_ATE * (takeup_rate / 85.0) * coverage_scale
adjusted_se = BASELINE_SE * (takeup_rate / 85.0) * coverage_scale
ci_lower = adjusted_ate - 1.96 * adjusted_se
ci_upper = adjusted_ate + 1.96 * adjusted_se

newly_insured_point = abs(adjusted_ate) / 100 * pop_nonexpansion
newly_insured_lo = abs(ci_upper) / 100 * pop_nonexpansion
newly_insured_hi = abs(ci_lower) / 100 * pop_nonexpansion

# ============================================================
# Main metrics row
# ============================================================
st.subheader("📊 Estimated Causal Effect")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Effect (pp)", f"{adjusted_ate:.2f}")
col2.metric("95% CI Lower", f"{ci_lower:.2f}")
col3.metric("95% CI Upper", f"{ci_upper:.2f}")
col4.metric("Newly Insured (M)", f"{newly_insured_point:.2f}")

st.markdown(
    f"""
> **Scenario:** Under a **{takeup_rate}%** take-up rate and **{coverage_scale:.1f}×**
> generalizability scaling, Medicaid expansion is estimated to reduce uninsurance by
> **{abs(adjusted_ate):.2f} percentage points** (95% CI:
> [{abs(ci_upper):.2f}, {abs(ci_lower):.2f}]).
>
> Applied to **{pop_nonexpansion:.0f}M** under-65 residents across non-expansion states,
> this translates to roughly **{newly_insured_point:.2f}M newly insured** people
> (95% CI: [{newly_insured_lo:.2f}M, {newly_insured_hi:.2f}M]).
"""
)

st.markdown("---")

# ============================================================
# Tab interface for visualizations
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Parallel Trends",
     "🎯 Sensitivity Analysis",
     "🔄 Counterfactual",
     "📋 Data Summary"]
)

# ------------------------------------------------------------
# Tab 1: Parallel Trends (key DiD assumption visualization)
# ------------------------------------------------------------
with tab1:
    st.subheader("Parallel Trends: County-Level Uninsured Rates")
    st.markdown(
        "*The most important DiD diagnostic. If pre-2014 trends are parallel, "
        "the post-2014 divergence can be interpreted as causal.*"
    )

    # Population-weighted means by group and year
    def weighted_mean(x, w):
        return (x * w).sum() / w.sum()

    trends_rows = []
    for yr in sorted(df["year"].unique()):
        for grp in [0, 1]:
            d = df[(df["year"] == yr) & (df["treated"] == grp)]
            trends_rows.append({
                "year": yr,
                "treated": grp,
                "weighted_mean": weighted_mean(d["PCTUI"], d["NIPR"]),
                "unweighted_mean": d["PCTUI"].mean(),
            })
    trends = pd.DataFrame(trends_rows)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trends[trends["treated"] == 1]["year"],
        y=trends[trends["treated"] == 1]["weighted_mean"],
        mode="lines+markers",
        name="Expansion Counties",
        line=dict(color="#1a237e", width=3),
        marker=dict(size=8),
    ))
    fig.add_trace(go.Scatter(
        x=trends[trends["treated"] == 0]["year"],
        y=trends[trends["treated"] == 0]["weighted_mean"],
        mode="lines+markers",
        name="Non-Expansion Counties",
        line=dict(color="#c62828", width=3),
        marker=dict(size=8),
    ))
    fig.add_vline(
        x=2013.5, line_dash="dash", line_color="gray",
        annotation_text="ACA Expansion (2014)",
        annotation_position="top",
    )
    fig.update_layout(
        title="Population-Weighted Uninsured Rate by Expansion Status",
        xaxis_title="Year",
        yaxis_title="Uninsured Rate (%)",
        template="plotly_white",
        height=500,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "**Interpretation:** Pre-2014, both groups follow approximately parallel "
        "downward trends. After 2014, expansion counties experience a sharp "
        "additional decline — consistent with a causal treatment effect."
    )

# ------------------------------------------------------------
# Tab 2: Sensitivity to Take-Up Rate
# ------------------------------------------------------------
with tab2:
    st.subheader("How Does the Estimated Effect Vary With Take-Up Rate?")
    st.markdown(
        "*The shaded band represents the 95% confidence interval. "
        "The red line marks your current scenario.*"
    )

    takeup_range = np.arange(50, 101, 1)
    ates = BASELINE_ATE * (takeup_range / 85.0) * coverage_scale
    ses = BASELINE_SE * (takeup_range / 85.0) * coverage_scale

    fig2 = go.Figure()
    # Confidence band
    fig2.add_trace(go.Scatter(
        x=takeup_range, y=ates + 1.96 * ses,
        mode="lines", line=dict(width=0), showlegend=False,
    ))
    fig2.add_trace(go.Scatter(
        x=takeup_range, y=ates - 1.96 * ses,
        mode="lines", line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(26,35,126,0.2)",
        name="95% CI",
    ))
    # Point estimate line
    fig2.add_trace(go.Scatter(
        x=takeup_range, y=ates,
        mode="lines",
        line=dict(color="#1a237e", width=2.5),
        name="Estimated Effect",
    ))
    # Current scenario marker
    fig2.add_vline(
        x=takeup_rate, line_dash="dash", line_color="red",
        annotation_text=f"Current: {takeup_rate}%",
        annotation_position="top right",
    )
    # Zero reference
    fig2.add_hline(y=0, line_dash="dot", line_color="gray")
    fig2.update_layout(
        title="What-If: Effect on Uninsured Rate as Take-Up Varies",
        xaxis_title="Eligibility Take-Up Rate (%)",
        yaxis_title="Estimated Effect (percentage points)",
        template="plotly_white",
        height=500,
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.info(
        "**Interpretation:** As take-up rate falls below 85%, the effect attenuates "
        "proportionally. At very low take-up rates (50%), the confidence interval "
        "may approach zero, suggesting the policy's effectiveness depends critically "
        "on outreach and enrollment infrastructure."
    )

# ------------------------------------------------------------
# Tab 3: Counterfactual Scenario
# ------------------------------------------------------------
with tab3:
    st.subheader("Counterfactual: What If All Non-Expansion States Adopted?")
    st.markdown(
        "*This is the central policy counterfactual: applying the estimated effect "
        "to the populations of all 10 non-expansion states.*"
    )

    full_ate = BASELINE_ATE * coverage_scale
    full_se = BASELINE_SE * coverage_scale
    full_ci = (full_ate - 1.96 * full_se, full_ate + 1.96 * full_se)
    full_insured = abs(full_ate) / 100 * pop_nonexpansion
    full_insured_lo = abs(full_ci[1]) / 100 * pop_nonexpansion
    full_insured_hi = abs(full_ci[0]) / 100 * pop_nonexpansion

    # Comparison: doubled treatment intensity scenario (course requirement)
    double_ate = full_ate * 2.0
    double_se = full_se * 2.0
    double_ci = (double_ate - 1.96 * double_se, double_ate + 1.96 * double_se)
    double_insured = abs(double_ate) / 100 * pop_nonexpansion

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### Scenario A: Baseline Adoption")
        st.metric("Effect (pp)", f"{full_ate:.2f}",
                  f"95% CI: [{full_ci[0]:.2f}, {full_ci[1]:.2f}]")
        st.metric("Newly Insured (M)", f"{full_insured:.2f}",
                  f"Range: [{full_insured_lo:.2f}, {full_insured_hi:.2f}]")
        st.markdown(
            f"If all 10 non-expansion states adopted Medicaid expansion at "
            f"baseline take-up, an estimated **{full_insured:.2f}M** additional "
            f"under-65 residents would gain coverage."
        )

    with col_b:
        st.markdown("### Scenario B: Treatment Intensity Doubled")
        st.metric("Effect (pp)", f"{double_ate:.2f}",
                  f"95% CI: [{double_ci[0]:.2f}, {double_ci[1]:.2f}]")
        st.metric("Newly Insured (M)", f"{double_insured:.2f}")
        st.markdown(
            "If treatment intensity were doubled (e.g., expansion combined with "
            "aggressive outreach campaigns or supplementary state subsidies), "
            f"the estimated effect would scale to **{double_ate:.2f} pp** — "
            f"insuring roughly **{double_insured:.2f}M** more people."
        )

    # Visual comparison of scenarios
    scenarios_df = pd.DataFrame({
        "Scenario": ["Current", "All States Adopt", "Doubled Intensity"],
        "Effect": [adjusted_ate, full_ate, double_ate],
        "Lower": [ci_lower, full_ci[0], double_ci[0]],
        "Upper": [ci_upper, full_ci[1], double_ci[1]],
    })

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=scenarios_df["Scenario"],
        y=scenarios_df["Effect"],
        error_y=dict(
            type="data",
            symmetric=False,
            array=scenarios_df["Upper"] - scenarios_df["Effect"],
            arrayminus=scenarios_df["Effect"] - scenarios_df["Lower"],
        ),
        marker=dict(color=["#1a237e", "#2e7d32", "#ef6c00"]),
        text=[f"{v:.2f}" for v in scenarios_df["Effect"]],
        textposition="auto",
    ))
    fig3.add_hline(y=0, line_dash="dot", line_color="gray")
    fig3.update_layout(
        title="Estimated Effect by Scenario (with 95% CIs)",
        yaxis_title="Effect on Uninsured Rate (pp)",
        template="plotly_white",
        height=450,
        showlegend=False,
    )
    st.plotly_chart(fig3, use_container_width=True)

# ------------------------------------------------------------
# Tab 4: Data Summary
# ------------------------------------------------------------
with tab4:
    st.subheader("Dataset Summary")
    col_x, col_y, col_z = st.columns(3)
    col_x.metric("Total Observations", f"{len(df):,}")
    col_y.metric("Counties", f"{df['county_id'].nunique():,}")
    col_z.metric("Years", f"{df['year'].min()}–{df['year'].max()}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Treatment Group (Expansion)**")
        st.metric("Counties", f"{df[df['treated']==1]['county_id'].nunique():,}")
        st.metric("States", f"{df[df['treated']==1]['state_name'].nunique()}")
    with col_b:
        st.markdown("**Control Group (Non-Expansion)**")
        st.metric("Counties", f"{df[df['treated']==0]['county_id'].nunique():,}")
        st.metric("States", f"{df[df['treated']==0]['state_name'].nunique()}")

    st.markdown("### Group Means (PCTUI)")
    means_table = (df.groupby(["treated", "post"])["PCTUI"]
                     .agg(["mean", "std", "count"])
                     .round(2)
                     .reset_index())
    means_table["treated"] = means_table["treated"].map(
        {0: "Control", 1: "Treated"}
    )
    means_table["post"] = means_table["post"].map(
        {0: "Pre (2009-2013)", 1: "Post (2014-2023)"}
    )
    means_table.columns = ["Group", "Period", "Mean PCTUI",
                           "SD PCTUI", "N county-years"]
    st.dataframe(means_table, use_container_width=True)

# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.markdown(
    "**Source code:** "
    "[github.com/ZuiTu00/econ-5200-medicaid-did]"
    "(https://github.com/ZuiTu00/econ-5200-medicaid-did) | "
    "**Methodology:** Two-Way Fixed Effects DiD with state-clustered SEs | "
    "**Data:** U.S. Census SAHIE 2009–2023"
)
