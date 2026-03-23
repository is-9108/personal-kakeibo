"""SCR-02 グラフ・分析。"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

import plotly.express as px
import streamlit as st

from common import fmt_yen, http_client, render_sidebar_nav

st.set_page_config(page_title="家計簿 | グラフ", layout="wide")
render_sidebar_nav()

st.title("グラフ・分析")


def parse_tx_date(tx: dict) -> date:
    s = tx.get("date")
    if not s:
        return date.today()
    if isinstance(s, str):
        return date.fromisoformat(s.split("T", 1)[0] if "T" in s else s[:10])
    return date.today()


def load_expense_categories() -> dict[int, str]:
    with http_client() as c:
        r = c.get("/categories", params={"type": "expense"})
        r.raise_for_status()
        rows = r.json()
    return {int(x["id"]): x["name"] for x in rows}


def load_transactions() -> list[dict]:
    with http_client() as c:
        r = c.get("/transactions", params={"limit": 500, "skip": 0})
        r.raise_for_status()
        return r.json()


today = date.today()
mode = st.radio("期間", ["今月", "先月", "指定"], horizontal=True)
if mode == "今月":
    y, m = today.year, today.month
elif mode == "先月":
    if today.month == 1:
        y, m = today.year - 1, 12
    else:
        y, m = today.year, today.month - 1
else:
    cy = st.number_input("年", min_value=2000, max_value=2100, value=today.year)
    cm = st.selectbox("月", list(range(1, 13)), index=today.month - 1)
    y, m = int(cy), int(cm)

try:
    cat_names = load_expense_categories()
    txs = load_transactions()
except Exception as e:
    st.error(f"データ取得エラー: {e}")
    st.stop()

in_month = [
    t
    for t in txs
    if parse_tx_date(t).year == y and parse_tx_date(t).month == m
]
income_total = sum(int(t["amount"]) for t in in_month if t.get("type") == "income")
expense_total = sum(int(t["amount"]) for t in in_month if t.get("type") == "expense")

agg: dict[str, int] = defaultdict(int)
for t in in_month:
    if t.get("type") != "expense":
        continue
    cid = int(t["category_id"])
    agg[cat_names.get(cid, str(cid))] += int(t["amount"])

st.metric("収入合計", fmt_yen(income_total))
st.metric("支出合計", fmt_yen(expense_total))
st.metric("収支差額", fmt_yen(income_total - expense_total))

if not agg:
    st.info("この期間の支出はありません。")
else:
    names = list(agg.keys())
    values = [agg[k] for k in names]
    ratios = [v / expense_total if expense_total else 0 for v in values]

    fig = px.pie(names=names, values=values, title="カテゴリ別支出")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("内訳")
    rows = sorted(zip(names, values, ratios), key=lambda x: -x[1])
    for name, val, r in rows:
        st.write(f"**{name}** … {fmt_yen(val)}（{r * 100:.1f}%）")
