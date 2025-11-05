# ==========================================================
# functions.py — Indian Market (NSE/BSE + Indices) Support
# ==========================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.colors as pc


# ==========================================================
# INDIAN INDEX SYMBOLS MAP
# ==========================================================
INDIAN_INDICES = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "^CNXFIN",
    "NIFTYFIN": "^CNXFIN",
    "NIFTY IT": "^CNXIT",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY REALTY": "^CNXREALTY",
    "NIFTY PSU BANK": "^CNXPSUBANK",
    "NIFTY ENERGY": "^CNXENERGY",
    "NIFTY MIDCAP 50": "^NSEMDCP50",
    "NIFTY MIDCAP 100": "^NSEMDCP100",
    "NIFTY SMALLCAP 50": "^NSESMLCP50",
    "NIFTY SMALLCAP 100": "^NSESMLCP100",
    "SENSEX": "^BSESN",
    "BSESENSEX": "^BSESN",
    "INDIA VIX": "^INDIAVIX",
}


# ==========================================================
# FETCH F&O LIST
# ==========================================================
@st.cache_data(ttl=86400)
def fetch_fno_list():
    """Fetch NSE F&O stock list from NSE official site."""
    try:
        url = "https://archives.nseindia.com/content/fo/fo_underlyinglist.csv"
        df = pd.read_csv(url)
        symbols = sorted(df["SYMBOL"].unique())
        return [f"{s}.NS" for s in symbols]
    except Exception:
        # fallback list
        return [
            "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
            "SBIN.NS", "LT.NS", "AXISBANK.NS", "ITC.NS", "BHARTIARTL.NS",
            "MARUTI.NS", "KOTAKBANK.NS", "BAJFINANCE.NS", "HCLTECH.NS",
            "SUNPHARMA.NS", "TITAN.NS", "ONGC.NS", "WIPRO.NS", "ULTRACEMCO.NS",
        ]


# ==========================================================
# CORE FETCHING FUNCTIONS
# ==========================================================
@st.cache_data(ttl=3600)
def fetch_info(ticker: str):
    """Fetch stock or index info from Yahoo Finance."""
    ticker = ticker.upper().strip()

    if ticker in INDIAN_INDICES:
        ticker = INDIAN_INDICES[ticker]

    try:
        if not ticker.endswith((".NS", ".BO", "=X", "^")):
            for suffix in [".NS", ".BO"]:
                t = yf.Ticker(ticker + suffix)
                info = t.info
                if info and "quoteType" in info:
                    return info

        ticker_obj = yf.Ticker(ticker)
        return ticker_obj.info
    except Exception as e:
        return e


@st.cache_data(ttl=3600)
def fetch_history(ticker: str, period="6mo", interval="1d"):
    """Fetch historical price data."""
    try:
        ticker_obj = yf.Ticker(ticker)
        return ticker_obj.history(period=period, interval=interval)
    except Exception as e:
        return e


@st.cache_data(ttl=3600)
def fetch_balance(ticker: str, tp="Annual"):
    """Fetch balance sheet data."""
    try:
        ticker_obj = yf.Ticker(ticker)
        if tp == "Annual":
            return ticker_obj.balance_sheet
        return ticker_obj.quarterly_balance_sheet
    except Exception as e:
        return e


@st.cache_data(ttl=3600)
def fetch_income(ticker: str, tp="Annual"):
    """Fetch income statement data."""
    try:
        ticker_obj = yf.Ticker(ticker)
        if tp == "Annual":
            return ticker_obj.income_stmt
        return ticker_obj.quarterly_income_stmt
    except Exception as e:
        return e


@st.cache_data(ttl=3600)
def fetch_cash(ticker: str, tp="Annual"):
    """Fetch cash flow data."""
    try:
        ticker_obj = yf.Ticker(ticker)
        if tp == "Annual":
            return ticker_obj.cashflow
        return ticker_obj.quarterly_cashflow
    except Exception as e:
        return e


@st.cache_data(ttl=3600)
def fetch_table(url: str):
    """Fetch Yahoo Finance tables."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        df_list = pd.read_html(response.content)
        return df_list[0]
    except Exception as e:
        return e


def remove_duplicates(lst):
    """Remove duplicates while preserving order."""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ==========================================================
# VISUALIZATION HELPERS
# ==========================================================
def plot_balance(df, ticker="", currency="INR"):
    df.columns = pd.to_datetime(df.columns).strftime("%Y")
    fig = go.Figure()
    if "Total Assets" in df.index:
        fig.add_trace(go.Bar(x=df.columns, y=df.loc["Total Assets"], name="Total Assets"))
    if "Total Liabilities Net Minority Interest" in df.index:
        fig.add_trace(go.Bar(x=df.columns, y=df.loc["Total Liabilities Net Minority Interest"], name="Liabilities"))
    if "Stockholders Equity" in df.index:
        fig.add_trace(go.Bar(x=df.columns, y=df.loc["Stockholders Equity"], name="Equity"))
    fig.update_layout(
        barmode="group",
        title=f"Balance Sheet — {ticker}",
        yaxis_title=f"Amount ({currency})",
    )
    return fig


def plot_income(df, ticker="", currency="INR"):
    df.columns = pd.to_datetime(df.columns).strftime("%Y")
    fig = go.Figure()
    if "Total Revenue" in df.index:
        fig.add_trace(go.Bar(x=df.columns, y=df.loc["Total Revenue"], name="Revenue"))
    if "Net Income Common Stockholders" in df.index:
        fig.add_trace(go.Bar(x=df.columns, y=df.loc["Net Income Common Stockholders"], name="Net Income"))
    fig.update_layout(
        barmode="group",
        title=f"Income Statement — {ticker}",
        yaxis_title=f"Amount ({currency})",
    )
    return fig


def plot_cash(df, ticker="", currency="INR"):
    df.columns = pd.to_datetime(df.columns).strftime("%Y")
    fig = go.Figure()
    for flow in ["Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow"]:
        if flow in df.index:
            fig.add_trace(go.Bar(x=df.columns, y=df.loc[flow], name=flow))
    fig.update_layout(
        barmode="group",
        title=f"Cash Flow — {ticker}",
        yaxis_title=f"Amount ({currency})",
    )
    return fig


def plot_capital(df, ticker="", currency="INR"):
    fig = go.Figure()
    if "Total Debt" in df.index and "Stockholders Equity" in df.index:
        fig.add_trace(go.Bar(x=df.columns, y=df.loc["Total Debt"], name="Total Debt"))
        fig.add_trace(go.Bar(x=df.columns, y=df.loc["Stockholders Equity"], name="Equity"))
    fig.update_layout(
        barmode="stack",
        title=f"Capital Structure — {ticker}",
        yaxis_title=f"Amount ({currency})",
    )
    return fig
