import yfinance as yf
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import numpy as np
import ta
import plotly.graph_objects as go

st.title(" Multi-Stock Market Visualizer & Analyzer")

st.write("""
Welcome to your all-in-one dashboard for tracking and comparing global stocks.  
Simply enter one or more ticker symbols (e.g., **AAPL, MSFT, TSLA**), pick a time range, and explore:

- 📈 Historical closing prices
- 🔁 Moving average crossovers with buy/sell signals
- 📊 Technical indicators (RSI, MACD)
- 🕯️ Interactive candlestick charts
- 📥 Downloadable CSV of Raw data

Ideal for retail investors, students, and market enthusiasts.
""")


tickers = st.text_input("Enter Ticker Symbols (comma-separated, e.g., AAPL, MSFT, TSLA)", "AAPL, MSFT")
start_date, end_date = st.date_input(
    "Select Date Range",
    value=(datetime.date(2024, 1, 1), datetime.date.today())
)

# Slider to choose the moving averages window
short_window = st.slider("Short-Term MA (days)", min_value=2, max_value=50, value=10)
long_window = st.slider("Long-Term MA (days)", min_value=10, max_value=200, value=30)

if tickers:
    tickers = [t.strip().upper() for t in tickers.split(",")]
    all_data = {}

    for symbol in tickers:
        stock = yf.Ticker(symbol)
        hist = stock.history(start=start_date, end=end_date)
        if hist.empty:
            st.warning(f"⚠️ No data found for {symbol}")
        else:
            hist = hist[['Close']].rename(columns={'Close': symbol})
            all_data[symbol] = hist

    if all_data:
        merged_df = pd.concat(all_data.values(), axis=1)
        st.subheader("📊 Multi-Stock Closing Price Comparison")
        st.line_chart(merged_df)


if tickers:
    ticker = tickers[0]  # Use the first stock for detailed analysis

    try:
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)

        if data.empty:
            st.warning("⚠️ No data available. Try a different symbol or period.")
        if start_date >= end_date:
            st.error("Start date must be before end date.")
        else:
            # Calculate Moving averages
            data = stock.history(start=start_date, end=end_date)
            data['Short_MA'] = data['Close'].rolling(window=short_window).mean()
            data['Long_MA'] = data['Close'].rolling(window=long_window).mean()

            data['Signal'] = 0  # default: no signal
            data['Signal'][short_window:] = np.where(
                data['Short_MA'][short_window:] > data['Long_MA'][short_window:], 1, 0
            )
            data['Position'] = data['Signal'].diff()

            # Show table for stock prices
            st.markdown("### Stock Data Overview")
            st.write("""
            The table below displays the raw historical data for the selected stock(s) over the chosen time range.  
            It includes key trading metrics like:

            - **Open**: Price at the start of the trading day  
            - **High / Low**: Highest and lowest prices during the day  
            - **Close**: Final trading price of the day  
            - **Volume**: Total number of shares traded  
            - **Dividends & Splits**: Corporate actions (if any)

            """)
            st.dataframe(data)

            # Plot moving averages graph
            # Plot with Buy/Sell Signals
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(data['Close'], label="Closing Price", color='blue')
            ax.plot(data['Short_MA'], label=f"{short_window}-Day Short MA", color='orange')
            ax.plot(data['Long_MA'], label=f"{long_window}-Day Long MA", color='green')

            # Plot Buy Signals (Golden Cross)
            ax.plot(data[data['Position'] == 1].index,
                    data['Short_MA'][data['Position'] == 1],
                    '^', markersize=10, color='green', label='Buy Signal')

            # Plot Sell Signals (Death Cross)
            ax.plot(data[data['Position'] == -1].index,
                    data['Short_MA'][data['Position'] == -1],
                    'v', markersize=10, color='red', label='Sell Signal')

            st.markdown("### 📉 Price Chart with Moving Averages & Trading Signals")
            st.write("""
            This chart shows the stock's **daily closing price** along with its **short-term and long-term moving averages**.  
            We also highlight **Buy** and **Sell signals** based on moving average crossovers:

            - ✅ A **Buy Signal** (green ▲) appears when the short MA crosses above the long MA — potential uptrend  
            - ❌ A **Sell Signal** (red ▼) appears when the short MA crosses below the long MA — possible downtrend

            Use these signals as technical cues, not guaranteed predictors.
            """)

            ax.set_title("Stock Price with Moving Averages and Buy/Sell Signals")
            ax.set_xlabel("Date")
            ax.set_ylabel("Price (USD)")
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)


            # Stock Analysis
            with st.expander("📈 Stock Analysis (Click to Expand)"):
                st.write("""
                This section summarizes the stock's overall performance during the selected time period.
                
                - **Highest Price**: The peak price observed
                - **Lowest Price**: The lowest recorded trading price
                - **Percentage Change**: % gain or loss from start to end

                Use this for a quick performance snapshot before diving into technical indicators.
                """)
                
                highest_price = data['High'].max()
                lowest_price = data['Low'].min()
                pct_change = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100

                st.write(f"**Highest Price:** ${highest_price:.2f}")
                st.write(f"**Lowest Price:** ${lowest_price:.2f}")
                st.write(f"**Percentage Change:** {pct_change:.2f}%")


# Technical indicators (RSI, MACD)
data = data.copy()
data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
data['MACD'] = ta.trend.MACD(data['Close']).macd()

st.subheader("📊 Technical Indicators")
st.line_chart(data[['RSI', 'MACD']])

#candle stick chart
fig_candle = go.Figure(data=[go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close']
)])
st.subheader("📊 Candlestick Chart")
st.plotly_chart(fig_candle)

#download the csv
csv = data.to_csv().encode('utf-8')
st.download_button(
    "Download CSV",
    csv,
    "stock_data.csv",
    "text/csv",
    key='download-csv'
)
