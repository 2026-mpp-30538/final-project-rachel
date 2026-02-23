# Dashboard code will go here. 

# ideas:
# some sort of plot of income and number of violations or seasonal number of violations but you can toggle it by type of violation
# seasonal trends map where you toggle the months to see which violation types are the most common
# or select a violation type and then toggle for seasonal trends, or select month and it shows most common type
# could add toggle to map as well for month --> scatterplot for income on each page

# to tooltip add address, and fine if it can be merged in

# scatterplot: block out the income to 20k then do average number of violations on y axis
# maybe panel next to scatterplot
# incorporate reason for violation

import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
from pathlib import Path
import os
import altair as alt

st.set_page_config(layout="wide")

st.title("Chicago Building Violations from 2024-2026 by Category")

# Load Data
@st.cache_data
def load_data():
    BASE_DIR = Path(__file__).resolve().parents[1]
    data_path = BASE_DIR / "data" / "derived-data" / "Building_Violations_w_ACS.gpkg"
    gdf = gpd.read_file(data_path)
    gdf = gdf.rename(columns={
    "VIOLATION DATE": "violation_date",
    "VIOLATION DESCRIPTION": "violation_description"
    })
    gdf["violation_date"] = pd.to_datetime(gdf["violation_date"])
    gdf["violation_date"] = gdf["violation_date"].dt.strftime("%Y-%m-%d")

    return gdf

gdf = load_data()

# Sidebar Category Toggle
categories = sorted(gdf["violation_category"].dropna().unique())

selected_category = st.sidebar.selectbox(
    "Select Violation Category",
    categories
)

filtered = gdf[gdf["violation_category"] == selected_category].copy()

# Aggregate to tract level
tract_level = (
    filtered
    .groupby("GEOID")
    .agg(
        per_cap_inc=("per_cap_inc", "first"),
        population=("population", "first"),
        violations=("GEOID", "size")  
    )
    .reset_index()
)

# Calculate violations per 1,000 residents
tract_level["violations_per_1000"] = (
    tract_level["violations"] /
    tract_level["population"]
) * 1000

st.write("Number of violations shown:", len(filtered))

st.subheader("Violations per 1,000 vs Per Capita Income (Tract Level)")

scatter = alt.Chart(tract_level).mark_circle(size=60, opacity=0.6).encode(
    x=alt.X("per_cap_inc:Q", title="Per Capita Income"),
    y=alt.Y("violations_per_1000:Q", title="Violations per 1,000 Residents"),
    tooltip=[
        "GEOID",
        "per_cap_inc",
        "violations_per_1000",
        "violations"
    ]
)

trendline = alt.Chart(tract_level).transform_regression(
    "per_cap_inc",
    "violations_per_1000"
).mark_line(size=3, color="black").encode(
    x="per_cap_inc:Q",
    y="violations_per_1000:Q"
)

chart = (scatter + trendline).properties(
    width=700,
    height=500
).interactive()

st.altair_chart(chart)


# PyDeck Layer
st.subheader("Interactive Map")

layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered,
    get_position='[LONGITUDE, LATITUDE]',
    get_radius=50,   
    get_fill_color=[200, 30, 0, 140],
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=41.8781,
    longitude=-87.6298,
      zoom=10,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={
    "html": "<b>Category:</b> {violation_category}<br/><b>Date:</b> {violation_date}<br/><b>Description:</b> {violation_description}",
    "style": {"backgroundColor": "steelblue", "color": "white"},
    },   
)

st.pydeck_chart(deck)
