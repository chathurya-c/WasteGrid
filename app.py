import pandas as pd
import plotly.express as px
import streamlit as st

from wastegrid import (
    alert_engine,
    analytics_dashboards,
    analytics_module,
    auth,
    calendar_module,
    citizen_module,
    components,
    data,
    db,
    facility_module,
    forecast,
    map_module,
    optimizer,
    reports_module,
    settings_module,
    simulator_module,
    theme,
    vehicle_module,
)

# 1. Page Configuration (Full Widescreen Layout)
st.set_page_config(
    page_title="WasteGrid 2.0 — Smart Municipal Waste Management",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database schema and seed data
db.init_db()

# 2. Session State Initialization
defaults = {
    "event_active": False,
    "reoptimized": True,
    "theme": "light",
    "outage_facility": None,
    "nav_selection": "home",
    "show_auth_modal": False,
    "show_help": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# 3. Handle Special Action Query Parameters
if st.query_params.get("logout") == "1":
    if "logout" in st.query_params:
        del st.query_params["logout"]
    auth.logout()

if st.query_params.get("profile") == "1":
    if "profile" in st.query_params:
        del st.query_params["profile"]
    st.session_state["show_auth_modal"] = True

# Handle navigation via query params (e.g. ?nav=maps, ?nav=services, ?nav=settings)
req_nav = st.query_params.get("nav")
if req_nav:
    nav_map_aliases = {
        "maps": "map",
        "gis": "map",
        "live_maps": "map",
        "overview": "home",
        "dashboard": "home",
        "fleet": "fleet_ops",
        "citizen": "citizen_ops",
    }
    st.session_state["nav_selection"] = nav_map_aliases.get(req_nav, req_nav)

if st.query_params.get("alert_nav") == "1":
    st.session_state["nav_selection"] = "alerts"
    if "alert_nav" in st.query_params:
        del st.query_params["alert_nav"]

if st.query_params.get("footer_info"):
    st.session_state["footer_info_active"] = st.query_params.get("footer_info")
    if "footer_info" in st.query_params:
        del st.query_params["footer_info"]

if st.query_params.get("help") == "1":
    if "help" in st.query_params:
        del st.query_params["help"]
    st.session_state["show_help"] = True

# 4. Theme Resolution
param_theme = st.query_params.get("theme")
if param_theme in ["light", "dark"]:
    st.session_state.theme = param_theme
elif "theme" not in st.session_state or st.session_state.theme not in ["light", "dark"]:
    st.session_state.theme = "light"

# Always keep active theme and current dashboard in query params for reload persistence
st.query_params["theme"] = st.session_state.theme
st.query_params["nav"] = st.session_state.get("nav_selection", "home")
palette = theme.get_palette(st.session_state.theme)
theme.inject_css(palette)


def render_html(content):
    clean = "\n".join(
        line.strip() for line in str(content).strip().splitlines() if line.strip()
    )
    if hasattr(st, "html"):
        st.html(clean)
    else:
        st.markdown(clean, unsafe_allow_html=True)


# =========================================================================
# 5. Core Computational Grid Data
uploaded = st.session_state.get("csv_uploader")
if uploaded is not None:
    try:
        sources = data.load_sources_from_csv(uploaded)
        data_mode = "CSV Upload"
    except Exception:
        sources = data.SAMPLE_SOURCES
        data_mode = "Sample Baseline"
else:
    sources = data.SAMPLE_SOURCES
    data_mode = "Sample Baseline"

sources = data.apply_event_state(sources, st.session_state.event_active)
wet_total, dry_total, total_waste = data.totals(sources)

# Dynamic facilities from database
db_facilities = db.get_all_facilities(include_offline=True)
active_facilities = []
for f in db_facilities:
    fc = dict(f)
    if st.session_state.outage_facility == fc["id"]:
        fc["capacity_kg"] = 0
        fc["status"] = "offline"
    active_facilities.append(fc)

total_capacity = sum(
    f["capacity_kg"] for f in active_facilities if f.get("status") != "offline"
)
active_trucks_count = len(
    [
        v
        for v in db.get_all_vehicles()
        if v.get("status") in ["available", "in_transit", "assigned"]
    ]
)

# Optimization Calculation
if st.session_state.reoptimized:
    allocations, overflow = optimizer.optimize(active_facilities, wet_total, dry_total)
else:
    allocations = {}
    base_plan = {"A": 2000, "B": 1800, "C": 1400, "D": 2200, "E": 1200}
    for f in active_facilities:
        fid = f["id"]
        if f["capacity_kg"] <= 0 or f.get("status") == "offline":
            allocations[fid] = 0
        else:
            allocations[fid] = min(base_plan.get(fid, 1000), f["capacity_kg"])

    assigned_wet = (
        allocations.get("A", 0) + allocations.get("B", 0) + allocations.get("E", 0)
    )
    assigned_dry = allocations.get("C", 0) + allocations.get("D", 0)
    overflow = {}
    if wet_total > assigned_wet:
        overflow["wet"] = wet_total - assigned_wet
    if dry_total > assigned_dry:
        overflow["dry"] = dry_total - assigned_dry

st.session_state.allocations = allocations
st.session_state.overflow = overflow
total_overflow = optimizer.total_overflow(overflow)

# Synchronize predictive alerts
alert_engine.evaluate_and_sync_alerts()
pending_alert_count = alert_engine.get_pending_alert_count()

# Grid System Status Determination
if total_overflow > 0:
    system_status = "alert"
elif st.session_state.outage_facility or any(
    f.get("status") in ["offline", "maintenance"] for f in db_facilities
):
    system_status = "warn"
else:
    system_status = "optimal"

# 6. Current User and 5-Tenant Respective Sidebar Navigation
current_user = auth.get_current_user()
user_role = current_user.get("role") if current_user else None

# Core Base Navigation matching the hand-drawn wireframe
BASE_NAV = [
    ("🏠 Home", "home"),
    ("🛠️ Services", "services"),
    ("📅 Events", "events"),
    ("🗺️ Live Maps", "map"),
    ("🚨 Alerts", "alerts"),
]

# Build Respective Sidebar for Each of the 5 Tenants (Settings included in sidebar before logout)
if user_role in ["state", "state_authority"]:
    TENANT_NAV = BASE_NAV + [
        ("🏛️ State Policy", "state_policy"),
        ("📊 Statewide Reports", "reports"),
        ("⚙️ Settings", "settings"),
    ]
elif user_role == "commissioner":
    TENANT_NAV = BASE_NAV + [
        ("⚖️ Reallocation LP", "allocation_exec"),
        ("📈 Executive KPIs", "kpis_exec"),
        ("⚙️ Settings", "settings"),
    ]
elif user_role in ["waste_officer", "municipality"]:
    TENANT_NAV = BASE_NAV + [
        ("🚛 Fleet Telematics", "fleet_ops"),
        ("🗳️ Citizen Grievances", "citizen_ops"),
        ("⚙️ Settings", "settings"),
    ]
elif user_role in ["zonal_officer", "district"]:
    TENANT_NAV = BASE_NAV + [
        ("📍 Ward Blackspots", "ward_spots"),
        ("👥 Citizen Reports", "citizen_zonal"),
        ("⚙️ Settings", "settings"),
    ]
elif user_role in ["processing_facility", "recycling_facility", "factory"]:
    TENANT_NAV = BASE_NAV + [
        ("🏭 Plant Inflow", "plant_inflow"),
        ("♻️ Material Recovery", "recycling_ops"),
        ("⚙️ Settings", "settings"),
    ]
elif user_role == "truck_driver":
    TENANT_NAV = [
        ("📱 In-Cab MDT Terminal", "driver_in_cab"),
        ("🗺️ Live Route GPS", "driver_route"),
        ("⚖️ Weighbridge Pass", "driver_pass"),
        ("📢 Central Dispatch Alerts", "alerts"),
        ("⚙️ Settings", "settings"),
    ]
elif user_role == "admin":
    TENANT_NAV = BASE_NAV + [
        ("🛡️ User Governance", "users"),
        ("🧪 Simulator Sandbox", "simulator"),
        ("📑 Reports", "reports"),
        ("⚙️ Settings", "settings"),
    ]
else:
    # Public / Guest Visitor Navigation
    TENANT_NAV = BASE_NAV + [
        ("⚙️ Settings", "settings"),
    ]

# Map legacy nav keys if present
legacy_map = {
    "overview": "home",
    "operations": "map",
    "allocation": "services",
    "analytics": "reports",
    "alerts_citizen": "alerts",
    "admin_reports": "reports",
}
if st.session_state.nav_selection in legacy_map:
    st.session_state.nav_selection = legacy_map[st.session_state.nav_selection]

# 7. Left Sidebar Construction matching user hand-drawn wireframe
with st.sidebar:
    # Sidebar Header Brand
    logo_uri = theme.get_logo_data_uri()
    render_html(
        f"""
        <div style="display:flex; align-items:center; gap:12px; padding:6px 0 16px 0; border-bottom:1px solid {palette["border"]}; margin-bottom:16px;">
            <img src="{logo_uri}" alt="WasteGrid Logo" style="width:42px; height:42px; object-fit:contain; filter:drop-shadow(0 2px 6px rgba(0,0,0,0.18));" />
            <div>
                <div style="font-size:1.24rem; font-weight:900; color:{palette["text"]}; letter-spacing:-0.02em;">WasteGrid</div>
                <div style="font-size:0.65rem; color:{palette["muted"]}; letter-spacing:0.12em; text-transform:uppercase; font-weight:700;">Predict. Detect. Allocate.</div>
            </div>
        </div>
        """
    )

    # Active Tenant Badge if logged in
    if current_user:
        u_fname = (
            current_user.get("full_name") or current_user.get("username") or "Officer"
        )
        u_role_title = (
            current_user.get("authority_title")
            or str(current_user.get("role", "Authority")).title()
        )
        render_html(
            f"""
            <div style="background:{palette["bg_soft"]}; border:1px solid {palette["border"]}; border-radius:8px; padding:10px 12px; margin-bottom:14px; font-size:0.75rem;">
                <div style="font-weight:700; color:{palette["text"]}; display:flex; align-items:center; gap:6px;">
                    <span>👤</span> <span>{u_fname}</span>
                </div>
                <div style="font-size:0.68rem; color:{palette["blue"]}; font-weight:700; text-transform:uppercase; margin-top:3px;">
                    {u_role_title}
                </div>
            </div>
            """
        )

    # Clean Sidebar Navigation Buttons: Icon on Left, Name on Right, NO RADIO DOTS!
    for label, nav_key in TENANT_NAV:
        is_active = st.session_state.nav_selection == nav_key
        if st.button(
            label,
            key=f"sb_nav_btn_{nav_key}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            st.session_state.nav_selection = nav_key
            st.query_params["nav"] = nav_key
            st.rerun()

    # Bottom of Sidebar: When logged in, show Logout Icon with Logout under it, and NOTHING ELSE AFTER IT!
    if current_user:
        st.markdown(
            f"<div style='margin-top:18px; padding-top:12px; border-top:1px solid {palette['border']}; text-align:center;'></div>",
            unsafe_allow_html=True,
        )
        if st.button(
            "🚪\n\nLogout",
            key="btn_sb_logout_bottom",
            use_container_width=True,
            help="Sign out of WasteGrid",
        ):
            auth.logout()

# 8. Modals & Overlay Drawers
if st.session_state.get("show_auth_modal"):
    auth.render_auth_modal(palette)

if st.session_state.get("footer_info_active"):
    components.render_footer_info_modal(st.session_state["footer_info_active"], palette)

if st.session_state.get("show_help"):
    components.render_help_section(palette)

# 9. Top Navigation Bar (Logo on Left, Profile/Login on Right)
components.top_nav_bar(
    user=current_user,
    theme=st.session_state.theme,
    p=palette,
    alert_count=pending_alert_count,
    active_nav=st.session_state.nav_selection,
)

current_nav_key = st.session_state.get("nav_selection", "home")

# Guarantee that if not logged in, user is directly returned to Home Authority Dashboard
if not current_user and current_nav_key not in [
    "home",
    "services",
    "events",
    "map",
    "alerts",
    "settings",
    "overview",
]:
    current_nav_key = "home"
    st.session_state["nav_selection"] = "home"
    st.query_params["nav"] = "home"

# =========================================================================
# PAGE 1: HOME AUTHORITY DASHBOARD (INSPIRED BY WIREFRAME LAYOUT)
# =========================================================================
if current_nav_key in ["home", "overview"]:
    # 1. Executive Status / Welcome Banner
    if current_user:
        u_name = (
            current_user.get("full_name")
            or current_user.get("username")
            or "Authorized Officer"
        )
        u_role_text = current_user.get("authority_title") or "Municipal Authority"
        u_juris = current_user.get("jurisdiction") or "City Operations"
        render_html(
            f"""
            <div style="background:linear-gradient(135deg, rgba(2, 132, 199, 0.08) 0%, rgba(16, 185, 129, 0.08) 100%); 
                        border:1px solid rgba(2, 132, 199, 0.25); border-radius:10px; padding:12px 18px; margin-bottom:20px; 
                        display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.3rem;">📍</span>
                    <div>
                        <div style="font-size:0.85rem; font-weight:800; color:{palette["text"]};">
                            WasteGrid Municipal Authority Operations Command Center
                        </div>
                        <div style="font-size:0.74rem; color:{palette["muted"]}; margin-top:2px;">
                            Logged in as <b>{u_name}</b> ({u_role_text}) · Scope: <b>{u_juris}</b>
                        </div>
                    </div>
                </div>
                <span style="font-size:0.68rem; font-weight:700; background:rgba(16,185,129,0.15); color:{palette["success"]}; border:1px solid rgba(16,185,129,0.3); padding:4px 10px; border-radius:999px; text-transform:uppercase;">
                    ● Live Grid Authenticated
                </span>
            </div>
            """
        )
    else:
        render_html(
            f"""
            <div style="background:linear-gradient(135deg, rgba(2, 132, 199, 0.08) 0%, rgba(16, 185, 129, 0.08) 100%); 
                        border:1px solid rgba(2, 132, 199, 0.25); border-radius:10px; padding:12px 18px; margin-bottom:20px; 
                        display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.3rem;">🏛️</span>
                    <div>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="font-size:0.85rem; font-weight:800; color:{palette["text"]};">WasteGrid — Smart Municipal Solid-Waste Platform</span>
                            <span style="background:rgba(239, 68, 68, 0.12); color:#ef4444; border:1px solid rgba(239, 68, 68, 0.3); font-size:0.65rem; padding:1px 7px; border-radius:999px; font-weight:800; text-transform:uppercase;">🏆 Hackathon Pilot</span>
                        </div>
                        <div style="font-size:0.74rem; color:{palette["muted"]}; margin-top:2px;">
                            Predict. Detect. Allocate. · Official 5-Tenant Decision Support Architecture (Hackathon Demo)
                        </div>
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:0.72rem; color:{palette["muted"]};">Click the Profile icon <b>(P)</b> at top-right to sign in or view authority roles.</span>
                </div>
            </div>
            """
        )

    # Dedicated Role-Specific Dashboard for Each Official Authority Login
    if current_user:
        user_role = current_user.get("role", "municipality")
        if user_role == "truck_driver":
            vehicle_module.render_truck_driver_dashboard(palette, current_user)
        elif user_role == "admin":
            analytics_module.render_super_admin_view(
                palette, active_facilities, allocations, pending_alert_count
            )
        elif user_role in ["state", "state_authority"]:
            analytics_module.render_state_authority_view(palette)
        elif user_role == "commissioner":
            analytics_module.render_commissioner_view(palette, pending_alert_count)
        elif user_role in ["waste_officer", "municipality"]:
            analytics_module.render_waste_officer_view(palette, pending_alert_count)
        elif user_role in ["zonal_officer", "district"]:
            analytics_module.render_zonal_officer_view(palette)
        elif user_role in ["processing_facility", "factory"]:
            analytics_module.render_processing_facility_view(
                active_facilities, allocations, palette
            )
        elif user_role == "recycling_facility":
            analytics_module.render_recycling_facility_view(
                active_facilities, allocations, palette
            )
        else:
            analytics_module.render_municipal_office_view(palette, pending_alert_count)

        if user_role != "truck_driver":
            with st.expander(
                "🌐 RAW MUNICIPAL GRID ALLOCATION TELEMETRY & MULTI-STREAM FLOW",
                expanded=False,
            ):
                components.stream_breakdown(wet_total, dry_total, palette)
                components.facility_grid(
                    active_facilities,
                    allocations,
                    palette,
                    outage=st.session_state.outage_facility,
                )
                fixed_overflow = optimizer.fixed_allocation_overflow(
                    total_waste, total_capacity
                )
                components.comparison_cards(fixed_overflow, total_overflow, palette)
    else:
        # 3-Minute Demo Master Overview (Clean, Uncluttered, Executive)
        components.render_demo_overview(
            palette,
            sources,
            allocations,
            total_waste,
            total_capacity,
            active_facilities,
            active_trucks_count,
            pending_alert_count,
            total_overflow,
        )

# =========================================================================
# PAGE 2: SERVICES & SMART LP ALLOCATION
# =========================================================================
elif current_nav_key in ["services", "allocation"]:
    tab_opt, tab_esg, tab_sim, tab_facs = st.tabs(
        [
            "⚡ Multi-Objective LP Solver (Simplex)",
            "🌱 Carbon & ESG Scorecard",
            "🧪 Scenario Simulator Sandbox",
            "🏭 Facility Processing Nodes",
        ]
    )

    with tab_opt:
        optimizer.render_smart_allocation_page(palette, wet_total, dry_total)

    with tab_esg:
        wet_alloc = (
            allocations.get("A", 0) + allocations.get("B", 0) + allocations.get("E", 0)
        )
        dry_alloc = allocations.get("C", 0) + allocations.get("D", 0)
        analytics_module.render_carbon_scorecard(
            wet_alloc, dry_alloc, total_overflow, total_waste, palette
        )

    with tab_sim:
        simulator_module.render_scenario_simulator_page(palette, wet_total, dry_total)

    with tab_facs:
        facility_module.render_facility_management_page(palette)

# =========================================================================
# PAGE 3: EVENTS & HOLIDAY SURGE CALENDAR
# =========================================================================
elif current_nav_key == "events":
    tab_cal, tab_fc, tab_trends = st.tabs(
        [
            "📅 Municipal Event Calendar & Surge Register",
            "🔮 7-Day ML Forecast & Trend Dynamics",
            "📊 Ward-Level Generation Patterns",
        ]
    )

    with tab_cal:
        calendar_module.render_calendar_section(palette, total_capacity=total_capacity)

    with tab_fc:
        st.markdown(
            f"""
            <div style="background:{palette["card_bg"]}; border:1px solid {palette["border"]}; border-left:4px solid {palette["purple"]};
                        border-radius:8px; padding:18px 22px; margin-bottom:20px;">
                <div style="font-size:1.15rem; font-weight:800; color:{palette["text"]};">🔮 7-Day Predictive Waste Forecast & Capacity Ceilings</div>
                <div style="font-size:0.75rem; color:{palette["muted"]}; margin-top:4px;">
                    Calibrated on day-of-week commercial activity, residential weekend multipliers, and holiday event surges.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_fc1, col_fc2, col_fc3 = st.columns(3)
        with col_fc1:
            st.markdown(
                f"""<div class="m-card hero"><div class="m-label">📅 7-Day Cumulative Volume</div><div class="m-value">{(total_waste * 7.15) / 1000:.1f} T</div></div>""",
                unsafe_allow_html=True,
            )
        with col_fc2:
            st.markdown(
                """<div class="m-card"><div class="m-label">⚡ Peak Demand Surge Day</div><div class="m-value">Saturday (Weekend Peak)</div></div>""",
                unsafe_allow_html=True,
            )
        with col_fc3:
            st.markdown(
                f"""<div class="m-card green"><div class="m-label">🛡️ Minimum Reserve Margin</div><div class="m-value">{max(0, total_capacity - total_waste) / 1000:.2f} T Buffer</div></div>""",
                unsafe_allow_html=True,
            )

        forecast_rows = forecast.forecast_week(sources, total_capacity)
        forecast_df = pd.DataFrame(forecast_rows)
        components.forecast_section(forecast_df, palette)

    with tab_trends:
        st.markdown(
            '<div class="sec-title">📊 WARD-LEVEL PREDICTED GENERATION DYNAMICS</div>',
            unsafe_allow_html=True,
        )
        ward_fcs = []
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for s in sources:
            for d in days:
                mult = (
                    1.25
                    if d in ["Sat", "Sun"] and "house" in s["id"]
                    else (0.4 if d in ["Sat", "Sun"] and "office" in s["id"] else 1.0)
                )
                ward_fcs.append(
                    {
                        "Source": s["id"].upper(),
                        "Day": d,
                        "Waste (kg)": round(s["baseline_kg"] * mult),
                    }
                )
        df_wf = pd.DataFrame(ward_fcs)

        fig_w = px.bar(
            df_wf,
            x="Day",
            y="Waste (kg)",
            color="Source",
            barmode="stack",
            title="Projected Daily Generation by Municipal Source Stream",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_w.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=palette["text"],
            height=320,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_w, use_container_width=True)

# =========================================================================
# PAGE 4: LIVE MAP & FLEET TELEMATICS
# =========================================================================
elif current_nav_key in ["map", "operations"]:
    tab_map, tab_fleet, tab_facs = st.tabs(
        [
            "🗺️ Live GIS Waste Map & Heatmap",
            "🚚 Vehicle Tracking & Fleet Dispatch",
            "🏭 Facility Processing Nodes",
        ]
    )

    with tab_map:
        map_module.render_map_page(palette)

    with tab_fleet:
        vehicle_module.render_vehicle_tracking_page(palette)

    with tab_facs:
        facility_module.render_facility_management_page(palette)

# =========================================================================
# PAGE 4: ANALYTICS & 7-DAY FORECAST
# =========================================================================
elif current_nav_key == "analytics":
    tab_trends, tab_fc, tab_esg, tab_perf = st.tabs(
        [
            "📈 Waste Generation Trends",
            "🔮 7-Day ML Forecast",
            "🌱 Carbon & ESG Scorecard",
            "🏆 Municipal SLA Performance",
        ]
    )

    with tab_trends:
        analytics_dashboards.render_waste_analytics_page(palette)

    with tab_fc:
        st.markdown(
            f"""
            <div style="background:{palette["card_bg"]}; border:1px solid {palette["border"]}; border-left:4px solid {palette["purple"]};
                        border-radius:8px; padding:18px 22px; margin-bottom:20px;">
                <div style="font-size:1.15rem; font-weight:800; color:{palette["text"]};">🔮 7-Day Predictive Waste Forecast & Capacity Ceilings</div>
                <div style="font-size:0.75rem; color:{palette["muted"]}; margin-top:4px;">
                    Calibrated on day-of-week commercial activity, residential weekend multipliers, and holiday event surges.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_fc1, col_fc2, col_fc3 = st.columns(3)
        with col_fc1:
            st.markdown(
                f"""<div class="m-card hero"><div class="m-label">📅 7-Day Cumulative Volume</div><div class="m-value">{(total_waste * 7.15) / 1000:.1f} T</div></div>""",
                unsafe_allow_html=True,
            )
        with col_fc2:
            st.markdown(
                """<div class="m-card"><div class="m-label">⚡ Peak Demand Surge Day</div><div class="m-value">Saturday (Weekend Peak)</div></div>""",
                unsafe_allow_html=True,
            )
        with col_fc3:
            st.markdown(
                f"""<div class="m-card green"><div class="m-label">🛡️ Minimum Reserve Margin</div><div class="m-value">{max(0, total_capacity - total_waste) / 1000:.2f} T Buffer</div></div>""",
                unsafe_allow_html=True,
            )

        forecast_rows = forecast.forecast_week(sources, total_capacity)
        forecast_df = pd.DataFrame(forecast_rows)
        components.forecast_section(forecast_df, palette)

        st.markdown(
            '<div class="sec-title">📊 WARD-LEVEL PREDICTED GENERATION DYNAMICS</div>',
            unsafe_allow_html=True,
        )
        ward_fcs = []
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for s in sources:
            for d in days:
                mult = (
                    1.25
                    if d in ["Sat", "Sun"] and "house" in s["id"]
                    else (0.4 if d in ["Sat", "Sun"] and "office" in s["id"] else 1.0)
                )
                ward_fcs.append(
                    {
                        "Source": s["id"].upper(),
                        "Day": d,
                        "Waste (kg)": round(s["baseline_kg"] * mult),
                    }
                )
        df_wf = pd.DataFrame(ward_fcs)

        fig_w = px.bar(
            df_wf,
            x="Day",
            y="Waste (kg)",
            color="Source",
            barmode="stack",
            title="Projected Daily Generation by Municipal Source Stream",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_w.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=palette["text"],
            height=320,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_w, use_container_width=True)

    with tab_esg:
        wet_alloc = (
            allocations.get("A", 0) + allocations.get("B", 0) + allocations.get("E", 0)
        )
        dry_alloc = allocations.get("C", 0) + allocations.get("D", 0)
        analytics_module.render_carbon_scorecard(
            wet_alloc, dry_alloc, total_overflow, total_waste, palette
        )

    with tab_perf:
        analytics_dashboards.render_performance_dashboard_page(palette)

# =========================================================================
# PAGE 5: ALERTS & CITIZEN GRIEVANCES
# =========================================================================
elif current_nav_key in ["alerts", "alerts_citizen"]:
    tab_alerts, tab_citizen = st.tabs(
        [
            "🚨 Predictive Overflow Alerts",
            "📢 Citizen Grievance Portal & File Ticket",
        ]
    )

    with tab_alerts:
        alert_engine.render_alerts_dashboard(palette)

    with tab_citizen:
        citizen_module.render_citizen_reports_page(palette)

# =========================================================================
# PAGE 6: AUDITS, REPORTS & PERFORMANCE
# =========================================================================
elif current_nav_key in ["reports", "admin_reports"]:
    tab_rep, tab_trends, tab_perf = st.tabs(
        [
            "📑 Executive Reports & Excel Export",
            "📈 Waste Generation Trends & Analytics",
            "🏆 Municipal SLA Performance",
        ]
    )

    with tab_rep:
        reports_module.render_reports_page(palette)

    with tab_trends:
        analytics_dashboards.render_waste_analytics_page(palette)

    with tab_perf:
        analytics_dashboards.render_performance_dashboard_page(palette)

# =========================================================================
# PAGE 7: SETTINGS & GOVERNANCE
# =========================================================================
elif current_nav_key == "settings":
    tabs_list = [
        "⚙️ System Settings & Telemetry API",
        "📁 Data Ingestion & CSV Import",
        "👤 Account Profile & Security",
    ]
    if current_user and current_user.get("role") == "admin":
        tabs_list.append("👥 User Role Management (Admin)")

    st_tabs = st.tabs(tabs_list)
    with st_tabs[0]:
        settings_module.render_settings_page(palette)
    with st_tabs[1]:
        settings_module.render_data_ingestion_tab(palette)
    with st_tabs[2]:
        settings_module.render_profile_page(palette)
    if current_user and current_user.get("role") == "admin":
        with st_tabs[3]:
            analytics_dashboards.render_user_management_page(palette)

# =========================================================================
# TENANT-SPECIFIC CONSOLES
# =========================================================================
elif current_nav_key == "driver_in_cab":
    vehicle_module.render_truck_driver_dashboard(palette, current_user)

elif current_nav_key == "driver_route":
    vehicle_module.render_truck_driver_gps_route(palette, current_user)

elif current_nav_key == "driver_pass":
    vehicle_module.render_truck_driver_weighbridge_pass(palette, current_user)

elif current_nav_key == "state_policy":
    analytics_module.render_state_authority_view(palette)
    wet_alloc = (
        allocations.get("A", 0) + allocations.get("B", 0) + allocations.get("E", 0)
    )
    dry_alloc = allocations.get("C", 0) + allocations.get("D", 0)
    analytics_module.render_carbon_scorecard(
        wet_alloc, dry_alloc, total_overflow, total_waste, palette
    )

elif current_nav_key == "allocation_exec":
    optimizer.render_smart_allocation_page(palette, wet_total, dry_total)

elif current_nav_key == "kpis_exec":
    analytics_dashboards.render_performance_dashboard_page(palette)

elif current_nav_key == "fleet_ops":
    vehicle_module.render_vehicle_tracking_page(palette)

elif current_nav_key in ["citizen_ops", "citizen_zonal"]:
    citizen_module.render_citizen_reports_page(palette)

elif current_nav_key == "ward_spots":
    analytics_module.render_zonal_officer_view(palette)
    alert_engine.render_alerts_dashboard(palette)

elif current_nav_key == "plant_inflow":
    facility_module.render_facility_management_page(palette)

elif current_nav_key == "recycling_ops":
    analytics_module.render_recycling_facility_view(
        active_facilities, allocations, palette
    )

elif current_nav_key == "users":
    analytics_dashboards.render_user_management_page(palette)

elif current_nav_key == "simulator":
    simulator_module.render_scenario_simulator_page(palette, wet_total, dry_total)

# =========================================================================
# PAGE 8: LOGOUT
# =========================================================================
elif current_nav_key == "logout":
    auth.logout()

# =========================================================================
# PROFESSIONAL REAL WEBSITE FOOTER
# =========================================================================
components.website_footer(palette)
