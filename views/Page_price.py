# views/Page_price.py  — Indian market only (NSE/BSE + indices)

from functions import *
from contact import contact_form
from streamlit_javascript import st_javascript
from zoneinfo import ZoneInfo

# ---------------- UI: Contact dialog ----------------
@st.dialog("Contact Me")
def show_contact_form():
    contact_form()

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Indian Stocks",
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
if 'timezone' not in st.session_state:
    timezone = st_javascript("""await (async () => {
                    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                    return userTimezone
                    })().then(returnValue => returnValue)""")
    if isinstance(timezone, int):
        st.stop()
    st.session_state['timezone'] = ZoneInfo(timezone)

# ---------------- Session state ----------------
all_my_widget_keys_to_keep = {
    'current_time_price_page': datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0, tzinfo=None),
    'tickers': "RELIANCE.NS",             # default to Indian market
    'dark_mode': False,
    'toggle_theme': False,
    'financial_period': "Annual"
}
for key, val in all_my_widget_keys_to_keep.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------------- Sidebar ----------------
with st.sidebar:
    TOGGLE_THEME = st.toggle(
        label="Dark mode :material/dark_mode:",
        key="toggle_theme",
        help="Switch to dark theme"
    )
    if TOGGLE_THEME != st.session_state['dark_mode']:
        st._config.set_option('theme.base', "dark" if TOGGLE_THEME else "light")
        st.session_state['dark_mode'] = TOGGLE_THEME
        st.rerun()

    # India-focused sample portfolios
    PORTFOLIOS = {
        "Top 5 NSE (Large)": "RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS, ICICIBANK.NS",
        "IT Leaders": "TCS.NS, INFY.NS, WIPRO.NS, HCLTECH.NS, LTIM.NS",
        "Banks": "HDFCBANK.NS, ICICIBANK.NS, SBIN.NS, KOTAKBANK.NS, AXISBANK.NS",
        "NSE Indices": "^NSEI, ^NSEBANK, ^CNXIT, ^CNXFMCG, ^INDIAVIX",
        "BSE Indices": "^BSESN",
    }

    PORTFOLIO = st.selectbox(
        label="Portfolios",
        options=[None] + list(PORTFOLIOS.keys()),
        index=0,
        help="Choose a predefined Indian portfolio or leave None to customize"
    )
    if PORTFOLIO is not None:
        st.session_state["tickers"] = PORTFOLIOS[PORTFOLIO]

    TICKERS = st.text_input(
        label="Securities (comma-separated):",
        key='tickers'
    )
    st.write("eg.: RELIANCE, TCS, HDFCBANK or ^NSEI, ^BSESN (max 10)")

    # Clean and de-dup
    TICKERS = [item.strip().upper() for item in TICKERS.split(",") if item.strip() != ""]
    TICKERS = remove_duplicates(TICKERS)

    if len(TICKERS) > 10:
        st.error("Only first 10 tickers are shown")
        TICKERS = TICKERS[:10]

    # Validate via fetch_info (functions.py auto-detects .NS/.BO and indices)
    _tickers = []
    for T in TICKERS:
        info = fetch_info(T)
        if isinstance(info, Exception) or not isinstance(info, dict) or len(info) == 0:
            st.error(f"Failed to load info for '{T}'")
            fetch_info.clear(T)
        else:
            qtype = info.get('quoteType', "")
            if qtype not in ["EQUITY", "ETF", "INDEX"]:
                st.error(f"{T} has an invalid quoteType ({qtype})")
            else:
                _tickers.append(T)
    TICKERS = _tickers

    # Period & Interval (yfinance)
    period_list   = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    PERIOD = st.selectbox("Period", period_list, index=3)

    interval_list = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
    # Ensure valid combos (short intervals not valid for very long periods)
    if PERIOD in interval_list:
        idx = interval_list.index(PERIOD)
        interval_list = interval_list[:idx]
    INTERVAL = st.selectbox("Interval", interval_list, index=interval_list.index("1d"))

    # Single-ticker extra options
    if len(TICKERS) == 1:
        TOGGLE_VOL = st.toggle(label="Volume", value=True)
        indicator_list = ['SMA_20', 'SMA_50', 'SMA_200', 'SMA_X', 'EMA_20', 'EMA_50', 'EMA_200', 'EMA_X', 'ATR', 'MACD', 'RSI']
        INDICATORS = st.multiselect("Technical indicators:", options=indicator_list)
        if 'SMA_X' in INDICATORS or 'EMA_X' in INDICATORS:
            TIME_SPAN = st.slider("Select time span:", min_value=10, max_value=200, value=30)
            INDICATORS = [i.replace("X", str(TIME_SPAN)) if '_X' in i else i for i in INDICATORS]

    st.write("")
    if st.button("Refresh data"):
        st.session_state['current_time_price_page'] = datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0, tzinfo=None)
        fetch_table.clear()
        fetch_info.clear()
        fetch_history.clear()
        st.success("Refreshed!")

    st.write("Last update:", st.session_state['current_time_price_page'])
    st.markdown("Made with ❤️ by Leonardo")
    c1, c2 = st.columns(2, gap="small")
    with c1:
        if st.button("✉️ Contact Me", key="contact"):
            show_contact_form()
    with c2:
        st.link_button(label="", url="https://ko-fi.com/leoantiqui", icon=":material/coffee:")

    st.write("")
    _c1, _c2 = st.columns(2, gap="small")
    with _c1:
        st.markdown("<p style='text-align: right;'>Powered by:</p>", unsafe_allow_html=True)
    with _c2:
        st.image("imgs/logo_yahoo_lightpurple.svg", width=100)

