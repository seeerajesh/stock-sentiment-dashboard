import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from textblob import TextBlob
from bs4 import BeautifulSoup

# List of top 300 NSE stocks (replace with actual tickers)
nifty500_tickers = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "HCLTECH.NS", "ASIANPAINT.NS", "MARUTI.NS", "AXISBANK.NS",
    "ITC.NS", "ONGC.NS", "WIPRO.NS", "ULTRACEMCO.NS", "TITAN.NS"
]  # Extend to 300 stocks

NEWS_API_KEY = "953be01115d64859b8f1fe76e69d9a3c"

# Function to fetch stock data
def fetch_stock_data():
    try:
        stock_data = []
        for ticker in nifty500_tickers[:300]:  # Limiting to 300 stocks
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            
            # Fetch futures and options data (Placeholder logic)
            futures_price = None  # Replace with actual API call
            options_price = None  # Replace with actual API call
            
            # Fetch sentiment score
            sentiment_score = fetch_sentiment_score(ticker)
            
            # Define recommendation based on sentiment and trends
            recommendation = "BUY" if sentiment_score > 0.2 else "HOLD" if -0.2 <= sentiment_score <= 0.2 else "SELL"
            
            stock_info = {
                "Stock": ticker,
                "Price": stock.info.get("currentPrice", None),
                "52W High": stock.info.get("fiftyTwoWeekHigh", None),
                "52W Low": stock.info.get("fiftyTwoWeekLow", None),
                "Volume": hist["Volume"].iloc[-1] if not hist.empty else None,
                "9 Day MA": hist["Close"].rolling(window=9).mean().iloc[-1] if not hist.empty else None,
                "50 Day MA": hist["Close"].rolling(window=50).mean().iloc[-1] if not hist.empty else None,
                "Futures Price": futures_price,
                "Options Price": options_price,
                "Sentiment Score": sentiment_score,
                "Recommendation": recommendation
            }
            stock_data.append(stock_info)
        
        return pd.DataFrame(stock_data)
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return pd.DataFrame()

# Function to fetch sentiment score from News API
def fetch_sentiment_score(ticker):
    try:
        url = f"https://newsapi.org/v2/everything?q={ticker}&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        articles = response.json().get("articles", [])
        
        sentiment_total = 0
        for article in articles[:10]:  # Limit to first 10 articles
            sentiment = TextBlob(article["title"]).sentiment.polarity
            sentiment_total += sentiment
        
        return sentiment_total / len(articles) if articles else 0
    except Exception:
        return 0

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
