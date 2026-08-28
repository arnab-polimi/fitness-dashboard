"""
Sleep & Circadian Recovery Telemetry View.
"""
from typing import Optional
import streamlit as st
import pandas as pd
import numpy as np

from src.models.user_profile import UserProfile
from src.ui.components import render_metric_card
from src.ui.charts import (
    plot_sleep_stage_breakdown_chart,
    plot_sleep_score_and_rhr_chart,
)
from src.ui.icons import render_view_header, render_section_header, get_icon_html


def render_sleep_view(
    health_df: Optional[pd.DataFrame],
    user_profile: UserProfile,
) -> None:
    """Renders Sleep Architecture & Circadian Recovery View."""
    render_view_header(
        title="Sleep & Circadian Recovery Intelligence",
        caption="Analyze sleep architecture (Deep, REM, Light stages), sleep score trends, resting heart rate recovery, and sleep debt.",
        icon_name="sleep",
    )

    if health_df is None or health_df.empty or "sleep_duration_seconds" not in health_df.columns:
        st.info("No sleep telemetry data loaded yet.")
        st.caption("You can sync your GarminDb database or load synthetic sample health telemetry from the Data Import tab.")
        return

    df = health_df[health_df["sleep_duration_seconds"].notna() & (health_df["sleep_duration_seconds"] > 0)].copy()
    if df.empty:
        st.info("No sleep records found in the database.")
        return

    df["date_dt"] = pd.to_datetime(df["date"])
    df = df.sort_values("date_dt", ascending=True)

    # Calculate Summary Metrics
    total_dur_hrs = df["sleep_duration_seconds"] / 3600.0
    avg_sleep_hrs = np.mean(total_dur_hrs)
    
    scores = df["sleep_score"].dropna()
    avg_score = np.mean(scores) if not scores.empty else 0.0

    deep_hrs = (df["deep_sleep_seconds"].dropna() / 3600.0) if "deep_sleep_seconds" in df.columns else pd.Series()
    avg_deep_hrs = np.mean(deep_hrs) if not deep_hrs.empty else 0.0

    rem_hrs = (df["rem_sleep_seconds"].dropna() / 3600.0) if "rem_sleep_seconds" in df.columns else pd.Series()
    avg_rem_hrs = np.mean(rem_hrs) if not rem_hrs.empty else 0.0

    rhrs = df["resting_hr"].dropna() if "resting_hr" in df.columns else pd.Series()
    avg_rhr = np.mean(rhrs) if not rhrs.empty else 0.0

    # 7-day rolling sleep debt vs 8h target
    last_7d = total_dur_hrs.tail(7)
    weekly_debt_hrs = sum(last_7d - 8.0) if not last_7d.empty else 0.0

    # 1. Top KPI Grid
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            label="Avg Sleep Duration",
            value=f"{avg_sleep_hrs:.1f} hrs",
            subtext="Target: 8.0 hrs / night",
            delta=f"Deep: {avg_deep_hrs:.1f}h | REM: {avg_rem_hrs:.1f}h",
            delta_type="pos" if avg_sleep_hrs >= 7.5 else "neg",
        )
    with c2:
        render_metric_card(
            label="Sleep Quality Score",
            value=f"{avg_score:.0f} / 100",
            subtext="Garmin Sleep Index",
            delta="Optimal Recovery" if avg_score >= 80 else "Needs Rest",
            delta_type="pos" if avg_score >= 78 else "neg",
        )
    with c3:
        render_metric_card(
            label="Resting Heart Rate",
            value=f"{avg_rhr:.0f} bpm" if avg_rhr > 0 else "--",
            subtext="Nightly Baseline",
            delta="Cardiovascular Recovery",
            delta_type="pos",
        )
    with c4:
        render_metric_card(
            label="7-Day Sleep Debt",
            value=f"{weekly_debt_hrs:+.1f} hrs",
            subtext="Cumulative vs 8h/night",
            delta="Surplus Rest" if weekly_debt_hrs >= 0 else "Sleep Deficit",
            delta_type="pos" if weekly_debt_hrs >= -2.0 else "neg",
        )

    # 2. Sleep Architecture Charts
    render_section_header("Sleep Architecture & Stage Breakdown", icon_name="sleep")
    st.plotly_chart(plot_sleep_stage_breakdown_chart(df), use_container_width=True)

    render_section_header("Sleep Score & Resting HR Dynamics", icon_name="heartbeat")
    st.plotly_chart(plot_sleep_score_and_rhr_chart(df), use_container_width=True)

    # 3. Circadian Recovery & Sleep Science Callout
    render_section_header("Circadian Recovery & Sports Science Insights", icon_name="sleep")
    sleep_icon = get_icon_html("sleep", size=20, margin_right=8)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); border: 1px solid #3b322e; border-left: 4px solid #c1d37f; border-radius: 12px; padding: 18px 22px; margin-bottom: 24px;">
        <div style="font-size: 0.95rem; font-weight: 700; color: #f0e2a3; margin-bottom: 8px; display: flex; align-items: center;">
            {sleep_icon}<span>Physiological Sleep Stages & Endurance Performance</span>
        </div>
        <div style="font-size: 0.84rem; color: #c8b99c; line-height: 1.6;">
            • <strong>Slow-Wave Deep Sleep ({avg_deep_hrs:.1f}h avg)</strong> triggers Human Growth Hormone (HGH) release, protein synthesis, and muscle tissue repair after heavy aerobic workloads.<br>
            • <strong>REM Sleep ({avg_rem_hrs:.1f}h avg)</strong> consolidates motor learning, neuromuscular coordination, and central nervous system (CNS) fatigue recovery.<br>
            • <strong>Resting HR ({avg_rhr:.0f} bpm avg)</strong> is your primary autonomic nervous system indicator. An elevated RHR (+3–5 bpm above baseline) indicates incomplete recovery or impending illness.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Sleep History Log Table
    render_section_header("Daily Sleep Log History", icon_name="sleep")
    log_rows = []
    for _, r in df.sort_values("date_dt", ascending=False).iterrows():
        dur_h = (r["sleep_duration_seconds"] / 3600.0) if pd.notna(r.get("sleep_duration_seconds")) else 0.0
        deep_h = (r["deep_sleep_seconds"] / 3600.0) if pd.notna(r.get("deep_sleep_seconds")) else 0.0
        rem_h = (r["rem_sleep_seconds"] / 3600.0) if pd.notna(r.get("rem_sleep_seconds")) else 0.0
        light_h = (r["light_sleep_seconds"] / 3600.0) if pd.notna(r.get("light_sleep_seconds")) else 0.0
        score_val = f"{int(r['sleep_score'])}/100" if pd.notna(r.get("sleep_score")) else "--"
        rhr_val = f"{int(r['resting_hr'])} bpm" if pd.notna(r.get("resting_hr")) else "--"

        log_rows.append({
            "Date": pd.to_datetime(r["date"]).strftime("%Y-%m-%d"),
            "Total Sleep": f"{dur_h:.1f} hrs",
            "Sleep Score": score_val,
            "Deep Sleep": f"{deep_h:.1f} hrs",
            "REM Sleep": f"{rem_h:.1f} hrs",
            "Light Sleep": f"{light_h:.1f} hrs",
            "Resting HR": rhr_val,
        })
    st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)
