# TypeScript 编码规范

## 严格模式与 any

- 项目必须开启 `strict: true`；禁止通过关闭编译选项绕过类型错误。
- 禁止使用 `any`；不确定类型时优先 `unknown` + 类型收窄。
- 第三方库缺失类型时使用 `declare module` 补充声明，禁止整文件 `@ts-nocheck`。
- `@ts-ignore` 必须携带原因注释，并优先替换为 `@ts-expect-error`（错误消失时编译报错提醒清理）。

## 类型定义与命名

- 类型与接口使用 PascalCase，不加 `I` 前缀：`UserInfo`、`OrderStatus`。
- 接口与 type 的选择：对象结构用 `interface`，联合、工具类型用 `type`。
- API 响应类型统一放在 api 模块内并导出；组件间共享类型放 `types/` 目录。
- 类型导入使用 `import type`，避免运行时误引入。

## 枚举与联合类型

- 字面量集合优先使用 `as const` 对象 + `typeof` 推导，其次是 `enum`；字符串 union 适合轻量场景。
- 状态类取值必须收敛为联合类型，禁止裸 string 传递状态。

## 泛型使用

- 泛型参数使用语义化名称：`TItem`、`TResponse`，避免裸 `T2`、`K1`。
- 通用请求、列表、分页逻辑必须泛型化复用，如 `usePagination<TItem>()`。

## 类型断言

- `as` 断言仅允许用于确知运行时结构的边界（如 JSON 反序列化），并尽量用类型守卫替代。
- 禁止双重断言 `as unknown as T`；确需时必须在评审中说明。
- DOM 查询结果必须判空后再断言，如 `as HTMLInputElement` 前先校验非空。
