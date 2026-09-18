---
type: repository-guide
status: active
tags:
  - documentation
  - formatting
---

# 文档排版规范

本规范以四份 TIDE 数学教材为基准：
[[20-tide-decentralized-neural-network/settlegraph-learning-note|SettleGraph]]、
[[20-tide-decentralized-neural-network/timed-dag-region-selector-learning-note|TimedDAG 区域选择]]、
[[20-tide-decentralized-neural-network/timed-dag-chunk-prefill-learning-note|TimedDAG 分块预填充]]、
[[20-tide-decentralized-neural-network/positive-delay-graph-finite-cut-learning-note|正时延有限切面]]。

正文遵循标准 Markdown；数学、双链、块引用和 Callout 使用 Obsidian 支持的扩展语法。

## Markdown 结构

- 每个文档只使用一个 `#` 标题；下级标题按层级递进，不跳级，不在标题中嵌入 HTML 标签或样式属性。
- 普通段落写成一段一行，段落之间空一行。建议启用 Obsidian 的 `strictLineBreaks`（严格换行）；不要用源码换行、行尾两个空格、单反斜杠或 `<br>` 制造视觉换行。
- 标题、列表、引用、代码块、表格和独立公式前后留空行。列表内的续段与公式须缩进到父项正文列；嵌套层级保持一致，不要意外变成代码块。
- 内部链接优先使用 `[[文件|显示文本]]` 或 `[[文件#标题|显示文本]]`，提交前检查目标文件和标题均存在。

## 数学公式

- 行内公式使用 `$...$`，不跨源码行；过长的行内推导改为独立公式。独立公式使用单独成行的 `$$` 定界符。
- 长公式使用 `aligned`、`gathered` 或 `cases`，在语义运算符处用 `\\` 换行并用 `&` 对齐。不要依赖浏览器自动折行来保持等式结构。
- 用 `\;` 等命令表示必要间距；重排时保留符号、运算顺序和条件，不借排版修改数学结论。
- 不在 Obsidian 数学块中使用 `\label`、`\eqref` 作为锚点；需要编号时用简短的 `\tag{1}` 或 `\tag{AR-1}`，不要把长标题放进编号。公式块后另起一行写 `^block-id`，再空一行接正文；引用用 `[[文件#^block-id|式号]]`。
- 公式中确需颜色时使用 MathJax 的 `\color{...}`；不要用 HTML 字体标签包裹正文或公式。

## 表格、Callout 与分页

- 表格单元格保持短小；长证据、解释和链接改成列表或分段 Callout。表格每行列数必须一致，表头后紧跟分隔行。
- 表格中的竖线须转义；数学条件竖线优先用 `\mid`，避免被解析成分列。
- Callout 使用 `> [!type] 标题` 开始，正文每行都保留 `>`。`|page` 只用于教材中经过验证的显式分页。
- 需要整页保留的公式、表格或 Callout 必须先在 A4 导出中验证，避免把大块内容强行设置为不可拆分。

## Frontmatter 与 PDF 验收

- 活跃文档至少包含 `type`、`status`、`tags`。数学教材增加 `cssclasses: [textbook-math]`；证据表文档按需增加 `compact-evidence-table`。
- 导出前选择 A4、纵向、100% 缩放，按实际页边距检查正文、公式、表格和代码块。建议以左右各 20 mm、正文宽约 170 mm 验收；屏幕上可以横向滚动不代表 PDF 能完整打印。MathJax 不得出现错误占位符，公式不能被裁切。
- 归档和 `scratch` 草稿可以保留历史写法，但只要纳入正式阅读或 PDF 导出，就应按本规范整理。
