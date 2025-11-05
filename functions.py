# ==========================================================
# functions.py — Indian Market (NSE/BSE + Indices) Support
# ==========================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import random
from fp.fp import FreeProxy
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.colors as pc


# -------------------------
# PROXY SETUP
# -------------------------
def get_proxy_dict(probability=0.1):
    """Return a proxy occasionally (5–10% of the time) to bypass Yahoo rate limits."""
    try:
        if random.random() < probability:
            proxy = FreeProxy(rand=True).get()
            return {"http": proxy, "https": proxy}
    except:
        pass
    return None


# -------------------------
# INDIAN INDEX SYMBOLS MAP
# -------------------------
INDIAN_INDICES = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "^CNXFIN",
    "NIFTYFIN": "^CNXFIN",
    "NIFTY IT": "^CNXIT",
    "NIFTYIT": "^CNXIT",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTYFMCG": "^CNXFMCG",
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTYAUTO": "^CNXAUTO",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTYMETAL": "^CNXMETAL",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTYPHARMA": "^CNXPHARMA",
    "NIFTY REALTY": "^CNXREALTY",
    "NIFTYREALTY": "^CNXREALTY",
    "NIFTY PSU BANK": "^CNXPSUBANK",
    "NIFTYPSUBANK": "^CNXPSUBANK",
    "NIFTY ENERGY": "^CNXENERGY",
    "NIFTYENERGY": "^CNXENERGY",
    "NIFTY MIDCAP 50": "^NSEMDCP50",
    "NIFTYMIDCAP50": "^NSEMDCP50",
    "NIFTY MIDCAP 100": "^NSEMDCP100",
    "NIFTYMIDCAP100": "^NSEMDCP100",
    "NIFTY SMALLCAP 50": "^NSESMLCP50",
    "NIFTYSMALLCAP50": "^NSESMLCP50",
    "NIFTY SMALLCAP 100": "^NSESMLCP100",
    "NIFTYSMALLCAP100": "^NSESMLCP100",
    "SENSEX": "^BSESN",
    "BSESENSEX": "^BSESN",
    "SENSEX NEXT 50": "^BSESN50",
    "INDIA VIX": "^INDIAVIX",
}

@st.cache_data(ttl=86400)  # cache for 1 day
def fetch_fno_list():
    """
    Fetches all NSE F&O (derivative) stocks from NSE India website.
    Returns a list of ticker symbols (with .NS suffix).
    """
    try:
        url = "https://archives.nseindia.com/content/fo/fo_underlyinglist.csv"
        df = pd.read_csv(url)
        symbols = sorted(df["SYMBOL"].unique())
        return [f"{s}.NS" for s in symbols]
    except Exception:
        # fallback: static snapshot (Aug 2025)
        fallback_symbols = [
            "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "LT.NS",
            "AXISBANK.NS", "ITC.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "BAJFINANCE.NS", "ADANIENT.NS",
            "MARUTI.NS", "HCLTECH.NS", "WIPRO.NS", "HDFCLIFE.NS", "ULTRACEMCO.NS", "SUNPHARMA.NS",
            "DRREDDY.NS", "NTPC.NS", "TITAN.NS", "POWERGRID.NS", "GRASIM.NS", "ONGC.NS",
            "TATAMOTORS.NS", "ADANIPORTS.NS", "BPCL.NS", "HINDUNILVR.NS", "BRITANNIA.NS",
            "COALINDIA.NS", "HEROMOTOCO.NS", "TECHM.NS", "BAJAJFINSV.NS", "CIPLA.NS", "NESTLEIND.NS",
            "INDUSINDBK.NS", "HINDALCO.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "ADANIGREEN.NS",
            "ADANIPOWER.NS", "DIVISLAB.NS", "PIDILITIND.NS", "SBILIFE.NS", "BAJAJ-AUTO.NS",
            "EICHERMOT.NS", "SHREECEM.NS", "UPL.NS", "DMART.NS"
        ]
        return fallback_symbols

# -------------------------
# FETCH FUNCTIONS
# -------------------------
@st.cache_data
def fetch_info(ticker: str):
    """Fetch general info for NSE/BSE stocks or Indian indices."""
    ticker = ticker.upper().strip()

    # Handle Indian indices
    if ticker in INDIAN_INDICES:
        ticker = INDIAN_INDICES[ticker]

    try:
        if not ticker.endswith((".NS", ".BO", "=X", "^")):
            # Try NSE first
            test_ticker = yf.Ticker(f"{ticker}.NS")
            info = test_ticker.info
            if info and "quoteType" in info:
                return info
            # Try BSE
            test_ticker = yf.Ticker(f"{ticker}.BO")
            info = test_ticker.info
            if info and "quoteType" in info:
                return info

        proxy = get_proxy_dict()
        yf.set_config(proxy=proxy)
        ticker_obj = yf.Ticker(ticker)
