"""
Plotly interactive chart builders with dark cyber/stealth aesthetics.
"""
from typing import List, Optional
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.models.metrics import RiskReport
from src.models.user_profile import UserProfile

PLOT_LAYOUT_DARK = dict(
    paper_bgcolor="rgba(18, 14, 13, 0.0)",
    plot_bgcolor="rgba(26, 20, 19, 0.6)",
    font=dict(family="Inter, sans-serif", color="#f0e2a3", size=11),
    margin=dict(l=28, r=15, t=40, b=35),
    autosize=True,
    xaxis=dict(
        gridcolor="#3b322e",
        zerolinecolor="#7d7059",
        showgrid=True,
        tickfont=dict(color="#c8b99c", size=10),
    ),
    yaxis=dict(
        gridcolor="#3b322e",
        zerolinecolor="#7d7059",
        showgrid=True,
        tickfont=dict(color="#c8b99c", size=10),
    ),
    legend=dict(
        bgcolor="rgba(28, 23, 22, 0.85)",
        bordercolor="#3b322e",
        borderwidth=1,
        font=dict(color="#f0e2a3", size=9.5),
    ),
    hoverlabel=dict(
        bgcolor="#1c1716",
        bordercolor="#c1d37f",
        font=dict(family="JetBrains Mono, monospace", color="#f0e2a3", size=11),
    ),
)


