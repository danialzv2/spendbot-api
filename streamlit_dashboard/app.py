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

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

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

/* budget pace bar */
.pace-track {
    width: 100%;
    height: 12px;
    background: #1a1a1a;
    border-radius: 99px;
    overflow: hidden;
    margin: 0.5rem 0;
}
.pace-fill {
    height: 100%;
    border-radius: 99px;
    transition: width 0.6s ease;
}

/* trend pill */
.trend-up   { color: #f87171; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace !important; }
.trend-down { color: #4ade80; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace !important; }
.trend-flat { color: #666;    font-size: 0.78rem; font-family: 'JetBrains Mono', monospace !important; }

/* cat trend row */
.cat-trend-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.55rem 0;
    border-bottom: 1px solid #161616;
}
.cat-trend-row:last-child { border-bottom: none; }
.cat-name { font-size: 0.85rem; color: #ede8df; }
.cat-amounts { font-family: 'JetBrains Mono', monospace !important; font-size: 0.75rem; color: #555; }

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

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background: #111 !important;
    border-color: #222 !important;
    color: #ede8df !important;
    border-radius: 10px !important;
}
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
    df["month_label"] = df["timestamp"].dt.strftime("%B %Y")
    df["day_of_week"] = df["timestamp"].dt.day_name()
    return df

# ── Helpers ───────────────────────────────────────────────────────────────────
CAT_EMOJI = {"Food":"🍜","Drinks":"🧋","Groceries":"🛒","Clothing":"👕","Transport":"🚗",
             "Entertainment":"🎮","Health":"💊","Bills":"📄","Other":"📦"}

def delta_html(now, prev, invert=False):
    if prev == 0:
        return '<span class="delta-flat">no prior data</span>'
    pct = ((now - prev) / prev) * 100
    cls = "delta-up" if pct > 0 else "delta-down"
    arrow = "▲" if pct > 0 else "▼"
    return f'<span class="{cls}">{arrow} {abs(pct):.1f}% vs prior period</span>'

def bar_chart_html(series: pd.Series, max_val=None, color="#c8f564") -> str:
    if series.empty: return ""
    mv = max_val or series.max() or 1
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

def trend_html(now, prev):
    if prev == 0:
        return '<span class="trend-flat">— new</span>'
    pct = ((now - prev) / prev) * 100
    if pct > 5:
        return f'<span class="trend-up">▲ {abs(pct):.0f}%</span>'
    elif pct < -5:
        return f'<span class="trend-down">▼ {abs(pct):.0f}%</span>'
    else:
        return f'<span class="trend-flat">→ {abs(pct):.0f}%</span>'

# ── Load ──────────────────────────────────────────────────────────────────────
try:
    df_all = load_data()
except Exception as e:
    st.error(f"Could not load Google Sheet: {e}")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filters")
    chat_input = st.text_input("Telegram Chat ID (optional)")
    st.markdown("---")
    if st.button("🔄 Refresh"):
        st.cache_data.clear(); st.rerun()
    st.caption("Auto-refreshes every 60s")

# ── Apply chat filter ─────────────────────────────────────────────────────────
df_base = df_all.copy()
if chat_input:
    df_base = df_base[df_base["chat_id"].astype(str) == chat_input.strip()]

if df_base.empty:
    st.markdown("## 💸 SpendBot")
    st.info("No data yet. Start logging via Telegram!")
    st.stop()

df_base = detect_anomalies(df_base)
now_my  = datetime.now(MY_TZ)

# ── Build month options for dropdown ─────────────────────────────────────────
available_months = (
    df_base[["month", "month_label"]]
    .drop_duplicates()
    .sort_values("month", ascending=False)
)
month_options = ["Overall"] + available_months["month_label"].tolist()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:1rem">
  <div style="font-size:1.9rem;font-weight:800;letter-spacing:-0.5px;line-height:1.1">💸 SpendBot</div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#444;margin-top:4px">
    {now_my.strftime("%A, %d %B %Y · %H:%M MYT")}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Month selector ────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">Period</div>', unsafe_allow_html=True)
selected_label = st.selectbox(
    "View spending for",
    options=month_options,
    index=0,
    label_visibility="collapsed"
)

# Filter df based on selected month
if selected_label == "Overall":
    df = df_base.copy()
    period_display = "All Time"
else:
    matched = available_months[available_months["month_label"] == selected_label]["month"].values
    if len(matched):
        df = df_base[df_base["month"] == matched[0]].copy()
    else:
        df = df_base.copy()
    period_display = selected_label

# ── Pre-compute ───────────────────────────────────────────────────────────────
today_str     = now_my.date()
yesterday_str = today_str - timedelta(days=1)
this_month    = now_my.strftime("%Y-%m")
last_month    = (now_my.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

spend_today      = df_base[df_base["date"] == today_str]["amount"].sum()
spend_yesterday  = df_base[df_base["date"] == yesterday_str]["amount"].sum()
spend_this_month = df_base[df_base["month"] == this_month]["amount"].sum()
spend_last_month = df_base[df_base["month"] == last_month]["amount"].sum()
this_week_s      = today_str - timedelta(days=today_str.weekday())
spend_this_week  = df_base[df_base["date"] >= this_week_s]["amount"].sum()
last_week_s      = this_week_s - timedelta(days=7)
last_week_e      = this_week_s - timedelta(days=1)
spend_last_week  = df_base[(df_base["date"] >= last_week_s) & (df_base["date"] <= last_week_e)]["amount"].sum()

total_selected = df["amount"].sum()
tx_count       = len(df)
avg_tx         = df["amount"].mean() if tx_count else 0
top_cat        = df.groupby("category")["amount"].sum().idxmax() if tx_count else "—"

days_so_far    = max((now_my.date() - pd.Timestamp(this_month + "-01").date()).days + 1, 1)
days_last_month_count = (pd.Timestamp(this_month + "-01") - timedelta(days=1)).day
avg_daily_this = spend_this_month / days_so_far
avg_daily_last = spend_last_month / days_last_month_count if days_last_month_count else 0

# ── Anomaly banners ───────────────────────────────────────────────────────────
for _, row in df[df["is_anomaly"]].head(3).iterrows():
    st.markdown(
        f'<div class="anomaly">🚨 Unusual spend — RM {row["amount"]:.2f} '
        f'on {row["category"]} at {row["place"]} · {row["timestamp"].strftime("%d %b")}</div>',
        unsafe_allow_html=True
    )

# ── KPI Cards ─────────────────────────────────────────────────────────────────
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
        <div class="card-delta"><span class="delta-flat">{tx_count} transactions · {period_display}</span></div>
    </div>""", unsafe_allow_html=True)
with c6:
    st.markdown(f"""<div class="card">
        <div class="card-label">Top Category</div>
        <div class="card-value" style="font-size:1.3rem">{CAT_EMOJI.get(top_cat,"")} {top_cat}</div>
        <div class="card-delta"><span class="delta-flat">RM {total_selected:,.2f} total · {period_display}</span></div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ── MONTHLY SPENDING BREAKDOWN ────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">Monthly Spending — ' + period_display + '</div>', unsafe_allow_html=True)

cat_totals_selected = df.groupby("category")["amount"].sum().sort_values(ascending=False)
st.markdown(bar_chart_html(cat_totals_selected), unsafe_allow_html=True)

# Monthly total summary card
if selected_label != "Overall":
    days_in_period = df["date"].nunique()
    avg_per_day    = total_selected / days_in_period if days_in_period else 0
    top_place_sel  = df.groupby("place")["amount"].sum().idxmax() if not df.empty else "—"
    top_place_amt  = df[df["place"] == top_place_sel]["amount"].sum() if not df.empty else 0

    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown(f"""<div class="card">
            <div class="card-label">Total Spent</div>
            <div class="card-value accent">RM {total_selected:,.2f}</div>
            <div class="card-delta"><span class="delta-flat">{tx_count} transactions</span></div>
        </div>""", unsafe_allow_html=True)
    with p2:
        st.markdown(f"""<div class="card">
            <div class="card-label">Daily Average</div>
            <div class="card-value">RM {avg_per_day:,.2f}</div>
            <div class="card-delta"><span class="delta-flat">across {days_in_period} active days</span></div>
        </div>""", unsafe_allow_html=True)
    with p3:
        st.markdown(f"""<div class="card">
            <div class="card-label">Top Place</div>
            <div class="card-value" style="font-size:1.1rem">{top_place_sel}</div>
            <div class="card-delta"><span class="delta-flat">RM {top_place_amt:,.2f} total</span></div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ── MONTHLY COMPARISON (month over month) ────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">Month over Month</div>', unsafe_allow_html=True)

monthly_totals = (
    df_base.groupby(["month", "month_label"])["amount"]
    .sum()
    .reset_index()
    .sort_values("month", ascending=True)
    .tail(6)  # last 6 months
)

if len(monthly_totals) > 1:
    chart_df = monthly_totals.set_index("month_label")[["amount"]].rename(columns={"amount": "RM"})
    st.line_chart(chart_df, color="#c8f564", height=180, use_container_width=True)
elif len(monthly_totals) == 1:
    st.info("Need at least 2 months of data to show trend.")

# ── Category trend (this month vs last month) ─────────────────────────────────
cats_this = df_base[df_base["month"] == this_month].groupby("category")["amount"].sum()
cats_last = df_base[df_base["month"] == last_month].groupby("category")["amount"].sum()
all_cats  = sorted(set(cats_this.index) | set(cats_last.index))

if all_cats and spend_last_month > 0:
    rows_html = ""
    for cat in sorted(all_cats, key=lambda c: cats_this.get(c, 0), reverse=True):
        now_amt  = cats_this.get(cat, 0)
        prev_amt = cats_last.get(cat, 0)
        emoji    = CAT_EMOJI.get(cat, "📦")
        t_html   = trend_html(now_amt, prev_amt)
        rows_html += f"""
        <div class="cat-trend-row">
          <div class="cat-name">{emoji} {cat}</div>
          <div style="display:flex;align-items:center;gap:1rem">
            <div class="cat-amounts">RM {prev_amt:,.0f} → RM {now_amt:,.0f}</div>
            {t_html}
          </div>
        </div>"""
    st.markdown(
        f'<div style="background:#111;border:1px solid #1e1e1e;border-radius:16px;padding:0.5rem 1rem">{rows_html}</div>',
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════════════════════════════════════
# ── BUDGET PACE ───────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">Budget Pace</div>', unsafe_allow_html=True)

if spend_last_month > 0:
    days_in_month   = (pd.Timestamp(this_month + "-01") + pd.offsets.MonthEnd(0)).day
    day_of_month    = now_my.day
    expected_spend  = (spend_last_month / days_in_month) * day_of_month
    pace_pct        = min((spend_this_month / spend_last_month) * 100, 150)
    expected_pct    = (expected_spend / spend_last_month) * 100

    if spend_this_month <= expected_spend * 0.85:
        pace_color  = "#4ade80"
        pace_label  = "🟢 Under budget pace"
        pace_msg    = f"You're spending <b>less than expected</b> at this point in the month. On track to spend RM {(spend_this_month/day_of_month*days_in_month):,.0f} this month vs last month's RM {spend_last_month:,.0f}."
    elif spend_this_month <= expected_spend * 1.15:
        pace_color  = "#fbbf24"
        pace_label  = "🟡 On track"
        pace_msg    = f"Spending is roughly on par with last month's pace. Projected: RM {(spend_this_month/day_of_month*days_in_month):,.0f} vs last month's RM {spend_last_month:,.0f}."
    else:
        pace_color  = "#f87171"
        pace_label  = "🔴 Ahead of last month's pace"
        pace_msg    = f"You're spending <b>faster than last month</b>. Projected: RM {(spend_this_month/day_of_month*days_in_month):,.0f} vs last month's RM {spend_last_month:,.0f}."

    st.markdown(f"""
    <div class="card">
        <div class="card-label">{pace_label} &nbsp;·&nbsp; Day {day_of_month} of {days_in_month}</div>
        <div style="display:flex;justify-content:space-between;margin:0.4rem 0 0.2rem 0">
            <span style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#555">RM 0</span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#555">Last month: RM {spend_last_month:,.0f}</span>
        </div>
        <div class="pace-track">
            <div class="pace-fill" style="width:{min(pace_pct,100):.1f}%;background:{pace_color}"></div>
        </div>
        <div style="display:flex;justify-content:space-between;margin-top:0.3rem">
            <span style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:{pace_color}">
                This month: RM {spend_this_month:,.0f} ({pace_pct:.0f}%)
            </span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#444">
                Expected by today: RM {expected_spend:,.0f}
            </span>
        </div>
        <div class="insight-text" style="margin-top:0.6rem">{pace_msg}</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown('<div class="insight"><div class="insight-icon">💡</div><div class="insight-text">Budget pace needs at least 1 full prior month of data.</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ── SPENDING PATTERNS ─────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">Spending Patterns</div>', unsafe_allow_html=True)

p1, p2 = st.columns(2)

# Day of week heatmap
with p1:
    st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;color:#555;margin-bottom:0.5rem;text-transform:uppercase;letter-spacing:1px">By Day of Week</div>', unsafe_allow_html=True)
    dow_order  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    dow_totals = df_base.groupby("day_of_week")["amount"].sum().reindex(dow_order).fillna(0)
    st.markdown(bar_chart_html(dow_totals, color="#7dd3fc"), unsafe_allow_html=True)

# Top places
with p2:
    st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;color:#555;margin-bottom:0.5rem;text-transform:uppercase;letter-spacing:1px">Top Places</div>', unsafe_allow_html=True)
    top_places = df.groupby("place")["amount"].sum().sort_values(ascending=False).head(7)
    if "Unknown" in top_places.index:
        top_places = top_places.drop("Unknown")
    st.markdown(bar_chart_html(top_places, color="#f9a8d4"), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ── AUTO INSIGHTS ─────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">Auto Insights</div>', unsafe_allow_html=True)

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

# Biggest single transaction this month
if not df_base[df_base["month"] == this_month].empty:
    biggest = df_base[df_base["month"] == this_month].loc[df_base[df_base["month"] == this_month]["amount"].idxmax()]
    insights.append(("💥", f"Biggest transaction this month: <b>RM {biggest['amount']:.2f}</b> at {biggest['place']} ({biggest['category']}) on {biggest['timestamp'].strftime('%d %b')}."))

# Spend-free days this month
all_days_this_month = pd.date_range(
    start=pd.Timestamp(this_month + "-01"),
    end=pd.Timestamp(now_my.date()),
    freq="D"
).date.tolist()
active_days     = set(df_base[df_base["month"] == this_month]["date"].tolist())
spend_free_days = len([d for d in all_days_this_month if d not in active_days])
if spend_free_days > 0:
    insights.append(("🧘", f"<b>{spend_free_days} spend-free day{'s' if spend_free_days > 1 else ''}</b> so far this month. Every one counts!"))

# Most expensive day of week
if len(df_base) >= 7:
    dow_avg = df_base.groupby("day_of_week")["amount"].mean()
    worst_day = dow_avg.idxmax()
    insights.append(("📅", f"<b>{worst_day}</b> is historically your highest-spend day of the week (avg RM {dow_avg[worst_day]:.2f} per transaction)."))

# Category this month vs last
if spend_last_month > 0 and not cats_this.empty:
    top = cats_this.idxmax()
    now_amt  = cats_this.get(top, 0)
    prev_amt = cats_last.get(top, 0)
    if prev_amt > 0:
        diff_pct = ((now_amt - prev_amt) / prev_amt) * 100
        direction = f"up {diff_pct:.0f}%" if diff_pct > 0 else f"down {abs(diff_pct):.0f}%"
        insights.append(("🏷️", f"<b>{CAT_EMOJI.get(top,'')} {top}</b> is your top category this month at RM {now_amt:.2f} — {direction} from last month's RM {prev_amt:.2f}."))

# Anomaly summary
anom_count = df["is_anomaly"].sum()
if anom_count > 0:
    insights.append(("🚨", f"<b>{anom_count} unusual transaction{'s' if anom_count > 1 else ''}</b> detected in this period — significantly higher than your normal for those categories."))

# Weekend vs weekday
df_base_copy = df_base.copy()
df_base_copy["is_weekend"] = df_base_copy["day_of_week"].isin(["Saturday", "Sunday"])
weekend_avg  = df_base_copy[df_base_copy["is_weekend"]]["amount"].mean()
weekday_avg  = df_base_copy[~df_base_copy["is_weekend"]]["amount"].mean()
if weekend_avg and weekday_avg:
    if weekend_avg > weekday_avg * 1.2:
        insights.append(("🛍️", f"You spend <b>more on weekends</b> (avg RM {weekend_avg:.2f}/tx) than weekdays (avg RM {weekday_avg:.2f}/tx). Weekend lifestyle tax is real."))
    elif weekday_avg > weekend_avg * 1.2:
        insights.append(("💼", f"You actually spend <b>more on weekdays</b> (avg RM {weekday_avg:.2f}/tx) than weekends (avg RM {weekend_avg:.2f}/tx)."))

for icon, text in insights:
    st.markdown(f'<div class="insight"><div class="insight-icon">{icon}</div>'
                f'<div class="insight-text">{text}</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ── RECENT TRANSACTIONS ───────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">Recent Transactions — ' + period_display + '</div>', unsafe_allow_html=True)

recent = df.sort_values("timestamp", ascending=False).head(30)
rows_html = ""
for _, row in recent.iterrows():
    flag  = " 🚨" if row.get("is_anomaly") else ""
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

st.markdown(
    f'<div style="background:#111;border:1px solid #1e1e1e;border-radius:16px;padding:0.5rem 1rem">{rows_html}</div>',
    unsafe_allow_html=True
)

# ── Export ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
csv = df[["timestamp","amount","category","place","note"]].to_csv(index=False)
st.download_button(f"⬇️ Export CSV ({period_display})", csv, "spending.csv", "text/csv", use_container_width=True)