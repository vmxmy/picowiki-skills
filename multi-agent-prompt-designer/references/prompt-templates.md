# Prompt Templates

Use this file when drafting the final PicoClaw-facing runtime prompt.

These are templates, not rigid forms.
Start from one template, then adapt it to the user's goal.

## Doctor Add-On Block

Insert this block near the beginning of most PicoClaw mission prompts.

```text
环境检查要求：
- 第一阶段不要直接启动完整任务。
- 先运行一次 doctor 式环境检查，确认当前本地可用能力。

至少检查以下三类：
1. MCP
- 当前已配置、已启用、可达的 MCP 能力
- 哪些 MCP 是缺失的、不可达的、或需要延迟发现的

2. CLI
- 当前机器上已安装、可执行的本地 CLI 工具
- 哪些 CLI 可以直接作为专门源接入路径

3. Skills
- 当前已安装的 skills
- 哪些 skills 可以补足信息源、平台接入或任务执行能力

- doctor 阶段完成后，必须把结论写入 `SPEC.md` 和 `STATUS.json`。
- 在 doctor 没确认之前，不要假设某个 MCP、CLI 或 skill 一定可用。
```

## Shared Tracking Block

Insert this block into most final prompts.

```text
任务追踪要求：
- 请先创建任务目录：
  workspace/tasks/<task-slug>-<timestamp>/

- 必须创建并维护以下文件：
  - SPEC.md
  - STATUS.json
  - EXECUTION_LOG.md
  - RESULTS.tsv
  - AGENTS/<agent-name>.md
  - FINAL/report.md

- `SPEC.md` 必须作为人类可读的任务规范和分解主文档，包含：
  - 任务目标
  - 约束
  - agent 分工
  - phase 划分
  - task decomposition 表
  - success criteria
  - failure handling
  - current status

- `STATUS.json` 必须作为机器可读状态板，记录：
  - 当前 phase
  - 每个 agent 的状态
  - 已完成 / 失败 / 超时数量
  - 最近更新时间
  - 每个 agent 的 `restart_count`
  - 每个 agent 的 `last_heartbeat` 或最近进度时间戳（若适用）

- 主线程 / 协调者必须作为 watchdog 定时检查任务和 agent 状态：
  - 优先使用 PicoClaw 内置的 `cron` 和 `heartbeat` 机制作为 watchdog tick 来源
  - 按固定间隔巡检整体状态和每个 agent 的状态
  - 对 child work 优先按 PicoClaw 的 `spawn` / `SubTurn` / `spawn_status` / `EventBus` 语义来判断健康度
  - 如果发现 agent 失败、超时或长时间无进展，则尝试重启
  - 需要 deferred follow-up 时，优先用 `steering` 和 `Continue()` 驱动恢复而不是发明外部控制面
  - 每次重启都必须记录到 `EXECUTION_LOG.md` 和 `STATUS.json`
  - 继续巡检与恢复，直到所有必需任务完成或达到不可恢复条件
  - 不要让 watchdog 连续性依赖于单次 LLM API 调用是否成功

- 每个 agent 完成后必须：
  1. 回写自己的 `AGENTS/<agent-name>.md`
  2. 向 `EXECUTION_LOG.md` 追加一条执行记录
  3. 更新 `STATUS.json`
  4. 向 `RESULTS.tsv` 追加一条紧凑结果记录
  5. 在适当的时候通知用户其完成情况或阶段结果

- `RESULTS.tsv` 应至少记录：
  - timestamp
  - agent
  - task_id
  - attempt
  - status
  - keep_or_discard
  - artifact
  - summary

- 如果协调者发现无法解决的故障，必须：
  - 停止任务
  - 在 `STATUS.json` 中标记任务失败或终止
  - 在 `EXECUTION_LOG.md` 中写明故障、已尝试的恢复动作和终止原因
  - 明确通知用户，并给出后续建议或缓解措施

- 协调者必须在以下节点通知用户：
  - 任务已启动
  - 第一批 agent 已启动
  - 每个 phase 完成
  - 出现重大失败、重复重启或严重阻塞
  - 最终报告已完成
  - 任务因不可恢复故障而停止
```

