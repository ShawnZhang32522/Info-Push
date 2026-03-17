from __future__ import annotations

import re
from typing import Any

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/pbc", tags=["pbc"])

BASE_URL = "https://wzdig.pbc.gov.cn/search/pcRender"
PAGE_ID = "c177a85bd02b4114bebebd210809f691"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"


class QueryRequest(BaseModel):
    q: str = Field(..., description="search keyword, e.g. 存款")
    p_no: int = Field(default=1, ge=1, description="page number")
    advtime: int = Field(default=2, ge=0, le=4, description="time filter from site")
    sr: str = Field(default="score desc", description="sort rule")
    include_detail: bool = Field(default=True, description="whether to fetch detail pages")
    max_records: int = Field(default=10, ge=1, le=30, description="max records to return")


class QueryResponse(BaseModel):
    query: str
    total: int
    records: list[dict[str, Any]]


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


async def fetch_search_html(*, q: str, p_no: int, advtime: int, sr: str) -> str:
    params = {"pageId": PAGE_ID}
    headers = {"User-Agent": UA}
    data = {"sr": sr, "advtime": advtime, "pNo": p_no, "q": q}
    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.post(BASE_URL, params=params, headers=headers, data=data)
        resp.raise_for_status()
        return resp.text


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
    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.text


def parse_detail_page(html: str) -> dict[str, str]:
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

    return {
        "title": meta_title or page_title,
        "publish_date": meta_date or page_date,
        "source_site": meta_site,
        "content_preview": content[:1200],
        "extract_strategy": strategy,
    }


@router.post("/search", response_model=QueryResponse)
async def pbc_search(req: QueryRequest) -> QueryResponse:
    html = await fetch_search_html(q=req.q, p_no=req.p_no, advtime=req.advtime, sr=req.sr)
    records = parse_search_results(html)[: req.max_records]

    if req.include_detail:
        enriched: list[dict[str, Any]] = []
        for rec in records:
            try:
                detail_html = await fetch_detail(rec["url"])
                detail = parse_detail_page(detail_html)
            except Exception as exc:
                detail = {"error": str(exc)}
            enriched.append({**rec, "detail": detail})
        records_out: list[dict[str, Any]] = enriched
    else:
        records_out = records

    return QueryResponse(query=req.q, total=len(records_out), records=records_out)

