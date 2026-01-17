import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import pytz
from datetime import datetime, time
import time as t_lib

# --- Configuration ---
INITIAL_CAPITAL = 1000000  # 10 Lakhs
MAX_ALLOCATION_PER_TRADE = 0.20  # Max 20% of capital per stock for diversification
TARGET_PROFIT = 0.02  # Sell at 2% profit
STOP_LOSS = 0.01      # Sell at 1% loss
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)
TIMEZONE = pytz.timezone('Asia/Kolkata')

# Watchlist (Top Liquid Stocks in NSE for Momentum)
WATCHLIST = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 
             'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'KOTAKBANK.NS', 'LT.NS']

# --- Helper Functions ---

def is_market_open():
    """Checks if current IST time is within NSE market hours."""
    now = datetime.now(TIMEZONE).time()
    # For educational testing, you might want to comment out the next line to test offline
    return MARKET_OPEN <= now <= MARKET_CLOSE

def get_live_data(tickers):
    """Fetches live data for watchlist."""
    try:
        data = yf.download(tickers, period="1d", interval="5m", group_by='ticker', progress=False)
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def analyze_market(data):
    """
    Momentum Strategy: Picks stocks with > 0.5% gain and positive trend.
    Returns a DataFrame of 'Buy' signals.
    """
    signals = []
    if data is None or data.empty:
        return []

    for ticker in WATCHLIST:
        try:
            # Handle Multi-index columns from yfinance
            stock_data = data[ticker]
            if stock_data.empty:
                continue
            
            latest = stock_data.iloc[-1]
            open_price = latest['Open']
            close_price = latest['Close']
            
            # Simple Momentum Condition: Price is up > 0.5% from candle open
            pct_change = (close_price - open_price) / open_price
            
            if pct_change > 0.005: # 0.5% momentum threshold
                signals.append({
                    'ticker': ticker,
                    'price': close_price,
                    'change': pct_change
                })
        except KeyError:
            continue
            
    return sorted(signals, key=lambda x: x['change'], reverse=True) # Maximize potential

# --- Session State Management (Virtual Account) ---

if 'balance' not in st.session_state:
    st.session_state.balance = INITIAL_CAPITAL
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {} # Format: {'TICKER': {'qty': 10, 'buy_price': 100}}
if 'trade_log' not in st.session_state:
    st.session_state.trade_log = []
if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False

# --- Trading Bot Logic ---

def execute_trade_cycle():
    status_placeholder = st.empty()
    
    if not is_market_open():
        status_placeholder.warning("Market is Closed (09:15 - 15:30 IST). Bot is sleeping.")
        return

    status_placeholder.info("Fetching market data...")
    data = get_live_data(WATCHLIST)
    
    # 1. Check existing positions (Sell Logic)
    portfolio = st.session_state.portfolio
    to_sell = []
    
    for ticker, pos in portfolio.items():
        try:
            current_price = data[ticker]['Close'].iloc[-1]
            buy_price = pos['buy_price']
            qty = pos['qty']
            pnl_pct = (current_price - buy_price) / buy_price
            
            # Sell Check: Target Met or Stop Loss Hit
            if pnl_pct >= TARGET_PROFIT or pnl_pct <= -STOP_LOSS:
                sell_val = qty * current_price
                st.session_state.balance += sell_val
                st.session_state.trade_log.append({
                    "Action": "SELL",
                    "Ticker": ticker,
                    "Price": round(current_price, 2),
                    "Qty": qty,
                    "PnL": round(sell_val - (qty * buy_price), 2),
                    "Time": datetime.now(TIMEZONE).strftime("%H:%M:%S")
                })
                to_sell.append(ticker)
        except Exception as e:
            continue
            
    for ticker in to_sell:
        del st.session_state.portfolio[ticker]

    # 2. Check for new opportunities (Buy Logic)
    # Only buy if we have cash and existing positions are < max exposure
    opportunities = analyze_market(data)
    
    for opp in opportunities:
        ticker = opp['ticker']
        price = opp['price']
        
        # Don't buy if already owned
        if ticker in st.session_state.portfolio:
            continue
            
        # Position Sizing: Max 20% of CURRENT capital per trade
        allocatable_cash = st.session_state.balance * MAX_ALLOCATION_PER_TRADE
        
        if allocatable_cash > price:
            qty = int(allocatable_cash // price)
            cost = qty * price
            
            # Execute Buy
            st.session_state.balance -= cost
            st.session_state.portfolio[ticker] = {'qty': qty, 'buy_price': price}
            st.session_state.trade_log.append({
                "Action": "BUY",
                "Ticker": ticker,
                "Price": round(price, 2),
                "Qty": qty,
                "PnL": 0,
                "Time": datetime.now(TIMEZONE).strftime("%H:%M:%S")
            })

    status_placeholder.success(f"Cycle completed at {datetime.now(TIMEZONE).strftime('%H:%M:%S')}")

# --- UI Layout ---

st.set_page_config(layout="wide", page_title="AlgoTrader Edu")
st.title("⚡ Educational Intraday Bot (NSE/BSE)")

# Sidebar Controls
with st.sidebar:
    st.header("Bot Controls")
    if st.button("Start/Stop Bot"):
        st.session_state.bot_active = not st.session_state.bot_active
    
    st.metric("Bot Status", "Running" if st.session_state.bot_active else "Stopped")
    st.warning("⚠️ Data delayed by ~15 mins (Yahoo Finance)")

# Dashboard Stats
col1, col2, col3 = st.columns(3)
current_value = st.session_state.balance
# Add unrealized PnL from held stocks roughly
portfolio_val = 0
for t, p in st.session_state.portfolio.items():
    portfolio_val += p['qty'] * p['buy_price'] # Using buy price for speed approximation

total_equity = current_value + portfolio_val

col1.metric("Total Portfolio Value", f"₹{total_equity:,.2f}")
col2.metric("Cash Balance", f"₹{st.session_state.balance:,.2f}")
col3.metric("Open Positions", len(st.session_state.portfolio))

# Main Charts & Tables
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Live Portfolio Performance")
    if st.session_state.portfolio:
        # Create a DataFrame for active holdings
        holdings_data = []
        for t, p in st.session_state.portfolio.items():
            holdings_data.append({"Ticker": t, "Qty": p['qty'], "Buy Price": p['buy_price']})
        st.dataframe(pd.DataFrame(holdings_data), use_container_width=True)
    else:
        st.info("No open positions. Waiting for signals...")

    st.subheader("Trade Log")
    if st.session_state.trade_log:
        df_log = pd.DataFrame(st.session_state.trade_log)
        st.dataframe(df_log.iloc[::-1], use_container_width=True) # Show newest first

with c2:
    st.subheader("Market Trend (Nifty)")
    # Simple chart of Nifty 50
    nifty = yf.download("^NSEI", period="1d", interval="5m", progress=False)
    if not nifty.empty:
        fig = go.Figure(data=[go.Candlestick(x=nifty.index,
                        open=nifty['Open'], high=nifty['High'],
                        low=nifty['Low'], close=nifty['Close'])])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

# Auto-Run Logic (Simulation Loop)
if st.session_state.bot_active:
    execute_trade_cycle()
    t_lib.sleep(5) # Wait 5 seconds before rerun
    st.rerun()
