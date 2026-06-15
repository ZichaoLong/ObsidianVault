---
type: review
status: active
date: 2026-06-15
tags:
  - recursive-decomposition
  - memory
  - code-review
  - phase1
---

# recursive-reasoning-agents 代码审视

> [!summary] 本页定位
> 本页审视收到的代码仓库 `/home/zlong/llm/recursive-reasoning-agents`。这里讨论的是代码仓库自身能直接支持什么结论，不等同于 Phase 1 报告和汇报材料中全部实验结论。报告材料中的 D² 大规模结果仍可作为阶段结果引用，但应明确它们不是由当前代码仓库内完整评测产物直接复现出来的。

## 一页版结论

这个代码仓库最有价值的地方，不是证明“递归分解 + memory 已经成立”，而是清楚记录了从 naive recursive decomposition 到 context preservation、isolation、verification、complexity routing、structural diversity 的工程演化。

仓库内可复核的实证证据有限：

- `1st-Agent` 有 AIME 10 题结果：Baseline CoT `2/10 = 20%`，Agent `3/10 = 30%`。
- `2nd-Agent` 只有 1 道 AIME 结果：`1/1`，耗时约 `1437s`。
- `3rd-Agent` 只有 1 道 AIME 结果：`1/1`，耗时约 `2300s`。
- `v5-Diversity-Voting` 有 standalone structural diversity voting 实现，但仓库内没有随附 GSM8K / SynthMath 大规模评测输出。
- `v6-Semantic-Entropy-Routing` 的 README 声称 D² / semantic entropy routing 结果，但实际 `recursive_agent/` 代码是 HCE-guided recursive decomposition + event sourcing + memory tools，不是 entropy voting / arbiter 的可复核实现。

因此，当前最稳的读法是：

> 代码仓库支持“系统迭代暴露并修复了递归分解 agent 的若干关键 failure modes”；但不支持仅凭该仓库就宣称“memory-augmented recursive decomposition 已被证明”或“D² 大规模结果可由仓库直接复现”。

这与 [[current-status|当前状态：D² / Phase 1]] 的收缩版结论一致：Phase 1 最强信号来自 adaptive compute / structured ensemble / trace-aware arbitration，而不是 memory 本身。

## 代码仓库能直接支持什么

### 1. v1 的小样本改进存在，但非常弱

`1st-Agent/results/comparison_table.csv` 记录：

| Dataset | Method | Accuracy | Correct | Total | Avg Steps |
| --- | --- | ---: | ---: | ---: | ---: |
| AIME | Baseline CoT | 20.00% | 2 | 10 | N/A |
| AIME | Agent (Recursive Decomp + Memory) | 30.00% | 3 | 10 | 9.9 |

这个结果能说明：

- 初始 recursive decomposition + memory agent 在这 10 道 AIME 样本上略高于 CoT。
- 它足以作为工程探索起点。

但它不能说明：

- 递归分解是主要收益来源。
- memory 是主要收益来源。
- 结果可泛化到更大 benchmark。
- 结果有稳定统计意义。

### 2. v1 failure modes 很清楚

v1 的代码和日志暴露了几个典型问题：

- 子问题只有字符串描述，缺少必要上下文。
- 子问题结果合成方式过于粗糙，例如直接用 `" | ".join(subproblem_solutions)` 拼接。
- memory 搜索和复用缺少质量门控，容易缓存错误或垃圾结果。
- trace 中出现“缺少具体集合 / 缺少上下文”的症状，说明 naive decomposition 会把原题语义切碎。

这些问题本身是有研究价值的，因为它们解释了为什么“把题拆开”并不自动带来收益。

### 3. v2/v3 主要是架构修复，不是强实证结果

v2 文档明确识别了 v1 的主要失败：

- context loss。
- naive combination。
- memory poisoning。
- lack of verification / reflection。
- single-model overload。

v3 进一步引入：

- master-slave 架构。
- recursive worker。
- file-based isolated workspace。
- verifier。
- quality-gated memory。

这些是合理的系统修复方向，但仓库内 v2/v3 结果都只有单题 AIME 产物。因此，它们更适合作为“架构演化证据”，不适合作为“性能结论证据”。

### 4. v4 是 HCE / ARD standalone 骨架

`4th-Agent-ARD-HCE` 引入了 complexity assessment、blackboard、direct-vs-decompose routing、architect / executor / judge / specialist / synthesizer / verifier 等角色。

