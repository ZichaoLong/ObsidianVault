---
type: mathematical-architecture-example
status: active
cssclasses:
  - textbook-math
tags:
  - tide
  - mathematics
  - semantic-anchor
  - architecture
  - weighted-kv
---

# 带权 KV 的全连接分层实例

本文将 [[weighted-kv-sparse-activation-example|带权 KV 的局部计算与区域选择]] 与相邻层全连接、按输入位置对齐的结构组合。局部教材给出计算函数、连续性条件和联合求值见证；本文固定图、时间、位置、来源与输出绑定，并给出逐区域的记忆配置、因果读出及架构成本。

本文提供相邻层全连接、每层一个区域的基线；[[weighted-kv-hb-lattice-example|HB-Lattice 实例]] 给出多区域及稀疏邻域的另一种组合。

阅读需掌握 [[settlegraph-learning-note|SettleGraph]] 的单次结算与上述局部函数。各尺寸和数值参数取自声明的配置；给定配置、输入和初态以后，全部前向值唯一确定。

## 1. 分层拓扑与时间

### 1.1 节点、区域与消息边

取正整数深度 $L$、区域宽度 $n$，定义

$$
\begin{aligned}
J&=\{1,\ldots,L\},\\
V&=\{v_{\ell,s}:1\le\ell\le L,\ 1\le s\le n\},\\
\rho(v_{\ell,s})&=\ell,\qquad
\mathcal R_\ell=\{v_{\ell,1},\ldots,v_{\ell,n}\}.
\end{aligned}
\tag{1}
$$

对 $1\le\ell<L$ 和 $1\le s,r\le n$，设边 $a_{\ell,s,r}$ 从 $v_{\ell,s}$ 指向 $v_{\ell+1,r}$，时延为 $1$。这些边组成全部消息边。固定按 $(\ell,s)$ 字典序排列的节点全序，用于选择平票。$L=1$ 时消息边集为空。

每个第一层节点具有输入端口 $i_s$，每个最后一层节点具有输出端口 $o_s$：

$$
\mathsf I=\{i_1,\ldots,i_n\},\quad
\mathsf O=\{o_1,\ldots,o_n\},\qquad
\gamma(i_s)=v_{1,s},\quad \varepsilon(o_s)=v_{L,s}.
$$

### 1.2 输入位置与处理时间

固定输入长度 $N\ge1$，位置范围为 $[N]=\{0,\ldots,N-1\}$。第 $\ell$ 个区域的秩为 $\ell$，令 $D=L+2$，并定义

$$
\theta_{v_{\ell,s},t}=Dt+\ell,\qquad
\iota_{i_s}(t)=Dt+1,\qquad t\in[N].
\tag{2}
$$

相邻层消息在 $Dt+\ell+1$ 到达，恰为下一层的处理时间。严格区域秩、边时延与端口日程满足 SettleGraph 的合法时间编码，每节点每位置至多处理一次。各位置的图内作用均落在 $[Dt,D(t+1))$，位置边界没有跨界消息。

### 1.3 位置坐标、窗口与衰减

对区域 $\ell$ 中的节点固定

$$
\operatorname{Pos}_{v_{\ell,s}}(\theta)=\frac{\theta-\ell}{D}.
$$

于是当前查询位置为 $\operatorname{Pos}_{v_{\ell,s}}(Dt+\ell)=t$，在输入位置 $t'$ 写入的 key 位置为 $t'$。局部 RoPE 自动成为按输入位置定义的 RoPE；稀疏写入仍使用原始位置，有空档时保留相应距离。

局部教材的窗口 $T_v$ 按逻辑时间计量。同节点在位置 $t'$ 写入的条目，到位置 $t$ 时可读，当且仅当

