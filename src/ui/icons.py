"""
Centralized icon management system for ApexFitness.
Loads local PNG icons directly from the /icons directory, encodes them to base64 data URIs,
applies inversion filters for high-contrast visibility on dark backgrounds, and renders clean HTML elements.
"""
import base64
import os
from typing import Dict, List, Optional
import streamlit as st

ICONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "icons"))

# Semantic mapping from sport/feature names to filename in icons/
ICON_MAPPINGS: Dict[str, str] = {
    # Sports
    "running": "running.png",
    "run": "running.png",
    "trail_run": "running.png",
    "treadmill_run": "running.png",
    "walking": "walking.png",
    "walk": "walking.png",
    "cycling": "bike.png",
    "bike": "bike.png",
    "ride": "bike.png",
    "swimming": "swimming.png",
    "swim": "swimming.png",
    "yoga": "yoga.png",
    "mobility": "yoga.png",
    "stretch": "yoga.png",
    "pilates": "yoga.png",
    "hiking": "hiking.png",
    "hike": "hiking.png",
    "trail": "hiking.png",
    "strength": "bench.png",
    "gym": "bench.png",
    "weights": "bench.png",
    "bench": "bench.png",
    "workout": "bench.png",
    "multisport": "multisport.png",
    "multi-sport": "multisport.png",
    "cross_training": "multisport.png",
    "cross-training": "multisport.png",
    "all": "multisport.png",
    "all_activities": "multisport.png",
    # Dashboard Features / Views
    "overview": "overview.png",
    "dashboard": "overview.png",
    "plan": "plan.png",
    "training_plan": "plan.png",
    "injury_risk": "injury_risk.png",
    "risk": "injury_risk.png",

    "race_predictor": "race_predictor.png",
    "race": "race_predictor.png",
    "insights": "insights.png",
    "analysis": "insights.png",
    "intelligence": "insights.png",
    "import": "import.png",
    "sync": "import.png",
    "settings": "settings.png",
    "athlete": "settings.png",
    # Telemetry / Health / Sleep / Physical Metrics
    "heartbeat": "heartbeat.png",
    "heart": "heartbeat.png",
    "cardio": "heartbeat.png",
    "cardiovascular": "heartbeat.png",
    "resting_hr": "heartbeat.png",
    "recovery": "recovery.png",
    "sleep": "recovery.png",
    "rest": "recovery.png",
    "cadence": "cadence.png",
    "spm": "cadence.png",
    "calories": "calories.png",
    "kcal": "calories.png",
    "burn": "calories.png",
    "speed": "speed.png",
    "velocity": "speed.png",
    "pace": "speed.png",
}


ICON_BG_COLOR = "#f0e2a3"


def get_icon_base64(icon_name: str) -> Optional[str]:
    """
    Returns the fresh base64 data URI for an icon name or filename directly from disk.
    """
    if not icon_name:
        return None

    filename = ICON_MAPPINGS.get(icon_name.lower().strip(), icon_name.strip())
    if not filename.lower().endswith((".png", ".svg", ".jpg", ".webp")):
        filename = f"{filename}.png"

    path = os.path.join(ICONS_DIR, filename)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(filename)[1].lstrip(".").lower()
            mime = f"image/{ext}" if ext != "svg" else "image/svg+xml"
            return f"data:{mime};base64,{encoded}"
    except Exception:
        return None


