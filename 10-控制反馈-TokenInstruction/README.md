---
type: index
status: active
tags:
  - control-feedback
  - token-instruction
---

# 控制反馈 / Token = Instruction

本目录用于整理控制反馈线的当前主线、问题地图、对标机制谱系、理论命题、实验命题、challenge 与 defense。读者不需要从头顺序读完所有内容，建议先按问题进入。

当前执行层只保留两条最小可输命题：

1. 理论命题：局部状态更新闭包。
2. 实验命题：事件对象 -> 可归因 -> 可纠偏。

> [!summary] 当前边界
> 这条线不直接主张 `workspace + load/store` 已经优于最强 LLM+Agent；当前只验证它是否形成独立、可归因、可纠偏的工作方式候选层。

需要保留但不直接扩张执行计划的问题，放入问题地图与 challenge / defense 链中。

## 读者先带走什么

- `Next Token` 是基础 bet，`Token = Instruction` 是对 token 语义的推广，不是否定 next-token 范式。
- 当前主线不是证明“新机制已经赢”，而是把理论侧和实验侧压成可输命题。
- 理论侧当前押 [[10-控制反馈-TokenInstruction/理论与Defense#局部状态更新闭包|局部状态更新闭包]]，实验侧当前押 [[10-控制反馈-TokenInstruction/实验与机制Defense#控制反馈：事件对象实验计划|事件对象 -> 可归因 -> 可纠偏]]。
- [[10-控制反馈-TokenInstruction/主线-计划-问题地图#控制反馈：问题展开地图|问题展开地图]]、[[10-控制反馈-TokenInstruction/实验与机制Defense#控制反馈：对标机制谱系|对标机制谱系]] 和 challenge / defense 是主线约束，不是附属材料。
- 历史动机用于理解为什么会走到这里，但不直接等于当前主张。

## 主题页

| 页面 | 读者问题 | 使用方式 |
| --- | --- | --- |
| [[10-控制反馈-TokenInstruction/主线-计划-问题地图|主线、计划与问题地图]] | 现在到底主张什么，问题空间如何展开，接下来做什么？ | 第一优先阅读。 |
| [[10-控制反馈-TokenInstruction/理论与Defense|理论与 Defense]] | 理论命题怎么定义，challenge 如何回应？ | 进入理论侧时阅读。 |
| [[10-控制反馈-TokenInstruction/实验与机制Defense|实验、机制与 Defense]] | 实验如何设计，要对标什么机制，计划如何被攻击？ | 进入实验侧时阅读。 |
| [[10-控制反馈-TokenInstruction/历史动机|历史动机]] | 这些想法最初从哪里来？ | 作为背景材料跳读。 |

## 关键章节直达

- [[10-控制反馈-TokenInstruction/主线-计划-问题地图#控制反馈：当前主线总览|当前主线总览]]
- [[10-控制反馈-TokenInstruction/主线-计划-问题地图#控制反馈：问题展开地图|问题展开地图]]
- [[10-控制反馈-TokenInstruction/实验与机制Defense#控制反馈：对标机制谱系|对标机制谱系]]
- [[10-控制反馈-TokenInstruction/理论与Defense#局部状态更新闭包|局部状态更新闭包]]
- [[10-控制反馈-TokenInstruction/实验与机制Defense#控制反馈：事件对象实验计划|事件对象实验计划]]
- [[10-控制反馈-TokenInstruction/主线-计划-问题地图#控制反馈：当前计划与 Defense|当前计划与 Defense]]
- [[10-控制反馈-TokenInstruction/历史动机#历史动机：Token[Instruction] = Opcode + Operands|Token[Instruction] = Opcode + Operands]]

## 阅读顺序

1. 先读 [[10-控制反馈-TokenInstruction/主线-计划-问题地图|主线、计划与问题地图]]，把当前立场、双命题和问题空间看清楚。
2. 若要判断理论命题是否站得住，读 [[10-控制反馈-TokenInstruction/理论与Defense|理论与 Defense]]。
3. 若要判断实验是否能落地，读 [[10-控制反馈-TokenInstruction/实验与机制Defense|实验、机制与 Defense]]。
4. 若要回看出发点和复杂度理论动机，读 [[10-控制反馈-TokenInstruction/历史动机|历史动机]]。
