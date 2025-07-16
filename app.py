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
    st.title("FinSight; Multi-Stock Market Visualizer & Analyzer")

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

    # --- Ticker input and date range ---
    tickers_input = st.text_input("Enter Ticker Symbols (comma-separated)", "AAPL, MSFT")
    start_date, end_date = st.date_input(
        "Select Date Range",
        value=(datetime.date(2024, 1, 1), datetime.date.today())
    )

    # --- Moving Average sliders ---
    short_window = st.slider("Short-Term MA (days)", min_value=2, max_value=50, value=10)
    long_window = st.slider("Long-Term MA (days)", min_value=10, max_value=200, value=30)

    # --- Fetch data for all tickers ---
    if tickers_input:
        tickers = [t.strip().upper() for t in tickers_input.split(",")]
        all_data = {}

        for symbol in tickers:
            stock = yf.Ticker(symbol)
            hist = stock.history(start=start_date, end=end_date)
            if hist.empty:
                st.warning(f"⚠️ No data found for {symbol}")
            else:
                all_data[symbol] = hist  # Full data, including OHLC

        # --- Multi-stock closing price chart ---
        if all_data:
            close_df = pd.concat([df['Close'].rename(sym) for sym, df in all_data.items()], axis=1)
            st.subheader("📉 Multi-Stock Closing Price Comparison")
            st.line_chart(close_df)

        # --- Single stock selection for detailed view ---
        if all_data:
            selected_ticker = st.selectbox("Select a stock to view detailed analysis:", list(all_data.keys()))
            data = all_data[selected_ticker].copy()

            st.markdown(f"### 📋 Stock Data Overview: {selected_ticker}")
            st.write("""
            The table below displays the raw historical data for the selected stock over the chosen time range.  
            It includes key trading metrics like:

            - **Open**: Price at the start of the trading day  
            - **High / Low**: Highest and lowest prices during the day  
            - **Close**: Final trading price of the day  
            - **Volume**: Total number of shares traded  
            - **Dividends & Splits**: Corporate actions (if any)
            """)
            st.dataframe(data)

            # --- Analysis + Moving Average Crossovers ---
            try:
                data['Short_MA'] = data['Close'].rolling(window=short_window).mean()
                data['Long_MA'] = data['Close'].rolling(window=long_window).mean()
                data['Signal'] = 0
                data['Signal'][short_window:] = np.where(
                    data['Short_MA'][short_window:] > data['Long_MA'][short_window:], 1, 0
                )
                data['Position'] = data['Signal'].diff()

                with st.expander("📊 Stock Analysis (Click to Expand)"):
                    highest_price = data['High'].max()
                    lowest_price = data['Low'].min()
                    pct_change = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100

                    st.write(f"**Highest Price:** ${highest_price:.2f}")
                    st.write(f"**Lowest Price:** ${lowest_price:.2f}")
                    st.write(f"**Percentage Change:** {pct_change:.2f}%")
            except Exception as e:
                st.error(f"❌ Error during analysis: {e}")


