"""
Truck-to-Municipality Telematics Bridge and Dynamic Dispatch Module for WasteGrid.
Bridges the physical gap between compactor truck fleets and central municipal command:
- IoT weight load cells on hydraulic lifters
- Real-time GPS telematics & in-cab driver companion tablets
- Automated RFID weighbridge handshake at processing plant gates
- Real-time dynamic diversion protocol during facility outages & event surges
"""

import streamlit as st


def get_truck_fleet(event_active=False, outage_facility=None):
    """
    Generate the active municipal truck fleet and determine real-time
    routing status based on active grid conditions (events/outages).
    """
    base_trucks = [
        {
            "id": "KA-01-EA-101",
            "driver": "Ramesh Kumar",
            "zone": "Downtown Residential Hub",
            "capacity_kg": 3000,
            "payload_kg": 2400,
            "type": "wet",
            "base_target": "A",
            "target_facility": "A",
            "facility_name": "Organic Biocompost (Facility A)",
            "speed_kmh": 32,
            "eta_mins": 8,
            "status": "In Transit",
            "telemetry": "Hydraulic Load Cell Active · GPS Locked",
        },
        {
            "id": "KA-01-EA-102",
            "driver": "Shivakumar N.",
            "zone": "Suburban Green Villas",
            "capacity_kg": 2500,
            "payload_kg": 1800,
            "type": "wet",
            "base_target": "B",
            "target_facility": "B",
            "facility_name": "Anaerobic Digester (Facility B)",
            "speed_kmh": 28,
            "eta_mins": 14,
            "status": "In Transit",
            "telemetry": "Hydraulic Load Cell Active · GPS Locked",
        },
        {
            "id": "KA-04-MB-204",
            "driver": "Mohammed Rafiq",
            "zone": "Culinary Food Market",
            "capacity_kg": 3500,
            "payload_kg": 2200,
            "type": "wet",
            "base_target": "A",
            "target_facility": "A",
            "facility_name": "Organic Biocompost (Facility A)",
            "speed_kmh": 0,
            "eta_mins": 0,
            "status": "Weighbridge Discharge",
            "telemetry": "RFID Gate Handshake Verified · Gross 7,420 kg",
        },
        {
            "id": "KA-04-MB-312",
            "driver": "Anand Vardhan",
            "zone": "Silicon Tech Park Towers",
            "capacity_kg": 2000,
            "payload_kg": 950,
            "type": "dry",
            "base_target": "C",
            "target_facility": "C",
            "facility_name": "Material Recovery Facility (Facility C)",
            "speed_kmh": 38,
            "eta_mins": 11,
            "status": "In Transit",
            "telemetry": "Dry Compactor Active · GPS Locked",
        },
        {
            "id": "KA-05-AB-405",
            "driver": "Venkatesh Murthy",
            "zone": "Grand Central Mall",
            "capacity_kg": 2500,
            "payload_kg": 1200,
            "type": "dry",
            "base_target": "C",
            "target_facility": "C",
            "facility_name": "Material Recovery Facility (Facility C)",
            "speed_kmh": 22,
            "eta_mins": 19,
            "status": "In Transit",
            "telemetry": "Dry Compactor Active · GPS Locked",
        },
        {
            "id": "KA-05-AB-512",
            "driver": "Syed Imran",
            "zone": "University Campus & Hostels",
            "capacity_kg": 2000,
            "payload_kg": 750,
            "type": "dry",
            "base_target": "C",
            "target_facility": "C",
            "facility_name": "Material Recovery Facility (Facility C)",
            "speed_kmh": 34,
            "eta_mins": 7,
            "status": "In Transit",
            "telemetry": "Dry Compactor Active · GPS Locked",
        },
        {
            "id": "KA-01-EA-601",
            "driver": "Basavaraj Patil",
            "zone": "Civic Center & Public Offices",
            "capacity_kg": 2000,
            "payload_kg": 550,
            "type": "dry",
            "base_target": "C",
            "target_facility": "C",
            "facility_name": "Material Recovery Facility (Facility C)",
            "speed_kmh": 0,
            "eta_mins": 0,
            "status": "Loading at Ward",
            "telemetry": "Bin Lifter Sensor Active · 45% Bin Capacity",
        },
    ]

    # Add special emergency surge truck if an event is active
    if event_active:
        base_trucks.append(
            {
                "id": "KA-02-EM-999",
                "driver": "Guru Prasad (Surge Taskforce)",
                "zone": "Civic Event / Festival Zone",
                "capacity_kg": 5000,
                "payload_kg": 4000,
                "type": "wet",
                "base_target": "A",
                "target_facility": "A",
                "facility_name": "Organic Biocompost (Facility A) [Priority Buffer]",
                "speed_kmh": 41,
                "eta_mins": 15,
                "status": "Surge Response",
                "telemetry": "High-Capacity Dual Compactor · Priority Beacon Active",
            }
        )

    # Apply dynamic rerouting if a facility is offline
    fleet = []
    for t in base_trucks:
        truck = dict(t)
        if outage_facility and truck["base_target"] == outage_facility:
            # Dynamic Diversion by WasteGrid LP Solver!
            if truck["type"] == "wet":
                truck["target_facility"] = "A"
                truck["facility_name"] = (
                    "Organic Biocompost (Facility A) [Auto-Diverted]"
                )
                truck["status"] = "⚡ Diverted En Route"
                truck["telemetry"] = (
                    f"Diverted from {outage_facility} to A via LP Re-balancer · ETA +6 mins"
                )
            elif truck["type"] == "dry":
                truck["target_facility"] = "Secondary Transfer Depot"
                truck["facility_name"] = "East Transfer Depot [Buffer Storage]"
                truck["status"] = "⚡ Diverted to Depot"
                truck["telemetry"] = (
                    "Facility C Offline · Rerouted to Regional Transfer Depot"
                )
        fleet.append(truck)

    return fleet