# ---------------- Main page ----------------
st.title("📈 Indian Stock Market")

# ---- FIRST SECTION: Indian indices snapshot (no web-scraping) ----
# Uses Yahoo symbols directly to avoid fragile HTML scraping
INDIA_INDEX_SYMBOLS = [
    ("NIFTY 50", "^NSEI"),
    ("SENSEX", "^BSESN"),
    ("BANKNIFTY", "^NSEBANK"),
    ("NIFTY IT", "^CNXIT"),
    ("NIFTY FMCG", "^CNXFMCG"),
    ("INDIA VIX", "^INDIAVIX"),
]

col1, col2, col3 = st.columns(3, gap="small")

def _metric_for_symbol(name, symbol):
    try:
        info = fetch_info(symbol)
        if isinstance(info, Exception) or not isinstance(info, dict):
            return name, symbol, None, None
        price = info.get("regularMarketPrice")
        change = info.get("regularMarketChange")
        chg_pct = info.get("regularMarketChangePercent")
        # fallback to previousClose if no live price (indices sometimes)
        if price is None:
            price = info.get("previousClose", None)
            change = None if price is None else 0
            chg_pct = None
        return name, symbol, price, (f"{change:+.2f} ({chg_pct:+.2f}%)" if change is not None and chg_pct is not None else None)
    except Exception:
        return name, symbol, None, None

with col1:
    st.subheader("Indices A")
    with st.container(border=True):
        for label, sym in INDIA_INDEX_SYMBOLS[:2]:
            n, s, p, d = _metric_for_symbol(label, sym)
            st.metric(label=f"{n} ({s})", value="—" if p is None else f"{p}", delta=d)

with col2:
    st.subheader("Indices B")
    with st.container(border=True):
        for label, sym in INDIA_INDEX_SYMBOLS[2:4]:
            n, s, p, d = _metric_for_symbol(label, sym)
            st.metric(label=f"{n} ({s})", value="—" if p is None else f"{p}", delta=d)

with col3:
    st.subheader("Indices C")
    with st.container(border=True):
        for label, sym in INDIA_INDEX_SYMBOLS[4:6]:
            n, s, p, d = _metric_for_symbol(label, sym)
            st.metric(label=f"{n} ({s})", value="—" if p is None else f"{p}", delta=d)

# ---- SECOND SECTION ----
if len(TICKERS) == 0:
    st.header("Security: None")
    st.error("Please enter at least one Indian equity or index.")
    st.stop()

