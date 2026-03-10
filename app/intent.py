from __future__ import annotations

import json
import re
from datetime import date, timedelta

import httpx

from app.config import SETTINGS
from app.models import IntentParams

CITY_TO_CODE = {
    "北京": "110000",
    "上海": "310000",
    "天津": "120000",
    "成都": "510100",
    "济南": "370100",
    "石家庄": "130100",
}

DEFAULT_KEYWORDS = ["银行", "存款", "资质", "资格", "监管", "现金"]
MSG_TYPE_MAP = {
    "招标": "3",
    "招标公告": "3",
    "中标": "4",
    "中标公告": "4",
}


def _date_window(days: int) -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


def _parse_days(text: str) -> int | None:
    m = re.search(r"近\s*(\d+)\s*天", text)
    if not m:
        return None
    return max(1, int(m.group(1)))


def _parse_city(text: str) -> tuple[str | None, str | None]:
    for city, code in CITY_TO_CODE.items():
        if city in text:
            return city, code
    return None, None


def _parse_keywords(text: str) -> list[str]:
    found = [k for k in DEFAULT_KEYWORDS if k in text]
    if found:
        return found
    custom = re.findall(r"关键词[:：]\s*([^\n]+)", text)
    if custom:
        return [x for x in re.split(r"[,\s，]+", custom[0].strip()) if x]
    return DEFAULT_KEYWORDS[:2]


def _parse_msg_type(text: str) -> str | None:
    for k, v in MSG_TYPE_MAP.items():
        if k in text:
            return v
    return None


async def _llm_parse(user_input: str, page_index: int, page_size: int) -> IntentParams | None:
    if not (SETTINGS.llm_enabled and SETTINGS.llm_api_url and SETTINGS.llm_model):
        return None
    prompt = (
        "You are a query parser for Chinese tender search. "
        "Return ONLY JSON with keys: keywords(list[str]), city, area_code, "
        "pub_date_start(YYYY-MM-DD), pub_date_end(YYYY-MM-DD), msg_type(3 or 4 or null), admin_only(bool). "
        f"User input: {user_input}"
    )
    headers = {"Content-Type": "application/json"}
    if SETTINGS.llm_api_key:
        headers["Authorization"] = f"Bearer {SETTINGS.llm_api_key}"
    body = {
        "model": SETTINGS.llm_model,
        "messages": [
            {"role": "system", "content": "Output strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(SETTINGS.llm_api_url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return None

    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        parsed["page_index"] = page_index
        parsed["page_size"] = page_size
        return IntentParams.model_validate(parsed)
    except Exception:
        return None


async def parse_intent(user_input: str, page_index: int, page_size: int) -> IntentParams:
    llm_result = await _llm_parse(user_input=user_input, page_index=page_index, page_size=page_size)
    if llm_result is not None:
        return llm_result

    days = _parse_days(user_input) or SETTINGS.default_days
    start, end = _date_window(days)
    city, area_code = _parse_city(user_input)
    keywords = _parse_keywords(user_input)
    msg_type = _parse_msg_type(user_input)

    return IntentParams(
        keywords=keywords,
        city=city,
        area_code=area_code,
        pub_date_start=start,
        pub_date_end=end,
        msg_type=msg_type,
        page_index=page_index,
        page_size=page_size,
        admin_only=True,
    )

