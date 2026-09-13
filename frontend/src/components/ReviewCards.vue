<script setup lang="ts">
/** 违规结果卡片：严重度着色，展示条款出处、问题、代码片段与修复建议 */
import type { ReviewItem } from '../types'

defineProps<{ items: ReviewItem[] }>()

const SEVERITY_LABEL: Record<ReviewItem['severity'], string> = {
  high: '严重',
  medium: '一般',
  low: '提示',
}
</script>

<template>
  <div class="review-cards">
    <div v-if="items.some((i) => i.uncovered)" class="review-uncovered">
      规范未覆盖该代码场景，无法给出有依据的审查结论。
    </div>
    <div
      v-for="(item, i) in items.filter((it) => !it.uncovered)"
      :key="i"
      class="review-card"
      :class="item.severity"
    >
      <div class="review-head">
        <span class="badge" :class="item.severity">{{ SEVERITY_LABEL[item.severity] }}</span>
        <span v-if="item.section" class="review-clause">《{{ item.section.split(' > ')[0] }}》{{ item.section }}</span>
      </div>
      <div class="review-issue">{{ item.issue }}</div>
      <pre v-if="item.quote" class="review-quote">{{ item.quote }}</pre>
      <div class="review-fix"><b>建议</b>{{ item.suggestion }}</div>
    </div>
    <div v-if="!items.some((it) => !it.uncovered)" class="review-clean">
      未发现违反规范的问题。
    </div>
  </div>
</template>

<style scoped>
.review-card {
  border: 1px solid var(--border);
  border-left: 3px solid var(--severity-medium);
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: var(--panel);
}
.review-card.high {
  border-left-color: var(--severity-high);
}
.review-card.low {
  border-left-color: var(--severity-low);
}
.review-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}
.badge {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 999px;
  color: #fff;
  background: var(--severity-medium);
}
.badge.high {
  background: var(--severity-high);
}
.badge.low {
  background: var(--severity-low);
}
.review-clause {
  font-size: 12px;
  color: var(--text-dim);
}
.review-issue {
  font-size: 13.5px;
  line-height: 1.6;
}
.review-quote {
  margin: 8px 0;
  padding: 8px 10px;
  background: var(--bg-soft);
  border-radius: 8px;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
}
.review-fix {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-dim);
}
.review-fix b {
  color: var(--accent);
  margin-right: 6px;
}
.review-uncovered,
.review-clean {
  font-size: 13px;
  color: var(--text-dim);
  padding: 8px 0;
}
</style>
