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

    if st.session_state.pop("profile_save_success", False):
        st.success("Profile settings saved successfully! Training metrics updated.")

    with st.form("user_profile_form"):
        render_section_header("Athlete Profile")
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("Athlete Name", value=user_profile.name)
            gender = st.selectbox(
                "Biological Sex (TRIMP exponent)",
                ["male", "female"],
                index=0 if (user_profile.gender or "").lower() == "male" else 1,
            )
        with col2:
            age = st.number_input("Age", min_value=12, max_value=100, value=int(user_profile.age or 30))
            weight_kg = st.number_input(
                "Weight (kg)",
                min_value=30.0,
                max_value=200.0,
                value=float(user_profile.weight_kg or 70.0),
                step=0.5,
            )
        with col3:
            units = st.selectbox(
                "Preferred Units",
                ["metric", "imperial"],
                index=0 if (user_profile.units or "").lower() == "metric" else 1,
            )

        render_section_header("Cardiovascular & Threshold Baselines", icon_name="heartbeat")
        c1, c2, c3 = st.columns(3)
        with c1:
            resting_hr = st.number_input(
                "Resting Heart Rate (bpm)",
                min_value=30,
                max_value=100,
                value=int(user_profile.resting_hr or 50),
            )
            max_hr = st.number_input(
                "Maximum Heart Rate (bpm)",
                min_value=120,
                max_value=230,
                value=int(user_profile.max_hr or 190),
            )
        with c2:
            lthr = st.number_input(
                "Lactate Threshold HR (LTHR bpm)",
                min_value=100,
                max_value=210,
                value=int(user_profile.lthr or 168),
            )
            ftp_watts = st.number_input(
                "Running FTP (Watts)",
                min_value=100.0,
                max_value=600.0,
                value=float(user_profile.ftp_watts or 250.0),
            )
        with c3:
            # Threshold pace in min:sec /km
            cur_sec = user_profile.threshold_pace_sec_km or 270.0
            cur_min = int(cur_sec // 60)
            cur_remainder_sec = int(round(cur_sec % 60))

            t_min = st.number_input("Threshold Pace (Minutes)", min_value=2, max_value=10, value=cur_min)
            t_sec = st.number_input("Threshold Pace (Seconds)", min_value=0, max_value=59, value=cur_remainder_sec)
            threshold_pace_sec_km = float(t_min * 60 + t_sec)

        render_section_header("Target Race Goal")
        rc1, rc2 = st.columns(2)
        with rc1:
            race_options = [
                "None",
                "5K (5.0 km)",
                "10K (10.0 km)",
                "Half Marathon (21.1 km)",
                "Marathon (42.2 km)",
            ]
            cur_dist = user_profile.target_race_distance_km
            if cur_dist is None or cur_dist <= 0:
                default_dist_idx = 0
            elif abs(cur_dist - 5.0) < 0.5:
                default_dist_idx = 1
            elif abs(cur_dist - 10.0) < 0.5:
                default_dist_idx = 2
            elif abs(cur_dist - 21.0975) < 1.0 or abs(cur_dist - 21.1) < 1.0:
                default_dist_idx = 3
            elif abs(cur_dist - 42.195) < 1.0 or abs(cur_dist - 42.2) < 1.0:
                default_dist_idx = 4
            else:
                default_dist_idx = 0

            race_dist = st.selectbox(
                "Target Race Distance",
                race_options,
                index=default_dist_idx,
            )
            if "5K" in race_dist:
                target_race_dist_km = 5.0
            elif "10K" in race_dist:
                target_race_dist_km = 10.0
            elif "Half" in race_dist:
                target_race_dist_km = 21.0975
            elif "Marathon" in race_dist:
                target_race_dist_km = 42.195
            else:
                target_race_dist_km = None

        with rc2:
            race_date_str = st.text_input("Target Race Date (YYYY-MM-DD)", value=user_profile.target_race_date or "")

        render_section_header("Device Telemetry Synchronization")
        auto_sync = st.checkbox(
            "Auto-update Resting HR and Weight from Garmin sync",
            value=getattr(user_profile, "auto_sync_baselines", False),
            help="When checked, running a Garmin sync will automatically update your Resting HR and Weight from health records. When unchecked (default), your custom values saved here will never be overwritten.",
        )

        submitted = st.form_submit_button("Save Profile Configuration", type="primary")
        if submitted:
            updated_profile = UserProfile(
                user_id=user_profile.user_id,
                name=name.strip() if name else "Runner",
                gender=gender,
                age=int(age),
                weight_kg=float(weight_kg),
                resting_hr=int(resting_hr),
                max_hr=int(max_hr),
                lthr=int(lthr),
                threshold_pace_sec_km=threshold_pace_sec_km,
                ftp_watts=float(ftp_watts) if ftp_watts else 250.0,
                units=units,
                target_race_distance_km=target_race_dist_km,
                target_race_date=race_date_str.strip() if race_date_str and race_date_str.strip() else None,
                auto_sync_baselines=auto_sync,
            )
            db_manager.save_user_profile(updated_profile)
            st.session_state["profile_save_success"] = True
            st.toast("Profile settings saved successfully!", icon="✅")
            on_profile_updated(updated_profile)

    # Connected Hardware Ecosystem Section
    render_section_header("Connected Hardware Ecosystem", icon_name="settings")
    from src.ingestion.garmindb_pipeline import GarminDbPipeline
    devices = GarminDbPipeline.get_connected_devices()

    dev_cols = st.columns(len(devices) if devices else 1)
    for idx, dev in enumerate(devices):
        with dev_cols[idx]:
            is_active = dev.get("is_active", False)
            badge_color = "#c1d37f" if is_active else "#94a3b8"
            badge_text = "ACTIVE PRIMARY WATCH" if is_active else "PAIRED LEGACY DEVICE"
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%);
                            border: 1px solid {'#80923F' if is_active else '#3b322e'};
                            border-radius: 12px; padding: 16px 18px; margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: 700; color: #f0e2a3; font-size: 1.05rem;">{dev['product']}</span>
                        <span style="font-size: 0.65rem; color: {badge_color}; background: rgba(193,211,127,0.1); padding: 2px 6px; border-radius: 4px; border: 1px solid {badge_color}; font-weight: 700;">
                            {badge_text}
                        </span>
                    </div>
                    <div style="font-size: 0.78rem; color: #c8b99c; margin-bottom: 4px;">
                        Manufacturer: <strong style="color: #ffffff;">{dev.get('manufacturer', 'Garmin')}</strong>
                    </div>
                    <div style="font-size: 0.78rem; color: #c8b99c; margin-bottom: 4px;">
                        Serial Number: <code style="color: #c1d37f;">{dev['serial_number']}</code>
                    </div>
                    <div style="font-size: 0.74rem; color: #94a3b8; margin-top: 8px; border-top: 1px solid #332a27; padding-top: 6px;">
                        {'Elevate v4 • Overnight HRV • Running Dynamics • EPOC Load' if is_active else 'Legacy Baseline • Historical Workouts'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
