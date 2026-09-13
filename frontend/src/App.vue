<script setup lang="ts">
/** 主界面：模式切换（问答/审查）+ 消息流 + 自动滚动 + 输入区 */
import { nextTick, ref, watch } from 'vue'
import ChatInput from './components/ChatInput.vue'
import MessageBubble from './components/MessageBubble.vue'
import { useChatStore } from './stores/chat'

const store = useChatStore()
const listRef = ref<HTMLElement | null>(null)

// 消息数量或最后一条消息长度变化时滚到底部（流式跟随）
watch(
  () => {
    const last = store.messages[store.messages.length - 1]
    return (
      store.messages.length * 1000 +
      (last?.content.length ?? 0) +
      (last?.reasoning?.length ?? 0) +
      (last?.reviewItems?.length ?? 0)
    )
  },
  () => {
    nextTick(() => listRef.value?.scrollTo({ top: listRef.value.scrollHeight }))
  },
)
</script>

<template>
  <div class="app">
    <header class="header">
      <div class="title">
        前端工程规范问答 Agent
        <span class="subtitle">RAG 引用溯源 · 流式输出 · 代码审查</span>
      </div>
      <div class="mode-switch">
        <button
          class="mode-btn"
          :class="{ on: store.mode === 'chat' }"
          @click="store.mode = 'chat'"
        >
          规范问答
        </button>
        <button
          class="mode-btn"
          :class="{ on: store.mode === 'review' }"
          @click="store.mode = 'review'"
        >
          代码审查
        </button>
      </div>
      <button class="clear-btn" :disabled="store.busy || !store.messages.length" @click="store.clear">
        清空
      </button>
    </header>

    <main ref="listRef" class="chat-list">
      <div v-if="!store.messages.length" class="empty">
        <h2>问我任何前端工程规范问题</h2>
        <p>回答基于规范知识库检索，每个结论都带 [n] 引用角标，hover 可查看原文条款。</p>
        <div class="hints">
          <button @click="store.send('CSS 类名应该怎么命名？')">CSS 类名应该怎么命名？</button>
          <button @click="store.send('组件的 props 有什么设计要求？')">组件的 props 有什么设计要求？</button>
          <button @click="store.send('生产环境可以打印用户手机号吗？')">生产环境可以打印用户手机号吗？</button>
        </div>
      </div>
      <MessageBubble v-for="(m, i) in store.messages" :key="i" :message="m" />
    </main>

    <footer class="footer">
      <ChatInput />
    </footer>
  </div>
</template>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 900px;
  margin: 0 auto;
}
.header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 4px;
  border-bottom: 1px solid var(--border);
}
.title {
  font-weight: 700;
  font-size: 16px;
  margin-right: auto;
}
.subtitle {
  font-weight: 400;
  font-size: 12px;
  color: var(--text-dim);
  margin-left: 8px;
}
.mode-switch {
  display: flex;
  background: var(--bg-soft);
  border-radius: 10px;
  padding: 3px;
}
.mode-btn {
  border: none;
  background: none;
  padding: 6px 14px;
  font-size: 13px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-dim);
}
.mode-btn.on {
  background: var(--panel);
  color: var(--accent);
  font-weight: 600;
  box-shadow: 0 1px 4px rgb(0 0 0 / 8%);
}
.clear-btn {
  border: none;
  background: none;
  font-size: 13px;
  color: var(--text-dim);
  cursor: pointer;
}
.clear-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.chat-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 4px;
}
.empty {
  text-align: center;
  margin-top: 12vh;
  color: var(--text-dim);
}
.empty h2 {
  color: var(--text);
  font-size: 20px;
  margin-bottom: 8px;
}
.empty p {
  font-size: 13.5px;
}
.hints {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 18px;
  flex-wrap: wrap;
}
.hints button {
  border: 1px solid var(--border);
  background: var(--panel);
  border-radius: 999px;
  padding: 7px 14px;
  font-size: 13px;
  cursor: pointer;
  color: var(--text);
}
.hints button:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.footer {
  padding: 10px 0 16px;
}
</style>
