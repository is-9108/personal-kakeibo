"""Streamlit 共通: API ベース URL とサイドバー。"""

from __future__ import annotations

import os

import httpx
import streamlit as st

_DEFAULT_API = "http://127.0.0.1:8000/api/v1"


def api_base() -> str:
    return os.environ.get("FASTAPI_BASE", _DEFAULT_API).rstrip("/")


def http_client() -> httpx.Client:
    return httpx.Client(base_url=api_base(), timeout=30.0)


def render_sidebar_nav() -> None:
    """仕様 6.2 に近いサイドバー（マルチページリンク）。エントリ `frontend/app.py` からの相対パス。"""
    with st.sidebar:
        st.header("家計簿")
        st.divider()
        st.page_link("app.py", label="収支入力・一覧", icon="📝")
        st.page_link("pages/2_graph.py", label="グラフ・分析", icon="📊")
        st.page_link("pages/3_report.py", label="月次レポート", icon="📅")
        st.page_link("pages/4_settings.py", label="設定", icon="⚙️")
        st.divider()
        st.caption(f"API: `{api_base()}`")


def fmt_yen(n: int) -> str:
    return f"¥{n:,}"
