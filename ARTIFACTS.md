# 维护源、生成物与留存文件

Git 保存持续维护的源文件。能由这些源文件重建的产物默认只在本地生成；用户明确指定的成品按路径登记留存。生成物清单与构建命令统一保存在 [generated-artifacts.json](generated-artifacts.json)，忽略规则按具体输出路径设置。

| 内容 | 维护方式 |
|---|---|
| 正文、展示脚本、Python、CSS、JS、依赖说明 | 跟踪，作为编辑与重建入口 |
| 图集 PNG／SVG、演示 HTML、导出 PDF、预览、生成的讲者备注 | 本地生成，默认不跟踪 |
| 日常渲染与检查报告 | 本地生成；需要留存某次结果时另存快照并登记 |
| 手工 SVG、PPTX、原始图片及外部资料 | 作为源文件跟踪，避免被生成器覆盖 |
| 已留存的历史核验与来源快照 | 跟踪，清单的 `retained` 记录理由 |

当前可重建的范围包括 Tide 图集、展示材料和 `assets/` 中八张插图的导出物。五张手工 SVG 与三份 PPTX 是持续维护的图源，编辑方法与来源见[素材说明](assets/README.md)。复杂拓扑 PNG 继续作为原始素材保存。

## 本地生成

使用 Python 3.10+，从仓库根目录运行统一入口：

```bash
python3 tools/build.py          # 图集、素材导出、展示 HTML 和讲者备注
python3 tools/build.py --full   # 另导出 Tide 展示 PDF、预览和浏览器检查报告
```

[构建入口](tools/build.py)读取产物清单的 `command`、`build_mode` 和 `depends_on`，按依赖顺序调用现有生成器，使用当前 Python 环境。它在开始前检查依赖，任一步失败即停止，生成后核对本次所需产物和 Tide 文档。普通构建不需要浏览器；尚未生成的完整导出文件可以缺省。

首次使用，在 Python 环境中安装[图集依赖](20-tide-decentralized-neural-network/figures/requirements.txt)。当前绘图脚本采用固定字体路径；Debian/Ubuntu 的安装方式为：

```bash
python3 -m pip install -r 20-tide-decentralized-neural-network/figures/requirements.txt
sudo apt-get install libcairo2 fonts-noto-cjk fonts-dejavu-core fonts-dejavu-extra
```

完整导出另需 Google Chrome、Node.js 18+、Playwright CLI 和预览标题字体：

```bash
sudo apt-get install fonts-noto-cjk-extra
npm install --global @playwright/cli@0.1.12
```

构建脚本只提示缺少的依赖，不自动安装系统软件。其他系统需提供等价字体路径和渲染环境；CI 使用 Ubuntu 24.04、Python 3.12 和 Node.js 22。

各生成器仍可单独运行：

```bash
python3 assets/render.py
python3 20-tide-decentralized-neural-network/figures/render.py --group legacy
python3 20-tide-decentralized-neural-network/figures/render.py --group local --record-provenance
python3 20-tide-decentralized-neural-network/presentations/design-introduction/build.py
python3 20-tide-decentralized-neural-network/presentations/design-introduction/export.py
```

图集文件仍生成到 `figures/`，展示文件仍生成到 `presentations/design-introduction/`，原有本地链接保持。只修改展示时通常运行 `build.py` 即可；PDF 与预览按需导出。首次克隆尚未生成的图片和成品链接，要在对应构建后才能打开。

`assets/render.py` 为五份手工 SVG 生成 PNG，并从三份 PPTX 生成 SVG、PNG 和单页 PDF。它直接读取 PPTX 中的原生公式、坐标与连线；数学字体来自 `fonts-dejavu-extra`，无需 Office 或 LibreOffice。素材图的 PDF 使用 Cairo 生成，包含在普通构建中；Tide 展示的 PDF 需要浏览器，使用 `--full`。

`--record-provenance` 现在写入忽略的 `figures/local-render-checks.json`。既有 `legacy-provenance.json`、`local-provenance.json` 和实现核验 JSON 作为历史证据保留，正常构建不覆盖它们。

## 修改图形与保留成品

使用 Python 维护的图应修改源码再生成。若转为手工维护，将 SVG 另存到例如 `figures/manual/` 的位置，纳入跟踪，并让需要它的生成器读取该文件。保留布局、文字等手工成果时，生成脚本不得继续写入同一路径。

用户明确指定某个生成成品需要随仓库保存时，将其准确路径与理由加入清单的 `retained`，同时撤销该路径的忽略规则；如仍需自动生成，也保留它的输出登记。历史核验快照注明日期、来源版本和验证范围，使用独立文件名保存。

## 检查

```bash
# 新克隆只含源文件时也应通过；显示尚待生成的文件数量。
python3 tools/check_artifacts.py
python3 20-tide-decentralized-neural-network/tools/check_documents.py
python3 -m unittest discover -s tools -p 'test_*.py'

# 完成上面的完整构建后，要求全部登记产物实际存在。
python3 tools/check_artifacts.py --require-built
python3 20-tide-decentralized-neural-network/tools/check_documents.py --require-built
```

检查会发现意外跟踪的生成物、缺少的忽略规则、缺失的生成脚本和未登记的失效链接。普通模式仅允许清单中的准确产物路径及明确登记的输出目录缺省；不会把所有图片或所有缺失链接视为正常。

## GitHub Actions

[Repository checks](.github/workflows/repository.yml)在每次 push 和 pull request 时检查产物跟踪、Tide 文档、构建顺序、失败处理及 PPTX 导出行为。轻量检查只依赖 Python 标准库和 Git；公式内容、曲线几何、分组缩放和多行公式都有检查，实际字体渲染由完整构建验证。

需要验证完整生成时，在 GitHub 的 **Actions → Repository checks → Run workflow** 选择分支运行。该流程先执行轻量检查，再安装渲染依赖并运行 `python3 tools/build.py --full`，检查浏览器交互、25 个停点的布局、全部登记产物及工作区是否干净。结果在 Actions 日志中查看；生成物随运行环境清理，不回写仓库。

两种检查均使用完整 Git 检出。完整构建按需触发，日常编辑可先运行本地普通构建。

历史清理的范围、提交映射与旧克隆的同步方法见 [2026-10-28 治理记录](20-tide-decentralized-neural-network/records/history/2026-10-28-artifact-governance.md)。
