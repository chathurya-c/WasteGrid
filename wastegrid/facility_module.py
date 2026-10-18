"""
Dynamic Facility Management Module for WasteGrid 2.0.
Supports unlimited database-backed processing facilities with full CRUD operations,
capacity updates, compatibility matrix adjustments, and live operational status toggling.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from wastegrid import db


def render_facility_management_page(palette):
    """Render the complete Facility Management dashboard and administration console."""
    p = palette

    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-left:4px solid {p["blue"]};
                    border-radius:8px; padding:18px 22px; margin-bottom:20px;">
            <div style="font-size:1.15rem; font-weight:800; color:{p["text"]};">🏭 Municipal Processing Facilities Management</div>
            <div style="font-size:0.75rem; color:{p["muted"]}; margin-top:4px;">
                Manage dynamic processing plants, biogas digesters, MRFs, and waste-to-energy facilities across the municipal grid.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    facilities = db.get_all_facilities(include_offline=True)
    if not facilities:
        st.warning("No facilities found in database.")
        return

    # 1. Facility KPI Metrics Row
    total_facs = len(facilities)
    online_facs = sum(1 for f in facilities if f["status"] == "online")
    total_cap_kg = sum(f["capacity_kg"] for f in facilities if f["status"] == "online")
    total_load_kg = sum(f["current_load_kg"] for f in facilities)
    overall_util = (total_load_kg / total_cap_kg * 100) if total_cap_kg > 0 else 0
    avg_eff = (
        sum(f.get("efficiency_pct", 95.0) for f in facilities) / total_facs
        if total_facs > 0
        else 0
    )

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="m-card"><div class="m-label">🏭 Total Plants</div><div class="m-value">{total_facs} Plants</div></div>
            <div class="m-card green"><div class="m-label">⚡ Online Capacity</div><div class="m-value">{total_cap_kg / 1000:.2f} Tons</div></div>
            <div class="m-card hero"><div class="m-label">📊 Current Grid Load</div><div class="m-value {"red" if overall_util > 90 else "green"}">{total_load_kg / 1000:.2f} Tons</div></div>
            <div class="m-card purple"><div class="m-label">✨ Avg Efficiency</div><div class="m-value">{avg_eff:.1f}%</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Interactive Facility Capacity vs Load Chart (Plotly)
    df_facs = pd.DataFrame(facilities)
    df_facs["Capacity (T)"] = df_facs["capacity_kg"] / 1000
    df_facs["Load (T)"] = df_facs["current_load_kg"] / 1000
    df_facs["Utilization %"] = df_facs.apply(
        lambda r: (
            (r["current_load_kg"] / r["capacity_kg"] * 100)
            if r["capacity_kg"] > 0
            else 0
        ),
        axis=1,
    )

    col_chart1, col_chart2 = st.columns([3, 2])
    with col_chart1:
        st.markdown(
            '<div class="sec-title">📊 Facility Capacity & Load Comparison</div>',
            unsafe_allow_html=True,
        )
        fig_bar = px.bar(
            df_facs,
            x="id",
            y=["Load (T)", "Capacity (T)"],
            barmode="group",
            title="Allocated Load vs Maximum Ceiling by Plant",
            color_discrete_sequence=[p["accent"], p["blue"]],
            labels={"value": "Tons (T)", "variable": "Metric", "id": "Facility ID"},
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=p["text"],
            margin=dict(l=10, r=10, t=35, b=10),
            height=280,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        st.markdown(
            '<div class="sec-title">🥧 Processing Technology Mix</div>',
            unsafe_allow_html=True,
        )
        fig_pie = px.pie(
            df_facs,
            names="type",
            values="capacity_kg",
            title="Capacity Share by Facility Type",
            color_discrete_sequence=[p["blue"], p["success"], p["purple"], p["warn"]],
            hole=0.45,
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=p["text"],
            margin=dict(l=10, r=10, t=35, b=10),
            height=280,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # 3. Live Facility Register Table
    st.markdown(
        '<div class="sec-title">📋 Active Municipal Facilities Directory</div>',
        unsafe_allow_html=True,
    )

    table_rows = []
    for f in facilities:
        fid = f["id"]
        stat = f["status"]
        if stat == "online":
            pill = '<span class="fc-pill safe">● Online</span>'
        elif stat == "maintenance":
            pill = '<span class="fc-pill overflow" style="background:rgba(245,158,11,0.15); color:#f59e0b;">🔧 Maintenance</span>'
        else:
            pill = '<span class="fc-pill overflow">🛑 Offline</span>'

        cap_t = f["capacity_kg"] / 1000
        load_t = f["current_load_kg"] / 1000
        util = (
            (f["current_load_kg"] / f["capacity_kg"] * 100)
            if f["capacity_kg"] > 0
            else 0
        )

        table_rows.append(
            f"""<tr>
                <td><b>Plant {fid}</b></td>
                <td><b>{f["name"]}</b></td>
                <td><code>{f["type"].upper()}</code></td>
                <td><span style="text-transform:uppercase; font-weight:700;">{f["accepts"]}</span></td>
                <td>{load_t:.2f} / {cap_t:.2f} T ({util:.1f}%)</td>
                <td>{f["distance_km"]} km</td>
                <td>{f.get("cost_per_ton", 350.0):.0f} ₹/T</td>
                <td>{f.get("efficiency_pct", 95.0):.1f}%</td>
                <td>{pill}</td>
            </tr>"""
        )

    st.markdown(
        f"""<div class="fc-table-wrap">
            <table class="fc-table">
                <thead><tr>
                    <th>ID</th><th>Facility Name</th><th>Technology Type</th><th>Accepts</th>
                    <th>Load / Capacity</th><th>Distance</th><th>Cost / Ton</th><th>Efficiency</th><th>Status</th>
                </tr></thead>
                <tbody>{"".join(table_rows)}</tbody>
            </table>
        </div>""",
        unsafe_allow_html=True,
    )

    # 4. Facility Management Controls (Add / Update / Outage Toggle)
    col_add, col_edit = st.columns([1, 1], gap="large")

    with col_add:
        st.markdown(
            '<div class="sec-title">➕ Commission New Facility</div>',
            unsafe_allow_html=True,
        )
        with st.form("add_facility_form"):
            new_id = (
                st.text_input("Facility Identifier (ID)", placeholder="e.g. F, G, H")
                .strip()
                .upper()
            )
            new_name = st.text_input(
                "Facility Display Name", placeholder="e.g. East Metro Compost Yard"
            )
            new_type = st.selectbox(
                "Facility Type",
                ["biocompost", "anaerobic_digester", "mrf", "waste_to_energy"],
            )
            new_accepts = st.selectbox("Accepted Stream", ["wet", "dry", "mixed"])
            new_cap = st.number_input(
                "Design Capacity (kg)",
                min_value=500.0,
                max_value=50000.0,
                value=2500.0,
                step=500.0,
            )
            new_dist = st.number_input(
                "Avg Distance from Center (km)",
                min_value=1.0,
                max_value=100.0,
                value=9.5,
                step=0.5,
            )
            new_lat = st.number_input("Latitude", value=12.9350, format="%.4f")
            new_lon = st.number_input("Longitude", value=77.6100, format="%.4f")
            new_hours = st.text_input("Operating Hours", value="06:00 - 22:00")
            new_cost = st.number_input(
                "Processing Cost per Ton (INR)",
                min_value=100.0,
                max_value=2000.0,
                value=320.0,
                step=10.0,
            )
            new_eff = st.number_input(
                "Efficiency Rating (%)",
                min_value=50.0,
                max_value=100.0,
                value=96.0,
                step=0.5,
            )

            btn_create = st.form_submit_button(
                "Commission Plant to Grid ➔", use_container_width=True
            )
            if btn_create:
                if new_id and new_name:
                    success, msg = db.add_facility(
                        new_id,
                        new_name,
                        new_type,
                        new_accepts,
                        new_cap,
                        new_dist,
                        new_lat,
                        new_lon,
                        new_hours,
                        new_eff,
                        new_cost,
                        0.04,
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please provide a valid facility ID and name.")

    with col_edit:
        st.markdown(
            '<div class="sec-title">⚙️ Update Facility Operational Parameters</div>',
            unsafe_allow_html=True,
        )
        fac_options = {
            f["id"]: f"{f['id']} - {f['name']} ({f['status'].upper()})"
            for f in facilities
        }
        selected_fid = st.selectbox(
            "Select Facility to Edit",
            list(fac_options.keys()),
            format_func=lambda x: fac_options[x],
        )

        selected_fac = next((f for f in facilities if f["id"] == selected_fid), None)
        if selected_fac:
            with st.form("edit_facility_form"):
                ed_name = st.text_input("Facility Name", value=selected_fac["name"])
                ed_type = st.selectbox(
                    "Facility Type",
                    ["biocompost", "anaerobic_digester", "mrf", "waste_to_energy"],
                    index=[
                        "biocompost",
                        "anaerobic_digester",
                        "mrf",
                        "waste_to_energy",
                    ].index(selected_fac.get("type", "biocompost")),
                )
                ed_accepts = st.selectbox(
                    "Accepts Stream",
                    ["wet", "dry", "mixed"],
                    index=["wet", "dry", "mixed"].index(
                        selected_fac.get("accepts", "wet")
                    ),
                )
                ed_cap = st.number_input(
                    "Capacity (kg)",
                    min_value=100.0,
                    max_value=100000.0,
                    value=float(selected_fac["capacity_kg"]),
                    step=500.0,
                )
                ed_status = st.selectbox(
                    "Operating Status",
                    ["online", "maintenance", "offline"],
                    index=["online", "maintenance", "offline"].index(
                        selected_fac.get("status", "online")
                    ),
                )
                ed_dist = st.number_input(
                    "Distance (km)",
                    min_value=0.5,
                    max_value=100.0,
                    value=float(selected_fac["distance_km"]),
                    step=0.5,
                )
                ed_cost = st.number_input(
                    "Cost per Ton (INR)",
                    min_value=50.0,
                    max_value=5000.0,
                    value=float(selected_fac.get("cost_per_ton", 350.0)),
                    step=10.0,
                )
                ed_eff = st.number_input(
                    "Efficiency %",
                    min_value=10.0,
                    max_value=100.0,
                    value=float(selected_fac.get("efficiency_pct", 95.0)),
                    step=0.5,
                )

                col_u1, col_u2 = st.columns([2, 1])
                with col_u1:
                    btn_update = st.form_submit_button(
                        "Save Parameter Changes", use_container_width=True
                    )
                with col_u2:
                    btn_del = st.form_submit_button(
                        "Decommission 🗑️", use_container_width=True
                    )

                if btn_update:
                    db.update_facility(
                        selected_fid,
                        ed_name,
                        ed_type,
                        ed_accepts,
                        ed_cap,
                        ed_status,
                        ed_dist,
                        ed_cost,
                        ed_eff,
                    )
                    st.success(f"Facility {selected_fid} updated successfully.")
                    st.rerun()

                if btn_del:
                    db.delete_facility(selected_fid)
                    st.warning(f"Facility {selected_fid} decommissioned from database.")
                    st.rerun()

    # 5. Factory Machinery & Hardware Units Management (Adding Extra Machines)
    st.markdown(
        '<div class="sec-title" style="margin-top:28px;">⚙️ Processing Plant Machinery & Hardware Units Management</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Add extra machines, trommels, shredders, or digester tanks to any plant. Installing a machine automatically increases that facility's intake capacity and updates the central LP optimization dispatch matrix."
    )

    machines = db.get_facility_machines()
    mach_col1, mach_col2 = st.columns([1.4, 1], gap="large")

    with mach_col1:
        if machines:
            m_rows = []
            for m in machines:
                stat_badge = (
                    '<span class="fc-pill safe">● Operational</span>'
                    if m.get("status") == "operational"
                    else '<span class="fc-pill overflow">🔧 Maintenance</span>'
                )
                m_rows.append(
                    f"""<tr>
                        <td><b>{m["machine_name"]}</b><br><span style="font-size:0.7rem; color:{p["muted"]};">Model: {m.get("model_number", "N/A")}</span></td>
                        <td><b>Plant {m["facility_id"]}</b><br><span style="font-size:0.7rem; color:{p["muted"]};">{m.get("facility_name", "")}</span></td>
                        <td><code>{m["machine_type"].upper()}</code></td>
                        <td><b style="color:{p["success"]};">+{m["capacity_kg_day"]:,.0f} kg/day</b></td>
                        <td>{m.get("power_kw", 45.0):.0f} kW</td>
                        <td>{stat_badge}</td>
                    </tr>"""
                )
            st.markdown(
                f"""<div class="fc-table-wrap">
                    <table class="fc-table">
                        <thead><tr>
                            <th>Machine Unit</th><th>Installed Plant</th><th>Category</th>
                            <th>Added Capacity</th><th>Power</th><th>Status</th>
                        </tr></thead>
                        <tbody>{"".join(m_rows)}</tbody>
                    </table>
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            st.info(
                "No auxiliary machinery registered yet. Use the installation form on the right to add a machine."
            )

    with mach_col2:
        st.markdown(
            f'<div style="font-size:0.9rem; font-weight:800; color:{p["text"]}; margin-bottom:8px;">➕ Install Extra Machine to Factory</div>',
            unsafe_allow_html=True,
        )
        with st.form("add_machine_form"):
            target_fac_id = st.selectbox(
                "Target Processing Plant",
                [f["id"] for f in facilities],
                format_func=lambda x: (
                    f"Plant {x} — {next((f['name'] for f in facilities if f['id'] == x), x)}"
                ),
                key="mach_target_fac",
            )
            m_name = st.text_input(
                "Machine Name", placeholder="e.g. Heavy-Duty Rotary Shredder Mark-IV"
            )
            m_type = st.selectbox(
                "Machine Technology Type",
                [
                    "shredder",
                    "digester",
                    "trommel",
                    "optical_sorter",
                    "baler",
                    "boiler",
                    "pelletizer",
                ],
            )
            m_model = st.text_input("Model / Serial No", placeholder="e.g. SH-400-PRO")
            m_cap = st.number_input(
                "Intake Capacity Contribution (kg/day)",
                min_value=100.0,
                max_value=25000.0,
                value=2000.0,
                step=250.0,
            )
            m_power = st.number_input(
                "Power Rating (kW)",
                min_value=5.0,
                max_value=500.0,
                value=45.0,
                step=5.0,
            )

            btn_add_mach = st.form_submit_button(
                "Install Machine & Expand Plant Capacity ➔",
                type="primary",
                use_container_width=True,
            )
            if btn_add_mach:
                if m_name.strip():
                    ok, msg = db.add_facility_machine(
                        target_fac_id,
                        m_name.strip(),
                        m_type,
                        m_model.strip(),
                        m_cap,
                        m_power,
                    )
                    if ok:
                        st.success(msg)
                        st.toast(
                            f"🎉 Machine added! Plant {target_fac_id} capacity increased by +{m_cap:,.0f} kg/day."
                        )
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please provide a valid machine name.")
