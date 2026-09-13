<script setup lang="ts">
/** 思考过程折叠面板：思考中显示脉冲动画，完成后可折叠回看 */
import { ref, watch } from 'vue'

const props = defineProps<{
  reasoning: string
  active: boolean
}>()

const open = ref(false)
watch(
  () => props.active,
  (v) => {
    if (v) open.value = true
  },
)
</script>

<template>
  <div class="thinking" :class="{ active }">
    <button class="thinking-head" type="button" @click="open = !open">
      <span v-if="active" class="thinking-dots"><i></i><i></i><i></i></span>
      <span class="thinking-label">{{ active ? '思考中…' : '思考过程' }}</span>
      <span class="thinking-arrow" :class="{ open }">▾</span>
    </button>
    <pre v-show="open" class="thinking-body">{{ reasoning || '（暂无思考内容）' }}</pre>
  </div>
</template>

<style scoped>
.thinking {
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 10px;
  overflow: hidden;
  background: var(--bg-soft);
}
.thinking.active {
  border-color: var(--accent-weak);
}
.thinking-head {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 12px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12.5px;
  color: var(--text-dim);
}
.thinking-label {
  flex: 1;
  text-align: left;
}
.thinking-arrow {
  transition: transform 0.15s;
}
.thinking-arrow.open {
  transform: rotate(180deg);
}
.thinking-body {
  margin: 0;
  padding: 10px 12px;
  max-height: 200px;
  overflow-y: auto;
  font-size: 12px;
  line-height: 1.7;
  color: var(--text-dim);
  white-space: pre-wrap;
  border-top: 1px dashed var(--border);
}
.thinking-dots {
  display: inline-flex;
  gap: 3px;
}
.thinking-dots i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--accent);
  animation: blink 1.2s infinite ease-in-out;
}
.thinking-dots i:nth-child(2) {
  animation-delay: 0.2s;
}
.thinking-dots i:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes blink {
  0%,
  80%,
  100% {
    opacity: 0.25;
  }
  40% {
    opacity: 1;
  }
}
</style>
