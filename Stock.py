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
def fetch_options_data_nse():
    try:
        url = "https://www.nseindia.com/api/marketstatus"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        data = response.json()

        options_data = []
        if "giftnifty" in data:
            for contract in data["giftnifty"]:
                if contract["SYMBOL"] == "RELIANCE":
                    options_data.append({
                        "Stock": "RELIANCE",
                        "Type": contract["INSTRUMENTTYPE"],
                        "Strike Price": contract["STRIKEPRICE"],
                        "Expiry Date": contract["EXPIRYDATE"],
                        "Last Price": contract["LASTPRICE"],
                        "Day Change": contract["DAYCHANGE"],
                        "% Change": contract["PERCHANGE"],
                        "Contracts Traded": contract["CONTRACTSTRADED"]
                    })
        
        return pd.DataFrame(options_data) if options_data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching options data from NSE: {e}")
        return pd.DataFrame()

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
