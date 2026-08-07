---
type: research-memo
status: active
tags:
  - control-feedback
  - active-information-acquisition
  - explicit-state-semantics
  - local-state-access
  - stigmergic-state
---

# 主动信息获取与自书写状态

> [!summary] 本页定位
> 本页审视 [[30-technical-notes/hilbert-sixth-problem-and-ai-entropy|从希尔伯特第六问题到普利高津：AI 熵增与耗散结构类比]] 与 Control Feedback 主线的关系，并把其中可用的“外部信息输入、反馈、记忆沉积与选择性丢弃”改写成候选数学对象。它是一份研究备忘，不替代 [[current-mainline]]、[[experiment-protocol]] 或 [[theory-and-challenges]]，也不把耗散结构类比作为 A/B 成立的证据。

## 一页版结论

原文与 Control Feedback 最直接的关系，不是热力学，而是下面这个闭环：

```text
隐藏的任务/环境状态
    -> 模型选择下一次观察或操作
    -> runtime 返回局部观察或状态变化结果
    -> 模型更新决策状态
    -> 继续选择观察、修改、验证、提交或回滚
```

这条闭环可以分别落入 A、B 与 A+B：

| 分支 | 更准确的对象 | 原文中最接近的直观说法 |
| --- | --- | --- |
| A：显式状态语义 | 可回放、可归因、可纠偏的状态转移事件 | 信息如何进入、保留、丢弃和纠错 |
| B：局部状态访问 | 部分可观察状态上的主动观测选择 | 主动选择外部信息输入通道 |
| A+B | 模型既选择观察，又显式修改未来将被读取的 workspace | 自书写边界条件、沉积记忆或 stigmergy |

最值得吸收的候选理论是 task-relative value of information：一次读取、检索或验证是否降低了当前任务的最优决策风险，并且其收益是否超过访问成本。最不应直接吸收的是“负熵输入”“排熵”和“严格耗散结构”等尚未定义系统边界与熵泛函的表述。

这条视角不能替 A/B 提供现实 novelty。RAG、tools、verifier、checkpoint、rollback 和 memory 已被强 Agent runtime 广泛吸收；Control Feedback 仍必须按现有强基线、2x2 和成本账本接受裁决。

## 1. 主张层级与术语边界

本页使用四种结论层级：

| 层级 | 含义 | 能否支撑 A/B 主张 |
| --- | --- | --- |
| **现有研究定义** | 已在当前主线或实验协议中声明 | 可以作为实验前提 |
| **候选形式化** | 给出集合、随机变量或函数，但尚未形成完整理论 | 只能指导实验 |
| **经验指标** | 可由 trace、任务标签或模型输出估计 | 只能形成实验结果 |
| **启发性类比** | 迁移直观问题，没有严格对应 | 不可以 |

本文保留 `token`、`instruction`、`workspace`、`read`、`write`、`verify`、`commit`、`rollback` 等既有接口词。以下词不能不加限定地互换：

- 热力学熵。
- Shannon entropy。
- conditional entropy。
- task uncertainty。
- prediction error。
- semantic quality。
- verifier confidence。
- workspace information volume。

特别是，“外部输入带来信息”不推出“外部输入降低任务不确定性”；错误、无关或对抗性观察可能不提供信息，甚至导致更差决策。

## 2. Control Feedback 的最小随机模型

### 2.1 基础对象

以下只是候选形式化。给定概率空间：

$$
(\Omega,\mathcal F,\mathbb P).
$$

给定下列非空集合：

- 可数 workspace 状态集合 $\mathcal W$。
- 有限任务相关目标集合 $\mathcal Z$。
- 可数控制动作集合 $\mathcal A$。
- 可数局部观察集合 $\mathcal O$。
- 有限最终决策集合 $\mathcal D$。

对任意非空可数集合 $U$，定义 $U$ 上的概率质量函数集合：

$$
\Delta(U)
=
\left\{
p:U\to[0,1]
\quad\middle|\quad
\sum_{u\in U}p(u)=1
\right\}.
$$

这里采用有限或可数集合，是为了让本页的求和、条件概率和 Shannon entropy 不依赖额外测度论技术；它不表示现实 workspace 必须很小。

对每个离散决策步 $t\in\mathbb N$，给定随机变量：

