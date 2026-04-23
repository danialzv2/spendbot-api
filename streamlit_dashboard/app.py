import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os, json

MY_TZ = ZoneInfo("Asia/Kuala_Lumpur")

st.set_page_config(page_title="SpendBot", page_icon="💸", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;800&family=JetBrains+Mono:wght@400;500&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Bricolage Grotesque', sans-serif !important;
    -webkit-tap-highlight-color: transparent;
}
.stApp { background: #0a0a0a !important; color: #ede8df !important; }
.block-container { padding: 1rem 1rem 3rem 1rem !important; max-width: 900px !important; }

/* hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* sidebar */
section[data-testid="stSidebar"] { background: #111 !important; border-right: 1px solid #1e1e1e; }

/* metric cards */
.card {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 16px;
    padding: 1.1rem 1.2rem;
    margin-bottom: 0.5rem;
    position: relative;
    overflow: hidden;
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #c8f564, transparent);
}
.card-label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.68rem;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0.4rem;
}
.card-value {
    font-size: 1.7rem;
    font-weight: 800;
    color: #ede8df;
    line-height: 1.1;
}
.card-value.accent { color: #c8f564; }
.card-delta {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem;
    margin-top: 0.3rem;
}
.delta-up   { color: #f87171; }
.delta-down { color: #4ade80; }
.delta-flat { color: #666; }

/* section headers */
.section-head {
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #444;
    margin: 1.8rem 0 0.8rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1a1a1a;
}

/* bar chart */
.bar-row {
    display: flex;
    align-items: center;
    margin-bottom: 0.55rem;
    gap: 0.6rem;
}
.bar-label {
    font-size: 0.82rem;
    color: #aaa;
    min-width: 90px;
    max-width: 90px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.bar-track {
    flex: 1;
    height: 8px;
    background: #1a1a1a;
    border-radius: 99px;
    overflow: hidden;
}
.bar-fill {
    height: 100%;
    border-radius: 99px;
    background: #c8f564;
    transition: width 0.6s ease;
}
.bar-fill.muted { background: #2a2a2a; border: 1px solid #333; }
.bar-amount {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem;
    color: #777;
    min-width: 64px;
    text-align: right;
}

/* insight cards */
.insight {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 12px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    gap: 0.8rem;
    align-items: flex-start;
}
.insight-icon { font-size: 1.1rem; margin-top: 1px; flex-shrink: 0; }
.insight-text { font-size: 0.85rem; color: #aaa; line-height: 1.5; }
.insight-text b { color: #ede8df; }

/* anomaly */
.anomaly {
    background: #180e0e;
    border: 1px solid #5c1a1a;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.82rem;
    color: #f87171;
    font-family: 'JetBrains Mono', monospace !important;
}

/* tx table */
.tx-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.65rem 0;
    border-bottom: 1px solid #161616;
    gap: 0.5rem;
}
.tx-row:last-child { border-bottom: none; }
.tx-left { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }
.tx-place { font-size: 0.88rem; color: #ede8df; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tx-meta  { font-size: 0.72rem; color: #555; font-family: 'JetBrains Mono', monospace !important; }
.tx-amount { font-family: 'JetBrains Mono', monospace !important; font-size: 0.9rem; font-weight: 600; color: #c8f564; white-space: nowrap; flex-shrink: 0; }
.cat-pill {
    display: inline-block;
    background: #181818;
    border: 1px solid #252525;
    border-radius: 99px;
    padding: 1px 8px;
    font-size: 0.68rem;
    color: #666;
    font-family: 'JetBrains Mono', monospace !important;
}

/* stSelectbox, stTextInput */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background: #111 !important;
    border-color: #222 !important;
    color: #ede8df !important;
    border-radius: 10px !important;
}

/* buttons */
.stButton > button {
    background: #c8f564 !important;
    color: #0a0a0a !important;
    font-family: 'Bricolage Grotesque', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.45rem 1.2rem !important;
    font-size: 0.85rem !important;
}
.stDownloadButton > button {
    background: #161616 !important;
    color: #888 !important;
    border: 1px solid #222 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Google Sheets ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_sheet():
    if "GSHEET_CREDS" in st.secrets:
        sheet_name = st.secrets.get("GSHEET_NAME", "SpendBot")
        creds_dict = {k: v for k, v in st.secrets["GSHEET_CREDS"].items()}
    else:
        sheet_name = os.environ.get("GSHEET_NAME", "SpendBot")
        raw = os.environ["GSHEET_CREDS"]
        import re as _re
        def fix_key(s):
            m = _re.search(r'"private_key"\s*:\s*"(.*?)"(?=\s*,)', s, _re.DOTALL)
            if m:
                fixed = m.group(1).replace('\n', '\\n').replace('\r', '')
                s = s[:m.start(1)] + fixed + s[m.end(1):]
            return s
        creds_dict = json.loads(fix_key(raw))

    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

@st.cache_data(ttl=60)
def load_data():
    sheet   = get_sheet()
    records = sheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=["timestamp","chat_id","amount","category","place","note"])
    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["amount"]    = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["date"]      = df["timestamp"].dt.date
    df["week"]      = df["timestamp"].dt.to_period("W").astype(str)
    df["month"]     = df["timestamp"].dt.to_period("M").astype(str)
    return df

# ── Helpers ───────────────────────────────────────────────────────────────────
CAT_EMOJI = {"Food":"🍜","Transport":"🚗","Shopping":"🛍️","Entertainment":"🎮",
             "Health":"💊","Bills":"📄","Education":"📚","Other":"📦"}

def delta_html(now, prev, invert=False):
    if prev == 0:
        return '<span class="delta-flat">no prior data</span>'
    pct = ((now - prev) / prev) * 100
    up  = pct > 0
    if invert: up = not up
    cls = "delta-up" if (pct > 0) else "delta-down"
    arrow = "▲" if pct > 0 else "▼"
    return f'<span class="{cls}">{arrow} {abs(pct):.1f}% vs prior period</span>'

def bar_chart_html(series: pd.Series, max_val=None, color="#c8f564") -> str:
    if series.empty: return ""
    mv   = max_val or series.max() or 1
    rows = ""
    for label, val in series.items():
        pct = min((val / mv) * 100, 100)
        rows += f"""
        <div class="bar-row">
          <div class="bar-label" title="{label}">{label}</div>
          <div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>
          <div class="bar-amount">RM {val:,.0f}</div>
        </div>"""
    return rows

def detect_anomalies(df):
    df = df.copy()
    df["is_anomaly"] = False
    for cat in df["category"].unique():
        mask = df["category"] == cat
        s    = df.loc[mask, "amount"]
        if len(s) < 3: continue
        std  = s.std()
        if std == 0: continue
        z = (df.loc[mask, "amount"] - s.mean()) / std
        df.loc[mask & (z.abs() > 2), "is_anomaly"] = True
    return df

# ── Load ──────────────────────────────────────────────────────────────────────
try:
    df_all = load_data()
except Exception as e:
    st.error(f"Could not load Google Sheet: {e}")
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filters")
    period     = st.selectbox("Period", ["Last 7 days","Last 30 days","Last 90 days","All time"], index=1)
    chat_input = st.text_input("Telegram Chat ID (optional)")
    st.markdown("---")
    if st.button("🔄 Refresh"):
        st.cache_data.clear(); st.rerun()
    st.caption("Auto-refreshes every 60s")

period_days = {"Last 7 days":7,"Last 30 days":30,"Last 90 days":90,"All time":None}[period]

df = df_all.copy()
if chat_input:
    df = df[df["chat_id"].astype(str) == chat_input.strip()]
if period_days:
    cutoff = datetime.now() - timedelta(days=period_days)
    df     = df[df["timestamp"] >= pd.Timestamp(cutoff)]

if df.empty:
    st.markdown("## 💸 SpendBot")
    st.info("No data yet. Start logging via Telegram!")
    st.stop()

df = detect_anomalies(df)
now_my = datetime.now(MY_TZ)

# ── Pre-compute periods ───────────────────────────────────────────────────────
today_str     = now_my.date()
yesterday_str = today_str - timedelta(days=1)
this_month    = now_my.strftime("%Y-%m")
last_month    = (now_my.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
this_week_s   = today_str - timedelta(days=today_str.weekday())
last_week_s   = this_week_s - timedelta(days=7)
last_week_e   = this_week_s - timedelta(days=1)

spend_today     = df[df["date"] == today_str]["amount"].sum()
spend_yesterday = df[df["date"] == yesterday_str]["amount"].sum()
spend_this_month= df[df["month"] == this_month]["amount"].sum()
spend_last_month= df[df["month"] == last_month]["amount"].sum()
spend_this_week = df[df["date"] >= this_week_s]["amount"].sum()
spend_last_week = df[(df["date"] >= last_week_s) & (df["date"] <= last_week_e)]["amount"].sum()
total_all       = df["amount"].sum()
tx_count        = len(df)
avg_tx          = df["amount"].mean() if tx_count else 0
top_cat         = df.groupby("category")["amount"].sum().idxmax() if tx_count else "—"

# Days in month so far for daily average
days_so_far = max((now_my.date() - pd.Timestamp(this_month + "-01").date()).days + 1, 1)
avg_daily_this  = spend_this_month / days_so_far
days_last_month = (pd.Timestamp(this_month + "-01") - timedelta(days=1)).day
avg_daily_last  = spend_last_month / days_last_month if days_last_month else 0

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:1.5rem">
  <div style="font-size:1.9rem;font-weight:800;letter-spacing:-0.5px;line-height:1.1">💸 SpendBot</div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#444;margin-top:4px">
    {now_my.strftime("%A, %d %B %Y · %H:%M MYT")}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Anomaly banners ───────────────────────────────────────────────────────────
for _, row in df[df["is_anomaly"]].head(3).iterrows():
    st.markdown(
        f'<div class="anomaly">🚨 Unusual spend — RM {row["amount"]:.2f} '
        f'on {row["category"]} at {row["place"]} · {row["timestamp"].strftime("%d %b")}</div>',
        unsafe_allow_html=True
    )

# ── KPI row ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">Overview</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""<div class="card">
        <div class="card-label">Today</div>
        <div class="card-value accent">RM {spend_today:,.2f}</div>
        <div class="card-delta">{delta_html(spend_today, spend_yesterday)}</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="card">
        <div class="card-label">This Month</div>
        <div class="card-value">RM {spend_this_month:,.2f}</div>
        <div class="card-delta">{delta_html(spend_this_month, spend_last_month)}</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""<div class="card">
        <div class="card-label">This Week</div>
        <div class="card-value">RM {spend_this_week:,.2f}</div>
        <div class="card-delta">{delta_html(spend_this_week, spend_last_week)}</div>
    </div>""", unsafe_allow_html=True)

c4, c5, c6 = st.columns(3)
with c4:
    st.markdown(f"""<div class="card">
        <div class="card-label">Avg / Day (this month)</div>
        <div class="card-value">RM {avg_daily_this:,.2f}</div>
        <div class="card-delta">{delta_html(avg_daily_this, avg_daily_last)}</div>
    </div>""", unsafe_allow_html=True)

with c5:
    st.markdown(f"""<div class="card">
        <div class="card-label">Avg per Transaction</div>
        <div class="card-value">RM {avg_tx:,.2f}</div>
        <div class="card-delta"><span class="delta-flat">{tx_count} transactions</span></div>
    </div>""", unsafe_allow_html=True)

with c6:
    st.markdown(f"""<div class="card">
        <div class="card-label">Top Category</div>
        <div class="card-value" style="font-size:1.3rem">{CAT_EMOJI.get(top_cat,"")} {top_cat}</div>
        <div class="card-delta"><span class="delta-flat">RM {total_all:,.2f} total</span></div>
    </div>""", unsafe_allow_html=True)

# ── Auto Analysis / Insights ──────────────────────────────────────────────────
st.markdown('<div class="section-head">Auto Analysis</div>', unsafe_allow_html=True)

insights = []

# Today vs yesterday
if spend_today > 0 and spend_yesterday > 0:
    diff = spend_today - spend_yesterday
    if diff > 0:
        insights.append(("📈", f"You spent <b>RM {diff:.2f} more</b> today than yesterday (RM {spend_yesterday:.2f})."))
    else:
        insights.append(("📉", f"You spent <b>RM {abs(diff):.2f} less</b> today than yesterday (RM {spend_yesterday:.2f}). Good job!"))
elif spend_today == 0:
    insights.append(("✨", "No spending recorded today yet."))

# Month vs last month
if spend_last_month > 0:
    proj = avg_daily_this * now_my.day
    if proj > spend_last_month:
        insights.append(("⚠️", f"At this pace you're on track to spend <b>RM {proj:,.0f}</b> this month — "
                               f"<b>RM {proj-spend_last_month:,.0f} more</b> than last month (RM {spend_last_month:,.0f})."))
    else:
        insights.append(("🎯", f"On track to spend <b>RM {proj:,.0f}</b> this month — "
                               f"<b>RM {spend_last_month-proj:,.0f} less</b> than last month (RM {spend_last_month:,.0f})."))

# Daily average comparison
if avg_daily_last > 0:
    if avg_daily_this > avg_daily_last * 1.2:
        insights.append(("🔴", f"Daily average this month <b>RM {avg_daily_this:.2f}</b> is "
                               f"<b>{((avg_daily_this/avg_daily_last)-1)*100:.0f}% higher</b> than last month's RM {avg_daily_last:.2f}."))
    elif avg_daily_this < avg_daily_last * 0.8:
        insights.append(("🟢", f"Daily average this month <b>RM {avg_daily_this:.2f}</b> is "
                               f"<b>{(1-(avg_daily_this/avg_daily_last))*100:.0f}% lower</b> than last month's RM {avg_daily_last:.2f}. Saving well!"))

# Biggest category this month
cat_this_month = df[df["month"] == this_month].groupby("category")["amount"].sum()
if not cat_this_month.empty:
    top = cat_this_month.idxmax()
    top_amt = cat_this_month.max()
    top_pct = (top_amt / spend_this_month * 100) if spend_this_month else 0
    insights.append(("🏷️", f"<b>{CAT_EMOJI.get(top,'')} {top}</b> is your biggest spend category this month "
                           f"at <b>RM {top_amt:.2f} ({top_pct:.0f}%)</b> of total."))

# Most frequent place
top_place = df.groupby("place")["amount"].count().idxmax() if not df.empty else None
top_place_amt = df[df["place"] == top_place]["amount"].sum() if top_place else 0
if top_place and top_place != "Unknown":
    insights.append(("📍", f"You visit <b>{top_place}</b> the most — "
                           f"RM {top_place_amt:.2f} spent there in this period."))

# Anomaly summary
anom_count = df["is_anomaly"].sum()
if anom_count > 0:
    insights.append(("🚨", f"<b>{anom_count} unusual transaction{'s' if anom_count>1 else ''}</b> detected — "
                           f"significantly higher than your normal spending in those categories."))

for icon, text in insights:
    st.markdown(f'<div class="insight"><div class="insight-icon">{icon}</div>'
                f'<div class="insight-text">{text}</div></div>', unsafe_allow_html=True)

# ── By Category bar chart ─────────────────────────────────────────────────────
st.markdown('<div class="section-head">By Category</div>', unsafe_allow_html=True)
cat_totals = df.groupby("category")["amount"].sum().sort_values(ascending=False)
st.markdown(bar_chart_html(cat_totals), unsafe_allow_html=True)

# ── Daily spending (native Streamlit chart — mobile friendly) ─────────────────
st.markdown('<div class="section-head">Daily Spending</div>', unsafe_allow_html=True)
daily = df.groupby("date")["amount"].sum().reset_index()
daily.columns = ["date", "RM"]
daily["date"] = pd.to_datetime(daily["date"])
st.bar_chart(daily.set_index("date"), color="#c8f564", height=200, use_container_width=True)

# ── Top Places ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">Top Places</div>', unsafe_allow_html=True)
top_places = df.groupby("place")["amount"].sum().sort_values(ascending=False).head(8)
st.markdown(bar_chart_html(top_places, color="#7dd3fc"), unsafe_allow_html=True)

# ── This Month vs Last Month side-by-side bars ────────────────────────────────
st.markdown('<div class="section-head">This Month vs Last Month (by Category)</div>', unsafe_allow_html=True)
cats_this = df[df["month"] == this_month].groupby("category")["amount"].sum()
cats_last = df[df["month"] == last_month].groupby("category")["amount"].sum()
all_cats  = sorted(set(cats_this.index) | set(cats_last.index))
max_val   = max(cats_this.max() if not cats_this.empty else 0,
                cats_last.max() if not cats_last.empty else 0) or 1

if all_cats:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;color:#555;margin-bottom:0.5rem">THIS MONTH</div>', unsafe_allow_html=True)
        s = pd.Series({c: cats_this.get(c, 0) for c in all_cats})
        st.markdown(bar_chart_html(s, max_val=max_val, color="#c8f564"), unsafe_allow_html=True)
    with col_b:
        st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;color:#555;margin-bottom:0.5rem">LAST MONTH</div>', unsafe_allow_html=True)
        s = pd.Series({c: cats_last.get(c, 0) for c in all_cats})
        st.markdown(bar_chart_html(s, max_val=max_val, color="#555"), unsafe_allow_html=True)

# ── Recent Transactions ───────────────────────────────────────────────────────
st.markdown('<div class="section-head">Recent Transactions</div>', unsafe_allow_html=True)
recent = df.sort_values("timestamp", ascending=False).head(30)
rows_html = ""
for _, row in recent.iterrows():
    flag = " 🚨" if row.get("is_anomaly") else ""
    emoji = CAT_EMOJI.get(row["category"], "📦")
    rows_html += f"""
    <div class="tx-row">
      <div class="tx-left">
        <div class="tx-place">{emoji} {row['place'] or '—'}{flag}</div>
        <div class="tx-meta">{row['timestamp'].strftime('%d %b · %H:%M')} &nbsp;·&nbsp;
          <span class="cat-pill">{row['category']}</span>
          {"&nbsp;·&nbsp;" + str(row['note']) if row.get('note') else ""}
        </div>
      </div>
      <div class="tx-amount">RM {row['amount']:.2f}</div>
    </div>"""

st.markdown(f'<div style="background:#111;border:1px solid #1e1e1e;border-radius:16px;padding:0.5rem 1rem">{rows_html}</div>',
            unsafe_allow_html=True)

# ── Export ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
csv = df[["timestamp","amount","category","place","note"]].to_csv(index=False)
st.download_button("⬇️ Export CSV", csv, "spending.csv", "text/csv", use_container_width=True)