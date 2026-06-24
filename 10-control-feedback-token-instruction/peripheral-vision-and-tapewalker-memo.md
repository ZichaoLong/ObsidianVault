---
type: memo
status: draft
date: 2026-06-24
tags:
  - control-feedback
  - local-state-access
  - active-access
  - tapewalker
  - peripheral-vision
  - memo
---

# Peripheral Vision and TapeWalker Memo

> [!summary] 本页定位
> 本页是独立备忘，暂不合入控制反馈主线。它记录一个问题：TapeWalker 当前 `load()` 的下采样是否缺少类似人类 peripheral vision 的机制；如果缺少，应该如何理解这个缺口，以及是否值得在 B2 / TapeWalker 中近似。

## 核心判断

TapeWalker 当前的 `load()` 下采样，更接近：

> sparse probe：在一个窗口中抽取少量位置，返回这些位置的相对精确内容。

人的 peripheral vision 更接近：

> low-bandwidth feature field：大范围、低分辨率、连续覆盖的传感器信号，与内部注意力和眼动控制协同工作。

二者不是同一个东西。

关键区别不是“是否少读 token”，而是：

> peripheral vision 在低成本、受限带宽下，仍保留空间 / 序关系 / 显著性 / 异常 / 变化信号，从而指导下一次 attention、fixation、zoom 或 move。

因此更严谨的说法是：

> peripheral-like 机制的价值不是单纯节省 token，而是在低成本周边观察中保留足够方向信号。

## 下采样与 Peripheral Vision 的差异

| 机制 | 看到什么 | 导航意义 |
| --- | --- | --- |
| 当前 `load()` 下采样 | 在窗口中抽几个 cell，返回这些 cell 的精确文本或内容 | 容易漏掉未采样区域，更像 sparse probe。 |
| peripheral vision | 覆盖更大范围，但每处只给粗特征、形状、密度、运动、saliency、异常感 | 能判断哪里值得看，指导下一次 focus / zoom / move。 |
| hierarchical summary | 每个区域一个摘要、统计或 bucket feature | 工程上最接近 peripheral-like overview。 |
| retrieval / resolver | 直接返回候选目标或候选区域 | 更强，但可能跳过主动观察过程，吸收 TapeWalker 的贡献。 |

如果只有 sparse downsampling，模型可能仍然接近盲走：

- 没抽到的位置完全不可见。
- 局部连续性容易被破坏。
- 很难判断下一步应该向左、向右、放大、缩小还是跳转。
- 如果依赖外部 search，TapeWalker 的主动视野价值又会被 resolver 吸收。

真正的 peripheral-like observation 应该更像：

```text
center:
  高保真局部内容

near periphery:
  相邻区域的低保真结构信息

far periphery:
  更远区域的极低保真统计、变化、边界或异常信号

budget / topology metadata:
  当前视野、剩余预算、可导航关系、dirty flag
```

## 人类 Peripheral Vision 的类比边界

人类 peripheral vision 不是离线摘要索引。

它是：

> 低成本、受限带宽的传感器输入，加上内部高级注意力、眼动、记忆和 world model 的协同。

它同时做到两件事：

- 降低高保真感知成本。
- 提供下一步注意力分配和眼动控制的方向信号。

但 TapeWalker 在文本、trace、workspace 上没有天然传感器层。所谓 peripheral-like overview 多半只能是：

- 派生视图。
- summary layer。
- feature layer。
- index layer。
- learned sensor / encoder。

这导致一个重要边界：

> 在 workspace 上，peripheral-like overview 不是免费感知层，而是需要构造、维护、计费和防止智能泄漏的派生层。

人也有成本和错误：

- 外周视觉分辨率低。
- 眼动和注意力有成本。
- 视觉记忆会陈旧。
- 内部 world model 会误判。

但人不需要在每次外部世界变化后维护一个显式 summary database；workspace overview 若要动态更新，则必须处理一致性和维护成本。

## 对 TapeWalker 的缺口

如果 TapeWalker 只提供：

```text
load(pos, radius)
load_sparse(window, max_items)
```

那么它更像局部窗口读取或稀疏探针，而不是 foveated perception。

若 TapeWalker 要主张 `active foveated workspace access`，缺口在于：

> 它需要一种 topology-preserving, saliency-aware, budgeted peripheral observation，使模型能在不读取全局内容的情况下获得下一步导航方向。

这里的目标不是仿生复刻，而是给控制器提供可测的方向信号。

可以把目标问题写成：

> 能否构造一种成本受控的低保真周边观察，使它在不泄露答案、不变成强 resolver 的前提下，为局部访问策略提供可用的方向信号？

## 远景：Learned Sensor

从历史动机看，最远景的形态不应是纯 cell/token 型 overview，而应更接近：

```text
workspace region
  -> learned sensor / encoder
  -> compact latent or coarse feature field
  -> controller decides next fixation / zoom / move
```

这里 `Load` 不是把 token 原文搬给 LLM，而是通过一个可训练感知层，把 workspace 转成低带宽状态信号。

这更接近“线型上下文中的局部读取 + embedding”的设想，也更像人眼与视觉皮层的关系。

