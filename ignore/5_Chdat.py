import streamlit as st
import pandas as pd
import requests
import json

# Set page config
st.set_page_config(
    page_title="Property Recommendation Chatbot",
    page_icon="💬",
    layout="wide"
)

# Load the data
@st.cache_data
def load_data():
    data = pd.read_csv("Airbnb_Open_Data.csv", low_memory=False)
    data['price'] = data['price'].str.replace('$', '').str.replace(',', '').astype(float)
    data.columns = data.columns.str.lower().str.replace(' ', '_')
    return data

df = load_data()

# Initialize chat history in session state if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Initialize property preferences in session state
if 'preferences' not in st.session_state:
    st.session_state.preferences = {
        'budget': None,
        'neighborhood': None,
        'room_type': None,
        'min_rating': None,
        'instant_book': None
    }

# Function to process user input and generate response
def process_user_input(user_input):
    # Extract preferences from user input
    input_lower = user_input.lower()
    
    # Reset preferences for new query to avoid stale values
    st.session_state.preferences = {
        'budget': None,
        'neighborhood': None,
        'room_type': None,
        'min_rating': None,
        'instant_book': None
    }
    
    # Extract preferences from user input with improved pattern matching
    if 'budget' in input_lower or '$' in input_lower or 'price' in input_lower:
        try:
            # Extract number after $ or before 'dollars' or 'per night'
            import re
            numbers = re.findall(r'\$?(\d+(?:\.\d+)?)', input_lower)
            if numbers:
                st.session_state.preferences['budget'] = float(numbers[0])
        except:
            pass
    
    if 'neighborhood' in input_lower or 'area' in input_lower or 'location' in input_lower:
        for neighborhood in df['neighbourhood'].unique():
            if str(neighborhood).lower() in input_lower:
                st.session_state.preferences['neighborhood'] = neighborhood
                break
    
    if 'room' in input_lower or 'property' in input_lower or 'place' in input_lower:
        for room_type in df['room_type'].unique():
            if str(room_type).lower() in input_lower:
                st.session_state.preferences['room_type'] = room_type
                break
    
    if 'rating' in input_lower or 'star' in input_lower or 'review' in input_lower:
        try:
            numbers = re.findall(r'(\d+(?:\.\d+)?)', input_lower)
            if numbers:
                st.session_state.preferences['min_rating'] = float(numbers[0])
        except:
            pass
    
    if ('instant' in input_lower and 'book' in input_lower) or 'quick' in input_lower:
        st.session_state.preferences['instant_book'] = True
    
    # Generate response based on current preferences
    response = generate_recommendation()
    return response