def plot_pmc_chart(daily_df: pd.DataFrame) -> go.Figure:
    """
    Enhanced Performance Management Chart (PMC):
    - CTL (Fitness - 42d EWMA) with cyan glow area fill
    - ATL (Fatigue - 7d EWMA) with magenta glow line
    - TSB (Form = CTL - ATL) continuous spline curve with zero reference
    - Daily TSS bars dynamically color-coded by intensity
    - Shaded physiological training & recovery zones
    """
    if daily_df.empty:
        fig = go.Figure()
        fig.update_layout(**PLOT_LAYOUT_DARK, title="No Training Data Available")
        return fig

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.07,
        row_heights=[0.72, 0.28],
        subplot_titles=(
            "<b>Performance Management Dynamics (Fitness • Fatigue • Form)</b>",
            "<b>Daily Training Stress Volume (TSS)</b>",
        ),
    )

    # 1. TSS Color Grading by Workout Stress Intensity
    tss_colors = []
    for tss in daily_df["total_tss"]:
        if tss <= 0:
            tss_colors.append("rgba(114, 95, 83, 0.3)")
        elif tss < 50:
            tss_colors.append("rgba(193, 211, 127, 0.75)")   # Willow Green / Recovery
        elif tss < 90:
            tss_colors.append("rgba(160, 162, 109, 0.8)")    # Palm Leaf / Aerobic
        elif tss < 140:
            tss_colors.append("rgba(226, 213, 139, 0.85)")   # Light Gold / Threshold
        else:
            tss_colors.append("rgba(249, 212, 187, 0.95)")   # Peach Fuzz / High Stress

    fig.add_trace(
        go.Bar(
            x=daily_df["date"],
            y=daily_df["total_tss"],
            name="Daily TSS",
            marker=dict(color=tss_colors, line=dict(color="rgba(255, 255, 255, 0.15)", width=1)),
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Daily TSS: <b>%{y:.0f}</b><extra></extra>",
        ),
        row=2,
        col=1,
    )

    # 2. Fitness (CTL 42d) - Natural Olive Moss Green (#80923F)
    fig.add_trace(
        go.Scatter(
            x=daily_df["date"],
            y=daily_df["ctl"],
            name="Fitness (CTL 42d)",
            line=dict(color="#80923F", width=3.0, shape="spline", smoothing=0.8),
            fill="tozeroy",
            fillcolor="rgba(128, 146, 63, 0.15)",
            mode="lines",
            hovertemplate="<b>Fitness (CTL):</b> %{y:.1f}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # 3. Fatigue (ATL 7d) - Terracotta Crimson Red (#7A2921)
    fig.add_trace(
        go.Scatter(
            x=daily_df["date"],
            y=daily_df["atl"],
            name="Fatigue (ATL 7d)",
            line=dict(color="#7A2921", width=2.4, shape="spline", smoothing=0.8),
            fill="tozeroy",
            fillcolor="rgba(122, 41, 33, 0.12)",
            mode="lines",
            hovertemplate="<b>Fatigue (ATL):</b> %{y:.1f}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # 4. Form (TSB = CTL - ATL) - Steel Blue Spline Curve (#4D71B2)
    fig.add_trace(
        go.Scatter(
            x=daily_df["date"],
            y=daily_df["tsb"],
            name="Form (TSB)",
            line=dict(color="#4D71B2", width=2.6, shape="spline", smoothing=0.8),
            mode="lines",
            hovertemplate="<b>Form (TSB):</b> %{y:+.1f}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Reference Zero Line for Form
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="rgba(240, 226, 163, 0.35)",
        line_width=1.2,
        row=1,
        col=1,
    )

    # Shaded Physiological Form Zones
    fig.add_hrect(
        y0=10, y1=25,
        fillcolor="rgba(193, 211, 127, 0.08)", line_width=0,
        annotation_text="Race Ready (+10 to +25)", annotation_position="top right",
        annotation_font=dict(size=9, color="#c1d37f"),
        row=1, col=1,
    )
    fig.add_hrect(
        y0=-10, y1=10,
        fillcolor="rgba(160, 162, 109, 0.05)", line_width=0,
        annotation_text="Neutral / Productive (-10 to +10)", annotation_position="top right",
        annotation_font=dict(size=9, color="#a0a26d"),
        row=1, col=1,
    )
    fig.add_hrect(
        y0=-30, y1=-10,
        fillcolor="rgba(226, 213, 139, 0.07)", line_width=0,
        annotation_text="Optimal Overload (-30 to -10)", annotation_position="bottom right",
        annotation_font=dict(size=9, color="#e2d58b"),
        row=1, col=1,
    )
    fig.add_hrect(
        y0=-50, y1=-30,
        fillcolor="rgba(249, 212, 187, 0.08)", line_width=0,
        annotation_text="High Fatigue / Overreaching (< -30)", annotation_position="bottom right",
        annotation_font=dict(size=9, color="#f9d4bb"),
        row=1, col=1,
    )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        height=540,
        margin=dict(l=28, r=15, t=65, b=35),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(28, 23, 22, 0.85)",
            bordercolor="#3b322e",
            font=dict(size=9.5),
        ),
    )
    fig.update_layout(layout)
    fig.update_yaxes(title_text="Training Load", row=1, col=1)
    fig.update_yaxes(title_text="TSS", row=2, col=1)
    return fig


def plot_form_corridor_chart(daily_df: pd.DataFrame) -> go.Figure:
    """
    Dedicated Form (TSB) Freshness & Fatigue Corridor Chart.
    Visualizes exact readiness peaks and overload building cycles.
    """
    if daily_df.empty or "tsb" not in daily_df.columns:
        return go.Figure()

    df = daily_df.copy()
    fig = go.Figure()

    # Form curve
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["tsb"],
            name="Form (TSB)",
            line=dict(color="#38bdf8", width=2.8, shape="spline", smoothing=0.8),
            mode="lines+markers",
            marker=dict(
                size=5,
                color=["#10b981" if val >= 10 else ("#4d71b2" if val >= -10 else ("#f59e0b" if val >= -30 else "#ef4444")) for val in df["tsb"]],
            ),
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Form (TSB): <b>%{y:+.1f}</b><extra></extra>",
        )
    )

    # Zero Line
    fig.add_hline(y=0, line_dash="solid", line_color="rgba(255, 255, 255, 0.4)", line_width=1.5)

    # Shaded Target Form Corridors
    fig.add_hrect(
        y0=10, y1=25,
        fillcolor="rgba(16, 185, 129, 0.12)", line_width=1, line_color="rgba(16, 185, 129, 0.3)",
        annotation_text=" Peak Race Form (+10 to +25)", annotation_position="top left",
        annotation_font=dict(size=10, color="#10b981"),
    )
    fig.add_hrect(
        y0=-10, y1=10,
        fillcolor="rgba(77, 113, 178, 0.12)", line_width=0,
        annotation_text=" Productive Maintenance (-10 to +10)", annotation_position="top left",
        annotation_font=dict(size=10, color="#4d71b2"),
    )
    fig.add_hrect(
        y0=-30, y1=-10,
        fillcolor="rgba(245, 158, 11, 0.10)", line_width=1, line_color="rgba(245, 158, 11, 0.3)",
        annotation_text=" Optimal Progressive Overload (-30 to -10)", annotation_position="bottom left",
        annotation_font=dict(size=10, color="#f59e0b"),
    )
    fig.add_hrect(
        y0=-60, y1=-30,
        fillcolor="rgba(239, 68, 68, 0.12)", line_width=1, line_color="rgba(239, 68, 68, 0.3)",
        annotation_text=" Overreaching & Injury Risk Zone (< -30)", annotation_position="bottom left",
        annotation_font=dict(size=10, color="#ef4444"),
    )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title="<b>Form (TSB) Freshness & Fatigue Corridor Trajectory</b>",
        yaxis_title="Training Stress Balance (TSB)",
        height=380,
    )
    fig.update_layout(layout)
    return fig


