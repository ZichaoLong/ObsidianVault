---
type: mathematical-learning-note
status: active-learning
as-of: 2026-09-04
semantic-profile: TimedDAG-v0
cssclasses:
  - textbook-math
tags:
  - tide
  - timed-dag
  - asynchronous-messages
  - logical-time
  - mathematics
  - learning-note
---

# TimedDAG-v0：从 SettleGraph 到跨 Token 汇合的最小数学模型

> [!summary] 本页定位
> 本页不是已经完成的正式规范，也不声称已有通用异步 executor。它从 SettleGraph 出发，只增加一项能力：不同 Token 的消息可以在同一节点、同一逻辑时刻成为一次联合事件。
>
> 本页优先使用有限集合、函数、关系和普通归纳描述语义；解释器是数学构造的直接实现，而不是另一套事实来源。当前路线入口见 [[current-mainline]]。

> [!tip] 第一次只读到哪里
> 第一次读第 0、1 节；在第 2 节只读定义 2.1（图）、2.2（注入时间）、2.5（seal）、2.6（桶）和 2.8（事件），然后直接读第 3 节并完成四道手算题。identity、完整类型和 continuation 在真正写证明时再补。第 4 节以后按任务查阅，不需要一次读完。

## 0. 唯一的新问题

SettleGraph 的一次结算属于一个 Token：即使 Token 0 和 Token 1 的 Tensor 被同一个 packed kernel 一起计算，它们仍然是两个语义事件。

TimedDAG-v0 把节点事件的主索引改成逻辑时刻：

```text
SettleGraph
  (node v, token 0)  一个事件
  (node v, token 1)  另一个事件

TimedDAG-v0
  token 0 的消息 ─┐
                   ├─> (node v, logical time 5) 一个联合事件
  token 1 的消息 ─┘
```

本页只回答：

> 什么样的最小数学语义，既允许这种跨 Token 汇合，又仍有确定的有限 cut、分块执行和通用解释器？

## 1. 三种“异步”必须分开

“异步”可能表示三件不同的事。

1. **物理乱序**：相同语义消息在机器上的送达或完成顺序不同。
2. **跨 Token 同刻汇合**：不同 Token 的消息具有相同逻辑到达时间，由同一个节点事件联合处理。
3. **部分到达即提交**：节点还不知道当前时刻的消息是否收齐，就先改变状态或发布输出。

TimedDAG-v0 允许前两项，不允许第三项。第三项只有在以后满足至少一个条件时才进入新 profile：

- 增量操作具有已证明的交换律和结合律；
- 所有部分结果只暂存，输入关闭后统一提交；
- 规定与物理到达无关的 canonical fold 顺序；
- 正式定义对已发布结果的 retraction。

因此，本页中的物理调度可以异步，模型函数却不能偶然依赖线程竞争。

## 2. TimedDAG-v0 的数学对象

### 2.1 基础记号

令：

$$
\mathbb N=\{0,1,2,\ldots\},
\qquad
[n]=\{0,1,\ldots,n-1\}.
$$

对集合 $X$：

- $X^*$ 表示 $X$ 上的有限序列集合；
- $\mathcal P_{\mathrm{fin}}(X)$ 表示 $X$ 的有限子集集合。

固定一个带严格全序 $\prec_{\mathrm{ID}}$ 的稳定标识符集合 $\mathsf{ID}$。这里“稳定”只表示标识符由 schema 和语义坐标决定，不由墙钟顺序、线程编号或本次 chunk 划分决定。

本页只讨论有限空间图和自然数逻辑时间。偏序时间、无限节点集和连续时间全部延期。

### 2.2 定义 2.1：TimedDAG schema

一个 TimedDAG-v0 schema 是有限元组：

$$
\mathcal G=(V,A,\operatorname{src},\operatorname{dst},\delta,\prec_V,\prec_A),
$$

其中：

- $V$ 是有限非空节点集；
- $A$ 是有限边标识符集；
- $\operatorname{src},\operatorname{dst}:A\to V$ 分别给出每条边的源节点和目标节点；
- $\delta:A\to\mathbb N_{>0}$ 给出正整数逻辑时延；
- $\prec_V$ 和 $\prec_A$ 分别是 $V$ 与 $A$ 上的固定严格全序，只用于 canonical serialization 和平票处理。

边 $a\in A$ 诱导节点关系：

$$
E_{\mathcal G}
=\{(\operatorname{src}(a),\operatorname{dst}(a))\mid a\in A\}
\subseteq V\times V.
$$

TimedDAG-v0 要求 $(V,E_{\mathcal G})$ 无环。因为边本身具有独立 identity，$A$ 可以表达端点相同但身份不同的两条边。

