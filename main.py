
# currentWorkingDirectory = "D:\\BHT_Class\\Advance_Software\\Project\\berlingeoheatmap\\"
# currentWorkingDirectory = "/mount/src/berlingeoheatmap1/"

# -----------------------------------------------------------------------------
import os
currentWorkingDirectory = os.path.dirname(os.path.abspath(__file__))
os.chdir(currentWorkingDirectory)
print("Current working directory\n" + os.getcwd())

import pandas                        as pd
from core import methods             as m1
from core import HelperTools         as ht

from config                          import pdict

import streamlit as st

from src.malfunction.ui.malfunction_ui import show_malfunction_page, has_open_malfunctions
from src.malfunction.ui.malfunction_ui import show_malfunction_page
from src.rating.ui.rating_ui import show_rating_page

# -----------------------------------------------------------------------------
@ht.timer
def main():
    """Main: Generation of Streamlit App for visualizing electric charging stations & residents in Berlin"""

    # --- top-level menu ------------------------------------------------------
    st.sidebar.title("Menu")
    page = st.sidebar.radio("Go to", ("Map", "Ratings", "Malfunction"))

    if has_open_malfunctions():
        st.warning(
            " Some charging stations currently have reported malfunctions." " Please checkout malfunction station before visiting. ", icon="⚠️"
        )

    # Load raw geodata (postal code polygons)
    df_geodat_plz   = pd.read_csv(os.path.join("datasets", pdict["file_geodat_plz"]), sep=';', encoding='latin-1')
    
    # Load and preprocess electric charging station dataset
    df_lstat        = pd.read_csv(os.path.join("datasets", pdict["file_lstations"]), sep=';', encoding='utf-8', header=0)
    df_lstat2       = m1.preprop_lstat(df_lstat, df_geodat_plz, pdict)
    gdf_lstat3      = m1.count_plz_occurrences(df_lstat2)

    # for KW specific counts
    gdf_lstat3_kw   = m1.count_plz_by_kw(df_lstat2)    
    
    # Load and preprocess residents dataset
    df_residents    = pd.read_csv(os.path.join("datasets", pdict["file_residents"]), encoding='latin-1')
    gdf_residents2  = m1.preprop_resid(df_residents, df_geodat_plz, pdict)
    
# -----------------------------------------------------------------------------------------------------------------------
    # Start Streamlit map visualization
    # --- choose page ---------------------------------------------------------
    if page == "Map":
        m1.make_streamlit_electric_Charging_resid(
            gdf_lstat3,
            gdf_residents2,
            gdf_lstat3_kw
        )
    elif page == "Ratings":
        show_rating_page(df_lstat)
    else: # Malfunction
        show_malfunction_page(df_lstat) # pass stations dataset to build station choices

if __name__ == "__main__": 
    main()

