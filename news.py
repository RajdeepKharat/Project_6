import streamlit as st
import feedparser
import requests
import time
from datetime import datetime
from typing import Optional

# ------------------- CONFIG -------------------
st.set_page_config(
    page_title="Market Pulse – News & Fundamentals",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Color Palette
CORAL = "#ff7a59"
MINT = "#66ffc3"
BG = "#0f1720"

# Alpha Vantage key (you can store it in Streamlit secrets)
API_KEY = st.secrets.get("ALPHA_VANTAGE_API_KEY", "G1IQMIUZ789FA5Z1")  # replace if needed

# ------------------- FUNCTIONS -------------------
def fetch_google_news(query="stock market OR finance OR IPO OR earnings", when="7d", max_items=20):
    """Fetch Google News RSS for given query."""
    base_url = "https://news.google.com/rss/search"
    params = {
        "q": f"{query} when:{when}",
        "hl": "en-IN",
        "gl": "IN",
        "ceid": "IN:en",
    }
    rss_url = base_url + "?" + "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
    feed = feedparser.parse(rss_url)
    articles = []
    for entry in feed.entries[:max_items]:
        pub_time = None
        if "published_parsed" in entry:
            pub_time = datetime(*entry.published_parsed[:6])
        articles.append({
            "title": entry.get("title"),
            "link": entry.get("link"),
            "summary": entry.get("summary", ""),
            "published": pub_time,
        })
    return articles


def alphavantage_search_symbol(keywords: str, apikey: Optional[str] = None):
    """Find best ticker using Alpha Vantage SYMBOL_SEARCH."""
    apikey = apikey or API_KEY
    if not apikey:
        return None
    url = "https://www.alphavantage.co/query"
    params = {"function": "SYMBOL_SEARCH", "keywords": keywords, "apikey": apikey}
    try:
        r = requests.get(url, params=params, timeout=10)
        j = r.json()
        matches = j.get("bestMatches", [])
        if matches:
            m = matches[0]
            return {
                "symbol": m.get("1. symbol"),
                "name": m.get("2. name"),
                "region": m.get("4. region"),
                "matchScore": m.get("9. matchScore"),
            }
    except Exception:
        return None
    return None


def alphavantage_overview(symbol: str, apikey: Optional[str] = None):
    """Fetch company fundamentals using Alpha Vantage OVERVIEW."""
    apikey = apikey or API_KEY
    if not apikey or not symbol:
        return None
    url = "https://www.alphavantage.co/query"
    params = {"function": "OVERVIEW", "symbol": symbol, "apikey": apikey}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if not data or "Note" in data or "Information" in data:
            return {"error": "Rate limited or no data available."}
        fields = [
            "Name", "Symbol", "MarketCapitalization", "PERatio", "EPS",
            "RevenueTTM", "ProfitMargin", "AnalystTargetPrice", "Currency",
            "Description"
        ]
        return {k: data.get(k, "N/A") for k in fields}
    except Exception:
        return None

# ------------------- UI -------------------

# Custom styling
st.markdown(
    f"""
    <style>
    body {{
        background-color: {BG};
    }}
    .stApp {{
        background: linear-gradient(180deg, {BG}, #07121a);
        color: #e6eef3;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {MINT};
    }}
    a {{
        color: {CORAL} !important;
        text-decoration: none;
    }}
    .fundamentals-box {{
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 12px;
        background-color: rgba(255,255,255,0.03);
        margin-top: 8px;
    }}
    .news-card {{
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        background: rgba(255,255,255,0.02);
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar
st.sidebar.title("🔍 Filter News")
query = st.sidebar.text_input("Search Topic", "stock market OR finance OR earnings OR IPO OR acquisition")
when = st.sidebar.selectbox("Time Window", ["1d", "3d", "7d"], index=2)
max_items = st.sidebar.slider("Number of articles", 5, 30, 15)

st.title("📈 Market Pulse")
st.markdown(f"Showing latest **finance & stock market news** from Google News (last {when}).")

articles = fetch_google_news(query=query, when=when, max_items=max_items)

if not articles:
    st.warning("No news found. Try a different query.")
else:
    for art in articles:
        with st.container():
            st.markdown(f"### [{art['title']}]({art['link']})")
            if art["published"]:
                st.caption(f"🕒 Published: {art['published'].strftime('%Y-%m-%d %H:%M')}")
            st.markdown(art["summary"], unsafe_allow_html=True)

            # Try symbol detection
            match = alphavantage_search_symbol(art["title"])
            if match and match.get("symbol"):
                st.markdown(f"**Detected Company:** {match['name']} ({match['symbol']}) — {match['region']}")
                with st.spinner("Fetching fundamentals..."):
                    data = alphavantage_overview(match["symbol"])
                    time.sleep(1)  # avoid rate limit
                    if data:
                        if "error" in data:
                            st.error(data["error"])
                        else:
                            with st.expander("📊 Fundamentals", expanded=False):
                                st.markdown(f"<div class='fundamentals-box'>", unsafe_allow_html=True)
                                for k, v in data.items():
                                    if k == "Description":
                                        st.markdown(f"**{k}:** {v[:300]}...")
                                    else:
                                        st.markdown(f"**{k}:** {v}")
                                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No direct company match found for this news item.")
            st.markdown("---")
