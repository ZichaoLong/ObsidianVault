---
type: mathematical-learning-note
status: active
cssclasses:
  - textbook-math
tags:
  - tide
  - mathematics
  - semantic-anchor
  - local-semantics
  - learning-note
  - memory
  - sparse-activation
---

# 带权 KV 与稀疏 Full：局部计算语义与退火

本文定义一族接收驱动的神经计算模块：带来源信息的消息聚合、私有带权 KV、当前内容与记忆的描述量、保证非空选择的预算分配，以及带权多头 Attention 和前馈残差。记忆读取、局部评分、区域匹配、发送增益和预算正则分别选择，共用写入与 Full。节点接收后先形成记忆和描述量，区域选择决定哪些节点应用 Full；有正发送上界的候选时至少激活一个。

函数采用四篇正典的共同签名与作用结果。学过 [[settlegraph-learning-note|SettleGraph]] 或 [[timed-dag-region-selector-learning-note|TimedDAG]] 后，可沿第 2 节的函数、第 3 节的选择结构与算例阅读。第 4 节解释强度、记忆与零消息，第 5 节证明固定正温度的连续性及单位输入的硬化连续性；第 6--7 节给出联合求值、继续与工作量。正式证明见附录 A，计算表示、求解与反向见附录 S。

[[weighted-kv-layered-example|全连接分层实例]] 与 [[weighted-kv-hb-lattice-example|HB-Lattice 实例]] 分别绑定拓扑、时间和边界。局部函数和空间连接按第 2.9 节组合；设计取舍见 [机制备忘](memos/architecture/selector-and-memory.md)，训练方案见 [实验与推进](memos/learning-systems/weighted-kv-experiment-plan.md)，程序对应关系见 [实现核对](weighted-kv-implementation-checks.md)。

## 1. 适用结构与基本对象

### 1.1 图、局部函数与组合参数

固定有限正时延图及其区域划分、输入输出端口和注入日程，另固定节点全序用于硬选择平票。以下函数适用于 PositiveDelayGraph；满足无环条件或单次结算条件时，分别得到 TimedDAG、SettleGraph 中的同名函数。

节点保存私有 KV，初态为空；区域选择历史取单点集 $Y_j=\{*\}$。同一区域可共享声明的参数，节点各自保有状态与计算快照。消息与状态按正典的逻辑时间 $\theta$ 读取。

一次作用中，Agg 将完整输入纤维变为本地内容 $h$，Upd 将旧状态 $q$ 更新为 $\widetilde q$，Read 从更新后的状态和本地内容形成描述量。SelStep 汇集区域描述量，返回激活集合 $A$ 与控制族 $(c_v)$。本函数族取 BO 与默认 Next，全部候选保留 $\widetilde q$，激活者再从该快照计算 Full。第 3.5 节给出一次完整手算。

一个组合需给出图与日程、来源类别映射、位置坐标，以及所比较的输出槽集合。来源映射把端口或边身份变为聚合使用的类别；输出槽集合指定数值读出比较哪些端口和时刻。第 2.9 节列出全部局部绑定。一次运行固定图、参数、时间规则、窗口与选择配置。

### 1.2 宽度、归一化与参数

取正整数内容宽度 $d$、Attention 头数 $H_{\mathrm{att}}$ 与每头宽度 $d_h$，满足 $H_{\mathrm{att}}d_h=d$。另取聚合瓶颈宽度 $p_a$、记忆描述宽度 $d_s$、评分隐藏宽度 $d_r$、选择匹配宽度 $d_{\mathrm{sel}}$、KV 适配秩 $r_a$ 与前馈宽度 $d_f$，均为正整数。内容宽度 $d$ 在相连区域间相容，其余宽度可逐区域声明。

固定 $\epsilon>0$，对任意宽度 $p$ 定义无仿射参数的 RMS 归一化和逐坐标激活：

$$
\mathcal N_p(x)=\frac{x}{\sqrt{\epsilon+\|x\|_2^2/p}},
\qquad
\sigma(x)=\frac1{1+e^{-x}},
\qquad
\operatorname{SiLU}(x)=x\,\sigma(x).
\tag{1}
$$

$\epsilon$ 是模型函数的一部分。下文所有矩阵、偏置和残差尺度均为有限实参数；$\odot$ 表示逐坐标乘法，方括号表示向量拼接。共享范围和参数约束在使用处给出。

### 1.3 消息、强度与数值比较

消息载荷空间取 $P=\mathbb R^{1+d}$，写作 $(m,z)$，其中 $m$ 是强度坐标，$z\in\mathbb R^d$ 是内容。令 $m_+=\max(m,0)$，所有接收函数用 $m_+$ 解释强度，因此在整个 $P$ 上有定义；本模型实际发出的强度非负。局部消息的数值投影为

$$
\pi_P(m,z)=(m_+,m_+z),
\qquad \pi_P(\bot)=0\in\mathbb R^{1+d}.
\tag{2}
$$

内容单独保存，其贡献由强度乘一次得到。$(0,z)$ 是存在的零强度消息，仍可使接收方成为候选；$\bot$ 是缺席，不提供候选资格。式 (2) 定义后文连续性所比较的数值对象，不把这两种规范记录视为相同。

### 1.4 逻辑时间与位置坐标

为每个节点固定位置函数

$$
\operatorname{Pos}_v:\mathbb N\to\mathbb R.
$$

逻辑时间 $\theta$ 决定消息到达、状态顺序和窗口成员；$\operatorname{Pos}_v(\theta)$ 为 Attention 提供位置坐标。本文使用的仿射族为

$$
\operatorname{Pos}_v(\theta)
=\frac{\theta-o_v^{\mathrm{pos}}}{s_v^{\mathrm{pos}}},
\qquad o_v^{\mathrm{pos}}\in\mathbb R,\quad s_v^{\mathrm{pos}}>0.
$$

$o_v^{\mathrm{pos}}=0,s_v^{\mathrm{pos}}=1$ 直接编码逻辑时间。SettleGraph 的 $\theta_{v,t}=Dt+r_v$ 可取 $o_v^{\mathrm{pos}}=r_v,s_v^{\mathrm{pos}}=D$，于是 $\operatorname{Pos}_v(\theta_{v,t})=t$，恢复通常的输入位置。一般图中，同一纤维可以汇合不同输入位置的消息；这里编码当前聚合的处理时间和历史条目的写入时间，无需给混合内容指定唯一来源位置。

位置函数在整条继续运行中固定，不随接收次数、激活次数或分段边界改变。更一般的固定实值位置函数也可用于下文定义与有限切面证明；具体组合须给出其完整定义。

## 2. 完整局部定义

### 2.1 带来源信息的接收聚合

对区域 $j$，固定有限来源类别集，以及从每个节点输入端口或父边标签到来源类别的映射 $\operatorname{SrcClass}_v$。具体类别由组合配置给出，不依赖当前候选数或消息到达次序。不同来源可以使用同一类别，所有原子仍分别参与聚合。

区域共享 $A_j\in\mathbb R^{p_a\times d}$、$B_j\in\mathbb R^{d\times p_a}$ 和来源嵌入 $e_{j,a}\in\mathbb R^{p_a}$，固定尺度 $\alpha_{\mathrm{agg}}\ge0$。对 $z=(\mathrm{ext},i,k,p)$ 取来源标签 $(\mathrm{ext},i)$，对 $z=(\mathrm{msg},\eta,a,p)$ 取 $(\mathrm{msg},a)$，记为 $\operatorname{source}(z)$。对任意有限 $B\subseteq\mathsf{Atom}_v$，将各原子的来源和值记为 $(a_i,(m_i,z_i))$；这个枚举只用于求和，仍保留所有原子。定义

$$
\begin{aligned}
r&=\sum_i(m_i)_+,\\
\bar z&=\frac{\sum_i(m_i)_+z_i}{r}
&& (r>0),\\
\bar f&=\frac{\sum_i(m_i)_+
  \operatorname{SiLU}(A_j\mathcal N_d(z_i)+e_{j,\operatorname{SrcClass}_v(a_i)})}{r}
&& (r>0),\\
u&=\begin{cases}
\bar z+\alpha_{\mathrm{agg}}B_j\bar f,&r>0,\\
0,&r=0,
\end{cases}
\qquad h=(r,u).
\end{aligned}
\tag{3}
$$

当 $r=0$ 时不求两个商。在三层均取 $X_v=P=\mathbb R^{1+d}$，并令

$$
\operatorname{Agg}_v:\mathbb N\times\mathcal P_{\mathrm{fin}}(\mathsf{Atom}_v)\to X_v,
\qquad \operatorname{Agg}_v(\theta,B)=(r,u).
$$

空集同样由式 (3) 得到 $(0,0)$；实际没有输入时保持无节点作用。来源分类可忽略不需要的时间坐标，原子和规范记录仍保留这些坐标。

均值残差保留内容尺度；非线性来源项使相反内容、不同来源的组合不必因均值相同而不可区分。它将输入内容压缩为 $d$ 维摘要，部分消息信息会丢失。$\alpha_{\mathrm{agg}}=0$ 恢复普通加权均值。

零强度项不进入两个加权和。全体强度同时缩放且仍为正时，$u$ 不变，$r$ 改变；下述写入、评分与发送上界分别读取这个强度信息。

共享的 $A_j,B_j$ 让节点在共同特征空间解释来源，减少参数，并在输入相同时允许复用聚合。来源嵌入进入非线性之前，能改变不同来源的响应，但仍共享投影方向。稀疏图中不同节点收到不同邻域的消息，即使参数共享，内容和历史也会分化。

需要更强的节点或来源分工时，可将式 (3) 的非线性残差写为

$$
\begin{aligned}
F_{v,a}(z)&=B_{v,a}\operatorname{SiLU}
 (A_{v,a}\mathcal N_d(z)+e_{v,a}),\\
u&=\bar z+\frac{\alpha_{\mathrm{agg}}}{r}
 \sum_i(m_i)_+F_{v,\operatorname{SrcClass}_v(a_i)}(z_i)
 \quad(r>0),
\qquad u=0\quad(r=0).
\end{aligned}
\tag{3a}
$$

其中 $A_{v,a}\in\mathbb R^{p_a\times d}$、$B_{v,a}\in\mathbb R^{d\times p_a}$、$e_{v,a}\in\mathbb R^{p_a}$。下列绑定均给出完整的 Agg：

| 聚合配置 | 参数绑定 | 主要取舍 |
|---|---|---|
| 区域共享 | $A_{v,a}=A_j,B_{v,a}=B_j,e_{v,a}=e_{j,a}$ | 恢复式 (3)，共享特征空间与参数 |
| 节点独立 | $A_{v,a}=A_v,B_{v,a}=B_v$，嵌入按节点和类别声明 | 节点可在压缩前提取不同信息，增加准备成本 |
| 来源独立 | $A_{v,a}=A_{j,a},B_{v,a}=B_{j,a},e_{v,a}=e_{j,a}$ | 不同来源采用不同投影，参数随类别数增长 |
| 节点与来源适配 | $A_{v,a}=A_j+L^A_{v,a}R^A_{v,a}$，$B_{v,a}=B_j+L^B_{v,a}R^B_{v,a}$ | 以指定秩控制分化与成本 |

最后一行取正整数秩 $r_{\mathrm{agg}}$；$L^A,R^A,L^B,R^B$ 的形状依次为 $p_a\times r_{\mathrm{agg}}$、$r_{\mathrm{agg}}\times d$、$d\times r_{\mathrm{agg}}$、$r_{\mathrm{agg}}\times p_a$，嵌入另行声明。按需共享其中因子也属于这个绑定。

这些差异发生在消息被压缩之前；聚合后的节点适配一般无法恢复已经丢失的信息。附录 A 的证明适用于上述全部绑定：所需条件是固定、连续且在有界内容上有界的 $F_{v,a}$，以及强度加权。

### 2.2 接收驱动的时间窗口 KV

节点状态空间 $S_v$ 是全部有限序列

$$
q=((\xi_i,k_i,\nu_i,p_i,w_i))_{i=1}^N,
\quad \xi_i\in\mathbb N,\quad
k_i,\nu_i\in\mathbb R^d,\quad
p_i\in\mathbb R^{d_s},\quad w_i\ge0.
\tag{4}
$$

$k_i,\nu_i$ 按头分成 $d_h$ 维子向量；$p_i$ 是供 Read 使用的摘要特征，$w_i$ 是独立的写入权重，$\xi_i$ 是原始逻辑时间。初态为空；可达运行中每节点每逻辑时间至多写一项。

区域共享基座 $W_j^{\mathrm{KV}}\in\mathbb R^{2d\times d}$，节点各有 $U_v\in\mathbb R^{2d\times r_a}$、$V_v^{\mathrm{ad}}\in\mathbb R^{r_a\times d}$ 与 $W_v^S\in\mathbb R^{d_s\times d}$。定义

$$
\begin{aligned}
[k_v(u);\nu_v(u)]
  &=(W_j^{\mathrm{KV}}+U_vV_v^{\mathrm{ad}})\mathcal N_d(u),\\
p_v(u)&=W_v^S\mathcal N_d(u),
\qquad w(r)=\min(1,r_+).
\end{aligned}
\tag{5}
$$

共享基座给出区域共同的 KV 投影，节点差异由秩至多为 $r_a$ 的乘积提供。相同输入的基座投影可共同求值，各节点仍保存私有条目。取 $r_a=d$、$W_j^{\mathrm{KV}}=0$、$V_v^{\mathrm{ad}}=I_d$ 与 $U_v=[W_v^K;W_v^V]$，即可表示任意独立的 K、V 投影。式 (5) 定义写入；Attention 读取由第 2.7 节给出。

为每节点固定窗口 $T_v\in\mathbb N_{\ge1}\cup\{\infty\}$，以原始逻辑时间计量。定义遮罩

$$
\chi_{v,\theta}(\xi)=\mathbf1[0\le\theta-\xi<T_v].
$$

$q|_{v,\theta}$ 表示按原序保留 $\chi_{v,\theta}(\xi_i)=1$ 的条目。接收更新是

$$
\widetilde q=\operatorname{Upd}_v(q,\theta,(r,u))
=\begin{cases}
q|_{v,\theta}\mathbin{\oplus}
  (\theta,k_v(u),\nu_v(u),p_v(u),w(r)),&r>0,\\
