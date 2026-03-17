# intelligence-push

面向 OpenClaw 的本地检索服务：接收关键词 `q`，查询中国人民银行检索页，解析列表页与详情页，并返回结构化 JSON，供后续 LLM 总结使用。

## 功能

- 接口：`POST /api/pbc/search`
- 入参核心字段：`q`（关键词）
- 自动解析：
  - 列表字段：`title`、`url`、`publish_date`、`snippet`
  - 详情字段：`detail.title`、`detail.publish_date`、`detail.source_site`、`detail.content_preview`
- 可选开关：`include_detail=true/false`

## 快速启动

```bash
git clone https://github.com/ShawnZhang32522/Info-Push.git
cd Info-Push
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

启动后访问：

- 健康检查：`http://127.0.0.1:8000/health`
- Swagger：`http://127.0.0.1:8000/docs`

## API 说明

### `POST /api/pbc/search`

请求体示例：

```json
{
  "q": "存款",
  "p_no": 1,
  "advtime": 2,
  "sr": "score desc",
  "include_detail": true,
  "max_records": 10
}
```

字段说明：

- `q`：搜索关键词（必填）
- `p_no`：页码，默认 `1`
- `advtime`：时间范围，默认 `2`（站点筛选值）
- `sr`：排序，默认 `score desc`
- `include_detail`：是否抓取详情页并解析，默认 `true`
- `max_records`：最多返回几条，默认 `10`，最大 `30`

返回体（节选）：

```json
{
  "query": "存款",
  "total": 2,
  "records": [
    {
      "title": "2026年中央国库现金管理商业银行定期存款（三期）招投标通知",
      "url": "https://www.pbc.gov.cn/...",
      "publish_date": "2026年03月16日",
      "snippet": "2026年中央国库现金管理商业银行定期存款（三期）招投标",
      "detail": {
        "title": "2026年中央国库现金管理商业银行定期存款（三期）招投标通知",
        "publish_date": "2026-03-16",
        "source_site": "货币政策司",
        "content_preview": "....",
        "extract_strategy": "meta_description"
      }
    }
  ]
}
```

## OpenClaw 接入方式

在 OpenClaw 中通过 `exec` 调用本地 API（不要用 `web_fetch` 访问 localhost）：

```bash
curl -sS -X POST "http://127.0.0.1:8000/api/pbc/search" \
  -H "Content-Type: application/json" \
  -d '{"q":"<USER_QUERY>","p_no":1,"advtime":2,"sr":"score desc","include_detail":true,"max_records":10}'
```

建议参数映射：

- OpenClaw 从用户问题提取核心关键词，写入 `q`
- 固定 `include_detail=true`，确保拿到 `detail.content_preview`
- 后续 LLM 总结时，重点使用：
  - `records[*].title`
  - `records[*].publish_date`
  - `records[*].detail.source_site`
  - `records[*].detail.content_preview`

## 项目结构

```text
intelligence-push/
  app/
    main.py
  scripts/
    fetch_pbc.py
  skills/
    tender-query/
      SKILL.md
  README.md
```

## 说明

- 当前版本仅完成“检索 + 结构化返回”。
- 你可以在 OpenClaw 里先完成参数解析与接口调用，再把返回结果交给 LLM 做总结。
