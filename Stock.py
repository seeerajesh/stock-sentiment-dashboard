import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import datetime

# Function to fetch stock data
def fetch_stock_data():
    try:
        stock_data = []
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

# Fetch options data from NSE API (without Selenium)
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
                    "D-5": historical_prices.get("D-5", "N/A"),
                    "D-4": historical_prices.get("D-4", "N/A"),
                    "D-3": historical_prices.get("D-3", "N/A"),
                    "D-2": historical_prices.get("D-2", "N/A"),
                    "D-1": historical_prices.get("D-1", "N/A"),
                })
            
            if pe_data:
                historical_prices = fetch_historical_option_prices(symbol, pe_data.get("strikePrice"), "PE")
                options_data.append({
                    "Stock": symbol,
                    "Option Type": "PE",
                    "Expiry Date": pe_data.get("expiryDate", "N/A"),
                    "Strike Price": pe_data.get("strikePrice", "N/A"),
                    "Last Traded Price": pe_data.get("lastPrice", "N/A"),
                    "D-5": historical_prices.get("D-5", "N/A"),
                    "D-4": historical_prices.get("D-4", "N/A"),
                    "D-3": historical_prices.get("D-3", "N/A"),
                    "D-2": historical_prices.get("D-2", "N/A"),
                    "D-1": historical_prices.get("D-1", "N/A"),
                })
        
        return pd.DataFrame(options_data) if options_data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching options data from NSE: {e}")
        return pd.DataFrame()

# Fetch historical option prices (Placeholder, needs a working data source)
def fetch_historical_option_prices(symbol, strike_price, option_type):
    try:
        stock = yf.Ticker(f"{symbol}.NS")
        hist = stock.history(period="5d")
        if not hist.empty:
            prices = hist["Close"][-5:].tolist()
            return {f"D-{i+1}": prices[i] for i in range(len(prices))}
    except Exception as e:
        st.error(f"Error fetching historical option prices: {e}")
    return {}

# Streamlit UI Setup
st.title("Stock Sentiment Dashboard")

df = fetch_stock_data()

if not df.empty:
    df_sorted = df.sort_values(by='Stock', ascending=True).head(20)
    st.dataframe(df_sorted)

    # Fetch and display options data from NSE
    st.write("### Options Data (NSE API)")
    options_df = fetch_options_data_nse()
    if not options_df.empty:
        st.dataframe(options_df)
    else:
        st.warning("No options data available.")
else:
    st.warning("No stock data available.")
