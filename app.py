import yfinance as yf
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import numpy as np
import ta
import plotly.graph_objects as go

# UI
dark_mode = st.toggle("🌙 Enable Dark Mode")

if dark_mode:
    st.markdown("""
        <style>
            body { background-color: #0e1117; color: white; }
            .stApp { background-color: #0e1117; color: white; }
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
            body { background-color: white; color: black; }
            .stApp { background-color: white; color: black; }
        </style>
        """, unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([" Overview", " Trend & Indicator Analysis", " Candlestick chart", "Downloads"])

with tab1:
    st.title(" Multi-Stock Market Visualizer & Analyzer")

    st.write("""
    Welcome to your all-in-one dashboard for tracking and comparing global stocks.  
    Simply enter one or more ticker symbols (e.g., **AAPL, MSFT, TSLA**), pick a time range, and explore:

    - 📈 Historical closing prices
    - 🔁 Moving average crossovers with buy/sell signals
    - 📊 Technical indicators (RSI, MACD, etc)
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
                st.markdown(f"### Stock Data Overview: {ticker}")
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

                st.markdown("### Price Chart with Moving Averages & Trading Signals")
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
                try:
                    with st.expander(" Stock Analysis (Click to Expand)"):
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

                except Exception as e:
                    st.error(f"An error occurred: {e}")
        except Exception as e:
                    st.error(f"An error occurred: {e}")



with tab2:
    st.subheader(" Trend & Indicator Analysis")

    st.markdown("### Price Chart with Moving Averages & Trading Signals")
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

    st.markdown("### Technical Indicator Trends")
    st.write("""
    This section helps you explore key technical indicators to understand market trends, momentum, and potential reversal points.

    You can choose from options like RSI, MACD, SMA, and EMA to analyze price behavior over time.
    """)
    # Let user choose which indicators to show
    indicators_selected = st.multiselect(
        "Choose Technical Indicators to Display",
        ["RSI", "MACD", "SMA (50)", "SMA (100)", "EMA (20)", "EMA (50)"],
        default=["RSI", "MACD"]
    )

    # Compute selected indicators
    data = data.copy()

    if "RSI" in indicators_selected:
        data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()

    if "MACD" in indicators_selected:
        data['MACD'] = ta.trend.MACD(data['Close']).macd()

    if "SMA (50)" in indicators_selected:
        data['SMA (50)'] = data['Close'].rolling(window=50).mean()

    if "SMA (100)" in indicators_selected:
        data['SMA (100)'] = data['Close'].rolling(window=100).mean()

    if "EMA (20)" in indicators_selected:
        data['EMA (20)'] = data['Close'].ewm(span=20, adjust=False).mean()

    if "EMA (50)" in indicators_selected:
        data['EMA (50)'] = data['Close'].ewm(span=50, adjust=False).mean()

    # Filter only selected columns that exist in the dataframe
    plot_cols = [col for col in indicators_selected if col in data.columns]

    # Display line chart
    if plot_cols:
        st.line_chart(data[plot_cols])
    else:
        st.warning("Please select at least one indicator to visualize.")

    # Optional: Add explanation for each technical indicator 
    with st.expander(" Indicator Descriptions (Click to Expand)"):
        st.markdown("""
        - **RSI (Relative Strength Index)**:  
        Identifies overbought (>70) or oversold (<30) conditions in the market.

        - **MACD (Moving Average Convergence Divergence)**:  
        Tracks momentum shifts through short- and long-term moving averages.

        - **SMA (Simple Moving Average)**:  
        Smooths out price data by averaging over a defined period (e.g., 50, 100 days).

        - **EMA (Exponential Moving Average)**:  
        Like SMA but gives more weight to recent prices, making it more responsive.

        These indicators help detect trend strength, reversals, and potential entry/exit signals.
        """)


with tab3:
    #candle stick chart
    fig_candle = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close']
    )])
    st.subheader("Candlestick Chart")

    st.markdown("""
    This candlestick chart shows daily price action with:

    - 🟩 **Green candles**: Closing price is higher than opening → bullish
    - 🟥 **Red candles**: Closing price is lower than opening → bearish
    - **Wicks**: Represent the intraday high and low

    Use this chart to analyze price trends, market sentiment, and volatility.
    """)

    # Render the candlestick chart
    st.plotly_chart(fig_candle)


# download the data
with tab4: 
    st.subheader("📥 Download Your Data")

    st.write("""
    Export your selected stock's historical data for further analysis, reporting, or personal records.  
    This includes:
    
    - **OHLC (Open, High, Low, Close)** prices  
    - **Volume**  
    - **Moving Averages (if selected)**  
    - **Technical Indicators (RSI, MACD, etc.)**  
    
    Data is formatted as a `.csv` file and encoded in UTF-8 for maximum compatibility.
    """)

    csv = data.to_csv().encode('utf-8')
    st.download_button(
        "⬇️ Download CSV",
        csv,
        "stock_data.csv",
        "text/csv",
        key='download-csv'
    )

