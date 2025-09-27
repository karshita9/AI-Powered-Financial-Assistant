# app.py
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import your agent (must be in same folder)
from financial_agent import multi_ai_agent

st.set_page_config(page_title="📊 AI-Powered Financial Assistant", layout="wide")


def flatten_yf_columns(df: pd.DataFrame) -> pd.DataFrame:
    """If yfinance returns MultiIndex columns (('Close','AAPL')), flatten to single-level names."""
    if isinstance(df.columns, pd.MultiIndex):
        try:
            df.columns = df.columns.get_level_values(0)
        except Exception:
            df.columns = ['_'.join([str(x) for x in col if x not in (None, '')]).strip() for col in df.columns]
    df.columns = [str(c).strip() for c in df.columns]
    return df


def safe_extract_text_from_agent(resp) -> str:
    """Extract the human-readable reply from an agent response."""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        for k in ("content", "text", "response", "output"):
            if k in resp and isinstance(resp[k], str):
                return resp[k]
        if "messages" in resp and isinstance(resp["messages"], list):
            for m in reversed(resp["messages"]):
                if isinstance(m, dict) and m.get("role") == "assistant" and isinstance(m.get("content"), str):
                    return m.get("content")
        return str(resp)
    try:
        if hasattr(resp, "content") and isinstance(resp.content, str):
            return resp.content
    except Exception:
        pass
    try:
        if hasattr(resp, "messages"):
            msgs = resp.messages
            for m in reversed(msgs):
                if hasattr(m, "content") and isinstance(m.content, str):
                    return m.content
                if isinstance(m, dict) and m.get("role") == "assistant" and isinstance(m.get("content"), str):
                    return m.get("content")
    except Exception:
        pass
    return str(resp)


def clean_ai_text(ai_text: str) -> str:
    """Remove internal [transfer task ...] or <function=...> notes."""
    import re
    ai_text = re.sub(r"\[.*?transfer.*?\]", "", ai_text, flags=re.IGNORECASE)
    ai_text = re.sub(r"<.*?>", "", ai_text)  # remove <function=...> if any
    ai_text = "\n".join([line.strip() for line in ai_text.splitlines() if line.strip()])
    return ai_text.strip()


st.title("📊 AI-Powered Financial Assistant")

# ---------------- Sidebar ----------------
st.sidebar.header("Choose Parameters")

ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, TCS.NS)", "AAPL").upper()
period_value = st.sidebar.number_input("Enter Value", min_value=1, value=30)
period_unit = st.sidebar.selectbox("Select Unit", ["Days", "Months", "Years"])
user_query = st.sidebar.text_area("💬 Ask AI (optional)", f"Summarize analyst recommendations and recent news for {ticker}")

# Convert to yfinance period
if period_unit == "Days":
    period_arg = f"{period_value}d"
elif period_unit == "Months":
    period_arg = f"{period_value}mo"
else:
    period_arg = f"{period_value}y"

# ---------------- Data fetch ----------------
st.subheader(f"📈 {ticker} Stock Data ({period_value} {period_unit})")

try:
    raw = yf.download(ticker, period=period_arg, interval="1d", progress=False)

    if raw is None or raw.empty:
        st.error("⚠ No data found. Check the ticker symbol or try a different period.")
    else:
        raw = flatten_yf_columns(raw)
        df = raw.reset_index()

        required_cols = {"Open", "High", "Low", "Close", "Volume"}
        if not required_cols.issubset(set(df.columns)):
            st.error(f"⚠ Data does not contain required columns. Found: {list(df.columns)}")
        else:
            if len(df) >= 20:
                df["SMA20"] = df["Close"].rolling(window=20).mean()
            else:
                df["SMA20"] = pd.Series([None] * len(df))

            # --- Overview metrics ---
            try:
                current_price = float(df["Close"].iloc[-1])
                prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else current_price
                change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close != 0 else 0.0
            except Exception:
                current_price, prev_close, change_pct = None, None, None

            st.markdown("### Overview")
            st.caption("A quick snapshot of the latest stock performance — current price, yesterday’s close, and daily change %.")
            c1, c2, c3 = st.columns(3)
            c1.metric("Current Price", f"${current_price:,.2f}" if current_price else "N/A")
            c2.metric("Previous Close", f"${prev_close:,.2f}" if prev_close else "N/A")
            c3.metric("Change (%)", f"{change_pct:.2f}%" if change_pct else "N/A")

            # --- Candlestick ---
            st.markdown("### Candlestick Chart")
            st.caption("This shows *daily stock price movements*. \n\n"
                       "- *X-axis* = Dates \n"
                       "- *Y-axis* = Price (in USD) \n\n"
                       "Green = stock closed higher than it opened. "
                       "Red = stock closed lower than it opened.")
            fig = go.Figure(data=[go.Candlestick(
                x=df["Date"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"]
            )])
            fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_white", height=480)
            st.plotly_chart(fig, use_container_width=True)

            # --- Price + SMA chart ---
            st.markdown("### Price Trend (Close + SMA20)")
            st.caption("This line chart shows the stock’s *daily closing price* and the *20-day Simple Moving Average (SMA20)*. \n\n"
                       "- *X-axis* = Dates \n"
                       "- *Y-axis* = Price (in USD) \n\n"
                       "SMA20 smooths short-term ups/downs, helping spot overall trends.")
            if "SMA20" in df.columns and df["SMA20"].notna().sum() > 0:
                st.line_chart(df.set_index("Date")[["Close", "SMA20"]])
            else:
                st.line_chart(df.set_index("Date")[["Close"]])

            # --- Recent data ---
            st.markdown("### Recent Data")
            st.caption("A table of the last *10 trading days* showing: \n"
                       "- *Open* (first price of the day) \n"
                       "- *High* (max price of the day) \n"
                       "- *Low* (min price of the day) \n"
                       "- *Close* (final price of the day) \n"
                       "- *Volume* (number of shares traded)")
            st.dataframe(df.tail(10).reset_index(drop=True))

            # --- AI Chat / Summary ---
            st.markdown("### 🤖 AI Assistant")
            st.write("Ask a question about this stock, or use the default sidebar prompt for a quick summary.")
            if st.button("Ask AI"):
                prompt = user_query.strip() or f"Summarize analyst recommendations and recent news for {ticker}."
                sma_text = f"{df['SMA20'].iloc[-1]:.2f}" if "SMA20" in df.columns and pd.notna(df['SMA20'].iloc[-1]) else "N/A"
                context = (
                    f"Stock: {ticker}\n"
                    f"Current Price: {current_price if current_price else 'N/A'}\n"
                    f"Change%: {change_pct if change_pct else 'N/A'}\n"
                    f"SMA20: {sma_text}\n"
                    f"Period: last {period_value} {period_unit.lower()}\n\n"
                    "Please answer concisely with a short summary and bullets. Include sources if possible.\n"
                )
                full_query = f"{context}\nUser Question: {prompt}"

                with st.spinner("🤖 AI thinking..."):
                    try:
                        ai_raw = multi_ai_agent.run(full_query, stream=False)
                        ai_text = safe_extract_text_from_agent(ai_raw)
                        ai_text = clean_ai_text(ai_text)   # 🚨 CLEAN HERE
                    except Exception as e:
                        ai_text = f"⚠ Error from agent: {e}"

                st.markdown("#### AI Response")
                st.markdown(ai_text)

except Exception as exc:
    st.error(f"❌ Error fetching data or running agent: {exc}")
