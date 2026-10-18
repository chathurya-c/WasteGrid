"""
Advanced Scenario Simulator Sandbox for WasteGrid 2.0.
Enables municipal operators and city planners to stress-test grid resilience without
affecting live operational data:
- Waste increase multiplier (10% to 100%)
- Festival and public event surges
- Multiple facility breakdown combinations
- Vehicle fleet shortages & capacity throttles
- Hypothetical new plant commissioning
- Recycling diversion rate enhancements
- Side-by-side Plotly comparison of utilization, overflow, cost, and CO2 emissions
- Scenario saving and cataloging
"""

import plotly.graph_objects as go
import streamlit as st

from wastegrid import db, optimizer


def render_scenario_simulator_page(palette, baseline_wet, baseline_dry):
    """Render the full interactive Scenario Simulator sandbox."""
    p = palette
    facilities = db.get_all_facilities(include_offline=True)

    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-left:4px solid #a855f7;
                    border-radius:8px; padding:18px 22px; margin-bottom:20px;">
            <div style="font-size:1.15rem; font-weight:800; color:{p["text"]};">🧪 Advanced Municipal Grid Scenario Simulator</div>
            <div style="font-size:0.75rem; color:{p["muted"]}; margin-top:4px;">
                Simulate catastrophic breakdowns, demographic growth, festival surges, and green policies in a risk-free isolated sandbox.
            </div>
            <div style="margin-top:6px; font-size:0.68rem; color:#8ba3c7;">
                <b>Safety Isolation:</b> Simulations do NOT alter operational database records unless explicitly applied.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Simulator Input Sandbox Controls
    with st.expander("🎛️ SIMULATION PARAMETERS & STRESS-TEST LEVERS", expanded=True):
        col_s1, col_s2, col_s3 = st.columns(3)

        with col_s1:
            st.markdown("<b>📈 Waste Demand Surges</b>", unsafe_allow_html=True)
            waste_increase_pct = st.slider(
                "Demographic / Urban Growth Surge (%)", 0, 100, 25, 5
            )
            event_spike_kg = st.number_input(
                "Scheduled Festival / Event Spike (kg)", 0, 30000, 3000, 500
            )
            recycling_boost_pct = st.slider(
                "Recycling Diversion Target (%)", 0, 50, 15, 5
            )

        with col_s2:
            st.markdown(
                "<b>🛑 Facility Failure Contingencies</b>", unsafe_allow_html=True
            )
            fac_ids = [f["id"] for f in facilities]
            sim_outages = st.multiselect(
                "Simulate Facility Outages / Shutdowns", fac_ids, default=["B"]
            )
            capacity_throttle_pct = st.slider(
                "Network Grid Throttle (Power Outages %)", 0, 50, 0, 5
            )

        with col_s3:
            st.markdown(
                "<b>🏗️ Future Infrastructure Planning</b>", unsafe_allow_html=True
            )
            sim_add_new_plant = st.checkbox(
                "Simulate Commissioning Hypothetical Plant F", value=False
            )
            new_plant_cap_kg = (
                st.number_input("Plant F Design Capacity (kg)", 1000, 20000, 4000, 500)
                if sim_add_new_plant
                else 0
            )
            new_plant_stream = (
                st.selectbox("Plant F Technology", ["wet", "dry", "mixed"])
                if sim_add_new_plant
                else "wet"
            )
            fleet_shortage_pct = st.slider(
                "Truck Fleet Shortage (Strike / Fuel Crisis %)", 0, 60, 0, 10
            )

        col_act1, col_act2 = st.columns([1, 4])
        with col_act1:
            run_sim = st.button(
                "🧪 Run Simulation", key="btn_run_sim", use_container_width=True
            )

    # 2. Compute Simulation Models
    # Base Operational Reference
    base_res = optimizer.optimize_multi_objective(
        facilities, baseline_wet, baseline_dry, objective="balanced"
    )

    # Simulated Demand
    sim_wet = (baseline_wet * (1.0 + waste_increase_pct / 100.0)) + (
        event_spike_kg * 0.7
    )
    # Recycling boost diverts dry waste
    sim_dry = max(
        200.0,
        (baseline_dry * (1.0 + waste_increase_pct / 100.0))
        * (1.0 - recycling_boost_pct / 100.0)
        + (event_spike_kg * 0.3),
    )

    # Simulated Facilities
    sim_facilities = []
    for f in facilities:
        fc = dict(f)
        if fc["id"] in sim_outages:
            fc["capacity_kg"] = 0.0
            fc["status"] = "offline"
        else:
            fc["capacity_kg"] = fc["capacity_kg"] * (
                1.0 - capacity_throttle_pct / 100.0
            )
        sim_facilities.append(fc)

    if sim_add_new_plant:
        sim_facilities.append(
            {
                "id": "F",
                "name": "Hypothetical Advanced Eco-Plant F",
                "type": "biocompost" if new_plant_stream == "wet" else "mrf",
                "accepts": new_plant_stream,
                "capacity_kg": float(new_plant_cap_kg),
                "current_load_kg": 0.0,
                "distance_km": 12.0,
                "cost_per_ton": 310.0,
                "carbon_factor_kg": 0.03,
                "status": "online",
            }
        )

    # Run Solver on Simulated Sandbox
    sim_res = optimizer.optimize_multi_objective(
        sim_facilities, sim_wet, sim_dry, objective="balanced"
    )

    # 3. Side-by-Side Before vs After Simulation Dashboard
    st.markdown(
        '<div class="sec-title">📊 SIMULATION IMPACT SCORECARD: BASELINE VS SIMULATED STRESS TEST</div>',
        unsafe_allow_html=True,
    )

    diff_waste = sim_res["total_waste"] - base_res["total_waste"]
    diff_ovf = sim_res["total_overflow"] - base_res["total_overflow"]
    diff_cost = sim_res["transport_cost_inr"] - base_res["transport_cost_inr"]
    diff_carb = sim_res["carbon_emissions_kg"] - base_res["carbon_emissions_kg"]

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(
            "Simulated Total Waste",
            f"{sim_res['total_waste'] / 1000:.2f} T",
            delta=f"{diff_waste / 1000:+.2f} T",
        )
    with col_m2:
        st.metric(
            "Simulated Plant Capacity",
            f"{sim_res['total_capacity'] / 1000:.2f} T",
            delta=f"{(sim_res['total_capacity'] - base_res['total_capacity']) / 1000:+.2f} T",
        )
    with col_m3:
        st.metric(
            "Simulated Overflow Risk",
            f"{sim_res['total_overflow'] / 1000:.2f} T",
            delta=f"{diff_ovf / 1000:+.2f} T",
            delta_color="inverse",
        )
    with col_m4:
        st.metric(
            "Simulated Route Cost",
            f"{sim_res['transport_cost_inr']:,.0f} ₹",
            delta=f"{diff_cost:+,.0f} ₹",
            delta_color="inverse",
        )

    # 4. Comparative Charts
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        fig_cap = go.Figure(
            data=[
                go.Bar(
                    name="Baseline Operations",
                    x=["Total Waste", "Total Capacity", "Overflow"],
                    y=[
                        base_res["total_waste"] / 1000,
                        base_res["total_capacity"] / 1000,
                        base_res["total_overflow"] / 1000,
                    ],
                    marker_color=p["blue"],
                ),
                go.Bar(
                    name="Simulated Scenario",
                    x=["Total Waste", "Total Capacity", "Overflow"],
                    y=[
                        sim_res["total_waste"] / 1000,
                        sim_res["total_capacity"] / 1000,
                        sim_res["total_overflow"] / 1000,
                    ],
                    marker_color=p["accent"],
                ),
            ]
        )
        fig_cap.update_layout(
            barmode="group",
            title="Grid Capacity & Overflow Stress Comparison",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=p["text"],
            height=280,
            margin=dict(l=10, r=10, t=35, b=10),
            yaxis_title="Tons (T)",
        )
        st.plotly_chart(fig_cap, use_container_width=True)

    with col_g2:
        # Facility Utilization Shift
        fac_labels = [f["id"] for f in sim_facilities]
        b_util = [
            (base_res["allocations"].get(fid, 0) / f.get("capacity_kg", 1) * 100)
            for fid, f in [
                (fid, next((x for x in facilities if x["id"] == fid), {}))
                for fid in fac_labels
            ]
        ]
        s_util = [
            (sim_res["allocations"].get(f["id"], 0) / f["capacity_kg"] * 100)
            if f["capacity_kg"] > 0
            else 0
            for f in sim_facilities
        ]

        fig_fac = go.Figure(
            data=[
                go.Bar(
                    name="Baseline Load %",
                    x=fac_labels,
                    y=b_util,
                    marker_color=p["success"],
                ),
                go.Bar(
                    name="Simulated Load %",
                    x=fac_labels,
                    y=s_util,
                    marker_color="#f59e0b",
                ),
            ]
        )
        fig_fac.update_layout(
            barmode="group",
            title="Individual Facility Utilization Shifts",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=p["text"],
            height=280,
            margin=dict(l=10, r=10, t=35, b=10),
            yaxis_title="% Load",
        )
        st.plotly_chart(fig_fac, use_container_width=True)

    # 5. Save Scenario to Database
    st.markdown("<br>", unsafe_allow_html=True)
    with (
        st.expander(
            "💾 ARCHIVE SCENARIO TO MUNICIPAL CONTINGENCY DATABASE", expanded=False
        ),
        st.form("save_scenario_form"),
    ):
        scen_name = st.text_input(
            "Scenario Name",
            placeholder="e.g. Dasara Festival Surge + Plant B Major Overhaul",
        )
        scen_desc = st.text_input(
            "Contingency Summary",
            placeholder="e.g. Tests grid viability with 25% surge and digester offline",
        )
        btn_save = st.form_submit_button(
            "Save Contingency Plan to Database", use_container_width=True
        )

        if btn_save:
            if scen_name:
                curr_u = st.session_state.get("authenticated_user", {}).get(
                    "username", "admin"
                )
                params = {
                    "waste_increase_pct": waste_increase_pct,
                    "event_spike_kg": event_spike_kg,
                    "recycling_boost_pct": recycling_boost_pct,
                    "sim_outages": sim_outages,
                    "capacity_throttle_pct": capacity_throttle_pct,
                }
                results = {
                    "sim_total_waste": sim_res["total_waste"],
                    "sim_overflow": sim_res["total_overflow"],
                    "sim_cost": sim_res["transport_cost_inr"],
                    "sim_carbon": sim_res["carbon_emissions_kg"],
                }
                db.save_scenario(scen_name, scen_desc, params, results, curr_u)
                st.success(f"Scenario '{scen_name}' permanently archived in database!")
            else:
                st.warning("Please provide a name for the scenario.")

    # 6. Saved Scenarios Directory
    saved_scenarios = db.get_all_scenarios()
    if saved_scenarios:
        st.markdown(
            '<div class="sec-title">📚 ARCHIVED CONTINGENCY SCENARIOS</div>',
            unsafe_allow_html=True,
        )
        for sc in saved_scenarios[:5]:
            st.markdown(
                f"""<div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-radius:6px; padding:12px 16px; margin-bottom:8px;">
                    <b>{sc["name"]}</b> · <span style="font-size:0.75rem; color:{p["muted"]};">Archived by {sc["created_by"]} on {sc["created_at"][:10]}</span><br>
                    <small style="color:{p["muted"]};">{sc.get("description", "")}</small>
                </div>""",
                unsafe_allow_html=True,
            )
