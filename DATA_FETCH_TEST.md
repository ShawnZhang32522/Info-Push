# Data Fetch Test Guide

This document explains how to reproduce the data acquisition process for the **Info-Push project**.

The goal is to obtain structured information from government websites, including:

- title
- publish time
- source
- url

These data will later be pushed to the user side after keyword filtering.

---

# 1 Data Acquisition Method

The main workflow:

1. Open the target website
2. Use Chrome DevTools to capture network requests
3. Identify the real search API
4. Reproduce the request using Postman
5. Parse returned JSON to extract:
    - title
    - content
    - url

---

# 2 Tianjin Finance Bureau

Target website:

https://cz.tj.gov.cn/zwgk_53713/

This website belongs to the **Tianjin Finance Bureau**, a government department responsible for fiscal management in Tianjin.  [oai_citation:0‡维基百科](https://zh.wikipedia.org/wiki/%E5%A4%A9%E6%B4%A5%E5%B8%82%E8%B4%A2%E6%94%BF%E5%B1%80?utm_source=chatgpt.com)

---

## 2.1 Capture Request

Steps:

1. Open the website
2. Press **F12**
3. Open **Network**
4. Select **Fetch/XHR**
5. Enter keyword (example: 银行)

Find request:https://cz.tj.gov.cn/igs/front/search.jhtml
Request method:GET
---

## 2.2 Request Parameters

Example request:GET https://cz.tj.gov.cn/igs/front/search.jhtml
Query Params:

| Param | Example | Description |
|------|------|------|
| code | auto-generated | search session id |
| pageSize | 10 | results per page |
| queryAll | true | search all fields |
| searchWord | 银行 | keyword |
| siteId | 42 | site identifier |

Example full request:https://cz.tj.gov.cn/igs/front/search.jhtml?code=xxxx&pageSize=10&queryAll=true&searchWord=银行&siteId=42
---

## 2.3 Response Example

The API returns JSON data.

Example structure:

```json
{
 "page": {
  "content": [
   {
    "title": "天津市民族贸易和民族特需商品生产贷款贴息怎么申请？",
    "trs_time": "2024-12-30",
    "trs_site": "天津市财政局",
    "url": "https://cz.tj.gov.cn/..."
   }
  ]
 }
}
2.4 Extract Fields

Important fields:
    Field                   Meaning
    title               article title
    trs_time             publish date
    trs_site                 source
    url                    article link
    content                  summary
# 3 Tianjin Financial Work Committee

Target website:https://jrgz.tj.gov.cn/xxfb/tzggl_1/
## 3.1 Capture Request

Steps:
	1.	Open the site
	2.	Press F12
	3.	Go to Network
	4.	Select Fetch/XHR
Find request:https://jrgz.tj.gov.cn/igs/front/search.jhtml
Request method:GET
## 3.2 Request Parameters

Example:https://jrgz.tj.gov.cn/igs/front/search.jhtml

Params:
Param                    Example
code                    session id
pageSize                    10
queryAll                   true
searchWord                  银行
siteId                       36
Example request:https://jrgz.tj.gov.cn/igs/front/search.jhtml?code=xxxx&pageSize=10&queryAll=true&searchWord=银行&siteId=36

##  3.3 Response Structure

Example JSON:
{
 "page": {
  "content":[
   {
    "title":"通知公告标题",
    "trs_time":"2024-03-01",
    "url":"https://jrgz.tj.gov.cn/xxx.html"
   }
  ]
 }
}
# 4 Article Detail

Each search result contains a URL.

Example:https://jrgz.tj.gov.cn/xxfb/tzggl_l/202403/t20240301_123456.html
Request method:GET
Return:

HTML page containing the full article content.

# 5 Data Processing Strategy

Final extracted data format:
{
 title: "",
 publish_time: "",
 source: "",
 url: ""
}
Example:
{
 title: "天津市预算单位银行账户管理办法的通知",
 publish_time: "2013-03-11",
 source: "天津市财政局",
 url: "https://cz.tj.gov.cn/..."
}
# 6 Keyword Filtering

The project monitors multiple institutions:
	•	People’s Bank branches
	•	Financial regulatory authorities
	•	Finance bureau
	•	financial committees

Keywords:
银行
存款
资质
资格
监管
现金
Only articles containing these keywords will be pushed to users.
# 7 Summary

The data acquisition process is:
Website
   ↓
Network capture
   ↓
Search API
   ↓
Postman test
   ↓
Parse JSON
   ↓
Extract title + url
   ↓
Push to system


git branch
git branch
