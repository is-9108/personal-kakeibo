"""SCR-01 収支入力・一覧（トップ）。"""

from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from common import fmt_yen, http_client, render_sidebar_nav

st.set_page_config(page_title="家計簿 | 収支", layout="wide", initial_sidebar_state="expanded")
render_sidebar_nav()


def load_categories(tx_type: str) -> list[dict]:
    with http_client() as c:
        r = c.get("/categories", params={"type": tx_type})
        r.raise_for_status()
        rows = r.json()
    return sorted(rows, key=lambda x: x.get("sort_order", 0))


def load_payment_methods() -> list[dict]:
    with http_client() as c:
        r = c.get("/payment-methods")
        r.raise_for_status()
        rows = r.json()
    return sorted(rows, key=lambda x: x.get("sort_order", 0))


def load_transactions(limit: int = 30) -> list[dict]:
    with http_client() as c:
        r = c.get("/transactions", params={"limit": limit, "skip": 0})
        r.raise_for_status()
        return r.json()


def category_name_map() -> dict[int, str]:
    out: dict[int, str] = {}
    for typ in ("income", "expense"):
        for c in load_categories(typ):
            out[int(c["id"])] = c["name"]
    return out


def payment_name_map() -> dict[int, str]:
    return {int(p["id"]): p["name"] for p in load_payment_methods()}


if "edit_transaction" not in st.session_state:
    st.session_state.edit_transaction = None


st.title("収支入力・一覧")

cats_inc = load_categories("income")
cats_exp = load_categories("expense")
pms = load_payment_methods()
cat_names = category_name_map()
pm_names = payment_name_map()

edit = st.session_state.edit_transaction

st.subheader("収支を入力")
with st.form("tx_form", clear_on_submit=not bool(edit)):
    default_date = date.today()
    default_type = "expense"
    default_cat = cats_exp[0]["id"] if cats_exp else None
    default_pm = int(pms[0]["id"]) if pms else None
    default_memo = ""
    default_amount = 0

    if edit:
        raw_date = edit.get("date")
        if isinstance(raw_date, str):
            default_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).date()
        default_type = edit.get("type", "expense")
        default_cat = edit.get("category_id")
        default_amount = int(edit.get("amount", 0))
        pm = edit.get("payment_method_id")
        default_pm = int(pm) if pm is not None else None
        default_memo = edit.get("memo") or ""

    tx_date = st.date_input("日付", value=default_date)
    tx_type = st.radio("区分", options=["expense", "income"], format_func=lambda x: "支出" if x == "expense" else "収入", horizontal=True, index=0 if default_type == "expense" else 1)

    cats = cats_exp if tx_type == "expense" else cats_inc
    cat_labels = {c["name"]: int(c["id"]) for c in cats}
    if not cat_labels:
        st.warning("カテゴリがありません。バックエンドを起動しシードを確認してください。")
        st.stop()

    current_cat_name = next((n for n, i in cat_labels.items() if i == default_cat), next(iter(cat_labels)))
    cat_choice = st.selectbox("カテゴリ", options=list(cat_labels.keys()), index=list(cat_labels.keys()).index(current_cat_name) if current_cat_name in cat_labels else 0)

    amount = st.number_input("金額（円）", min_value=1, value=max(1, default_amount), step=1)

    payment_method_id = None
    if tx_type == "expense":
        pm_labels = {p["name"]: int(p["id"]) for p in pms}
        if not pm_labels:
            st.warning("支払い方法マスタがありません。")
            st.stop()
        cur_pm = next((n for n, i in pm_labels.items() if i == default_pm), next(iter(pm_labels)))
        pm_choice = st.selectbox("支払い方法", options=list(pm_labels.keys()), index=list(pm_labels.keys()).index(cur_pm) if cur_pm in pm_labels else 0)
        payment_method_id = pm_labels[pm_choice]
    else:
        st.caption("収入では支払い方法は不要です。")

    memo = st.text_input("メモ（任意）", value=default_memo, max_chars=200)

    submitted = st.form_submit_button("登録する" if not edit else "更新する")

    if submitted:
        cat_id = cat_labels[cat_choice]
        body: dict = {
            "date": datetime.combine(tx_date, datetime.min.time()).isoformat(),
            "type": tx_type,
            "category_id": cat_id,
            "amount": int(amount),
            "memo": memo or "",
        }
        if tx_type == "expense":
            body["payment_method_id"] = payment_method_id
        else:
            body["payment_method_id"] = None

        try:
            with http_client() as c:
                if edit:
                    tid = int(edit["id"])
                    r = c.put(f"/transactions/{tid}", json=body)
                else:
                    r = c.post("/transactions", json=body)
                r.raise_for_status()
            st.success("保存しました。")
            st.session_state.edit_transaction = None
            st.rerun()
        except Exception as e:
            st.error(f"API エラー: {e}")

if edit:
    if st.button("編集をキャンセル"):
        st.session_state.edit_transaction = None
        st.rerun()

st.subheader("最近の収支（最大30件）")

try:
    txs = load_transactions(30)
except Exception as e:
    st.error(f"一覧の取得に失敗しました: {e}")
    st.stop()

if not txs:
    st.info("まだ取引がありません。")
else:
    for t in txs:
        tid = int(t["id"])
        cid = int(t["category_id"])
        cname = cat_names.get(cid, str(cid))
        pm = t.get("payment_method_id")
        pm_label = pm_names.get(int(pm), "—") if pm is not None else "—"
        raw_date = t.get("date", "")
        if isinstance(raw_date, str):
            try:
                dpart = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).strftime("%m/%d")
            except ValueError:
                dpart = raw_date[:10]
        else:
            dpart = str(raw_date)
        typ_label = "支出" if t.get("type") == "expense" else "収入"
        line = f"{dpart} {typ_label} {cname} {fmt_yen(int(t['amount']))} {pm_label}"
        if t.get("memo"):
            line += f" — {t['memo']}"
        c1, c2, c3 = st.columns([4, 1, 1])
        with c1:
            st.write(line)
        with c2:
            if st.button("編集", key=f"e{tid}"):
                st.session_state.edit_transaction = t
                st.session_state.pop("confirm_delete_id", None)
                st.rerun()
        with c3:
            if st.button("削除", key=f"d{tid}"):
                st.session_state.confirm_delete_id = tid
                st.rerun()


if st.session_state.get("confirm_delete_id"):
    del_id = int(st.session_state.confirm_delete_id)

    @st.dialog("削除の確認")
    def _confirm_delete() -> None:
        st.write("この取引を削除しますか？")
        a, b = st.columns(2)
        with a:
            if st.button("キャンセル", key="cd_cancel"):
                st.session_state.confirm_delete_id = None
                st.rerun()
        with b:
            if st.button("削除する", key="cd_ok", type="primary"):
                try:
                    with http_client() as c:
                        r = c.delete(f"/transactions/{del_id}")
                        r.raise_for_status()
                    st.session_state.confirm_delete_id = None
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    _confirm_delete()
