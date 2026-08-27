"""
Reusable Streamlit UI component renderers with dark modern styling.
"""
from typing import List, Optional
import streamlit as st

from src.models.metrics import FitnessInsight, RacePrediction, RiskReport, RiskSignal


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


def render_insight_card(insight: FitnessInsight) -> None:
    """Renders a structured 'What is happening to my fitness?' intelligence card."""
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
            <div style="font-size: 1.05rem; font-weight: 700; color: #f8fafc; display: flex; align-items: center; gap: 8px;">
                <span>{insight.icon}</span> <span>{insight.title}</span>
            </div>
            <span class="badge {badge_type}">{insight.category.upper()}</span>
        </div>
        <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 10px;">
            {insight.explanation}
        </div>
        <div style="font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; color: #94a3b8; background: rgba(15,23,42,0.6); padding: 6px 10px; border-radius: 6px; margin-bottom: 8px;">
            🔍 Evidence: {insight.metric_evidence}
        </div>
        <div style="font-size: 0.82rem; color: #38bdf8; font-weight: 600; display: flex; align-items: center; gap: 6px;">
            <span>💡 Recommendation:</span> <span style="color: #e2e8f0; font-weight: 400;">{insight.action_item}</span>
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
        st.markdown(f"<span style='color: {signal.status_color}; font-weight: 700;'>● {signal.status}</span>", unsafe_allow_html=True)
        st.progress(signal.score / 100.0)
    with col3:
        st.markdown(f"<span style='font-size: 0.84rem; color: #cbd5e1;'>{signal.summary}</span>", unsafe_allow_html=True)
        st.caption(f"Action: {signal.recommendation}")
    st.divider()


def render_disclaimer_banner(custom_text: Optional[str] = None) -> None:
    """Renders transparent medical disclaimer banner."""
    disclaimer = custom_text or (
        "⚠️ <strong>TRAINING-STRESS & INJURY-RISK INDICATOR NOTICE:</strong> This algorithm evaluates "
        "physiological training load dynamics (ACWR, Monotony, Ramp Rates, Cadence variations). It is an "
        "operational training load risk indicator, NOT a medical diagnostic tool or clinical prediction of injury. "
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
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 800; color: #00d2ff; margin: 4px 0;">
                        {pred.formatted_time}
                    </div>
                    <div style="font-size: 0.85rem; color: #94a3b8; font-weight: 600;">
                        {pred.formatted_pace}
                    </div>
                    <div style="font-size: 0.72rem; color: #64748b; margin-top: 6px;">
                        Confidence: <strong style="color: #cbd5e1;">{pred.confidence_level}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
