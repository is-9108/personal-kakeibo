"""SCR-04 設定（固定費）。"""

from __future__ import annotations

import streamlit as st

from common import http_client, render_sidebar_nav

st.set_page_config(page_title="家計簿 | 設定", layout="wide")
render_sidebar_nav()

st.title("設定")
st.subheader("固定費")

try:
    with http_client() as c:
        r = c.get("/fixed-costs")
        r.raise_for_status()
        rows = r.json()
except Exception as e:
    st.error(f"取得エラー: {e}")
    st.stop()

if not rows:
    st.info("固定費のレコードがありません。DB に fixed_costs を登録してください。")
    st.stop()

for fc in rows:
    fid = int(fc["id"])
    name = fc.get("name", f"ID {fid}")
    st.markdown(f"### {name}")
    with st.form(key=f"fc_{fid}"):
        amount = st.number_input("金額（円）", min_value=1, value=int(fc.get("amount", 1)), step=1, key=f"a_{fid}")
        day = st.selectbox("毎月の登録日", list(range(1, 29)), index=max(0, int(fc.get("day_of_month", 1)) - 1), key=f"d_{fid}")
        active = st.checkbox("有効", value=bool(int(fc.get("is_active", 1))), key=f"on_{fid}")
        if st.form_submit_button("保存する"):
            try:
                with http_client() as c:
                    pr = c.put(
                        f"/fixed-costs/{fid}",
                        json={
                            "amount": int(amount),
                            "day_of_month": int(day),
                            "is_active": bool(active),
                        },
                    )
                    pr.raise_for_status()
                st.success("保存しました。")
            except Exception as e:
                st.error(str(e))
