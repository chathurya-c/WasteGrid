"""
Citizen Waste Reporting and Municipal Resolution Console for WasteGrid 2.0.
Supports civic complaint logging and municipal action workflows:
- Public Citizen Complaint Submission (overflowing bins, illegal dumping, missed collection, segregation issues)
- Unique Ticket Tracking ID generation
- Municipal Review & Dispatch Console (assign to compactor truck, mark in-progress/resolved)
- Resolution audit notes and citizen status lookup
"""

import streamlit as st

from wastegrid import db


def render_citizen_reports_page(palette):
    """Render the Citizen Reporting Portal & Municipal Grievance Redressal Console."""
    p = palette

    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-left:4px solid #10b981;
                    border-radius:8px; padding:18px 22px; margin-bottom:20px;">
            <div style="font-size:1.15rem; font-weight:800; color:{p["text"]};">📢 Citizen Waste Grievance & Municipal Redressal Portal</div>
            <div style="font-size:0.75rem; color:{p["muted"]}; margin-top:4px;">
                Empowering citizens to report sanitation bottlenecks and enabling municipal sanitation officers to dispatch rapid-response units.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_submit, tab_admin, tab_track = st.tabs(
        [
            "📝 Submit Sanitation Report",
            "👮 Municipal Resolution Console",
            "🔍 Track Grievance Status",
        ]
    )

    # =========================================================================
    # TAB 1: SUBMIT NEW CITIZEN REPORT
    # =========================================================================
    with tab_submit:
        st.markdown(
            '<div class="sec-title">📝 LODGE A PUBLIC SANITATION INCIDENT</div>',
            unsafe_allow_html=True,
        )

        with st.form("citizen_report_form"):
            col1, col2 = st.columns(2)
            with col1:
                cat = st.selectbox(
                    "Grievance Category",
                    [
                        "overflowing_bin",
                        "illegal_dumping",
                        "missed_collection",
                        "segregation_issue",
                    ],
                    format_func=lambda x: {
                        "overflowing_bin": "🗑️ Overflowing Garbage Dumpster / Bin",
                        "illegal_dumping": "🚫 Illegal Roadside / Plot Dumping",
                        "missed_collection": "🚚 Missed Door-to-Door Collection",
                        "segregation_issue": "⚠️ Waste Segregation Violation",
                    }[x],
                )
                loc_name = st.text_input(
                    "Exact Location / Landmark",
                    placeholder="e.g. Near 12th Main Junction, Indiranagar",
                )
                ward = st.text_input(
                    "Ward Number / Area", placeholder="e.g. WARD-112 (Domlur)"
                )

            with col2:
                c_name = st.text_input(
                    "Citizen Full Name", placeholder="e.g. Ramesh Hegde"
                )
                c_phone = st.text_input(
                    "Contact Mobile Phone", placeholder="+91 98450 XXXXX"
                )
                photo_file = st.file_uploader(
                    "Attach Incident Photo (Optional)", type=["jpg", "png", "jpeg"]
                )

            desc = st.text_area(
                "Detailed Incident Description",
                placeholder="Describe the severity, duration, and accessibility of the waste accumulation...",
            )
            submit_report = st.form_submit_button(
                "Lodge Official Grievance ➔", use_container_width=True
            )

            if submit_report:
                if loc_name and desc:
                    photo_name = photo_file.name if photo_file else None
                    tracking_id = db.add_citizen_report(
                        cat,
                        desc,
                        loc_name,
                        ward or "WARD-01",
                        12.9716,
                        77.5946,
                        photo_name,
                        c_name or "Anonymous Citizen",
                        c_phone or "N/A",
                    )
                    st.success(
                        f"✅ Grievance officially lodged! Your tracking ticket number is: **`{tracking_id}`**"
                    )
                    st.info(
                        "Save this ticket ID to monitor dispatch resolution progress."
                    )
                else:
                    st.warning(
                        "Please provide both a location landmark and detailed description."
                    )

    # =========================================================================
    # TAB 2: MUNICIPAL RESOLUTION CONSOLE (ADMIN)
    # =========================================================================
    with tab_admin:
        all_reports = db.get_all_citizen_reports()
        vehicles = db.get_all_vehicles()
        truck_options = [f"{v['id']} ({v['driver_name']})" for v in vehicles]

        # KPIs
        tot_rep = len(all_reports)
        sub_count = sum(1 for r in all_reports if r["status"] == "submitted")
        prog_count = sum(1 for r in all_reports if r["status"] == "in_progress")
        res_count = sum(1 for r in all_reports if r["status"] == "resolved")

        st.markdown(
            f"""
            <div class="metric-grid">
                <div class="m-card"><div class="m-label">📑 Total Reports</div><div class="m-value">{tot_rep}</div></div>
                <div class="m-card hero"><div class="m-label">🚨 Needs Action</div><div class="m-value {"red" if sub_count > 0 else "green"}">{sub_count}</div></div>
                <div class="m-card"><div class="m-label">🚚 In Progress</div><div class="m-value warn">{prog_count}</div></div>
                <div class="m-card green"><div class="m-label">✓ Resolved</div><div class="m-value">{res_count}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Filters
        c_filter1, c_filter2 = st.columns([1, 1])
        with c_filter1:
            stat_filter = st.selectbox(
                "Status Filter",
                ["all", "submitted", "in_progress", "resolved", "rejected"],
            )
        with c_filter2:
            cat_filter = st.selectbox(
                "Category Filter",
                [
                    "all",
                    "overflowing_bin",
                    "illegal_dumping",
                    "missed_collection",
                    "segregation_issue",
                ],
            )

        displayed_reports = all_reports
        if stat_filter != "all":
            displayed_reports = [
                r for r in displayed_reports if r["status"] == stat_filter
            ]
        if cat_filter != "all":
            displayed_reports = [
                r for r in displayed_reports if r["category"] == cat_filter
            ]

        st.markdown(
            '<div class="sec-title">📋 ACTIVE CITIZEN GRIEVANCE TICKETS</div>',
            unsafe_allow_html=True,
        )

        for rep in displayed_reports:
            rid = rep["id"]
            stat = rep["status"]
            stat_color = (
                "#ef4444"
                if stat == "submitted"
                else ("#f59e0b" if stat == "in_progress" else "#22c55e")
            )
            category_title = rep["category"].replace("_", " ").title()

            st.markdown(
                f"""
                <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-left:5px solid {stat_color};
                            border-radius:8px; padding:16px 20px; margin-bottom:14px; box-shadow:{p["shadow"]};">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <div><b><code>{rep["tracking_id"]}</code></b> · <span style="font-size:0.8rem; font-weight:700;">{category_title}</span></div>
                        <div style="font-size:0.75rem; font-weight:700; color:{stat_color}; text-transform:uppercase;">● {stat}</div>
                    </div>
                    <div style="font-size:0.85rem; color:{p["text"]}; margin-bottom:6px;">
                        <b>Location:</b> {rep["location_name"]} (Ward: {rep["ward"]})
                    </div>
                    <div style="font-size:0.8rem; color:{p["muted"]}; margin-bottom:10px;">
                        {rep["description"]}
                    </div>
                    <div style="font-size:0.75rem; color:{p["muted"]};">
                        Reported by: <b>{rep["citizen_name"]}</b> ({rep["citizen_phone"]}) on {rep["reported_at"][:19]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Admin Management Actions per Ticket
            if stat != "resolved":
                with st.expander(
                    f"⚙️ Resolve / Assign Ticket #{rep['tracking_id']}", expanded=False
                ):
                    col_u1, col_u2 = st.columns(2)
                    with col_u1:
                        assign_truck = st.selectbox(
                            "Assign Response Vehicle",
                            truck_options,
                            key=f"asstrk_{rid}",
                        )
                        new_stat = st.selectbox(
                            "Update Status",
                            ["in_progress", "resolved", "rejected"],
                            key=f"nstat_{rid}",
                        )
                    with col_u2:
                        res_notes = st.text_input(
                            "Operational Action Note",
                            placeholder="e.g. Cleared by compactor crew",
                            key=f"rnotes_{rid}",
                        )
                        if st.button("Update Grievance ➔", key=f"btn_upd_{rid}"):
                            db.update_citizen_report_status(
                                rid,
                                new_stat,
                                assigned_to=assign_truck,
                                resolution_notes=res_notes,
                            )
                            st.success(
                                f"Ticket {rep['tracking_id']} updated to {new_stat.upper()}!"
                            )
                            st.rerun()

    # =========================================================================
    # TAB 3: TRACK GRIEVANCE STATUS (CITIZEN LOOKUP)
    # =========================================================================
    with tab_track:
        st.markdown(
            '<div class="sec-title">🔍 REAL-TIME CITIZEN TICKET TRACKER</div>',
            unsafe_allow_html=True,
        )
        search_id = (
            st.text_input("Enter your Ticket ID", placeholder="e.g. WG-REP-2026-9041")
            .strip()
            .upper()
        )

        if search_id:
            reports_match = [
                r
                for r in db.get_all_citizen_reports()
                if r["tracking_id"].upper() == search_id
            ]
            if reports_match:
                match = reports_match[0]
                m_stat = match["status"]
                m_col = (
                    "#ef4444"
                    if m_stat == "submitted"
                    else ("#f59e0b" if m_stat == "in_progress" else "#22c55e")
                )
                st.markdown(
                    f"""
                    <div style="background:{p["card_bg"]}; border:2px solid {m_col}; border-radius:10px; padding:22px; margin-top:14px;">
                        <div style="font-size:1.1rem; font-weight:800; color:{m_col}; margin-bottom:8px;">
                            STATUS: {m_stat.upper()}
                        </div>
                        <div style="font-size:0.85rem; color:{p["text"]}; line-height:1.6;">
                            <b>Ticket Reference:</b> <code>{match["tracking_id"]}</code><br>
                            <b>Category:</b> {match["category"].replace("_", " ").title()}<br>
                            <b>Location:</b> {match["location_name"]} (Ward: {match["ward"]})<br>
                            <b>Reported At:</b> {match["reported_at"][:19]}<br>
                            <b>Assigned Response Unit:</b> {match.get("assigned_to") or "Under Municipal Dispatch Review"}<br>
                            <b>Resolution Notes:</b> {match.get("resolution_notes") or "Unit scheduled for nearest collection cycle."}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.error(
                    "No ticket found matching that reference ID. Please check and retry."
                )
