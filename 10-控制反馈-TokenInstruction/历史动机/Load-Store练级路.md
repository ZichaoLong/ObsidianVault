---
type: historical-note
status: archived
tags:
  - control-feedback
  - token-instruction
  - load-store
  - historical-motivation
---

# 历史动机：Load/Store 练级路

> [!note] 历史定位
> 这页保存 `Load/Store` 早期图示材料。它用于说明从线性上下文访问走向显式工作空间寻址、图结构访问的直觉；当前收缩后的实验版本见 [[10-控制反馈-TokenInstruction/事件对象实验计划|事件对象实验计划]]。

## 线性上下文中的局部读取

![[assets/images/Load_Store练级路-01.png]]

这张图对应一个早期直觉：如果上下文仍主要是线性 token 序列，那么 `Load` 的核心问题就是在长序列中定位一个局部片段，并把它作为后续控制步骤的反馈信号。

## 图结构工作空间

![[assets/images/Load_Store练级路-02.png]]

这张图对应另一个早期直觉：当工作空间不是单一线性上下文，而是图结构、索引结构或分块状态时，`Load/Store` 的价值不只在于“能读写”，还在于能把搜索、定位、局部修补限制在更小的结构邻域中。

## 与当前主线的关系

这页只保留历史图示直觉。当前不直接主张 `Load/Store` 一定优于最强 LLM+Agent，而是先验证：

- [[10-控制反馈-TokenInstruction/局部状态更新闭包|局部状态更新闭包]] 是否存在。
- [[10-控制反馈-TokenInstruction/事件对象实验计划|事件对象 -> 可归因 -> 可纠偏]] 是否能在现实系统中形成。