它说明项目开始从“固定递归分解”转向“按复杂度自适应计算分配”。但该目录没有随附完整实验 harness 和结果产物，不能单独支撑性能主张。

### 5. v5 的代码可以支持 structural diversity voting 机制存在

`v5-Diversity-Voting/agent_v5.py` 实现了：

- 三种结构化 prompt。
- 并行运行。
- answer extraction / normalization。
- majority vote。

这与当前主线中的 `structured ensemble` 解释一致。它说明 v5 的机制边界比较清楚：v5 不是 memory 系统，而是结构化多样性投票。

但仓库内没有大规模评测输出，因此 v5 的性能数字仍应来自外部报告材料，而不是代码仓库自身。

### 6. v6 的目录名 / README 与代码实现不一致

这是本次审视中最重要的不一致。

`v6-Semantic-Entropy-Routing/README.md` 声称：

- D² / semantic entropy routing。
- GSM8K `89.39%`。
- SynthMath-1K `71.7%`。
- GSM8K-200 `93.5%`。
- entropy routing、adversarial verifier、tiebreaker / arbiter。

但 `v6-Semantic-Entropy-Routing/recursive_agent/recursive_agent.py` 实际实现的是：

- HCE API complexity analysis。
- LLM decomposition strategy。
- recursive subtask solving。
- memory operations。
- event sourcing。
- direct execution vs decomposition。
- subtask combination。

在 `recursive_agent/` 代码中，没有看到完整的 semantic entropy voting、unanimous / 2:1 / all-disagree routing、arbiter traces、five-vote final decision 等 D² 关键实现。

所以，v6 需要拆成两个层次理解：

| 层次 | 状态 | 说明 |
| --- | --- | --- |
| README / 报告叙事 | D² / semantic entropy routing | 可作为外部材料声称，但需要配套源码和评测产物 |
| 当前 `recursive_agent/` 代码 | HCE-guided recursive decomposition | 是另一个 agent 骨架，不是 D² 可复核实现 |

这不意味着 D² 结果一定不成立；它只意味着当前代码仓库没有把 D² 的关键实现和评测闭环完整交付出来。

## 代码层面的积极信号

尽管证据边界需要收缩，代码里有几个积极信号：

- 迭代路线真实：从 v1 到 v6，不是一次性包装，而是不断遇到 failure modes 后改系统结构。
- v2/v3 对 v1 失败的诊断比较准确，尤其是 context envelope、verified memory、isolation workspace 等方向。
- v5 的机制边界清楚，适合作为 structured diversity voting baseline。
- v6 actual code 里 event sourcing 和 memory tools 是对“可审计 agent runtime”的合理尝试。
- HCE / ARD 表明团队已经意识到 uniform compute 不合理，开始转向 adaptive compute。

这些信号支持继续研究，但更像“工程探索成熟度”而不是“科学命题已证明”。

## 主要风险与攻击面

### 1. 代码证据与汇报数字之间有缺口

当前文档和汇报材料可以继续引用 D² 的 GSM8K / SynthMath 结果，但必须标注来源：

- 如果来自报告 / PPT：写成“材料记录”或“外部报告记录”。
- 如果来自代码仓库：必须有评测脚本、数据版本、模型、运行命令、原始输出。

否则验收或复审时容易被攻击为“代码无法复现主结论”。

### 2. Memory 仍不是当前代码证据的主贡献

代码中有多种 memory：

- v1 networkx graph memory。
- v2/v3 working memory / verified memory 设计。
- v6 scratchpad / session / persistent memory tools。

但没有看到足够的 memory on/off、verified vs raw memory、stale memory / distractor memory 等消融。因此当前不能把“memory 是收益来源”写成强结论。

更稳的说法是：

> Memory 是贯穿系统演化的重要工程模块，但其独立收益尚未由当前代码仓库证明。

### 3. Recursive decomposition 的证据也需要收缩

v3 更接近真正的 recursive workspace agent；v6 actual code 也有 recursive decomposition。但最终汇报中最强的 D² 结果，更像 structural ensemble + adaptive routing。

因此不能把 D² 的提升直接归因给“递归分解”。

更稳的说法是：

> 递归分解是早期主线和部分实现机制；当前最强结果更接近结构化多样性和自适应计算分配。

### 4. v6 actual code 的运行依赖不够封闭

`hce_adapter.py` 默认调用本地 Flask API `http://127.0.0.1:5000/api/analyze`。失败时会 fallback 到 mock `MODERATE`。

