# 项目内 Pi CLI

本目录为 **仅项目内** 的 Pi 可执行/依赖落点。

- 配置：`config/agent.yaml` → `pi.executable`（相对仓库根）
- **禁止** 使用全局 `pi` / `which pi` / PATH 回退
- 未真正安装上游 Pi 时，`GET /api/v1/agent/pi/status` 会提示未安装并降级 local/template

安装：

```bash
python scripts/setup_pi_cli.py
```

默认安装 `@earendil-works/pi-coding-agent` + `typebox`（SDK 桥接依赖）。

## Stage 5 编排桥接

`bridge/chat.mjs`：Python 宿主经 stdio JSONL 调用本桥接，桥接以同进程 SDK
（`createAgentSession` + `customTools` 代理）运行 Pi；工具执行经 HTTP loopback
回宿主 `POST /api/v1/agent/tool-run`（host-executed 红线：数字永由宿主计算）。

可选环境变量：

- `PI_NPM_PACKAGE`：覆盖安装包（空格分隔多个）
- `SKIP_NPM=1`：仅写 stub，不调用 npm
- `PI_BRIDGE_MODEL`：桥接用模型（如 deepseek-chat），缺省走 pi 默认/凭证