$$
W_t:\Omega\to\mathcal W,
$$

$$
Z:\Omega\to\mathcal Z,
$$

$$
A_t:\Omega\to\mathcal A,
$$

$$
O_t:\Omega\to\mathcal O.
$$

$W_t$ 表示第 $t$ 步操作前的完整 workspace/environment state。$Z$ 表示当前任务真正关心但模型尚不完全知道的量，例如：

- failed trace 的 first bad step。
- 被违反的约束。
- 需要修复的对象。
- 下一步应采取的最优操作类别。

$A_t$ 可以是 `read`、`navigate`、`write`、`patch`、`verify`、`commit`、`rollback` 或其他已声明动作。$O_t$ 是 runtime 返回的局部窗口、工具结果、验证结果、错误信息或状态差异。

### 2.2 状态转移与观察

给定 workspace transition kernel：

$$
P:\mathcal W\times\mathcal A
\to\Delta(\mathcal W),
$$

其中 $\Delta(\mathcal W)$ 表示 $\mathcal W$ 上的概率分布集合。$P(w,a)$ 描述在状态 $w$ 执行动作 $a$ 后的下一 workspace 状态分布。

给定 observation kernel：

$$
Q:\mathcal W\times\mathcal A
\to\Delta(\mathcal O).
$$

$Q(w,a)$ 描述动作 $a$ 执行后、下一 workspace 状态为 $w$ 时可能收到的观察分布。确定性工具是退化分布的特例。

本页采用下列时间顺序。给定 $W_t=w$ 并固定执行 $A_t=a$：

$$
W_{t+1}\sim P(w,a),
$$

然后：

$$
O_{t+1}\sim Q(W_{t+1},a).
$$

$O_0$ 作为初始观察由任务实例给定。该顺序只是一种最小约定；若具体 runtime 在状态修改前后各返回一次 observation，应扩展 observation tuple，而不是含糊改变下标含义。

定义第 $t$ 步决策前的可见历史：

$$
H_t=(O_0,A_0,O_1,A_1,\ldots,A_{t-1},O_t).
$$

令 $\mathcal H_t$ 是所有合法 $H_t$ 的集合。策略是函数：

$$
\pi_t:\mathcal H_t\to\Delta(\mathcal A).
$$

这给出了“模型根据已有观察主动选择下一反馈信源或状态操作”的最小对象。

### 2.3 完整状态 Markov 与局部观察非 Markov

若 $W_t$ 已经包含决定未来所需的全部 workspace、外部环境、checkpoint、event log、模型 session state 和 pending operation，则过程可以在扩展状态 $W_t$ 上写成 Markov transition。

模型通常只能看见 $H_t$ 或某个局部 observation，而不能直接看见 $W_t$。因此对模型而言，问题是 partially observable；局部观察序列本身一般不满足 Markov 性。

这比“有 KV 或记忆，所以系统非 Markov”更准确：Markov 性取决于状态是否完整，而不是系统有没有长期记忆。

## 3. B 分支：主动信息获取

### 3.1 Information gain 必须相对于任务目标

令 $\mathcal A^{obs}\subseteq\mathcal A$ 是不改变任务目标 $Z$ 的 observation action 集合，例如只读 `read_window`、search 或 verify。给定满足：

$$
\mathbb P(H_t=h)>0
$$

的历史值 $h\in\mathcal H_t$，定义目标变量的 prior probability mass function：

$$
b_h(z)=\mathbb P(Z=z\mid H_t=h),
\qquad z\in\mathcal Z.
$$

固定某个 $a\in\mathcal A^{obs}$。这里“固定”表示实验或策略主动选择 $a$，而不是从历史数据中筛选恰好满足 $A_t=a$ 的样本。由 $H_t=h$ 下 $(W_t,Z)$ 的条件分布、transition kernel $P$ 和 observation kernel $Q$，得到 $(Z,O_{t+1})$ 的联合概率质量函数：

$$
J_{h,a}:\mathcal Z\times\mathcal O\to[0,1].
$$

定义 observation marginal：

$$
J^O_{h,a}(o)=\sum_{z\in\mathcal Z}J_{h,a}(z,o).
$$

