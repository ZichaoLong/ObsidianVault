---
type: mathematical-index
status: active
tags:
  - tide
  - mathematics
  - semantic-anchor
---

# 数学符号与函数对应索引

本页汇集四篇正典、带权 KV 局部教材及其组合实例的共同名称。相同名称使用相同数学类型；局部特化选择空间与函数，组合实例另给结构、时间与边界绑定。各定义的推导与证明由所列教材给出。

## 基础对象与时间

| 符号 | 含义 |
|---|---|
| $V,A,\operatorname{src},\operatorname{dst},\delta$ | 节点、独立消息边身份、端点与正整数时延 |
| $\mathsf I,\mathsf O,\gamma,\varepsilon$ | 输入／输出端口及其所属节点 |
| $J,\rho,\mathcal R_j$ | 区域标识、节点归属与区域成员 |
| $\theta,t,\iota_i(k)$ | 逻辑时间、输入位置、端口位置的注入时间 |
| $P,P_\bot$ | 消息承载值空间及增加缺席标记后的空间 |
| $\mathsf{Atom}_v,B_{v,\theta}$ | 可到达节点的带来源原子、完整时间纤维 |
| $\mathcal C_{j,\theta},\mathcal A_{j,\theta}$ | 候选集合、激活集合 |
| $S_v,X_v,D_v,\mathsf C_v,Y_j$ | 节点状态、本地内容、描述量、局部控制、选择历史空间 |
| $q,\widetilde q,q^{\mathrm{cmp}},q^{\mathrm{next}}$ | 旧状态、候选状态、计算快照、下一持久状态 |
| $\tau_j,\kappa_j,K_j$ | 描述模式、状态采用模式、激活数上界 |

SettleGraph 用 $\theta_{v,t}=Dt+r_v$ 与端口日程对齐；$q_v^{[t]}=q_v^{Dt}$、$y_j^{[t]}=y_j^{Dt}$ 是位置边界状态。其简写 $h_{v,t}$ 等均表示时间 $\theta_{v,t}$ 的同名坐标。一般图的状态上标 $\theta$ 始终为逻辑时间。

带权 KV 的 $K_j$ 是正典接口声明的激活数量上限。约束软选择与直接 Attention 取区域节点总数，硬选择取 $k_j$。$k_j$ 还用作约束软选择的发送强度总和上限，直接 Attention 不使用该参数。三种选择均在有效候选非空时至少激活一个；总和下限 $\min(1,\sum_v\mu_v)$ 属于约束软选择。选择温度 $\tau_{\mathrm{soft}}$ 与描述模式 $\tau_j$ 分别定义。记忆窗口 $T_v$ 和输入步长 $\Delta_{\mathrm{in}}$ 均按逻辑时间计量。

以下符号由 [KV 局部教材](weighted-kv-sparse-activation-example.md) 定义，在共同函数签名内部使用：

| 符号 | 局部含义 |
|---|---|
| $\mu_v,c_v$ | 每个候选的发送上限与本次发送强度；$c_v$ 对应正典控制量 |
| $Z_j^{\mathrm{sel}},p_v^{\mathrm{sel}}$ | 直接 Attention 的归一化总权重 $\sum_u\mu_u e^{s_u/\tau_{\mathrm{soft}}}$ 与归一化占比；$c_v=\mu_vp_v^{\mathrm{sel}}$，见局部教材 §7.9 |
| $Q_j^{\mathrm{sel}},K_v^{\mathrm{sel}},\alpha_j^{\mathrm{loc}},\alpha_j^{\mathrm{sel}}$ | 区域 query、节点 key、局部评分与区域匹配尺度；见局部教材 §7.6 |
| $\mathfrak m_j,\mathfrak f_j,\mathfrak s_j$ | 记忆描述 sum／qry、局部评分 cat／match、区域评分 ind／att |
| $\mathfrak g_j,\gamma_v^{\mathfrak g_j},\gamma_{\max}$ | fixed／context 增益、其数值及固定有限上界；$\mu_v(q,\theta,r,u)=\min(1,\gamma_v^{\mathfrak g_j}r_+)$ |
| $\mathfrak b_j,R^{\mathfrak b_j},\alpha_j^{\mathrm{ent}}$ | 正则族 quad／bern／ent、相应正则及 ent 的固定形状参数 |
| $C_{\mathrm{eff}},M_j,b_j$ | 有效候选集 $\{v:\mu_v>0\}$、发送上限之和 $\sum_v\mu_v$、约束软选择的发送强度总和下限 $\min(1,M_j)$ |
| $F(\mu),t_v,\lambda_U,\lambda_L$ | 约束软选择可行域、调整后评分 $s_v-\eta_j$、总和上下限乘子；响应使用 $\lambda=\lambda_U-\lambda_L$ |
| $\xi_i,T_v,\chi_{v,\theta}(\xi_i)$ | KV 条目的原始写入时间、有限或无限窗口、当前时间遮罩 |
| $\operatorname{Pos}_v(\theta)$ | 固定位置函数；仿射族为 $(\theta-o_v^{\mathrm{pos}})/s_v^{\mathrm{pos}}$ |
| $\operatorname{Rot}_{v,h}(p)$ | 对 Q/K 的指定坐标对施加位置旋转；旋转维数为零时取恒等 |
| $d^{\mathrm{rot}}_{v,h},\omega^{\mathrm{rot}}_{v,h,a}$ | 每头旋转维数及频率，与评分宽度 $d_r$ 分别定义 |
| $\beta_{v,a},b^{\mathrm{pos}}_{v,h}$ | 按逻辑时间的摘要衰减率、按位置坐标的可选距离偏置斜率 |
| $\pi_{\mathrm{KV},v,\theta}$ | 按原始时间槽对齐的有效加权状态投影 |

