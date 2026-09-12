# Git 提交与分支规范

## 提交信息（Conventional Commits）

- 提交信息格式：`type(scope): subject`，如 `feat(order): 支持批量导出`。
- type 取值：`feat`、`fix`、`refactor`、`style`、`perf`、`test`、`docs`、`chore`、`build`、`ci`。
- scope 为业务域或模块名，使用 kebab-case。
- subject 使用中文或英文祈使句，结尾不加句号，长度不超过 50 字符。
- 破坏性变更必须携带 `!` 并在正文标注 `BREAKING CHANGE:`。

## 分支命名

- 功能分支：`feat/<工单号>-<短描述>`，如 `feat/ORD-1024-order-export`。
- 修复分支：`fix/<工单号>-<短描述>`。
- 发布分支：`release/v<版本号>`；热修复分支：`hotfix/v<版本号>`。
- 禁止使用个人名、`test`、`tmp` 等无语义分支名。

## 合并请求（MR）

- MR 目标分支为 develop 或当前迭代集成分支，禁止直接向 main 提交。
- MR 描述必须包含：变更目的、影响范围、自测结论。
- 至少 1 名评审人批准且流水线通过方可合并；合并方式默认 squash。

## 提交粒度

- 一次提交只做一件事：新增功能、修复缺陷、格式化不混在同一提交。
- 提交前必须通过 lint 与类型检查；禁止提交注释掉的死代码与调试语句。
