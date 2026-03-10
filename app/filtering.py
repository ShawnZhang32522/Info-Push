from __future__ import annotations

import re

from app.models import IntentParams, TenderItem

ALLOWED_CITIES = {"天津", "成都", "北京", "上海", "济南", "石家庄"}
ADMIN_PATTERNS = [
    r"人民政府",
    r"财政局",
    r"教育局",
    r"卫生健康",
    r"公安局",
    r"人力资源和社会保障",
    r"行政",
    r"事业单位",
    r"管理局",
    r"委员会",
    r"中心",
    r"医院",
    r"学校",
]


def _unit_name(item: dict) -> str:
    first = (item.get("BidInviUnitList") or [])
    if not first:
        return ""
    return first[0].get("Name", "") or ""


def _is_admin_entity(name: str) -> bool:
    if not name:
        return False
    return any(re.search(p, name) for p in ADMIN_PATTERNS)


def _matched_keywords(title: str, keywords: list[str]) -> list[str]:
    return [k for k in keywords if k in (title or "")]


def _city_pass(city: str | None) -> bool:
    if not city:
        return False
    return any(allowed in city for allowed in ALLOWED_CITIES)


def normalize_and_filter(rows: list[dict], intent: IntentParams) -> list[TenderItem]:
    result: list[TenderItem] = []
    seen: set[tuple[str, str, str]] = set()

    for row in rows:
        title = row.get("Title", "") or ""
        city = row.get("City")
        publish_date = row.get("PublishDate", "") or ""
        content_url = row.get("ContentUrl", "") or ""
        unit_name = _unit_name(row)
        is_admin = _is_admin_entity(unit_name)
        matched = _matched_keywords(title, intent.keywords)

        if not _city_pass(city):
            continue
        if not matched:
            continue
        if intent.admin_only and not is_admin:
            continue

        dedup_key = (title.strip(), publish_date.strip(), content_url.strip())
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        result.append(
            TenderItem(
                id=row.get("Id", ""),
                title=title,
                project_no=row.get("ProjectNo"),
                province=row.get("Province"),
                city=city,
                publish_date=publish_date,
                content_url=content_url,
                bid_invi_unit_list=row.get("BidInviUnitList", []),
                bid_progress_list=row.get("BidProgressList", []),
                matched_keywords=matched,
                is_admin_entity=is_admin,
            )
        )

    result.sort(key=lambda x: x.publish_date or "", reverse=True)
    return result

