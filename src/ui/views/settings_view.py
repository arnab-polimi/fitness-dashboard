"""
User Profile & Physiological Parameters Settings View.
"""
from typing import Callable
import streamlit as st

from src.models.user_profile import UserProfile
from src.db.database import DatabaseManager
from src.ui.icons import render_view_header, render_section_header


def render_settings_view(
    db_manager: DatabaseManager,
    user_profile: UserProfile,
    on_profile_updated: Callable[[UserProfile], None],
) -> None:
    render_view_header(
        title="Physiological Parameters & Athlete Profile",
        caption="Customize your physiological baselines to ensure precise TRIMP, hrTSS, Heart Rate Zones, and Training Stress calculations.",
    )

    with st.form("user_profile_form"):
        render_section_header("Athlete Profile")
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("Athlete Name", value=user_profile.name)
            gender = st.selectbox("Biological Sex (TRIMP exponent)", ["male", "female"], index=0 if user_profile.gender == "male" else 1)
        with col2:
            age = st.number_input("Age", min_value=12, max_value=100, value=user_profile.age)
            weight_kg = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=user_profile.weight_kg, step=0.5)
        with col3:
            units = st.selectbox("Preferred Units", ["metric", "imperial"], index=0 if user_profile.units == "metric" else 1)

        render_section_header("Cardiovascular & Threshold Baselines", icon_name="heartbeat")
        c1, c2, c3 = st.columns(3)
        with c1:
            resting_hr = st.number_input("Resting Heart Rate (bpm)", min_value=30, max_value=100, value=user_profile.resting_hr)
            max_hr = st.number_input("Maximum Heart Rate (bpm)", min_value=120, max_value=230, value=user_profile.max_hr)
        with c2:
            lthr = st.number_input("Lactate Threshold HR (LTHR bpm)", min_value=100, max_value=210, value=user_profile.lthr)
            ftp_watts = st.number_input("Running FTP (Watts)", min_value=100.0, max_value=600.0, value=user_profile.ftp_watts or 250.0)
        with c3:
            # Threshold pace in min:sec /km
            cur_sec = user_profile.threshold_pace_sec_km
            cur_min = int(cur_sec // 60)
            cur_remainder_sec = int(cur_sec % 60)

            t_min = st.number_input("Threshold Pace (Minutes)", min_value=2, max_value=10, value=cur_min)
            t_sec = st.number_input("Threshold Pace (Seconds)", min_value=0, max_value=59, value=cur_remainder_sec)
            threshold_pace_sec_km = float(t_min * 60 + t_sec)

        render_section_header("Target Race Goal")
        rc1, rc2 = st.columns(2)
        with rc1:
            race_dist = st.selectbox(
                "Target Race Distance",
                ["None", "5K (5.0 km)", "10K (10.0 km)", "Half Marathon (21.1 km)", "Marathon (42.2 km)"],
                index=3,
            )
            target_race_dist_km = 21.0975 if "Half" in race_dist else (42.195 if "Marathon" in race_dist else (10.0 if "10K" in race_dist else (5.0 if "5K" in race_dist else None)))
        with rc2:
            race_date_str = st.text_input("Target Race Date (YYYY-MM-DD)", value=user_profile.target_race_date or "")

        submitted = st.form_submit_button("Save Profile Configuration", type="primary")
        if submitted:
            updated_profile = UserProfile(
                user_id=user_profile.user_id,
                name=name,
                gender=gender,
                age=age,
                weight_kg=weight_kg,
                resting_hr=resting_hr,
                max_hr=max_hr,
                lthr=lthr,
                threshold_pace_sec_km=threshold_pace_sec_km,
                ftp_watts=ftp_watts,
                units=units,
                target_race_distance_km=target_race_dist_km,
                target_race_date=race_date_str if race_date_str else None,
            )
            db_manager.save_user_profile(updated_profile)
            on_profile_updated(updated_profile)
            st.success("Profile settings saved successfully! Training metrics updated.")
