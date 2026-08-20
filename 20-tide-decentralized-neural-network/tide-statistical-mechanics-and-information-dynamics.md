---
type: research-memo
status: active
tags:
  - tide
  - statistical-mechanics
  - information-dynamics
  - semantic-quotient
  - research-hypothesis
---

# Tide、统计力学与信息动力学

> [!summary] 本页定位
> 本页审视 [[30-technical-notes/hilbert-sixth-problem-and-ai-entropy|从希尔伯特第六问题到普利高津：AI 熵增与耗散结构类比]] 与 Tide 主线的关系。它是一份研究备忘，不是正式数学文档，不向 [[tide-mathematical-foundations]] 导入定义、引理或定理。凡是尚未给出概率空间、函数、关系、极限过程或误差界的物理对应，均只视为类比或待检验假设。

> [!note] 与两条战略路线的关系
> Graph 收缩线提供更丰富的局部路径、汇聚和状态对象，适合提出路径相关性与宏观极限问题；checkpoint 生长线提供稳定基线、并行候选和配对反事实，更适合判断这些统计量是否真的预测质量、梯度或训练稳定性。两条路线可以共享测量方法，但统计相似性不能证明架构汇合。

## 一页版结论

原文最有价值的部分不是“熵增可以证明 AI”，而是提出了三个适合 Tide 继续追问的问题：

1. 微观计算历史经过压缩后，哪些信息必须保留，才能继续满足同一个可观察语义契约？
2. 大量局部、稀疏交互形成的路径重汇聚与相关性，如何影响表示、梯度、路由和训练稳定性？
3. 当 site 数、深度切片数或空间尺度增长时，Tide 是否存在可描述的宏观统计演化？

与 Tide 现有理论最直接的接口是：

- “粗粒化后仍保持有效动力学”对应 contract-relative semantic quotient，而不是未经定义的熵增。
- KV、SSM、Linear Attention accumulator 对应 reference contract 中的持久状态或边界状态，而不是绝对意义上的“完整历史”或“历史摘要”。
- 有限碰撞历史与有限 logical event DAG 都使用图记录依赖，但二者的顶点、边、概率结构和定理目标不同，不能直接互换。
- 高性能 `prefill` 的关键仍是低 span 组合结构。路径汇聚、记忆和反馈本身既不是充分条件，也不是否定条件。

本页建议新增一条位于正式 correctness 理论外侧的研究支线：

> 对 Tide 局部稀疏 Graph 的路径相关性、节点经验分布、路由占用分布和快慢状态进行可测量、可证伪的统计研究；只有在对象与尺度明确后，才进一步讨论 kinetic limit、hydrodynamic limit 或 dissipative structure。

## 1. 主张层级

本页使用下列四种标签区分结论强度。

| 标签 | 含义 | 是否可作为 Tide 证明前提 |
| --- | --- | --- |
| **正式结果** | 已在 Tide 数学文档中给出定义和证明 | 可以 |
| **工程事实** | 可由代码、artifact 或实验复现 | 只能作为实现证据 |
| **候选形式化** | 已给出可能的数学对象，但尚无完整定理 | 不可以 |
| **启发性类比** | 只迁移提问方式或直观图景 | 不可以 |

原文关于 Deng–Hani–Ma 工作的论文、长时间 Boltzmann 推导和 cumulant/molecule/cutting method 背景有真实文献来源。原文进一步把 H 定理、Loschmidt 悖论、Transformer 环结构与耗散结构连成统一叙事，这一部分主要属于启发性类比；不能视为上述数学论文对神经网络作出的推论。

## 2. 碰撞历史图与 Tide event DAG

### 2.1 共同点只到“用图记录历史”为止

Deng–Hani–Ma 工作中的 diagram 或 molecule 是微观粒子系统展开中的组合对象，用于组织 cumulant、碰撞历史和估计。Tide 的 logical event DAG 则是一次有限 reference execution 中实际事件及其直接语义依赖关系。

二者都可以回答“当前对象依赖哪些更早对象”，但至少有下列差异：

