"""
Data Ingestion, CSV Import & Deduplication Manager View.
"""
from typing import List, Callable
import streamlit as st

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.db.database import DatabaseManager
from src.ingestion.file_detector import detect_and_parse_csv
from src.ingestion.deduplicator import ActivityDeduplicator
from src.data.synthetic_generator import generate_synthetic_training_history


def render_import_view(
    db_manager: DatabaseManager,
    user_profile: UserProfile,
    on_data_updated: Callable[[], None],
) -> None:
    st.markdown("## 📥 Data Ingestion & Cross-Source Sync")
    st.caption("Import your Garmin Connect or Strava activity exports. Automatic format detection and intelligent cross-source deduplication are applied.")

    # 1. File Upload Section
    st.markdown("### 📤 Upload Garmin or Strava CSV Exports")
    uploaded_files = st.file_uploader(
        "Select Activities CSV file(s) from Garmin Connect or Strava",
        type=["csv"],
        accept_multiple_files=True,
        help="Upload 'Activities.csv' from Garmin Connect or 'activities.csv' from Strava archive export.",
    )

    if uploaded_files:
        if st.button("🚀 Process & Ingest Uploaded Files", type="primary"):
            total_parsed = []
            sources_detected = []

            for uploaded_file in uploaded_files:
                file_bytes = uploaded_file.read()
                src_type, acts = detect_and_parse_csv(file_bytes, filename=uploaded_file.name)
                sources_detected.append(f"{uploaded_file.name} ({src_type.upper()}: {len(acts)} activities)")
                total_parsed.extend(acts)

            if total_parsed:
                # Deduplicate against existing DB activities
                existing_acts = db_manager.get_all_activities()
                deduped_acts, stats = ActivityDeduplicator.deduplicate_list(total_parsed, existing_acts)

                # Save all to DB
                saved_count = db_manager.bulk_save_activities(deduped_acts)

                st.success(f"✅ Successfully ingested {len(total_parsed)} activities from: {', '.join(sources_detected)}!")
                st.info(
                    f"📊 **Deduplication Audit:** {stats['total_incoming']} incoming records ➔ "
                    f"{stats['duplicates_found']} duplicate overlaps identified ➔ "
                    f"{stats['merged_count']} cross-source merged ➔ "
                    f"**{saved_count} total canonical activities in database.**"
                )
                on_data_updated()
            else:
                st.error("No valid activities could be parsed from the uploaded file(s). Please verify the CSV format.")

    st.divider()

    # 2. Synthetic Development Data Loader
    st.markdown("### 🧪 Synthetic Development Dataset")
    st.caption("Need to preview dashboard functionality right away? Load a realistic 6-month synthetic runner dataset.")
    st.warning("⚠️ Note: Synthetic dataset activities are explicitly tagged and labeled as `[SYNTHETIC DEV DATA]`.")

    col1, col2 = st.columns([3, 2])
    with col1:
        synth_days = st.slider("Simulation Duration (Days)", min_value=30, max_value=240, value=180, step=30)
    with col2:
        st.write("")
        st.write("")
        if st.button("⚡ Load Realistic Synthetic Dataset", type="secondary"):
            with st.spinner("Synthesizing 6-month periodized training history..."):
                synth_acts = generate_synthetic_training_history(days=synth_days, user_profile=user_profile)
                db_manager.bulk_save_activities(synth_acts)
                st.success(f"Loaded {len(synth_acts)} synthetic development activities ({synth_days} days).")
                on_data_updated()

    st.divider()

    # 3. Database Maintenance & Reset
    st.markdown("### 🗑️ Database Maintenance")
    count = db_manager.count_activities()
    st.write(f"Current activities in local database: **{count}**")

    if count > 0:
        if st.button("⚠️ Clear & Reset All Database Activities", type="secondary"):
            db_manager.clear_all_activities()
            st.success("All activities have been wiped from local database.")
            on_data_updated()

    # 4. Instructions Expander
    with st.expander("📖 How to export data from Garmin Connect and Strava"):
        st.markdown("""
        #### How to Export Garmin Connect CSV:
        1. Log in to [Garmin Connect](https://connect.garmin.com/).
        2. In the left navigation menu, click **Activities** ➔ **All Activities**.
        3. Scroll down or filter to the date range you wish to export.
        4. In the top-right of the table, click the **Export CSV** link.
        5. Upload the resulting `Activities.csv` file here!

        #### How to Export Strava CSV:
        1. Log in to [Strava](https://www.strava.com/).
        2. Hover over your profile photo in top-right ➔ click **Settings**.
        3. Click **My Account** on the left menu.
        4. Scroll down to **Download or Delete Your Account** and click **Get Started**.
        5. Under step 2, click **Request Your Archive**.
        6. Once downloaded and unzipped, upload the `activities.csv` file here!
        """)
