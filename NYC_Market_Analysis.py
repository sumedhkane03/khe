import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Set page config before any other Streamlit commands
st.set_page_config(
    page_title="NYC Airbnb Analytics",
    page_icon="🏠",
    layout="wide"
)

@st.cache_data
def load_data():
    data = pd.read_csv("Airbnb_Open_Data.csv", low_memory=False)
    # Clean price column
    data['price'] = data['price'].str.replace('$', '').str.replace(',', '').astype(float)
    data.columns = data.columns.str.lower().str.replace(' ', '_')
    
    # Add neighborhood boundaries and coordinates
    neighborhood_coords = {
        'Manhattan': {'lat': 40.7831, 'lon': -73.9712, 'bounds': [[40.7005, -74.0196], [40.8784, -73.9070]]},
        'Brooklyn': {'lat': 40.6782, 'lon': -73.9442, 'bounds': [[40.5707, -74.0431], [40.7395, -73.8330]]},
        'Queens': {'lat': 40.7282, 'lon': -73.7949, 'bounds': [[40.5408, -73.9617], [40.8012, -73.7001]]},
        'Bronx': {'lat': 40.8448, 'lon': -73.8648, 'bounds': [[40.7855, -73.9336], [40.9156, -73.7654]]},
        'Staten Island': {'lat': 40.5795, 'lon': -74.1502, 'bounds': [[40.4969, -74.2557], [40.6517, -74.0522]]},
        'Bushwick': {'lat': 40.6950, 'lon': -73.9171, 'bounds': [[40.6789, -73.9298], [40.7031, -73.9044]]},
        'Williamsburg': {'lat': 40.7081, 'lon': -73.9570, 'bounds': [[40.6997, -73.9685], [40.7185, -73.9435]]},
        'Harlem': {'lat': 40.8116, 'lon': -73.9465, 'bounds': [[40.7998, -73.9589], [40.8234, -73.9341]]},
        'Bedford-Stuyvesant': {'lat': 40.6872, 'lon': -73.9417, 'bounds': [[40.6775, -73.9561], [40.6969, -73.9273]]},
        'Hell\'s Kitchen': {'lat': 40.7632, 'lon': -73.9919, 'bounds': [[40.7548, -74.0023], [40.7716, -73.9815]]},
        'Upper East Side': {'lat': 40.7736, 'lon': -73.9566, 'bounds': [[40.7632, -73.9685], [40.7840, -73.9447]]},
        'East Village': {'lat': 40.7265, 'lon': -73.9815, 'bounds': [[40.7205, -73.9917], [40.7325, -73.9713]]},
        'Upper West Side': {'lat': 40.7870, 'lon': -73.9754, 'bounds': [[40.7766, -73.9873], [40.7974, -73.9635]]},
        'Lower East Side': {'lat': 40.7168, 'lon': -73.9861, 'bounds': [[40.7108, -73.9963], [40.7228, -73.9759]]},
        'Chelsea': {'lat': 40.7466, 'lon': -74.0009, 'bounds': [[40.7382, -74.0113], [40.7550, -73.9905]]}
    }
    
    # Add lat/lon to the dataframe more safely
    def get_coordinate(x, coord_type):
        if pd.isna(x):  # Check for NaN values
            return None
        x = str(x)  # Convert to string to handle float values
        return (neighborhood_coords.get(x, {}).get(coord_type) or 
                neighborhood_coords.get(x.title(), {}).get(coord_type))

    data['lat'] = data['neighbourhood'].apply(lambda x: get_coordinate(x, 'lat'))
    data['lon'] = data['neighbourhood'].apply(lambda x: get_coordinate(x, 'lon'))
    
    return data, neighborhood_coords

# Load data once at startup
df, neighborhood_coords = load_data()

# Initialize neighborhoods and room types
neighborhoods = sorted([n for n in df['neighbourhood'].unique() if pd.notna(n)])
room_types = sorted([rt for rt in df['room_type'].unique() if pd.notna(rt)])

