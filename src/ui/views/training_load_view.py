"""
Training Load & Performance Management (PMC) View.
"""
from typing import List, Optional
import streamlit as st
import pandas as pd

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.models.metrics import DailyLoad
from src.ui.components import render_form_dynamics_hero
from src.ui.charts import (
    plot_pmc_chart,
    plot_form_corridor_chart,
    plot_weekly_mileage_and_load,
    PLOT_LAYOUT_DARK,
)
from src.ui.icons import render_view_header
import plotly.graph_objects as go


def render_training_load_view(
    activities: List[Activity],
    daily_loads: List[DailyLoad],
    user_profile: UserProfile,
    daily_df: pd.DataFrame,
) -> None:
    render_view_header(
        title="Training Load & Performance Management Dynamics",
        caption=(
            "Exponentially Weighted Moving Averages (EWMA) tracking Chronic Training Load (Fitness), "
            "Acute Training Load (Fatigue), and Training Stress Balance (Form & Readiness)."
        ),
        icon_name="overview",
    )

    if daily_df.empty or not daily_loads:
        st.info("No training data available. Please import activities to generate your Performance Management Chart.")
        return

    # 1. Top Hero Telemetry & Form Spectrum Bar
    latest_dl = daily_loads[-1]
    prev_7d_dl = daily_loads[-8] if len(daily_loads) >= 8 else (daily_loads[0] if daily_loads else None)
    render_form_dynamics_hero(
        latest=latest_dl,
        prev_7d=prev_7d_dl,
        acwr=latest_dl.acwr,
        ramp_rate=latest_dl.ramp_rate_ctl,
    )

    # 2. Controls & Timeframe Selector
    t_col1, t_col2 = st.columns([3, 4])
    with t_col1:
        timeframe = st.segmented_control(
            "Select Timeframe",
            options=["Last 30 Days", "Last 90 Days", "Last 180 Days", "Last 1 Year", "All Time"],
            default="Last 90 Days",
        ) if hasattr(st, "segmented_control") else st.selectbox(
            "Select Timeframe",
            ["Last 30 Days", "Last 90 Days", "Last 180 Days", "Last 1 Year", "All Time"],
            index=1,
        )

    # Filter dataframe based on timeframe
    df = daily_df.copy()
    df["date_dt"] = pd.to_datetime(df["date"]).dt.date
    today = pd.to_datetime("now").date()

    if timeframe == "Last 30 Days":
        cutoff = today - pd.Timedelta(days=30)
        df = df[df["date_dt"] >= cutoff]
    elif timeframe == "Last 90 Days":
        cutoff = today - pd.Timedelta(days=90)
        df = df[df["date_dt"] >= cutoff]
    elif timeframe == "Last 180 Days":
        cutoff = today - pd.Timedelta(days=180)
        df = df[df["date_dt"] >= cutoff]
    elif timeframe == "Last 1 Year":
        cutoff = today - pd.Timedelta(days=365)
        df = df[df["date_dt"] >= cutoff]

    # 3. Tabbed Visual Analytics
    tab_pmc, tab_form, tab_weekly, tab_monotony = st.tabs([
        "Performance Management (PMC)",
        "Form & Readiness Corridor",
        "Weekly Volume & Progression",
        "Training Monotony & Strain",
    ])

    with tab_pmc:
        st.plotly_chart(plot_pmc_chart(df), use_container_width=True)

    with tab_form:
        st.plotly_chart(plot_form_corridor_chart(df), use_container_width=True)
        st.caption(
            "**Form Corridor Strategy:** During build blocks, maintain TSB between **-10 and -30** to create progressive overload. "
            "For race day or key time trials, taper training volume until TSB ascends into the **+10 to +25** peak zone."
        )

    with tab_weekly:
        st.plotly_chart(plot_weekly_mileage_and_load(df, user_profile.units), use_container_width=True)

    with tab_monotony:
        st.markdown("#### Foster's Monotony & Strain Index")
        st.caption("Monotony measures day-to-day training uniformity. High monotony (>1.5) combined with high load triggers elevated strain.")

        fig_monotony = go.Figure()
        if "monotony" in df.columns and df["monotony"].notna().any():
            fig_monotony.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["monotony"],
                    name="Training Monotony",
                    line=dict(color="#06b6d4", width=2.5, shape="spline"),
                    fill="tozeroy",
                    fillcolor="rgba(6, 182, 212, 0.08)",
                )
            )
            fig_monotony.add_hline(
                y=1.5,
                line_dash="dash",
                line_color="#f59e0b",
                line_width=1.5,
                annotation_text="Caution Baseline (>1.5)",
                annotation_position="top left",
                annotation_font=dict(size=10, color="#f59e0b"),
            )
            fig_monotony.add_hline(
                y=2.0,
                line_dash="dot",
                line_color="#ef4444",
                line_width=1.5,
                annotation_text="High Monotony Danger (>2.0)",
                annotation_position="top left",
                annotation_font=dict(size=10, color="#ef4444"),
            )
        layout = dict(PLOT_LAYOUT_DARK)
        layout.update(
            title="<b>7-Day Rolling Training Monotony (Load Variance)</b>",
            yaxis_title="Monotony Score",
            height=340,
        )
        fig_monotony.update_layout(layout)
        st.plotly_chart(fig_monotony, use_container_width=True)

    # 4. Educational & Physiological Mechanics
    with st.expander("Sports Science Guide: Banister TRIMP, hrTSS, CTL, ATL & TSB"):
        st.markdown("""
        ### The Science of Banister's Impulse-Response Model
        
        The **Performance Management Chart (PMC)** models how your body adapts to training stress over time through two competing physiological responses:

        1. **Fitness (CTL — Chronic Training Load)**:
           - **Exponential Time Constant ($\\tau = 42$ days)**
           - Represents your accumulated aerobic capacity, mitochondrial density, capillary network, and cardiovascular endurance base.
           - Builds steadily over weeks and months of consistent training volume.

        2. **Fatigue (ATL — Acute Training Load)**:
           - **Exponential Time Constant ($\\tau = 7$ days)**
           - Represents short-term physiological fatigue, muscle glycogen depletion, central nervous system tiredness, and tissue micro-trauma.
           - Rises rapidly following hard workouts and decays quickly with rest.

        3. **Form (TSB — Training Stress Balance)**:
           - **Formula**: $\\text{TSB} = \\text{CTL} - \\text{ATL}$
           - Reflects whether you are primed for racing or fatigued from building:
             - **+10 to +25 (Race Ready / Fresh)**: Fatigue has cleared while fitness is retained. Ideal peak performance window.
             - **-10 to +10 (Neutral / Productive)**: Balanced adaptation and recovery for consistent maintenance.
             - **-30 to -10 (Optimal Progressive Overload)**: Building chronic fitness through manageable, productive training fatigue.
             - **< -30 (High Fatigue / Overreaching)**: Fatigue severely outweighs fitness. Risk of injury, burnout, and non-functional overreaching.

        4. **Heart-Rate Training Stress Score (hrTSS)**:
           - Quantifies the physiological cost of each running session using duration and intensity relative to your Lactate Threshold Heart Rate (LTHR):
           $$\\text{hrTSS} = \\left( \\frac{t \\times (\\text{HR}_{\\text{avg}} / \\text{LTHR})^2}{3600} \\right) \\times 100$$
        """)
