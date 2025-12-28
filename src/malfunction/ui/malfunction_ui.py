import os
import sqlite3
from uuid import UUID

import streamlit as st
import pandas as pd

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
    """
    Streamlit UI for malfunction reporting and admin-approved list.
    df_lstat: original charging-stations dataframe to build station labels.
    """
    st.title("Charging Station Malfunction")

    service = _get_malfunction_service()

    station_options = sorted(df_lstat["station_label"].unique())  # adapt column name

    service = _get_malfunction_service()


    # ------------------------------------------------------------------ #
    # Radio: choose section
    # ------------------------------------------------------------------ #
    section = st.radio(
        "Select view",
        ("Report malfunction", "Malfunction list"),
        horizontal=True
    )

    # ------------------------------------------------------------------ #
    # Section 1: Report malfunction
    # ------------------------------------------------------------------ #
    if section == "Report malfunction":
        st.subheader("Submit malfunction report")

        with st.form("malfunction_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            station = st.selectbox(
                "Select station",
                station_options,
                placeholder="Choose a station...",
                index=None,
            )
            description = st.text_area("Problem of the station")

            submitted = st.form_submit_button("Submit report")

        if submitted:
            try:
                incident_id = service.submit_report(
                    reporter_name=name,
                    reporter_email=email,
                    station_label=station,
                    description=description,
                )
                st.success(f"Report submitted. Incident ID: {incident_id}")
            except Exception as e:
                st.error(f"Could not submit report: {e}")

    # ------------------------------------------------------------------ #
    # Section 2: Malfunction list (admin side)
    # ------------------------------------------------------------------ #
    else:
        # st.subheader("Approved malfunctions")

        # approve_id_str = st.text_input("Incident ID to approve (admin)")
        # if st.button("Approve report"):
        #     try:
        #         service.validate_report(UUID(approve_id_str))
        #         st.success("Report approved and published.")
        #     except Exception as e:
        #         st.error(f"Could not approve report: {e}")

        # conn = _get_db_connection()
        # df_valid = _load_valid_incidents(conn)
        # if df_valid.empty:
        #     st.info("No approved malfunctions yet.")
        # else:
        #     st.dataframe(df_valid)


        conn = _get_db_connection()

        # Load all reports (or only valid ones, as you prefer)
        df = pd.read_sql_query(
            """
            SELECT id,
                reporter_name,
                reporter_email,
                station_label,
                description,
                is_valid,
                is_solved,
                points_awarded,
                status
            FROM incidents
            WHERE is_valid = 1
            ORDER BY rowid DESC
            """,
            conn,
        )

        st.write("Number of incidents:", len(df))


        if df.empty:
            st.info("No malfunction history found.")
        else:
            # start from original df
            df_view = df.copy()

            # create nicely named columns from the originals
            df_view["Station"] = df_view["station_label"]
            df_view["Description"] = df_view["description"]
            df_view["Solved"] = df_view["is_solved"].astype(bool)

            # now choose only the renamed columns to display
            cols_to_show = ["Station", "Description", "Solved"]
            df_view = df_view[cols_to_show]

            def color_rows(row):
                # here row["Solved"] is bool
                if row["Solved"]:
                    return ["background-color: lightgreen"] * len(row)
                else:
                    return ["background-color: Khaki"] * len(row)

            styled = df_view.style.apply(color_rows, axis=1)

            st.dataframe(styled, use_container_width=True)



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
