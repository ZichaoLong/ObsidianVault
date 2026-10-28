# 仓库维护约定

- Git 跟踪正文、维护源、原始素材和明确留存的证据。由源文件机械生成的图片、HTML、PDF、备注和日常报告默认不跟踪；规则见 [ARTIFACTS.md](ARTIFACTS.md)。
- 新增生成物时，在 [generated-artifacts.json](generated-artifacts.json) 登记准确路径、生成脚本和命令，并添加对应的精确忽略规则。不要按扩展名全局忽略图片或文档。
- 用户明确要求留存的成品加入清单的 `retained`，注明用途。手工维护的 SVG 等属于源文件，放在生成器不会覆盖的位置；接入生成流程时读取该源文件。
- 日常生成过程不得覆盖历史核验快照。原始素材和历史证据的归类以来源和用途为准，不能只按文件格式删除。
- 提交前运行 `python3 tools/check_artifacts.py`；涉及 Tide 文档时运行 `python3 20-tide-decentralized-neural-network/tools/check_documents.py`。完整构建验证使用两者的 `--require-built` 参数；尚未构建的已登记产物可缺省，其他失效链接仍须修复。