def plot_weekly_mileage_and_load(daily_df: pd.DataFrame, unit: str = "metric") -> go.Figure:
    """Aggregates daily data by week to show weekly distance, TSS volume, and CTL growth."""
    if daily_df.empty:
        return go.Figure()

    df = daily_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W-SUN").apply(lambda r: r.start_time)

    weekly = df.groupby("week").agg(
        total_dist=("distance_meters", "sum"),
        total_tss=("total_tss", "sum"),
        run_count=("activity_count", "sum"),
        end_ctl=("ctl", "last"),
    ).reset_index()

    weekly["dist_display"] = weekly["total_dist"] / (1609.344 if unit == "imperial" else 1000.0)
    unit_label = "Miles" if unit == "imperial" else "Kilometers"

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Weekly Mileage Bars (#6f8423)
    fig.add_trace(
        go.Bar(
            x=weekly["week"],
            y=weekly["dist_display"],
            name=f"Weekly Distance ({unit_label})",
            marker=dict(
                color="rgba(111, 132, 35, 0.85)",
                line=dict(color="#6f8423", width=1.2),
            ),
            hovertemplate="<b>Week of %{x|%b %d}</b><br>Distance: <b>%{y:.1f} " + unit_label + "</b><extra></extra>",
        ),
        secondary_y=False,
    )

    # Weekly TSS Line
    fig.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["total_tss"],
            name="Weekly TSS Stress",
            line=dict(color="#f59e0b", width=2.5),
            mode="lines+markers",
            marker=dict(size=6, color="#fbbf24"),
            hovertemplate="Weekly TSS: <b>%{y:.0f}</b><extra></extra>",
        ),
        secondary_y=True,
    )

    # CTL Progression Line
    if "end_ctl" in weekly.columns and weekly["end_ctl"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=weekly["week"],
                y=weekly["end_ctl"],
                name="Fitness (CTL Trend)",
                line=dict(color="#00d2ff", width=2.2, dash="dot"),
                mode="lines",
                hovertemplate="End of Week CTL: <b>%{y:.1f}</b><extra></extra>",
            ),
            secondary_y=True,
        )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title=f"<b>Weekly Mileage ({unit_label}), TSS Volume & Fitness Progression</b>",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_layout(layout)
    fig.update_yaxes(title_text=f"Distance ({unit_label})", secondary_y=False)
    fig.update_yaxes(title_text="TSS & CTL Score", secondary_y=True)
    return fig


def plot_hr_vs_pace_scatter(activities_df: pd.DataFrame) -> go.Figure:
    """Scatter plot of Average Pace vs Heart Rate across all runs."""
    if activities_df.empty or "avg_pace_sec_km" not in activities_df.columns:
        return go.Figure()

    df = activities_df[
        (activities_df["avg_pace_sec_km"].notna()) &
        (activities_df["avg_hr"].notna()) &
        (activities_df["avg_pace_sec_km"] > 150) &
        (activities_df["avg_pace_sec_km"] < 600) &
        (activities_df["avg_hr"] > 90)
    ].copy()

    if df.empty:
        return go.Figure()

    df["pace_min_km"] = df["avg_pace_sec_km"] / 60.0
    df["date_str"] = pd.to_datetime(df["start_time"]).dt.strftime("%Y-%m-%d")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["pace_min_km"],
            y=df["avg_hr"],
            mode="markers",
            marker=dict(
                size=9,
                color=pd.to_datetime(df["start_time"]).astype("int64") // 10**9,
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(
                    title=dict(text="Timeline", font=dict(size=11, color="#cbd5e1")),
                    tickfont=dict(size=9, color="#94a3b8"),
                    len=0.75,
                    thickness=12,
                    x=1.02,
                ),
                line=dict(color="#0f172a", width=1),
            ),
            text=df.apply(lambda r: f"{r['title']}<br>Date: {r['date_str']}<br>Pace: {int(r['pace_min_km'])}:{int((r['pace_min_km']%1)*60):02d} /km<br>HR: {r['avg_hr']:.0f} bpm<br>Dist: {r['distance_km']:.1f} km", axis=1),
            hoverinfo="text",
            name="Workouts",
        )
    )

    if len(df) >= 3:
        z = np.polyfit(df["pace_min_km"], df["avg_hr"], 1)
        p = np.poly1d(z)
        x_vals = np.linspace(df["pace_min_km"].min(), df["pace_min_km"].max(), 50)
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=p(x_vals),
                mode="lines",
                name="Cardiac Drift",
                line=dict(color="#f43f5e", width=2, dash="dash"),
            )
        )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title="Heart Rate vs. Pace (Cardiovascular Efficiency Profile)",
        xaxis_title="Pace (min/km) [Faster ←]",
        yaxis_title="Average Heart Rate (bpm)",
        xaxis=dict(autorange="reversed"),
        height=400,
        showlegend=False,
    )
    fig.update_layout(layout)
    return fig


