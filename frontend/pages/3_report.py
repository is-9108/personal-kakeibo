"""SCR-03 月次レポート。"""

from __future__ import annotations

from datetime import date
from typing import Any

import plotly.express as px
import streamlit as st

from common import fmt_yen, http_client, render_sidebar_nav

st.set_page_config(page_title="家計簿 | レポート", layout="wide")
render_sidebar_nav()

st.title("月次レポート")

try:
    with http_client() as c:
        r = c.get("/reports", params={"limit": 100})
        r.raise_for_status()
        report_list: list[dict[str, Any]] = r.json()
except Exception as e:
    st.error(f"一覧取得エラー: {e}")
    st.stop()

col_a, col_b = st.columns([3, 1])
with col_a:
    if report_list:
        labels = [f"{x['year']}年{x['month']}月" for x in report_list]
        idx = st.selectbox("対象月", range(len(labels)), format_func=lambda i: labels[i])
        sel = report_list[idx]
        y, m = int(sel["year"]), int(sel["month"])
    else:
        st.info("保存済みレポートがありません。下から手動生成できます。")
        today = date.today()
        y = st.number_input("年（生成・表示）", min_value=2000, max_value=2100, value=today.year)
        m = st.selectbox("月（生成・表示）", list(range(1, 13)), index=today.month - 1)

with col_b:
    st.write("")
    st.write("")
    if st.button("手動生成"):
        try:
            with http_client() as c:
                gr = c.post(f"/reports/{y}/{m}/generate")
                gr.raise_for_status()
            st.success("生成しました。")
            st.rerun()
        except Exception as e:
            st.error(str(e))

try:
    with http_client() as c:
        rr = c.get(f"/reports/{y}/{m}")
except Exception as e:
    st.error(f"レポート取得エラー: {e}")
    st.stop()

if rr.status_code == 404:
    st.warning("この月のレポートはまだありません。「手動生成」で作成してください。")
    st.stop()

try:
    rr.raise_for_status()
    rep = rr.json()
except Exception as e:
    st.error(f"レポート取得エラー: {e}")
    st.stop()

st.subheader(f"{rep['year']}年{rep['month']}月")
st.write(f"**収入** {fmt_yen(rep['total_income'])}")
st.write(f"**支出** {fmt_yen(rep['total_expense'])}")
st.write(f"**収支** {fmt_yen(rep['balance'])}")

breakdown = rep.get("category_breakdown") or []
if breakdown:
    names = [x.get("category_name", "") for x in breakdown]
    vals = [int(x.get("total_amount", 0)) for x in breakdown]
    fig = px.pie(names=names, values=vals, title="カテゴリ別支出（レポート）")
    st.plotly_chart(fig, use_container_width=True)

prev = rep.get("prev_month_diff")
if prev is None:
    st.caption("先月比データなし（初月のため）")
else:
    st.subheader("先月比")
    st.write(
        f"収入差 {fmt_yen(int(prev.get('income_diff', 0)))} "
        f"（率 {float(prev.get('income_diff_rate', 0)) * 100:.2f}%）"
    )
    st.write(
        f"支出差 {fmt_yen(int(prev.get('expense_diff', 0)))} "
        f"（率 {float(prev.get('expense_diff_rate', 0)) * 100:.2f}%）"
    )
    cats = prev.get("categories") or []
    if cats:
        for row in cats:
            st.write(
                f"- {row.get('category_name', '')}: "
                f"{fmt_yen(int(row.get('diff_amount', 0)))} "
                f"（率 {float(row.get('diff_rate', 0)) * 100:.2f}%）"
            )
