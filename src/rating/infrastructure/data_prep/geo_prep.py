"""
Geospatial data preparation for rating/charging context.
"""
import pandas as pd
import geopandas as gpd
from src.shared.utils.timing import timer


def sort_by_plz_add_geometry(dfr: pd.DataFrame, dfg: pd.DataFrame, pdict: dict) -> gpd.GeoDataFrame:
    dframe = dfr.copy()
    df_geo = dfg.copy()

    sorted_df = (
        dframe.sort_values(by="PLZ")
        .reset_index(drop=True)
        .sort_index()
    )

    sorted_df2 = sorted_df.merge(df_geo, on=pdict["geocode"], how="left")
    sorted_df3 = sorted_df2.dropna(subset=["geometry"])

    sorted_df3["geometry"] = gpd.GeoSeries.from_wkt(sorted_df3["geometry"])
    ret = gpd.GeoDataFrame(sorted_df3, geometry="geometry")
    return ret


@timer
def preprop_lstat(dfr: pd.DataFrame, dfg: pd.DataFrame, pdict: dict) -> gpd.GeoDataFrame:
    """Preprocess Ladesaeulenregister.csv into Berlin PLZ GeoDataFrame."""
    dframe = dfr.copy()
    df_geo = dfg.copy()

    dframe2 = dframe.loc[:, ["Postleitzahl", "Bundesland", "Breitengrad", "Längengrad", "Nennleistung Ladeeinrichtung [kW]"]]
    dframe2.rename(columns={"Nennleistung Ladeeinrichtung [kW]": "KW", "Postleitzahl": "PLZ"}, inplace=True)

    dframe2["Breitengrad"] = dframe2["Breitengrad"].astype(str)
    dframe2["Längengrad"] = dframe2["Längengrad"].astype(str)
    dframe2["Breitengrad"] = dframe2["Breitengrad"].str.replace(",", ".")
    dframe2["Längengrad"] = dframe2["Längengrad"].str.replace(",", ".")

    dframe3 = dframe2[
        (dframe2["Bundesland"] == "Berlin")
        & (dframe2["PLZ"] > 10115)
        & (dframe2["PLZ"] < 14200)
    ]

    ret = sort_by_plz_add_geometry(dframe3, df_geo, pdict)
    return ret


@timer
def count_plz_occurrences(df_lstat2: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Count charging stations per PLZ."""
    result_df = (
        df_lstat2.groupby("PLZ").agg(Number=("PLZ", "count"), geometry=("geometry", "first"))
        .reset_index()
    )
    return result_df


@timer
def count_plz_by_kw(df_lstat2: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Count charging stations per PLZ grouped by KW."""
    result_df = (
        df_lstat2.groupby(["PLZ", "KW"]).agg(Number=("KW", "count"), geometry=("geometry", "first"))
        .reset_index()
    )
    return result_df


@timer
def preprop_resid(dfr: pd.DataFrame, dfg: pd.DataFrame, pdict: dict) -> gpd.GeoDataFrame:
    """Preprocess residents CSV into Berlin PLZ GeoDataFrame."""
    dframe = dfr.copy()
    df_geo = dfg.copy()

    dframe2 = dframe.loc[:, ["plz", "einwohner", "lat", "lon"]]
    dframe2.rename(columns={"plz": "PLZ", "einwohner": "Einwohner", "lat": "Breitengrad", "lon": "Längengrad"}, inplace=True)

    dframe2["Breitengrad"] = dframe2["Breitengrad"].astype(str)
    dframe2["Längengrad"] = dframe2["Längengrad"].astype(str)
    dframe2["Breitengrad"] = dframe2["Breitengrad"].str.replace(",", ".")
    dframe2["Längengrad"] = dframe2["Längengrad"].str.replace(",", ".")

    dframe3 = dframe2[
        (dframe2["PLZ"] > 10000)
        & (dframe2["PLZ"] < 14200)
    ]

    ret = sort_by_plz_add_geometry(dframe3, df_geo, pdict)
    return ret
