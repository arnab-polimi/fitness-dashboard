"""
Hiking & Trail Mountain Dynamics Analytics View.
"""
from typing import List
import streamlit as st
import pandas as pd
import numpy as np

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.ui.components import render_metric_card
from src.ui.charts import plot_hiking_charts
from src.ui.icons import render_view_header, render_section_header, get_icon_html


def render_hiking_view(
    activities: List[Activity],
    user_profile: UserProfile,
    activities_df: pd.DataFrame,
) -> None:
    render_view_header(
        title="Hiking & Trail Elevation Intelligence",
        caption="Track mountain trail distance, cumulative vertical ascent (D+), climbing velocity (VAM), and high-incline cardiovascular load.",
        icon_name="hiking",
    )

    hike_acts = [a for a in activities if a.sport_type in ["hiking", "hike"]]

    if not hike_acts:
        st.info("No hiking activities found in your history yet. Import mountain/trail hikes to see elevation intelligence here.")
        return

    hike_df = pd.DataFrame([a.to_dict() for a in hike_acts])
    if not hike_df.empty:
        hike_df["start_time"] = pd.to_datetime(hike_df["start_time"])

    total_dist_km = sum(a.distance_km for a in hike_acts)
    unit_dist_label = f"{total_dist_km:.1f} km" if user_profile.units == "metric" else f"{total_dist_km * 0.621371:.1f} mi"
    total_sec = sum(a.duration_seconds for a in hike_acts)
    hours = total_sec / 3600.0

    total_ascent = sum(a.elevation_gain_m or 0 for a in hike_acts)
    ascent_label = f"+{total_ascent:,.0f} m" if user_profile.units == "metric" else f"+{total_ascent * 3.28084:,.0f} ft"

    vam = (total_ascent / hours) if hours > 0 else 0.0

    hrs = [a.avg_hr for a in hike_acts if a.avg_hr and a.avg_hr > 0]
    avg_hr = np.mean(hrs) if hrs else 0.0

    cals = sum(a.calories or 0 for a in hike_acts)

    # 1. Top KPI Grid
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            label="Total Vertical Gain (D+)",
            value=ascent_label,
            subtext=f"{len(hike_acts)} Mountain Hikes",
            delta="Cumulative Climb",
            delta_type="pos",
        )
    with c2:
        render_metric_card(
            label="Trail Time & Distance",
            value=f"{hours:.1f} hrs",
            subtext=f"Total Dist: {unit_dist_label}",
            delta=f"{hours/max(1, len(hike_acts)):.1f}h / hike avg",
            delta_type="neutral",
        )
    with c3:
        render_metric_card(
            label="Vertical Ascent Speed",
            value=f"{vam:.0f} m/h",
            subtext="VAM (Climbing Rate)",
            delta="Incline Power",
            delta_type="pos",
        )
    with c4:
        render_metric_card(
            label="Hiking Heart Rate",
            value=f"{avg_hr:.0f} bpm" if avg_hr > 0 else "--",
            subtext=f"Total Burn: {cals:,.0f} kcal",
            delta="Aerobic Incline Load",
            delta_type="pos",
        )

    # 2. Hiking Charts
    if not hike_df.empty:
        st.plotly_chart(plot_hiking_charts(hike_df, user_profile.units), use_container_width=True)

    # 3. Mountain Trail Training Dynamics
    render_section_header("Muscular Endurance & Inclines on the Trail")
    hike_icon_html = get_icon_html("hiking", size=20, margin_right=8)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #101726 0%, #162035 100%); border: 1px solid #1e2c4a; border-left: 4px solid #a855f7; border-radius: 12px; padding: 18px 22px; margin-bottom: 20px;">
        <div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px; display: flex; align-items: center;">
            {hike_icon_html}<span>Muscular Endurance & Tendon Stiffness Adaptation</span>
        </div>
        <div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.6;">
            Sustained hiking under steep inclines develops posterior chain strength (calves, hamstrings, glutes) and foot arch stability without high impact stress.
            Accumulating <strong>{ascent_label}</strong> of vertical gain prepares the aerobic system for trail running, mountain ultra marathons, and hilly road courses.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Activity Log Table
    render_section_header("Hiking Trail History")
    log_data = []
    for a in sorted(hike_acts, key=lambda x: x.start_time, reverse=True):
        log_data.append({
            "Date": a.start_time.strftime("%Y-%m-%d %H:%M"),
            "Title": a.title,
            "Distance": f"{a.distance_km:.1f} km" if user_profile.units == "metric" else f"{a.distance_miles:.1f} mi",
            "Duration": a.formatted_duration,
            "Vertical Gain": f"+{a.elevation_gain_m:.0f} m" if a.elevation_gain_m else "--",
            "Avg HR": f"{a.avg_hr:.0f} bpm" if a.avg_hr else "--",
            "Calories": f"{a.calories:.0f} kcal" if a.calories else "--",
        })
    st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)