q,&r\le0.
\end{cases}
\tag{6}
$$

$\oplus$ 表示追加。每个正强度纤维只写一条，KV 内容不预乘 $w$；全部零消息不追加，也不触发清理。是否执行本节点 Full 不参与写入决定。

所有读取同样使用 $\chi_{v,\theta}$。没有候选或只有零强度输入时，保存序列可以含已过期条目，但它们不会再被读出；下一次正接收再清理。有限 $T_v$ 下，由每逻辑时间至多写一项，可达保存序列始终至多含 $T_v$ 项。$T_v=\infty$ 保留全部接收历史，在每个有限切面仍只有有限项。历史覆盖范围取决于该节点实际收到的内容。

窗口按时间而不按“最近收到多少条”定义：一条趋零的输入不会挤掉一条仍在时间窗口内的强记忆。窗口长度固定，内容驱动淘汰或计数淘汰属于其他函数族。

### 2.3 记忆描述与成对的 Read、SelStep

先选择记忆描述、局部评分与发送增益，再选择是否汇集区域信息。这些选择在区域内固定；不同区域可作不同选择。节点的 Read 给出描述量，SelStep 将该类型的描述量转成评分和控制。

**时间摘要。** 对每节点取 $\beta_{v,\mathrm{long}}=0$、$\beta_{v,\mathrm{short}}>0$，均按逻辑时间计量。固定节点后省略部分下标，对 $a\in\{\mathrm{short},\mathrm{long}\}$ 定义

$$
\begin{aligned}
\omega_i^a(\theta)&=\chi_{v,\theta}(\xi_i)w_i
 e^{-\beta_{v,a}(\theta-\xi_i)_+},\\
W_a(q,\theta)&=\sum_i\omega_i^a(\theta),\\
M_a^{\mathrm{sum}}(q,\theta)&=
 \frac{\sum_i\omega_i^a(\theta)p_i}{\max(1,W_a(q,\theta))}.
\end{aligned}
\tag{7}
$$

短期摘要突出近期接收，长期摘要覆盖整个窗口；分母使最后一条弱记忆消失时摘要也趋零。摘要本身只按时间和写入权重汇集，当前内容在后续评分中与它交互。

**内容检索。** 另取节点矩阵 $W_v^{\mathrm{RQ}},W_v^{\mathrm{RK}},W_v^{\mathrm{RV}}\in\mathbb R^{d_s\times d}$，定义

$$
\begin{aligned}
Q_v^{\mathrm{read}}(u)&=W_v^{\mathrm{RQ}}\mathcal N_d(u),\qquad
K_{v,i}^{\mathrm{read}}=W_v^{\mathrm{RK}}k_i,\qquad
V_{v,i}^{\mathrm{read}}=W_v^{\mathrm{RV}}\nu_i,\\
\ell_{v,i}^{\mathrm{read}}&=
\frac{
 [\operatorname{Rot}_v^{\mathrm{read}}(\operatorname{Pos}_v(\theta))Q_v^{\mathrm{read}}(u)]^\top
 [\operatorname{Rot}_v^{\mathrm{read}}(\operatorname{Pos}_v(\xi_i))K_{v,i}^{\mathrm{read}}]
}{\sqrt{d_s}},\\
M_a^{\mathrm{qry}}(q,\theta,u)&=
\begin{cases}
\displaystyle \min(1,W_a)
 \frac{\sum_i\omega_i^a e^{\ell_{v,i}^{\mathrm{read}}}V_{v,i}^{\mathrm{read}}}
      {\sum_i\omega_i^a e^{\ell_{v,i}^{\mathrm{read}}}},&W_a>0,\\
0,&W_a=0.
\end{cases}
\end{aligned}
\tag{7a}
$$

取偶数 $0\le d_v^{\mathrm{rot,read}}\le d_s$、坐标配对及有限频率 $\omega_{v,a}^{\mathrm{rot,read}}$。$\operatorname{Rot}_v^{\mathrm{read}}$ 使用第 2.7 节的旋转矩阵族，宽度换为 $d_s$，采用这些独立参数；零旋转维数给出内容匹配。它沿用同一 $\operatorname{Pos}_v$，与 Full 的位置配置分别选择。两个时间尺度共用本次检索 logit。此时先用当前内容查询私有 KV，再把检索结果交给评分；无须执行 Full 的输出投影或前馈。宽度与检索量允许接近 Full，成本按实际配置计量。

固定 $\mathfrak m_j\in\{\mathrm{sum},\mathrm{qry}\}$ 后，以下 $M_a$ 表示相应记忆描述，均在 $(q,\theta,u)$ 的适用自变量上求值。

**拼接局部评分。** 定义

$$
\begin{aligned}
f_v(q,\theta,r,u)=
\big[&\mathcal N_d(u);\ \log(1+r_+);\
 M_{\mathrm{short}};\ M_{\mathrm{long}};\\
 &\log(1+W_{\mathrm{short}});\
 \log(1+W_{\mathrm{long}});\\
 &p_v(u)\odot M_{\mathrm{short}};\
 p_v(u)\odot M_{\mathrm{long}}\big],\\
s_v^{\mathrm{cat}}(q,\theta,r,u)
 &=b_v+a_v^\top
   \operatorname{SiLU}(W_v^r f_v(q,\theta,r,u)+b_v^r).
\end{aligned}
\tag{8}
$$

$f_v$ 的宽度为 $d+4d_s+3$，$W_v^r\in\mathbb R^{d_r\times(d+4d_s+3)}$，$a_v,b_v^r\in\mathbb R^{d_r}$，$b_v\in\mathbb R$，均按节点独立。这是拼接特征上的单隐藏层网络；不同列的权重分别解释内容、强度、记忆质量与交互项。

**分组编码与内容—记忆匹配。** 另定义三组输入

$$
z_v^{\mathrm{cur}}=\mathcal N_d(u),\qquad
z_v^{\mathrm{mem}}=[M_{\mathrm{short}};M_{\mathrm{long}}],\qquad
z_v^{\mathrm{stat}}=[\log(1+r_+);\log(1+W_{\mathrm{short}});\log(1+W_{\mathrm{long}})].
$$

对 $g\in\{\mathrm{cur},\mathrm{mem},\mathrm{stat}\}$，输入宽度依次为 $n_g=d,2d_s,3$，定义

$$
\begin{aligned}
E_v^g(z)&=\mathcal N_{d_{\mathrm{sel}}}
 \bigl(C_v^{\mathrm{enc},g}\operatorname{SiLU}(B_v^{\mathrm{enc},g} z+b_v^{\mathrm{enc},g})+d_v^{\mathrm{enc},g}\bigr),\\
x_v^{\mathrm{match}}&=E_v^{\mathrm{cur}}(z_v^{\mathrm{cur}}),\qquad
e_v^{\mathrm{match}}=E_v^{\mathrm{mem}}(z_v^{\mathrm{mem}}),\qquad
z_v^{\mathrm{match}}=E_v^{\mathrm{stat}}(z_v^{\mathrm{stat}}),\\
h_v^{\mathrm{match}}&=[x_v^{\mathrm{match}};e_v^{\mathrm{match}};z_v^{\mathrm{match}}],\\
F_v^{\mathrm{match}}(h)&=(w_v^{\mathrm{match}})^\top
 \left[\operatorname{SiLU}(W_v^{\mathrm{match,gate}}h+b_v^{\mathrm{match,gate}})
       \odot(W_v^{\mathrm{match,up}}h+b_v^{\mathrm{match,up}})\right],\\
s_v^{\mathrm{match}}&=b_v^{\mathrm{match}}
 +\alpha_v^{\mathrm{match}}\frac{(x_v^{\mathrm{match}})^\top e_v^{\mathrm{match}}}{\sqrt{d_{\mathrm{sel}}}}
 +\alpha_v^{\mathrm{res}}F_v^{\mathrm{match}}(h_v^{\mathrm{match}}),\\
s_v^{\mathrm{loc}}&=s_v^{\mathfrak f_j},\qquad
\mathfrak f_j\in\{\mathrm{cat},\mathrm{match}\}.
\end{aligned}
\tag{8a}
$$

这里 $B_v^{\mathrm{enc},g}\in\mathbb R^{d_r\times n_g}$、$C_v^{\mathrm{enc},g}\in\mathbb R^{d_{\mathrm{sel}}\times d_r}$，两个偏置分别为 $d_r,d_{\mathrm{sel}}$ 维；$W_v^{\mathrm{match,gate}},W_v^{\mathrm{match,up}}\in\mathbb R^{d_r\times3d_{\mathrm{sel}}}$，$b_v^{\mathrm{match,gate}},b_v^{\mathrm{match,up}},w_v^{\mathrm{match}}\in\mathbb R^{d_r}$，$b_v^{\mathrm{match}}$ 为标量。两个非负尺度及全部参数有限。各组先独立编码并归一化，匹配项表达当前内容与记忆的关系，残差项补充统计量及非线性交互。参数默认按节点独立，也可在配置中声明同形评分头的参数相等。

$\mathrm{cat}$ 提供较小的基线；$\mathrm{match}$ 加入结构性偏好和准备成本。分组后的非线性、归一化与显式匹配构成函数差异；仅将一个线性矩阵拆成三块再相加，会得到原来的线性运算。两种局部评分均可搭配任一种记忆描述与下述区域评分。

**有界发送增益。** 写入强度仍为 $w(r)$。选择 $\mathfrak g_j\in\{\mathrm{fixed},\mathrm{context}\}$，固定有限 $\gamma_{\max}\ge1$，定义

$$
\begin{aligned}
\gamma_v^{\mathrm{fixed}}&=\gamma_v,\qquad 1\le\gamma_v\le\gamma_{\max},\\
\gamma_v^{\mathrm{context}}(q,\theta,r,u)
 &=1+(\gamma_{\max}-1)\sigma\!\left(
 b_v^\gamma+(a_v^\gamma)^\top
 \operatorname{SiLU}(W_v^\gamma f_v(q,\theta,r,u)+b_v^{\gamma,h})\right),\\
\mu_v(q,\theta,r,u)&=\min\left(1,\gamma_v^{\mathfrak g_j}(q,\theta,r,u)r_+\right).
\end{aligned}
\tag{9}
$$

固定增益省略无关自变量，可通过 $\gamma_v=1+(\gamma_{\max}-1)\sigma(\zeta_v)$ 训练。上下文增益读取式 (8) 的同一特征，$W_v^\gamma\in\mathbb R^{d_r\times(d+4d_s+3)}$，$a_v^\gamma,b_v^{\gamma,h}\in\mathbb R^{d_r}$，$b_v^\gamma\in\mathbb R$；它可根据当前内容及已有记忆调整唤醒程度。$\gamma_{\max}=1$ 给出不放大的对照。两种选择均满足 $0\le\mu_v\le\gamma_{\max}r_+$，故零接收处发送上界趋零；$r\ge1$ 时均有 $\mu_v=1$。

**独立评分。** 选择 $\mathfrak s_j=\mathrm{ind}$ 时，取

$$
D_v^{\mathrm{ind}}=[0,1]\times\mathbb R,\qquad
\operatorname{Describe}_v^{\mathrm{ind}}(q,\theta,(r,u))
  =(\mu_v(q,\theta,r,u),s_v^{\mathrm{loc}}(q,\theta,r,u)).
$$

描述量是两个标量：发送上界和节点评分。当前内容与记忆已由所选局部网络压缩为评分；SelStep 直接取 $s_v=s_v^{\mathrm{loc}}$。在独立评分的分配阶段，$\mu_v$ 只进入预算可行域及所选正则；硬阶段还用它判定有效候选与发送强度。选择了上下文增益时，$\mu_v$ 本身也读取内容与记忆。

**区域 Attention 评分。** 选择 $\mathfrak s_j=\mathrm{att}$ 时，定义

$$
\begin{aligned}
x_v^{\mathrm{sel}}(u)&=W_v^{\mathrm{loc}}\mathcal N_d(u)+b_v^{\mathrm{loc}},\\
K_v^{\mathrm{sel}}(q,\theta,u)&=W_v^{\mathrm{mem}}
 [M_{\mathrm{short}};M_{\mathrm{long}};
 \log(1+W_{\mathrm{short}});\log(1+W_{\mathrm{long}})]
 +b_v^{\mathrm{mem}},\\
D_v^{\mathrm{att}}&=[0,1]\times\mathbb R^{d_{\mathrm{sel}}}
 \times\mathbb R^{d_{\mathrm{sel}}}\times\mathbb R,\\
\operatorname{Describe}_v^{\mathrm{att}}(q,\theta,(r,u))
 &=(\mu_v(q,\theta,r,u),x_v^{\mathrm{sel}}(u),K_v^{\mathrm{sel}}(q,\theta,u),s_v^{\mathrm{loc}}(q,\theta,r,u)).
\end{aligned}
\tag{9a}
$$

$W_v^{\mathrm{loc}}$、$W_v^{\mathrm{mem}}$ 的形状为 $d_{\mathrm{sel}}\times d$、$d_{\mathrm{sel}}\times(2d_s+2)$，两个偏置属于 $\mathbb R^{d_{\mathrm{sel}}}$。同一区域共享匹配宽度和坐标含义，投影参数按节点声明。

对完整候选集 $C$，SelStep 内部先形成共享 query，再产生各候选评分：

$$
\begin{aligned}
\bar x_j&=\frac{\sum_{v\in C}\mu_v x_v^{\mathrm{sel}}}
                    {\max(1,\sum_{v\in C}\mu_v)},\\
Q_j^{\mathrm{sel}}&=\psi_j(\bar x_j),\qquad
\psi_j(x)=W_j^{\mathrm{out,sel}}
 \operatorname{SiLU}(W_j^{\mathrm{in,sel}}x+b_j^{\mathrm{in,sel}})
 +b_j^{\mathrm{out,sel}},\\
s_v&=\alpha_j^{\mathrm{loc}}s_v^{\mathrm{loc}}
  +\alpha_j^{\mathrm{sel}}
   \frac{(Q_j^{\mathrm{sel}})^\top K_v^{\mathrm{sel}}}{\sqrt{d_{\mathrm{sel}}}}.
