import streamlit as st
import pandas as pd
import requests
import os
import json

# Set your Openrouter API key (or set it as an environment variable)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

@st.cache_data
def load_data():
    # Load and clean the Airbnb NYC dataset
    try:
        df = pd.read_csv("Airbnb_Open_Data.csv", low_memory=False)
        # Clean price column - handle string values with $ and commas
        df['price'] = df['price'].str.replace('$', '').str.replace(',', '').astype(float)
        df = df.dropna(subset=['price'])  # Remove rows with missing prices
        
        # Ensure required columns exist and handle column name variations
        required_columns = ['price', 'neighbourhood', 'availability_365', 'number_of_reviews']
        column_mapping = {
            'availability_365': ['availability_365', 'availability', 'days_available'],
            'number_of_reviews': ['number_of_reviews', 'review_count', 'reviews']
        }
        
        # Map column variations to standard names
        for std_col, variations in column_mapping.items():
            if std_col not in df.columns:
                for var in variations:
                    if var in df.columns:
                        df[std_col] = df[var]
                        break
                if std_col not in df.columns:
                    df[std_col] = 0  # Default value if column not found
        
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
    "price": "mean",
    "availability_365": "mean",
    "number_of_reviews": "mean"
}).reset_index()

def get_llm_response_openrouter(conversation_history):
    """
    Call the Openrouter API to get a chatbot response.
    The conversation_history is a list of messages in the format:
      {"role": "system" | "user" | "assistant", "content": "text"}
    """
    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    payload = {
        "model": "gpt-4",  # You can also use "gpt-3.5-turbo" or another available model
        "messages": conversation_history,
        "max_tokens": 150,
        "temperature": 0.7,
    }
    response = requests.post(endpoint, headers=headers, json=payload)
    if response.status_code != 200:
        st.error(f"Error: {response.status_code} - {response.text}")
        return "Sorry, I encountered an error while fetching the response."
    response_json = response.json()
    return response_json["choices"][0]["message"]["content"].strip()

# Initialize chat history in session_state if not already present
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [
        {"role": "system", "content": "You are an Airbnb recommendation assistant. Based on the aggregated neighborhood data from the Airbnb NYC dataset, provide recommendations for the best place to live. The data context is: " +
         neighborhood_stats.to_json(orient='records')}
    ]

st.title("Airbnb Living Advisor Chatbot")
st.markdown("Chat with our bot to find out the best place to live based on Airbnb data!")

# Chat input widget
user_input = st.text_input("You:", key="user_input")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    # Call Openrouter API to generate a response using the conversation history
    bot_response = get_llm_response_openrouter(st.session_state.chat_history)
    st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
    st.experimental_rerun()  # Refresh the page to update the chat history

# Display the conversation history
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"**Bot:** {msg['content']}")