# Function to generate property recommendations based on preferences
def generate_recommendation():
    filtered_df = df.copy()
    preferences = st.session_state.preferences
    
    # Apply base filters
    if preferences['budget']:
        filtered_df = filtered_df[filtered_df['price'] <= preferences['budget']]
    
    if preferences['neighborhood']:
        filtered_df = filtered_df[filtered_df['neighbourhood'] == preferences['neighborhood']]
    
    if preferences['room_type']:
        filtered_df = filtered_df[filtered_df['room_type'] == preferences['room_type']]
    
    if preferences['min_rating']:
        filtered_df = filtered_df[filtered_df['review_rate_number'] >= preferences['min_rating']]
    
    if preferences['instant_book']:
        filtered_df = filtered_df[filtered_df['instant_bookable'] == 'TRUE']
    
    if filtered_df.empty:
        return "I couldn't find any properties matching your exact preferences. Try adjusting your criteria - perhaps consider a different neighborhood or increasing your budget slightly."
    
    # Calculate weighted scores for ranking
    filtered_df['review_score'] = filtered_df['review_rate_number'] * filtered_df['number_of_reviews'].clip(upper=100) / 100
    filtered_df['price_score'] = 1 - (filtered_df['price'] - filtered_df['price'].min()) / (filtered_df['price'].max() - filtered_df['price'].min())
    filtered_df['availability_score'] = filtered_df['availability_365'] / 365
    
    # Combined weighted score
    filtered_df['total_score'] = (
        filtered_df['review_score'] * 0.4 +
        filtered_df['price_score'] * 0.4 +
        filtered_df['availability_score'] * 0.2
    )
    
    # Sort by total score
    filtered_df = filtered_df.sort_values('total_score', ascending=False)
    
    # Get top 3 properties
    top_properties = filtered_df.head(3)
    
    # Calculate market insights
    avg_price = filtered_df['price'].mean()
    neighborhood_avg = df[df['neighbourhood'] == preferences['neighborhood']]['price'].mean() if preferences['neighborhood'] else None
    
    response = "Based on your preferences, here are the best matches:\n\n"
    
    for idx, property in top_properties.iterrows():
        response += f"Option {top_properties.index.get_loc(idx) + 1}:\n"
        response += f"🏠 {property['room_type']} in {property['neighbourhood']}\n"
        response += f"💰 ${property['price']:.2f} per night"
        
        # Price comparison
        if neighborhood_avg:
            price_diff = ((property['price'] - neighborhood_avg) / neighborhood_avg) * 100
            if price_diff < 0:
                response += f" ({abs(price_diff):.1f}% below {property['neighbourhood']} average)\n"
            else:
                response += f" ({price_diff:.1f}% above {property['neighbourhood']} average)\n"
        else:
            if property['price'] < avg_price:
                response += f" (${(avg_price - property['price']):.2f} below market average)\n"
            else:
                response += "\n"
        
        # Enhanced property details
        response += f"⭐ {property['review_rate_number']}/5 ({property['number_of_reviews']} reviews)"
        if property['number_of_reviews'] > df['number_of_reviews'].median():
            response += " - Highly Reviewed!\n"
        else:
            response += "\n"
            
        response += f"📅 Available for {property['availability_365']} days/year"
        if property['availability_365'] > 300:
            response += " - High Availability!\n"
        else:
            response += "\n"
            
        if property['instant_bookable'] == 'TRUE':
            response += "⚡ Instant Booking Available\n"
            
        if 'host_identity_verified' in property and property['host_identity_verified'] == 'verified':
            response += "✅ Verified Host\n"
            
        response += "\n"
    
    # Market insights
    total_matches = len(filtered_df)
    if total_matches > 3:
        response += f"\nI found {total_matches - 3} more properties matching your criteria. "
        response += "Would you like to see more options or refine your search?\n\n"
    
    # Add market context
    if preferences['neighborhood']:
        avg_rating = df[df['neighbourhood'] == preferences['neighborhood']]['review_rate_number'].mean()
        response += f"📊 Market Insight: {preferences['neighborhood']} has an average rating of {avg_rating:.1f}/5"
    
    return response

# Main chat interface
st.title("🤖 Property Recommendation Chatbot")
st.markdown("""
    Welcome! I'm your personal property finder. Tell me about your preferences, and I'll help you find the perfect Airbnb property in NYC.
    You can tell me about:
    - Your budget
    - Preferred neighborhood
    - Type of room you're looking for
    - Minimum rating
    - If you need instant booking
""")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("What kind of property are you looking for?"):
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        response = process_user_input(prompt)
        st.write(response)
    st.session_state.chat_history.append({"role": "assistant", "content": response})

# Sidebar with current preferences
st.sidebar.title("Current Preferences 📋")
preferences = st.session_state.preferences

st.sidebar.markdown("### Your Requirements")
if preferences['budget']:
    st.sidebar.write(f"💰 Budget: ${preferences['budget']:.2f}")
if preferences['neighborhood']:
    st.sidebar.write(f"📍 Neighborhood: {preferences['neighborhood']}")
if preferences['room_type']:
    st.sidebar.write(f"🏠 Room Type: {preferences['room_type']}")
if preferences['min_rating']:
    st.sidebar.write(f"⭐ Minimum Rating: {preferences['min_rating']}/5")
if preferences['instant_book']:
    st.sidebar.write("⚡ Instant Booking: Yes")

# Reset preferences button
if st.sidebar.button("Reset Preferences"):
    st.session_state.preferences = {
        'budget': None,
        'neighborhood': None,
        'room_type': None,
        'min_rating': None,
        'instant_book': None
    }
    st.rerun()