"""
Race Performance Predictor and Jack Daniels Training Paces View.
"""
from typing import List
import streamlit as st
import pandas as pd

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.models.metrics import RacePrediction
from src.analytics.running_metrics import (
    RunningMetricsCalculator,
    get_training_paces_from_vdot,
    calculate_vdot_from_race,
)
from src.ui.components import render_race_prediction_cards


def render_race_predictor_view(
    activities: List[Activity],
    user_profile: UserProfile,
    race_predictions: List[RacePrediction],
) -> None:
    st.markdown("## 🏁 Race Predictor & Training Pace Calculator")
    st.caption("Jack Daniels VDOT tables & Pete Riegel endurance power formulas calibrated to your Chronic Training Load (CTL).")

    # Race Predictions Section
    st.markdown("### 🏆 Projected Race Capabilities")
    render_race_prediction_cards(race_predictions)

    st.divider()

    # Peak VDOT & Training Paces
    current_peak_vdot = RunningMetricsCalculator.get_peak_vdot(activities)

    st.markdown("### 🎯 Jack Daniels Training Paces")
    st.caption(f"Calculated from your current peak VDOT score: **{current_peak_vdot:.1f}**")

    paces = get_training_paces_from_vdot(current_peak_vdot)
    rows = []
    for name, data in paces.items():
        rows.append({
            "Training Zone": name,
            "Target Pace (min/km)": data["formatted_range_km"],
            "Target Pace (min/mi)": data["formatted_range_mi"],
            "Physiological Purpose": data["purpose"],
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

    # Interactive Custom VDOT Calculator
    st.markdown("### 🧮 Interactive Custom VDOT Calculator")
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            custom_dist = st.selectbox(
                "Benchmark Distance",
                ["5,000m (5K)", "10,000m (10K)", "Half Marathon (21.1K)", "Marathon (42.2K)"],
                index=0,
            )
            dist_m = 5000.0 if "5K" in custom_dist else (10000.0 if "10K" in custom_dist else (21097.5 if "Half" in custom_dist else 42195.0))
        with c2:
            custom_min = st.number_input("Time Minutes", min_value=10, max_value=360, value=20 if "5K" in custom_dist else 45)
        with c3:
            custom_sec = st.number_input("Time Seconds", min_value=0, max_value=59, value=0)

        custom_total_sec = custom_min * 60 + custom_sec
        calc_vdot = calculate_vdot_from_race(dist_m, custom_total_sec)

        if calc_vdot:
            st.success(f"⚡ Calculated VDOT: **{calc_vdot:.1f}**")
            custom_paces = get_training_paces_from_vdot(calc_vdot)
            c_rows = [{"Zone": k, "Pace": v["formatted_range_km"], "Purpose": v["purpose"]} for k, v in custom_paces.items()]
            st.dataframe(pd.DataFrame(c_rows), use_container_width=True, hide_index=True)
