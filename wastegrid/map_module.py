"""
Interactive GIS Waste Map and Geographic Heatmap for WasteGrid 2.0.
Built with Folium and Streamlit-Folium:
- Real-time facility operational status markers (Green, Yellow, Orange, Red)
- Waste generation thermal density heatmap
- Interactive popups with capacity, load, stream compatibility
- Reallocation transport route vectors
- Multi-dimensional filters (Zone, Stream Type, Facility Status)
"""

import folium
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium

from wastegrid import db


def render_map_page(palette):
    """Render the full interactive GIS Waste Map & Heatmap console."""
    p = palette

    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-left:4px solid {p["blue"]};
                    border-radius:8px; padding:18px 22px; margin-bottom:20px;">
            <div style="font-size:1.15rem; font-weight:800; color:{p["text"]};">🗺️ Live Municipal Waste Map & Geographic Heatmap</div>
            <div style="font-size:0.75rem; color:{p["muted"]}; margin-top:4px;">
                Geospatial visualization of collection wards, thermal waste generation density, facility capacity thresholds, and active dispatch vectors.
            </div>
            <div style="margin-top:6px; font-size:0.68rem; color:#8ba3c7;">
                <b>Notice:</b> Geospatial telemetry calibrated on Bengaluru Urban Municipal District coordinates. Includes real-time sensor inputs and simulation vectors.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    facilities = db.get_all_facilities(include_offline=True)
    sources = db.get_all_waste_sources()
    vehicles = db.get_all_vehicles()

    # 1. Map Control Filter Bar
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        zones = ["All Zones"] + sorted(
            list(set(s.get("zone", "Central") for s in sources))
        )
        sel_zone = st.selectbox("Municipal Zone", zones)
    with col_f2:
        sel_stream = st.selectbox(
            "Waste Stream", ["All Streams", "Wet / Organic", "Dry / Recyclable"]
        )
    with col_f3:
        show_heatmap = st.checkbox("Show Density Heatmap", value=True)
    with col_f4:
        show_routes = st.checkbox("Show Transfer Vectors", value=True)

    # Filter sources
    filtered_sources = sources
    if sel_zone != "All Zones":
        filtered_sources = [s for s in filtered_sources if s.get("zone") == sel_zone]
    if sel_stream == "Wet / Organic":
        filtered_sources = [s for s in filtered_sources if s.get("waste_type") == "wet"]
    elif sel_stream == "Dry / Recyclable":
        filtered_sources = [s for s in filtered_sources if s.get("waste_type") == "dry"]

    # Base Folium Map centered on Bengaluru (Using OpenStreetMap, CartoDB Dark Matter & Esri)
    center_lat, center_lon = 12.9650, 77.6050
    is_dark = p.get("name") == "dark"
    default_tiles = "CartoDB dark_matter" if is_dark else "OpenStreetMap"
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles=default_tiles,
        prefer_canvas=True,
    )

    if is_dark:
        folium.TileLayer(
            tiles="OpenStreetMap",
            name="OpenStreetMap (Light)",
            control=True,
        ).add_to(m)
    else:
        folium.TileLayer(
            tiles="CartoDB dark_matter",
            name="CartoDB Dark Matter",
            control=True,
        ).add_to(m)

    # Add Esri World Street Map Layer as an alternate clean basemap
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; National Geographic, DeLorme, NAVTEQ",
        name="Esri World Streets",
        control=True,
    ).add_to(m)

    # 2. Add Heatmap Layer
    if show_heatmap and filtered_sources:
        heat_data = [
            [
                s["latitude"],
                s["longitude"],
                float(s["baseline_kg"] + s.get("active_spike_kg", 0)),
            ]
            for s in filtered_sources
        ]
        HeatMap(
            heat_data,
            radius=28,
            blur=20,
            max_zoom=14,
            gradient={0.2: "#3b82f6", 0.5: "#eab308", 0.8: "#f97316", 1.0: "#ef4444"},
        ).add_to(m)

    # 3. Add Waste Sources Markers
    for s in filtered_sources:
        total_s_kg = s["baseline_kg"] + s.get("active_spike_kg", 0)
        wtype = s.get("waste_type", "wet").upper()
        color = "#00d2ff" if wtype == "WET" else "#c084fc"

        popup_html = f"""
        <div style="font-family:sans-serif; font-size:12px; width:200px;">
            <b style="font-size:13px; color:#1e293b;">{s["name"]}</b><br>
            <b>Ward:</b> {s["ward_code"]} ({s["zone"]})<br>
            <b>Daily Generation:</b> {total_s_kg:,.0f} kg<br>
            <b>Stream:</b> {wtype}<br>
            <small style="color:#64748b;">Source Telemetry: Smart Compactor Bins</small>
        </div>
        """

        folium.CircleMarker(
            location=[s["latitude"], s["longitude"]],
            radius=7 + min(12, int(total_s_kg / 300)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"{s['name']}: {total_s_kg:,.0f} kg ({wtype})",
        ).add_to(m)

    # 4. Add Processing Facilities Markers
    fac_coords = {}
    for f in facilities:
        fid = f["id"]
        fac_coords[fid] = (f["latitude"], f["longitude"])
        cap_kg = f["capacity_kg"]
        load_kg = f["current_load_kg"]
        util = (load_kg / cap_kg * 100) if cap_kg > 0 else 0
        stat = f["status"]

        # Color-code facility threshold markers
        if stat != "online":
            icon_color = "red"
            badge = "OFFLINE"
        elif util < 70:
            icon_color = "green"
            badge = "NORMAL LOAD"
        elif util < 85:
            icon_color = "blue"
            badge = "MODERATE"
        elif util < 95:
            icon_color = "orange"
            badge = "ELEVATED WARNING"
        else:
            icon_color = "red"
            badge = "CRITICAL CAPACITY"

        popup_html = f"""
        <div style="font-family:sans-serif; font-size:12px; width:230px;">
            <b style="font-size:14px; color:#0f172a;">Facility {fid}: {f["name"]}</b><br>
            <b style="color:{icon_color};">Status: {badge} ({util:.1f}%)</b><br>
            <b>Technology:</b> {f["type"].upper()}<br>
            <b>Accepts:</b> {f["accepts"].upper()}<br>
            <b>Current Load:</b> {load_kg:,.0f} / {cap_kg:,.0f} kg<br>
            <b>Distance:</b> {f["distance_km"]} km | <b>Cost:</b> {f.get("cost_per_ton", 350):.0f} ₹/T<br>
            <b>Operating Hours:</b> {f.get("operating_hours", "24/7")}
        </div>
        """

        folium.Marker(
            location=[f["latitude"], f["longitude"]],
            icon=folium.Icon(color=icon_color, icon="industry", prefix="fa"),
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"Plant {fid}: {f['name']} ({util:.1f}% utilized)",
        ).add_to(m)

    # 5. Add Transfer Route Vectors
    if show_routes:
        # Route vectors from sources to facilities based on compatibility
        for s in filtered_sources:
            wtype = s.get("waste_type", "wet")
            target_fid = "A" if wtype == "wet" else "C"
            if target_fid in fac_coords:
                f_lat, f_lon = fac_coords[target_fid]
                line_color = "#3b82f6" if wtype == "wet" else "#a855f7"
                folium.PolyLine(
                    locations=[(s["latitude"], s["longitude"]), (f_lat, f_lon)],
                    color=line_color,
                    weight=2,
                    opacity=0.45,
                    dash_array="5, 8",
                    tooltip=f"Transfer Vector: {s['name']} ➔ Plant {target_fid}",
                ).add_to(m)

    # Layer control for toggling base maps
    folium.LayerControl(position="topright").add_to(m)

    # 6. Render Map in Streamlit with native container width
    st_folium(m, use_container_width=True, height=540, returned_objects=[])

    # 7. Map Legend Card
    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-radius:8px; padding:14px 20px; margin-top:14px;">
            <div style="font-size:0.75rem; font-weight:800; letter-spacing:0.12em; text-transform:uppercase; color:{p["text"]}; margin-bottom:10px;">
                🗺️ Geospatial Legend & Indicator Guide
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:24px; font-size:0.75rem; color:{p["text"]};">
                <div><span style="color:#22c55e;">●</span> <b>Green Plant Marker:</b> Normal Utilization (&lt;70%)</div>
                <div><span style="color:#3b82f6;">●</span> <b>Blue Plant Marker:</b> Moderate Load (70–84%)</div>
                <div><span style="color:#f59e0b;">●</span> <b>Orange Plant Marker:</b> Elevated Warning (85–94%)</div>
                <div><span style="color:#ef4444;">●</span> <b>Red Plant Marker:</b> Critical Capacity / Offline (&ge;95%)</div>
                <div><span style="color:#00d2ff;">●</span> <b>Cyan Circle:</b> Wet/Organic Waste Source</div>
                <div><span style="color:#c084fc;">●</span> <b>Purple Circle:</b> Dry/Recyclable Waste Source</div>
                <div><span style="color:#3b82f6;">- - -</span> <b>Dotted Vector:</b> Active Municipal Transfer Route</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