# ---------- Single ticker ----------
if len(TICKERS) == 1:
    TICKER = TICKERS[0]
    info = fetch_info(TICKER)
    if isinstance(info, Exception) or not isinstance(info, dict) or len(info) == 0:
        st.error(f"Failed to load info for '{TICKER}'")
        fetch_info.clear(TICKER)
        st.stop()

    NAME = info.get('shortName', TICKER)
    st.header(f"Security: {TICKER}")
    st.write(NAME)

    # ---- INFO PANEL ----
    with st.expander("More info"):
        col1, col2 = st.columns([0.32, 0.68], gap="small")
        with col1:
            df_info = info_table(info).reset_index().rename(columns={"index": "Feature", 0: "Value"})
            st.dataframe(df_info, hide_index=True)
        with col2:
            BUSINESS_SUMMARY = info.get('longBusinessSummary', "")
            if BUSINESS_SUMMARY:
                st.write(BUSINESS_SUMMARY)
            else:
                st.info("No business summary available for this symbol.")

    # ---- Metrics (robust for indices too) ----
    # Prefer live fields when present
    PRICE = info.get('regularMarketPrice', info.get('currentPrice', info.get('previousClose', 0)))
    PREVIOUS_PRICE = info.get('previousClose', None)
    CHANGE = None if (PRICE is None or PREVIOUS_PRICE is None) else (PRICE - PREVIOUS_PRICE)
    CHANGE_PER = None if CHANGE is None or PREVIOUS_PRICE in (None, 0) else (CHANGE / PREVIOUS_PRICE) * 100
    HIGH = info.get('dayHigh', None)
    LOW = info.get('dayLow', None)
    CURRENCY = info.get('currency', "INR")
    VOLUME = info.get('volume', None)
    FIFTY_TWO_WEEK_LOW = info.get('fiftyTwoWeekLow', None)
    FIFTY_TWO_WEEK_HIGH = info.get('fiftyTwoWeekHigh', None)

    if CHANGE_PER in (None, 0):
        st.metric("Latest Price", value=f'{PRICE if PRICE is not None else "—"} {CURRENCY}')
    else:
        st.metric("Latest Price", value=f'{PRICE:.2f} {CURRENCY}', delta=f'{CHANGE:.2f} ({CHANGE_PER:.2f}%)')

    c1, c2, c3 = st.columns(3, gap="medium")
    c1.metric("High", value=f'{HIGH:.2f} {CURRENCY}' if HIGH is not None else "—")
    c2.metric("Low", value=f'{LOW:.2f} {CURRENCY}' if LOW is not None else "—")
    c3.metric("Volume", value=f'{VOLUME:,}' if isinstance(VOLUME, (int, float)) else "—")

    # ---- Price history + indicators ----
    hist = fetch_history(TICKER, period=PERIOD, interval=INTERVAL)
    if isinstance(hist, Exception) or hist is None or len(hist) == 0:
        st.error(f"Failed to fetch price history for {TICKER}")
        fetch_history.clear(TICKER, period=PERIOD, interval=INTERVAL)
        st.stop()

    df = hist.copy()

    # Performance metrics (guard short histories)
    if len(df) >= 2:
        LEN = len(df)
        pct_1p  = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
        pct_12p = (df['Close'].iloc[-1] - df['Close'].iloc[int(LEN/2)]) / df['Close'].iloc[int(LEN/2)]
        pct_14p = (df['Close'].iloc[-1] - df['Close'].iloc[int(LEN/4)]) / df['Close'].iloc[int(LEN/4)]
        m1, m2, m3 = st.columns(3, gap="medium")
        m1.metric("1 Period",  f'{pct_1p*100:.2f}%')
        m2.metric("1/2 Period",f'{pct_12p*100:.2f}%')
        m3.metric("1/4 Period",f'{pct_14p*100:.2f}%')

    # Volume + indicators
    if 'TOGGLE_VOL' in locals() and TOGGLE_VOL:
        df['ΔVolume%'] = df['Volume'].pct_change(periods=1) * 100
        df['ΔVolume%'] = df['ΔVolume%'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else None)
    else:
        if 'Volume' in df.columns:
            df = df.drop(columns=['Volume'], axis=1)

    if 'INDICATORS' in locals():
        for IND in INDICATORS:
            if "SMA" in IND:
                window = int(IND.split("_")[1])
                df[IND] = df['Close'].rolling(window=window, min_periods=1).mean()
            if "EMA" in IND:
                window = int(IND.split("_")[1])
                df[IND] = df['Close'].ewm(span=window, adjust=False, min_periods=1).mean()

        if "ATR" in INDICATORS:
            Prev_Close = df['Close'].shift(1)
            High_Low = df['High'] - df['Low']
            High_PrevClose = abs(df['High'] - Prev_Close)
            Low_PrevClose = abs(df['Low'] - Prev_Close)
            df['TR'] = pd.concat([High_Low, High_PrevClose, Low_PrevClose], axis=1).max(axis=1)
            df['ATR'] = df['TR'].rolling(window=14, min_periods=1).mean()
            df = df.drop(columns=['TR'], axis=1)

        if "MACD" in INDICATORS:
            ema_short = df['Close'].ewm(span=12, adjust=False, min_periods=1).mean()
            ema_long  = df['Close'].ewm(span=26, adjust=False, min_periods=1).mean()
            df['MACD'] = ema_short - ema_long
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False, min_periods=1).mean()
            df['MACD_Hist'] = df['MACD'] - df['Signal']

        if "RSI" in INDICATORS:
            delta = df['Close'].pct_change(periods=1) * 100
            gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
            rs = gain / loss.replace(0, pd.NA)
            df['RSI'] = 100 - (100 / (1 + rs))

    fig = plot_candles_stick_bar(df, title="Candlestick Chart", currency=CURRENCY)
    if FIFTY_TWO_WEEK_LOW is not None:
        fig.add_hline(y=FIFTY_TWO_WEEK_LOW, line=dict(color="black", dash="dash", width=1),
                      annotation_text='52 Week Low', row=1, col=1)
    if FIFTY_TWO_WEEK_HIGH is not None:
        fig.add_hline(y=FIFTY_TWO_WEEK_HIGH, line=dict(color="black", dash="dash", width=1),
                      annotation_text='52 Week High', row=1, col=1)

    st.plotly_chart(fig, use_container_width=True)
    with st.expander("Show data"):
        st.dataframe(data=df.reset_index(), hide_index=False)

