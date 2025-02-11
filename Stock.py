import streamlit as st
import pandas as pd
import requests

# Placeholder function to fetch stock data (Replace with actual API calls)
def fetch_stock_data():
    data = {
        'Stock': ['TCS', 'INFY', 'HDFCBANK', 'RELIANCE', 'SBIN'],
        'Price': [3650, 1500, 1600, 2500, 600],
        '52W High': [4000, 1700, 1800, 2700, 650],
        '52W Low': [3200, 1300, 1400, 2200, 500],
        'Sentiment Score': [0.8, 0.6, -0.2, 0.3, -0.5],
        'Recommendation': ['BUY', 'BUY', 'HOLD', 'BUY', 'SELL']
    }
    return pd.DataFrame(data)

# Streamlit UI Setup
st.title("Stock Sentiment Dashboard")

# Fetch data
df = fetch_stock_data()

# Filter: Top 20 by Sentiment Score
df_sorted = df.sort_values(by='Sentiment Score', ascending=False).head(20)

# Display Dataframe
st.dataframe(df_sorted)

# Additional Filters
st.sidebar.header("Filters")
selected_stock = st.sidebar.selectbox("Select Stock", ['All'] + list(df['Stock'].unique()))
if selected_stock != 'All':
    df_sorted = df_sorted[df_sorted['Stock'] == selected_stock]

st.write("### Filtered Stocks")
st.dataframe(df_sorted)
