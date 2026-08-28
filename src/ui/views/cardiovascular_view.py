"""
Cardiovascular, Efficiency & Aerobic Decoupling View.
"""
from typing import List, Optional
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
    plot_recovery_telemetry_chart,
    PLOT_LAYOUT_DARK,
)
from src.ui.icons import render_view_header, render_section_header
import plotly.graph_objects as go


def render_cardiovascular_view(
    activities: List[Activity],
    daily_loads: List[DailyLoad],
    user_profile: UserProfile,
    daily_df: pd.DataFrame,
    activities_df: pd.DataFrame,
    health_df: Optional[pd.DataFrame] = None,
) -> None:
    render_view_header(
        title="Cardiovascular Telemetry & Aerobic Efficiency",
        caption="Track mitochondrial density progression, resting HR recovery baselines, cardiac drift, and polarized zone balance.",
        icon_name="heartbeat",
    )

    if activities_df.empty and (health_df is None or health_df.empty):
        st.info("No activity or health data available. Synchronize GarminDb or import activities to analyze cardiovascular metrics.")
        return

    # Garmin Health Recovery Telemetry (if available)
    if health_df is not None and not health_df.empty and "resting_hr" in health_df.columns:
        valid_rhr = health_df[health_df["resting_hr"].notna()]
        if not valid_rhr.empty:
            render_section_header("Garmin Recovery & Resting Heart Rate Telemetry", icon_name="heartbeat")
            st.plotly_chart(plot_recovery_telemetry_chart(health_df), use_container_width=True)

    # Top Row: HR vs Pace and Efficiency Factor
    if not activities_df.empty:
        render_section_header("Aerobic Profile & Efficiency Factor", icon_name="heartbeat")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_hr_vs_pace_scatter(activities_df), use_container_width=True)
        with col2:
            st.plotly_chart(plot_efficiency_factor_trend(daily_df), use_container_width=True)

        # Bottom Row: Aerobic Decoupling and HR Zones
        col3, col4 = st.columns(2)
        with col3:
            long_runs = activities_df[
                (activities_df["sport_type"].isin(["run", "trail_run"])) &
                (activities_df["distance_km"] >= 6.0) &
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
                title="Aerobic Decoupling (Cardiac Drift on Runs >6km)",
                yaxis_title="Decoupling Rate (%)",
                height=320,
            )
            fig_decoupling.update_layout(layout)
            st.plotly_chart(fig_decoupling, use_container_width=True)

        with col4:
            st.plotly_chart(plot_hr_zones_distribution(activities_df, user_profile), use_container_width=True)

    # Educational Expander
    with st.expander("Deep Dive: Efficiency Factor (EF) and Aerobic Decoupling (Pw:HR)"):
        st.markdown("""
        - **Efficiency Factor (EF)**: Calculated as $\\text{Speed (m/min)} / \\text{Average HR (bpm)}$.
          - As your aerobic base deepens and stroke volume increases, EF goes up (you run faster at the same heart rate).
        - **Aerobic Decoupling (Pw:HR / Pa:HR)**:
          - Measures whether your heart rate rises while pace stays steady in the second half of a workout.
          - **< 5.0% Decoupling**: Excellent aerobic stamina and fat-burning economy.
          - **> 5.0% Decoupling**: Indicates cardiac drift caused by incomplete aerobic development, high ambient heat, or dehydration.
        """)
