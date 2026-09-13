/** 会话状态：消息列表 + 流式接收 + 两模式切换 */
import { defineStore } from 'pinia'
import { reactive, ref } from 'vue'
import { streamSSE } from '../composables/useSSE'
import type { Message, Mode } from '../types'

export const useChatStore = defineStore('chat', () => {
  const mode = ref<Mode>('chat')
  const messages = ref<Message[]>([])
  const busy = ref(false)
  let controller: AbortController | null = null

  async function send(text: string): Promise<void> {
    const question = text.trim()
    if (busy.value || !question) return
    busy.value = true
    messages.value.push({ role: 'user', content: question, mode: mode.value })

    const m = reactive<Message>({
      role: 'assistant',
      content: '',
      mode: mode.value,
      reasoning: '',
      sources: [],
      reviewItems: [],
      streaming: true,
      thinking: true,
    })
    messages.value.push(m)
    controller = new AbortController()

    const endpoint = m.mode
    try {
      await streamSSE(
        endpoint,
        { question, top_k: 5 },
        {
          onToken: (c) => {
            m.thinking = false
            m.content += c
          },
          onReasoning: (c) => {
            m.reasoning = (m.reasoning ?? '') + c
          },
          onSources: (s) => {
            m.sources = s
          },
          onReviewItem: (item) => {
            m.thinking = false
            m.reviewItems?.push(item)
          },
          onError: (msg) => {
            m.error = msg
          },
        },
        controller.signal,
      )
    } catch (e) {
      if (!controller.signal.aborted) {
        m.error = e instanceof Error ? e.message : String(e)
      }
    } finally {
      m.streaming = false
      m.thinking = false
      busy.value = false
      controller = null
    }
  }

  function stop(): void {
    controller?.abort()
    controller = null
    busy.value = false
    const last = messages.value[messages.value.length - 1]
    if (last?.role === 'assistant') {
      last.streaming = false
      last.thinking = false
    }
  }

  function clear(): void {
    if (busy.value) return
    messages.value = []
  }

  return { mode, messages, busy, send, stop, clear }
})
