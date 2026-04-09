# picowiki-skills

Claude Code skills for personal knowledge management and API integration.

## Skills Overview

| Skill | Purpose | Key Operations |
|-------|---------|---------------|
| `llm-wiki` | Obsidian vault knowledge base following Karpathy's LLM Wiki pattern | ingest, query, lint |
| `mptext-api` | WeChat public account article exporter API integration | search accounts, download articles |
| `mmx-cli` | MiniMax full-modality CLI for AI Agents | video, speech, music, coding |

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
│   ├── concepts/     # 概念/主题页
│   ├── entities/     # 人物/组织/技术实体页
│   └── comparisons/  # 分析与综合
├── output/           # 查询结果与报告
├── SCHEMA.md         # LLM 行为规则
├── index.md          # 内容目录
└── log.md            # 操作日志（仅追加）
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

## mmx-cli

MiniMax MMX-CLI — 面向 AI Agent 的全模态命令行工具。

**项目地址**：https://github.com/MiniMax-AI/cli

### What it does

Agent 天然适合命令行模式（执行命令 → 拿到结果），MiniMax 将全模态能力通过 CLI 暴露给 Agent，无需适配接口、无需编写 MCP Server。

核心价值：Agent 可独立完成完整工作流
> 资料搜集 → 生成文案 → 合成语音旁白 → 配图配乐 → 视频制作

### 安装

```bash
pip install mmx-cli
# 或
npm install -g mmx-cli
```

需要设置环境变量 `MINIMAX_API_KEY`。Token Plan：https://platform.minimax.com/subscribe/token-plan

### Agent 优化设计

| 特性 | 说明 |
|------|------|
| **输出隔离** | 进度条/彩色字符 → stderr；stdout 仅输出干净的文件路径或 JSON |
| **语义化 Exit Code** | 失败时返回数字代号（1=通用错误, 2=鉴权失败, 3=参数错误, 4=超时, 5=网络异常），Agent 无需解析英文报错 |
| **非阻塞/异步** | 参数缺失直接报错退出，不傻等输入；`--async` 支持长耗时任务后台执行 |

### 主要命令

```bash
# 视频生成
mmx-cli generate video "a cat playing piano" --duration 10 --output ./video.mp4 --quiet

# 语音合成
mmx-cli generate speech "你好，世界" --voice "female_warm" --output ./speech.mp3

# 音乐创作
mmx-cli generate music "a relaxing jazz piece" --output ./music.mp3

# 编程模型
mmx-cli chat "用 Python 写一个快速排序" --model coding

# Token 用量查询
mmx-cli usage
```

### 完整工作流示例

Agent 自动制作视频介绍：

```bash
# 1. 生成文案
mmx-cli chat "写一段 30 秒产品介绍文案" > script.txt

# 2. 合成语音
SCRIPT=$(cat script.txt)
mmx-cli generate speech "$SCRIPT" --voice "female_pro" --output narration.mp3

# 3. 生成配图视频
mmx-cli generate video "产品功能演示，简洁现代风格" --output visuals.mp4

# 4. 合并（需 ffmpeg）
ffmpeg -i visuals.mp4 -i narration.mp3 -c:v copy -c:a aac final.mp4
```

### 与 MCP Server 对比

| 维度 | MCP Server | MMX-CLI |
|------|------------|---------|
| 接入成本 | 需要编写 Server | 两行安装 |
| 模型覆盖 | 单模型 | 全模态（视频/语音/音乐/编程） |
| Agent 适配 | 需二次开发 | 原生支持 |
| 交互模式 | Request/Response | 命令行 + Exit Code |

### Trigger Keywords

- `/mmx-cli`
- "MiniMax"、"MMX"、"mmx-cli"、"视频生成"
- "语音合成"、"音乐创作"、"全模态"
- "minimax"、"token plan"

---

## Installation

### 完整安装（所有 skills）

```bash
git clone https://github.com/vmxmy/picowiki-skills.git ~/.claude/skills/picowiki-skills
```

### 单独安装某个 skill

```bash
ln -s ~/.claude/skills/picowiki-skills/llm-wiki ~/.claude/skills/llm-wiki
ln -s ~/.claude/skills/picowiki-skills/mptext-api ~/.claude/skills/mptext-api
ln -s ~/.claude/skills/picowiki-skills/mmx-cli ~/.claude/skills/mmx-cli
```

### 更新

```bash
cd ~/.claude/skills/picowiki-skills && git pull
```

---

## License

Personal use. No license for redistribution.
