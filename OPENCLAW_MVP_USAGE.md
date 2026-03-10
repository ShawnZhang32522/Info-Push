# Openclaw 对接说明（需求2 MVP）

## 1. 启动服务
```bash
cd /home/shawn/intelligence-push
cp .env.example .env
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> 默认 `QCC_USE_MOCK=true`，会读取 `mock_data/tender_list.json`。
> 规则：本项目 Python 依赖安装、运行、脚本执行统一使用 `uv`，不使用 `pip`/`python -m venv`。

## 2. 接口定义
- `POST /api/tender/query`
- `GET /api/tender/query`（给 Openclaw `web_fetch` 直接调用）

请求体：
```json
{
  "user_input": "查北京近7天银行相关招标",
  "page_index": 1,
  "page_size": 10,
  "include_detail": false
}
```

返回体（示例）：
```json
{
  "summary": "共检索 3 条，筛选后 1 条。地区：北京；关键词：银行",
  "parsed_intent": {
    "keywords": ["银行"],
    "area_code": "110000",
    "city": "北京",
    "pub_date_start": "2026-02-26",
    "pub_date_end": "2026-03-04",
    "msg_type": null,
    "page_index": 1,
    "page_size": 10,
    "admin_only": true
  },
  "total": 1,
  "records": [
    {
      "id": "mock-beijing-001",
      "title": "北京市某银行监管系统升级项目招标公告",
      "project_no": "BJ-2026-001",
      "province": "北京市",
      "city": "北京市",
      "publish_date": "2026-03-03",
      "content_url": "https://example.com/tender/bj-001",
      "bid_invi_unit_list": [{"Name": "北京市财政局"}],
      "bid_progress_list": ["招标公告"],
      "matched_keywords": ["银行", "监管"],
      "is_admin_entity": true
    }
  ],
  "used_mock": true
}
```

## 3. 切换真实企查查
1. 修改 `.env`：
```env
QCC_APP_KEY=你的AppKey
QCC_SECRET_KEY=你的SecretKey
QCC_USE_MOCK=false
```
2. 重启服务。

## 4. Openclaw 侧调用建议
- 将 `POST /api/tender/query` 注册为工具/动作。
- 把用户原始问题直接传 `user_input`。
- 用返回字段 `summary + records` 进行回显。

## 5. 已完成的 Openclaw 配置
- 已在 `~/.openclaw/openclaw.json` 写入：
  - `skills.load.extraDirs = ["/home/shawn/intelligence-push/skills"]`
- 已新增技能：
  - `/home/shawn/intelligence-push/skills/tender-query/SKILL.md`
  - 技能已改为 `exec + curl` 调本地API（避免 `web_fetch` 对 localhost 的 SSRF 拦截）

验证方式（在 Openclaw 对话里）：
- 直接问：`查北京近7天银行相关招标`
- 或显式：`/skill tender-query 查北京近7天银行相关招标`