## Reconnaissance Add-On Block

Insert this block when the full mission should be informed by a small first-wave research pass.

```text
前置调研要求：
- 在设计和启动完整任务前，先设计并执行若干小型调研任务。
- 这些调研任务的目标不是完成主任务，而是为主任务收集设计所需的信息。
- 调研任务应尽量小、快、低风险、高信息密度。
- 调研阶段必须先建立 baseline，并在进入完整任务前做 `advance` / `discard` 决策。

建议至少包含以下几类小任务：
1. 工具面调研
- 检查当前可用工具、关键能力、是否存在状态查询、通知、内置 `cron`、内置 `heartbeat` 机制
- 检查是否已配置多个搜索源、`web_fetch`、`spawn_status`、`send_file`、`MCP`、`skills` / `find_skills`

2. 运行时约束调研
- 检查并发上限、时间预算、可能的卡死点、重启策略约束
- 给出建议的最大并发 agent 数量区间，供用户确认

3. 信息源质量调研
- 快速比较几个候选来源或工作流，识别高价值源与噪声源
- 明确哪些来源可通过 PicoClaw built-ins 访问，哪些需要 MCP，哪些需要 skills，哪些只能作为降级来源
- 对通用 Web 层明确记录：哪些搜索 provider 已启用、哪些 provider 更适合作为主骨干、`web_fetch` 是否可稳定读取全文
- 对 X/Twitter 明确记录：浏览器模式可用、cookie 注入模式可用、或两者都不可用
- 对 YouTube 明确记录：`yt-dlp` 可用、MCP 可用、skill 可用、或仅能降级访问

4. 任务分解调研
- 比较几种 agent 分工方式，判断哪种更独立、更适合并行

5. 风险与故障模式调研
- 识别最可能的失败、超时、阻塞、重复劳动或汇总失控问题

- 每个调研 agent 完成后都必须回写记录。
- 协调者必须汇总调研结果，并先更新 `SPEC.md`，再进入完整任务阶段。
- 协调者必须明确标记哪些方案、来源、分工或策略 `advance`，哪些 `discard`。
- 协调者必须在完整任务启动前，向用户确认最大并发 agent 进程数量。
- 只有在用户确认并发上限后，才允许启动完整任务的主 worker 波次。
- 如果调研结果表明完整任务不可行或风险过高，必须先向用户说明，再决定是否继续。
```

## Research Tooling Add-On Block

Insert this block for long-running research or intelligence tasks.

```text
研究任务工具与信息源要求：
- 在完整任务开始前，先确认当前 PicoClaw 环境是否具备足够的信息采集能力。
- 至少检查以下类别：
  - `web_search`
  - `web_fetch`
  - `heartbeat`
  - `cron`
  - `spawn_status`
  - `send_file`
  - `MCP`
  - `skills` / `find_skills`

- 对依赖当前外部信息的研究任务，优先要求：
  - 至少两个不同风格的搜索源可用，用于交叉验证
  - `web_fetch` 可读取完整页面内容
  - 搜索结果中的高价值条目必须通过 full-page fetch 复核，而不是只看摘要片段
  - `heartbeat` / `cron` 可用于长任务 continuity
  - `spawn_status` 可用于观察子任务
  - `send_file` 可用于交付最终报告

- 如果任务需要 X/Twitter、Reddit、YouTube、Wiki/Wikipedia、行情、财报、数据库等专门信息源：
  - 不要假设 PicoClaw 原生内置支持全部这些源
  - 必须先确认这些源当前是通过 built-ins、MCP、skills 还是 fallback web 方法访问

- 对 X/Twitter，必须明确采用哪种接入模式：
  - 浏览器模式：从已登录浏览器 profile 提取 cookie
  - cookie 注入模式：显式提供 `auth_token` + `ct0`
  - Linux/headless 优先：优先使用 cookie 注入模式，而不是浏览器提取模式
  - 若使用 `bird`，将 `https://bird.fast/` 作为其正式来源记录到 `SPEC.md`

