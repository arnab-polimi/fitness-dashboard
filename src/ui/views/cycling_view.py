"""
Cycling & Biking Telemetry Analytics View.
"""
from typing import List
import streamlit as st
import pandas as pd
import numpy as np

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.ui.components import render_metric_card
from src.ui.charts import plot_cycling_charts
from src.ui.icons import render_view_header, render_section_header, get_icon_html


def render_cycling_view(
    activities: List[Activity],
    user_profile: UserProfile,
    activities_df: pd.DataFrame,
) -> None:
    render_view_header(
        title="Cycling & Saddle Telemetry",
        caption="Track cycling distance, average speeds, saddle time, aerobic speed efficiency, and elevation climb.",
        icon_name="cycling",
    )

    bike_acts = [a for a in activities if a.sport_type in ["cycling", "bike", "ride"]]

    if not bike_acts:
        st.info("No cycling activities found in your history yet. Import Garmin/Strava rides to see cycling telemetry here.")
        return

    bike_df = pd.DataFrame([a.to_dict() for a in bike_acts])
    if not bike_df.empty:
        bike_df["start_time"] = pd.to_datetime(bike_df["start_time"])

    total_dist_km = sum(a.distance_km for a in bike_acts)
    unit_dist_label = f"{total_dist_km:.1f} km" if user_profile.units == "metric" else f"{total_dist_km * 0.621371:.1f} mi"
    total_sec = sum(a.duration_seconds for a in bike_acts)
    hours = total_sec / 3600.0

    speeds = [a.speed_kmh for a in bike_acts if a.speed_kmh > 0]
    avg_speed_kmh = np.mean(speeds) if speeds else ((total_dist_km / hours) if hours > 0 else 0.0)
    speed_label = f"{avg_speed_kmh:.1f} km/h" if user_profile.units == "metric" else f"{avg_speed_kmh * 0.621371:.1f} mph"

    hrs = [a.avg_hr for a in bike_acts if a.avg_hr and a.avg_hr > 0]
    avg_hr = np.mean(hrs) if hrs else 0.0

    cals = sum(a.calories or 0 for a in bike_acts)
    elev = sum(a.elevation_gain_m or 0 for a in bike_acts)
    elev_label = f"+{elev:.0f} m" if user_profile.units == "metric" else f"+{elev * 3.28084:.0f} ft"

    longest_km = max(a.distance_km for a in bike_acts)
    longest_label = f"{longest_km:.1f} km" if user_profile.units == "metric" else f"{longest_km * 0.621371:.1f} mi"

    # 1. Top KPI Grid
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            label="Total Saddle Distance",
            value=unit_dist_label,
            subtext=f"{len(bike_acts)} Total Rides",
            delta=f"Longest: {longest_label}",
            delta_type="pos",
        )
    with c2:
        render_metric_card(
            label="Total Saddle Time",
            value=f"{hours:.1f} hrs",
            subtext=f"Avg: {hours/max(1, len(bike_acts)):.1f}h / ride",
            delta="Aerobic Volume",
            delta_type="pos",
        )
    with c3:
        render_metric_card(
            label="Average Speed",
            value=speed_label,
            subtext=f"Total Burn: {cals:.0f} kcal",
            delta="Cruising Velocity",
            delta_type="pos",
        )
    with c4:
        render_metric_card(
            label="Cycling Heart Rate",
            value=f"{avg_hr:.0f} bpm" if avg_hr > 0 else "--",
            subtext=f"Total Ascent: {elev_label}",
            delta="Cardio Load",
            delta_type="neutral",
        )

    # 2. Cycling Charts
    if not bike_df.empty:
        st.plotly_chart(plot_cycling_charts(bike_df, user_profile.units), use_container_width=True)

    # 3. Cycling Cross-Training Dynamics
    render_section_header("Cycling Cross-Training Benefits for Runners")
    bike_icon_html = get_icon_html("bike", size=20, margin_right=8)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #101726 0%, #162035 100%); border: 1px solid #1e2c4a; border-left: 4px solid #f59e0b; border-radius: 12px; padding: 18px 22px; margin-bottom: 20px;">
        <div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px; display: flex; align-items: center;">
            {bike_icon_html}<span>Non-Impact Cardiovascular Engine Building</span>
        </div>
        <div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.6;">
            Cycling provides high-volume aerobic stimulus and quad/glute concentric strengthening without pounding the joints, bones, or Achilles tendons. 
            Logging <strong>{hours:.1f} hours</strong> in the saddle builds stroke volume and mitochondrial density while minimizing orthopedic injury risk.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Activity Log Table
    render_section_header("Cycling Activity History", icon_name="cycling")
    log_data = []
    for a in sorted(bike_acts, key=lambda x: x.start_time, reverse=True):
        spd = a.speed_kmh * (1.0 if user_profile.units == "metric" else 0.621371)
        spd_u = "km/h" if user_profile.units == "metric" else "mph"
        log_data.append({
            "Date": a.start_time.strftime("%Y-%m-%d %H:%M"),
            "Title": a.title,
            "Distance": f"{a.distance_km:.1f} km" if user_profile.units == "metric" else f"{a.distance_miles:.1f} mi",
            "Duration": a.formatted_duration,
            "Avg Speed": f"{spd:.1f} {spd_u}",
            "Avg HR": f"{a.avg_hr:.0f} bpm" if a.avg_hr else "--",
            "Calories": f"{a.calories:.0f} kcal" if a.calories else "--",
            "Ascent": f"+{a.elevation_gain_m:.0f} m" if a.elevation_gain_m else "--",
        })
    st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)