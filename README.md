# intelligence-push · 招投标情报推送服务

> 一个为 [OpenClaw](https://openclaw.ai) 提供的招投标查询 Skill，覆盖北京、上海、天津、成都、济南、石家庄六个重点城市，支持行政事业单位招标信息的关键词过滤与智能检索。

---

## 目录

- [功能概览](#功能概览)
- [快速开始](#快速开始)
- [在 OpenClaw 中注册此 Skill](#在-openclaw-中注册此-skill)
- [环境变量说明](#环境变量说明)
- [接口文档](#接口文档)
- [切换真实企查查数据](#切换真实企查查数据)
- [项目结构](#项目结构)

---

## 功能概览

- **覆盖地区**：天津、成都、北京、上海、济南、石家庄
- **关键词过滤**：银行、存款、资质、资格、监管、现金
- **数据源**：企查查招投标 API（默认启用 Mock 数据，无需 Key 即可体验）
- **接入方式**：FastAPI 本地服务 + OpenClaw `exec` 工具调用

---

## 快速开始

**前置要求**：已安装 [uv](https://docs.astral.sh/uv/)

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/intelligence-push.git
cd intelligence-push

# 2. 复制环境变量文件（默认使用 Mock 数据，无需填写真实 Key）
cp .env.example .env

# 3. 安装依赖
uv sync

# 4. 启动服务
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

服务启动后，访问 http://127.0.0.1:8000/health 验证是否正常运行。

---

## 在 OpenClaw 中注册此 Skill

### 第一步：确认服务已在本机运行

确保上一步的 `uvicorn` 服务正在运行，监听 `127.0.0.1:8000`。

### 第二步：配置 OpenClaw 加载本项目的 Skills 目录

找到 OpenClaw 的配置文件，默认路径为：

```
~/.openclaw/openclaw.json
```

在配置文件中添加 `skills.load.extraDirs`，指向本仓库的 `skills` 目录：

```json
{
  "skills": {
    "load": {
      "extraDirs": ["/your/path/to/intelligence-push/skills"]
    }
  }
}
```

> 请将 `/your/path/to/intelligence-push` 替换为你实际的仓库克隆路径。
> 如果 `openclaw.json` 中已有其他配置，只需将上述字段合并进去，不要覆盖整个文件。

### 第三步：重启 OpenClaw

保存配置文件后，完全退出并重新启动 OpenClaw，使新的 Skills 目录生效。

### 第四步：开启"允许执行本地命令"权限

此 Skill 通过 `exec` 工具调用本地 `curl` 命令访问服务（原因：OpenClaw 的 `web_fetch` 会拦截对 localhost 的请求）。

在 OpenClaw 设置中，找到并开启：

```
设置 → 安全 → 允许执行本地命令（Allow exec / shell commands）
```

### 第五步：验证 Skill 已加载

在 OpenClaw 对话框中输入以下任一问题，Skill 应自动触发：

```
查北京近7天银行相关招标
```

```
天津最近有哪些存款相关采购项目？
```

```
/skill tender-query 查石家庄的资质审核相关招标
```

如果返回了结构化的招标列表，说明 Skill 注册成功。

---

## 环境变量说明

在项目根目录创建 `.env` 文件（参考 `.env.example`）：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `QCC_USE_MOCK` | `true` | `true` 时读取 Mock 数据，无需真实 Key |
| `QCC_APP_KEY` | 空 | 企查查 AppKey（仅 Mock=false 时需要）|
| `QCC_SECRET_KEY` | 空 | 企查查 SecretKey（仅 Mock=false 时需要）|
| `QCC_TIMEOUT_SECONDS` | `20` | 企查查 API 超时时间（秒）|
| `DEFAULT_PAGE_SIZE` | `10` | 默认每页返回条数 |
| `DEFAULT_DAYS` | `7` | 默认查询最近天数 |
| `LLM_ENABLED` | `false` | 是否启用 LLM 意图增强解析 |
| `LLM_API_URL` | 空 | LLM API 地址（如 OpenAI 兼容接口）|
| `LLM_API_KEY` | 空 | LLM API Key |
| `LLM_MODEL` | 空 | LLM 模型名称 |

---

## 接口文档

服务启动后可访问交互式文档：http://127.0.0.1:8000/docs

### `POST /api/tender/query`

```json
{
  "user_input": "查北京近7天银行相关招标",
  "page_index": 1,
  "page_size": 10,
  "include_detail": false
}
```

**响应示例：**

```json
{
  "summary": "共检索 3 条，筛选后 1 条。地区：北京；关键词：银行",
  "parsed_intent": {
    "keywords": ["银行"],
    "area_code": "110000",
    "city": "北京",
    "pub_date_start": "2026-03-03",
    "pub_date_end": "2026-03-10"
  },
  "total": 1,
  "records": [
    {
      "id": "mock-beijing-001",
      "title": "北京市某银行监管系统升级项目招标公告",
      "province": "北京市",
      "city": "北京市",
      "publish_date": "2026-03-03",
      "content_url": "https://example.com/tender/bj-001",
      "matched_keywords": ["银行", "监管"],
      "is_admin_entity": true
    }
  ],
  "used_mock": true
}
```

### `GET /api/tender/query`

同上，参数通过 Query String 传递，方便直接在浏览器测试：

```
GET /api/tender/query?user_input=北京银行招标&page_size=5
```

---

## 切换真实企查查数据

1. 申请企查查开发者账号，获取 `AppKey` 和 `SecretKey`
2. 修改 `.env`：

```env
QCC_APP_KEY=你的AppKey
QCC_SECRET_KEY=你的SecretKey
QCC_USE_MOCK=false
```

3. 重启服务：

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 项目结构

```
intelligence-push/
├── app/
│   ├── main.py          # FastAPI 路由入口
│   ├── config.py        # 环境变量加载
│   ├── models.py        # Pydantic 数据模型
│   ├── intent.py        # 用户意图解析（关键词 / 地区提取）
│   ├── filtering.py     # 数据过滤与行政事业单位识别
│   └── qcc_client.py    # 企查查 API 客户端
├── skills/
│   └── tender-query/
│       └── SKILL.md     # OpenClaw Skill 定义文件
├── mock_data/
│   └── tender_list.json # Mock 测试数据
├── pyproject.toml       # uv 项目配置
├── .env.example         # 环境变量模板
└── README.md
```

---

## 开发规范

- Python 依赖管理、运行、脚本执行统一使用 `uv`，不使用 `pip install` / 手工 `venv`。
- Mock 模式下无需任何外部账号，适合本地开发和演示。