\end{aligned}
\tag{9b}
$$

两个区域矩阵均为 $d_{\mathrm{sel}}\times d_{\mathrm{sel}}$，偏置为 $d_{\mathrm{sel}}$ 维，尺度为固定非负有限参数。取 $\alpha_j^{\mathrm{loc}}=1,\alpha_j^{\mathrm{sel}}=0$ 恢复独立评分的数值；取 $\alpha_j^{\mathrm{loc}}=0$ 隔离区域匹配的作用。空候选仍直接返回空选择。

共享 query 表达该区域当前收到的信息，keys 表达各节点的私有记忆；$\mathrm{qry}$ 配置还让 keys 随本次内容检索而改变。Attention 匹配产生评分，第 2.4--2.5 节再决定预算分配和激活。这里的单 query 匹配对候选数是线性工作量，无须构造候选两两匹配矩阵。

$\mu_v$ 加权使零上界候选不影响其他节点的 query，趋零候选的影响也趋零；按候选数直接取均值一般不具备这个性质。区域划分同时规定选择可共享的信息范围。多个局部区域分别形成 query，无须在整个层上集中选择。

两种评分各自绑定 $D_v=D_v^{\mathfrak s_j}$，并使用对应 Describe，三个全函数统一为

$$
\begin{aligned}
\operatorname{Read}_v^+(\widetilde q,\theta,h)
 &=\operatorname{Describe}_v^{\mathfrak s_j}(\widetilde q,\theta,h),\\
\operatorname{Read}_v^-(q,\theta,h)
 &=\operatorname{Describe}_v^{\mathfrak s_j}(q,\theta,h),\\
\operatorname{Read}_v^0(\theta,h)
 &=\operatorname{Describe}_v^{\mathfrak s_j}((),\theta,h).
\end{aligned}
\tag{10}
$$

实际描述模式取 $\tau_j=+$；这里 $j=\rho(v)$。Read 和 SelStep 按 $\mathfrak s_j$ 成对选择，后者只读对应描述量，不自行访问节点状态。记忆描述 $\mathfrak m_j$、局部评分 $\mathfrak f_j$ 与增益 $\mathfrak g_j$ 均不改变该描述空间；区域 Attention 还将 $\mu_v$ 用于 query 汇集。基线取 $\mathfrak m_j=\mathrm{sum},\mathfrak f_j=\mathrm{cat},\mathfrak s_j=\mathrm{ind},\mathfrak g_j=\mathrm{fixed}$，其余选择可逐项比较。

### 2.4 保证非空的软选择

对区域 $j$，令 $C\subseteq\mathcal R_j$ 是完整候选集，按第 2.3 节的成对绑定从描述量取得 $(\mu_v,s_v)$。固定整数质量预算上限 $1\le k_j\le|\mathcal R_j|$、阈值 $\eta_j\in\mathbb R$ 与平滑参数 $\tau_{\mathrm{soft}}>0$，记调整后评分 $t_v=s_v-\eta_j$。阈值与其他配置在本次前向固定，不读取运行队列或 batch 同伴。

定义有效候选、可用总质量与发送质量下限

$$
C_{\mathrm{eff}}=\{v\in C:\mu_v>0\},\qquad
M_j=\sum_{v\in C}\mu_v,\qquad b_j=\min(1,M_j).
$$

控制空间取 $\mathsf C_v=[0,1]$。先固定可行域，再选择正则族 $\mathfrak b_j\in\{\mathrm{quad},\mathrm{bern},\mathrm{ent}\}$。门控定义为

$$
\begin{aligned}
F(\mu)&=\left\{c:0\le c_v\le\mu_v,\quad b_j\le\sum_{v\in C}c_v\le k_j\right\},\\
c^{\tau_{\mathrm{soft}}}
  &=\mathop{\arg\max}_{c\in F(\mu)}
  \left\{\sum_{v\in C}t_vc_v+
    \tau_{\mathrm{soft}}R^{\mathfrak b_j}(c;\mu)\right\}.
\end{aligned}
\tag{11}
$$

三种正则为

$$
\begin{aligned}
R^{\mathrm{quad}}(c;\mu)&=-\frac12\sum_vc_v^2,\\
R^{\mathrm{bern}}(c;\mu)&=\sum_{v:\mu_v>0}\mu_v h_B(c_v/\mu_v),
& h_B(p)&=-p\log p-(1-p)\log(1-p),\\
R^{\mathrm{ent}}(c;\mu)&=\sum_v h_\alpha(c_v),
& h_\alpha(c)&=
\begin{cases}
-c\log c,&\alpha=1,\\
\dfrac{c-c^\alpha}{\alpha(\alpha-1)},&1<\alpha\le2.
\end{cases}
\end{aligned}
\tag{11a}
$$

端点按 $0\log0=0$ 延拓；$\mathrm{bern}$ 的零上界项取零。$\mathrm{ent}$ 的形状参数 $\alpha=\alpha_j^{\mathrm{ent}}\in[1,2]$ 在配置中固定。二次正则偏好较小的平方范数；二元熵作用于各上界的占用比例；Shannon／Tsallis 熵作用于发送质量。三者在有效坐标上严格凹。由于 $b_j\le M_j$ 且 $b_j\le1\le k_j$，可行集非空、紧且凸，每种正温度解都存在且唯一。

$C_{\mathrm{eff}}\ne\varnothing$ 时总质量为正，至少一个节点激活；$M_j\to0$ 时下限同步趋零。尤其当 $M_j\le1$ 时，约束强制 $c=\mu$，评分和正则均不影响分配。这是所选质量下限的结果；它比“至少激活一个”更强。$k_j=1,M_j\ge1$ 时总质量恒为 $1$，共同阈值 $\eta_j$ 无效；$k_j>1$ 时阈值可调节超过下限的用量。将总质量固定为 $\min(k_j,M_j)$ 则定义另一个可行域。

以下处理 $M_j>1$。省略温度下标，写 $\tau=\tau_{\mathrm{soft}}$，定义各坐标的响应：

| 正则 | $g_{\mathfrak b}(x,\mu;\tau)$ |
|---|---|
| $\mathrm{quad}$ | $\operatorname{clip}(x/\tau,0,\mu)$ |
| $\mathrm{bern}$ | $\mu\,\sigma(x/\tau)$ |
| $\mathrm{ent},\alpha=1$ | $\min(\mu,\exp(x/\tau-1))$ |
| $\mathrm{ent},1<\alpha\le2$ | $\min\!\left(\mu,\left[(\alpha-1)x/\tau+1/\alpha\right]_+^{1/(\alpha-1)}\right)$ |

其中 $\operatorname{clip}(x,l,h)=\min(h,\max(l,x))$。记 $S=\sum_vc_v$，解满足

$$
\begin{aligned}
c_v&=g_{\mathfrak b_j}(t_v-\lambda,\mu_v;\tau),\\
\lambda&=\lambda_U-\lambda_L,\qquad \lambda_U,\lambda_L\ge0,\\
b_j&\le S\le k_j,\qquad
\lambda_U(S-k_j)=0,\qquad \lambda_L(b_j-S)=0.
\end{aligned}
\tag{12}
$$

先尝试 $\lambda=0$；若 $S>k_j$，求 $S=k_j$ 的非负乘子；若 $S<b_j$，求 $S=b_j$ 的非正乘子。各响应单调，故只需求一个标量根。二次族可按断点排序，全部族均可用二分或带区间保护的 Newton 法；反向由最优性条件直接求导，无须展开求根迭代。求解映射与分段导数见附录 S.3。

当 $k_j=1$ 且有效上界全为 $1$ 时，$\mathrm{ent}$ 正好成为单纯形上的 $\alpha$-entmax：$\alpha=1$ 给出 $\operatorname{softmax}(t/\tau)$，$\alpha=2$ 给出 sparsemax，二次族也给出 sparsemax。唯一最高分下，这些单纯形函数的零温极限均为 Top-1。式 (11) 的一般可行域允许多节点硬端点；可选节点数由约束与评分决定。

总质量可变时须保留线性项的影响：

$$
R^{\mathrm{ent}}_{\alpha=2}
=R^{\mathrm{quad}}+\frac12\sum_vc_v.
\tag{12a}
$$

因此相同 $t,\tau$ 下，$\alpha=2$ 的解等于二次族在 $t+\tau/2$ 下的解。要恢复同一数值，取 $\eta_j^{\mathrm{ent},2}=\eta_j^{\mathrm{quad}}+\tau/2$。这项差别在固定总质量上消失。本文将一般可行域上的 $\mathrm{ent}$ 称为带上界的 entmax 预算族。

正温度下，$\mathrm{bern}$ 和 $\mathrm{ent},\alpha=1$ 给所有有效候选正门控；前者在 $M_j>1$ 时也不精确达到上界。二次族与 $\mathrm{ent},\alpha>1$ 可以产生精确零和上界饱和。这个差别同时影响梯度覆盖和实际计算量。

**质量预算 $k_j$ 不等于正式执行容量 $K_j$。** 软规格取 $K_j=|\mathcal R_j|$，返回

$$
A=\{v\in C:c_v>0\},\qquad (c_v)_{v\in C},\qquad *.
\tag{13}
$$

所有候选都有控制量，只有正门控节点激活。空候选返回空集合、空控制族和原历史；非空但全为零上界时，同样不激活任何节点。零上界节点既不占预算，也不会因高分被激活。支持集规格与硬规格在单位外部输入的普通运行中只发正强度消息，因此非空候选集就是非空有效候选集。

另可声明一个全候选参考规格 $A=C$，保持同一门控，令零门控节点走第 2.7 节的廉价零分支。它保留额外的 Full 与零消息记录。它的额外事件仍具有零数值贡献。

### 2.5 硬选择与质量预算的边界

$\tau_{\mathrm{soft}}=0$ 时另行定义硬函数，不代入式 (12)。硬规格取 $K_j=k_j$。令

$$
C_+=\{v\in C_{\mathrm{eff}}:t_v>0\}.
$$

若 $C_+\ne\varnothing$，按 $t_v$ 降序选择前 $\min(k_j,|C_+|)$ 个。若 $C_+=\varnothing$ 且 $C_{\mathrm{eff}}\ne\varnothing$，选择有效候选中评分最高的一个；$C_{\mathrm{eff}}=\varnothing$ 时取 $A=\varnothing$。两种排序的平票均按固定节点序。返回

$$
c_v^{\mathrm{hard}}=\mu_v\mathbf1[v\in A]\quad(v\in C),
\qquad \text{下一历史为 }*.
\tag{14}
$$

这是对所有描述量都有定义的全函数。有效候选非空时，$1\le|A|\le\min(k_j,|C_{\mathrm{eff}}|)$；零上界候选始终不参与选择。阈值决定是否在最优的一个节点以外继续选取。

第 5.2 节在单位输入与端点评分条件下证明整网软运行收敛到此硬函数；第 5.3 节给出相应边界例子。

### 2.6 BO、计算快照与下一状态

取 BO，即 $\kappa_j=1$，并采用默认 Next。对每个候选，

$$
q^{\mathrm{cmp}}=\widetilde q,\qquad
\operatorname{Next}_v(q,q^{\mathrm{cmp}},\theta,h,
             \mathbf1[v\in A],c_v)=q^{\mathrm{cmp}}.
\tag{15}
$$

因此候选状态、Full 的计算快照、下一持久状态相同。未选中者也保留接收更新；没有输入者保持原状态。节点无需等待本次选择才决定如何写入，本次 Full 的结果也不回写自己的 KV。

### 2.7 Full：带权多头 Attention 与前馈残差

以下先定义正门控时的昂贵内容函数。对每个头 $1\le h\le H_{\mathrm{att}}$，取 $W^Q_{v,h}\in\mathbb R^{d_h\times d}$。固定偶数 $0\le d^{\mathrm{rot}}_{v,h}\le d_h$、坐标配对与有限频率 $\omega^{\mathrm{rot}}_{v,h,a}$，定义

$$
\begin{aligned}
\operatorname{Rot}_{v,h}(p)
 &=I_{d_h-d^{\mathrm{rot}}_{v,h}}
   \oplus\bigoplus_{a=1}^{d^{\mathrm{rot}}_{v,h}/2}
   \begin{pmatrix}
   \cos(\omega^{\mathrm{rot}}_{v,h,a}p)&-\sin(\omega^{\mathrm{rot}}_{v,h,a}p)\\
   \sin(\omega^{\mathrm{rot}}_{v,h,a}p)&\cos(\omega^{\mathrm{rot}}_{v,h,a}p)
   \end{pmatrix}.
\end{aligned}
$$

这里的 $\oplus$ 为矩阵直和。旋转维数为零时 $\operatorname{Rot}=I_{d_h}$；旋转全部或部分坐标分别得到完整或部分 RoPE。旋转维数与评分隐藏宽度 $d_r$ 各自独立。

另可取非负距离偏置斜率 $b^{\mathrm{pos}}_{v,h}$，通常置零。定义

$$
\begin{aligned}
Q_{v,h}(u)&=W^Q_{v,h}\mathcal N_d(u),\\
\widehat w_i&=\chi_{v,\theta}(\xi_i)w_i,\qquad
W=\sum_i\widehat w_i,\qquad a(W)=\min(1,W),\\
\ell_{i,h}&=\frac{
 [\operatorname{Rot}_{v,h}(\operatorname{Pos}_v(\theta))Q_{v,h}(u)]^\top
 [\operatorname{Rot}_{v,h}(\operatorname{Pos}_v(\xi_i))k_{i,h}]}{\sqrt{d_h}}
 -b^{\mathrm{pos}}_{v,h}
   (\operatorname{Pos}_v(\theta)-\operatorname{Pos}_v(\xi_i))_+,\\
R_{v,h}(q,\theta,u)
&=\begin{cases}
\displaystyle a(W)
 \frac{\sum_i\widehat w_i e^{\ell_{i,h}}\nu_{i,h}}
      {\sum_i\widehat w_i e^{\ell_{i,h}}},&W>0,\\
0,&W=0.
\end{cases}
\end{aligned}
\tag{16}
$$

数学状态中的 $k_i$ 保持未旋转形式，$\nu_i,p_i$ 也不施加旋转。上述旋转满足

