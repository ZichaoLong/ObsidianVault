---
type: mathematical-model-instances
status: active
cssclasses:
  - textbook-math
tags:
  - tide
  - mathematics
  - instances
  - weighted-message
---

# 全连接分层图上的带权消息实例

本文在[全连接分层拓扑](../topologies/fully-connected-layered.md)上绑定带权消息的局部函数，给出 KV、稠密 Attention 和混合记忆实例，并推导各自的传播、继续与计算量。局部函数的定义与证明分别见[共同架构](../local-semantics/weighted-message/architecture-learning-note.md)、[区域分配](../local-semantics/weighted-message/region-allocation-learning-note.md)、[KV](../local-semantics/weighted-message/kv-memory-learning-note.md)和[循环记忆](../local-semantics/weighted-message/recurrent-memory-learning-note.md)。

## 1. 采用的定义与参数

### 1.1 图与局部选择

取拓扑定义中的深度 $L$、区域宽度 $n$ 和输入长度 $N$，沿用节点 $v_{\ell,s}$、区域、边 $a_{\ell,s,r}$、端口及日程，$D=L+2$。全部实例保持这份图与时间绑定。

| 实例 | 完整绑定 |
|---|---|
| KV 基线 | §2.1—2.3：KV 时间摘要、独立拼接评分、固定增益、约束 quad |
| 稠密 Attention | §2.5：沿用 KV 基线的状态、聚合与边界，替换区域评分和发送 |
| KV 与循环记忆 | §3：沿用指定 KV 组合的边界、聚合、评分与发送，逐区域替换状态及其读取 |

每个实例允许声明尺寸、矩阵、偏置和标量参数；所有选择与参数在一次模型绑定中确定。各区域使用相同载荷宽度，描述与评分按共同架构 §5 检查相容性。其他已定义的局部函数可以形成新的绑定，其传播与数值性质按相应条件判断。

### 1.2 KV 的位置、窗口与衰减

对区域 $\ell$ 中的节点固定

$$
\operatorname{Pos}_{v_{\ell,s}}(\theta)=\frac{\theta-\ell}{D}.
$$

于是当前查询位置为 $\operatorname{Pos}_{v_{\ell,s}}(Dt+\ell)=t$，在输入位置 $t'$ 写入的 key 位置为 $t'$。局部 RoPE 自动成为按输入位置定义的 RoPE；稀疏写入仍使用原始位置，有空档时保留相应距离。

KV 教材的窗口 $T_v$ 按逻辑时间计量。同节点在位置 $t'$ 写入的条目，到位置 $t$ 时可读，当且仅当

