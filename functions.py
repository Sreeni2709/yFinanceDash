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