$$
\operatorname{Rot}_{v,h}(p)^\top\operatorname{Rot}_{v,h}(q)
=\operatorname{Rot}_{v,h}(q-p),
$$

故旋转后的匹配依赖相对坐标，并包含各频率对应的相位信息。下面三种配置共用式 (16)：

| 配置 | 旋转维数 | 距离偏置 |
|---|---|---|
| NoPE | $d^{\mathrm{rot}}_{v,h}=0$ | $b^{\mathrm{pos}}_{v,h}=0$ |
| 完整 RoPE | $d^{\mathrm{rot}}_{v,h}=d_h$，要求 $d_h$ 为偶数 | 通常为零 |
| 部分 RoPE | $0<d^{\mathrm{rot}}_{v,h}<d_h$，旋转维数为偶数 | 通常为零 |

NoPE 的 Full 匹配使用内容，时间窗口、摘要和状态顺序仍保留时间信息。可选的线性距离偏置在 softmax 中乘入 $e^{-b^{\mathrm{pos}}_{v,h}\Delta p_+}$，是一种距离衰减；它与 RoPE 的旋转可以分别配置。

非空有效记忆的权重全为 $1$ 时，式 (16) 恰为所选位置配置下的普通多头 Attention；结合式 (5) 的独立投影特例可恢复常用的 K、V 参数化。最后一条弱记忆消失时，$a(W)$ 使读出趋零；只把弱权重放进 softmax 分子、分母会相互抵消，不能得到这一性质。$a(1)=1$，单位记忆保持原尺度。

取 $W_v^O\in\mathbb R^{d\times d}$、$W_v^{\mathrm{gate}},W_v^{\mathrm{up}}\in\mathbb R^{d_f\times d}$、$W_v^{\mathrm{down}}\in\mathbb R^{d\times d_f}$ 以及非负残差尺度 $\alpha_{\mathrm{att}},\alpha_{\mathrm{ff}}$，定义

$$
\begin{aligned}
x_v&=u+\alpha_{\mathrm{att}}W_v^O
       [R_{v,1};\ldots;R_{v,H_{\mathrm{att}}}],\\
G_v(q,\theta,u)
 &=x_v+\alpha_{\mathrm{ff}}W_v^{\mathrm{down}}
 \left[
 \operatorname{SiLU}(W_v^{\mathrm{gate}}\mathcal N_d(x_v))
 \odot W_v^{\mathrm{up}}\mathcal N_d(x_v)
 \right].
\end{aligned}
\tag{17}
$$

第二行为预归一化的 SwiGLU 前馈残差。查询、Attention 和前馈只在需要正门控内容时求值。载荷函数 $\operatorname{EmitValue}_v:S_v\times\mathbb N\times X_v\times\mathsf C_v\to P$ 定义为

$$
\operatorname{EmitValue}_v(q^{\mathrm{cmp}},\theta,(r,u),c)
=\begin{cases}
(0,0),&c=0,\\
(c,G_v(q^{\mathrm{cmp}},\theta,u)),&c>0.
\end{cases}
\tag{18}
$$

发送贡献是 $cG_v$，门控作用于整个内容，包括输入残差。上界已经约束 $c$，不再发送 $(\mu_v c,\cdot)$，也不把内容预先写成 $cG_v$ 后再乘一次 $c$。记忆权重、Attention 归一化权重与发送门控承担不同角色。

在三个层级中统一定义广播提升

$$
\Delta_v(p)=
\bigl((p)_{a\in\operatorname{Out}(v)},
      (p)_{o\in\operatorname{OutPort}(v)}\bigr),
\qquad \operatorname{Full}_v=\Delta_v\circ\operatorname{EmitValue}_v.
$$

三层都只对 $v\in A$ 调用 Full。一次激活向所有出边和输出端口发送同一个载荷；来源信息在接收时由固定边标签提供。本设计未再加入按出边分配的门控。

零分支使 Full 在整个控制空间上有定义。支持集规格不调用它；全候选参考规格可以在 Attention 前直接返回。Full 只读既定快照，产生的内容经下游接收影响下游记忆。

### 2.8 输出边界与连续读出

先固定有限输出槽集合 $\Lambda\subseteq\mathbb N\times\mathsf O$。从完整输出记录 $Z$ 取

$$
Z_\Lambda=\{z\in Z:(\operatorname{outtime}(z),\operatorname{outport}(z))\in\Lambda\}.
$$

对任意有限输出记录集合 $\mathcal M$，将其载荷记为 $(m_i,z_i)$，定义

$$
O(\mathcal M)=\frac{\sum_i(m_i)_+z_i}{\max(1,\sum_i(m_i)_+)},\qquad
\operatorname{ReadOut}_\Lambda(Z)=O(Z_\Lambda).
\tag{19}
$$

空集合给零向量。待声明槽位全部确定后求值。一个单位载荷原样读出，多个相同单位载荷的读出保持原尺度，总强度趋零时读出趋零。原始输出的端口和时间身份仍保留在 $Z$ 中；全零输出与缺席输出均读出零。

组合配置选择有限集合 $\Lambda$，并声明其任务含义。例如序列模型可为每个输入位置指定一组 $\Lambda_t$，令 $O_t=\operatorname{ReadOut}_{\Lambda_t}(Z)$。这种数值汇集发生在图外，不增加图内作用或输出记录。

### 2.9 局部绑定与组合条件

本函数族的配置先选择聚合绑定、记忆描述 $\mathfrak m_j$、局部评分 $\mathfrak f_j$、区域评分 $\mathfrak s_j$、发送增益 $\mathfrak g_j$ 和预算正则 $\mathfrak b_j$，再给出各宽度、$T_v,\epsilon$、矩阵与偏置、残差与评分尺度、摘要衰减率、位置函数、Read 与 Full 各自的旋转维数和频率、可选距离偏置、$\gamma_{\max}$ 与所选增益参数，以及各区域的 $k_j,\eta_j$。软规格另给 $\tau_{\mathrm{soft}}$、适用的 $\alpha_j^{\mathrm{ent}}$ 和支持集／全候选规则；硬规格采用第 2.5 节。它们在单次前向期间不变；分段继续同一次运行时使用同一配置。

| 共同对象 | 局部绑定 |
|---|---|
| $P,X_v$ | $\mathbb R^{1+d}$ |
| $S_v,q_v^{\mathrm{init}}$ | 式 (4) 的有限 KV 序列、空初态 |
| $D_v,\mathsf C_v,Y_j$ | 第 2.3 节的 $D_v^{\mathfrak s_j}$，$[0,1]$，$\{*\}$ |
| $\operatorname{Agg}_v,\operatorname{Upd}_v$ | 式 (3) 或 (3a)、式 (6) |
| $\operatorname{Read}^{0,-,+}_v$ | 式 (10)，实际描述模式 $\tau_j=+$ |
| $\operatorname{SelStep}_{j,C}$ | 由第 2.3 节取得评分，再取软式 (11)--(13) 或硬式 (14)，历史保持 |
| $\kappa_j,\operatorname{Next}_v$ | $\kappa_j=1$、式 (15) |
| $\operatorname{Full}_v$ | 三层均取 $\Delta_v\circ\operatorname{EmitValue}_v$，载荷由式 (18) 给出 |
| 数值读出 | 式 (19) 的 $\operatorname{ReadOut}_\Lambda$，槽集合由组合配置给出 |

空候选时 $\operatorname{SelStep}_{j,\varnothing}(*,\theta,())=(\varnothing,(),*)$。所有函数沿正典参数次序，Agg 接收完整原子集合，Full 返回逐边／逐端口两个值族。正典中的描述模式 $\tau_j$ 与平滑参数 $\tau_{\mathrm{soft}}$ 分别定义。

组合时还须满足：$1\le k_j\le|\mathcal R_j|$；来源映射覆盖所有输入端口和入边标签；共享参数与各节点宽度相容；Read 的描述空间与该区域 SelStep 相容；窗口、摘要衰减和位置坐标的尺度明确；每个读出组的端口、时刻及输入位置含义明确。硬化结论另需第 5.2 节的输入与间隔条件。

## 3. 预算选择的结构与例子

### 3.1 质量、支持与容量

固定一次选择，省略区域下标，记 $M=\sum_v\mu_v$、$b=\min(1,M)$、$S=\sum_vc_v$。

| 对象 | 数学含义 | 约束 |
|---|---|---|
| $\mu_v$ | 候选的发送上界 | $0\le\mu_v\le1$ |
| $c_v$ | 本次发送强度 | $0\le c_v\le\mu_v$ |
| $b,k$ | 区域总质量的下界、上界 | $b\le S\le k$ |
| $A$ | 本次正门控支持 | $A=\{v:c_v>0\}$ |
| $K$ | 正式激活容量 | $\lvert A\rvert\le K$；软规格为区域宽度，硬规格为 $k$ |
| $\eta,\tau$ | 共同评分阈值、正则尺度 | $t_v=s_v-\eta$，软规格 $\tau>0$ |

每个正门控都至多为 $1$，故 $S\le|A|$。例如 $k=2$ 时，$(0.8,0.6,0.4,0.2)$ 的总质量为 $2$，支持数为 $4$。硬规格直接约束选中者数量；在二元上界处，选中者各发送单位强度，因而 $S=|A|$。

式 (11) 的约束还给出两个直接推论。$M\le1$ 时，$b=M$ 与逐坐标上界强制 $c=\mu$。$k=1,M\ge1$ 时，总质量恒为 $1$，共同阈值只在目标中减去常数，因此不改变分配；$M<1$ 时门控已由上界固定。$k>1$ 时阈值可以调节超过下限的用量；达到下限后，共同阈值继续变化只改变乘子。

$M-b$ 是在逐坐标上界之下可放弃的总质量。它为零时，可行集只有 $\mu$ 一个点。候选收到弱消息与整个区域的可行集是否单点，由各自的 $r_v$ 和总量 $M$ 分别确定。

### 3.2 正则的支持与响应斜率

式 (12) 将各坐标写为 $c_v=g(t_v-\lambda,\mu_v;\tau)$。固定乘子和上界，记响应斜率为 $a_v=\partial g/\partial(t_v-\lambda)$。下表在 $M>1$ 的光滑分支上成立。

| 正则 | 正温度的支持与边界 | 自由坐标斜率 $a_v$ |
|---|---|---|
| quad | 可精确为零或达到上界 | $1/\tau$ |
| bern | 每个有效坐标严格处于上下界之间 | $\mu_v p_v^{\mathrm{occ}}(1-p_v^{\mathrm{occ}})/\tau$，$p_v^{\mathrm{occ}}=c_v/\mu_v$ |
| ent，$\alpha=1$ | 每个有效坐标为正，可达到上界 | $c_v/\tau$ |
| ent，$1<\alpha\le2$ | 可精确为零或达到上界 | $c_v^{2-\alpha}/\tau$ |

quad 与 ent 的严格零或上界饱和分支对评分的直接斜率为零。$1<\alpha<2$ 时，自由坐标趋零也使斜率趋零；quad 的自由斜率保持 $1/\tau$，到边界再切换分支。bern 的斜率随占用比例接近两端而趋小。完整导数还需计入共同乘子，见 §3.4。

在 $k=1$、有效上界全为 $1$ 时，ent 恢复单纯形上的 softmax／entmax／sparsemax；一般预算域还保留逐坐标上界及可变总质量。ent 的 $\alpha=2$ 与 quad 按式 (12a) 的阈值移位相互恢复。

固定评分、上界和预算，令 $\tau\to\infty$，则解趋向可行集上正则的唯一最大值：quad 是下限质量上的最小范数分配；bern 在 $\mu/2$ 可行时取它；ent 取其受约束的熵最大值。此结论由目标除以 $\tau$、紧性及严格凹性得到。不同正则的高温总质量因而可以不同。

### 3.3 两节点竞争与有限温度饱和

取 quad、$\mu=(1,1)$、$k=1$，记 $\Delta=s_1-s_2$。由 $c_2=1-c_1$，在目标中求导并投影到区间，得到

$$
c_1=\operatorname{clip}\left(\frac12+\frac{\Delta}{2\tau},0,1\right),
\qquad c_2=1-c_1.
$$

$|\Delta|<\tau$ 时两个节点均激活，质量随评分差连续变化。$\Delta\ge\tau$ 时门控为 $(1,0)$；严格不等式内的小幅评分变化保持同一门控。控制量始终在 $[0,1]$ 内，饱和发生于投影后的边界。$\Delta=0$ 时任意正温度均分质量；$\Delta>0$ 时 $\tau\le\Delta$ 已给出硬门控。

再取 $t=(4,3,2,1)$、上界全为 $1$、$k=2$：

| $\tau$ | 软门控 | 正门控支持数 |
|---|---|---|
| $5$ | $(0.8,0.6,0.4,0.2)$ | $4$ |
| $2$ | $(1,0.75,0.25,0)$ | $3$ |
| $0.4$ | $(1,1,0,0)$ | $2$ |

精确零使支持集规格省去对应 Full 与发送；收到输入的候选仍完成准备和写入。若下游整个纤维因此缺席，其节点作用也缺席。bern 与 Shannon 的正温度解保持全部有效支持，质量集中时仍执行这些节点的 Full。

### 3.4 分配导数与内容依赖

固定一次选择的光滑分支、上界和温度。若总质量固定在边界 $B$，微分 $\sum_vc_v=B$ 得

$$
d\lambda=\frac{\sum_v a_v\,ds_v}{\sum_v a_v},\qquad
dc_v=a_v(ds_v-d\lambda),\qquad \sum_v a_v>0.
$$

对任意可微标量目标 $\mathcal L$，令 $g_v=\partial\mathcal L/\partial c_v$、$\bar g=\sum_v a_vg_v/\sum_v a_v$，于是

$$
\frac{\partial\mathcal L}{\partial s_v}=a_v(g_v-\bar g).
$$

分配比较各自由坐标的边际影响。$a_v>0$ 且 $g_v<\bar g$ 时，该评分的负梯度方向为增大；固定其余评分且至少有两个自由坐标时，提高该评分会把质量分向该候选。共同乘子协调各自由坐标，ind 的独立评分也具有这个分配耦合。两质量界均松弛时，乘子为零，各坐标直接按自身响应变化。

