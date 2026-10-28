# 插图来源与重建记录

## 2026-10-28：简单图改为 SVG，架构图复用 PPTX

五张简单图根据历史 PNG 手工重画为 SVG，正文改为引用 SVG。三张架构图继续使用原 PPTX；本次没有修改 PPTX 的内容。维护入口、生成命令与字体要求见 [README](README.md)。

已重建的 PNG 和两份既有 PDF 改为本地导出，不再跟踪。原始版本可从下表的固定提交读取；本次使用普通提交，未改写历史。复杂拓扑图 `images/load-store-progression-02.png` 保持原文件。

### 手工重画的核对范围

| 图 | 核对内容 |
|---|---|
| Load/Store | 五处文字、thinking 回路、网络与 Embedding 的方向、窗口输出与反馈、16 格线性上下文 |
| 布尔电路 | 六个逻辑门及连接；输入 (0,1,0)，中间结果与输出 1；上下层的 NOT／AND／OR 保持 |
| 常深度电路 | AND／OR 层级、已画出的连接、输入与省略号；polynomial fan-in 和 constant depth 标注 |
| 图灵机 | START 1 → 3 → 4 → HALT 2；三条转移标签及状态 4 的自环；纸带 `abaa`、九个 Δ 与四个点 |
| 多带与单带编码 | 三条纸带和对应读写头位置 2、3、1；单带的分隔符、空白符与三处点标记 |

SVG 保留独立文字、形状与分组，字体、线宽和少量间距重新排版。PNG 由 SVG 生成，不声称与历史 PNG 逐像素相同。

### PPTX 导出范围

| 源文件 | 原生公式 | 连接线 | 图形对象 | 分组 |
|---|---:|---:|---:|---:|
| gpt-diagram.pptx | 49 | 34 | 59 | 19 |
| rnn-diagram.pptx | 26 | 21 | 34 | 13 |
| sequence-parallel-rnn-diagram.pptx | 69 | 59 | 78 | 4 |

导出器选择 Office Math 原生分支，跳过兼容分支里的 PNG；直接读取形状、上下标、定界符、颜色、组变换和连接线坐标。曲线按 DrawingML 的 `curvedConnector3` 两段三次 Bézier 几何解释；参数形式可对照 [DrawingML 预设形状定义](https://github.com/apache/poi/blob/trunk/poi/src/main/resources/org/apache/poi/sl/draw/geom/presetShapeDefinitions.xml)。多行数学段落按行保留，文字使用变换后的文本框排版，避免分组非等比缩放拉伸字形。

字体统一为 DejaVu Sans、DejaVu Math TeX Gyre 与 Noto Sans CJK；其字形和原来的 Arial／Cambria 有差异。公式字符、上下标归属、连接方向和原文件布局继续取自 PPTX。新增未支持的对象会明确报错，避免静默省略。生成 SVG 内保留源文件与公式摘要；日常报告另写忽略的 `render-checks.json`。

本地核对使用 Pillow 12.1.1、CairoSVG 2.8.2，并以旧 PNG 为参照逐图目视检查。八张 SVG 均经 Chrome 显示检查，文字没有超出画布；三份 PDF 的字体均已嵌入。自动检查覆盖 144 个公式的完整性与字符、114 条连接线、两段曲线控制点、分组缩放、多行公式及不支持对象的失败行为。源码检查与完整构建接入仓库 CI。

## 原始图像与导出快照

下表指向转换前的固定提交 `99d69c5fc3a129630322b3a16a13007c2836ede4`。当前同路径 PNG／PDF 为新生成物；需要历史原件时使用下表链接。

| 历史文件 | SHA256 |
|---|---|
| [images/load-store-progression-01.png](https://github.com/ZichaoLong/ObsidianVault/blob/99d69c5fc3a129630322b3a16a13007c2836ede4/assets/images/load-store-progression-01.png) | `a6789290d5cbe035a3ef8edcbe6e77d00cc7994e4c2e9d170ce2f2e12c32f1b0` |
| [images/ai-time-scaling-law-theoretical-evidence-01.png](https://github.com/ZichaoLong/ObsidianVault/blob/99d69c5fc3a129630322b3a16a13007c2836ede4/assets/images/ai-time-scaling-law-theoretical-evidence-01.png) | `4eb01472390505ca8678795824a280457f08f77122dae3ede4de0d8f00572b53` |
| [images/ai-time-scaling-law-theoretical-evidence-02.png](https://github.com/ZichaoLong/ObsidianVault/blob/99d69c5fc3a129630322b3a16a13007c2836ede4/assets/images/ai-time-scaling-law-theoretical-evidence-02.png) | `9250478b970e66981d0777ab78c317aeec6e3b3633c54a33574d7e68cafb5839` |
| [images/control-feedback-token-instruction-opcode-operands-01.png](https://github.com/ZichaoLong/ObsidianVault/blob/99d69c5fc3a129630322b3a16a13007c2836ede4/assets/images/control-feedback-token-instruction-opcode-operands-01.png) | `593fb331ab6a6ad4890403b89b37f321411b37822ff3185a833b15a761987103` |
| [images/control-feedback-token-instruction-opcode-operands-02.png](https://github.com/ZichaoLong/ObsidianVault/blob/99d69c5fc3a129630322b3a16a13007c2836ede4/assets/images/control-feedback-token-instruction-opcode-operands-02.png) | `1060ac6468a8f0d6a1b5e90acf0c5f58e61ea22762b251bac8c6eb0577b1f68d` |
| [fig/gpt-diagram.png](https://github.com/ZichaoLong/ObsidianVault/blob/99d69c5fc3a129630322b3a16a13007c2836ede4/assets/fig/gpt-diagram.png) | `4ea398874484de492315f6db47caa04fa5b65259b7e9e347f6db1e6c9cefb5e3` |
| [fig/rnn-diagram.png](https://github.com/ZichaoLong/ObsidianVault/blob/99d69c5fc3a129630322b3a16a13007c2836ede4/assets/fig/rnn-diagram.png) | `f244fd1d28f3409fd4a19b75129ec29fd0c99136af67ad26c55b0989e8ff0db5` |
| [fig/sequence-parallel-rnn-diagram.png](https://github.com/ZichaoLong/ObsidianVault/blob/99d69c5fc3a129630322b3a16a13007c2836ede4/assets/fig/sequence-parallel-rnn-diagram.png) | `7df5e31538d13dbc9987216f9d699a6efa678715a451022e4a99f99501574854` |
| [fig/gpt-diagram.pdf](https://github.com/ZichaoLong/ObsidianVault/blob/99d69c5fc3a129630322b3a16a13007c2836ede4/assets/fig/gpt-diagram.pdf) | `baec31f5b0cffa6860a3a104bed56531a57eb0a2b3b70cc5bc68598309f9702a` |
| [fig/sequence-parallel-rnn-diagram.pdf](https://github.com/ZichaoLong/ObsidianVault/blob/99d69c5fc3a129630322b3a16a13007c2836ede4/assets/fig/sequence-parallel-rnn-diagram.pdf) | `4909d67f7bc47453713c43bf7804782d0bd7c9c56593b0067fee237e3c7aa073` |

五张简单图于 2026-06-04 从旧笔记 MHTML 提取为 PNG，[历史抽取映射](https://github.com/ZichaoLong/ObsidianVault/blob/16fcd0e2577ec82651db376c71021c3c0d85ae57/_migration/mhtml-image-map.md)保存原文与附件的对应。本次以这些 PNG 为重画参照，未把它们声称为已恢复的原始矢量文件。
