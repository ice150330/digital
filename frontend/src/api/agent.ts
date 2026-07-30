import { getData, postData } from './http'

export interface ToolTraceItem {
  tool: string
  args?: Record<string, unknown>
  ok?: boolean
  error?: string | null
  result?: unknown
}

export interface ChatData {
  runtime: string
  session_id: string
  reply: string
  observed_facts: string[]
  inferences: string[]
  recommendations: string[]
  open_questions: string[]
  tool_trace: ToolTraceItem[]
  latency_ms?: number
  pi_status?: Record<string, unknown> | null
}

export interface PiStatusData {
  installed: boolean
  executable: string | null
  valid_prefix: boolean
  code: string | null
  message: string | null
  hint: string | null
}

export function chatAgent(body: {
  message: string
  session_id?: string
  runtime?: string
}) {
  return postData<ChatData>('/agent/chat', body, { timeout: 120000 })
}

export function fetchAgentSession(sessionId: string) {
  return getData<Record<string, unknown>>(`/agent/sessions/${sessionId}`)
}

export function fetchPiStatus() {
  return getData<PiStatusData>('/agent/pi/status')
}

export function setRuntime(runtime: string) {
  return postData<{ runtime: string; message?: string }>('/agent/runtime', { runtime })
}
