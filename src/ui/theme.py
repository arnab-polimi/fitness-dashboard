"""
Custom Dark Professional Styling and CSS Theme.
"""
import streamlit as st


def apply_dark_theme():
    """Applies sleek dark theme styling, card containers, badge accents, and typography."""
    custom_css = """
    <style>
        /* Import Inter / JetBrains Mono fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

        /* Root color definitions */
        :root {
            --bg-primary: #0b0f19;
            --bg-card: #131b2e;
            --bg-card-hover: #1a253f;
            --border-color: #1e2d4d;
            --accent-cyan: #00d2ff;
            --accent-emerald: #00ffa3;
            --accent-coral: #ff4772;
            --accent-amber: #ffaa00;
            --accent-purple: #9d4edd;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
        }

        /* Base app styling */
        .stApp {
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #0d1322 !important;
            border-right: 1px solid #1a2640 !important;
        }

        /* Hide default header decor */
        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        /* Custom metric card */
        .metric-card {
            background: linear-gradient(135deg, #131b2e 0%, #17223b 100%);
            border: 1px solid #1e2e4f;
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
            transition: transform 0.2s ease, border-color 0.2s ease;
            margin-bottom: 12px;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            border-color: #2e4475;
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
            color: #ffffff;
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
            color: var(--accent-emerald);
            font-weight: 600;
        }

        .metric-delta-neg {
            color: var(--accent-coral);
            font-weight: 600;
        }

        /* Glassmorphism Section Card */
        .section-card {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
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
        .badge-optimal { background: rgba(0, 255, 163, 0.15); color: #00ffa3; border: 1px solid rgba(0, 255, 163, 0.3); }
        .badge-caution { background: rgba(255, 170, 0, 0.15); color: #ffaa00; border: 1px solid rgba(255, 170, 0, 0.3); }
        .badge-high { background: rgba(255, 71, 114, 0.15); color: #ff4772; border: 1px solid rgba(255, 71, 114, 0.3); }
        .badge-info { background: rgba(0, 210, 255, 0.15); color: #00d2ff; border: 1px solid rgba(0, 210, 255, 0.3); }

        /* Insight container */
        .insight-card {
            background: #131c31;
            border-left: 4px solid var(--accent-cyan);
            border-radius: 0 12px 12px 0;
            padding: 16px 20px;
            margin-bottom: 16px;
        }
        .insight-card-positive { border-left-color: #00ffa3; }
        .insight-card-warning { border-left-color: #ffaa00; }
        .insight-card-critical { border-left-color: #ff4772; }

        /* Disclaimer Box */
        .disclaimer-box {
            background: rgba(255, 170, 0, 0.06);
            border: 1px dashed rgba(255, 170, 0, 0.35);
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 0.78rem;
            color: #d1d5db;
            margin-top: 16px;
            margin-bottom: 20px;
            line-height: 1.45;
        }

        /* Streamlit Tabs Customization */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 8px 16px;
            color: #94a3b8;
            background-color: transparent;
            font-weight: 600;
            font-size: 0.88rem;
        }

        .stTabs [aria-selected="true"] {
            background-color: #1a253f !important;
            color: #00d2ff !important;
            border-bottom: 2px solid #00d2ff !important;
        }

        /* Custom scrollbars */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #0b0f19;
        }
        ::-webkit-scrollbar-thumb {
            background: #1e2d4d;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #2e4475;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
