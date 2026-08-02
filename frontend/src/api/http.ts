import axios, { type AxiosError } from 'axios'

/** 后端统一 envelope */
export interface ApiEnvelope<T> {
  ok: boolean
  data: T | null
  error: { code: string; message: string; detail?: Record<string, unknown> } | null
  request_id: string
}

export const apiBaseURL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  'http://127.0.0.1:9800/api/v1'

export const http = axios.create({
  baseURL: apiBaseURL,
  timeout: 30000,
})

const ERROR_CODE_MESSAGES: Record<string, string> = {
  VALIDATION_ERROR: '输入内容不符合要求，请检查后重试',
  SCHEMA_MISMATCH: '输入字段与当前模型不一致，请刷新特征信息',
  MODEL_NOT_LOADED: '模型尚未加载，请先运行训练流程',
  ARTIFACT_MISSING: '缺少分析产物，请先运行数据与训练脚本',
  AGENT_TOOL_FAILED: '分析工具执行失败，请查看工具轨迹',
  PI_NOT_INSTALLED: '项目内 Pi 尚未安装，本轮可切换本地工具',
  PI_PATH_INVALID: 'Pi 路径不符合项目隔离要求',
  LLM_UNAVAILABLE: 'LLM 当前不可用，可切换模板模式继续演示',
  RATE_LIMIT: '请求过于频繁，请稍后再试',
}

function envelopeMessage(body: ApiEnvelope<unknown> | null): string {
  const code = body?.error?.code
  return body?.error?.message || (code ? ERROR_CODE_MESSAGES[code] : '') || '请求失败'
}

function unwrapError(err: unknown): Error {
  const ax = err as AxiosError<ApiEnvelope<unknown>>
  if (ax.response?.data?.error) {
    return new Error(envelopeMessage(ax.response.data))
  }
  if (err instanceof Error && err.message) {
    return err
  }
  return new Error('网络错误，请确认后端已启动')
}

export interface StreamEvent<T = unknown> {
  event: string
  data: T
}

export interface StreamConnection {
  abort: () => void
  completed: Promise<void>
}

function parseEventBlock(block: string): StreamEvent | null {
  let event = 'message'
  const dataLines: string[] = []
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
  }
  if (!dataLines.length) return null
  const raw = dataLines.join('\n')
  try {
    return { event, data: JSON.parse(raw) }
  } catch {
    return { event, data: raw }
  }
}

/** 使用 fetch/ReadableStream 消费 POST SSE；返回 abort 以支持停止生成。 */
export function postStream(
  path: string,
  payload: unknown,
  onEvent: (event: StreamEvent) => void,
  opts?: { timeout?: number },
): StreamConnection {
  const controller = new AbortController()
  let timedOut = false
  const timeout = opts?.timeout ?? 180000
  const timer = window.setTimeout(() => {
    timedOut = true
    controller.abort()
  }, timeout)

  const completed = (async () => {
    try {
      const response = await fetch(`${apiBaseURL}${path}`, {
        method: 'POST',
        headers: {
          Accept: 'text/event-stream',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload ?? {}),
        credentials: 'include',
        signal: controller.signal,
      })
      if (!response.ok) {
        let body: ApiEnvelope<unknown> | null = null
        try {
          body = await response.json() as ApiEnvelope<unknown>
        } catch {
          // 非 envelope 响应统一进入中文兜底。
        }
        throw new Error(envelopeMessage(body))
      }
      if (!response.body) throw new Error('浏览器不支持流式响应，请更新浏览器后重试')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        buffer += decoder.decode(value, { stream: !done })
        buffer = buffer.replace(/\r\n/g, '\n')
        let boundary = buffer.indexOf('\n\n')
        while (boundary >= 0) {
          const block = buffer.slice(0, boundary)
          buffer = buffer.slice(boundary + 2)
          const parsed = parseEventBlock(block)
          if (parsed) onEvent(parsed)
          boundary = buffer.indexOf('\n\n')
        }
        if (done) break
      }
      const trailing = parseEventBlock(buffer.trim())
      if (trailing) onEvent(trailing)
    } catch (error) {
      if (controller.signal.aborted && !timedOut) return
      if (timedOut) throw new Error('流式请求超时，请稍后重试')
      throw unwrapError(error)
    } finally {
      window.clearTimeout(timer)
    }
  })()

  return { abort: () => controller.abort(), completed }
}

/** 解析 envelope；失败时抛出中文错误信息 */
export async function getData<T>(path: string, params?: Record<string, unknown>): Promise<{ data: T; requestId: string }> {
  try {
    const resp = await http.get<ApiEnvelope<T>>(path, { params })
    const body = resp.data
    if (!body.ok || body.data == null) {
      throw new Error(body.error?.message || '请求失败')
    }
    return { data: body.data, requestId: body.request_id }
  } catch (err) {
    throw unwrapError(err)
  }
}

export async function postData<T>(
  path: string,
  payload?: unknown,
  opts?: { timeout?: number },
): Promise<{ data: T; requestId: string }> {
  try {
    const resp = await http.post<ApiEnvelope<T>>(path, payload ?? {}, {
      timeout: opts?.timeout ?? 30000,
    })
    const body = resp.data
    if (!body.ok || body.data == null) {
      throw new Error(body.error?.message || '请求失败')
    }
    return { data: body.data, requestId: body.request_id }
  } catch (err) {
    throw unwrapError(err)
  }
}

export async function putData<T>(
  path: string,
  payload?: unknown,
  opts?: { timeout?: number },
): Promise<{ data: T; requestId: string }> {
  try {
    const resp = await http.put<ApiEnvelope<T>>(path, payload ?? {}, {
      timeout: opts?.timeout ?? 30000,
    })
    const body = resp.data
    if (!body.ok || body.data == null) {
      throw new Error(envelopeMessage(body))
    }
    return { data: body.data, requestId: body.request_id }
  } catch (err) {
    throw unwrapError(err)
  }
}

export async function deleteData<T>(path: string): Promise<{ data: T; requestId: string }> {
  try {
    const resp = await http.delete<ApiEnvelope<T>>(path)
    const body = resp.data
    if (!body.ok || body.data == null) {
      throw new Error(envelopeMessage(body))
    }
    return { data: body.data, requestId: body.request_id }
  } catch (err) {
    throw unwrapError(err)
  }
}
