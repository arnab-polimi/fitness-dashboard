"""
Sleep & Circadian Recovery Telemetry View.
"""
from typing import Optional
import streamlit as st
import pandas as pd
import numpy as np

from src.models.user_profile import UserProfile
from src.analytics.sleep_score import CircadianTimingCalculator
from src.ui.components import render_metric_card, render_sleep_ui_card
from src.ui.charts import (
    plot_sleep_stage_breakdown_chart,
    plot_sleep_schedule_and_timing_chart,
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
        caption="Analyze sleep architecture (Deep, REM, Light stages), bedtime/wake-up timing trends, recovery scores, and sleep debt.",
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
    df = df.sort_values("date_dt", ascending=True).reset_index(drop=True)

    # 1. Timeframe Filter Selector (Default to Last 30 Days / Last Month)
    t_col1, t_col2 = st.columns([3, 4])
    with t_col1:
        timeframe = st.segmented_control(
            "Timeframe",
            options=[
                "Last 30 Days (Last Month)",
                "Last 7 Days (1 Week)",
                "Last 14 Days (2 Weeks)",
                "Last 60 Days (2 Months)",
                "Last 90 Days (3 Months)",
                "All Available History",
            ],
            default="Last 30 Days (Last Month)",
            key="sleep_view_timeframe",
        ) if hasattr(st, "segmented_control") else st.selectbox(
            "Timeframe",
            [
                "Last 30 Days (Last Month)",
                "Last 7 Days (1 Week)",
                "Last 14 Days (2 Weeks)",
                "Last 60 Days (2 Months)",
                "Last 90 Days (3 Months)",
                "All Available History",
            ],
            index=0,
            key="sleep_view_timeframe",
        )

    max_dt = df["date_dt"].max()
    if timeframe == "Last 7 Days (1 Week)":
        filtered_df = df[df["date_dt"] >= (max_dt - pd.Timedelta(days=7))].copy()
    elif timeframe == "Last 14 Days (2 Weeks)":
        filtered_df = df[df["date_dt"] >= (max_dt - pd.Timedelta(days=14))].copy()
    elif timeframe == "Last 30 Days (Last Month)":
        filtered_df = df[df["date_dt"] >= (max_dt - pd.Timedelta(days=30))].copy()
    elif timeframe == "Last 60 Days (2 Months)":
        filtered_df = df[df["date_dt"] >= (max_dt - pd.Timedelta(days=60))].copy()
    elif timeframe == "Last 90 Days (3 Months)":
        filtered_df = df[df["date_dt"] >= (max_dt - pd.Timedelta(days=90))].copy()
    else:
        filtered_df = df.copy()

    if filtered_df.empty:
        filtered_df = df.copy()

    # Calculate Overall Summary Metrics (from full dataset)
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

    # 7-day rolling metrics & latest night telemetry
    latest_row = df.iloc[-1]
    latest_dur_hrs = (latest_row["sleep_duration_seconds"] / 3600.0) if pd.notna(latest_row.get("sleep_duration_seconds")) else 0.0
    latest_score = latest_row.get("sleep_score")
    latest_rhr = latest_row.get("resting_hr")
    latest_deep_hrs = (latest_row["deep_sleep_seconds"] / 3600.0) if pd.notna(latest_row.get("deep_sleep_seconds")) else 0.0
    latest_rem_hrs = (latest_row["rem_sleep_seconds"] / 3600.0) if pd.notna(latest_row.get("rem_sleep_seconds")) else 0.0
    latest_date_str = pd.to_datetime(latest_row["date"]).strftime("%b %d")

    last_7d_dur = total_dur_hrs.tail(7)
    avg_7d_dur = np.mean(last_7d_dur) if not last_7d_dur.empty else avg_sleep_hrs
    last_7d_scores = scores.tail(7)
    avg_7d_score = np.mean(last_7d_scores) if not last_7d_scores.empty else avg_score
    last_7d_rhr = rhrs.tail(7)
    avg_7d_rhr = np.mean(last_7d_rhr) if not last_7d_rhr.empty else avg_rhr

    weekly_debt_hrs = sum(last_7d_dur - 8.0) if not last_7d_dur.empty else 0.0

    # 2. Top Recovery KPI Grid
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            label=f"Latest Sleep ({latest_date_str})",
            value=f"{latest_dur_hrs:.1f} hrs",
            subtext=f"7-Day Avg: {avg_7d_dur:.1f} hrs / night",
            delta=f"Deep: {latest_deep_hrs:.1f}h | REM: {latest_rem_hrs:.1f}h",
            delta_type="pos" if latest_dur_hrs >= 7.0 else "neg",
        )
    with c2:
        render_metric_card(
            label="Latest Sleep Score",
            value=f"{latest_score:.0f} / 100" if pd.notna(latest_score) else "--",
            subtext=f"7-Day Avg: {avg_7d_score:.0f} / 100",
            delta="Optimal Recovery" if (latest_score or 0) >= 80 else ("Fair Quality" if (latest_score or 0) >= 70 else "Needs Rest"),
            delta_type="pos" if (latest_score or 0) >= 75 else "neg",
        )
    with c3:
        rhr_delta_str = f"{latest_rhr - avg_7d_rhr:+.0f} bpm vs 7d avg" if (pd.notna(latest_rhr) and pd.notna(avg_7d_rhr)) else "Baseline"
        render_metric_card(
            label="Resting Heart Rate",
            value=f"{latest_rhr:.0f} bpm" if pd.notna(latest_rhr) else "--",
            subtext=f"7-Day Baseline: {avg_7d_rhr:.0f} bpm",
            delta=rhr_delta_str,
            delta_type="pos" if (pd.notna(latest_rhr) and latest_rhr <= avg_7d_rhr) else "neg",
        )
    with c4:
        render_metric_card(
            label="7-Day Sleep Debt",
            value=f"{weekly_debt_hrs:+.1f} hrs",
            subtext="Cumulative vs 8h/night (7d)",
            delta="Surplus Rest" if weekly_debt_hrs >= 0 else "Sleep Deficit",
            delta_type="pos" if weekly_debt_hrs >= -2.0 else "neg",
        )

    # Calculate Circadian & Sleep Timing Telemetry for the active timeframe
    circ_df = CircadianTimingCalculator.calculate_timing_dataframe(filtered_df)
    circ_metrics = CircadianTimingCalculator.calculate_circadian_metrics(circ_df)

    # 3. Sleep Architecture & Stage Breakdown (Featured Sleep UI Card + Stage Bar Chart)
    render_section_header("Sleep Architecture & Stage Breakdown", icon_name="sleep")

    # Interactive Night Selector for Sleep UI Card
    nights_list = circ_df.sort_values("date_dt", ascending=False).reset_index(drop=True)
    if not nights_list.empty:
        night_labels = [
            f"{pd.to_datetime(r['date']).strftime('%b %d, %Y')}" + (" (Latest)" if idx == 0 else "")
            for idx, (_, r) in enumerate(nights_list.iterrows())
        ]
        col_c1, col_c2 = st.columns([4, 6])
        with col_c1:
            sel_night_idx = st.selectbox(
                "Inspect Night Telemetry",
                range(len(night_labels)),
                format_func=lambda i: night_labels[i],
                index=0,
                key="selected_sleep_ui_night_idx",
            )
        selected_night_row = nights_list.iloc[sel_night_idx]
        selected_date_label = "Today" if sel_night_idx == 0 else pd.to_datetime(selected_night_row["date"]).strftime("%b %d")

        # Render the high-fidelity Sleep Architecture UI Card matching sleep UI.png
        render_sleep_ui_card(selected_night_row, date_label=selected_date_label, goal_hours=8.0)

    st.plotly_chart(
        plot_sleep_stage_breakdown_chart(
            filtered_df,
            title=f"<b>Daily Sleep Architecture & Stage Distribution ({timeframe})</b>",
        ),
        use_container_width=True,
    )

    # 4. Sleep Schedule & Circadian Timing Trends (Bedtime & Wake-Up Times)
    render_section_header("Sleep Schedule & Circadian Timing Trends", icon_name="sleep")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_metric_card(
            label="Average Bedtime",
            value=circ_metrics["avg_bedtime_str"],
            subtext=f"Consistency: ±{circ_metrics['bed_variability_min']:.0f} mins",
            delta="Stable Onset" if circ_metrics["bed_variability_min"] <= 35 else "Variable Bedtime",
            delta_type="pos" if circ_metrics["bed_variability_min"] <= 35 else "neg",
        )
    with k2:
        render_metric_card(
            label="Average Wake Time",
            value=circ_metrics["avg_wake_str"],
            subtext=f"Consistency: ±{circ_metrics['wake_variability_min']:.0f} mins",
            delta="Stable Awakening" if circ_metrics["wake_variability_min"] <= 35 else "Variable Wake",
            delta_type="pos" if circ_metrics["wake_variability_min"] <= 35 else "neg",
        )
    with k3:
        render_metric_card(
            label="Sleep Midpoint",
            value=circ_metrics["midpoint_str"],
            subtext="Circadian Phase Anchor",
            delta="Mid-Sleep Core",
            delta_type="neutral",
        )
    with k4:
        render_metric_card(
            label="Circadian Regularity",
            value=f"{circ_metrics['regularity_score']:.0f} / 100",
            subtext=circ_metrics["consistency_label"],
            delta="Optimal Sync" if circ_metrics["regularity_score"] >= 80 else "Irregular Drift",
            delta_type="pos" if circ_metrics["regularity_score"] >= 75 else "neg",
        )

    st.plotly_chart(
        plot_sleep_schedule_and_timing_chart(
            filtered_df,
            title=f"<b>Sleeping Time & Waking Up Time Trend ({timeframe})</b>",
        ),
        use_container_width=True,
    )

    # 5. Sleep Score & Resting HR Dynamics
    render_section_header("Sleep Score & Resting HR Dynamics", icon_name="heartbeat")
    st.plotly_chart(plot_sleep_score_and_rhr_chart(filtered_df), use_container_width=True)

    # 6. Circadian Recovery & Sports Science Insights Callout
    render_section_header("Circadian Recovery & Sports Science Insights", icon_name="sleep")
    sleep_icon = get_icon_html("sleep", size=20, margin_right=8)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); border: 1px solid #3b322e; border-left: 4px solid #c1d37f; border-radius: 12px; padding: 18px 22px; margin-bottom: 24px;">
        <div style="font-size: 0.95rem; font-weight: 700; color: #f0e2a3; margin-bottom: 8px; display: flex; align-items: center;">
            {sleep_icon}<span>Physiological Sleep Stages, Circadian Stability & Athletic Performance</span>
        </div>
        <div style="font-size: 0.84rem; color: #c8b99c; line-height: 1.6;">
            • <strong>Circadian Regularity (Avg Bedtime {circ_metrics['avg_bedtime_str']} | Wake {circ_metrics['avg_wake_str']}):</strong> Going to sleep and waking up at consistent times anchors your suprachiasmatic nucleus (SCN), ensuring consistent melatonin and cortisol rhythms for deeper physical recovery.<br>
            • <strong>Slow-Wave Deep Sleep ({avg_deep_hrs:.1f}h avg):</strong> Triggers Human Growth Hormone (HGH) release, protein synthesis, and muscle tissue repair after heavy aerobic workloads.<br>
            • <strong>REM Sleep ({avg_rem_hrs:.1f}h avg):</strong> Consolidates motor learning, neuromuscular coordination, and central nervous system (CNS) fatigue recovery.<br>
            • <strong>Resting HR ({avg_rhr:.0f} bpm avg):</strong> Your primary autonomic nervous system indicator. An elevated RHR (+3–5 bpm above baseline) indicates incomplete recovery, systemic inflammation, or impending illness.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 7. Enhanced Sleep History Log Table
    render_section_header("Daily Sleep Log History", icon_name="sleep")
    log_rows = []
    for _, r in circ_df.sort_values("date_dt", ascending=False).iterrows():
        dur_h = (r["sleep_duration_seconds"] / 3600.0) if pd.notna(r.get("sleep_duration_seconds")) else 0.0
        deep_h = (r["deep_sleep_seconds"] / 3600.0) if pd.notna(r.get("deep_sleep_seconds")) else 0.0
        rem_h = (r["rem_sleep_seconds"] / 3600.0) if pd.notna(r.get("rem_sleep_seconds")) else 0.0
        light_h = (r["light_sleep_seconds"] / 3600.0) if pd.notna(r.get("light_sleep_seconds")) else 0.0
        score_val = f"{int(r['sleep_score'])}/100" if pd.notna(r.get("sleep_score")) else "--"
        rhr_val = f"{int(r['resting_hr'])} bpm" if pd.notna(r.get("resting_hr")) else "--"
        bed_str = r.get("bed_str") or "--"
        wake_str = r.get("wake_str") or "--"

        log_rows.append({
            "Date": pd.to_datetime(r["date"]).strftime("%Y-%m-%d"),
            "Bedtime": bed_str,
            "Wake Time": wake_str,
            "Total Sleep": f"{dur_h:.1f} hrs",
            "Sleep Score": score_val,
            "Deep Sleep": f"{deep_h:.1f} hrs",
            "REM Sleep": f"{rem_h:.1f} hrs",
            "Light Sleep": f"{light_h:.1f} hrs",
            "Resting HR": rhr_val,
        })
    st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)