对满足 $J^O_{h,a}(o)>0$ 的 $o\in\mathcal O$，定义 posterior：

$$
b_{h,a,o}(z)
=
\frac{J_{h,a}(z,o)}{J^O_{h,a}(o)}.
$$

对有限集合 $\mathcal Z$ 上的概率质量函数 $b$，定义 Shannon entropy：

$$
H(b)=-\sum_{z:b(z)>0}b(z)\log b(z).
$$

其中 $\log$ 使用任意预先固定且大于 $1$ 的底；改变底只会按常数倍改变 entropy 单位。

动作 $a$ 的候选 conditional information gain 定义为：

$$
\operatorname{IG}(a\mid h)
=
H(b_h)
-
\sum_{o:J^O_{h,a}(o)>0}
J^O_{h,a}(o)H(b_{h,a,o}).
$$

它衡量：主动选择动作 $a$ 后得到的观察，平均减少了多少关于任务目标 $Z$ 的 Shannon uncertainty。按该定义，$\operatorname{IG}(a\mid h)$ 等于联合分布 $J_{h,a}$ 下 $Z$ 与 $O_{t+1}$ 的 mutual information，因而非负。

这里必须使用任务目标 $Z$，而不是整个 workspace $W_t$。一个读取动作可能返回大量与任务无关的数据，从而携带很高的信息量，却没有提高 first-error localization 或 repair 成功率。

### 3.2 Value of information 比 entropy reduction 更一般

给定非负损失函数：

$$
\ell:\mathcal D\times\mathcal Z\to\mathbb R_{\ge 0}.
$$

对任意 $\mathcal Z$ 上的 probability mass function $b$，定义 Bayes risk：

$$
R(b)
=
\min_{d\in\mathcal D}
\sum_{z\in\mathcal Z}b(z)\ell(d,z).
$$

由于 $\mathcal D$ 非空且有限，上式最小值存在。

对当前决策步 $t$，给定动作成本函数：

$$
C_t:\mathcal H_t\times\mathcal A\to\mathbb R_{\ge 0},
$$

以及成本权重 $\lambda\ge 0$，定义候选 task-relative value of information：

$$
\operatorname{VoI}(a\mid h)
=
R(b_h)
-
\sum_{o:J^O_{h,a}(o)>0}
J^O_{h,a}(o)R(b_{h,a,o})
-
\lambda C_t(h,a).
$$

前两项之差是取得 observation 后最优决策风险的期望下降量；最后一项把读取 token、tool call、wall time 或其他成本计入同一个目标。

Information gain 也可解释为允许决策报告任意目标概率分布时，观察前后最优 logarithmic score 的期望改善；这个解释使用的决策集合超出了上面为简化最小值存在性而采用的有限 $\mathcal D$。在一般有限决策与任务损失下，VoI 比 entropy reduction 更贴近实验目标。

### 3.3 对 B 实验的含义

B 当前的 `trace-local first-error localization` 是很适合该形式化的任务：

- $Z$ 可以定义为有限 first-bad-step 集合或 acceptable interval。
- $a$ 可以定义为下一次 `read_window`、地址或 resolver query。
- $O_{t+1}$ 是返回的 trace slice。
- $C(h,a)$ 可以包含 observation tokens、tool call、navigation step 和 wall time。
- $\ell$ 可以使用 first-step distance、interval miss 或 downstream-symptom confusion loss。

不过，真实模型通常没有精确 posterior，因此无法直接计算真实 IG/VoI。第一阶段可在 semi-synthetic 任务中利用已知生成过程和标签计算 oracle value；随后再研究 learned value estimator。不能把 oracle posterior、first-error label 或 future trace 信息泄漏给实验组。

## 4. A 分支：显式状态转移事件

### 4.1 事件不是热力学粒子

A 的核心对象是可进入后续决策的显式状态事件。给定下列非空集合：event id 集合 $\mathcal I$、event-kind 集合 $\mathcal K$、目标引用集合 $\mathcal R_f$、参数集合 $\mathcal U$、返回值或 delta 集合 $\mathcal V$、执行状态集合 $\mathcal S_e$、checkpoint 引用集合 $\mathcal B$ 和 provenance 集合 $\mathcal P_e$。定义候选事件集合：

