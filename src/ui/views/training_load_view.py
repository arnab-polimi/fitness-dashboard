"""
Training Load & Performance Management (PMC) View.
"""
from typing import List
import streamlit as st
import pandas as pd

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.models.metrics import DailyLoad
from src.ui.charts import plot_pmc_chart, plot_weekly_mileage_and_load, PLOT_LAYOUT_DARK
import plotly.graph_objects as go


def render_training_load_view(
    activities: List[Activity],
    daily_loads: List[DailyLoad],
    user_profile: UserProfile,
    daily_df: pd.DataFrame,
) -> None:
    st.markdown("## 📊 Training Load & Performance Management (PMC)")
    st.caption("Exponentially Weighted Moving Averages for Chronic Training Load (Fitness), Acute Training Load (Fatigue), and Training Stress Balance (Form).")

    if daily_df.empty:
        st.info("No training data available. Please import activities to generate your Performance Management Chart.")
        return

    # Date range selector filter
    col1, col2 = st.columns([2, 4])
    with col1:
        timeframe = st.selectbox(
            "Select Timeframe",
            ["Last 90 Days", "Last 30 Days", "Last 180 Days", "Last 1 Year", "All Time"],
            index=0,
        )

    # Filter dataframe
    df = daily_df.copy()
    today = pd.to_datetime("now").date()

    if timeframe == "Last 30 Days":
        cutoff = today - pd.Timedelta(days=30)
        df = df[df["date"] >= cutoff]
    elif timeframe == "Last 90 Days":
        cutoff = today - pd.Timedelta(days=90)
        df = df[df["date"] >= cutoff]
    elif timeframe == "Last 180 Days":
        cutoff = today - pd.Timedelta(days=180)
        df = df[df["date"] >= cutoff]
    elif timeframe == "Last 1 Year":
        cutoff = today - pd.Timedelta(days=365)
        df = df[df["date"] >= cutoff]

    # Main PMC Chart
    st.plotly_chart(plot_pmc_chart(df), use_container_width=True)

    # Secondary Charts: Monotony & Strain
    st.markdown("### 🔄 Training Monotony & Strain Dynamics")
    st.caption("Foster's Monotony reflects daily load variance; Strain reflects cumulative fatigue potential.")

    fig_monotony = go.Figure()
    if "monotony" in df.columns:
        fig_monotony.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["monotony"],
                name="Training Monotony",
                line=dict(color="#06b6d4", width=2),
            )
        )
        fig_monotony.add_hline(
            y=1.5,
            line_dash="dash",
            line_color="#f59e0b",
            annotation_text="Caution (>1.5)",
            annotation_position="top left",
        )
        fig_monotony.add_hline(
            y=2.0,
            line_dash="dot",
            line_color="#ef4444",
            annotation_text="High Monotony (>2.0)",
            annotation_position="top left",
        )
    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(title="7-Day Rolling Training Monotony", yaxis_title="Monotony Score", height=300)
    fig_monotony.update_layout(layout)
    st.plotly_chart(fig_monotony, use_container_width=True)

    # Educational Expander
    with st.expander("📚 Understanding Banister EWMA, CTL, ATL, and TSB"):
        st.markdown("""
        - **CTL (Chronic Training Load / Fitness)**: Represents your 42-day rolling aerobic engine and physical preparedness. Calculated with an exponential decay time constant $\\tau = 42$ days.
        - **ATL (Acute Training Load / Fatigue)**: Represents your 7-day immediate fatigue. Calculated with an exponential decay time constant $\\tau = 7$ days.
        - **TSB (Training Stress Balance / Form)**: $TSB = CTL - ATL$.
          - **+10 to +25**: Fresh & Race Ready.
          - **-10 to +10**: Productive Maintenance.
          - **-30 to -10**: Optimal Progressive Overload (Building fitness with manageable fatigue).
          - **< -30**: High Fatigue / Overreaching danger.
        - **rTSS (Running Training Stress Score)**: Quantifies the physiological stress of running based on duration and pace intensity relative to your lactate threshold pace ($vLT$).
        """)