# Main page content
st.title("NYC Airbnb Market Analytics Dashboard")
st.markdown("""
    Welcome to the NYC Airbnb Analytics Dashboard! This application provides comprehensive 
    market analysis and predictive insights for Airbnb properties across New York City.
""")

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

if 'min_nights' not in st.session_state:
    st.session_state.min_nights = 7

if 'superhost_only' not in st.session_state:
    st.session_state.superhost_only = False

if 'instant_book' not in st.session_state:
    st.session_state.instant_book = False

if 'sort_by' not in st.session_state:
    st.session_state.sort_by = "Price (Low to High)"

# Create a container for quick filters
st.sidebar.header("Quick Overview Filters 🔍")

# Add neighborhood selection for overview
st.session_state.selected_neighborhoods = st.sidebar.multiselect(
    "Select Neighborhoods to View",
    options=neighborhoods,
    default=st.session_state.selected_neighborhoods
)

# Add room type selection for overview
st.session_state.selected_room_types = st.sidebar.multiselect(
    "Select Room Types to View",
    options=room_types,
    default=st.session_state.selected_room_types
)

# Add price range overview
st.session_state.price_range = st.sidebar.slider(
    "Price Range Overview ($)",
    min_value=float(df['price'].min()),
    max_value=float(df['price'].max()),
    value=st.session_state.price_range,
    step=50.0
)

# Add additional filters
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

st.session_state.min_nights = st.sidebar.slider(
    "Maximum Minimum Nights",
    min_value=1,
    max_value=int(df['minimum_nights'].max()),
    value=st.session_state.min_nights,
    step=1
)

st.session_state.superhost_only = st.sidebar.checkbox("Show Superhost Properties Only", value=st.session_state.superhost_only)
st.session_state.instant_book = st.sidebar.checkbox("Show Instant Book Properties Only", value=st.session_state.instant_book)

# Add sorting options
st.session_state.sort_by = st.sidebar.selectbox(
    "Sort by",
    ["Price (Low to High)", "Price (High to Low)", "Availability", "Most Popular"],
    index=["Price (Low to High)", "Price (High to Low)", "Availability", "Most Popular"].index(st.session_state.sort_by)
)

# Add warning if no selections made
if not st.session_state.selected_neighborhoods or not st.session_state.selected_room_types:
    st.warning("Please select at least one neighborhood and room type from the sidebar to view available properties.")
    filtered_data = pd.DataFrame()
