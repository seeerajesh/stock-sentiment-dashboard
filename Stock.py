import streamlit as st
import pandas as pd
import yfinance as yf

# List of top 300 NSE stocks (replace with actual tickers)
nifty500_tickers = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "HCLTECH.NS", "ASIANPAINT.NS", "MARUTI.NS", "AXISBANK.NS",
    "ITC.NS", "ONGC.NS", "WIPRO.NS", "ULTRACEMCO.NS", "TITAN.NS",
    "SUNPHARMA.NS", "TATASTEEL.NS", "TECHM.NS", "NTPC.NS", "POWERGRID.NS",
    "BAJAJFINSV.NS", "JSWSTEEL.NS", "NESTLEIND.NS", "HDFCLIFE.NS", "DRREDDY.NS",
    "CIPLA.NS", "ADANIENT.NS", "GRASIM.NS", "BPCL.NS", "EICHERMOT.NS",
    "INDUSINDBK.NS", "BRITANNIA.NS", "COALINDIA.NS", "APOLLOHOSP.NS", "DIVISLAB.NS",
    "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "ADANIGREEN.NS", "PIDILITIND.NS", "DABUR.NS",
    "ICICIPRULI.NS", "HINDZINC.NS", "GAIL.NS", "IOC.NS", "SBILIFE.NS",
    "SIEMENS.NS", "LTI.NS", "PNB.NS", "M&M.NS", "BOSCHLTD.NS",
    "BANKBARODA.NS", "SRF.NS", "HAVELLS.NS", "BIOCON.NS", "AMBUJACEM.NS",
    "TATAPOWER.NS", "AUROPHARMA.NS", "TATAMOTORS.NS", "LUPIN.NS", "MPHASIS.NS"
]

# Function to fetch stock data
def fetch_stock_data():
    try:
        stock_data = []
        for ticker in nifty500_tickers[:300]:  # Limiting to 300 stocks
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
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return pd.DataFrame()

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
