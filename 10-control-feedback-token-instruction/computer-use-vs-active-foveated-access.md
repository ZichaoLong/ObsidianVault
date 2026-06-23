---
type: memo
status: draft
date: 2026-06-17
tags:
  - control-feedback
  - local-state-access
  - active-access
  - computer-use
  - memo
---

# Computer Use vs Active Foveated Access

> [!summary] 本页定位
> 本页是独立备忘，不合入控制反馈主线。它只记录 `computer use` 与 TapeWalker 式 `active foveated workspace access` 的关系、差异和后续研究含义。

## 一句话结论

`computer use` 与 `active foveated workspace access` 在高层上相似：二者都是“观察 -> 动作 -> 再观察”的主动反馈闭环。

但二者不是同一个东西。

更精确地说：

> `computer use` 是视觉 / UI 环境中的具身工具接口；`active foveated workspace access` 是受控 workspace 上的一等公民视野访问接口。

## 相似之处

二者都具备：

- 主动观察。
- 多步交互。
- 局部反馈。
- 根据当前观察选择下一步动作。
- 外部状态会被动作改变。

因此，在控制反馈线中，`computer use` 应被视为 `active foveated` 的相邻机制和强基线，而不是无关对象。

OpenAI 的 computer use 文档给出的基本形态是：模型检查 screenshots，并返回 click、type、scroll 等 UI actions，由外部环境执行并返回新的 observation。参考：[OpenAI Computer use](https://developers.openai.com/api/docs/guides/tools-computer-use)。

## 核心差异

| 维度 | Computer use | TapeWalker / active foveated workspace access |
| --- | --- | --- |
| 状态空间 | GUI / 浏览器 / 桌面 / app UI | 人工定义的 workspace，可是文本、trace、表、图、文件片段 |
| 观察方式 | screenshot / 可见窗口 / UI 状态 | `pos + fov + load_range / load_cell / zoom` |
| 地址 | 像素坐标、UI 元素、窗口位置，可能有 accessibility / DOM 辅助 | 显式 address / cell / cursor / mark |
| 视野控制 | 通过 scroll、click、window focus、browser zoom 等间接控制 | `fov` 是一等公民，可直接放大、缩小、移动 |
| 写入方式 | click / type / drag / shortcut，修改真实 UI 状态 | `store / insert / delete / patch / commit` 修改 workspace |
| 可控实验性 | 噪声大，UI 状态复杂，难严格控制信息预算 | 可强制隐藏全局状态、固定 observation budget、记录访问轨迹 |
| 研究价值 | 强现实基线，适合真实 GUI 任务 | 更适合研究 B 分支机制、selector 学习、局部访问策略 |

## Computer Use 是否缺少主动视野控制

结论：不缺主动性，但通常缺少显式、一等公民的视野控制。

`computer use` 可以：

- 滚动页面。
- 点击元素。
- 切换窗口。
- 聚焦区域。
- 输入文本。
- 调整浏览器页面状态。

这些动作会间接改变下一次 observation。

但这类视野控制通常是 UI 操作的副产品，而不是类似下面这样的显式 workspace 指令：

```text
move(pos)
zoom(fov)
load(cell)
load_range(start, end)
mark(pos)
goto_mark(mark_id)
```

也就是说，`computer use` 的视野控制更像：

> 在真实 UI 中移动身体和眼睛。

而 TapeWalker 的视野控制更像：

> 在受控状态空间里操作一个带 `pos / fov / address / cell` 语义的读写头。

## 什么时候 Computer Use 会接近 Active Foveated

如果 computer-use harness 暴露更结构化的观察动作，它会接近 `active foveated workspace access`。

例如：

```text
crop(x, y, w, h)
zoom(level)
scroll(delta)
inspect(region)
read_accessibility_node(id)
read_dom_subtree(node_id)
focus_region(region_id)
```

此时，computer use 不再只是“看整张 screenshot 后点击”，而是具有更明确的局部观察、局部放大、局部读取能力。

但即使如此，它通常仍与 TapeWalker 有两个差异：

- UI 环境的状态边界、cell 粒度、address schema 通常不是为实验可辨识性设计的。
- UI action 往往同时改变视野和外部世界状态，难以把 observation action 与 write/action effect 严格拆开。

## 对控制反馈线的意义

`computer use` 对 `active foveated` 是强基线，不是反驳。

它说明：

> 现代 Agent 已经具备某种主动观察和局部交互能力。

因此，TapeWalker 不能主张：

> 现有 Agent 完全没有主动视野访问。

TapeWalker 更可守的主张应是：

> 显式 `pos / fov / address / cell` 这层接口是否让观察策略更可控、更可训练、更可回放、更适合局部纠偏。

## 实验含义

如果任务是 UI / 视觉空间导航，必须把 computer use 放进强基线。

对照至少包括：

- screenshot + click / type / scroll 的普通 computer use agent。
- computer use + accessibility tree / DOM。
- computer use + crop / zoom / region inspect，如果 harness 支持。
- TapeWalker-style `pos / fov / load / mark / write` workspace。

真正要比较的不是“是否能完成 UI 任务”，而是：

- observation tokens。
- 操作步数。
- false negative。
- 定位步数。
- 局部修复成功率。
- 轨迹是否可监督训练。
- 视野控制策略是否能长度泛化。

## 当前判断

`computer use` 是 `active foveated workspace access` 的现实相邻形态。

它已经覆盖了：

- 主动观察。
- UI 空间中的局部交互。
- 通过滚动 / 点击 / 聚焦间接控制下一步视野。

但它通常没有明确覆盖：

- 受控 workspace 上的一等公民 `fov`。
- 显式 address / cell / mark。
- 固定 observation budget 下的 selector / navigator 实验协议。
- observation action 与 write action 的清晰分离。
- 可回放、可归因、可训练的局部访问轨迹。

因此，`computer use` 应进入 `active foveated` 的对标谱系，但不应与 TapeWalker 直接画等号。

