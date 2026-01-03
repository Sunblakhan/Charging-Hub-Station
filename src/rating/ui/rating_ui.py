import streamlit as st
import pandas as pd
import sqlite3
import time
from streamlit_star_rating import st_star_rating 

from src.rating.application.services.RatingService import RatingService, StationNotInBerlinError
from src.rating.application.services.real_station_lookup import RealStationLookup
from src.rating.infrastructure.repositories.SqliteRatingRepository import SqliteRatingRepository

def show_rating_page(df_lstat):
    """
    Enhanced UI: Form resets ONLY on successful submission using Dynamic Keys.
    Auto-fills email from logged-in session.
    """
    st.title("⭐ Rate a Charging Station")
    st.markdown("Share your experience to help other EV drivers in Berlin.")

    # 1. Get Logged-in User
    user = st.session_state.get('user')
    user_email = user.email if user else ""

    # Initialize a session state counter to manage form resets
    if "rating_form_id" not in st.session_state:
        st.session_state.rating_form_id = 0

    tab_rate, tab_view = st.tabs(["📝 Rate Station", "📊 View Ratings"])

    # ------------------------------------------------------------------ #
    # TAB 1: Rate Station
    # ------------------------------------------------------------------ #
    with tab_rate:
        st.subheader("Submit your Review")
        
        # Station Selection (Strict Berlin Filter)
        df_berlin_only = df_lstat[
            df_lstat["station_label"].astype(str).str.contains(r' Berlin\s*$', case=False, regex=True, na=False)
        ]
        
        station_labels = sorted(df_berlin_only["station_label"].unique())

        selected_station = st.selectbox(
            "Select a Station", 
            station_labels, 
            index=None, 
            placeholder="Search for a station address..."
        )

        if selected_station:
            st.info(f"You are rating: **{selected_station}**")

        st.divider()

        # Form Logic
        with st.form("rating_form", clear_on_submit=False):
            
            # Helper variable for dynamic keys
            form_id = st.session_state.rating_form_id
            
            col1, col2 = st.columns(2)
            with col1:
                # Name is still manual (User object doesn't store Full Name)
                name = st.text_input("Your Name", placeholder="e.g. Selcan Ipek Ugay", key=f"rate_name_{form_id}")
            with col2:
                # --- AUTO-FILL EMAIL ---
                # We use value=user_email to pre-fill it
                # We use disabled=True so they can't change it
                email = st.text_input("Your Email", value=user_email, disabled=True, key=f"rate_email_{form_id}")

            stars = st_star_rating(
                label="How was your charging experience?",
                maxValue=5,
                defaultValue=3,
                key=f"rate_stars_{form_id}", 
                size=30,
                emoticons=False
            )

            review = st.text_area("Write a Review", placeholder="Was it fast? Was it blocked? Let us know...", height=100, key=f"rate_review_{form_id}")

            submitted = st.form_submit_button("🚀 Submit Rating", type="primary", use_container_width=True)

            if submitted:
                # --- VALIDATION ---
                if not selected_station:
                    st.error("⚠️ Please choose a station above before submitting.")
                
                # Email validation is less critical now since it comes from login, but good to keep
                elif "@" not in email or "." not in email:
                    st.error("⚠️ Invalid email detected.")

                else:
                    # --- DATABASE SAVE ---
                    conn = sqlite3.connect("ratings.db")
                    repo = SqliteRatingRepository(conn)
                    station_lookup = RealStationLookup()
                    service = RatingService(repo, station_lookup)

                    try:
                        result = service.create_rating(
                            user_name=name,
                            user_email=email,
                            station_label=selected_station,
                            stars=stars,
                            review_text=review if review.strip() else None,
                        )
                    except StationNotInBerlinError:
                        st.error("Selected station is not in Berlin.")
                    except ValueError as e:
                        st.error(f"Invalid input: {e}")
                    else:
                        # --- SUCCESS ---
                        st.toast("Rating submitted successfully!", icon="✅")
                        st.success(f"Thank you! New average: {result['average_stars']:.2f} ⭐")
                        
                        # --- INCREMENT ID TO RESET FORM ---
                        st.session_state.rating_form_id += 1
                        time.sleep(1.5)
                        st.rerun()

    # ------------------------------------------------------------------ #
    # TAB 2: View Station Ratings (No changes needed)
    # ------------------------------------------------------------------ #
    with tab_view:
        st.subheader("Station Insights")

        conn = sqlite3.connect("ratings.db")
        repo = SqliteRatingRepository(conn)
        ratings = repo.all()

        if not ratings:
            st.info("📭 No ratings stored yet. Be the first to rate!")
            return

        rows = []
        for r in ratings:
            rows.append({
                "Station": r.station_label.value,
                "User": r.name.value,
                "Rating": r.stars.value,
                "Review": r.review.value,
            })
        df_all = pd.DataFrame(rows)

        col_filter, col_metric = st.columns([2, 1])
        
        with col_filter:
            station_options = ["All Stations"] + sorted(df_all["Station"].unique())
            filter_station = st.selectbox("Filter by Station", station_options, index=0)

        if filter_station == "All Stations":
            df_avg = (
                df_all.groupby("Station", as_index=False)["Rating"]
                .mean()
                .rename(columns={"Rating": "Average Stars"})
            )
            
            with col_metric:
                st.metric("Total Reviews", len(df_all), delta="All Time")

            st.dataframe(
                df_avg,
                use_container_width=True,
                column_config={
                    "Average Stars": st.column_config.ProgressColumn(
                        "Average Rating",
                        format="%.2f",
                        min_value=1,
                        max_value=5,
                    ),
                },
                hide_index=True
            )
        else:
            df_station = df_all[df_all["Station"] == filter_station]
            avg_stars = df_station["Rating"].mean()
            
            with col_metric:
                st.metric(label="Station Average", value=f"{avg_stars:.1f} ⭐", delta=f"{len(df_station)} reviews")

            st.dataframe(
                df_station[["User", "Rating", "Review"]],
                use_container_width=True,
                column_config={
                    "Rating": st.column_config.NumberColumn(
                        "Stars",
                        format="%d ⭐"
                    ),
                    "Review": st.column_config.TextColumn(
                        "Comment",
                        width="large"
                    )
                },
                hide_index=True
            )