- 对 X/Twitter，必须在 reconnaissance 阶段先做最小可用性验证，例如：
  - 账户识别（whoami）
  - 简单搜索
  - 简单读取

- 对 YouTube，必须明确采用哪种接入模式：
  - `yt-dlp` 模式：本地 CLI 抽取元数据、播放列表、字幕、可用 transcript 线索
  - MCP 模式：通过 transcript/media/server 提供 YouTube 内容能力
  - skill 模式：通过已安装 skill 做 transcript 或内容抓取
  - Linux/headless 优先：优先使用 `yt-dlp` 模式
  - 若使用 `yt-dlp`，将 `https://github.com/yt-dlp/yt-dlp` 作为其正式来源记录到 `SPEC.md`

- 对 YouTube，必须在 reconnaissance 阶段先做最小可用性验证，例如：
  - 读取视频元数据
  - 检查字幕 / transcript 是否可获得
  - 检查 playlist / channel 内容是否可枚举

- 如果关键信息源缺失，协调者必须：
  - 在 `SPEC.md` 中记录缺口
  - 评估是否需要 MCP / skills 扩展
  - 决定任务是否继续、降级或等待补充配置
```

## Template 1: General Multi-Agent Mission

Use for most goals.

```text
开始一个多 agent 协作任务：<TITLE>。

任务目标：
<PRIMARY GOAL>

运行时假设：
- 这是一个 PicoClaw 原生多 agent 运行时。
- 请使用 PicoClaw 的 Heartbeat、cron、spawn/SubTurn、steering、Continue 和消息机制来完成协调、并行执行、验证与汇总。
- 主任务负责分工、时间控制、状态跟踪和最终收敛。

执行原则：
- 优先发现并使用 PicoClaw 当前启用的可用工具，不要假设工具固定存在。
- 尽量并行执行独立工作流。
- 避免重复劳动和范围重叠。
- 主线程必须定时巡检任务和 agent 状态，发现失败或卡死时优先自动恢复。
- 优先用 PicoClaw 内置 `cron` 或 `heartbeat` 保障 watchdog 不因 LLM API 波动而中断。
- 先建立 baseline，再决定完整任务的主策略。
- 对关键来源、分解方式和候选策略做 `advance` / `discard` 决策。
- 使用受限写入面：worker 只写各自作用域文件，共享状态与主规范由协调者维护。
- 允许部分子任务失败，但不允许整体没有最终结果。
- 若存在冲突结论，请显式保留冲突，不要强行统一。
- 若关键故障在重试预算内仍无法恢复，必须停止任务并向用户解释原因和建议。

<INSERT DOCTOR ADD-ON BLOCK>

<INSERT SHARED TRACKING BLOCK>

<INSERT RECONNAISSANCE ADD-ON BLOCK WHEN NEEDED>

<INSERT RESEARCH TOOLING ADD-ON BLOCK WHEN NEEDED>

Agent 结构：
1. coordinator-agent
- 负责整体编排、阶段推进、状态记录、最终输出

2. <WORKER A>
- 负责：<SCOPE>

3. <WORKER B>
- 负责：<SCOPE>

4. skeptic-agent
- 负责挑战主结论、发现遗漏与弱证据

5. synthesizer-agent
- 负责整合各 agent 产物并生成最终报告

阶段计划：
- 第 0 阶段：建立工作目录、状态文件、分工表
- 第 1 阶段：执行前置调研任务并更新 `SPEC.md`
- 第 2 阶段：并行执行独立工作流
- 第 3 阶段：交叉验证与补洞
- 第 4 阶段：汇总并产出最终结果

