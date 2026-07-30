import axios, { type AxiosError } from 'axios'

/** 后端统一 envelope */
export interface ApiEnvelope<T> {
  ok: boolean
  data: T | null
  error: { code: string; message: string; detail?: Record<string, unknown> } | null
  request_id: string
}

const baseURL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  'http://127.0.0.1:8000/api/v1'

export const http = axios.create({
  baseURL,
  timeout: 30000,
})

function unwrapError(err: unknown): Error {
  const ax = err as AxiosError<ApiEnvelope<unknown>>
  if (ax.response?.data?.error?.message) {
    return new Error(ax.response.data.error.message)
  }
  if (err instanceof Error && err.message) {
    return err
  }
  return new Error('网络错误，请确认后端已启动')
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