def get_icon_html(
    icon_name: str,
    size: int = 22,
    margin_right: int = 8,
    vertical_align: str = "middle",
    extra_style: str = "",
    invert: bool = False,
    with_bg: bool = True,
) -> str:
    """
    Generates an HTML element with base64 data URI for embedding in UI components.
    Uses solid #f0e2a3 background to render high-contrast black icons cleanly.
    """
    uri = get_icon_base64(icon_name)
    if not uri:
        return ""
    
    filter_style = "filter: invert(1) brightness(1.25); " if invert else "filter: none; "
    
    if with_bg:
        padding = max(3, int(size * 0.15))
        badge_dim = size + (padding * 2)
        container_style = (
            f"display: inline-flex; align-items: center; justify-content: center; "
            f"width: {badge_dim}px; height: {badge_dim}px; "
            f"background: {ICON_BG_COLOR}; "
            f"border-radius: 7px; border: 1px solid rgba(0, 0, 0, 0.15); "
            f"vertical-align: {vertical_align}; margin-right: {margin_right}px; "
            f"box-shadow: 0 2px 6px rgba(0,0,0,0.35); flex-shrink: 0; {extra_style}"
        )
        img_style = f"width: {size}px; height: {size}px; object-fit: contain; display: block; {filter_style}"
        return f'<div style="{container_style}"><img src="{uri}" alt="{icon_name}" style="{img_style}" /></div>'
    else:
        style = (
            f"width: {size}px; height: {size}px; vertical-align: {vertical_align}; "
            f"margin-right: {margin_right}px; display: inline-block; object-fit: contain; "
            f"{filter_style}{extra_style}"
        )
        return f'<img src="{uri}" alt="{icon_name}" style="{style}" />'


def get_icon_badge_html(
    icon_name: str,
    icon_size: int = 20,
    badge_size: int = 34,
    margin_right: int = 12,
    invert: bool = False,
) -> str:
    """
    Renders a black icon inside a capsule badge with solid #f0e2a3 background.
    """
    uri = get_icon_base64(icon_name)
    if not uri:
        return ""
    
    filter_style = "filter: invert(1) brightness(1.3);" if invert else "filter: none;"
    badge_html = (
        f'<div style="display: inline-flex; align-items: center; justify-content: center; width: {badge_size}px; height: {badge_size}px; background: {ICON_BG_COLOR}; border: 1px solid rgba(0, 0, 0, 0.15); border-radius: 9px; margin-right: {margin_right}px; flex-shrink: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.35);">'
        f'<img src="{uri}" alt="{icon_name}" style="width: {icon_size}px; height: {icon_size}px; {filter_style} object-fit: contain; display: block;" />'
        f'</div>'
    )
    return badge_html


def get_sport_icon_html(sport_type: str, size: int = 18) -> str:
    """
    Generates an inline HTML icon tag for a given sport type.
    """
    if not sport_type:
        return ""
    clean_type = sport_type.lower().strip()
    return get_icon_html(clean_type, size=size, margin_right=6, vertical_align="text-bottom")


def render_view_header(
    title: str,
    caption: Optional[str] = None,
    icon_name: Optional[str] = None,
    size: int = 24,
) -> None:
    """
    Renders a standard view level-2 heading with an embedded high-contrast icon badge.
    """
    icon_badge = get_icon_badge_html(icon_name, icon_size=size, badge_size=size + 14, margin_right=12) if icon_name else ""
    st.markdown(
        f'<div style="display: flex; align-items: center; margin-bottom: 4px;">'
        f'{icon_badge}'
        f'<h2 style="margin: 0; padding: 0; font-size: 1.55rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.01em;">{title}</h2>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if caption:
        st.caption(caption)


def render_section_header(
    title: str,
    icon_name: Optional[str] = None,
    size: int = 18,
) -> None:
    """
    Renders a level-3 section header with an optional embedded high-contrast icon badge.
    """
    icon_badge = get_icon_badge_html(icon_name, icon_size=size, badge_size=size + 10, margin_right=8) if icon_name else ""
    st.markdown(
        f'<div style="display: flex; align-items: center; margin-top: 16px; margin-bottom: 8px;">'
        f'{icon_badge}'
        f'<h3 style="margin: 0; padding: 0; font-size: 1.15rem; font-weight: 700; color: #f1f5f9;">{title}</h3>'
        f'</div>',
        unsafe_allow_html=True,
    )


def get_available_icon_files() -> List[str]:
    """Returns a list of all icon filenames in the icons directory."""
    if not os.path.exists(ICONS_DIR):
        return []
    return [f for f in sorted(os.listdir(ICONS_DIR)) if f.lower().endswith((".png", ".svg", ".jpg", ".webp"))]
