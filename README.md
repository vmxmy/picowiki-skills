# picowiki-skills

Claude Code skills for personal knowledge management and API integration.

## Skills Overview

| Skill | Purpose | Key Operations |
|-------|---------|---------------|
| `llm-wiki` | Obsidian vault knowledge base following Karpathy's LLM Wiki pattern | ingest, query, lint |
| `mptext-api` | WeChat public account article exporter API integration | search accounts, download articles |

---

## llm-wiki

Karpathy's LLM Wiki pattern — a persistent, compounding knowledge base built on an Obsidian vault.

### What it does

LLM 对知识库进行增量维护：读取原始文档 → 生成摘要卡片 → 提炼概念/实体页 → 更新索引。与 RAG 不同，这是持久化的知识积累，而非每次查询的临时检索。

### Three-Layer Architecture

```
vault/
├── raw/              # 不可变原始文档（LLM 只读）
├── wiki/
│   ├── sources/      # 每篇来源的摘要卡片
│   ├── concepts/    # 概念/主题页
│   ├── entities/    # 人物/组织/技术实体页
│   └── comparisons/ # 分析与综合
├── output/          # 查询结果与报告
├── SCHEMA.md        # LLM 行为规则
├── index.md         # 内容目录
└── log.md           # 操作日志（仅追加）
```

### Operations

| Operation | Trigger | Description |
|-----------|---------|-------------|
| **Ingest** | `/llm-wiki ingest <文章/文档>` | 读取来源 → 生成摘要卡片 → 更新概念/实体页 → 追加日志 |
| **Query** | `/llm-wiki query <问题>` | 搜索相关页 → 综合答案 → 写入 output/ 并返回 |
| **Lint** | `/llm-wiki lint` | 检查断链、孤儿页、过时内容、frontmatter 一致性 |
| **Init** | `/llm-wiki init [vault路径]` | 初始化完整三层架构 |

### Vault Auto-Detection

Skill 会按以下顺序检测 Obsidian vault 路径：
1. 读取 Obsidian 配置文件 `obsidian.json` 中的 vault 路径
2. 遍历常见位置查找包含 `.obsidian` 配置的目录
3. iCloud 路径：`~/Library/Mobile Documents/com~apple~CloudDocs/Documents/`

### Trigger Keywords

- `/llm-wiki`
- "知识库"、"LLM wiki"、"ingest"、"Obsidian"
- "导入文档"、"构建知识库"、"知识管理"

### Frontmatter Standard

```yaml
---
type: source        # source | concept | entity
title: "标题"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [标签1, 标签2]
sources:
  - "[[wiki/sources/来源页]]"
---
```

---

## mptext-api

微信公众号文章导出 API（https://down.mptext.top）集成工具。

### What it does

通过 mptext API 搜索公众号、获取文章列表、下载文章内容（html/markdown/text/json 格式）。

### API Endpoints

| # | Endpoint | Auth | Description |
|---|----------|------|-------------|
| 1 | `/api/public/v1/account` | 需要 | 按关键字搜索公众号 |
| 2 | `/api/public/v1/accountbyurl` | 需要 | 通过文章链接查询公众号 |
| 3 | `/api/public/v1/article` | 需要 | 获取公众号历史文章列表 |
| 4 | `/api/public/v1/download` | **不需要** | 下载文章内容 |
| 5 | `/api/public/beta/authorinfo` | **不需要** | 查询公众号主体信息 |
| 6 | `/api/public/beta/aboutbiz` | 需要 | 查询公众号主体信息（高级） |

### Authentication

需要认证的接口（1, 2, 3, 6），通过以下任一方式传递密钥：
- 请求头：`X-Auth-Key: <密钥>`
- Cookie：`auth-key=<密钥>`

密钥与 mptext 网站登录绑定，扫码登录后自动刷新。登录失效后密钥也失效。

### Quick Start

```bash
# 下载文章为 Markdown（无需认证）
curl -G "https://down.mptext.top/api/public/v1/download" \
  --data-urlencode "url=https://mp.weixin.qq.com/s/xxxx" \
  -d "format=markdown"

# 搜索公众号（需要认证）
curl -G "https://down.mptext.top/api/public/v1/account" \
  -H "X-Auth-Key: $AUTH_KEY" \
  -d "keyword=关键词" \
  -d "size=10"
```

### Trigger Keywords

- `/mptext-api`
- "公众号"、"微信文章"、"mptext"、"下载文章"
- "搜索公众号"、"文章导出"、"WeChat article"

---

## Installation

### 完整安装（所有 skills）

```bash
git clone https://github.com/vmxmy/picowiki-skills.git ~/.claude/skills/picowiki-skills
```

### 单独安装某个 skill

```bash
# llm-wiki
ln -s ~/.claude/skills/picowiki-skills/llm-wiki ~/.claude/skills/llm-wiki

# mptext-api
ln -s ~/.claude/skills/picowiki-skills/mptext-api ~/.claude/skills/mptext-api
```

### 更新

```bash
cd ~/.claude/skills/picowiki-skills && git pull
```

---

## License

Personal use. No license for redistribution.