工具发现与使用要求：
- 开始时先检查当前可用工具。
- 优先使用内置工具、文件工具、搜索/抓取工具、MCP 工具。
- 仅在确实需要时追加新的工具发现。
- 若不同 agent 适合不同工具，请按各自职责选择。
- 避免所有 agent 重复做同一轮工具探测。

最终输出要求：
- <FINAL DELIVERABLE SHAPE>

开始时先：
1. 先运行 doctor 检查本地可用的 MCP、CLI 和 skills
2. 将 doctor 结论写入 `SPEC.md` 和 `STATUS.json`
3. 给出分工表
4. 建立状态追踪
5. 明确说明将优先使用 PicoClaw 原生机制
6. 先向用户确认最大并发 agent 进程数量
7. 在用户确认后启动第一批并行 agent
8. 回复任务已启动以及状态查询方式
```

## Template 2: Burst Fan-Out Stress Test

Use for high-concurrency tasks, monitoring swarms, and broad coverage.

```text
开始一个高并发多 agent 压测任务：<TITLE>。

任务目标：
在严格时间预算内，通过大量并行 agent 对 <TOPIC> 做广覆盖观测、交叉验证和快速收敛。

核心要求：
- 这是一个高扇出任务。
- 请优先最大化安全并行度。
- 请尽快启动大量窄职责 agent，而不是少量宽职责 agent。
- 如果运行时存在并发上限，请先检测并报告。
- 在执行前必须向用户确认最大并发 agent 进程数量。
- 即使部分 agent 失败，也必须在截止时间前交付可用结论。

时间预算：
- 总时长：<TIME BUDGET>
- 启动阶段：<TIME>
- 广覆盖阶段：<TIME>
- 验证补洞阶段：<TIME>
- 最终收敛阶段：<TIME>

<INSERT SHARED TRACKING BLOCK>

<INSERT RECONNAISSANCE ADD-ON BLOCK WHEN NEEDED>

Agent 编组：
- coordinator-agent
- tool-scout-agent
- <NARROW AGENT 1>
- <NARROW AGENT 2>
- ...
- contradiction-agent
- critic-agent
- synthesizer-agent

每个 worker 输出格式：
- 主题
- 关键发现
- 证据与来源
- 直接影响
- 置信度
- 待验证点
- 一句话结论

最终报告必须包含：
1. Executive Summary
2. Concurrency Outcome
3. Key Findings
4. Contradictions and Unknowns
5. Final Synthesis
6. Stress-Test Self-Evaluation

开始时先：
1. 先运行 doctor 检查本地可用的 MCP、CLI 和 skills
2. 报告当前 PicoClaw 并发限制与相关原生机制可用性
3. 创建任务目录和状态文件
4. 先设计并启动一批小型调研 agent
5. 根据调研结果更新 `SPEC.md`
6. 向用户确认最大并发 agent 进程数量
7. 在用户确认后再启动完整任务所需的第一批并行 agent
8. 回复任务已启动与状态查询方式
```

## Template 3: Research Pipeline

Use for deeper analysis where evidence quality matters more than raw fan-out.

```text
开始一个多 agent 研究任务：<TITLE>。

任务目标：
围绕 <QUESTION> 进行结构化研究，并输出可审阅的最终结论。

执行结构：
- discovery stage
- analysis stage
- verification stage
- synthesis stage

<INSERT SHARED TRACKING BLOCK>

<INSERT RECONNAISSANCE ADD-ON BLOCK WHEN NEEDED>

Agent 结构：
1. coordinator-agent
2. discovery-agent(s)
3. analyst-agent(s)
4. verifier-agent
5. skeptic-agent
6. synthesizer-agent

阶段要求：
- 发现阶段负责收集候选证据
- 分析阶段负责解释与结构化归纳
- 验证阶段负责反驳、补洞、找冲突
- 汇总阶段负责输出最终结论和剩余不确定性

最终输出必须包含：
- research question
- evidence summary
- main conclusions
- counterarguments
- unresolved questions
- final recommendation or answer

