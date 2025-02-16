import streamlit as st
import pandas as pd
import plotly.express as px

# Set page config
st.set_page_config(
    page_title="Market Analytics - NYC Airbnb",
    page_icon="📊",
    layout="wide"
)

# Load data from main app
@st.cache_data
def load_data():
    data = pd.read_csv("Airbnb_Open_Data.csv", low_memory=False)
    data['price'] = data['price'].str.replace('$', '').str.replace(',', '').astype(float)
    data.columns = data.columns.str.lower().str.replace(' ', '_')
    return data

df = load_data()

st.title("📊 NYC Airbnb Market Analytics")
st.markdown("""
    Dive deep into the NYC Airbnb market trends and patterns. This page provides comprehensive 
    analytics about pricing, demand, and seasonal variations across different neighborhoods.
""")

# Market Overview Section
st.header("Market Overview")

# Initialize neighborhoods and room types
neighborhoods = sorted([n for n in df['neighbourhood'].unique() if pd.notna(n)])
room_types = sorted([rt for rt in df['room_type'].unique() if pd.notna(rt)])

# Initialize session state if not exists
if 'selected_neighborhoods' not in st.session_state:
    st.session_state.selected_neighborhoods = neighborhoods[:3] if len(neighborhoods) >= 3 else neighborhoods

if 'selected_room_types' not in st.session_state:
    st.session_state.selected_room_types = room_types[:3] if len(room_types) >= 3 else room_types

if 'price_range' not in st.session_state:
    st.session_state.price_range = (float(df['price'].min()), float(df['price'].quantile(0.75)))

if 'min_rating' not in st.session_state:
    st.session_state.min_rating = 4.0

if 'min_reviews' not in st.session_state:
    st.session_state.min_reviews = 5

# Sidebar filters
st.sidebar.header("Market Analytics Filters 🔍")

# Add neighborhood selection
st.session_state.selected_neighborhoods = st.sidebar.multiselect(
    "Select Neighborhoods",
    options=neighborhoods,
    default=st.session_state.selected_neighborhoods
)

# Add room type selection
st.session_state.selected_room_types = st.sidebar.multiselect(
    "Select Room Types",
    options=room_types,
    default=st.session_state.selected_room_types
)

# Add price range filter
st.session_state.price_range = st.sidebar.slider(
    "Price Range ($)",
    min_value=float(df['price'].min()),
    max_value=float(df['price'].max()),
    value=st.session_state.price_range,
    step=50.0
)

# Filter data based on selections
filtered_df = df[
    (df['neighbourhood'].isin(st.session_state.selected_neighborhoods)) &
    (df['room_type'].isin(st.session_state.selected_room_types)) &
    (df['price'].between(st.session_state.price_range[0], st.session_state.price_range[1]))
]

# Create three columns for key metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Average Price", f"${filtered_df['price'].mean():.2f}", 
              delta=f"${filtered_df['price'].mean() - df['price'].mean():.2f} vs Overall")
with col2:
    st.metric("Total Properties", f"{len(filtered_df):,}",
              delta=f"{len(filtered_df)/len(df)*100:.1f}% of Total")
with col3:
    st.metric("Avg Days Available", f"{filtered_df['availability_365'].mean():.0f}",
              delta=f"{filtered_df['availability_365'].mean() - df['availability_365'].mean():.0f} days")

# Price Distribution
st.subheader("Price Distribution by Neighborhood")
fig_price = px.box(filtered_df, 
                   x='neighbourhood', 
                   y='price',
                   title='Price Distribution Across Selected Neighborhoods',
                   labels={'neighbourhood': 'Neighborhood', 'price': 'Price ($)'})
fig_price.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_price, use_container_width=True)

# Seasonal Analysis
st.header("Seasonal Analysis")

# Calculate seasonal metrics
seasonal_col1, seasonal_col2 = st.columns(2)

with seasonal_col1:
    peak_season_premium = ((df['price'].quantile(0.75) / df['price'].quantile(0.25)) - 1) * 100
    st.metric(
        "Peak Season Premium",
        f"{peak_season_premium:.1f}%",
        help="Price premium during high-demand seasons"
    )

with seasonal_col2:
    occupancy_variation = df['availability_365'].std() / df['availability_365'].mean() * 100
    st.metric(
        "Seasonal Volatility",
        f"{occupancy_variation:.1f}%",
        help="Variation in occupancy rates across seasons"
    )

# Room Type Analysis
st.header("Room Type Analysis")

# Calculate average price by room type
room_type_stats = df.groupby('room_type').agg({
    'price': ['mean', 'count'],
    'review_rate_number': 'mean'
}).reset_index()

room_type_stats.columns = ['room_type', 'avg_price', 'count', 'avg_rating']

fig_room = px.bar(room_type_stats,
                  x='room_type',
                  y='avg_price',
                  color='avg_rating',
                  text='count',
                  title='Average Price and Rating by Room Type',
                  labels={
                      'room_type': 'Room Type',
                      'avg_price': 'Average Price ($)',
                      'avg_rating': 'Average Rating',
                      'count': 'Number of Properties'
                  })

st.plotly_chart(fig_room, use_container_width=True)