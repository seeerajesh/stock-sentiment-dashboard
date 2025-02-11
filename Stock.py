import streamlit as st
import pandas as pd
import requests
import time
from bs4 import BeautifulSoup

# Function to fetch top 300 stocks from NSE India
def fetch_stock_data():
    url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)  # Establish session
    time.sleep(1)  # Avoid bot detection
    
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        st.error("Failed to fetch stock data from NSE. Try again later.")
        return pd.DataFrame()
    
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        st.error("Error decoding JSON response from NSE. NSE may be blocking access.")
        return pd.DataFrame()
    
    stocks = sorted(data.get("data", []), key=lambda x: x['totalTradedVolume'], reverse=True)[:300]
    df = pd.DataFrame(stocks)[['symbol', 'lastPrice', 'dayHigh', 'dayLow', 'totalTradedVolume']]
    df.rename(columns={
        'symbol': 'Stock',
        'lastPrice': 'Price',
        'dayHigh': '52W High',
        'dayLow': '52W Low',
        'totalTradedVolume': 'Volume'
    }, inplace=True)
    
    df['9 Day MA'] = df['Price']  # Placeholder, needs calculation
    df['50 Day MA'] = df['Price']  # Placeholder, needs calculation
    df['Futures Price'] = None  # Placeholder for F&O data
    df['Options Price'] = None  # Placeholder for F&O data
    df['Sentiment Score'] = None  # Placeholder for sentiment analysis
    df['Recommendation'] = None  # Placeholder for buy/sell logic
    
    return df

# Streamlit UI Setup
st.title("Stock Sentiment Dashboard")

# Fetch data
df = fetch_stock_data()

if not df.empty:
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
else:
    st.warning("No stock data available.")