开始时先：
1. 先运行 doctor 检查本地可用的 MCP、CLI 和 skills
2. 输出研究分工
3. 建立阶段产物目录
4. 先启动小型调研任务以确认工具、来源和风险
5. 将调研结论写入 `SPEC.md`
6. 向用户确认最大并发 agent 进程数量
7. 在用户确认后再启动 discovery agents
8. 回复任务已启动
```

## Template 4: Coding Collaboration Prompt

Use when the user wants a multi-agent coding mission.

```text
开始一个多 agent 编码协作任务：<TITLE>。

任务目标：
完成 <ENGINEERING GOAL>，并通过多 agent 并行协作提升速度与覆盖率。

执行原则：
- 先理解代码库与工具面
- 再拆分独立工作流
- 避免多个 agent 写同一文件，除非已明确所有权
- 保持最终结果可验证
- 不要为了并行而制造无意义分工

<INSERT SHARED TRACKING BLOCK>

<INSERT RECONNAISSANCE ADD-ON BLOCK WHEN NEEDED>

推荐 agent 结构：
1. coordinator-agent
2. codebase-mapper-agent
3. implementation-agent(s)
4. test-agent
5. reviewer-agent
6. synthesizer-agent

最终输出必须包含：
- implementation summary
- changed areas
- validation outcome
- known risks
- follow-up suggestions

开始时先：
1. 先运行 doctor 检查本地可用的 MCP、CLI 和 skills
2. 输出代码协作分工表
3. 标注每个 agent 的文件所有权
4. 先启动若干小型调研任务以确认代码入口、工具面和测试路径
5. 将调研结论写入 `SPEC.md`
6. 向用户确认最大并发 agent 进程数量
7. 建立状态追踪
8. 在用户确认后启动第一批 agent
```

## Template 5: Monitoring / Watch Task

Use for long-running or scheduled monitoring missions.

```text
开始一个多 agent 监控任务：<TITLE>。

任务目标：
在 <TIME WINDOW> 内持续监控 <TOPIC>，通过多个 agent 覆盖不同信号源，并按阶段输出中报与总报。

执行原则：
- 长任务优先拆成独立监控 agent
- 主任务负责状态、节奏和汇总
- 每个监控 agent 应独立记录进度和失败项
- 单个 agent 失败不得导致整体停止
- 到截止时间必须交付最终总报

<INSERT SHARED TRACKING BLOCK>

<INSERT RECONNAISSANCE ADD-ON BLOCK WHEN NEEDED>

Agent 结构：
- coordinator-agent
- source-scout-agent(s)
- domain-watch-agent(s)
- contradiction-agent
- hourly-synthesis-agent
- final-synthesis-agent

最终报告必须包含：
- major developments
- source index
- impact analysis
- uncertainty and gaps
- runtime stability notes

开始时先：
1. 建立监控目录结构
2. 先启动若干小型调研任务以确认来源质量、刷新节奏和工具可用性
3. 将调研结论写入 `SPEC.md`
4. 向用户确认最大并发 agent 进程数量
5. 在用户确认后启动监控 agent
6. 创建状态文件
7. 回复任务已启动和查询方式
```

## Template Selection Rules

| User goal | Best template |
|---|---|
| General task -> complete orchestration prompt | Template 1 |
| Many parallel agents, short deadline, stress test | Template 2 |
| Deep research and verification | Template 3 |
| Multi-agent coding collaboration | Template 4 |
| Ongoing watch or scheduled monitoring | Template 5 |

If needed:
- start from one template
- borrow sections from another
- keep the final prompt coherent

## Final Assembly Checklist

Before returning the final prompt, check:
- Is the topology appropriate?
- Are the agents narrow enough?
- Is tool discovery explicit?
- Does the prompt define the task folder and tracking files?
- Does it require per-agent writeback?
- Does it require user notification?
- Is there a clear convergence phase?
- Are failure states handled?
- Could the runtime start immediately from this prompt?
