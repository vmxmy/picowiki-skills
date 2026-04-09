---
name: mmx-cli
description: MiniMax MMX-CLI tool — full-modality CLI for AI Agents. Use when integrating MiniMax models (video generation, TTS, music, programming) into Claude Code, OpenClaw, or other agent runtimes. Triggers on: "MiniMax", "MMX", "mmx-cli", "视频生成", "语音合成", "音乐创作", "全模态", "minimax", "token plan".
---

# mmx-cli

MiniMax MMX-CLI — 面向 AI Agent 的全模态命令行工具，支持视频生成、语音合成、音乐创作、编程模型。

**项目地址**：https://github.com/MiniMax-AI/cli

## 核心价值

Agent 天然适合命令行模式（执行命令 → 拿到结果），MiniMax 将全模态能力通过 CLI 暴露给 Agent，无需适配接口、无需编写 MCP Server。

Agent 可独立完成完整工作流：
> 资料搜集 → 生成文案 → 合成语音旁白 → 配图配乐 → 视频制作

## 安装

```bash
pip install mmx-cli
# 或
npm install -g mmx-cli
```

## Token Plan

MMX-CLI 无缝接入 [MiniMax Token Plan](https://platform.minimax.com/subscribe/token-plan)，可显示套餐用量。

## Agent 优化设计

MMX-CLI 针对 Agent 自动化场景的专门优化：

### 1. 输出隔离与纯数据模式

- 进度条、彩色字符等人类友好信息 → **stderr**
- stdout 仅输出干净的文件路径或 JSON 数据
- 配合 `--quiet` + `--output json` 可彻底切断交互式界面

```bash
mmx-cli generate video "prompt" --quiet --output json
```

### 2. 语义化 Exit Code

失败时返回独立数字代号，Agent 无需解析英文报错即可判断错误类型：

| 退出码 | 含义 |
|--------|------|
| 1 | 通用错误 |
| 2 | 鉴权失败 |
| 3 | 参数错误 |
| 4 | 超时 |
| 5 | 网络异常 |

Agent 通过读取 `$?` 即可判断是否重试。

### 3. 非阻塞与异步任务控制

- 参数缺失直接报错退出，不傻等输入
- 长耗时任务用 `--async` 切换后台模式

```bash
# 异步模式
mmx-cli generate video "prompt" --async

# Agent 可同时处理其他任务
```

## 主要命令

### 视频生成

```bash
mmx-cli generate video "a cat playing piano" --duration 10 --output ./video.mp4
```

### 语音合成（TTS）

```bash
mmx-cli generate speech "你好，世界" --voice "female_warm" --output ./speech.mp3
```

### 音乐创作

```bash
mmx-cli generate music "a relaxing jazz piece" --output ./music.mp3
```

### 编程模型

```bash
mmx-cli chat "用 Python 写一个快速排序" --model coding
```

### Token 用量查询

```bash
mmx-cli usage
```

## Claude Code 中使用

通过 Bash 工具直接调用：

```bash
# 视频生成
mmx-cli generate video "产品介绍动画" --output ./output.mp4 --quiet

# 语音旁白
mmx-cli generate speech "今天发布 MMX-CLI" --voice "male_pro" --output ./intro.mp3

# 查看 token 用量
mmx-cli usage
```

## 完整工作流示例

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

## 与 MCP Server 的对比

| 维度 | MCP Server | MMX-CLI |
|------|------------|---------|
| 接入成本 | 需要编写 Server | 两行安装 |
| 模型覆盖 | 单模型 | 全模态（视频/语音/音乐/编程） |
| Agent 适配 | 需二次开发 | 原生支持 |
| 交互模式 | Request/Response | 命令行 + Exit Code |

## 注意事项

- 需要 MiniMax API Key，通过环境变量 `MINIMAX_API_KEY` 设置
- Token Plan 页面：https://platform.minimax.com/subscribe/token-plan
- 视频生成通常需要等待一段时间，建议使用 `--async` 模式
- 退出码语义化设计是核心亮点——充分利用这一特性做重试逻辑
