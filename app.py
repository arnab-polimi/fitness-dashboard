"""
ApexFitness - Professional Personal Fitness Intelligence Dashboard.
Main Streamlit Application Entrypoint with GarminDb Pipeline Support.
"""
import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(
    page_title="ApexFitness | Personal Fitness Intelligence",
    page_icon=None,
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
from src.ingestion.garmin_sync_runner import GarminSyncRunner, DEFAULT_GARMIN_SYNC_SCRIPT
from src.ui.theme import apply_dark_theme
from src.ui.icons import get_icon_html
from src.ui.views import (
    render_overview_view,
    render_training_load_view,
    render_cardiovascular_view,
    render_injury_risk_view,
    render_insights_view,
    render_race_predictor_view,
    render_import_view,
    render_settings_view,
    render_walking_view,
    render_cycling_view,
    render_hiking_view,
    render_yoga_view,
    render_multisport_view,
    render_sleep_view,
)

# Apply sleek modern dark theme styling
apply_dark_theme()


def init_state():
    """Initializes state and performs one Garmin refresh per opened session."""
    if "db_manager" not in st.session_state or not hasattr(st.session_state.db_manager, "get_daily_health_df"):
        st.session_state.db_manager = DatabaseManager()
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = st.session_state.db_manager.get_user_profile()
    if "initial_garmindb_checked" not in st.session_state:
        auto_sync_status = {"status": "not_started", "message": ""}
        if GarminSyncRunner.is_available(DEFAULT_GARMIN_SYNC_SCRIPT):
            try:
                download_result = GarminSyncRunner.run(DEFAULT_GARMIN_SYNC_SCRIPT)
                if download_result["status"] != "success":
                    auto_sync_status = {
                        "status": "download_failed",
                        "message": "Garmin download did not finish. Existing dashboard data is still available.",
                    }
                else:
                    sync_result = GarminDbPipeline.sync_all(
                        st.session_state.db_manager,
                        st.session_state.user_profile,
                    )
                    auto_sync_status = {
                        "status": "success",
                        "message": (
                            f"Garmin refreshed: {sync_result['activities_extracted']} activities and "
                            f"{sync_result['health_days_saved']} health days processed."
                        ),
                    }
                st.session_state.user_profile = st.session_state.db_manager.get_user_profile()
            except Exception as exc:
                auto_sync_status = {
                    "status": "failed",
                    "message": f"Automatic Garmin sync could not run: {exc}",
                }
        elif st.session_state.db_manager.count_activities() == 0 and GarminDbPipeline.is_garmindb_available():
            try:
                sync_result = GarminDbPipeline.sync_all(
                    st.session_state.db_manager,
                    st.session_state.user_profile,
                )
                auto_sync_status = {
                    "status": "offline_import",
                    "message": f"Imported existing GarminDb data: {sync_result['activities_extracted']} activities.",
                }
                st.session_state.user_profile = st.session_state.db_manager.get_user_profile()
            except Exception as exc:
                auto_sync_status = {"status": "failed", "message": f"GarminDb import failed: {exc}"}
        else:
            auto_sync_status = {
                "status": "script_unavailable",
                "message": "Automatic Garmin download is unavailable; existing dashboard data was retained.",
            }
        st.session_state.garmin_auto_sync_status = auto_sync_status
        st.session_state.initial_garmindb_checked = True


init_state()
db: DatabaseManager = st.session_state.db_manager
user_profile: UserProfile = st.session_state.user_profile

# 2. Fetch and Process Data
activities = db.get_all_activities()
health_df = db.get_daily_health_df()
raw_garmin_runs = GarminDbPipeline.get_raw_running_activities()

if activities:
    activities = RunningMetricsCalculator.enrich_activities(activities, user_profile)
    load_activities = raw_garmin_runs or activities
    daily_loads = TrainingLoadEngine.calculate_daily_metrics(load_activities, user_profile)
    current_ctl = daily_loads[-1].ctl if daily_loads else 45.0
    race_predictions = RacePredictor.predict_all(activities, user_profile, current_ctl=current_ctl)
    risk_report = InjuryRiskEngine.evaluate(daily_loads, load_activities)
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


# 3. Sidebar Navigation & Activity Focus Selector
with st.sidebar:
    run_brand_icon = get_icon_html("running", size=24, margin_right=8)
    st.markdown(
        f"""
        <div style="padding: 6px 0 14px 0; display: flex; align-items: center;">
            {run_brand_icon}
            <div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #c1d37f; letter-spacing: -0.01em; line-height: 1.1;">
                    APEX FITNESS
                </div>
                <div style="font-size: 0.68rem; color: #c8b99c; letter-spacing: 0.08em; text-transform: uppercase;">
                    Physical Intelligence Platform
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    auto_sync_status = st.session_state.get("garmin_auto_sync_status")
    if auto_sync_status and auto_sync_status["status"] in {"success", "offline_import"}:
        st.caption(f"{auto_sync_status['message']}")
    elif auto_sync_status and auto_sync_status["status"] in {"download_failed", "failed"}:
        st.warning(auto_sync_status["message"])

    # 1. Sport / Activity Mode Selector
    st.markdown(
        """
        <div style="font-size: 0.68rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
            Activity Focus
        </div>
        """,
        unsafe_allow_html=True,
    )
    sport_focus = st.selectbox(
        "Activity Focus",
        [
            "Running",
            "Walking",
            "Cycling",
            "Hiking",
            "Yoga & Mobility",
            "All Activities",
        ],
        index=0,
        label_visibility="collapsed",
    )

    # 2. Dynamic Sport-Specific Quick Stats Widget
    if sport_focus == "Running" and daily_loads:
        latest = daily_loads[-1]
        run_w_icon = get_icon_html("running", size=16, margin_right=6)
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); border: 1px solid #3b322e; border-radius: 10px; padding: 12px 14px; margin-top: 8px; margin-bottom: 14px; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #332a27; padding-bottom: 6px;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #f0e2a3; display: flex; align-items: center;">{run_w_icon}{user_profile.name}</span>
                    <span style="font-size: 0.65rem; font-family: 'JetBrains Mono', monospace; color: #c1d37f; background: rgba(193,211,127,0.12); padding: 1px 5px; border-radius: 4px; border: 1px solid rgba(193,211,127,0.3);">
                        RUNNING
                    </span>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Fitness (CTL):</span> <strong style="color: #80923F;">{latest.ctl:.1f}</strong>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Fatigue (ATL):</span> <strong style="color: #7A2921;">{latest.atl:.1f}</strong>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Form (TSB):</span> <strong style="color: {latest.form_color};">{latest.tsb:+.1f}</strong>
                </div>
                <div style="text-align: center; border-top: 1px solid #332a27; padding-top: 6px;">
                    <span class="badge" style="background: rgba(240, 226, 163, 0.08); color: {latest.form_color}; border: 1px solid {latest.form_color}; font-size: 0.64rem; padding: 2px 8px;">
                        {latest.form_state}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif sport_focus == "Walking":
        walk_acts = [a for a in activities if a.sport_type in ["walking", "walk"]]
        walk_km = sum(a.distance_km for a in walk_acts)
        walk_hours = sum(a.duration_seconds for a in walk_acts) / 3600.0
        walk_w_icon = get_icon_html("walking", size=16, margin_right=6)
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); border: 1px solid #3b322e; border-radius: 10px; padding: 12px 14px; margin-top: 8px; margin-bottom: 14px; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #332a27; padding-bottom: 6px;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #f0e2a3; display: flex; align-items: center;">{walk_w_icon}Walking Summary</span>
                    <span style="font-size: 0.65rem; color: #c1d37f; background: rgba(193,211,127,0.12); padding: 1px 5px; border-radius: 4px; border: 1px solid rgba(193,211,127,0.3);">{len(walk_acts)} SESSIONS</span>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Total Distance:</span> <strong style="color: #c1d37f;">{walk_km:.1f} km</strong>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Active Time:</span> <strong style="color: #abb273;">{walk_hours:.1f} hrs</strong>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between;">
                    <span>Est. Steps:</span> <strong style="color: #f0e2a3;">{int(walk_km*1300):,}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif sport_focus == "Cycling":
        bike_acts = [a for a in activities if a.sport_type in ["cycling", "bike", "ride"]]
        bike_km = sum(a.distance_km for a in bike_acts)
        bike_hours = sum(a.duration_seconds for a in bike_acts) / 3600.0
        avg_spd = (bike_km / bike_hours) if bike_hours > 0 else 0.0
        bike_w_icon = get_icon_html("bike", size=16, margin_right=6)
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); border: 1px solid #3b322e; border-radius: 10px; padding: 12px 14px; margin-top: 8px; margin-bottom: 14px; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #332a27; padding-bottom: 6px;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #f0e2a3; display: flex; align-items: center;">{bike_w_icon}Cycling Summary</span>
                    <span style="font-size: 0.65rem; color: #e2d58b; background: rgba(226,213,139,0.12); padding: 1px 5px; border-radius: 4px; border: 1px solid rgba(226,213,139,0.3);">{len(bike_acts)} RIDES</span>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Saddle Distance:</span> <strong style="color: #e2d58b;">{bike_km:.1f} km</strong>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Avg Speed:</span> <strong style="color: #abb273;">{avg_spd:.1f} km/h</strong>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between;">
                    <span>Saddle Time:</span> <strong style="color: #f0e2a3;">{bike_hours:.1f} hrs</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif sport_focus == "Hiking":
        hike_acts = [a for a in activities if a.sport_type in ["hiking", "hike"]]
        hike_km = sum(a.distance_km for a in hike_acts)
        hike_ascent = sum(a.elevation_gain_m or 0 for a in hike_acts)
        hike_hours = sum(a.duration_seconds for a in hike_acts) / 3600.0
        hike_w_icon = get_icon_html("hiking", size=16, margin_right=6)
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); border: 1px solid #3b322e; border-radius: 10px; padding: 12px 14px; margin-top: 8px; margin-bottom: 14px; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #332a27; padding-bottom: 6px;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #f0e2a3; display: flex; align-items: center;">{hike_w_icon}Hiking Summary</span>
                    <span style="font-size: 0.65rem; color: #abb273; background: rgba(171,178,115,0.12); padding: 1px 5px; border-radius: 4px; border: 1px solid rgba(171,178,115,0.3);">{len(hike_acts)} HIKES</span>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Ascent (D+):</span> <strong style="color: #c1d37f;">+{hike_ascent:,.0f} m</strong>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Trail Distance:</span> <strong style="color: #abb273;">{hike_km:.1f} km</strong>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between;">
                    <span>Trail Time:</span> <strong style="color: #f0e2a3;">{hike_hours:.1f} hrs</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif sport_focus == "Yoga & Mobility":
        yoga_acts = [a for a in activities if a.sport_type in ["yoga", "pilates", "mobility", "stretch"]]
        yoga_mins = sum(a.duration_seconds for a in yoga_acts) / 60.0
        hrs = [a.avg_hr for a in yoga_acts if a.avg_hr and a.avg_hr > 0]
        avg_hr = (sum(hrs) / len(hrs)) if hrs else 0.0
        yoga_w_icon = get_icon_html("yoga", size=16, margin_right=6)
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); border: 1px solid #3b322e; border-radius: 10px; padding: 12px 14px; margin-top: 8px; margin-bottom: 14px; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #332a27; padding-bottom: 6px;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #f0e2a3; display: flex; align-items: center;">{yoga_w_icon}Yoga Summary</span>
                    <span style="font-size: 0.65rem; color: #f9d4bb; background: rgba(249,212,187,0.12); padding: 1px 5px; border-radius: 4px; border: 1px solid rgba(249,212,187,0.3);">{len(yoga_acts)} SESSIONS</span>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Mat Time:</span> <strong style="color: #f9d4bb;">{int(yoga_mins)} mins</strong>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Calming HR:</span> <strong style="color: #e2d58b;">{avg_hr:.0f} bpm</strong>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between;">
                    <span>Recovery State:</span> <strong style="color: #c1d37f;">Restorative</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif sport_focus == "All Activities":
        total_km = sum(a.distance_km for a in activities)
        total_hours = sum(a.duration_seconds for a in activities) / 3600.0
        all_w_icon = get_icon_html("multisport", size=16, margin_right=6)
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); border: 1px solid #3b322e; border-radius: 10px; padding: 12px 14px; margin-top: 8px; margin-bottom: 14px; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #332a27; padding-bottom: 6px;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #f0e2a3; display: flex; align-items: center;">{all_w_icon}All Activities Summary</span>
                    <span style="font-size: 0.65rem; color: #c1d37f; background: rgba(193,211,127,0.12); padding: 1px 5px; border-radius: 4px; border: 1px solid rgba(193,211,127,0.3);">{len(activities)} TOTAL</span>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Total Distance:</span> <strong style="color: #c1d37f;">{total_km:.1f} km</strong>
                </div>
                <div style="font-size: 0.72rem; color: #c8b99c; display: flex; justify-content: space-between;">
                    <span>Active Hours:</span> <strong style="color: #abb273;">{total_hours:.1f} hrs</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Dynamic Navigation Menu Based on Sport Focus
    if sport_focus == "Running":
        nav_options = [
            "Executive Overview",
            "Training Load & PMC",
            "Cardiovascular & Efficiency",
            "Sleep & Recovery Intelligence",
            "Training Stress & Risk",
            "Fitness Insights & Analysis",
            "Race Predictor & VDOT",
            "Data Import & Sync",
            "Athlete Settings",
        ]
    elif sport_focus == "Walking":
        nav_options = [
            "Walking Overview",
            "Data Import & Sync",
            "Athlete Settings",
        ]
    elif sport_focus == "Cycling":
        nav_options = [
            "Cycling Overview",
            "Data Import & Sync",
            "Athlete Settings",
        ]
    elif sport_focus == "Hiking":
        nav_options = [
            "Hiking Overview",
            "Data Import & Sync",
            "Athlete Settings",
        ]
    elif sport_focus == "Yoga & Mobility":
        nav_options = [
            "Yoga & Mobility Overview",
            "Data Import & Sync",
            "Athlete Settings",
        ]
    else:  # All Activities
        nav_options = [
            "Multi-Sport Overview",
            "Sleep & Recovery Intelligence",
            "Data Import & Sync",
            "Athlete Settings",
        ]

    nav_selection = st.radio(
        "Navigation",
        nav_options,
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown(
        """
        <div style="font-size: 0.68rem; color: #64748b; text-align: center; line-height: 1.4;">
            ApexFitness Platform<br>
            Running • Walking • Cycling • Hiking • Yoga • Swimming
        </div>
        """,
        unsafe_allow_html=True,
    )


# 4. View Router
if nav_selection == "Executive Overview":
    render_overview_view(
        activities, daily_loads, user_profile, race_predictions, risk_report, daily_df, activities_df
    )
elif nav_selection == "Training Load & PMC":
    render_training_load_view(activities, daily_loads, user_profile, daily_df)
elif nav_selection == "Cardiovascular & Efficiency":
    render_cardiovascular_view(activities, daily_loads, user_profile, daily_df, activities_df, health_df)
elif nav_selection == "Sleep & Recovery Intelligence":
    render_sleep_view(health_df, user_profile)
elif nav_selection == "Training Stress & Risk":
    render_injury_risk_view(activities, daily_loads, risk_report)
elif nav_selection == "Fitness Insights & Analysis":
    render_insights_view(insights)
elif nav_selection == "Race Predictor & VDOT":
    render_race_predictor_view(activities, user_profile, race_predictions)
elif nav_selection == "Walking Overview":
    render_walking_view(activities, user_profile, activities_df)
elif nav_selection == "Cycling Overview":
    render_cycling_view(activities, user_profile, activities_df)
elif nav_selection == "Hiking Overview":
    render_hiking_view(activities, user_profile, activities_df)
elif nav_selection == "Yoga & Mobility Overview":
    render_yoga_view(activities, user_profile, activities_df)
elif nav_selection == "Multi-Sport Overview":
    render_multisport_view(activities, user_profile, activities_df)
elif nav_selection == "Data Import & Sync":
    render_import_view(db, user_profile, on_data_change)
elif nav_selection == "Athlete Settings":
    render_settings_view(db, user_profile, on_profile_change)