def plot_efficiency_factor_trend(daily_df: pd.DataFrame) -> go.Figure:
    """Time-series chart of Efficiency Factor (Speed m/min / HR)."""
    if daily_df.empty or "efficiency_factor" not in daily_df.columns:
        return go.Figure()

    df = daily_df[daily_df["efficiency_factor"].notna()].copy()
    if df.empty:
        return go.Figure()

    df["rolling_ef"] = df["efficiency_factor"].rolling(window=14, min_periods=3).mean()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["efficiency_factor"],
            mode="markers",
            marker=dict(color="#38bdf8", size=6, opacity=0.7),
            name="Daily Activity EF",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["rolling_ef"],
            mode="lines",
            line=dict(color="#00ffa3", width=2.5),
            name="14-Day Aerobic Trend",
        )
    )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title="Aerobic Efficiency Factor Trend (Speed / Avg HR)",
        yaxis_title="Efficiency Factor (m/min per bpm)",
        height=360,
    )
    fig.update_layout(layout)
    return fig


def plot_recovery_telemetry_chart(health_df: pd.DataFrame) -> go.Figure:
    """
    Plots daily Resting Heart Rate and Sleep Duration trends from GarminDb.
    """
    if health_df.empty or "resting_hr" not in health_df.columns:
        return go.Figure()

    df = health_df[health_df["resting_hr"].notna()].copy()
    if df.empty:
        return go.Figure()

    df["rhr_7d"] = df["resting_hr"].rolling(window=7, min_periods=2).mean()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Sleep hours bar if available
    if "sleep_duration_seconds" in df.columns:
        df["sleep_hours"] = df["sleep_duration_seconds"] / 3600.0
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["sleep_hours"],
                name="Sleep Duration (Hours)",
                marker=dict(color="#5e5b90"),
            ),
            secondary_y=True,
        )

    # Resting HR daily dots
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["resting_hr"],
            mode="markers",
            name="Daily Resting HR",
            marker=dict(color="#38bdf8", size=6, opacity=0.8),
        ),
        secondary_y=False,
    )

    # 7-day RHR trendline
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["rhr_7d"],
            mode="lines",
            name="7-Day RHR Baseline",
            line=dict(color="#00ffa3", width=2.5),
        ),
        secondary_y=False,
    )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title="Garmin Recovery Telemetry: Resting Heart Rate & Sleep Dynamics",
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_layout(layout)
    fig.update_yaxes(title_text="Resting Heart Rate (bpm)", secondary_y=False)
    if "sleep_duration_seconds" in df.columns:
        fig.update_yaxes(title_text="Sleep (Hours)", secondary_y=True)
    return fig


