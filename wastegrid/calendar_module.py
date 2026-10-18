"""
Predictive Calendar and Event / Holiday Scheduler for WasteGrid.
Tracks national holidays, regional festivals, and scheduled civic notices to
forecast waste spikes in advance and trigger pre-allocation protocols.
"""

from datetime import date, datetime, timedelta

import streamlit as st

# Pre-configured National Holidays and Regional Festivals
DEFAULT_HOLIDAYS = [
    {
        "date": "2026-10-02",
        "name": "Gandhi Jayanti",
        "type": "National Holiday",
        "surge_pct": 15,
        "primary_stream": "dry",
        "desc": "Public holiday; commercial retail spike & cardboard packaging.",
    },
    {
        "date": "2026-10-11",
        "name": "Maha Navami / Ayudha Puja",
        "type": "State Festival",
        "surge_pct": 45,
        "primary_stream": "wet",
        "desc": "Vehicle & tool worship; massive surge in flowers, ash gourds, banana trunks.",
    },
    {
        "date": "2026-10-12",
        "name": "Vijayadashami / Dasara",
        "type": "State Festival",
        "surge_pct": 50,
        "primary_stream": "wet",
        "desc": "Grand festive processions; organic waste surge across markets and temples.",
    },
    {
        "date": "2026-10-31",
        "name": "Naraka Chaturdashi (Deepavali)",
        "type": "National Festival",
        "surge_pct": 55,
        "primary_stream": "dry",
        "desc": "Festival of Lights; surge in gift cartons, packaging, and fireworks residue.",
    },
    {
        "date": "2026-11-01",
        "name": "State Foundation Day",
        "type": "State Day",
        "surge_pct": 30,
        "primary_stream": "mixed",
        "desc": "State Foundation Day; city rallies and cultural gatherings.",
    },
    {
        "date": "2026-11-02",
        "name": "Balipadyami (Deepavali)",
        "type": "Regional Festival",
        "surge_pct": 35,
        "primary_stream": "wet",
        "desc": "Family gatherings & festive community dining.",
    },
    {
        "date": "2026-12-25",
        "name": "Christmas Day",
        "type": "National Holiday",
        "surge_pct": 35,
        "primary_stream": "dry",
        "desc": "Commercial retail, gift packaging, and restaurant dining spikes.",
    },
    {
        "date": "2026-12-31",
        "name": "New Year's Eve Celebrations",
        "type": "Civic Event",
        "surge_pct": 65,
        "primary_stream": "mixed",
        "desc": "Night-life, outdoor food stalls, and high-density beverage waste.",
    },
]


def init_calendar_state():
    """Initialize scheduled custom notice events in session state."""
    if "custom_events" not in st.session_state:
        st.session_state.custom_events = [
            {
                "notice_id": "BBMP/EVT/2026-108",
                "name": "Bengaluru Tech Summit 2026",
                "date": "2026-10-18",
                "spike_kg": 3500,
                "primary_stream": "dry",
                "location": "Palace Grounds, Bengaluru",
                "notes": "Convention gathering; high plastic, paper, and food catering demand.",
            },
            {
                "notice_id": "BBMP/EVT/2026-142",
                "name": "City Marathon & Green Walk",
                "date": "2026-10-25",
                "spike_kg": 2800,
                "primary_stream": "dry",
                "location": "Cubbon Park - MG Road Circuit",
                "notes": "Hydration station paper cups, energy bar wrappers, and bio-waste.",
            },
        ]


def get_all_calendar_events():
    """Combine built-in holidays and custom user notice events."""
    init_calendar_state()
    events_by_date = {}

    for h in DEFAULT_HOLIDAYS:
        events_by_date[h["date"]] = {
            "title": h["name"],
            "type": h["type"],
            "surge_pct": h["surge_pct"],
            "spike_kg": round(5200 * (h["surge_pct"] / 100)),
            "primary_stream": h["primary_stream"],
            "desc": h["desc"],
            "is_custom": False,
        }

    for c in st.session_state.custom_events:
        c_date = str(c["date"])
        spike = c["spike_kg"]
        pct = round((spike / 5200) * 100)
        events_by_date[c_date] = {
            "title": f"📢 {c['name']} ({c['notice_id']})",
            "type": "Civic Notice",
            "surge_pct": pct,
            "spike_kg": spike,
            "primary_stream": c["primary_stream"],
            "desc": f"{c['location']} · {c.get('notes', '')}",
            "is_custom": True,
        }

    return events_by_date


