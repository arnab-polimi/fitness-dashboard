"""
Unit tests for centralized icon rendering system and solid #f0e2a3 background generation.
"""
from src.ui.icons import (
    ICON_BG_COLOR,
    get_icon_base64,
    get_icon_html,
    get_icon_badge_html,
    get_sport_icon_html,
    get_available_icon_files,
)


def test_icon_bg_color_definition():
    """Verify that the icon background color is solid #f0e2a3."""
    assert ICON_BG_COLOR.lower() == "#f0e2a3"


def test_get_icon_base64():
    """Test retrieving base64 URI for existing and missing icons."""
    uri = get_icon_base64("running")
    assert uri is not None
    assert uri.startswith("data:image/png;base64,")

    invalid = get_icon_base64("non_existent_icon_xyz")
    assert invalid is None


def test_get_icon_html_with_bg():
    """Verify get_icon_html renders solid #f0e2a3 container for black icons."""
    html = get_icon_html("running", size=24, with_bg=True)
    assert html != ""
    assert "#f0e2a3" in html
    assert "filter: none;" in html


def test_get_icon_badge_html():
    """Verify get_icon_badge_html renders black icon inside solid #f0e2a3 capsule badge."""
    badge_html = get_icon_badge_html("hiking", icon_size=20, badge_size=34)
    assert badge_html != ""
    assert "#f0e2a3" in badge_html
    assert "filter: none;" in badge_html


def test_get_sport_icon_html():
    """Verify sport icon helper."""
    sport_html = get_sport_icon_html("bike", size=18)
    assert sport_html != ""
    assert "#f0e2a3" in sport_html


def test_get_available_icon_files():
    """Verify listing available icon files."""
    files = get_available_icon_files()
    assert len(files) > 0
    assert "running.png" in files
