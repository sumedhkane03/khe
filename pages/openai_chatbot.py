import streamlit as st
import pandas as pd
import openai
import os

# Set your OpenAI API key (or set it as an environment variable)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

@st.cache_data
def load_data():
    # Load and clean the Airbnb NYC dataset
    try:
        df = pd.read_csv("Airbnb_Open_Data.csv", low_memory=False)
        # Clean price column - handle string values with $ and commas
        df['price'] = df['price'].str.replace('$', '').str.replace(',', '').astype(float)
        df = df.dropna(subset=['price'])  # Remove rows with missing prices
        
        # Remove outliers by filtering listings above the 95th percentile of price
        df = df[df["price"] < df["price"].quantile(0.95)]
        return df
    except FileNotFoundError:
        st.error("Error: Could not find the Airbnb dataset file. Please ensure 'Airbnb_Open_Data.csv' is in the correct directory.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

data = load_data()

# Compute aggregated neighborhood statistics
neighborhood_stats = data.groupby("neighbourhood").agg({
    "price": ["mean", "min", "max"],
    "availability_365": "mean",
    "number_of_reviews": "mean",
    "review_rate_number": "mean"
}).reset_index()

def get_openai_response(conversation_history):
    """Call the OpenAI API to get a chatbot response."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=conversation_history,
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return "Sorry, I encountered an error while fetching the response."

# Initialize chat history in session_state if not already present
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [
        {"role": "system", "content": f"""You are an Airbnb recommendation assistant for NYC properties. 
        Use this neighborhood statistics data to provide informed recommendations: {neighborhood_stats.to_json(orient='records')}
        
        Key points to consider in your responses:
        1. Use the neighborhood statistics to compare prices and ratings
        2. Mention specific neighborhood insights when relevant
        3. Provide data-driven recommendations
        4. Be conversational and helpful
        5. When discussing prices, always provide context (e.g., compared to neighborhood average)
        6. Highlight unique features of recommended areas
        """}
    ]

st.title("🏠 NYC Airbnb Advisor (Powered by OpenAI)")
st.markdown("""Chat with our AI assistant to find the perfect Airbnb in NYC! 
I can help you understand:
- Neighborhood insights and comparisons
- Price ranges and value opportunities
- Popular areas and hidden gems
- Local amenities and characteristics
""")

# Chat input widget
user_input = st.text_input("You:", key="user_input")

if user_input and not user_input.isspace():
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Get AI response
    bot_response = get_openai_response(st.session_state.chat_history)
    st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
    st.experimental_rerun()  # Refresh the page to update the chat history

# Display the conversation history
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"**Assistant:** {msg['content']}")

# Add a note about the OpenAI API key
st.sidebar.markdown("### Configuration")
if not OPENAI_API_KEY:
    st.sidebar.warning("Please set your OpenAI API key in the environment variables to enable the chatbot.")