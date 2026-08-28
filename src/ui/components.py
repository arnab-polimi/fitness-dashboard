"""
Reusable Streamlit UI component renderers with dark modern styling.
"""
from typing import List, Optional
import streamlit as st

from src.models.metrics import DailyLoad, FitnessInsight, RacePrediction, RiskReport, RiskSignal


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

    card_html = f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
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

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #1c1716 0%, #26201e 100%); 
                    border: 1px solid #3b322e; border-radius: 14px; padding: 20px 24px; margin-bottom: 24px; 
                    box-shadow: 0 6px 20px rgba(0,0,0,0.45);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #332a27; padding-bottom: 12px; margin-bottom: 16px;">
                <div>
                    <span style="font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #e2d58b; letter-spacing: 0.08em;">
                        BIOSTRATA™ PHYSIOLOGICAL PATTERN RECOGNIZER & FITNESS AGE
                    </span>
                    <h3 style="margin: 4px 0 0 0; font-size: 1.35rem; color: #f0e2a3; font-weight: 800;">{report.category}</h3>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.75rem; color: #c8b99c;">BIOSTRATA SCORE</div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: #f0e2a3; font-family: 'JetBrains Mono', monospace;">{report.fitness_score:.0f}<span style="font-size: 0.9rem; color: #c8b99c;">/100</span></div>
                </div>
            </div>
            
            <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; margin-bottom: 18px;">
                <div style="background: rgba(240, 226, 163, 0.08); border: 1px solid rgba(240, 226, 163, 0.25); border-radius: 10px; padding: 12px 18px; text-align: center;">
                    <div style="font-size: 0.72rem; color: #c8b99c; font-weight: 600;">CALCULATED FITNESS AGE</div>
                    <div style="font-size: 2rem; font-weight: 800; color: #f0e2a3; font-family: 'JetBrains Mono', monospace; line-height: 1.1;">{report.fitness_age:.1f} <span style="font-size: 0.9rem;">YRS</span></div>
                    <div style="font-size: 0.72rem; font-weight: 700; color: {delta_color}; margin-top: 4px;">{delta_str}</div>
                </div>

                <div style="flex: 1; min-width: 250px;">
                    <div style="font-size: 0.78rem; color: #c8b99c; margin-bottom: 6px;"><b>Physiological Breakdown vs Age Group Norms:</b></div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.8rem; color: #f0e2a3;">
                        <div>💓 <b>Resting HR Impact:</b> <span style="color: #f0e2a3;">{report.rhr_impact_years:+.1f} yrs</span></div>
                        <div>📈 <b>Fitness Volume (CTL):</b> <span style="color: #f0e2a3;">{report.ctl_impact_years:+.1f} yrs</span></div>
                        <div>🏃 <b>Aerobic Capacity (VDOT):</b> <span style="color: #f0e2a3;">{report.vdot_impact_years:+.1f} yrs</span></div>
                        <div>💤 <b>Sleep Architecture:</b> <span style="color: #f0e2a3;">{report.sleep_impact_years:+.1f} yrs</span></div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if report.detected_patterns:
        st.markdown("#### 🔍 Detected Physiological Patterns & Recovery Trends")
        for pat in report.detected_patterns:
            border_c = "#3b322e"
            bg_c = "rgba(255, 255, 255, 0.02)"
            if pat["type"] == "positive":
                border_c = "#40c463"
                bg_c = "rgba(64, 196, 99, 0.05)"
            elif pat["type"] == "warning":
                border_c = "#e2d58b"
                bg_c = "rgba(226, 213, 139, 0.05)"

            st.markdown(
                f"""
                <div style="background: {bg_c}; border-left: 4px solid {border_c}; border-top: 1px solid #3b322e; border-right: 1px solid #3b322e; border-bottom: 1px solid #3b322e;
                            border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
                    <div style="font-size: 0.92rem; font-weight: 700; color: #f0e2a3;">{pat['title']}</div>
                    <div style="font-size: 0.82rem; color: #c8b99c; margin-top: 4px; line-height: 1.4;">{pat['summary']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )