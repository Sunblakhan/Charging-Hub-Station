import os
import sqlite3
from uuid import UUID

import streamlit as st
import pandas as pd
import time
from src.malfunction.application.services.MalfunctionService import MalfunctionService
from src.malfunction.infrastructure.repositories.IncidentRepository import IncidentRepository


def _get_db_connection() -> sqlite3.Connection:
    # base dir is the folder where main.py is
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # go up from src/malfunction/ui to project root
    project_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))
    db_path = os.path.join(project_root, "malfunction.db")

    # ensure directory exists (it does: project_root)
    return sqlite3.connect(db_path)

def has_open_malfunctions() -> bool:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))
    db_path = os.path.join(project_root, "malfunction.db")

    if not os.path.exists(db_path):
        return False

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        """
        SELECT COUNT(*) AS n
        FROM incidents
        WHERE is_valid = 1 AND is_solved = 0
        """,
        conn,
    )
    conn.close()
    return int(df["n"][0]) > 0

def _get_malfunction_service() -> MalfunctionService:
    conn = _get_db_connection()
    repo = IncidentRepository(conn)
    return MalfunctionService(repo)


def show_malfunction_page(df_lstat):
    st.title("🔧 Malfunction Management")

    # 1. Get current user and service
    user = st.session_state.get('user')
    service = _get_malfunction_service()

    # =========================================================================
    # VIEW A: MANAGEMENT MODE (For Operators AND Admins)
    # =========================================================================
    if user and (user.role == 'operator' or user.role == 'admin'):
        
        # --- HEADER & DATA FETCHING ---
        if user.role == 'admin':
            st.info("🛡️ **Admin Mode:** Viewing all malfunction reports across Berlin.")
            incidents = service.get_all_incidents()
        else:
            # Operator Logic
            if not user.station_label:
                st.error("Operator has no assigned station. Contact Admin.")
                return
            st.info(f"👤 **Operator Mode:** Managing reports for **{user.station_label}**")
            incidents = service.get_incidents_for_station(user.station_label)

        # Create Tabs
        tab_manage, tab_report = st.tabs(["📋 Manage Reports", "➕ Submit New Report"])

        # --- TAB 1: MANAGE REPORTS (Editable Table) ---
        with tab_manage:
            if not incidents:
                st.info("No reports found.")
            else:
                # Prepare Data for Table
                data = []
                for inc in incidents:
                    data.append({
                        "ID": str(inc.id),
                        "Station": inc.station_label.value, # Helpful for Admin to see which station
                        "Reporter": inc.reporter_name.value,
                        "Description": inc.description.value,
                        "Valid?": inc.is_valid,
                        "Solved?": inc.is_solved,
                        "Status": inc.status
                    })
                
                df_incidents = pd.DataFrame(data)

                st.caption("Tick the boxes to update status. Click 'Save Changes' to apply.")
                
                # Configure Columns (Show Station column only if Admin)
                col_config = {
                        "ID": st.column_config.TextColumn(disabled=True),
                        "Station": st.column_config.TextColumn(disabled=True, width="medium"),
                        "Reporter": st.column_config.TextColumn(disabled=True),
                        "Description": st.column_config.TextColumn(disabled=True, width="large"),
                        "Valid?": st.column_config.CheckboxColumn("Valid?", help="Is this a real issue?"),
                        "Solved?": st.column_config.CheckboxColumn("Solved?", help="Is it fixed?"),
                        "Status": st.column_config.TextColumn(disabled=True),
                }

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
                    st.success("✅ Database updated successfully!")
                    time.sleep(1)
                    st.rerun()

        # --- TAB 2: SUBMIT NEW REPORT ---
        with tab_report:
            st.subheader("Submit Internal Report")
            with st.form("internal_report_form"):
                name = st.text_input("Reporter Name", value="Admin" if user.role == 'admin' else "Operator") 
                email = st.text_input("Reporter Email", value=user.email, disabled=True)
                
                # If Admin, allow selecting ANY station. If Operator, lock to theirs.
                if user.role == 'admin':
                    # Filter Berlin stations for dropdown
                    df_berlin = df_lstat[df_lstat["station_label"].astype(str).str.contains(r' Berlin\s*$', case=False, regex=True, na=False)]
                    admin_station_options = sorted(df_berlin["station_label"].unique())
                    station_input = st.selectbox("Select Station", admin_station_options)
                else:
                    # Lock for Operator
                    station_input = st.text_input("Station", value=user.station_label, disabled=True)
                
                description = st.text_area("Problem description")
                submitted = st.form_submit_button("Submit Report")

            if submitted:
                try:
                    # For operators, station_input is just the string. For admin selectbox, it's the same.
                    final_station = station_input if user.role == 'admin' else user.station_label
                    
                    incident_id = service.submit_report(name, email, final_station, description)
                    st.success(f"Report submitted! ID: {incident_id}")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # =========================================================================
    # VIEW B: PUBLIC USER (Report Only)
    # =========================================================================
    else:
        # Standard Public View Logic
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



def _load_valid_incidents(conn: sqlite3.Connection):

    df = pd.read_sql_query(
        """
        SELECT id,
               reporter_name,
               reporter_email,
               station_label,
               description,
               points_awarded,
               status
        FROM incidents
        WHERE is_valid = 1
        ORDER BY rowid DESC
        """,
        conn,
    )
    return df
