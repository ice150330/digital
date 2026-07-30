# 项目内 Pi CLI

本目录为 **仅项目内** 的 Pi 可执行/依赖落点。

- 配置：`config/agent.yaml` → `pi.executable`（相对仓库根）
- **禁止** 使用全局 `pi` / `which pi` / PATH 回退
- 未真正安装上游 Pi 时，`GET /api/v1/agent/pi/status` 会提示未安装并降级 local/template

安装：

```bash
python scripts/setup_pi_cli.py
```

可选环境变量：

- `PI_NPM_PACKAGE`：npm 包名（默认创建本地 stub）
- `SKIP_NPM=1`：仅写 stub，不调用 npm