quad 的自由子块为 $\tau^{-1}(I-\mathbf1\mathbf1^\top/|\mathcal F|)$，其中 $\mathcal F=\{v:0<c_v<\mu_v\}$。总质量固定且只有一个自由坐标时，该评分导数为零；所有自由候选的 $g_v$ 相同时，中心化同样给出零梯度。$M<1$ 时直接由 $c=\mu$ 得到零评分 Jacobian 和恒等上界 Jacobian。上界变化及各分支边界的完整导数见附录 S.3。

发送投影 $(c_v,c_vG_v)$ 同时依赖控制和 Full 内容。描述量经评分参与分配，区域 Attention 的共享 query 又让各候选内容影响其他评分；因此零门控但正上界的候选可经 query 保留其他候选的反馈。未激活者保存的写入还可进入未来 Read 或 Full，沿保留的依赖链传回导数。未求值的 Full 内容不提供该步替代分支的数值依据。

强度与内容在这些依赖中相互作用：强度决定加权聚合、写入和上界，内容与记忆决定评分及上下文增益。全部输入强度同比例缩放时聚合均值保持；若后续写入、上界和读出尺度也处于饱和区，目标可主要依赖相对分配。

固定评分且存在严格间隔时，低温可进入评分导数为零的饱和区；仍处于自由区的斜率则含 $1/\tau$。前向连续性由值的极限描述，这些导数在趋零温度下另有各自的边界行为。

### 3.5 一个区域的完整作用

以下完整作用例取二次预算族、拼接局部评分与固定增益。取无内部边的区域 $\{a,b,c\}$，初始缓存为空，$d=d_s=H_{\mathrm{att}}=1$、$\epsilon=1$、$\alpha_{\mathrm{agg}}=0$、$\gamma_v=1$，位置配置取 NoPE，采用时间摘要与独立评分。本次 $a$ 收到 $(0.5,1),(0.5,1)$，$b$ 收到 $(1,-1)$，$c$ 收到 $(0,9)$。三个节点都是候选。令 key、query 为零，value 与摘要投影均为 $\sqrt2$，故单位内容的归一化投影仍是 $\pm1$。

评分网络输出常数 $s=(2,1,100)$，可由零输出权重与相应偏置实现。取 $\eta_j=0,k_j=1,\tau_{\mathrm{soft}}=2$。

| 节点 | 聚合 $(r,u)$ | 新写入 $(k,\nu,p,w)$ | 上界 $\mu$ | 评分 $s$ | 门控 $c$ |
|---|---|---|---|---|---|
| $a$ | $(1,1)$ | $(0,1,1,1)$ | $1$ | $2$ | $0.75$ |
| $b$ | $(1,-1)$ | $(0,-1,-1,1)$ | $1$ | $1$ | $0.25$ |
| $c$ | $(0,0)$ | 不追加 | $0$ | $100$ | $0$ |

式 (12) 取 $\lambda=0.5$。零强度的 $c$ 不占预算。三者都完成状态采用，此时尚未计算 Full。

令 $W_v^O=1,\alpha_{\mathrm{att}}=1,\alpha_{\mathrm{ff}}=0$。$a,b$ 的 Attention 分别读出 $1,-1$，Full 内容为 $2,-2$，发送 $(0.75,2),(0.25,-2)$。若直接作为终端，$O=1$；若共同到达采用式 (3) 且 $\alpha_{\mathrm{agg}}=0$ 的下游，则下游得到 $(r,u)=(1,1)$，再开始自己的接收流程。

保持评分不变，将温度降到 $0.5$，门控已经是 $(1,0,0)$，只执行 $a$ 的 Full，终端 $O=2$。将阈值改为 $\eta_j=3$，同一温度下门控保持不变；在原温度 $2$ 下仍为 $(0.75,0.25,0)$，可取 $\lambda=-2.5$。这里上下质量界都为 $1$，共同阈值不改变分配。硬函数在全部有效评分低于阈值时仍选最高分的 $a$；$c$ 的零上界使其始终不参与选择。

### 3.6 未激活节点的记忆如何在以后有用

再取同一区域的两个节点 $a,b$，各有输入与输出端口，没有内部边。各输入端口在时间 $1,4$ 分别收到 $(1,1),(1,-1)$，取 $T_a=T_b\ge4$。沿用上一例的投影与 Full，每次读出同刻两个端口的输出；硬规格 $k_j=1,\eta_j=0$，评分改为

$$
s_a=0.5,\qquad
s_b=0.75-M_{\mathrm{long}}^{\mathrm{sum}}(\widetilde q_b,\theta).
$$

这属于式 (8) 的网络：$\operatorname{SiLU}(x)-\operatorname{SiLU}(-x)=x$，两个隐藏单元即可表达该线性项。

| 位置 | 两节点新写入的 $(\xi,\nu,p,w)$ | $M_{\mathrm{long}}$ | $(s_a,s_b)$ | 激活者 | 终端 $O$ |
|---|---|---|---|---|---|
| $0$ | $(1,1,1,1)$ | $1$ | $(0.5,-0.25)$ | $a$ | $2$ |
| $1$ | $(4,-1,-1,1)$ | $0$ | $(0.5,0.75)$ | $b$ | $-1$ |

第一次 $b$ 未激活，但保留 $+1$ 的记忆。第二次它的 Attention 读出 $(1-1)/2=0$，残差内容为 $-1$；若误删第一次未激活时的写入，Attention 会返回 $-1$，Full 内容变成 $-2$。本次选择与内容计算因此使用了前次未激活时保留的记忆。

### 3.7 区域 query 如何随候选变化

取 $d_{\mathrm{sel}}=2$，两个候选的描述量满足

$$
\begin{aligned}
\mu_a=1,\quad &x_a^{\mathrm{sel}}=(1,0),\quad K_a^{\mathrm{sel}}=(\sqrt2,0),\\
\mu_b=\varepsilon,\quad &x_b^{\mathrm{sel}}=(-1,0),\quad K_b^{\mathrm{sel}}=(-\sqrt2,0),
\qquad 0\le\varepsilon\le\tfrac12.
\end{aligned}
$$

取 $\alpha_j^{\mathrm{loc}}=0,\alpha_j^{\mathrm{sel}}=1$，$\psi_j(x_1,x_2)=(x_1,0)$。这个函数属于式 (9b)：取零偏置、$W_j^{\mathrm{in,sel}}=\left(\begin{smallmatrix}1&0\\-1&0\end{smallmatrix}\right)$、$W_j^{\mathrm{out,sel}}=\left(\begin{smallmatrix}1&-1\\0&0\end{smallmatrix}\right)$，利用 SiLU 的差恒等式即可。

于是

$$
Q_j^{\mathrm{sel}}=\left(\frac{1-\varepsilon}{1+\varepsilon},0\right),\qquad
s_a=\frac{1-\varepsilon}{1+\varepsilon},\quad s_b=-s_a.
$$

取 $k_j=1,\eta_j=0,\tau_{\mathrm{soft}}=1$。总质量为 $1$，投影给出

$$
c_b=\max\left(0,\frac{3\varepsilon-1}{2(1+\varepsilon)}\right),
\qquad c_a=1-c_b.
$$

在给定范围内 $c_b\le\varepsilon$。当 $\varepsilon=1/2$ 时，门控为 $(5/6,1/6)$；当 $\varepsilon\le1/3$ 时为 $(1,0)$。$b$ 在未激活但有正上界时仍参与 query，其上界趋零后影响连续消失，得到只保留 $a$ 的结果。加入任意零上界候选也不会改变 query 或这些控制量。

## 4. 零消息、状态投影与数值尺度

### 4.1 在同一逻辑时刻比较有效缓存

缓存长度可以变化，过期条目也可能尚未物理清理。固定有限切面 $B$，对从空初态可达的缓存按原始时间槽对齐，缺失槽补零。在比较时刻 $\theta\le B$ 定义

$$
\pi_{\mathrm{KV},v,\theta}(q)
=\bigl(
\chi_{v,\theta}(\xi)w_\xi,\
\chi_{v,\theta}(\xi)w_\xi k_\xi,\
\chi_{v,\theta}(\xi)w_\xi\nu_\xi,\
\chi_{v,\theta}(\xi)w_\xi p_\xi
\bigr)_{0\le\xi\le B}.
\tag{20}
$$

候选快照在其处理时间比较，切面状态在切面时间比较。这里比较的是可读的加权记忆，不要求弱条目的裸 key/value 收敛。

一条任意弱的正接收可能触发式 (6) 清掉旧过期项，而零接收保留原列表，故保存列表未必连续。式 (20) 在两种情况下都把过期项置零；这些项以后也不会重新进入窗口。前向连续性因此使用这个时刻相关投影，固定规格的精确求值仍须返回该规格要求的原始状态。

### 4.2 弱消息与最后一条记忆

在有限有界输入邻域内，式 (3) 或 (3a) 是内容的加权平均加有界非线性项，$u$ 有界。正极限接收强度处，$u$ 连续；总强度趋零时，$u$ 未必有唯一极限，但新条目的 $w,wk,w\nu,wp$ 全部趋零。归一化中的固定 $\epsilon>0$ 保证投影不因零范数出现奇点。

固定 $\theta$ 时，窗口遮罩和时间衰减只取决于原始时间身份。有效总权重 $W\to0$ 时，式 (16) 满足

$$
\|R_{v,h}\|_2\le a(W)\max_i\|\nu_{i,h}\|_2\longrightarrow0.
$$

固定位置函数与旋转频率后，这些结论对 NoPE、完整及部分 RoPE 均成立。旋转保持范数，固定时间槽使位置和窗口不随弱消息消失而移动。若用有效条目的序号编码位置，删除一个弱条目可能改变其后所有位置，便失去此前提。有界性与读取连续性的证明见附录 A.2--A.3。

### 4.3 选择与候选消失

固定 $\tau_{\mathrm{soft}}>0$，式 (11) 的解随评分与上界连续，并在固定截断模式内分段光滑。候选消失可按上界为零的坐标比较。正极限上界处评分须收敛，趋零上界处评分有界即可。时间摘要和内容检索均满足相应读取条件；区域 Attention 的加权 query 排除消失候选的影响，保留候选的评分因而收敛。

接收上界使弱候选的门控随接收强度消失；当整个区域的可用质量趋零时，质量下限也趋零。全零纤维与无纤维都保持状态，硬函数也忽略零上界。由此得到：

> [!theorem] 性质 1：零消息删除
> 在本函数族的软或硬规格中，增加或删除零强度消息不改变其余正强度计算及有效状态、局部消息投影和外部读出。软支持集规格与全候选参考规格具有相同的这些数值；原始候选、Full、消息和输出事件记录可以不同。

选择连续性与性质 1 的正式证明见附录 A.4--A.5。同一固定规格的等价求值必须保留全部规范记录；前向投影相等与反向规则相等分别检验。

### 4.4 各种权重的职责与衰减

| 数量 | 含义 | 避免的混淆 |
|---|---|---|
| $r,u$ | 收到多少强度、其聚合内容 | 不把 $u$ 先乘 $r$ 再写入 |
| $w(r)$ | 当前信息进入记忆的权重 | 不由本节点是否选中决定 |
| $\mu_v(q,\theta,r,u)$ | 当前可发送强度的上界 | 有界增益放大可用性，写入仍按 $w(r)$ |
| Attention 权重与 $a(W)$ | 记忆内的读取比例、总记忆消失的尺度 | 单位记忆不固定衰减 |
| $c_v$ | 整个 Full 内容的发送强度 | 不再额外乘一次 $\mu_v$ 或 $c_v$ |

令 $\alpha_{\mathrm{agg}}=\alpha_{\mathrm{att}}=\alpha_{\mathrm{ff}}=0$，单位门控单路径给出 $(1,u)\mapsto(1,u)$，可作为尺度基准。恢复残差分支后，尺度还受网络参数控制；带来源聚合会改变内容，不能再把整块称为恒等映射。

弱写入可以触发对已有强记忆的读取。发送贡献为 $cG_v$：有界增益可以提高 $c$，已有记忆与 Full 参数可以改变 $G_v$。两者分别影响强度与内容；新证据的写入仍为 $w(r)$，不会因唤醒旧记忆而变强。

在每区只有一个有效候选、无其他输入的单路径上，非空约束给出 $c=\mu$。若沿路固定增益均为 $4$，接收强度 $0.01$ 可依次产生 $0.04,0.16,0.64,1$ 的发送强度。弱信号因此可以在有限路径内恢复到单位强度。多个候选竞争时，门控可以低于上界，放大机会不保证一定被使用。

在无其他输入的长度 $L$ 单路径上，若各步增益上界为 $\Gamma_\ell<\infty$，则末端强度满足 $c_L\le r_0\prod_{\ell=1}^L\Gamma_\ell$。固定有限路径上，$r_0\to0$ 仍使发送及有界内容的贡献趋零。若要求任意小的正接收都立即产生固定非零强度，就会在零处不连续。本文的固定有限增益兼容弱接收放大与零边界连续性，不给出无限路径上的一致稳定性。增益增大使截断条件更早满足；上界饱和后，增益到上界的局部导数为零。

## 5. 有限切面上的连续性与硬化

本节固定图、全部模型参数、窗口、位置与评分配置，并从空初态比较有限切面以前的运行。消息使用式 (2)，缓存使用式 (20) 的有效投影，外部使用式 (19) 的连续读出。

| 比较 | 变化的量 | 极限结论 |
|---|---|---|
| 正温度连续性 | 输入投影收敛，温度固定或趋于正值 | 收敛到对应软运行的数值投影 |
| 单次选择的零温极限 | 上界与有效评分收敛，温度趋零 | 收敛到极限线性问题的唯一最优解 |
| 单位输入的整网硬化 | 同一外部输入与参数，温度趋零 | 在硬端点评分条件下收敛到对应硬运行 |

第一行允许弱候选消失；第二行确定优化极限；第三行说明何时该极限恰为本文的硬模型。比较对象均为数值投影，原始事件数与支持集另行计数。

### 5.1 固定正温度的数值连续性

