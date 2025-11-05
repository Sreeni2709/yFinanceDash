# ---- IMPORTS ----
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import yfinance as yf
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.colors as pc

# ---- STREAMLIT CACHING HELPERS ----
@st.cache_data(ttl=3600)
def fetch_info(ticker: str):
    """Fetch stock or index info from Yahoo Finance"""
    try:
        ticker = yf.Ticker(ticker)
        return ticker.info
    except Exception as e:
        return e


@st.cache_data(ttl=3600)
def fetch_history(ticker: str, period="6mo", interval="1d", start=None):
    """Fetch historical price data"""
    try:
        t = yf.Ticker(ticker)
        if start:
            return t.history(start=start, interval=interval)
        else:
            return t.history(period=period, interval=interval)
    except Exception as e:
        return e


@st.cache_data(ttl=3600)
def fetch_balance(ticker: str, tp="Annual"):
    """Fetch balance sheet"""
    try:
        t = yf.Ticker(ticker)
        if tp == "Annual":
            return t.balance_sheet
        else:
            return t.quarterly_balance_sheet
    except Exception as e:
        return e


@st.cache_data(ttl=3600)
def fetch_income(ticker: str, tp="Annual"):
    """Fetch income statement"""
    try:
        t = yf.Ticker(ticker)
        if tp == "Annual":
            return t.income_stmt
        else:
            return t.quarterly_income_stmt
    except Exception as e:
        return e


@st.cache_data(ttl=3600)
def fetch_cash(ticker: str, tp="Annual"):
    """Fetch cash flow"""
    try:
        t = yf.Ticker(ticker)
        if tp == "Annual":
            return t.cashflow
        else:
            return t.quarterly_cashflow
    except Exception as e:
        return e


@st.cache_data(ttl=3600)
def fetch_table(url: str):
    """Fetch table from Yahoo Finance HTML page"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        df_list = pd.read_html(response.content)
        return df_list[0]
    except Exception as e:
        return e


def remove_duplicates(lst):
    """Remove duplicates while preserving order"""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ---- INDIAN INDICES ----
INDIAN_INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "^CNXFIN",
    "NIFTY NEXT 50": "^NSMIDCP",
    "NIFTY MIDCAP 50": "^NSEMDCP50",
    "NIFTY MIDCAP 100": "^NSEMDCP100",
    "NIFTY SMALLCAP 50": "^NSESMLCP50",
    "NIFTY SMALLCAP 100": "^NSESMLCP100",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY IT": "^CNXIT",
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY REALTY": "^CNXREALTY",
    "NIFTY ENERGY": "^CNXENERGY",
    "NIFTY PSU BANK": "^CNXPSUBANK",
    "INDIA VIX": "^INDIAVIX",
}

# ---- FNO STOCKS ----
@st.cache_data(ttl=86400)
def fetch_fno_list():
    """Fetch NSE F&O stock list from NSE website"""
    try:
        url = "https://archives.nseindia.com/content/fo/fo_underlyings.csv"
        df = pd.read_csv(url)
        df = df.dropna(subset=["SYMBOL"])
        symbols = [f"{x}.NS" for x in df["SYMBOL"].tolist()]
        return symbols
    except Exception:
        # Fallback static list (Top 20 F&O)
        return [
            "RELIANCE.NS", "TCS.NS", "INFY.NS", "ICICIBANK.NS", "HDFCBANK.NS",
            "SBIN.NS", "AXISBANK.NS", "LT.NS", "ITC.NS", "BHARTIARTL.NS",
            "MARUTI.NS", "KOTAKBANK.NS", "HCLTECH.NS", "SUNPHARMA.NS",
            "ADANIENT.NS", "ADANIPORTS.NS", "TITAN.NS", "ONGC.NS", "WIPRO.NS", "ULTRACEMCO.NS"
        ]


# ---- VISUALIZATION FUNCTIONS ----
def plot_balance(df, ticker="", currency="INR"):
    df.columns = pd.to_datetime(df.columns).strftime('%Y')
    fig = go.Figure()
    if "Total Assets" in df.index:
        fig.add_trace(go.Bar(
            x=df.columns, y=df.loc["Total Assets"], name="Total Assets", marker_color="green"
        ))
    if "Total Liabilities Net Minority Interest" in df.index:
        fig.add_trace(go.Bar(
            x=df.columns, y=df.loc["Total Liabilities Net Minority Interest"],
            name="Total Liabilities", marker_color="red"
        ))
    if "Stockholders Equity" in df.index:
        fig.add_trace(go.Bar(
            x=df.columns, y=df.loc["Stockholders Equity"], name="Equity", marker_color="blue"
        ))
    fig.update_layout(
        barmode="group",
        title=f"Balance Sheet — {ticker}",
        yaxis_title=f"Amount ({currency})",
        xaxis_title="Year",
    )
    return fig


def plot_income(df, ticker="", currency="INR"):
    df.columns = pd.to_datetime(df.columns).strftime('%Y')
    fig = go.Figure()

    if "Total Revenue" in df.index:
        fig.add_trace(go.Bar(
            x=df.columns,
            y=df.loc["Total Revenue"],
            name="Total Revenue",
            marker_color="green"
        ))

    if "Net Income Common Stockholders" in df.index:
        fig.add_trace(go.Bar(
            x=df.columns,
            y=df.loc["Net Income Common Stockholders"],
            name="Net Income",
            marker_color="orange"
        ))

    fig.update_layout(
        barmode="group",
        title=f"Income Statement — {ticker}",
        yaxis_title=f"Amount ({currency})",
        xaxis_title="Year",
    )

    return fig

