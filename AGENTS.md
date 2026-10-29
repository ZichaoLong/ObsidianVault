# 仓库维护约定

- 开始工作先读 [ARTIFACTS.md 的维护地图](ARTIFACTS.md#各条工作线的维护地图)，定位当前研究线、维护源、构建组和需要人工核对的下游。全仓适用这份规则；各目录 README 说明具体编辑方式。
- Git 跟踪正文、维护源、原始素材和明确留存的证据。可重建的图片、HTML、PDF、备注和日常报告默认不跟踪；不要直接修改同名导出物作为持续成果。
- 修改图形、展示或其上游定义后，使用 `python3 tools/check_artifacts.py --affected <仓库相对路径>` 查影响；区分 `REBUILD` 与 `REVIEW`，先核对受影响的定义、例子、图形源和展示内容，再运行 `python3 tools/build.py --group <组名>`。重新生成成功不代表语义同步已经完成。
- 拉取、切换 Git 分支、合并或进入新 worktree 后检查产物状态。用 `--changed-from <同步前提交>` 查变动影响；忽略的本地产物不会随 Git 更新。所需组应为 `CURRENT`；静态展示交付前构建 `presentation-export`。同一 worktree 顺序构建。
- 新增／改名／移除生成物时，同步 [generated-artifacts.json](generated-artifacts.json) 的输入、输出、人工核对来源与依赖、源目录注册、准确忽略路径和文档引用。不要按扩展名全局忽略图片或文档。新媒体源加入 `asset_sources`，新增产物目录加入 `asset_directories`。
- 手工维护的 SVG 等属于源文件，放在生成器不会覆盖的位置并让生成器读取它。用户明确指定的成品加入 `retained`，注明理由。日常生成不得覆盖历史核验快照；原始素材的归类以来源和用途为准。
- 检测到过期或未归类文件时先确认来源。保护用户未提交内容和历史留存文件；检查器不会自动删除旧产物，不使用全仓 `git clean -fdx` 处理同步。
- 提交前运行 `python3 tools/check_artifacts.py`、`python3 tools/check_links.py`；涉及 Tide 时另运行 `python3 20-tide-decentralized-neural-network/tools/check_documents.py`。修改构建／检查工具时运行 `python3 -m unittest discover -s tools -p 'test_*.py'`。
- 构建后用 `python3 tools/check_artifacts.py --require-built --group <组名>` 严格核验所需组；完整构建后省略 `--group`，并运行 `python3 tools/check_links.py --require-built`。新克隆可缺省已登记产物，其他失效链接须修复。提交、推送按当前任务授权执行。
