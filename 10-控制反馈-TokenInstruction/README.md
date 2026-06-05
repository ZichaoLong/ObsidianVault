---
type: index
status: active
tags:
  - control-feedback
  - token-instruction
---

# 控制反馈 / Token = Instruction

本目录用于整理控制反馈线的当前主线、历史动机、理论命题、实验命题、challenge 与 defense。

当前执行层只保留两条最小可输命题：

1. 理论命题：局部状态更新闭包。
2. 实验命题：事件对象 -> 可归因 -> 可纠偏。

> [!summary] 当前边界
> 这条线不直接主张 `workspace + load/store` 已经优于最强 LLM+Agent；当前只验证它是否形成独立、可归因、可纠偏的工作方式候选层。

需要保留但不直接扩张执行计划的问题，放入问题地图与 challenge / defense 链中。

## 主题页

- [[10-控制反馈-TokenInstruction/主线-计划-问题地图|主线、计划与问题地图]]
- [[10-控制反馈-TokenInstruction/理论与Defense|理论与 Defense]]
- [[10-控制反馈-TokenInstruction/实验与机制Defense|实验、机制与 Defense]]
- [[10-控制反馈-TokenInstruction/历史动机|历史动机]]

## 关键章节直达

- [[10-控制反馈-TokenInstruction/主线-计划-问题地图#控制反馈：当前主线总览|当前主线总览]]
- [[10-控制反馈-TokenInstruction/主线-计划-问题地图#控制反馈：当前计划与 Defense|当前计划与 Defense]]
- [[10-控制反馈-TokenInstruction/理论与Defense#局部状态更新闭包|局部状态更新闭包]]
- [[10-控制反馈-TokenInstruction/实验与机制Defense#控制反馈：事件对象实验计划|事件对象实验计划]]
- [[10-控制反馈-TokenInstruction/主线-计划-问题地图#控制反馈：问题展开地图|问题展开地图]]
- [[10-控制反馈-TokenInstruction/历史动机#历史动机：Token[Instruction] = Opcode + Operands|Token[Instruction] = Opcode + Operands]]

## 阅读顺序

1. 先读 [[10-控制反馈-TokenInstruction/主线-计划-问题地图|主线、计划与问题地图]]，把当前立场、双命题和问题空间看清楚。
2. 若要进入理论侧，读 [[10-控制反馈-TokenInstruction/理论与Defense|理论与 Defense]]。
3. 若要进入实验侧，读 [[10-控制反馈-TokenInstruction/实验与机制Defense|实验、机制与 Defense]]。
4. 若要回看出发点，读 [[10-控制反馈-TokenInstruction/历史动机|历史动机]]。
