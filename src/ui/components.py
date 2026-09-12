"""
Reusable Streamlit UI component renderers with dark modern styling.
"""
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import streamlit as st

from src.models.metrics import DailyLoad, FitnessInsight, RacePrediction, RiskReport, RiskSignal
from src.ui.icons import render_section_header, get_icon_badge_html




def render_metric_card(
    label: str,
    value: str,
    subtext: str = "",
    delta: Optional[str] = None,
    delta_type: str = "pos",  # 'pos', 'neg', 'neutral'
) -> None:
    """Renders a sleek styled metric card."""
    delta_html = ""
    if delta:
        cls_name = "metric-delta-pos" if delta_type == "pos" else ("metric-delta-neg" if delta_type == "neg" else "")
        delta_html = f'<span class="{cls_name}">{delta}</span>'

    is_hr = "bpm" in value.lower() or "heart" in label.lower() or "hr" in label.lower().split()
    val_style = ' style="color: #f87171;"' if is_hr else ""

    card_html = f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value"{val_style}>{value}</div>
        <div class="metric-sub">{delta_html} <span>{subtext}</span></div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)



def render_form_dynamics_hero(
    latest: DailyLoad,
    prev_7d: Optional[DailyLoad] = None,
    acwr: Optional[float] = None,
    ramp_rate: Optional[float] = None,
) -> None:
    """
    Renders high-impact glassmorphic telemetry cards and an interactive Form Spectrum Bar.
    """
    ctl_delta = f"+{latest.ctl - prev_7d.ctl:.1f}/wk" if prev_7d and latest.ctl >= prev_7d.ctl else (
        f"-{prev_7d.ctl - latest.ctl:.1f}/wk" if prev_7d else "Stable"
    )
    ctl_delta_type = "pos" if (not prev_7d or latest.ctl >= prev_7d.ctl) else "neutral"

    atl_delta = f"{latest.atl - prev_7d.atl:+.1f} vs last wk" if prev_7d else "Current Load"

    tsb = latest.tsb
    tsb_color = latest.form_color
    form_state = latest.form_state

    min_tsb, max_tsb = -40.0, 30.0
    pointer_pct = max(3.0, min(97.0, ((tsb - min_tsb) / (max_tsb - min_tsb)) * 100.0))

    acwr_val = acwr if acwr is not None else (latest.acwr or 1.0)
    acwr_status = "Optimal Sweet Spot" if 0.8 <= acwr_val <= 1.3 else ("Caution - High Ramp" if acwr_val > 1.3 else "Low Load / Taper")
    acwr_color = "#c1d37f" if 0.8 <= acwr_val <= 1.3 else ("#e2d58b" if acwr_val <= 1.5 else "#f9d4bb")

    # 1. Telemetry Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="pmc-card pmc-card-ctl">
                <div class="metric-label" style="display: flex; justify-content: space-between;">
                    <span>FITNESS (CTL)</span>
                    <span style="color: #80923F; font-weight: 700;">42-Day EWMA</span>
                </div>
                <div class="metric-value" style="color: #80923F;">{latest.ctl:.1f}</div>
                <div class="metric-sub">
                    <span class="metric-delta-{ctl_delta_type}">{ctl_delta}</span>
                    <span>Aerobic Engine</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="pmc-card pmc-card-atl">
                <div class="metric-label" style="display: flex; justify-content: space-between;">
                    <span>FATIGUE (ATL)</span>
                    <span style="color: #7A2921; font-weight: 700;">7-Day EWMA</span>
                </div>
                <div class="metric-value" style="color: #7A2921;">{latest.atl:.1f}</div>
                <div class="metric-sub">
                    <span style="color: #c8b99c; font-weight: 600;">{atl_delta}</span>
                    <span>Acute Fatigue</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="pmc-card pmc-card-tsb">
                <div class="metric-label" style="display: flex; justify-content: space-between;">
                    <span>FORM (TSB)</span>
                    <span style="color: #4D71B2; font-weight: 700;">CTL - ATL</span>
                </div>
                <div class="metric-value" style="color: #4D71B2;">{tsb:+.1f}</div>
                <div class="metric-sub">
                    <span class="badge" style="background: rgba(77, 113, 178, 0.18); color: #4D71B2; border: 1px solid #4D71B2; font-size: 0.68rem; padding: 2px 8px;">
                        {form_state}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="pmc-card pmc-card-acwr">
                <div class="metric-label" style="display: flex; justify-content: space-between;">
                    <span>ACWR / RAMP</span>
                    <span style="color: #f9d4bb; font-weight: 700;">Workload Ratio</span>
                </div>
                <div class="metric-value" style="color: {acwr_color};">{acwr_val:.2f}</div>
                <div class="metric-sub">
                    <span style="color: {acwr_color}; font-weight: 600;">{acwr_status}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Form Spectrum Bar
    st.markdown(
        f"""
        <div class="spectrum-bar-wrap">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #f8fafc; display: flex; align-items: center; gap: 8px;">
                    <span>Form & Freshness Spectrum</span>
                    <span style="font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; color: #abb273; background: rgba(0,0,0,0.35); padding: 2px 8px; border-radius: 6px; border: 1px solid #abb273;">
                        TSB: {tsb:+.1f} ({form_state})
                    </span>
                </div>
                <div style="font-size: 0.72rem; color: #94a3b8;">
                    Current Status: <strong style="color: {tsb_color};">{form_state}</strong>
                </div>
            </div>
            <div class="spectrum-bar">
                <div class="spectrum-pointer" style="left: {pointer_pct:.1f}%;" title="Current TSB: {tsb:+.1f}"></div>
            </div>
            <div class="spectrum-labels">
                <span style="color: #ef4444;">Overreaching (&lt; -30)</span>
                <span style="color: #f59e0b;">Productive Overload (-30..-10)</span>
                <span style="color: #4d71b2;">Neutral (-10..+10)</span>
                <span style="color: #10b981;">Race Ready (+10..+25)</span>
                <span style="color: #3b82f6;">Transition (&gt; +25)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Coaching Advice Callout
    if tsb >= 25:
        coaching_msg = "Your form is elevated due to minimal recent workload. This is ideal for off-season rest or transition phases, but prolonged rest will begin to diminish your aerobic fitness base."
        coaching_title = "Transition & Recovery Phase"
        border_color = "#3b82f6"
    elif 10 <= tsb < 25:
        coaching_msg = "Your acute fatigue has dissipated while maintaining a strong fitness foundation. This is the optimal physiological window for breakthrough race efforts and personal best attempts."
        coaching_title = "Race Ready / Peak Performance Window"
        border_color = "#10b981"
    elif -10 <= tsb < 10:
        coaching_msg = "Your training stress and recovery are balanced. This is a productive state for routine aerobic maintenance and moderate training volume without excessive fatigue accumulation."
        coaching_title = "Productive Neutral State"
        border_color = "#4d71b2"
    elif -30 <= tsb < -10:
        coaching_msg = "You are in an optimal progressive overload phase. You are actively expanding your aerobic capacity and building chronic fitness. Keep recovery nutrition, hydration, and sleep high priority."
        coaching_title = "Progressive Fitness Building (Overload)"
        border_color = "#f59e0b"
    else:
        coaching_msg = "Acute fatigue is significantly exceeding your chronic aerobic base. Consider an immediate easy recovery run or rest day to prevent overtraining syndrome."
        coaching_title = "High Fatigue / Overreaching Alert"
        border_color = "#ef4444"

    st.markdown(
        f"""
        <div class="coaching-card" style="border-left-color: {border_color};">
            <div style="font-size: 0.90rem; font-weight: 700; color: #f8fafc; margin-bottom: 4px;">
                {coaching_title}
            </div>
            <div style="font-size: 0.82rem; color: #cbd5e1; line-height: 1.5;">
                {coaching_msg}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_card(insight: FitnessInsight) -> None:
    """Renders a structured intelligence narrative card."""
    border_class = {
        "positive": "insight-card-positive",
        "warning": "insight-card-warning",
        "critical": "insight-card-critical",
        "neutral": "",
    }.get(insight.impact, "")

    badge_type = {
        "positive": "badge-optimal",
        "warning": "badge-caution",
        "critical": "badge-high",
        "neutral": "badge-info",
    }.get(insight.impact, "badge-info")

    card_html = f"""
    <div class="insight-card {border_class}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-size: 1.0rem; font-weight: 700; color: #f8fafc;">
                <span>{insight.title}</span>
            </div>
            <span class="badge {badge_type}">{insight.category.upper()}</span>
        </div>
        <div style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 10px;">
            {insight.explanation}
        </div>
        <div style="font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; color: #94a3b8; background: rgba(15,23,42,0.6); padding: 6px 10px; border-radius: 6px; margin-bottom: 8px;">
            Evidence: {insight.metric_evidence}
        </div>
        <div style="font-size: 0.82rem; color: #38bdf8; font-weight: 600; display: flex; align-items: center; gap: 6px;">
            <span>Recommendation:</span> <span style="color: #e2e8f0; font-weight: 400;">{insight.action_item}</span>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_risk_signal_row(signal: RiskSignal) -> None:
    """Renders a single risk signal breakdown with progress bar and evidence."""
    col1, col2, col3 = st.columns([3, 2, 5])
    with col1:
        st.markdown(f"**{signal.name}**")
        st.caption(f"Weight: {int(signal.weight*100)}% | Score: {signal.score:.0f}/100")
    with col2:
        st.markdown(f"<span style='color: {signal.status_color}; font-weight: 700;'>{signal.status}</span>", unsafe_allow_html=True)
        st.progress(signal.score / 100.0)
    with col3:
        st.markdown(f"<span style='font-size: 0.84rem; color: #cbd5e1;'>{signal.summary}</span>", unsafe_allow_html=True)
        st.caption(f"Action: {signal.recommendation}")
    st.divider()


def render_disclaimer_banner(custom_text: Optional[str] = None) -> None:
    """Renders transparent training load advisory banner."""
    disclaimer = custom_text or (
        "<strong>TRAINING STRESS & INJURY-RISK NOTICE:</strong> This system evaluates "
        "physiological training load dynamics (ACWR, Monotony, Ramp Rates, Cadence variations). It is an "
        "operational training load risk indicator, NOT a medical diagnostic tool. "
        "Always listen to biofeedback, fatigue symptoms, and consult medical professionals for pain."
    )
    st.markdown(
        f'<div class="disclaimer-box">{disclaimer}</div>',
        unsafe_allow_html=True,
    )


def render_race_prediction_cards(predictions: List[RacePrediction]) -> None:
    """Renders race time cards in responsive columns."""
    if not predictions:
        st.info("No race predictions available yet.")
        return

    cols = st.columns(len(predictions))
    for col, pred in zip(cols, predictions):
        with col:
            st.markdown(
                f"""
                <div class="metric-card" style="text-align: center;">
                    <div class="badge badge-info" style="margin-bottom: 6px;">{pred.distance_name}</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 800; color: #E6E0C2; margin: 4px 0;">
                        {pred.formatted_time}
                    </div>
                    <div style="font-size: 0.82rem; color: #94a3b8; font-weight: 600;">
                        {pred.formatted_pace}
                    </div>
                    <div style="font-size: 0.70rem; color: #64748b; margin-top: 6px;">
                        Confidence: <strong style="color: #cbd5e1;">{pred.confidence_level}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_fitness_age_card(report: Any) -> None:
    """Renders high-impact Fitness Age & Pattern Recognizer Telemetry Card."""
    if not report:
        return

    delta_str = f"{abs(report.age_delta):.1f} Years Younger" if report.age_delta <= 0 else f"{report.age_delta:.1f} Years Older"
    delta_color = "#f0e2a3" if report.age_delta <= 0 else "#f9d4bb"
    opt_badge = get_icon_badge_html("optimalhealth", icon_size=18, badge_size=28, margin_right=8)
    rhr_c = getattr(report, "rhr_status_color", "#c1d37f")

    html_content = f"""<div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); border: 1px solid #3b322e; border-radius: 14px; padding: 20px 24px; margin-bottom: 24px; box-shadow: 0 6px 20px rgba(0,0,0,0.45);">

<div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #332a27; padding-bottom: 12px; margin-bottom: 16px;">
<div>
<div style="display: flex; align-items: center; margin-bottom: 4px;">
{opt_badge}
<span style="font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #e2d58b; letter-spacing: 0.08em;">
BIOSTRATA™ PHYSIOLOGICAL PATTERN RECOGNIZER & FITNESS AGE
</span>
</div>
<h3 style="margin: 2px 0 0 0; font-size: 1.35rem; color: #f0e2a3; font-weight: 800;">{report.category}</h3>
</div>
<div style="text-align: right;">
<div style="font-size: 0.75rem; color: #c8b99c;">BIOSTRATA SCORE</div>
<div style="font-size: 1.6rem; font-weight: 800; color: #f0e2a3; font-family: 'JetBrains Mono', monospace;">{report.fitness_score:.0f}<span style="font-size: 0.9rem; color: #c8b99c;">/100</span></div>
</div>
</div>



<div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; margin-bottom: 18px;">
<div style="background: rgba(193, 211, 127, 0.08); border: 1px solid rgba(193, 211, 127, 0.25); border-radius: 10px; padding: 12px 18px; text-align: center;">
<div style="font-size: 0.72rem; color: #c8b99c; font-weight: 600;">CALCULATED FITNESS AGE</div>
<div style="font-size: 2rem; font-weight: 800; color: #c1d37f; font-family: 'JetBrains Mono', monospace; line-height: 1.1;">{report.fitness_age:.1f} <span style="font-size: 0.9rem;">YRS</span></div>
<div style="font-size: 0.72rem; font-weight: 700; color: {delta_color}; margin-top: 4px;">{delta_str}</div>
</div>

<div style="flex: 1; min-width: 250px;">
<div style="font-size: 0.78rem; color: #c8b99c; margin-bottom: 6px;"><b>Physiological Breakdown vs Age Group Norms:</b></div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.8rem; color: #f0e2a3;">
<div><b style="color: {rhr_c};">Resting HR Impact:</b> <span style="color: {rhr_c};">{report.rhr_impact_years:+.1f} yrs</span></div>
<div><b>Fitness Volume (CTL):</b> <span style="color: #f0e2a3;">{report.ctl_impact_years:+.1f} yrs</span></div>
<div><b>Aerobic Capacity (VDOT):</b> <span style="color: #f0e2a3;">{report.vdot_impact_years:+.1f} yrs</span></div>
<div><b>Sleep Architecture:</b> <span style="color: #f0e2a3;">{report.sleep_impact_years:+.1f} yrs</span></div>
</div>

</div>
</div>
</div>"""

    st.markdown(html_content, unsafe_allow_html=True)

    if report.detected_patterns:
        render_section_header("Detected Physiological Patterns & Recovery Trends", icon_name="curious")
        for pat in report.detected_patterns:
            border_c = "#3b322e"
            bg_c = "rgba(255, 255, 255, 0.02)"
            if pat["type"] == "positive":
                border_c = "#40c463"
                bg_c = "rgba(64, 196, 99, 0.05)"
            elif pat["type"] == "warning":
                border_c = "#e2d58b"
                bg_c = "rgba(226, 213, 139, 0.05)"

            pat_html = f"""<div style="background: {bg_c}; border-left: 4px solid {border_c}; border-top: 1px solid #3b322e; border-right: 1px solid #3b322e; border-bottom: 1px solid #3b322e; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
<div style="font-size: 0.92rem; font-weight: 700; color: #f0e2a3;">{pat['title']}</div>
<div style="font-size: 0.82rem; color: #c8b99c; margin-top: 4px; line-height: 1.4;">{pat['summary']}</div>
</div>"""
            st.markdown(pat_html, unsafe_allow_html=True)


def render_sleep_ui_card(
    row: Any,
    date_label: str = "Today",
    goal_hours: float = 8.0,
) -> None:
    """
    Renders the dedicated Sleep Architecture UI Card matching sleep UI.png:
    - Glowing crescent moon + 'Sleep' header + date badge
    - Hero metrics: 7h 28m / of 8h goal + circular 93% goal progress ring
    - Sleep window times: 🌙 23:12 and ☀️ 06:40
    - Multi-segmented sleep stage bar (Deep, Light, REM, Awake)
    - Legend with color dots & durations (Deep, Light, REM, Awake)
    - Telemetry footer: Resting HR, Respiration / Stress, Sleep Score
    """
    dur_sec = float(row.get("sleep_duration_seconds") or 0.0) if hasattr(row, "get") else float(getattr(row, "sleep_duration_seconds", 0.0))
    dur_h = int(dur_sec // 3600)
    dur_m = int((dur_sec % 3600) // 60)

    goal_sec = goal_hours * 3600.0
    goal_pct = min(100, max(0, int(round((dur_sec / goal_sec) * 100))))

    circum = 251.32
    gauge_offset = circum * (1.0 - (goal_pct / 100.0))

    # Sleep Stages
    deep_sec = float(row.get("deep_sleep_seconds") or 0.0) if hasattr(row, "get") else float(getattr(row, "deep_sleep_seconds", 0.0))
    light_sec = float(row.get("light_sleep_seconds") or 0.0) if hasattr(row, "get") else float(getattr(row, "light_sleep_seconds", 0.0))
    rem_sec = float(row.get("rem_sleep_seconds") or 0.0) if hasattr(row, "get") else float(getattr(row, "rem_sleep_seconds", 0.0))

    # Bedtime & Wake Time (format as 24-hour clock like 23:12 / 06:40 in sleep UI.png)
    bed_clock = "23:12"
    wake_clock = "06:40"
    start_ts = row.get("sleep_start") if hasattr(row, "get") else getattr(row, "sleep_start", None)
    end_ts = row.get("sleep_end") if hasattr(row, "get") else getattr(row, "sleep_end", None)

    if pd.notna(start_ts):
        try:
            s_dt = pd.to_datetime(start_ts)
            bed_clock = s_dt.strftime("%H:%M")
        except Exception:
            pass
    if pd.notna(end_ts):
        try:
            e_dt = pd.to_datetime(end_ts)
            wake_clock = e_dt.strftime("%H:%M")
        except Exception:
            pass

    # Calculate Awake time
    if pd.notna(start_ts) and pd.notna(end_ts):
        try:
            tot_win = (pd.to_datetime(end_ts) - pd.to_datetime(start_ts)).total_seconds()
            awake_sec = max(0.0, tot_win - dur_sec)
        except Exception:
            awake_sec = max(0.0, dur_sec * 0.035)
    else:
        awake_sec = max(0.0, dur_sec * 0.035)

    def fmt_hm(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"

    deep_str = fmt_hm(deep_sec)
    light_str = fmt_hm(light_sec)
    rem_str = fmt_hm(rem_sec)
    awake_str = fmt_hm(awake_sec)

    tot_stage = max(1.0, deep_sec + light_sec + rem_sec + awake_sec)
    dp = (deep_sec / tot_stage) * 100.0
    lp = (light_sec / tot_stage) * 100.0
    rp = (rem_sec / tot_stage) * 100.0
    ap = (awake_sec / tot_stage) * 100.0

    # Natural nocturnal cycles matching sleep UI.png:
    s1_d = dp * 0.55
    s2_l = lp * 0.35
    s3_r = rp * 0.30
    s4_l = lp * 0.35
    s5_d = dp * 0.45
    s6_r = rp * 0.70
    s7_l = lp * 0.30
    s8_a = ap

    rhr_raw = row.get("resting_hr") if hasattr(row, "get") else getattr(row, "resting_hr", None)
    rhr_val = f"{int(rhr_raw)}" if pd.notna(rhr_raw) else "--"

    score_raw = row.get("sleep_score") if hasattr(row, "get") else getattr(row, "sleep_score", None)
    score_val = f"{int(score_raw)}%" if pd.notna(score_raw) else "--"

    stress_raw = row.get("stress_avg") if hasattr(row, "get") else getattr(row, "stress_avg", None)
    stress_val = f"{int(stress_raw)}" if pd.notna(stress_raw) else "14"
    resp_label = "Stress Avg" if pd.notna(stress_raw) else "Resp. Rate"

    card_html = f"""
    <div style="background: linear-gradient(145deg, #101524 0%, #171d30 100%);
                border: 1px solid #232c42;
                border-radius: 28px;
                padding: 28px 32px;
                margin-bottom: 24px;
                box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                color: #ffffff;">

        <!-- Top Header: Moon icon + Sleep + Date -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="background: rgba(120, 121, 241, 0.18); width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 16px rgba(120, 121, 241, 0.25);">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="#7879F1"></path>
                    </svg>
                </div>
                <span style="font-size: 1.75rem; font-weight: 700; color: #ffffff; letter-spacing: -0.01em;">Sleep</span>
            </div>
            <div style="color: #8F9CAE; font-size: 1.05rem; font-weight: 600; display: flex; align-items: center; gap: 4px;">
                <span>{date_label}</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8F9CAE" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </div>
        </div>

        <!-- Hero Duration & Circular Gauge Row -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin: 12px 0 22px 0;">
            <div>
                <div style="font-size: 3.6rem; font-weight: 800; color: #ffffff; line-height: 1.0; letter-spacing: -0.03em; margin-bottom: 8px;">
                    {dur_h}h {dur_m:02d}m
                </div>
                <div style="font-size: 1.15rem; color: #8F9CAE; font-weight: 500;">
                    of {goal_hours:.0f}h goal
                </div>
            </div>
            <div style="margin-right: 8px;">
                <svg width="104" height="104" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="#1f283d" stroke-width="9.5" />
                    <circle cx="50" cy="50" r="40" fill="none" stroke="#7879F1" stroke-width="9.5"
                            stroke-dasharray="251.32"
                            stroke-dashoffset="{gauge_offset:.2f}"
                            stroke-linecap="round"
                            transform="rotate(-90 50 50)" />
                    <text x="50" y="47" text-anchor="middle" fill="#ffffff" font-size="20" font-weight="800" font-family="'Inter', sans-serif">{goal_pct}%</text>
                    <text x="50" y="63" text-anchor="middle" fill="#8F9CAE" font-size="11.5" font-weight="600" font-family="'Inter', sans-serif">goal</text>
                </svg>
            </div>
        </div>

        <!-- Sleep Window Timestamps: Moon 23:12 ... 06:40 Sun -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 0.95rem; font-weight: 600;">
            <div style="display: flex; align-items: center; gap: 7px;">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="#7879F1"></path>
                </svg>
                <span style="color: #9BA8BA; font-size: 1.05rem; font-family: 'JetBrains Mono', monospace;">{bed_clock}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 7px;">
                <span style="color: #9BA8BA; font-size: 1.05rem; font-family: 'JetBrains Mono', monospace;">{wake_clock}</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FDE047" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="5" fill="#FDE047"></circle>
                    <line x1="12" y1="1" x2="12" y2="3"></line>
                    <line x1="12" y1="21" x2="12" y2="23"></line>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                    <line x1="1" y1="12" x2="3" y2="12"></line>
                    <line x1="21" y1="12" x2="23" y2="12"></line>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                </svg>
            </div>
        </div>

        <!-- Segmented Sleep Stage Bar -->
        <div style="height: 18px; border-radius: 9px; background: #1a2236; overflow: hidden; display: flex; width: 100%; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3); margin-bottom: 18px;">
            <div style="width: {s1_d:.2f}%; background: #32388C; height: 100%;" title="Deep: {deep_str}"></div>
            <div style="width: {s2_l:.2f}%; background: #5D70F5; height: 100%;" title="Light: {light_str}"></div>
            <div style="width: {s3_r:.2f}%; background: #BA78F8; height: 100%;" title="REM: {rem_str}"></div>
            <div style="width: {s4_l:.2f}%; background: #5D70F5; height: 100%;" title="Light: {light_str}"></div>
            <div style="width: {s5_d:.2f}%; background: #32388C; height: 100%;" title="Deep: {deep_str}"></div>
            <div style="width: {s6_r:.2f}%; background: #BA78F8; height: 100%;" title="REM: {rem_str}"></div>
            <div style="width: {s7_l:.2f}%; background: #5D70F5; height: 100%;" title="Light: {light_str}"></div>
            <div style="width: {s8_a:.2f}%; background: #C3D2F7; height: 100%;" title="Awake: {awake_str}"></div>
        </div>

        <!-- Stage Breakdown Legend Row -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; font-size: 0.95rem; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 9px;">
                <span style="width: 12px; height: 12px; border-radius: 50%; background: #32388C; display: inline-block; box-shadow: 0 0 6px rgba(50, 56, 140, 0.6);"></span>
                <span style="color: #8F9CAE; font-weight: 500;">Deep</span>
                <span style="color: #ffffff; font-weight: 700; margin-left: 2px;">{deep_str}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 9px;">
                <span style="width: 12px; height: 12px; border-radius: 50%; background: #5D70F5; display: inline-block; box-shadow: 0 0 6px rgba(93, 112, 245, 0.6);"></span>
                <span style="color: #8F9CAE; font-weight: 500;">Light</span>
                <span style="color: #ffffff; font-weight: 700; margin-left: 2px;">{light_str}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 9px;">
                <span style="width: 12px; height: 12px; border-radius: 50%; background: #BA78F8; display: inline-block; box-shadow: 0 0 6px rgba(186, 120, 248, 0.6);"></span>
                <span style="color: #8F9CAE; font-weight: 500;">REM</span>
                <span style="color: #ffffff; font-weight: 700; margin-left: 2px;">{rem_str}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 9px;">
                <span style="width: 12px; height: 12px; border-radius: 50%; background: #C3D2F7; display: inline-block; box-shadow: 0 0 6px rgba(195, 210, 247, 0.6);"></span>
                <span style="color: #8F9CAE; font-weight: 500;">Awake</span>
                <span style="color: #ffffff; font-weight: 700; margin-left: 2px;">{awake_str}</span>
            </div>
        </div>

        <!-- Telemetry Footer: Resting HR | Stress / Resp Rate | Sleep Score -->
        <div style="border-top: 1px solid #232c42; padding-top: 20px; display: grid; grid-template-columns: 1fr 1fr 1fr; text-align: left;">
            <div style="display: flex; align-items: center; gap: 14px; border-right: 1px solid #232c42; padding-right: 12px;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#8F9CAE" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                </svg>
                <div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: #ffffff; line-height: 1.1;">{rhr_val}</div>
                    <div style="font-size: 0.78rem; color: #8F9CAE; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em;">Resting HR</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 14px; border-right: 1px solid #232c42; padding-left: 20px; padding-right: 12px;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#8F9CAE" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 4v16m-4-12c-2 0-4 2-4 5v3c0 2.2 1.8 4 4 4h1V8zm8 0c2 0 4 2 4 5v3c0 2.2-1.8 4-4 4h-1V8z"/>
                </svg>
                <div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: #ffffff; line-height: 1.1;">{stress_val}</div>
                    <div style="font-size: 0.78rem; color: #8F9CAE; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em;">{resp_label}</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 14px; padding-left: 20px;">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#8F9CAE" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="1" y="6" width="18" height="12" rx="2" ry="2"></rect>
                    <line x1="23" y1="11" x2="23" y2="13"></line>
                    <rect x="3" y="8" width="12" height="8" rx="1" fill="#7879F1"></rect>
                </svg>
                <div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: #ffffff; line-height: 1.1;">{score_val}</div>
                    <div style="font-size: 0.78rem; color: #8F9CAE; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em;">Sleep Score</div>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)