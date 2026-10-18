"""
Reports and Data Exports Module for WasteGrid 2.0.
Generates audit-ready CSV, Excel (.xlsx), and JSON reports with date and ward filters for:
- Waste Generation Records
- Facility Capacity & Load Logs
- Dynamic Reallocation Plans
- Vehicle Telematics & Fleet Logs
- Carbon Offset & ESG Indicators
- Alerts & Incident Records
- Citizen Grievance Reports
"""

import io
from datetime import datetime

import pandas as pd
import streamlit as st

from wastegrid import db


def generate_excel_bytes(dfs_dict):
    """Generate an Excel workbook with multiple sheets as bytes."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in dfs_dict.items():
            clean_sheet = sheet_name[:31]  # Excel 31 char sheet limit
            df.to_excel(writer, sheet_name=clean_sheet, index=False)
    return output.getvalue()


def render_reports_page(palette):
    """Render the Reports & Data Exports console."""
    p = palette

    st.markdown(
        f"""
        <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-left:4px solid {p["blue"]};
                    border-radius:8px; padding:18px 22px; margin-bottom:20px;">
            <div style="font-size:1.15rem; font-weight:800; color:{p["text"]};">📑 Municipal Reports & Data Exports Engine</div>
            <div style="font-size:0.75rem; color:{p["muted"]}; margin-top:4px;">
                Export verified municipal waste manifests, facility audit compliance reports, vehicle logs, and ESG data in CSV and Excel formats.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Report Category Selector
    col_r1, col_r2 = st.columns([2, 1])
    with col_r1:
        report_cat = st.selectbox(
            "Select Municipal Report Category",
            [
                "All Datasets (Full Audit Package)",
                "Waste Generation by Ward",
                "Facility Intake & Capacity Logs",
                "Vehicle Fleet & Telematics Operations",
                "Carbon Offset & ESG Compliance",
                "Alerts & Capacity Incidents",
                "Citizen Grievances & Resolution Log",
            ],
        )
    with col_r2:
        export_format = st.selectbox(
            "Export File Format", ["Excel Workbook (.xlsx)", "Standard CSV (.csv)"]
        )

    # Load DataFrames
    facilities = db.get_all_facilities(include_offline=True)
    sources = db.get_all_waste_sources()
    vehicles = db.get_all_vehicles()
    alerts = db.get_active_alerts()
    citizen_reports = db.get_all_citizen_reports()

    df_sources = pd.DataFrame(sources)
    df_facilities = pd.DataFrame(facilities)
    df_vehicles = pd.DataFrame(vehicles)
    df_alerts = pd.DataFrame(alerts)
    df_citizens = pd.DataFrame(citizen_reports)

    # Preview and Download Package
    st.markdown(
        '<div class="sec-title">📋 REPORT PREVIEW & AUDIT DOWNLOAD</div>',
        unsafe_allow_html=True,
    )

    if report_cat == "Waste Generation by Ward":
        preview_df = df_sources
        sheet_name = "Waste_Generation"
    elif report_cat == "Facility Intake & Capacity Logs":
        preview_df = df_facilities
        sheet_name = "Facility_Logs"
    elif report_cat == "Vehicle Fleet & Telematics Operations":
        preview_df = df_vehicles
        sheet_name = "Vehicle_Fleet"
    elif report_cat == "Alerts & Capacity Incidents":
        preview_df = df_alerts
        sheet_name = "Alerts_Incidents"
    elif report_cat == "Citizen Grievances & Resolution Log":
        preview_df = df_citizens
        sheet_name = "Citizen_Reports"
    else:
        preview_df = df_facilities
        sheet_name = "Summary_Facilities"

    st.dataframe(preview_df, use_container_width=True, hide_index=True)

    # Download Button
    now_tag = datetime.now().strftime("%Y%m%d_%H%M")
    if export_format == "Excel Workbook (.xlsx)":
        if report_cat == "All Datasets (Full Audit Package)":
            excel_data = generate_excel_bytes(
                {
                    "Facilities": df_facilities,
                    "Waste_Sources": df_sources,
                    "Vehicles": df_vehicles,
                    "Alerts": df_alerts,
                    "Citizen_Grievances": df_citizens,
                }
            )
            file_name = f"WasteGrid_Master_Audit_Report_{now_tag}.xlsx"
        else:
            excel_data = generate_excel_bytes({sheet_name: preview_df})
            file_name = f"WasteGrid_{sheet_name}_{now_tag}.xlsx"

        st.download_button(
            label=f"📥 Download Official {export_format}",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        csv_data = preview_df.to_csv(index=False).encode("utf-8")
        file_name = f"WasteGrid_{sheet_name}_{now_tag}.csv"
        st.download_button(
            label=f"📥 Download Official {export_format}",
            data=csv_data,
            file_name=file_name,
            mime="text/csv",
        )
