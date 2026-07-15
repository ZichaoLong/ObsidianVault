---
type: note
status: draft
cssclasses:
  - textbook-math
tags:
  - tide
  - prefill-decode
  - sparse-routing
  - load-balancing
  - math
---

# 带令牌归属的一般有向无环图路由

> [!summary] 本页定位
> 本页研究一个固定周期 Tide 参考模型。令牌 $t$ 在绝对内部轮次 $Rt$ 注入；模型在 $R(t+1)$ 的固定边界产生第 $t$ 个读出；空间结构是任意有限的单位时延有向无环图，长路径消息可以跨边界继续传播。本文定义消息、状态、类型化逻辑事件、事件依赖有向无环图、三种同刻转移语义配置，以及绝对时间流式调度与节点拓扑序分块调度。

> [!important] 核心结论
> 等层有向无环图不是封闭有限精确分块执行的必要条件。对于本文固定周期、空间无环的严格语义配置，只要消息保留所有者、因果前沿和时间戳，每个可变状态都有唯一的持有节点，路由只沿空间有向无环图前进，并且每个节点都能把完整的带时间戳事件流精确转导为分块结果，就可以把绝对时间流式调度等价重排为节点拓扑序分块调度。该结论包含固定周期读出产物，但不自动给出低并行跨度，也尚未构造可直接接续解码的边界状态。

> [!warning] 正确性不自动推出高性能
> 本页主定理只证明流式调度与分块调度计算同一参考语义。它允许一个节点在一次调用中处理完整分块，并消除逐令牌的全局主机编排；但若节点局部转移本身含有顺序状态链或控制链，其内部并行跨度仍可随事件数线性增长。要达到 Transformer/Mamba 意义上的低令牌轴并行跨度，还需要因果注意力、扫描、分段批量处理、紧凑打包稀疏计算核等额外结构，并要求总事件数受控。

## 0. 术语、记号与固定周期外部接口

### 术语约定与中英文对照

本文保留部分已经成为模型、数学或实现接口名称的英文术语，但正文遵循以下约定：

1. 解释性正文原则上使用中文；中英文对应关系集中由下表给出，不要求正文反复并列英文。
2. 数学符号、公式字段、函数名、代码接口、固定缩写与模型专名可以保留英文。
3. 确有跨领域歧义时，可在首次出现处补写“中文（English）”，但英文不作为正文句法骨架。
4. `timestamp` 在英文对照或接口中始终写成一个单词，不使用 `time stamp`。
5. 下表中的“本文简写或说明”不是新的数学对象；严格含义仍由后续定义给出。

#### 时间与边界

| 中文 | 英文 | 本文简写或说明 |
| --- | --- | --- |
| 固定周期 | fixed period | 周期长度记为 $R$ |
| 内部轮次 | internal round | 指图内部推进一次的离散逻辑轮次 |
| 绝对内部轮次 | absolute internal round | 不随令牌重新从零计数 |
| 阶段 | phase | 同一内部轮次内按屏障、可见性和提交次序划分的分段 |
| 逻辑时间戳 | logical timestamp | 后文可简称时间戳；本文不用 `time stamp` |
| 注入 | injection / inject | 令牌进入输入节点的固定边界事件 |
| 读出 | readout | 从输出节点状态提取 $y_t$，不同于采样 |
| 采样 | sampling / sample | 根据读出选择下一个自回归令牌 |
| 边界 | boundary | 相邻固定周期之间的逻辑分界 |
| 墙钟时间 | wall-clock time | 真实设备时间，不等于逻辑时间 |
| 截止时间 | deadline | 墙钟性能约束，不属于参考语义本身 |

#### 事件、消息与状态

| 中文 | 英文 | 本文简写或说明 |
| --- | --- | --- |
| 逻辑事件 | logical event | 表示一次已经实例化的逻辑计算记录 |
| 事件头 | event header | 事件标识符、种类、位置、时间戳、支持集和因果前沿组成的元组 |
| 事件值 | event value | 记为 $\nu(e)$ |
| 事件依赖图 | event dependency graph | 若无环，则称为逻辑事件有向无环图 |
| 依赖边 | dependency edge | 表示直接的数据、状态或控制依赖 |
| 消息 | message | 沿空间边传播的带时间戳记录 |
| 收件箱 | inbox | 按节点、时间戳和所有者分桶的消息多重集 |
| 所有者 / 归属令牌 | owner / owner token | 表示当前轨迹归属于哪个令牌，不等于因果前沿 |
| 所有者支持集 | owner support | 事件当前联合处理或标识的所有者集合，记为支持集 |
| 因果前沿 | causal frontier | 语义对象的令牌前缀依赖上界；若对象是可选记录，则同时覆盖其存在性 |
| 状态 | state | 节点持有的持久数值状态 |
| 增广状态 | augmented state | 数值状态与因果前沿组成的有序对 |
| 提交 | commit | 使状态或输出对后继逻辑事件可见 |
| 提交轨迹 | commit trace | 按规范提交次序排列的状态版本 |
| 在途消息 | in-flight message | 已派发、但在当前边界尚未到达或消费的消息 |
| 来源信息 | provenance | 用于说明一个产物由哪些逻辑对象产生；比所有者和因果前沿更完整 |
| 路径谱系 | lineage | 某条消息或路由轨迹的确定性传播链标识 |
| 产物 | artifact | 正确性契约中必须比较的隐藏表示、状态、路由、消息和读出等结果 |
| 来源槽位 | birth slot | 注入时创建、随后只沿一条路径前进的守恒信号槽位 |
| 输出逻辑值 | logits | 归一化或采样之前的模型输出分数 |

#### 执行、调度与性能

| 中文 | 英文 | 本文简写或说明 |
| --- | --- | --- |
| 参考语义 | reference semantics | 被不同实现或调度共同保持的规范语义 |
| 转移 | transition | 一次有明确输入、输出与状态更新的确定函数 |
| 转导器 | transducer | 对一条有序输入流执行转移并产生输出流和状态的对象 |
| 路由 | routing | 根据带标签输出选择出边 |
| 选择器 | selector | 实现路由决策的确定函数；可变状态必须显式纳入契约 |
| 调度 | schedule | 满足依赖关系的一种逻辑执行顺序 |
| 绝对时间流式调度 | absolute-time streaming schedule | 按绝对轮次与阶段推进 |
| 节点拓扑序分块调度 | node-topological chunk schedule | 按空间有向无环图的拓扑序逐节点处理完整事件流 |
| 封闭有限执行 | closed finite execution | 最后一个读出后继续冲刷当前有限输入产生的消息 |
| 延续状态 | continuation state | 可直接接续下一周期的节点状态与在途消息 |
| 精确分块正确性 | exact chunk correctness | 分块执行与参考产物严格相等 |
| 工作量 | work | 总原语操作数或其上界 |
| 并行跨度 | span | 无限处理器理想化下的关键路径长度 |
| 关键路径 | critical path | 由依赖关系决定、无法并行缩短的最长路径 |
| 性能见证 | performance witness | 正确性之外，对工作量、并行跨度和吞吐量的独立证明或测量 |
| 有向无环图 | directed acyclic graph, DAG | 后文通常写作“有向无环图”；公式和固定缩写可保留 DAG |
| 计算核 | kernel | 节点内部承担数值计算或局部控制计算的实现单元 |
| 运行时 | runtime | 承担事件组织、调度、消息传递和状态提交的执行系统 |
| 事件中间表示 | Event IR | 实现层用于显式保存逻辑事件、字段与依赖关系的中间表示 |
| 预填充 / 解码 | prefill / decode | 给定令牌块的并行处理 / 逐步自回归处理 |
| 语义配置 | semantic profile | 固定转移、状态可见性、提交和路由含义的一组约定 |
| 类型化 | typed | 对事件种类、字段和依赖关系给出显式类型约束 |

### 定义 0.1：基础集合记号

定义自然数与正整数：

$$
\mathbb N=\{0,1,2,\ldots\},
$$

$$
\mathbb N_{>0}=\{1,2,3,\ldots\}.
$$

对 $L\in\mathbb N$，定义：

$$
[L]=\{0,1,\ldots,L-1\}.
$$

若 $L=0$，则 $[L]=\varnothing$。

有限序列使用圆括号表示。有限多重集保留重复元素，不因载荷相等而去重。

