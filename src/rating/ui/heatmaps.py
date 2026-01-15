"""
Streamlit/Folium heatmaps for charging stations and residents.
"""
import folium
from branca.colormap import LinearColormap
import streamlit as st
from streamlit_folium import folium_static


def make_streamlit_electric_charging_resid(dframe_stations, dframe_residents, dframe_kw):
    """Render heatmaps for residents and charging stations in Streamlit."""
    dframe1 = dframe_stations.copy()
    dframe2 = dframe_residents.copy()
    dframe3 = dframe_kw.copy()

    st.title("Heatmaps: Electric Charging Stations and Residents")
    layer_selection = st.radio("Select Layer", ("Residents", "Charging_Stations", "Charging Stations_KW_Grouped"))
    m = folium.Map(location=[52.52, 13.40], zoom_start=10)

    if layer_selection == "Residents":
        color_map = LinearColormap(colors=["yellow", "red"], vmin=dframe2["Einwohner"].min(), vmax=dframe2["Einwohner"].max())
        for _, row in dframe2.iterrows():
            folium.GeoJson(
                row["geometry"],
                style_function=lambda x, color=color_map(row["Einwohner"]): {
                    "fillColor": color,
                    "color": "black",
                    "weight": 1,
                    "fillOpacity": 0.7,
                },
                tooltip=f"PLZ: {row['PLZ']}, Einwohner: {row['Einwohner']}",
            ).add_to(m)

    elif layer_selection == "Charging_Stations":
        color_map = LinearColormap(colors=["yellow", "red"], vmin=dframe1["Number"].min(), vmax=dframe1["Number"].max())
        for _, row in dframe1.iterrows():
            folium.GeoJson(
                row["geometry"],
                style_function=lambda x, color=color_map(row["Number"]): {
                    "fillColor": color,
                    "color": "black",
                    "weight": 1,
                    "fillOpacity": 0.7,
                },
                tooltip=f"PLZ: {row['PLZ']}, Number: {row['Number']}",
            ).add_to(m)

    else:
        unique_kw = sorted(dframe3["KW"].unique())
        selected_kw = st.selectbox("Select KW", unique_kw)
        df_kw = dframe3[dframe3["KW"] == selected_kw]
        color_map = LinearColormap(colors=["yellow", "red"], vmin=df_kw["Number"].min(), vmax=df_kw["Number"].max())

        for _, row in df_kw.iterrows():
            folium.GeoJson(
                row["geometry"],
                style_function=lambda x, color=color_map(row["Number"]): {
                    "fillColor": color,
                    "color": "black",
                    "weight": 1,
                    "fillOpacity": 0.7,
                },
                tooltip=f"PLZ: {row['PLZ']}, Stations: {row['Number']}, KW: {row['KW']}",
            ).add_to(m)

    color_map.add_to(m)
    folium_static(m, width=800, height=600)
