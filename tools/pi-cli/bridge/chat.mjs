#!/usr/bin/env node
/**
 * Pi 编排桥接（Stage 5）：Python 宿主 ↔ @earendil-works/pi-coding-agent SDK。
 *
 * 范式参考 F:\Project\VibeStart（createAgentSession 同进程 SDK + customTools +
 * ExtensionFactory 注入 + session.subscribe 事件流），适配本项目的宿主接地红线：
 *
 *   红线（AGENTS §9.1 host-executed tools）：
 *   - 每个 customTool 的 execute 仅是【代理】——HTTP loopback 到宿主
 *     POST {api_base}/agent/tool-run，由 Python REGISTRY 实际计算；
 *   - Pi 只负责编排（选工具/定参数）与叙述，永不产生数字；
 *   - 工具清单来自宿主 GET {api_base}/agent/tools/manifest（@tool 声明为唯一真相）。
 *
 * 协议（单次进程，stdio JSONL）：
 *   stdin  一行 JSON：{ message, session_id, api_base, cwd? }
 *   stdout 逐行 JSON 事件：
 *     {type:"ready", model, n_tools}
 *     {type:"tool_start", tool, args}
 *     {type:"tool_end", tool, ok, result, error}
 *     {type:"done", reply, model, n_tool_calls}
 *     {type:"error", message}
 *
 * 依赖：@earendil-works/pi-coding-agent + typebox（见 tools/pi-cli/package.json；
 * python scripts/setup_pi_cli.py 安装）。node ≥ 22（原生 fetch）。
 */
import { createAgentSession, DefaultResourceLoader, SessionManager, SettingsManager, defineTool } from '@earendil-works/pi-coding-agent'
import { Type } from 'typebox'

// ---------------------------------------------------------------------------
// stdin 请求
// ---------------------------------------------------------------------------

function readStdinLine() {
  return new Promise((resolve, reject) => {
    let buf = ''
    process.stdin.setEncoding('utf-8')
    process.stdin.on('data', (chunk) => {
      buf += chunk
      const idx = buf.indexOf('\n')
      if (idx >= 0 || chunk === '') {
        resolve(idx >= 0 ? buf.slice(0, idx) : buf)
        process.stdin.pause()
      }
    })
    process.stdin.on('end', () => resolve(buf))
    process.stdin.on('error', reject)
    // 防挂死：30s 无输入自终止
    setTimeout(() => reject(new Error('bridge stdin timeout')), 30_000).unref()
  })
}

const out = (obj) => process.stdout.write(JSON.stringify(obj) + '\n')
const fail = (message) => {
  out({ type: 'error', message })
  process.exit(1)
}

let req
try {
  req = JSON.parse((await readStdinLine()).trim() || '{}')
} catch (e) {
  fail(`无法解析 stdin 请求: ${e.message}`)
}
const { message, api_base: apiBase } = req
if (!message || !apiBase) fail('缺少 message 或 api_base')

// ---------------------------------------------------------------------------
// 宿主接地指令（ExtensionFactory 注入，等价 VibeStart 的 before_agent_start）
// ---------------------------------------------------------------------------

const HOST_INSTRUCTION = `你是「数字营销转化分析」系统的编排中枢（Pi），运行在项目内部。数据分析工具已全部注册。

【硬性规则 · 必须遵守】
1. 所有数字、指标、SHAP、百分比**只来自工具调用结果**——禁止凭空产生任何数字；未调用工具就不要给出数字。
2. 只使用已注册的分析工具（参数见各工具说明）；禁止文件读写、命令执行等一切编码类操作。
3. 得到工具结果后，用中文组织回复，覆盖：【观察事实】（引用工具结果中的关键数字）/【推断】/【建议】/【待确认】。
4. 口径红线：主指标是 PR-AUC，Accuracy 仅对照并须并列 Dummy；关联规则与反事实为相关/模型行为口径，**不构成因果**；预算模拟为期望值口径，非收益承诺；分群训练不含 Conversion，簇转化率为事后统计；实验 CI 重叠时不得宣称某 run 更优。
5. 回复简洁专业，适合本科答辩演示。`

const contextFactory = (pi) => {
  pi.on('before_agent_start', async () => ({
    message: {
      customType: 'digital-marketing-context',
      display: false,
      content: HOST_INSTRUCTION,
    },
  }))
}

// ---------------------------------------------------------------------------
// customTools：宿主工具代理（execute → loopback HTTP → Python REGISTRY 实算）
// ---------------------------------------------------------------------------

