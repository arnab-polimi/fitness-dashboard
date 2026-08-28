"""
Training Plan & Upcoming Workouts View.
Displays uploaded PDF training plans, upcoming scheduled workouts, and adherence analytics.
"""
import os
from datetime import datetime, date, timedelta
import pandas as pd
import streamlit as st

from src.db.database import DatabaseManager
from src.ingestion.pdf_plan_parser import PDFPlanParser
from src.ui.components import render_metric_card
from src.ui.icons import render_view_header, render_section_header, get_icon_html


def render_training_plan_view(db_manager: DatabaseManager):

    """Renders the Training Plan and Upcoming Workouts view."""
    render_view_header(
        title="Training Plan & Upcoming Workouts",
        caption="Ingest PDF training schedules, view upcoming sessions, and track adherence.",
        icon_name="plan"
    )


    # 1. PDF Upload & Importer Controls
    with st.expander("📥 Import / Upload PDF Training Plan", expanded=False):
        col1, col2 = st.columns([2, 1])

        with col1:
            uploaded_pdf = st.file_uploader(
                "Upload Training Plan PDF (with dates present)",
                type=["pdf"],
                help="Upload a PDF file containing your training schedule with dates."
            )
            if uploaded_pdf is not None:
                if st.button("🚀 Process & Load Uploaded PDF", type="primary", use_container_width=True):
                    with st.spinner("Extracting dates and workouts from PDF..."):
                        try:
                            workouts = PDFPlanParser.parse_pdf(uploaded_pdf)
                            if workouts:
                                db_manager.clear_scheduled_workouts()
                                count = db_manager.save_scheduled_workouts(workouts)
                                st.success(f"Successfully loaded {count} scheduled workouts from PDF!")
                                st.rerun()
                            else:
                                st.error("No dates or workouts could be parsed from the PDF. Ensure dates and workout items are present.")
                        except Exception as e:
                            st.error(f"Error parsing PDF: {e}")

        with col2:
            st.markdown("#### ⚡ Quick Actions")
            sample_pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "10K_Weekly_Training_Plan_Weeks_1-13.pdf")
            if os.path.exists(sample_pdf_path):
                if st.button("📋 Load Pre-bundled 10K Plan (Weeks 1–13)", use_container_width=True):
                    with st.spinner("Loading 10K Training Plan..."):
                        workouts = PDFPlanParser._generate_10k_master_schedule(year=2026)
                        db_manager.clear_scheduled_workouts()
                        count = db_manager.save_scheduled_workouts(workouts)
                        st.success(f"Loaded {count} workouts into Training Plan!")
                        st.rerun()

            if st.button("🗑️ Clear Training Plan", use_container_width=True):
                db_manager.clear_scheduled_workouts()
                st.info("Cleared scheduled training plan.")
                st.rerun()

    # Load scheduled workouts from database
    scheduled_df = db_manager.get_scheduled_workouts()

    # Auto-seed sample plan if database currently empty so user sees immediate value
    if scheduled_df.empty:
        workouts = PDFPlanParser._generate_10k_master_schedule(year=2026)
        db_manager.save_scheduled_workouts(workouts)
        scheduled_df = db_manager.get_scheduled_workouts()

    today_str = date.today().isoformat()
    today_dt = date.today()

    # Filter upcoming vs past
    if not scheduled_df.empty:
        scheduled_df["workout_date_dt"] = pd.to_datetime(scheduled_df["workout_date"]).dt.date
        upcoming_df = scheduled_df[scheduled_df["workout_date_dt"] >= today_dt].sort_values("workout_date")
        past_df = scheduled_df[scheduled_df["workout_date_dt"] < today_dt].sort_values("workout_date")
    else:
        upcoming_df = pd.DataFrame()
        past_df = pd.DataFrame()

    # 2. Today's Scheduled Workout Section
    render_section_header("Today's Scheduled Workout", icon_name="running")

    today_row = scheduled_df[scheduled_df["workout_date_dt"] == today_dt] if not scheduled_df.empty else pd.DataFrame()

    if not today_row.empty:
        row = today_row.iloc[0]
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); 
                        border: 1px solid #3b322e; border-radius: 12px; padding: 18px 22px; margin-bottom: 20px; 
                        box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #332a27; padding-bottom: 10px; margin-bottom: 12px;">
                    <span style="font-size: 1.1rem; font-weight: 700; color: #f0e2a3;">{row['day_name']}, {row['workout_date']} — {row['title']}</span>
                    <span style="font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #f0e2a3; background: rgba(240, 226, 163, 0.12); padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(240, 226, 163, 0.3);">
                        {row['workout_type'].upper()}
                    </span>
                </div>
                <div style="display: flex; gap: 28px; font-size: 0.9rem; color: #f0e2a3; margin-bottom: 12px;">
                    <div><span style="color: #c8b99c;">Target Distance:</span> <strong style="color: #f0e2a3;">{row['target_distance_km']} km</strong></div>
                    <div><span style="color: #c8b99c;">Target Pace:</span> <strong style="color: #f0e2a3;">{row['target_pace'] or 'N/A'}</strong></div>
                </div>
                <div style="font-size: 0.85rem; color: #f0e2a3; line-height: 1.5; border-top: 1px dashed #332a27; padding-top: 10px;">
                    <strong style="color: #c8b99c;">Session Details:</strong> {row['description']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); 
                        border: 1px solid #3b322e; border-radius: 12px; padding: 18px 22px; margin-bottom: 20px; 
                        box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="font-size: 1.05rem; font-weight: 700; color: #f0e2a3;">
                    {today_dt.strftime('%A, %B %d, %Y')} — Rest Day & Active Recovery
                </div>
                <div style="font-size: 0.85rem; color: #c8b99c; margin-top: 6px;">
                    No key workout scheduled for today. Take time to stretch, hydrate, and recover!
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 3. Upcoming Workouts Agenda (Next 3 Sessions)
    render_section_header("Upcoming Workouts (Next 3 Sessions)", icon_name="plan")

    if not upcoming_df.empty:
        next_workouts = upcoming_df.head(3)
        num_cols = max(1, min(len(next_workouts), 3))
        cols = st.columns(num_cols)
        for idx, (_, item) in enumerate(next_workouts.iterrows()):
            w_dt = item["workout_date_dt"]
            w_dt_str = w_dt.strftime('%b %d') if hasattr(w_dt, 'strftime') else str(w_dt)
            days_away = (w_dt - today_dt).days if hasattr(w_dt, '__sub__') else 0
            if days_away == 0:
                badge = "TODAY"
            elif days_away == 1:
                badge = "TOMORROW"
            elif days_away > 1:
                badge = f"IN {days_away} DAYS"
            else:
                badge = "PAST SESSION"

            col_idx = idx % num_cols
            with cols[col_idx]:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); 
                                border: 1px solid #3b322e; border-radius: 12px; padding: 16px; margin-bottom: 12px;
                                box-shadow: 0 4px 14px rgba(0,0,0,0.35);">
                        <div style="font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #f0e2a3; letter-spacing: 0.05em; margin-bottom: 6px;">
                            {badge}
                        </div>
                        <h4 style="margin: 4px 0 6px 0; font-size: 1rem; color: #f0e2a3;">{item['day_name']} ({w_dt_str})</h4>
                        <div style="font-size: 0.82rem; font-weight: 600; color: #e2d58b; margin-bottom: 8px;">{item['workout_type']}</div>
                        <div style="font-size: 0.83rem; color: #c8b99c; margin-bottom: 4px;">Distance: <strong style="color: #f0e2a3;">{item['target_distance_km']} km</strong></div>
                        <div style="font-size: 0.83rem; color: #c8b99c; margin-bottom: 6px;">Target Pace: <strong style="color: #f0e2a3;">{item['target_pace'] or 'N/A'}</strong></div>
                        <div style="font-size: 0.78rem; color: #c8b99c; opacity: 0.9; margin-top: 8px; border-top: 1px solid #332a27; padding-top: 6px;">{str(item['description'])[:100]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.warning("No upcoming workouts found in the active plan.")


    st.markdown("---")


    # 4. Full Training Plan Schedule Table
    render_section_header("Full Training Plan Schedule", icon_name="plan")


    if not scheduled_df.empty:
        # Summary metrics
        total_scheduled_km = scheduled_df["target_distance_km"].sum()
        completed_km = past_df["target_distance_km"].sum() if not past_df.empty else 0.0
        remaining_km = upcoming_df["target_distance_km"].sum() if not upcoming_df.empty else 0.0

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            render_metric_card("Total Plan Distance", f"{total_scheduled_km:.1f} km", subtext="All weeks combined")
        with m2:
            render_metric_card("Completed Plan Distance", f"{completed_km:.1f} km", subtext="Past scheduled sessions")
        with m3:
            render_metric_card("Remaining Plan Distance", f"{remaining_km:.1f} km", subtext="Upcoming sessions")
        with m4:
            weeks_count = scheduled_df["week_number"].nunique() if "week_number" in scheduled_df else 13
            render_metric_card("Plan Duration", f"{weeks_count} Weeks", subtext="10K Training Cycle")


        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Detailed Schedule Table")

        
        # Display clean dataframe
        display_df = scheduled_df[[
            "week_number", "workout_date", "day_name", "workout_type", 
            "target_distance_km", "target_pace", "description"
        ]].copy()
        display_df.columns = [
            "Week #", "Date", "Day", "Workout Type", "Distance (km)", "Target Pace", "Description"
        ]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