| 方面 | 碰撞历史 diagram | Tide logical event DAG |
| --- | --- | --- |
| 顶点 | 碰撞、粒子历史或展开对象 | 计算、状态、控制、消息、可见性或提交事件 |
| 边 | 碰撞历史中的组合关联 | reference semantics 要求的直接依赖 |
| 主要用途 | 对展开项作概率、几何与组合估计 | 证明某个 schedule/lowering 保持语义 |
| “环”的作用 | 可能引入额外约束与相关性 | 有向环意味着普通拓扑求值不可直接成立 |
| 结论类型 | 极限、误差小量、相关性控制 | exact correctness、partial order、work/span |

因此，“两者都是图”不足以把碰撞图上的 cycle estimate 搬到 Tide event DAG。

### 2.2 四个容易混淆的对象

1. **有向 event cycle**：事件依赖形成有向环。Tide strict core 要求正时延展开或封装为独立 fixed-point/root-solve kernel。
2. **静态空间 Graph 的带延迟环**：空间节点可以重复使用，但有限 token/round/version 展开后仍可能得到 DAG。
3. **路径重汇聚**：同一祖先的影响经两条不同有向路径到达同一后继，形成 diamond。它不是有向环。
4. **自回归反馈**：输出影响后续输入。固定有限 token 序列并按输入位置展开后，它通常仍是从较早位置指向较晚位置的 DAG。

标准 Transformer 的 residual 连接在展开图中是从第 $\ell$ 层到第 $\ell+1$ 层的 identity edge，不是同一事件上的 self-loop。把 residual、diamond、跨 token 反馈和硬球 recollision 都称为“环”，会丢失 Tide 正在研究的依赖差异。

### 2.3 对 Tide 的真实启发

正式 correctness 仍使用 logical event DAG。统计力学类比可在其外侧增加另一个问题：

> 在已经正确展开的 event DAG 上，路径重汇聚、共同祖先和重复影响的统计量是否与表示干涉、梯度方差、路由漂移或生成退化相关？

这是新的可检验问题，不是现有 event-DAG theorem 的推论。

## 3. 粗粒化与 semantic quotient

### 3.1 最直接的数学桥梁

设 fine reference contract 的状态空间为 $\mathcal S^{fine}$，coarse contract 的状态空间为 $\mathcal S^{coarse}$，并给定状态抽象函数：

$$
\alpha:\mathcal S^{fine}\to\mathcal S^{coarse}.
$$

再设 fine 与 coarse 的单步转移分别为：

$$
\mathcal T^{fine}:X\times\mathcal S^{fine}
\to Y^{fine}\times\mathcal S^{fine},
$$

$$
\mathcal T^{coarse}:X\times\mathcal S^{coarse}
\to Y^{coarse}\times\mathcal S^{coarse},
$$

并给定输出抽象函数：

$$
\beta:Y^{fine}\to Y^{coarse}.
$$

若对任意 $x\in X$ 和 $s\in\mathcal S^{fine}$，由

