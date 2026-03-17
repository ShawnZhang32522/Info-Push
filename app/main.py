from __future__ import annotations

from fastapi import FastAPI

from app.pbc import router as pbc_router

app = FastAPI(title="OpenClaw Info Push Service", version="0.1.0")

app.include_router(pbc_router)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
