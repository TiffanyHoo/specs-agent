# 状态管理规范

## Store 划分

- 全局状态使用 Pinia，按业务域拆分 store：`useUserStore`、`useOrderStore`，禁止单一巨型 store。
- store 只存放跨组件共享的状态；组件私有状态保留在组件内，禁止一切状态入 store。
- 服务端数据的缓存优先由请求层管理（SWRV/自建缓存），store 不做接口数据的二次镜像。

## Store 编写

- 统一使用 setup store 语法（`defineStore` + 组合式函数写法）。
- store 内的异步动作必须处理错误并返回明确结果，禁止吞异常。
- 派生数据一律用 getter（computed），禁止在 action 中手动维护冗余副本。

## 持久化与初始化

- 需要持久化的状态（登录态、偏好设置）显式声明持久化 key 与字段，禁止整 store 落盘。
- 敏感信息（token）默认放内存 + sessionStorage，禁止写 localStorage 明文。
- store 必须提供 `reset()` 用于登出与测试清理。

## 使用约束

- 组件中禁止在 `watch`/生命周期外直接修改 store 之外的引用；修改一律通过 action。
- 禁止 store 之间循环依赖；跨 store 协作在 action 中显式引入对方实例。
- store 命名文件与 store 同名：`useUserStore` 对应 `stores/user.ts`。
