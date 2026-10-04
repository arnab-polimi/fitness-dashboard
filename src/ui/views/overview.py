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
from src.analytics.fitness_age import FitnessAgeEngine
from src.ui.components import (
    render_metric_card,
    render_disclaimer_banner,
    render_race_prediction_cards,
    render_fitness_age_card,
)
from src.ui.charts import (
    plot_pmc_chart,
    plot_weekly_mileage_and_load,
    plot_fenix_running_dynamics_chart,
    plot_garmin_hr_zones_breakdown,
    plot_hrv_status_chart,
    plot_body_battery_chart,
)
from src.ui.icons import render_view_header, render_section_header, get_icon_html


def render_overview_view(
    activities: List[Activity],
    daily_loads: List[DailyLoad],
    user_profile: UserProfile,
    race_predictions: List[RacePrediction],
    risk_report: RiskReport,
    daily_df: pd.DataFrame,
    activities_df: pd.DataFrame,
    health_df: Optional[pd.DataFrame] = None,
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

    # Hardware Device Badge (Garmin Fenix 7 Upgrade Indicator)
    has_fenix = any(getattr(a, "device_name", "") == "Garmin Fenix 7" or (getattr(a, "garmin_training_load", None) is not None) for a in activities)
    if has_fenix:
        fenix_icon = get_icon_html("settings", size=18, margin_right=8)
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(193,211,127,0.12) 0%, rgba(56,189,248,0.08) 100%);
                        border: 1px solid rgba(193,211,127,0.3); border-radius: 10px; padding: 10px 16px; margin-bottom: 20px;
                        display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 14px rgba(0,0,0,0.25);">
                <div style="display: flex; align-items: center;">
                    {fenix_icon}
                    <div>
                        <span style="font-weight: 700; color: #f0e2a3; font-size: 0.92rem;">Hardware Synchronized: Garmin Fenix 7</span>
                        <span style="color: #94a3b8; font-size: 0.78rem; margin-left: 10px;">• Elevate v4 Optical Sensor • Overnight HRV • Native EPOC Load • Running Dynamics</span>
                    </div>
                </div>
                <div>
                    <span class="badge" style="background: rgba(193,211,127,0.2); color: #c1d37f; border: 1px solid #c1d37f; font-size: 0.72rem; padding: 3px 10px;">
                        PRIMARY TRACKER ACTIVE
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 4. Garmin Fenix 7 Recovery & Readiness Scorecard (HRV, Body Battery, SpO2, Respiration)
    if health_df is not None and not health_df.empty:
        valid_hrv = health_df[health_df["hrv_last_night"].notna()] if "hrv_last_night" in health_df.columns else pd.DataFrame()
        valid_bb = health_df[health_df["body_battery_max"].notna()] if "body_battery_max" in health_df.columns else pd.DataFrame()
        valid_spo2 = health_df[health_df["spo2_avg"].notna()] if "spo2_avg" in health_df.columns else pd.DataFrame()
        valid_rr = health_df[health_df["rr_waking_avg"].notna()] if "rr_waking_avg" in health_df.columns else pd.DataFrame()

        if not valid_hrv.empty or not valid_bb.empty or not valid_spo2.empty:
            render_section_header("Garmin Fenix 7 Daily Recovery & Physiological Telemetry", icon_name="heartbeat")
            f1, f2, f3, f4 = st.columns(4)

            # HRV Card
            with f1:
                if not valid_hrv.empty:
                    latest_hrv_row = valid_hrv.iloc[-1]
                    hrv_val = latest_hrv_row["hrv_last_night"]
                    hrv_7d = latest_hrv_row.get("hrv_weekly_avg")
                    hrv_st = str(latest_hrv_row.get("hrv_status") or "Balanced")
                    render_metric_card(
                        label="Overnight HRV Status",
                        value=f"{hrv_val:.0f} ms",
                        subtext=f"7d Baseline: {hrv_7d:.0f} ms" if pd.notna(hrv_7d) else "Overnight rMSSD",
                        delta=f"Status: {hrv_st}",
                        delta_type="pos" if "balanced" in hrv_st.lower() else "neg",
                    )
                else:
                    render_metric_card(label="Overnight HRV Status", value="--", subtext="Syncing telemetry", delta="Calibrating", delta_type="neutral")

            # Body Battery Card
            with f2:
                if not valid_bb.empty:
                    latest_bb_row = valid_bb.iloc[-1]
                    bb_max = latest_bb_row.get("body_battery_max")
                    bb_charged = latest_bb_row.get("body_battery_charged")
                    render_metric_card(
                        label="Body Battery™ Level",
                        value=f"{bb_max:.0f} / 100" if pd.notna(bb_max) else "--",
                        subtext=f"Overnight Charge: +{bb_charged:.0f}" if pd.notna(bb_charged) else "Recharge Level",
                        delta="Peak Energy Restored" if (bb_max or 0) >= 85 else "Moderate Reserve",
                        delta_type="pos" if (bb_max or 0) >= 80 else "neg",
                    )
                else:
                    render_metric_card(label="Body Battery™ Level", value="--", subtext="Telemetry pending", delta="Standby", delta_type="neutral")

            # Pulse Ox Card
            with f3:
                if not valid_spo2.empty:
                    latest_spo2_row = valid_spo2.iloc[-1]
                    spo2_val = latest_spo2_row.get("spo2_avg")
                    spo2_min = latest_spo2_row.get("spo2_min")
                    render_metric_card(
                        label="Pulse Ox (SpO2)",
                        value=f"{spo2_val:.1f}%" if pd.notna(spo2_val) else "--",
                        subtext=f"Daily Min: {spo2_min:.0f}%" if pd.notna(spo2_min) else "Blood Saturation",
                        delta="Normal Saturation" if (spo2_val or 0) >= 95 else "Borderline Low",
                        delta_type="pos" if (spo2_val or 0) >= 95 else "neg",
                    )
                else:
                    render_metric_card(label="Pulse Ox (SpO2)", value="--", subtext="Telemetry pending", delta="Standby", delta_type="neutral")

            # Waking Respiration Card
            with f4:
                if not valid_rr.empty:
                    latest_rr_row = valid_rr.iloc[-1]
                    rr_val = latest_rr_row.get("rr_waking_avg")
                    floors = latest_rr_row.get("floors_climbed")
                    render_metric_card(
                        label="Waking Respiration Rate",
                        value=f"{rr_val:.0f} brpm" if pd.notna(rr_val) else "--",
                        subtext=f"Floors Climbed: {floors:.0f}" if pd.notna(floors) else "Breaths / Minute",
                        delta="Optimal Breath Rhythm" if (12 <= (rr_val or 14) <= 18) else "Elevated RR",
                        delta_type="pos" if (12 <= (rr_val or 14) <= 18) else "neutral",
                    )
                else:
                    render_metric_card(label="Waking Respiration", value="--", subtext="Telemetry pending", delta="Standby", delta_type="neutral")

    # 5. Fenix 7 Advanced Running Dynamics & Zone Distribution
    fenix_runs = [a for a in activities if a.sport_type in ["run", "trail_run", "treadmill_run"] and (a.vertical_oscillation_mm or a.ground_contact_time_ms)]
    if fenix_runs:
        render_section_header("Fenix 7 Biomechanical Running Dynamics & Heart Rate Zones", icon_name="running")
        recent_vo = [a.vertical_oscillation_mm for a in fenix_runs if a.vertical_oscillation_mm]
        recent_vr = [a.vertical_ratio for a in fenix_runs if a.vertical_ratio]
        recent_gct = [a.ground_contact_time_ms for a in fenix_runs if a.ground_contact_time_ms]
        recent_stride = [a.stride_length_m for a in fenix_runs if a.stride_length_m]

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            avg_vo = np.mean(recent_vo) if recent_vo else 0.0
            render_metric_card(
                label="Vertical Oscillation",
                value=f"{avg_vo:.1f} mm" if avg_vo > 0 else "--",
                subtext="Vertical Bounce per Stride",
                delta="Optimal: 60-85 mm" if avg_vo <= 85 else "Excess Bounce",
                delta_type="pos" if avg_vo <= 85 else "neg",
            )
        with d2:
            avg_vr = np.mean(recent_vr) if recent_vr else 0.0
            render_metric_card(
                label="Vertical Ratio",
                value=f"{avg_vr:.1f}%" if avg_vr > 0 else "--",
                subtext="Cost of Bounce vs Stride",
                delta="Elite Economy" if avg_vr <= 9.0 else "Good Economy",
                delta_type="pos" if avg_vr <= 9.5 else "neutral",
            )
        with d3:
            avg_gct = np.mean(recent_gct) if recent_gct else 0.0
            render_metric_card(
                label="Ground Contact Time",
                value=f"{avg_gct:.0f} ms" if avg_gct > 0 else "--",
                subtext="Stance Duration",
                delta="Quick Turnover" if avg_gct <= 265 else "Typical Contact",
                delta_type="pos" if avg_gct <= 265 else "neutral",
            )
        with d4:
            avg_str = np.mean(recent_stride) if recent_stride else 0.0
            render_metric_card(
                label="Stride Length",
                value=f"{avg_str:.2f} m" if avg_str > 0 else "--",
                subtext="Running Stride Extension",
                delta="Clean Extension",
                delta_type="pos",
            )

        # Visual charts for zones and dynamics
        zc1, zc2 = st.columns(2)
        with zc1:
            st.plotly_chart(plot_garmin_hr_zones_breakdown(activities_df), use_container_width=True)
        with zc2:
            st.plotly_chart(plot_fenix_running_dynamics_chart(activities_df), use_container_width=True)

    # 6. Fitness Age & Physiological Pattern Recognizer
    fa_report = FitnessAgeEngine.calculate_fitness_age(
        user_profile=user_profile,
        daily_df=daily_df,
        health_df=health_df,
        recent_vdot=peak_vdot
    )
    render_fitness_age_card(fa_report)

    # 7. Projected Race Performance Cards
    render_section_header("Estimated Race Performance (5K, 10K, Half & Full Marathon)", icon_name="running")
    render_race_prediction_cards(race_predictions)

    # 8. Performance Management Chart (PMC)
    render_section_header("Performance Management Dynamics (PMC)", icon_name="overview")
    pmc_fig = plot_pmc_chart(daily_df)
    st.plotly_chart(pmc_fig, use_container_width=True)

    # 9. Weekly Volume & Training Stress
    render_section_header("Weekly Training Load & Distance Trends", icon_name="overview")
    weekly_fig = plot_weekly_mileage_and_load(daily_df, user_profile.units)
    st.plotly_chart(weekly_fig, use_container_width=True)

    # Disclaimer
    render_disclaimer_banner(risk_report.disclaimer)
