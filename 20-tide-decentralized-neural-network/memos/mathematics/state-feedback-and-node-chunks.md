---
type: research-memo
status: semantic-boundary-memo
semantic-baseline: tide-core-2
as-of: 2026-09-17
tags:
  - tide
  - state
  - prefill
---

# 状态递归、完整输出反馈与节点因果块

正典 TimedDAG 语义把本次计算快照、下一持久状态和完整输出分别记录；[[../../timed-dag-chunk-prefill-learning-note|分块教材]] 再为状态递归、完整输出和二者的联合求值定义精确契约。本页整理一个更窄的边界问题：完整输出值本身参加后续状态递归时，节点块需要增加哪些输入输出坐标。

## 1. 三种状态依赖

固定节点，令旧状态、本地输入、选择控制和完整输出分别为
$q_\theta,h_\theta,c_\theta,z_\theta$。

### 1.1 完整输出以前确定下一状态

正典语义采用：

$$
q^{\mathrm{cmp}}_\theta
=A(q_\theta,h_\theta,c_\theta),
\qquad
q_{\theta+1}
=N(q_\theta,q^{\mathrm{cmp}}_\theta,h_\theta,c_\theta),
$$

随后：

$$
z_\theta=F(q^{\mathrm{cmp}}_\theta,h_\theta,c_\theta).
$$

这里状态轨迹可以由 `BatchState` 从左边界状态和整段驱动量产生；也可以由
`BatchNode` 与全部 $z_\theta$ 一起产生。激活后清空、激活计数、阈值状态、KV 追加和标准 SSM 递归都可以属于这个类别。

### 1.2 完整输出只反馈节点私有状态

考虑：

$$
(z_\theta,q_{\theta+1})
=T(q_\theta,h_\theta,c_\theta).
$$

后一个时间的节点输出读取 $q_{\theta+1}$，region selector 与其他节点在块内不读取这项私有状态。相应联合契约取：

$$
\operatorname{CausalNode}_I
\left(q_b,(\theta,h_\theta,c_\theta)_{\theta\in I}^{\uparrow}\right)
=
\left(
(z_\theta,q_{\theta+1})_{\theta\in I}^{\uparrow},q_c
\right),
$$

并要求其完整轨迹逐坐标等于标量递归。这项契约把 $F$ 到下一状态的边保留在联合块内部。continuation 仍保存右边界私有状态；精化记录仍保留全部概念中间状态。

### 1.3 完整输出反馈共同选择

若：

$$
z_\theta
\longrightarrow q_{\theta+1}
\longrightarrow S_{j,\theta'}
\longrightarrow z_{\theta'},
$$

则中间状态离开单节点块并由 region 共同选择读取。一个节点私有契约只能推进到该边界。要继续整块求值，需要覆盖相关节点和 selector 的精确区域契约；若函数类没有这种契约，最大前沿在这里形成新的自适应阶段。

## 2. 契约必须说明的坐标

一个 Full-feedback 节点契约至少声明：

1. 左边界私有状态的集合与 owner；
2. 块内每个逻辑时间的输入、控制和 active 指示；
3. $z_\theta$ 与 $q_{\theta+1}$ 的标量参考递归；
4. 返回的完整输出轨迹、状态轨迹与右边界状态；
5. 哪些中间状态可以被块外 selector 或其他节点读取；
6. 与 finite cut 的跨界消息和 continuation 怎样组合；
7. 对所声明函数类成立的逐坐标精确等式。

一次调用的存在只给出外层块。工作量、并行深度和设备效果还需要结合摘要、扫描公式或具体算法。

## 3. 统一逻辑时间

状态块保留每个真实逻辑时间坐标。若相邻实际节点事件位于时间 $2$ 与 $10$，驱动序列中的时间差仍为 $8$。惰性衰减、时间位置编码和时延相关状态更新都读取这项差值。

## 4. 与正典语义的边界

正典局部函数保持 `Next` 在本次 `Full` 以前确定，因此第 1.1 节直接适用正典
$P/S/U/F$。第 1.2--1.3 节改变局部事件边，需要扩充节点状态转移的规范定义，再证明 finite-cut 存在性、continuation 与精化定理。它们可以使用同一套契约相对最大前沿框架，但不能只通过改变成本标记获得。
