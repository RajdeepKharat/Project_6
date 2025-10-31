import streamlit as st
import feedparser
import yfinance as yf
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="Market Pulse", layout="wide")
st.title("📰 Market Pulse — Live Finance & Stock Insights")

# --- FUNCTION: Fetch fundamentals from yfinance ---
def get_fundamentals(company_name):
    try:
        # Try direct ticker
        ticker = yf.Ticker(company_name)
        info = ticker.info
        if "longName" not in info:
            return None

        return {
            "Company": info.get("longName", "N/A"),
            "Symbol": info.get("symbol", "N/A"),
            "Sector": info.get("sector", "N/A"),
            "Market Cap": f"{info.get('marketCap', 0) / 1e9:.2f} B",
            "P/E Ratio": info.get("trailingPE", "N/A"),
            "EPS (TTM)": info.get("trailingEps", "N/A"),
            "Book Value": info.get("bookValue", "N/A"),
            "Dividend Yield": f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get("dividendYield") else "N/A",
            "52-Week High": info.get("fiftyTwoWeekHigh", "N/A"),
            "52-Week Low": info.get("fiftyTwoWeekLow", "N/A"),
            "Current Price": info.get("currentPrice", "N/A"),
        }

    except Exception as e:
        return None

# --- FUNCTION: Smartly guess company ticker ---
def guess_ticker_from_headline(title):
    # Example: "Reliance shares rise as oil prices surge"
    words = re.findall(r"[A-Z][a-z]+", title)
    possible = [w.upper() for w in words if len(w) > 3]  # Filter short words
    for w in possible:
        try:
            # Try NSE format first
            ticker = yf.Ticker(f"{w}.NS")
            if "longName" in ticker.info:
                return f"{w}.NS"
        except Exception:
            continue
    return None

# --- FETCH LATEST FINANCE NEWS ---
st.subheader("🗞 Latest Financial News (Past 7 Days)")
feed = feedparser.parse("https://news.google.com/rss/search?q=finance+india+when:7d&hl=en-IN&gl=IN&ceid=IN:en")
news_items = feed.entries[:10]

if not news_items:
    st.warning("Could not load news feed. Please try again later.")
else:
    for entry in news_items:
        title = entry.title
        link = entry.link
        st.markdown(f"### [{title}]({link})")

        ticker = guess_ticker_from_headline(title)
        if ticker:
            fundamentals = get_fundamentals(ticker)
            if fundamentals:
                with st.expander(f"💼 Fundamentals — {fundamentals['Company']} ({fundamentals['Symbol']})"):
                    cols = st.columns(2)
                    items = list(fundamentals.items())
                    for i in range(0, len(items), 2):
                        with cols[i % 2]:
                            st.write(f"**{items[i][0]}:** {items[i][1]}")
                            if i + 1 < len(items):
                                st.write(f"**{items[i+1][0]}:** {items[i+1][1]}")
            else:
                st.caption(f"⚠️ Could not fetch fundamentals for {ticker}.")
        else:
            st.caption("No clear company detected in headline.")
