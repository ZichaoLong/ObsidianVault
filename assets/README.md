# 插图与编辑入口

五张简单图以手工 SVG 为维护源，三张架构图继续以原 PPTX 为维护源。SVG 源和 PPTX 随 Git 保存；从它们导出的 PNG、PDF、架构图 SVG 及日常检查报告按[生成物约定](../ARTIFACTS.md)在本地重建。

## 简单图：直接编辑 SVG

| 图示 | 维护源 | PNG 导出 |
|---|---|---|
| 有状态网络与 Load/Store 窗口 | [SVG](images/load-store-progression-01.svg) | [PNG](images/load-store-progression-01.png) |
| 布尔电路与一次求值 | [SVG](images/ai-time-scaling-law-theoretical-evidence-01.svg) | [PNG](images/ai-time-scaling-law-theoretical-evidence-01.png) |
| 常深度与多项式扇入 | [SVG](images/ai-time-scaling-law-theoretical-evidence-02.svg) | [PNG](images/ai-time-scaling-law-theoretical-evidence-02.png) |
| 图灵机状态转移与纸带 | [SVG](images/control-feedback-token-instruction-opcode-operands-01.svg) | [PNG](images/control-feedback-token-instruction-opcode-operands-01.png) |
| 多带图灵机与单带编码 | [SVG](images/control-feedback-token-instruction-opcode-operands-02.svg) | [PNG](images/control-feedback-token-instruction-opcode-operands-02.png) |

用 Inkscape 打开 SVG，按 `T` 改文字，使用选择工具移动或缩放图形。逻辑门、状态、纸带和标注分别编组；移动节点后需相应调整连接线端点。保存 SVG 后运行生成命令即可更新 PNG，生成器不会覆盖这些手工 SVG。

这些图重画自历史 PNG，保留原有运算符、状态转移、纸带符号、读写头位置与连接关系；字体、线宽和少量间距重新排版。历史原图、校验值和核对范围见[来源记录](PROVENANCE.md)。正文直接引用 SVG，首次克隆即可阅读这五张图。

## 架构图：继续编辑 PPTX

| 图示 | 维护源 | 本地导出 |
|---|---|---|
| GPT | [PPTX](fig/gpt-diagram.pptx) | [SVG](fig/gpt-diagram.svg) · [PNG](fig/gpt-diagram.png) · [PDF](fig/gpt-diagram.pdf) |
| RNN | [PPTX](fig/rnn-diagram.pptx) | [SVG](fig/rnn-diagram.svg) · [PNG](fig/rnn-diagram.png) · [PDF](fig/rnn-diagram.pdf) |
| 可序列并行的 RNN | [PPTX](fig/sequence-parallel-rnn-diagram.pptx) | [SVG](fig/sequence-parallel-rnn-diagram.svg) · [PNG](fig/sequence-parallel-rnn-diagram.png) · [PDF](fig/sequence-parallel-rnn-diagram.pdf) |

在 PowerPoint 中改文字、编辑原生公式或移动对象，保存 PPTX 后重新生成。导出器从 PPTX 读取文字、公式、分组坐标和连接线几何，输出纯 SVG 文字与图元；没有嵌入公式位图。跨平台字体统一为 DejaVu、DejaVu Math TeX Gyre 和 Noto Sans CJK，字体外观与原来的 Cambria／Arial 有差异。

在其他电脑查看 SVG 时，安装同样的字体可保持版面；PNG 和已嵌入字体的 PDF 适合直接分享。

[导出器](../tools/pptx_svg.py)支持这三张图当前使用的矩形、圆角矩形、直线／曲线连接、上下标和定界符。新增尚不支持的公式或图形对象时会报错，需要扩展导出器后再构建。生成的 SVG 可用于查看、复制到展示材料；持续编辑以 PPTX 为入口，重新生成会覆盖同名导出文件。

## 生成

按[统一构建说明](../ARTIFACTS.md#本地生成)安装 Python 依赖、Cairo、Noto CJK、DejaVu 字体；PPTX 导出还需 `fonts-dejavu-extra` 中的数学字体。构建无需安装 PowerPoint 或 LibreOffice。

```bash
# 从仓库根目录运行，生成这八张图的 14 个导出文件及检查报告。
python3 assets/render.py

# 一并构建全部图集、素材和展示 HTML；--full 另导出 Tide 展示 PDF。
python3 tools/build.py
```

需要另存预览时使用 `python3 assets/render.py --output-dir /tmp/assets-preview`，结果按 `images/`、`fig/` 子目录输出。来源目录中的 SVG 与 PPTX 保持原样。日常的 [render-checks.json](render-checks.json)记录源文件、字体和输出哈希，并核对 Office Math 对象与文字没有遗漏或重复。

图源列表由 [catalog.json](catalog.json)声明，准确输出路径登记在仓库的[产物清单](../generated-artifacts.json)。新增图源时同步更新两处以及精确忽略规则。

## 保留的复杂拓扑图

[load-store-progression-02.png](images/load-store-progression-02.png)沿用原 PNG，不参与本次转换与构建。此前移除的 `linked-list-transformer-star-moe-decentralized-graph-nn-02.png` 是它的重复别名；Git 历史仍保存原记录。