async function callHostTool(name, args) {
  const resp = await fetch(`${apiBase}/agent/tool-run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, args: args ?? {} }),
  })
  if (!resp.ok) return { ok: false, error: `loopback HTTP ${resp.status}` }
  const body = await resp.json()
  return body?.data ?? { ok: false, error: 'loopback 响应缺少 data' }
}

let manifest
try {
  const resp = await fetch(`${apiBase}/agent/tools/manifest`)
  const body = await resp.json()
  manifest = body?.data?.tools ?? []
} catch (e) {
  fail(`无法获取宿主工具清单（宿主 API 是否已在 ${apiBase} 启动？）: ${e.message}`)
}
if (manifest.length === 0) fail('宿主工具清单为空')

const customTools = manifest.map((t) => {
  const paramsDesc = JSON.stringify(t.parameters?.properties ?? {})
  return defineTool({
    name: t.name,
    label: t.name,
    description: `${t.description}\n参数: ${paramsDesc}`,
    promptSnippet: `${t.name}：${t.description}`,
    promptGuidelines: [
      `${t.name} 仅在需要其数据时调用；结果中的数字可直接引用于回复。`,
    ],
    // 宽松 schema：参数语义在 description 中给出；宿主 run_tool 会做真实校验
    parameters: Type.Object({}, { additionalProperties: true }),
    execute: async (_toolCallId, params) => {
      const d = await callHostTool(t.name, params ?? {})
      if (!d.ok) {
        return {
          content: [{ type: 'text', text: `工具 ${t.name} 执行失败: ${d.error ?? '未知错误'}` }],
          isError: true,
          details: { ok: false, error: d.error },
        }
      }
      // 回灌给模型的文本截断，防上下文膨胀；details 带全量结果供事件流读取
      const text = JSON.stringify(d.result).slice(0, 6000)
      return {
        content: [{ type: 'text', text: `工具 ${t.name} 结果 JSON: ${text}` }],
        details: { ok: true, result: d.result },
      }
    },
  })
})

// ---------------------------------------------------------------------------
// 会话：同进程 SDK（VibeStart 范式），内存态会话管理（多轮由宿主侧持久化）
// ---------------------------------------------------------------------------

const cwd = req.cwd ?? process.cwd()
let assistantText = ''
let nToolCalls = 0
let modelName = ''

const resourceLoader = new DefaultResourceLoader({
  cwd,
  extensionFactories: [contextFactory],
})
await resourceLoader.reload()

let session
try {
  // 优先尝试携带 model（env PI_BRIDGE_MODEL，如 deepseek-chat）；不支持则回落默认
  const opts = {
    cwd,
    resourceLoader,
    customTools,
    sessionManager: SessionManager.inMemory(cwd),
    settingsManager: SettingsManager.inMemory(),
  }
  if (process.env.PI_BRIDGE_MODEL) opts.model = process.env.PI_BRIDGE_MODEL
  ;({ session } = await createAgentSession(opts))
} catch (e1) {
  try {
    ;({ session } = await createAgentSession({
      cwd,
      resourceLoader,
      customTools,
      sessionManager: SessionManager.inMemory(cwd),
      settingsManager: SettingsManager.inMemory(),
    }))
  } catch (e2) {
    fail(`createAgentSession 失败: ${e2.message}（首次: ${e1.message}）`)
  }
}

try {
  const m = session.model
  modelName = m?.name ?? m?.id ?? ''
} catch {
  modelName = ''
}

session.subscribe((event) => {
  try {
    switch (event.type) {
      case 'message_update': {
        const ame = event.assistantMessageEvent
        if (ame?.type === 'text_delta') assistantText += ame.delta
        break
      }
      case 'tool_execution_start':
        nToolCalls++
        out({ type: 'tool_start', tool: event.toolName, args: event.args ?? {} })
        break
      case 'tool_execution_end': {
        const details = event.result?.details
        out({
          type: 'tool_end',
          tool: event.toolName,
          ok: Boolean(details?.ok) && !event.isError,
          result: details?.result ?? null,
          error: event.isError ? String(details?.error ?? '执行失败') : null,
        })
        break
      }
      case 'agent_end': {
        // 兜底：delta 未拼全时从消息列表取最终文本
        if (assistantText === '') {
          const msgs = event.messages ?? []
          for (let i = msgs.length - 1; i >= 0; i--) {
            const mm = msgs[i]
            if (mm?.role === 'assistant' && Array.isArray(mm.content)) {
              const txt = mm.content
                .filter((p) => p.type === 'text' && typeof p.text === 'string')
                .map((p) => p.text)
                .join('\n')
              if (txt !== '') {
                assistantText = txt
                break
              }
            }
          }
        }
        break
      }
      case 'agent_settled':
        out({ type: 'done', reply: assistantText, model: modelName, n_tool_calls: nToolCalls })
        try {
          session.dispose()
        } catch {
          /* ignore */
        }
        process.exit(0)
        break
    }
  } catch (err) {
    // 事件处理绝不向 SDK 事件循环抛异常
    process.stderr.write(`[bridge] 事件处理错误: ${err}\n`)
  }
})

try {
  await session.prompt(String(message))
} catch (e) {
  fail(`session.prompt 失败: ${e?.message ?? e}`)
}

// 兜底：部分版本不发 agent_settled 时，prompt 返回即结束
setTimeout(() => {
  out({ type: 'done', reply: assistantText, model: modelName, n_tool_calls: nToolCalls })
  process.exit(0)
}, 2_000).unref()