对 $v\in V$，定义：

$$
\operatorname{In}(v)=\{a\in A\mid \operatorname{dst}(a)=v\},
\qquad
\operatorname{Out}(v)=\{a\in A\mid \operatorname{src}(a)=v\}.
$$

本页暂时把一条入边视为一个输入 channel。独立的 node port 类型以后可以在不改变核心时间语义的前提下加入。

### 2.3 定义 2.2：输入位置与逻辑注入时间

固定有限输入长度 $L\in\mathbb N$。Token 位置集合为 $[L]$。

给定严格递增函数：

$$
\iota:[L]\to\mathbb N,
$$

称 $\iota(t)$ 为输入位置 $t$ 的逻辑注入时间。

`token position` 和 `logical time` 是不同对象。$\iota(t)=t$ 是最小例子的方便选择，不是 TimedDAG 的普遍公理。

给定入口节点集 $V_{\mathrm{in}}\subseteq V$，并要求每个空间 source 都是入口：

$$
\operatorname{In}(v)=\varnothing
\Longrightarrow
v\in V_{\mathrm{in}}.
$$

入口也可以同时具有内部入边。一次输入注入记录写成：

$$
j=(\nu,t,\iota(t),v,p),
$$

其中 $\nu\in\mathsf{ID}$ 是稳定注入标识符，$t\in[L]$，$v\in V_{\mathrm{in}}$，$p$ 属于给定非空 payload 集 $\mathsf P$。其坐标投影分别记为 $\operatorname{iid}$、$\operatorname{token}$、$\operatorname{itime}$、$\operatorname{dst}$ 和 $\operatorname{payload}$。

用 $\mathsf{Inj}_{\mathcal G,L}$ 表示全部这类合法注入记录。当前可见的注入 history 是有限集 $J\in\mathcal P_{\mathrm{fin}}(\mathsf{Inj}_{\mathcal G,L})$，并要求 $\operatorname{iid}$ 唯一：同一注入标识符不能指向两条不同记录。第一版 fixture 可以直接给定完整 $J$，暂不研究 selector 怎样决定初始路径。

### 2.4 定义 2.3：timed message

一条消息是七元组：

$$
m=(\mu,a,\tau_s,\tau_a,O,p,e),
$$

其中：

- $\mu\in\mathsf{ID}$ 是 message identity；
- $a\in A$ 是 edge identity；
- $\tau_s,\tau_a\in\mathbb N$ 是逻辑发送和到达时间；
- $O\in\mathcal P_{\mathrm{fin}}([L])$ 是 owner-label set；
- $p\in\mathsf P$ 是 payload；
- $e\in\mathsf{ID}$ 是 producer event identity。

合法消息必须满足：

$$
\tau_a=\tau_s+\delta(a).
\tag{TD-1}
$$

各坐标投影记为 $\operatorname{mid}$、$\operatorname{edge}$、$\operatorname{send}$、$\operatorname{arrival}$、$\operatorname{owner}$、$\operatorname{payload}$ 和 $\operatorname{producer}$。用 $\mathsf{Msg}_{\mathcal G}$ 表示满足式 TD-1 的全部合法消息集合。

$O$ 只说明消息对外声明的 Token 归属，不决定逻辑时间，也不自动证明 payload 实质依赖哪些输入。需要证明自回归因果性时，另加 dependency support；见第 7 节。

### 2.5 定义 2.4：history 与唯一身份

一个有限消息 history 是有限集合：

$$
H\in\mathcal P_{\mathrm{fin}}(\mathsf{Msg}_{\mathcal G}),
$$

并满足 message identity 唯一：

