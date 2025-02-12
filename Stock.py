import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from textblob import TextBlob
from smartapi import SmartConnect  # Angel Broking API
import datetime

# Angel Broking API Credentials
API_KEY = "mN0Yc5MP"
SECRET_KEY = "ea2177a7-d947-4f68-a844-e9b9e1da365c"
CLIENT_ID = "R12345"

NEWS_API_KEY = "953be01115d64859b8f1fe76e69d9a3c"

def get_smartapi_session():
    obj = SmartConnect(api_key=API_KEY)
    data = obj.generateSession(CLIENT_ID, SECRET_KEY)
    return obj

def fetch_stock_data():
    try:
        obj = get_smartapi_session()
        stock_data = []
        today = datetime.date.today()

        for ticker in nifty500_tickers[:300]:  # Limiting to 300 stocks
            stock = yf.Ticker(ticker + ".NS")
            hist = stock.history(period="1y")

            # Fetch Futures and Options Data
            future_price, call_price, put_price = None, None, None
            opt_trend = "Neutral"

            try:
                future_data = obj.ltpData("NSE", ticker, "FUT")
                call_data = obj.ltpData("NSE", ticker, "OPT")
                put_data = obj.ltpData("NSE", ticker, "PE")
                
                future_price = future_data['data']['ltp'] if 'data' in future_data else None
                call_price = call_data['data']['ltp'] if 'data' in call_data else None
                put_price = put_data['data']['ltp'] if 'data' in put_data else None
            except Exception as e:
                st.warning(f"Error fetching options data for {ticker}: {e}")

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
                "Futures Price": future_price,
                "Call Option Price": call_price,
                "Put Option Price": put_price,
                "Options Trend": opt_trend,
                "Sentiment Score": sentiment_score,
                "Recommendation": recommendation
            }
            stock_data.append(stock_info)

        return pd.DataFrame(stock_data)
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return pd.DataFrame()

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
