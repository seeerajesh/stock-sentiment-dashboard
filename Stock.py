import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from textblob import TextBlob
import datetime
from bs4 import BeautifulSoup

# Fetch stock data
def fetch_stock_data():
    try:
        stock_data = []
        today = datetime.date.today()
        nifty500_tickers = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]  # Replace with actual top 300 stocks

        for ticker in nifty500_tickers[:300]:  # Limiting to 300 stocks
            stock = yf.Ticker(ticker + ".NS")
            hist = stock.history(period="1y")

            ma_9 = hist["Close"].rolling(window=9).mean().iloc[-1] if not hist.empty else None
            ma_50 = hist["Close"].rolling(window=50).mean().iloc[-1] if not hist.empty else None
            ma_trend = "Positive" if ma_9 and ma_50 and ma_9 > ma_50 else "Negative"

            stock_info = {
                "Stock": ticker,
                "Price": stock.info.get("currentPrice", None),
                "52W High": stock.info.get("fiftyTwoWeekHigh", None),
                "52W Low": stock.info.get("fiftyTwoWeekLow", None),
                "Volume": hist["Volume"].iloc[-1] if not hist.empty else None,
                "9 Day MA": ma_9,
                "50 Day MA": ma_50,
                "MA Trend": ma_trend
            }
            stock_data.append(stock_info)

        return pd.DataFrame(stock_data)
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return pd.DataFrame()

# Fetch stock-related news from Moneycontrol
def fetch_stock_news_moneycontrol(ticker):
    try:
        url = f"https://www.moneycontrol.com/news/tags/{ticker}.html"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, 'html.parser')

        articles = []
        for news in soup.find_all('li', class_='clearfix')[:5]:
            title_tag = news.find('h2')
            link_tag = news.find('a')
            if title_tag and link_tag:
                title = title_tag.text.strip()
                link = link_tag['href']
                articles.append({"Stock": ticker, "Title": title, "URL": link})

        return pd.DataFrame(articles)
    except Exception as e:
        st.error(f"Error fetching news data for {ticker}: {e}")
        return pd.DataFrame()

# Fetch options data from NSE API
def fetch_options_data_nse(symbol="RELIANCE"):
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.nseindia.com"
        })
        session.get("https://www.nseindia.com")  # Establish session

        url = "https://www.nseindia.com/api/option-chain-equities"
        params = {"symbol": symbol}
        response = session.get(url, params=params)
        
        if response.status_code != 200:
            st.error(f"Error fetching options data: HTTP {response.status_code}")
            return pd.DataFrame()
        
        data = response.json()
        
        options_data = []
        if "records" in data and "data" in data["records"]:
            for option in data["records"]["data"]:
                ce_data = option.get("CE", {})
                pe_data = option.get("PE", {})
                
                if ce_data:
                    historical_prices = fetch_historical_option_prices(symbol, ce_data.get("strikePrice"), "CE")
                    options_data.append({
                        "Stock": symbol,
                        "Option Type": "CE",
                        "Expiry Date": ce_data.get("expiryDate", "N/A"),
                        "Strike Price": ce_data.get("strikePrice", "N/A"),
                        "Last Traded Price": ce_data.get("lastPrice", "N/A"),
                        "5-Day Prices": historical_prices
                    })
                
                if pe_data:
                    historical_prices = fetch_historical_option_prices(symbol, pe_data.get("strikePrice"), "PE")
                    options_data.append({
                        "Stock": symbol,
                        "Option Type": "PE",
                        "Expiry Date": pe_data.get("expiryDate", "N/A"),
                        "Strike Price": pe_data.get("strikePrice", "N/A"),
                        "Last Traded Price": pe_data.get("lastPrice", "N/A"),
                        "5-Day Prices": historical_prices
                    })
        
        return pd.DataFrame(options_data) if options_data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching options data from NSE: {e}")
        return pd.DataFrame()

# Fetch historical option prices
def fetch_historical_option_prices(symbol, strike_price, option_type):
    try:
        stock = yf.Ticker(f"{symbol}.NS")
        hist = stock.history(period="5d")
        if not hist.empty:
            return list(hist["Close"][-5:].values)
    except Exception as e:
        st.error(f"Error fetching historical option prices: {e}")
    return []

# Streamlit UI Setup
st.title("Stock Sentiment Dashboard")

df = fetch_stock_data()

if not df.empty:
    df_sorted = df.sort_values(by='Stock', ascending=True).head(20)
    st.dataframe(df_sorted)

    st.sidebar.header("Filters")
    selected_stock = st.sidebar.selectbox("Select Stock", ['All'] + list(df['Stock'].unique()))
    if selected_stock != 'All':
        df_sorted = df_sorted[df_sorted['Stock'] == selected_stock]

    st.write("### Filtered Stocks")
    st.dataframe(df_sorted)

    # Fetch and display news data
    st.write("### Stock News")
    news_df = pd.concat([fetch_stock_news_moneycontrol(ticker) for ticker in df['Stock'].unique()])
    if not news_df.empty:
        st.dataframe(news_df)
    else:
        st.warning("No news available for selected stocks.")
    
    # Fetch and display options data from NSE
    st.write("### Options Data (NSE API)")
    options_df = fetch_options_data_nse()
    if not options_df.empty:
        st.dataframe(options_df)
    else:
        st.warning("No options data available.")
else:
    st.warning("No stock data available.")
