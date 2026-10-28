# 维护源、生成物与留存文件

Git 保存持续维护的源文件。能由这些源文件重建的产物默认只在本地生成；用户明确指定的成品按路径登记留存。生成物清单与构建命令统一保存在 [generated-artifacts.json](generated-artifacts.json)，忽略规则按具体输出路径设置。

| 内容 | 维护方式 |
|---|---|
| 正文、展示脚本、Python、CSS、JS、依赖说明 | 跟踪，作为编辑与重建入口 |
| 图集 PNG／SVG、演示 HTML、导出 PDF、预览、生成的讲者备注 | 本地生成，默认不跟踪 |
| 日常渲染与检查报告 | 本地生成；需要留存某次结果时另存快照并登记 |
| 手工 SVG、PPTX、原始图片及外部资料 | 作为源文件跟踪，避免被生成器覆盖 |
| 已留存的历史核验与来源快照 | 跟踪，清单的 `retained` 记录理由 |

`assets/` 中的既有插图和 PPTX 继续作为资料保存。本轮已确认可重建的范围为 Tide 图集和展示材料；其他附件需先核对来源与导出关系再归类。

## 本地生成

先安装 [图集依赖](20-tide-decentralized-neural-network/figures/requirements.txt)、Cairo、Noto CJK 与 DejaVu 字体。PDF 导出还需要 `playwright-cli` 和 Chrome。以下命令在仓库根目录运行：

```bash
python3 20-tide-decentralized-neural-network/figures/render.py --group legacy
python3 20-tide-decentralized-neural-network/figures/render.py --group local --record-provenance
python3 20-tide-decentralized-neural-network/presentations/design-introduction/build.py
python3 20-tide-decentralized-neural-network/presentations/design-introduction/export.py
```

图集文件仍生成到 `figures/`，展示文件仍生成到 `presentations/design-introduction/`，原有本地链接保持。只修改展示时通常运行 `build.py` 即可；PDF 与预览按需导出。首次克隆尚未生成的图片和成品链接，要在对应构建后才能打开。

`--record-provenance` 现在写入忽略的 `figures/local-render-checks.json`。既有 `legacy-provenance.json`、`local-provenance.json` 和实现核验 JSON 作为历史证据保留，正常构建不覆盖它们。

## 修改图形与保留成品

使用 Python 维护的图应修改源码再生成。若转为手工维护，将 SVG 另存到例如 `figures/manual/` 的位置，纳入跟踪，并让需要它的生成器读取该文件。保留布局、文字等手工成果时，生成脚本不得继续写入同一路径。

用户明确指定某个生成成品需要随仓库保存时，将其准确路径与理由加入清单的 `retained`，同时撤销该路径的忽略规则；如仍需自动生成，也保留它的输出登记。历史核验快照注明日期、来源版本和验证范围，使用独立文件名保存。

## 检查

```bash
# 新克隆只含源文件时也应通过；显示尚待生成的文件数量。
python3 tools/check_artifacts.py
python3 20-tide-decentralized-neural-network/tools/check_documents.py

# 完成上面的完整构建后，要求全部登记产物实际存在。
python3 tools/check_artifacts.py --require-built
python3 20-tide-decentralized-neural-network/tools/check_documents.py --require-built
```

检查会发现意外跟踪的生成物、缺少的忽略规则、缺失的生成脚本和未登记的失效链接。普通模式仅允许清单中的准确产物路径及明确登记的输出目录缺省；不会把所有图片或所有缺失链接视为正常。

历史清理的范围、提交映射与旧克隆的同步方法见 [2026-10-28 治理记录](20-tide-decentralized-neural-network/records/history/2026-10-28-artifact-governance.md)。
