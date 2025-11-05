# ==============================================================
# views/Page_price.py — Indian Market Dashboard (Indices + F&O)
# ==============================================================

from functions import *
from contact import contact_form
from streamlit_javascript import st_javascript
from zoneinfo import ZoneInfo
import datetime
import pandas as pd

# ---------------- UI: Contact dialog ----------------
@st.dialog("Contact Me")
def show_contact_form():
    contact_form()

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Indian Stock Market",
    page_icon=":material/currency_rupee:",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"Get help": "https://github.com/LMAPcoder"}
)

# ---------------- Small logo style ----------------
st.html("""
  <style>
    [alt=Logo] {
      height: 3rem;
      width: auto;
      padding-left: 1rem;
    }
  </style>
""")

# ---------------- Timezone ----------------
if "timezone" not in st.session_state:
    timezone = st_javascript("""await (async () => {
                    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                    return userTimezone
                    })().then(returnValue => returnValue)""")
    if isinstance(timezone, int):
        st.stop()
    st.session_state["timezone"] = ZoneInfo(timezone)

# ---------------- Session state ----------------
if "tickers" not in st.session_state:
    st.session_state["tickers"] = "RELIANCE.NS"
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False
if "current_time_price_page" not in st.session_state:
    st.session_state["current_time_price_page"] = datetime.datetime.now(
        st.session_state["timezone"]
    ).replace(microsecond=0, tzinfo=None)

# ======================================================
# SIDEBAR — SELECTION
# ======================================================
with st.sidebar:
    st.header("🇮🇳 Indian Market Dashboard")

    # --- Dark mode ---
    TOGGLE_THEME = st.toggle(
        label="Dark mode :material/dark_mode:",
        key="toggle_theme",
        help="Switch between light/dark mode",
    )
    if TOGGLE_THEME != st.session_state["dark_mode"]:
        st._config.set_option("theme.base", "dark" if TOGGLE_THEME else "light")
        st.session_state["dark_mode"] = TOGGLE_THEME
        st.rerun()

    # --- Choose data type ---
    market_type = st.radio(
        "Select Market Segment:",
        ["NSE/BSE Stocks", "Indices", "F&O Stocks"],
        index=0,
        horizontal=True,
    )

    # ---- Stocks ----
    if market_type == "NSE/BSE Stocks":
        TICKERS = st.text_input(
            label="Enter tickers:",
            value="RELIANCE.NS, HDFCBANK.NS",
            key="tickers",
        )
        TICKERS = [t.strip().upper() for t in TICKERS.split(",") if t.strip()]

    # ---- Indices ----
    elif market_type == "Indices":
        INDEX_NAMES = sorted(INDIAN_INDICES_FULL.keys())
        SELECTED = st.multiselect(
            "Select Indices (multiple allowed):",
            options=INDEX_NAMES,
            default=["NIFTY 50", "SENSEX"],
        )
        TICKERS = [INDIAN_INDICES_FULL[i] for i in SELECTED]

    # ---- F&O Stocks ----
    elif market_type == "F&O Stocks":
        fno_list = fetch_fno_list()
        SELECTED = st.multiselect(
            "Select F&O Stocks:",
            options=fno_list,
            default=["RELIANCE.NS", "TCS.NS", "INFY.NS"],
        )
        TICKERS = SELECTED

    # --- Validation ---
    if len(TICKERS) > 10:
        st.warning("⚠️ Only first 10 tickers are processed.")
        TICKERS = TICKERS[:10]

    # --- Period and interval ---
    period_list = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    PERIOD = st.selectbox("Period", options=period_list, index=3)

    interval_list = [
        "1m", "2m", "5m", "15m", "30m", "60m", "90m",
        "1h", "1d", "5d", "1wk", "1mo", "3mo"
    ]
    if PERIOD in interval_list:
        idx = interval_list.index(PERIOD)
        interval_list = interval_list[:idx]
    INTERVAL = st.selectbox("Interval", options=interval_list, index=len(interval_list) - 4)

    # --- Indicators for single stock view ---
    if len(TICKERS) == 1 and market_type != "Indices":
        TOGGLE_VOL = st.toggle("Show Volume", value=True)
        indicator_list = [
            "SMA_20", "SMA_50", "SMA_200", "SMA_X",
            "EMA_20", "EMA_50", "EMA_200", "EMA_X",
            "ATR", "MACD", "RSI",
        ]
        INDICATORS = st.multiselect("Technical indicators:", options=indicator_list)
        if "SMA_X" in INDICATORS or "EMA_X" in INDICATORS:
            TIME_SPAN = st.slider("Select custom period:", 10, 200, 30)
            INDICATORS = [
                i.replace("X", str(TIME_SPAN)) if "_X" in i else i for i in INDICATORS
            ]
    else:
        TOGGLE_VOL = False
        INDICATORS = []

    # --- Refresh ---
    if st.button("🔄 Refresh Data"):
        fetch_info.clear()
        fetch_history.clear()
        fetch_table.clear()
        st.session_state["current_time_price_page"] = datetime.datetime.now(
            st.session_state["timezone"]
        ).replace(microsecond=0, tzinfo=None)
        st.success("Data refreshed!")

    st.write("Last update:", st.session_state["current_time_price_page"])
    st.markdown("---")
    st.markdown("Made with ❤️ by Leonardo")
    if st.button("✉️ Contact Me"):
        show_contact_form()
    st.image("imgs/logo_yahoo_lightpurple.svg", width=120)

