"""
Multi-Sport & Cross-Training Unified Overview.
"""
from typing import List
import streamlit as st
import pandas as pd
import numpy as np

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.ui.components import render_metric_card
from src.ui.charts import plot_multisport_distribution, plot_weekly_multisport_stacked
from src.ui.icons import render_view_header, render_section_header, get_icon_html


def render_multisport_view(
    activities: List[Activity],
    user_profile: UserProfile,
    activities_df: pd.DataFrame,
) -> None:
    render_view_header(
        title="Multi-Sport & Cross-Training Ecosystem",
        caption="Comprehensive view combining Running, Walking, Cycling, Hiking, Yoga, Swimming, and Cross-Training.",
        icon_name="multisport",
    )

    if not activities:
        st.info("No activities available yet. Please import or record activities to see your multi-sport intelligence.")
        return

    total_dist_km = sum(a.distance_km for a in activities)
    unit_dist_label = f"{total_dist_km:,.1f} km" if user_profile.units == "metric" else f"{total_dist_km * 0.621371:,.1f} mi"
    total_sec = sum(a.duration_seconds for a in activities)
    hours = total_sec / 3600.0
    cals = sum(a.calories or 0 for a in activities)

    # Breakdown by sport
    sports_count = {}
    for a in activities:
        stype = a.sport_type or "other"
        sports_count[stype] = sports_count.get(stype, 0) + 1

    # 1. Top KPI Grid
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            label="Total Active Time",
            value=f"{hours:.1f} hrs",
            subtext=f"{len(activities)} Total Activities",
            delta="Cross-Training Volume",
            delta_type="pos",
        )
    with c2:
        render_metric_card(
            label="Multi-Sport Distance",
            value=unit_dist_label,
            subtext="All Sports Combined",
            delta=f"{len(sports_count)} Distinct Disciplines",
            delta_type="pos",
        )
    with c3:
        render_metric_card(
            label="Total Calorie Expenditure",
            value=f"{cals:,.0f} kcal",
            subtext="Cumulative Burn",
            delta="Metabolic Engine",
            delta_type="pos",
        )
    with c4:
        run_count = sum(1 for a in activities if a.sport_type in ["run", "trail_run", "treadmill_run"])
        cross_count = len(activities) - run_count
        render_metric_card(
            label="Cross-Training Balance",
            value=f"{cross_count} / {len(activities)}",
            subtext=f"{run_count} Runs • {cross_count} Non-Run",
            delta="Balanced Athlete",
            delta_type="pos",
        )

    # 2. Multi-Sport Charts
    col1, col2 = st.columns([1, 1])
    with col1:
        st.plotly_chart(plot_multisport_distribution(activities_df), use_container_width=True)
    with col2:
        st.plotly_chart(plot_weekly_multisport_stacked(activities_df), use_container_width=True)

    # 3. Unified Activity Log
    render_section_header("Unified Multi-Sport Activity Log", icon_name="multisport")
    log_data = []
    for a in sorted(activities, key=lambda x: x.start_time, reverse=True):
        sport_display = a.sport_type.replace("_", " ").title() if a.sport_type else "Other"

        log_data.append({
            "Date": a.start_time.strftime("%Y-%m-%d %H:%M"),
            "Sport": sport_display,
            "Title": a.title,
            "Distance": f"{a.distance_km:.2f} km" if (a.distance_km > 0 and user_profile.units == 'metric') else (f"{a.distance_miles:.2f} mi" if a.distance_km > 0 else "--"),
            "Duration": a.formatted_duration,
            "Avg HR": f"{a.avg_hr:.0f} bpm" if a.avg_hr else "--",
            "Calories": f"{a.calories:.0f} kcal" if a.calories else "--",
        })
    st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)