def add_custom_notice(notice_id, name, event_date, spike_kg, stream, location, notes):
    """Add a new scheduled municipal notice event."""
    init_calendar_state()
    st.session_state.custom_events.append(
        {
            "notice_id": notice_id.strip()
            or f"NOTC-{datetime.now().strftime('%m%d%H%M')}",
            "name": name.strip(),
            "date": str(event_date),
            "spike_kg": float(spike_kg),
            "primary_stream": stream,
            "location": location.strip(),
            "notes": notes.strip(),
        }
    )


def render_calendar_section(palette, total_capacity=7000):
    """Render the full interactive Predictive Calendar & Event Scheduler."""
    p = palette
    init_calendar_state()
    all_events = get_all_calendar_events()

    st.markdown(
        '<div class="cal-header-card">'
        '<div class="cal-title-row">'
        '<div><div class="cal-title">📅 Municipal Surge Calendar & Predictive Holiday Forecaster</div>'
        '<div class="cal-sub">Correlates national holidays, state festivals, and civic event notices with automated waste surge models.</div></div>'
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # 1. Add Event Notice Drawer
    with st.expander(
        "➕ REGISTER UPCOMING EVENT NOTICE (PRE-ALLOCATE GRID)", expanded=False
    ):
        st.markdown(
            f'<div style="font-size:0.75rem; color:{p["muted"]}; margin-bottom:12px;">'
            "When a municipal department or police commissionerate issues an event clearance notice, "
            "register the event details here. WasteGrid automatically forecasts the surge date and pre-allocates facility buffer capacity."
            "</div>",
            unsafe_allow_html=True,
        )

        with st.form("new_event_notice_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                f_name = st.text_input(
                    "Event Name", placeholder="e.g. Annual Cultural Expo & Festival"
                )
                f_notice = st.text_input(
                    "Notice / Order Ref. No.", placeholder="e.g. BBMP/CL/2026/099"
                )
            with col2:
                f_date = st.date_input("Event Date", value=date(2026, 10, 20))
                f_spike = st.number_input(
                    "Estimated Waste Surge (kg)",
                    min_value=500,
                    max_value=25000,
                    value=3000,
                    step=500,
                )
            with col3:
                f_stream = st.selectbox(
                    "Predominant Waste Stream",
                    ["wet", "dry", "mixed"],
                    format_func=lambda x: {
                        "wet": "💧 Organic / Food Stalls (Wet)",
                        "dry": "📦 Merchandise / Packaging (Dry)",
                        "mixed": "🔄 Mixed Municipal Streams",
                    }[x],
                )
                f_loc = st.text_input(
                    "Venue / Ward Location", placeholder="e.g. Freedom Park, Ward 77"
                )

            f_notes = st.text_input(
                "Operational Logistics Note",
                placeholder="e.g. Request 2 extra collection trucks & priority gate at Facility A",
            )
            submit_event = st.form_submit_button(
                "🗓️ Add Event & Update Predictive Schedule", use_container_width=True
            )

            if submit_event:
                if f_name:
                    add_custom_notice(
                        f_notice, f_name, f_date, f_spike, f_stream, f_loc, f_notes
                    )
                    st.success(
                        f"Event notice '{f_name}' on {f_date} registered! Predictive capacity buffer allocated."
                    )
                    st.rerun()
                else:
                    st.error("Please enter a valid event name.")

    # 2. Upcoming High-Impact Dates Grid (Next 30 Days)
    st.markdown(
        '<div class="sec-title">🔔 UPCOMING SURGE DATES & CAPACITY IMPACT PROJECTION</div>',
        unsafe_allow_html=True,
    )

    # Generate 14-day timeline starting from Oct 1, 2026
    start_dt = date(2026, 10, 1)
    timeline_cards = []

    for day_offset in range(16):
        cur_dt = start_dt + timedelta(days=day_offset)
        dt_str = cur_dt.strftime("%Y-%m-%d")
        day_name = cur_dt.strftime("%a")
        day_num = cur_dt.strftime("%d %b")

        is_weekend = cur_dt.weekday() in [5, 6]
        base_demand_kg = 5200 * (1.15 if is_weekend else 1.0)
        event_info = all_events.get(dt_str)

        if event_info:
            spike_kg = event_info["spike_kg"]
            total_pred_kg = base_demand_kg + spike_kg
            ev_title = event_info["title"]
            ev_badge = f'<span class="cal-badge festival">{event_info["type"]} (+{event_info["surge_pct"]}%)</span>'
        else:
            spike_kg = 0
            total_pred_kg = base_demand_kg
            ev_title = "Standard Routine Collection"
            ev_badge = (
                '<span class="cal-badge normal">Nominal</span>'
                if not is_weekend
                else '<span class="cal-badge weekend">Weekend Peak</span>'
            )

        total_pred_tons = total_pred_kg / 1000
        capacity_tons = total_capacity / 1000
        is_overflow = total_pred_kg > total_capacity
        ovf_tons = max(0, total_pred_tons - capacity_tons)

        card_cls = "danger" if is_overflow else ("warn" if event_info else "normal")
        status_text = (
            f"🚨 Capacity Breach (+{ovf_tons:.2f} T)"
            if is_overflow
            else f"✓ Buffer Safe ({capacity_tons - total_pred_tons:.2f} T)"
        )

        timeline_cards.append(
            f'<div class="cal-date-card {card_cls}">'
            f'<div class="cal-date-top"><span class="cal-day-num">{day_num}</span><span class="cal-day-name">{day_name}</span></div>'
            f'<div class="cal-event-name" title="{ev_title}">{ev_title}</div>'
            f'<div class="cal-badge-wrap">{ev_badge}</div>'
            f'<div class="cal-demand-val">{total_pred_tons:.2f} T</div>'
            f'<div class="cal-status-text">{status_text}</div>'
            f"</div>"
        )

    st.markdown(
        '<div class="cal-timeline-grid">' + "".join(timeline_cards) + "</div>",
        unsafe_allow_html=True,
    )

    # 3. Master Holiday & Event Register Table
    st.markdown(
        '<div class="sec-title">📋 MASTER SCHEDULED NOTICE & FESTIVAL LOGBOOK</div>',
        unsafe_allow_html=True,
    )

    table_rows = []
    sorted_dates = sorted(all_events.keys())
    for d in sorted_dates:
        ev = all_events[d]
        dt_obj = datetime.strptime(d, "%Y-%m-%d")
        f_date_str = dt_obj.strftime("%d %B %Y (%A)")

        pred_tons = (5200 + ev["spike_kg"]) / 1000
        risk_pill = (
            f'<span class="fc-pill overflow">▲ High Surge Risk ({pred_tons:.2f} T)</span>'
            if pred_tons > 7.0
            else f'<span class="fc-pill safe">● Handled ({pred_tons:.2f} T)</span>'
        )

        stream_pill = (
            "💧 Organic (Wet)"
            if ev["primary_stream"] == "wet"
            else (
                "📦 Packaging (Dry)"
                if ev["primary_stream"] == "dry"
                else "🔄 Mixed Streams"
            )
        )
        badge_type = f'<b>{ev["title"]}</b> <span style="font-size:0.65rem; color:{p["muted"]};">[{ev["type"]}]</span>'

        table_rows.append(
            f"<tr>"
            f"<td><b>{f_date_str}</b></td>"
            f"<td>{badge_type}</td>"
            f"<td>+{ev['spike_kg']:,} kg (+{ev['surge_pct']}%)</td>"
            f"<td>{stream_pill}</td>"
            f"<td>{risk_pill}</td>"
            f"<td><small>{ev['desc']}</small></td>"
            f"</tr>"
        )

    st.markdown(
        f'<div class="fc-table-wrap">'
        f'<table class="fc-table">'
        f"<thead><tr>"
        f"<th>Scheduled Date</th>"
        f"<th>Occasion / Notice Reference</th>"
        f"<th>Anticipated Surge</th>"
        f"<th>Primary Stream</th>"
        f"<th>Grid Status</th>"
        f"<th>Logistics Mitigation Guideline</th>"
        f"</tr></thead>"
        f"<tbody>"
        f"{''.join(table_rows)}"
        f"</tbody>"
        f"</table>"
        f"</div>",
        unsafe_allow_html=True,
    )
