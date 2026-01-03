import os
import time
import sqlite3
from uuid import UUID

import streamlit as st
import pandas as pd

from src.malfunction.application.services.MalfunctionService import MalfunctionService
from src.malfunction.infrastructure.repositories.IncidentRepository import IncidentRepository


def _get_db_connection() -> sqlite3.Connection:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))
    db_path = os.path.join(project_root, "malfunction.db")
    return sqlite3.connect(db_path)

def has_open_malfunctions() -> bool:
    # (Keep your existing has_open_malfunctions code here)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))
    db_path = os.path.join(project_root, "malfunction.db")

    if not os.path.exists(db_path):
        return False

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT COUNT(*) AS n FROM incidents WHERE is_valid = 1 AND is_solved = 0", conn)
    conn.close()
    return int(df["n"][0]) > 0

def _get_malfunction_service() -> MalfunctionService:
    conn = _get_db_connection()
    repo = IncidentRepository(conn)
    return MalfunctionService(repo)


def show_malfunction_page(df_lstat):
    st.title("🔧 Malfunction Management")

    user = st.session_state.get('user')
    service = _get_malfunction_service()

    # =========================================================================
    # INTERNAL VIEW (Admin or Operator)
    # =========================================================================
    if user and (user.role == 'operator' or user.role == 'admin'):
        
        # --- 1. SETUP DATA & TABS ---
        incidents = []
        tab_manage = None
        tab_report = None

        if user.role == 'admin':
            st.info("🛡️ **Admin Mode:** View and Manage all reports.")
            incidents = service.get_all_incidents()
            # Admin CANNOT submit reports -> Only 1 Tab
            tab_manage, = st.tabs(["📋 Manage Reports"]) 
        
        else: # Operator
            if not user.station_label:
                st.error("Operator has no assigned station.")
                return
            st.info(f"👤 **Operator Mode:** Managing **{user.station_label}**")
            incidents = service.get_incidents_for_station(user.station_label)
            # Operator CAN submit reports -> 2 Tabs
            tab_manage, tab_report = st.tabs(["📋 Manage Reports", "➕ Submit New Report"])


        # --- 2. TAB: MANAGE REPORTS (Shared) ---
        with tab_manage:
            if not incidents:
                st.info("No reports found.")
            else:
                data = []
                for inc in incidents:
                    data.append({
                        "ID": str(inc.id),
                        "Station": inc.station_label.value,
                        "Reporter": inc.reporter_name.value,
                        "Description": inc.description.value,
                        "Valid?": inc.is_valid,
                        "Solved?": inc.is_solved,
                        "Status": inc.status
                    })
                
                df_incidents = pd.DataFrame(data)

                # Configure Columns
                col_config = {
                        "ID": st.column_config.TextColumn(disabled=True),
                        "Station": st.column_config.TextColumn(disabled=True, width="medium"),
                        "Reporter": st.column_config.TextColumn(disabled=True),
                        "Description": st.column_config.TextColumn(disabled=True, width="large"),
                        "Valid?": st.column_config.CheckboxColumn("Valid?", help="Is this a real issue?"),
                        "Solved?": st.column_config.CheckboxColumn("Solved?", help="Is it fixed?"),
                        "Status": st.column_config.TextColumn(disabled=True),
                }

                st.caption("Tick the boxes to update status.")
                edited_df = st.data_editor(
                    df_incidents,
                    column_config=col_config,
                    hide_index=True,
                    key="malfunction_editor"
                )

                if st.button("💾 Save Changes", type="primary"):
                    for index, row in edited_df.iterrows():
                        service.update_incident_status(
                            incident_id=row["ID"],
                            is_valid=row["Valid?"],
                            is_solved=row["Solved?"]
                        )
                    st.toast("Updated successfully!", icon="✅")
                    time.sleep(1)
                    st.rerun()

        # --- 3. TAB: SUBMIT REPORT (Operator Only) ---
        if tab_report:
            with tab_report:
                st.subheader("Report an issue at your station")
                st.caption("Reports submitted by operators are automatically marked as **Valid**.")
                
                with st.form("operator_report_form"):
                    name = st.text_input("Reporter Name", value="Operator") 
                    email = st.text_input("Reporter Email", value=user.email, disabled=True)
                    st.text_input("Station", value=user.station_label, disabled=True)
                    description = st.text_area("Problem description")
                    
                    submitted = st.form_submit_button("Submit Report")

                if submitted:
                    try:
                        # Auto-Validate: Pass is_valid=True
                        incident_id = service.submit_report(
                            reporter_name=name, 
                            reporter_email=email, 
                            station_label=user.station_label, 
                            description=description,
                            is_valid=True 
                        )
                        st.success(f"Report submitted and validated! ID: {incident_id}")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # =========================================================================
    # PUBLIC VIEW (Regular User)
    # =========================================================================
    else:
        # Regex filter for Berlin
        df_berlin = df_lstat[df_lstat["station_label"].astype(str).str.contains(r' Berlin\s*$', case=False, regex=True, na=False)]
        station_options = sorted(df_berlin["station_label"].unique())

        section = st.radio("Select view", ("Report malfunction", "Malfunction list"), horizontal=True)

        if section == "Report malfunction":
            st.subheader("Submit malfunction report")
            with st.form("malfunction_form"):
                name = st.text_input("Name")
                email = st.text_input("Email")
                station = st.selectbox("Select station", station_options, index=None, placeholder="Choose...")
                description = st.text_area("Problem description")
                submitted = st.form_submit_button("Submit report")

            if submitted:
                try:
                    # Regular user -> is_valid=False (default)
                    incident_id = service.submit_report(name, email, station, description)
                    st.success(f"Report submitted! ID: {incident_id}")
                except Exception as e:
                    st.error(f"Error: {e}")

        else: 
            st.subheader("Current Issues")
            conn = _get_db_connection()
            df = pd.read_sql_query(
                "SELECT station_label as Station, description as Description FROM incidents WHERE is_valid=1 AND is_solved=0", 
                conn
            )
            if df.empty:
                st.info("No active malfunctions reported.")
            else:
                st.dataframe(df, use_container_width=True)