> [!theorem] 命题 2：固定正平滑参数的数值连续性
> 固定有限正时延图、有限输入槽集合、时间编码、全部参数与配置，包括窗口、位置函数和旋转频率，以及有限切面 $B$。从空缓存开始，若输入的式 (2) 投影收敛到合法端点输入，且所考察输入内容有界，则固定 $\tau_{\mathrm{soft}}>0$ 下，切面以前按时间对齐的局部消息与 Full 各载荷的式 (2) 投影、KV 状态的式 (20) 投影及切面以前有限输出槽的连续读出收敛到端点运行。相同结论适用于 $\tau_{\mathrm{soft}}$ 趋向一个正值。

证明见附录 A.6。弱写入与弱发送带趋零权重，区域 query 按发送上界加权，位置及窗口按固定时间槽解释。证明覆盖第 2 节的全部聚合、记忆描述、评分、有界增益与预算正则组合；$\alpha_j^{\mathrm{ent}}$ 和 $\gamma_{\max}$ 属于固定配置。

局部载荷在三个层级均逐边、逐端口比较。命题允许候选消失、有效候选全空和正时延反馈；原始缓存列表、激活集合、消息条数与 Full 调用数可以变化。连续依赖上述读出的标量目标也连续。

### 5.2 单位输入的硬化连续性

先独立考察硬运行。外部载荷取 $(1,z)$，这里限制的是强度坐标，内容 $z$ 可为任意给定的有限向量。更早的硬发送强度为 $0/1$ 时，当前接收总强度是非负整数；$1\le\gamma_v\le\gamma_{\max}$ 使

$$
\mu_v=\min(1,\gamma_v r_v)\in\{0,1\},\qquad
c_v^{\mathrm{hard}}=\mu_v\mathbf1[v\in A]\in\{0,1\}.
$$

按逻辑时间归纳，硬运行的发送、上界和写入权重均为二元值。此步只使用硬函数与单位外部强度。

再看一次选择的极限问题。令上界趋于二元值，正极限上界处的评分收敛，消失候选评分有界。以下条件保证线性目标在极限可行集上有唯一最优解，且恰为式 (14)：

- 有效候选至多一个时，无须评分条件。
- $k_j=1$ 且有效候选至少两个时，最高分与次高分严格分离。
- $k_j>1$ 且有效候选至少两个时，各有效调整后评分 $t_v\ne0$。正评分数超过 $k_j$ 时，第 $k_j$ 名与下一名严格分离；没有正评分时，最高分与次高分严格分离。

正则有界且乘以趋零温度，故在这些条件下软解趋于唯一硬解。可行集随上界变化的论证及各情形的唯一性见附录 A.4。

> [!theorem] 命题 3：单位输入的硬化连续性
> 固定有限正时延图、有限切面、全部模型参数与配置，以及单位强度外部输入 $(1,z)$，从空缓存开始。若硬端点运行的每次选择均满足上述对应情形的评分条件，则软规格 $\tau_{\mathrm{soft}}\downarrow0$ 的消息、有效缓存和连续读出投影收敛到硬规格。

证明按时间归纳：更早的软发送收敛，当前接收、有效记忆、上界与相关评分随之收敛；端点是刚才独立确定的硬运行，其上界二元，局部唯一性再给出控制量收敛。逐次推进即可得到整网结论，正式证明见附录 A.7。

软运行中的上界可以是小数，它们与消息、状态一起随温度变化。上述结论对满足条件的每个固定输入及有限切面成立，涵盖全连接、稀疏 HB、多区域与正时延反馈图。参数和配置随训练步骤变化时，所得轨迹还包含这些额外变化。

### 5.3 端点条件与反例

**选择边界。** 二元上界、$t=(3,3,1)$、$k=2$ 给出唯一门控 $(1,1,0)$；相等评分位于已经选中的集合内部。改为 $t=(3,1,1)$ 时，预算边界有平票，线性最优解可在后两个坐标分配。固定 ID 决定硬函数的一个结果，软极限由正则及趋近方式决定。

最小的传播例子是两个单位上界节点、相同评分、$k=1$ 与 quad。每个正温度均有 $c=(1/2,1/2)$；各自再连向一个独立区域的单节点，固定增益为 $1$，下游上界与发送均为 $1/2$。这是合法的两层 SettleGraph，说明单位输入的硬运行二元性还需配合评分条件，才能推出软运行收敛到该端点。

**阈值边界。** 取二元上界、$k=2$ 与 quad，局部评分列 $t^\tau=(1,\tau/2)$ 在 $0<\tau<1$ 时给出 $c^\tau=(1,1/2)$。端点评分为 $(1,0)$，硬函数给出 $(1,0)$。这里缺少阈值间隔，极限线性问题有多个最优解。

**固定小数上界。** 取 $\mu=(0.9,0.8)$、$t=(-2,-1)$、$k=1$。软可行域要求总质量为 $1$，唯一线性最优解为 $(0.2,0.8)$；硬函数保留最高分候选，给出 $(0,0.8)$。固定这种上界求局部极限，与命题 3 中上界随整网软运行趋于二元端点，是两种不同的比较。

### 5.4 有限正温度的精确硬门控

固定二元上界和满足 §5.2 条件的评分。有效候选至多一个时，可行集为单点，全部正则在任意正温度都给出硬门控。其余情况下，quad 的充分温度界为：

| 情形 | 足够的温度界 |
|---|---|
| $k=1$，或全部有效评分为负 | $\tau\le t_{(1)}-t_{(2)}$ |
| $k>1$，正评分数在 $1$ 至 $k$ 之间 | $\tau\le\min_{t_v>0}t_v$ |
| 正评分数超过 $k$ | $\tau\le t_{(k)}-t_{(k+1)}$ |

$t_{(i)}$ 表示按降序排列的调整后评分。ent 在固定 $\alpha>1$ 时也有充分小的正温度区间，精确产生同一硬门控；其零与单位响应阈值见附录 A.4。bern 与 Shannon 在正温度保持有效坐标为正，硬端点排除候选时通过极限达到零值。

这些界把所需温度与相关评分间隔联系起来。共同缩放 $t$ 与 $\tau$ 保持式 (11) 的解；固定阈值而只缩放原始 $s$，则还改变其相对阈值。整网比较采用 §5.2 的时间归纳，局部温度界用于已固定的评分与上界。

## 6. 局部批量契约

### 6.1 完整驱动纤维上的联合求值

固定区域 $j$ 与有限逻辑时间窗口 $I=[b,c)$，给定空初态可达运行在 $b$ 的区域节点状态，以及窗口内**区域全部节点、全部时间的完整输入纤维**，包括空纤维。边界缓存的写入时间均小于 $b$；关闭证据保证这些驱动纤维完整。区域历史是单点。

1. 对非空纤维应用已绑定的式 (3) 或 (3a)，对正接收计算式 (5) 的 KV、摘要特征与权重。
2. 按原始时间构造新增条目的前缀及时间窗口。正接收时过滤并追加，零接收或空纤维时保留原序列，精确恢复各时刻的保存状态。式 (7) 可用窗口和与衰减扫描；式 (7a) 可将各次 Read 查询在各自因果窗口上联合求值。
3. Read 产生所选类型的描述量，按区域与时间取得独立或区域匹配评分，再求式 (11) 或 (14)，返回激活、控制和式 (15) 的快照、下一状态。区域 query 只汇集同一时刻的完整候选。
4. 对每节点收集正式 Full 的时间集合 $\Theta$，将正门控查询组成时间批；每个查询只读取其快照内的因果时间窗口。全候选参考规格还返回全部廉价零 Full 及零消息。

