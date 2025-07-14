import streamlit as st
import pandas as pd
import pydeck as pdk

def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["passwords"]["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    html, body, .stApp {
        height: 100vh !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .main .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: calc(100vw - 300px) !important; /* Adjust for sidebar width */
        height: calc(100vh - 2px) !important; /* Account for minimal footer gap */
    }
    .stDeckGlJsonChart, .stDeckGlJsonChart iframe {
        height: 100% !important;
        width: 100% !important;
        min-height: 100% !important;
        min-width: 100% !important;
    }
    /* Style for the map container */
    div[data-testid="stVerticalBlock"] > div {
        height: 100% !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Minimize gap between map and footer */
    [data-testid="stFooter"] {
        margin-top: 2px !important;
        padding: 0 !important;
        height: auto !important;
    }
    /* Style for the legend */
    .legend-container {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    .legend-dot {
        width: 16px;
        height: 16px;
        background-color: rgb(255, 0, 0);
        border-radius: 50%;
        margin-right: 8px;
    }
    /* Style for individual options in multiselect dropdowns */
    div[data-testid="stMultiSelect"] div[role="option"] {
        background-color: #002060 !important;
        color: #FFFFFF !important; /* White text for options */
    }
    /* Ensure selected options also have the same background */
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background-color: #002060 !important;
        color: #FFFFFF !important; /* White text for selected tags */
    }
    </style>
    """,
    unsafe_allow_html=True
)

df = pd.read_csv("cluster_data.csv")  

st.sidebar.markdown(
    """
    <div class="legend-container">
        <div class="legend-dot"></div>
        <span>Syokimau DC</span>
    </div>
    """,
    unsafe_allow_html=True
)

territories = df["territory name"].unique().tolist()
selected_territories = st.sidebar.multiselect("Select Territory", territories, default=territories)

filtered_df = df[df["territory name"].isin(selected_territories)]

clusters = filtered_df["cluster name"].unique().tolist()
selected_clusters = st.sidebar.multiselect("Select Cluster", clusters, default=clusters)

filtered_df = filtered_df[filtered_df["cluster name"].isin(selected_clusters)]

if len(selected_territories) == 1:
    color_column = "cluster name"
else:
    color_column = "territory name"

preset_colors = [
    [255, 99, 132],   
    [54, 162, 235],   
    [255, 206, 86],   
    [75, 192, 192],   
    [153, 102, 255],  
    [255, 159, 64],   
    [199, 199, 199],  
    [83, 102, 255],   
    [0, 204, 102],    
    [255, 51, 153],   
    [102, 255, 255],  
    [153, 255, 51],   
]

unique_values = filtered_df[color_column].unique()
color_palette = {
    name: preset_colors[i % len(preset_colors)]
    for i, name in enumerate(unique_values)
}

filtered_df["color"] = filtered_df[color_column].map(color_palette)

syokimau_data = pd.DataFrame({
    "name": ["Syokimau DC"],
    "longitude": [36.91971405524983],
    "latitude": [1.362519418250539],
    "color": [[255, 0, 0]],  # Red dot
    "shop_name": ["Syokimau DC"],
    "phone number": ["N/A"],
    "cluster name": ["Distribution Center"],
    "territory name": ["Syokimau"]
})

syokimau_scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=syokimau_data,
    get_position='[longitude, latitude]',
    get_fill_color="color",
    get_radius=300, 
    pickable=True,
    stroked=True,
    filled=True,
    get_line_color=[255, 255, 255], 
    get_line_width=3,
)

deck_layers = []

if not filtered_df.empty:
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtered_df,
        get_position='[longitude, latitude]',
        get_fill_color="color",
        get_radius=100,
        pickable=True,
        auto_highlight=True,
    )
    deck_layers.append(scatter_layer)

deck_layers.append(syokimau_scatter_layer)

view_state = pdk.ViewState(
    latitude=filtered_df["latitude"].mean() if not filtered_df.empty else 1.362519418250539,
    longitude=filtered_df["longitude"].mean() if not filtered_df.empty else 36.91971405524983,
    zoom=10,
    pitch=0,
)

# Set Mapbox token using pydeck's built-in function
pdk.settings.set_mapbox_access_token(st.secrets["mapbox"]["token"])

deck = pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    layers=deck_layers,
    initial_view_state=view_state,
    tooltip={
        "html": """
        <b>Shop:</b> {shop_name}<br/>
        <b>Phone:</b> {phone number}<br/>
        <b>Cluster:</b> {cluster name}<br/>
        <b>Territory:</b> {territory name}
        """,
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
    }
)

with st.container():
    if filtered_df.empty:
        st.info("No shop data matches your current selection. Displaying Syokimau DC for reference.")
    st.pydeck_chart(deck, use_container_width=True)