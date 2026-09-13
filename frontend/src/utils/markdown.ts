/** 引用溯源：[n] 角标 → 可 hover 的 <sup class="cite">，代码块内不替换 */
import MarkdownIt from 'markdown-it'
import type { SourceChunk } from '../types'

export const md = new MarkdownIt({ breaks: true, linkify: true })

export function renderMessage(content: string, sources: SourceChunk[] = []): string {
  const html = md.render(content)
  // 按 <pre>/<code> 分段，仅代码外做角标替换，避免破坏代码块
  return html
    .split(/(<pre[\s\S]*?<\/pre>|<code[\s\S]*?<\/code>)/g)
    .map((part) =>
      part.startsWith('<pre') || part.startsWith('<code')
        ? part
        : part.replace(/\[(\d{1,2})\]/g, (raw, n: string) =>
            sources[Number(n) - 1]
              ? `<sup class="cite" data-n="${n}" title="来源 ${n}">${n}</sup>`
              : raw,
          ),
    )
    .join('')
}
