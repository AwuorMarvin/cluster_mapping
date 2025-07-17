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
    /* Style for hierarchical checkboxes */
    .territory-checkbox {
        font-weight: bold;
        margin-bottom: 5px;
        background-color: #f0f2f6;
        padding: 8px;
        border-radius: 4px;
        border-left: 4px solid #1f77b4;
    }
    .cluster-checkbox {
        margin-left: 20px;
        margin-bottom: 3px;
        font-size: 0.9em;
        padding: 4px 8px;
        background-color: #ffffff;
        border-radius: 3px;
        border-left: 2px solid #cccccc;
    }
    .checkbox-container {
        margin-bottom: 15px;
    }
    /* Custom styling for form checkboxes */
    .stForm .stCheckbox {
        margin-bottom: 8px;
    }
    .stForm .stCheckbox > label {
        font-size: 0.9em;
    }
    /* Territory checkbox styling */
    .territory-cb {
        font-weight: bold;
        background-color: #f0f2f6;
        padding: 8px;
        border-radius: 4px;
        margin-bottom: 5px;
        border-left: 4px solid #1f77b4;
    }
    /* Cluster checkbox styling */
    .cluster-cb {
        margin-left: 30px;
        padding: 4px 8px;
        background-color: #fafafa;
        border-radius: 3px;
        margin-bottom: 3px;
        border-left: 2px solid #cccccc;
        font-size: 0.85em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

df = pd.read_csv("cluster_data.csv")  

# Initialize session state for applied selections only
if "applied_territories" not in st.session_state:
    st.session_state.applied_territories = set()
if "applied_clusters" not in st.session_state:
    st.session_state.applied_clusters = set()
if "map_data" not in st.session_state:
    st.session_state.map_data = df  # Start with all data

st.sidebar.markdown(
    """
    <div class="legend-container">
        <div class="legend-dot"></div>
        <span>Syokimau DC</span>
    </div>
    """,
    unsafe_allow_html=True
)

# Create hierarchical selection interface using form
st.sidebar.subheader("Select Territories and Clusters")

with st.sidebar.form("territory_cluster_form"):
    territories = df["territory name"].dropna().unique().tolist()
    territory_clusters = {}

    # Group clusters by territory
    for territory in territories:
        territory_clusters[territory] = df[df["territory name"] == territory]["cluster name"].dropna().unique().tolist()

    # Store current selections
    selected_territories = set()
    selected_clusters = set()
    
    # Create hierarchical checkboxes
    for territory in territories:
        # Skip if territory is None or empty
        if not territory or pd.isna(territory):
            continue
            
        clusters_in_territory = territory_clusters[territory]
        
        # Territory checkbox with bold styling
        st.markdown(f"**🏘️ {str(territory)}**")
        territory_selected = st.checkbox(
            f"Select all in {str(territory)}",
            key=f"territory_{territory}",
            value=territory in st.session_state.applied_territories
        )
        
        if territory_selected:
            selected_territories.add(territory)
            # Auto-select all clusters in this territory
            for cluster in clusters_in_territory:
                if cluster and not pd.isna(cluster):
                    selected_clusters.add(cluster)
        
        # Add some spacing and indentation for clusters
        st.markdown("---")  # Separator line
        
        # Cluster checkboxes (indented)
        for cluster in clusters_in_territory:
            # Skip if cluster is None or empty
            if not cluster or pd.isna(cluster):
                continue
                
            # Auto-check cluster if territory is selected, otherwise use current applied state
            cluster_default = (territory_selected or cluster in st.session_state.applied_clusters)
            
            # Add indentation using columns
            col1, col2 = st.columns([1, 10])
            with col1:
                st.write("")  # Empty space for indentation
            with col2:
                cluster_selected = st.checkbox(
                    f"📍 {str(cluster)}",
                    key=f"cluster_{cluster}",
                    value=cluster_default
                )
            
            # Only add to selected if explicitly checked or territory is selected
            if cluster_selected or territory_selected:
                selected_clusters.add(cluster)
        
        # Add spacing between territories
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Submit button
    submitted = st.form_submit_button("Update Map", type="primary")
    
    if submitted:
        # Apply selections to map data
        st.session_state.applied_territories = selected_territories.copy()
        st.session_state.applied_clusters = selected_clusters.copy()
        
        # Filter data based on applied selections
        if st.session_state.applied_clusters:
            filtered_df = df[df["cluster name"].isin(st.session_state.applied_clusters)]
        else:
            filtered_df = pd.DataFrame()  # Empty dataframe if nothing selected
        
        st.session_state.map_data = filtered_df
        st.rerun()  # Force a rerun to update the map

# Use the data from session state
filtered_df = st.session_state.map_data

# Determine coloring logic based on applied selections
if len(st.session_state.applied_territories) == 1:
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

if not filtered_df.empty:
    unique_values = filtered_df[color_column].unique()
    color_palette = {
        name: preset_colors[i % len(preset_colors)]
        for i, name in enumerate(unique_values)
    }
    filtered_df["color"] = filtered_df[color_column].map(color_palette)

# Syokimau DC data (always shown)
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

# Set Mapbox token via environment variable (most reliable method)
import os
os.environ['MAPBOX_API_KEY'] = st.secrets["mapbox"]["token"]

deck = pdk.Deck(
    map_style='mapbox://styles/mapbox/streets-v11',  # Google Maps-like style
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