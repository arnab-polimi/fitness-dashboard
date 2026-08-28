"""
Yoga, Mobility & Parasympathetic Recovery Analytics View.
"""
from typing import List
import streamlit as st
import pandas as pd
import numpy as np

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.ui.components import render_metric_card
from src.ui.charts import plot_yoga_charts
from src.ui.icons import render_view_header, render_section_header, get_icon_html


def render_yoga_view(
    activities: List[Activity],
    user_profile: UserProfile,
    activities_df: pd.DataFrame,
) -> None:
    render_view_header(
        title="Yoga, Mobility & Autonomic Recovery",
        caption="Track mindful movement, flexibility sessions, parasympathetic nervous system calming, and active recovery practices.",
        icon_name="yoga",
    )

    yoga_acts = [a for a in activities if a.sport_type in ["yoga", "pilates", "mobility", "stretch"]]

    if not yoga_acts:
        st.info("No yoga or mobility sessions found in your history yet. Log your yoga or stretching sessions to see recovery insights here.")
        return

    yoga_df = pd.DataFrame([a.to_dict() for a in yoga_acts])
    if not yoga_df.empty:
        yoga_df["start_time"] = pd.to_datetime(yoga_df["start_time"])

    total_sec = sum(a.duration_seconds for a in yoga_acts)
    total_mins = total_sec / 60.0
    hours = total_sec / 3600.0

    hrs = [a.avg_hr for a in yoga_acts if a.avg_hr and a.avg_hr > 0]
    avg_hr = np.mean(hrs) if hrs else 0.0

    cals = sum(a.calories or 0 for a in yoga_acts)

    # 1. Top KPI Grid
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            label="Total Yoga Sessions",
            value=f"{len(yoga_acts)} Practices",
            subtext="Mindful Movement",
            delta="Consistency Streak",
            delta_type="pos",
        )
    with c2:
        render_metric_card(
            label="Total Mat Time",
            value=f"{hours:.1f} hrs",
            subtext=f"{int(total_mins)} Total Minutes",
            delta=f"{int(total_mins/max(1, len(yoga_acts)))}m / session avg",
            delta_type="pos",
        )
    with c3:
        render_metric_card(
            label="Parasympathetic HR",
            value=f"{avg_hr:.0f} bpm" if avg_hr > 0 else "--",
            subtext="Autonomic Calming Tone",
            delta="Rest & Restore",
            delta_type="pos",
        )
    with c4:
        render_metric_card(
            label="Energy Expenditure",
            value=f"{cals:.0f} kcal",
            subtext="Gentle Metabolic Flow",
            delta="Zero Impact",
            delta_type="pos",
        )

    # 2. Yoga Charts
    if not yoga_df.empty:
        st.plotly_chart(plot_yoga_charts(yoga_df), use_container_width=True)

    # 3. Yoga & Autonomic Restoration Mechanics
    render_section_header("Restoring Parasympathetic Balance & Fascial Mobility")
    yoga_icon_html = get_icon_html("yoga", size=20, margin_right=8)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #101726 0%, #162035 100%); border: 1px solid #1e2c4a; border-left: 4px solid #ec4899; border-radius: 12px; padding: 18px 22px; margin-bottom: 20px;">
        <div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px; display: flex; align-items: center;">
            {yoga_icon_html}<span>Autonomic Restoration & Injury Prevention</span>
        </div>
        <div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.6;">
            Intense training shifts the nervous system into sympathetic "fight or flight" dominance. Yoga practices with an average heart rate of <strong>{avg_hr:.0f} bpm</strong> activate the vagus nerve, accelerating heart rate variability (HRV) recovery, lowering systemic cortisol, and relieving hip and hamstring tightness.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Activity Log Table
    render_section_header("Yoga & Mobility Session History", icon_name="yoga")
    log_data = []
    for a in sorted(yoga_acts, key=lambda x: x.start_time, reverse=True):
        log_data.append({
            "Date": a.start_time.strftime("%Y-%m-%d %H:%M"),
            "Title": a.title,
            "Duration": a.formatted_duration,
            "Avg HR": f"{a.avg_hr:.0f} bpm" if a.avg_hr else "--",
            "Max HR": f"{a.max_hr:.0f} bpm" if a.max_hr else "--",
            "Calories": f"{a.calories:.0f} kcal" if a.calories else "--",
        })
    st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)