$$
\mathcal T^{fine}(x,s)=(y,s')
$$

与

$$
\mathcal T^{coarse}(x,\alpha(s))=(\widehat y,\widehat s')
$$

总能推出

$$
\widehat y=\beta(y),
\qquad
\widehat s'=\alpha(s'),
$$

则 coarse transition 精确实现了 fine transition 相对于 $(\alpha,\beta)$ 的商语义。这正是 [[tide-mathematical-foundations#定义 2.4：transition semantic quotient|semantic quotient]] 的核心关系。

原文所说“高阶相关信息离开当前可观察层，但宏观动力学仍有效”，若要进入 Tide 数学，必须被改写为上述交换关系，或者改写为明确带误差界的 approximate simulation。

### 3.2 丢失 provenance 何时安全

消息聚合、cache 压缩和 memory summary 都可能是多对一映射。多对一并不自动错误；安全性取决于被丢失的差异是否会被任何后继 kernel 或最终输出观察到。

Tide 已有的约束是：

- exact profile 必须证明 aggregation quotient 或局部交换关系。
- approximate profile 必须另行声明误差度量、误差预算和累积方式。
- 后继 kernel 不得用昂贵逆问题恢复上游已压缩信息，再把恢复成本藏在 runtime 之外。

这比“相关性被稀释”更适合作为 cache eviction、node-state compression 和 message aggregation 的工程准则。

## 4. KV、SSM 与 contract-specific sufficient state

### 4.1 KV cache 不是完整计算历史

标准 causal attention 的 KV cache 保存每层过去位置的 key/value 投影及实现所需的位置、长度或 mask metadata。它通常不保存：

- 过去位置的 query。
- FFN 中间激活。
- 完整 residual stream 的所有版本。
- 每个输出值在 event DAG 中经过的全部路径 provenance。

因此，KV cache 不是绝对意义上的完整历史。更准确的说法是：

> 对固定 Transformer 参数和未来 causal-attention read contract，过去 K/V 是实现精确 cached attention 所需的 contract-specific persistent state。

把 KV cache 纳入状态后，decode 可以写成：

$$
(y_t,S_{t+1})=\mathcal T(x_t,S_t).
$$

在这个扩展状态空间上，Transformer transition 是 Markov 的。称它“非 Markov”只能表示观察者故意遗漏了 KV 等必要状态。

### 4.2 SSM 不是自动得到的 Transformer 闭包

Mamba/SSM、Linear Attention 和 Transformer 可以分别拥有自己的 reference contract：

- Transformer 的状态通常随历史长度增长。
- SSM 的状态维度通常固定，并按 recurrence 更新。
- Linear Attention 保存对其 kernel 足够的 prefix accumulator。

SSM state 对 SSM 自己的 transition 是精确状态。它是否是某个 Transformer 的有效 coarse state，必须给出 $(\alpha,\beta)$、任务分布和 exact/approximate simulation 结果，不能由“固定状态类似 Boltzmann closure”自动推出。

## 5. 与 `prefill = decode` 和 adaptive routing 下界的关系

原文中的熵、采样与碰撞环不改变 Tide 当前的 correctness 定义：

$$
\mathcal C_L(x_{B:B+L},C_B)
=
\operatorname{Fold}_{\mathcal T}^{L}(x_{B:B+L},C_B).
$$

对于给定输入 chunk，这个等式比较同一个 reference transition 的 chunk implementation 与逐位置 fold。自回归采样可以位于该 transition 外部；只要比较时固定同一输入序列和同一左边界状态，就不需要引入热力学熵。

路径拓扑也不直接决定高性能 prefill：

- GPT 有大量跨位置依赖和路径重汇聚，但 causal attention 提供 causal-bulk implementation。
- Mamba 有跨位置 recurrence，但 affine map composition 提供 scan implementation。
- 一个没有空间环的 layered Graph 仍可能因不可组合的 stateful selector 形成 $\Omega(L)$ adaptive depth。

因此，Tide 的判据仍是：node/subgraph 是否属于 token-local、scan-composable、causal-bulk、有限 chunk-wide routing stage 或其他已证明低 span 的 family。所谓“环预算”不能替代 [[adaptive-routing-prefill-lower-bound]] 中的 adaptive-depth 分析。

## 6. 对 HB-Sliced 更有价值的统计力学视角

### 6.1 为什么 Tide 比 Transformer 更接近局部相互作用系统

HB-Sliced 当前候选明确具有：

- 空间节点与局部有界度连接。
- 多深度切片传播和可配置的层级 partition。
- 稀疏激活和局部 selector。
- 节点持久状态、控制状态与在途消息。
- always-on backbone，以及可进一步声明固定寿命和 merge point 的分支接口。

若寻找 reaction/transport、interacting-particle 或 kinetic-system 类比，这些对象比“把 token hidden 当成粒子”更自然：

| Tide 对象 | 候选物理角色 | 当前结论强度 |
| --- | --- | --- |
| 节点状态 | 离散空间上的局部场变量 | 启发性类比 |
| edge message | 局部输运载荷 | 启发性类比 |
| node kernel | 局部反应或状态转移 | 启发性类比 |
| selector/allocator | 门控、稀疏反应或资源约束 | 启发性类比 |
| backbone | 稳定公共输运与梯度通路 | 架构事实，可实验 |
| branch/merge | 有限生命周期扰动及回注 | 候选接口，可实验 |

但 HB-Sliced 的 learned kernel、层级异质性和 deterministic routing 与稀薄硬球系统仍有本质差异。局部有界度也不自动产生 propagation of chaos；局部相关性可能长期存在。未来应根据模型结构选择 interacting-particle limit、hydrodynamic limit、local weak limit 或其他工具，而不是预设一定得到 Boltzmann 方程。

### 6.2 候选多尺度对象

考虑一族有限空间 Graph：

$$
G_N=(V_N,E_N),
\qquad N=|V_N|.
$$

给每个节点 $v\in V_N$ 指定类型 $r(v)$、神经状态 $q_v^t$、控制状态 $c_v^t$ 和激活变量 $a_v^t\in\{0,1\}$。对某个节点类型 $r$，可定义候选经验测度：

$$
\mu_{N,r}^{t}
=
\frac{1}{|V_{N,r}|}
\sum_{v\in V_{N,r}}
\delta_{(q_v^t,c_v^t,a_v^t)},
$$

其中：

$$
V_{N,r}=\{v\in V_N\mid r(v)=r\}.
$$

这只是候选形式化。后续需要逐项声明：

1. $t$ 是输入位置、绝对轮次还是训练步。
2. 状态空间及其拓扑或度量。
3. Graph 序列如何随 $N$ 增长。
4. 随机性来自数据、初始化、routing、训练采样还是显式噪声。
5. 希望证明的是依概率收敛、分布收敛、稳定性还是有限尺度误差界。

对层级化 Tide，更可能需要按 global hub、region、cell、leaf 分类型，而不是假设所有节点 exchangeable。

## 7. 候选路径相关性研究

### 7.1 不使用含糊的“环密度”

在有限 event DAG $D=(\mathcal E,\mathcal A)$ 上，更适合分别研究：

- 两个事件是否具有共同祖先。
- 同一祖先到同一后继是否存在多条不同有向路径。
- 两条路径在哪个事件分叉、在哪个事件重汇聚。
- 不同路径携带值的 support 是否重叠。
- 局部 Jacobian 沿路径相乘后，对同一输出的贡献是否同向、抵消或高度相关。

这些对象可以支持三类实验：

1. 路径重汇聚与 residual/branch 表示冗余是否相关。
2. 路径 overlap 与 selector/节点梯度方差是否相关。
3. 长期生成退化是否与某类来源的 influence concentration 相关。

仅统计 attention map 上的非零边数或无向 cycle 数通常不够，因为它忽略权重、符号、值向量、非线性和后续 normalization。

### 7.2 与训练风险的接口

当前 Tide 已关注路径级分布漂移和长路径信用分配。路径相关性研究可以增加下列 artifact：

- 每个 merge 的有效来源数。
- 共同祖先占比与 support overlap。
- 各来源对输出或 loss 的 gradient attribution。
- branch delta 的范数、夹角和抵消率。
- 同一语义输入在不同 checkpoint 的路径 influence drift。
- 每个 receiver 的 Receive/Update/Read/Emit coverage，以及这些量随传播深度的衰减。
- receiver-private state 的 write-to-read 延迟、read sensitivity 与 freeze/clear/shuffle/no-read knockout 差异。
- selected-dispatch 与 broadcast-observe matched pair 的 source coverage、state use 和路径相关性差异。

它们是训练诊断指标，不是 `prefill = decode` correctness artifact。

路径相关统计必须区分四种常被口语合并为“路径长”的量：静态拓扑路径长度、某个 Token 的实际传播 hop 数、实际执行的昂贵模块数，以及 state write 到以后 read 的 Token 距离。它们分别对应拓扑、通信/控制、计算和延迟信用，不应合并为一个标量后直接归因。

## 8. Selector 的信息论指标

### 8.1 路由占用熵只测均衡

设在某个明确的统计窗口内，节点 $v$ 被激活 $n_v$ 次，并令：

$$
p_v=\frac{n_v}{\sum_{u\in V}n_u}.
$$

可定义 Shannon route-occupancy entropy：

$$
H_{route}=-\sum_{v:p_v>0}p_v\log p_v.
$$

$H_{route}$ 较高通常表示激活分布更均匀，但它不自动表示：

- selector 使用了语义信息。
- 节点形成了专门化。
- 输出质量更高。
- routing 可在 token 方向并行。
- 多 batch 或不同 chunk 切分保持语义不变。

因此必须联合测量：

- route entropy 与最大/最小负载。
- route 与语义标签、输入 feature 或任务类型的 mutual information。
- route churn、时间自相关和 checkpoint drift。
- 每个层级的激活率、梯度覆盖与语义覆盖。
- Receive/Update 覆盖、later-read state use 与有效梯度覆盖；激活均衡不等于训练均衡。
- chunk/decode/batch invariance artifact equality。

### 8.2 不能混用的“熵”

| 名称 | 数学对象 | 可回答的问题 |
| --- | --- | --- |
| 热力学熵 | 物理系统状态与能量交换的热力学量 | 硬件和环境的物理耗散 |
| Boltzmann $H$ 或 kinetic entropy | 粒子分布函数的泛函 | 动理学方程的宏观不可逆性 |
| token-distribution entropy | next-token 概率分布的 Shannon entropy | 模型预测不确定性 |
| route entropy | 激活节点分布的 Shannon entropy | 负载集中或均衡 |
| mutual information | 两个随机变量的联合分布泛函 | route 是否携带语义或观测减少多少不确定性 |
| hidden 几何扩散 | 向量分布的协方差、谱或流形统计 | 表示是否集中、各向异性或漂移 |
| contract information loss | 抽象映射合并了哪些可区分状态 | 压缩是否保持指定语义 |
| 任务质量 | loss、accuracy、reward 或 verifier 结果 | 系统是否完成任务 |

这些量之间没有无条件等价关系。“高熵”“低熵”“信息丰富”“有序”和“高质量”必须分别声明数学对象，不能互相替换。

## 9. 耗散结构何时才成为可研究命题

把训练或推理称为 dissipative structure，目前只能作为类比。若要形成 Tide 命题，至少需要给出：

1. 系统边界：哪些变量属于系统，哪些属于环境。
2. 随机状态过程：例如 $Z_t$ 的状态空间与 transition kernel。
3. 能量或信息通量：输入、输出和擦除分别对应哪个可测量量。
4. 熵泛函或 Lyapunov functional：它作用在哪个概率分布上。
5. 稳态或长期分布：所谓“由流维持”具体表示哪种收敛或不变分布。
6. 序参量：路由占用、feature amplitude、状态相关长度或其他明确函数。
7. 阈值或分岔：控制参数变化时，哪个统计量发生何种可重复变化。

在这些对象缺失时，下列说法均不能承担证明：

- LayerNorm 是恒温器。
- attention temperature 是字面热力学温度。
- 采样把 Shannon entropy 排出系统。
- 训练权重是储存的负熵。
- AR 会话严格属于 Prigogine dissipative structure。

硬件耗电与散热是真实物理耗散，但对几乎所有计算都成立，不能单独解释 Tide 的算法或模型优势。

## 10. 与 Control Feedback 和 Memory 线的边界接口

原文把 prompt、RAG、工具返回和 verifier 信号称为负熵输入。这一说法适合作为直观提示，但跨研究线时应改写为：

> 系统通过 observation/action event 获得外部信息，更新显式状态或 belief，并可能降低任务相关不确定性。

对 Control Feedback，最直接的候选量是某次局部读取、工具调用或验证前后的 conditional entropy、expected information gain、错误定位率和后续修复收益。对递归分解与 Memory，最直接的问题是 raw trace、summary 和 verified artifact 分别保留了哪些后续可观察语义。

这些问题与 Tide 的 semantic quotient 和 provenance 相通，但它们属于不同 reference contract：

- Tide 研究模型/runtime 的消息、状态、路由与 chunk/decode 等价。
- Control Feedback 研究显式状态事件和主动选择反馈信源。
- Recursive Decomposition/Memory 研究可验证、可复用的子问题 artifact。

三条线可以共享“状态压缩是否保留任务语义”和“观测是否提供有效信息”两个问题，但不能共享未经重新声明的状态空间、事件或正确性定理。

## 11. 推荐研究顺序

### 第一阶段：沿用现有 exact contract

1. 把 KV、SSM、node memory、selector load state 分别写成 reference contract 的状态坐标。
2. 对每种聚合或压缩声明 exact quotient、approximate simulation 或不作保证。
3. 保持 `prefill = decode`、artifact equality 和 adaptive-depth 分析不变。
4. 对 checkpoint 生长实验记录源模型、growth operator 与结构变异边界，不把不同谱系模型的统计量直接混合。

### 第二阶段：先测量，不预设物理理论

1. 为 HB-Sliced/HB-Line 增加 route entropy、语义互信息、route churn 和层级负载统计。
2. 沿 [[tide-checkpoint-growth-experiment-contract]] 的两条工作流和 matched propagation profiles，为 receiver/branch/merge 增加来源数、support overlap、state use、delta 夹角和 gradient attribution；历史 P0-P6 只作为局部诊断坐标。
3. 在固定参数、数据与 schedule 下检查这些量是否能预测训练不稳定或质量变化。

### 第三阶段：构造最小随机模型

1. 固定一族局部有界度 Graph。
2. 使用明确的随机输入、随机初始化或 routing law。
3. 定义节点经验测度与有限尺度 observable。
4. 先证明或数值验证有限时间稳定性、集中性和相关长度。

### 第四阶段：再选择极限理论

根据最小模型的结构，判断适合研究 propagation of chaos、mean-field、hydrodynamic limit、local weak convergence、non-equilibrium steady state，还是只保留有限尺度统计。不要先决定“必然是 Boltzmann”或“必然是耗散结构”。

## 12. 当前可主张与不可主张

当前可以主张：

- 原文提供了与 Tide semantic quotient、persistent state、path provenance 和局部稀疏 Graph 相交的研究问题。
- contract-relative coarse-graining 可以由现有 Tide semantic quotient 精确表达。
- route entropy、path overlap 和节点经验测度可以被定义为新的实验或候选数学对象。
- Tide 的真实空间局部性使 interacting-system 视角比在标准 Transformer 上更自然。

当前不能主张：

- Deng–Hani–Ma 的数学结果证明了 Transformer/Tide 的熵增、可靠生成或训练稳定性。
- Transformer event DAG 中的 diamond、residual 或 AR feedback 等同于硬球 recollision。
- KV cache 是完整计算历史，或 SSM 是 Transformer 的已证 kinetic closure。
- 环越少就越容易 prefill，或环越多就越智能。
- 当前 Tide/HB-Sliced 已经具有 kinetic limit、propagation of chaos 或 dissipative structure theorem。
- 任意信息丢弃、cache eviction 或 selector 稀疏化都构成安全“排熵”。

## 参考入口

- [[30-technical-notes/hilbert-sixth-problem-and-ai-entropy|从希尔伯特第六问题到普利高津：AI 熵增与耗散结构类比]]
- [[tide-mathematical-foundations|Tide 数学基础]]
- [[adaptive-routing-prefill-lower-bound|Adaptive Routing Prefill Lower Bound]]
- [[tide-model-architecture-and-training|Tide 模型架构与训练]]
- [[tide-background-history-and-references|Tide 背景、历史谱系与参考资料]]
- [[10-control-feedback-token-instruction/current-mainline|控制反馈：当前主线]]
- [[11-recursive-decomposition-memory/mechanism-landscape|递归分解与 Memory 机制谱系]]
