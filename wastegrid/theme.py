import base64
from pathlib import Path

import streamlit as st


@st.cache_data
def get_logo_data_uri():
    """Returns base64-encoded Data URI for logo.png to render crisp graphics in HTML."""
    logo_path = Path(__file__).resolve().parent.parent / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"
    return ""


def get_palette(theme="light"):
    if theme == "dark":
        return {
            "name": "dark",
            "bg": "#0d131d",  # Deep rich obsidian-slate (NOT pitch pure black)
            "bg_soft": "#141c28",  # Subtle secondary surface
            "card_bg": "#151e2b",  # Elevated card background
            "card_hover": "#1c2738",  # Hover state
            "border": "#223145",  # Crisp slate border
            "border_subtle": "#1a2636",
            "text": "#f1f5f9",  # Soft porcelain white (NOT harsh glare)
            "muted": "#94a3b8",  # Refined slate gray
            "accent": "#ff3856",  # Luminous surgical red
            "accent_bg": "rgba(255, 56, 86, 0.12)",
            "success": "#22c55e",  # Luminous emerald
            "warn": "#fbbf24",  # Warm radiant amber
            "blue": "#38bdf8",  # Sky cyan
            "purple": "#a855f7",  # Radiant purple
            "shadow": "0 2px 6px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.3)",
            "divider": "#223145",
        }

    # Light palette: Soft architectural zinc-slate (NOT blinding pure white)
    return {
        "name": "light",
        "bg": "#eef2f6",  # Balanced atmosphere slate (NOT stark #ffffff)
        "bg_soft": "#e2e7ef",  # Subtle secondary surface
        "card_bg": "#ffffff",  # Crisp elevated card
        "card_hover": "#f8fafc",  # Hover state
        "border": "#dbe3ec",  # Subtle crisp border
        "border_subtle": "#e8eef6",
        "text": "#0f172a",  # Rich deep slate (NOT harsh jet black)
        "muted": "#64748b",  # Elegant slate gray
        "accent": "#d5001c",  # Porsche red
        "accent_bg": "rgba(213, 0, 28, 0.08)",
        "success": "#16a34a",  # Fresh emerald
        "warn": "#d97706",  # Warm amber
        "blue": "#0284c7",  # Vibrant ocean blue
        "purple": "#7c3aed",  # Royal purple
        "shadow": "0 1px 3px rgba(15,23,42,0.06), 0 6px 16px rgba(15,23,42,0.04)",
        "divider": "#dbe3ec",
    }


