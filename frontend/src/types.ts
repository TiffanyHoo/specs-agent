/** 与后端 NDJSON 事件契约一一对应（见 backend/main.py） */
export type Mode = 'chat' | 'review'

export interface SourceChunk {
  n: number
  id: string
  doc_title: string
  section: string
  content: string
  score: number
}

export interface ReviewItem {
  clause_n: number | null
  clause_id: string | null
  section: string | null
  severity: 'high' | 'medium' | 'low'
  issue: string
  quote: string
  suggestion: string
  /** grade 判定规范未覆盖时的占位 */
  uncovered?: boolean
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  mode: Mode
  reasoning?: string
  sources?: SourceChunk[]
  reviewItems?: ReviewItem[]
  streaming?: boolean
  /** 仅收到 reasoning、尚未开始回答 */
  thinking?: boolean
  error?: string
}
