import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import json
import os
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="SpendBot Dashboard", page_icon="💸", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background: #0d0d0d; color: #f0ede6; }
.metric-card {
    background: #141414; border: 1px solid #242424;
    border-radius: 14px; padding: 1.2rem 1.4rem; text-align: center;
}
.metric-label { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #666; text-transform: uppercase; letter-spacing: 1px; }
.metric-value { font-size: 2rem; font-weight: 800; color: #c8f564; margin: 6px 0 0 0; }
.anomaly-banner {
    background: #1f1010; border: 1px solid #8b2020; border-radius: 10px;
    padding: 0.9rem 1.2rem; color: #f08080;
    font-family: 'DM Mono', monospace; font-size: 0.85rem; margin-bottom: 0.6rem;
}
</style>
""", unsafe_allow_html=True)

# ── Google Sheets connection ──────────────────────────────────────────────────
@st.cache_resource
def get_sheet():
    # Try Streamlit secrets first (TOML table format)
    if "GSHEET_CREDS" in st.secrets:
        sheet_name = st.secrets.get("GSHEET_NAME", "SpendBot")
        creds_dict = {k: v for k, v in st.secrets["GSHEET_CREDS"].items()}
    else:
        # Local .env fallback
        sheet_name = os.environ.get("GSHEET_NAME", "SpendBot")
        creds_raw = os.environ["GSHEET_CREDS"].replace("\\n", "\n")
        creds_dict = json.loads(creds_raw)

    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

@st.cache_data(ttl=60)
def load_data():
    sheet = get_sheet()
    records = sheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=["timestamp", "chat_id", "amount", "category", "place", "note"])
    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["date"] = df["timestamp"].dt.date
    return df

# ── Anomaly detection (z-score per category) ──────────────────────────────────
def detect_anomalies(df: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["is_anomaly"] = False
    for cat in df["category"].unique():
        mask = df["category"] == cat
        subset = df.loc[mask, "amount"]
        if len(subset) < 3:
            continue
        mean, std = subset.mean(), subset.std()
        if std == 0:
            continue
        z = (df.loc[mask, "amount"] - mean) / std
        df.loc[mask & (z.abs() > threshold), "is_anomaly"] = True
    return df

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown('<div style="font-size:2.4rem;font-weight:800;letter-spacing:-1px">💸 SpendBot Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:0.8rem;color:#555;margin-bottom:1.5rem">your spending · google sheets + gemini</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🔧 Filters")
    period = st.selectbox("Period", ["Last 7 days", "Last 30 days", "Last 90 days", "All time"])
    period_days = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90, "All time": None}[period]
    chat_id_filter = st.text_input("Filter by Telegram Chat ID", help="Leave blank to show all users")
    st.markdown("---")
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Auto-refreshes every 60s")

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Could not load Google Sheet: {e}")
    st.stop()

if df_raw.empty:
    st.info("No spending data yet. Start logging via Telegram!")
    st.stop()

# Apply filters
df = df_raw.copy()
if chat_id_filter:
    df = df[df["chat_id"].astype(str) == chat_id_filter.strip()]
if period_days:
    cutoff = datetime.now() - timedelta(days=period_days)
    df = df[df["timestamp"] >= cutoff]

if df.empty:
    st.warning("No data for selected filters.")
    st.stop()

df = detect_anomalies(df)

# ── Anomaly alerts ────────────────────────────────────────────────────────────
for _, row in df[df["is_anomaly"]].iterrows():
    st.markdown(
        f'<div class="anomaly-banner">🚨 <b>Unusual spend:</b> RM {row["amount"]:.2f} '
        f'on {row["category"]} at {row["place"]} '
        f'({row["timestamp"].strftime("%d %b %Y")})</div>',
        unsafe_allow_html=True
    )

# ── KPI cards ─────────────────────────────────────────────────────────────────
total = df["amount"].sum()
avg_daily = df.groupby("date")["amount"].sum().mean()
top_cat = df.groupby("category")["amount"].sum().idxmax()
txn_count = len(df)

for col, label, value in zip(
    st.columns(4),
    ["Total Spent", "Avg / Day", "Top Category", "Transactions"],
    [f"RM {total:,.2f}", f"RM {avg_daily:,.2f}", top_cat, str(txn_count)],
):
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{label}</div>'
            f'<div class="metric-value">{value}</div></div>',
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
DARK = dict(plot_bgcolor="#141414", paper_bgcolor="#141414", font_color="#f0ede6")

col1, col2 = st.columns([3, 2])
with col1:
    daily = df.groupby("date")["amount"].sum().reset_index()
    fig = px.bar(daily, x="date", y="amount", title="Daily Spending", color_discrete_sequence=["#c8f564"])
    fig.update_layout(**DARK, xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"), margin=dict(l=0,r=0,t=40,b=0))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    cat_totals = df.groupby("category")["amount"].sum().reset_index()
    fig = px.pie(cat_totals, values="amount", names="category", title="By Category",
                 color_discrete_sequence=px.colors.sequential.Plasma_r, hole=0.45)
    fig.update_layout(**DARK, margin=dict(l=0,r=0,t=40,b=0))
    st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    df["week"] = df["timestamp"].dt.to_period("W").astype(str)
    weekly = df.groupby(["week", "category"])["amount"].sum().reset_index()
    fig = px.bar(weekly, x="week", y="amount", color="category", title="Weekly by Category",
                 color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_layout(**DARK, xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"), margin=dict(l=0,r=0,t=40,b=0))
    st.plotly_chart(fig, use_container_width=True)

with col4:
    top_places = df.groupby("place")["amount"].sum().nlargest(8).reset_index()
    fig = px.bar(top_places, x="amount", y="place", orientation="h", title="Top Places",
                 color_discrete_sequence=["#c8f564"])
    fig.update_layout(**DARK, yaxis=dict(gridcolor="#222", autorange="reversed"),
                      xaxis=dict(gridcolor="#222"), margin=dict(l=0,r=0,t=40,b=0))
    st.plotly_chart(fig, use_container_width=True)

# ── Recent transactions ───────────────────────────────────────────────────────
st.markdown("### 📋 Recent Transactions")
recent = df[["timestamp","amount","category","place","note","is_anomaly"]].copy().head(50)
recent["timestamp"] = recent["timestamp"].dt.strftime("%d %b %Y %H:%M")
recent["amount"] = recent["amount"].apply(lambda x: f"RM {x:.2f}")
recent["🚨"] = recent["is_anomaly"].apply(lambda x: "🚨" if x else "")
recent = recent.drop(columns=["is_anomaly"])
st.dataframe(recent, use_container_width=True, hide_index=True)

csv = df[["timestamp","amount","category","place","note"]].to_csv(index=False)
st.download_button("⬇️ Export CSV", csv, "spending.csv", "text/csv")