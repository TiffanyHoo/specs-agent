# 前端安全规范

## XSS 防护

- 默认使用插值与模板绑定渲染；`v-html` 仅允许用于可信来源内容，且必须经过 DOMPurify 消毒。
- URL 类输入渲染前校验协议白名单（http/https），禁止 `javascript:` 伪协议注入。
- 动态拼接 HTML 字符串被禁止；富文本必须走统一的消毒管道。

## CSRF 与鉴权

- token 存储遵循最小暴露：默认内存 + sessionStorage，禁止 localStorage 明文长期持有。
- 依赖 Cookie 鉴权时后端启用 SameSite 与 CSRF Token，前端不得随意关闭凭证策略。
- 登出与 token 失效必须清理内存、存储与全局状态中的全部痕迹。

## 依赖与供应链

- 新增依赖必须评审维护活跃度与体积；锁定版本，禁止使用 `*` 与 `latest`。
- 定期执行依赖漏洞扫描，高危漏洞 48 小时内升级或规避。
- 禁止从非官方源安装包；启用 lockfile 校验。

## 敏感数据与其他

- 源码、日志、埋点中禁止出现密钥、完整手机号、身份证等敏感信息；必要时脱敏展示。
- 生产环境关闭 sourcemap 上传至公开路径；调试面板与 vConsole 仅在灰度/测试包启用。
- 外链必须 `rel="noopener noreferrer"`；iframe 嵌入第三方内容须沙箱化。
