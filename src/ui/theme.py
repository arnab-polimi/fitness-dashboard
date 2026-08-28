"""
Custom Carbon Obsidian Dark Theme without Blue Tints.
Features high-contrast typography, neutral carbon glassmorphism cards,
and crisp icon contrast.
"""
import streamlit as st


def apply_dark_theme():
    """Applies sleek neutral carbon dark theme styling."""
    custom_css = """
    <style>
        /* Import Inter / JetBrains Mono fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

        /* Palette 10 Color Definitions */
        :root {
            --pal-mauve-bark: #664E4C;
            --pal-ash-brown: #725F53;
            --pal-olive-wood: #7D7059;
            --pal-palm-leaf: #949166;
            --pal-palm-light: #A0A26D;
            --pal-dry-sage: #ABB273;
            --pal-willow-green: #C1D37F;
            --pal-light-gold: #E2D58B;
            --pal-vanilla: #F0E2A3;
            --pal-peach-fuzz: #F9D4BB;

            --bg-primary: #120e0d;
            --bg-card: #1c1716;
            --bg-card-hover: #26201e;
            --border-color: #3b322e;
            --border-hover: #7d7059;
            --accent-primary: #a0a26d;
            --accent-secondary: #c1d37f;
            --accent-gold: #e2d58b;
            --accent-peach: #f9d4bb;
            --accent-sage: #abb273;
            --text-primary: #f0e2a3;
            --text-secondary: #c8b99c;
            --text-muted: #8c7e6c;
            --icon-bg: #f0e2a3;
        }

        /* Icon Badge Solid Container for High-Contrast Black Icons */
        .icon-gradient-badge, .icon-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--icon-bg) !important;
            border: 1px solid rgba(0, 0, 0, 0.15) !important;
            border-radius: 9px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
        }
        .icon-gradient-badge img, .icon-badge img {
            filter: none !important;
        }

        /* Base app styling */
        .stApp {
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #0d0a09 !important;
            border-right: 1px solid #26201e !important;
        }

        /* Hide default header decor */
        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        /* Custom metric card */
        .metric-card {
            background: linear-gradient(135deg, #1c1716 0%, #26201e 100%);
            border: 1px solid #3b322e;
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
            transition: transform 0.2s ease, border-color 0.2s ease;
            margin-bottom: 12px;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            border-color: var(--border-hover);
        }

        .metric-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-secondary);
            font-weight: 600;
            margin-bottom: 6px;
        }

        .metric-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.65rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 4px;
            line-height: 1.1;
        }

        .metric-sub {
            font-size: 0.75rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .metric-delta-pos {
            color: var(--pal-willow-green);
            font-weight: 600;
        }

        .metric-delta-neg {
            color: var(--pal-peach-fuzz);
            font-weight: 600;
        }

        /* Section Card */
        .section-card {
            background: #191413;
            border: 1px solid #332a27;
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .badge-optimal { background: rgba(193, 211, 127, 0.18); color: #c1d37f; border: 1px solid rgba(193, 211, 127, 0.4); }
        .badge-caution { background: rgba(226, 213, 139, 0.18); color: #e2d58b; border: 1px solid rgba(226, 213, 139, 0.4); }
        .badge-high { background: rgba(249, 212, 187, 0.18); color: #f9d4bb; border: 1px solid rgba(249, 212, 187, 0.4); }
        .badge-info { background: rgba(160, 162, 109, 0.18); color: #a0a26d; border: 1px solid rgba(160, 162, 109, 0.4); }

        /* Insight container */
        .insight-card {
            background: #1a1514;
            border-left: 4px solid var(--pal-palm-light);
            border-radius: 0 12px 12px 0;
            padding: 16px 20px;
            margin-bottom: 16px;
            border-top: 1px solid #332a27;
            border-right: 1px solid #332a27;
            border-bottom: 1px solid #332a27;
        }
        .insight-card-positive { border-left-color: #c1d37f; }
        .insight-card-warning { border-left-color: #e2d58b; }
        .insight-card-critical { border-left-color: #f9d4bb; }

        /* Disclaimer Box */
        .disclaimer-box {
            background: rgba(226, 213, 139, 0.06);
            border: 1px dashed rgba(226, 213, 139, 0.35);
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 0.78rem;
            color: #f0e2a3;
            margin-top: 16px;
            margin-bottom: 20px;
            line-height: 1.45;
        }

        /* Streamlit Tabs Customization */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
            border-bottom: 1px solid #332a27;
            padding-bottom: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 8px 16px;
            color: #c8b99c;
            background-color: transparent;
            font-weight: 600;
            font-size: 0.88rem;
        }

        .stTabs [aria-selected="true"] {
            background-color: #241e1c !important;
            color: #c1d37f !important;
            border-bottom: 2px solid #c1d37f !important;
        }

        /* PMC & Form Dynamics Cards */
        .pmc-card {
            background: linear-gradient(135deg, #1c1716 0%, #26201e 100%);
            border: 1px solid #3b322e;
            border-radius: 14px;
            padding: 18px 20px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
            transition: all 0.25s ease;
        }
        .pmc-card:hover {
            transform: translateY(-2px);
            border-color: #7d7059;
            box-shadow: 0 8px 28px rgba(0, 0, 0, 0.6);
        }
        .pmc-card-ctl { border-top: 3px solid #80923F; }
        .pmc-card-atl { border-top: 3px solid #7A2921; }
        .pmc-card-tsb { border-top: 3px solid #4D71B2; }
        .pmc-card-acwr { border-top: 3px solid #f9d4bb; }

        /* Form Spectrum Visual Bar */
        .spectrum-bar-wrap {
            background: #14100f;
            border: 1px solid #2e2624;
            border-radius: 12px;
            padding: 16px 20px;
            margin: 16px 0 24px 0;
        }
        .spectrum-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, 
                #664e4c 0%, 
                #725f53 20%, 
                #949166 40%, 
                #abb273 60%, 
                #c1d37f 80%, 
                #f9d4bb 100%
            );
            position: relative;
            margin: 18px 0 10px 0;
        }
        .spectrum-pointer {
            position: absolute;
            top: -7px;
            width: 26px;
            height: 26px;
            background: #f0e2a3;
            border: 3px solid #120e0d;
            border-radius: 50%;
            transform: translateX(-50%);
            box-shadow: none;
            transition: left 0.4s ease;
        }
        .spectrum-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.72rem;
            font-weight: 600;
            color: #c8b99c;
            letter-spacing: 0.02em;
        }

        /* Coaching Callout Box */
        .coaching-card {
            background: linear-gradient(135deg, rgba(28, 23, 22, 0.95) 0%, rgba(38, 32, 30, 0.95) 100%);
            border: 1px solid #3b322e;
            border-left: 4px solid #a0a26d;
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        }

        /* Custom scrollbars */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #120e0d;
        }
        ::-webkit-scrollbar-thumb {
            background: #3b322e;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #7d7059;
        }

        /* Streamlit Loading Spinner - Centered & Enlarged */
        [data-testid="stStatusWidget"], [data-testid="stSpinner"], .stSpinner {
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            z-index: 999999 !important;
            background: rgba(28, 23, 22, 0.92) !important;
            border: 1px solid #3b322e !important;
            border-radius: 16px !important;
            padding: 24px 36px !important;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.8) !important;
            backdrop-filter: blur(8px) !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
        }
        [data-testid="stStatusWidget"] svg, [data-testid="stSpinner"] svg, .stSpinner svg {
            width: 54px !important;
            height: 54px !important;
            color: #c1d37f !important;
        }
        [data-testid="stStatusWidget"] span, [data-testid="stSpinner"] span, .stSpinner span {
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            color: #f0e2a3 !important;
            margin-top: 12px !important;
        }

        /* Mobile Screen Responsiveness Optimizations (< 768px) */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1.5rem !important;
                padding-bottom: 2.5rem !important;
                padding-left: 0.35rem !important;
                padding-right: 0.35rem !important;
                max-width: 100vw !important;
            }
            [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
                margin-bottom: 6px !important;
            }
            .metric-card {
                padding: 12px 14px !important;
                margin-bottom: 8px !important;
            }
            .metric-value {
                font-size: 1.38rem !important;
            }
            .stPlotlyChart {
                width: 100% !important;
                min-width: 100% !important;
            }
            .js-plotly-plot, .plot-container {
                width: 100% !important;
            }
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