#technical overview
with tab2:
    # Let the user choose one ticker to analyze
    selected_ticker = st.selectbox(
        "Select a stock to view detailed analysis",
        list(all_data.keys()),
        key="section1"
    )
    selected_data = all_data[selected_ticker].copy()

    st.markdown("### Price Chart with Moving Averages & Trading Signals")
    st.write("""
        This chart shows the stock's **daily closing price** along with its **short-term and long-term moving averages**.  
        We also highlight **Buy** and **Sell signals** based on moving average crossovers:

        - ✅ A **Buy Signal** (green ▲) appears when the short MA crosses above the long MA — potential uptrend  
        - ❌ A **Sell Signal** (red ▼) appears when the short MA crosses below the long MA — possible downtrend

        Use these signals as technical cues, not guaranteed predictors.
    """)

    # Calculate moving averages
    selected_data["Short_MA"] = selected_data["Close"].rolling(window=short_window).mean()
    selected_data["Long_MA"] = selected_data["Close"].rolling(window=long_window).mean()

    # Identify buy/sell signals
    buy_signals = (selected_data["Short_MA"] > selected_data["Long_MA"]) & \
                  (selected_data["Short_MA"].shift() <= selected_data["Long_MA"].shift())
    sell_signals = (selected_data["Short_MA"] < selected_data["Long_MA"]) & \
                   (selected_data["Short_MA"].shift() >= selected_data["Long_MA"].shift())

    # Plot chart
    fig, ax = plt.subplots()
    ax.plot(selected_data.index, selected_data["Close"], label="Close", color="blue")
    ax.plot(selected_data.index, selected_data["Short_MA"], label=f"{short_window}-Day MA", color="green")
    ax.plot(selected_data.index, selected_data["Long_MA"], label=f"{long_window}-Day MA", color="red")
    ax.scatter(selected_data.index[buy_signals], selected_data["Close"][buy_signals], marker="^", color="green", label="Buy Signal")
    ax.scatter(selected_data.index[sell_signals], selected_data["Close"][sell_signals], marker="v", color="red", label="Sell Signal")
    ax.set_title(f"{selected_ticker} - Price with Moving Averages & Signals")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()
    st.pyplot(fig)

    # Technical Indicators Section
    st.markdown("### Technical Indicator Trends")
    st.write("""
        This section helps you explore key technical indicators to understand market trends, momentum, and potential reversal points.
        You can choose from options like RSI, MACD, SMA, and EMA to analyze price behavior over time.
    """)

    indicators_selected = st.multiselect(
        "Choose Technical Indicators to Display",
        ["RSI", "MACD", "SMA (50)", "SMA (100)", "EMA (20)", "EMA (50)"],
        default=["RSI", "MACD"]
    )

    # Compute selected indicators
    if "RSI" in indicators_selected:
        selected_data['RSI'] = ta.momentum.RSIIndicator(selected_data['Close']).rsi()
    if "MACD" in indicators_selected:
        selected_data['MACD'] = ta.trend.MACD(selected_data['Close']).macd()
    if "SMA (50)" in indicators_selected:
        selected_data['SMA (50)'] = selected_data['Close'].rolling(window=50).mean()
    if "SMA (100)" in indicators_selected:
        selected_data['SMA (100)'] = selected_data['Close'].rolling(window=100).mean()
    if "EMA (20)" in indicators_selected:
        selected_data['EMA (20)'] = selected_data['Close'].ewm(span=20, adjust=False).mean()
    if "EMA (50)" in indicators_selected:
        selected_data['EMA (50)'] = selected_data['Close'].ewm(span=50, adjust=False).mean()

    plot_cols = [col for col in indicators_selected if col in selected_data.columns]
    if plot_cols:
        st.line_chart(selected_data[plot_cols])
    else:
        st.warning("Please select at least one indicator to visualize.")

    with st.expander("Indicator Descriptions (Click to Expand)"):
        st.markdown("""
        - **RSI (Relative Strength Index)**:  
          Identifies overbought (>70) or oversold (<30) conditions.

        - **MACD (Moving Average Convergence Divergence)**:  
          Detects trend momentum based on two EMAs.

        - **SMA (Simple Moving Average)**:  
          Smooths out prices over a period (e.g., 50, 100 days).

        - **EMA (Exponential Moving Average)**:  
          Like SMA but reacts faster to recent prices.
        """)




# candle stick
with tab3:
    st.subheader("Candlestick Chart")

    # Let user choose one stock
    selected_ticker_candle = st.selectbox(
        "Select a stock to view candlestick chart",
        list(all_data.keys()),
        key="candle_tab"
    )

    # Fetch fresh OHLCV data for candlestick chart
    candle_data = yf.Ticker(selected_ticker_candle).history(start=start_date, end=end_date)

    if candle_data.empty:
        st.warning(f"No data available for {selected_ticker_candle}")
    else:
        candle_data.reset_index(inplace=True)

        st.markdown("""
        This candlestick chart shows daily price action with:

        - 🟩 **Green candles**: Closing price is higher than opening → bullish  
        - 🟥 **Red candles**: Closing price is lower than opening → bearish  
        - **Wicks**: Represent the intraday high and low  

        Use this chart to analyze price trends, market sentiment, and volatility.
        """)

        # Plot candlestick chart
        fig_candle = go.Figure(data=[go.Candlestick(
            x=candle_data['Date'],
            open=candle_data['Open'],
            high=candle_data['High'],
            low=candle_data['Low'],
            close=candle_data['Close'],
            increasing_line_color='green',
            decreasing_line_color='red'
        )])

        fig_candle.update_layout(
            title=f"{selected_ticker_candle} - Candlestick Chart",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig_candle, use_container_width=True)







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

    # Let user select a stock to download
    selected_ticker_download = st.selectbox(
        "Choose a stock to export",
        list(all_data.keys()),
        key="download_tab"
    )

    data_to_download = all_data[selected_ticker_download].copy()

    # Preview
    st.markdown("##### Preview of Data to be Downloaded")
    st.dataframe(data_to_download.head())

    # Download
    st.download_button(
        label="Download CSV",
        data=data_to_download.to_csv().encode("utf-8"),
        file_name=f"{selected_ticker_download}_data.csv",
        mime="text/csv"
    )


