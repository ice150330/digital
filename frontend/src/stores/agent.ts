import { defineStore } from 'pinia'
import {
  chatAgentStream,
  deleteAgentSession,
  fetchAgentSession,
  fetchAgentSessions,
  type AgentStreamStatus,
  type ChatData,
  type ToolTraceItem,
} from '../api/agent'
import { useStreamChat } from '../composables/useStreamChat'

export interface SessionSummary {
  id: string
  title: string
  createdAt?: string
  updatedAt: string
  runtime?: string
  toolCount?: number
  messageCount?: number
}

export interface AgentUiMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  data?: ChatData
  streaming?: boolean
}

export type AgentRunPhase = 'idle' | 'planning' | 'tooling' | 'bridge' | 'replying' | 'done' | 'error' | 'stopped'

const storageKey = 'digital-agent-session-summaries'
const streamControl = useStreamChat()

function safeSummaries(): SessionSummary[] {
  try {
    const raw = localStorage.getItem(storageKey)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveSummaries(items: SessionSummary[]) {
  try {
    localStorage.setItem(storageKey, JSON.stringify(items.slice(0, 50)))
  } catch {
    /* 隐私模式或存储受限时仍允许当前会话工作。 */
  }
}

function assistantData(value: unknown): ChatData | null {
  if (!value || typeof value !== 'object') return null
  const candidate = value as Partial<ChatData>
  return typeof candidate.reply === 'string' && typeof candidate.session_id === 'string'
    ? candidate as ChatData
    : null
}

export const useAgentStore = defineStore('agent', {
  state: () => ({
    currentSessionId: null as string | null,
    messages: [] as AgentUiMessage[],
    sessions: safeSummaries(),
    loading: false,
    streaming: false,
    error: null as string | null,
    runtime: 'pi',
    runPhase: 'idle' as AgentRunPhase,
    runStatusText: '等待提问',
    activeTool: null as string | null,
    eventCount: 0,
    completedToolCount: 0,
    chartCount: 0,
    lastEventAt: null as string | null,
  }),
  actions: {
    noteEvent() {
      this.eventCount += 1
      this.lastEventAt = new Date().toISOString()
    },
    applyStatus(status: AgentStreamStatus) {
      this.noteEvent()
      if (status.phase === 'bridge' || status.phase === 'planning' || status.phase === 'tooling' || status.phase === 'replying') {
        this.runPhase = status.phase
      }
      this.runStatusText = status.message || this.runStatusText
    },
    resetRunState(text = '等待提问') {
      this.runPhase = 'idle'
      this.runStatusText = text
      this.activeTool = null
      this.eventCount = 0
      this.completedToolCount = 0
      this.chartCount = 0
      this.lastEventAt = null
    },
    async loadSessions() {
      const cached = safeSummaries()
      try {
        const { data } = await fetchAgentSessions(50)
        const remote = data.items.map((item) => ({
          id: item.session_id,
          title: item.last_user_message.slice(0, 32) || '未命名会话',
          createdAt: item.created_at,
          updatedAt: item.updated_at,
          runtime: item.runtime,
          toolCount: item.tool_count,
          messageCount: item.message_count,
        }))
        this.sessions = [...remote, ...cached.filter((item) => !remote.some((remoteItem) => remoteItem.id === item.id))]
        saveSummaries(this.sessions)
      } catch {
        this.sessions = cached
      }
    },
    createSession() {
      this.currentSessionId = null
      this.messages = []
      this.error = null
      this.resetRunState()
    },
    async deleteSession(id: string) {
      this.error = null
      try {
        await deleteAgentSession(id)
        this.sessions = this.sessions.filter((item) => item.id !== id)
        saveSummaries(this.sessions)
        if (this.currentSessionId === id) this.createSession()
      } catch (error) {
        this.error = error instanceof Error ? error.message : '会话删除失败'
      }
    },
    async loadSession(id: string) {
      this.loading = true
      this.error = null
      try {
        const { data } = await fetchAgentSession(id)
        const messages: AgentUiMessage[] = []
        for (const [index, item] of ((data.messages || []) as Array<{ role: string; content: unknown }>).entries()) {
          if (item.role === 'user' && typeof item.content === 'string') {
            messages.push({ id: `${id}-user-${index}`, role: 'user', content: item.content })
          } else if (item.role === 'assistant') {
            const payload = assistantData(item.content)
            if (payload) messages.push({ id: `${id}-assistant-${index}`, role: 'assistant', content: payload.reply, data: payload })
          }
        }
        this.currentSessionId = id
        this.messages = messages
        this.resetRunState('已载入历史会话')
      } catch (error) {
        this.error = error instanceof Error ? error.message : '历史会话加载失败'
      } finally {
        this.loading = false
      }
    },
    stopStreaming() {
      streamControl.stop()
      const assistant = [...this.messages].reverse().find((item) => item.role === 'assistant' && item.streaming)
      if (assistant) assistant.streaming = false
      this.loading = false
      this.streaming = false
      this.runPhase = 'stopped'
      this.runStatusText = '已停止生成'
      this.activeTool = null
    },
    async sendMessage(text: string) {
      const message = text.trim()
      if (!message || this.loading || this.streaming) return
      this.error = null
      this.loading = true
      this.runPhase = 'planning'
      this.runStatusText = '正在发送问题'
      this.activeTool = null
      this.eventCount = 0
      this.completedToolCount = 0
      this.chartCount = 0
      this.lastEventAt = new Date().toISOString()
      const userId = `${Date.now()}-user`
      this.messages.push({ id: userId, role: 'user', content: message })
      const data: ChatData = {
        runtime: this.runtime,
        session_id: this.currentSessionId || '',
        reply: '',
        observed_facts: [],
        inferences: [],
        recommendations: [],
        open_questions: [],
        tool_trace: [],
        llm_model: null,
      }
      const assistant: AgentUiMessage = {
        id: `${Date.now()}-assistant`,
        role: 'assistant',
        content: '',
        data,
        streaming: true,
      }
      this.messages.push(assistant)
      const currentAssistant = () => this.messages.find((item) => item.id === assistant.id) || assistant
      const currentData = () => currentAssistant().data || data
      this.streaming = true
      this.loading = false
      let streamError: Error | null = null
      let completedByServer = false
      try {
        const connection = chatAgentStream(
          { message, session_id: this.currentSessionId || undefined, runtime: this.runtime },
          {
            text: ({ delta }) => {
              this.noteEvent()
              this.runPhase = 'replying'
              this.runStatusText = '正在接收上游 AI 回复'
              const target = currentAssistant()
              const targetData = currentData()
              target.content += delta
              targetData.reply = target.content
            },
            toolStart: ({ tool, args }) => {
              this.noteEvent()
              this.runPhase = 'tooling'
              this.runStatusText = `正在执行 ${tool}`
              this.activeTool = tool
              currentData().tool_trace.push({ tool, args, ok: undefined })
            },
            toolEnd: (item) => {
              this.noteEvent()
              this.completedToolCount += 1
              this.runStatusText = item.ok === false ? `${item.tool} 执行失败` : `${item.tool} 执行完成`
              if (this.activeTool === item.tool) this.activeTool = null
              const targetData = currentData()
              const pending = [...targetData.tool_trace]
                .reverse()
                .find((entry) => entry.tool === item.tool && entry.ok === undefined)
              if (pending) Object.assign(pending, item)
              else targetData.tool_trace.push(item)
            },
            chart: ({ spec }) => {
              this.noteEvent()
              this.chartCount += 1
              this.runStatusText = '已生成会话图表'
              const targetData = currentData()
              const chartStep = [...targetData.tool_trace]
                .reverse()
                .find((entry) => entry.tool === 'render_chart' && entry.ok !== false)
              if (chartStep) chartStep.result = spec
              else targetData.tool_trace.push({ tool: 'render_chart', ok: true, result: spec })
            },
            status: (status) => {
              this.applyStatus(status)
            },
            facts: ({ items }) => { currentData().observed_facts = items },
            inferences: ({ items }) => { currentData().inferences = items },
            recommendations: ({ items }) => { currentData().recommendations = items },
            openQuestions: ({ items }) => { currentData().open_questions = items },
            done: (done) => {
              this.noteEvent()
              completedByServer = true
              const target = currentAssistant()
              const targetData = currentData()
              targetData.session_id = done.session_id
              targetData.runtime = done.runtime || targetData.runtime
              targetData.latency_ms = done.latency_ms ?? undefined
              targetData.pi_fallback = done.pi_fallback
              targetData.pi_status = done.pi_status
              targetData.llm_model = done.llm_model
              target.streaming = false
              this.streaming = false
              this.runPhase = 'done'
              this.runStatusText = '会话完成'
              this.activeTool = null
              this.currentSessionId = done.session_id
              const now = new Date().toISOString()
              const existing = this.sessions.find((item) => item.id === done.session_id)
              const summary: SessionSummary = {
                id: done.session_id,
                title: message.slice(0, 32),
                createdAt: existing?.createdAt || now,
                updatedAt: now,
                runtime: targetData.runtime,
                toolCount: targetData.tool_trace.length,
                messageCount: this.messages.length,
              }
              this.sessions = [summary, ...this.sessions.filter((item) => item.id !== summary.id)]
              saveSummaries(this.sessions)
            },
            error: ({ message: errorMessage }) => {
              this.noteEvent()
              this.runPhase = 'error'
              this.runStatusText = errorMessage || 'Agent 流式执行失败'
              this.activeTool = null
              streamError = new Error(errorMessage || 'Agent 流式执行失败')
            },
          },
        )
        streamControl.attach(connection.abort)
        await connection.completed
        if (streamError) throw streamError
        if (!completedByServer && this.streaming) throw new Error('流式响应提前结束，请重试')
      } catch (error) {
        this.error = error instanceof Error ? error.message : '对话失败'
        this.runPhase = 'error'
        this.runStatusText = this.error
        this.activeTool = null
      } finally {
        streamControl.release()
        currentAssistant().streaming = false
        this.loading = false
        this.streaming = false
      }
    },
    async retryTool(item: ToolTraceItem) {
      const hint = item.tool === 'render_chart' ? '请重新生成刚才的图表。' : `请重试工具 ${item.tool} 并说明结果。`
      await this.sendMessage(hint)
    },
  },
})