def inject_css(p):
    st.markdown(
        f"""
    <style>
        html, body, [class*="css"], .stApp, button, input, textarea {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif !important;
            -webkit-font-smoothing: antialiased;
        }}

        /* Force background and text colors on all Streamlit wrapper containers */
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main,
        [data-testid="stHeader"],
        [data-testid="stBottom"],
        .main {{
            background: {p["bg"]} !important;
            background-color: {p["bg"]} !important;
            color: {p["text"]} !important;
        }}

        h1, h2, h3, h4, p, span, label {{ color: {p["text"]}; }}

        /* Ensure pre, code, and code containers match active palette with zero dark glitches in light mode */
        pre, code, .stCodeBlock, [data-testid="stCodeBlock"] {{
            background-color: {p["bg_soft"]} !important;
            color: {p["text"]} !important;
            border: 1px solid {p["border"]} !important;
            border-radius: 6px !important;
        }}

        /* Universal Dialog & BaseWeb Modal Styling matching active theme palette */
        div[data-baseweb="modal"] div[role="dialog"],
        div[data-baseweb="modal"] [data-baseweb="modal-body"],
        div[role="dialog"],
        div[data-testid="stDialog"],
        div[data-testid="stModal"],
        [data-testid="stDialog"] > div {{
            background-color: {p["card_bg"]} !important;
            background: {p["card_bg"]} !important;
            color: {p["text"]} !important;
            border: 1.5px solid {p["border"]} !important;
            border-radius: 16px !important;
            box-shadow: {p["shadow"]} !important;
        }}

        div[data-baseweb="modal"] div[role="dialog"] *,
        div[data-testid="stDialog"] * {{
            color: {p["text"]};
        }}

        /* Universal Input Fields & Form Controls across Modals and Dashboards */
        div[data-baseweb="modal"] input,
        div[data-baseweb="modal"] textarea,
        div[data-testid="stDialog"] input,
        div[data-testid="stDialog"] textarea,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-baseweb="input"] > div,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        div[data-testid="stDialog"] [data-baseweb="select"] > div,
        div[data-baseweb="modal"] [data-baseweb="select"] > div {{
            background-color: {p["card_bg"]} !important;
            color: {p["text"]} !important;
            border: 1px solid {p["border"]} !important;
            border-radius: 8px !important;
        }}

        /* Universal Select Dropdowns & Popovers */
        [data-baseweb="popover"],
        [data-baseweb="menu"],
        div[role="listbox"] {{
            background-color: {p["card_bg"]} !important;
            background: {p["card_bg"]} !important;
            color: {p["text"]} !important;
            border: 1px solid {p["border"]} !important;
            box-shadow: {p["shadow"]} !important;
            border-radius: 8px !important;
        }}
        div[role="option"] {{
            color: {p["text"]} !important;
            background-color: {p["card_bg"]} !important;
        }}
        div[role="option"]:hover,
        div[role="option"][aria-selected="true"] {{
            background-color: {p["bg_soft"]} !important;
            color: {p["blue"]} !important;
        }}

        /* Universal Main Page & Modal Tabs */
        div[data-baseweb="modal"] [data-baseweb="tab-list"],
        div[data-testid="stDialog"] [data-baseweb="tab-list"],
        [data-testid="stTabs"] [data-baseweb="tab-list"],
        div[data-baseweb="tab-list"] {{
            border-bottom: 2px solid {p["border"]} !important;
            background: transparent !important;
        }}

        div[data-baseweb="modal"] button[data-baseweb="tab"],
        div[data-testid="stDialog"] button[data-baseweb="tab"],
        [data-testid="stTabs"] button[data-baseweb="tab"],
        div[data-baseweb="tab-list"] button[data-baseweb="tab"] {{
            color: {p["muted"]} !important;
            font-weight: 700 !important;
            background: transparent !important;
            border: none !important;
            border-bottom: 2.5px solid transparent !important;
        }}

        div[data-baseweb="modal"] button[data-baseweb="tab"]:hover,
        div[data-testid="stDialog"] button[data-baseweb="tab"]:hover,
        [data-testid="stTabs"] button[data-baseweb="tab"]:hover,
        div[data-baseweb="tab-list"] button[data-baseweb="tab"]:hover {{
            color: {p["blue"]} !important;
            background: {p["card_hover"]} !important;
        }}

        div[data-baseweb="modal"] button[data-baseweb="tab"][aria-selected="true"],
        div[data-testid="stDialog"] button[data-baseweb="tab"][aria-selected="true"],
        [data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
        div[data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] {{
            color: {p["accent"]} !important;
            font-weight: 800 !important;
            border-bottom: 2.5px solid {p["accent"]} !important;
            background: transparent !important;
        }}

        div[data-baseweb="modal"] button[data-baseweb="tab"] p,
        div[data-testid="stDialog"] button[data-baseweb="tab"] p,
        [data-testid="stTabs"] button[data-baseweb="tab"] p,
        div[data-baseweb="tab-list"] button[data-baseweb="tab"] p {{
            color: inherit !important;
        }}

        /* Streamlit Metric Cards */
        [data-testid="stMetric"] {{
            background: {p["card_bg"]} !important;
            border: 1px solid {p["border"]} !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            box-shadow: {p["shadow"]} !important;
        }}
        [data-testid="stMetricLabel"] * {{
            color: {p["muted"]} !important;
        }}
        [data-testid="stMetricValue"] * {{
            color: {p["text"]} !important;
        }}

        /* Streamlit Alert Callouts */
        [data-testid="stAlert"] {{
            border-radius: 8px !important;
            border: 1px solid {p["border"]} !important;
            background-color: {p["card_bg"]} !important;
            color: {p["text"]} !important;
        }}
        [data-testid="stAlert"] * {{
            color: {p["text"]} !important;
        }}

        /* Modal Buttons */
        div[data-baseweb="modal"] .stButton > button,
        div[data-testid="stDialog"] .stButton > button {{
            background-color: {p["card_bg"]} !important;
            color: {p["text"]} !important;
            border: 1.5px solid {p["border"]} !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
        }}

        div[data-baseweb="modal"] .stButton > button:hover,
        div[data-testid="stDialog"] .stButton > button:hover {{
            border-color: {p["blue"]} !important;
            background-color: {p["card_hover"]} !important;
            color: {p["blue"]} !important;
        }}

        div[data-baseweb="modal"] button[kind="primary"],
        div[data-testid="stDialog"] button[kind="primary"],
        div[data-baseweb="modal"] button[data-testid="stBaseButton-primary"],
        div[data-testid="stDialog"] button[data-testid="stBaseButton-primary"],
        div[data-baseweb="modal"] form button,
        div[data-testid="stDialog"] form button {{
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 800 !important;
        }}
        div[data-baseweb="modal"] form button *,
        div[data-testid="stDialog"] form button * {{
            color: #ffffff !important;
        }}

        [data-testid="stHeader"] {{
            height: 3rem !important;
            background: transparent !important;
            z-index: 100 !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: {p["bg_soft"]} !important;
            border-right: 1px solid {p["border"]} !important;
        }}
        [data-testid="stSidebar"] * {{
            color: {p["text"]};
        }}
        /* Keep stToolbar visible for stExpandSidebarButton */
        [data-testid="stToolbar"] {{
            display: flex !important;
            visibility: visible !important;
            background: transparent !important;
            height: 3rem !important;
        }}
        [data-testid="stToolbarActions"],
        #MainMenu,
        footer {{
            display: none !important;
            visibility: hidden !important;
        }}

        /* Crisp 3-Bars Hamburger Button to Open Sidebar */
        [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapsedControl"] {{
            display: inline-flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: fixed !important;
            top: 14px !important;
            left: 18px !important;
            z-index: 9999999 !important;
            background: {p["card_bg"]} !important;
            border: 1.5px solid {p["border"]} !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            box-shadow: {p["shadow"]} !important;
            cursor: pointer !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.2s ease !important;
        }}
        [data-testid="stExpandSidebarButton"]:hover,
        [data-testid="stSidebarCollapsedControl"]:hover {{
            border-color: {p["blue"]} !important;
            background: {p["card_hover"]} !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        }}
        [data-testid="stExpandSidebarButton"]::before,
        [data-testid="stSidebarCollapsedControl"] button::before {{
            content: "☰" !important;
            font-size: 1.4rem !important;
            font-weight: 900 !important;
            color: {p["text"]} !important;
            display: inline-block !important;
            line-height: 1 !important;
        }}
        [data-testid="stExpandSidebarButton"] svg,
        [data-testid="stExpandSidebarButton"] span,
        [data-testid="stSidebarCollapsedControl"] svg {{
            display: none !important;
        }}
        [data-testid="stSidebarCollapseButton"] {{
            display: flex !important;
            visibility: visible !important;
            color: {p["text"]} !important;
            background: {p["card_bg"]} !important;
            border: 1px solid {p["border"]} !important;
            border-radius: 6px !important;
            padding: 4px 8px !important;
        }}
        [data-testid="stSidebarCollapseButton"]:hover {{
            border-color: {p["accent"]} !important;
            color: {p["accent"]} !important;
        }}

        .block-container {{
            padding-top: 1.2rem !important;
            padding-bottom: 3.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important;
            width: 100% !important;
        }}

        /* Full-Width Hero Section */
        .wg-hero {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(2, 132, 199, 0.15) 50%, rgba(124, 58, 237, 0.1) 100%);
            border: 1.5px solid rgba(16, 185, 129, 0.35);
            border-radius: 14px;
            padding: 24px 28px;
            margin-bottom: 22px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            position: relative;
        }}

        /* Services Grid */
        .services-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
            margin-bottom: 24px;
        }}
        @media (max-width: 1100px) {{
            .services-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        @media (max-width: 650px) {{
            .services-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        .service-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 12px;
            padding: 20px;
            box-shadow: {p["shadow"]};
            transition: all 0.25s ease;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .service-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.12);
            border-color: {p["blue"]};
        }}

        /* Professional Full Footer */
        .site-footer {{
            margin-top: 48px;
            padding-top: 32px;
            border-top: 1px solid {p["border"]};
            color: {p["muted"]};
            font-size: 0.82rem;
            line-height: 1.7;
        }}
        .footer-grid {{
            display: grid;
            grid-template-columns: 2.2fr 1.2fr 1.3fr 1.3fr;
            gap: 28px;
            margin-bottom: 24px;
        }}
        @media (max-width: 900px) {{
            .footer-grid {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}
        }}
        .footer-col-title {{
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: {p["text"]};
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .footer-bottom {{
            padding-top: 18px;
            border-top: 1px solid {p["border_subtle"]};
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.72rem;
            color: {p["muted"]};
            flex-wrap: wrap;
            gap: 12px;
        }}

        /* Header */
        .wg-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 20px;
            border-bottom: 2px solid {p["border"]};
            margin-bottom: 24px;
        }}
        .wg-brand {{ display: flex; align-items: center; gap: 14px; }}
        .wg-brand img {{ width: 50px; height: 50px; border-radius: 8px; }}
        .wg-title {{
            font-size: 1.7rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1;
            color: {p["text"]};
        }}
        .wg-tagline {{
            font-size: 0.68rem;
            color: {p["muted"]};
            margin-top: 6px;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            font-weight: 600;
        }}

        /* Header Controls */
        .hdr-controls {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .hdr-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            border-radius: 999px;
            font-size: 0.66rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            box-shadow: {p["shadow"]};
            transition: all 0.3s ease;
        }}
        .hdr-badge.optimal {{ border-color: rgba(34, 197, 94, 0.4); color: {p["success"]}; }}
        .hdr-badge.warn {{ border-color: rgba(245, 158, 11, 0.5); color: {p["warn"]}; }}
        .hdr-badge.alert {{ border-color: rgba(255, 56, 86, 0.5); color: {p["accent"]}; }}
        
        .pulse-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            display: inline-block;
            animation: pulseBeacon 1.8s infinite ease-in-out;
        }}
        .pulse-dot.green {{ background: {p["success"]}; box-shadow: 0 0 8px {p["success"]}; }}
        .pulse-dot.yellow {{ background: {p["warn"]}; box-shadow: 0 0 8px {p["warn"]}; }}
        .pulse-dot.red {{ background: {p["accent"]}; box-shadow: 0 0 8px {p["accent"]}; }}

        .theme-toggle-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: {p["text"]} !important;
            text-decoration: none !important;
            box-shadow: {p["shadow"]};
            transition: all 0.2s ease;
        }}
        .theme-toggle-link:hover {{
            border-color: {p["accent"]};
            color: {p["accent"]} !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}

        /* Metric row */
        .metric-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1.3fr 1fr;
            gap: 16px;
            margin-bottom: 22px;
        }}
        .m-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-top: 3px solid {p["blue"]};
            border-radius: 8px;
            padding: 22px;
            box-shadow: {p["shadow"]};
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .m-card:hover {{
            transform: translateY(-3px);
            border-color: {p["muted"]};
            box-shadow: 0 8px 24px rgba(0,0,0,0.18);
        }}
        .m-card.hero {{
            border-top: 3px solid {p["accent"]};
        }}
        .m-card.green {{ border-top: 3px solid {p["success"]}; }}
        .m-card.purple {{ border-top: 3px solid {p["purple"]}; }}
        .m-label {{
            font-size: 0.62rem;
            color: {p["muted"]};
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-weight: 700;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .m-value {{
            font-size: 2.4rem;
            font-weight: 600;
            letter-spacing: -0.03em;
            line-height: 1;
            color: {p["text"]};
            font-variant-numeric: tabular-nums;
        }}
        .m-card.hero .m-value {{ font-size: 3rem; }}
        .m-value.text {{ font-size: 1.5rem; font-weight: 600; }}
        .m-value.red {{ color: {p["accent"]} !important; }}
        .m-value.green {{ color: {p["success"]} !important; }}

        /* Status Banner */
        .wg-status {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-left: 4px solid {p["success"]};
            border-radius: 6px;
            padding: 16px 22px;
            font-size: 0.85rem;
            color: {p["text"]};
            margin-bottom: 20px;
            box-shadow: {p["shadow"]};
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .wg-status.red {{
            border-left-color: {p["accent"]};
            background: {p["accent_bg"]};
            color: {p["accent"]} !important;
            font-weight: 700;
        }}
        .wg-status.warn {{
            border-left-color: {p["warn"]};
            background: rgba(245,158,11,0.08);
            color: {p["warn"]} !important;
            margin-top: -12px;
            margin-bottom: 20px;
            font-weight: 600;
        }}

        /* Action buttons */
        .action-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-bottom: 22px;
        }}
        .act-btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            text-align: center;
            padding: 16px 12px;
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: {p["text"]} !important;
            text-decoration: none !important;
            box-shadow: {p["shadow"]};
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .act-btn:hover {{
            border-color: {p["accent"]};
            color: {p["accent"]} !important;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(213,0,28,0.2);
        }}
        .act-btn.primary {{
            background: {p["accent"]};
            color: #ffffff !important;
            border-color: {p["accent"]};
        }}
        .act-btn.primary:hover {{
            background: #b00018;
            border-color: #b00018;
            color: #ffffff !important;
            box-shadow: 0 6px 20px rgba(213,0,28,0.4);
        }}

        /* Stream Breakdown Component */
        .breakdown-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 24px;
            box-shadow: {p["shadow"]};
        }}
        .breakdown-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .breakdown-title {{
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: {p["muted"]};
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .breakdown-ratio {{
            font-size: 0.8rem;
            font-weight: 600;
            color: {p["text"]};
            font-variant-numeric: tabular-nums;
        }}
        .split-bar-wrap {{
            height: 10px;
            background: {p["border"]};
            border-radius: 5px;
            overflow: hidden;
            display: flex;
            margin-bottom: 14px;
        }}
        .split-bar-wet {{
            height: 100%;
            background: {p["blue"]};
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .split-bar-dry {{
            height: 100%;
            background: {p["purple"]};
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .breakdown-legend {{
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: {p["muted"]};
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}

        /* Section titles */
        .sec-title {{
            font-size: 0.72rem;
            font-weight: 800;
            color: {p["text"]};
            letter-spacing: 0.22em;
            text-transform: uppercase;
            margin: 18px 0 16px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid {p["accent"]};
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}

        /* Facility cards */
        .fac-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }}
        .fac-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            padding: 22px;
            box-shadow: {p["shadow"]};
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .fac-card:hover {{
            transform: translateY(-3px);
            border-color: {p["muted"]};
            box-shadow: 0 8px 24px rgba(0,0,0,0.18);
        }}
        .fac-card.offline {{
            opacity: 0.6;
            border-style: dashed;
        }}
        .fac-name-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .fac-name {{
            font-weight: 700;
            font-size: 0.98rem;
            color: {p["text"]};
        }}
        .fac-badge {{
            font-size: 0.6rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 4px 10px;
            border-radius: 999px;
        }}
        .fac-badge.active {{ background: rgba(34, 197, 94, 0.15); color: {p["success"]}; border: 1px solid rgba(34, 197, 94, 0.3); }}
        .fac-badge.offline {{ background: rgba(239, 68, 68, 0.15); color: {p["accent"]}; border: 1px solid rgba(239, 68, 68, 0.3); }}
        .fac-type {{
            font-size: 0.6rem;
            color: {p["muted"]};
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-weight: 600;
            margin-top: 6px;
        }}
        .fac-bar-wrap {{
            height: 8px;
            background: {p["border"]};
            border-radius: 4px;
            overflow: hidden;
            margin-top: 18px;
        }}
        .fac-bar {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .fac-stat {{
            margin-top: 12px;
            font-size: 0.82rem;
            color: {p["text"]};
            font-weight: 500;
            font-variant-numeric: tabular-nums;
        }}
        .fac-util {{
            margin-top: 6px;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}

        /* Comparison cards */
        .cmp-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 22px;
        }}
        .cmp-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-top: 3px solid {p["muted"]};
            border-radius: 8px;
            padding: 24px;
            box-shadow: {p["shadow"]};
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .cmp-card:hover {{ transform: translateY(-3px); }}
        .cmp-card.win {{
            border-top-color: {p["success"]};
        }}
        .cmp-label {{
            font-size: 0.62rem;
            color: {p["muted"]};
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-weight: 700;
            margin-bottom: 14px;
        }}
        .cmp-value {{
            font-size: 2.4rem;
            font-weight: 600;
            letter-spacing: -0.03em;
            line-height: 1;
            color: {p["text"]};
            font-variant-numeric: tabular-nums;
        }}
        .cmp-value.red {{ color: {p["accent"]} !important; }}
        .cmp-value.green {{ color: {p["success"]} !important; }}

        /* Success banner */
        .success-banner {{
            border-left: 4px solid {p["success"]};
            background: rgba(22,163,74,0.08);
            border-radius: 6px;
            padding: 16px 22px;
            font-size: 0.85rem;
            font-weight: 700;
            color: {p["success"]};
            box-shadow: {p["shadow"]};
            margin-top: 14px;
            margin-bottom: 24px;
        }}

        /* 7-Day Forecast Visual Grid */
        .fc-visual-grid {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 12px;
            margin-bottom: 18px;
        }}
        .fc-day-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            padding: 16px 12px;
            text-align: center;
            box-shadow: {p["shadow"]};
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }}
        .fc-day-card:hover {{
            transform: translateY(-3px);
            border-color: {p["muted"]};
        }}
        .fc-day-card.overflow {{
            border-color: {p["accent"]};
            background: {p["accent_bg"]};
        }}
        .fc-day-name {{
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: {p["muted"]};
            margin-bottom: 8px;
        }}
        .fc-meter-wrap {{
            height: 90px;
            width: 14px;
            background: {p["border"]};
            border-radius: 7px;
            margin: 0 auto 12px auto;
            position: relative;
            display: flex;
            align-items: flex-end;
            overflow: hidden;
        }}
        .fc-meter-fill {{
            width: 100%;
            border-radius: 7px;
            transition: height 0.8s ease;
        }}
        .fc-meter-fill.normal {{ background: {p["blue"]}; }}
        .fc-meter-fill.surge {{ background: {p["accent"]}; }}
        .fc-day-val {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {p["text"]};
            font-variant-numeric: tabular-nums;
            line-height: 1;
        }}
        .fc-day-badge {{
            font-size: 0.58rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-top: 8px;
            padding: 3px 6px;
            border-radius: 4px;
            display: inline-block;
        }}
        .fc-day-badge.safe {{ background: rgba(34,197,94,0.15); color: {p["success"]}; }}
        .fc-day-badge.risk {{ background: rgba(255,56,86,0.2); color: {p["accent"]}; }}

        /* Executive HTML Forecast Table */
        .fc-table-wrap {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            overflow: hidden;
            box-shadow: {p["shadow"]};
            margin-bottom: 28px;
        }}
        .fc-table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.82rem;
        }}
        .fc-table th {{
            background: {p["bg_soft"]};
            color: {p["muted"]};
            font-size: 0.64rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            padding: 14px 18px;
            border-bottom: 1px solid {p["border"]};
        }}
        .fc-table td {{
            padding: 13px 18px;
            border-bottom: 1px solid {p["border_subtle"]};
            color: {p["text"]};
            font-variant-numeric: tabular-nums;
        }}
        .fc-table tr:last-child td {{
            border-bottom: none;
        }}
        .fc-table tr:hover td {{
            background: {p["bg_soft"]};
        }}
        .fc-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 9px;
            border-radius: 999px;
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}
        .fc-pill.safe {{ background: rgba(34,197,94,0.12); color: {p["success"]}; }}
        .fc-pill.overflow {{ background: rgba(255,56,86,0.15); color: {p["accent"]}; }}

        /* Data Ingestion Box */
        .data-source-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 28px;
            box-shadow: {p["shadow"]};
        }}

        /* Streamlit overrides */
        [data-testid="stExpander"],
        details[data-testid="stExpander"],
        [data-testid="stExpander"] details {{
            background: {p["card_bg"]} !important;
            background-color: {p["card_bg"]} !important;
            border: 1px solid {p["border"]} !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            box-shadow: {p["shadow"]} !important;
            margin-bottom: 24px !important;
        }}
        [data-testid="stExpander"] summary,
        details[data-testid="stExpander"] > summary,
        [data-testid="stExpander"] > summary {{
            background: {p["card_bg"]} !important;
            background-color: {p["card_bg"]} !important;
            font-weight: 700 !important;
            font-size: 0.72rem !important;
            letter-spacing: 0.14em !important;
            text-transform: uppercase !important;
            padding: 16px 22px !important;
            color: {p["text"]} !important;
            border-bottom: 1px solid {p["border_subtle"]} !important;
        }}
        [data-testid="stExpander"] summary:hover,
        details[data-testid="stExpander"] > summary:hover {{
            background: {p["bg_soft"]} !important;
            background-color: {p["bg_soft"]} !important;
            color: {p["accent"]} !important;
        }}
        [data-testid="stExpander"] summary *,
        details[data-testid="stExpander"] > summary * {{
            color: {p["text"]} !important;
        }}
        [data-testid="stExpanderDetails"] {{
            background: {p["card_bg"]} !important;
            background-color: {p["card_bg"]} !important;
            padding: 16px 22px !important;
        }}

        /* File Uploader styling */
        [data-testid="stFileUploader"] {{
            background: transparent !important;
            padding: 4px 0 !important;
        }}
        [data-testid="stFileUploaderDropzone"] {{
            background: {p["bg_soft"]} !important;
            border: 1px dashed {p["muted"]} !important;
            border-radius: 8px !important;
            padding: 16px !important;
            transition: all 0.2s ease !important;
        }}
        [data-testid="stFileUploaderDropzone"]:hover {{
            border-color: {p["accent"]} !important;
            background: {p["accent_bg"]} !important;
        }}
        [data-testid="stFileUploaderDropzone"] * {{
            color: {p["text"]} !important;
        }}
        [data-testid="stFileUploaderDropzone"] button {{
            background: {p["card_bg"]} !important;
            border: 1px solid {p["border"]} !important;
            color: {p["text"]} !important;
            font-weight: 700 !important;
            font-size: 0.72rem !important;
            letter-spacing: 0.08em !important;
            border-radius: 6px !important;
            box-shadow: {p["shadow"]} !important;
            transition: all 0.2s ease !important;
        }}
        [data-testid="stFileUploaderDropzone"] button:hover {{
            border-color: {p["accent"]} !important;
            color: {p["accent"]} !important;
            transform: translateY(-1px) !important;
        }}
        [data-testid="stFileUploaderDropzone"] button * {{
            color: {p["text"]} !important;
        }}

        /* Streamlit Native Buttons (Used for 4 Actions Grid) */
        [data-testid="stBaseButton-secondary"] {{
            background: {p["card_bg"]} !important;
            border: 1px solid {p["border"]} !important;
            border-radius: 6px !important;
            padding: 14px 12px !important;
            color: {p["text"]} !important;
            box-shadow: {p["shadow"]} !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
        }}
        [data-testid="stBaseButton-secondary"]:hover {{
            border-color: {p["accent"]} !important;
            color: {p["accent"]} !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(213,0,28,0.2) !important;
        }}
        [data-testid="stBaseButton-secondary"] p,
        [data-testid="stBaseButton-secondary"] span,
        [data-testid="stBaseButton-secondary"] div {{
            color: {p["text"]} !important;
            font-size: 0.72rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.12em !important;
            text-transform: uppercase !important;
        }}
        [data-testid="stBaseButton-secondary"]:hover p,
        [data-testid="stBaseButton-secondary"]:hover span,
        [data-testid="stBaseButton-secondary"]:hover div {{
            color: {p["accent"]} !important;
        }}

        [data-testid="stBaseButton-primary"] {{
            background: {p["accent"]} !important;
            border: 1px solid {p["accent"]} !important;
            border-radius: 6px !important;
            padding: 14px 12px !important;
            color: #ffffff !important;
            box-shadow: 0 4px 14px rgba(213,0,28,0.3) !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
        }}
        [data-testid="stBaseButton-primary"]:hover {{
            background: #b00018 !important;
            border-color: #b00018 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(213,0,28,0.5) !important;
        }}
        [data-testid="stBaseButton-primary"] p,
        [data-testid="stBaseButton-primary"] span,
        [data-testid="stBaseButton-primary"] div {{
            color: #ffffff !important;
            font-size: 0.72rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.12em !important;
            text-transform: uppercase !important;
        }}

        /* Download Button Fix */
        .stDownloadButton, [data-testid="stDownloadButton"] {{
            display: inline-block !important;
            margin: 8px 0 !important;
        }}
        .stDownloadButton > button,
        [data-testid="stDownloadButton"] > button {{
            background: {p["accent"]} !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 0.74rem !important;
            letter-spacing: 0.12em !important;
            text-transform: uppercase !important;
            border: 1px solid {p["accent"]} !important;
            border-radius: 6px !important;
            padding: 12px 24px !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 14px rgba(213,0,28,0.25) !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 8px !important;
            cursor: pointer !important;
            width: auto !important;
        }}
        .stDownloadButton > button p,
        .stDownloadButton > button span,
        .stDownloadButton > button div,
        [data-testid="stDownloadButton"] > button p,
        [data-testid="stDownloadButton"] > button span,
        [data-testid="stDownloadButton"] > button div {{
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 0.74rem !important;
            letter-spacing: 0.12em !important;
            text-transform: uppercase !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        .stDownloadButton > button:hover,
        [data-testid="stDownloadButton"] > button:hover {{
            background: #b00018 !important;
            border-color: #b00018 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 22px rgba(213,0,28,0.4) !important;
        }}

        /* =================== AUTH & LOGIN SCREEN =================== */
        .login-wrapper {{
            max-width: 860px;
            margin: 20px auto 30px auto;
        }}
        .login-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 12px;
            padding: 28px 32px;
            box-shadow: {p["shadow"]};
            margin-bottom: 24px;
        }}
        .login-header {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 12px;
        }}
        .login-title {{
            font-size: 2rem;
            font-weight: 800;
            color: {p["text"]};
            letter-spacing: -0.03em;
            line-height: 1;
        }}
        .login-sub {{
            font-size: 0.72rem;
            color: {p["muted"]};
            letter-spacing: 0.16em;
            text-transform: uppercase;
            font-weight: 600;
            margin-top: 6px;
        }}
        .login-notice {{
            font-size: 0.85rem;
            color: {p["text"]};
            opacity: 0.85;
            line-height: 1.5;
        }}
        .login-box-header {{
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: {p["text"]};
            margin-bottom: 16px;
            padding-bottom: 6px;
            border-bottom: 2px solid {p["accent"]};
        }}
        .quick-role-row {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 10px;
            transition: all 0.2s ease;
        }}
        .quick-role-row:hover {{
            border-color: {p["accent"]};
            transform: translateX(4px);
        }}
        .quick-role-title {{
            font-size: 0.82rem;
            font-weight: 700;
            color: {p["text"]};
        }}
        .quick-role-sub {{
            font-size: 0.68rem;
            color: {p["muted"]};
            margin-top: 2px;
        }}
        .creds-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            padding: 20px 24px;
            box-shadow: {p["shadow"]};
        }}
        .creds-title {{
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            color: {p["text"]};
            margin-bottom: 14px;
        }}

        /* =================== ROLE HEADER & LOGOUT =================== */
        .user-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 14px;
            border-radius: 999px;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            color: {p["text"]};
            box-shadow: {p["shadow"]};
        }}
        .user-pill .badge {{
            background: {p["accent_bg"]};
            color: {p["accent"]};
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 0.6rem;
        }}

        /* =================== ROLE HERO BANNER =================== */
        .role-view-hero {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-left: 5px solid {p["blue"]};
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 24px;
            box-shadow: {p["shadow"]};
        }}
        .role-hero-title {{
            font-size: 1.15rem;
            font-weight: 800;
            color: {p["text"]};
            letter-spacing: -0.01em;
            margin-bottom: 6px;
        }}
        .role-hero-sub {{
            font-size: 0.76rem;
            color: {p["muted"]};
            line-height: 1.4;
        }}

        /* =================== PREDICTIVE CALENDAR =================== */
        .cal-header-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 22px;
            box-shadow: {p["shadow"]};
        }}
        .cal-title-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .cal-title {{
            font-size: 1.1rem;
            font-weight: 800;
            color: {p["text"]};
            letter-spacing: -0.01em;
        }}
        .cal-sub {{
            font-size: 0.75rem;
            color: {p["muted"]};
            margin-top: 4px;
        }}
        .cal-timeline-grid {{
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            gap: 10px;
            margin-bottom: 24px;
        }}
        @media (max-width: 1200px) {{
            .cal-timeline-grid {{ grid-template-columns: repeat(4, 1fr); }}
        }}
        .cal-date-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            padding: 12px 10px;
            text-align: center;
            box-shadow: {p["shadow"]};
            transition: all 0.25s ease;
            position: relative;
        }}
        .cal-date-card:hover {{
            transform: translateY(-3px);
            border-color: {p["muted"]};
        }}
        .cal-date-card.danger {{
            border-color: {p["accent"]};
            background: {p["accent_bg"]};
        }}
        .cal-date-card.warn {{
            border-color: {p["warn"]};
        }}
        .cal-date-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.7rem;
            margin-bottom: 6px;
        }}
        .cal-day-num {{
            font-weight: 800;
            color: {p["text"]};
        }}
        .cal-day-name {{
            font-weight: 600;
            color: {p["muted"]};
            text-transform: uppercase;
        }}
        .cal-event-name {{
            font-size: 0.65rem;
            font-weight: 700;
            color: {p["text"]};
            height: 28px;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.2;
            margin-bottom: 6px;
        }}
        .cal-badge {{
            font-size: 0.55rem;
            font-weight: 700;
            padding: 2px 5px;
            border-radius: 4px;
            display: inline-block;
            text-transform: uppercase;
        }}
        .cal-badge.normal {{ background: {p["bg_soft"]}; color: {p["muted"]}; }}
        .cal-badge.weekend {{ background: rgba(59,130,246,0.15); color: {p["blue"]}; }}
        .cal-badge.festival {{ background: rgba(245,158,11,0.2); color: {p["warn"]}; }}
        .cal-demand-val {{
            font-size: 0.95rem;
            font-weight: 800;
            color: {p["text"]};
            margin-top: 6px;
            font-variant-numeric: tabular-nums;
        }}
        .cal-status-text {{
            font-size: 0.58rem;
            font-weight: 700;
            margin-top: 4px;
            color: {p["muted"]};
        }}
        .cal-date-card.danger .cal-status-text {{ color: {p["accent"]}; }}
        .cal-date-card.normal .cal-status-text {{ color: {p["success"]}; }}

        /* =================== TRUCK FLEET BRIDGE =================== */
        .truck-header-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 22px;
            box-shadow: {p["shadow"]};
        }}
        .truck-title {{
            font-size: 1.1rem;
            font-weight: 800;
            color: {p["text"]};
            letter-spacing: -0.01em;
        }}
        .truck-sub {{
            font-size: 0.75rem;
            color: {p["muted"]};
            margin-top: 4px;
        }}
        .bridge-flow-wrap {{
            display: grid;
            grid-template-columns: 1fr auto 1fr auto 1fr auto 1fr auto 1.2fr;
            gap: 10px;
            align-items: center;
            background: {p["bg_soft"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            padding: 18px 20px;
            margin: 12px 0 20px 0;
        }}
        @media (max-width: 1024px) {{
            .bridge-flow-wrap {{ grid-template-columns: 1fr; }}
            .bridge-arrow {{ display: none; }}
        }}
        .bridge-step {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-radius: 6px;
            padding: 12px 14px;
            text-align: left;
            box-shadow: {p["shadow"]};
        }}
        .bridge-step.highlight {{
            border-color: {p["accent"]};
            background: {p["accent_bg"]};
        }}
        .bridge-step-num {{
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: {p["blue"]};
            color: #ffffff;
            font-size: 0.68rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 8px;
        }}
        .bridge-step.highlight .bridge-step-num {{
            background: {p["accent"]};
        }}
        .bridge-step-title {{
            font-size: 0.75rem;
            font-weight: 800;
            color: {p["text"]};
            margin-bottom: 4px;
        }}
        .bridge-step-body {{
            font-size: 0.65rem;
            color: {p["muted"]};
            line-height: 1.35;
        }}
        .bridge-arrow {{
            color: {p["muted"]};
            font-size: 1.2rem;
            font-weight: 800;
        }}

        /* =================== CARBON SCORECARD =================== */
        .carbon-card {{
            background: {p["card_bg"]};
            border: 1px solid {p["border"]};
            border-top: 3px solid {p["success"]};
            border-radius: 8px;
            padding: 22px 26px;
            margin-bottom: 26px;
            box-shadow: {p["shadow"]};
        }}
        .carbon-title-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
        }}
        .carbon-title {{
            font-size: 1rem;
            font-weight: 800;
            color: {p["text"]};
            letter-spacing: -0.01em;
        }}
        .carbon-sub {{
            font-size: 0.72rem;
            color: {p["muted"]};
            margin-top: 3px;
        }}
        .carbon-badge {{
            font-size: 0.64rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 5px 12px;
            border-radius: 999px;
            background: rgba(34,197,94,0.12);
            color: {p["success"]};
            border: 1px solid rgba(34,197,94,0.3);
        }}
        .carbon-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
        }}
        .c-stat-box {{
            background: {p["bg_soft"]};
            border: 1px solid {p["border_subtle"]};
            border-radius: 6px;
            padding: 16px 14px;
            text-align: left;
        }}
        .c-stat-label {{
            font-size: 0.64rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: {p["muted"]};
            margin-bottom: 8px;
        }}
        .c-stat-val {{
            font-size: 1.7rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: {p["text"]};
            line-height: 1;
            font-variant-numeric: tabular-nums;
        }}
        .c-stat-val.green {{ color: {p["success"]}; }}
        .c-stat-val.blue {{ color: {p["blue"]}; }}
        .c-stat-val.purple {{ color: {p["purple"]}; }}
        .c-stat-val.warn {{ color: {p["warn"]}; }}
        .c-unit {{
            font-size: 0.8rem;
            font-weight: 600;
            color: {p["muted"]};
        }}
        .c-stat-sub {{
            font-size: 0.62rem;
            color: {p["muted"]};
            margin-top: 6px;
        }}

        /* Animations */
        @keyframes pulseBeacon {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.3); opacity: 0.6; }}
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )
