# ---- IMPORTS ----
import streamlit as st
import datetime
from zoneinfo import ZoneInfo
from streamlit_javascript import st_javascript
from functions import *
from contact import contact_form

# ---- CONTACT FORM ----
@st.dialog("Contact Me")
def show_contact_form():
    contact_form()

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="Indian Market Financials",
    page_icon=":material/currency_rupee:",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"Get help": "https://github.com/LMAPcoder"}
)

# ---- LOGO ----
st.html("""
  <style>
    [alt=Logo] {
      height: 3rem;
      width: auto;
      padding-left: 1rem;
    }
  </style>
""")

# ---- TIME ZONE ----
if 'timezone' not in st.session_state:
    timezone = st_javascript("""await (async () => {
                    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                    return userTimezone
                    })().then(returnValue => returnValue)""")
    if isinstance(timezone, int):
        st.stop()
    st.session_state['timezone'] = ZoneInfo(timezone)

# ---- SESSION STATE ----
default_state = {
    'current_time_financials_page': datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0, tzinfo=None),
    'tickers': "RELIANCE.NS",
    'financial_period': "Annual"
}
for k, v in default_state.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---- HELPER: DETECT AND FIX INDIAN TICKERS ----
def detect_market_type(ticker: str):
    """
    Detect and return proper Indian market ticker.
    Adds .NS (NSE) or .BO (BSE) automatically if missing.
    Also detects Indian indices (NIFTY, BANKNIFTY, etc.).
    """
    ticker = ticker.upper().strip()

    # ---- Indian Indices Map ----
    indian_indices = {
        "NIFTY": "^NSEI",
        "NIFTY50": "^NSEI",
        "NIFTY NEXT 50": "^NSMIDCP",
        "NIFTYNEXT50": "^NSMIDCP",
        "NIFTY MIDCAP 50": "^NSEMDCP50",
        "NIFTYMIDCAP50": "^NSEMDCP50",
        "NIFTY MIDCAP 100": "^NSEMDCP100",
        "NIFTYMIDCAP100": "^NSEMDCP100",
        "NIFTY SMALLCAP 50": "^NSESMLCP50",
        "NIFTYSMALLCAP50": "^NSESMLCP50",
        "NIFTY SMALLCAP 100": "^NSESMLCP100",
        "NIFTYSMALLCAP100": "^NSESMLCP100",
        "BANKNIFTY": "^NSEBANK",
        "FINNIFTY": "^CNXFIN",
        "NIFTYFIN": "^CNXFIN",
        "NIFTY FMCG": "^CNXFMCG",
        "NIFTYFMCG": "^CNXFMCG",
        "NIFTY IT": "^CNXIT",
        "NIFTYIT": "^CNXIT",
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
        "SENSEX": "^BSESN",
        "BSESENSEX": "^BSESN",
        "SENSEX NEXT 50": "^BSESN50",
        "INDIA VIX": "^INDIAVIX"
    }

    # Check if it’s an index
    if ticker in indian_indices:
        return indian_indices[ticker]

    # Handle stocks with or without suffix
    if ticker.endswith(".NS") or ticker.endswith(".BO"):
        return ticker

    # Try NSE first
    try:
        info = fetch_info(f"{ticker}.NS")
        if not isinstance(info, Exception):
            return f"{ticker}.NS"
    except:
        pass

    # Try BSE next
    try:
        info = fetch_info(f"{ticker}.BO")
        if not isinstance(info, Exception):
            return f"{ticker}.BO"
    except:
        pass

    return None

# ---- SIDEBAR ----
with st.sidebar:
    st.header("🇮🇳 Indian Stock Market")

    TICKERS = st.text_input(
        label="Enter stocks or indices (comma-separated):",
        value=st.session_state['tickers'],
        key='tickers'
    )

    raw_tickers = [t.strip().upper() for t in TICKERS.split(",") if t.strip() != ""]
    raw_tickers = remove_duplicates(raw_tickers)

    # Apply detection logic
    detected_tickers = []
    for t in raw_tickers:
        fixed = detect_market_type(t)
        if fixed:
            detected_tickers.append(fixed)
        else:
            st.error(f"❌ Could not identify Indian market ticker for '{t}'")

    if len(detected_tickers) > 10:
        st.warning("Only first 10 tickers are processed")
        detected_tickers = detected_tickers[:10]

    TICKERS = detected_tickers

    TIME_PERIOD = st.radio(
        label="Time Period:",
        options=["Annual", "Quarterly"],
        key="financial_period"
    )

    if st.button("🔄 Refresh Data"):
        st.session_state['current_time_financials_page'] = datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0, tzinfo=None)
        fetch_info.clear()
        fetch_balance.clear()
        fetch_income.clear()
        fetch_cash.clear()
        st.success("✅ Data refreshed successfully!")

    st.write("Last update:", st.session_state['current_time_financials_page'])
    st.markdown("---")

    st.markdown("Made with ❤️ by Leonardo")
    if st.button("✉️ Contact Me", key="contact"):
        show_contact_form()

    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<p style='text-align: right;'>Powered by:</p>", unsafe_allow_html=True)
    with col2:
        st.image("imgs/logo_yahoo_lightpurple.svg", width=100)

# ---- MAIN PAGE ----
st.title("📈 Indian Market Financial Dashboard")

if len(TICKERS) == 0:
    st.error("Please enter at least one valid NSE/BSE stock or Indian index.")
    st.stop()

if len(TICKERS) == 1:
    TICKER = TICKERS[0]
    info = fetch_info(TICKER)

    if isinstance(info, Exception):
        st.error(info)
        fetch_info.clear(TICKER)
        st.stop()

    NAME = info.get('shortName', TICKER)
    CURRENCY = info.get('financialCurrency', "INR")

    st.subheader(f"{NAME} ({TICKER}) — {CURRENCY}")

    bs = fetch_balance(TICKER, tp=TIME_PERIOD)
    ist = fetch_income(TICKER, tp=TIME_PERIOD)
    cf = fetch_cash(TICKER, tp=TIME_PERIOD)

    # ---- CAPITAL STRUCTURE ----
    st.header("🏗️ Capital Structure")
    if isinstance(bs, Exception):
        st.error(bs)
        fetch_balance.clear(TICKER, tp=TIME_PERIOD)
        st.stop()
    st.plotly_chart(plot_capital(bs, ticker=TICKER, currency=CURRENCY), use_container_width=True)

    # ---- BALANCE SHEET ----
    st.header("📘 Balance Sheet")
    st.plotly_chart(plot_balance(bs[bs.columns[::-1]], ticker=TICKER, currency=CURRENCY), use_container_width=True)
    with st.expander("Show components"):
        tab1, tab2, tab3 = st.tabs(["Assets", "Liabilities", "Equity"])
        with tab1:
            st.plotly_chart(plot_assets(bs, ticker=TICKER, currency=CURRENCY), use_container_width=True)
        with
