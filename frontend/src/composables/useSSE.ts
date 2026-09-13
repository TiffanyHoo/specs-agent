/**
 * POST + ReadableStream 消费后端 NDJSON 事件流。
 * 不用 EventSource：它不支持 POST，也无法携带 JSON body。
 */
import type { ReviewItem, SourceChunk } from '../types'

export interface StreamCallbacks {
  onToken?(content: string): void
  onReasoning?(content: string): void
  onSources?(sources: SourceChunk[]): void
  onReviewItem?(item: ReviewItem): void
  onError?(message: string): void
}

interface WireEvent {
  type: 'token' | 'reasoning' | 'sources' | 'review_item' | 'error'
  content?: string
  sources?: SourceChunk[]
  item?: ReviewItem
  message?: string
}

export async function streamSSE(
  endpoint: 'chat' | 'review',
  body: { question: string; top_k?: number },
  cb: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`/api/${endpoint}/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  if (!res.ok || !res.body) {
    throw new Error(`请求失败：HTTP ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const dispatch = (raw: string): void => {
    const line = raw.trim()
    if (!line) return
    let ev: WireEvent
    try {
      ev = JSON.parse(line) as WireEvent
    } catch {
      return // 忽略半包/脏数据
    }
    switch (ev.type) {
      case 'token':
        cb.onToken?.(ev.content ?? '')
        break
      case 'reasoning':
        cb.onReasoning?.(ev.content ?? '')
        break
      case 'sources':
        cb.onSources?.(ev.sources ?? [])
        break
      case 'review_item':
        if (ev.item) cb.onReviewItem?.(ev.item)
        break
      case 'error':
        cb.onError?.(ev.message ?? '未知错误')
        break
    }
  }

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? '' // 末段可能不完整，留到下一轮
    parts.forEach(dispatch)
  }
  dispatch(buffer)
}
