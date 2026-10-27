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
