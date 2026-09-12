# 项目目录结构

## 总体结构

```text
src/
├── api/            # 接口层：按域拆分模块
├── components/     # 公共通用组件
├── composables/    # 公共组合式函数
├── features/       # 业务域模块（按业务垂直拆分）
├── router/         # 路由配置
├── stores/         # 全局状态
├── styles/         # 全局样式与设计令牌
├── utils/          # 纯函数工具
└── main.ts
```

## features 业务域

- 每个业务域独立成目录，内部自带 `components/`、`composables/`、`api.ts`（或复用全局 api）。
- 跨域复用的逻辑必须上提到全局 `composables/` 或 `components/`，禁止 feature 之间互相 import。
- 域内组件命名不带域名前缀；域外引用时由路径体现归属。

## components 公共组件

- 仅存放两个及以上业务域复用的组件；只服务单一域的组件放域内。
- 每个公共组件目录包含：组件文件、类型定义、`README.md` 或 demo。
- 公共组件必须无业务依赖：不 import 任何 feature 目录与 stores 中的业务 store。

## api 接口层

- 接口按后端域拆分文件，如 `api/order.ts`、`api/user.ts`。
- api 模块只做请求与类型定义，禁止包含组件状态逻辑。
- 所有接口函数必须显式声明请求与响应类型，禁止裸用 `any`。

## composables 目录

- 组合式函数按能力命名文件：`useAuth.ts`、`usePagination.ts`。
- 一个文件一个 composable；超过 200 行应拆分。
- 组合式函数必须返回纯值与函数，不直接操作 DOM 组件实例。
