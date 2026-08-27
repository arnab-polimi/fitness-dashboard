"""
Transparent Multi-Signal Training Stress & Injury Risk Assessment View.
Explicitly labeled as a training load indicator, not a medical prediction.
"""
from typing import List
import streamlit as st
import pandas as pd

from src.models.activity import Activity
from src.models.metrics import DailyLoad, RiskReport
from src.ui.components import (
    render_disclaimer_banner,
    render_risk_signal_row,
    render_metric_card,
)
from src.ui.charts import plot_acwr_gauge, plot_risk_radar


def render_injury_risk_view(
    activities: List[Activity],
    daily_loads: List[DailyLoad],
    risk_report: RiskReport,
) -> None:
    st.markdown("## 🛡️ Transparent Training-Stress & Injury-Risk Indicator")
    st.caption("A multi-signal algorithmic assessment of training load distribution, volume ramps, and biomechanical fatigue.")

    # Explicit Medical Disclaimer
    render_disclaimer_banner(risk_report.disclaimer)

    if not daily_loads:
        st.info("Import training data to generate your multi-signal injury risk assessment.")
        return

    # Top KPI summary cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            label="Composite Risk Score",
            value=f"{risk_report.composite_score:.0f} / 100",
            subtext=risk_report.overall_status,
            delta="Multi-Signal Index",
            delta_type="pos" if risk_report.composite_score < 50 else "neg",
        )
    with c2:
        render_metric_card(
            label="Acute:Chronic Workload (ACWR)",
            value=f"{risk_report.acwr_value:.2f}",
            subtext="Optimal Zone: 0.80 – 1.30",
            delta="Safe" if 0.8 <= risk_report.acwr_value <= 1.3 else "Caution",
            delta_type="pos" if 0.8 <= risk_report.acwr_value <= 1.3 else "neg",
        )
    with c3:
        render_metric_card(
            label="7-Day Fitness Ramp Rate",
            value=f"{risk_report.ramp_rate_7d:+.1f} TSS/wk",
            subtext="Target: < 5.0 TSS/week",
            delta="Sustainable" if risk_report.ramp_rate_7d <= 5.0 else "Aggressive",
            delta_type="pos" if risk_report.ramp_rate_7d <= 5.0 else "neg",
        )
    with c4:
        render_metric_card(
            label="Consecutive Hard Days",
            value=f"{risk_report.consecutive_hard_days} Days",
            subtext="Days with TSS > 60",
            delta="Safe" if risk_report.consecutive_hard_days <= 1 else "Recovery Needed",
            delta_type="pos" if risk_report.consecutive_hard_days <= 1 else "neg",
        )

    # Middle Charts: ACWR Gauge & Multi-Signal Radar
    g_col1, g_col2 = st.columns([1, 1])
    with g_col1:
        st.plotly_chart(plot_acwr_gauge(risk_report.acwr_value), use_container_width=True)
    with g_col2:
        st.plotly_chart(plot_risk_radar(risk_report), use_container_width=True)

    # Detailed Multi-Signal Breakdown
    st.markdown("### 📋 Transparent Multi-Signal Audit")
    st.caption("Every signal's mathematical weighting, current value, status, and underlying evidence:")

    for signal in risk_report.signals:
        render_risk_signal_row(signal)

    # Actionable Coaching Guidance
    st.markdown("### 💡 Recommended Training Modifications")
    for rec in risk_report.actionable_guidance:
        st.markdown(f"- **{rec}**")

    # Methodological Transparency Expander
    with st.expander("🔍 Scientific Methodology & Signal Weighting"):
        st.markdown("""
        ### Why a Multi-Signal Approach?
        Single metrics (like the 10% rule or ACWR in isolation) fail to account for how stress interacts across different physiological systems. 
        This engine models 5 distinct operational risk factors:
        
        1. **Acute:Chronic Workload Ratio (ACWR - 30% weight)**:
           - Compares acute fatigue (7-day load) to chronic fitness (28-day load).
           - Tim Gabbett's sports science framework establishes the 0.8–1.3 range as the sweet spot for adaptation with lowest relative tissue breakdown risk.
        2. **7-Day Ramp Rate (20% weight)**:
           - Tracks the weekly climb in Chronic Training Load (CTL).
           - Ramping $> 5-8$ TSS/week exposes connective tissues (Achilles tendon, plantar fascia, patellar tendon) faster than collagen synthesis can adapt.
        3. **Foster's Training Monotony & Strain (20% weight)**:
           - Measures daily load dispersion $\\text{Mean} / \\text{SD}$.
           - High monotony ($> 1.8$) indicates an absence of polarized recovery days, leading to chronic glycogen depletion and blunted supercompensation.
        4. **Consecutive High-Load Days (15% weight)**:
           - Consecutive days exceeding 60 TSS without an intervening easy or rest day.
        5. **Biomechanical & Decoupling Variance (15% weight)**:
           - Detects neuromuscular fatigue signals such as sudden cadence drops ($> 4\%$) or premature cardiac decoupling ($> 8\%$).
        """)
