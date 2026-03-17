from __future__ import annotations

import asyncio
import json
import re

import httpx

BASE_URL = "https://wzdig.pbc.gov.cn/search/pcRender"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"


async def fetch_raw_html() -> str:
    params = {"pageId": "c177a85bd02b4114bebebd210809f691"}
    headers = {"User-Agent": UA}
    data = {"sr": "score desc", "advtime": 2, "pNo": 1, "q": "存款"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(BASE_URL, params=params, headers=headers, data=data)
        return resp.text


def _strip_tags(text: str) -> str:
    no_tags = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", no_tags).strip()


def _meta_content(html: str, name: str) -> str:
    match = re.search(
        rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\'](.*?)["\']',
        html,
        flags=re.S | re.I,
    )
    return _strip_tags(match.group(1)) if match else ""


def _extract_longest_text_block(html: str) -> str:
    cleaned = re.sub(r"<script.*?>.*?</script>", " ", html, flags=re.S | re.I)
    cleaned = re.sub(r"<style.*?>.*?</style>", " ", cleaned, flags=re.S | re.I)
    cleaned = re.sub(r"<noscript.*?>.*?</noscript>", " ", cleaned, flags=re.S | re.I)
    text = _strip_tags(cleaned)
    chunks = re.split(r"[。！？\n\r]+", text)
    chunks = [c.strip() for c in chunks if len(c.strip()) >= 40]
    if not chunks:
        return ""
    return max(chunks, key=len)


def _quality_score(content: str) -> int:
    length = len(content)
    if length >= 1500:
        return 95
    if length >= 800:
        return 85
    if length >= 300:
        return 70
    if length >= 120:
        return 55
    if length >= 40:
        return 35
    return 10


def parse_search_results(html: str) -> list[dict[str, str]]:
    blocks = re.findall(
        r'<div class="searchMod">\s*<div class="news-style1">(.*?)</div>\s*</div>',
        html,
        flags=re.S,
    )
    records: list[dict[str, str]] = []
    for block in blocks:
        h3_match = re.search(
            r"<h3>\s*<a[^>]*href=\"(?P<url>[^\"]+)\"[^>]*appId=\"(?P<app_id>[^\"]+)\"[^>]*>(?P<title>.*?)</a>",
            block,
            flags=re.S,
        )
        snippet_match = re.search(
            r'<p class="txtCon[^"]*">\s*(?P<snippet>.*?)\s*</p>',
            block,
            flags=re.S,
        )
        date_match = re.search(
            r"<p class=\"dates\">.*?<span>\s*(?P<date>\d{4}年\d{2}月\d{2}日)\s*</span>",
            block,
            flags=re.S,
        )
        if not h3_match:
            continue
        records.append(
            {
                "title": _strip_tags(h3_match.group("title")),
                "url": h3_match.group("url").strip(),
                "app_id": h3_match.group("app_id").strip(),
                "snippet": _strip_tags(snippet_match.group("snippet")) if snippet_match else "",
                "publish_date": date_match.group("date").strip() if date_match else "",
            }
        )
    return records


async def fetch_detail(url: str) -> str:
    headers = {"User-Agent": UA}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, headers=headers)
        return resp.text


def parse_detail_page(html: str) -> dict[str, str | int]:
    meta_title = _meta_content(html, "ArticleTitle")
    meta_date = _meta_content(html, "PubDate")
    meta_desc = _meta_content(html, "Description")
    meta_site = _meta_content(html, "SiteName")

    title_match = re.search(r"<title>\s*(.*?)\s*</title>", html, flags=re.S | re.I)
    page_title = _strip_tags(title_match.group(1)) if title_match else ""
    date_match = re.search(r"(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}日?)", html)
    page_date = date_match.group(1) if date_match else ""

    strategy = "meta_description"
    content = meta_desc

    if len(content) < 80:
        zoom_match = re.search(
            r'<div[^>]+id=["\']zoom["\'][^>]*>(.*?)</div>',
            html,
            flags=re.S | re.I,
        )
        if zoom_match:
            content = _strip_tags(zoom_match.group(1))
            strategy = "zoom_div"

    if len(content) < 80:
        article_match = re.search(
            r'<div[^>]+class="[^"]*(?:TRS_Editor|article|content|zoom|news-content)[^"]*"[^>]*>(.*?)</div>',
            html,
            flags=re.S | re.I,
        )
        if article_match:
            content = _strip_tags(article_match.group(1))
            strategy = "article_container"

    if len(content) < 80:
        content = _extract_longest_text_block(html)
        strategy = "fallback_longest_text"

    title = meta_title or page_title
    publish_date = meta_date or page_date
    score = _quality_score(content)

    return {
        "title": title,
        "publish_date": publish_date,
        "source_site": meta_site,
        "content_preview": content[:1200],
        "extract_strategy": strategy,
        "quality_score": score,
    }


async def main() -> None:
    html = await fetch_raw_html()
    records = parse_search_results(html)
    print(f"parsed_records={len(records)}")
    print(json.dumps(records, ensure_ascii=False, indent=2))
    for idx, record in enumerate(records, start=1):
        detail_html = await fetch_detail(record["url"])
        detail = parse_detail_page(detail_html)
        print(f"\n===== DETAIL #{idx} =====")
        print(f"url: {record['url']}")
        print(json.dumps(detail, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

