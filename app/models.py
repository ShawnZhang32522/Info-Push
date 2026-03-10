from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    user_input: str = Field(..., description="Natural language query from Openclaw")
    page_index: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=20)
    include_detail: bool = False


class IntentParams(BaseModel):
    keywords: list[str]
    area_code: str | None = None
    city: str | None = None
    pub_date_start: str | None = None
    pub_date_end: str | None = None
    msg_type: str | None = None
    page_index: int = 1
    page_size: int = 10
    admin_only: bool = True


class TenderItem(BaseModel):
    id: str
    title: str
    project_no: str | None = None
    province: str | None = None
    city: str | None = None
    publish_date: str | None = None
    content_url: str | None = None
    bid_invi_unit_list: list[dict[str, Any]] = Field(default_factory=list)
    bid_progress_list: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    is_admin_entity: bool = False


class QueryResponse(BaseModel):
    summary: str
    parsed_intent: IntentParams
    total: int
    records: list[TenderItem]
    used_mock: bool

