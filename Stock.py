import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from textblob import TextBlob
import datetime

# Angel Broking API Credentials (Not used for now)
API_KEY = "mN0Yc5MP"
SECRET_KEY = "f84c35fb-f7ba-47e0-9939-89e9100a97c1"
CLIENT_ID = "R12345"
NEWS_API_KEY = "953be01115d64859b8f1fe76e69d9a3c"

# Fetch stock data

def fetch_stock_data():
    try:
        stock_data = []
        today = datetime.date.today()
        nifty500_tickers = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]  # Replace with actual top 300 stocks

        for ticker in nifty500_tickers[:300]:  # Limiting to 300 stocks
            stock = yf.Ticker(ticker + ".NS")
            hist = stock.history(period="1y")

            sentiment_score = fetch_sentiment_score(ticker)

            ma_9 = hist["Close"].rolling(window=9).mean().iloc[-1] if not hist.empty else None
            ma_50 = hist["Close"].rolling(window=50).mean().iloc[-1] if not hist.empty else None
            ma_trend = "Positive" if ma_9 and ma_50 and ma_9 > ma_50 else "Negative"

            recommendation = "BUY" if sentiment_score > 0.2 else "HOLD" if -0.2 <= sentiment_score <= 0.2 else "SELL"

            stock_info = {
                "Stock": ticker,
                "Price": stock.info.get("currentPrice", None),
                "52W High": stock.info.get("fiftyTwoWeekHigh", None),
                "52W Low": stock.info.get("fiftyTwoWeekLow", None),
                "Volume": hist["Volume"].iloc[-1] if not hist.empty else None,
                "9 Day MA": ma_9,
                "50 Day MA": ma_50,
                "MA Trend": ma_trend,
                "Futures Price": None,
                "Call Option Price": None,
                "Put Option Price": None,
                "Options Trend": "Neutral",
                "Sentiment Score": sentiment_score,
                "Recommendation": recommendation
            }
            stock_data.append(stock_info)

        return pd.DataFrame(stock_data)
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return pd.DataFrame()

# Fetch sentiment score
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

df = fetch_stock_data()

if not df.empty:
    df_sorted = df.sort_values(by='Sentiment Score', ascending=False).head(20)
    st.dataframe(df_sorted)

    st.sidebar.header("Filters")
    selected_stock = st.sidebar.selectbox("Select Stock", ['All'] + list(df['Stock'].unique()))
    if selected_stock != 'All':
        df_sorted = df_sorted[df_sorted['Stock'] == selected_stock]

    st.write("### Filtered Stocks")
    st.dataframe(df_sorted)
else:
    st.warning("No stock data available.")