def plot_acwr_gauge(acwr_val: float) -> go.Figure:
    """Speedometer-style gauge for Acute:Chronic Workload Ratio."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=acwr_val,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Acute:Chronic Workload Ratio (ACWR)", "font": {"size": 14, "color": "#cbd5e1"}},
            delta={"reference": 1.0, "increasing": {"color": "#f59e0b"}},
            gauge={
                "axis": {"range": [0.0, 2.2], "tickwidth": 1, "tickcolor": "#64748b"},
                "bar": {"color": "#00d2ff", "thickness": 0.3},
                "bgcolor": "rgba(15, 22, 38, 0.8)",
                "borderwidth": 1,
                "bordercolor": "#1e293b",
                "steps": [
                    {"range": [0.0, 0.8], "color": "rgba(59, 130, 246, 0.25)"},
                    {"range": [0.8, 1.3], "color": "rgba(16, 185, 129, 0.35)"},
                    {"range": [1.3, 1.5], "color": "rgba(245, 158, 11, 0.35)"},
                    {"range": [1.5, 2.2], "color": "rgba(239, 68, 68, 0.35)"},
                ],
                "threshold": {
                    "line": {"color": "#ef4444", "width": 3},
                    "thickness": 0.75,
                    "value": 1.5,
                },
            },
        )
    )
    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(height=240, margin=dict(l=25, r=25, t=30, b=20))
    fig.update_layout(layout)
    return fig


def plot_risk_radar(risk_report: RiskReport) -> go.Figure:
    """Radar chart displaying the 5 transparent injury risk signals."""
    if not risk_report.signals:
        return go.Figure()

    categories = [s.name.split("(")[0].strip() for s in risk_report.signals]
    scores = [s.score for s in risk_report.signals]

    categories.append(categories[0])
    scores.append(scores[0])

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=scores,
            theta=categories,
            fill="toself",
            fillcolor="rgba(239, 68, 68, 0.2)" if risk_report.composite_score >= 50 else "rgba(16, 185, 129, 0.2)",
            line=dict(color=risk_report.status_color, width=2.5),
            name="Risk Signature",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color="#64748b"), gridcolor="#1e293b"),
            angularaxis=dict(tickfont=dict(size=10, color="#cbd5e1"), gridcolor="#1e293b"),
            bgcolor="rgba(15, 22, 38, 0.6)",
        ),
        paper_bgcolor="rgba(19, 27, 46, 0.0)",
        margin=dict(l=40, r=40, t=30, b=30),
        height=320,
        showlegend=False,
    )
    return fig


def plot_hr_zones_distribution(activities_df: pd.DataFrame, user_profile: UserProfile) -> go.Figure:
    """Polar / Bar breakdown of activity heart rates across 5 training zones."""
    if activities_df.empty or "avg_hr" not in activities_df.columns:
        return go.Figure()

    valid_hrs = activities_df["avg_hr"].dropna().values
    if len(valid_hrs) == 0:
        return go.Figure()

    mhr = user_profile.max_hr
    zones = ["Zone 1\n(<60%)", "Zone 2\n(60-70%)", "Zone 3\n(70-80%)", "Zone 4\n(80-90%)", "Zone 5\n(>90%)"]
    counts = [0, 0, 0, 0, 0]

    for hr in valid_hrs:
        pct = hr / mhr
        if pct < 0.60:
            counts[0] += 1
        elif pct < 0.70:
            counts[1] += 1
        elif pct < 0.80:
            counts[2] += 1
        elif pct < 0.90:
            counts[3] += 1
        else:
            counts[4] += 1

    total = sum(counts)
    pcts = [(c / total) * 100.0 for c in counts] if total > 0 else [0]*5

    colors = ["#3b82f6", "#10b981", "#06b6d4", "#f59e0b", "#ef4444"]

    fig = go.Figure(
        go.Bar(
            x=zones,
            y=pcts,
            marker=dict(color=colors, line=dict(color="#1e293b", width=1)),
            text=[f"{p:.1f}% ({c})" for p, c in zip(pcts, counts)],
            textposition="auto",
        )
    )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title="Training Intensity Distribution by HR Zone",
        yaxis_title="% of Workouts",
        height=320,
    )
    fig.update_layout(layout)
    return fig


def plot_walking_charts(walking_df: pd.DataFrame, unit: str = "metric") -> go.Figure:
    """Plots walking volume, pace, and step progression."""
    if walking_df.empty:
        return go.Figure()

    df = walking_df.copy()
    df["date"] = pd.to_datetime(df["start_time"]).dt.date
    dist_factor = 1.0 if unit == "metric" else 0.621371
    unit_name = "km" if unit == "metric" else "mi"
    df["dist_disp"] = df["distance_km"] * dist_factor

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Distance bars
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["dist_disp"],
            name=f"Walk Distance ({unit_name})",
            marker=dict(color="rgba(16, 185, 129, 0.75)", line=dict(color="#34d399", width=1.2)),
            hovertemplate="<b>%{x}</b><br>Distance: <b>%{y:.2f} " + unit_name + "</b><extra></extra>",
        ),
        secondary_y=False,
    )

    # Average Heart Rate / Pace Line
    if "avg_hr" in df.columns and df["avg_hr"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["avg_hr"],
                name="Avg Walking HR (bpm)",
                line=dict(color="#38bdf8", width=2.5),
                mode="lines+markers",
                marker=dict(size=6, color="#00d2ff"),
                hovertemplate="Avg HR: <b>%{y:.0f} bpm</b><extra></extra>",
            ),
            secondary_y=True,
        )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title=f"<b>Walking Sessions: Distance ({unit_name}) & Heart Rate Dynamics</b>",
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_layout(layout)
    fig.update_yaxes(title_text=f"Walk Distance ({unit_name})", secondary_y=False)
    fig.update_yaxes(title_text="Heart Rate (bpm)", secondary_y=True)
    return fig


def plot_cycling_charts(cycling_df: pd.DataFrame, unit: str = "metric") -> go.Figure:
    """Plots cycling saddle distance, speed (km/h or mph), and elevation climb."""
    if cycling_df.empty:
        return go.Figure()

    df = cycling_df.copy()
    df["date"] = pd.to_datetime(df["start_time"]).dt.date
    dist_factor = 1.0 if unit == "metric" else 0.621371
    unit_name = "km" if unit == "metric" else "mi"
    speed_unit = "km/h" if unit == "metric" else "mph"
    dist_col = df["distance_km"] if "distance_km" in df.columns else (df["distance_meters"] / 1000.0 if "distance_meters" in df.columns else pd.Series(0.0, index=df.index))
    df["dist_disp"] = dist_col * dist_factor

    if "speed_kmh" in df.columns:
        raw_speed = df["speed_kmh"]
    elif "duration_seconds" in df.columns:
        dur_hours = (df["duration_seconds"] / 3600.0).replace(0, float("nan"))
        raw_speed = (dist_col / dur_hours).fillna(0.0)
    else:
        raw_speed = pd.Series(0.0, index=df.index)

    df["speed_disp"] = raw_speed * (1.0 if unit == "metric" else 0.621371)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Saddle Distance Bars
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["dist_disp"],
            name=f"Ride Distance ({unit_name})",
            marker=dict(color="rgba(245, 158, 11, 0.75)", line=dict(color="#fbbf24", width=1.2)),
            hovertemplate="<b>%{x}</b><br>Distance: <b>%{y:.1f} " + unit_name + "</b><extra></extra>",
        ),
        secondary_y=False,
    )

    # Speed Line
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["speed_disp"],
            name=f"Avg Speed ({speed_unit})",
            line=dict(color="#00d2ff", width=2.5),
            mode="lines+markers",
            marker=dict(size=7, color="#38bdf8"),
            hovertemplate="Speed: <b>%{y:.1f} " + speed_unit + "</b><extra></extra>",
        ),
        secondary_y=True,
    )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title=f"<b>Cycling Telemetry: Saddle Distance ({unit_name}) & Speed ({speed_unit})</b>",
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_layout(layout)
    fig.update_yaxes(title_text=f"Distance ({unit_name})", secondary_y=False)
    fig.update_yaxes(title_text=f"Speed ({speed_unit})", secondary_y=True)
    return fig


def plot_hiking_charts(hiking_df: pd.DataFrame, unit: str = "metric") -> go.Figure:
    """Plots hiking trail elevation gain (D+), trail distance, and ascent velocity."""
    if hiking_df.empty:
        return go.Figure()

    df = hiking_df.copy()
    df["date"] = pd.to_datetime(df["start_time"]).dt.date
    dist_factor = 1.0 if unit == "metric" else 0.621371
    elev_factor = 1.0 if unit == "metric" else 3.28084
    dist_name = "km" if unit == "metric" else "mi"
    elev_name = "m" if unit == "metric" else "ft"

    df["dist_disp"] = df["distance_km"] * dist_factor
    df["elev_disp"] = (df["elevation_gain_m"] if "elevation_gain_m" in df.columns else 0.0) * elev_factor

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Elevation Gain (D+) Bars
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["elev_disp"],
            name=f"Ascent D+ ({elev_name})",
            marker=dict(color="rgba(168, 85, 247, 0.75)", line=dict(color="#c084fc", width=1.2)),
            hovertemplate="<b>%{x}</b><br>Elevation Gain: <b>+%{y:.0f} " + elev_name + "</b><extra></extra>",
        ),
        secondary_y=False,
    )

    # Trail Distance Line
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["dist_disp"],
            name=f"Trail Distance ({dist_name})",
            line=dict(color="#10b981", width=2.5),
            mode="lines+markers",
            marker=dict(size=7, color="#34d399"),
            hovertemplate="Trail Distance: <b>%{y:.1f} " + dist_name + "</b><extra></extra>",
        ),
        secondary_y=True,
    )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title=f"<b>Mountain & Trail Hiking: Vertical Gain (+{elev_name}) & Trail Distance ({dist_name})</b>",
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_layout(layout)
    fig.update_yaxes(title_text=f"Elevation Gain (+{elev_name})", secondary_y=False)
    fig.update_yaxes(title_text=f"Distance ({dist_name})", secondary_y=True)
    return fig


def plot_yoga_charts(yoga_df: pd.DataFrame) -> go.Figure:
    """Plots yoga mindfulness practice minutes and autonomic heart rate calming."""
    if yoga_df.empty:
        return go.Figure()

    df = yoga_df.copy()
    df["date"] = pd.to_datetime(df["start_time"]).dt.date
    df["duration_mins"] = df["duration_seconds"] / 60.0

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Practice Duration Bars
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["duration_mins"],
            name="Mat Time (Minutes)",
            marker=dict(color="rgba(6, 182, 212, 0.75)", line=dict(color="#22d3ee", width=1.2)),
            hovertemplate="<b>%{x}</b><br>Duration: <b>%{y:.0f} mins</b><extra></extra>",
        ),
        secondary_y=False,
    )

    # Calming Heart Rate Line
    if "avg_hr" in df.columns and df["avg_hr"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["avg_hr"],
                name="Parasympathetic HR (bpm)",
                line=dict(color="#a855f7", width=2.5),
                mode="lines+markers",
                marker=dict(size=7, color="#c084fc"),
                hovertemplate="Avg HR: <b>%{y:.0f} bpm</b><extra></extra>",
            ),
            secondary_y=True,
        )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title="<b>Yoga & Mindful Mobility: Session Duration & Autonomic Calming HR</b>",
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_layout(layout)
    fig.update_yaxes(title_text="Practice Duration (Minutes)", secondary_y=False)
    fig.update_yaxes(title_text="Heart Rate (bpm)", secondary_y=True)
    return fig


def plot_multisport_distribution(activities_df: pd.DataFrame) -> go.Figure:
    """Donut chart showing time/volume distribution across all physical sports."""
    if activities_df.empty or "sport_type" not in activities_df.columns:
        return go.Figure()

    df = activities_df.copy()
    df["duration_hours"] = df["duration_seconds"] / 3600.0

    sport_labels = {
        "run": "Running",
        "trail_run": "Trail Running",
        "treadmill_run": "Treadmill Run",
        "walking": "Walking",
        "cycling": "Cycling / Biking",
        "hiking": "Hiking & Trail",
        "yoga": "Yoga & Mobility",
        "swimming": "Swimming",
        "strength": "Strength & Gym",
        "other": "Other Workouts",
    }

    df["sport_name"] = df["sport_type"].map(lambda s: sport_labels.get(str(s).lower(), str(s).capitalize()))
    sport_grp = df.groupby("sport_name").agg(
        total_hours=("duration_hours", "sum"),
        count=("id", "count"),
    ).reset_index()

    color_map = {
        "Running": "#00d2ff",
        "Trail Running": "#06b6d4",
        "Treadmill Run": "#38bdf8",
        "Walking": "#10b981",
        "Cycling / Biking": "#f59e0b",
        "Hiking & Trail": "#a855f7",
        "Yoga & Mobility": "#ec4899",
        "Swimming": "#3b82f6",
        "Strength & Gym": "#ef4444",
        "Other Workouts": "#64748b",
    }

    colors = [color_map.get(name, "#94a3b8") for name in sport_grp["sport_name"]]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=sport_grp["sport_name"],
                values=sport_grp["total_hours"],
                hole=0.55,
                marker=dict(colors=colors, line=dict(color="#0f172a", width=2)),
                textinfo="label+percent",
                hoverinfo="label+value+percent",
                hovertemplate="<b>%{label}</b><br>Total Time: <b>%{value:.1f} hrs</b> (%{percent})<extra></extra>",
            )
        ]
    )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title="<b>Physical Training Distribution (Active Time Share)</b>",
        height=360,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    fig.update_layout(layout)
    return fig


def plot_weekly_multisport_stacked(activities_df: pd.DataFrame) -> go.Figure:
    """Stacked weekly training hours breakdown by physical activity."""
    if activities_df.empty or "start_time" not in activities_df.columns:
        return go.Figure()

    df = activities_df.copy()
    df["start_dt"] = pd.to_datetime(df["start_time"])
    df["week"] = df["start_dt"].dt.to_period("W-SUN").apply(lambda r: r.start_time)
    df["duration_hours"] = df["duration_seconds"] / 3600.0

    sport_labels = {
        "run": "Running",
        "trail_run": "Running",
        "treadmill_run": "Running",
        "walking": "Walking",
        "cycling": "Cycling",
        "hiking": "Hiking",
        "yoga": "Yoga",
        "swimming": "Swimming",
        "strength": "Strength",
        "other": "Other",
    }
    df["sport_category"] = df["sport_type"].map(lambda s: sport_labels.get(str(s).lower(), "Other"))

    pivot = df.pivot_table(
        index="week",
        columns="sport_category",
        values="duration_hours",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()

    color_map = {
        "Running": "#00d2ff",
        "Walking": "#10b981",
        "Cycling": "#f59e0b",
        "Hiking": "#a855f7",
        "Yoga": "#ec4899",
        "Swimming": "#3b82f6",
        "Strength": "#ef4444",
        "Other": "#64748b",
    }

    fig = go.Figure()
    for col in pivot.columns:
        if col == "week":
            continue
        fig.add_trace(
            go.Bar(
                x=pivot["week"],
                y=pivot[col],
                name=col,
                marker=dict(color=color_map.get(col, "#94a3b8")),
                hovertemplate=f"<b>%{{x|%b %d}}</b><br>{col}: <b>%{{y:.1f}} hrs</b><extra></extra>",
            )
        )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title="<b>Weekly Cross-Training Volume by Sport (Active Hours)</b>",
        barmode="stack",
        height=380,
        yaxis_title="Total Active Hours",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_layout(layout)
    return fig


def plot_sleep_stage_breakdown_chart(health_df: pd.DataFrame) -> go.Figure:
    """
    Stacked Bar Chart of Deep, REM, and Light Sleep Stages (in hours) over time using Palette colors.
    """
    if health_df.empty or "sleep_duration_seconds" not in health_df.columns:
        fig = go.Figure()
        fig.update_layout(**PLOT_LAYOUT_DARK, title="No Sleep Stage Data Available")
        return fig

    df = health_df[health_df["sleep_duration_seconds"].notna() & (health_df["sleep_duration_seconds"] > 0)].copy()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**PLOT_LAYOUT_DARK, title="No Sleep Stage Data Available")
        return fig

    df["date_str"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["deep_hrs"] = (df["deep_sleep_seconds"].fillna(0.0) / 3600.0).round(2)
    df["rem_hrs"] = (df["rem_sleep_seconds"].fillna(0.0) / 3600.0).round(2)
    df["light_hrs"] = (df["light_sleep_seconds"].fillna(0.0) / 3600.0).round(2)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["date_str"],
            y=df["deep_hrs"],
            name="Deep Sleep (Physical Repair)",
            marker=dict(
                color="#201C5F",
                line=dict(width=0.6, color="#1c1716"),
            ),
            hovertemplate="<b>%{x}</b><br>Deep Sleep: <b>%{y:.2f} hrs</b><extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=df["date_str"],
            y=df["light_hrs"],
            name="Light Sleep",
            marker=dict(
                color="#6E6EC3",
                line=dict(width=0.6, color="#1c1716"),
            ),
            hovertemplate="<b>%{x}</b><br>Light Sleep: <b>%{y:.2f} hrs</b><extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=df["date_str"],
            y=df["rem_hrs"],
            name="REM Sleep (Neural Restoration)",
            marker=dict(
                color="#ddddfc",
                line=dict(width=0.6, color="#1c1716"),
            ),
            hovertemplate="<b>%{x}</b><br>REM Sleep: <b>%{y:.2f} hrs</b><extra></extra>",
        )
    )

    # Target 8 Hour Reference Line
    fig.add_hline(
        y=8.0,
        line_dash="dash",
        line_color="#f0e2a3",
        line_width=1.5,
        annotation_text="Optimal Target (8.0h)",
        annotation_position="top left",
        annotation_font=dict(size=10, color="#f0e2a3"),
    )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title="<b>Daily Sleep Architecture & Stage Distribution (Hours)</b>",
        barmode="stack",
        height=420,
        margin=dict(l=28, r=15, t=65, b=35),
        yaxis_title="Sleep Duration (Hours)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="center",
            x=0.5,
            font=dict(size=9.5),
            traceorder="normal",
        ),
    )
    fig.update_layout(layout)
    return fig


def plot_sleep_score_and_rhr_chart(health_df: pd.DataFrame) -> go.Figure:
    """
    Dual-axis trend chart comparing Sleep Quality Score vs Resting Heart Rate (RHR).
    """
    if health_df.empty or "sleep_score" not in health_df.columns:
        fig = go.Figure()
        fig.update_layout(**PLOT_LAYOUT_DARK, title="No Sleep Telemetry Available")
        return fig

    df = health_df[health_df["sleep_score"].notna()].copy()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**PLOT_LAYOUT_DARK, title="No Sleep Telemetry Available")
        return fig

    df["date_str"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df["date_str"],
            y=df["sleep_score"],
            name="Sleep Score (0-100)",
            line=dict(color="#c1d37f", width=2.8, shape="spline", smoothing=0.8),
            fill="tozeroy",
            fillcolor="rgba(193, 211, 127, 0.08)",
            hovertemplate="<b>%{x}</b><br>Sleep Score: <b>%{y:.0f}/100</b><extra></extra>",
        ),
        secondary_y=False,
    )

    if "resting_hr" in df.columns and df["resting_hr"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df["date_str"],
                y=df["resting_hr"],
                name="Resting HR (BPM)",
                line=dict(color="#f9d4bb", width=2.2, shape="spline", smoothing=0.8),
                hovertemplate="<b>%{x}</b><br>Resting HR: <b>%{y:.0f} bpm</b><extra></extra>",
            ),
            secondary_y=True,
        )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title="<b>Sleep Quality Score vs Resting Heart Rate Telemetry</b>",
        height=400,
        margin=dict(l=28, r=15, t=65, b=35),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="center",
            x=0.5,
            font=dict(size=9.5),
        ),
    )
    fig.update_layout(layout)
    fig.update_yaxes(title_text="Sleep Score (0-100)", range=[50, 100], secondary_y=False)
    fig.update_yaxes(title_text="Resting HR (bpm)", secondary_y=True)
    return fig



