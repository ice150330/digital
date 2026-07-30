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
