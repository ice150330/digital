#!/usr/bin/env python3
"""在项目内 tools/pi-cli/ 安装 Pi CLI 占位/依赖（禁止全局 pi）。"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PI_DIR = ROOT / "tools" / "pi-cli"


README_TXT = """# 项目内 Pi CLI

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
"""


STUB_JS = """#!/usr/bin/env node
// 项目内 Pi stub：便于路径校验与演示降级；非生产 LLM 宿主
const args = process.argv.slice(2);
if (args.includes('--version') || args.includes('-v')) {
  console.log('pi-stub 0.1.0 (project-local)');
  process.exit(0);
}
if (args.includes('--help') || args.includes('-h') || args.length === 0) {
  console.log('pi-stub: project-local placeholder under tools/pi-cli/');
  console.log('Host tools remain the source of truth for metrics.');
  process.exit(0);
}
console.log(JSON.stringify({ ok: true, runtime: 'pi-stub', args }));
process.exit(0);
"""


def write_stub() -> Path:
    PI_DIR.mkdir(parents=True, exist_ok=True)
    (PI_DIR / "README.md").write_text(README_TXT, encoding="utf-8")
    bin_dir = PI_DIR / "node_modules" / ".bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    stub = bin_dir / "pi"
    stub.write_text(STUB_JS, encoding="utf-8")
    try:
        stub.chmod(0o755)
    except OSError:
        pass
    # Windows cmd shim
    cmd = bin_dir / "pi.cmd"
    cmd.write_text(
        "@echo off\r\nnode \"%~dp0pi\" %*\r\n",
        encoding="utf-8",
    )
    # package.json 标记（type=module 供 Stage5 bridge/chat.mjs ESM 导入）
    pkg = {
        "name": "digital-marketing-pi-cli",
        "private": True,
        "version": "0.1.0",
        "type": "module",
        "description": "Project-local Pi CLI root (no global install)",
        "bin": {"pi": "node_modules/.bin/pi"},
    }
    (PI_DIR / "package.json").write_text(json.dumps(pkg, indent=2), encoding="utf-8")
    # .gitignore 内依赖可选
    gi = PI_DIR / ".gitignore"
    if not gi.is_file():
        gi.write_text("node_modules/\n", encoding="utf-8")
    return stub


DEFAULT_NPM_PACKAGES = "@earendil-works/pi-coding-agent typebox"


def try_npm_install() -> bool:
    """安装 Pi SDK + 桥接依赖（Stage 5 起默认安装；SKIP_NPM=1 跳过）。"""
    if os.environ.get("SKIP_NPM") == "1":
        return False
    npm = shutil.which("npm")
    if not npm:
        print("未找到 npm，仅写入 stub", flush=True)
        return False
    pkg = os.environ.get("PI_NPM_PACKAGE", "").strip() or DEFAULT_NPM_PACKAGES
    packages = pkg.split()
    print(f"+ npm install {' '.join(packages)} (cwd={PI_DIR})", flush=True)
    r = subprocess.run(
        [npm, "install", *packages, "--no-fund", "--no-audit"],
        cwd=str(PI_DIR),
        shell=False,
    )
    if r.returncode != 0:
        print("npm install 失败：仍为 stub，Pi 编排将降级 local/template", flush=True)
    return r.returncode == 0


def main() -> int:
    print(f"Pi 安装根: {PI_DIR}", flush=True)
    stub = write_stub()
    print(f"已写入 stub: {stub}", flush=True)
    try_npm_install()
    # 校验路径约束
    sys.path.insert(0, str(ROOT / "src"))
    from digital_marketing.agent.pi_runtime import pi_status

    st = pi_status()
    print(json.dumps(st, ensure_ascii=False, indent=2), flush=True)
    if not st.get("valid_prefix"):
        print("路径前缀校验失败", file=sys.stderr)
        return 1
    if not st.get("installed"):
        print("警告: status.installed=false，请检查 stub 是否落盘", file=sys.stderr)
        return 1
    print("setup_pi_cli done（仅项目内 tools/pi-cli/）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