本文沿用 [[step-transition-mathematical-specification#定义 1.2：顺序 fold|顺序折叠]]、[[step-transition-mathematical-specification#定义 3.6a：logical event DAG program|逻辑事件有向无环图]] 与 [[adaptive-routing-prefill-impossibility]] 的结论，但本页所需对象均在首次使用前重新定义。

### 定义 0.2：输入序列与固定周期

给定令牌空间 $X$、读出空间 $Y$、分块长度 $L\in\mathbb N$、固定周期：

$$
R\in\mathbb N_{>0},
$$

以及输入序列：

$$
x_{0:L}=(x_0,\ldots,x_{L-1})\in X^L.
$$

对每个 $t\in[L]$，定义令牌 $x_t$ 的绝对注入轮次：

$$
\operatorname{InTime}(t)=Rt.
\tag{GD-0.1}
$$
^eq-fixed-injection-time

定义第 $t$ 个读出的绝对轮次：

$$
\operatorname{OutTime}(t)=R(t+1).
\tag{GD-0.2}
$$
^eq-fixed-readout-time

$R$ 是参考语义的常数，不依赖输入值、节点状态、任何模型内部决策或当前运行时活动。内部计算不能推迟或提前式 GD-0.1 与 GD-0.2 规定的边界。

这里 $R$ 首先是逻辑周期。若还要求真实设备每隔固定墙钟周期 $T_{\mathrm{ext}}>0$ 输出一个令牌，则实现必须证明第 $t$ 个读出在墙钟截止时间 $(t+1)T_{\mathrm{ext}}$ 前完成。该实时吞吐量条件属于性能见证，不由后文的调度等价定理自动推出。

### 定义 0.3：阶段与完整逻辑时间戳

取阶段数：

$$
N_{\mathrm{phase}}\in\mathbb N_{>0},
\qquad
N_{\mathrm{phase}}\geq 6,
$$

以及按执行先后排列的阶段元组：

$$
\mathcal P
=
(\varphi_0,\ldots,\varphi_{N_{\mathrm{phase}}-1}).
$$

定义完整逻辑时间戳集合：

$$
\Theta
=
\mathbb N\times\{0,\ldots,N_{\mathrm{phase}}-1\}.
$$

对 $(\tau,i),(\tau',j)\in\Theta$，定义字典序严格次序 $<_{\Theta}$：

$$
(\tau,i)<_{\Theta}(\tau',j)
$$

当且仅当：

$$
\tau<\tau',
$$

或：

$$
\tau=\tau'
\quad\text{且}\quad
i<j.
$$

指定六个不同阶段索引：

$$
i_{\mathrm{arrive}},
i_{\mathrm{step}},
i_{\mathrm{commit}},
i_{\mathrm{read}},
i_{\mathrm{sample}},
i_{\mathrm{inject}}
\in
\{0,\ldots,N_{\mathrm{phase}}-1\},
$$

满足：

$$
i_{\mathrm{arrive}}
<
i_{\mathrm{step}}
<
i_{\mathrm{commit}}
<
i_{\mathrm{read}}
<
i_{\mathrm{sample}}
<
i_{\mathrm{inject}}.
\tag{GD-0.3}
$$
^eq-boundary-phase-order

定义第 $t$ 个令牌的注入时间戳：

$$
\theta_t^{\mathrm{in}}
=
(Rt,i_{\mathrm{inject}}),
$$

以及第 $t$ 个读出与采样时间戳：

$$
\theta_t^{\mathrm{out}}
=
(R(t+1),i_{\mathrm{read}}),
$$

$$
\theta_t^{\mathrm{sample}}
=
(R(t+1),i_{\mathrm{sample}}).
$$

因此当 $t+1\in[L]$ 时：

$$
\theta_t^{\mathrm{out}}
<_{\Theta}
\theta_t^{\mathrm{sample}}
<_{\Theta}
\theta_{t+1}^{\mathrm{in}}.
\tag{GD-0.4}
$$
^eq-read-sample-inject-order

### 定义 0.4：教师强制与自回归外部接口

在教师强制/预填充参考中，$x_{0:L}$ 是给定边界数据；虽然物理实现可以一次持有整个张量，令牌 $x_t$ 在逻辑上只能从 $\theta_t^{\mathrm{in}}$ 开始可见。

在自回归参考中，给定确定性令牌选择函数：

$$
\operatorname{SelectToken}:Y\to X,
$$

并要求第 $t$ 个固定周期读出 $y_t\in Y$ 产生后：

$$
x_{t+1}
=
\operatorname{SelectToken}(y_t),
\qquad t+1\in[L].
\tag{GD-0.5}
$$
^eq-autoregressive-token-selection

到达、节点转移与状态提交均在读出之前完成，因此绝对轮次 $R(t+1)$ 到达输出节点的最短路径消息可以影响 $y_t$。式 GD-0.4 保证随后先选择令牌，最后注入下一令牌。后文的分块正确性定理以给定输入序列的教师强制参考为比较对象；式 GD-0.5 额外定义纯推理如何把连续两个固定周期连接起来。

## 1. 一般单位时延空间有向无环图

### 定义 1.1：带输入输出的空间有向无环图

一个带输入输出的空间有向无环图是三元组：

$$
(G,s,z),
$$

其中：

- $G=(V,E)$ 是有限有向无环图。
- $s\in V$ 是唯一输入节点。
- $z\in V$ 是唯一输出节点。
- $s\neq z$。
- 每个 $v\in V$ 都位于至少一条从 $s$ 到 $z$ 的有向路径上。

另外固定节点集合 $V$ 与边集合 $E$ 的静态全序 $<_{V}$、$<_{E}$，只用于规范序列化与确定性并列消解；它们不表示额外计算依赖。

对边 $(u,v)\in E$，$u$ 称为 $v$ 的直接空间前驱，$v$ 称为 $u$ 的直接空间后继。

### 定义 1.2：有向路径与路径长度

从节点 $u$ 到节点 $v$ 的一条有向路径是节点元组：

$$
p=(v_0,v_1,\ldots,v_k),
$$

满足：

$$
v_0=u,\qquad v_k=v,
$$

并且对每个 $i\in\{0,\ldots,k-1\}$：

$$
(v_i,v_{i+1})\in E.
$$

路径 $p$ 的边数称为路径长度，记为：

$$
|p|=k.
$$

定义从输入节点到 $v$ 的可达路径长度集合：

$$
\Lambda(v)
=
\{|p|\mid p\text{ 是从 }s\text{ 到 }v\text{ 的有向路径}\}.
$$

因为 $G$ 有限且无环，$\Lambda(v)$ 是有限非空集合。

定义空间有向无环图的最大路径长度：

$$
D
=
\max_{v\in V}\max\Lambda(v).
$$

由于有向路径不能重复经过同一个节点：

$$
D\leq |V|-1.
$$

定义输入到输出的最短路径长度：

$$
d_{\min}
=
\min\Lambda(z).
$$

本文固定周期严格语义配置取：

$$
R=d_{\min}.
\tag{GD-1.1}
$$
^eq-period-shortest-path

由 $s\neq z$，有 $d_{\min}\geq 1$，所以式 GD-1.1 与定义 0.2 的 $R\in\mathbb N_{>0}$ 一致。因此令牌 $t$ 沿最短输入输出路径产生的信号恰好在绝对轮次 $R(t+1)$ 到达输出边界。式 [[#^eq-read-sample-inject-order|GD-0.4]] 进一步规定同一边界上先读出，再采样，最后注入。当 $D>R$ 时，更长路径仍会跨越该边界，并只能影响逻辑时间更晚的状态/读出。

### 定义 1.3：单位时延边

本文假设每条边的参考传播时延恰好为一个全局内部轮次：

$$
\operatorname{delay}(u,v)=1,
\qquad (u,v)\in E.
$$

这是一条语义约束，不是硬件传输延迟。物理运行时可以融合传输、使用缓冲区或异步执行，但必须保持逻辑到达时间。

> [!note] 一般有向无环图与等层有向无环图
> 若对任意节点 $v$，集合 $\Lambda(v)$ 只有一个元素，则所有从 $s$ 到 $v$ 的路径等长，旧文档中的等层有向无环图是本页模型的特殊情形。本文不再把这一性质作为前提，也不通过中继节点改变原边的单位时延。

## 2. 前缀因果性与固定周期路径时间

### 定义 2.1：前缀因果对象与因果前沿

定义因果前沿索引空间：

$$
\mathbb F_L
=
\{-1\}\cup[L].
$$

给定由输入序列 $x_{0:L}$ 决定的任意语义对象 $q$，以及 $c\in\mathbb F_L$。称 $q$ 是 $c$-前缀因果的，当且仅当对任意两个输入序列 $x_{0:L}$ 与 $\bar x_{0:L}$：

$$
x_j=\bar x_j,
\qquad
0\leq j\leq c,
$$

都蕴含两次执行中的 $q$ 相同。若 $c=-1$，该条件表示 $q$ 与全部输入令牌无关。

若 $q$ 是一个动态产生的可选记录，则把它的值域扩展为：

$$
\mathcal Q_\bot
=
\mathcal Q\cup\{\bot\},
$$

其中 $\bot$ 表示该记录不存在。因此“$q$ 相同”同时要求两次执行中存在性与存在时的数值都相同。这里的 $q$ 仍只是可选语义对象；$q=\bot$ 不表示发生了一次带空值的计算记录。

若运行时为 $q$ 声明：

$$
\operatorname{frontier}(q)=c,
$$

则要求 $q$ 至少是 $c$-前缀因果的。因果前沿可以是保守上界，不要求一定是最小依赖令牌索引。输入令牌满足：

$$
\operatorname{frontier}(x_t)=t.
$$

### 定义 2.1a：抽象逻辑事件头与事件值

给定有限事件种类集合 $\mathcal K$。一次已经实例化的执行中，一个实际逻辑事件头是六元组：

$$
h_e
=
(\eta_e,\kappa_e,\ell_e,\theta_e,\Omega_e,c_e),
\tag{GD-2.0}
$$
^eq-logical-event-header

其中：

- $\eta_e$ 是来自静态全序标识符空间的、全局唯一且确定生成的逻辑事件标识符。
- $\kappa_e\in\mathcal K$ 是事件种类。
- $\ell_e\in V\cup\{\mathtt{external}\}$ 是事件位置。
- $\theta_e\in\Theta$ 是事件值对后继可见的逻辑提交时间戳。
- $\Omega_e\subseteq[L]$ 是该事件直接联合处理或标识的所有者支持集。
- $c_e\in\mathbb F_L$ 是事件值的有效因果前沿。

对每个实际事件头 $h_e$，声明值空间 $\mathcal V_e$，并赋予唯一事件值：

$$
\nu(e)\in\mathcal V_e.
$$

定义实际事件的字段投影：

$$
\operatorname{id}(e)=\eta_e,
\quad
\operatorname{kind}(e)=\kappa_e,
\quad
\operatorname{loc}(e)=\ell_e,
$$

$$
\operatorname{time}(e)=\theta_e,
\quad
\operatorname{support}(e)=\Omega_e,
\quad
\operatorname{frontier}(e)=c_e.
$$

本文把二元组 $(h_e,\nu(e))$ 称为逻辑事件实例，并在值已明确时简写为 $e$。实际事件集合只包含真正发生的事件。动态存在性不通过“值为 $\bot$ 的假事件”表达，而通过源事件值中的可选路由/消息记录表达。一个已经发生的节点事件仍可以把“无路由可见的隐藏表示”作为其结构化值的某个 $\bot$ 分量；这不表示该事件未发生。

### 定义 2.1b：抽象事件图与依赖边

给定一次有限执行的实际事件集合 $\mathcal E$，以及二元关系：

$$
\mathcal A\subseteq\mathcal E\times\mathcal E.
$$

定义事件图：

$$
D=(\mathcal E,\mathcal A).
$$

要求 $\mathcal A$ 中每个有序对都表示参考语义中的直接数据、状态或控制依赖：$e'$ 的事件头、存在性或值读取了 $e$ 产生的某个产物。该关系此处可以不完备，但不能加入没有语义依赖的任意次序边。

若 $(e,e')\in\mathcal A$，称 $e$ 是 $e'$ 的直接依赖，并记为：

$$
e\longrightarrow e'.
$$

若 $D$ 无有向环，则称其为逻辑事件有向无环图。这里尚未规定哪些参考依赖必须进入 $\mathcal A$；第 7 节将为固定周期 Tide 执行实例化关系 $\mathcal A_L^P$，并定义依赖完备性。

### 定义 2.1c：固定边界事件头

定义边界事件种类集合：

$$
\mathcal K_{\mathrm{bdry}}
=
\{\mathtt{inject},\mathtt{readout},\mathtt{sample}\}.
$$

对每个 $t\in[L]$，定义必定发生的输入事件头：

$$
h_{e_t^{\mathrm{in}}}
=
(\eta_t^{\mathrm{in}},\mathtt{inject},s,
\theta_t^{\mathrm{in}},\{t\},t),
$$

以及必定发生的固定读出事件头：

$$
h_{e_t^{\mathrm{out}}}
=
(\eta_t^{\mathrm{out}},\mathtt{readout},z,
\theta_t^{\mathrm{out}},[t+1],t).
$$

自回归执行还定义采样事件头：

$$
h_{e_t^{\mathrm{sample}}}
=
(\eta_t^{\mathrm{sample}},\mathtt{sample},\mathtt{external},
\theta_t^{\mathrm{sample}},[t+1],t).
$$

教师强制执行不实例化采样事件。边界事件的值空间与值在定义 7.1 中登记；本定义只固定事件恒等、种类、位置、时间戳、支持集与因果前沿。

### 定义 2.2：所在周期与周期内轮次偏移

对绝对轮次 $\tau\in\mathbb N$，定义其所处周期的索引：

$$
q_R(\tau)
=
\left\lfloor\frac{\tau}{R}\right\rfloor,
$$

以及周期内轮次偏移：

$$
r_R(\tau)
=
\tau-Rq_R(\tau).
$$

由欧几里得除法：

$$
0\leq r_R(\tau)<R.
$$

$q_R(\tau)$ 是全局时钟已经进入的周期编号，不是任意消息的所有者令牌。

### 定义 2.3：路径年龄与固定周期到达时间

给定令牌索引 $t\in[L]$、节点 $v\in V$ 与一条从 $s$ 到 $v$ 的路径 $p$。定义该路径实例的路径年龄：

$$
k(p)=|p|,
$$

绝对到达轮次：

$$
A_R(t,p)
=
Rt+|p|,
\tag{GD-2.1}
$$
^eq-fixed-arrival-round

以及到达时间戳：

$$
\theta_R^{\mathrm{arr}}(t,p)
=
(A_R(t,p),i_{\mathrm{arrive}}).
\tag{GD-2.2}
$$
^eq-fixed-arrival-timestamp

路径年龄可以大于 $R$。此时该路径实例在令牌 $t+1$ 的注入边界之后才到达，固定周期本身不截断它。

### 推论 2.3a：最短路径在固定读出前提交

若 $p$ 是从 $s$ 到 $z$ 的最短路径，则 $|p|=R$，并且：

$$
\theta_R^{\mathrm{arr}}(t,p)
=
(R(t+1),i_{\mathrm{arrive}}).
$$

由式 GD-0.3：

$$
(R(t+1),i_{\mathrm{arrive}})
<_{\Theta}
(R(t+1),i_{\mathrm{commit}})
<_{\Theta}
\theta_t^{\mathrm{out}}.
$$

因此，只要最短路径到达所触发的输出节点转移在本轮次正常执行，其已提交的状态可以被第 $t$ 个固定读出读取。

**证明。**

由 $|p|=R$ 与式 GD-2.1，到达轮次为 $Rt+R=R(t+1)$；阶段不等式直接来自式 GD-0.3。

<div class="qed" aria-label="证毕">∎</div>

### 定义 2.4：时间戳处可用的输入前缀

若 $L>0$，对任意 $\theta\in\Theta$，定义在 $\theta$ 之前已经完成注入的最大令牌索引：

$$
a_{R,L}(\theta)
=
\max
\left(
\{-1\}
\cup
\{t\in[L]\mid \theta_t^{\mathrm{in}}\leq_{\Theta}\theta\}
\right),
\tag{GD-2.3}
$$
^eq-available-prefix

其中 $\leq_{\Theta}$ 是由 $<_{\Theta}$ 诱导的非严格次序。

本文要求每个计算核只读取在其时间戳已经可见的输入令牌。任意在时间戳 $\theta$ 产生并声明因果前沿的良构的语义对象 $q$ 必须具有有效因果前沿，并满足：

$$
\operatorname{frontier}(q)
\leq
a_{R,L}(\theta)
\tag{GD-2.4}
$$
^eq-timestamp-frontier-bound

特别地，每个逻辑事件实例 $e$ 必须满足：

$$
\operatorname{frontier}(e)
\leq
a_{R,L}(\operatorname{time}(e)),
$$

并且 $\nu(e)$ 是定义 2.1 意义下的 $\operatorname{frontier}(e)$-前缀因果对象。动态事件存在性的前缀因果性必须在产生该事件的可选路由/消息记录上单独登记，不能由实际事件头自行推出。

特别地，在边界轮次 $R(t+1)$ 的读出阶段，下一次注入尚未发生，因此对每个 $t\in[L]$：

$$
a_{R,L}(\theta_t^{\mathrm{out}})=t.
\tag{GD-2.5}
$$
^eq-readout-prefix

**证明。**

令牌 $x_0,\ldots,x_t$ 的注入时间戳都不晚于 $\theta_t^{\mathrm{out}}$。若 $j>t$ 且 $j\in[L]$，则 $\theta_j^{\mathrm{in}}\geq_{\Theta}\theta_{t+1}^{\mathrm{in}}>_{\Theta}\theta_t^{\mathrm{out}}$；当 $t=L-1$ 时不存在这样的 $j$。代入式 [[#^eq-available-prefix|GD-2.3]] 即得式 GD-2.5。

<div class="qed" aria-label="证毕">∎</div>

### 例 2.5：不同令牌路径实例的同刻碰撞

考虑：

```text
s -----------------> v
s -> a -> b --------> v
```

记长路径为 $p_A=(s,a,b,v)$，短路径为 $p_B=(s,v)$。它们的长度分别为 $3$ 与 $1$。取固定周期：

$$
R=2.
$$

- 令牌 A 的索引为 $0$，沿长路径到达 $v$ 的轮次为 $A_R(0,p_A)=0+3=3$。
- 令牌 B 的索引为 $1$，沿短路径到达 $v$ 的轮次为 $A_R(1,p_B)=2+1=3$。

因此两个路径实例在同一节点 $v$、同一到达时间戳 $(3,i_{\mathrm{arrive}})$ 到达。

### 命题 2.6：一般有向无环图中不能由节点与时间恢复所有者

若存在节点 $v$、两个不同令牌索引 $t_A,t_B\in[L]$ 与两条从 $s$ 到 $v$ 的路径 $p_A,p_B$，满足：

$$
Rt_A+|p_A|
=
Rt_B+|p_B|,
$$

则 $(v,A_R(t_A,p_A))$ 不能唯一确定路径实例的令牌索引。因此后文定义消息时必须显式保留所有者字段。

**证明。**

两个路径实例的到达轮次分别为：

$$
\tau_A=Rt_A+|p_A|,
$$

$$
\tau_B=Rt_B+|p_B|.
$$

由题设：

$$
\tau_B
=
Rt_B+|p_B|
=
Rt_A+|p_A|
=
\tau_A.
$$

但 $t_A\neq t_B$，所以 $(v,\tau)$ 不能唯一确定所有者。

<div class="qed" aria-label="证毕">∎</div>

这个命题说明所有者标签不是冗余字段。若把同刻不同令牌路径的记录无标签合并，后续输出对齐、路由、损失、回放与归因都会失去明确语义。

### 命题 2.7：前序令牌晚到与所有者逆序条件

取 $t_A<t_B$，并令两条路径 $p_A,p_B$ 都从 $s$ 到达同一节点 $v$。则后序令牌 B 的路径实例先于前序令牌 A 的路径实例到达，当且仅当：

$$
|p_A|-|p_B|
>
R(t_B-t_A).
$$

二者同刻到达，当且仅当上式中的 $>$ 改为 $=$。

**证明。**

由式 [[#^eq-fixed-arrival-round|GD-2.1]]：

$$
\tau_A=Rt_A+|p_A|,
\qquad
\tau_B=Rt_B+|p_B|.
$$

因此：

$$
\tau_B<\tau_A
$$

当且仅当：

$$
Rt_B+|p_B|
<
Rt_A+|p_A|,
$$

移项即得结论。同刻条件同理。

<div class="qed" aria-label="证毕">∎</div>

这个命题表明：即使输入/输出时钟固定，只要路径长度差超过令牌注入轮次差，一般有向无环图仍会出现后序令牌路径先到。该事实由拓扑结构与固定 $R$ 共同决定，不由选择器改写时间戳。

## 3. 可选的双皮层空间结构

### 定义 3.1：输入/输出双皮层有向无环图

设输入皮层为：

$$
G_I=(V_I,E_I),
$$

其执行方向从输入节点 $s$ 指向输入桥接节点 $b_I$。

设输出皮层为：

$$
G_O=(V_O,E_O),
$$

其执行方向从输出桥接节点 $b_O$ 指向输出节点 $z$。

假设：

$$
V_I\cap V_O=\varnothing.
$$

增加唯一单向桥接：

$$
(b_I,b_O).
$$

组合图定义为：

$$
G
=
\left(
V_I\cup V_O,\,
E_I\cup E_O\cup\{(b_I,b_O)\}
\right).
$$

$G_O$ 可以与 $G_I$ 反向同构，但反向同构只描述结构对应关系，不增加从输出皮层返回输入皮层的执行边。

### 引理 3.2：单向桥接保持有向无环性

若 $G_I$ 与 $G_O$ 都是有向无环图，且不存在从 $V_O$ 指向 $V_I$ 的边，则定义 3.1 的组合图 $G$ 是有向无环图。

**证明。**

假设 $G$ 中存在有向环。若该环完全位于 $V_I$ 或 $V_O$，分别与 $G_I$ 或 $G_O$ 是有向无环图矛盾。

若该环同时经过两侧，则它必须通过桥接 $(b_I,b_O)$ 从 $V_I$ 进入 $V_O$。要回到 $V_I$，环中必须存在一条从 $V_O$ 指向 $V_I$ 的边，但前提排除了这种边，矛盾。

所以 $G$ 无有向环。

<div class="qed" aria-label="证毕">∎</div>

## 4. 消息、收件箱与有限事件性

### 定义 4.1：带因果标签和时间戳的消息

给定带静态全序的逻辑消息标识符空间 $\mathsf{MID}$、元数据空间 $\mathcal U$ 与载荷空间 $\mathcal P$。若不同边使用不同载荷类型，可把 $\mathcal P$ 取为带边或类型标签的不交并。

一条消息是元组：

$$
m=(\iota,t,c,\theta,u,v,\mu,p),
$$

属于：

$$
\mathsf{MID}
\times[L]
\times\mathbb F_L
\times\Theta
\times V\times V
\times\mathcal U
\times\mathcal P,
$$

其中：

- $\iota$ 是全局唯一逻辑消息标识符。
- $t\in[L]$ 是所有者令牌。
- $c\in\mathbb F_L$ 是满足定义 2.1 的因果前沿。
- $t\leq c$，即消息因果前沿同时覆盖轨迹所有者来源信息。
- $\theta=(\tau,i_{\mathrm{arrive}})\in\Theta$ 是到达时间戳。
- $u\in V$ 是源节点。
- $v\in V$ 是目标节点。
- $(u,v)\in E$。
- $\mu\in\mathcal U$ 是元数据，例如来源槽位、源端口、路由标识符或谱系标识符；不需要元数据时可令 $\mathcal U$ 为单元素集合。
- $p\in\mathcal P$ 是载荷。

定义字段读取函数：

$$
\operatorname{id}(m)=\iota,
\qquad
\operatorname{owner}(m)=t,
$$

$$
\operatorname{frontier}(m)=c,
\qquad
\operatorname{arrival}(m)=\theta,
\qquad
\operatorname{src}(m)=u,
\qquad
\operatorname{dst}(m)=v.
$$

若 $\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}})$，定义：

$$
\operatorname{arrivalRound}(m)=\tau.
$$

记所有满足上述约束的有效消息的集合为 $\mathcal R$。对节点 $v$，定义其入站消息记录空间：

$$
\mathcal R_v
=
\{m\in\mathcal R\mid\operatorname{dst}(m)=v\}.
$$

消息标识符使重复载荷仍保持为不同消息。逻辑消息标识符必须由输入标识符、路由谱系、源/目标、所有者/因果前沿、时间戳或来源槽位等语义字段确定性生成，不能来自依赖线程竞争顺序的全局自增计数。参考语义不依赖物理线程首先写入收件箱的顺序。

对每个输入令牌 $t\in[L]$，定义不属于边消息集合的边界注入记录：

$$
b_t^{\mathrm{in}}
=
(t,\theta_t^{\mathrm{in}},s,x_t).
$$

该记录在第 7 节实例化为输入逻辑事件。它的所有者/因果前沿都是 $t$，但它不是从某条空间边到达的消息。

### 定义 4.2：单位时延派发

若常规节点事件在绝对轮次 $\tau$ 的提交阶段，或输入事件在 $(\tau,i_{\mathrm{inject}})$，产生带所有者 $t'\in[L]$ 与因果前沿 $c'\in\mathbb F_L$ 的输出记录，其中 $t'\leq c'$，并沿已选边 $(v,w)\in E$ 派发，则新消息必须满足：

$$
\operatorname{owner}(m')=t',
\qquad
\operatorname{frontier}(m')=c',
$$

$$
\operatorname{arrival}(m')
=
(\tau+1,i_{\mathrm{arrive}}),
\tag{GD-3}
$$
^eq-unit-delay-dispatch

$$
\operatorname{src}(m')=v,
\qquad
\operatorname{dst}(m')=w.
$$

路由可以更新载荷、消息标识符与其他元数据，但不能独立改写节点输出已声明的所有者/因果前沿，也不能改写逻辑到达时间戳。

### 定义 4.2a：跨边界延续语义

一条消息轨迹是有限消息序列：

$$
\gamma=(m_1,\ldots,m_q),
$$

满足 $m_1$ 是某个边界注入记录 $b_t^{\mathrm{in}}$ 产生的第一跳边消息，并且对每个 $j<q$，消费 $m_j$ 的节点转移产生了 $m_{j+1}$。轨迹可以在选择器终止派发时结束，也可以在不同轨迹被联合/融合转移消费时合并。

固定周期边界本身不删除、吸收或重写任何已经存在的边消息。一个消息只会因为以下两种原因结束生命周期：

1. 它到达目标并被相应节点事件消费。
2. 产生它的选择器明确选择不再派发后继消息。

特别地，若某条轨迹的下一条消息的到达轮次大于 $R(t+1)$，该消息仍保留其式 GD-3 决定的时间戳，并在后续周期到达。读出、采样与下一令牌注入不执行隐式清除。

### 定义 4.3：按节点、时间和所有者分桶的收件箱

对节点 $v$、绝对时间 $\tau$ 与所有者 $t$，定义有限消息多重集：

$$
I_{v,\tau,t}
=
\left\{
m\ \middle|\
\operatorname{dst}(m)=v,\,
\operatorname{arrival}(m)=(\tau,i_{\mathrm{arrive}}),\,
\operatorname{owner}(m)=t
\right\}_{\mathrm{multi}}.
\tag{GD-4}
$$
^eq-general-owner-inbox

定义同刻到达 $v$ 的所有者集合：

$$
\mathcal O_{v,\tau}
=
\{t\in[L]\mid I_{v,\tau,t}\neq\varnothing\}.
$$

把它按令牌索引递增排列：

$$
O_{v,\tau}^{\uparrow}=(t_1,t_2,\ldots,t_m),
\qquad t_1<t_2<\cdots<t_m.
$$

### 定义 4.4：同所有者、同刻聚合

对每个节点 $v$，给定输入空间 $X_v$ 和确定性聚合器：

$$
\operatorname{Aggregate}_v:
\mathcal M_{\mathrm{fin}}(\mathcal R_v)
\to X_v,
$$

其中 $\mathcal R_v$ 是到达 $v$ 的消息记录空间，$\mathcal M_{\mathrm{fin}}(\mathcal R_v)$ 表示其有限多重集。

定义：

$$
x_{v,\tau,t}
=
\operatorname{Aggregate}_v(I_{v,\tau,t}).
\tag{GD-5}
$$
^eq-general-owner-aggregate

聚合值默认声明保守因果前沿：

$$
\operatorname{frontier}(x_{v,\tau,t})
=
\max_{m\in I_{v,\tau,t}}
\operatorname{frontier}(m).
$$

若聚合器能够证明忽略了某些因果前沿较高的消息，可以声明更小但仍有效的因果前沿；不能在没有证明时降低标签。

如果聚合器与顺序无关，它直接作用于多重集。若业务语义要求顺序，必须先按固定字段，例如 `(source node id, message id)`，做规范排序；不能使用物理到达竞争作为隐式顺序。

不同绝对时间的消息不在本步骤聚合。同一个所有者可以因不同路径长度在同一节点多次激活：

$$
x_{v,\tau_1,t},
\qquad
x_{v,\tau_2,t},
\qquad
\tau_1\neq\tau_2.
$$

### 引理 4.5：有限时间范围

若令牌数为 $L>0$，则所有由这些令牌产生并沿 $G$ 传播的消息都满足：

$$
0\leq\tau\leq R(L-1)+D.
\tag{GD-6}
$$
^eq-finite-horizon

**证明。**

对每条消息保留一个只用于时序证明的见证 $(t,p)$：$t\in[L]$ 是某个触发该事件链的输入注入，$p$ 是从 $s$ 到当前目标的有向路径，并满足：

$$
\tau=Rt+|p|.
$$

从边界注入记录产生的第一条消息使用从 $s$ 开始的相应单边路径。若节点调用由一条带见证 $(t,p)$ 的入站消息触发，则沿边 $(v,w)$ 发出的任意消息可以取延长路径 $p\mathbin{\|}(v,w)$ 作为见证。所有者/因果前沿提升不改变绝对时间，也不影响这个时序见证。

因为默认语义配置不在空时间戳自主发射消息，所有已派发的消息都可由上述归纳得到见证。又因为 $t\leq L-1$ 且 $|p|\leq D$：

$$
\tau=Rt+|p|
\leq
R(L-1)+D.
$$

<div class="qed" aria-label="证毕">∎</div>

### 引理 4.6：有限事件性

假设每次节点调用只沿有限出边集合发出有限条消息。对任意有限输入分块，一次执行产生的消息集合有限。

**证明。**

有限有向无环图中有向路径数量有限。每条消息只能沿边方向前进，不能返回已经经过的节点。初始注入数有限，每次调用的扇出有限，所以对有限路径树做有限次展开后，总消息数有限。

<div class="qed" aria-label="证毕">∎</div>

有限不等于高效。一般有向无环图的路径数量可以随 $|V|$ 指数增长，因此后文仍需单独加入稀疏事件预算。

## 5. 节点持有状态与三种同刻/融合语义

### 定义 5.1：节点持有的持久上下文

每个节点 $v$ 有状态空间：

$$
\mathcal S_v,
$$

以及初始状态：

$$
S_v^0\in\mathcal S_v.
$$

其具体实现可以是：

- KV 缓存。
- Mamba/SSM 递归状态。
- 线性注意力累加器。
- 显式节点记忆。
- 其他具有分块正确性契约的状态。

严格语义配置要求每个可变状态位置有唯一所有者节点。若多个节点必须联合修改同一状态，应把它们封装为一个具有独立事件流契约的超级节点/子图算子。

持久状态属于节点，不属于某个令牌。为进行因果审计，把实际数值状态与其因果前沿写成增广状态：

$$
\widetilde S_v=(S_v,c_v^S),
\qquad
c_v^S\in\mathbb F_L.
$$

定义增广状态空间：

$$
\widetilde{\mathcal S}_v
=
\mathcal S_v\times\mathbb F_L.
$$

初始状态不依赖输入，声明：

$$
c_v^{S,0}=-1.
$$

因此增广初始状态为：

$$
\widetilde S_v^0=(S_v^0,-1).
$$

对任意 $\widetilde S=(S,c^S)\in\widetilde{\mathcal S}_v$，定义投影：

$$
\operatorname{num}(\widetilde S)=S,
\qquad
\operatorname{frontier}(\widetilde S)=c^S.
$$

从本定义之后，所有参考转移的状态参数和值域都使用增广状态空间 $\widetilde{\mathcal S}_v$；数值计算核只需读取 $\operatorname{num}(\widetilde S)$，但运行时必须同时传播并提交因果前沿投影。前两种语义配置可以只把该标签用于审计，因果前沿融合语义配置则会用它决定新的出站所有者。

对任意节点转移，若它读取 $n\in\mathbb N_{>0}$ 个语义对象，其因果前沿为：

$$
c_1,\ldots,c_n,
$$

则输出隐藏表示与后状态默认声明：

$$
c_{\mathrm{out}}
=
\max_{1\leq i\leq n}c_i.
$$

计算核若通过因果掩码、带版本的状态或独立证明得到更紧的依赖上界，可以声明更小的有效因果前沿；但带所有者标签的路由/消息记录还必须把该轨迹所有者计入保守来源信息上界，因此不得把因果前沿降到所有者以下。按所有者排序的/原子联合语义配置保留轨迹所有者，即使 $c_{\mathrm{out}}>\operatorname{owner}$；这个不等式正是所有者前缀污染的显式检测信号。

因此：

```text
消息 / 隐藏表示 / 路由记录 -> 带所有者标签 + 带因果前沿标签
持久上下文                -> 节点持有 + 带因果前沿标签
```

### 定义 5.2：同刻所有者元组

对非空所有者集合：

$$
O_{v,\tau}^{\uparrow}=(t_1,\ldots,t_m),
$$

定义节点 $v$ 在时间 $\tau$ 的按所有者索引的输入元组：

$$
B_{v,\tau}
=
\bigl(
(t_1,x_{v,\tau,t_1}),
\ldots,
(t_m,x_{v,\tau,t_m})
\bigr).
$$

该元组的顺序由令牌索引唯一决定，不依赖运行时调度。

同时定义不按所有者分开的完整同刻收件箱：

$$
I_{v,\tau}
=
\biguplus_{t\in\mathcal O_{v,\tau}}
I_{v,\tau,t},
$$

其中 $\biguplus$ 表示保留重复消息的多重集并。因果前沿融合语义配置直接对 $I_{v,\tau}$ 做一次联合计算。

默认严格语义配置中，没有收件箱事件的节点状态保持不变。若模型需要在空时间戳执行衰减，应另行定义：

$$
\operatorname{Idle}_v:
\mathbb N\times\widetilde{\mathcal S}_v
\to
\widetilde{\mathcal S}_v,
$$

并把所有空时间戳更新纳入第 7 节定义的节点参考与分块产物。本文后续公式取 $\operatorname{Idle}_v(\tau,S)=S$；非平凡空闲/衰减是相同证明框架下的扩展，不是免费省略项。

#### 定义 5.2a：节点的绝对时间事件次序

对同一节点的两个所有者事件次序键：

$$
k=(\tau,t),
\qquad
k'=(\tau',t'),
$$

定义：

$$
k\prec_v k'
$$

当且仅当：

$$
\tau<\tau',
$$

或：

$$
\tau=\tau'
\quad\text{且}\quad
t<t'.
$$

因此节点状态首先按绝对时间演进；只有绝对时间相同，才使用所有者令牌打破并列。

#### 例 5.2b：跨时间的所有者逆序

取固定周期 $R=2$。考虑所有者 A 的令牌索引为 $0$，沿长度 $4$ 的路径到达 $v$；所有者 B 的令牌索引为 $1$，沿长度 $1$ 的路径到达 $v$。二者到达轮次为：

$$
\tau_A=R\cdot 0+4=4,
\qquad
\tau_B=R\cdot 1+1=3.
$$

虽然 $t_A<t_B$，但在绝对时间事件次序中：

$$
(\tau_B,t_B)\prec_v(\tau_A,t_A).
$$

所以 B 的短路径事件会先更新节点状态，A 的晚到事件可能读取 B 的影响。后文的按所有者排序的语义配置只规定同一 $\tau$ 内的顺序，不消除这种跨时间所有者逆序。

### 5.3 配置 O：同一时间戳内按所有者顺序折叠

#### 定义 5.3：单所有者事件转移

给定数值隐藏表示空间 $H_v$。定义路由可见的带标签隐藏表示空间：

$$
\mathcal Z_v
=
\{\bot\}
\uplus
(H_v\times\mathbb F_L),
$$

其中 $\uplus$ 表示不交并。若 $z=(h,c)\in H_v\times\mathbb F_L$，定义：

$$
\operatorname{payload}(z)=h,
\qquad
\operatorname{frontier}(z)=c.
$$

一个带所有者标签的输出记录是有序对 $r=(t,z)\in[L]\times\mathcal Z_v$。定义 $\operatorname{owner}(r)=t$；当 $z\neq\bot$ 时，定义 $\operatorname{frontier}(r)=\operatorname{frontier}(z)$，并要求：

$$
\operatorname{owner}(r)
\leq
\operatorname{frontier}(r).
$$

$\bot$ 表示该事件已执行，但不产生路由可见的隐藏表示。节点 $v$ 的单事件转移是确定函数：

$$
\mathcal T_v:
\mathbb N\times\mathbb N\times X_v\times\widetilde{\mathcal S}_v
\to
\mathcal Z_v\times\widetilde{\mathcal S}_v.
$$

输入的两个自然数依次是所有者令牌 $t$ 与绝对时间 $\tau$。返回的带标签隐藏表示与后状态必须满足定义 5.1 的因果前沿传播规则。

#### 定义 5.4：按所有者排序的同刻转移

给定：

$$
B_{v,\tau}
=
\bigl((t_1,x_1),\ldots,(t_m,x_m)\bigr),
\qquad t_1<\cdots<t_m,
$$

以及进入该时间戳前的增广状态 $\widetilde S^{(0)}\in\widetilde{\mathcal S}_v$。递归定义：

$$
(z_i,\widetilde S^{(i)})
=
\mathcal T_v(t_i,\tau,x_i,\widetilde S^{(i-1)}),
\qquad i=1,\ldots,m.
\tag{GD-7}
$$
^eq-owner-ordered-group

该时间戳的所有者输出与提交后状态分别为：

$$
Z_{v,\tau}^{\mathrm{ord}}
=
\bigl((t_1,z_1),\ldots,(t_m,z_m)\bigr),
$$

其中每个非 $\bot$ 的 $z_i$ 都显式包含因果前沿，不再省略该字段。

$$
\widetilde S^+
=
\widetilde S^{(m)}.
$$

若 A、B 同刻到达且 $t_A<t_B$，则 B 的转移读取 A 已经更新后的状态。因果方向是：

$$
A\longrightarrow B.
$$

按所有者排序的是同一时间戳内的参考语义；完整节点事件流仍按定义 5.2a 的 $(\tau,t)$ 字典序次序演进。它不要求物理实现真的逐所有者循环。若能证明一个因果掩码、扫描或其他批量计算核等于式 [[#^eq-owner-ordered-group|GD-7]]，则可以联合执行。

### 5.4 配置 J：同一时间戳的原子联合转移

#### 定义 5.5：联合转移与整体状态增量

定义 $\mathcal B_v$ 为所有有限按所有者索引的输入元组的集合。其任意元素具有形式：

$$
B
=
\bigl((t_1,x_1),\ldots,(t_m,x_m)\bigr),
\qquad
t_1<\cdots<t_m.
$$

其中 $m\in\mathbb N_{>0}$、$t_i\in[L]$ 且 $x_i\in X_v$。

定义 $\mathcal Z_v^\star$ 为所有具有相同所有者键形式的有限带标签隐藏表示元组的集合：

$$
Z
=
\bigl((t_1,z_1),\ldots,(t_m,z_m)\bigr).
$$

其中 $z_i\in\mathcal Z_v$。

调用 $\mathcal J_v$ 时，输出元组必须与输入元组使用完全相同的所有者键序列；若某个所有者不产生隐藏表示，则相应位置写为 $\bot$。

对节点 $v$，给定增量空间 $\Delta_v$、提交函数：

$$
\operatorname{Commit}_v:
\widetilde{\mathcal S}_v\times\Delta_v
\to\widetilde{\mathcal S}_v,
$$

并要求 $\operatorname{Commit}_v$ 是确定函数，且其返回状态的因果前沿投影满足定义 5.1 的有效因果前沿规则；$\Delta_v$ 可以携带数值增量与计算该标签所需的审计信息。

以及原子联合转移：

$$
\mathcal J_v:
\mathbb N\times\mathcal B_v\times\widetilde{\mathcal S}_v
\to
\mathcal Z_v^\star\times\Delta_v.
$$

对任意时间戳 $\tau$、所有者元组 $B_{v,\tau}$ 与进入该时间戳前的增广状态 $\widetilde S$，定义：

$$
\mathcal J_v(\tau,B_{v,\tau},\widetilde S)
=
\left(
Z_{v,\tau}^{\mathrm{joint}},
\Delta_{v,\tau}
\right),
\tag{GD-8}
$$
^eq-atomic-joint-transition

其中：

$$
Z_{v,\tau}^{\mathrm{joint}}
=
\bigl((t_1,z_1),\ldots,(t_m,z_m)\bigr)
$$

仍为按所有者索引的输出；每个非 $\bot$ 的 $z_i$ 显式包含经过证明或按默认最大值规则得到的因果前沿。状态只在联合计算结束后提交一次：

$$
\widetilde S^+
=
\operatorname{Commit}_v(\widetilde S,\Delta_{v,\tau}).
\tag{GD-9}
$$
^eq-atomic-joint-commit

定义联合转移与提交的组合：

$$
\operatorname{Atomic}_v(\tau,B_{v,\tau},\widetilde S)
=
\left(
Z_{v,\tau}^{\mathrm{joint}},
\operatorname{Commit}_v(\widetilde S,\Delta_{v,\tau})
\right).
\tag{GD-9a}
$$
^eq-atomic-joint-composed

$\Delta_{v,\tau}$ 属于节点的整体状态更新，不要求归属于某个单独令牌。为了回放与归因，可以额外保留按所有者划分的增量分解，但它不是数学正确性的必要字段。

原子联合允许：

- 所有所有者读取同一个前状态。
- 联合计算核比较多个所有者的输入。
- 每个所有者的输出依赖同刻其他所有者。
- 联合计算核使用所有者索引构造三角掩码。

它不允许把多个所有者变成一个永久无所有者的在途信号。出站记录仍必须按所有者分开。

#### 定义 5.6：同刻所有者因果联合算子

对 $t\in\mathcal O_{v,\tau}$，定义所有者前缀：

若：

$$
B_{v,\tau}
=
\bigl((t_1,x_1),\ldots,(t_m,x_m)\bigr),
$$

并且 $t=t_j$，则：

$$
B_{v,\tau}^{\leq t}
=
\bigl((t_1,x_1),\ldots,(t_j,x_j)\bigr).
$$

若所有者 $t$ 的隐藏表示与路由决策只依赖：

$$
(\widetilde S,\tau,B_{v,\tau}^{\leq t}),
$$

而不依赖所有者大于 $t$ 的输入，则称联合算子在该时间戳内是所有者因果的。

这是比任意联合更强的约束。任意联合只保证绝对时间语义；它不自动保证令牌所有者意义下的前缀因果性。

### 定义 5.7：联合算子与有序折叠等价

把定义 5.4 的递归结果记为：

$$
\operatorname{GroupFold}_{\mathcal T_v}(\tau,B,\widetilde S)
=
\left(
Z_{v,\tau}^{\mathrm{ord}},
\widetilde S^{(m)}
\right).
\tag{GD-9b}
$$
^eq-owner-group-fold

若对任意 $\tau$、任意所有者元组 $B\in\mathcal B_v$ 和任意增广状态 $\widetilde S\in\widetilde{\mathcal S}_v$：

$$
\operatorname{Atomic}_v(\tau,B,\widetilde S)
=
\operatorname{GroupFold}_{\mathcal T_v}(\tau,B,\widetilde S),
\tag{GD-10}
$$
^eq-joint-ordered-equivalence

则称原子联合算子与按所有者排序的分组折叠等价。这里要求相等的是：

- 每个所有者的隐藏表示。
- 每个所有者的路由可见记录。
- 时间戳结束后的状态。

只比较整体增量或最终状态不足以建立等价。

### 命题 5.8：折叠等价的联合执行不改变语义

若式 [[#^eq-joint-ordered-equivalence|GD-10]] 对节点 $v$ 成立，则在该节点上用 $\mathcal J_v$ 一次执行整个时间戳分组，与按所有者令牌顺序执行 $\mathcal T_v$ 得到相同的可观察产物。

**证明。**

这是式 [[#^eq-joint-ordered-equivalence|GD-10]] 的直接展开：定义已经要求所有者输出、路由可见的记录与最终状态全部相等。

<div class="qed" aria-label="证毕">∎</div>

### 例 5.9：最终状态相同但语义不同

本例只写数值载荷，并假设两种实现使用相同的合法因果前沿标签；因此省略式中的增广状态与带标签隐藏表示外壳。

令：

$$
S\in\mathbb R,
$$

单事件转移为：

$$
\mathcal T(x,S)=(S+x,S+x).
$$

取：

$$
S=0,\qquad x_A=1,\qquad x_B=2.
$$

按所有者排序的折叠得到：

$$
h_A=1,\qquad h_B=3,\qquad S^+=3.
$$

若快照联合分别从旧状态计算，再把增量相加，则可能得到：

$$
h_A=1,\qquad h_B=2,\qquad S^+=3.
$$

两者最终状态都是 $3$，但 B 的隐藏表示不同，所以后续路由与输出也可能不同。

### 5.10 配置 F：因果前沿归属的原子融合

#### 定义 5.10：融合因果前沿

给定节点 $v$ 在时间 $\tau$ 的非空完整收件箱 $I_{v,\tau}$ 与增广前状态 $\widetilde S$，记：

$$
c_v^{S,-}
=
\operatorname{frontier}(\widetilde S).
$$

定义本次融合的因果前沿：

$$
c_{v,\tau}^{\star}
=
\max
\left(
\{c_v^{S,-}\}
\cup
\{\operatorname{frontier}(m)\mid m\in I_{v,\tau}\}
\right).
\tag{GD-F1}
$$
^eq-frontier-fusion-max

这个定义必须读取前状态的因果前沿。若当前输入只有 A、B，但前状态已经受 C 影响且 $C>B$，则：

$$
c_{v,\tau}^{\star}=C,
$$

不能把新输出错误标记为 B。

#### 定义 5.11：原子融合转移

因果前沿融合计算核是确定函数：

$$
\mathcal F_v:
\mathbb N
\times
\mathcal M_{\mathrm{fin}}(\mathcal R_v)
\times
\widetilde{\mathcal S}_v
\to
(H_v\cup\{\bot\})
\times
\Delta_v.
$$

它对完整同刻收件箱与增广前状态做一次联合计算：

$$
\mathcal F_v(\tau,I_{v,\tau},\widetilde S)
=
(h^\star,\Delta^\star).
\tag{GD-F2}
$$
^eq-frontier-fusion-transition

增广状态仍通过 $\operatorname{Commit}_v$ 一次提交：

$$
\widetilde S^+
=
\operatorname{Commit}_v(\widetilde S,\Delta^\star),
$$

并要求其因果前沿投影满足：

$$
\operatorname{frontier}(\widetilde S^+)
=
c_{v,\tau}^{\star}.
$$

若 $h^\star\neq\bot$，该时间戳只产生一个统一的所有者记录：

$$
Z_{v,\tau}^{\mathrm{front}}
=
\bigl((c_{v,\tau}^{\star},z^\star)\bigr),
\tag{GD-F3}
$$
^eq-frontier-owned-output

其中：

$$
z^\star
=
(h^\star,c_{v,\tau}^{\star})
\in
\mathcal Z_v,
$$

且该带所有者标签的记录满足：

$$
\operatorname{owner}(c_{v,\tau}^{\star},z^\star)
=
\operatorname{frontier}(z^\star)
=
c_{v,\tau}^{\star}.
$$

所有出站消息都继承这个所有者/因果前沿。原始 A/B 轨迹谱系可以保存在元数据中，但不再各自产生传播中的输出。该操作因此是一个明确的语义商，而不是对按所有者排序的或原子联合语义配置的免费重排。

#### 例 5.11a：A/B 统一发射与前状态污染

令 A、B 的令牌索引分别为：

$$
A=0,
\qquad
B=1.
$$

若同刻收件箱只含 A/B，且前状态因果前沿不超过 B，则：

$$
c^\star
=
\max(c_v^{S,-},0,1)
=
1,
$$

所以联合计算可以只发射一个所有者/因果前沿都为 B 的输出。

若前状态已经受令牌 C 影响，且：

$$
C=2>B,
\qquad
c_v^{S,-}=2,
$$

则：

$$
c^\star
=
\max(2,0,1)
=
2.
$$

此时数值计算即使当前只混合 A/B，也不能把输出标记为 B；必须标记为 C，或改用不含 C 的带版本的/带掩码的状态。

#### 定义 5.11b：因果前沿融合路由原语

定义节点 $v$ 的出边集合：

$$
\operatorname{Out}(v)
=
\{(v,u)\in E\}.
$$

因果前沿融合路由原语是确定函数：

$$
\operatorname{Route}_v^{\mathrm{front}}:
\mathbb N\times([L]\times\mathcal Z_v)
\to
2^{\operatorname{Out}(v)}.
$$

它只能读取绝对时间、统一的带所有者标签输出与静态参数；对 $z=\bot$ 返回空集。沿任一已选边生成的消息必须保留该输出的所有者/因果前沿，且消息标识符、元数据与载荷构造都必须是确定函数。第 6 节将在此原语上增加候选分数，并定义另外两种语义配置的选择器。

#### 引理 5.12：前缀因果组合

给定 $n\in\mathbb N_{>0}$。设语义对象：

$$
q_1,\ldots,q_n
$$

分别具有有效因果前沿：

$$
c_1,\ldots,c_n.
$$

若 $f$ 是不读取其他输入令牌数据的确定函数，令：

$$
q=f(q_1,\ldots,q_n)
$$

并定义：

$$
c^\star
=
\max_{1\leq i\leq n}c_i,
$$

则 $q$ 是 $c^\star$-前缀因果的。

**证明。**

取任意两个在前缀 $0{:}c^\star$ 上相同的输入序列。因为每个 $c_i\leq c^\star$，两次执行中所有 $q_i$ 都相同。$f$ 是确定函数且不读取其他令牌数据，所以两次得到的 $q$ 相同。

<div class="qed" aria-label="证毕">∎</div>

#### 定理 5.13：因果前沿融合的令牌前缀不变量

假设：

1. 初始状态因果前沿为 $-1$。
2. 定义 2.1c 的输入事件 $e_t^{\mathrm{in}}$ 的所有者支持集为 $\{t\}$，因果前沿为 $t$。
3. 每个数值计算核只读取其显式收件箱、前状态、静态参数与逻辑元数据；路由使用定义 5.11b 的纯函数。
4. 每次融合按式 [[#^eq-frontier-fusion-max|GD-F1]] 更新状态因果前沿，并按式 [[#^eq-frontier-owned-output|GD-F3]] 标记统一输出。

则任意因果前沿融合状态或消息若声明因果前沿/所有者为 $c$，其数值内容只依赖：

$$
x_0,\ldots,x_c.
$$

特别地，不会出现一个所有者为 A 的晚到信号读取 B 后仍继续标记为 A；它至少被提升到当前因果前沿。

**证明。**

沿绝对时间流式执行归纳。初始状态与令牌无关，所以因果前沿 $-1$ 有效；输入 $x_t$ 的因果前沿 $t$ 有效。

假设某次融合的前状态与全部收件箱消息都具有有效因果前沿。式 [[#^eq-frontier-fusion-max|GD-F1]] 取这些因果前沿的最大值 $c^\star$。由引理 5.12，$\mathcal F_v$ 产生的 $h^\star$、$\Delta^\star$ 与提交后的数值状态都是 $c^\star$-前缀因果的。式 [[#^eq-frontier-owned-output|GD-F3]] 又把输出所有者/因果前沿与 $c^\star$ 对齐，所以不变量被保持。

定义 5.11b 的路由原语是这些前缀因果输出、绝对时间与静态参数的确定函数，所以已选路由的存在性也保持同一个因果前沿上界。单位时延空间派发只复制已经有效的所有者/因果前沿标签，不读取新的令牌数据。对所有绝对时间及其中的节点事件重复上述论证，结论成立。

<div class="qed" aria-label="证毕">∎</div>

#### 推论 5.13a：依赖边上的因果前沿单调性

对因果前沿融合逻辑事件 $e$，使用定义 2.1a 的事件级因果前沿。输入事件取令牌索引；节点融合事件取式 GD-F1 的 $c_{v,\tau}^{\star}$；读出/采样事件取对应固定周期前缀索引。

在定理 5.13 的前提下，对因果前沿融合执行的任意逻辑依赖边：

$$
e\longrightarrow e',
$$

都有：

$$
\operatorname{frontier}(e)
\leq
\operatorname{frontier}(e').
$$

因此有限逻辑事件有向无环图可以先按因果前沿递增分组，再在同一因果前沿内取拓扑序；不存在从较大因果前沿指向较小因果前沿的依赖边。

**证明。**

空间派发保持所有者/因果前沿不变，所以空间依赖边上因果前沿相等。局部状态/融合依赖的输出因果前沿由式 [[#^eq-frontier-fusion-max|GD-F1]] 取所有输入与前状态因果前沿的最大值，所以不小于任一前驱的因果前沿。

对边界依赖，第 $t$ 个读出/采样事件的因果前沿都是 $t$；由式 GD-2.4，任何在 $\theta_t^{\mathrm{out}}$ 前可见的状态前驱，其因果前沿都不超过 $t$。自回归采样到下一输入的边从因果前沿 $t$ 指向 $t+1$。输入事件没有更早的令牌数据前驱。

因此每条依赖边上因果前沿单调不减。把有限事件节点按因果前沿分组后，跨组边只会从较小组指向较大组；每个同因果前沿诱导子图仍是有向无环图，所以可在组内取拓扑序。

<div class="qed" aria-label="证毕">∎</div>

这个推论使因果前沿融合更容易嵌入 [[step-transition-mathematical-specification#定义 3.6a：logical event DAG program|令牌前缀逻辑事件有向无环图]]：因果前沿是因果依赖的令牌上界。但它仍不推出每个因果前沿/令牌恰好产生一个输出读出。

#### 命题 5.14：提升因果前沿不自动带来高性能预填充

式 [[#^eq-frontier-fusion-max|GD-F1]] 中的 $\max$ 是满足结合律的归约，可以低成本批量计算。但数值状态若按时间戳分组 $G_0,\ldots,G_{q-1}$ 满足：

$$
S_{j+1}=\Phi_{G_j}(S_j),
$$

则任意 $\Phi_{G_j}$ 仍形成：

$$
S_0\to S_1\to\cdots\to S_q
$$

的顺序依赖链。要获得 Transformer/Mamba 意义上的高性能分块预填充，还需要至少一种额外结构：

- $\Phi_{G_j}$ 有紧凑表示，并在函数组合下闭合，可用并行/分块扫描。
- 全部输出可由因果掩码、分段注意力或其他因果批量计算核联合计算。
- 节点转移是令牌局部/分组局部，不读取前序可变状态。

例如仿射递推：

$$
S_{j+1}=A_jS_j+b_j
$$

可以通过满足结合律的有序对组合做扫描；Mamba/SSM 属于这一方向。因果注意力则通过带掩码的批量计算核获得预填充。因果前沿归属解决的是因果标记问题，不替代这些数值收缩。

### 5.15 三种语义配置的边界

| 语义配置 | 同刻计算 | 出站所有者 | 所有者/因果前沿关系 | 高性能前提 |
| --- | --- | --- | --- | --- |
| 按所有者排序 | A 提交后 B 读取 | 保留轨迹所有者 | 跨时间所有者逆序可使因果前沿大于所有者；标签必须显式记录 | 因果批量/扫描 |
| 原子联合 | A/B 与前状态一次联合计算，保留按所有者输出 | 保留各轨迹所有者 | 任意联合甚至不保证同刻所有者前缀；需分别登记因果前沿 | 联合分块契约 |
| 因果前沿融合 | A/B 与前状态一次联合计算，只发射统一输出 | 提升为全部依赖的最大因果前沿 | 所有者与因果前沿对齐，并由定理 5.13 给出前缀上界 | 仍需扫描、因果批量或无状态分组计算核 |

## 6. 一般有向无环图上的路由

### 定义 6.1：局部候选分数

对节点 $v$ 在时间 $\tau$ 产生的非空带标签输出：

$$
(t,z),
\qquad
z=(h,c)\in H_v\times\mathbb F_L,
$$

以及每条出边 $(v,u)\in E$，定义：

$$
s_{v,\tau,t\to u}
=
g_{v\to u}(h)
+b_{v\to u}
+d_{v\to u}(t,\tau).
\tag{GD-11}
$$
^eq-general-routing-score

其中：

- $g_{v\to u}:H_v\to\mathbb R$ 是学习得到的内容分数。
- $b_{v\to u}\in\mathbb R$ 是静态的学习或配置偏置。
- $d_{v\to u}:[L]\times\mathbb N\to\mathbb R$ 是只读取所有者、绝对时间与边/节点静态配置的确定性先验。

三项都不读取此前令牌的实际硬路由计数。

### 定义 6.2：保持标签的纯选择器

按所有者排序的语义配置给定确定函数：

$$
\rho_v^{\mathrm{ord}}:
\mathbb N\times[L]\times\mathcal Z_v
\to
2^{\operatorname{Out}(v)},
$$

其中 $2^{\operatorname{Out}(v)}$ 表示 $\operatorname{Out}(v)$ 的幂集。

并定义：

$$
A_{v,\tau,t}
=
\rho_v^{\mathrm{ord}}(\tau,t,z)
\subseteq
\operatorname{Out}(v).
$$

要求 $\rho_v^{\mathrm{ord}}(\tau,t,\bot)=\varnothing$。

按所有者排序的语义配置中，$A_{v,\tau,t}$ 只能读取该所有者的 $z$ 与静态配置。需要由节点状态影响路由的信息，必须先由 $\mathcal T_v$ 显式写入 $z$ 的载荷；选择器不再隐式选择读取提交前还是提交后的状态视图。

令 $\mathcal A_v^\star$ 为所有有限的、按所有者索引的已选边集合元组：

$$
\bigl((t_1,A_1),\ldots,(t_m,A_m)\bigr),
\qquad
m\in\mathbb N_{>0},
\qquad
t_i\in[L],
\qquad
t_1<\cdots<t_m,
\qquad
A_i\subseteq\operatorname{Out}(v).
$$

原子联合语义配置给定确定函数：

$$
\rho_v^{\mathrm{joint}}:
\mathbb N\times\mathcal Z_v^\star
\to
\mathcal A_v^\star.
$$

它读取 $\tau$ 与整个 $Z_{v,\tau}^{\mathrm{joint}}$，并返回具有完全相同所有者键序列的已选边集合元组：

$$
\bigl((t,A_{v,\tau,t})\bigr)_{t\in O_{v,\tau}^{\uparrow}}
=
\rho_v^{\mathrm{joint}}
\left(
\tau,Z_{v,\tau}^{\mathrm{joint}}
\right).
$$

因此联合选择器可以比较同刻多个带所有者标签的隐藏表示，但联合转移的前状态和后状态可见性已经在 $Z_{v,\tau}^{\mathrm{joint}}$ 的定义中固定，不由选择器临时决定。

因果前沿融合语义配置只有一个统一记录：

$$
(t,z)
=
\left(
c_{v,\tau}^{\star},
z^\star
\right),
$$

因果前沿融合语义配置使用定义 5.11b 的路由原语，并只对该统一记录选择：

$$
A_{v,\tau,t}
=
\operatorname{Route}_v^{\mathrm{front}}(\tau,(t,z)).
$$

无论使用哪种语义配置，选择器都必须：

- 确定性处理并列消解。
- 只选择 $v$ 的出站边。
- 对每个出站消息保留节点输出已声明的所有者/因果前沿标签；所有者提升只能发生在定义 5.11 的融合转移内。
- 不根据路由结果追溯修改已经提交的同刻节点状态，除非这种修改已写入节点转移契约。

若选择器具有可变状态，该状态必须有唯一所有者节点，并纳入 $\widetilde{\mathcal S}_v$ 以及第 7 节定义的节点参考/分块契约。这足以定义正确性，但不自动提供高性能。严格高性能语义配置进一步要求：`affectcount/selectcount` 一类跨事件反馈要么删除，要么给出独立的扫描/批量收缩证明。

### 定义 6.3：已选载荷派发

若带标签输出为 $(t,z)$、$z=(h,c)$，且 $(v,u)\in A_{v,\tau,t}$，给定载荷子类型 $\mathcal P_{v\to u}\subseteq\mathcal P$ 与投影 $P_{v\to u}:H_v\to\mathcal P_{v\to u}$，定义：

$$
p'
=
P_{v\to u}(h),
$$

并发出满足式 [[#^eq-unit-delay-dispatch|GD-3]] 的消息：

$$
m'
=
(\iota',t,c,(\tau+1,i_{\mathrm{arrive}}),v,u,\mu',p').
$$

其中 $\iota'\in\mathsf{MID}$ 与 $\mu'\in\mathcal U$ 必须由源事件标识符、已选边、所有者/因果前沿、来源槽位与谱系等已声明字段确定性生成，不能依赖物理线程竞争顺序。

不同所有者可以选择同一边。它们仍是所有者不同的两条消息。

### 备注 6.4：A 影响后续路由的三条语义路径

按所有者排序的语义配置中，A 可以先更新节点持有的状态，B 再读取该状态：

$$
x_A
\to
S_A
\to
h_B
\to
A_{v,\tau,B}.
$$

原子联合语义配置中，A 的当前输入可以通过联合算子直接影响 B 的隐藏表示或路由：

$$
(x_A,x_B,S)
\to
\mathcal J_v
\to
h_B
\to
A_{v,\tau,B}.
$$

前两条路径语义不同，实验时不能只看最终状态后把它们视为同一个模型。

因果前沿融合语义配置不再保留 A/B 两条出站轨迹，而是：

$$
(I_A,I_B,S)
\to
\mathcal F_v
\to
(h^\star,c^\star)
\to
A_{v,\tau,c^\star}.
$$

若 $c^\star=B$，则统一发射归属 B；若前状态已受 C 影响且 $C>B$，则发射必须归属 C。

## 7. 类型化逻辑事件、节点流与分块契约

### 定义 7.1：语义配置专属的逻辑事件

取语义配置：

$$
P\in\{\mathrm{ord},\mathrm{joint},\mathrm{front}\}.
$$

定义事件种类集合：

$$
\mathcal K^P
=
\mathcal K_{\mathrm{bdry}}
\cup
\{\mathtt{node}_P\}.
$$

语义配置 $P$ 的事件是定义 2.1a 的逻辑事件实例，并取 $\mathcal K=\mathcal K^P$。为便于阅读，后文把它的事件头继续写成：

$$
h_e
=
(\eta,\kappa,\ell,\theta,\Omega,c),
\tag{GD-E1}
$$
^eq-logical-event-instance

该事件头是 [[step-transition-mathematical-specification#定义 3.6a：logical event DAG program|定义 3.6a]] 的固定周期 Tide 实例化：$\theta$ 对应抽象逻辑时间戳，$\Omega$ 对应支持集，$c$ 对应因果前沿。每个事件的值 $\nu(e)$ 与事件头一起满足定义 2.1a 和式 GD-2.4。事件级因果前沿 $c$ 是整个事件值的有效保守上界；值内的单个隐藏表示、状态或消息产物可以登记不大于 $c$ 的更紧因果前沿。

实际事件集合只登记真正发生的事件。选择器不选择某条边时，相应节点事件的路由集合中没有该边，也不会产生该出站消息；不会为“未发生的下游事件”伪造一个值为 $\bot$ 的事件。另一方面，已经发生的节点事件可以包含 $\bot$ 隐藏表示分量，表示该转移已执行但没有产生路由可见的隐藏表示。

本文使用以下事件实例：

1. 对每个 $t\in[L]$，使用定义 2.1c 的输入事件头 $h_{e_t^{\mathrm{in}}}$。

2. 对非空常规收件箱分组：按所有者排序的语义配置为每个 $(v,\tau,t)$ 建立一个事件，其提交时间戳为 $(\tau,i_{\mathrm{commit}})$、所有者支持集为 $\{t\}$；联合/因果前沿语义配置为每个 $(v,\tau)$ 建立一个事件，所有者支持集为 $\mathcal O_{v,\tau}$。其事件级因果前沿必须是该事件值的有效上界；因果前沿融合语义配置取式 GD-F1 的 $c_{v,\tau}^{\star}$。

3. 对每个 $t\in[L]$，使用定义 2.1c 的固定读出事件头 $h_{e_t^{\mathrm{out}}}$。

读出事件对每个 $t$ 必定存在，不能被选择器取消、推迟或改写时间戳。

4. 自回归执行额外包含定义 2.1c 的采样事件头 $h_{e_t^{\mathrm{sample}}}$。

教师强制分块定理不需要采样事件；它把 $x_{0:L}$ 作为边界数据。

事件值空间必须按种类显式登记：输入事件值包含边界注入记录 $b_t^{\mathrm{in}}$；输入/节点事件值还至少包含带标签隐藏表示、已提交的状态版本、路由记录与已派发的消息；$\nu(e_t^{\mathrm{out}})=y_t\in Y$；$\nu(e_t^{\mathrm{sample}})=\operatorname{SelectToken}(y_t)\in X$。实现不能把这些参考语义可见的产物隐藏为未比较的副作用。

### 定义 7.2：直接依赖与依赖完备性

给定一次已经实例化的有限参考执行，其事件集合记为：

$$
\mathcal E_L^P.
$$

定义直接依赖关系：

$$
\mathcal A_L^P
\subseteq
\mathcal E_L^P\times\mathcal E_L^P,
$$

为包含下列边的最小关系：

1. **消息边**：若事件 $e$ 派发的消息被事件 $e'$ 的收件箱消费，则 $(e,e')\in\mathcal A_L^P$。输入事件产生的第一跳消息也使用该规则。
2. **状态边**：若同一节点的事件 $e'$ 读取事件 $e$ 提交后的状态版本，且中间没有其他覆盖该版本的提交，则 $(e,e')\in\mathcal A_L^P$。
3. **读出边**：若 $e$ 是输出节点 $z$ 在 $\theta_t^{\mathrm{out}}$ 之前的最后一个状态提交事件，则 $(e,e_t^{\mathrm{out}})\in\mathcal A_L^P$；若不存在这样的事件，读出使用边界初始状态。
4. **自回归边界边**：在纯推理中，$(e_t^{\mathrm{out}},e_t^{\mathrm{sample}})\in\mathcal A_L^P$，并且当 $t+1\in[L]$ 时，$(e_t^{\mathrm{sample}},e_{t+1}^{\mathrm{in}})\in\mathcal A_L^P$。

若选择器被细化为独立事件，则选择器值到路由或消息产生事件的控制边也必须加入 $\mathcal A_L^P$。本文默认选择器是相应节点事件的内部原语；已选路由集合与每条可选出站消息都属于该节点事件值，不能依赖未声明的全局状态。某个下游常规事件是否实例化，由其收件箱是否非空决定；该收件箱中每条消息都必须通过消息边追溯到源事件。

定义事件图：

$$
D_L^P
=
(\mathcal E_L^P,\mathcal A_L^P).
$$

称 $D_L^P$ 依赖完备，当且仅当任何被实际执行读取、且可能改变事件头、事件值、状态版本、路由、消息或读出的参考依赖，都由 $\mathcal A_L^P$ 中的一条边、显式边界数据参数，或事件局部原语内部已声明的顺序表示。未选择的路由/消息以源事件值中的空集合或缺失可选记录表示，不额外建立值为 $\bot$ 的事件节点。

对 $e\in\mathcal E_L^P$，定义：

$$
\operatorname{Pred}(e)
=
\{e'\in\mathcal E_L^P\mid(e',e)\in\mathcal A_L^P\}.
$$

对每个事件 $e$，给定显式声明的边界数据空间 $\mathcal B_e$。它只能包含该事件允许读取的输入令牌前缀、其位置的初始状态投影、静态参数与逻辑元数据。给定确定性事件函数：

$$
F_e:
\{h_e\}
\times
\left(
\prod_{e'\in\operatorname{Pred}(e)}\mathcal V_{e'}
\right)
\times\mathcal B_e
\to
\mathcal V_e,
$$

并要求 $F_e$ 只读取式 GD-E1 的事件头 $h_e$、直接前驱与已声明边界数据。事件头不是额外的令牌数据通道：其中任何会随执行改变的支持集、因果前沿或标识符字段，都必须由直接前驱记录与静态规范化规则唯一导出；不能把未声明的数值信息编码进事件标识符或元数据。较粗事件若在物理实现中展开为多个操作，必须先细化为依赖完备的逻辑子事件有向无环图，或给出融合原语保持语义的证明。

对本文严格 Tide 语义配置，只有 $e_t^{\mathrm{in}}$ 可以从 $X^L$ 直接读取 $x_t$。常规节点事件只能通过入站消息、局部状态前驱、静态参数与逻辑元数据获得依赖令牌的信息；读出事件只能读取式 GD-E3 指定的输出节点状态快照；采样事件只能读取对应读出值与静态选择参数。

### 定义 7.3：完整节点输入流

对每个非空常规时间戳分组，定义：

$$
E_{v,\tau}
=
\left(
q_R(\tau),
r_R(\tau),
I_{v,\tau},
B_{v,\tau}
\right).
$$

定义常规分组记录的执行时间戳：

$$
\theta_{v,\tau}^{\mathrm{step}}
=
(\tau,i_{\mathrm{step}}).
$$

对节点 $v$，把全部常规分组记录与仅在 $v=s$ 时存在的注入记录合并，并按 $<_{\Theta}$ 排列，得到完整节点输入流：

$$
\mathbf U_v.
$$

更明确地，$\mathbf U_v$ 的记录集合为：

$$
\left\{
(\theta_{v,\tau}^{\mathrm{step}},E_{v,\tau})
\mid I_{v,\tau}\neq\varnothing
\right\}
$$

与：

$$
\left\{
(\theta_t^{\mathrm{in}},b_t^{\mathrm{in}})
\mid t\in[L],\ v=s
\right\}
$$

的不交并。由引理 4.5 与引理 4.6，$\mathbf U_v$ 是有限序列。

### 定义 7.4：节点参考转导器与提交轨迹

给定输入节点的注入转移：

$$
\mathcal I_s:
[L]\times X\times\widetilde{\mathcal S}_s
\to
\mathcal Z_s\times\widetilde{\mathcal S}_s.
$$

若 $\mathcal I_s$ 对令牌 $t$ 返回非空带标签隐藏表示 $z$，则输入事件的带所有者标签的输出为 $(t,z)$，并必须满足 $t\leq\operatorname{frontier}(z)$。

节点参考转导器 $\operatorname{Ref}_v^P$ 按 $\mathbf U_v$ 的时间戳顺序处理记录：

- 注入记录使用 $\mathcal I_s$。
- 若 $P=\mathrm{ord}$，常规分组使用式 [[#^eq-owner-ordered-group|GD-7]]。
- 若 $P=\mathrm{joint}$，常规分组使用式 [[#^eq-atomic-joint-transition|GD-8]] 与式 [[#^eq-atomic-joint-commit|GD-9]]。
- 若 $P=\mathrm{front}$，常规分组使用式 [[#^eq-frontier-fusion-transition|GD-F2]] 与式 [[#^eq-frontier-owned-output|GD-F3]]。
- 每个带标签输出经过第 6 节选择器与单位时延派发。

每次状态更新都产生一个提交记录：

$$
q=(\eta_q,\chi_q,\widetilde S_v^q),
$$

其中 $\chi_q\in\mathbb N\times\{0,\ldots,N_{\mathrm{phase}}-1\}\times\mathbb N$ 是完整提交次序键。常规所有者事件使用 $\chi_q=(\tau,i_{\mathrm{commit}},t)$；联合/因果前沿事件使用 $\chi_q=(\tau,i_{\mathrm{commit}},0)$；注入转移使用 $\chi_q=(Rt,i_{\mathrm{inject}},t)$。若 $\chi_q=(\tau_q,i_q,j_q)$，定义提交时间戳投影：

$$
\operatorname{ctime}(q)=(\tau_q,i_q)\in\Theta.
$$

按 $\chi_q$ 的字典序次序排列全部提交记录，得到状态提交轨迹 $\mathbf Q_v^P$。

定义：

$$
\operatorname{Ref}_v^P(\mathbf U_v,\widetilde S_v^0)
=
\left(
\mathbf H_v^P,
\mathbf Q_v^P,
\mathbf R_v^P,
\mathbf M_{v,\mathrm{out}}^P,
\widetilde S_v^{P,\mathrm{final}}
\right).
\tag{GD-E2}
$$
^eq-node-reference-artifacts

五项依次是带标签隐藏表示记录、完整状态提交轨迹、路由记录、出站消息流与最终增广状态。

上述四类记录流都必须使用规范逻辑次序：先按源事件的提交键，再按所有者、边标识符与确定性记录/消息标识符排序。它们不能按物理线程完成或缓冲区追加的先后顺序排列；否则式 GD-E2 与 GD-12 中的序列相等没有确定含义。

### 定义 7.5：固定周期读出

给定读出函数：

$$
\rho_z:
[L]\times\widetilde{\mathcal S}_z
\to Y.
$$

任何读出所需的隐藏表示/输出寄存器都必须是 $\mathcal S_z$ 的显式组件，不能作为 $\rho_z$ 的隐藏全局输入。

对任意时间戳 $\theta$，定义：

$$
\mathbf Q_z^{P,<\theta}
=
\{q\in\mathbf Q_z^P\mid\operatorname{ctime}(q)<_{\Theta}\theta\}.
$$

若该集合非空，在其中按完整 $\chi_q$ 次序取最后一个提交记录，并把其增广状态定义为 $\widetilde S_z^{<\theta}$；若集合为空，则定义 $\widetilde S_z^{<\theta}=\widetilde S_z^0$。

第 $t$ 个固定周期读出定义为：

$$
y_t
=
\rho_z
\left(
t,
\widetilde S_z^{<\theta_t^{\mathrm{out}}}
\right).
\tag{GD-E3}
$$
^eq-fixed-period-readout

定义读出序列：

$$
y_{0:L}=(y_0,\ldots,y_{L-1})\in Y^L.
$$

式 GD-E3 对每个 $t\in[L]$ 必须执行一次。长路径消息若在 $\theta_t^{\mathrm{out}}$ 之后才提交，只能影响后续读出，不能追溯修改 $y_t$。

### 定义 7.6：节点事件流分块算子

节点 $v$ 在语义配置 $P$ 下的分块算子是函数：

$$
\mathcal C_v^P:
(\mathbf U_v,\widetilde S_v^0)
\mapsto
\left(
\widehat{\mathbf H}_v^P,
\widehat{\mathbf Q}_v^P,
\widehat{\mathbf R}_v^P,
\widehat{\mathbf M}_{v,\mathrm{out}}^P,
\widehat{\widetilde S}_v^{P,\mathrm{final}}
\right).
$$

称它满足精确节点分块契约，当且仅当对任意有限合法节点输入流：

$$
\mathcal C_v^P(\mathbf U_v,\widetilde S_v^0)
=
\operatorname{Ref}_v^P(\mathbf U_v,\widetilde S_v^0).
\tag{GD-12}
$$
^eq-node-event-stream-contract

等式比较式 GD-E2 的全部五类产物。特别地，只比较最终状态或最终输出逻辑值不足以证明该契约。

### 引理 7.7：有限参考执行的事件有向无环图

在引理 4.6 的条件下，给定任意语义配置 $P$，教师强制事件图 $D_L^P$ 是有限有向无环图。若再加入定义 7.1 的采样事件与自回归边界边，有限前缀的自回归事件图仍是有向无环图。

**证明。**

由引理 4.6，消息与常规节点事件数有限；输入、读出与采样事件各至多 $L$ 个，所以事件集合有限。

给每个事件定义字典序等级。注入、读出与采样事件使用其 $\Theta$ 时间戳，并追加并列消解坐标 $0$。按所有者排序的节点事件使用：

$$
\operatorname{rank}(e_{v,\tau,t})
=
(\tau,i_{\mathrm{commit}},t).
$$

联合/因果前沿节点事件使用：

$$
\operatorname{rank}(e_{v,\tau})
=
(\tau,i_{\mathrm{commit}},0).
$$

消息边把轮次从 $\tau$ 推进到 $\tau+1$。局部状态边按节点参考次序指向更大的时间戳，或在按所有者排序的同刻分组内指向更大的所有者索引。读出边由式 GD-0.3 从提交阶段指向读出阶段。自回归边界边由式 GD-0.4 从读出指向采样，再指向下一注入。每类边都严格增加等级，所以不存在有向环。

<div class="qed" aria-label="证毕">∎</div>

### 例 7.8：计算核族与分块实现映射

| 节点计算核 | 逻辑事件语义 | 可能的分块实现 |
| --- | --- | --- |
| 逐令牌映射 / FFN | 事件独立读取各自输入 | 批量化矩阵乘 / 融合的逐元素计算 |
| 因果注意力 | 事件值只读取允许的因果前缀 | 紧凑打包 QKV + 因果掩码 / 融合的注意力 |
| Mamba/SSM | 状态边形成仿射/选择性递推 | 并行/分块扫描或选择性扫描计算核 |
| 线性注意力 | 前缀累加器状态边 | 满足结合律的扫描 / 分块累加器 |
| 同轮次集合交互 | 原子联合节点事件 | 分段集合计算核 / 分组注意力 |
| 由因果前沿归属的状态融合 | 同刻多重集与前状态产生一个事件值 | 分段归约 + 扫描/因果批量计算核 |
| 任意黑盒转移 | 按依赖完备的事件次序 | 顺序回退；只证明正确性 |

分块实现映射可以按 $(\tau,q_R(\tau),r_R(\tau),t,c,\mu)$ 排序与打包，但必须保持式 GD-12 和全部直接依赖。

### 7.9 收件箱完备性与节点内等待

在同步绝对时间参考中，每个内部轮次的阶段屏障直接保证收件箱分组完整，不需要水位标记作为模型语义。

异步物理运行时若要在没有全局屏障的情况下执行同一参考，可以使用水位标记、前驱完成信号或分块结束标记，证明不会再补来时间戳不超过某界的消息。水位标记是物理进度凭证，不是逻辑事件；只有当模型行为显式读取水位标记时，它才必须提升为控制事件。

即使完整 $\mathbf U_v$ 已一次性交给节点，状态边仍可能形成顺序依赖。分块算子可以使用批量化映射、扫描、带掩码的批量计算核，或在没有收缩时使用节点局部顺序循环。后者仍可满足 GD-12，但节点局部并行跨度可以是 $\Theta(M_v)$。

如果生成 $\mathbf U_v$ 必须先读取 $v$ 自己尚未产生的输出、沿空间环返回的消息，或未纳入事件图的共享可变选择器状态，则节点拓扑序分解失败。本页的空间有向无环图、唯一状态所有者与仅向前路由正是用于排除这类循环就绪依赖。

## 8. 流式调度与节点拓扑序分块调度

### 定义 8.1：绝对时间流式调度

若 $L=0$，执行没有输入注入，所有节点保持初始状态。若 $L>0$，流式参考按：

$$
\tau=0,1,\ldots,H_L,
$$

推进，其中：

$$
H_L
=
R(L-1)+D.
\tag{GD-8.1}
$$
^eq-streaming-horizon

由 $R=d_{\min}\leq D$，有 $RL\leq H_L$，所以最后一个固定读出轮次 $RL$ 已包含在该时间范围内。

本定义采用 **封闭有限执行**：在第 $L-1$ 个读出后不再注入新令牌，但继续执行到 $H_L$，使这 $L$ 个注入已经产生的所有空间消息都被消费或显式终止。因此本节得到的最终节点状态是冲刷后状态，不是假想的下一注入边界 $RL$ 上、仍保留在途消息的延续状态。后者必须把边界状态快照与在途消息多重集一起定义，属于风险九所述的下一步嵌入定理。

在每个绝对轮次 $\tau$，严格按定义 0.3 的阶段次序执行：

1. 在 $i_{\mathrm{arrive}}$ 收集到达时间戳为 $(\tau,i_{\mathrm{arrive}})$ 的消息，构造 $I_{v,\tau,t}$、$I_{v,\tau}$ 与 $B_{v,\tau}$。
2. 在 $i_{\mathrm{step}}$ 执行全部非空常规节点分组，并在 $i_{\mathrm{commit}}$ 提交状态、路由与出站消息记录。
3. 若存在 $t\in[L]$ 满足 $\tau=R(t+1)$，在 $i_{\mathrm{read}}$ 执行固定读出事件 $e_t^{\mathrm{out}}$；自回归执行随后在 $i_{\mathrm{sample}}$ 执行 $e_t^{\mathrm{sample}}$。
4. 若存在 $t\in[L]$ 满足 $\tau=Rt$，在 $i_{\mathrm{inject}}$ 执行输入事件 $e_t^{\mathrm{in}}$。教师强制参考读取给定 $x_t$；自回归参考对 $t>0$ 读取前一采样事件的值。
5. 本轮次派发的空间消息按式 GD-3 在 $(\tau+1,i_{\mathrm{arrive}})$ 到达。

每个固定读出都按式 GD-E3 读取提交轨迹快照。因为每条边时延为 $1$，同一个轮次内不存在从一个空间节点到另一个空间节点的零时延消息依赖。

### 定义 8.2：空间拓扑序

空间有向无环图的拓扑序是元组：

$$
\pi=(v_1,v_2,\ldots,v_N),
\qquad N=|V|,
$$

满足每个节点恰好出现一次，并且：

$$
(v_i,v_j)\in E
\quad\Longrightarrow\quad
i<j.
$$

有限有向无环图至少存在一个拓扑序。

### 定义 8.3：节点拓扑序分块调度

给定教师强制边界序列 $x_{0:L}$ 与拓扑序 $\pi$。分块调度依次处理：

$$
v_1,v_2,\ldots,v_N.
$$

处理节点 $v_i$ 时：

1. 它的所有空间前驱已经完成。
2. 从所有前驱出站流合并常规收件箱分组；若 $v_i=s$，再加入固定注入记录，得到完整 $\mathbf U_{v_i}$。
3. 调用 $\mathcal C_{v_i}^P$ 一次处理整条节点输入流。
4. 把得到的出站消息加入空间后继的待处理收件箱。

全部节点完成后，使用 $\widehat{\mathbf Q}_z^P$ 按式 GD-E3 计算固定读出序列。互不依赖的节点可以并行执行；元组 $\pi$ 只用于定义一种合法顺序。

### 定理 8.4：固定周期一般有向无环图调度等价定理

给定任意有限输入分块、任意语义配置：

$$
P\in\{\mathrm{ord},\mathrm{joint},\mathrm{front}\},
$$

并假设：

1. 空间图 $G$ 满足定义 1.1，不要求 $\Lambda(v)$ 为单元素集合。
2. 固定周期满足 $R=d_{\min}$，注入/读出/采样阶段满足式 GD-0.3 与 GD-0.4。
3. 每条边满足单位时延派发，边界满足定义 4.2a 的跨边界延续语义。
4. 每条消息保留所有者、因果前沿、到达时间戳与消息标识符。
5. 收件箱聚合满足定义 4.4。
6. 每个可变状态位置有唯一所有者节点。
7. 路由只沿 $E$ 前进且是确定函数；任何可变路由状态都由唯一节点持有，并包含在该节点事件/值与分块契约中。
8. 事件图满足定义 7.2 的依赖完备性。
9. 每个节点的分块算子满足式 GD-12，并比较完整提交轨迹。
10. 执行满足引理 4.6 的有限事件条件。

则节点拓扑序分块调度与绝对时间流式调度产生完全相同的：

- 每个节点的带时间戳的收件箱。
- 每条所有者/带因果前沿标签的隐藏表示记录。
- 每个节点的完整状态提交轨迹。
- 已选路由。
- 全部已派发的消息。
- 每个节点在封闭时间范围 $H_L$ 后的冲刷后最终上下文状态与状态因果前沿。
- 固定时间戳 $\theta_t^{\mathrm{out}}$ 上的读出序列 $y_{0:L}$。

因此教师强制流式与分块执行计算同一个封闭有限固定周期参考语义。

**证明。**

取空间有向无环图的任意拓扑序：

$$
\pi=(v_1,\ldots,v_N).
$$

由前提 6-8，每个节点的可变依赖都由该节点的增广状态、入站消息、静态参数与已声明边界数据给出；不存在跨节点的隐藏共享状态依赖。因此，一旦 $\mathbf U_v$ 与 $\widetilde S_v^0$ 相同，$\operatorname{Ref}_v^P$ 的全部产物就唯一确定。

对 $i=1,\ldots,N$ 做数学归纳，证明节点 $v_i$ 在两种调度中得到相同完整 $\mathbf U_{v_i}$，并产生式 GD-E2 的相同产物。

当 $i=1$ 时，$v_1=s$。定义 1.1 要求每个 $v\neq s$ 都位于一条从 $s$ 出发的非零长度路径上，所以它至少有一个空间前驱。另一方面，$s$ 不可能有入边：若 $(u,s)\in E$，则 $u$ 可从 $s$ 到达，进而形成从 $s$ 到 $u$ 再回到 $s$ 的有向环。因此 $s$ 是唯一入度为零的节点，任意拓扑序都以 $s$ 开始。输入节点的 $\mathbf U_s$ 在两种调度中都由同一组固定记录 $b_t^{\mathrm{in}}$ 构成。由式 GD-12，分块算子与流式参考转导器产生相同隐藏表示记录、提交轨迹、路由、出站消息与最终增广状态。

假设结论对 $v_1,\ldots,v_{i-1}$ 成立。考虑 $v_i$。由拓扑序的定义，$v_i$ 的每个直接前驱都位于：

$$
\{v_1,\ldots,v_{i-1}\}.
$$

由归纳假设，每个前驱在两种调度中产生完全相同的出站消息流。因此，把所有目标为 $v_i$ 的消息按 $(\tau,t)$ 分桶后，得到相同的：

$$
I_{v_i,\tau,t},
$$

相同的原始多重集 $I_{v_i,\tau}$、所有者元组 $B_{v_i,\tau}$，以及相同的完整节点输入流 $\mathbf U_{v_i}$。

在流式调度中，节点 $v_i$ 按参考事件次序对 $\mathbf U_{v_i}$ 执行 $\operatorname{Ref}_{v_i}^P$。在分块调度中，它执行 $\mathcal C_{v_i}^P$。由式 GD-12，两者产生式 GD-E2 的全部相同产物。

所以结论对 $v_i$ 成立。由数学归纳法，结论对所有节点成立，特别地 $\mathbf Q_z^P=\widehat{\mathbf Q}_z^P$。对每个 $t\in[L]$ 应用同一个式 GD-E3，得到相同 $y_t$。

证明中没有使用“所有到达同一节点的路径等长”，所以一般有向无环图中的路径长度碰撞被完整保留，而不是通过中继节点消除。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.4a：固定周期读出不被长路径追溯修改

在定理 8.4 的条件下，任意到达/提交时间戳晚于 $\theta_t^{\mathrm{out}}$ 的事件都不会改变 $y_t$，但可以通过后续状态边影响 $y_{t+1},y_{t+2},\ldots$。

**证明。**

由式 GD-E3，$y_t$ 只读取 $\theta_t^{\mathrm{out}}$ 之前的最后已提交的状态。更晚事件不属于该快照；后续读出使用更晚快照，因而仍可读取其影响。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.5：按所有者排序配置的正确性

若每个节点的分块算子精确实现按所有者排序的事件流折叠，则节点拓扑序分块执行与按所有者排序的绝对时间流式参考等价。

**证明。**

在定理 8.4 中取 $P=\mathrm{ord}$。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.6：原子联合配置的正确性

若每个节点的分块算子精确实现原子联合时间戳转移，则节点拓扑序分块执行与原子联合绝对时间流式参考等价。

**证明。**

在定理 8.4 中取 $P=\mathrm{joint}$。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.6a：因果前沿融合配置的正确性

若每个节点的分块算子精确实现由因果前沿归属的原子融合事件流转移，则节点拓扑序分块执行与因果前沿融合绝对时间流式参考等价，并在定理 5.13 的前提下保持令牌前缀因果前沿不变量。

**证明。**

在定理 8.4 中取 $P=\mathrm{front}$，得到调度等价；再应用定理 5.13，得到因果前沿不变量。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.7：折叠等价的联合实现映射

若每个节点的联合算子还满足式 [[#^eq-joint-ordered-equivalence|GD-10]]，则联合分块执行、按所有者排序的分块执行与按所有者排序的流式参考三者等价。

**证明。**

由命题 5.8，每个时间戳分组上联合与有序产物相同。对每个节点的时间戳流归纳，可得两种节点参考转导器相同。再分别应用推论 8.5 与推论 8.6。

<div class="qed" aria-label="证毕">∎</div>

### 推论 8.8：等长路径模型是本定理的特殊情形

若对每个节点 $v$，存在唯一 $d(v)$ 使：

$$
\Lambda(v)=\{d(v)\},
$$

则令牌 $t$ 的任意轨迹消息到达 $v$ 的轮次唯一为 $Rt+d(v)$；不同轨迹所有者不会在同一 $v$、同一到达轮次到达。定理 8.4 仍然成立，并在按所有者排序或原子联合语义配置中退化为等层有向无环图的调度等价结论；因果前沿融合语义配置仍可因持久状态依赖发生所有者提升。

**证明。**

由式 GD-2.1，任意从令牌 $t$ 注入并到达 $v$ 的轨迹路径都有 $\tau=Rt+d(v)$。若 $t\neq t'$：

$$
Rt+d(v)
\neq
Rt'+d(v),
$$

所以不存在同刻轨迹所有者碰撞。其余结论直接由定理 8.4 得到。

<div class="qed" aria-label="证毕">∎</div>

## 9. 正确性之外：工作量、并行跨度与超稀疏约束

### 9.0 三层性能目标

本文把“支持分块预填充”拆成三个不能混用的层级：

| 层级 | 要求 | 允许的节点内实现 | 本页状态 |
| --- | --- | --- | --- |
| 封闭有限精确分块正确性 | 一次分块调用与封闭有限逐时间戳参考产物完全相同 | 包括顺序回退 | 由定理 8.4 归约到节点契约 |
| 节点局部分块吞吐量 | 一个节点一次或少量调用处理完整多令牌 / 多轮次流；本地打包，批量收发边消息，无逐令牌全局编排 | 普通 C++/设备循环、分支、取分数最高的若干项、聚集/分散、局部矩阵计算核均可 | Tide 当前首要性能目标 |
| 序列轴低并行跨度 | 跨令牌/事件依赖可被收缩，不保留长度随分块线性增长的关键路径 | 令牌局部映射、因果注意力、扫描、分段批量等 | 更强的可选目标，需逐计算核证明 |

在默认恒等空闲语义下，固定周期 $R$ 不会自动破坏前两层；它只决定注入/读出的截止时间与每个节点的带时间戳事件流。若空时间戳也执行非平凡衰减/更新，其工作量/并行跨度必须另行计入。真正阻止第三层的是节点局部状态/控制转移缺少可组合结构，而不是“一个外部周期含 $R$ 个内部轮次”这一事实本身。

因此，若每个节点映射到独立设备，合理的第一阶段实现是：空间前驱批量生成完整或分块事件流，节点在本设备内对这些记录做排序/分段/打包后一次处理，再批量派发。节点内某些选择器/路由代码即使只能顺序执行，也不要求运行时回到逐令牌的跨设备控制循环；但它的实际并行跨度与吞吐必须诚实计入性能报告。

### 定义 9.1：节点事件数

定义封闭执行的轮次索引集合：

$$
\mathbb T_L
=
\begin{cases}
\varnothing,&L=0,\\
\{0,\ldots,H_L\},&L>0.
\end{cases}
$$

定义节点 $v$ 的所有者事件数：

$$
M_v
=
\sum_{\tau\in\mathbb T_L}|\mathcal O_{v,\tau}|.
$$

定义全图所有者事件数：

$$
M
=
\sum_{v\in V}M_v.
$$

令 $\mathcal M_{\mathrm{dispatch}}$ 为执行中全部已派发的消息的集合，定义其消息总数：

$$
N_{\mathrm{msg}}
=
\left|\mathcal M_{\mathrm{dispatch}}\right|.
$$

原子联合与因果前沿融合语义配置的时间戳分组数可能小于 $M_v$，但联合/融合计算核的工作量必须计入它读取的全部原始消息与所有者记录。

定义实际常规节点事件数：

$$
M_{\mathrm{node}}^P
=
\begin{cases}
M,&P=\mathrm{ord},\\
\displaystyle\sum_{v\in V}
\left|\{\tau\in\mathbb T_L\mid I_{v,\tau}\neq\varnothing\}\right|,
&P\in\{\mathrm{joint},\mathrm{front}\}.
\end{cases}
$$

教师强制执行还固定包含 $L$ 个注入事件与 $L$ 个读出事件。因此若把全部逻辑事件计入，定义：

$$
M_{\mathrm{all}}^{\mathrm{TF}}
=
M_{\mathrm{node}}^P+2L,
$$

其中 $M_{\mathrm{node}}^P$ 是按所选语义配置实际建立的常规节点事件数。自回归有限前缀另增加 $L$ 个采样事件。性能报告不能把这些边界事件、提交轨迹或读出成本视为免费。

### 定义 9.2：节点分块工作量与并行跨度

记节点 $v$ 的分块算子工作量上界与并行跨度上界分别为：

$$
W_v,
\qquad
P_v.
$$

工作量是总原语操作数的抽象；并行跨度是在依赖关系与无限处理器理想化下的关键路径长度。二者都是性能见证，不属于定理 8.4 的正确性结论。

### 命题 9.3：粗粒度节点拓扑序工作量/并行跨度上界

令 $W_{\mathrm{transport}}$ 表示全部已派发消息的序列化、传输、合并与物化工作量。节点拓扑序调度的总工作量满足：

$$
W_{\mathrm{graph}}
\leq
\sum_{v\in V}W_v
+W_{\mathrm{transport}}
+W_{\mathrm{out}}.
\tag{GD-13}
$$
^eq-general-dag-work

其中 $W_{\mathrm{out}}$ 是从输出节点提交轨迹计算并记录全部 $L$ 个固定读出的工作量。对每个节点 $v$，令 $C_v^{\mathrm{sched}}\geq 0$ 表示未包含在 $P_v$ 中的节点间流合并、传输与调度器并行跨度；令 $P_{\mathrm{out}}$ 表示同一读出阶段的并行跨度。若无依赖节点可并行，则粗粒度并行跨度满足：

$$
P_{\mathrm{graph}}
\leq
\max_{p}
\sum_{v\in p}
\bigl(P_v+C_v^{\mathrm{sched}}\bigr)
+P_{\mathrm{out}},
\tag{GD-14}
$$
^eq-general-dag-span

其中最大值遍历空间有向无环图的所有有向路径。

**证明。**

这里 $W_v$ 已包含节点局部收件箱聚合、转移、路由，以及输入节点对注入记录的处理。消息载荷大小、跨设备通信、全局排序或非线性索引构建的成本全部计入 $W_{\mathrm{transport}}$；固定读出函数 $\rho_z$ 与输出物化的全部成本计入 $W_{\mathrm{out}}$。把三类互不重叠的工作量相加即得式 GD-13。

分块调度的节点级依赖图就是空间有向无环图。任意节点计算关键路径对应其中一条有向路径；沿该路径累加每个节点的分块并行跨度与调度开销，再加入输出读出提取的并行跨度，得到式 GD-14。

<div class="qed" aria-label="证毕">∎</div>

这个命题解释了“一般有向无环图仍可能支持高性能分块预填充”的准确含义：

- 图级顺序深度由空间关键路径决定，而不是由令牌数直接决定。
- 但若某个 $P_v=\Theta(M_v)$ 且没有扫描/批量收缩，令牌轴顺序链只是被封装进节点计算核，并没有消失。
- 若 $M$ 本身因扇出指数增长，即使并行跨度较小，总工作量与内存占用仍不可接受。

### 定义 9.4：固定来源信号槽位

给定常数：

$$
K\in\mathbb N_{>0}.
$$

每个输入令牌 $b\in[L]$ 在注入时最多创建 $K$ 个不可变来源槽位：

$$
(b,q),
\qquad
q\in[K].
$$

这里 $b$ 是来源令牌，不随后续所有者/因果前沿提升改变。槽位标识符 $(b,q)$ 写入消息元数据。严格槽位语义配置要求：

- 每个槽位在任一时刻最多对应一条活跃传播中的消息。
- 一个槽位到达节点后，最多选择一条出边。
- 槽位可以终止或与其他槽位在节点内联合计算，但不能复制为两个同时活跃的同标识符槽位。
- 每个来源槽位在注入/分裂时至多初始化一次；终止后不能重新初始化或复用。已初始化槽位可以沿一条空间路径依次访问多个节点。
- 若需要分裂，只能从同一来源令牌从未激活过的固定槽位池中分配；新槽位从分裂节点开始一条新的单路径轨迹。
- 因果前沿融合可以消费多个入站来源槽位，并保留其中一个或若干已有槽位继续传播；不能因为所有者提升到更大的因果前沿而获得新的槽位池。

在该语义配置中，路由记录不再只是边集合，而是槽位到边的指派：

$$
A_{v,\tau}^{\mathrm{slot}}
\subseteq
([L]\times[K])
\times
\{(v,u)\in E\}.
$$

同一个来源槽位标识符在 $A_{v,\tau}^{\mathrm{slot}}$ 中至多出现一次。若多个槽位在同一事件分组中聚合，节点计算核必须显式给出哪些槽位合并、终止与继续传播；不能在丢失槽位恒等后仍声称满足槽位守恒。

### 命题 9.5：固定槽位的事件上界

在严格槽位语义配置中，每个来源令牌的全部槽位节点访问次数不超过：

$$
K|V|.
$$

长度为 $L$ 的分块的所有者事件总数满足：

$$
M\leq LK|V|.
\tag{GD-15}
$$
^eq-owner-slot-event-bound

**证明。**

每个来源槽位至多初始化一次，并且初始化后不复制，只沿一条路由路径前进。空间图无环，所以该路径最多访问每个节点一次，节点访问次数不超过 $|V|$。每个来源令牌最多有 $K$ 个槽位，因此其全部槽位访问次数不超过 $K|V|$。因果前沿提升只改变因果所有者标签，不创建来源槽位。每个所有者事件至少消费一次槽位访问，所以所有者事件数不超过槽位访问次数；对 $L$ 个来源令牌求和得到式 GD-15。

<div class="qed" aria-label="证毕">∎</div>

固定来源槽位不是唯一的稀疏设计，但它给出一个不依赖空间层级、所有者提升，也不需要跨令牌在线计数器的明确上界。若改为“每个事件独立选择分数最高的 $K$ 条出边”，最坏事件数可能随有向无环图深度指数增长，不能称为超稀疏保证。

## 10. 空间/时间均衡与选择器配置

### 定义 10.1：节点激活负载

在固定槽位语义配置中，定义：

$$
a_{b,q,v}
=
\begin{cases}
1,&\text{来源令牌 }b\text{ 的槽位 }q\text{ 访问节点 }v,\\
0,&\text{否则}.
\end{cases}
$$

定义长度为 $L$ 的节点负载：

$$
n_v^{(L)}
=
\sum_{b\in[L]}\sum_{q\in[K]}a_{b,q,v}.
\tag{GD-16}
$$
^eq-general-node-load

若不采用槽位语义配置，可以把 $n_v^{(L)}$ 改为到达 $v$ 的所有者事件数，但必须同时报告事件复制数量。

### 10.2 当前 LH 在线计数选择器

给定隐藏表示摘要空间 $\mathcal H$、控制状态空间 $\mathcal Q$ 与硬路由空间 $\mathcal R_{\mathrm{route}}$，以及确定函数：

$$
\rho:
\mathcal H\times\mathcal Q
\to
\mathcal R_{\mathrm{route}},
$$

$$
U:
\mathcal Q\times\mathcal R_{\mathrm{route}}
\to
\mathcal Q.
$$

给定有限事件数 $J\in\mathbb N_{>0}$。对按参考次序排列的 $j\in[J]$，当前 LH 风格的选择器可以抽象为：

$$
R_j=\rho(H_j,Q_j),
$$

$$
Q_{j+1}=U(Q_j,R_j),
$$

其中第二式只对 $j+1\in[J]$ 使用；$H_j\in\mathcal H$、$Q_j\in\mathcal Q$、$R_j\in\mathcal R_{\mathrm{route}}$，且 $Q_j$ 包含 `affectcount/selectcount`。这可以直接惩罚近期热点，但形成：

$$
Q_0\to R_0\to Q_1\to R_1\to\cdots.
$$

若 $j$ 沿令牌轴或事件轴增长，且组合转移不具有已证明的扫描或批量结构，就进入 [[adaptive-routing-prefill-impossibility]] 所述的自适应控制链。

### 命题 10.3：强在线反馈的依赖代价

如果后一个路由必须读取由前一个实际硬路由更新的控制状态，且该更新/路由组合没有额外已证明的收缩，则精确执行存在相应长度的顺序控制链。

**证明。**

后一个路由需要更新后的 $Q_{j+1}$；$Q_{j+1}$ 需要前一个硬路由 $R_j$；$R_j$ 又读取 $Q_j$。因此每一步都依赖前一步，得到上述控制链。

<div class="qed" aria-label="证毕">∎</div>

### 10.4 预填充兼容的均衡层

在严格语义配置中，均衡拆成以下互不替代的层：

| 层 | 方法 | 是否进入逐事件前向状态 |
| --- | --- | --- |
| 结构上界 | 固定来源槽位、有限出度、静态可用性 | 否 |
| 静态容量 | 边/节点偏置、设备容量权重、拓扑分区 | 否 |
| 确定性时间分散 | $d_{v\to u}(t,\tau)$ | 否 |
| 训练期均衡 | 节点负载 / 时间窗口损失 | 只影响梯度 |
| 在线硬均衡 | 持久路由计数器 | 是；通常形成控制链 |

给定目标节点容量权重：

$$
\pi_v>0,
\qquad
\sum_{v\in V}\pi_v=1,
$$

定义归一化实际负载：

$$
\widehat p_v
=
\frac{n_v^{(L)}}{\sum_{u\in V}n_u^{(L)}}.
$$

分母为 $0$ 时把损失定义为 $0$。空间均衡目标可以写为：

$$
\mathcal L_{\mathrm{space}}
=
\sum_{v\in V}
(\widehat p_v-\pi_v)^2.
\tag{GD-17}
$$
^eq-general-space-balance-loss

给定窗口宽度 $B\in\mathbb N_{>0}$。对每个 $j\in\mathbb N$，定义绝对时间窗口：

$$
W_j
=
\{jB,\ldots,(j+1)B-1\},
$$

可以统计到达时间落入 $W_j$ 的节点事件，构造 $\mathcal L_{\mathrm{time}}$。它约束真实流水线时间上的热点，而不是把外部令牌索引误当作唯一到达时间。

### 命题 10.5：跨令牌硬容量约束的三种基本选择

给定硬容量 $C\in\mathbb N$。若要求任意输入上、任意时间窗口内节点 $v$ 的硬准入不超过 $C$，而多个所有者都可能选择 $v$，则精确选择器至少采用以下一种机制：

1. 用静态资格约束/配额预先限制可选所有者/槽位。
2. 联合观察一个已知所有者/事件集合后做指派。
3. 在线维护已使用容量，让后续决策读取此前的准入结果。

第二种机制是否允许取决于参考语义：原子联合与因果前沿融合可以在同一时间戳分组内使用它，但不能免费跨越尚未形成的未来分组。第三种机制形成在线控制链。第一种最容易保持原生兼容严格预填充，但会限制内容路由的自由度。

**证明。**

若资格未预先限制，当超过 $C$ 个候选同时或先后希望进入 $v$ 时，选择器必须依据其他候选拒绝其中一部分。若同时观察一个已知集合后联合决定，属于第二类；若按到达顺序读取已用容量，属于第三类；剩余情形只能提前限制资格，属于第一类。

<div class="qed" aria-label="证毕">∎</div>

### 10.6 三种选择器配置

| 语义配置 | 状态与均衡 | 分块预填充位置 |
| --- | --- | --- |
| `LH-exact streaming` | 每次硬路由后更新持久计数 | 保留原行为，但通常含长自适应链 |
| `General-DAG strict` | 固定来源槽位、静态偏置/先验、训练损失 | 满足定理 8.4 封闭有限正确性的候选 |
| `Block-lagged` | 分块内冻结计数器，分块后更新 | 分块内可批量，分块间仍顺序 |

## 11. 三种同刻/融合语义的实验设计

按所有者排序的、原子联合与因果前沿融合不应混成一个实验条件。前两种保留按所有者轨迹；第三种主动做语义商，并改变出站所有者。

### 11.1 必做正确性门槛

| 检查项 | 参考 | 分块候选 | 判定 |
| --- | --- | --- | --- |
| 有序标量 | 按 $(\tau,t)$ 顺序执行 | 紧凑打包/扫描/因果批量 | 全部产物相等 |
| 联合标量 | 按 $\tau$ 调用 $\mathcal J_v$ | 分组化/分段批量 | 全部产物相等 |
| 因果前沿融合标量 | 按 $\tau$ 调用 $\mathcal F_v$，统一发射 | 分段融合 + 扫描/因果批量 | 全部产物相等 |
| 因果前沿不变量 | 式 GD-F1 的标量传播 | 批量化最大值/因果前沿传播 | 所有输出/状态满足定理 5.13 |
| 联合对比有序 | 两套参考 | 直接比较 | 只在式 GD-10 成立时期待相等 |
| 融合对比按所有者处理 | 三套参考 | 直接比较 | 默认不期待相等；评估语义商的质量/效率 |
| 流式对比拓扑序 | 封闭有限绝对时间调度 | 节点拓扑序调度 | 定理 8.4 所列产物 |

产物相等至少包括：

- 按所有者/因果前沿隐藏表示。
- 完整状态提交轨迹与每次提交的次序键。
- 状态因果前沿。
- 已选边。
- 消息标识符、所有者、因果前沿、来源槽位、到达时间戳、目标与载荷。
- 最终节点状态。
- 每个固定 $\theta_t^{\mathrm{out}}$ 的读出 $y_t$。

### 11.2 最小诊断任务

1. **不等长路径碰撞**：直接边与两跳/三跳路径使多个所有者在同一节点、同一 $\tau$ 相遇。
2. **跨时间所有者逆序**：让 B 的短路径事件先于 A 的长路径事件到达，检查绝对时间状态可见性。
3. **状态因果前沿污染**：当前输入只有 A/B，但前状态因果前沿为 C>B；验证发射必须归属 C 而不是 B。
4. **因果前沿融合**：A/B 同刻联合计算，只发射一个所有者 B 的消息，并与按所有者联合输出比较。
5. **累加器反例**：复现实例 5.9，确保测试能发现“最终状态相同但按所有者输出不同”。
6. **因果注意力节点**：分别验证事件次序掩码与所有者次序掩码的标量/批量等价。
7. **SSM/线性注意力节点**：验证不规则事件流的紧凑打包扫描。
8. **联合交互节点**：让路由 B 显式依赖同刻 A 的特征，检查联合语义。
9. **稀疏来源槽位路由**：检查事件上界、槽位守恒、融合时的槽位消耗与输出可达性。
10. **双皮层有向无环图**：验证多路径输入皮层、单向桥接与输出皮层的完整拓扑执行。

### 11.3 性能与质量指标

- 输出与产物是否正确且相等。
- 所有者事件总数 $M$。
- 节点分块工作量与实测延迟。
- 图关键路径并行跨度。
- 打包利用率与填充浪费。
- 节点/边负载分布。
- 碰撞密度：同一 $(v,\tau)$ 中所有者数分布。
- 因果前沿提升距离与提升频率。
- 融合压缩比：原始所有者记录数 / 统一输出数。
- 路由稳定性与训练质量。
- 有序、联合与因果前沿融合语义配置的任务质量差异。

## 12. 对当前 LH/Tide 机制的迁移

| 当前机制 | 一般有向无环图严格语义配置的处理 |
| --- | --- |
| 输入/输出皮层 + 桥接 | 保留为定义 3.1 的可选空间结构 |
| 每条边的单位时延 | 直接保留 |
| 信号载荷 | 增加消息标识符、所有者、因果前沿、到达时间戳、来源槽位 |
| 外部令牌时钟 | 固定为 $Rt$ 注入与 $R(t+1)$ 读出，不由选择器/路由改写 |
| 同绝对内部轮次多源聚合 | 同时保留原始收件箱与所有者视图；选择有序、联合或因果前沿融合契约 |
| 局部隐藏表示/KV | 归入节点持有的状态与节点转导器 |
| `signal norm` | 作为式 GD-11 的局部内容特征 |
| `affectcount/selectcount` | 流式语义配置保留；严格语义配置改为日志、训练统计或静态偏置来源 |
| 持久公平次序 | 不进入严格精确前向路由 |
| `clear_after_activation` | 必须成为节点转移的显式状态更新，并证明分块契约；不能作为选择器副作用 |
| 紧凑打包/CROSSBATCH | 作为 $\mathcal C_v^P$ 的物理实现映射，不改变参考语义 |
| 阶段屏障 | 可封装在节点/子图转导器；不得产生未声明的零时延共享状态环 |

当前原生 LH 可以继续作为黄金参考实现，但本页不主张它自动满足任一严格语义配置。特别需要逐项检查：

- 现有聚合是否保留所有者/时间来源信息。
- 现有状态/消息是否能增加因果前沿审计标签。
- 选择器计数器是否跨所有者/事件形成自适应链。
- 同一绝对内部轮次的节点更新是有序、联合、因果前沿融合，还是依赖线程顺序。
- 记忆清除/衰减的可见性与提交时序。
- 输出状态是否显式包含式 GD-E3 所需的读出寄存器。

## 13. 全面设计审视

### 13.1 已经解决的结构问题

1. **不再修改路径时延**：跳跃边保持单位时延，不通过中继分层改写参考语义。
2. **外部时钟固定**：令牌 $t$ 在 $Rt$ 注入，第 $t$ 个读出在 $R(t+1)$ 发生；选择器/路由不能修改时钟。
3. **完整逻辑时间明确**：绝对轮次、阶段、路径年龄、所有者与因果前沿是不同字段；同一边界的提交/读出/采样/注入顺序由式 GD-0.3 固定。
4. **逻辑事件已类型化**：输入、节点、读出与采样事件都有事件标识符、种类、位置、时间戳、所有者支持集与因果前沿。
5. **依赖完备性已成为前提**：消息、状态、读出与自回归边界依赖均显式进入事件有向无环图。
6. **固定读出已进入正确性契约**：节点分块必须对齐完整提交轨迹，定理 8.4 直接推出每个 $y_t$ 相同。
7. **一般有向无环图有直接证明**：证明按空间拓扑序归纳，不要求等长路径。
8. **长期上下文位置明确**：长期历史进入节点持有的 KV/SSM/累加器，不藏在无所有者的游走信号中。
9. **正确性与性能分层**：定理 8.4 证明调度等价；第 9 节再区分节点局部分块吞吐量、令牌轴低并行跨度、工作量与事件上界。
10. **稀疏性不再依赖空间层级**：固定来源槽位给出适用于一般有向无环图与所有者提升的 $LK|V|$ 上界。

这里“已经解决”只指流式与分块调度相对同一个绝对时间参考的等价性，不表示已经解决该参考与标准令牌前缀自回归语义的关系。

### 13.2 仍然存在的主要风险

#### 风险一：节点分块契约可能只是把顺序链藏进计算核

式 GD-12 是正确性契约，不是性能结论。若选择器或状态转移是任意黑盒，$\mathcal C_v^P$ 可能只能顺序执行整条事件流。

研究上必须为每类节点声明：

- 令牌局部。
- 因果注意力/批量。
- 可由扫描组合。
- 同刻联合。
- 顺序回退。

并分别给出工作量/并行跨度见证。

#### 风险二：一般有向无环图的绝对时间次序不自动等于令牌次序

即使选择按所有者排序的语义配置，一般有向无环图仍允许例 5.2b 的所有者逆序：由命题 2.7，当路径长度差超过固定值 $R(t_B-t_A)$ 时，较晚令牌的短路径事件会先于较早令牌的长路径事件修改同一节点状态。该行为由固定 $R$ 与拓扑结构决定，运行时选择器不能改写其时间戳。原子联合还进一步允许较早所有者的同刻输出读取较晚所有者的输入。

这些行为属于本文绝对时间参考；它们不要求所有者小的事件永远先于所有者大的事件。令牌前缀正确性改由完整时间戳可见性与因果前沿上界保证：式 GD-2.5 要求第 $t$ 个读出发生时尚不可见 $x_{t+1}$，式 GD-2.4 要求事件值的因果前沿不超过其时间戳可见前缀。

因此仍需要分别验证：

- 流式绝对时间因果性。
- 每个事件函数是否满足式 GD-2.4。
- 输出读出是否满足因果前沿 $\leq t$。
- 是否允许跨时间所有者逆序。
- 是否要求定义 5.6 的所有者因果联合条件。
- 是否实际满足式 GD-10。
- 是否采用定理 5.13 的因果前沿提升不变量。

#### 风险三：所有者/因果前沿不能代替完整来源信息

同一所有者/因果前沿可以经不同路径、不同来源槽位、不同绝对时间多次到达同一节点。因果前沿只给出依赖上界，不说明具体依赖了哪些令牌；仅保留所有者/因果前沿仍不足以回放。逻辑事件标识符、消息标识符、到达时间戳、源、来源槽位与路由谱系都应进入执行轨迹。

#### 风险四：固定槽位可能限制表达力

$K$ 条来源槽位轨迹给出清晰上界，但禁止无界分裂。需要实验判断：

- 小 $K$ 是否足以覆盖有用的局部通信。
- 合并/融合后如何保留、消费或释放来源槽位。
- 训练是否出现槽位坍缩。
- 是否需要静态分层槽位池，而不是自由复制。

如果放松槽位守恒，必须提供新的事件数上界。

#### 风险五：全局负载均衡仍未被免费解决

静态偏置、先验和训练损失只保证分布意义上的均衡，不保证任意输入的即时硬均衡。原子联合/因果前沿融合只能联合处理已知时间戳分组，不能自动解决跨全部未来事件的容量分配。

#### 风险六：固定读出已定义，但其表示能力尚未验证

式 GD-E3 已固定“一周期一读出”，并要求读出寄存器是 $\mathcal S_z$ 的显式组件。剩余风险不再是读出是否存在，而是：

- 固定截止时间前的事件祖先是否足以产生有训练价值的 $y_t$。
- 长路径只影响未来读出的归纳偏置是否合理。
- 因果前沿融合是否过早丢失按所有者轨迹信息。
- 读出状态的训练目标、损失对齐与梯度路径是否明确。

#### 风险七：本页不覆盖图环

空间图无环是主定理前提。特殊递归子图可以：

- 按有限轮次展开为事件有向无环图。
- 增加时延/状态边界。
- 封装为有独立分块契约的超级节点。

同一逻辑时间的零时延代数环不在本页范围内，见 [[finite-event-dag-and-zero-delay-loops-memo]]。

#### 风险八：训练与后端实现映射仍需独立验证

调度正确性不自动证明：

- 反向图与梯度累积等价。
- 稀疏紧凑打包计算核在 Ascend 上高效。
- 动态形状、分段排序与通信成本可接受。
- 数值重排只产生声明范围内的浮点误差。

#### 风险九：固定周期事件参考语义尚未嵌入统一 StepTransition

本页把固定周期事件语义作为主要参考语义，并证明其两种封闭有限调度等价。定义 8.1 在最后一个读出后继续冲刷到 $H_L$，所以式 GD-E2 的最终状态是冲刷后状态；它们不等于下一注入边界上“节点状态 + 尚未到达消息”组成的延续状态。

要得到可接续解码的预填充交接状态，尚需构造单周期转移：

$$
\mathcal T_R:
X\times\mathcal S_R
\to
Y\times\mathcal S_R
$$

使 $\mathcal S_R$ 显式包含全部节点状态与跨边界在途消息；定义每个边界切面的状态快照；再证明连续 $L$ 个周期的事件执行正好是 $\operatorname{Fold}_{\mathcal T_R}^L$ 的展开。该嵌入定理是把本页结果提升为统一模型级 `prefill == decode` 定理的下一步。

### 13.3 当前推荐的最小实现顺序

1. 实现固定 $R$、六阶段边界次序与每周期强制读出。
2. 实现类型化事件键：`(event_id, kind, location, timestamp, owner_support, frontier)`。
3. 实现消息键：`(message_id, owner, frontier, arrival_timestamp, src, dst, birth_slot, lineage)`。
4. 实现一般有向无环图绝对时间标量参考，并输出完整的事件、消息和提交账本。
5. 实现按所有者排序的节点拓扑序分块执行器，并对齐式 GD-E2 的五类产物与全部 $y_t$。
6. 定义边界切面、在途消息多重集与统一 $\mathcal T_R$，证明延续状态的折叠嵌入。
7. 为逐令牌映射、注意力、SSM/线性注意力增加紧凑打包节点计算核；其他局部逻辑先允许顺序回退。
8. 实现原子联合与因果前沿融合标量/分块语义配置。
9. 用不等长路径碰撞、所有者逆序、跨边界延续、固定读出与状态因果前沿污染比较三种语义配置。
10. 加入固定来源槽位、工作量/并行跨度与负载指标。
11. 最后再引入训练期均衡和更复杂选择器。

### 13.4 当前可主张与不可主张

当前可以主张：

- 一般有限单位时延有向无环图在本文条件下具有封闭有限精确节点拓扑序分块调度。
- 固定周期注入/读出与跨边界延续消息可以同时纳入该调度等价。
- 每个有限教师强制执行在本文条件下具有类型化、依赖完备的事件有向无环图。
- 令牌所有者在非等长路径中是必要来源信息字段。
- 按所有者排序的、原子联合与因果前沿融合都可以分别建立调度等价定理。
- 折叠等价的联合计算核可以批量实现按所有者排序的语义。
- 因果前沿融合在定理 5.13 的条件下保持显式令牌前缀依赖上界。
- 固定来源槽位给出一个兼容所有者提升的超稀疏事件上界。

当前不能主张：

- 任意一般有向无环图、任意节点计算核都有高性能预填充。
- 原子联合与按所有者排序的在未证明式 GD-10 时语义相同。
- 因果前沿融合的数值状态转移自动具有扫描/批量高性能实现。
- 当前计算核/选择器族已经给出低并行跨度的并行预填充见证。
- 当前 LH 选择器已满足严格语义配置。
- 静态/训练均衡能提供任意输入上的硬容量。
- 封闭执行的冲刷后最终状态可以直接作为下一令牌边界的解码延续状态。
- 本页调度定理已经等同于统一 $\mathcal T_R$ 上的完整模型级 `prefill == decode` 定理。
- 本页已经解决图环、反向或 Ascend 实现映射。

## 14. 研究结论

一般有向无环图下，所有者与因果前沿都不应被删除，但二者职责不同。绝对时间决定何时发生；轨迹所有者表示哪条令牌路径正被推进；因果前沿给出数值内容依赖到哪个令牌前缀；节点持有的状态决定历史如何影响当前计算。因果前沿融合会主动终止多个旧轨迹，并把统一输出的所有者提升为因果前沿。

最小正向命题是：

> 对任意满足 $R=d_{\min}$ 的有限单位时延空间有向无环图，只要固定注入/读出阶段次序、跨边界延续语义、类型化事件依赖、唯一状态归属与精确节点分块契约均成立，就可以把封闭有限教师强制绝对时间流式执行重排为节点拓扑序分块执行，并保持全部隐藏表示、提交、路由、消息、冲刷后最终状态与固定周期读出产物。

这个命题保留了 Tide 所需的一般空间有向无环图，也把真正的性能问题准确地下推到：

- 节点事件流计算核是否至少具有可接受的局部分块吞吐量，以及是否进一步具有因果批量、扫描或联合执行所需的低并行跨度结构。
- 事件数是否有超稀疏上界。
- 选择器是否避免不可收缩的跨令牌控制链。
- 有序、联合与因果前沿融合语义中哪一种更有训练价值、任务价值与可实现的数值收缩。
