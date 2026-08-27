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
    paper_bgcolor="rgba(19, 27, 46, 0.0)",
    plot_bgcolor="rgba(15, 22, 38, 0.6)",
    font=dict(family="Inter, sans-serif", color="#94a3b8", size=11),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(
        gridcolor="#1e293b",
        zerolinecolor="#334155",
        showgrid=True,
        tickfont=dict(color="#64748b"),
    ),
    yaxis=dict(
        gridcolor="#1e293b",
        zerolinecolor="#334155",
        showgrid=True,
        tickfont=dict(color="#64748b"),
    ),
    legend=dict(
        bgcolor="rgba(19, 27, 46, 0.8)",
        bordercolor="#1e293b",
        borderwidth=1,
        font=dict(color="#cbd5e1", size=10),
    ),
    hoverlabel=dict(
        bgcolor="#0f172a",
        bordercolor="#38bdf8",
        font=dict(family="JetBrains Mono, monospace", color="#f8fafc", size=11),
    ),
)


def plot_pmc_chart(daily_df: pd.DataFrame) -> go.Figure:
    """
    Performance Management Chart (PMC):
    - CTL (Fitness) 42d EWMA
    - ATL (Fatigue) 7d EWMA
    - TSB (Form) CTL - ATL
    - Daily TSS bars
    """
    if daily_df.empty:
        fig = go.Figure()
        fig.update_layout(**PLOT_LAYOUT_DARK, title="No Training Data Available")
        return fig

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.75, 0.25],
        subplot_titles=("Fitness (CTL), Fatigue (ATL) & Form (TSB)", "Daily Training Stress Score (TSS)"),
    )

    # 1. Daily TSS Bar
    fig.add_trace(
        go.Bar(
            x=daily_df["date"],
            y=daily_df["total_tss"],
            name="Daily TSS",
            marker=dict(color="rgba(148, 163, 184, 0.35)", line=dict(color="rgba(148, 163, 184, 0.6)", width=1)),
            hoverinfo="x+y",
        ),
        row=2,
        col=1,
    )

    # TSB Shaded Area (Form)
    tsb_colors = ["#10b981" if v >= 0 else "#ef4444" for v in daily_df["tsb"]]
    fig.add_trace(
        go.Bar(
            x=daily_df["date"],
            y=daily_df["tsb"],
            name="TSB (Form)",
            marker=dict(color=tsb_colors, opacity=0.4),
            hoverinfo="x+y",
        ),
        row=1,
        col=1,
    )

    # CTL Line (Fitness)
    fig.add_trace(
        go.Scatter(
            x=daily_df["date"],
            y=daily_df["ctl"],
            name="CTL (Fitness 42d)",
            line=dict(color="#00d2ff", width=2.5),
            mode="lines",
        ),
        row=1,
        col=1,
    )

    # ATL Line (Fatigue)
    fig.add_trace(
        go.Scatter(
            x=daily_df["date"],
            y=daily_df["atl"],
            name="ATL (Fatigue 7d)",
            line=dict(color="#a855f7", width=2.0, dash="dot"),
            mode="lines",
        ),
        row=1,
        col=1,
    )

    # Reference Zones for TSB
    fig.add_hrect(
        y0=10, y1=25,
        fillcolor="rgba(16, 185, 129, 0.08)", line_width=0,
        annotation_text="Race Ready (+10 to +25)", annotation_position="top right",
        annotation_font=dict(size=9, color="#10b981"),
        row=1, col=1,
    )
    fig.add_hrect(
        y0=-10, y1=10,
        fillcolor="rgba(6, 182, 212, 0.06)", line_width=0,
        annotation_text="Productive (-10 to +10)", annotation_position="top right",
        annotation_font=dict(size=9, color="#06b6d4"),
        row=1, col=1,
    )
    fig.add_hrect(
        y0=-30, y1=-10,
        fillcolor="rgba(245, 158, 11, 0.08)", line_width=0,
        annotation_text="Optimal Overload (-30 to -10)", annotation_position="bottom right",
        annotation_font=dict(size=9, color="#f59e0b"),
        row=1, col=1,
    )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        height=520,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_layout(layout)
    return fig


def plot_weekly_mileage_and_load(daily_df: pd.DataFrame, unit: str = "metric") -> go.Figure:
    """Aggregates daily data by week to show weekly distance and TSS volume."""
    if daily_df.empty:
        return go.Figure()

    df = daily_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W-SUN").apply(lambda r: r.start_time)

    weekly = df.groupby("week").agg(
        total_dist=("distance_meters", "sum"),
        total_tss=("total_tss", "sum"),
        run_count=("activity_count", "sum"),
    ).reset_index()

    weekly["dist_display"] = weekly["total_dist"] / (1609.344 if unit == "imperial" else 1000.0)
    unit_label = "Miles" if unit == "imperial" else "Kilometers"

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=weekly["week"],
            y=weekly["dist_display"],
            name=f"Weekly Distance ({unit_label})",
            marker=dict(color="#3b82f6", opacity=0.85, line=dict(color="#60a5fa", width=1)),
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["total_tss"],
            name="Weekly TSS",
            line=dict(color="#f59e0b", width=2.5),
            mode="lines+markers",
        ),
        secondary_y=True,
    )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title=f"Weekly Mileage ({unit_label}) & Training Stress Volume",
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_layout(layout)
    fig.update_yaxes(title_text=f"Distance ({unit_label})", secondary_y=False)
    fig.update_yaxes(title_text="Total TSS", secondary_y=True)
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
                colorbar=dict(title="Timeline", tickfont=dict(color="#94a3b8")),
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
                name="Cardiac Drift / Pace Curve",
                line=dict(color="#f43f5e", width=2, dash="dash"),
            )
        )

    layout = dict(PLOT_LAYOUT_DARK)
    layout.update(
        title="Heart Rate vs. Pace (Cardiovascular Efficiency Profile)",
        xaxis_title="Pace (min/km) [Faster ➔]",
        yaxis_title="Average Heart Rate (bpm)",
        xaxis=dict(autorange="reversed"),
        height=400,
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
                marker=dict(color="rgba(168, 85, 247, 0.4)", line=dict(color="#c084fc", width=1)),
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
