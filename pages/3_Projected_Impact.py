import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Set page config
st.set_page_config(
    page_title="Market Predictions - NYC Airbnb",
    page_icon="🔮",
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

st.title("🔮 NYC Airbnb Market Predictions")
st.markdown("""
    Explore detailed market predictions and forecasts for the NYC Airbnb market. 
    This analysis helps you understand future trends, seasonal patterns, and potential 
    market opportunities.
""")

# Initialize neighborhoods and room types
neighborhoods = sorted([n for n in df['neighbourhood'].unique() if pd.notna(n)])
room_types = sorted([rt for rt in df['room_type'].unique() if pd.notna(rt)])

# Sidebar filters
st.sidebar.header("Prediction Filters 🎯")

# Add neighborhood selection
selected_neighborhoods = st.sidebar.multiselect(
    "Select Neighborhoods",
    options=neighborhoods,
    default=neighborhoods[:3] if len(neighborhoods) >= 3 else neighborhoods
)

# Add room type selection
selected_room_types = st.sidebar.multiselect(
    "Select Room Types",
    options=room_types,
    default=room_types[:3] if len(room_types) >= 3 else room_types
)

# Filter data based on selections
if not selected_neighborhoods or not selected_room_types:
    st.warning("Please select at least one neighborhood and room type from the sidebar.")
    filtered_data = pd.DataFrame()
else:
    filtered_data = df[
        (df['neighbourhood'].isin(selected_neighborhoods)) &
        (df['room_type'].isin(selected_room_types))
    ]

    if not filtered_data.empty:
        # Price Trend Forecasting
        st.header("📈 Price Trend Forecasting")
        
        # Calculate historical price trends
        price_trends = filtered_data.groupby('neighbourhood')['price'].agg([
            'mean',
            'std',
            lambda x: np.percentile(x, 25),
            lambda x: np.percentile(x, 75)
        ]).reset_index()
        price_trends.columns = ['neighbourhood', 'mean_price', 'std_price', 'lower_quartile', 'upper_quartile']
        
        # Generate future dates for forecasting
        future_dates = pd.date_range(start=datetime.now(), periods=12, freq='M')
        
        # Create forecast visualization
        forecast_data = []
        for _, row in price_trends.iterrows():
            base_price = row['mean_price']
            std_price = row['std_price']
            
            # Generate forecasted prices with some randomness and trend
            for i, date in enumerate(future_dates):
                seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * i / 12)  # Seasonal variation
                trend_factor = 1 + 0.02 * i  # Upward trend
                forecasted_price = base_price * seasonal_factor * trend_factor
                
                forecast_data.append({
                    'date': date,
                    'neighbourhood': row['neighbourhood'],
                    'forecasted_price': forecasted_price,
                    'lower_bound': forecasted_price - std_price,
                    'upper_bound': forecasted_price + std_price
                })
        
        forecast_df = pd.DataFrame(forecast_data)
        
        # Plot price forecasts
        fig_forecast = px.line(
            forecast_df,
            x='date',
            y='forecasted_price',
            color='neighbourhood',
            title='12-Month Price Forecast by Neighborhood',
            labels={
                'date': 'Month',
                'forecasted_price': 'Forecasted Price ($)',
                'neighbourhood': 'Neighborhood'
            }
        )
        
        # Add confidence intervals
        for neighborhood in forecast_df['neighbourhood'].unique():
            neighborhood_data = forecast_df[forecast_df['neighbourhood'] == neighborhood]
            fig_forecast.add_scatter(
                x=neighborhood_data['date'].tolist() + neighborhood_data['date'].tolist()[::-1],
                y=neighborhood_data['upper_bound'].tolist() + neighborhood_data['lower_bound'].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(0,100,80,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                name=f'{neighborhood} Confidence Interval'
            )
        
        st.plotly_chart(fig_forecast, use_container_width=True)
        
        # Seasonal Demand Analysis
        st.header("🌊 Seasonal Demand Patterns")
        
        # Calculate seasonal metrics
        seasonal_col1, seasonal_col2, seasonal_col3 = st.columns(3)
        
        with seasonal_col1:
            peak_season_premium = ((filtered_data['price'].quantile(0.75) / 
                                  filtered_data['price'].quantile(0.25)) - 1) * 100
            st.metric(
                "Peak Season Premium",
                f"{peak_season_premium:.1f}%",
                help="Expected price premium during high-demand seasons"
            )
        
        with seasonal_col2:
            occupancy_prediction = filtered_data['availability_365'].mean()
            st.metric(
                "Predicted Occupancy",
                f"{100 - (occupancy_prediction/365*100):.1f}%",
                help="Forecasted average occupancy rate"
            )
        
        with seasonal_col3:
            demand_score = (filtered_data['number_of_reviews'].mean() / 
                          df['number_of_reviews'].mean()) * 100
            st.metric(
                "Relative Demand Score",
                f"{demand_score:.1f}",
                help="Demand score relative to market average (100 = average)"
            )
        
        # Market Growth Indicators
        st.header("📊 Market Growth Indicators")
        
        # Calculate growth metrics
        growth_col1, growth_col2 = st.columns(2)
        
        with growth_col1:
            price_momentum = ((filtered_data['price'].mean() - df['price'].mean()) / 
                            df['price'].mean()) * 100
            st.metric(
                "Price Momentum",
                f"{price_momentum:.1f}%",
                delta=f"{price_momentum:.1f}% vs Market Average"
            )
            
            # Price Growth Forecast
            current_avg_price = filtered_data['price'].mean()
            forecasted_growth = current_avg_price * (1 + price_momentum/100)
            st.metric(
                "12-Month Price Forecast",
                f"${forecasted_growth:.2f}",
                delta=f"${forecasted_growth - current_avg_price:.2f} change"
            )
        
        with growth_col2:
            # Market Saturation Analysis
            total_listings = len(filtered_data)
            total_market = len(df)
            market_share = (total_listings / total_market) * 100
            
            st.metric(
                "Market Share",
                f"{market_share:.1f}%",
                help="Selected segments' share of total market"
            )
            
            # Competition Index
            avg_reviews_per_listing = filtered_data['number_of_reviews'].mean()
            competition_index = (avg_reviews_per_listing / 
                               df['number_of_reviews'].mean()) * 100
            
            st.metric(
                "Competition Index",
                f"{competition_index:.1f}",
                help="Measure of market competition (100 = average)"
            )
        
        # Investment Recommendations
        st.header("💡 Investment Insights")
        
        # Generate recommendations based on analysis
        recommendations = []
        
        # Price-based recommendations
        if price_momentum > 5:
            recommendations.append(f"Strong price growth potential with {price_momentum:.1f}% price momentum")
        elif price_momentum < -5:
            recommendations.append("Consider competitive pricing strategies in this market")
        
        # Demand-based recommendations
        if demand_score > 110:
            recommendations.append("High demand market with strong booking potential")
        elif demand_score < 90:
            recommendations.append("Consider marketing strategies to increase visibility")
        
        # Seasonality recommendations
        if peak_season_premium > 20:
            recommendations.append(f"Strong seasonal variation with {peak_season_premium:.1f}% peak season premium")
        
        # Competition recommendations
        if competition_index > 110:
            recommendations.append("Highly competitive market - focus on differentiation")
        elif competition_index < 90:
            recommendations.append("Market opportunity with lower competition")
        
        # Display recommendations
        for rec in recommendations:
            st.info(rec)
        
        # Risk Assessment
        st.subheader("⚠️ Risk Assessment")
        
        risk_score = 0
        risk_factors = []
        
        # Price volatility risk
        price_volatility = filtered_data['price'].std() / filtered_data['price'].mean()
        if price_volatility > 0.5:
            risk_score += 2
            risk_factors.append("High price volatility")
        
        # Market saturation risk
        if market_share > 30:
            risk_score += 1
            risk_factors.append("High market saturation")
        
        # Seasonal dependency risk
        if peak_season_premium > 30:
            risk_score += 1
            risk_factors.append("High seasonal dependency")
        
        # Competition risk
        if competition_index > 120:
            risk_score += 1
            risk_factors.append("Intense competition")
        
        # Display risk assessment
        risk_level = "Low" if risk_score <= 1 else "Moderate" if risk_score <= 3 else "High"
        st.metric("Risk Level", risk_level, help="Overall risk assessment based on multiple factors")
        
        if risk_factors:
            st.caption("Key Risk Factors:")
            for factor in risk_factors:
                st.warning(factor)
        else:
            st.success("No significant risk factors identified")