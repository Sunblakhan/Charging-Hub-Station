import sqlite3
import streamlit as st
import pandas as pd

from src.rating.application.services.RatingService import RatingService, StationNotInBerlinError
from src.rating.application.services.real_station_lookup import RealStationLookup
from src.rating.infrastructure.repositories.SqliteRatingRepository import SqliteRatingRepository


def show_rating_page(df_lstat):
    """
    Simple UI for submitting a rating.
    df_lstat is your preprocessed charging-station dataframe (only Berlin rows).
    """
    st.title("Rate a Charging Station")

    section = st.radio(
        "Select view",
        ("Rate Station", "View Station Ratings"),
        horizontal=True,
    )

    # ------------------------------------------------------------------ #
    # Section 1: Rate Station
    # ------------------------------------------------------------------ #
    if section == "Rate Station":
        st.subheader("Submit a Rating")

        # Build station options from your dataframe (labels end with 'Berlin')
        station_labels = sorted(df_lstat["station_label"].unique())  # adapt column name
        selected_station = st.selectbox("Select station", station_labels, placeholder="Choose a station...", index = None)

        name = st.text_input("Name")
        email = st.text_input("Email")
        stars = st.slider("Stars", min_value=1, max_value=5, step=1)
        review = st.text_area("Review (optional)")

        if st.button("Submit rating"):
            # wire up RatingService with SQLite + station lookup

            if selected_station is None:
                st.error("Please choose a station before submitting.")
                return

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
                # from value objects (email, name, stars, etc.)
                st.error(f"Invalid input: {e}")
            else:
                st.success("Rating saved successfully!")
                st.write(f"Average rating for this station: {result['average_stars']:.2f}")

        # ------------------------------------------------------------------ #
        # Section 2: View Station Ratings   
        # ------------------------------------------------------------------ #
    else:
        # st.subheader("View Station Ratings")

        # conn = sqlite3.connect("ratings.db")
        # repo = SqliteRatingRepository(conn)

        # ratings = repo.all()

        # if not ratings:
        #     st.info("No ratings stored yet.")
        #     return

        # # Build DataFrame from domain entities
        # data = []
        # for r in ratings:
        #     data.append(
        #         {
        #             "Station": r.station_label.value,
        #             "Name": r.name.value,
        #             # "Email": r.email.value,
        #             "Stars": r.stars.value,
        #             "Review": r.review.value,
        #             # "Created at": r.created_at.strftime("%Y-%m-%d %H:%M"),
        #         }
        #     )

        # df = pd.DataFrame(data)

        # # --- station filter ---
        # station_options = ["<All stations>"] + sorted(df["Station"].unique())
        # selected_station = st.selectbox(
        #     "Filter by station",
        #     station_options,
        #     index=0,
        # )

        # if selected_station != "<All stations>":
        #     df = df[df["Station"] == selected_station]

        # # --- coloring by stars ---
        # def color_row(row):
        #     stars = row["Stars"]
        #     if stars >= 4:
        #         return ["background-color: #d4edda"] * len(row)  # green
        #     elif stars == 3:
        #         return ["background-color: #fff3cd"] * len(row)  # yellow
        #     else:
        #         return ["background-color: #f8d7da"] * len(row)  # light red

        # st.dataframe(df.style.apply(color_row, axis=1))

        st.subheader("View Station Ratings")

        conn = sqlite3.connect("ratings.db")
        repo = SqliteRatingRepository(conn)

        ratings = repo.all()

        if not ratings:
            st.info("No ratings stored yet.")
            return

        # Build full ratings DataFrame (one row per rating)
        rows = []
        for r in ratings:
            rows.append(
                {
                    "Station": r.station_label.value,
                    "Name": r.name.value,
                    "Stars": r.stars.value,
                    "Review": r.review.value,
                }
            )
        df_all = pd.DataFrame(rows)

        # --- station filter selectbox ---
        station_options = ["<All stations>"] + sorted(df_all["Station"].unique())
        selected_station = st.selectbox(
            "Choose station",
            station_options,
            index=0,
        )

        # --- case 1: no specific station -> show one row per station with average ---
        if selected_station == "<All stations>":
            df_avg = (
                df_all.groupby("Station", as_index=False)["Stars"]
                .mean()
                .rename(columns={"Stars": "Average Stars"})
            )

            df_avg["Average Stars"] = df_avg["Average Stars"].round(2)

            def color_row_avg(row):
                avg = row["Average Stars"]
                if avg >= 4:
                    return ["background-color: #d4edda"] * len(row)
                elif avg >= 3:
                    return ["background-color: #fff3cd"] * len(row)
                else:
                    return ["background-color: #f8d7da"] * len(row)

            styled = (
                df_avg.style
                .format({"Average Stars": "{:.2f}"})   # 2 decimal places for display
                .apply(color_row_avg, axis=1)          # numeric comparisons work
            )

            st.dataframe(styled)

        # --- case 2: specific station selected -> show avg + all ratings with name/review ---
        else:
            df_station = df_all[df_all["Station"] == selected_station]

            avg_stars = df_station["Stars"].mean()

            st.markdown(f"**Station:** {selected_station}")
            st.markdown(f"**Average rating:** {avg_stars:.2f} ⭐")

            def color_row_detail(row):
                stars = row["Stars"]
                if stars >= 4:
                    return ["background-color: #d4edda"] * len(row)
                elif stars == 3:
                    return ["background-color: #fff3cd"] * len(row)
                else:
                    return ["background-color: #f8d7da"] * len(row)

            # only show name, stars, review for individual ratings
            df_detail = df_station[["Name", "Stars", "Review"]]
            st.dataframe(df_detail.style.apply(color_row_detail, axis=1))