$$
0\le D(t-t')<T_v.
$$

有限窗口每次读取至多覆盖 $\lceil T_v/D\rceil$ 个输入位置。为区域 $\ell$ 选择 $H_\ell\in\mathbb N_{\ge1}\cup\{\infty\}$，令 $T_v=DH_\ell$。有限 $H_\ell$ 覆盖含当前位置的最近 $H_\ell$ 个位置，$H_\ell=\infty$ 保留全部接收历史。没有正接收的位置不写入；过期条目仍按原始时间遮罩读取。

若短期摘要按输入位置使用衰减率 $\bar\beta_{\ell,\mathrm{short}}>0$，则设 $\beta_{v,\mathrm{short}}=\bar\beta_{\ell,\mathrm{short}}/D$，得到 $e^{-\bar\beta_{\ell,\mathrm{short}}(t-t')}$。长期率为零。可选 Attention 距离偏置按 $\operatorname{Pos}$ 计算，斜率直接按输入位置声明。

改变深度时，$D$ 随之变化，按以上关系同步改变位置尺度、逻辑窗口和摘要衰减，即可保持相同的输入位置尺度。每条序列的后续分段继续使用该序列原有的 $t$ 与 $\theta$。

## 2. 局部函数与边界绑定

### 2.1 函数、初态与来源类别

所有节点和区域采用 [局部教材 §10.1—10.2](weighted-kv-sparse-activation-example.md#101-函数与参数对应) 的空间、函数及参数次序，包括空缓存初态、单点选择历史、$\tau_j=+$、$\kappa_j=1$、默认 Next，以及 $\operatorname{Full}_v=\Delta_v\circ\operatorname{EmitValue}_v$。约束软选择与硬选择声明整数 $1\le k_j\le n$，分别限制发送强度之和与激活数量；直接 Attention 与固定总强度 Attention 分别按局部教材 §7.9、§7.10 发送。各正温度选择取 $K_j=n$，硬选择取 $K_j=k_j$；这些函数均在有效候选非空时至少激活一个节点。

基线绑定区域共享 Agg、时间摘要 $\mathfrak m_j=\mathrm{sum}$、拼接局部评分 $\mathfrak f_j=\mathrm{cat}$、独立区域评分 $\mathfrak s_j=\mathrm{ind}$、固定增益 $\mathfrak g_j=\mathrm{fixed}$ 与二次正则 $\mathfrak b_j=\mathrm{quad}$。其他组合逐区域选择局部教材已定义的其他取值。发送规则的共同性质见[局部教材 §7.11](weighted-kv-sparse-activation-example.md#711-发送规则的比较)，配置键沿用其附录 S.2；Read 的描述空间与 SelStep 按区域评分成对绑定。

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
\tag{3}
$$

完整输出记录记为 $Z$。采用局部教材 §5.4 的同一个 $\operatorname{ReadOut}$，固定

$$
\begin{aligned}
\Lambda_t&=\{(Dt+L,o_s):1\le s\le n\},\\
O_t&=\operatorname{ReadOut}_{\Lambda_t}(Z),\\
y_t&=h_t+\alpha_{\mathrm{out}}W_{\mathrm{out}}O_t,
\qquad W_{\mathrm{out}}\in\mathbb R^{d\times d},\quad
\alpha_{\mathrm{out}}\ge0.
\end{aligned}
\tag{4}
$$

终端端口记录的时间为 $Dt+L$。在 $Dt+L+1$ 比较这组已经确定的槽，取得图外读出 $O_t$；该读出不产生新的图内作用或输出记录。通用 ReadOut 在全部终端缺席时定义为零；本实例的单位输入与非空选择保证每位置都有正强度终端输出，证明见 §2.4。内容相消仍可能使数值 $O_t=0$。

若采用 SettleGraph §6.4 的派生单槽记法，可在 $Z_{\Lambda_t}$ 非空时令 $b_t=(1,O_t)$，为空时令 $b_t=\bot$，并取 $\pi_{\mathrm{out}}(1,z)=z,\pi_{\mathrm{out}}(\bot)=0$。这个派生读出由端口记录确定。

式 (4) 可以接入已有因果主干。独立语言模型可令 $h_t$ 为 token 嵌入，以 $y_t$ 接任务读出。由位置顺序与私有状态递归，$y_t$ 只依赖截至位置 $t$ 的输入。

### 2.3 逐区域的记忆与位置配置

在本实例中，每个区域选择同一套记忆和位置参数，区域间允许不同。窗口覆盖、位置坐标与位置变换分别指定：

| 配置项 | 区域 $\ell$ 的数学绑定 |
|---|---|
| 局部函数族 | 各区域采用带权 KV；基线为共享 Agg、时间摘要与独立评分，其他组合按局部教材 §10.1—10.2 成对绑定 |
| 局部评分与区域评分 | local_score 为 cat／match，region_score 为 ind／att，两项独立选择 |
| 发送增益 | send_gain 为 fixed／context，绑定有限 gamma_max 及相应参数 |
| 预算正则 | soft 使用 budget_family 为 quad／bern／ent；ent 另声明 ent_alpha $\in[1,2]$，共享相同总和上下限 |
| 选择函数 | selection_mode 为 soft／direct／attention／hard；attention 另取 attention_base 为 uniform／reception；参数生效范围见局部教材附录 S.2 |
| 记忆范围 | $H_\ell$，各节点取 $T_v=DH_\ell$ |
| 位置坐标 | $o_v^{\mathrm{pos}}=\ell,s_v^{\mathrm{pos}}=D$，故 $\operatorname{Pos}_v(Dt+\ell)=t$ |
| Full 旋转范围 | 各头取偶数 $d^{\mathrm{rot}}_\ell\le d_h$；零、全部、部分分别对应 NoPE、完整和部分 RoPE |
| 旋转频率 | 对 $d^{\mathrm{rot}}_\ell>0$，可取 $\omega^{\mathrm{rot}}_{v,h,a}=b_\ell^{-2(a-1)/d^{\mathrm{rot}}_\ell}$，$b_\ell>1$，$1\le a\le d^{\mathrm{rot}}_\ell/2$ |
| Read 检索位置 | 采用内容检索时，独立声明其旋转维数和频率，仍使用相同 $\operatorname{Pos}_v$；时间摘要无需检索旋转 |
| 摘要衰减 | $\beta_{v,\mathrm{short}}=\bar\beta_{\ell,\mathrm{short}}/D$，$\beta_{v,\mathrm{long}}=0$ |
| 距离偏置 | 基线取 $b^{\mathrm{pos}}_{v,h}=0$ |
| 其余局部参数 | 宽度、投影、残差、评分、$\gamma_v,k_\ell,\eta_\ell$ 及选择函数按局部教材完整声明 |

以下给出两个可直接代入的配置形状。共同取 $L=8$、$n=4$、$d=512$、$H_{\mathrm{att}}=8$、$d_h=64$、$k_\ell=1$，有旋转时取 $b_\ell=10^4$；其余参数使用同一份声明。

| 配置 | 区域 | $H_\ell$ | $d^{\mathrm{rot}}_\ell$ | 意义 |
|---|---|---|---|---|
| A：全历史 RoPE | $1,\ldots,8$ | $\infty$ | $64$ | 在全部接收历史上使用完整 RoPE |
| B：窗口 RoPE 与全历史 NoPE | $1,2,3,5,6,7$ | $512$ | $64$ | 近期 KV 与完整 RoPE |
| B：窗口 RoPE 与全历史 NoPE | $4,8$ | $\infty$ | $0$ | 全历史 KV 与内容匹配 |

将某区域的 $64$ 改为 $32$ 即得部分 RoPE 变式。全历史始终指该节点接收并保存的聚合历史；上游稀疏选择仍决定哪些信息进入该历史。配置 B 在区域间组合不同的记忆范围与位置函数。

各区域采用不同位置机制仍使用同一个载荷空间。进一步将某些区域替换为循环记忆时，须先给出该局部函数族的状态、更新、读取、Full 及连续性条件，再检查区域选择与跨区域载荷的相容性。本文的两个配置均由已经定义的 KV 函数构成。

### 2.4 每层的接收、写入与输出

在每个输入位置 $t$，所有层的全部节点都会收到正强度消息。第一层接收强度为 $1$，故 $w=\mu=1$。若某层全体节点有 $\mu=1$，则约束软选择的发送强度之和在 $[1,k_j]$ 内，直接 Attention 与固定总强度 Attention 的总和均为 $1$，硬选择激活 $1$ 至 $k_j$ 个节点并各自产生单位强度载荷。每个下一层节点收到全部激活者的广播，接收强度至少为 $1$，于是仍有 $w=\mu=1$。逐层归纳即可到达终端。

因此同层节点的接收强度、写入权重、发送上限和写入时间相同。在位置 $t$ 的接收更新之后，有限窗口的缓存长度均为 $\min(t+1,H_\ell)$，全历史缓存长度为 $t+1$。KV 内容可因各节点的聚合、适配器和投影不同而分化；激活选择不改变本层的写入次数。

这些结论也覆盖上下文增益：由于接收强度始终至少为 $1$，$\mu=1$ 已由上界截断确定，增益网络不会改变本实例的前向结果。

采用约束软选择或硬选择的层取 $k_j=1$ 时，该层每位置的发送强度之和恒为 $1$，共同阈值 $\eta_j$ 不影响选择。温度与评分差异决定约束软选择的激活集合，硬选择在该层恰激活一个节点。直接 Attention 与固定总强度 Attention 在本实例中始终发送总强度 $1$。

### 2.5 固定尺度的稠密 Attention 组合

每区域取 region_score=att、alpha_loc=0、alpha_sel=1，并固定 tau_soft，例如取 $1$。记忆、聚合与位置仍按 §2.1—2.3 绑定。发送规则可取：

| 规则 | 配置与定义 |
|---|---|
| 固定总强度 Attention | selection_mode=attention、attention_base=uniform 或 reception，采用局部教材 §7.10 |
| 直接 Attention | selection_mode=direct，采用[局部教材 §7.9](weighted-kv-sparse-activation-example.md#79-直接-attention-发送) |
| 约束 Shannon | selection_mode=soft、budget_family=ent、ent_alpha=1、k=1，采用局部教材 §7.8 |

由 §2.4，每次选择均有 $\mu_v=1$，上表全部配置直接得到普通 softmax，具有相同前向和评分导数。固定评分而独立改变 $\mu$ 时，各函数的导数仍按其自身定义计算。

每层全部 $n$ 个节点执行 Full，发送强度是区域 query 对节点 keys 的 Attention 权重，总和为 $1$。正典容量取 $K_j=n$。各节点继续保存自己的 KV；广播之后，下一层每个节点收到全部父节点的加权内容。本组合的训练与推理可以始终保持同一正温度。

这些设置可用于全部区域，也可只用于其中部分区域；其余区域采用已定义的其他选择函数。各组合的接收与写入继续满足 §2.4，Full 和消息工作按 §4.2 计数。

## 3. 组合成立的条件

| 对象或性质 | 本实例的绑定与依据 |
|---|---|
| 承载值与本地内容 | $P=X_v=\mathbb R^{1+d}$；图传递局部教材定义的带强度载荷 |
| 区域容量 | 使用 $k_j$ 时满足 $1\le k_j\le n$；各正温度选择取 $K_j=n$，硬选择取 $K_j=k_j$ |
| 来源与共享 | §2.1 覆盖全部输入端口和入边；聚合绑定、描述空间及成对的 Read／SelStep 按局部教材给定 |
| 单次结算 | §1 的严格分层、正时延与注入日程满足 SettleGraph 条件 |
| 状态与时间 | 空初态、单点历史；窗口与摘要衰减按逻辑时间，位置函数按 §1.3 恢复输入位置 |
| 区域位置配置 | §2.3 固定每区域的窗口、坐标、旋转维数与频率；分段继续保持同一配置 |
| 输出比较 | §2.2 声明有限槽集合和连续数值读出，缺席组读出零 |
| 正温度连续性 | 各区域使用约束软选择或 direct 时，按局部教材 §9.5 的固定配置、有界输入及有限切面条件使用 |
| 非空传播 | §2.4 保证每层全体节点接收并写入，每位置有正强度终端输出 |
| 硬化连续性 | 比较各区域均用局部教材式 (12) 的软运行与均用式 (14) 的硬运行；单位输入给出二元硬上限，评分条件按局部教材 §9.7 核对 |

给定上述配置即可直接应用共同的 P/S/U/F 递归。硬化所需的评分间隔取决于参数与输入，须在所考察硬运行上核对。拓扑允许相同局部函数在不同尺寸下组合，各性质按自己的前提使用。

<a id="5-整窗口求值与架构成本"></a>

## 4. 整窗口求值与架构成本

### 4.1 从局部契约到整段求值

局部教材 §10.3—10.4 构造 $\operatorname{BatchRegionState}^{\mathrm{KV}}_{j,I}$ 与 $\operatorname{BatchFull}^{\mathrm{KV}}_{v,\Theta}$，前提是目标窗口的完整驱动纤维已经给定。

取 $0\le p\le q\le N$，输入位置区间 $[p,q)$ 对应逻辑时间窗口 $I=[Dp,Dq)$。给定其完整端口输入及左切面，第一层的窗口纤维已确定；其状态块给出全部快照和选择，逐节点 Full 批给出发往第二层的全部消息。依次沿区域顺序处理，就能为下一层提供完整窗口纤维。局部写入不依赖本节点选择或 Full，区域内部也没有消息边，因此可以直接应用 [分块教材 §6](timed-dag-chunk-prefill-learning-note.md#6-严格分层区域的整块定理)。

所得策略每区域至多使用一个状态块，每节点至多使用一个额外 Full 时间批。这个结论计量外层调用；块内投影、摘要和 Attention 的工作仍随窗口长度增长。每个 query 使用原始处理时间，每个 key 使用原始写入时间，因此各区域的 NoPE 或 RoPE 配置直接沿用局部教材 §10.3—10.4 的联合求值见证。

从输入位置 $q$ 继续时，保留 $Q_{Dq}$ 及原有时间编码，下一位置仍为 $q$。任意连续分块与逐位置求值均能恢复同一记录与边界状态；全历史区域需保留其完整接收历史，有限窗口区域按既定规则保留可恢复的状态。位于位置内部的一般切面同样可以继续，边界须包含跨界消息。计算表示与解码见局部教材附录 S。

### 4.2 共享计算与宽度成本

相邻层全连接与广播 Full 使同一区域的节点面对相同上游载荷；§2.1 的来源绑定使其类别也一致。在区域共享 Agg 的基线中，区域聚合与共享 KV 基座投影可各计算一次，节点继续分别计算适配器、记忆描述、评分及被选择的 Full。采用节点独立或不同的来源适配时，须重新判断哪些中间量相同。不同节点保有自己的 KV 和参数。

硬运行每个输入位置满足

$$
\begin{aligned}
L\le\#\mathrm{Full}&\le\sum_{j=1}^{L}k_j,\\
\#\mathrm{candidate}&=Ln,\\
n(L-1)\le\#\mathrm{internal\ message}&\le n\sum_{j=1}^{L-1}k_j.
\end{aligned}
\tag{5}
$$

§2.4 保证每层都有正强度发送，下一层全部 $n$ 个节点始终成为候选并写入。区域宽度增加时，准备、缓存与消息成本仍可能增长。每节点的参数和运算量采用局部教材附录 S.4 的估计，缓存窗口按 §1.3 换算。

若全部区域采用固定总强度 Attention、直接 Attention、bern 或 ent 的 $\alpha=1$，正温度下每位置有 $Ln$ 次 Full 和 $(L-1)n^2$ 条内部消息。其他软正则按实际激活数量计数；全部区域使用硬选择时满足式 (5)。两种局部评分及内容检索的准备成本另计，不能由发送强度之和推算。

整段求值可以共同计算前缀投影、窗口摘要与查询；逐位置继续仍承担候选准备、KV 读取和消息工作。本实例减少激活时可减少 Full 和消息条数，各层候选与写入次数保持不变。

## 5. 配置的生效条件

| 配置与条件 | 数学结果 |
|---|---|
| 单位入口，采用本文任一选择函数或逐区域组合 | 每层逐节点 $w=\mu=1$，同层写入时刻相同 |
| fixed／context 增益 | 上界已为 $1$，改变增益不改变前向 |
| $k_j=1$ | 发送强度之和恒为 $1$，共同阈值无效 |
| §2.5 的稠密 Attention 配置 | 每层直接以 softmax 分配单位发送强度，全部 $n$ 个节点激活 |
| 区域共享 Agg，来源绑定如 §2.1 | 同层聚合内容相同，可复用共同投影；私有参数仍可产生不同 KV 和 Full |
| 同参数、同历史及同输入 | 对应局部数值相同；私有状态的名称本身不产生数值差异 |

模型使用与训练目标见 [训练实验与推进](memos/learning-systems/weighted-kv-experiment-plan.md)，具体程序与上述性质的对应见 [实现核对](weighted-kv-implementation-checks.md)。
