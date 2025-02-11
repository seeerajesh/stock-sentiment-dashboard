import streamlit as st
import pandas as pd
import yfinance as yf

# Function to fetch top 300 NSE stocks from Yahoo Finance
def fetch_stock_data():
    # Fetch top 300 NSE stocks dynamically
    nifty500_tickers = [ticker + ".NS" for ticker in pd.read_html("https://en.wikipedia.org/wiki/NIFTY_500")[1]["Symbol"].head(300).tolist()]
    
    stock_data = []
    for ticker in nifty500_tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        stock_info = {
            "Stock": ticker,
            "Price": stock.info.get("currentPrice", None),
            "52W High": stock.info.get("fiftyTwoWeekHigh", None),
            "52W Low": stock.info.get("fiftyTwoWeekLow", None),
            "Volume": hist["Volume"].iloc[-1] if not hist.empty else None,
            "9 Day MA": hist["Close"].rolling(window=9).mean().iloc[-1] if not hist.empty else None,
            "50 Day MA": hist["Close"].rolling(window=50).mean().iloc[-1] if not hist.empty else None,
            "Futures Price": None,  # Placeholder for F&O data
            "Options Price": None,  # Placeholder for F&O data
            "Sentiment Score": None,  # Placeholder for sentiment analysis
            "Recommendation": None  # Placeholder for buy/sell logic
        }
        stock_data.append(stock_info)
    
    return pd.DataFrame(stock_data)

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
