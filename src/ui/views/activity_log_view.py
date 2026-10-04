"""
Activity Log & Individual Workout Deep-Dive Inspector.
"""
from typing import List
import streamlit as st
import pandas as pd

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.analytics.running_metrics import format_pace_sec_km
from src.ui.icons import render_view_header, render_section_header


def render_activity_log_view(
    activities: List[Activity],
    user_profile: UserProfile,
    activities_df: pd.DataFrame,
) -> None:
    render_view_header(
        title="Activity Log & Workout Inspector",
        caption="Comprehensive log of all canonical, deduplicated activities across Garmin, Strava, and manual uploads.",
        icon_name="overview",
    )

    if activities_df.empty:
        st.info("No activities found in database.")
        return

    # Filters row
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        sport_filter = st.selectbox(
            "Filter by Sport",
            ["All Sports"] + sorted(list(activities_df["sport_type"].unique())),
            index=0,
        )
    with col2:
        source_filter = st.selectbox(
            "Filter by Source",
            ["All Sources"] + sorted(list(activities_df["source"].unique())),
            index=0,
        )
    with col3:
        search_query = st.text_input("Search Activity Title / Notes", "")

    # Apply filters
    filtered_df = activities_df.copy()
    if sport_filter != "All Sports":
        filtered_df = filtered_df[filtered_df["sport_type"] == sport_filter]
    if source_filter != "All Sources":
        filtered_df = filtered_df[filtered_df["source"] == source_filter]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_query, case=False, na=False) |
            filtered_df["notes"].str.contains(search_query, case=False, na=False)
        ]

    # Formatted display table
    display_df = pd.DataFrame()
    display_df["Date"] = pd.to_datetime(filtered_df["start_time"]).dt.strftime("%Y-%m-%d %H:%M")
    display_df["Title"] = filtered_df["title"]
    display_df["Sport"] = filtered_df["sport_type"].apply(lambda s: s.replace("_", " ").title() if pd.notna(s) else "")
    display_df["Device"] = filtered_df["device_name"].fillna("Garmin") if "device_name" in filtered_df.columns else filtered_df["source"]
    display_df["Distance (km)"] = filtered_df["distance_km"].round(2)
    display_df["Duration"] = filtered_df["duration_seconds"].apply(lambda s: f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d}")
    display_df["Pace"] = filtered_df["avg_pace_sec_km"].apply(lambda p: format_pace_sec_km(p, user_profile.units))
    display_df["Avg HR"] = filtered_df["avg_hr"].apply(lambda h: f"{int(h)} bpm" if pd.notna(h) else "--")
    display_df["Cadence"] = filtered_df["avg_cadence"].apply(lambda c: f"{int(c)} spm" if pd.notna(c) else "--")
    if "garmin_training_load" in filtered_df.columns:
        display_df["Garmin Load"] = filtered_df["garmin_training_load"].apply(lambda l: f"{l:.1f}" if pd.notna(l) else "--")
    display_df["TSS"] = filtered_df["tss"].round(1)
    display_df["EF"] = filtered_df["efficiency_factor"].round(2)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    # Activity Inspector Expander
    render_section_header("Workout Inspector")
    activity_options = {f"{a.start_time.strftime('%Y-%m-%d %H:%M')} - {a.title} ({a.distance_km:.1f} km)": a.id for a in sorted(activities, key=lambda x: x.start_time, reverse=True)}

    if activity_options:
        selected_label = st.selectbox("Select Activity to Inspect", list(activity_options.keys()))
        selected_id = activity_options[selected_label]
        selected_act = next((a for a in activities if a.id == selected_id), None)

        if selected_act:
            if selected_act.device_name:
                st.caption(f"**Hardware Device:** {selected_act.device_name} • Source: {selected_act.source.capitalize()}")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Distance", f"{selected_act.distance_km:.2f} km")
                st.metric("Duration", selected_act.formatted_duration)
                st.metric("Pace", selected_act.formatted_pace)
            with c2:
                st.metric("Avg HR", f"{selected_act.avg_hr:.0f} bpm" if selected_act.avg_hr else "--")
                st.metric("Max HR", f"{selected_act.max_hr:.0f} bpm" if selected_act.max_hr else "--")
                st.metric("Cadence", f"{selected_act.avg_cadence:.0f} spm" if selected_act.avg_cadence else "--")
            with c3:
                load_label = f"{selected_act.garmin_training_load:.1f}" if selected_act.garmin_training_load is not None else "--"
                st.metric("Garmin EPOC Load", load_label)
                st.metric("Training Stress (TSS)", f"{selected_act.tss:.1f}" if selected_act.tss else "--")
                st.metric("TRIMP Score", f"{selected_act.trimp:.1f}" if selected_act.trimp else "--")
            with c4:
                st.metric("Aerobic TE", f"{selected_act.aerobic_te:.1f}" if selected_act.aerobic_te else "--")
                st.metric("Anaerobic TE", f"{selected_act.anaerobic_te:.1f}" if selected_act.anaerobic_te else "--")
                st.metric("Efficiency Factor", f"{selected_act.efficiency_factor:.2f}" if selected_act.efficiency_factor else "--")

            # Fenix 7 Running Dynamics & Heart Rate Zones (if recorded)
            has_fenix_act_telemetry = (
                selected_act.vertical_oscillation_mm is not None or
                selected_act.ground_contact_time_ms is not None or
                (selected_act.hrz_1_seconds or 0) > 0 or
                (selected_act.hrz_2_seconds or 0) > 0
            )
            if has_fenix_act_telemetry:
                st.markdown("##### Garmin Fenix 7 Biomechanics & Zone Distribution")
                bc1, bc2, bc3, bc4 = st.columns(4)
                with bc1:
                    st.metric("Vert. Oscillation", f"{selected_act.vertical_oscillation_mm:.1f} mm" if selected_act.vertical_oscillation_mm else "--")
                with bc2:
                    st.metric("Vertical Ratio", f"{selected_act.vertical_ratio:.1f}%" if selected_act.vertical_ratio else "--")
                with bc3:
                    st.metric("Ground Contact Time", f"{selected_act.ground_contact_time_ms:.0f} ms" if selected_act.ground_contact_time_ms else "--")
                with bc4:
                    st.metric("Stride Length", f"{selected_act.stride_length_m:.2f} m" if selected_act.stride_length_m else "--")

                if (selected_act.hrz_1_seconds or 0) + (selected_act.hrz_2_seconds or 0) + (selected_act.hrz_3_seconds or 0) > 0:
                    z1_m = (selected_act.hrz_1_seconds or 0) / 60.0
                    z2_m = (selected_act.hrz_2_seconds or 0) / 60.0
                    z3_m = (selected_act.hrz_3_seconds or 0) / 60.0
                    z4_m = (selected_act.hrz_4_seconds or 0) / 60.0
                    z5_m = (selected_act.hrz_5_seconds or 0) / 60.0
                    st.caption(f"**Measured HR Zones:** Z1: {z1_m:.1f}m | Z2: {z2_m:.1f}m | Z3: {z3_m:.1f}m | Z4: {z4_m:.1f}m | Z5: {z5_m:.1f}m")

            if selected_act.raw_data:
                with st.expander("Raw Ingested Metadata"):
                    st.json(selected_act.raw_data)
