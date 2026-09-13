<script setup lang="ts">
/** 消息气泡：用户消息 / 助手消息（Markdown + 角标 popover + 思考折叠 + 审查卡片） */
import { computed, ref } from 'vue'
import type { Message, SourceChunk } from '../types'
import { renderMessage } from '../utils/markdown'
import CitationPopover from './CitationPopover.vue'
import ReviewCards from './ReviewCards.vue'
import ThinkingPanel from './ThinkingPanel.vue'

const props = defineProps<{ message: Message }>()

const rendered = computed(() =>
  props.message.role === 'assistant'
    ? renderMessage(props.message.content, props.message.sources)
    : props.message.content,
)

const popover = ref<{ source: SourceChunk; x: number; y: number } | null>(null)

function onBodyClick(e: MouseEvent): void {
  const el = (e.target as HTMLElement).closest?.('.cite') as HTMLElement | null
  if (!el) {
    popover.value = null
    return
  }
  const source = props.message.sources?.[Number(el.dataset.n) - 1]
  if (!source) return
  const rect = el.getBoundingClientRect()
  popover.value = { source, x: rect.left + rect.width / 2, y: rect.top }
}
</script>

<template>
  <div class="msg" :class="message.role">
    <div class="avatar">{{ message.role === 'user' ? '我' : '规' }}</div>
    <div class="bubble">
      <!-- 审查结果卡片 -->
      <ReviewCards v-if="message.role === 'assistant' && message.reviewItems?.length" :items="message.reviewItems" />

      <ThinkingPanel
        v-if="message.role === 'assistant' && (message.reasoning || message.thinking)"
        :reasoning="message.reasoning ?? ''"
        :active="!!message.thinking"
      />

      <!-- 问答正文 -->
      <div
        v-if="message.content"
        class="md"
        @click="onBodyClick"
        v-html="rendered"
      ></div>
      <div v-else-if="message.role === 'assistant' && !message.thinking && message.streaming" class="waiting">
        检索规范条款中…
      </div>

      <!-- 引用来源条 -->
      <div v-if="message.sources?.length" class="sources">
        <span class="sources-label">来源</span>
        <span v-for="s in message.sources" :key="s.id" class="source-chip">[{{ s.n }}] {{ s.section }}</span>
      </div>

      <div v-if="message.error" class="msg-error">出错了：{{ message.error }}</div>
      <CitationPopover
        :source="popover?.source ?? null"
        :x="popover?.x ?? 0"
        :y="popover?.y ?? 0"
        @close="popover = null"
      />
    </div>
  </div>
</template>

<style scoped>
.msg {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.msg.user {
  flex-direction: row-reverse;
}
.avatar {
  flex: none;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  font-size: 13px;
  color: #fff;
  background: linear-gradient(135deg, #6b7cff, #4f46e5);
}
.msg.user .avatar {
  background: linear-gradient(135deg, #9ca3af, #6b7280);
}
.bubble {
  position: relative;
  max-width: min(760px, 88%);
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 10px 14px;
}
.msg.user .bubble {
  background: var(--accent-weak);
  border-color: transparent;
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.6;
}
.waiting {
  font-size: 13px;
  color: var(--text-dim);
}
.sources {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed var(--border);
}
.sources-label {
  font-size: 12px;
  color: var(--text-dim);
}
.source-chip {
  font-size: 11.5px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--bg-soft);
  color: var(--text-dim);
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.msg-error {
  margin-top: 8px;
  font-size: 13px;
  color: var(--severity-high);
}
</style>
