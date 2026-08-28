"""
Executive Overview Dashboard View.
Shows all key running performance, fitness, load, recovery, and risk indicators.
"""
from typing import List
import streamlit as st
import pandas as pd
import numpy as np

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.models.metrics import DailyLoad, RacePrediction, RiskReport
from src.analytics.running_metrics import (
    format_pace_sec_km,
    RunningMetricsCalculator,
)
from src.ui.components import (
    render_metric_card,
    render_disclaimer_banner,
    render_race_prediction_cards,
)
from src.ui.charts import plot_pmc_chart, plot_weekly_mileage_and_load
from src.ui.icons import render_view_header, render_section_header


def render_overview_view(
    activities: List[Activity],
    daily_loads: List[DailyLoad],
    user_profile: UserProfile,
    race_predictions: List[RacePrediction],
    risk_report: RiskReport,
    daily_df: pd.DataFrame,
    activities_df: pd.DataFrame,
) -> None:
    """Renders the executive summary overview."""
    render_view_header(
        title="Executive Fitness & Performance Overview",
        caption="Real-time telemetry, aerobic efficiency, chronic training load, and multi-signal training risk.",
        icon_name="overview",
    )

    if not activities or not daily_loads:
        st.warning("Welcome to Personal Fitness Intelligence! No activity data loaded yet.")
        st.info("Head over to the **Data Import & Sync** tab to upload your Garmin/Strava CSVs or load sample development data in one click.")
        return

    # Calculate summary metrics
    total_dist_km = sum(a.distance_km for a in activities)
    dist_label = f"{total_dist_km:.1f} km" if user_profile.units == "metric" else f"{total_dist_km * 0.621371:.1f} mi"

    # Recent 30 days metrics
    cutoff_30d = pd.to_datetime("now") - pd.Timedelta(days=30)
    recent_acts = [a for a in activities if a.start_time >= cutoff_30d]
    recent_dist = sum(a.distance_km for a in recent_acts)

    # Average Pace & HR across runs
    run_acts = [a for a in activities if a.sport_type in ["run", "trail_run", "treadmill_run"] and a.effective_pace_sec_km > 0]
    avg_pace_sec = np.mean([a.effective_pace_sec_km for a in run_acts]) if run_acts else 0.0
    avg_hr = np.mean([a.avg_hr for a in run_acts if a.avg_hr]) if run_acts else 0.0

    # Cadence
    cadences = [a.avg_cadence for a in run_acts if a.avg_cadence and a.avg_cadence > 120]
    avg_cad = np.mean(cadences) if cadences else 0.0

    # VO2max / VDOT
    peak_vdot = RunningMetricsCalculator.get_peak_vdot(activities)

    # Threshold
    t_pace_str = format_pace_sec_km(user_profile.threshold_pace_sec_km, user_profile.units)
    t_hr_str = f"{user_profile.lthr} bpm"

    # Weekly Load
    last_7_tss = sum(d.total_tss for d in daily_loads[-7:]) if len(daily_loads) >= 7 else 0.0

    # Efficiency Factor
    recent_efs = [a.efficiency_factor for a in run_acts[-10:] if a.efficiency_factor]
    avg_ef = np.mean(recent_efs) if recent_efs else 0.0

    # Aerobic Decoupling
    recent_decouplings = [a.aerobic_decoupling for a in run_acts[-5:] if a.aerobic_decoupling is not None]
    avg_decoupling = np.mean(recent_decouplings) if recent_decouplings else 0.0

    # Latest Form (TSB) and Fitness (CTL)
    latest_dl = daily_loads[-1]
    ctl = latest_dl.ctl
    tsb = latest_dl.tsb

    # 1. Top KPI Grid Row 1 (Core Running Metrics)
    r1_col1, r1_col2, r1_col3, r1_col4 = st.columns(4)
    with r1_col1:
        render_metric_card(
            label="Total Mileage",
            value=dist_label,
            subtext=f"Last 30 Days: {recent_dist:.1f} km",
            delta=f"{len(activities)} Total Activities",
            delta_type="neutral",
        )
    with r1_col2:
        render_metric_card(
            label="Average Running Pace",
            value=format_pace_sec_km(avg_pace_sec, user_profile.units),
            subtext="All-time running average",
            delta=f"Threshold: {t_pace_str}",
            delta_type="pos",
        )
    with r1_col3:
        render_metric_card(
            label="Avg Heart Rate / Threshold",
            value=f"{avg_hr:.0f} bpm" if avg_hr > 0 else "--",
            subtext=f"LTHR: {t_hr_str} | Max: {user_profile.max_hr}",
            delta="Aerobic Base",
            delta_type="pos",
        )
    with r1_col4:
        render_metric_card(
            label="Running Cadence",
            value=f"{avg_cad:.0f} spm" if avg_cad > 0 else "--",
            subtext="Steps / Minute",
            delta="Optimal: 170-185",
            delta_type="pos" if 170 <= avg_cad <= 185 else "neutral",
        )

    # 2. Top KPI Grid Row 2 (Physiological & Fitness Load)
    r2_col1, r2_col2, r2_col3, r2_col4 = st.columns(4)
    with r2_col1:
        render_metric_card(
            label="Estimated VO2max / VDOT",
            value=f"{peak_vdot:.1f}",
            subtext="Jack Daniels VDOT Formula",
            delta="Aerobic Engine",
            delta_type="pos",
        )
    with r2_col2:
        render_metric_card(
            label="Weekly Training Load",
            value=f"{last_7_tss:.0f} TSS",
            subtext="7-Day Rolling Volume",
            delta=f"Ramp: {latest_dl.ramp_rate_ctl:+.1f}/wk",
            delta_type="pos" if (latest_dl.ramp_rate_ctl or 0) <= 5 else "neg",
        )
    with r2_col3:
        render_metric_card(
            label="HR-to-Pace Efficiency (EF)",
            value=f"{avg_ef:.2f}" if avg_ef > 0 else "--",
            subtext="Speed (m/min) per Heartbeat",
            delta="Aerobic Economy",
            delta_type="pos",
        )
    with r2_col4:
        render_metric_card(
            label="Aerobic Decoupling",
            value=f"{avg_decoupling:.1f}%" if avg_decoupling > 0 else "< 3.0%",
            subtext="Cardiac Drift (Target < 5%)",
            delta="Well Coupled" if avg_decoupling < 5 else "Elevated Drift",
            delta_type="pos" if avg_decoupling < 5 else "neg",
        )

    # 3. Top KPI Grid Row 3 (Form, Readiness & Risk Indicator)
    r3_col1, r3_col2, r3_col3, r3_col4 = st.columns(4)
    with r3_col1:
        render_metric_card(
            label="Fitness (CTL)",
            value=f"{ctl:.1f}",
            subtext="42-Day Chronic Workload",
            delta="Aerobic Foundation",
            delta_type="pos",
        )
    with r3_col2:
        render_metric_card(
            label="Recovery / Form (TSB)",
            value=f"{tsb:+.1f}",
            subtext=latest_dl.form_state,
            delta="Freshness" if tsb > 10 else ("Fatigued" if tsb < -10 else "Optimal"),
            delta_type="pos" if tsb >= -15 else "neg",
        )
    with r3_col3:
        render_metric_card(
            label="Workload Ratio (ACWR)",
            value=f"{risk_report.acwr_value:.2f}",
            subtext="Acute 7d vs Chronic 28d",
            delta="Sweet Spot" if 0.8 <= risk_report.acwr_value <= 1.3 else "High Ramp",
            delta_type="pos" if 0.8 <= risk_report.acwr_value <= 1.3 else "neg",
        )
    with r3_col4:
        render_metric_card(
            label="Training Stress Risk Level",
            value=f"{risk_report.composite_score:.0f} / 100",
            subtext=risk_report.overall_status,
            delta="Multi-Signal Assessment",
            delta_type="pos" if risk_report.composite_score < 50 else "neg",
        )

    # 4. Projected Race Performance Cards
    render_section_header("Estimated Race Performance (5K, 10K, Half & Full Marathon)", icon_name="running")
    render_race_prediction_cards(race_predictions)

    # 5. Interactive PMC Chart
    render_section_header("Fitness, Fatigue & Form Dynamics (Performance Management Chart)", icon_name="overview")
    st.plotly_chart(plot_pmc_chart(daily_df), use_container_width=True)

    # 6. Weekly Mileage & Load
    st.plotly_chart(plot_weekly_mileage_and_load(daily_df, user_profile.units), use_container_width=True)

    # Disclaimer
    render_disclaimer_banner(risk_report.disclaimer)
