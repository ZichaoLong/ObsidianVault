---
type: mathematical-instance
status: active
tags: [tide, hb, weighted-message]
---

# HB 多跨度图的三组主绑定

本文将[共同连接图](../topologies/hb-multiscale.md)与已有记忆、[角色分配](../local-semantics/weighted-message/region-allocation-learning-note.md#415-带角色上下界的二次分配)组成可实现的模型族。只保留三组主局部绑定；拓扑尺寸、hub 放置、分区及时间是单独的对照轴。任一行给定所列形状的全部有限参数后，就是完整模型，不再等待选择未定义的函数。

三组记忆、Hub 分区和参数归属的选择理由见[主干候选的形成与取舍](backbone-design.md)；本页负责把这些选择组成可求值的模型。

## 1. 先组成一个混合记忆模型

主配置取 9 层宽度 $4,4,4,8,8,8,4,4,4$，$n=32,h=4$，三个探针数都为 1，非末层每位置有 hub，末层只有 D，group 分区；共 48 个位置、92 区、1712 节点。首先绑定 HB-Timed，输入间隔 $T=4$、入口 $4t+1$。

所有节点采用共同架构的 $P=X_v=\mathbb R^{1+d}$，取 $d=128$、$d_s=d_{\mathrm{sel}}=32$、$d_r=32$、聚合隐藏宽度 $p_a=16$、Full 隐藏宽度 $d_f=512$，归一化 $\epsilon=10^{-5}$。普通节点用有限窗口 KV，hub 用 SSD。函数的归属如下。

| 接口 | 完整选择 |
|---|---|
| Agg | [来源分类聚合](../local-semantics/weighted-message/architecture-learning-note.md#2-接收聚合)，类别与共享见下文，$\alpha_{\mathrm{agg}}=1$ |
| $S_v,q_v^{\mathrm{init}}$, Upd, Mem, $p_v,G_v$ | D 取 KV 的相应函数，H 取 SSD；参数见 §2 |
| Describe, Read | Read$^+$，cat 局部评分，att 区域评分，content_stats key，query_weight=received，$\alpha_{\mathrm{loc}}=\alpha_{\mathrm{sel}}=1$；描述增加角色上下界 |
| SelStep | role_bounded_quad、区间模式、lower_base=mu、固定增益 $\gamma=\gamma_{\max}=2$、固定阈值 $\eta=0$、$\tau_{\mathrm{sel}}=1$，预算见 §3 |
| Next | 全部候选保留 Upd；$Y_j=\{*\}$，正典容量 $K_j=|\mathcal R_j|$ |
| Full | 在本次新状态上求 $G_v$，向所有出边／输出端口广播 $(c_v,G_v)$；$c_v=0$ 不执行 Full |
| 输入 | 每个首层现存节点的入口注入 $(1,E_{\mathrm{role}(v)}x_t)$，两个 $E\in\mathbb R^{d\times d_{\mathrm{in}}}$ 为共享有限矩阵 |
| 输出 | 末层所有 D 端口的原始记录 $Z$；需要单个槽时可用共同 ReadOut，对全部缺席返回零 |

来源类为 ext，以及各入边的 DD1、DD2、DD4、DH1、HH1/2/4、HD1/2/4；不存在的类无需计算。与旧 HB 的“每个父节点一个类别”相比，本实例按边族保留区别，避免参数随每条边增加。Agg 的 $A_v,B_v,e_{v,a}$ 按 §4 的整体参数配置绑定；原子仍逐条参与，不合并边身份。这种聚合在固定宽度内容中压缩信息，不保证无损保留全部来源。

主配置的 hub 没有专门的新汇总算子：它使用同一 Agg 接口，区别在来源、参数、SSD 状态和分配边界。后续若另引入分来源槽、逐边载荷或回取机制，需要另定义，不能由 hub 名称推断。

## 2. 两类记忆与三个主候选

以 $P_{\mathrm{in}}$ 表示当前输入周期：Timed 取 $P_{\mathrm{in}}=T$，Settle 取 $P_{\mathrm{in}}=D=M+1$。以下时钟规定在一次运行及所有 chunk 中保持。

**KV。** 采用 [KV 教材](../local-semantics/weighted-message/kv-memory-learning-note.md)的空缓存初态、Upd、sum 描述和完整 Attention／前馈内容函数。$H_{\mathrm{att}}=4,d_h=32$；共享配置默认 $r_a=8$（尺寸对照取 $\min(r_{\mathrm{ad}},d)$），独立配置按 §4 取 $r_a=d$ 的完整投影表示；窗口为 $T_v=128P_{\mathrm{in}}$ 个逻辑时间，短期率 $\beta_{\mathrm{short}}=\log2/(8P_{\mathrm{in}})$、长期率零。Full 每头旋转全部 32 维，频率 $10^{-4\cdot2(a-1)/32}$；距离偏置取零，$\alpha_{\mathrm{att}}=\alpha_{\mathrm{ff}}=1$。sum 描述不额外使用查询旋转。其余投影、摘要与前馈矩阵按教材给定形状，是有限可训练参数。

**SSD。** 采用 [SSD 教材](../local-semantics/weighted-message/recurrent-memory/ssd-learning-note.md)的零矩阵、零摘要与空缓存初态，全部 Upd、state 描述及内容公式。4 头、1 组、$d_m=32,d_k=32$，短卷积 conv_size=4；矩阵被动衰减零，摘要短期率 $\log2/(8P_{\mathrm{in}})$、长期率零，output_norm_eps=$10^{-5}$，$\alpha_{\mathrm{mem}}=\alpha_{\mathrm{ff}}=1$。有限的投影、卷积系数、$A^{\log},b^\Delta,D_h$、归一化尺度、读取与前馈矩阵均按教材形状给定。

位置和卷积有两种明确的对照口径。主候选采用输入周期换算：Timed 的 $\operatorname{Pos}_v(\theta)=(\theta-1)/P_{\mathrm{in}}$；Settle 用 $(\theta-r_v)/P_{\mathrm{in}}$，故对齐作用处为输入位置 $t$。相对旋转中逐节点常数偏移抵消。Timed 的 conv_stride=1，覆盖相邻逻辑槽；Settle 的 conv_stride=$D$，覆盖相邻输入位置。如此比较的是各时间结构下的实用局部配置。若要**只改边时延**，在共同 $D>M$ 下比较 Timed 与 Settle，须给两侧固定相同日程以及相同 Pos、逻辑窗口、衰减、conv_stride。两种口径分别标注，不把多项变化归因于一项。

有限 KV 窗口 $128P_{\mathrm{in}}$ 表示逻辑时间窗口，不代表缓存恒为 128 项：Timed 中一个节点可以在每个逻辑时间收到不同作用，最多存 $128P_{\mathrm{in}}$ 项；Settle 主配置每个输入位置至多写一次，最多 128 项。SSD 状态固定大小，但所有正接收仍执行更新。

| 主候选 | 普通节点 | hub | 用途与代价 |
|---|---|---|---|
| K | 有限窗口 KV、sum | 同样 KV、sum | 统一算子、显式历史读取的基线；常收消息的 hub 缓存与读取开销较大 |
| S | SSD、state | 同样 SSD、state | 固定状态与统一递归算子；历史被压缩，检索细节可能受限 |
| X，优先建议 | 有限窗口 KV、sum | SSD、state | 普通节点保留细节历史，hub 持续压缩背景；需要两类算子分组 |

三组全部使用 §1 的聚合、评分、分配、Next、输入与输出；只替换本表的记忆整组函数。无 hub 时 K 与 X 是同一个模型，只需保留 K／S 两个不同对照。Gated Delta、基础 affine／delta 及其他分配规则继续作为已有候选目录，不要求第一轮一并实现。排序是实现与设计建议，不是训练效果结论。

## 3. 三种分区及角色预算

普通区取 $k_D=\max(1,\lceil n/32\rceil)$作为默认档；在已登记尺寸 $n=8,16,32,64,128$ 中，可改选 $\{1,2,4,8,16,32,64\}\cap[1,n]$ 或按[统一比较绑定](backbone-comparison.md)选择 pool。小区不必追求约 3%，实际活跃按运行统计。Hub 取有限保底 $\beta=1/4$，默认 $k_H=\max(1,h/2)$（本配置 $h=1,2,4$）；若 $h$ 为其他整数可取 $\max(1,\lceil h/2\rceil)$，并重算约束。

| 分区 | 预算与边界 |
|---|---|
| group | D 区 $k_D$；H 区 $k_H$，各 hub 的 $\alpha=1/k_H$，故 $\overline c_h=\mu_h,\underline c_h=\mu_h/4$ |
| singleton | D 区 $k_D$；每个 H 区 $k=1$、固定通过 $c_h=\mu_h$ |
| mixed | 整区 $k=k_D+k_H$，普通边界不变，hub 取 $\beta=1/4,\alpha=1/k$ |

这三个具体预算均满足角色分配的全输入可行条件。group 对四个 hub 保留共同权衡；singleton 将选择解耦，但固定通过也改变了发送待遇，因此它不是纯分区消融。若只比较分区，需要同时说明如何匹配预算、评分和通过规则；不能宣称两区总预算相等就会等价。

主配置的三种分区共用不含末层 H 的空间图。没有 hub 的位置（含末层）只设普通区，预算取 $k_D$；表中 mixed 的合并预算仅用于同时含 D/H 的位置。复现旧 mixed 配置时可按拓扑定义开启 `terminal_hubs`；这会恢复末层共同选择，属于另一个明确的图绑定。

固定通过的 group 可另取 $k_H=h$；所有 hub 的 $c=\mu$，不再需要靠共同评分分配。Mixed 固定通过必须至少留出 $h$ 的可行预算。非必要时不增加更多角色约束。

## 4. 参数共享与独立状态

主绑定优先采用[三档整体参数绑定](parameter-profiles.md)中的 `region_shared`：将同层同角色等相容节点组按实际区域再拆分，区内矩阵基座加节点私有适配器，区域头逐区域独立。`layer_shared` 保留原跨区域的层级共享，`independent` 使全部节点与区域参数独立。两个共享档的适配秩默认 8，可取 4／16；模块范围和适配方式相同，只改变共享范围。Agg 通过节点参数接口绑定；KV 写入的区域基座例外、独立完整投影表示及 mixed 区规则见该页。

三档覆盖 Agg、来源嵌入、记忆、门／卷积／归一化、描述／评分和 Full，不再逐模块展开共享候选。所有状态始终私有；区域共享使扩宽新增独立基座，并将共享梯度归约限定在区内，层级共享可跨区域归约。各档仍需处理消息反传和数据并行通信。参数量、状态量和通信量分别记录。

旧 HB 教学实例继续保留自身参数定义。新 [HB-Settle 三图实例](hb-settle-weighted-message.md)与 LH 复用本页的 K／S／X 和上述三档参数绑定；不要求实现所有轴的笛卡尔积。

## 5. 精确求值与输出依赖

HB 全部边增加区域秩。给定完整外部输入窗口及左切面，可以按区域序先收齐该区整个时间窗口的驱动，再调用 KV／SSD 的精确块构造，产生所有 Read、选择、Full 和下游消息。区域头无持久历史，Upd 不依赖选择结果；SSD 已知驱动后可使用仿射复合，KV 使用带原时间的写入前缀及查询。因此满足分块教材的局部见证与严格分层整块定理。这里没有承诺任何特定内核的吞吐或串行深度。

切面继续保存每节点状态、单点区域历史和在途消息；在 Timed 的输入周期边界通常仍有迟到消息，不能清空。严格 Settle 在完整输入位置的间隔切面没有跨位置消息，但节点记忆仍传递历史。

输出就绪不增加另一项语义规则。完整驱动、旧状态、Read、SelStep 和 Full 已决定端口值何时可以精确求出。以输入在时刻 0、4 的示意为例：旧输入经时延 6、新输入经时延 2 在时刻 6 合并，聚合只写一次；Settle 版中同源各路径一起到达，则会形成不同的写入和选择。Settle 版仍从历史状态读取旧输入，并非完全没有跨 token 信息。

若节点时刻 5 的接收更新尚未求出，时刻 6 读取其新旧记忆的结果也尚未确定；这不要求等待时刻 5 的 Full，因为本支线 Next 直接保留 Upd。若同区 A、B 都是时刻 6 的候选，A 的控制可依赖 B 的描述，即使没有 B 到 A 的消息边；不要求先求 B 的 Full。若潜在父节点 P 的选择尚未决定，就还不知道 P 会不会在该时刻发送：选择确定 $c_P=0$ 后可以确认缺席，无需执行一个不存在的 Full。区域拆分能去掉共同选择的依赖，仍保留真实消息和自身历史的依赖。

这些区别说明最短消息路径不是自动的物理时延保证。它也不意味着所有输出都要等整张网络：只要本输出的完整依赖已求出，就可产生该端口记录，无关的更晚消息可继续推进。

语言任务外接 Pronounce 可消费这些记录；其窗口、prefill／decode 组织、状态和 next-token 规则属于下游，本仓库不进一步设计该头。

连接和时间核对见[HB／LH 程序](../examples/hb_lh_checks.py)；局部公式沿各记忆教材与角色分配的核对程序验证。这里没有执行整网神经数值实现或训练。

尺寸扩展、FC 统一绑定、二次幂预算及主干参数范围统一见[比较绑定](backbone-comparison.md)；原宽图主配置不被窄图覆盖。
