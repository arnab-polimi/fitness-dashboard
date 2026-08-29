"""
Data Ingestion, GarminDb Pipeline & CSV Import View.
"""
import os
import subprocess
from typing import List, Callable
import streamlit as st

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.db.database import DatabaseManager
from src.ingestion.garmindb_pipeline import GarminDbPipeline, DEFAULT_GARMIDB_DIR
from src.ingestion.garmin_sync_runner import GarminSyncRunner, DEFAULT_GARMIN_SYNC_SCRIPT
from src.ingestion.file_detector import detect_and_parse_csv
from src.ingestion.deduplicator import ActivityDeduplicator
from src.data.synthetic_generator import generate_synthetic_training_history, generate_synthetic_health_records
from src.ui.icons import render_view_header, render_section_header


def render_import_view(
    db_manager: DatabaseManager,
    user_profile: UserProfile,
    on_data_updated: Callable[[], None],
) -> None:
    render_view_header(
        title="Data Ingestion & Sync Engine",
        caption="Synchronize directly with your GitHub Actions cloud sync, local **GarminDb** database, or import activity CSV exports.",
        icon_name="import",
    )

    # 0. GitHub Actions Remote Sync Pull Section
    render_section_header("GitHub Cloud Sync")
    st.caption("Pull the latest telemetry and activities synchronized automatically by GitHub Actions into your local dashboard.")

    col_gh1, col_gh2 = st.columns([2, 3])
    with col_gh1:
        if st.button("☁️ Pull Latest from GitHub Cloud", type="primary"):
            with st.spinner("Pulling latest fitness_data.db from GitHub repository..."):
                try:
                    res = subprocess.run(["git", "pull", "--rebase"], capture_output=True, text=True, check=True)
                    st.success("Successfully pulled latest synced data from GitHub!")
                    st.caption(res.stdout or "Repository up-to-date.")
                    on_data_updated()
                except Exception as e:
                    st.error(f"Failed to pull from GitHub: {e}")

    st.divider()

    # 1. GarminDb Download + Direct Pipeline Sync Section
    render_section_header("GarminDb Direct Pipeline")
    st.caption("Directly ingests all activities, high-resolution laps, and continuous daily health telemetry (Resting HR, Sleep, Stress, Weight) from your local GarminDb.")

    with st.container():
        garmindb_path_input = st.text_input(
            "GarminDb Database Directory",
            value=DEFAULT_GARMIDB_DIR,
            help="Path to the directory containing garmin_activities.db, garmin.db, and garmin_summary.db",
        )
        garmindb_stats = GarminDbPipeline.get_garmindb_stats(garmindb_path_input)

        sync_script_input = st.text_input(
            "Garmin download script (optional)",
            value=DEFAULT_GARMIN_SYNC_SCRIPT,
            help="Runs the local daily GarminDB refresh before the dashboard imports its databases. The email/report master script is intentionally not used.",
        )
        c_fetch, c_sync = st.columns(2)
        with c_fetch:
            fetch_and_sync_btn = st.button(
                "Download from Garmin & Sync",
                type="primary",
                disabled=not GarminSyncRunner.is_available(sync_script_input),
            )
        with c_sync:
            sync_garmindb_btn = st.button("Import Existing GarminDb Data")

        if sync_script_input and not GarminSyncRunner.is_available(sync_script_input):
            st.info("The optional Garmin download script was not found. You can still import existing GarminDb data, or update the path above.")

        if fetch_and_sync_btn:
            with st.spinner("Downloading from Garmin, updating GarminDb, and importing dashboard data…"):
                try:
                    download_result = GarminSyncRunner.run(sync_script_input)
                    if download_result["status"] != "success":
                        st.error(f"Garmin download did not finish successfully (exit code: {download_result['exit_code']}).")
                        with st.expander("Safe sync log tail"):
                            st.code(download_result["summary"])
                    else:
                        sync_res = GarminDbPipeline.sync_all(
                            target_db=db_manager,
                            user_profile=user_profile,
                            db_dir=garmindb_path_input,
                        )
                        st.success(
                            f"Garmin download and dashboard sync complete: {sync_res['activities_extracted']} activities, "
                            f"{sync_res['laps_processed']} laps, and {sync_res['health_days_saved']} health days processed."
                        )
                        on_data_updated()
                except Exception as e:
                    st.error(f"Error during Garmin download and sync: {e}")

        # The direct import button remains available for offline/manual GarminDb updates.
        if sync_garmindb_btn:
            with st.spinner("Connecting to GarminDb and synchronizing telemetry..."):
                try:
                    sync_res = GarminDbPipeline.sync_all(
                        target_db=db_manager,
                        user_profile=user_profile,
                        db_dir=garmindb_path_input,
                    )
                    st.success(
                        f"**GarminDb Sync Successful!** Ingested {sync_res['activities_extracted']} activities "
                        f"({sync_res['laps_processed']} laps) and {sync_res['health_days_saved']} days of health telemetry."
                    )
                    if sync_res.get("updated_resting_hr"):
                        st.info(f"Athlete Profile updated: Resting HR calibrated to **{sync_res['updated_resting_hr']} bpm**, Weight to **{sync_res['updated_weight_kg']:.1f} kg**.")
                    on_data_updated()
                except Exception as e:
                    st.error(f"Error synchronizing with GarminDb: {e}")

        # Status is rendered after the path inputs so it always describes the selected directory.
        if garmindb_stats["available"]:
            st.markdown(
                f"""
                <div style="background: rgba(0, 210, 255, 0.08); border: 1px solid rgba(0, 210, 255, 0.3); border-radius: 8px; padding: 10px 14px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #00d2ff;">GarminDb Detected:</strong>
                        <span style="color: #cbd5e1; font-size: 0.88rem;">{garmindb_stats['activity_count']} Activities • {garmindb_stats['laps_count']} Laps • {garmindb_stats['health_days_count']} Days of Health Telemetry</span>
                    </div>
                    <span class="badge badge-optimal">READY TO SYNC</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.warning(f"No GarminDb databases found at `{garmindb_path_input}`. Check path or download with GarminDb tool.")

    st.divider()

    # 2. File Upload Section (CSV / Strava)
    render_section_header("Upload Garmin or Strava CSV Exports")
    st.caption("Upload raw CSV exports from Garmin Connect or Strava Archive.")
    uploaded_files = st.file_uploader(
        "Select Activities CSV file(s)",
        type=["csv"],
        accept_multiple_files=True,
        help="Upload 'Activities.csv' from Garmin Connect or 'activities.csv' from Strava archive export.",
    )

    if uploaded_files:
        if st.button("Process & Ingest Uploaded CSV Files", type="secondary"):
            total_parsed = []
            sources_detected = []

            for uploaded_file in uploaded_files:
                file_bytes = uploaded_file.read()
                src_type, acts = detect_and_parse_csv(file_bytes, filename=uploaded_file.name)
                sources_detected.append(f"{uploaded_file.name} ({src_type.upper()}: {len(acts)} activities)")
                total_parsed.extend(acts)

            if total_parsed:
                existing_acts = db_manager.get_all_activities()
                deduped_acts, stats = ActivityDeduplicator.deduplicate_list(total_parsed, existing_acts)
                saved_count = db_manager.bulk_save_activities(deduped_acts)

                st.success(f"Successfully ingested {len(total_parsed)} activities from: {', '.join(sources_detected)}!")
                st.info(
                    f"**Deduplication Audit:** {stats['total_incoming']} incoming records • "
                    f"{stats['duplicates_found']} duplicates identified • "
                    f"{stats['merged_count']} cross-source merged • "
                    f"**{saved_count} total canonical activities in database.**"
                )
                on_data_updated()
            else:
                st.error("No valid activities could be parsed from the uploaded file(s). Please verify the CSV format.")

    st.divider()

    # 3. Synthetic Development Data Loader
    render_section_header("Synthetic Development Dataset")
    st.caption("Need to preview simulated 6-month periodized training data?")
    st.warning("Note: Synthetic dataset activities are explicitly tagged and labeled as `[SYNTHETIC DEV DATA]`.")

    col1, col2 = st.columns([3, 2])
    with col1:
        synth_days = st.slider("Simulation Duration (Days)", min_value=30, max_value=240, value=180, step=30)
    with col2:
        st.write("")
        st.write("")
        if st.button("Load Realistic Synthetic Dataset", type="secondary"):
            with st.spinner("Synthesizing 6-month periodized training history and sleep telemetry..."):
                synth_acts = generate_synthetic_training_history(days=synth_days, user_profile=user_profile)
                db_manager.bulk_save_activities(synth_acts)
                synth_health = generate_synthetic_health_records(days=synth_days)
                db_manager.save_daily_health_records(synth_health)
                st.success(f"Loaded {len(synth_acts)} synthetic activities and {len(synth_health)} sleep/health telemetry records ({synth_days} days).")
                on_data_updated()

    st.divider()

    # 4. Database Maintenance & Reset
    render_section_header("Database Maintenance")
    count = db_manager.count_activities()
    st.write(f"Current activities in local database: **{count}**")

    if count > 0:
        if st.button("Clear & Reset All Database Activities", type="secondary"):
            db_manager.clear_all_activities()
            st.success("All activities and health telemetry have been wiped from local database.")
            on_data_updated()
