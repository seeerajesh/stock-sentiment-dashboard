import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from textblob import TextBlob
import datetime

# Alpha Vantage API Key (Replace with your key)
ALPHA_VANTAGE_API_KEY = "YOUR_API_KEY"

# Fetch stock data
def fetch_stock_data():
    try:
        stock_data = []
        today = datetime.date.today()
        nifty500_tickers = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]  # Replace with actual top 300 stocks

        for ticker in nifty500_tickers[:300]:  # Limiting to 300 stocks
            stock = yf.Ticker(ticker + ".NS")
            hist = stock.history(period="1y")

            sentiment_score = fetch_sentiment_score_alpha_vantage(ticker)

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
                "Sentiment Score": sentiment_score,
                "Recommendation": recommendation
            }
            stock_data.append(stock_info)

        return pd.DataFrame(stock_data)
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return pd.DataFrame()

# Fetch sentiment score via Alpha Vantage
def fetch_sentiment_score_alpha_vantage(ticker):
    try:
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        sentiment_total = 0
        count = 0
        
        if "feed" in data:
            for article in data["feed"][:5]:
                sentiment_score = article.get("overall_sentiment_score", 0)
                sentiment_total += sentiment_score
                count += 1
        
        return sentiment_total / count if count > 0 else 0
    except Exception:
        return 0

# Fetch stock-related news from Alpha Vantage
def fetch_stock_news_alpha_vantage(ticker):
    try:
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()

        articles = []
        if "feed" in data:
            for article in data["feed"][:5]:
                title = article.get("title", "No Title")
                url = article.get("url", "#")
                articles.append({"Stock": ticker, "Title": title, "URL": url})
        
        return pd.DataFrame(articles)
    except Exception as e:
        st.error(f"Error fetching news data for {ticker}: {e}")
        return pd.DataFrame()

# Fetch options data
def fetch_options_data(ticker):
    try:
        stock = yf.Ticker(ticker + ".NS")
        expiry_dates = stock.options
        options_data = []
        
        if expiry_dates:
            for expiry in expiry_dates[:1]:  # Limiting to the nearest expiry
                options = stock.option_chain(expiry)
                for option_type, df in zip(["Calls", "Puts"], [options.calls, options.puts]):
                    df["Type"] = option_type
                    df["Stock"] = ticker
                    df["Expiry"] = expiry
                    options_data.append(df)
        
        return pd.concat(options_data) if options_data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching options data for {ticker}: {e}")
        return pd.DataFrame()

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

    # Fetch and display news data
    st.write("### Stock News")
    news_df = pd.concat([fetch_stock_news_alpha_vantage(ticker) for ticker in df['Stock'].unique()])
    if not news_df.empty:
        st.dataframe(news_df)
    else:
        st.warning("No news available for selected stocks.")
    
    # Fetch and display options data
    st.write("### Options Data")
    options_df = pd.concat([fetch_options_data(ticker) for ticker in df['Stock'].unique()])
    if not options_df.empty:
        st.dataframe(options_df)
    else:
        st.warning("No options data available.")
else:
    st.warning("No stock data available.")
