"""
Walking & Active Recovery Analytics View.
"""
from typing import List
import streamlit as st
import pandas as pd
import numpy as np

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.analytics.running_metrics import format_pace_sec_km
from src.ui.components import render_metric_card
from src.ui.charts import plot_walking_charts
from src.ui.icons import render_view_header, render_section_header, get_icon_html


def render_walking_view(
    activities: List[Activity],
    user_profile: UserProfile,
    activities_df: pd.DataFrame,
) -> None:
    render_view_header(
        title="Walking & Active Recovery Intelligence",
        caption="Track walking volume, active daily movement, low-stress aerobic conditioning, and active recovery metrics.",
        icon_name="walking",
    )

    walk_acts = [a for a in activities if a.sport_type in ["walking", "walk"]]

    if not walk_acts:
        st.info("No walking activities found in your history yet. Import walking activities or log walks to see metrics here.")
        return

    walk_df = pd.DataFrame([a.to_dict() for a in walk_acts])
    if not walk_df.empty:
        walk_df["start_time"] = pd.to_datetime(walk_df["start_time"])

    total_dist_km = sum(a.distance_km for a in walk_acts)
    unit_dist_label = f"{total_dist_km:.2f} km" if user_profile.units == "metric" else f"{total_dist_km * 0.621371:.2f} mi"
    total_sec = sum(a.duration_seconds for a in walk_acts)
    hours = total_sec / 3600.0

    paces = [a.effective_pace_sec_km for a in walk_acts if a.effective_pace_sec_km > 0]
    avg_pace_sec = np.mean(paces) if paces else 0.0
    avg_speed_kmh = (total_dist_km / hours) if hours > 0 else 0.0

    hrs = [a.avg_hr for a in walk_acts if a.avg_hr and a.avg_hr > 0]
    avg_hr = np.mean(hrs) if hrs else 0.0

    cals = sum(a.calories or 0 for a in walk_acts)
    elev = sum(a.elevation_gain_m or 0 for a in walk_acts)
    elev_label = f"+{elev:.0f} m" if user_profile.units == "metric" else f"+{elev * 3.28084:.0f} ft"

    est_steps = int(total_dist_km * 1300)

    # 1. Top KPI Grid
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            label="Total Walk Distance",
            value=unit_dist_label,
            subtext=f"{len(walk_acts)} Total Walks",
            delta=f"{est_steps:,} Est. Steps",
            delta_type="pos",
        )
    with c2:
        render_metric_card(
            label="Active Walking Time",
            value=f"{hours:.1f} hrs",
            subtext=f"Total: {int(total_sec//60)} mins",
            delta=f"{hours/max(1, len(walk_acts)):.1f}h / walk avg",
            delta_type="neutral",
        )
    with c3:
        render_metric_card(
            label="Average Walking Pace",
            value=format_pace_sec_km(avg_pace_sec, user_profile.units),
            subtext=f"Speed: {avg_speed_kmh:.1f} km/h",
            delta="Zone 1 Aerobic",
            delta_type="pos",
        )
    with c4:
        render_metric_card(
            label="Walking Heart Rate",
            value=f"{avg_hr:.0f} bpm" if avg_hr > 0 else "--",
            subtext=f"Burn: {cals:.0f} kcal | Elev: {elev_label}",
            delta="Active Recovery",
            delta_type="pos",
        )

    # 2. Walking Charts
    if not walk_df.empty:
        st.plotly_chart(plot_walking_charts(walk_df, user_profile.units), use_container_width=True)

    # 3. Active Recovery & Physiological Benefits
    render_section_header("Active Recovery & Aerobic Base Mechanics")
    walk_icon_html = get_icon_html("walking", size=20, margin_right=8)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #101726 0%, #162035 100%); border: 1px solid #1e2c4a; border-left: 4px solid #10b981; border-radius: 12px; padding: 18px 22px; margin-bottom: 20px;">
        <div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px; display: flex; align-items: center;">
            {walk_icon_html}<span>Why Walking is Powerful for Endurance Athletes</span>
        </div>
        <div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.6;">
            Walking promotes <strong>non-fatiguing active recovery</strong> by stimulating lymphatic drainage and capillary blood flow without the eccentric muscle-damaging ground reaction forces of running (1.0–1.2× bodyweight vs. 2.5–3.0×).
            With an average walking heart rate of <strong>{avg_hr:.0f} bpm</strong>, walking helps facilitate aerobic lipid oxidation and parasympathetic nervous system recovery.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Activity Log Table
    render_section_header("Walking Activity History", icon_name="walking")
    log_data = []
    for a in sorted(walk_acts, key=lambda x: x.start_time, reverse=True):
        log_data.append({
            "Date": a.start_time.strftime("%Y-%m-%d %H:%M"),
            "Title": a.title,
            "Distance": f"{a.distance_km:.2f} km" if user_profile.units == "metric" else f"{a.distance_miles:.2f} mi",
            "Duration": a.formatted_duration,
            "Pace": format_pace_sec_km(a.effective_pace_sec_km, user_profile.units),
            "Avg HR": f"{a.avg_hr:.0f} bpm" if a.avg_hr else "--",
            "Calories": f"{a.calories:.0f} kcal" if a.calories else "--",
            "Elevation": f"+{a.elevation_gain_m:.0f} m" if a.elevation_gain_m else "--",
        })
    st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)