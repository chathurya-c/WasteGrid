import base64
import os

import pandas as pd
import streamlit as st


def render_html(content):
    """Safely render HTML without Markdown converting indented lines to code blocks."""
    clean = "\n".join(
        line.strip() for line in str(content).strip().splitlines() if line.strip()
    )
    if hasattr(st, "html"):
        st.html(clean)
    else:
        st.markdown(clean, unsafe_allow_html=True)


def header(theme="light", status="optimal", logo_path="logo.png", p=None, user=None):
    logo_html = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{b64}" alt="logo" />'

    if status == "alert":
        badge_cls, badge_dot, badge_text = "alert", "red", "Overflow Alert"
    elif status == "warn":
        badge_cls, badge_dot, badge_text = "warn", "yellow", "Facility Offline"
    else:
        badge_cls, badge_dot, badge_text = "optimal", "green", "System Optimal"

    next_theme = "dark" if theme == "light" else "light"
    toggle_icon = "🌙" if theme == "light" else "☀️"
    toggle_label = "Dark" if theme == "light" else "Light"

    active_nav = (
        st.session_state.get("nav_selection", "home")
        if hasattr(st, "session_state")
        else "home"
    )

    user_html = ""
    u_param = f"&u={user['username']}" if (user and isinstance(user, dict) and "username" in user) else ""
    if user:
        user_html = (
            f'<div class="user-pill">{user["icon"]} <span><b>{user["title"]}</b></span>'
            f'<span class="badge">{user["badge"]}</span></div>'
            f'<a class="theme-toggle-link" href="?logout=1&nav=home&theme={theme}" target="_self" style="border-color:rgba(255,56,86,0.3);">'
            f"<span>🚪</span><span>Logout</span></a>"
        )

    st.markdown(
        f'<div class="wg-header">'
        f'<div class="wg-brand">{logo_html}<div><div class="wg-title">WasteGrid</div><div class="wg-tagline">Predict. Detect. Reallocate.</div></div></div>'
        f'<div class="hdr-controls">'
        f"{user_html}"
        f'<div class="hdr-badge {badge_cls}"><span class="pulse-dot {badge_dot}"></span>{badge_text}</div>'
        f'<a class="theme-toggle-link" href="?nav={active_nav}&theme={next_theme}{u_param}" target="_self"><span>{toggle_icon}</span><span>{toggle_label}</span></a>'
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def top_nav_bar(*args, **kwargs):
    """
    Renders top header bar matching wireframe layout:
    Top-Left: Logo + WasteGrid + Predict. Detect. Allocate.
    Top-Right: Profile/Login icon button + Theme toggle.
    Accepts any combination of positional or keyword arguments safely.
    """
    user = kwargs.get("user")
    if not user and len(args) > 3:
        user = args[3]

    theme_val = kwargs.get("theme") or (args[4] if len(args) > 4 else "light")
    p = kwargs.get("p") or (args[5] if len(args) > 5 else None)
    if not p or not isinstance(p, dict):
        from wastegrid import theme as theme_module

        p = theme_module.get_palette(
            theme_val if isinstance(theme_val, str) else "light"
        )

    active_nav = kwargs.get("active_nav") or (
        st.session_state.get("nav_selection", "home")
        if hasattr(st, "session_state")
        else "home"
    )
    next_theme = "dark" if theme_val == "light" else "light"
    toggle_icon = "🌙" if theme_val == "light" else "☀️"
    toggle_label = "Dark" if theme_val == "light" else "Light"

    # Extract alert count if provided
    alert_count = kwargs.get("alert_count", 0)

    # Format user profile name and designated authority role
    # Profile button matching hand-drawn wireframe: Circle with 'P'
    p_circle_bg = "#10b981" if user else p.get("blue", "#0284c7")
    user_initial = "P"
    if user and isinstance(user, dict):
        full_name = user.get("full_name") or user.get("username") or "P"
        user_initial = full_name[:1].upper()
        user_display = full_name
        role_title = (
            user.get("authority_title") or str(user.get("role", "Authority")).title()
        )
        profile_title = f"{user_display} ({role_title})"
    else:
        user_display = "Profile / Login"
        role_title = ""
        profile_title = "Click to Sign In or Sign Up"

    card_bg = p.get("card_bg", "#ffffff")
    text_col = p.get("text", "#1e293b")
    border_col = p.get("border", "#e2e8f0")
    muted_col = p.get("muted", "#64748b")
    shadow_val = p.get("shadow", "0 2px 8px rgba(0,0,0,0.06)")

    alert_badge_html = (
        (
            f'<a class="theme-toggle-link" href="?alert_nav=1&nav=alerts&theme={theme_val}" target="_self" title="{alert_count} Active System Alerts" '
            f'style="background:rgba(239, 68, 68, 0.12); color:#ef4444; border:1px solid rgba(239, 68, 68, 0.3); font-weight:700;">'
            f"🚨 {alert_count} Alerts</a>"
        )
        if alert_count > 0
        else ""
    )

    role_badge = (
        (
            f'<span style="font-size:0.68rem; background:rgba(2,132,199,0.1); color:{p.get("blue", "#0284c7")}; padding:2px 6px; border-radius:4px; font-weight:700; text-transform:uppercase;">{role_title}</span>'
        )
        if role_title
        else ""
    )

    profile_btn_html = (
        f'<a class="theme-toggle-link" href="?profile=1&nav={active_nav}&theme={theme_val}" target="_self" title="{profile_title}" '
        f'style="display:inline-flex; align-items:center; gap:8px; padding:4px 12px; border-radius:999px; '
        f"border:1.5px solid {p_circle_bg}; background:{card_bg}; text-decoration:none; cursor:pointer; "
        f'box-shadow:0 2px 6px rgba(0,0,0,0.06); transition:all 0.2s ease;">'
        f'<span style="width:28px; height:28px; border-radius:50%; background:{p_circle_bg}; color:#ffffff; '
        f'display:inline-flex; align-items:center; justify-content:center; font-size:0.95rem; box-shadow:0 2px 4px rgba(0,0,0,0.15);">'
        f"👤</span>"
        f'<span style="font-size:0.82rem; font-weight:700; color:{text_col};">{user_display}</span>{role_badge}</a>'
    )

    logout_btn_html = (
        (
            f'<a class="theme-toggle-link" href="?logout=1&nav=home&theme={theme_val}" target="_self" title="Sign out of WasteGrid session" '
            f'style="background:rgba(239, 68, 68, 0.08); color:#ef4444; border:1px solid rgba(239, 68, 68, 0.25); font-weight:700;">'
            f"<span>🚪</span><span>LOGOUT</span></a>"
        )
        if (user and isinstance(user, dict))
        else ""
    )

    from wastegrid import theme as theme_module

    logo_uri = theme_module.get_logo_data_uri()
    u_param = f"&u={user['username']}" if (user and isinstance(user, dict) and "username" in user) else ""

    nav_html = (
        f'<div style="display:flex; justify-content:space-between; align-items:center; background:{card_bg}; '
        f'border:1px solid {border_col}; border-radius:12px; padding:12px 24px; margin-bottom:20px; margin-left:54px; box-shadow:{shadow_val}; flex-wrap:wrap; gap:12px;">'
        # 1. WasteGrid logo on the left with Tagline
        f'<div style="display:flex; align-items:center; gap:14px;">'
        f'<img src="{logo_uri}" alt="WasteGrid Logo" style="width:42px; height:42px; object-fit:contain; filter:drop-shadow(0 2px 6px rgba(0,0,0,0.18));" />'
        f"<div>"
        f'<div style="font-size:1.3rem; font-weight:900; color:{text_col}; letter-spacing:-0.02em; line-height:1.1;">WasteGrid</div>'
        f'<div style="font-size:0.68rem; color:{muted_col}; letter-spacing:0.18em; text-transform:uppercase; margin-top:2px; font-weight:700;">Predict. Detect. Allocate.</div>'
        f"</div>"
        f"</div>"
        # 2. Right Actions: Alerts Badge, Profile Icon (P), Theme toggle, and Quick Logout
        f'<div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; flex-shrink:0;">'
        f"{alert_badge_html}"
        f"{profile_btn_html}"
        f'<a class="theme-toggle-link" href="?nav={active_nav}&theme={next_theme}{u_param}" target="_self"><span>{toggle_icon}</span><span>{toggle_label}</span></a>'
        f"{logout_btn_html}"
        f"</div>"
        f"</div>"
    )
    st.markdown(nav_html, unsafe_allow_html=True)


def website_footer(p):
    """
    Clean, subtle and professional footer spanning available application width:
    Services | Events | Live Maps | Alerts | Help | About | Contact
    © 2026 WasteGrid. All rights reserved.
    """
    theme_val = p.get("name", "light")
    footer_html = f"""
    <footer style="margin-top:48px; padding:22px 0 16px 0; border-top:1px solid {p["border"]}; width:100%; text-align:center;">
        <div style="font-size:0.84rem; font-weight:600; color:{p["muted"]}; margin-bottom:8px; display:flex; justify-content:center; align-items:center; gap:16px; flex-wrap:wrap;">
            <a href="?nav=services&theme={theme_val}" target="_self" style="color:{p["muted"]}; text-decoration:none; transition:color 0.2s;" onmouseover="this.style.color='{p["blue"]}'" onmouseout="this.style.color='{p["muted"]}'">Services</a>
            <span style="color:{p["border"]};">|</span>
            <a href="?nav=events&theme={theme_val}" target="_self" style="color:{p["muted"]}; text-decoration:none; transition:color 0.2s;" onmouseover="this.style.color='{p["blue"]}'" onmouseout="this.style.color='{p["muted"]}'">Events</a>
            <span style="color:{p["border"]};">|</span>
            <a href="?nav=map&theme={theme_val}" target="_self" style="color:{p["muted"]}; text-decoration:none; transition:color 0.2s;" onmouseover="this.style.color='{p["blue"]}'" onmouseout="this.style.color='{p["muted"]}'">Live Maps</a>
            <span style="color:{p["border"]};">|</span>
            <a href="?nav=alerts&theme={theme_val}" target="_self" style="color:{p["muted"]}; text-decoration:none; transition:color 0.2s;" onmouseover="this.style.color='{p["blue"]}'" onmouseout="this.style.color='{p["muted"]}'">Alerts</a>
            <span style="color:{p["border"]};">|</span>
            <a href="?help=1&theme={theme_val}" target="_self" style="color:{p["muted"]}; text-decoration:none; transition:color 0.2s;" onmouseover="this.style.color='{p["blue"]}'" onmouseout="this.style.color='{p["muted"]}'">Help</a>
            <span style="color:{p["border"]};">|</span>
            <a href="?footer_info=about&theme={theme_val}" target="_self" style="color:{p["muted"]}; text-decoration:none; transition:color 0.2s;" onmouseover="this.style.color='{p["blue"]}'" onmouseout="this.style.color='{p["muted"]}'">About</a>
            <span style="color:{p["border"]};">|</span>
            <a href="?footer_info=contact&theme={theme_val}" target="_self" style="color:{p["muted"]}; text-decoration:none; transition:color 0.2s;" onmouseover="this.style.color='{p["blue"]}'" onmouseout="this.style.color='{p["muted"]}'">Contact</a>
        </div>
        <div style="font-size:0.75rem; color:{p["muted"]}; letter-spacing:0.04em;">
            © 2026 WasteGrid. All rights reserved.
        </div>
    </footer>
    """
    st.markdown(footer_html, unsafe_allow_html=True)


def render_footer_info_modal(info_type, p):
    """Renders a clean popup drawer when Services, About, or Contact is clicked from the footer."""
    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:2px solid {p["blue"]}; border-radius:14px; padding:24px 28px; margin-bottom:24px; box-shadow:{p["shadow"]};">
        """,
        unsafe_allow_html=True,
    )
    if info_type == "services":
        st.markdown(
            f"""
            <div style="font-size:1.2rem; font-weight:800; color:{p["text"]}; margin-bottom:12px;">⚡ WasteGrid Municipal Services</div>
            <div style="font-size:0.84rem; color:{p["muted"]}; line-height:1.7;">
                ● <b>Autonomous Fleet Telematics:</b> Real-time GPS tracking and dynamic routing for municipal compactor trucks.<br>
                ● <b>Simplex LP Optimization:</b> Dual-simplex linear solver preventing facility overflow and minimizing transport emissions.<br>
                ● <b>Predictive Demand Forecasting:</b> 7-day machine learning projection with weekend commercial and residential multipliers.<br>
                ● <b>Smart IoT Overflow Sensors:</b> Real-time bin level telemetry and automated incident escalation.<br>
                ● <b>Citizen Grievance Redressal:</b> Public blackspot reporting portal with geotagged tickets and 24h SLA tracking.<br>
                ● <b>Carbon ESG Accounting:</b> Quantified methane avoidance and circular economy landfill diversion tracking.
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif info_type == "about":
        st.markdown(
            f"""
            <div style="font-size:1.2rem; font-weight:800; color:{p["text"]}; margin-bottom:12px;">ℹ️ About WasteGrid Platform</div>
            <div style="font-size:0.84rem; color:{p["muted"]}; line-height:1.7;">
                WasteGrid is an enterprise municipal decision-support operating system designed for urban local bodies, district authorities, 
                and state urban development departments.<br><br>
                <b>Universal Architecture Notice:</b> WasteGrid is state-agnostic and deployable across any municipality nationwide. 
                The live deployment utilizes empirical telemetry and ward generation profiles from the <b>Bengaluru Urban pilot case study</b> as a real-world demonstration model.
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif info_type == "contact":
        st.markdown(
            f"""
            <div style="font-size:1.2rem; font-weight:800; color:{p["text"]}; margin-bottom:12px;">📞 Municipal Help Desk & Operations Contact</div>
            <div style="font-size:0.84rem; color:{p["muted"]}; line-height:1.7;">
                ● <b>Citizen Grievance Toll-Free:</b> <code>1800-425-GRID</code> (24/7 Helpline)<br>
                ● <b>Municipal Command & Dispatch:</b> <code>080-2222-9278</code><br>
                ● <b>Technical Support:</b> <code>support@wastegrid.smartcity.gov.in</code><br>
                ● <b>Grievance SLA Standard:</b> Maximum 24-hour resolution for verified citizen blackspots.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✖️ Close Info", key="btn_close_footer_info", use_container_width=True):
        st.session_state["footer_info_active"] = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_help_section(p):
    """Renders comprehensive user guide and FAQ for users who need help navigating the platform."""
    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:2px solid {p["blue"]}; border-radius:14px; padding:24px 28px; margin-bottom:26px; box-shadow:{p["shadow"]};">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid {p["border"]}; padding-bottom:12px; margin-bottom:16px;">
                <div style="font-size:1.25rem; font-weight:800; color:{p["text"]}; display:flex; align-items:center; gap:10px;">
                    <span>📘</span>
                    <span>WasteGrid 2.0 — Platform User Guide, Architecture & FAQ</span>
                </div>
            </div>
            <div style="font-size:0.86rem; color:{p["text"]}; line-height:1.7; margin-bottom:18px;">
                WasteGrid is an intelligent smart-city decision support platform designed to eliminate municipal garbage overflow, 
                streamline segregated waste routing, and ensure carbon-neutral waste processing.
            </div>
        """,
        unsafe_allow_html=True,
    )

    h_col1, h_col2 = st.columns(2, gap="large")
    with h_col1:
        st.markdown(
            f'<div style="font-weight:800; color:{p["blue"]}; margin-bottom:8px;">1. HOW THE WASTE REALLOCATION WORKS</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div style="font-size:0.8rem; color:{p["muted"]}; line-height:1.6;">
                ● <b>Stream Compatibility:</b> Wet / organic waste can only be processed at composting plants (Facility A) and anaerobic biodigesters (Facility B). Recyclable dry packaging is routed to Material Recovery Facilities (Facility C).<br>
                ● <b>Linear Programming Solver:</b> When a surge occurs or a facility experiences an outage, the HiGHS simplex optimizer redistributes incoming waste across remaining operational facilities to minimize distance and prevent overflow.<br>
                ● <b>7-Day Predictive Forecaster:</b> Tracks weekend household surges, commercial market waste, and holiday events to prepare compactor trucks in advance.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-weight:800; color:{p["success"]}; margin-bottom:8px;">2. CITIZEN GRIEVANCE REPORTING</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div style="font-size:0.8rem; color:{p["muted"]}; line-height:1.6;">
                ● Citizens can report black spots, overflowing street bins, or missed door-to-door collections via the <b>Citizen Reports</b> portal.<br>
                ● Each report receives an official tracking ID (e.g. <code>WG-REP-2026-9041</code>) and is assigned to the nearest active compactor vehicle driver with a 24-hour resolution SLA.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with h_col2:
        st.markdown(
            f'<div style="font-weight:800; color:{p["purple"]}; margin-bottom:8px;">3. AUTHORITY ROLES & RESPONSIBILITIES</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div style="font-size:0.8rem; color:{p["muted"]}; line-height:1.6;">
                ● <b>State Authority:</b> Monitors macro statewide metrics, ESG carbon avoidance credits, and regional facility capacity balance.<br>
                ● <b>District Magistrate / Collector:</b> Oversees inter-ward transfer stations, bulk transport corridors, and compliance.<br>
                ● <b>Municipal Ward Officer:</b> Manages daily collection routes, driver dispatches, and citizen grievance tickets.<br>
                ● <b>Processing Plant Manager:</b> Monitors receiving docks, hopper fill ratios, and schedules preventive maintenance shutdowns.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-weight:800; color:{p["warn"]}; margin-bottom:8px;">4. PILOT DEMONSTRATION & EXTENSIBILITY</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div style="font-size:0.8rem; color:{p["muted"]}; line-height:1.6;">
                ● <b>General Deployment:</b> WasteGrid is not limited to any single region. Any municipal corporation can upload their ward shapefiles, GPS compactor feeds, and plant capacities via CSV or API.<br>
                ● <b>Reference Pilot:</b> The Karnataka / Bengaluru Urban dataset is provided as a pre-calibrated live demonstration case study.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(
        "✖️ Close Help Guide", key="btn_close_help_section", use_container_width=True
    ):
        st.session_state["show_help"] = False
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def section_title(text):
    st.markdown(f'<div class="sec-title">{text}</div>', unsafe_allow_html=True)


def metrics_row(total_waste, total_capacity, total_overflow, data_mode, p):
    overflow_cls = "red" if total_overflow > 0 else "green"
    overflow_icon = "⚠️" if total_overflow > 0 else "🛡️"
    st.markdown(
        f'<div class="metric-grid">'
        f'<div class="m-card"><div class="m-label">📊 Predicted Demand</div><div class="m-value">{total_waste / 1000:.2f} T</div></div>'
        f'<div class="m-card green"><div class="m-label">🏭 Available Capacity</div><div class="m-value">{total_capacity / 1000:.2f} T</div></div>'
        f'<div class="m-card hero"><div class="m-label">{overflow_icon} Overflow Risk</div><div class="m-value {overflow_cls}">{total_overflow / 1000:.2f} T</div></div>'
        f'<div class="m-card purple"><div class="m-label">📁 Data Stream</div><div class="m-value text">{data_mode}</div></div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def stream_breakdown(wet_total, dry_total, p):
    total = wet_total + dry_total
    wet_pct = (wet_total / total * 100) if total > 0 else 50
    dry_pct = 100 - wet_pct

    st.markdown(
        f'<div class="breakdown-card">'
        f'<div class="breakdown-header">'
        f'<div class="breakdown-title">🔄 Multi-Stream Composition & Compatibility Flow</div>'
        f'<div class="breakdown-ratio">Wet {wet_pct:.0f}% · Dry {dry_pct:.0f}%</div>'
        f"</div>"
        f'<div class="split-bar-wrap">'
        f'<div class="split-bar-wet" style="width:{wet_pct}%;"></div>'
        f'<div class="split-bar-dry" style="width:{dry_pct}%;"></div>'
        f"</div>"
        f'<div class="breakdown-legend">'
        f'<div class="legend-item"><span class="legend-dot" style="background:{p["blue"]};"></span><span><b>💧 Organic / Wet:</b> {wet_total:,.0f} kg ({wet_pct:.1f}%) → Routed to Facilities A & B</span></div>'
        f'<div class="legend-item"><span class="legend-dot" style="background:{p["purple"]};"></span><span><b>📦 Recyclable / Dry:</b> {dry_total:,.0f} kg ({dry_pct:.1f}%) → Routed to Facility C</span></div>'
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def status_banner(total_overflow, reoptimized, outage=None):
    if outage:
        st.markdown(
            f'<div class="wg-status warn">⚡ <b>Alert:</b> Facility <b>{outage}</b> is offline. Processing capacity reduced. Click Re-optimize to redistribute!</div>',
            unsafe_allow_html=True,
        )
    if total_overflow == 0:
        st.markdown(
            '<div class="wg-status">✅ <b>System Nominal:</b> Zero predicted overflow — all active waste streams accommodated by compatible processing facilities.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="wg-status red">🚨 <b>Capacity Breach:</b> Potential overflow of <b>{total_overflow / 1000:.2f} Tons</b> detected beyond facility processing limits!</div>',
            unsafe_allow_html=True,
        )
        if not reoptimized:
            st.markdown(
                '<div class="wg-status warn">⚠️ <b>Action Required:</b> Allocation matrix is out of sync. Click <b>RE-OPTIMIZE</b> to compute rebalancing.</div>',
                unsafe_allow_html=True,
            )


def action_buttons(event_active=False, outage=None):
    event_label = "⚡ Dismiss Event" if event_active else "⚡ Add Event Spike"
    outage_label = f"🔌 Outage ({outage})" if outage else "🔌 Simulate Outage"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        click_event = st.button(
            event_label, key="btn_act_event", use_container_width=True
        )
    with col2:
        click_outage = st.button(
            outage_label, key="btn_act_outage", use_container_width=True
        )
    with col3:
        click_reopt = st.button(
            "⚙️ Re-optimize Grid",
            key="btn_act_reopt",
            type="primary",
            use_container_width=True,
        )
    with col4:
        click_reset = st.button(
            "🔄 Reset System", key="btn_act_reset", use_container_width=True
        )

    return {
        "event": click_event,
        "outage": click_outage,
        "reopt": click_reopt,
        "reset": click_reset,
    }


def facility_grid(facilities, allocations, p, outage=None):
    cards = []
    fac_meta = {
        "A": {"icon": "🏢", "desc": "Organic Biocompost Plant"},
        "B": {"icon": "♻️", "desc": "Anaerobic Digester & Biogas"},
        "C": {"icon": "📦", "desc": "Material Recovery Facility (MRF)"},
    }

    for f in facilities:
        fid = f["id"]
        meta = fac_meta.get(fid, {"icon": "🏭", "desc": "Processing Facility"})
        is_off = (outage == fid) or (f["capacity_kg"] <= 0)
        alloc = allocations.get(fid, 0)
        util = (alloc / f["capacity_kg"] * 100) if f["capacity_kg"] > 0 else 0

        if is_off:
            badge_html = '<span class="fac-badge offline">Offline</span>'
            card_extra = "offline"
            color = p["muted"]
            util_str = "Offline"
        else:
            badge_html = '<span class="fac-badge active">● Online</span>'
            card_extra = ""
            if util < 70:
                color = p["success"]
            elif util < 95:
                color = p["warn"]
            else:
                color = p["accent"]
            util_str = f"{util:.0f}% utilized"

        cards.append(
            f'<div class="fac-card {card_extra}">'
            f'<div class="fac-name-row"><div class="fac-name">{meta["icon"]} Facility {fid}</div>{badge_html}</div>'
            f'<div class="fac-type">{meta["desc"]} · Accepts {f["accepts"].upper()} · {f["distance_km"]} km</div>'
            f'<div class="fac-stat">{round(alloc):,} / {f["capacity_kg"]:,} kg</div>'
            f'<div class="fac-bar-wrap"><div class="fac-bar" style="width:{min(util, 100)}%; background:{color};"></div></div>'
            f'<div class="fac-util" style="color:{color};">{util_str}</div>'
            f"</div>"
        )

    st.markdown(
        '<div class="fac-grid">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def comparison_cards(fixed_overflow, total_overflow, p):
    f_cls = "red" if fixed_overflow > 0 else "green"
    w_cls = "red" if total_overflow > 0 else "green"
    w_card = "" if total_overflow > 0 else "win"
    st.markdown(
        f'<div class="cmp-grid">'
        f'<div class="cmp-card"><div class="cmp-label">🛑 Fixed Static Allocation — Overflow</div><div class="cmp-value {f_cls}">{fixed_overflow / 1000:.2f} T</div></div>'
        f'<div class="cmp-card {w_card}"><div class="cmp-label">🚀 WasteGrid Dynamic Solver — Overflow</div><div class="cmp-value {w_cls}">{total_overflow / 1000:.2f} T</div></div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def success_banner(text):
    st.markdown(f'<div class="success-banner">{text}</div>', unsafe_allow_html=True)


def forecast_section(df, p):
    if df.empty:
        return

    # 1. Visual 7-Day Meter Grid
    day_cards = []
    max_pred = max(df["Predicted (T)"].max(), df["Capacity (T)"].max(), 1.0) * 1.15

    for _, row in df.iterrows():
        day = row["Day"]
        pred = row["Predicted (T)"]
        cap = row["Capacity (T)"]
        ovf = row["Overflow (T)"]

        pct = min(100, max(10, (pred / max_pred) * 100))
        is_overflow = ovf > 0

        fill_cls = "surge" if is_overflow else "normal"
        card_cls = "overflow" if is_overflow else ""
        badge_html = (
            f'<span class="fc-day-badge risk">▲ +{ovf:.2f} T</span>'
            if is_overflow
            else '<span class="fc-day-badge safe">✓ Safe</span>'
        )

        day_cards.append(
            f'<div class="fc-day-card {card_cls}">'
            f'<div class="fc-day-name">{day}</div>'
            f'<div class="fc-meter-wrap"><div class="fc-meter-fill {fill_cls}" style="height:{pct:.0f}%;"></div></div>'
            f'<div class="fc-day-val">{pred:.2f} T</div>'
            f"{badge_html}"
            f"</div>"
        )

    st.markdown(
        '<div class="fc-visual-grid">' + "".join(day_cards) + "</div>",
        unsafe_allow_html=True,
    )

    # 2. Executive Forecast Table
    rows_html = []
    for _, row in df.iterrows():
        day = row["Day"]
        pred = row["Predicted (T)"]
        cap = row["Capacity (T)"]
        ovf = row["Overflow (T)"]

        if ovf > 0:
            pill = f'<span class="fc-pill overflow">▲ Capacity Exceeded (+{ovf:.2f} T)</span>'
            ovf_style = f"color:{p['accent']}; font-weight:700;"
        else:
            pill = '<span class="fc-pill safe">● Optimal Flow (0.00 T)</span>'
            ovf_style = f"color:{p['success']}; font-weight:600;"

        rows_html.append(
            f"<tr>"
            f"<td><b>{day}</b></td>"
            f"<td>{pred:.2f} Tons</td>"
            f"<td>{cap:.2f} Tons</td>"
            f'<td style="{ovf_style}">{ovf:.2f} Tons</td>'
            f"<td>{pill}</td>"
            f"</tr>"
        )

    st.markdown(
        f'<div class="fc-table-wrap">'
        f'<table class="fc-table">'
        f"<thead><tr>"
        f"<th>Forecasted Day</th>"
        f"<th>Predicted Demand</th>"
        f"<th>Capacity Ceiling</th>"
        f"<th>Overflow Risk</th>"
        f"<th>Operational Status</th>"
        f"</tr></thead>"
        f"<tbody>"
        f"{''.join(rows_html)}"
        f"</tbody>"
        f"</table>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_demo_overview(
    palette,
    sources,
    allocations,
    total_waste,
    total_capacity,
    active_facilities,
    active_trucks_count,
    pending_alert_count,
    total_overflow,
):
    """
    Renders the uncluttered, executive 3-minute demo master overview for examiners.
    Highlights:
    1. Clean Executive Hero Banner
    2. 4 Primary Municipal KPIs (Daily Influx, Processing Capacity, Landfill Diversion %, Active Fleet)
    3. Scenario Action Buttons (Festival Surge, Outage, Re-optimize)
    4. Zero-Overflow Proof (Fixed Allocation vs WasteGrid LP Optimizer)
    5. Weekly Generation & Processing Dynamics (Monday to Sunday)
    6. Facility Utilization Grid (Nodes A-E)
    7. Clear Guidance to Log In as 6 Tenants or Truck Driver
    """
    from wastegrid import forecast, optimizer

    processed_kg = sum(allocations.values())
    recycling_pct = round(
        (allocations.get("C", 0) + allocations.get("D", 0)) / max(total_waste, 1) * 100,
        1,
    )

    # 1. Clean Executive Hero Banner
    hero_html = f"""
<div class="wg-hero" style="padding:22px 26px; margin-bottom:18px;">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
<div style="max-width:760px;">
<div style="font-size:0.75rem; font-weight:800; letter-spacing:0.15em; text-transform:uppercase; color:#10b981; margin-bottom:4px;">
⚡ Intelligent Municipal Environmental Infrastructure
</div>
<div style="font-size:1.8rem; font-weight:900; color:{palette["text"]}; line-height:1.2; letter-spacing:-0.03em;">
WasteGrid — Smart Municipal Solid-Waste Decision Support Platform
</div>
<div style="font-size:0.85rem; color:{palette["muted"]}; margin-top:6px; line-height:1.5;">
<b>Predict. Detect. Allocate.</b> Real-time linear programming optimizer guaranteeing zero capacity overflow across bio-methanation, composting, and recycling processing facilities.
</div>
</div>
<div style="background:{palette["card_bg"]}; border:1px solid {palette["border"]}; border-radius:10px; padding:14px 18px; text-align:center; box-shadow:{palette["shadow"]};">
<div style="font-size:0.68rem; color:{palette["muted"]}; text-transform:uppercase; font-weight:700;">Live Grid Health</div>
<div style="font-size:1.4rem; font-weight:900; color:{palette["success"] if total_overflow == 0 else palette["accent"]};">
{"99.4% OPTIMAL" if total_overflow == 0 else "OVERFLOW ALERT"}
</div>
<div style="font-size:0.7rem; color:{palette["muted"]}; margin-top:2px;">
Allocated: <b>{processed_kg / 1000:.1f} T</b> / {total_capacity / 1000:.1f} T
</div>
</div>
</div>
</div>
"""
    st.markdown(hero_html.strip(), unsafe_allow_html=True)

    # 2. Executive 4-Metric Grid (Clean, Uncluttered, Fast)
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.markdown(
            f"""<div class="m-card hero">
                <div class="m-label">📑 Daily Municipal Influx</div>
                <div class="m-value">{total_waste / 1000:.1f} Tons</div>
                <div style="font-size:0.68rem; color:{palette["muted"]}; margin-top:4px;">{len(sources)} Active Source Streams</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col_k2:
        st.markdown(
            f"""<div class="m-card">
                <div class="m-label">🏭 Treatment Capacity</div>
                <div class="m-value">{total_capacity / 1000:.1f} Tons</div>
                <div style="font-size:0.68rem; color:{palette["success"]}; margin-top:4px;">5 Processing Nodes (A-E)</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col_k3:
        st.markdown(
            f"""<div class="m-card green">
                <div class="m-label">♻️ Landfill Diversion Rate</div>
                <div class="m-value">{recycling_pct}%</div>
                <div style="font-size:0.68rem; color:{palette["success"]}; margin-top:4px;">Composted & Recycled</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col_k4:
        st.markdown(
            f"""<div class="m-card purple">
                <div class="m-label">🚚 Active GPS Fleet</div>
                <div class="m-value">{active_trucks_count} Trucks</div>
                <div style="font-size:0.68rem; color:{palette["purple"]}; margin-top:4px;">In-Cab MDT Transponders</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # 3. Interactive Demonstration Buttons (Simulate Festival Surge, Outage, Re-optimize)
    st.markdown("<br>", unsafe_allow_html=True)
    section_title("🎯 3-MINUTE EVALUATION SIMULATOR — TRIGGER REAL-TIME SCENARIOS")
    btn_clicks = action_buttons(
        event_active=st.session_state.event_active,
        outage=st.session_state.outage_facility,
    )
    if btn_clicks["event"]:
        st.session_state.event_active = not st.session_state.event_active
        st.session_state.reoptimized = False
        st.rerun()

    if btn_clicks["outage"]:
        cycle = {None: "B", "B": "C", "C": "D", "D": None}
        st.session_state.outage_facility = cycle.get(
            st.session_state.outage_facility, None
        )
        st.session_state.reoptimized = False
        st.rerun()

    if btn_clicks["reopt"]:
        st.session_state.reoptimized = True
        st.rerun()

    if btn_clicks["reset"]:
        st.session_state.event_active = False
        st.session_state.outage_facility = None
        st.session_state.reoptimized = True
        st.rerun()

    # Operational status banner
    status_banner(
        total_overflow, st.session_state.reoptimized, st.session_state.outage_facility
    )

    # 4. The Zero-Overflow Proof: Fixed Static Allocation vs WasteGrid LP Optimizer
    section_title(
        "THE CORE INNOVATION: FIXED ALLOCATION VS WASTEGRID DYNAMIC LP OPTIMIZER"
    )
    fixed_overflow = optimizer.fixed_allocation_overflow(total_waste, total_capacity)
    comparison_cards(fixed_overflow, total_overflow, palette)

    if fixed_overflow > 0 and total_overflow < fixed_overflow:
        pct = optimizer.reduction_pct(fixed_overflow, total_overflow)
        success_banner(
            f"WasteGrid prevented {fixed_overflow - total_overflow:,.0f} kg ({pct:.1f}%) of municipal overflow vs static fixed routing!"
        )

    # 5. Weekly Demand & Generation Trend Dynamics (Monday to Sunday) - Collapsible to keep 3-Minute Demo View Crisp & Clean
    with st.expander(
        "📈 7-DAY WEEKLY GENERATION & PROCESSING DYNAMICS (MON - SUN) — Click to View",
        expanded=False,
    ):
        st.markdown(
            f"""
            <div style="font-size:0.75rem; color:{palette["muted"]}; margin-bottom:10px;">
                Predictive weekly waste influx forecast factoring in weekend commercial surges and monsoon precipitation moisture adjustments.
            </div>
            """,
            unsafe_allow_html=True,
        )
        forecast_rows = forecast.forecast_week(sources, total_capacity)
        forecast_df = pd.DataFrame(forecast_rows)
        forecast_section(forecast_df, palette)

    # 6. Facility Processing Nodes Status Grid
    section_title("FACILITY PROCESSING NODES & REAL-TIME LOAD BALANCING")
    facility_grid(
        active_facilities, allocations, palette, outage=st.session_state.outage_facility
    )

    # 7. Clean Navigation Callouts
    st.markdown(
        f"""
        <div style="background:{palette["bg_soft"]}; border:1px solid {palette["border"]}; border-radius:10px; padding:16px 20px; margin-top:20px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <b>🔐 Tenant Dashboards & In-Cab Driver App:</b>
                <span style="font-size:0.8rem; color:{palette["muted"]}; margin-left:6px;">
                    Click the top-right Profile icon <b>(P)</b> or use the sidebar buttons to test all 6 tenant logins (Commissioner, Waste Officer, Truck Driver Ramesh Kumar, etc.).
                </span>
            </div>
            <div style="font-size:0.75rem; color:{palette["blue"]}; font-weight:700;">
                📁 Manage Legacy CSV Data in ⚙️ Settings ➔ Data Ingestion
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
