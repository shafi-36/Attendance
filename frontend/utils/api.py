"""Shared API helper utilities for the Streamlit frontend."""
import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8010")


def _auth_headers() -> dict:
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(path: str, params: dict | None = None) -> requests.Response:
    return requests.get(
        f"{API_BASE_URL}{path}",
        headers=_auth_headers(),
        params=params,
        timeout=15,
    )


def api_post(path: str, json: dict | None = None, data=None, files=None) -> requests.Response:
    return requests.post(
        f"{API_BASE_URL}{path}",
        headers=_auth_headers() if (data or files) else {**_auth_headers(), "Content-Type": "application/json"},
        json=json,
        data=data,
        files=files,
        timeout=30,
    )


def api_post_form(path: str, data: dict, files=None, timeout: int = 180) -> requests.Response:
    """Multipart form post (for student registration with image)."""
    return requests.post(
        f"{API_BASE_URL}{path}",
        headers=_auth_headers(),
        data=data,
        files=files,
        timeout=timeout,
    )


def api_put(path: str, json: dict | None = None) -> requests.Response:
    return requests.put(
        f"{API_BASE_URL}{path}",
        headers=_auth_headers(),
        json=json,
        timeout=15,
    )


def api_delete(path: str) -> requests.Response:
    return requests.delete(
        f"{API_BASE_URL}{path}",
        headers=_auth_headers(),
        timeout=15,
    )


def handle_error(resp: requests.Response, context: str = "") -> bool:
    """Show error toast and return True if response is an error."""
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        st.error(f"{context}: {detail}" if context else detail)
        return True
    return False