$$
0\le D(t-t')<T_v.
$$

有限窗口每次读取至多覆盖 $\lceil T_v/D\rceil$ 个输入位置。为区域 $\ell$ 选择 $H_\ell\in\mathbb N_{\ge1}\cup\{\infty\}$，令 $T_v=DH_\ell$。有限 $H_\ell$ 覆盖含当前位置的最近 $H_\ell$ 个位置，$H_\ell=\infty$ 保留全部接收历史。没有正接收的位置不写入；过期条目仍按原始时间遮罩读取。

若短期摘要按输入位置使用衰减率 $\bar\beta_{\ell,\mathrm{short}}>0$，则设 $\beta_{v,\mathrm{short}}=\bar\beta_{\ell,\mathrm{short}}/D$，得到 $e^{-\bar\beta_{\ell,\mathrm{short}}(t-t')}$。长期率为零。可选 Attention 距离偏置按 $\operatorname{Pos}$ 计算，斜率直接按输入位置声明。

改变深度时，$D$ 随之变化，按以上关系同步改变位置尺度、逻辑窗口和摘要衰减，即可保持相同的输入位置尺度。每条序列的后续分段继续使用该序列原有的 $t$ 与 $\theta$。

## 2. KV 基线与发送变式

本节给出 KV 基线的完整绑定。后续替换使用 §1.1 选定的图、时间与端口；各模块的函数定义由[共同架构](../local-semantics/weighted-message/architecture-learning-note.md)及相应教材给出。

### 2.1 函数、初态与来源类别

所有节点采用共同架构的 $P=X_v=\mathbb R^{1+d}$、区域共享 Agg、全部候选保留更新的 Next 和广播 Full。记忆取 KV 空缓存初态、时间摘要与其内容函数；描述读取取 $\tau_j=+$。区域使用单点历史、拼接独立评分、固定增益和约束二次分配，声明 $1\le k_j\le n$、阈值与正温度，正典容量为 $K_j=n$。宽度、矩阵、偏置、共享关系与残差尺度按各定义给定有限值，位置参数见 §1.2 与 §2.3。

各区域可替换相容的记忆、评分或发送函数。替换时按共同架构 §5 检查类型，按区域分配教材 §2.8 绑定容量；具体配置名见附录 S。

来源类别按区域定义。第一层只使用入口类别 $\mathrm{in}$，令 $\operatorname{SrcClass}_{v_{1,s}}(\mathrm{ext},i_s)=\mathrm{in}$。对 $\ell>1$，类别为上一层节点身份，令

$$
\operatorname{SrcClass}_{v_{\ell,r}}(\mathrm{msg},a_{\ell-1,s,r})
=v_{\ell-1,s}.
$$

同一父节点通向不同接收者的消息因此具有相同类别；原始原子仍保留各自的边身份与时间。区域内共享聚合参数和 KV 基座，各节点分别具有适配器、摘要、评分与 Full 参数，私有状态分别保存。

### 2.2 输入与连续读出

设 $h_t\in\mathbb R^d$ 是只依赖输入前缀的表示序列。全部输入端口在位置 $t$ 接收相同单位强度载荷：

$$
x_{i_s}(t)=(1,h_t),\qquad 1\le s\le n.
\tag{1}
$$

完整输出记录记为 $Z$。采用局部架构教材 §4 的同一个 $\operatorname{ReadOut}$，固定

$$
\begin{aligned}
\Lambda_t&=\{(Dt+L,o_s):1\le s\le n\},\\
O_t&=\operatorname{ReadOut}_{\Lambda_t}(Z),\\
y_t&=h_t+\alpha_{\mathrm{out}}W_{\mathrm{out}}O_t,
\qquad W_{\mathrm{out}}\in\mathbb R^{d\times d},\quad
\alpha_{\mathrm{out}}\ge0.
\end{aligned}
\tag{2}
$$

终端端口记录的时间为 $Dt+L$。在 $Dt+L+1$ 比较这组已经确定的槽，取得图外读出 $O_t$；该读出不产生新的图内作用或输出记录。通用 ReadOut 在全部终端缺席时定义为零；本实例的单位输入与非空选择保证每位置都有正强度终端输出，证明见 §2.4。内容相消仍可能使数值 $O_t=0$。

若采用 SettleGraph §6.4 的派生单槽记法，可在 $Z_{\Lambda_t}$ 非空时令 $b_t=(1,O_t)$，为空时令 $b_t=\bot$，并取 $\pi_{\mathrm{out}}(1,z)=z,\pi_{\mathrm{out}}(\bot)=0$。这个派生读出由端口记录确定。

式 (2) 可以接入已有因果主干。独立语言模型可令 $h_t$ 为 token 嵌入，以 $y_t$ 接任务读出。由位置顺序与私有状态递归，$y_t$ 只依赖截至位置 $t$ 的输入。

### 2.3 逐区域的记忆与位置配置

在本实例中，每个区域选择同一套记忆和位置参数，区域间允许不同。窗口覆盖、位置坐标与位置变换分别指定：

| 配置项 | 区域 $\ell$ 的数学绑定 |
|---|---|
| 记忆范围 | $H_\ell$，各节点取 $T_v=DH_\ell$ |
| 位置坐标 | $o_v^{\mathrm{pos}}=\ell,s_v^{\mathrm{pos}}=D$，故 $\operatorname{Pos}_v(Dt+\ell)=t$ |
| Full 旋转范围 | 各头取偶数 $d^{\mathrm{rot}}_\ell\le d_h$；零、全部、部分分别对应 NoPE、完整和部分 RoPE |
| 旋转频率 | 对 $d^{\mathrm{rot}}_\ell>0$，可取 $\omega^{\mathrm{rot}}_{v,h,a}=b_\ell^{-2(a-1)/d^{\mathrm{rot}}_\ell}$，$b_\ell>1$，$1\le a\le d^{\mathrm{rot}}_\ell/2$ |
| Read 检索位置 | 采用内容检索时，独立声明其旋转维数和频率，仍使用相同 $\operatorname{Pos}_v$；时间摘要无需检索旋转 |
| 摘要衰减 | $\beta_{v,\mathrm{short}}=\bar\beta_{\ell,\mathrm{short}}/D$，$\beta_{v,\mathrm{long}}=0$ |
| 距离偏置 | 基线取 $b^{\mathrm{pos}}_{v,h}=0$ |

以下给出两个可直接代入的配置形状。共同取 $L=8$、$n=4$、$d=512$、$H_{\mathrm{att}}=8$、$d_h=64$、$k_\ell=1$，有旋转时取 $b_\ell=10^4$；其余参数使用同一份声明。

| 配置 | 区域 | $H_\ell$ | $d^{\mathrm{rot}}_\ell$ | 意义 |
|---|---|---|---|---|
| A：全历史 RoPE | $1,\ldots,8$ | $\infty$ | $64$ | 在全部接收历史上使用完整 RoPE |
| B：窗口 RoPE 与全历史 NoPE | $1,2,3,5,6,7$ | $512$ | $64$ | 近期 KV 与完整 RoPE |
| B：窗口 RoPE 与全历史 NoPE | $4,8$ | $\infty$ | $0$ | 全历史 KV 与内容匹配 |

将某区域的 $64$ 改为 $32$ 即得部分 RoPE 变式。全历史始终指该节点接收并保存的聚合历史；上游稀疏选择仍决定哪些信息进入该历史。配置 B 在区域间组合不同的记忆范围与位置函数。

各区域采用不同位置机制仍使用同一个载荷空间。本文的两个配置均使用 KV。循环与 KV 的异构组合见第 3 节。

### 2.4 每层的接收、写入与输出

在每个输入位置 $t$，所有层的全部节点都会收到正强度消息。第一层接收强度为 $1$，故 $w=\mu=1$。若某层全体节点有 $\mu=1$，则约束软选择的发送强度之和在 $[1,k_j]$ 内，直接 Attention、固定总强度 Attention 和 pooled 的总和均为 $1$，dense 的总和为 $\min(k_j,n)\ge1$，硬选择激活 $1$ 至 $k_j$ 个节点并各自产生单位强度载荷。每个下一层节点收到全部激活者的广播，接收强度至少为 $1$，于是仍有 $w=\mu=1$。逐层归纳即可到达终端。

因此同层节点的接收强度、写入权重、发送上限和写入时间相同。在位置 $t$ 的接收更新之后，有限窗口的缓存长度均为 $\min(t+1,H_\ell)$，全历史缓存长度为 $t+1$。区域共享 Agg 的基线还具有相同的聚合内容；KV 仍可因节点的适配器和私有投影不同而分化。采用节点独立聚合时，聚合内容也可不同。激活选择不改变本层的写入次数。

这些结论也覆盖上下文增益：由于接收强度始终至少为 $1$，$\mu=1$ 已由上界截断确定，增益网络不会改变本实例的前向结果。

采用约束软选择或硬选择的层取 $k_j=1$ 时，该层每位置的发送强度之和恒为 $1$，共同阈值 $\eta_j$ 不影响选择。温度与评分差异决定约束软选择的激活集合，硬选择在该层恰激活一个节点。直接 Attention 与固定总强度 Attention 在本实例中始终发送总强度 $1$。

### 2.5 固定尺度的稠密 Attention 组合

每区域使用区域 Attention 评分，取 $\alpha_j^{\mathrm{loc}}=0,\alpha_j^{\mathrm{sel}}=1$，固定正温度。记忆、聚合与位置保持 §2.1—2.3 的绑定。由 §2.4，各次 $w_v=\mu_v=1$。直接 Attention、固定总强度 Attention、区域总量后分份额，以及 $k_j=1$ 的约束 Shannon，均给出

$$
c_v=\frac{e^{s_v/\tau_{\mathrm{soft}}}}{\sum_{u\in\mathcal R_j}e^{s_u/\tau_{\mathrm{soft}}}}.
$$

这些组合具有相同的前向和评分导数；两种 query 权重也相同。固定评分而独立改变 $\mu$ 时，各函数的导数仍按自己的定义计算。评分无关的稠密分配则直接均分。

每层全部 $n$ 个节点执行 Full，发送强度是区域 query 对节点 keys 的 Attention 权重，总和为 $1$。正典容量取 $K_j=n$。各节点继续保存自己的 KV；广播之后，下一层每个节点收到全部父节点的加权内容。本组合的训练与推理可以始终保持同一正温度。

这些设置可用于全部区域，也可只用于其中部分区域；其余区域采用已定义的其他选择函数。各组合的接收与写入继续满足 §2.4，Full 和消息工作按 §5.2 计数。

## 3. KV 与循环记忆的组合

保持 §1.1 选定的图、时间和 §2.2 的入口、输出。在 §2.3 的八层形状中，可令区域 $4,8$ 使用 [delta 模块](../local-semantics/weighted-message/recurrent-memory-learning-note.md)，其余区域使用配置 B 的 KV；也可将这两个区域取为 affine。替换区域采用循环教材的状态空间、零初态、Upd、Mem、当前特征和完整内容函数 $G_v$，取 $d_k=d_m=64,d_s=32$、memory_read=state、Read$^+$，短期衰减率按 $\lambda_{\mathrm{short}}=\bar\lambda_{\mathrm{short}}/D$ 换算，长期率为零。循环区域不使用 KV 的窗口和位置旋转。

各区域的聚合、评分与发送继续按共同接口绑定；匹配宽度、增益界和相应矩阵全部声明。第 2.4 节的单位接收归纳只依赖发送规则，继续成立；同层 KV 长度的结论只用于保留 KV 的区域。循环区域以固定大小矩阵保存有效状态。

联合求值分别使用 KV 前缀与循环仿射复合，按层取得完整驱动输入，故仍可应用第 5.1 节的整窗口策略。位置边界保存各自完整状态；消息宽度和读出相同，组合是合法 SettleGraph。数值性质按共同架构 §6 应用，两种记忆分别提供局部引理。

## 4. 组合成立的条件

| 对象或性质 | 本实例的绑定与依据 |
|---|---|
| 承载值与本地内容 | $P=X_v=\mathbb R^{1+d}$；图传递共同架构定义的带强度载荷 |
| 区域容量 | 使用 $k_j$ 时满足 $1\le k_j\le n$；除硬选择外的各函数取 $K_j=n$，硬选择取 $K_j=k_j$ |
| 来源与共享 | §2.1 覆盖全部输入端口和入边；聚合绑定、描述空间及成对的 Read／SelStep 按共同架构与区域分配教材给定 |
| 单次结算 | [拓扑的时间定义](../topologies/fully-connected-layered.md#2-输入位置与处理时间)满足 SettleGraph 条件 |
| 状态与时间 | 各模块初态、单点区域历史；KV 窗口和循环衰减按逻辑时间，KV 位置按 §1.2 换算 |
| 区域记忆配置 | KV 使用 §2.3 的窗口与位置，循环使用 §3 的状态与衰减；继续保持各自配置 |
| 输出比较 | §2.2 声明有限槽集合和连续数值读出，缺席组读出零 |
| 正温度连续性 | 各区域使用约束分配、direct、pooled 或 dense 时，按共同架构 §6.2 的条件使用，各记忆模块验证其状态假设 |
| 非空传播 | §2.4 保证每层全体节点接收并写入，每位置有正强度终端输出 |
| 硬化连续性 | 按共同架构 §6.3 比较约束分配与配对硬选择，核对对应硬运行的评分条件 |

给定上述配置即可直接应用共同的 P/S/U/F 递归。硬化所需的评分间隔取决于参数与输入，须在所考察硬运行上核对。拓扑允许相同局部函数在不同尺寸下组合，各性质按自己的前提使用。

## 5. 整窗口求值与架构成本

### 5.1 从局部契约到整段求值

给定目标窗口的完整驱动纤维，KV 教材 §6 的前缀与读取构造、循环教材 §4 的仿射复合分别提供精确的 BatchRegionState 与逐节点 BatchFull。每个区域使用自己所选模块的契约。

取 $0\le p\le q\le N$，输入位置区间 $[p,q)$ 对应逻辑时间窗口 $I=[Dp,Dq)$。给定其完整端口输入及左切面，第一层的窗口纤维已确定；其状态块给出全部快照和选择，逐节点 Full 批给出发往第二层的全部消息。依次沿区域顺序处理，就能为下一层提供完整窗口纤维。局部写入不依赖本节点选择或 Full，区域内部也没有消息边，因此可以直接应用 [分块教材 §6](../timed-dag-chunk-prefill-learning-note.md#6-严格分层区域的整块定理)。

所得策略每区域至多使用一个状态块，每节点至多使用一个额外 Full 时间批。这个结论计量外层调用；块内的写入、描述与完整内容计算仍随窗口长度增长。KV 的 query 和 key 分别使用原始处理时间与写入时间，循环状态使用原始逻辑时钟；各自的联合算法保持这些时间与快照。

从输入位置 $q$ 继续时，保留 $Q_{Dq}$ 及原有时间编码，下一位置仍为 $q$。任意连续分块与逐位置求值均能恢复同一记录与边界状态；全历史 KV 区域保留完整接收历史，有限窗口 KV 保留可恢复的窗口状态；循环区域保存矩阵、摘要和时间戳。位于位置内部的一般切面同样可以继续，边界须包含跨界消息。计算表示与解码分别见所选记忆教材。

### 5.2 共享计算与宽度成本

相邻层全连接与广播 Full 使同一区域的节点面对相同上游载荷；§2.1 的来源绑定使其类别也一致。在区域共享 Agg 的 KV 基线中，区域聚合与共享 KV 基座投影可各计算一次，各节点仍分别保存 KV，计算适配器、记忆描述、评分及被选择的 Full。循环区域可复用相同的聚合，其状态投影与更新按循环模块计算。采用节点独立或不同的来源适配时，须重新判断哪些中间量相同。

硬运行每个输入位置满足

$$
\begin{aligned}
L\le\#\mathrm{Full}&\le\sum_{j=1}^{L}k_j,\\
\#\mathrm{candidate}&=Ln,\\
n(L-1)\le\#\mathrm{internal\ message}&\le n\sum_{j=1}^{L-1}k_j.
\end{aligned}
\tag{3}
$$

§2.4 保证每层都有正强度发送，下一层全部 $n$ 个节点始终成为候选并写入。区域宽度增加时，准备、状态与消息成本仍可能增长。工作分类见共同架构附录 S.2，具体状态与算术成本按所选记忆模块计算；KV 窗口按 §1.2 换算，循环状态大小由矩阵宽度确定。

若全部区域采用固定总强度 Attention、直接 Attention、pooled、dense、bern 或 ent 的 $\alpha=1$，正温度下每位置有 $Ln$ 次 Full 和 $(L-1)n^2$ 条内部消息。其他软正则按实际激活数量计数；全部区域使用硬选择时满足式 (3)。两种局部评分及内容检索的准备成本另计，不能由发送强度之和推算。

整段求值使用各模块的精确联合算法；逐位置继续仍承担候选准备、记忆读取和消息工作。本实例减少激活时可减少 Full 和消息条数，各层候选与写入次数保持不变。

## 附录 S：配置对应

基线使用 memory_family=kv、memory_read=sum、read_mode=+、local_score=cat、region_score=ind、send_gain=fixed、selection_mode=soft、budget_family=quad。所有节点的初态、来源与矩阵形状由第 2 节确定；位置绑定对应 KV 教材的 Pos、窗口与旋转配置。

第 2.5 节使用 region_score=att、alpha_loc=0、alpha_sel=1 和固定 tau_soft。四种等值发送分别取 direct、attention、pooled，以及 soft／ent／ent_alpha=1／k=1。第 3 节替换区域的 memory_family 和 memory_read，其余沿用所选组合。完整取值与生效范围统一见[区域分配附录 S.1](../local-semantics/weighted-message/region-allocation-learning-note.md#s1-配置名称)。

实现核对见[局部架构实现对应](../reference/weighted-message-implementation-checks.md)，任务与训练比较见[可选研究问题](../memos/training/weighted-message-research-questions.md)。
