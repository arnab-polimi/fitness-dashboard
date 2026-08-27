"""
ApexFitness - Professional Personal Fitness Intelligence Dashboard.
Main Streamlit Application Entrypoint with GarminDb Pipeline Support.
"""
import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(
    page_title="ApexFitness | Personal Fitness Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.models.user_profile import UserProfile
from src.db.database import DatabaseManager
from src.analytics.training_load import TrainingLoadEngine
from src.analytics.running_metrics import RunningMetricsCalculator
from src.analytics.race_predictor import RacePredictor
from src.analytics.injury_risk import InjuryRiskEngine
from src.insights.engine import FitnessInsightsEngine
from src.ingestion.garmindb_pipeline import GarminDbPipeline
from src.ui.theme import apply_dark_theme
from src.ui.views import (
    render_overview_view,
    render_training_load_view,
    render_cardiovascular_view,
    render_injury_risk_view,
    render_insights_view,
    render_race_predictor_view,
    render_activity_log_view,
    render_import_view,
    render_settings_view,
)

# Apply sleek modern dark theme styling
apply_dark_theme()


def init_state():
    """Initializes session state, database manager, and optional GarminDb auto-sync."""
    if "db_manager" not in st.session_state or not hasattr(st.session_state.db_manager, "get_daily_health_df"):
        st.session_state.db_manager = DatabaseManager()
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = st.session_state.db_manager.get_user_profile()
    if "initial_garmindb_checked" not in st.session_state:
        # Check if database is empty and GarminDb is available
        if st.session_state.db_manager.count_activities() == 0 and GarminDbPipeline.is_garmindb_available():
            try:
                GarminDbPipeline.sync_all(st.session_state.db_manager, st.session_state.user_profile)
                st.session_state.user_profile = st.session_state.db_manager.get_user_profile()
            except Exception:
                pass
        st.session_state.initial_garmindb_checked = True


init_state()
db: DatabaseManager = st.session_state.db_manager
user_profile: UserProfile = st.session_state.user_profile

# 2. Fetch and Process Data
activities = db.get_all_activities()
health_df = db.get_daily_health_df()

if activities:
    activities = RunningMetricsCalculator.enrich_activities(activities, user_profile)
    daily_loads = TrainingLoadEngine.calculate_daily_metrics(activities, user_profile)
    current_ctl = daily_loads[-1].ctl if daily_loads else 45.0
    race_predictions = RacePredictor.predict_all(activities, user_profile, current_ctl=current_ctl)
    risk_report = InjuryRiskEngine.evaluate(daily_loads, activities)
    insights = FitnessInsightsEngine.generate_all_insights(
        activities, daily_loads, user_profile, race_predictions, risk_report
    )
    activities_df = db.get_activities_df()
    daily_df = pd.DataFrame([
        {
            "date": dl.date,
            "distance_meters": dl.distance_meters,
            "duration_seconds": dl.duration_seconds,
            "activity_count": dl.activity_count,
            "total_tss": dl.total_tss,
            "total_trimp": dl.total_trimp,
            "ctl": dl.ctl,
            "atl": dl.atl,
            "tsb": dl.tsb,
            "acwr": dl.acwr,
            "ramp_rate_ctl": dl.ramp_rate_ctl,
            "monotony": dl.monotony,
            "strain": dl.strain,
            "efficiency_factor": dl.efficiency_factor,
        }
        for dl in daily_loads
    ])
else:
    daily_loads = []
    race_predictions = []
    risk_report = InjuryRiskEngine._default_empty_report()
    insights = FitnessInsightsEngine.generate_all_insights([], [], user_profile, [], risk_report)
    activities_df = pd.DataFrame()
    daily_df = pd.DataFrame()


def on_data_change():
    st.rerun()


def on_profile_change(new_prof: UserProfile):
    st.session_state.user_profile = new_prof
    st.rerun()


# 3. Sidebar Navigation & Athlete Telemetry
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 8px 0 16px 0;">
            <div style="font-size: 1.25rem; font-weight: 800; color: #00d2ff; letter-spacing: -0.02em;">
                ⚡ APEX FITNESS
            </div>
            <div style="font-size: 0.72rem; color: #94a3b8; letter-spacing: 0.08em; text-transform: uppercase;">
                Personal Fitness Intelligence
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Athlete Quick Stats
    if daily_loads:
        latest = daily_loads[-1]
        st.markdown(
            f"""
            <div style="background: #131c31; border: 1px solid #1e2d4d; border-radius: 10px; padding: 12px 14px; margin-bottom: 16px;">
                <div style="font-size: 0.8rem; font-weight: 700; color: #f8fafc; margin-bottom: 4px;">
                    👤 {user_profile.name}
                </div>
                <div style="font-size: 0.72rem; color: #94a3b8; display: flex; justify-content: space-between; margin-bottom: 2px;">
                    <span>Fitness (CTL):</span> <strong style="color: #00d2ff;">{latest.ctl:.1f}</strong>
                </div>
                <div style="font-size: 0.72rem; color: #94a3b8; display: flex; justify-content: space-between; margin-bottom: 2px;">
                    <span>Fatigue (ATL):</span> <strong style="color: #a855f7;">{latest.atl:.1f}</strong>
                </div>
                <div style="font-size: 0.72rem; color: #94a3b8; display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Form (TSB):</span> <strong style="color: {latest.form_color};">{latest.tsb:+.1f}</strong>
                </div>
                <div style="margin-top: 6px; text-align: center;">
                    <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: {risk_report.status_color}; border: 1px solid {risk_report.status_color}; font-size: 0.68rem;">
                        {risk_report.overall_status}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Navigation Menu
    nav_selection = st.radio(
        "Navigation",
        [
            "⚡ Executive Overview",
            "📈 Training Load & PMC",
            "🫀 Cardiovascular & Efficiency",
            "🛡️ Training Stress & Risk",
            "🧠 What is Happening to My Fitness?",
            "🏁 Race Predictor & VDOT",
            "🏃 Activity Log & Inspector",
            "📥 Data Import & Sync",
            "⚙️ Athlete Settings",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown(
        """
        <div style="font-size: 0.7rem; color: #64748b; text-align: center;">
            ApexFitness v2.0 • GarminDb Direct<br>
            Multi-Signal Load & Biomechanics
        </div>
        """,
        unsafe_allow_html=True,
    )


# 4. View Router
if nav_selection == "⚡ Executive Overview":
    render_overview_view(
        activities, daily_loads, user_profile, race_predictions, risk_report, daily_df, activities_df
    )
elif nav_selection == "📈 Training Load & PMC":
    render_training_load_view(activities, daily_loads, user_profile, daily_df)
elif nav_selection == "🫀 Cardiovascular & Efficiency":
    render_cardiovascular_view(activities, daily_loads, user_profile, daily_df, activities_df, health_df)
elif nav_selection == "🛡️ Training Stress & Risk":
    render_injury_risk_view(activities, daily_loads, risk_report)
elif nav_selection == "🧠 What is Happening to My Fitness?":
    render_insights_view(insights)
elif nav_selection == "🏁 Race Predictor & VDOT":
    render_race_predictor_view(activities, user_profile, race_predictions)
elif nav_selection == "🏃 Activity Log & Inspector":
    render_activity_log_view(activities, user_profile, activities_df)
elif nav_selection == "📥 Data Import & Sync":
    render_import_view(db, user_profile, on_data_change)
elif nav_selection == "⚙️ Athlete Settings":
    render_settings_view(db, user_profile, on_profile_change)
