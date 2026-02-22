# Dashboard code will go here. 

# ideas:
# some sort of plot of income and number of violations or seasonal number of violations but you can toggle it by type of violation
# seasonal trends map where you toggle the months to see which violation types are the most common
# or select a violation type and then toggle for seasonal trends, or select month and it shows most common type

import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
from pathlib import Path
import os

st.set_page_config(layout="wide")

st.title("Chicago Building Violations from 2024-2026 by Category")

# Load Data
@st.cache_data
def load_data():
    current_wd = os.getcwd()
    script_dir = Path(current_wd)
    violations_gdf = gpd.read_file(script_dir / '../data/derived-data/Building_Violations_w_ACS.gpkg')
    violations_gdf = violations_gdf.to_crs(epsg=4326)
    return gdf

gdf = load_data()

# Aggregate to tract level
tract_counts = (
    gdf
    .groupby(["GEOID", "violation_category"])
    .size()
    .reset_index(name="num_violations")
)

# Merge back geometry
tract_map = (
    gdf[["GEOID", "geometry"]]
    .drop_duplicates()
    .merge(tract_counts, on="GEOID")
)

# Sidebar toggle
categories = sorted(tract_map["violation_category"].unique())

selected_category = st.sidebar.selectbox(
    "Select Violation Category",
    categories
)

map_data = tract_map[tract_map["violation_category"] == selected_category]


# Color scaling
max_val = map_data["num_violations"].max()
map_data["color_intensity"] = map_data["num_violations"] / max_val


# PyDeck Layer
layer = pdk.Layer(
    "GeoJsonLayer",
    map_data,
    get_fill_color=[
        "255 * properties.color_intensity",
        "50",
        "100",
        "180"
    ],
    pickable=True,
    stroked=True,
    filled=True,
)

view_state = pdk.ViewState(
    latitude=41.8781,
    longitude=-87.6298,
    zoom=10,
    pitch=0,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={
        "html": "<b>Violations:</b> {num_violations}",
        "style": {"backgroundColor": "steelblue", "color": "white"},
    },
)

st.pydeck_chart(deck)