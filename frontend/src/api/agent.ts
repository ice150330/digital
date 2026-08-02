import { deleteData, getData, postData, postStream, type StreamConnection } from './http'

export interface ToolTraceItem {
  tool: string
  args?: Record<string, unknown>
  ok?: boolean
  error?: string | null
  result?: unknown
  duration_ms?: number | null
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
  pi_fallback?: boolean
}

export interface PiStatusData {
  installed: boolean
  executable: string | null
  valid_prefix: boolean
  code: string | null
  message: string | null
  hint: string | null
  is_stub: boolean
  default_runtime: string | null
  skills: string[]
  skills_detail: Array<{ name: string; description: string; path: string }>
  sessions_count: number
  fallback_reason: string | null
  bridge_ready: boolean
  bridge_note: string | null
}

export function chatAgent(body: {
  message: string
  session_id?: string
  runtime?: string
}) {
  return postData<ChatData>('/agent/chat', body, { timeout: 120000 })
}

export interface AgentStreamDone {
  session_id: string
  latency_ms?: number | null
  runtime?: string | null
  pi_fallback?: boolean
  pi_status?: Record<string, unknown> | null
}

export interface AgentStreamHandlers {
  text?: (data: { delta: string }) => void
  toolStart?: (data: { tool: string; args?: Record<string, unknown> }) => void
  toolEnd?: (data: ToolTraceItem) => void
  chart?: (data: { spec: Record<string, unknown> }) => void
  facts?: (data: { items: string[] }) => void
  inferences?: (data: { items: string[] }) => void
  recommendations?: (data: { items: string[] }) => void
  openQuestions?: (data: { items: string[] }) => void
  done?: (data: AgentStreamDone) => void
  error?: (data: { code: string; message: string }) => void
}

export function chatAgentStream(
  body: { message: string; session_id?: string; runtime?: string },
  handlers: AgentStreamHandlers,
): StreamConnection {
  return postStream('/agent/chat/stream', body, ({ event, data }) => {
    if (event === 'text') handlers.text?.(data as { delta: string })
    else if (event === 'tool_start') handlers.toolStart?.(data as { tool: string; args?: Record<string, unknown> })
    else if (event === 'tool_end') handlers.toolEnd?.(data as ToolTraceItem)
    else if (event === 'chart') handlers.chart?.(data as { spec: Record<string, unknown> })
    else if (event === 'facts') handlers.facts?.(data as { items: string[] })
    else if (event === 'inferences') handlers.inferences?.(data as { items: string[] })
    else if (event === 'recommendations') handlers.recommendations?.(data as { items: string[] })
    else if (event === 'open_questions') handlers.openQuestions?.(data as { items: string[] })
    else if (event === 'done') handlers.done?.(data as AgentStreamDone)
    else if (event === 'error') handlers.error?.(data as { code: string; message: string })
  }, { timeout: 180000 })
}

export function fetchAgentSession(sessionId: string) {
  return getData<Record<string, unknown>>(`/agent/sessions/${sessionId}`)
}

export interface AgentSessionSummary {
  session_id: string
  last_user_message: string
  created_at: string
  updated_at: string
  runtime: string
  tool_count: number
  message_count: number
}

export interface AgentSessionListData {
  items: AgentSessionSummary[]
  n: number
}

export function fetchAgentSessions(limit = 50) {
  return getData<AgentSessionListData>('/agent/sessions', { limit })
}

export function deleteAgentSession(sessionId: string) {
  return deleteData<{ session_id: string; deleted: boolean; message: string }>(`/agent/sessions/${sessionId}`)
}

export function fetchPiStatus() {
  return getData<PiStatusData>('/agent/pi/status')
}

export function setRuntime(runtime: string) {
  return postData<{ runtime: string; message?: string }>('/agent/runtime', { runtime })
}

// ---------------------------------------------------------------------------
// 阶段9：Pi 编排中枢
// ---------------------------------------------------------------------------

export interface AuditRow {
  ts: string
  request_id: string
  session_id?: string | null
  runtime: string
  user_message: string
  tool_calls: Array<{ tool: string; ok: boolean }>
  reply_digest?: string
  latency_ms?: number | null
  error?: string | null
}

export interface AuditRecentData {
  items: AuditRow[]
  n: number
  note?: string
}

export interface ReportData {
  report_path: string
  title: string
  n_sections: number
  n_sections_ok: number
  digest: string
  tool_trace: Array<{ tool: string; ok?: boolean; section?: string; error?: string | null }>
  disclaimer: string
}

export function fetchAuditRecent(limit = 50) {
  return getData<AuditRecentData>('/agent/audit/recent', { limit })
}

export function generateReport(body: { title?: string; sections?: string[] }) {
  return postData<ReportData>('/agent/report', body, { timeout: 120000 })
}
