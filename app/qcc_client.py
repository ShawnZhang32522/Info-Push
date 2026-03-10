from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import httpx

from app.config import SETTINGS
from app.models import IntentParams

QCC_BASE = "https://api.qichacha.com"
GET_LIST_URL = f"{QCC_BASE}/TenderCheck/GetList"
GET_DETAIL_URL = f"{QCC_BASE}/TenderCheck/GetDetail"


def _build_headers() -> dict[str, str]:
    ts = str(int(time.time()))
    token_raw = f"{SETTINGS.qcc_app_key}{ts}{SETTINGS.qcc_secret_key}"
    token = hashlib.md5(token_raw.encode("utf-8")).hexdigest().upper()
    return {"Token": token, "Timespan": ts}


def _mock_file() -> Path:
    return Path(__file__).resolve().parent.parent / "mock_data" / "tender_list.json"


def _to_query(intent: IntentParams, keyword: str) -> dict[str, str]:
    query: dict[str, str] = {
        "key": SETTINGS.qcc_app_key or "mock_app_key",
        "keyword": keyword,
        "pageIndex": str(intent.page_index),
        "pageSize": str(intent.page_size),
    }
    if intent.area_code:
        query["areaCode"] = intent.area_code
    if intent.msg_type:
        query["msgType"] = intent.msg_type
    if intent.pub_date_start:
        query["pubDateStart"] = intent.pub_date_start
    if intent.pub_date_end:
        query["pubDateEnd"] = intent.pub_date_end
    return query


async def fetch_tender_list(intent: IntentParams) -> tuple[list[dict[str, Any]], bool]:
    if SETTINGS.qcc_use_mock:
        data = json.loads(_mock_file().read_text(encoding="utf-8"))
        return data.get("Result", {}).get("Data", []), True

    headers = _build_headers()
    all_rows: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=SETTINGS.qcc_timeout_seconds) as client:
        for keyword in intent.keywords:
            params = _to_query(intent=intent, keyword=keyword)
            resp = await client.get(GET_LIST_URL, params=params, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
            rows = payload.get("Result", {}).get("Data", []) or []
            all_rows.extend(rows)
    return all_rows, False


async def fetch_tender_detail(tender_id: str) -> dict[str, Any]:
    if SETTINGS.qcc_use_mock:
        return {"Result": {"Data": {"Content": "mock detail content"}}}
    headers = _build_headers()
    params = {"key": SETTINGS.qcc_app_key, "id": tender_id}
    async with httpx.AsyncClient(timeout=SETTINGS.qcc_timeout_seconds) as client:
        resp = await client.get(GET_DETAIL_URL, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()

