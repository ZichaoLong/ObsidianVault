---
type: semantic-anchor
status: active
tags:
  - tide
  - semantic-anchor
---

# TIDE 语义锚点

本页汇总四篇教材的共同数学对象及定义分工。局部函数的完整类型见 [符号与函数索引](semantic-interface-index.md)，实例与证明见各教材。

## 共同局部语义

有限节点集 $V$ 由 $\rho:V\to J$ 划分为区域 $\mathcal R_j$。固定消息边 $a\in A$ 具有独立身份、端点和正整数时延 $\delta(a)$；输入与输出由端口标记。平行边保留各自身份。

消息承载值属于非空空间 $P$。每个节点另有状态、本地内容、描述量和控制空间 $S_v,X_v,D_v,\mathsf C_v$，每个区域有选择历史空间 $Y_j$。这些空间分别选择。来源原子保留端口或边、位置或发送时间及载荷；同节点同时间的完整原子集合为 $B_{v,\theta}$。

只有非空纤维产生节点事件。一个区域在同一时间的候选集合为 $\mathcal C_{j,\theta}=\{v\in\mathcal R_j:B_{v,\theta}\ne\varnothing\}$。局部函数按以下顺序给出值：

| 作用 | 所确定的结果 |
|---|---|
| $P$：准备 | $(h,\widetilde q,d)$，由 Agg、Upd 和所选 Read 得到 |
| $S$：选择 | $(\mathcal A,(c_v)_{v\in\mathcal C},y')$，由 SelStep 得到 |
| $U$：状态 | $(q^{\mathrm{cmp}},q^{\mathrm{next}})$，由采用规则与 Next 得到 |
| $F$：完整输出 | $(f^A,f^O)$，由 Full 得到 |

描述模式 $\tau_j\in\{0,-,+\}$ 决定读取当前内容、旧状态或候选状态。激活集合为候选子集，$|\mathcal A|\le K_j$，允许空选；每个候选都有控制量。采用模式 $\kappa_j$ 决定哪些候选状态成为本次快照，Next 再决定下一持久状态。

Next 的参数顺序为 $(q,q^{\mathrm{cmp}},\theta,h,a,c)$，Full 的参数顺序为 $(q^{\mathrm{cmp}},\theta,h,c)$。Next 和下一选择历史只使用 Full 以前确定的量，且不调用或重算 Full。Full 返回逐出边与逐输出端口两个 $P_\bot$ 值族，允许独立的有值与无值结果。

非候选节点保持状态，空候选区域保持历史；非空候选但空激活时仍有准备、选择与状态作用。所有局部函数均为确定的全函数。固定参数可以共享，节点状态和区域历史分别归属。

## 层级条件与教材分工

| 教材 | 结构与输入条件 | 主要结论 |
|---|---|---|
| [SettleGraph](settlegraph-learning-note.md) | 严格区域分层，$\theta_{v,t}=Dt+r_v$，$\delta(a)=r_{\mathrm{dst}(a)}-r_{\mathrm{src}(a)}$，端口日程对齐 | 每节点每位置至多一次处理；区域递归、位置继续及记录嵌入 |
| [TimedDAG](timed-dag-region-selector-learning-note.md) | 有限无环消息图、有限输入及严格递增端口日程 | 唯一有限完整记录、规范作用、合法暴露、关闭与切面继续 |
| [PositiveDelayGraph](positive-delay-graph-finite-cut-learning-note.md) | 有限正时延消息图，允许空间有环，输入局部有限 | 相容有限切面记录、区间组合、强连通分量求值 |
| [分块求值](timed-dag-chunk-prefill-learning-note.md) | 固定上述语义并给出精确联合契约 | 状态块、输出批、契约相对阶段及整窗口求值 |

SettleGraph 向 TimedDAG 保留全部图对象、端口和局部函数，仅重索引位置坐标并补齐空档状态。TimedDAG 完整记录逐切面限制后得到 PositiveDelayGraph 的相容记录族。严格分层使区域依赖向前，时间对齐进一步保证单位置单次处理；两项条件各有作用。

共同输入、广播 Full、终端聚合、有值输出保证均可作为附加实例。广播用 $\operatorname{Full}_v=\Delta_v\circ\operatorname{EmitValue}_v$ 表达，在三个层级使用同一类型。

## 记录、边界与联合求值

规范作用结果与调用标签分别记录返回值和所需输入。例如 $P$ 返回 $(h,\widetilde q,d)$，完整准备标签为 $(B,q,h,\widetilde q,d)$。旧状态须保留到 Next 使用，不能由结果三元组一般地恢复。

切面继续状态为

$$
Q_b=(b,(q_v^b)_v,(y_j^b)_j,W_b),\qquad
W_b=\{m:\operatorname{send}(m)<b\le\operatorname{time}(m)\}.
$$

共同区间接口为 $\Phi_{a,b}(Q_a,E_{[a,b)})=(\mathcal U_{[a,b)},Q_b)$。封闭下界证明输入完整；区间记录的函数值只依赖切面状态与外部记录。相邻记录通过 $\odot_b$ 粘合，共同状态边界识别一次，跨界消息只在其发送所属区间登记为新消息。

联合函数在 $\mathsf{AdmIn}(K)$ 上等于 $\operatorname{RefBlock}_K$，返回实际作用支持集、全部规范结果及范围要求的状态、消息和输出。BatchRegionState 只覆盖 $P/S/U$，BatchRegion 同时覆盖区域 Full。批次数、工作量与并行深度相对于固定契约及求值策略分析。

## 数学实例与实现对应

[带权 KV 局部教材](weighted-kv-sparse-activation-example.md) 选择具体空间、更新、评分、预算函数和广播 Full，给出连续性、训练信用路径、局部成本与联合求值见证。[分层架构实例](weighted-kv-layered-example.md) 另行绑定拓扑、时间、来源类别及输出槽，并定义任务接入与训练方案。组合核对容量、宽度、时间尺度和各性质的前提，局部函数沿用同一定义。

实现表示先经固定 Decode 得到数学值记录，再经遗忘投影删除辅助坐标。解码恢复确切状态和快照，不重执行参考递归来修补结果。有效记忆等有损投影、输出读出及指定反向规则各有独立比较关系。计算系统用语在教材附录与这些数学对象对应。