def render_truck_operations_section(palette, event_active=False, outage_facility=None):
    """Render the full interactive Truck Fleet & Municipality Telematics Console."""
    p = palette
    fleet = get_truck_fleet(event_active, outage_facility)

    total_trucks = len(fleet)
    total_payload = sum(t["payload_kg"] for t in fleet)
    diverted_count = sum(1 for t in fleet if "Diverted" in t["status"])
    discharging_count = sum(1 for t in fleet if "Discharge" in t["status"])

    # Header Card
    st.markdown(
        '<div class="truck-header-card">'
        '<div class="truck-title-row">'
        "<div>"
        '<div class="truck-title">🚚 Truck-to-Municipality Telematics Bridge & Dynamic Fleet Dispatch</div>'
        '<div class="truck-sub">Real-time IoT weight load cells, GPS geofencing, and automated in-cab turnaround rerouting.</div>'
        "</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # 1. Architectural Explainer: How the Bridge Works
    with st.expander(
        "ℹ️ HOW DO TRUCKS CONNECT WITH THE MUNICIPALITY? (TECHNICAL ARCHITECTURE)",
        expanded=False,
    ):
        st.markdown(
            '<div class="bridge-flow-wrap">'
            '<div class="bridge-step">'
            '<div class="bridge-step-num">1</div>'
            '<div class="bridge-step-title">IoT Load Cells on Lifters</div>'
            '<div class="bridge-step-body">Hydraulic pressure sensors on the compactor bin-lifter weigh every dumpster lift, calculating tare and payload to ±5 kg precision.</div>'
            "</div>"
            '<div class="bridge-arrow">➔</div>'
            '<div class="bridge-step">'
            '<div class="bridge-step-num">2</div>'
            '<div class="bridge-step-title">4G/NB-IoT Telematics Gateway</div>'
            '<div class="bridge-step-body">Truck telematics stream GPS coordinates, speed, and real-time payload every 10 seconds to the municipal cloud over MQTT.</div>'
            "</div>"
            '<div class="bridge-arrow">➔</div>'
            '<div class="bridge-step">'
            '<div class="bridge-step-num">3</div>'
            '<div class="bridge-step-title">In-Cab Companion App</div>'
            '<div class="bridge-step-body">Drivers carry an in-cab Android tablet receiving turn-by-turn routing generated by WasteGrid\'s linear optimization solver.</div>'
            "</div>"
            '<div class="bridge-arrow">➔</div>'
            '<div class="bridge-step">'
            '<div class="bridge-step-num">4</div>'
            '<div class="bridge-step-title">Automated RFID Weighbridge</div>'
            '<div class="bridge-step-body">On arrival at Plant A/B/C, windshield RFID tags trigger automated boom gates. Gross weight is recorded with zero manual paperwork.</div>'
            "</div>"
            '<div class="bridge-arrow">➔</div>'
            '<div class="bridge-step highlight">'
            '<div class="bridge-step-num">5</div>'
            '<div class="bridge-step-title">Dynamic Turnaround Divert</div>'
            '<div class="bridge-step-body"><b>The WasteGrid Edge:</b> If Facility B fails, WasteGrid immediately pushes turnaround alerts to en-route drivers, preventing gate gridlock!</div>'
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    # 2. Live Fleet KPI Row
    st.markdown(
        f'<div class="metric-grid">'
        f'<div class="m-card"><div class="m-label">🚛 Active Fleet</div><div class="m-value">{total_trucks} Units</div></div>'
        f'<div class="m-card green"><div class="m-label">⚖️ In-Transit Payload</div><div class="m-value">{total_payload / 1000:.2f} Tons</div></div>'
        f'<div class="m-card hero"><div class="m-label">⚡ Active Diverts</div><div class="m-value {"red" if diverted_count > 0 else "green"}">{diverted_count} Trucks</div></div>'
        f'<div class="m-card purple"><div class="m-label">🏁 Weighbridge Active</div><div class="m-value">{discharging_count} Units</div></div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # 3. Dynamic Rerouting Alert Banner if Diverts Active
    if diverted_count > 0:
        st.markdown(
            f'<div class="wg-status red">'
            f"🚨 <b>Emergency Dynamic Reroute In Effect:</b> Facility <b>{outage_facility}</b> is offline. "
            f"WasteGrid LP solver has re-routed <b>{diverted_count} active in-transit truck(s)</b> "
            f"to alternative facilities to prevent processing backlog and roadside dumping!"
            f"</div>",
            unsafe_allow_html=True,
        )

    # 4. Live Dispatch Console Table
    st.markdown(
        '<div class="sec-title">📡 LIVE VEHICLE TELEMATICS & DISPATCH MATRIX</div>',
        unsafe_allow_html=True,
    )

    truck_rows = []
    for t in fleet:
        is_diverted = "Diverted" in t["status"]
        if is_diverted:
            status_pill = f'<span class="fc-pill overflow">⚡ {t["status"]}</span>'
            target_style = f"color:{p['accent']}; font-weight:700;"
        elif "Discharge" in t["status"]:
            status_pill = f'<span class="fc-pill safe">● {t["status"]}</span>'
            target_style = f"color:{p['text']};"
        elif "Surge" in t["status"]:
            status_pill = f'<span class="fc-pill overflow">🚨 {t["status"]}</span>'
            target_style = f"color:{p['accent']}; font-weight:700;"
        else:
            status_pill = f'<span class="fc-pill safe">✓ {t["status"]}</span>'
            target_style = f"color:{p['text']};"

        pct_load = (t["payload_kg"] / t["capacity_kg"]) * 100
        stream_icon = "💧 Wet" if t["type"] == "wet" else "📦 Dry"

        truck_rows.append(
            f"<tr>"
            f"<td><b><code>{t['id']}</code></b></td>"
            f"<td>{t['driver']}</td>"
            f"<td>{t['zone']}</td>"
            f"<td>{t['payload_kg']:,} / {t['capacity_kg']:,} kg ({pct_load:.0f}%)</td>"
            f"<td>{stream_icon}</td>"
            f'<td style="{target_style}">{t["facility_name"]}</td>'
            f"<td>{t['speed_kmh']} km/h · ETA {t['eta_mins']}m</td>"
            f"<td>{status_pill}</td>"
            f'<td><small style="color:{p["muted"]};">{t["telemetry"]}</small></td>'
            f"</tr>"
        )

    st.markdown(
        f'<div class="fc-table-wrap">'
        f'<table class="fc-table">'
        f"<thead><tr>"
        f"<th>Vehicle Registration</th>"
        f"<th>Assigned Driver</th>"
        f"<th>Collection Zone</th>"
        f"<th>Payload / Capacity</th>"
        f"<th>Stream</th>"
        f"<th>Designated Processing Plant</th>"
        f"<th>Speed / ETA</th>"
        f"<th>Dispatch Status</th>"
        f"<th>Telemetry & Gate Sensor Log</th>"
        f"</tr></thead>"
        f"<tbody>"
        f"{''.join(truck_rows)}"
        f"</tbody>"
        f"</table>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # 5. Interactive Driver Broadcast Action
    col_b1, col_b2 = st.columns([3, 1])
    with col_b1:
        st.markdown(
            f'<div style="font-size:0.75rem; color:{p["muted"]};">'
            "Simulate pushing real-time route revisions over cellular telemetry to all in-transit drivers:"
            "</div>",
            unsafe_allow_html=True,
        )
    with col_b2:
        if st.button(
            "📡 Broadcast Reroute Dispatch",
            key="btn_broadcast_dispatch",
            use_container_width=True,
        ):
            st.toast(
                "✅ Dispatch packet broadcasted to 8 vehicle in-cab tablets! Telematics confirmed."
            )
