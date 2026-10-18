"""
Smart Waste Reallocation Linear Optimization Engine for WasteGrid 2.0.
Extends the linear programming solver with multi-objective optimization:
1. Minimum Overflow
2. Minimum Transportation Cost
3. Minimum Carbon Emissions
4. Balanced Optimization
Supports dynamic facilities, compatibility verification, route costing,
before-and-after impact analytics, and administrative approval workflows.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.optimize import linprog

from wastegrid import db

# =========================================================================
# CORE LINEAR PROGRAMMING SOLVER (BACKWARD COMPATIBLE & EXTENDED)
# =========================================================================


def optimize(facilities, wet_total, dry_total, use_lp=True, objective="balanced"):
    """
    Allocate waste streams to compatible facilities.
    Backward-compatible wrapper returning (allocations_dict, overflow_dict).
    """
    res = optimize_multi_objective(
        facilities, wet_total, dry_total, objective=objective
    )
    return res["allocations"], res["overflow"]


def optimize_multi_objective(facilities, wet_total, dry_total, objective="balanced"):
    """
    Advanced multi-objective LP optimization.
    Takes unlimited dynamic facilities from DB and optimizes based on chosen objective.
    """
    streams = [("wet", float(wet_total)), ("dry", float(dry_total))]

    # Build (facility_index, stream) compatibility pairs
    pairs = []
    for fi, f in enumerate(facilities):
        # Ignore facilities with zero or negative capacity
        if f.get("capacity_kg", 0) <= 0 or f.get("status") in [
            "offline",
            "maintenance",
        ]:
            continue
        accepts = f.get("accepts", "wet").lower()
        for stream, total in streams:
            if accepts == stream or accepts == "mixed":
                pairs.append((fi, stream))

    n_alloc = len(pairs)
    n_overflow = len(streams)
    n_vars = n_alloc + n_overflow

    if n_alloc == 0:
        # Fallback if all plants are offline
        allocations = {f["id"]: 0.0 for f in facilities}
        overflow = {s: tot for s, tot in streams if tot > 0}
        return _build_result_summary(facilities, allocations, overflow, streams, 0, 0)

    # Cost vector c based on objective choice
    c = np.zeros(n_vars)
    for i, (fi, _) in enumerate(pairs):
        f = facilities[fi]
        dist = f.get("distance_km", 5.0)
        proc_cost = f.get("cost_per_ton", 350.0) / 1000.0  # cost per kg
        carb_factor = f.get("carbon_factor_kg", 0.04)  # kg CO2 per kg

        if objective == "min_overflow":
            c[i] = dist * 0.05
        elif objective == "min_cost":
            c[i] = (dist * 0.12) + proc_cost
        elif objective == "min_carbon":
            c[i] = (dist * 0.08) + carb_factor
        else:  # balanced
            c[i] = (dist * 0.10) + (proc_cost * 0.5) + (carb_factor * 10)

    # Heavy penalty on overflow
    overflow_penalty = 10000.0 if objective == "min_overflow" else 5000.0
    for k in range(n_overflow):
        c[n_alloc + k] = overflow_penalty

    # Equality constraints: allocations per stream + overflow = total stream demand
    A_eq = []
    b_eq = []
    for k, (stream, total) in enumerate(streams):
        row = np.zeros(n_vars)
        for i, (_, s) in enumerate(pairs):
            if s == stream:
                row[i] = 1.0
        row[n_alloc + k] = 1.0
        A_eq.append(row)
        b_eq.append(total)

    # Inequality constraints: sum of allocations to facility <= capacity
    A_ub = []
    b_ub = []
    for fi, f in enumerate(facilities):
        row = np.zeros(n_vars)
        has_pair = False
        for i, (fac_idx, _) in enumerate(pairs):
            if fac_idx == fi:
                row[i] = 1.0
                has_pair = True
        if has_pair:
            A_ub.append(row)
            b_ub.append(max(0.0, f["capacity_kg"] - f.get("current_load_kg", 0.0)))

    bounds = [(0, None)] * n_vars

    try:
        res = linprog(
            c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs"
        )
        if not res.success:
            return _optimize_greedy_extended(facilities, wet_total, dry_total)
    except Exception:
        return _optimize_greedy_extended(facilities, wet_total, dry_total)

    # Extract allocations
    allocations = {f["id"]: 0.0 for f in facilities}
    for i, (fi, _) in enumerate(pairs):
        allocations[facilities[fi]["id"]] += res.x[i]

    # Extract overflow
    overflow = {}
    for k, (stream, _) in enumerate(streams):
        ovf = res.x[n_alloc + k]
        if ovf > 0.1:
            overflow[stream] = ovf

    return _build_result_summary(
        facilities, allocations, overflow, streams, pairs, res.x[:n_alloc]
    )


def _optimize_greedy_extended(facilities, wet_total, dry_total):
    """Greedy heuristic fallback when linear programming solver fails."""
    allocations = {f["id"]: 0.0 for f in facilities}
    overflow = {}
    streams = [("wet", wet_total), ("dry", dry_total)]

    for wtype, total in streams:
        compat = sorted(
            [
                f
                for f in facilities
                if (f.get("accepts") == wtype or f.get("accepts") == "mixed")
                and f.get("status") == "online"
            ],
            key=lambda f: f.get("distance_km", 10.0),
        )
        remaining = total
        for f in compat:
            avail = max(0.0, f["capacity_kg"] - f.get("current_load_kg", 0.0))
            if avail <= 0:
                continue
            alloc = min(remaining, avail)
            allocations[f["id"]] += alloc
            remaining -= alloc
            if remaining <= 0:
                break
        if remaining > 0:
            overflow[wtype] = remaining

    return _build_result_summary(facilities, allocations, overflow, streams, [], [])


def _build_result_summary(facilities, allocations, overflow, streams, pairs, x_allocs):
    """Calculate operational costs, carbon impact, and static comparison baseline."""
    total_waste = sum(tot for _, tot in streams)
    tot_overflow = sum(overflow.values())
    total_cap = sum(f["capacity_kg"] for f in facilities if f.get("status") == "online")

    # Dynamic Transport Cost & Carbon
    transport_cost = 0.0
    carbon_emissions = 0.0
    routes = []

    for f in facilities:
        fid = f["id"]
        alloc_kg = allocations.get(fid, 0.0)
        if alloc_kg > 0:
            dist = f.get("distance_km", 5.0)
            cost_per_ton = f.get("cost_per_ton", 350.0)
            c_factor = f.get("carbon_factor_kg", 0.04)

            t_cost = (alloc_kg / 1000.0 * cost_per_ton) + (dist * 18.0)
            c_kg = (alloc_kg * c_factor) + (dist * 0.25)
            transport_cost += t_cost
            carbon_emissions += c_kg

            routes.append(
                {
                    "facility_id": fid,
                    "facility_name": f.get("name", fid),
                    "allocated_kg": alloc_kg,
                    "distance_km": dist,
                    "cost_inr": t_cost,
                    "carbon_kg": c_kg,
                }
            )

    # Static baseline estimation for comparison
    static_overflow = max(0.0, total_waste - total_cap)
    static_cost = (total_waste / 1000.0 * 420.0) + 1200.0
    static_carbon = total_waste * 0.08

    return {
        "allocations": allocations,
        "overflow": overflow,
        "total_overflow": tot_overflow,
        "total_allocated": total_waste - tot_overflow,
        "total_waste": total_waste,
        "total_capacity": total_cap,
        "transport_cost_inr": transport_cost,
        "carbon_emissions_kg": carbon_emissions,
        "static_overflow": static_overflow,
        "static_cost_inr": static_cost,
        "static_carbon_kg": static_carbon,
        "cost_saved_inr": max(0.0, static_cost - transport_cost),
        "carbon_saved_kg": max(0.0, static_carbon - carbon_emissions),
        "routes": routes,
    }


def total_overflow(overflow):
    """Sum overflow values across streams."""
    return sum(overflow.values())


def fixed_allocation_overflow(total_waste, total_capacity):
    """Calculate fixed un-rebalanced baseline overflow."""
    return max(0.0, total_waste - total_capacity)


def reduction_pct(fixed_overflow, optimized_overflow):
    """Calculate percentage reduction in overflow."""
    if fixed_overflow <= 0:
        return 0.0
    return (fixed_overflow - optimized_overflow) / fixed_overflow * 100.0


# =========================================================================
# SMART ALLOCATION DASHBOARD UI
# =========================================================================


def render_smart_allocation_page(palette, wet_total, dry_total):
    """Render the full interactive Smart Waste Reallocation Console."""
    p = palette
    facilities = db.get_all_facilities(include_offline=True)

    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-left:4px solid {p["accent"]};
                    border-radius:8px; padding:18px 22px; margin-bottom:20px;">
            <div style="font-size:1.15rem; font-weight:800; color:{p["text"]};">⚡ Multi-Objective Dynamic Waste Reallocation Solver</div>
            <div style="font-size:0.75rem; color:{p["muted"]}; margin-top:4px;">
                High-performance linear programming (HiGHS LP) solver optimizing municipal waste routing across surviving plants in real-time.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Objective Selection and Parameter Controls
    col_obj1, col_obj2 = st.columns([2, 1])
    with col_obj1:
        obj_choice = st.selectbox(
            "Target Optimization Objective",
            ["balanced", "min_overflow", "min_cost", "min_carbon"],
            format_func=lambda x: {
                "balanced": "⚖️ Balanced Optimization (Minimize Overflow, Cost & Emissions)",
                "min_overflow": "🚨 Minimum Overflow (Heavy Penalty on Unprocessed Waste)",
                "min_cost": "💰 Minimum Transportation Cost (Shortest Route & Plant Fees)",
                "min_carbon": "🌿 Minimum Carbon Footprint (Lowest Transport & Process CO₂)",
            }[x],
        )
    with col_obj2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        run_solver = st.button(
            "🚀 Run Dynamic Solver", key="btn_run_lp_solver", use_container_width=True
        )

    # Execute Solver
    res = optimize_multi_objective(
        facilities, wet_total, dry_total, objective=obj_choice
    )

    # 2. Before vs After Impact KPIs
    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="m-card"><div class="m-label">📊 Predicted Waste</div><div class="m-value">{res["total_waste"] / 1000:.2f} Tons</div></div>
            <div class="m-card green"><div class="m-label">🏭 Active Capacity</div><div class="m-value">{res["total_capacity"] / 1000:.2f} Tons</div></div>
            <div class="m-card hero"><div class="m-label">🚨 Optimized Overflow</div><div class="m-value {"red" if res["total_overflow"] > 0 else "green"}">{res["total_overflow"] / 1000:.2f} Tons</div></div>
            <div class="m-card purple"><div class="m-label">💰 Estimated Cost</div><div class="m-value">{res["transport_cost_inr"]:,.0f} ₹</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Before vs After Comparison Charts (Plotly)
    col_c1, col_c2 = st.columns([1, 1])

    with col_c1:
        st.markdown(
            '<div class="sec-title">🛑 Overflow Comparison: Fixed vs WasteGrid</div>',
            unsafe_allow_html=True,
        )
        fig_ovf = go.Figure(
            data=[
                go.Bar(
                    name="Static Fixed Routing",
                    x=["Overflow"],
                    y=[res["static_overflow"] / 1000],
                    marker_color=p["accent"],
                ),
                go.Bar(
                    name="WasteGrid LP Solver",
                    x=["Overflow"],
                    y=[res["total_overflow"] / 1000],
                    marker_color=p["success"],
                ),
            ]
        )
        fig_ovf.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=p["text"],
            height=250,
            margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title="Tons (T)",
        )
        st.plotly_chart(fig_ovf, use_container_width=True)

    with col_c2:
        st.markdown(
            '<div class="sec-title">💰 Cost & Carbon Savings Comparison</div>',
            unsafe_allow_html=True,
        )
        fig_savings = go.Figure(
            data=[
                go.Bar(
                    name="Static Routing",
                    x=["Cost (₹ x100)", "CO₂ (kg)"],
                    y=[res["static_cost_inr"] / 100, res["static_carbon_kg"]],
                    marker_color=p["muted"],
                ),
                go.Bar(
                    name="WasteGrid LP",
                    x=["Cost (₹ x100)", "CO₂ (kg)"],
                    y=[res["transport_cost_inr"] / 100, res["carbon_emissions_kg"]],
                    marker_color=p["blue"],
                ),
            ]
        )
        fig_savings.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=p["text"],
            height=250,
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_savings, use_container_width=True)

    # 4. Proposed Transfer Route Allocation Plan Table
    st.markdown(
        '<div class="sec-title">🚚 PROPOSED TRANSFER ROUTES & FACILITY INTAKE QUOTAS</div>',
        unsafe_allow_html=True,
    )

    route_rows = []
    for r in res["routes"]:
        fid = r["facility_id"]
        fac = next((f for f in facilities if f["id"] == fid), {})
        cap = fac.get("capacity_kg", 1)
        util = (r["allocated_kg"] / cap * 100) if cap > 0 else 0

        route_rows.append(
            f"""<tr>
                <td><b>Plant {fid}</b></td>
                <td>{r["facility_name"]}</td>
                <td><b>{r["allocated_kg"]:,.0f} kg</b></td>
                <td>{cap:,.0f} kg ({util:.1f}%)</td>
                <td>{r["distance_km"]} km</td>
                <td>{r["cost_inr"]:,.0f} ₹</td>
                <td>{r["carbon_kg"]:.1f} kg CO₂</td>
                <td><span class="fc-pill safe">✓ Approved Match</span></td>
            </tr>"""
        )

    st.markdown(
        f"""<div class="fc-table-wrap">
            <table class="fc-table">
                <thead><tr>
                    <th>Facility ID</th><th>Facility Name</th><th>Allocated Intake</th><th>Plant Capacity</th>
                    <th>Distance</th><th>Route Cost</th><th>Emissions</th><th>Feasibility</th>
                </tr></thead>
                <tbody>{"".join(route_rows)}</tbody>
            </table>
        </div>""",
        unsafe_allow_html=True,
    )

    # 5. Administrative Approval & Application Workflow
    st.markdown("<br>", unsafe_allow_html=True)
    col_app1, col_app2 = st.columns([3, 1])
    with col_app1:
        st.markdown(
            f"""<div style="font-size:0.75rem; color:{p["muted"]};">
                Review the proposed allocation matrix above. Authorized municipal authorities can approve and commit
                this allocation to update live plant hopper levels, vehicle dispatch targets, and audit ledgers.
            </div>""",
            unsafe_allow_html=True,
        )
    with col_app2:
        if st.button(
            "✅ Approve & Apply Allocation",
            key="btn_approve_allocation",
            use_container_width=True,
        ):
            user = st.session_state.get("authenticated_user", {}).get(
                "username", "municipality_admin"
            )
            # Update facility current load in DB
            for fid, alloc_kg in res["allocations"].items():
                db.update_facility_load(fid, alloc_kg)
            # Save allocation run
            db.save_allocation_run(
                obj_choice,
                res["total_waste"],
                res["total_capacity"],
                res["total_overflow"],
                res["allocations"],
                user,
                res["transport_cost_inr"],
                res["carbon_saved_kg"],
            )
            db.add_audit_log(
                user,
                "ALLOCATION_APPROVED",
                f"Approved {obj_choice} allocation for {res['total_waste']} kg waste",
            )
            st.session_state.allocations = res["allocations"]
            st.session_state.overflow = res["overflow"]
            st.session_state.reoptimized = True
            st.success(
                "✅ Allocation plan officially approved and dispatched to live municipal grid!"
            )
            st.rerun()
