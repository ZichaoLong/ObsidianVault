# llm-notes 迁移清单

来源：`/home/zlong/llm/llm-notes`

## 摘要

- 文件总数：66
- 需要迁移：59
- Markdown：51
- mhtml 参考文件：7
- git 未跟踪来源文件：4

## 目标区域统计

- `10-控制反馈-TokenInstruction`：42
- `20-TIDE-去中心化神经网络`：3
- `30-技术笔记`：4
- `40-原始材料索引`：2
- `attachments/llm-notes/fig`：8
- `mhtml-reference-only`：7

## 需要注意

- `mhtml` 文件不迁移到 Obsidian，只作为图片恢复来源。
- `git_status = ??` 的来源文件同样纳入迁移，避免遗漏未提交内容。
- 详细逐文件清单见 `llm-notes-migration-manifest.tsv`。

## 逐文件清单

| source_path | kind | migrate | target_area | git_status | notes |
|---|---|---|---|---|---|
| AI 的 System1+System2.mhtml | mhtml_reference | no | mhtml-reference-only |  | Do not migrate; use only for image recovery. |
| AI的时间 Scaling Law 的一些理论佐证.mhtml | mhtml_reference | no | mhtml-reference-only |  | Do not migrate; use only for image recovery. |
| Load_Store练级路.mhtml | mhtml_reference | no | mhtml-reference-only | ?? | Do not migrate; use only for image recovery. |
| README.md | markdown | yes | 40-原始材料索引 |  | Needs manual classification. |
| content/scratch/Load_Store练级路.md | markdown | yes | 10-控制反馈-TokenInstruction | ?? | Load/store source note. |
| content/scratch/draft.md | markdown | yes | 30-技术笔记 |  | Background note. |
| content/scratch/notes.md | markdown | yes | 30-技术笔记 |  | Background note. |
| content/scratch/从链表(Transformer)、星型(MoE)到去中心化Graph神经网络.md | markdown | yes | 20-TIDE-去中心化神经网络 | ?? | TIDE source note. |
| content/scratch/杂谈.md | markdown | yes | 40-原始材料索引 |  | Needs manual classification. |
| content/tech-notes/Transformer-and-Beyond.md | markdown | yes | 30-技术笔记 |  | Background note. |
| content/tech-notes/ai-diffusion.md | markdown | yes | 30-技术笔记 |  | Background note. |
| content/thesis/AI 的 System1+System2.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback source note. |
| content/thesis/AI的时间 Scaling Law 的一些理论佐证.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback source note. |
| content/thesis/写在前面.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback source note. |
| content/thesis/控制反馈：Token[Instruction]=Opcode+Operands.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback source note. |
| defense/tide-Defense.md | markdown | yes | 20-TIDE-去中心化神经网络 |  | TIDE line. |
| defense/控制反馈-Bridge-Defense.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| defense/控制反馈-Defense-v2-Reply.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| defense/控制反馈-Defense-v2.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| defense/控制反馈-Defense.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| defense/控制反馈-Plan-v3-Defense.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| defense/控制反馈-当前Defense-2026-05-27.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| defense/控制反馈-理论问题与候选桥-Defense.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| fig/gpt-diagram.pdf | asset | yes | attachments/llm-notes/fig |  | Migrate as attachment. |
| fig/gpt-diagram.png | asset | yes | attachments/llm-notes/fig |  | Migrate as attachment. |
| fig/gpt-diagram.pptx | asset | yes | attachments/llm-notes/fig |  | Migrate as attachment. |
| fig/rnn-diagram.png | asset | yes | attachments/llm-notes/fig |  | Migrate as attachment. |
| fig/rnn-diagram.pptx | asset | yes | attachments/llm-notes/fig |  | Migrate as attachment. |
| fig/sequence-parallel-rnn-diagram.pdf | asset | yes | attachments/llm-notes/fig |  | Migrate as attachment. |
| fig/sequence-parallel-rnn-diagram.png | asset | yes | attachments/llm-notes/fig |  | Migrate as attachment. |
| fig/sequence-parallel-rnn-diagram.pptx | asset | yes | attachments/llm-notes/fig |  | Migrate as attachment. |
| plan/tide-Plan.md | markdown | yes | 20-TIDE-去中心化神经网络 |  | TIDE line. |
| plan/控制反馈-Bridge-Plan.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| plan/控制反馈-Plan-v2.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| plan/控制反馈-Plan-v3.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| plan/控制反馈-Plan.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| plan/控制反馈-primary-bet-层级.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| plan/控制反馈-test-time-state-hierarchy.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| plan/控制反馈-局部状态更新闭包-形式化草案.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| plan/控制反馈-当前计划-2026-05-27.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| plan/控制反馈-推进计划.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| plan/控制反馈-理论问题-原始表述.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| plan/控制反馈-理论问题计划.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| review/Adversary-Review-2026-05-25.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| review/控制反馈-Bridge-Layer-Challenges-2026-05-26.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| review/控制反馈-Defense-and-Plan-Challenges-2026-05-25.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| review/控制反馈-Defense-v2-Challenges.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| review/控制反馈-Plan-v3-Challenges-2026-05-26.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| review/控制反馈-Plan-v3-Defense-Challenges-2026-05-26.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| review/控制反馈-Plan-v3-Defense-Challenges-Bridge-2026-05-26.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| review/控制反馈-理论问题与候选桥-Challenges-2026-05-26.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| status/2026-05-25-route-memo.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| status/控制反馈-Bridge-Candidates-and-Theory-2026-05-26.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| status/控制反馈-NRAM与Next-Token关系-2026-05-27.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| status/控制反馈-双命题关系-2026-05-27.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| status/控制反馈-对标机制谱系-2026-05-27.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| status/控制反馈-当前总述-2026-05-27.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| status/控制反馈-文档索引-2026-05-26.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| status/控制反馈-最小不可替代增量与全局解释算子-2026-05-27.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| status/控制反馈-理论讨论备忘-2026-05-26.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| status/控制反馈-确定性层与智能层-2026-05-27.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| status/控制反馈-问题展开地图-2026-05-27.md | markdown | yes | 10-控制反馈-TokenInstruction |  | Control-feedback history. |
| 从链表(Transformer)、星型(MoE)到去中心化Graph神经网络.mhtml | mhtml_reference | no | mhtml-reference-only | ?? | Do not migrate; use only for image recovery. |
| 写在前面.mhtml | mhtml_reference | no | mhtml-reference-only |  | Do not migrate; use only for image recovery. |
| 控制反馈：Token[Instruction]=Opcode+Operands.mhtml | mhtml_reference | no | mhtml-reference-only |  | Do not migrate; use only for image recovery. |
| 杂谈.mhtml | mhtml_reference | no | mhtml-reference-only |  | Do not migrate; use only for image recovery. |
