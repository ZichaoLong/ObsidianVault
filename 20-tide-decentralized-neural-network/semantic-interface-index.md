---
type: mathematical-index
status: active
tags:
  - tide
  - mathematics
  - semantic-anchor
---

# 数学符号与函数对应索引

本页汇集四篇教材和局部函数实例的共同名称。定义与证明分别位于所链接教材；各篇的教学重述沿用这些数学对象。

## 基础对象

| 符号 | 含义 |
|---|---|
| $V,A,J,\rho,\mathcal R_j$ | 节点、消息边、区域标识、区域归属、区域 |
| $\theta,t,\delta$ | 逻辑时间、输入位置、正边时延 |
| $P,P_\bot$ | 消息值空间及增加缺席标记后的空间 |
| $B_{v,\theta},\mathcal C_{j,\theta},\mathcal A_{j,\theta}$ | 完整输入纤维、候选集合、激活集合 |
| $S_v,X_v,D_v,\mathsf C_v,Y_j$ | 节点状态、本地内容、描述量、局部控制、区域选择历史空间 |
| $q,\widetilde q,q^{\mathrm{cmp}},q^{\mathrm{next}}$ | 旧状态、候选状态、计算快照、下一持久状态 |
| $\tau_j,\kappa_j,K_j$ | 描述量模式、状态采用模式、激活容量上界 |
| $Q_b=(b,(q_v^b)_v,(y_j^b)_j,W_b)$ | 完整切面的继续状态 |

SettleGraph 的 $q_v^t$ 按输入位置索引。时间编码 $\theta_{v,t}=Dt+r_v$ 将其对应到一般图的逻辑时间坐标。分块输入步长记为 $\Delta_{\mathrm{in}}$，带权 KV 的平滑参数记为 $\tau_{\mathrm{soft}}$。

## 局部函数

以下类型见 [TimedDAG §4--5](timed-dag-region-selector-learning-note.md#4-节点的局部函数) 与 [PDG §1](positive-delay-graph-finite-cut-learning-note.md#14-内部消息输出和局部函数)。

| 函数 | 定义域与值域 |
|---|---|
| $\operatorname{Agg}_v$ | $\mathbb N\times\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_v)\to X_v$ |
| $\operatorname{Upd}_v$ | $S_v\times\mathbb N\times X_v\to S_v$ |
| $\operatorname{Read}_v^0$ | $\mathbb N\times X_v\to D_v$ |
| $\operatorname{Read}_v^-,\operatorname{Read}_v^+$ | $S_v\times\mathbb N\times X_v\to D_v$ |
| $\operatorname{SelStep}_{j,C}$ | $Y_j\times\mathbb N\times\prod_{v\in C}D_v\to\mathsf{Allowed}_{j,C}\times\prod_{v\in C}\mathsf C_v\times Y_j$ |
| $\operatorname{Next}_v$ | $S_v\times S_v\times\mathbb N\times X_v\times\{0,1\}\times\mathsf C_v\to S_v$ |
| $\operatorname{Full}_v$ | $S_v\times\mathbb N\times X_v\times\mathsf C_v\to(P_\bot)^{\operatorname{Out}(v)}\times(P_\bot)^{\operatorname{OutPort}(v)}$ |

其中 $\mathsf{Allowed}_{j,C}=\{A'\subseteq C:|A'|\le K_j\}$。Next 的两个状态参数依次为旧状态与计算快照。Full 的值经固定边和端口身份展开为消息与输出记录。

[SettleGraph §3--5](settlegraph-learning-note.md#3-每条边的一次结果) 取 $X_v=P$，聚合输入为带来源标签的非空序列，Full 返回单个 $P$ 值。[§10](settlegraph-learning-note.md#10-嵌入-timeddag) 用标签还原与广播提升 $\Delta_v$ 给出一般图中的对应函数。

[带权 KV §2.9](weighted-kv-sparse-activation-example.md#29-实例化配置) 列出该特例的全部绑定；其载荷函数名为 $\operatorname{EmitValue}_v$，一般图中 $\operatorname{Full}_v=\Delta_v\circ\operatorname{EmitValue}_v$。

## 作用、边界与联合求值

| 名称 | 数学含义 | 定义位置 |
|---|---|---|
| $P,S,U,F$ | 准备、选择、状态采用、完整输出四类作用及其规范值 | [TimedDAG §6.4](timed-dag-region-selector-learning-note.md#64-节点事件区域选择事件与四类作用) |
| $\operatorname{DoneTo}$ | 输入前缀关闭、相关状态与完整输出作用完成 | [TimedDAG §9.6](timed-dag-region-selector-learning-note.md#96-边下界怎样由上游完成推出) |
| $\operatorname{PublishedDoneTo}$ | 进一步包含相应内部消息已经纳入的条件 | 同上；[PDG §5.3](positive-delay-graph-finite-cut-learning-note.md#53-节点完成怎样推出出边封闭下界) |
| $\mathsf{AdmIn}(K),\mathsf{BlockOut}(K)$ | 作用范围的合法外部自变量与完整返回记录 | [分块 §2](timed-dag-chunk-prefill-learning-note.md#2-作用块外部边界与精确联合求值) |
| $\operatorname{ExpandFull}_{v,\Theta}$ | 将 Full 值族展开为作用、消息与输出记录 | [分块 §3.2](timed-dag-chunk-prefill-learning-note.md#32-逐坐标完整输出契约) |
| $\operatorname{RefBlock}_K$ | 边界唯一确定的参考联合函数 | 同上 |
| $\mathsf{ContractOwner},\operatorname{cown}$ | 联合契约的节点或区域归属 | [分块 §2.3](timed-dag-chunk-prefill-learning-note.md#23-精确联合求值与精化) |
| $\operatorname{Acts}(B,z)$ | 一次契约调用返回的实际作用支持集 | 同上 |
| $\operatorname{BatchFull},\operatorname{BatchState},\operatorname{BatchNode},\operatorname{BatchRegionState}$ | 完整输出、因果状态、节点联合、区域状态的精确见证 | [分块 §3](timed-dag-chunk-prefill-learning-note.md#3-三类节点契约与一种区域契约) |

PDG §10 对相同对象增加函数解释参数 $\mathbf F$。固定参数时，两篇采用相同的边界、支持集和精确性含义。TimedDAG §12.4 的 StatePath 给出一般状态递归的轨迹；BatchState 保留完整规范标签，其状态投影满足该递归。各项批次数同时依赖求值策略与契约族。

## 附录：实现对应的验证关系

实现可直接沿用上述函数名称，并记录相应数学对象及参数对应。具体数据表示通过固定解码取得数学值；联合求值通过精化取得规范作用记录。

- 局部函数：在声明的定义域上，解码后的结果等于对应函数值。
- 联合求值：实际作用支持集、各作用值、消息、输出与右边界状态等于参考记录。
- 层级嵌入：按已定义的时间、标签与输出映射比较记录。
- 切面继续：相同切面状态和后续输入产生相同后续记录。
- 特例比较：使用该特例明确指定的投影及其证明条件。
- 指定反向规则：另行比较声明的反向关系。

函数合并与不同存储表示均可通过这些关系说明其对应。具体检查、数值容差与验证结果由下游实现记录。
