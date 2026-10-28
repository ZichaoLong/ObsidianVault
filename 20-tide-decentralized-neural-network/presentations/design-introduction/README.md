# Tide 首版展示材料

从去中心化与稀疏化出发，在同一张 HB 小图上走完两次输入，再解释共同框架、Mem、可替换设计和上下层反馈。共 15 组画面、25 个可停顿步骤，最后一组为算例条件附页。

以下成品由本目录源文件生成，默认不随 Git 跟踪。首次克隆请先运行下方构建命令；HTML／备注由 `build.py` 生成，PDF／预览／渲染报告由 `export.py` 生成。维护与留存规则见[仓库约定](../../../ARTIFACTS.md)。

- [离线 HTML 演示](index.html)：下载后用浏览器打开；内容与图形内嵌，无需网络依赖。左右方向键或空格推进，N 打开备注与出处，G 打开目录；也支持按钮与左右滑动。
- [PDF 浏览版](tide-design-introduction.pdf)：25 页，每页保留一个停点，方便顺序阅读与批注。
- [六幅画面预览](preview.png)：快速查看节点图、完整输出、参与计数、记忆与实验边界。
- [讲者备注](speaker-notes.md)：各停点的数值条件、语义边界和定义链接。

设计主张见[短稿](../../memos/design/design-requirements-and-architecture.md)，讲述顺序依据[展示脚本](../design-introduction-script.md)。本场使用 [HB 三层实例](../../instances/hb-lattice-weighted-message.md#2-三层图上的分叉汇合与记忆)的同一组参数；标量输出用于核对机制，任务收益留待实验比较。

## 小修改

当前 HTML 提供播放、目录和备注；尚未实现直接改字、拖拽图形并保存的编辑界面。小修改通过编辑源文件、重新生成完成。也可以直接按停点说明希望怎样修改，由助手更新源文件和展示产物。

### 先定位画面和改动范围

地址末尾的 `#8.2` 表示第 8 组画面的第 2 个停点，也可在控制栏看到这个编号；它对应当前 PDF 的第 13 页。提修改时优先用停点编号或标题，说明只改当前画面，还是同步修改所有相关画面。例如：

- “8.2，把副标题里的‘长期摘要’改成‘长期记忆摘要’，其他内容保持。”
- “所有 HB 图，把左区 L 整体下移一点，连线跟着移动。”
- “只改 11.2，让当前接收的箭头更靠近 Describe。”

### 自己修改源文件

| 想修改什么 | 当前编辑入口 | 作用范围 |
|---|---|---|
| 标题、副标题、图右侧说明、备注、部分数学符号 | [content.py](content.py)，搜索屏幕上的原句 | 对应的 `step(...)`；有些词也会出现在备注或其他停点 |
| P/S/U/F、Mem、反馈图等固定版式里的文字或框图 | [build.py](build.py) 中的 `phases()`、`memory()`、`feedback()` 和 `body()` | 相应版式及其 `mode` 分支 |
| HB 节点图、图内标签、节点位置、连线、颜色 | [图形源](../../figures/src/design_introduction.py) | `REGIONS` 和配色是共用配置；`graph(stage)` 控制各阶段的显示 |
| 字号、间距、线条样式、页面布局 | [deck.css](deck.css)，查找对应选择器，例如 `.side`、`.key`、`.flow-box` | 共用样式会影响使用它的所有画面；仅改单个停点需增加局部样式 |

**改一个字。** 在 `content.py` 搜索“四个区域，十二个节点”，修改引号内的标题并保存。保留字符串外的引号、逗号和括号；文字里已有的 `<br>` 表示换行。若搜不到正文，继续查 `build.py` 和图形源。也可在仓库根目录搜索：

```bash
rg -n --glob '*.py' '要找的原句' \
  20-tide-decentralized-neural-network/presentations/design-introduction \
  20-tide-decentralized-neural-network/figures/src/design_introduction.py
```

**改一个符号。** 普通标签可以直接替换源文件中的 `θ`、`τ`、`→`、`I₁` 等字符；HTML 文字也使用 `<sub>...</sub>`、`<sup>...</sup>` 表示上下标。若改的是数学对象的名称或含义，检查同一对象的其他画面、备注与算例说明。

**移动一组节点。** 图形源的 `REGIONS` 每项依次为“框的 x、y、宽、高、标题、三个节点的 y 坐标”；节点的 x 坐标由框中心计算。例如把左区 L 整体下移 12 个图形坐标单位，将

```python
'L': (354, 36, 164, 208, '左区 L', [104, 164, 224]),
```

改为

```python
'L': (354, 48, 164, 208, '左区 L', [116, 176, 236]),
```

框和节点一起移动，连线端点按节点位置重新计算。该配置由所有 HB 停点共用；若只改一幅图，需要按 `stage` 单独处理。图形坐标会随画面缩放，并不总等于屏幕像素。改变连线关系或激活路径还会改变算例含义，须同时核对评分、输出和计数。

### 修改后预览

只看 HTML 时，保存源文件后运行下方的 `build.py` 命令，再刷新浏览器即可；正在看的 `#8.2` 等地址可继续定位同一停点。需要同步 PDF 和预览图时，再运行 `export.py`。常规小改无需每次导出全部 PDF。

`index.html`、`speaker-notes.md` 和 `figures/design-introduction/` 中的 SVG 都是生成文件，直接改它们会在下次构建时被覆盖。浏览器开发者工具可用于临时试字号或位置，确定后将改动写回源文件。

SVG 是矢量图，可以用 Inkscape 等工具拖动元素。但当前构建流程从 Python 生成并内嵌 SVG，尚不会读取手工修改的 SVG。若采用鼠标编辑某幅图的方式，需要先把它接为独立图源，再让构建脚本读取它；这样后续手改才会持续保留。整套 HTML 的拖拽编辑与保存则需要另做编辑功能。

## 内容与复现

[content.py](content.py) 保存屏幕文字、逐步画面、讲者备注与引用。[build.py](build.py) 将其与样式、交互及 SVG 图形合成单文件 HTML，并生成备注。节点布局与图形源在 [design_introduction.py](../../figures/src/design_introduction.py)，可编辑 SVG 位于 [figures/design-introduction/](../../figures/design-introduction/)。修改内容源后重新生成，避免直接编辑生成文件。

首次克隆可从仓库根目录运行 `python3 tools/build.py`，生成图集、展示 HTML 和备注；`python3 tools/build.py --full` 另生成 PDF 与预览。依赖安装及 GitHub Actions 的手动完整构建见[统一构建说明](../../../ARTIFACTS.md#本地生成)。

只修改本展示时，可继续单独运行：

```bash
python3 20-tide-decentralized-neural-network/presentations/design-introduction/build.py
python3 20-tide-decentralized-neural-network/presentations/design-introduction/export.py
```

HTML 构建只依赖 Python 标准库。导出另需 `playwright-cli`、Chrome、Pillow 与 Noto CJK 字体；[export.py](export.py) 临时启动回环地址服务器和独立浏览器会话，逐停点检查布局并导出 PDF、预览及[渲染记录](render-checks.json)。这些输出均只在本地保存。输出采用 1600 × 900 的 16:9 画面。静态导出按全部停点展开，不依赖过渡动画。

HTML 的定义链接按仓库相对路径组织；单独下载 HTML 后，仍可阅读所有画面和备注，定义原文需回到仓库查阅。小屏幕可横屏翻看，也可直接阅读 PDF。
