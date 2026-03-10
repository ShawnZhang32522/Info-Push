from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.filtering import normalize_and_filter
from app.intent import parse_intent
from app.models import QueryRequest, QueryResponse
from app.qcc_client import fetch_tender_detail, fetch_tender_list

app = FastAPI(title="Openclaw Tender Query Service", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/tender/query", response_model=QueryResponse)
async def tender_query(req: QueryRequest) -> QueryResponse:
    intent = await parse_intent(
        user_input=req.user_input,
        page_index=req.page_index,
        page_size=req.page_size,
    )

    try:
        rows, used_mock = await fetch_tender_list(intent=intent)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"QCC list request failed: {exc}") from exc

    filtered = normalize_and_filter(rows=rows, intent=intent)

    if req.include_detail and filtered:
        try:
            detail = await fetch_tender_detail(filtered[0].id)
            content = (
                detail.get("Result", {})
                .get("Data", {})
                .get("Content", "")
            )
            if content:
                filtered[0].title = f"{filtered[0].title}（含详情）"
        except Exception:
            pass

    summary = (
        f"共检索 {len(rows)} 条，筛选后 {len(filtered)} 条。"
        f"地区：{intent.city or '未指定'}；关键词：{'、'.join(intent.keywords)}"
    )

    return QueryResponse(
        summary=summary,
        parsed_intent=intent,
        total=len(filtered),
        records=filtered,
        used_mock=used_mock,
    )


@app.get("/api/tender/query", response_model=QueryResponse)
async def tender_query_get(
    user_input: str,
    page_index: int = 1,
    page_size: int = 10,
    include_detail: bool = False,
) -> QueryResponse:
    req = QueryRequest(
        user_input=user_input,
        page_index=page_index,
        page_size=page_size,
        include_detail=include_detail,
    )
    return await tender_query(req)
