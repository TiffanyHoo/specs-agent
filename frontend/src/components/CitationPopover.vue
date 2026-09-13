<script setup lang="ts">
/** 引用溯源悬浮卡片：全局唯一实例，通过 Teleport 挂到 body，fixed 定位跟随角标 */
import type { SourceChunk } from '../types'

const props = defineProps<{
  source: SourceChunk | null
  x: number
  y: number
}>()

const emit = defineEmits<{ close: [] }>()
void props
</script>

<template>
  <Teleport to="body">
    <div v-if="source" class="popover-mask" @click="emit('close')">
      <div
        class="popover"
        :style="{ left: `${x}px`, top: `${y}px` }"
        @click.stop
      >
        <div class="popover-title">《{{ source.doc_title }}》{{ source.section }}</div>
        <div class="popover-body">{{ source.content }}</div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.popover-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
}
.popover {
  position: fixed;
  transform: translate(-50%, calc(-100% - 10px));
  width: min(420px, 86vw);
  max-height: 280px;
  overflow-y: auto;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 8px 28px rgb(0 0 0 / 14%);
  padding: 12px 14px;
  cursor: default;
}
.popover-title {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--accent);
  margin-bottom: 6px;
}
.popover-body {
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  color: var(--text);
}
</style>
