import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from textblob import TextBlob
from nsepy.derivatives import get_expiry_date
from nsepy import get_history
import datetime

# List of top 300 NSE stocks (replace with actual tickers)
nifty500_tickers = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BAJFINANCE", "BHARTIARTL", "KOTAKBANK",
    "LT", "HCLTECH", "ASIANPAINT", "MARUTI", "AXISBANK",
    "ITC", "ONGC", "WIPRO", "ULTRACEMCO", "TITAN"
]  # Extend to 300 stocks

NEWS_API_KEY = "953be01115d64859b8f1fe76e69d9a3c"

def fetch_stock_data():
    try:
        stock_data = []
        today = datetime.date.today()
        expiry_dates = get_expiry_date(year=today.year, month=today.month)
        if len(expiry_dates) > 1:
            expiry_date = expiry_dates[1]  # Taking the second nearest expiry
        else:
            expiry_date = expiry_dates[0]

        for ticker in nifty500_tickers[:300]:  # Limiting to 300 stocks
            stock = yf.Ticker(ticker + ".NS")
            hist = stock.history(period="1y")

            # Fetch futures and options data using nsepy
            future_data = get_history(symbol=ticker, start=today - datetime.timedelta(days=30),
                                      end=today, index=False, futures=True, expiry_date=expiry_date)
            option_data = get_history(symbol=ticker, start=today - datetime.timedelta(days=30),
                                      end=today, index=False, option_type="CE", expiry_date=expiry_date)
            put_data = get_history(symbol=ticker, start=today - datetime.timedelta(days=30),
                                   end=today, index=False, option_type="PE", expiry_date=expiry_date)

            # Get latest call and put prices
            latest_call = option_data.iloc[-1]["Close"] if not option_data.empty else None
            latest_put = put_data.iloc[-1]["Close"] if not put_data.empty else None

            # Fetch sentiment score
            sentiment_score = fetch_sentiment_score(ticker)

            # Moving Average Trend
            ma_9 = hist["Close"].rolling(window=9).mean().iloc[-1] if not hist.empty else None
            ma_50 = hist["Close"].rolling(window=50).mean().iloc[-1] if not hist.empty else None
            ma_trend = "Positive" if ma_9 and ma_50 and ma_9 > ma_50 else "Negative"

            # Options Sentiment
            opt_trend = "Neutral"
            if latest_call and latest_put:
                if latest_call > option_data.iloc[-2]["Close"]:
                    opt_trend = "Positive"
                if latest_put > put_data.iloc[-2]["Close"]:
                    opt_trend = "Negative"

            # Define recommendation
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
                "Futures Price": future_data.iloc[-1]["Close"] if not future_data.empty else None,
                "Call Option Price": latest_call,
                "Put Option Price": latest_put,
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
