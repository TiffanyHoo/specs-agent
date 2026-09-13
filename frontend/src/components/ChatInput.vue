<script setup lang="ts">
/** 输入区：问答模式普通输入；审查模式适配代码粘贴（Ctrl+Enter 发送） */
import { ref } from 'vue'
import { useChatStore } from '../stores/chat'

const store = useChatStore()
const text = ref('')

function send(): void {
  if (!text.value.trim() || store.busy) return
  store.send(text.value)
  text.value = ''
}

function onKeydown(e: KeyboardEvent): void {
  if (e.key === 'Enter' && (e.ctrlKey || !e.shiftKey)) {
    e.preventDefault()
    send()
  }
}
</script>

<template>
  <div class="input-bar">
    <textarea
      v-model="text"
      rows="3"
      :placeholder="
        store.mode === 'review'
          ? '粘贴待审查代码（可附说明），Ctrl+Enter 发送'
          : '输入前端规范问题，如：组件的 props 应该怎么设计？（Enter 发送，Shift+Enter 换行）'
      "
      @keydown="onKeydown"
    ></textarea>
    <div class="input-actions">
      <span v-if="store.busy" class="stream-hint">生成中…</span>
      <button v-if="store.busy" class="btn ghost" @click="store.stop">停止</button>
      <button class="btn primary" :disabled="store.busy || !text.trim()" @click="send">
        {{ store.mode === 'review' ? '审查' : '发送' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.input-bar {
  border: 1px solid var(--border);
  background: var(--panel);
  border-radius: 14px;
  padding: 10px 12px;
}
textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  font: inherit;
  font-size: 14px;
  line-height: 1.6;
  background: transparent;
  color: var(--text);
  font-family: var(--mono);
}
.input-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}
.stream-hint {
  font-size: 12px;
  color: var(--text-dim);
  margin-right: auto;
}
.btn {
  border: none;
  border-radius: 9px;
  padding: 7px 18px;
  font-size: 13.5px;
  cursor: pointer;
}
.btn.primary {
  background: var(--accent);
  color: #fff;
}
.btn.primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.btn.ghost {
  background: var(--bg-soft);
  color: var(--text-dim);
}
</style>
