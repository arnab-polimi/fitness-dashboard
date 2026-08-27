"""
Cardiovascular, Efficiency & Aerobic Decoupling View.
"""
from typing import List
import streamlit as st
import pandas as pd
import numpy as np

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.models.metrics import DailyLoad
from src.ui.charts import (
    plot_hr_vs_pace_scatter,
    plot_efficiency_factor_trend,
    plot_hr_zones_distribution,
    PLOT_LAYOUT_DARK,
)
import plotly.graph_objects as go


def render_cardiovascular_view(
    activities: List[Activity],
    daily_loads: List[DailyLoad],
    user_profile: UserProfile,
    daily_df: pd.DataFrame,
    activities_df: pd.DataFrame,
) -> None:
    st.markdown("## 🫀 Cardiovascular Telemetry & Aerobic Efficiency")
    st.caption("Track mitochondrial density progression, cardiac drift, speed-per-heartbeat, and polarized zone balance.")

    if activities_df.empty:
        st.info("No activity data available. Import activities to analyze cardiovascular and efficiency metrics.")
        return

    # Top Row: HR vs Pace and Efficiency Factor
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_hr_vs_pace_scatter(activities_df), use_container_width=True)
    with col2:
        st.plotly_chart(plot_efficiency_factor_trend(daily_df), use_container_width=True)

    # Bottom Row: Aerobic Decoupling and HR Zones
    col3, col4 = st.columns(2)
    with col3:
        # Aerobic Decoupling Chart for Long Runs
        long_runs = activities_df[
            (activities_df["sport_type"].isin(["run", "trail_run"])) &
            (activities_df["distance_km"] >= 8.0) &
            (activities_df["aerobic_decoupling"].notna())
        ].copy()

        fig_decoupling = go.Figure()
        if not long_runs.empty:
            long_runs["date_str"] = pd.to_datetime(long_runs["start_time"]).dt.strftime("%Y-%m-%d")
            fig_decoupling.add_trace(
                go.Bar(
                    x=long_runs["date_str"],
                    y=long_runs["aerobic_decoupling"],
                    marker=dict(
                        color=["#10b981" if v <= 5.0 else ("#f59e0b" if v <= 8.0 else "#ef4444") for v in long_runs["aerobic_decoupling"]],
                        line=dict(color="#1e293b", width=1),
                    ),
                    name="Decoupling %",
                    text=[f"{v:.1f}%" for v in long_runs["aerobic_decoupling"]],
                    textposition="auto",
                )
            )
            fig_decoupling.add_hline(
                y=5.0,
                line_dash="dash",
                line_color="#10b981",
                annotation_text="Aerobic Threshold (5%)",
                annotation_position="top left",
            )
        layout = dict(PLOT_LAYOUT_DARK)
        layout.update(
            title="Aerobic Decoupling (Cardiac Drift on Runs >8km)",
            yaxis_title="Decoupling Rate (%)",
            height=320,
        )
        fig_decoupling.update_layout(layout)
        st.plotly_chart(fig_decoupling, use_container_width=True)

    with col4:
        st.plotly_chart(plot_hr_zones_distribution(activities_df, user_profile), use_container_width=True)

    # Educational Expander
    with st.expander("🔬 Deep Dive: Efficiency Factor (EF) and Aerobic Decoupling (Pw:HR)"):
        st.markdown("""
        - **Efficiency Factor (EF)**: Calculated as $\\text{Speed (m/min)} / \\text{Average HR (bpm)}$.
          - As your aerobic base deepens and stroke volume increases, EF goes up (you run faster at the same heart rate).
        - **Aerobic Decoupling (Pw:HR / Pa:HR)**:
          - Measures whether your heart rate rises while pace stays steady in the second half of a workout.
          - **< 5.0% Decoupling**: Excellent aerobic stamina and fat-burning economy.
          - **> 5.0% Decoupling**: Indicates cardiac drift caused by incomplete aerobic development, high ambient heat, or dehydration.
        """)