$$
m,m'\in H,
\quad
\operatorname{mid}(m)=\operatorname{mid}(m')
\Longrightarrow
m=m'.
\tag{TD-2}
$$

同一 owner、同一到达时间或相同 payload 都不能代替消息身份。

### 2.6 定义 2.5：seal

边 seal 是一个向量 $\sigma\in\mathbb N^A$；入口 seal 是 $\sigma_{\mathrm{in}}\in\mathbb N^{V_{\mathrm{in}}}$。对每条边 $a\in A$，$\sigma(a)=b$ 表示如下硬承诺：

> 在任何合法未来扩展中，都不会再在边 $a$ 上新增逻辑到达时间严格小于 $b$ 的消息。

形式上，若 $(H,\sigma)$ 是当前可见前缀，$H'\supseteq H$ 是任意合法未来扩展，则：

$$
m\in H'\setminus H,
\quad
\operatorname{edge}(m)=a
\Longrightarrow
\operatorname{arrival}(m)\ge\sigma(a).
\tag{TD-3}
$$

入口注入流类似地满足：未来不会再向入口节点 $v$ 增加注入时间小于 $\sigma_{\mathrm{in}}(v)$ 的记录。沿一次合法执行，两个 seal 向量都只能逐坐标单调不降；任何时间戳严格小于已经可见 seal 的迟到记录都使该执行非法。

队列当前为空不蕴含任何 seal。物理 channel 必须先让接收端看见全部时间小于 $b$ 的数据，才能让它看见 `seal=b`；若 seal 在网络上先到，runtime 必须暂存它。

### 2.7 定义 2.6：逻辑时间桶

对 $v\in V$ 和 $\theta\in\mathbb N$，定义消息桶：

$$
M_{v,\theta}(H)
=
\{m\in H
\mid \operatorname{dst}(\operatorname{edge}(m))=v,
\operatorname{arrival}(m)=\theta\}.
$$

定义注入桶：

$$
J_{v,\theta}(J)
=
\{j\in J
\mid \operatorname{dst}(j)=v,
\operatorname{itime}(j)=\theta\}.
$$

节点完整输入桶为带 tag 的不交并：

$$
B_{v,\theta}(H,J)
=
\bigl(\{\mathtt{msg}\}\times M_{v,\theta}(H)\bigr)
\sqcup
\bigl(\{\mathtt{inj}\}\times J_{v,\theta}(J)\bigr).
\tag{TD-4}
$$

定义该桶已经关闭，当且仅当：

$$
\operatorname{Closed}(v,\theta)
\Longleftrightarrow
\left(\forall a\in\operatorname{In}(v),\ \sigma(a)>\theta\right)
\land
\left(v\in V_{\mathrm{in}}\Longrightarrow
\sigma_{\mathrm{in}}(v)>\theta\right).
\tag{TD-5}
$$

严格不等号是实质的：`seal = 5` 只排除到达时间小于 5 的新消息，尚不能关闭时间桶 5；`seal = 6` 才能关闭它。若 $v$ 既是入口节点又有内部入边，则两类 seal 都必须越过 $\theta$；若某一类输入不存在，对应的全称条件为空真。

### 2.8 定义 2.7：局部状态与节点转导

对每个 $v\in V$，给定非空状态集 $S_v$、初始状态 $q_v^0\in S_v$ 和 artifact 集 $\mathsf{Artifact}_v$。

精确定义可到达 $v$ 的 tagged atom 集：

$$
\mathsf{Atom}_v
=
\left(
\{\mathtt{msg}\}
\times
\{m\in\mathsf{Msg}_{\mathcal G}
\mid \operatorname{dst}(\operatorname{edge}(m))=v\}
\right)
\sqcup
\left(
\{\mathtt{inj}\}
\times
\{j\in\mathsf{Inj}_{\mathcal G,L}
\mid \operatorname{dst}(j)=v\}
\right).
$$

定义节点输出指令集合：

$$
\mathsf{Out}_v
=
\operatorname{Out}(v)
\times
\mathcal P_{\mathrm{fin}}([L])
\times
\mathsf P.
$$

节点 $v$ 的 reference transition 是确定函数：

$$
F_v:
S_v\times\mathbb N\times\mathsf{Atom}_v^*
\longrightarrow
S_v\times\mathsf{Out}_v^*\times\mathsf{Artifact}_v^*,
\tag{TD-6}
$$

这里必须区分两个层次：把 $F_v$ 写成 total function 足以定义抽象语义；要得到一段真正可运行的通用解释器，还需为 $S_v$、$\mathsf P$ 和 artifacts 给出有效编码，并随节点提供一个必定终止、精确计算 $F_v$ 的 evaluator。解释器可以调用这个 evaluator，却不可能仅从任意程序文本自动判定它是否 total。因此后面的“存在性”都是带此前提的条件命题。

输入桶先排列成 canonical 序列：先固定 $\mathtt{inj}\prec\mathtt{msg}$；注入 atom 再按 $\prec_{\mathrm{ID}}$ 排列；消息 atom 再按 $\prec_A$ 和 $\prec_{\mathrm{ID}}$ 的字典序排列。也就是使用只依赖语义 identity 的键：

$$
(\text{atom tag},\ \text{channel order（若有）},\ \text{stable identity}).
\tag{TD-7}
$$

若具体节点希望忽略这个顺序，必须证明对应聚合具有所需交换律和结合律，不能改用物理到达顺序。

### 2.9 定义 2.8：节点事件

一个节点事件的语义键是：

$$
(v,\theta)\in V\times\mathbb N.
$$

TimedDAG-v0 规定每个 $(v,\theta)$ 至多执行一次，并且只在 $B_{v,\theta}\ne\varnothing$ 时创建事件。没有消息且没有注入的空桶只推进完成 frontier，不调用 $F_v$。

设 $D\subseteq V\times\mathbb N$ 是已经执行的事件键集合。定义：

$$
\operatorname{Ready}(v,\theta)
$$

当且仅当：

1. $B_{v,\theta}\ne\varnothing$；
2. $\operatorname{Closed}(v,\theta)$；
3. $(v,\theta)\notin D$；
4. 对每个 $\theta'<\theta$，若 $B_{v,\theta'}\ne\varnothing$，则 $(v,\theta')\in D$。

第 4 条使同一节点的 state version 按逻辑时间递增。不同节点之间若没有事件依赖，可以由物理 executor 任意调度。

若执行 $(v,\theta)$，令：

$$
F_v(q_v,\theta,\operatorname{canon}(B_{v,\theta}))
=(q_v',\mathbf o,\mathbf r).
$$

则原子地把 $q_v$ 改为 $q_v'$，把 $(v,\theta)$ 加入 $D$，并保存局部 artifacts $\mathbf r$。

对 $\mathbf o$ 中第 $k$ 条输出指令 $(a,O,p)$，产生稳定消息：

$$
m_k=
\bigl(
\mu(v,\theta,a,k),
a,
\theta,
\theta+\delta(a),
O,
p,
e(v,\theta)
\bigr).
\tag{TD-8}
$$

$e(v,\theta)$ 和 $\mu(v,\theta,a,k)$ 是由 schema identity 与这些语义坐标确定的稳定单射编码，不依赖 chunk 长度、调用次数或线程完成顺序。

Reference step 把所有 $m_k$ 一并加入 $H$。这里的 $H$ 是已经在语义上发布的消息 history，不是某个 OS receive queue；物理实现可以延迟或乱序搬运这些消息，但必须把未送达消息和未公开 seal 保存在自己的 continuation 中，并证明其投影与本页 reference 相同。

### 2.10 定义 2.9：运行构形与 continuation

一个运行构形至少是有限元组：

$$
C=(\mathbf q,H,J,\sigma,\sigma_{\mathrm{in}},D,\mathbf A,\boldsymbol\kappa),
\tag{TD-9}
$$

其中：

- $\mathbf q\in\prod_{v\in V}S_v$ 是当前节点状态；
- $H,J$ 是当前已在语义上发布或接受的消息和注入 history；
- $\sigma,\sigma_{\mathrm{in}}$ 是当前可见 seals；
- $D$ 是已执行事件键；
- $\mathbf A$ 是规范化语义 artifacts；
- $\kappa(v)$ 是节点已经封闭的逻辑时间前缀。

只把从初始状态 $\mathbf q^0$ 出发，经合法输入扩展、单调 seal 推进和定义 2.8 的事件步骤可达的元组称为合法构形；$\operatorname{RunTo}$ 的定义域只包含这些构形。这样式 TD-9 不是一张允许任意字段组合的数据库表。

第一版直接把完整构形 $C$ 作为 **reference continuation**。这样“充分 continuation”不是猜测一份缓存字段表，而是要求：从同一个 $C$ 和同一个合法未来输入扩展出发，后续 reference 结果完全相同。异步物理 executor 的 checkpoint 还必须保存尚未投影进 $C$ 的传输状态；那属于实现对 reference 的 refinement，不改变本页的模型函数。

物理线程顺序可以另记 schedule log，但它不属于 $\mathbf A$。比较不同执行时，$\mathbf A$ 按稳定语义键规范化后比较。

## 3. 最小跨 Token 汇合例子

设 $L=2$，并取：

$$
\iota(0)=0,
\qquad
\iota(1)=1.
$$

固定 DAG 中存在到节点 $v$ 的两条路径：

- 慢路径 $P_s$ 的总时延为 5；
- 快路径 $P_f$ 的总时延为 4。

fixture 用固定规则令 Token 0 在慢路径产生消息 $m_0$，Token 1 在快路径产生消息 $m_1$。暂不研究这个路由规则如何学习。

于是：

$$
\operatorname{arrival}(m_0)=\iota(0)+5=5,
$$

$$
\operatorname{arrival}(m_1)=\iota(1)+4=5.
$$

若 $m_0,m_1$ 都到达 $v$，则：

$$
B_{v,5}=\{(\mathtt{msg},m_0),(\mathtt{msg},m_1)\}.
$$

设 $v$ 的所有入边 $a$ 都满足：

$$
\sigma(a)\ge 6.
$$

由式 TD-5，$\operatorname{Closed}(v,5)$ 成立。若 $v$ 的更早非空桶都已执行，则 $(v,5)$ ready，并且 $F_v$ 只调用一次。

它收到的 owner-label set 可以是：

$$
\{0\}\cup\{1\}=\{0,1\}.
$$

但 $F_v$ 仍必须明确选择：

1. 分别产生 owner 0 和 owner 1 的输出；
2. 联合计算后仍产生两个有归属的输出；
3. 产生一个融合输出。

### 第一次阅读的四道手算题

1. 若某条入边只有 `seal=5`，式 TD-5 为什么尚不能关闭 $B_{v,5}$？
2. 若 $m_1$ 先在墙钟时间到达，哪个定义阻止 $v$ 立即执行？
3. 若把 $m_0,m_1$ 放进同一个 packed Tensor，但分别调用两次 $F_v$，这是否已经是联合事件？
4. 若一个标为 owner 0 的输出实质使用了 $m_1$，它是否可能违反自回归前缀因果性？

答案分别来自：严格 seal 不等式、`Closed` 条件、事件键与调用次数、owner 和 dependency support 的区别。

## 4. 一个支点引理和四个主目标

### 引理 4.1：关闭桶稳定性

若 $\operatorname{Closed}(v,\theta)$ 成立，则任意遵守已有 seal 的合法未来扩展都不会改变 $B_{v,\theta}$。

**证明思路。** 对任意入边 $a$，式 TD-5 给出 $\sigma(a)>\theta$。式 TD-3 说明未来新增消息的到达时间至少为 $\sigma(a)$，因而严格大于 $\theta$。入口注入流同理。所以未来扩展不能向 $B_{v,\theta}$ 增加原子。已有 history 不允许删除或改写，故该桶不变。∎

这个初等引理是整个 profile 的支点：节点等待的不是墙钟超时，而是一个使输入集合在所有合法未来中保持不变的数学证书。

### 命题目标 4.2：有限 cut 完成

给定 $b\in\mathbb N$。逻辑时间小于 $b$ 的候选事件键最多有：

$$
|V|\,b
$$

个，因为事件键属于 $V\times[b]$，且每个键至多执行一次。

若再假设：

1. 对每个入口 $v$，当前输入包含其全部时间小于 $b$ 的注入，并有 $\sigma_{\mathrm{in}}(v)\ge b$ 作为证明；
2. 每个 $F_v$ 都是 total function，并只产生有限输出序列；若结论要求可运行算法，还要给出它的可终止 evaluator；
3. seal 能按第 5 节的规则沿有限 DAG 前进；

则 cut $b$ 以下的事件、消息和 artifacts 都有限，并可由通用解释器构造完成。

需要正式证明的是第 3 条与“解释器不会在尚缺 seal 时伪造完成”。事件数上界本身不证明 source 一定提供进展。

### 命题目标 4.3：调度无关性

固定相同的 schema、初始状态、全部 $F_v$，以及由 seal 证明完整的同一 cut $b$ 输入。任意两个只选择 ready 事件并完成该 cut 的公平执行，其 cut-$b$ 构形与规范化语义 artifacts 应相同。

推荐证明方式是对 $\theta\in\mathbb N$ 归纳：

- 同一节点较早的 state event 已由 Ready 第 4 条固定；
- 每个 bucket 在关闭后由引理 4.1 固定；
- $F_v$ 是确定函数；
- $\delta(a)>0$，所以时刻 $\theta$ 的事件只能产生到达时间严格大于 $\theta$ 的消息；同刻不同节点不会通过新消息相互定义；
- node state 不跨节点共享。

因此同一时刻的独立 ready events 可交换。物理 schedule log 可以不同，但按 EventId/MessageId 排序后的语义对象相同。

### 命题目标 4.4：cut composition

设 $0\le c\le b$。定义部分函数 $\operatorname{RunTo}(C,b)$：其合法调用要求 $b\ge\kappa(v)$ 对每个 $v$ 成立；它从构形 $C$ 出发，完成所有逻辑时间小于 $b$ 的已封闭 reference work，并返回新构形。它保存已经产生但到达时间不小于 $b$ 的消息，却不执行时间不小于 $b$ 的节点事件，也不把任何 $\kappa(v)$ 超前推进到 $b$ 之外。Artifacts 已累积在返回构形的 $\mathbf A$ 坐标中，因此它的输入与输出类型相同。

再令 $\operatorname{Extend}(C,E)$ 表示给 $C$ 加入一个合法的未来外部输入扩展 $E$：新注入的时间不小于已有入口 seal，并单调推进入口 seal，但不改写既有 history、状态或 identity。若 $C_0$ 中的外部输入前缀已由入口 seal 封闭到 $c$，而 $E_{[c,b)}$ 给出下一段完整输入并把入口 seal 推进到至少 $b$，期望证明：

$$
\operatorname{RunTo}
\left(
\operatorname{Extend}(C_0,E_{[c,b)}),
b
\right)
=
\operatorname{RunTo}
\left(
\operatorname{Extend}
\left(
\operatorname{RunTo}(C_0,c),
E_{[c,b)}
\right),
b
\right),
\tag{TD-10}
$$

其中等号比较：

- 节点状态和 state versions；
- 已发布消息 history 与已执行事件键；
- seals 和 completed frontiers；
- event/message/local artifacts；
- 稳定 identities。

证明不应先从序列化格式开始，而应先证明式 TD-9 的构形是未来行为的充分状态。实现 checkpoint 只是该构形的一种无损编码。

### 命题目标 4.5：SettleGraph refinement

需要构造一个翻译 $\mathcal T$，把任意合法 SettleGraph Plan 和输入序列映射到 TimedDAG-v0 schema、输入与节点转导，使：

$$
\operatorname{Project}
\left(
\operatorname{Run}_{\mathrm{TimedDAG}}
(\mathcal T(\mathrm{Plan}),x)
\right)
=
\operatorname{InterpretToken}^{*}(\mathrm{Plan},x).
\tag{TD-11}
$$

投影必须比较完整 output、state、reached、observe、active、route、commit 和 `DATA/CLOSED`，不能只比较最终 hidden。

本页把式 TD-11 作为第四个主目标；第 8 节只给构造轮廓，目前不是已证定理。

## 5. seal 推进与通用解释器的构造

### 5.1 节点完成 frontier

对非入口节点 $v$，定义当前输入 frontier：

$$
f_C(v)=\min\{\sigma(a)\mid a\in\operatorname{In}(v)\}.
$$

若 $v$ 也是入口节点，则再把 $\sigma_{\mathrm{in}}(v)$ 加入取最小值的集合。纯入口节点只使用 injection frontier。

初始化 $\kappa(v)=0$，并保持不变量 $\kappa(v)\le f_C(v)$。Seal 单调性保证 $f_C(v)$ 也只会单调不降。

对任意满足

$$
\kappa(v)\le h\le f_C(v)
$$

的目标 $h$，若所有满足 $\theta<h$ 的非空桶都已经执行，则可以作单调更新：

$$
\kappa(v)\leftarrow h.
$$

$\kappa(v)=b$ 表示节点已经处理或确认为空的全部逻辑时刻 $\theta<b$。

### 5.2 输出 seal

TimedDAG-v0 的一个关键简化是：$F_v$ 在时刻 $\theta$ 产生的所有消息都以 $\theta$ 为发送时间；节点没有 timer 或自发事件。

因此，对出边 $a\in\operatorname{Out}(v)$，若 $\kappa(v)=b$，则可以安全发布下面这个新的 seal 候选，并与已有值取最大：

$$
\sigma(a)
\leftarrow
\max\{\sigma(a),\ b+\delta(a)\}.
\tag{TD-12}
$$

理由是未来节点事件的发送时间都不小于 $b$，其沿边 $a$ 的到达时间由式 TD-1 至少为 $b+\delta(a)$。

式 TD-12 会在加入 timer、可变内部延迟或环时发生变化；它只是 TimedDAG-v0 的简化规则。

### 5.3 构造性解释器

由于空间图是有限 DAG，可选任意拓扑序 $(v_0,\ldots,v_{|V|-1})$。对一个已获得足够入口 seal 的有限 cut，依次：

1. 构造 $v_i$ 在目标 cut 前的全部关闭非空桶；
2. 按逻辑时间递增反复应用 $F_{v_i}$；
3. 保存事件、状态提交和出站消息；
4. 用式 TD-12 推进所有出边 seal；
5. 进入下一个空间节点。

所有空间前驱都已经处理，故 $v_i$ 所需的数据和负完成信息都已确定。这给出通用 node-major 解释器的存在性构造。

同一个语义也可以由在线 ready-set 解释器构造：每次任取一个满足定义 2.8 的 ready key，执行后投递消息并推进可能的 seals。命题目标 4.3 要证明两种构造以及不同 ready 顺序产生同一规范化结果。

这一阶段无需 packed kernel。高性能实现以后只需证明自己模拟相同的 $F_v$ fold、消息集合和构形转移。

## 6. continuation 为什么先取完整构形

第一次实现 checkpoint 时，不需要立即寻找最小状态。直接序列化式 TD-9 的完整构形：

```text
node states and versions
published message history
input records
edge/input seals
executed event keys
canonical semantic artifacts or their committed prefix
node completion frontiers
schema identity
```

这样最容易证明式 TD-10。物理异步实现还要额外序列化未送达 message/seal envelope、队列序号或等价的传输状态，并证明它们投影到同一个 reference 构形。等 monolithic 与任意 cut resume 已经对拍，再研究哪些字段可由其他字段恢复、哪些 trace 可以裁剪。

过早最小化 continuation 容易把 pending message、已经发布的 seal 或 stable-ID 信息遗漏；这些遗漏通常只在非整齐 cut 上出现。

## 7. 自回归因果性是独立义务

owner-label set 不能证明自回归因果性。为每条注入、消息、状态和输出增加可选的 dependency support：

$$
\operatorname{supp}(z)\in\mathcal P_{\mathrm{fin}}([L]).
$$

输入位置 $t$ 的注入满足：

$$
\operatorname{supp}(j_t)=\{t\}.
$$

一个保守传播规则可以取：节点输出的 support 包含本次输入原子和所读旧状态 support 的并集。

若 $y_t$ 是位置 $t$ 的自回归读出，则必须证明：

$$
\operatorname{supp}(y_t)\subseteq[t+1].
\tag{TD-13}
$$

因此，在第 3 节的联合事件中，一个实际依赖 Token 1 消息的结果不能仅通过把 owner 写成 0，就合法地成为 $y_0$。它可以：

- 只影响 $y_1$ 或更晚读出；
- 更新只对未来可见的状态；
- 或证明 owner 0 的输出分量在函数上不依赖 Token 1。

外部输入的物理 Tensor 即使已经整段位于内存中，也只能从各自 $\iota(t)$ 起进入语义。readout time、下一 Token injection phase，以及迟到消息采用 deadline merge 还是 future-state update，需要在接入具体自回归模型时另行声明。

## 8. SettleGraph 嵌入的构造轮廓

SettleGraph 不被 TimedDAG-v0 替换，而应成为禁止跨 Token 汇合的受限 profile。

### 8.1 时间编码

为合法 SettleGraph Plan 选择一个确定的 region 拓扑序，并把每个 Token 内部的 candidate、arbitration、commit、compute 和 edge settlement 排成有限个 settlement steps。这里 $r$ 是覆盖这些操作的 **microstep rank**，不只是 region 编号；编译出的每条边都从较小 rank 指向较大 rank，其 $\delta$ 取两 rank 之差。

取大于单 Token 全部 settlement steps 的常数 $K$，定义：

$$
\theta(t,r)=Kt+r.
\tag{TD-14}
$$

同时取 $\iota(t)=Kt$。

于是 Token $t$ 的所有事件都早于 Token $t+1$ 的事件，不发生跨 Token 汇合。这个串行时间编码只用于证明最简单的 refinement，不声称是唯一或最高性能的物理调度。

### 8.2 RegionArbiter

把一个 selection region 编译成显式有限子图或确定 `RegionArbiter` 节点：

```text
receiver input settlement
→ reached/candidate records
→ RegionArbiter
→ observe/active decisions
→ state commit / NodeCompute / Emit
```

Plan 中所有候选身份已知；某候选在对应输入 channels 关闭后仍无数据，就确定为 not reached。RegionArbiter 对该 Token 只执行一次。

### 8.3 `DATA/CLOSED` 与 timed message/seal

- `DATA(edge, token)` 翻译为一条 timed message；
- `CLOSED(edge, token)` 翻译为该 edge/token 时隙不会产生数据的负完成事实；
- 因为嵌入按 Token 顺序结算，连续完成的时隙可以压缩为 edge seal；
- `CLOSED` 不是 payload，也不能翻译成零向量。

### 8.4 必须保持的观察量

式 TD-11 至少比较：

- SettleGraph 输出 hidden；
- receiver state 与 selector-history；
- reached、candidate、observe、active；
- selector、route、commit 和 Emit artifacts；
- 每个 `(edge,token)` 的 `DATA/CLOSED`。

建议先对 singleton、chain 和 diamond 三个 Plan 完成翻译与手算，再写一般 Plan 的拓扑归纳。

## 9. 数学先行的学习与实现顺序

### M0：纸面模型

1. 明确写出一个小图的 $V,A,s,d,\delta$。
2. 列出 $J,H,\sigma$。
3. 手算每个 $B_{v,\theta}$、Ready key 和状态变化。
4. 写出规范化 event/message trace。

### M1：证明两个初等事实

1. 完整写出引理 4.1 的证明。
2. 证明 cut $b$ 内事件数至多为 $|V|b$。
3. 对同一 $\theta$ 的两个不同 ready nodes，证明两次转移可交换。

### M2：整数 reference

把集合、函数和构形逐项翻译为最小程序。payload 只使用整数或有限 tuple，$F_v$ 只做加法、拼接或有限状态更新。

程序中的每个主要类型都应能指回本页一个定义；程序不能新增未写入数学模型的 timeout、默认排序或隐藏状态。

### M3：性质测试

- 随机改变 message delivery 顺序；
- 随机选择任意 ready event；
- 在 partial bucket、ready-before-execute、commit-before-downstream-consume 三类位置暂停；
- 与 canonical node-major 构造比较规范化 artifacts 和 continuation。

### M4：SettleGraph refinement

先手工翻译三个小 Plan，再实现翻译函数和 artifact projection。只有式 TD-11 的对象都能实际比较后，才写一般归纳证明。

### M5：Tensor 与优化

最后才把 payload 换成 Tensor。TimedDAG 的 packed executor、SettleGraph 的 packed executor和具体 Attention kernel可以共享优化技巧，但各自都必须对自己的 reference 语义负责。

## 10. 最小测试名

- `cross_token_same_time_is_one_event`
- `seal_equal_time_does_not_close_bucket`
- `no_fire_without_seal`
- `reject_message_behind_visible_seal`
- `delivery_order_preserves_semantics`
- `ready_order_preserves_semantics`
- `state_versions_follow_logical_time`
- `resume_from_partial_bucket`
- `resume_after_commit_before_downstream_consume`
- `future_token_dependency_is_not_hidden_by_owner`
- `settlegraph_trace_refinement`

测试比较规范化的语义 event/message/state 集合或序列，不要求物理 schedule log 完全相同。

## 11. 下一步为何是带正时延的环

完成式 TD-10 和 TD-11 后，下一台阶只删除“$(V,E_{\mathcal G})$ 无环”这一条，仍保留：

$$
\delta(a)>0.
$$

例如：

$$
(A,\theta)
\longrightarrow
(B,\theta+d_1)
\longrightarrow
(A,\theta+d_1+d_2),
\qquad d_1,d_2\ge1.
$$

静态 schema 虽然有环，动态事件的自然数时间仍严格增加。命题目标 4.3 的时间归纳因此仍有希望保留；新的困难主要是 seal 如何绕环推进，以及怎样证明每个 finite cut productive。

zero-delay cycle 继续拒绝。这样可以先理解“静态有环、动态事件仍按时间良基”，再单独研究 fixed point、solver 或偏序时间。

## 12. 完成条件

### 能手算

- [ ] 能区分 Token 位置、逻辑时间、owner 和墙钟时间。
- [ ] 能由式 TD-5 判断一个桶是否关闭。
- [ ] 能手算跨 Token 同刻汇合的完整事件和状态 trace。
- [ ] 能指出一个 owner 正确但 dependency support 非因果的例子。

### 能证明

- [ ] 引理 4.1 已有完整证明。
- [ ] finite-cut completion 的前提和证明完整。
- [ ] schedule independence 已由时间归纳证明。
- [ ] 构形充分性和 cut composition 已证明。
- [ ] SettleGraph refinement 已证明，或剩余缺口已缩成明确引理。

### 能实现

- [ ] 整数 reference 与纸面 trace 相同。
- [ ] 随机 delivery/ready schedule 对拍通过。
- [ ] 任意测试 cut 的 save/resume 对拍通过。
- [ ] EventId/MessageId 不随 chunk、schedule 或 replay 改变。
- [ ] 三个小型 SettleGraph Plan 的完整 artifact projection 对拍通过。

只有三组都完成，才把本页 `status` 从 `active-learning` 改成 `specified`，并创建 `DelayedGraph-v0`。

## 13. 按需查阅的旧材料

以下材料都不是前置阅读：

- 外部输入周期和绝对轮次：[[tide-mathematical-foundations#1. 输入流、绝对轮次与边界切面|输入流与绝对轮次]]。
- timed message 与单位边时延：[[tide-mathematical-foundations#定义 2.5：单位边时延|单位边时延]]。
- 同一时刻的消息桶：[[tide-mathematical-foundations#定义 4.2：输入原子、时间桶与节点输入序列|时间桶]]。
- 空间拓扑序为何不自动推出 chunk composition：[[tide-mathematical-foundations#命题 6.4：空间拓扑序构造不自动推出时间分块组合律|时间分块反例]]。
- 同刻多 owner 的三种输出语义：[[tide-mathematical-foundations#定义 C.3：同一逻辑时刻的多归属输入|同刻多归属]]。
- 更一般的 seal、watermark、continuation 与 `AdvanceUntil`：[[tide-mathematical-foundations#定义 D.9：source seal、progress frontier 与 hard output watermark|finite-cut 进展]]。

每次只查解决当前定义或证明所需的一小段。不要因为旧文档已经讨论 SCC 或偏序时间，就把它们提前加入 TimedDAG-v0。