前两步的写入不依赖本地选择或 Full，因此这些前缀恰好等于逐次递归状态；第三步得到同样的描述量与选择。它们构成 [[timed-dag-chunk-prefill-learning-note#3.5 区域控制—状态契约|区域控制—状态契约]] 的见证。第四步在确定快照上求同一个 Full，再按边和端口展开，构成 [[timed-dag-chunk-prefill-learning-note#3.2 逐坐标完整输出契约|逐节点 Full 契约]] 的见证。分别记为

$$
\begin{aligned}
\operatorname{BatchRegionState}^{\mathrm{KV}}_{j,I}
 &=\operatorname{RefRegionState}_{j,I},\\
\operatorname{BatchFull}^{\mathrm{KV}}_{v,\Theta}
 &=\operatorname{RefBlock}_{K^F_{v,\Theta}}.
\end{aligned}
\tag{21}
$$

第一式返回实际 $P/S/U$ 支持集、全部作用值和右边界状态；第二式返回全部正式 $F$ 值及经 $\operatorname{ExpandFull}$ 展开的消息、输出，输入输出类型均沿用正典。

这些契约何时可调用、各层级可得到怎样的批次，由 [[timed-dag-chunk-prefill-learning-note|分块预填充教材]]、[[settlegraph-learning-note#11. 节点级时间批的含义|SettleGraph]] 与 [[positive-delay-graph-finite-cut-learning-note|正时延图教材]] 给出。契约确定联合求值的数值与记录，工作量见第 7 节。

### 6.2 位置配置与分段继续

固定位置配置后，各局部函数仍只读取既定自变量。切面继续沿用正典的

$$
Q_b=(b,(q_v^b)_v,(y_j^b)_j,W_b),
\qquad
\Phi_{a,b}(Q_a,E_{[a,b)})=(\mathcal U_{[a,b)},Q_b).
$$

由相同 $Q_b$ 开始下一段，条目保留原始 $\xi_i$，新作用沿用全局 $\theta$，所以位置、遮罩、摘要及 Attention 与整段求值相同。精确区间记录仍按 $\odot_b$ 粘合。任意有限次切分，包括有空档的区间，均得到同一完整记录和右边界状态。

本函数族的 $y_j^b=*$；一般切面的 $W_b$ 仍须保留。SettleGraph 的位置边界 $b=Dt$ 满足 $W_b=\varnothing$，可由该位置及各节点状态继续。分段边界不重置时间或位置函数。可并行的批次由图与可用联合契约确定。

## 7. 局部工作与全图成本

聚合、KV 写入和 Read 在候选上执行，Full 在激活者上执行。Read 的摘要与内容检索具有各自的工作量。下表 $m$ 为本次入消息数，$N$ 为有效 KV 项数。

| 工作 | 典型量级与条件 |
|---|---|
| 接收聚合 | $m$ 条消息的共享式 (3) 约 $O(mp_a d+p_a d)$；式 (3a) 逐消息采用自己的绑定 |
| KV 与摘要投影 | 独立求值约 $O(d^2+dr_a+dd_s)$ |
| 时间摘要 | 朴素扫描 $O(Nd_s)$；窗口和与衰减累计可减少重复扫描 |
| 局部评分 | 拼接族约 $O(d_r(d+d_s))$；分组匹配族约 $O(d_r(d+d_s+d_{\mathrm{sel}}))$，含三组编码与门控残差 |
| 发送增益 | 固定增益为标量运算；上下文增益约 $O(d_r(d+d_s))$，特征可与局部评分共用 |
| 内容检索 | query 投影 $O(dd_s)$，已投影记忆上的检索 $O(Nd_s)$；直接重投影记忆另需 $O(Ndd_s)$，保存辅助投影则将此工作移到写入并增加存储 |
| 区域 Attention 描述量 | 每候选约 $O(d_{\mathrm{sel}}(d+d_s))$，局部评分残差按所用配置另计 |
| 区域 query 与匹配 | 每次选择约 $O(\lvert C\rvert d_{\mathrm{sel}}+d_{\mathrm{sel}}^2)$ |
| 预算分配 | 二次族断点排序为 $O(\lvert C\rvert\log\lvert C\rvert)$；通用标量求根每次 $O(\lvert C\rvert)$，另计迭代与精度；隐式反向为 $O(\lvert C\rvert)$ |
| 正门控 Full | $O(d^2+dd_f+Nd)$，$N$ 为当前有效 KV 项数 |
| 每节点缓存 | 有限窗口为 $O(T_v(2d+d_s))$；全历史在切面 $B$ 前至多 $B$ 项，另有时间、权重及可选辅助投影 |

相同来源类别与载荷的多重集，加相同聚合参数，才保证相同的 $(r,u)$。满足此条件时可共享聚合与 KV 基座投影；相同参数面对不同邻域时，仍须求不同的聚合与投影。HB 中的参数共享一般只减少参数和便于批量求值，不能自动把全区域准备合为一次。共享表示还须恢复各节点的确切状态。

记 $\mathcal E_C,\mathcal E_A$ 为一段运行内候选、激活者的节点—时间坐标，$\mathcal E_S$ 为实际区域选择坐标，$\mathcal M$ 为发出的内部消息。按不重复归属的工作量或累计执行时间，全图账本为

$$
\begin{aligned}
\mathcal W={}&\sum_{(v,\theta)\in\mathcal E_C}
 (C_{v,\theta}^{\mathrm{Agg}}+C_{v,\theta}^{\mathrm{KV}}+C_{v,\theta}^{\mathrm{Read}})
 +\sum_{(j,\theta)\in\mathcal E_S}C_{j,\theta}^{\mathrm{Sel}}\\
 &+\sum_{(v,\theta)\in\mathcal E_A}C_{v,\theta}^{\mathrm{Full}}
 +\sum_{m\in\mathcal M}C_m^{\mathrm{msg}}.
\end{aligned}
$$

这里各 $C$ 是声明的工作代价，共享计算计一次，缓存读写与输出汇集计入相应项。该和式给出加性工作量；并行执行的跨度还依赖计算之间的偏序。

上游不发送可使下游整个输入纤维缺席，进而移除相应准备、选择、Full 与消息。候选覆盖由出度、父邻域重叠和外部注入共同确定。[全连接实例](weighted-kv-layered-example.md#4-整窗口求值与架构成本)与 [HB 实例](weighted-kv-hb-lattice-example.md#4-候选传播与全图成本)给出具体计数。

## 附录 A：数值连续性的正式证明

### A.1 比较域与时间槽

固定有限正时延图、区域和端口、来源映射、全部模型参数与配置，以及整数切面 $B>0$。窗口允许 $T_v=\infty$，位置函数和频率固定。输入在 $[0,B)$ 内取自一个固定有限槽集合；各槽可有值或缺席。考虑从空缓存开始的一列运行，外部载荷内容一致有界，式 (2) 的槽投影收敛到某个合法端点输入。平滑参数的变化在相应命题中另行指定。

内部消息按边身份和发送时间对齐，输出按端口和输出时间对齐，写入按节点和原始时间对齐。缺席槽的投影取零。有限图、有限切面与正时延保证潜在槽只有有限个，包括切面前已发送而尚未到达的消息。以下收敛均为这些有限维投影的通常收敛。

同一时间的所有候选在区域内共同选择。证明中可将缺席节点补成 $\mu_v=0,c_v=0$，不增加规范作用；补入坐标的描述特征任取有界值，其对区域 query 的贡献为零；预算比较中零上界坐标的评分也可任取有界值。缓存投影始终在当前比较时刻使用式 (20)。

### A.2 有界性引理

**引理 A.1。** 在 A.1 的条件下，切面以前所有实际聚合内容、KV 内容、摘要、评分与 Full 内容一致有界。该界可选为与正温度无关。

**证明。** 对任意 $x$，$\|\mathcal N_p(x)\|_2\le\sqrt p$。因此式 (5) 的 $k,\nu,p$ 具有固定界，式 (3) 或 (3a) 的来源非线性项也有固定界。输入槽数有限、输入投影收敛，使外部有效强度一致有界；内部发送强度由 $0\le c_v\le1$ 控制。每个纤维的潜在原子数有限，故接收强度有界。

按逻辑时间归纳。给定此前发送内容的界，式 (3) 或 (3a) 的加权均值范数至多为本次输入内容范数的最大值，加来源项后仍有界。每节点在 $[0,B)$ 至多写 $B$ 项，$0\le w_i\le1$，式 (7) 的摘要有界。式 (7a) 的投影、固定时间槽上的旋转和 logit 有界，检索结果为有界 value 的凸组合乘以至多为 $1$ 的尺度，故同样有界；式 (8) 与 (8a) 的局部评分由有界输入、固定归一化和有限参数保持有界。式 (9) 的两种增益均处于固定区间 $[1,\gamma_{\max}]$。式 (9a) 的特征与 key 有界，式 (9b) 的加权汇集范数不超过特征范数的最大值，经过固定连续网络后，区域 query 与全部评分也有界。旋转矩阵范数为 $1$；有限个时间槽的位置值与距离偏置有限，所以式 (16) 的有效 logit 一致有界。Attention 是有界 value 的凸组合乘 $a(W)\le1$，仍有界。式 (17) 的前馈分支输入经归一化有界，故 Full 内容有界，完成归纳。正时延使这一步只使用更早时间的界。$\square$

本引理只给出固定有限切面上的界，不断言界随 $B$ 增大仍一致。

### A.3 聚合、写入与读取引理

**引理 A.2。** 在 A.2 的有界范围内，有下列结论：

1. 输入槽的式 (2) 投影收敛时，$r$ 收敛；若极限 $r^*>0$，则 $u\to u^*$。
2. 输入槽投影与旧缓存的有效投影均收敛时，接收后的有效投影也收敛。此结论包含 $r^*=0$ 和纤维缺席。
3. 有效缓存投影收敛时，式 (7) 的摘要收敛；若同时 $u\to u^*$，则式 (7a)、(16)--(17) 的检索、读取与内容函数收敛。正极限接收处的局部描述特征因此收敛，其余处保持有界。
4. 在同一区域所有候选同时满足以上条件时，式 (9b) 的 query 收敛，正极限上界处的最终评分收敛，其余评分保持有界。

**证明。** 各槽有效强度及强度乘内容均收敛，故 $r$ 及加权内容和收敛。正极限强度槽的内容可从这两个坐标相除恢复；零极限强度槽对有界来源非线性项的加权贡献趋零。若 $r^*>0$，式 (3) 或 (3a) 的加权分子收敛，分母趋于正数，得到第一项。

正极限接收处，式 (5) 的投影函数和 $w(r)$ 连续。若 $r\to0$，其有界性给出

$$
(w(r),w(r)k_v(u),w(r)\nu_v(u),w(r)p_v(u))\longrightarrow0.
$$

旧槽的遮罩按固定 $\xi$ 取值；式 (6) 清掉的条目在当前时刻的有效投影已经为零。可达旧条目均写于当前时刻以前，以后遮罩也不会从零变回一。因此零接收时保留旧列表与微弱正接收时清理旧列表具有相同的投影极限，并可继续传到下一个比较时刻，得到第二项。

式 (7) 是有效 $w,wp$ 坐标乘固定衰减后求和，再除以至少为 $1$ 的连续分母，故摘要连续。对 Attention，记 $\widehat w_i=\chi_{v,\theta}(\xi_i)w_i$。若极限 $W^*>0$，每个正极限权重槽的 $k_i,\nu_i$ 可由有效加权坐标除以权重恢复；其 logit 与 value 收敛。零极限权重槽的 $\widehat w_i e^{\ell_{i,h}}$ 与 $\widehat w_i e^{\ell_{i,h}}\nu_{i,h}$ 趋零，因为引理 A.1 给出一致界。分母极限严格为正，故商收敛。若 $W\to0$，则

$$
\|R_{v,h}\|_2\le\min(1,W)\max_i\|\nu_{i,h}\|_2\longrightarrow0,
$$

其中空列表的上界取零。式 (7a) 的 $W_a$ 使用固定时间衰减，投影与旋转连续且有界，故逐项重复上述商与零总权重论证，得到检索连续性。再应用式 (17)、(8)、(8a)、(9a) 的连续运算，得到第三项。正极限接收处，两种增益连续，故发送上界收敛；零极限处由 $0\le\mu_v\le\gamma_{\max}(r_v)_+$ 同样得到上界收敛，即使裸内容没有唯一极限。

最后在区域中将缺席候选补成零上界。若 $\mu_v^*>0$，则 $r_v^*>0$，其 $x_v^{\mathrm{sel}},K_v^{\mathrm{sel}},s_v^{\mathrm{loc}}$ 收敛；若 $\mu_v\to0$，有界性给出 $\mu_v x_v^{\mathrm{sel}}\to0$。式 (9b) 的分子和分母因此收敛，分母至少为 $1$，故 query 收敛。正极限上界候选的匹配评分随之收敛，其余评分由引理 A.1 保持有界，得到第四项。$\square$

### A.4 带上下质量界的选择引理

**引理 A.3。** 固定含 $m$ 个坐标的有限候选集、整数预算 $k\ge1$ 及式 (11a) 的一个正则族；entmax 的 $\alpha$ 固定。设 $\mu^{(n)}\to\mu^*$，各上界属于 $[0,1]$，评分 $t^{(n)}$ 一致有界，且在 $\mu_v^*>0$ 的坐标上收敛到 $t_v^*$。令 $c^{(n)}$ 是式 (11) 在温度 $\tau_n>0$ 下的解。

- 若 $\tau_n\to\tau_*>0$，则 $c^{(n)}$ 收敛到相应正温度解。
- 若 $\tau_n\to0$，且极限线性问题的最优解唯一，则 $c^{(n)}$ 收敛到该唯一解。

**证明。** 记

$$
M(\mu)=\sum_v\mu_v,\qquad b(\mu)=\min(1,M(\mu)),
\qquad F(\mu)=\{c:0\le c\le\mu,\ b(\mu)\le\textstyle\sum_v c_v\le k\}.
$$

所有解属于紧集 $[0,1]^m$。若 $c^{(n_l)}\to\bar c$，由 $b$ 连续和闭约束得 $\bar c\in F(\mu^*)$。反之，对任意 $d\in F(\mu^*)$，先取 $a_v^{(n)}=\min(d_v,\mu_v^{(n)})$。若 $\sum_va_v^{(n)}\ge b(\mu^{(n)})$，令 $d^{(n)}=a^{(n)}$；否则令

$$
\begin{aligned}
\delta_n&=b(\mu^{(n)})-\sum_va_v^{(n)},\qquad
R_n=\sum_v(\mu_v^{(n)}-a_v^{(n)}),\\
d_v^{(n)}&=a_v^{(n)}+
 \frac{\delta_n}{R_n}(\mu_v^{(n)}-a_v^{(n)}).
\end{aligned}
$$

后一分支有 $0<\delta_n\le R_n$，修正后总质量为 $b(\mu^{(n)})\le k$，故 $d^{(n)}\in F(\mu^{(n)})$。又因 $a^{(n)}\to d$ 且 $\sum_vd_v\ge b(\mu^*)$，修正量 $\delta_n\to0$，从而 $d^{(n)}\to d$。

令 $I_0=\{v:\mu_v^*=0\}$，将这些坐标的评分改成零，得到 $\widetilde t^{(n)}$。若原评分绝对值至多为 $M$，这个替换在整个 $F(\mu^{(n)})$ 上改变目标至多

$$
\epsilon_n=M\sum_{v\in I_0}\mu_v^{(n)}\longrightarrow0.
$$

在紧集 $\mathcal D=\{(\mu,c):0\le c\le\mu\le1\}$ 上，三种正则都联合连续且有界。二次与 entmax 项直接由各坐标函数的连续性得到。二元熵在 $\mu_v>0$ 处连续；趋零上界处有

$$
0\le\mu_v h_B(c_v/\mu_v)\le\mu_v\log2\longrightarrow0,
$$

故按零延拓也连续。固定正温度时，目标对有效坐标严格凹；零上界坐标已被约束固定，所以最优解唯一。

记 $\widetilde f_n(c)=\widetilde t^{(n)}\cdot c+\tau_nR(c;\mu^{(n)})$。沿上述可行收敛子列，正温度极限由联合连续性取得；零温度极限中，有界正则乘 $\tau_n$ 趋零。对可行恢复列 $d^{(n)}$ 同理。最优性给出

$$
\widetilde f_n(c^{(n)})
\ge\widetilde f_n(d^{(n)})-2\epsilon_n.
$$

令 $f_*(c)=t^*\cdot c+\tau_*R(c;\mu^*)$，零温情形取 $\tau_*=0$。沿上述子列取极限，得到 $f_*(\bar c)\ge f_*(d)$。因此每个聚点都是极限最优解。正温度下严格凹性给出唯一性；零温度下使用假定的唯一性。所有聚点相同，整列收敛。$\square$

**硬端点的唯一性。** 若 $\mu_v^*\in\{0,1\}$，零上界坐标固定为零。有效候选为空时，可行集只含零向量；只有一个时，质量下限强制该坐标为 $1$。以下设有效候选至少两个。

$k=1$ 时总质量为 $1$，最高分唯一便使全部质量集中于该坐标。$k>1$ 时，按第 5.2 节假设所有有效 $t_v^*\ne0$。没有正评分时，负系数使总质量恰为下限 $1$；最高分唯一再确定其分配。有正评分时，负评分坐标取零：将其质量转向未满的正评分坐标，或在正评分全满后去掉负评分质量，都严格提高目标且保持可行。正评分数不超过 $k$ 时，各正评分均取 $1$；超过 $k$ 时，第 $k$ 名的严格间隔使质量恰分配给前 $k$ 个。各情形均给出式 (14) 的唯一门控。

**有限温度精确性。** 有效候选至多一个时，可行集是单点。其余先看二次族：$k=1$ 或无正评分时，取 $\lambda=t_{(2)}$ 与 $\tau\le t_{(1)}-t_{(2)}$，最高分坐标为 $1$，其余为零；$k=1$ 时上下质量界同时取等号，任意符号的 $\lambda$ 均可分解为非负的 $\lambda_U-\lambda_L$；无正评分且 $k>1$ 时，$\lambda<0$ 对应下限乘子。$k>1$ 且正评分数在 $1$ 至 $k$ 之间时，取 $\lambda=0$ 与 $\tau\le\min_{t_v>0}t_v$；超过 $k$ 时，取 $\lambda=t_{(k+1)}>0$ 与 $\tau\le t_{(k)}-t_{(k+1)}$。代入式 (12) 均得到硬门控并满足互补条件。

对 entmax 的固定 $1<\alpha\le2$，二元上界上的响应精确为 $1$ 和 $0$ 的充分必要条件分别为

$$
t_v-\lambda\ge\tau/\alpha,\qquad
t_v-\lambda\le-\tau/[\alpha(\alpha-1)].
$$

记 $a_\tau=\tau/\alpha$、$z_\tau=\tau/[\alpha(\alpha-1)]$。选取最高分一个时，可令 $\lambda=t_{(2)}+z_\tau$，并要求 $a_\tau+z_\tau\le t_{(1)}-t_{(2)}$；无正评分且 $k>1$ 时，再要求 $z_\tau<-t_{(2)}$，使下限乘子符号正确。正评分数超过 $k$ 时，同理用 $\lambda=t_{(k+1)}+z_\tau>0$ 与预算边界间隔。选取全部正评分且数量不超过 $k$ 时，取 $\lambda=0$，要求 $a_\tau\le\min_{t_v>0}t_v$，以及有负评分时 $z_\tau\le\min_{t_v<0}(-t_v)$。严格间隔保证这些条件在充分小的温度成立，式 (12) 给出唯一硬门控。

二元熵与 $\alpha=1$ 的响应在 $\mu_v>0$、有限乘子和正温度下严格为正，故无法精确排除有效候选。可行域单点等强制情形直接由约束处理；它们不影响引理的极限结论。

### A.5 性质 1 的证明

增加或删除零强度原子不改变式 (3) 或 (3a) 的加权和。已有正接收处的写入与局部描述保持；仅含零消息的纤维有 $r=0$，式 (6) 保持状态，式 (9) 给出 $\mu=0$。式 (7) 与 (7a) 的既有读取保持不变；式 (9b) 中零上界候选对 query 的分子、分母贡献均为零，其他候选的最终评分也保持。因此这类候选加入软优化时只增添强制为零的坐标，$M_j,b_j$ 均不变；加入硬排序时也不进入 $C_{\mathrm{eff}}$。其他候选的控制量与单点历史保持。

支持集规格在这些坐标不执行 Full；全候选参考规格按式 (18) 产生零载荷。沿正时延按时间归纳，这些额外零消息只会重复上述情形，不改变后续正强度计算和状态。时间、位置、窗口均不重排，故有效状态、式 (2) 的槽投影及式 (19) 的读出相同。额外候选与零 Full、消息、输出的存在身份可以不同。$\square$

### A.6 命题 2 的证明

令正温度固定或趋于正值。按 $\theta=0,\ldots,B-1$ 归纳，并在每个切面比较有效状态。初始状态为空。正时延使当前内部输入只来自已经比较的更早发送槽，结合外部输入假设，当前完整纤维的载荷投影收敛。由引理 A.2，接收后有效缓存收敛，发送上界收敛，正极限接收处评分收敛，其余评分由引理 A.1 保持有界。缺席候选按 A.1 补成零上界，有效候选全空的情形也包含在内。

引理 A.3 给出控制量收敛。若端点 $c_v^*>0$，由 $c_v\le\mu_v\le\gamma_{\max}(r_v)_+$ 得到 $r_v^*>0$，聚合内容及 Full 内容收敛。若 $c_v^*=0$，实际 Full 内容保持有界，所以

$$
\pi_P(\operatorname{EmitValue}_v)
=(c_v,c_vG_v)\longrightarrow0;
$$

未调用 Full 的槽同样按零比较。广播逐边、逐端口保持这一结论。BO 与默认 Next 将接收后的状态直接采用，引理 A.2 的固定遮罩论证又给出下一切面的有效状态收敛，完成归纳。稀疏空档只传递原状态并推进比较时刻。

最后，式 (19) 的分子是消息投影中内容贡献的有限和，分母是有效强度和与 $1$ 的最大值，始终为正，故所有切面以前有限槽的读出收敛。$\square$

### A.7 命题 3 的证明

在硬端点运行中，初始无内部消息，外部强度为 $1$。若更早发送强度均为 $0/1$，当前总强度便为非负整数；两种增益均满足 $\gamma_v^{\mathfrak g_j}\ge1$，使 $\mu_v\in\{0,1\}$，式 (14) 再发送 $0/1$。按时间归纳，所有硬端点上界与非零写入权重均为二元值。

现在让软温度趋零，按 A.6 的同一归纳比较软运行与硬端点。聚合、缓存及正接收处评分的收敛仍由引理 A.2 给出。每次硬端点选择满足第 5.2 节对应情形的评分条件，因此 A.4 给出唯一线性最优解，恰为该次硬门控；引理 A.3 的零温度结论给出软控制量收敛。后续发送和状态采用与 A.6 相同，故消息、有效缓存及连续读出收敛。$\square$

这些命题允许有限切面内的正时延反馈，但不推出无限时域稳定性、梯度连续性或训练收敛。位置函数、频率、离散时间槽和窗口固定，是上述比较的共同前提。

## 附录 S：计算表示与数学对象

### S.1 状态、旋转与解码

沿用正典的“表示解码，再遗忘辅助坐标”两步关系。共享 KV 存储和不可变窗口视图可以表示式 (4) 的序列。设表示空间为 $\widehat S_v$、解码函数为 $\operatorname{decode}_v:\widehat S_v\to S_v$，每个 Full 视图须满足 $\operatorname{decode}_v(\widehat q^{\mathrm{cmp}}_{v,\theta})=q^{\mathrm{cmp}}_{v,\theta}$。边界缓存作为左前缀，新增条目按时间追加；视图还需保留本规格清理后的确切序列范围，包括尚未触发清理时的过期条目身份。

联合求值可先返回这种表示，经固定 Decode 得到数学值记录，再由 $\Pi_K^{\mathrm{blk}}$ 删除辅助字段。解码忠实恢复已经表示的序列、控制和快照，不调用参考递归补写或修补结果。按式 (20) 比较有效状态允许某些原始列表不同，不可据此声称同一规格的完整记录相等。进一步压缩或提前清理若不能解码为原状态，就需另行声明所比较的投影。

实现可保存原始 key，也可保存 $\widehat k_{i,h}=\operatorname{Rot}_{v,h}(\operatorname{Pos}_v(\xi_i))k_{i,h}$。后一表示经同一配置的逆旋转恢复原始 key；每项仍须保留 $\xi_i$，用于窗口、摘要和解码。Query 在自己的处理时间旋转，已旋转 key 避免重复旋转。节点、时间和配置身份共同确定旋转含义。

跨 chunk 继续须保存可恢复的 $Q_b$，并使用同一参数与位置配置。更改频率、坐标尺度或局部函数后，旧缓存通常已包含旧计算的结果；仅重旋转 key 不足以取得新规格从头运行的状态。继续、重算或显式状态转换应各自声明比较关系。

式 (7a) 的检索投影须从原始 key 取得，再施加 Read 自己的旋转；Full 的已旋转 key 通常不能直接代入该投影。可额外保存检索 key/value 投影，作为固定参数下的辅助表示，主状态仍须按声明解码。

式 (16) 可对正有效权重使用 $\ell_{i,h}+\log\widehat w_i$ 的稳定 softmax，再乘 $a(W)$；零权重遮罩，空记忆直接返回零。式 (7a) 同样可在正权重上采用稳定加权 softmax，并乘 $\min(1,W_a)$。KV 内容与权重分开保存，不以微小权重作除法恢复内容。有限精度下的下溢、近零阈值裁剪及替代反向需要另行声明；它们不能直接冒充本文的精确零规则或数学连续性结论。

### S.2 配置与数学规格

组合配置逐区域选择聚合共享方式、记忆描述、Read 与 SelStep 的成对绑定、节点宽度、窗口、位置函数，以及 Read 和 Full 的旋转参数，再绑定图、时间、来源及读出。宽度、坐标配对、预算和端口类型检查通过后，得到确定的参数空间和状态空间；给定参数值、初态和输入，参考递归唯一确定前向记录。

局部选项可按下表直接命名，实现名称与数学绑定一一对应：

| 配置键 | 数学对象 | 取值及定义 |
|---|---|---|
| memory | $\mathfrak m_j$ | sum：式 (7)；qry：式 (7a) |
| local_score | $\mathfrak f_j$ | cat：式 (8)；match：式 (8a) |
| region_score | $\mathfrak s_j$ | ind 或 att：第 2.3 节的 Describe 与 SelStep 评分 |
| send_gain | $\mathfrak g_j$ | fixed 或 context：式 (9)，另绑定 gamma_max 与相应参数 |
| budget_family | $\mathfrak b_j$ | quad、bern 或 ent：式 (11a) |
| ent_alpha | $\alpha_j^{\mathrm{ent}}$ | ent 使用的固定形状参数，范围 $[1,2]$ |
| selection_mode | 所用软／硬函数 | soft：式 (11)--(13)；hard：式 (14)，另声明全候选参考规格时的记录规则 |

基线依次为 sum、cat、ind、fixed、quad。每个配置确定参数空间、状态空间与相应前向函数，各族的反向目标见 S.3。相容组件可通过上述名称组合。

更改评分、正则、增益或位置配置，可能改变参数形状、前向函数与历史缓存；形状相同也不保证 checkpoint 的数值兼容。软转硬按第 5.2 节比较；其他切换的状态转换需另行给出。

异构组合可给其他区域绑定不同的状态、Upd、Read 和 Full，但须先完整定义该函数族及其组合条件。本文证明覆盖所定义的 KV 函数；循环记忆需要自己的零消息、状态连续性及批量求值论证。正时延反馈图还须由任务声明有限切面与读出时刻。

### S.3 预算分配的求解与反向

**前向。** 输入为有限向量 $(t,\mu)$、$k,\tau>0$ 及固定正则配置，输出为式 (11) 的唯一门控。先计算 $M=\sum\mu,b=\min(1,M)$；$M\le1$ 时直接返回 $c=\mu$，包括空集、全零上界与单个有效候选。这个分支也避免用有限二元熵乘子逼近被约束强制的上界。

$M>1$ 时先求 $\lambda=0$ 的响应。质量位于 $[b,k]$ 时直接返回；过大或过小时，分别求总质量 $B=k$ 或 $B=b$ 的根。此时必有 $0<B<M$。令 $q=B/M\in(0,1)$，对有效候选定义满足 $g_{\mathfrak b}(x_v,\mu_v;\tau)=q\mu_v$ 的值：

| 正则 | $x_v$ |
|---|---|
| quad | $\tau q\mu_v$ |
| bern | $\tau\log(q/(1-q))$ |
| ent，$\alpha=1$ | $\tau[1+\log(q\mu_v)]$ |
| ent，$\alpha>1$ | $\tau[(q\mu_v)^{\alpha-1}-1/\alpha]/(\alpha-1)$ |

取

$$
\lambda_{\mathrm{lo}}=\min_{v:\mu_v>0}(t_v-x_v),\qquad
\lambda_{\mathrm{hi}}=\max_{v:\mu_v>0}(t_v-x_v).
$$

响应单调给出 $S(\lambda_{\mathrm{lo}})\ge B\ge S(\lambda_{\mathrm{hi}})$。依次二分即可保留含根区间；也可取 Newton 步 $\lambda+(S(\lambda)-B)/\sum_v a_v$，仅在斜率非零且试探点落入保留区间时采用，否则退回二分。上限根应有非负乘子，下限根应有非正乘子；根区间可与对应半轴相交。平坦区间上乘子可能不唯一，门控仍唯一。

若初始区间宽度为 $D>0$，达到乘子区间宽度 $\varepsilon_\lambda$ 的二分工作量为 $O(|C|\max(1,\log_2(D/\varepsilon_\lambda)))$。若两端相同则直接求值。质量残差与坐标误差另用斜率界或区间两端的门控差判断；温度越小，同样的乘子误差可能导致更大门控误差。停止条件同时核对可行性与最优性残差，数值实现报告实际迭代和误差，不预设固定次数总能满足精度。

二次族还能按 $t_v-\tau\mu_v,t_v$ 排序并扫描分段，工作量为 $O(|C|\log|C|)$。在自由集 $\mathcal F=\{v:0<c_v<\mu_v\}$、上界集 $\mathcal U=\{v:c_v=\mu_v>0\}$ 与质量边界 $B$ 固定时，

$$
\lambda=\frac{\sum_{v\in\mathcal F}t_v+
 \tau\sum_{v\in\mathcal U}\mu_v-\tau B}{|\mathcal F|}
\qquad(\mathcal F\ne\varnothing).
$$

候选解须位于对应分段并满足互补条件；$\mathcal F=\varnothing$ 时直接验证饱和门控。ent 的 $\alpha=2$ 可按式 (12a) 移位后用同一算法。其他族均可采用上述标量求根；无需通用高维优化器。

**隐式反向。** 以下在固定约束分支与光滑区间内求导，$\tau,\alpha$ 固定。设 $x_v=t_v-\lambda$，定义 $a_v=\partial g/\partial x_v$、$e_v=\partial g/\partial\mu_v$，后者保持 $x_v$ 不变：

| 坐标状态 | $a_v$ | $e_v$ |
|---|---|---|
| quad，自由 | $1/\tau$ | $0$ |
| ent，自由 | $c_v^{2-\alpha}/\tau$；$\alpha=1$ 时为 $c_v/\tau$ | $0$ |
| bern，$p_v^{\mathrm{occ}}=c_v/\mu_v\in(0,1)$ | $\mu_vp_v^{\mathrm{occ}}(1-p_v^{\mathrm{occ}})/\tau$ | $p_v^{\mathrm{occ}}$ |
| quad 或 ent，上界饱和 | $0$ | $1$ |
| quad 或 ent，零饱和 | $0$ | $0$ |

零上界坐标作为强制零处理，是否向正上界移动属于边界约定。若总质量固定在 $B$，且 $A_0=\sum_v a_v>0$，微分约束给出

$$
d\lambda=\frac{\sum_v a_v\,dt_v+\sum_v e_v\,d\mu_v-dB}{A_0},
\qquad
dc_v=a_v(dt_v-d\lambda)+e_v\,d\mu_v.
$$

令上游梯度为 $g_v^{\mathcal L}=\partial\mathcal L/\partial c_v$，并记
$\bar g=\sum_v a_vg_v^{\mathcal L}/A_0$。向量—Jacobian 乘积为

$$
\frac{\partial\mathcal L}{\partial t_v}
 =a_v(g_v^{\mathcal L}-\bar g),\qquad
\frac{\partial\mathcal L}{\partial\mu_v}
 =e_v(g_v^{\mathcal L}-\bar g)+
   \bar g\,\frac{\partial B}{\partial\mu_v}.
$$

本文 $M>1$ 时的边界是常数 $B=1$ 或 $k$，故最后一项为零。二次族的评分自由子块恢复
$\tau^{-1}(I-\mathbf1\mathbf1^\top/|\mathcal F|)$；单个自由坐标且总质量固定时，该评分导数为零。若两质量界均松弛，则 $\lambda=0$ 固定，直接使用 $dc_v=a_vdt_v+e_vd\mu_v$。若 $M<1$，直接由 $c=\mu$ 得到零评分 Jacobian 和恒等上界 Jacobian。

当 $A_0=0$ 时不得除以零；严格饱和区内评分导数为零，上界坐标直接沿 $c_v=\mu_v$ 求导。若扰动使质量边界与饱和模式无法同时保持，则已位于分支边界，应采用声明的单侧或广义导数。$M=1$、精确断点、质量界松紧交界及增益的 $\min$ 边界也须单独处理。硬规格若继续训练，其替代梯度或探索另行定义。

反向只需保存门控、分支及必要的响应统计量，工作量为 $O(|C|)$，不必保存二分或 Newton 轨迹。这里的目标是精确最优解映射的导数；有限精度求根后代入会产生相应误差。若改为对有限次迭代本身自动求导，则应声明该不同的反向目标。完整梯度还须沿 $t=s-\eta$、上界、区域 query、keys、局部评分和记忆读取回传。若训练温度，在固定 $x,\mu$ 处有 $\partial g/\partial\tau=-a_vx_v/\tau$，再按同一质量约束修正；本文未定义训练 $\alpha$ 的反向。

**数值表示。** sigmoid 使用稳定形式；指数响应先在对数域与上界比较，饱和时直接返回原上界，避免溢出及指数还原上界的舍入误差。$\alpha$ 接近 $1$ 时，逆响应可将分子写为 $\operatorname{expm1}((\alpha-1)\log c)+(\alpha-1)/\alpha$，再除以 $\alpha-1$；正响应可在正底数上使用 log1p。计算中区分数学零、下溢零和人为裁剪零。极小 $a_v$ 与低温自由区具有不同的数值条件，精度对应见 [实现核对](weighted-kv-implementation-checks.md)。
