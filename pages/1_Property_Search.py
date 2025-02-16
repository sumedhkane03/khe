import streamlit as st
import pandas as pd
import plotly.express as px

# Set page config
st.set_page_config(
    page_title="Property Search - NYC Airbnb",
    page_icon="🏠",
    layout="wide"
)

# Load data
@st.cache_data
def load_data():
    data = pd.read_csv("Airbnb_Open_Data.csv", low_memory=False)
    data['price'] = data['price'].str.replace('$', '').str.replace(',', '').astype(float)
    data.columns = data.columns.str.lower().str.replace(' ', '_')
    return data

df = load_data()

st.title("🏠 NYC Airbnb Property Search")
st.markdown("""
    Find your perfect Airbnb stay in New York City. Use the filters to narrow down properties 
    based on your preferences.
""")

# Initialize neighborhoods and room types
neighborhoods = sorted([n for n in df['neighbourhood'].unique() if pd.notna(n)])
room_types = sorted([rt for rt in df['room_type'].unique() if pd.notna(rt)])

# Initialize global state variables if not exists
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

if 'superhost_only' not in st.session_state:
    st.session_state.superhost_only = False

if 'instant_book' not in st.session_state:
    st.session_state.instant_book = False

if 'property_display_count' not in st.session_state:
    st.session_state.property_display_count = 5

# Sidebar filters
st.sidebar.header("Search Filters 🔍")

# Neighborhood selection
neighborhoods = sorted([n for n in df['neighbourhood'].unique() if pd.notna(n)])
st.session_state.selected_neighborhoods = st.sidebar.multiselect(
    "Select Neighborhoods",
    options=neighborhoods,
    default=st.session_state.selected_neighborhoods
)

# Room type selection
room_types = sorted([rt for rt in df['room_type'].unique() if pd.notna(rt)])
st.session_state.selected_room_types = st.sidebar.multiselect(
    "Select Room Types",
    options=room_types,
    default=st.session_state.selected_room_types
)

# Price range filter
st.session_state.price_range = st.sidebar.slider(
    "Price Range ($)",
    min_value=float(df['price'].min()),
    max_value=float(df['price'].max()),
    value=st.session_state.price_range,
    step=50.0
)

# Additional filters
st.session_state.min_rating = st.sidebar.slider(
    "Minimum Rating",
    min_value=0.0,
    max_value=5.0,
    value=st.session_state.min_rating,
    step=0.5
)

st.session_state.min_reviews = st.sidebar.slider(
    "Minimum Number of Reviews",
    min_value=0,
    max_value=int(df['number_of_reviews'].max()),
    value=st.session_state.min_reviews,
    step=5
)

st.session_state.superhost_only = st.sidebar.checkbox("Show Superhost Properties Only", value=st.session_state.superhost_only)
st.session_state.instant_book = st.sidebar.checkbox("Show Instant Book Properties Only", value=st.session_state.instant_book)

# Apply filters
if not st.session_state.selected_neighborhoods or not st.session_state.selected_room_types:
    st.warning("Please select at least one neighborhood and room type from the sidebar.")
    filtered_data = pd.DataFrame()
else:
    filtered_data = df[
        (df["neighbourhood"].isin(st.session_state.selected_neighborhoods)) &
        (df["room_type"].isin(st.session_state.selected_room_types)) &
        (df["price"].between(st.session_state.price_range[0], st.session_state.price_range[1])) &
        (df["review_rate_number"] >= st.session_state.min_rating) &
        (df["number_of_reviews"] >= st.session_state.min_reviews)
    ]
    
    if st.session_state.superhost_only:
        filtered_data = filtered_data[filtered_data["host_identity_verified"] == "verified"]
    
    if st.session_state.instant_book:
        filtered_data = filtered_data[filtered_data["instant_bookable"] == "TRUE"]

# Display results
if not filtered_data.empty:
    st.header(f"Found {len(filtered_data)} Properties")
    
    # Sort options
    sort_by = st.selectbox(
        "Sort by",
        ["Price (Low to High)", "Price (High to Low)", "Most Popular", "Best Rated"]
    )
    
    if sort_by == "Price (Low to High)":
        filtered_data = filtered_data.sort_values("price")
    elif sort_by == "Price (High to Low)":
        filtered_data = filtered_data.sort_values("price", ascending=False)
    elif sort_by == "Most Popular":
        filtered_data = filtered_data.sort_values("number_of_reviews", ascending=False)
    else:  # Best Rated
        filtered_data = filtered_data.sort_values("review_rate_number", ascending=False)
    
    # Display properties
    for idx, (_, property) in enumerate(filtered_data.iterrows()):
        if idx < st.session_state.property_display_count:
            with st.expander(f"${property['price']:.0f} - {property['room_type']} in {property['neighbourhood']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Property Details**")
                    st.write(f"🏠 Room Type: {property['room_type']}")
                    st.write(f"📍 Neighborhood: {property['neighbourhood']}")
                    st.write(f"💰 Price: ${property['price']:.2f}/night")
                    st.write(f"📅 Availability: {property['availability_365']} days/year")
                
                with col2:
                    st.markdown("**Host Information**")
                    st.write(f"👤 Host: {property['host_name']}")
                    st.write(f"⭐ Rating: {property['review_rate_number']}/5")
                    st.write(f"📝 Reviews: {property['number_of_reviews']}")
                    if property['host_identity_verified'] == 'verified':
                        st.write("✅ Verified Host")
                    if property['instant_bookable'] == 'TRUE':
                        st.write("⚡ Instant Booking Available")
    
    # Show 'See More' button if there are more properties to display
    remaining_properties = len(filtered_data) - st.session_state.property_display_count
    if remaining_properties > 0:
        if st.button(f"See More ({remaining_properties} more properties)"):
            st.session_state.property_display_count += 5
            st.rerun()