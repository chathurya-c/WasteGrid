"""
Waste Analytics Dashboard, Performance Dashboard, and User Management for WasteGrid 2.0.
Features:
- Waste generation distribution & ward comparison analytics
- Plant efficiency, fleet turnaround, and citizen resolution performance scoring
- Administrative User Management and account governance console
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from wastegrid import db


def render_waste_analytics_page(palette):
    """Render the detailed Waste Analytics Dashboard."""
    p = palette
    sources = db.get_all_waste_sources()
    facilities = db.get_all_facilities(include_offline=True)

    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-left:4px solid {p["blue"]};
                    border-radius:8px; padding:18px 22px; margin-bottom:20px;">
            <div style="font-size:1.15rem; font-weight:800; color:{p["text"]};">📈 Municipal Waste Analytics & Stream Dynamics</div>
            <div style="font-size:0.75rem; color:{p["muted"]}; margin-top:4px;">
                In-depth municipal ward distribution, stream composition ratios, and generation vs processing capacity balances.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_sources = pd.DataFrame(sources)
    df_sources["Total (kg)"] = df_sources["baseline_kg"] + df_sources.get(
        "active_spike_kg", 0
    )

    # 1. KPIs
    tot_waste_kg = df_sources["Total (kg)"].sum()
    wet_kg = df_sources[df_sources["waste_type"] == "wet"]["Total (kg)"].sum()
    dry_kg = df_sources[df_sources["waste_type"] == "dry"]["Total (kg)"].sum()
    wet_pct = (wet_kg / tot_waste_kg * 100) if tot_waste_kg > 0 else 50
    dry_pct = 100 - wet_pct

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="m-card"><div class="m-label">📊 Total Generation</div><div class="m-value">{tot_waste_kg / 1000:.2f} Tons</div></div>
            <div class="m-card green"><div class="m-label">💧 Organic / Wet Stream</div><div class="m-value">{wet_kg / 1000:.2f} T ({wet_pct:.0f}%)</div></div>
            <div class="m-card purple"><div class="m-label">📦 Recyclable / Dry Stream</div><div class="m-value">{dry_kg / 1000:.2f} T ({dry_pct:.0f}%)</div></div>
            <div class="m-card hero"><div class="m-label">🏙️ Reporting Wards</div><div class="m-value">{len(df_sources)} Wards</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Charts Row
    col_c1, col_c2 = st.columns([1, 1])

    with col_c1:
        st.markdown(
            '<div class="sec-title">🥧 Waste Generation by Stream Composition</div>',
            unsafe_allow_html=True,
        )
        fig_donut = px.pie(
            df_sources,
            names="waste_type",
            values="Total (kg)",
            title="Wet vs Dry Material Split",
            color="waste_type",
            color_discrete_map={"wet": p["blue"], "dry": p["purple"]},
            hole=0.5,
        )
        fig_donut.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=p["text"],
            height=280,
            margin=dict(l=10, r=10, t=35, b=10),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_c2:
        st.markdown(
            '<div class="sec-title">📍 Ward & Zonal Comparison</div>',
            unsafe_allow_html=True,
        )
        fig_zone = px.bar(
            df_sources,
            x="zone",
            y="Total (kg)",
            color="waste_type",
            title="Waste Generation by Municipal Zone",
            color_discrete_map={"wet": p["blue"], "dry": p["purple"]},
            barmode="stack",
        )
        fig_zone.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=p["text"],
            height=280,
            margin=dict(l=10, r=10, t=35, b=10),
        )
        st.plotly_chart(fig_zone, use_container_width=True)

    # 3. Monthly Projection Trend (Plotly Area Chart)
    st.markdown(
        '<div class="sec-title">📅 30-Day Seasonal Waste Trend Projection</div>',
        unsafe_allow_html=True,
    )
    days = [f"Day {i}" for i in range(1, 31)]
    # Projected trend with weekend bumps
    import numpy as np

    base_arr = np.linspace(tot_waste_kg, tot_waste_kg * 1.15, 30)
    weekend_noise = [1.18 if i % 7 in [5, 6] else 1.0 for i in range(30)]
    proj_waste = base_arr * weekend_noise

    df_trend = pd.DataFrame({"Day": days, "Projected Waste (T)": proj_waste / 1000.0})
    fig_trend = px.area(
        df_trend,
        x="Day",
        y="Projected Waste (T)",
        title="30-Day Forward Demand Projection Curve",
        color_discrete_sequence=[p["blue"]],
    )
    fig_trend.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=p["text"],
        height=260,
        margin=dict(l=10, r=10, t=35, b=10),
    )
    st.plotly_chart(fig_trend, use_container_width=True)


def render_performance_dashboard_page(palette):
    """Render the Performance & SLA Compliance Dashboard."""
    p = palette
    facilities = db.get_all_facilities(include_offline=True)
    citizen_reports = db.get_all_citizen_reports()

    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-left:4px solid {p["success"]};
                    border-radius:8px; padding:18px 22px; margin-bottom:20px;">
            <div style="font-size:1.15rem; font-weight:800; color:{p["text"]};">🏆 Municipal Sanitation Performance & SLA Scorecard</div>
            <div style="font-size:0.75rem; color:{p["muted"]}; margin-top:4px;">
                Comprehensive operational ratings, facility uptime index, fleet turnaround SLA, and citizen redressal resolution efficiency.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tot_rep = len(citizen_reports)
    res_rep = sum(1 for r in citizen_reports if r["status"] == "resolved")
    sla_rate = (res_rep / tot_rep * 100) if tot_rep > 0 else 100.0
    avg_uptime = (
        sum(f.get("efficiency_pct", 95.0) for f in facilities) / len(facilities)
        if facilities
        else 95.0
    )

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="m-card green"><div class="m-label">⭐ Grid Performance Score</div><div class="m-value">94.8 / 100</div></div>
            <div class="m-card"><div class="m-label">🏭 Plant Uptime Rating</div><div class="m-value">{avg_uptime:.1f}%</div></div>
            <div class="m-card hero"><div class="m-label">⏱️ Grievance SLA Resolution</div><div class="m-value">{sla_rate:.1f}%</div></div>
            <div class="m-card purple"><div class="m-label">🚚 Fleet Route Adherence</div><div class="m-value">97.2%</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Facility Scores Table
    st.markdown(
        '<div class="sec-title">🏭 FACILITY PROCESSING PERFORMANCE MATRIX</div>',
        unsafe_allow_html=True,
    )
    f_rows = []
    for f in facilities:
        eff = f.get("efficiency_pct", 95.0)
        score_badge = (
            '<span class="fc-pill safe">A+ Exceeding</span>'
            if eff > 95
            else '<span class="fc-pill safe">A Standard</span>'
        )
        f_rows.append(
            f"""<tr>
                <td><b>Plant {f["id"]}</b></td>
                <td>{f["name"]}</td>
                <td>{f["type"].upper()}</td>
                <td>{eff:.1f}%</td>
                <td>{f.get("operating_hours", "06:00 - 22:00")}</td>
                <td>{score_badge}</td>
            </tr>"""
        )

    st.markdown(
        f"""<div class="fc-table-wrap">
            <table class="fc-table">
                <thead><tr><th>Plant ID</th><th>Plant Name</th><th>Technology</th><th>Efficiency Score</th><th>Operating SLA</th><th>Grade</th></tr></thead>
                <tbody>{"".join(f_rows)}</tbody>
            </table>
        </div>""",
        unsafe_allow_html=True,
    )


def render_user_management_page(palette):
    """Render User Management and Account Governance (Admin Only)."""
    p = palette
    users = db.get_all_users()

    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-left:4px solid {p["accent"]};
                    border-radius:8px; padding:18px 22px; margin-bottom:20px;">
            <div style="font-size:1.15rem; font-weight:800; color:{p["text"]};">👥 System User Management & Security Governance</div>
            <div style="font-size:0.75rem; color:{p["muted"]}; margin-top:4px;">
                Administrator console to create accounts, configure jurisdictional roles, toggle access, and maintain security audit logs.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Create New User Form
    with st.expander("➕ CREATE NEW OFFICIAL ACCOUNT", expanded=False):
        with st.form("create_user_form"):
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                new_uname = (
                    st.text_input("Username", placeholder="e.g. mysuru_admin")
                    .strip()
                    .lower()
                )
                new_pword = st.text_input("Initial Password", type="password")
                new_role = st.selectbox(
                    "Authority Role",
                    ["state", "district", "municipality", "factory", "admin"],
                )
                new_title = st.text_input(
                    "Authority Title",
                    placeholder="e.g. Mysuru City Corporation Administrator",
                )
            with col_u2:
                new_fname = st.text_input(
                    "Official Full Name", placeholder="e.g. Asha Ramesh"
                )
                new_email = st.text_input(
                    "Official Gov Email",
                    placeholder="e.g. asha.ramesh@smartcity.gov.in",
                )
                new_juris = st.text_input(
                    "Jurisdiction", placeholder="e.g. Urban Wards 1 to 65"
                )

            submit_u = st.form_submit_button(
                "Create Account ➔", use_container_width=True
            )
            if submit_u:
                if new_uname and new_pword and new_email:
                    success, msg = db.create_user(
                        new_uname,
                        new_pword,
                        new_role,
                        new_title,
                        new_juris,
                        new_fname,
                        new_email,
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill all required account fields.")

    # 2. Existing Users Directory Table
    st.markdown(
        '<div class="sec-title">📋 ACTIVE SYSTEM USER ACCOUNTS</div>',
        unsafe_allow_html=True,
    )
    u_rows = []
    for u in users:
        stat = (
            '<span style="color:#22c55e; font-weight:700;">Active</span>'
            if u["is_active"]
            else '<span style="color:#ef4444; font-weight:700;">Deactivated</span>'
        )
        last_log = u.get("last_login")[:19] if u.get("last_login") else "Never"
        u_rows.append(
            f"""<tr>
                <td><b>{u["id"]}</b></td>
                <td><b><code>{u["username"]}</code></b></td>
                <td>{u["full_name"]}</td>
                <td><code>{u["role"].upper()}</code></td>
                <td>{u["authority_title"]}</td>
                <td>{u["email"]}</td>
                <td>{last_log}</td>
                <td>{stat}</td>
            </tr>"""
        )

    st.markdown(
        f"""<div class="fc-table-wrap">
            <table class="fc-table">
                <thead><tr><th>#</th><th>Username</th><th>Full Name</th><th>Role</th><th>Authority Title</th><th>Email</th><th>Last Login</th><th>Status</th></tr></thead>
                <tbody>{"".join(u_rows)}</tbody>
            </table>
        </div>""",
        unsafe_allow_html=True,
    )

    # 3. User Activation & Password Reset Controls
    st.markdown(
        '<div class="sec-title">⚙️ ACCOUNT ACTION CONTROLS</div>',
        unsafe_allow_html=True,
    )
    col_act1, col_act2 = st.columns(2)

    with col_act1:
        u_options = {u["id"]: f"{u['username']} ({u['full_name']})" for u in users}
        sel_uid = st.selectbox(
            "Select Account", list(u_options.keys()), format_func=lambda x: u_options[x]
        )
        target_u = next((u for u in users if u["id"] == sel_uid), None)

        if target_u:
            new_state = not target_u["is_active"]
            btn_txt = (
                "Deactivate Account 🛑"
                if target_u["is_active"]
                else "Reactivate Account ✅"
            )
            if st.button(btn_txt, key=f"btn_toggle_u_{sel_uid}"):
                db.toggle_user_active(sel_uid, new_state)
                st.success(f"User {target_u['username']} status updated.")
                st.rerun()

    with col_act2:
        if target_u:
            with st.form("admin_reset_pwd_form"):
                admin_new_p = st.text_input(
                    "Reset Password for this User", type="password"
                )
                btn_reset = st.form_submit_button("Force Password Reset")
                if btn_reset:
                    if len(admin_new_p) >= 8:
                        db.update_user_password(target_u["username"], admin_new_p)
                        st.success(f"Password reset for {target_u['username']}!")
                    else:
                        st.warning("Password must be at least 8 characters.")
