import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import datetime
from bs4 import BeautifulSoup

def fetch_stock_data():
    try:
        stock_data = []
        nifty500_tickers = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]  # Replace with actual top 300 stocks

        for ticker in nifty500_tickers[:300]:
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

def fetch_options_data_nse(symbol="RELIANCE"):
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.nseindia.com"
        })

        url = "https://www.nseindia.com/api/option-chain-equities"
        params = {"symbol": symbol}
        response = session.get(url, params=params)

        if response.status_code != 200:
            st.error(f"Error fetching options data: HTTP {response.status_code}")
            return pd.DataFrame()
        
        data = response.json()
        if "records" not in data or "data" not in data["records"]:
            st.error("Unexpected response format from NSE API")
            return pd.DataFrame()
        
        options_data = []
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
                    **historical_prices
                })
            
            if pe_data:
                historical_prices = fetch_historical_option_prices(symbol, pe_data.get("strikePrice"), "PE")
                options_data.append({
                    "Stock": symbol,
                    "Option Type": "PE",
                    "Expiry Date": pe_data.get("expiryDate", "N/A"),
                    "Strike Price": pe_data.get("strikePrice", "N/A"),
                    "Last Traded Price": pe_data.get("lastPrice", "N/A"),
                    **historical_prices
                })
        
        return pd.DataFrame(options_data) if options_data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching options data from NSE: {e}")
        return pd.DataFrame()

def fetch_historical_option_prices(symbol, strike_price, option_type):
    try:
        stock = yf.Ticker(f"{symbol}.NS")
        hist = stock.history(period="5d")
        if not hist.empty:
            prices = hist["Close"][-5:].tolist()
            return {f"D-{5-i}": prices[i] for i in range(len(prices))}
    except Exception as e:
        st.error(f"Error fetching historical option prices: {e}")
    return {}

def fetch_news():
    try:
        url = "https://news.google.com/rss/search?q=India+stock+market&hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")

        news_data = []
        for item in items[:10]:
            news_data.append({
                "Title": item.title.text,
                "Link": item.link.text,
                "Publication Date": item.pubDate.text
            })

        return pd.DataFrame(news_data)
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return pd.DataFrame()

st.title("Stock Sentiment Dashboard")

df = fetch_stock_data()
if not df.empty:
    df_sorted = df.sort_values(by='Stock', ascending=True).head(20)
    st.dataframe(df_sorted)

    st.write("### Options Data (NSE API)")
    options_df = fetch_options_data_nse()
    if not options_df.empty:
        st.dataframe(options_df)
    else:
        st.warning("No options data available.")

    st.write("### Market News")
    news_df = fetch_news()
    if not news_df.empty:
        st.dataframe(news_df)
    else:
        st.warning("No news available.")
else:
    st.warning("No stock data available.")