但这条路很重，因为它牵涉：

- sensor 的训练目标。
- workspace 表示。
- sensor 与 controller 的接口。
- controller 与 sensor 是分阶段训练还是联合训练。
- 是否仍能复用现有 LLM。
- 如何防止 sensor 退化成 retriever / resolver。
- 如何计入构造、推理和维护成本。

因此，learned sensor 适合作为远景升级路径，不适合作为第一阶段默认实验。

## 现实推进：Derived Overview 作为 Sensor Proxy

短期更现实的做法，是先用 deterministic 或弱智能的 derived overview 作为 learned sensor 的 proxy。

但它必须被定位为：

> sensor proxy，而不是最终机制，也不是免费 peripheral vision。

可区分三档：

| 档位 | 说明 | 适用场景 | 主要风险 |
| --- | --- | --- | --- |
| `load_sparse` | 当前均匀下采样，返回少量精确 cell | 简单负控或基础对照 | 方向信号弱，容易漏检。 |
| `load_overview_static` | workspace 构建时生成 overview，后续不维护或只读 | trace first-error localization、长文档定位、日志定位 | 构建成本和任务特化程度需要计入。 |
| `load_overview_dynamic` | 每次写入后维护 overview | dynamic workspace recovery、频繁 patch/store | 更新成本、一致性成本、dependency tracking、智能泄漏都很强。 |

最稳的第一步是：

> 只在只读或近似只读任务里测试 `static overview`，不要一开始做 dynamic overview。

例如 `trace first-error localization` 可以把 trace 当成只读对象：

- trace 已经固定。
- overview 可以预先生成。
- 不涉及每次 cell 更新后的摘要一致性。
- 容易比较 `load_sparse`、`load_overview_static`、BM25 / vector、generated analyzer。

## 成本与归因风险

peripheral-like overview 最危险的地方，是它可能把 TapeWalker 的贡献偷走。

主要风险：

| 风险 | 含义 |
| --- | --- |
| update cost | 每次写入后需要更新哪些 bins / summaries / features。 |
| consistency cost | overview 与真实 cell 是否一致。 |
| intelligence leakage | summary / anomaly score 是否已经替模型完成判断。 |
| latency | store / patch 后是否需要重算 overview。 |
| dependency tracking | 哪些 summary 受哪些 cell 影响。 |
| training mismatch | 训练时 overview 干净，真实运行时 overview 陈旧或噪声大。 |
| resolver absorption | overview 过强时，机制变成 retrieval / analyzer，而不是 active foveated access。 |

因此必须坚持：

- overview 成本显式计入。
- overview 不应直接返回目标位置或答案。
- task-specific anomaly score 必须谨慎使用。
- deterministic feature 优先于 LLM summary。
- static overview 优先于 dynamic overview。
- 必须和 BM25 / vector / generated analyzer 对照。

## 可能的实验裁决

更合理的裁决不是单看 token 数，而是同时看成本和导航效果。

| 结果 | 解释 |
| --- | --- |
| token 降低，导航不变差 | 有压缩价值，但 peripheral 机制价值较弱。 |
| token 相同，导航更好 | 有方向信号价值。 |
| token 降低，导航更好 | 最接近 peripheral-like 成功。 |
| token 降低但漏检上升 | 下采样 / 压缩失败。 |
| 导航更好但 overview 成本很高 | 可能是 resolver / scaffold 吸收，需要收缩结论。 |
| 只有 LLM summary / anomaly score 有效 | 更像强 scaffold，需要谨慎解释。 |
| deterministic overview 有效 | 更支持“低保真周边特征场提供方向信号”。 |

## 与 B0 / B2 的关系

当前更稳的安排是：

```text
B0:
  addressed local cell/window access
  read_window only
  不默认引入 peripheral-like overview

B2 / TapeWalker static:
  load_sparse vs load_overview_static
  只读 trace / long document / log localization
  测方向信号与观察成本

B2 / TapeWalker dynamic:
  只有 static overview 有信号后，再研究 overview maintenance cost
```

因此 peripheral-like overview 的位置是：

> B2 / TapeWalker 的重要消融项和远景桥，不是 B 分支的默认 access mode。

## 尚未决定的问题

proxy 的具体做法还需要进一步讨论，不能在本页定案。

待定问题：

- `load_overview_static` 的接口应该返回哪些字段。
- 哪些字段是 generic feature，哪些已经 task-specific。
- 是否允许 LLM-generated summary。
- 是否允许 anomaly score。
- 如何定义 overview 的信息预算。
- 如何计入 overview 构建成本。
- trace task 中的 bucket 粒度如何选择。
- 是否需要 shuffled overview / corrupted overview 负控。
- 是否需要 learned sensor 作为第二阶段。
- learned sensor 的训练目标应该是方向预测、信息增益预测、错误区间预测，还是下一步 action imitation。

当前结论只到这里：

> TapeWalker 的 current `load()` 确实缺少 peripheral-like 周边感。这个缺口不应被简单补成“更强 summary”，而应作为 B2 的独立研究点：在受控成本下，低保真周边观察是否能提供可泛化的导航方向信号。
