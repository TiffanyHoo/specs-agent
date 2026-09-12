# 命名规范

统一的命名是代码可读性的第一道防线。本规范适用于所有前端项目。

## 变量与函数命名

- 变量与函数使用小驼峰 camelCase：`userName`、`fetchOrderList`。
- 布尔值必须带前缀 `is / has / should / can`，如 `isLoading`、`hasPermission`。
- 事件处理函数以 `handle` 开头，如 `handleSubmit`；回调 prop 以 `on` 开头，如 `onClose`。
- 异步取数函数以 `fetch` / `load` 开头；格式化函数以 `format` 开头。
- 禁止使用无意义命名：`data1`、`temp`、`foo`、单字母变量（循环索引 `i/j/k` 除外）。

## 组件命名

- 组件名使用大驼峰 PascalCase，且为至少两个单词的组合，如 `UserCard`、`OrderTable`。
- 禁止与 HTML 原生标签重名或仅单词命名，如 `Table`、`Button` 需改为 `BaseTable`、`ProButton`。
- 页面级组件以 `Page` 或 `View` 结尾，如 `OrderListPage`。
- 抽象通用组件以 `Base`、`Pro`、`App` 前缀区分层级。

## 常量命名

- 常量使用大写下划线 UPPER_SNAKE_CASE，如 `MAX_RETRY_COUNT`、`DEFAULT_PAGE_SIZE`。
- 枚举语义的常量集合使用 const 对象或 `Object.freeze`，命名以复数形式，如 `ORDER_STATUS`。

## CSS 类名命名

- 类名统一采用 BEM：`block__element--modifier`，如 `user-card__avatar--active`。
- 工具类允许使用语义短横线命名，如 `is-hidden`、`u-text-center`。
- 禁止拼音命名与无意义缩写；缩写仅限业界通用词，如 `btn`、`nav`。

## 文件与目录命名

- 组件文件与组件同名 PascalCase：`UserCard.vue`。
- composable 文件以 `use` 开头 camelCase：`useAuth.ts`。
- 普通工具模块使用 camelCase：`dateUtils.ts`；目录名使用 kebab-case：`user-center/`。
- 测试文件与被测文件同名加 `.spec` / `.test` 后缀。