这会带来复现风险：

- 如果 HCE API 未启动，系统仍然能跑，但实际逻辑已经变成 mock complexity。
- 如果不记录 HCE API 版本和输出，评测结果难以复现。
- 如果 complexity routing 是主张的一部分，fallback 行为必须在日志中显式标注。

### 5. 评测产物不足以支撑六代性能曲线

当前仓库足以支持“六代代码 / 设计存在”，但不足以支持“六代性能曲线由代码产物完整复现”。

需要补齐：

- 每代对应的 benchmark。
- 数据集版本。
- 模型版本。
- endpoint / decoding 参数。
- 运行命令。
- 原始输出。
- 汇总脚本。
- 成本统计。

## 对当前递归分解线文档的影响

当前 [[current-status|当前状态：D² / Phase 1]] 的大方向仍然合理，但需要读者理解其证据层级：

- `current-status` 汇总的是 Phase 1 报告 / 汇报材料中的整体结果。
- 本页审视的是收到的代码仓库能直接复核的内容。
- 两者并不完全等价。

因此，文档口径应保持：

- 可以说：Phase 1 材料记录 D² 在 GSM8K / SynthMath 上表现最好。
- 可以说：代码仓库展示了从 recursive decomposition 到 adaptive compute 的工程演化。
- 不应说：当前代码仓库已经完整复现 D² 大规模结果。
- 不应说：代码仓库已经证明 memory 或递归分解是主要收益来源。

## 建议的后续整理动作

### 1. 给代码仓库补一个 experiment manifest

建议在代码仓库顶层增加一个机器可读或人可读的实验清单：

| 字段 | 内容 |
| --- | --- |
| experiment_id | `v6_gsm8k_full_qwen25_3b_2026...` |
| code_path | 使用哪个目录和入口 |
| command | 完整运行命令 |
| model | 模型名称、权重版本、服务端 |
| dataset | 数据集名称、版本、split、样本数 |
| decoding | temperature、max_tokens、seed |
| result_file | 原始输出路径 |
| summary | accuracy、calls、tokens、wall-clock |
| commit | 代码提交哈希 |

这比继续补叙事更重要。

### 2. 把 archival iteration 和 reproducible baseline 分开

建议把六代代码分成两类：

- `archive/`：保留历史迭代和设计演化。
- `experiments/` 或 `reproducible/`：保留真正可复现实验入口。

这样既不丢历史，也不会让审稿人或验收方误以为每个目录都可直接复现最终结论。

### 3. 对 D² 补齐最小复现闭环

如果要继续主张 D²，至少需要一个小而完整的闭环：

- GSM8K-200 或固定 200 题切片。
- CoT baseline。
- same-prompt self-consistency k=3。
- v5 structural diversity voting。
- v6 entropy routing + arbiter。
- answer-only arbiter / trace-aware arbiter 消融。
- token / call / wall-clock 成本。

这比立即扩大任务更重要。

### 4. 对 memory 单独降维检验

如果要重新抬高 memory 主张，建议不要在完整 agent 上直接证明，而是先做更窄的对照：

- no memory。
- raw trace memory。
- final answer memory。
- verified subproblem memory。
- distractor / stale memory。
- cross-problem reuse。

只有 verified memory 显著优于 raw / final / no memory，memory 才能重新成为主贡献候选。

### 5. 继续保留 Lean / Kernel / 小模型作为未来方向

收到的代码仓库强化了一个判断：

> 普通数学 benchmark 上，memory 和递归分解很难被单独归因；未来如果要研究可复用中间对象，最好进入有 verifier、可复用 artifact、可度量成本的场景。

因此 [[future-lean-landscape|Lean 方向详尽调研]]、[[future-kernel-landscape|Kernel 性能优化工作谱系]]、[[future-small-model-landscape|小模型研究谱系调研]] 仍然是合理后续。

## 当前裁决

对这份代码仓库，建议给出如下审视意见：

> 代码仓库是有价值的工程演化记录，但不是最终 D² 结果的完整复现包。它支持“团队经历了从 naive recursive decomposition 到 adaptive compute / structured diversity 的真实迭代”，也支持“早期 recursive decomposition 暴露出 context loss、memory poisoning、combination failure 等关键问题”。但仓库内证据不足以单独证明 memory、递归分解或 D² 大规模结果。后续应优先补齐 experiment manifest、D² 最小复现闭环和 memory 消融，而不是继续扩大叙事。

