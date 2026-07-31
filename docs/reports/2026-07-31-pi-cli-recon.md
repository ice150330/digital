# Pi CLI 侦察报告（Stage 0）

- **日期：** 2026-07-31
- **侦察对象：** `@earendil-works/pi-coding-agent@0.83.0`（[earendil-works/pi](https://github.com/earendil-works/pi) monorepo）
- **方式：** 官方仓库 README + npm registry 清单（包尚未本地安装；`--help` 实测待安装后补录）

## 1. 包生态与最小依赖面

| 包 | 角色 | 本项目是否需要 |
|---|---|---|
| `@earendil-works/pi-coding-agent` | 交互式 coding agent CLI（bin: `pi` → `dist/cli.js`；SDK 入口 `createAgentSession` 等；另导出 `./rpc-entry`） | **是（唯一安装项）** |
| `@earendil-works/pi-agent-core` | agent runtime（工具调用 + 状态管理） | 传递依赖，自动装 |
| `@earendil-works/pi-ai` | 统一多 provider LLM API（内置 DeepSeek/Anthropic/OpenAI/… 数十家） | 传递依赖 |
| `@earendil-works/pi-tui` | 终端 UI | 传递依赖 |
| `packages/protocol` | 实验性二进制协议（4 字节 BE 长度前缀 + CBOR，不含传输层） | **否**（复杂度高于收益） |
| `packages/server`、`evals`、`storage/*` | 服务端/评测/存储 | 否 |

**最小需要 = `pi-coding-agent` 一个包**（CLI 子进程集成），不碰 CBOR protocol 包。要求 **node ≥ 22.19**（本机 v24 ✓）。

## 2. 三项能力结论（yes/no）

| 能力 | 结论 | 接口 |
|---|---|---|
| 非交互一次性提示 | **yes** | `-p, --print`；支持 `cat x \| pi -p "..."` 管道输入 |
| JSON/结构化输出 | **yes** | `--mode json`（JSON 事件流）；另有 `--mode rpc`（严格 `\n` 分隔 JSONL 帧的进程级 RPC） |
| 多轮会话续接 | **yes** | `--session <path\|id>` / `--session-dir <dir>` / `-c`(continue) / `-r`(resume) / `--no-session`；会话为 JSONL 树；env `PI_CODING_AGENT_SESSION_DIR` |

## 3. 与本项目红线相关的 flags（关键）

| flags | 用途（对齐 AGENTS.md） |
|---|---|
| `--no-tools, -nt` / `--tools <list>` / `--exclude-tools` | **§9.1 host-executed tools**：禁用内置 read/bash/edit/write/grep/find/ls，Pi 只做规划/叙述，数字永由宿主工具产出 |
| `--skill <path>` / `--no-skills` | 直接加载 `src/digital_marketing/agent/skills/*/SKILL.md`（§9.3 skills 生态） |
| `--session-dir <dir>` | 会话落 `outputs/agent_sessions/`（§9.3） |
| `--system-prompt` / `--append-system-prompt` | 注入五段契约 + 工具白名单 JSON + 口径红线句 |
| `--provider <name> --model <pattern> --api-key <key>` | 对齐 `agent.yaml` llm 节（DeepSeek 为内置 provider） |
| `--approve` / `defaultProjectTrust` | 非交互模式项目信任（否则弹询问） |
| `--offline`、env `PI_SKIP_VERSION_CHECK=1`、`PI_TELEMETRY=0`、`PI_OFFLINE=1` | 答辩离线友好 |

**安全提示（README 原文）：** "Pi packages run with full system access." / "Pi does not include a built-in permission system." → 集成层必须 `--no-tools`（或白名单只读工具）+ 不装第三方扩展（`--no-extensions`）。

**意外红利：** pi 原生加载仓库根的 `AGENTS.md`/`CLAUDE.md` 作为上下文文件——本仓库约束会自动进入 Pi 上下文。

## 4. 协议选型（锁定）

**方案 A 为主 + B 自动兜底**（Plan A/B 见重构计划 Stage 0 节）：

```text
A 主路（两段式 Plan→Execute→Narrate）
  ① pi -p "<消息 + 白名单工具 schema，要求仅输出 JSON 工具计划>" --mode json --no-tools ...
  ② 宿主 REGISTRY 执行计划（数字全由宿主产出）
  ③ pi -p "<工具结果 + 五段契约模板，仅叙述不产数字>" --mode json --no-tools ...
  任一环节解析失败 → 降级 B

B 兜底（纯叙述）
  宿主 plan_from_message 规划 + 执行 → 结果喂 pi -p 生成五段叙述
  B 再失败（无 Key/超时/非 JSON）→ 降级 local/template，pi_fallback=true（现有契约不变）
```

**不选 C**（`--mode rpc`/`createAgentSession` 深集成）：RPC 帧协议与扩展工具注册机制超出答辩必要工程量，列为后续可选项。
**分支 R 保留**：装包失败时 stub 协议化，解析路径同一套代码。

## 5. 集成命令模板（Stage 5 落实）

```bash
# 环境：cwd=project_root；PATH 仅注入 exe.parent（不依赖全局 pi）
PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 PI_OFFLINE=1 \
PI_CODING_AGENT_SESSION_DIR=outputs/agent_sessions \
tools/pi-cli/node_modules/.bin/pi \
  -p "<prompt>" \
  --mode json \
  --no-tools \            # 红线：宿主工具接地，Pi 不碰文件系统/shell
  --no-extensions \
  --skill src/digital_marketing/agent/skills/<name>/SKILL.md \
  --session-dir outputs/agent_sessions \
  --provider deepseek --model deepseek-chat \   # 来自 agent.yaml llm 节
  --append-system-prompt "<五段契约 + 红线句>" \
  --approve \
  --offline
```

## 6. 实测结论（2026-07-31 补录，v0.83.0 已安装）

- [x] **`pi --version` = 0.83.0**；`--help` 全文与本报告第 2/3 节一致（补充：`--provider` **默认 google**，须显式指定；`--session-id <id>` 精确会话；`--no-builtin-tools/-nbt` 禁内置但留扩展/自定义工具）
- [x] **最终集成未走 CLI 而走 SDK**（`createAgentSession` 同进程，范式来自 VibeStart）：`createAgentSession({ cwd, agentDir, resourceLoader, customTools, noTools:'builtin', modelRuntime, model, sessionManager: SessionManager.inMemory(cwd), settingsManager: SettingsManager.inMemory() })`；事件流 `session.subscribe`：`tool_execution_start/end`、`message_update.text_delta`、`agent_settled`
- [x] **关键 API 细节（踩坑实录）：**
  - `DefaultResourceLoader` 构造**必须显式传 `agentDir`**（`join(homedir(), '.pi', 'agent')`），SDK 不自填默认值，缺失即 `normalizePath` 崩溃
  - `createAgentSession` 的 `model` 是 `Model` 对象而非字符串：`ModelRuntime.create({})` → `getModel(providerId, modelId)`
  - `noTools: 'builtin'` 禁用内置 read/bash/edit/write 且**保留 customTools**（宿主接地红线的 SDK 级保障）
- [x] **DeepSeek Key**：pi-ai 读 `DEEPSEEK_API_KEY` 环境变量（实测生效，解析模型为 DeepSeek V4 Flash）；桥接经 `PI_BRIDGE_MODEL`（默认 `deepseek/deepseek-chat`）指定 provider/model
- [x] **实测联通（两轮）：**
  - 桥接单链路：Pi 自主调用 `get_dataset_profile` → 宿主 loopback 实算（n_rows=8000, positive_rate=0.8765）→ Pi 五段叙述且自发遵守 PR-AUC/Accuracy 口径
  - 全链路 `POST /agent/chat runtime=pi`：`pi_fallback=false`，Pi 自主编排 `get_model_metrics` + `render_chart` 双工具，grounding 从工具结果抽出 7 条 facts，chart-spec 正确（bar/渠道转化率/5 渠道），reply 为 Pi 组织的五段文本
- [x] 无 Key 时：桥接 `createAgentSession` 失败 → Python 侧降级 local（`pi_fallback=true`，契约不变）

## 7. 风险

| 风险 | 缓解 |
|---|---|
| LLM 输出非 JSON（方案 A 第①段） | 宽松解析（抽 JSON 块）+ 一次重试 → 降级 B |
| DeepSeek 限流/计费 | 默认 runtime 可一键切回 local；答辩前锁定演示模式 |
| 安装体积/网络 | 单次 npm install，lock 入库；离线时 stub 降级链路完整 |
| pi 读 AGENTS.md 注入超长上下文 | `--no-context-files` 可关（`-nc`），按需裁剪 |
