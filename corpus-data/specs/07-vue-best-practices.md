# Vue 组件编写规范

## script setup 与组合式 API

- 新代码统一使用 `<script setup lang="ts">`，禁止新增 Options API 组件。
- 组件内部逻辑按区块组织：props/emits → 响应式状态 → computed → 生命周期 → 方法。
- 对外暴露仅需 `defineExpose` 显式声明，禁止暴露内部实现细节。

## 响应式选择 ref 与 reactive

- 单值状态一律使用 `ref`；`reactive` 仅用于组合多个属性的局部状态对象。
- 禁止对 `reactive` 对象解构（丢失响应性），需要时使用 `toRefs`。
- `ref` 在模板中自动解包，脚本中必须带 `.value`。

## computed 与 watch

- 派生状态一律使用 `computed`，禁止在 `watch` 中手动同步派生值。
- `watch` 回调中禁止修改自身依赖的源，避免循环触发。
- 副作用（请求、DOM、定时器）放 `watchEffect` / `watch` 时必须考虑清理。
- 深层监听 `deep: true` 需评估性能成本，大对象禁止深度监听。

## v-for 与 key

- `v-for` 必须绑定稳定唯一 key，使用业务 ID，禁止使用数组索引（静态一次性列表除外）。
- 禁止 `v-for` 与 `v-if` 同节点使用：过滤用 computed 预处理。
- `v-for` 内禁止修改遍历源数组。

## 生命周期与清理

- 定时器、事件监听、观察者必须在 `onUnmounted` 或 watch 清理函数中销毁。
- 数据请求放在 `onMounted`；SSR 场景改用服务端钩子。
- 组件卸载后的异步回调必须防泄漏：使用 AbortController 或卸载标记位。