# ======================================================
# MAIN PAGE
# ======================================================
st.title("📊 Indian Stock Market Dashboard")

if len(TICKERS) == 0:
    st.warning("Please select or enter at least one ticker.")
    st.stop()

# ------------------------------------------------------
# INDEX DASHBOARD MODE
# ------------------------------------------------------
if market_type == "Indices":
    st.subheader("📈 Indian Indices Overview")

    cols = st.columns(3)
    for i, ticker in enumerate(TICKERS):
        info = fetch_info(ticker)
        if isinstance(info, Exception):
            continue
        # Reverse lookup name
        try:
            name = list(INDIAN_INDICES_FULL.keys())[
                list(INDIAN_INDICES_FULL.values()).index(ticker)
            ]
        except Exception:
            name = ticker
        price = info.get("regularMarketPrice", info.get("previousClose", 0))
        change = info.get("regularMarketChangePercent", 0)
        cols[i % 3].metric(
            label=f"{name} ({ticker})",
            value=f"{price:.2f}" if price else "—",
            delta=f"{change:+.2f}%" if change else None,
        )

    # Optional: line charts for index trend
    st.markdown("### 🪜 Index Trend")
    for ticker in TICKERS:
        hist = fetch_history(ticker, period="6mo", interval="1d")
        if isinstance(hist, Exception):
            st.error(f"Error fetching data for {ticker}")
            continue
        fig = plot_candles_stick(hist, title=ticker)
        st.plotly_chart(fig, use_container_width=True)
    st.stop()

# ------------------------------------------------------
# F&O or STOCKS DASHBOARD MODE
# ------------------------------------------------------
if len(TICKERS) == 1:
    TICKER = TICKERS[0]
    info = fetch_info(TICKER)
    if isinstance(info, Exception):
        st.error(info)
        st.stop()

    NAME = info.get("shortName", TICKER)
    st.header(f"Security: {NAME} ({TICKER})")

    # Info block
    with st.expander("Company / Instrument Info"):
        df_info = info_table(info).reset_index().rename(columns={"index": "Feature", 0: "Value"})
        st.dataframe(df_info, hide_index=True)

    # Metrics
    PRICE = info.get("regularMarketPrice", info.get("previousClose", 0))
    CHANGE = info.get("regularMarketChange", 0)
    CHGP = info.get("regularMarketChangePercent", 0)
    CURRENCY = info.get("currency", "INR")
    st.metric("Current Price", f"{PRICE:.2f} {CURRENCY}", f"{CHANGE:+.2f} ({CHGP:+.2f}%)")

    # History
    hist = fetch_history(TICKER, period=PERIOD, interval=INTERVAL)
    if isinstance(hist, Exception):
        st.error(hist)
        st.stop()
    df = hist.copy()

    # Technical indicators
    if TOGGLE_VOL:
        df["ΔVolume%"] = df["Volume"].pct_change() * 100
    for IND in INDICATORS:
        if "SMA" in IND:
            window = int(IND.split("_")[1])
            df[IND] = df["Close"].rolling(window, min_periods=1).mean()
        if "EMA" in IND:
            window = int(IND.split("_")[1])
            df[IND] = df["Close"].ewm(span=window, adjust=False, min_periods=1).mean()
        if IND == "RSI":
            delta = df["Close"].pct_change() * 100
            gain = delta.where(delta > 0, 0).rolling(14, min_periods=1).mean()
            loss = -delta.where(delta < 0, 0).rolling(14, min_periods=1).mean()
            rs = gain / loss.replace(0, pd.NA)
            df["RSI"] = 100 - (100 / (1 + rs))
        if IND == "ATR":
            prev_close = df["Close"].shift(1)
            df["TR"] = pd.concat(
                [(df["High"] - df["Low"]).abs(),
                 (df["High"] - prev_close).abs(),
                 (df["Low"] - prev_close).abs()], axis=1
            ).max(axis=1)
            df["ATR"] = df["TR"].rolling(14, min_periods=1).mean()
        if IND == "MACD":
            ema_short = df["Close"].ewm(span=12, adjust=False, min_periods=1).mean()
            ema_long = df["Close"].ewm(span=26, adjust=False, min_periods=1).mean()
            df["MACD"] = ema_short - ema_long
            df["Signal"] = df["MACD"].ewm(span=9, adjust=False, min_periods=1).mean()
            df["MACD_Hist"] = df["MACD"] - df["Signal"]

    # Plot candlestick
    fig = plot_candles_stick_bar(df, title=f"{NAME} ({TICKER})", currency=CURRENCY)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Show Data Table"):
        st.dataframe(df.reset_index(), hide_index=False)

# ------------------------------------------------------
# MULTIPLE STOCKS OR F&O TICKERS
# ------------------------------------------------------
else:
    st.header("Comparative View")

    dfs_hist, dfs_info = [], []
    for T in TICKERS:
        info = fetch_info(T)
        if isinstance(info, Exception):
            continue
        df_i = info_table(info).rename(columns={0: T}).reset_index().rename(columns={"index": "Feature"})
        dfs_info.append(df_i.set_index("Feature"))
        hist = fetch_history(T, period=PERIOD, interval=INTERVAL)
        if isinstance(hist, Exception):
            continue
