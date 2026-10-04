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
    plot_garmin_hr_zones_breakdown,
    plot_fenix_running_dynamics_chart,
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

        # Fenix 7 Native Heart Rate Zones & Biomechanical Dynamics
        has_fenix_metrics = (
            ("hrz_1_seconds" in activities_df.columns and activities_df["hrz_1_seconds"].notna().any()) or
            ("vertical_oscillation_mm" in activities_df.columns and activities_df["vertical_oscillation_mm"].notna().any())
        )
        if has_fenix_metrics:
            render_section_header("Garmin Fenix 7 Heart Rate Zones & Running Dynamics", icon_name="running")
            fc1, fc2 = st.columns(2)
            with fc1:
                st.plotly_chart(plot_garmin_hr_zones_breakdown(activities_df), use_container_width=True)
            with fc2:
                st.plotly_chart(plot_fenix_running_dynamics_chart(activities_df), use_container_width=True)

        # Bottom Row: Aerobic Decoupling and Calculated HR Zones
        render_section_header("Cardiac Drift & Intensity Zone Distribution", icon_name="heartbeat")
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
    with st.expander("Deep Dive: Fenix 7 Running Dynamics & Aerobic Efficiency"):
        st.markdown("""
        - **Vertical Oscillation (VO)**: The vertical bounce of your torso while running (measured in millimeters).
          - **Typical range**: 60 - 90 mm. Lower vertical oscillation means less wasted upward kinetic energy and more forward propulsion.
        - **Vertical Ratio (VR)**: The cost of bounce relative to your stride length ($VO / \\text{Stride Length} \\times 100$).
          - **< 8.0%**: World-class running economy.
          - **8.0% – 9.5%**: Excellent running efficiency.
          - **> 10.0%**: Indicates excessive upward bounce or overstriding.
        - **Ground Contact Time (GCT)**: The time your foot spends planted on the ground per stride (measured in milliseconds).
          - **< 240 ms**: Rapid sprint/interval foot turnover.
          - **240 – 280 ms**: Strong aerobic distance running cadence.
        - **Efficiency Factor (EF)**: Speed (m/min) per heartbeat. Increases as mitochondrial density and stroke volume develop.
        - **Aerobic Decoupling (Pw:HR)**: Cardiac drift during steady-pace long runs. Target **< 5.0%** for robust aerobic durability.
        """)
