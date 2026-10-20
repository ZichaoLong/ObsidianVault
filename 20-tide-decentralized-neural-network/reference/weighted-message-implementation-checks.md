---
type: implementation-conformance-guide
status: active
tags:
  - tide
  - local-semantics
  - validation
---

# 带权消息架构：实现与数学定义的对应

本文核对已选择的组合与数学定义是否一致。共同函数见[局部架构](../local-semantics/weighted-message/architecture-learning-note.md)，评分、分配和反向见[区域分配](../local-semantics/weighted-message/region-allocation-learning-note.md)，组合性质见[共同架构 §6](../local-semantics/weighted-message/architecture-learning-note.md#6-数值性质的组合)，记忆见 [KV](../local-semantics/weighted-message/kv-memory-learning-note.md)与[循环模块](../local-semantics/weighted-message/recurrent-memory-learning-note.md)。训练效果和研究优先级由[独立研究文档](../memos/training/weighted-message-research-questions.md)讨论。

## 1. 采用声明与比较对象

实现记录不可变上游提交、具体函数组合、图、时间、参数与状态表示。列出支持的 memory_family、memory_read、read_mode、评分、query_weight、allocation_base 和 selection_mode，检查各键的生效范围及类型。记录精度、容差、求根终止规则、下溢和裁剪，以及不可微边界的反向约定。名称迁移与采用记录见[版本对应](../records/semantic-versions-and-adoption.md)。

| 比较 | 必须保留的对象 |
|---|---|
| 参考递归与同一函数实现 | 完整 P/S/U/F 作用支持、结果、快照、持久状态、逐边与逐端口值族 |
| 联合求值与逐次求值 | 上述记录及右切面，包含在途消息和原始时钟 |
| 精确零消息的增删 | 共同架构命题 1 声明的消息投影、有效状态与读出；原始事件支持可不同 |
| 弱输入的极限 | 共同架构命题 2 声明的消息投影、有效状态与读出 |
| 约束分配与硬选择的极限 | 固定参数、单位输入、有限切面、硬运行评分条件下的数值投影 |
| quad／固定 $\alpha>1$ 的 ent 的正温度精确性 | 在上述条件及充分小正温度下，比较实际作用支持、全部作用结果、原始状态和完整切面 |
| 反向实现 | 声明的精确解映射、显式分配或另行指定反向的向量—Jacobian 乘积 |

有效状态投影可以遗忘过期项或不同时间戳，不能替代精确状态解码。数值试验核对实现，命题的一般性由证明给出。候选、控制正分量、Full 调用和消息数分别记录。

## 2. 共同函数

| 核对项 | 覆盖情形 |
|---|---|
| Agg | SrcClass 的带标签端口／入边定义域、完整纤维、来源、平行原子、空输入和零强度；同类别的不同原子各参与一次；同参数面对不同邻域仍分别求值 |
| Read 与描述 | 先定义后使用的类型；Read$^+$／$^-$／$^0$ 的状态和时间；描述宽度与区域 SelStep 相容 |
| Next | 所有候选保留接收更新；未激活也保留；不得读取或重算 Full |
| SelStep | 空候选、全零接收、单候选；每候选都有控制；单点历史；$K$ 按所选函数绑定 |
| Full | 正控制才激活；$(c,G)$ 的强度只在数值投影中乘一次；返回边与端口两个族 |
| 广播与读出 | 出度不除分强度；端口记录保留身份；空读出、相消与正强度存在分别核对 |

增益检查 $1\le\gamma\le\gamma_{\max}$、$\mu=\min(1,\gamma (r^{\mathrm{in}})_+)$。query_weight=received 时，固定接收与记忆特征，改变增益不能改变 query；direct_attention 且 allocation_base=received 时，固定评分后只经外乘 $\mu$ 生效。query_weight=mu 的原依赖继续保留。

相同参数与输入的共享求值只记一次工作，仍须恢复各节点的原始状态。前向移除依赖与 stop-gradient 的反向约定分别检查。

## 3. 区域分配

### 3.1 约束分配与硬选择

对实现支持的 quad、bern、Shannon 与固定形状 ent，检查节点上限、总和范围、互补条件和最优性；小规模可与独立求解或断点算法比较。覆盖单点可行集、$M=1$ 两侧、全低分、总和上下界、松弛总和、零个或一个未饱和分量。

求根区间、乘子符号、残差与误差分别报告。softmax 等值按[区域分配 §3.2](../local-semantics/weighted-message/region-allocation-learning-note.md#32-与-softmaxsparsemaxentmax-的关系)核对：区分对任意评分成立的单位上限条件与给定评分的可行性判定。覆盖非单位上限但 softmax 可行的算例，以及触及、超过上限时的前向与边界反向。ent 的 $\alpha=2$ 在总和可变时核对阈值移位。

硬选择核对稳定平票顺序、零接收排除、全非正时最高分保留与激活上限。硬函数的训练替代梯度属于独立声明。

### 3.2 无求根规则

| 规则 | 核对内容 |
|---|---|
| direct_attention | 两种基权重；$c\le\mu$；正接收全激活；单候选达到自身上限；不使用 k、eta、正则 |
| unit_attention | uniform 按真实候选，mu 按正接收；有支持时总和 $1$；允许 $c_v>\mu_v$ |
| pooled_attention | 总和 $\min(1,M)$；允许单节点超过 $\mu_v$；全部接收趋零时总发送趋零 |
| proportional | 与评分无关；总和 $\min(k,M)$；保留节点上限；无分配到评分的直接梯度 |

复现区域教材的弱接收算例、评分平移、候选置换、全零分支、很小正权重和大评分差。数学上的正支持不能以浮点下溢或近零裁剪代替。uniform 区分真实零强度候选与张量填充位置。

### 3.3 反向与边界

约束分配使用区域教材 §4.2 的隐式反向，或者明确声明有限迭代映射。光滑分支内用不跨界的扰动比较评分、上限和温度；总和固定在上下界时核对加权中心化，总和上下界都松弛时核对独立响应导数。复现该节 quad 的共同评分平移算例；$\sum_v a_v^{\mathrm{resp}}=0$ 单独处理。不可微点用声明的单侧或广义导数核对。

Attention 规则分别检查 $dp$、外乘幅度或区域总量的乘积法则。对原 direct_attention 基权重 mu，验证两条直接上限依赖；received 只在固定接收和评分时移除基权重中的增益通路。pooled_attention 在 $M<1$ 有总量导数，$M>1$ 无该项，$M=1$ 声明边界约定。

完整链路检查 query、key、评分头、增益头、记忆描述及写入。全零基权重处一般没有通常 Jacobian，遮罩自动微分与方向导数分别记录。跳过零 Full 和求内容后乘零的边界反向分别说明。

## 4. 记忆模块

| 模块 | 核对内容 |
|---|---|
| KV 写入 | 正接收一条、零接收不改；权重与 K/V 内容分开；私有适配恢复独立投影；未激活仍写入 |
| KV 读取 | sum／qry；最后一条弱记忆；窗口过期和长空档；qry 从原始 key 投影；位置按原始时间 |
| KV 表示 | 原始或旋转 key 的解码；清理前过期项与快照身份；分段不重排位置 |
| affine／delta | 完整状态、初态；衰减与写入次序；key 范数、门范围；两个时间尺度 |
| 循环弱输入 | 写入和遗忘共同趋中性；零事件保留原元组；插入趋弱事件后有效未来状态收敛 |
| 循环读取 | sum／state，旧、新、初态读取；逻辑时间衰减、单节点算例 |
| 循环联合求值 | 顺序与仿射复合的每个中间状态；矩阵复合方向；时间戳、零事件和右切面 |
| 异构组合 | 相同消息宽度、区域描述相容；每模块使用自己的状态、时间与表示解码 |

## 5. 数值性质、图与继续

数值比较按共同架构 §6 的固定图、参数、原始时间槽和有限切面进行，状态模块分别核对该节的局部假设。精确零消息增删与弱输入极限分别依照[性质对照](../local-semantics/weighted-message/architecture-learning-note.md#64-发送规则的性质对照)选择函数范围，覆盖弱消息、弱候选、全零接收、空档和正时延反馈。

复现共同架构 §6.2 的固定总强度 Attention 算例，分别检查 mu 与 uniform 的零候选行为。混合组合使用全候选参考计算时，保留消息存在掩码；只有满足零消息删除条件时，才以显式零消息替代缺席并比较相同数值。

复现区域分配 §5.3 的第二名间隔条件与四候选算例，核对有限正温度的精确分配。软硬比较使用单位输入和硬运行的评分条件；另复现平票、阈值临界及固定 $0<\mu_v<1$ 上限的反例。对全区域 quad／固定 $\alpha>1$ 的 ent，按共同架构附录 A.4 从硬运行取得有限温度界，并比较完整记录与切面。其他情形的数值收敛按自己的支持性质判断。pooled_attention 的固定正温度连续性不直接给出整网硬化保证。

[全连接拓扑](../topologies/fully-connected-layered.md)与 [HB-Lattice 拓扑](../topologies/hb-lattice.md)分别核对节点、区域、边、端口和时间对齐；图规模按固定结构计数。[全连接实例](../instances/fully-connected-layered-weighted-message.md)核对单位接收、配置等值及 KV 写入时间；[HB 实例](../instances/hb-lattice-weighted-message.md)核对区域到达、候选并集及广播计数。两类实例均检查各记忆模块的完整绑定和实际工作量。复现 direct_attention 的三层总量 $1,1/4,1/8$ 与固定总量规则的 $1,1,1$；不同评分的响应另按函数核对。

整段、不同长度分段、逐位置和位置内部切面均比较完整记录与边界。左状态须含原始时钟、区域历史和在途消息；给定完整驱动窗口后再核对各模块的联合契约。变更参数、位置或记忆类型后的继续，使用另外声明的转换或重算规则。

报告明确通过范围、误差、未覆盖组合与复现入口。性能测量与训练质量独立报告，不从局部数学性质推出加速或效果。

## 6. 仓库文档检查

[check_documents.py](../tools/check_documents.py)核对本地链接与锚点、四份局部教材的公式编号与 TeX 分组、空目录、正典版本及引用方向。正典的仓库内链接只指向四份正典之一，局部教材、实例与检索文档向上引用。脚本从自身位置定位仓库，可在任意工作目录执行；在仓库根目录使用：

```bash
python -B 20-tide-decentralized-neural-network/tools/check_documents.py
```

正典的预期哈希对应已审阅版本。确需修改正典时，先审阅差异并记入修订记录，再更新预期哈希。结构检查不判定数学命题的真假；神经函数的验证仍使用前述比较对象。

## 附录：教学参考程序的对应

[正时延图教学程序](../examples/positive_delay_graph_reference.py)用整数与有理数函数展示切面、快照和调度重排。其范围及教学例子见 [PDG 附录 S.10](../positive-delay-graph-finite-cut-learning-note.md#s10-有限检验的比较对象)。

| 程序名称或表示 | 数学对应 |
|---|---|
| Spec.budget | 正典的激活数量容量 $K_j$ |
| Spec.observe_all | 状态采用模式 $\kappa_j$；True 为全部候选采用 |
| update、read、select、next_state、full | Upd、按已选模式包装的 Read、SelStep、Next、Full |
| proposals、comparison_states、states | 候选状态、Full 快照、持久状态 |
| Full 返回的两个字典 | 逐边和逐端口值族；字典缺项解码为该坐标的 $\bot$ |
| Continuation | 切面 $Q_b$，包含节点状态、选择历史与跨界消息 |
| run_random_ready_schedule | 给定参考事件集合后，在其依赖图上重排求值 |

该程序覆盖延迟自环、两节点环、门控与选后清空，并比较完整记录和继续状态。在线封闭下界推进、局部神经函数和设备求值各需相应实现证据。这里的字段对应不改变教材签名。