else:
    filtered_data = df[
        (df["neighbourhood"].isin(st.session_state.selected_neighborhoods)) &
        (df["room_type"].isin(st.session_state.selected_room_types)) &
        (df["price"].between(st.session_state.price_range[0], st.session_state.price_range[1])) &
        (df["review_rate_number"] >= st.session_state.min_rating) &
        (df["number_of_reviews"] >= st.session_state.min_reviews) &
        (df["minimum_nights"] <= st.session_state.min_nights)
    ]
    
    if st.session_state.superhost_only:
        filtered_data = filtered_data[filtered_data["host_identity_verified"] == "verified"]
    
    if st.session_state.instant_book:
        filtered_data = filtered_data[filtered_data["instant_bookable"] == "TRUE"]
    
    # Sort the data based on user selection
    if st.session_state.sort_by == "Price (Low to High)":
        filtered_data = filtered_data.sort_values("price")
    elif st.session_state.sort_by == "Price (High to Low)":
        filtered_data = filtered_data.sort_values("price", ascending=False)
    elif st.session_state.sort_by == "Availability":
        filtered_data = filtered_data.sort_values("availability_365", ascending=False)
    else:  # Most Popular
        filtered_data = filtered_data.sort_values("number_of_reviews", ascending=False)
    
    # Only show visualizations if data is filtered
    if not filtered_data.empty:
        # Market Overview Section
        st.header("📊 Market Overview")
        
        # Create three columns for key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Price", f"${filtered_data['price'].mean():.2f}",
                     delta=f"${filtered_data['price'].mean() - df['price'].mean():.2f} vs NYC Avg")
        with col2:
            st.metric("Available Properties", f"{len(filtered_data):,}",
                     delta=f"{len(filtered_data)/len(df)*100:.1f}% of Total Listings")
        with col3:
            st.metric("Avg Days Available", f"{filtered_data['availability_365'].mean():.0f}",
                     delta=f"{filtered_data['availability_365'].mean() - df['availability_365'].mean():.0f} vs NYC Avg")

        # Neighborhood Map
        st.subheader("📍 Neighborhood Map")
        st.caption("Click on markers to see property details. Larger circles indicate more available properties.")
        st.caption(f"Selected Neighborhoods: {', '.join(st.session_state.selected_neighborhoods)}")
        
        avg_prices = filtered_data.groupby('neighbourhood').agg({
            'price': ['mean', 'count'],
            'availability_365': 'mean',
            'lat': 'first',
            'lon': 'first'
        }).reset_index()
        
        avg_prices.columns = ['neighbourhood', 'avg_price', 'listing_count', 'avg_availability', 'lat', 'lon']
        
        fig_map = px.scatter_mapbox(
            avg_prices,
            lat='lat',
            lon='lon',
            size='listing_count',
            color='avg_price',
            hover_name='neighbourhood',
            hover_data={
                'avg_price': ':$.2f',
                'listing_count': ':,',
                'avg_availability': ':.0f',
                'lat': False,
                'lon': False
            },
            color_continuous_scale='Viridis',
            labels={
                'avg_price': 'Average Price',
                'listing_count': 'Number of Listings',
                'avg_availability': 'Average Availability (days)'
            },
            zoom=10,
            center={"lat": 40.7128, "lon": -74.0060}
        )

        for neighborhood in st.session_state.selected_neighborhoods:
            possible_names = [neighborhood, neighborhood.title(), neighborhood.lower(), neighborhood.upper()]
            for name in possible_names:
                if name in neighborhood_coords:
                    bounds = neighborhood_coords[name]['bounds']
                    fig_map.add_shape(
                        type="rect",
                        x0=bounds[0][1], y0=bounds[0][0],
                        x1=bounds[1][1], y1=bounds[1][0],
                        line=dict(color="rgba(50, 171, 96, 0.7)", width=2),
                        fillcolor="rgba(50, 171, 96, 0.2)",
                        layer='below'
                    )

        fig_map.update_layout(
            mapbox=dict(
                style="open-street-map",
                zoom=10,
                center={"lat": 40.7128, "lon": -74.0060}
            ),
            margin={"r":0,"t":0,"l":0,"b":0},
            height=500,
            showlegend=True
        )
        
        st.plotly_chart(fig_map, use_container_width=True)

        # Predictive Analytics Section
        st.header("📈 Predictive Analytics")
        
        # Market Trend Analysis
        st.subheader("Market Trend Analysis")
        trend_col1, trend_col2 = st.columns(2)
        
        with trend_col1:
            avg_price_trend = filtered_data['price'].mean()
            price_momentum = ((filtered_data['price'].mean() - df['price'].mean()) / df['price'].mean()) * 100
            
            st.metric(
                "Price Trend",
                f"${avg_price_trend:.2f}",
                delta=f"{price_momentum:.1f}% vs Market Avg"
            )
        
        with trend_col2:
            avg_demand = filtered_data['number_of_reviews'].mean()
            demand_change = ((filtered_data['number_of_reviews'].mean() - df['number_of_reviews'].mean()) / 
                           df['number_of_reviews'].mean()) * 100
            
            st.metric(
                "Demand Index",
                f"{avg_demand:.1f}",
                delta=f"{demand_change:.1f}% vs Market Avg"
            )
        
        # Seasonal Patterns
        st.subheader("🌊 Seasonal Patterns")
        seasonal_col1, seasonal_col2, seasonal_col3 = st.columns(3)
        
        with seasonal_col1:
            peak_season_premium = ((filtered_data['price'].quantile(0.75) / filtered_data['price'].quantile(0.25)) - 1) * 100
            st.metric(
                "Peak Season Premium",
                f"{peak_season_premium:.1f}%",
                help="Price premium during high-demand seasons"
            )
        
        with seasonal_col2:
            occupancy_variation = filtered_data['availability_365'].std() / filtered_data['availability_365'].mean() * 100
            st.metric(
                "Seasonal Volatility",
                f"{occupancy_variation:.1f}%",
                help="Variation in occupancy rates across seasons"
            )
        
        with seasonal_col3:
            price_elasticity = 1 - (filtered_data['price'].std() / filtered_data['price'].mean())
            st.metric(
                "Price Elasticity",
                f"{price_elasticity:.2f}",
                help="Market's sensitivity to price changes"
            )
        
        # Market Recommendations
        st.subheader("📋 Market Recommendations")
        
        recommendations = [
            f"The selected area shows a {price_momentum:.1f}% price difference from the market average, suggesting a {'premium' if price_momentum > 0 else 'value'} market.",
            f"Demand is {'higher' if demand_change > 0 else 'lower'} than the market average by {abs(demand_change):.1f}%.",
            f"Seasonal premium of {peak_season_premium:.1f}% indicates {'significant' if peak_season_premium > 20 else 'moderate'} seasonal opportunities.",
            f"Price elasticity of {price_elasticity:.2f} suggests {'flexible' if price_elasticity < 0.5 else 'rigid'} pricing strategies are optimal."
        ]
        
        for rec in recommendations:
            st.info(rec)

        # Property Listings Section
        st.header("🏠 Available Properties")
        st.caption(f"Showing {len(filtered_data)} properties sorted by {st.session_state.sort_by}")

        # Initialize session state for property display count if not exists
        if 'property_display_count' not in st.session_state:
            st.session_state.property_display_count = 5

        # Display properties in an expandable list with pagination
        for idx, (_, property) in enumerate(filtered_data.iterrows()):
            if idx < st.session_state.property_display_count:
                with st.expander(f"${property['price']:.0f} - {property['room_type']} in {property['neighbourhood']}"):
                    # Create two columns for property details
                    detail_col1, detail_col2 = st.columns(2)
                    
                    with detail_col1:
                        st.markdown("**Property Details**")
                        st.write(f"🏠 Room Type: {property['room_type']}")
                        st.write(f"📍 Neighborhood: {property['neighbourhood']}")
                        st.write(f"💰 Price: ${property['price']:.2f}/night")
                        st.write(f"📅 Availability: {property['availability_365']} days/year")
                    
                    with detail_col2:
                        st.markdown("**Host Information**")
                        st.write(f"👤 Host: {property['host_name']}")
                        st.write(f"⭐ Reviews: {property['number_of_reviews']}")
                        if 'host_identity_verified' in property:
                            st.write(f"✓ Identity Verified: {property['host_identity_verified']}")
                        if 'instant_bookable' in property:
                            st.write(f"⚡ Instant Booking: {property['instant_bookable']}")
                    
                    # Additional property information
                    if 'service_fee' in property:
                        try:
                            service_fee = float(str(property['service_fee']).replace('$', '').replace(',', ''))
                            st.write(f"🔧 Service Fee: ${service_fee:.2f}")
                        except (ValueError, TypeError):
                            st.write(f"🔧 Service Fee: {property['service_fee']}")
                    if 'minimum_nights' in property:
                        st.write(f"🌙 Minimum Stay: {property['minimum_nights']} nights")
                    if 'review_rate_number' in property:
                        st.write(f"⭐ Rating: {property['review_rate_number']}/5")
                    if 'cancellation_policy' in property:
                        st.write(f"📋 Cancellation Policy: {property['cancellation_policy']}")

        # Show 'See More' button if there are more properties to display
        remaining_properties = len(filtered_data) - st.session_state.property_display_count
        if remaining_properties > 0:
            if st.button(f"See More ({remaining_properties} more properties)"):
                st.session_state.property_display_count += 5
                st.rerun()