# ---------- Multiple tickers ----------
else:
    TITLE = ", ".join(TICKERS)
    st.header(f"Securities: {TITLE}")

    dfs_hist, dfs_info = [], []

    for T in TICKERS:
        info = fetch_info(T)
        if isinstance(info, Exception) or not isinstance(info, dict) or len(info) == 0:
            st.error(f"Failed to load info for '{T}'")
            fetch_info.clear(T)
            continue

        dfi = info_table(info).rename(columns={0: T}).reset_index().rename(columns={"index": "Feature"})
        dfs_info.append(dfi.set_index("Feature"))

        hist = fetch_history(T, period=PERIOD, interval=INTERVAL)
        if isinstance(hist, Exception) or hist is None or len(hist) == 0:
            st.error(f"Failed history for '{T}'")
            fetch_history.clear(T, period=PERIOD, interval=INTERVAL)
            continue

        hist.insert(0, 'Ticker', T)
        hist['Pct_change'] = ((hist['Close'] - hist['Close'].iloc[0]) / hist['Close'].iloc[0])
        dfs_hist.append(hist)

    if len(dfs_hist) == 0:
        st.error("No valid data to display.")
        st.stop()

    # ----- Info table (merged) -----
    try:
        df_info_all = pd.concat(dfs_info, axis=1, join='outer').reset_index().rename(columns={"index": "Feature"})
        with st.expander("More info"):
            st.dataframe(df_info_all, hide_index=True)
    except Exception:
        pass

    # ----- Performance table -----
    df_hist_all = pd.concat(dfs_hist, ignore_index=False)
    fig = performance_table(df_hist_all, TICKERS)
    st.plotly_chart(fig, use_container_width=True)

    # ----- Percent change line chart -----
    fig = plot_line_multiple(df_hist_all, "Percent Change Line Chart")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Show data"):
        st.dataframe(data=df_hist_all.reset_index(), hide_index=False)
