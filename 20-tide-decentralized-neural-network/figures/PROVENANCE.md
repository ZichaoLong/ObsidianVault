# 图片来源与复现记录

## 2026-10-27：恢复已有图片

三份绘图脚本从当前会话 2026-10-12 至 2026-10-13 的原始绘图调用恢复，并按顺序应用后续补丁。恢复保留了绘制内容；仅将固定的临时输出路径改为脚本所在仓库目录，并增加 `--output-dir` 参数。

| 用户保存的原图 | 仓库图片 | 恢复源码 |
|---|---|---|
| `~/tide-structure.png` | [tide-structure.png](tide-structure.png) | [tide_structure.py](src/legacy/tide_structure.py) |
| `~/PSUF-simple.png` | [PSUF-simple.png](PSUF-simple.png) | [psuf_simple.py](src/legacy/psuf_simple.py) |
| `~/PSUF-complete.png` | [PSUF-complete.png](PSUF-complete.png) | [psuf_complete.py](src/legacy/psuf_complete.py) |

三份恢复脚本重新生成的 PNG 均与用户保存的原图逐像素、逐字节相同。原图及恢复前源码的 SHA-256、所用字体与渲染版本见 [legacy-provenance.json](legacy-provenance.json)。绘图源码和 PNG 均保存在仓库中，复现不需要会话记录。

旧图以 Pillow 和 Noto Sans CJK Regular／Bold（TTC 的索引 2）绘制。字体文件默认来自 `/usr/share/fonts/opentype/noto/`。相同源码在其他字体或渲染器版本上可能产生不同的排版或像素；图中数学含义仍以引用教材为准。

## 2026-10-27：局部语义图

新增十张局部语义图，每张同时保存可编辑 SVG、PNG 和 Python 生成函数。定义来自共同局部架构、区域分配、KV 及三种循环记忆与短卷积教材。各图的用途、选定条件、定义章节和逐文件 SHA-256 见 [local-provenance.json](local-provenance.json)；图集中的链接供顺序阅读和查阅。

本批定义对应提交 `6517ac525bce57bd20ea8f22753407d2fc331982` 中的教材内容。生成时使用 Python 3.14.4、Pillow 12.1.1、CairoSVG 2.8.2、Cairo 1.18.4，以及 Noto Sans CJK SC 与 DejaVu Sans。SVG 保留文字对象，字体文件及哈希列在记录中。图中上下标由生成器定位，中文与数学字符分别使用相应字体。

核验结果：

- 十张图均对照定义审读并目视检查；修正了完整内容的激活条件、KV 窗口示意和字体缺字。563 个 SVG 文字片段的全部字符在指定字体中都有对应字形。
- 指定总量算例与三个温度算例，均与现有区域参考程序的标量求解、独立可行面枚举两种结果一致。
- 固定时间槽例子使用现有卷积函数核对，包括零权重与趋弱接收；KV 两次接收例子的摘要、硬选择和残差输出逐项核对。
- 在独立输出目录重绘后，十份 SVG、十份 PNG 均与仓库输出逐字节相同；三份恢复图仍与原图哈希一致。
- 文档检查通过：正典教材哈希保持、局部公式结构及相对链接有效；图中记录的全部定义锚点另行核对。`git diff --check` 通过。

以后修订图中的数学内容时，同步核对所引用的定义与图中条件。完整重绘并审读后，用 `render.py --group local --record-provenance` 更新来源与渲染记录；普通重绘保留已有记录，便于对照。