$$
\mathcal E
=
\mathcal I\times\mathcal K\times\mathcal R_f\times\mathcal U
\times\mathcal V\times\mathcal S_e\times\mathcal B\times\mathcal B
\times\mathcal P_e.
$$

一个候选事件记录是元素：

$$
e_t=
(i_t,k_t,r_t,u_t,v_t,s_t,b_t,b_{t+1},p_t),
\qquad e_t\in\mathcal E,
$$

其中：

- $i_t$ 是 event id。
- $k_t$ 是 event kind，例如 `read/write/verify/commit/rollback`。
- $r_t$ 是目标 state object、address 或 scope。
- $u_t$ 是调用参数。
- $v_t$ 是返回值或 state delta。
- $s_t$ 是执行状态，例如 proposed/executed/failed/committed。
- $b_t,b_{t+1}$ 是操作前后的 checkpoint/state reference。
- $p_t$ 是 provenance，例如 parent event、tool call、evidence 或 verifier reference。

不同实现可以采用不同字段；A 的必要要求仍以 [[experiment-protocol#A 的最小阈值|A 的最小阈值]] 为准。本节元组只说明这些字段可被当作明确数学对象，而不是“信息流”的修辞。

### 4.2 Replay、归因与局部修复

给定初始状态 $w_0\in\mathcal W$ 和事件序列：

$$
e_{0:T}=(e_0,e_1,\ldots,e_{T-1}),
$$

候选 replay function 为：

$$
\operatorname{Replay}:\mathcal W\times\mathcal E^T\to\mathcal W\times\mathcal R,
$$

其中 $\mathcal E$ 是事件集合，$\mathcal R$ 是 replay report 集合。报告至少应说明：

- 哪些事件成功重放。
- 哪些外部输入无法复现。
- 最终状态是否与原轨迹一致。
- 哪个事件首次违反 invariant 或 verifier contract。

“选择性排出错误信息”在 A 中不应被写成熵流，而应被改写为可检查操作：verifier 标记失败事件，rollback 恢复 checkpoint，repair event 产生新 delta，再由 verifier 确认。

### 4.3 数据飞轮的具体版本

原文把新鲜数据、人类反馈和 verifier 称为外部负熵输入。A 更具体的候选数据飞轮是：

```text
失败轨迹
    -> event-level 归因
    -> 定位 first bad event
    -> 从 checkpoint replay
    -> 构造单事件反事实或局部 repair
    -> verifier 检查
    -> 形成 imitation / attribution / repair 样本
```

这条链只有在下列条件下才有训练价值：

- verifier 的适用范围和错误率明确。
- replay 能复现足够多的状态变化。
- counterfactual 不依赖未记录的隐藏副作用。
- repair 后的成功不是 validator/scaffold 直接替模型完成任务。
- 同类 repair 能迁移到 heldout trace，而不只是记住 event id。

## 5. A+B：自书写 workspace

### 5.1 Stigmergic state 的准确含义

若模型执行 `write/patch/mark/commit` 改变 $W_t$，而未来策略又通过 `read/search/inspect` 读取改变后的 $W_{t+1}$，则模型通过环境中的持久痕迹影响自己的后续行为：

$$
W_t
\xrightarrow{A_t^{write}}
W_{t+1}
\xrightarrow{A_{t+1}^{read}}
O_{t+2}
\xrightarrow{\pi_{t+2}}
A_{t+2}.
$$

这就是本页所称的 self-written 或 stigmergic workspace。它不是新算法名称，只是一个结构性质：过去动作留下环境痕迹，后续动作读取该痕迹。

相较于 KV cache，这个对应更直接：

- KV 通常由模型前向自动 append。
- workspace write 是显式控制动作。
- workspace 可以 patch、commit、rollback、branch 和 merge。
- workspace 还可能被人类、工具、subagent 或外部环境共同修改。

### 5.2 控制事件的角色分工

| 事件 | 在闭环中的角色 | 不能自动推出 |
| --- | --- | --- |
| `address/read` | 选择并取得局部 observation | 观察一定有用或真实 |
| `write/patch` | 改变 workspace state | 修改一定正确 |
| `verify` | 从环境取得关于某个 contract 的证据 | verifier 覆盖所有错误 |
| `commit` | 改变 delta 的正式可见性 | 提交后不可回滚 |
| `rollback` | 恢复到已记录 checkpoint | 恢复所有外部副作用 |
| `diagnose` | 推断错误事件、范围或原因 | 诊断等于修复 |
| `replay` | 重执行事件链并检查状态演化 | 外部世界可完全复现 |

这些区分能够把“输入信息、排出错误、维持有序”的叙事改写成可测试的状态机，而不需要热力学术语。

## 6. 原文中几类说法的 Control Feedback 翻译

| 原文说法 | Control Feedback 中更准确的翻译 |
| --- | --- |
| prompt/RAG/tools 是负熵输入 | 它们是 observation sources；是否有价值取决于 task-relative risk reduction |
| verifier 排出熵 | verifier 提供 evidence，runtime 根据 contract 拒绝、回滚或保留候选 |
| CoT 把高阶关联外化 | reasoning trace 把部分 latent computation 写成可观察、可引用但未必可靠的 artifact |
| KV 是自书写沉积记忆 | 显式 workspace、trace、checkpoint 和 patch 更接近可读写沉积状态 |
| 错误 token 形成恶性环 | 错误 state/event 被后继决策反复读取并扩大影响 |
| 遗忘是清淤 | summary/pruning 必须证明保留任务 contract，或接受可测错误 |
| 断流后系统退化 | 缺少新观察或 verifier 时，系统可能依赖过时 belief；但不保证质量单调下降 |

其中最后一列才可以进入 A/B 的实验或候选数学对象。

## 7. 与现有实验协议的接口

### 7.1 不改变 A/B 2x2

本页不增加新的主实验组。现有 2x2 仍是：

| 局部访问 / 显式语义 | 无显式状态语义 | 有显式状态语义 |
| --- | --- | --- |
| 无局部访问 | typed tools 强基线 | A |
| 有局部访问 | retrieval/index 强基线 | A+B |

information-theoretic 指标只能作为解释层或预注册辅助指标，不能让 A/B 组获得额外 oracle observation、隐藏标签或更强 verifier。

### 7.2 A 的候选新增指标

- replay state equality 或 replay divergence。
- event-level attribution accuracy。
- counterfactual validity rate。
- verifier-confirmed local repair success。
- repair 后同类错误复发率。
- hidden side-effect incidence。
- evidence/provenance completeness。

这些指标应与现有 sample efficiency、repair success 和成本账本联合报告。

### 7.3 B 的候选新增指标

- oracle observation value：仅限生成过程已知的 semi-synthetic 数据。
- learned VoI calibration：预测 observation value 与实际 risk reduction 的校准误差。
- useful-observation rate：观察后最优决策风险确实下降的比例。
- irrelevant-information ratio：返回 token 中不影响目标 posterior 或任务决策的比例估计。
- value per token/tool call/wall time。
- negative-value action rate：计入成本后 VoI 为负的动作比例。

这些指标不能替代 first-bad-step hit rate、returned token cost、navigation steps、global fallback 和 total-cost Pareto。

### 7.4 A+B 的候选新增指标

- 写入后被未来有效读取的 state delta 比例。
- stale/incorrect write 对后续决策的影响长度。
- verifier evidence 到 rollback/repair 的转化率。
- 被回滚 delta 中有效工作损失比例。
- event log/summary 压缩后的 replay 与 repair 保真度。
- 跨任务复用的 verified state artifact 数量与收益。

## 8. Strong baseline 仍然是裁决中心

原文把 RAG、工具、验证器和 test-time compute 统一描述为开放系统的信息通道。这种统一叙事会掩盖 Control Feedback 最主要的现实攻击：这些机制已经被现代 Agent runtime 广泛实现。

因此本页不能用来主张：

- A 第一次引入结构化工具事件。
- B 第一次让模型主动检索信息。
- A+B 第一次形成外部记忆闭环。
- 使用 verifier 就证明了显式状态语义有独立价值。
- 使用局部观察就证明了 `Load/Store` 是统一低层原语。

真正的裁决仍是：

- A 是否超过强 typed-tools + trace/logging/checkpoint/replay/diff/transaction。
- B 是否超过 full-context、BM25/vector、SQL/LSP、learned retriever、RLM 和 generated analyzer。
- A+B 是否在预注册指标和 full cost 下形成正交互或 Pareto 非支配点。

## 9. 与 Tide 和 Recursive Memory 的接口

### 9.1 与 Tide

[[20-tide-decentralized-neural-network/tide-statistical-mechanics-and-information-dynamics|Tide、统计力学与信息动力学]] 关注模型/runtime 内部消息、持久状态、routing 和 chunk/decode contract。本页关注 agent/runtime 如何选择外部观察并修改显式 workspace。

两条线可以共享：

- transition、event、provenance 和 visibility 的一般思想。
- 状态压缩是否保持指定 semantic contract 的问题。
- 物理 schedule 不应改变 reference semantics 的约束。

两条线不能直接共享状态集合、事件定义或 correctness theorem。

### 9.2 与 Recursive Decomposition/Memory

递归 Memory 线区分 raw trace、summary、skill 与 verified subproblem artifact。本页提供两个接口问题：

1. 某个 memory item 进入后续决策时，实际降低了多少 task risk？
2. memory summary 丢失 provenance 后，是否仍支持 replay、验证、局部 repair 和适用范围判断？

“选择性遗忘”只有在这些问题得到回答后才有工程含义；单纯减少 memory 大小或 token 数不等于安全排熵。

## 10. 推荐推进顺序

### 第一阶段：使用现有第一任务族

1. 在 semi-synthetic first-error trace 上明确有限目标变量 $Z$。
2. 为每个可读窗口记录实际 risk reduction 和访问成本。
3. 检验当前 selector 是否偏好高价值 observation，而不向模型泄漏 oracle value。

### 第二阶段：连接 A 的 replay 数据

1. 把 first bad step 映射到显式 event id 和 checkpoint。
2. 构造单事件 counterfactual 与局部 repair。
3. 用 verifier 检查 counterfactual validity 和 repair success。
4. 比较强 typed-tools baseline 是否能得到相同数据质量。

### 第三阶段：形成真正的 A+B 闭环

1. 模型先通过有限 observation budget 定位问题。
2. 模型产生显式 patch/write event。
3. runtime verify 后 commit 或 rollback。
4. 后续决策引用 event/provenance，而不是只读取自然语言摘要。
5. 检验 A+B 是否超过 A-only 与 B-only。

### 第四阶段：再研究 learned observation policy

只有在 oracle/规则化实验能验证 observation value 与任务收益的关系后，才训练 learned VoI estimator 或 observation policy。否则模型可能只学会调用格式、resolver 偏差或任务数据中的地址捷径。

## 11. 当前可主张与不可主张

当前可以主张：

- Control Feedback 可以被候选地写成部分可观察状态上的 observation/action loop。
- B 的局部反馈信源选择可以用 task-relative information gain 或 value of information 组织指标。
- A 的显式事件可以让 replay、归因、counterfactual 和局部 repair 成为明确对象。
- A+B workspace 比 KV cache 更直接地体现 self-written/stigmergic state。
- first-error localization 是检验 observation value 的合适有限目标任务之一。

当前不能主张：

- Agent 推理已经被证明是 Prigogine dissipative structure。
- prompt、RAG、tool result 或 verifier 必然降低任务熵。
- information gain 最大的观察必然使最终任务成功率最高。
- entropy reduction 可以替代强基线、成本账本或 A+B 交互指标。
- event replay 等于恢复所有真实外部副作用。
- 显式 workspace 的存在自动证明 `Token = Instruction` 或 `Load/Store` 应成为基础模型接口。

## 参考入口

- [[30-technical-notes/hilbert-sixth-problem-and-ai-entropy|从希尔伯特第六问题到普利高津：AI 熵增与耗散结构类比]]
- [[20-tide-decentralized-neural-network/tide-statistical-mechanics-and-information-dynamics|Tide、统计力学与信息动力学]]
- [[current-mainline|控制反馈：当前主线]]
- [[experiment-protocol|控制反馈：实验协议]]
- [[theory-and-challenges|控制反馈：理论与挑战]]
- [[reference-agent-tools-absorption|Agent 工程对 A/B 弱版本的吸收]]
- [[11-recursive-decomposition-memory/mechanism-landscape|递归分解与 Memory 机制谱系]]
