"""
Predictive Overflow Alerts Engine for WasteGrid 2.0.
Monitors live facility loads and forecast projections against calibrated thresholds:
- Normal: < 70%
- Moderate: 70% – 84%
- Warning: 85% – 94%
- Critical: >= 95% or Offline
Provides an interactive alerts console with severity filters and Acknowledge/Resolve workflows.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from wastegrid import db


def evaluate_and_sync_alerts():
    """
    Scan all active facilities and current demand to detect capacity breaches,
    offline plants, and forecast anomalies, synchronizing records to SQLite.
    """
    facilities = db.get_all_facilities(include_offline=True)
    existing_alerts = db.get_active_alerts(status_filter="pending")
    active_facility_alerts = {
        a["facility_id"]: a for a in existing_alerts if a["facility_id"]
    }

    for f in facilities:
        fid = f["id"]
        stat = f["status"]
        cap = f["capacity_kg"]
        load = f["current_load_kg"]
        util = (load / cap * 100) if cap > 0 else 100.0

        if stat == "offline" or stat == "maintenance":
            if fid not in active_facility_alerts:
                db.create_alert(
                    fid,
                    "critical",
                    util,
                    f"Plant {fid} ({f['name']}) is {stat.upper()}! Zero processing capacity available.",
                    "Execute emergency LP dynamic reallocation to divert incoming trucks to surviving facilities.",
                )
        elif util >= 95.0:
            if (
                fid not in active_facility_alerts
                or active_facility_alerts[fid]["severity"] != "critical"
            ):
                db.create_alert(
                    fid,
                    "critical",
                    util,
                    f"Plant {fid} ({f['name']}) has breached critical capacity threshold ({util:.1f}%).",
                    "Immediate turnaround diversion recommended. Restrict incoming ward truck dispatches.",
                )
        elif util >= 85.0:
            if fid not in active_facility_alerts:
                db.create_alert(
                    fid,
                    "warning",
                    util,
                    f"Plant {fid} ({f['name']}) operating under high stress load ({util:.1f}%).",
                    "Schedule secondary intake shifts and stage buffer storage at transfer stations.",
                )
        elif util >= 70.0:
            if fid not in active_facility_alerts:
                db.create_alert(
                    fid,
                    "moderate",
                    util,
                    f"Plant {fid} ({f['name']}) entered elevated utilization band ({util:.1f}%).",
                    "Monitor hopper intake rates and maintain standard operating efficiency.",
                )


def get_pending_alert_count():
    """Return count of active un-resolved alerts for badges."""
    alerts = db.get_active_alerts(status_filter="pending")
    return len(alerts)


def render_alerts_dashboard(palette):
    """Render the full interactive Alerts & Notifications Dashboard."""
    p = palette
    evaluate_and_sync_alerts()
    all_alerts = db.get_active_alerts()

    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-left:4px solid {p["accent"]};
                    border-radius:8px; padding:18px 22px; margin-bottom:20px;">
            <div style="font-size:1.15rem; font-weight:800; color:{p["text"]};">🔔 Predictive Overflow Alerts & Incident Console</div>
            <div style="font-size:0.75rem; color:{p["muted"]}; margin-top:4px;">
                Real-time automated incident detection powered by continuous load telemetry and multi-day forecast modeling.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not all_alerts:
        st.success(
            "✅ All systems optimal. Zero active alerts across the municipal grid."
        )
        return

    # 1. Alert KPIs
    total_count = len(all_alerts)
    pending_count = sum(1 for a in all_alerts if a["status"] == "pending")
    critical_count = sum(
        1
        for a in all_alerts
        if a["severity"] == "critical" and a["status"] != "resolved"
    )
    warning_count = sum(
        1
        for a in all_alerts
        if a["severity"] == "warning" and a["status"] != "resolved"
    )

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="m-card"><div class="m-label">🔔 Total Incidents</div><div class="m-value">{total_count} Logged</div></div>
            <div class="m-card hero"><div class="m-label">🚨 Critical Active</div><div class="m-value {"red" if critical_count > 0 else "green"}">{critical_count} Plants</div></div>
            <div class="m-card"><div class="m-label">⚠️ Warnings</div><div class="m-value {"warn" if warning_count > 0 else "green"}">{warning_count} Plants</div></div>
            <div class="m-card green"><div class="m-label">⏳ Pending Action</div><div class="m-value">{pending_count} Alerts</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Alert Analytics Chart
    df_alerts = pd.DataFrame(all_alerts)
    col_chart1, col_chart2 = st.columns([1, 1])

    with col_chart1:
        fig_sev = px.pie(
            df_alerts,
            names="severity",
            title="Incidents by Severity Level",
            color="severity",
            color_discrete_map={
                "critical": p["accent"],
                "warning": "#f59e0b",
                "moderate": p["blue"],
                "normal": p["success"],
            },
            hole=0.45,
        )
        fig_sev.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=p["text"],
            height=240,
            margin=dict(l=10, r=10, t=35, b=10),
        )
        st.plotly_chart(fig_sev, use_container_width=True)

    with col_chart2:
        fig_stat = px.bar(
            df_alerts,
            x="status",
            title="Alert Resolution Status Breakdown",
            color="status",
            color_discrete_map={
                "pending": p["accent"],
                "acknowledged": "#f59e0b",
                "resolved": p["success"],
            },
        )
        fig_stat.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=p["text"],
            height=240,
            margin=dict(l=10, r=10, t=35, b=10),
        )
        st.plotly_chart(fig_stat, use_container_width=True)

    # 3. Filter Controls
    col_sel1, col_sel2 = st.columns([1, 1])
    with col_sel1:
        sel_sev = st.selectbox(
            "Filter Severity",
            ["All Severities", "critical", "warning", "moderate", "normal"],
        )
    with col_sel2:
        sel_stat = st.selectbox(
            "Filter Status", ["All Statuses", "pending", "acknowledged", "resolved"]
        )

    filtered_alerts = all_alerts
    if sel_sev != "All Severities":
        filtered_alerts = [a for a in filtered_alerts if a["severity"] == sel_sev]
    if sel_stat != "All Statuses":
        filtered_alerts = [a for a in filtered_alerts if a["status"] == sel_stat]

    # 4. Interactive Incident Cards
    st.markdown(
        '<div class="sec-title">📋 ACTIVE INCIDENT QUEUE & OPERATIONAL DIRECTIVES</div>',
        unsafe_allow_html=True,
    )

    for a in filtered_alerts:
        aid = a["id"]
        fid = a["facility_id"]
        sev = a["severity"]
        stat = a["status"]
        util = a["utilization_pct"]

        if sev == "critical":
            border_col = p["accent"]
            sev_badge = '<span class="fc-pill overflow">🚨 CRITICAL</span>'
        elif sev == "warning":
            border_col = "#f59e0b"
            sev_badge = '<span class="fc-pill overflow" style="background:rgba(245,158,11,0.18); color:#f59e0b;">⚠️ WARNING</span>'
        elif sev == "moderate":
            border_col = p["blue"]
            sev_badge = f'<span class="fc-pill safe" style="background:rgba(59,130,246,0.18); color:{p["blue"]};">ℹ️ MODERATE</span>'
        else:
            border_col = p["success"]
            sev_badge = '<span class="fc-pill safe">● NORMAL</span>'

        if stat == "resolved":
            stat_pill = (
                '<span style="color:#22c55e; font-weight:700;">✓ RESOLVED</span>'
            )
        elif stat == "acknowledged":
            stat_pill = (
                '<span style="color:#f59e0b; font-weight:700;">👁️ ACKNOWLEDGED</span>'
            )
        else:
            stat_pill = f'<span style="color:{p["accent"]}; font-weight:700;">⏳ PENDING ACTION</span>'

        st.markdown(
            f"""
            <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-left:5px solid {border_col};
                        border-radius:8px; padding:16px 20px; margin-bottom:14px; box-shadow:{p["shadow"]};">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <div>{sev_badge} <b style="font-size:0.9rem; margin-left:8px;">Plant {fid}</b> · <span style="font-size:0.75rem; color:{p["muted"]};">{a["timestamp"]}</span></div>
                    <div>{stat_pill}</div>
                </div>
                <div style="font-size:0.85rem; font-weight:700; color:{p["text"]}; margin-bottom:6px;">
                    {a["message"]}
                </div>
                <div style="font-size:0.75rem; color:{p["muted"]}; background:{p["bg_soft"]}; padding:8px 12px; border-radius:6px; margin-bottom:10px;">
                    <b>Recommended Mitigation Directive:</b> {a["recommended_action"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Action Buttons per Alert
        if stat != "resolved":
            c_act1, c_act2, c_spacer = st.columns([1, 1, 4])
            with c_act1:
                if stat == "pending":
                    if st.button(f"Acknowledge #{aid}", key=f"ack_{aid}"):
                        db.update_alert_status(aid, "acknowledged")
                        st.toast("Alert marked as acknowledged.")
                        st.rerun()
            with c_act2:
                if st.button(f"Mark Resolved #{aid}", key=f"res_{aid}"):
                    curr_u = st.session_state.get("authenticated_user", {}).get(
                        "username", "admin"
                    )
                    db.update_alert_status(aid, "resolved", resolved_by=curr_u)
                    st.success(f"Incident #{aid} resolved.")
                    st.rerun()