分层组合取 $o_v^{\mathrm{pos}}=r_v,s_v^{\mathrm{pos}}=D$，恢复输入位置 $t$。窗口和摘要衰减按 $T_v=DH_j$、$\beta_{v,a}=\bar\beta_{j,a}/D$ 换算。分段继续保留原始时间及同一位置配置。

两种稠密发送函数沿用 SelStep 接口：[局部教材 §7.8](weighted-kv-sparse-activation-example.md#78-保留发送约束的稠密选择) 保留约束 Shannon 选择，[§7.9](weighted-kv-sparse-activation-example.md#79-直接-attention-发送) 定义无求根的直接 Attention。导数及普通 softmax 的适用条件见 §8.5—8.6。

## 局部函数

类型定义见 [TimedDAG §4--5](timed-dag-region-selector-learning-note.md#4-节点的局部函数)、[SettleGraph §3--5](settlegraph-learning-note.md#3-来源原子与时间纤维) 与 [正时延图 §1](positive-delay-graph-finite-cut-learning-note.md#14-内部消息输出和局部函数)。

| 名称 | 定义域与值域 |
|---|---|
| $\operatorname{Agg}_v$ | $\mathbb N\times\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_v)\to X_v$ |
| $\operatorname{Upd}_v$ | $S_v\times\mathbb N\times X_v\to S_v$ |
| $\operatorname{Read}_v^0$ | $\mathbb N\times X_v\to D_v$ |
| $\operatorname{Read}_v^-,\operatorname{Read}_v^+$ | $S_v\times\mathbb N\times X_v\to D_v$ |
| $\operatorname{SelStep}_{j,C}$ | $Y_j\times\mathbb N\times\prod_{v\in C}D_v\to\mathsf{Allowed}_{j,C}\times\prod_{v\in C}\mathsf C_v\times Y_j$ |
| $\operatorname{Next}_v$ | $S_v\times S_v\times\mathbb N\times X_v\times\{0,1\}\times\mathsf C_v\to S_v$ |
| $\operatorname{Full}_v$ | $S_v\times\mathbb N\times X_v\times\mathsf C_v\to(P_\bot)^{\operatorname{Out}(v)}\times(P_\bot)^{\operatorname{OutPort}(v)}$ |

$\mathsf{Allowed}_{j,C}=\{A'\subseteq C:|A'|\le K_j\}$。空候选返回 $(\varnothing,(),y)$。Next 的调用为 $\operatorname{Next}_v(q,q^{\mathrm{cmp}},\theta,h,a,c)$；Full 的调用为 $\operatorname{Full}_v(q^{\mathrm{cmp}},\theta,h,c)$。

三层均保留上述类型。广播实例另选 $\operatorname{EmitValue}_v:S_v\times\mathbb N\times X_v\times\mathsf C_v\to P$，并取 $\operatorname{Full}_v=\Delta_v\circ\operatorname{EmitValue}_v$。[KV 局部教材 §10.1—10.2](weighted-kv-sparse-activation-example.md#101-函数与参数对应) 给出函数绑定；$\operatorname{ReadOut}_\Lambda$ 的数值定义见其 §5.4。Read 与 SelStep 按描述空间 $D_v$ 成对绑定；记忆、局部评分、增益和选择函数在该类型内部组合。其[附录 S.2](weighted-kv-sparse-activation-example.md#s2-配置与数学函数) 给出同名配置键，[附录 S.3](weighted-kv-sparse-activation-example.md#s3-软选择的求解与反向) 给出约束软选择的求解与反向，[附录 S.5](weighted-kv-sparse-activation-example.md#s5-直接-attention-的求值与反向) 给出直接 Attention 的求值与边界反向。[全连接实例](weighted-kv-layered-example.md#1-分层拓扑与时间) 与 [HB-Lattice 实例](weighted-kv-hb-lattice-example.md#1-拓扑区域与时间) 给出各自的图、日程、区域、来源映射和输出槽集合 $\Lambda_t$。

## 作用、结果与调用标签

定义见 [TimedDAG §6.4](timed-dag-region-selector-learning-note.md#64-节点事件区域选择事件与四类作用)。

| 作用坐标 | 规范结果 $\mathcal T_x^{\mathrm{act}}$ | 调用标签 |
|---|---|---|
| $P_{v,\theta}=(\mathrm{prep},v,\theta)$ | $(h,\widetilde q,d)$ | $\operatorname{Lab}_P=(B,q,h,\widetilde q,d)$ |
| $S_{j,\theta}=(\mathrm{select},j,\theta)$ | $(\mathcal A,(c_v)_{v\in\mathcal C},y')$ | $\operatorname{Lab}_S=(\mathcal C,y,(d_v)_{v\in\mathcal C},\mathcal A,(c_v)_{v\in\mathcal C},y')$ |
| $U_{v,\theta}=(\mathrm{adopt},v,\theta)$ | $(q^{\mathrm{cmp}},q^{\mathrm{next}})$ | 同规范结果 |
| $F_{v,\theta}=(\mathrm{full},v,\theta)$ | $(f^A,f^O)$ | 同规范结果 |

$\operatorname{res}_P,\operatorname{res}_S$ 取标签的结果三元组。Next 所需旧状态来自显式状态边界或完整 Lab_P，准备结果三元组一般不包含可恢复的旧状态。

事件图统一记为 $\mathscr G_x^{\mathrm{ev}}=(\mathscr V_x^{\mathrm{ev}},\mathscr A_x^{\mathrm{ev}})$；有限切面在各符号增加 $<b$ 限制。$\operatorname{own}$ 映射作用到节点或选择历史归属，用于静态依赖图；$\operatorname{cown}$ 映射联合契约到 $(\mathrm{node},v)$ 或 $(\mathrm{region},j)$。两者定义域不同，其归属值通过 $v\leftrightarrow(\mathrm{node},v)$、$s_j\leftrightarrow(\mathrm{region},j)$ 对应。

## 封闭、切面与区间

| 名称 | 数学含义 |
|---|---|
| $\operatorname{ValidSeal},\sigma^{\mathrm{in}},\sigma^A$ | 当前集合覆盖所有时间严格小于相应下界的输入／到达消息 |
| $\lambda(v),\lambda(\mathcal R_j)$ | 节点全部输入下界的最小值、区域成员前沿的最小值 |
| $\operatorname{DoneTo}(v,b)$ | 输入前缀关闭，时间小于 $b$ 的状态与完整输出作用完成 |
| $\operatorname{PublishedDoneTo}(v,b)$ | 进一步要求相应源消息全部纳入当前记录 |
| $M_{<b}^{\mathrm{send}}$ | 发送时间小于 $b$ 的消息；其中可含尚未到达的消息 |
| $W_b$ | $\operatorname{send}(m)<b\le\operatorname{time}(m)$ 的跨界消息 |
| $Q_b$ | $(b,(q_v^b)_v,(y_j^b)_j,W_b)$ |
| $\Phi_{a,b}$ | $(Q_a,E_{[a,b)})\mapsto(\mathcal U_{[a,b)},Q_b)$，定义在可达且相容的输入域 $\operatorname{Adm}_{a,b}$ |
| $\odot_b$ | 两段记录粘合；共享状态边界识别一次，新消息按发送区间归属 |

纤维关闭要求 $\lambda(v)>\theta$。Completed 只要求作用完成，PublishedDone 还要求消息齐备；PDG 的强部分截面与 TimedDAG 的细粒度暴露通过这些条件对应。

区间接口在 [TimedDAG §11.5](timed-dag-region-selector-learning-note.md#115-区间转导与记录粘合)、[分块 §8.1](timed-dag-chunk-prefill-learning-note.md#81-输入分块组合) 与 [PDG §7](positive-delay-graph-finite-cut-learning-note.md#7-区间转导与复合) 同义。关闭证据与数值输入分别给出。空区间记录只含共同边界状态，是粘合的单位元。

## 联合求值

定义见 [分块 §2--3](timed-dag-chunk-prefill-learning-note.md#2-作用块外部边界与精确联合求值) 与 [PDG §10.2](positive-delay-graph-finite-cut-learning-note.md#102-有限区间的联合求值契约)。

| 名称 | 数学含义 |
|---|---|
| $K,K(\omega)$ | 潜在作用范围、某次实例的实际作用支持 |
| $\mathsf{AdmIn}(K),\mathsf{BlockOut}(K)$ | 全部合法外部自变量、包含实际支持集的完整返回记录 |
| $\operatorname{RefBlock}_K$ | 该边界唯一确定的参考联合函数 |
| $\operatorname{ExpandFull}_{v,\Theta}$ | 将 Full 值族按作用、边与端口展开成规范记录 |
| $\operatorname{BatchFull}_{v,\Theta}$ | 已知 $(q^{\mathrm{cmp}},\theta,h,c)$ 族上的 Full 见证 |
| $\operatorname{BatchState}_{K^U_{v,\Theta}}=\operatorname{BatchState}_{v,\Theta}$ | 节点状态轨迹及范围中实际 $P/U$、允许的局部 $S$ |
| $\operatorname{BatchNode}_{K^{UF}_{v,\Theta}}=\operatorname{BatchNode}_{v,\Theta}$ | 节点状态与完整输出 |
| $\operatorname{BatchRegionState}_{K^R_{j,I}}=\operatorname{BatchRegionState}_{j,I}$ | 区域 $P/S/U$、状态与历史轨迹 |
| $\operatorname{BatchRegion}_{K^{RF}_{j,I}}=\operatorname{BatchRegion}_{j,I}$ | 区域 $P/S/U/F$ 及其消息与输出 |
| $\operatorname{Acts}(B,z)$ | 契约调用在边界 $z$ 上返回的实际作用支持 |
| $\Lambda_v^U(I;\cdot),\Lambda_v^F(I;\cdot)$ | 实际状态作用时间、实际完整输出时间 |
| $R,m_v^U,m_v^F,m_v^{UF},m_j^R$ | 自适应阶段数、各类节点批数与区域块数 |

各见证均满足 $\mathcal K(z)=\operatorname{RefBlock}_K(z)$，并遵守范围的进入依赖与关闭条件。范围包含未发生坐标时，返回的实际支持集明确给出缺席。区域状态与区域状态加输出契约都可属于成本种类 $R$，覆盖范围区分二者。

PDG 增加 Full 解释参数 $\mathbf F$，写作 $\operatorname{RefBlock}_K^{\mathbf F}$ 等；固定解释后省略上标。$\Lambda_v^F(I;\mathbf F,\omega)$ 的上标 $F$ 始终表示作用种类。PDG 的性能比较固定其余局部函数，属于分块教材共同规格族的特例。批数和阶段数同时依赖规格、输入、策略和契约族。

TimedDAG §10.7、§12.4 的 StatePath 只返回一般递归的状态轨迹；BatchState 返回完整规范块，其状态投影才是该轨迹。

## 附录：实现对应的验证关系

实现可沿用上述名称与参数次序。具体表示通过固定解码取得数学值，再通过遗忘投影取得规范记录：

$$
\text{实现表示}\xrightarrow{\operatorname{Decode}}
\text{数学值及辅助字段}\xrightarrow{\Pi}\text{规范记录}.
$$

Decode 忠实恢复所表示的原子、状态、控制和快照；Pi 只删除辅助坐标。两者都不调用参考递归来补写或修正结果。局部函数核对解码后函数值，联合求值核对实际支持集及全部返回坐标，层级嵌入按明确的限制与重索引比较。

切面继续比较同一 $Q_b$ 与后续输入所得记录；KV 的有效状态投影 $\pi_{\mathrm{KV},v,\theta}$、外部读出及指定反向规则分别采用自身证明条件。有效投影可以丢弃原始状态细节，不能代替无损解码。KV 局部教材附录 A 给出正式连续性证明，附录 S 定义计算表示、求解与反向目标。[实现核对](weighted-kv-implementation-checks.md)整理位置、软硬极限和分段继续的检查范围；浮点容差和有限验证结果由具体实现声明。
