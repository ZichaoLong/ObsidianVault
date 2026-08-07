---
type: memo
status: draft
tags:
  - tide
  - sparse-routing
  - selector
  - training-stability
  - mixture-of-experts
  - ascend
---

# 分层点阵 Selector 训练稳定性备忘

> [!summary] 本页定位
> 本页记录分层点阵 Tide 候选架构中，CPU 侧严格时间递推 selector、加速卡侧节点计算、稀疏路径和节点持久状态共同带来的训练问题，以及从公开 MoE 研究和先进开源模型技术报告中可借鉴的稳定化方法。本文是研究备忘，不是数学定理、最终架构规范或已经验证的训练方案。

> [!example] 具体架构实例
> 将本页抽象收缩成四级 backbone、八平面 superblock、16 卡映射和三张结构图的候选方案见 [[hierarchical-backbone-multiplane-lattice-v0]]。

## 1. 当前候选架构

当前讨论的平面点阵首先是一个最低复杂度实例，不应被理解为最终只能有“平面、格子、节点”三个固定层次。更一般的候选架构可概括为：

1. 空间图由有限个前向计算阶段组成；最简单实例是顺序堆叠 32 或 96 个平面。
2. 每个平面包含规则点阵；最低层计算单元暂称节点，若干节点组成格子。
3. 节点之上还可以有 hub、区域、格子组或更高层 backbone。后续实现不应把层次数写死，而应允许配置多个路由与聚合尺度。
4. 为了使第一版理论和实现可控，层级区域优先采用嵌套或互不相交的层次划分。任意重叠区域会使状态归属、selector 读写范围和负载统计明显复杂化，可后置研究。
5. 每个节点只连接拓扑后继中的少量节点，因而通信度数有界。最低复杂度实例只允许相邻平面连接；后续可加入只向前的跨平面 shortcut。
6. 上游已激活节点向所有邻接后继发送消息。收到消息的节点总是执行状态更新；是否执行昂贵计算并继续发送，由本节点所属层级的 selector 或其他激活机制决定。
7. selector 可以存在于节点、格子或更高区域层级。不同层级可以使用不同策略，例如高层 always-on、格子级语义选择、格子内节点级负载分配。
8. selector 预期主要在 CPU 上处理紧凑控制数据；节点的大批量数值计算预期由加速卡处理。
9. 4x4 个格子可以静态映射到本机 16 张加速卡；每张卡负责一个格子在多个平面中的节点，跨格子通信只发生在几何相邻设备之间。

这里需要区分三个相互独立的层次概念：

| 概念 | 作用 |
| --- | --- |
| 计算层级 | 哪些节点或区域执行神经计算、持有什么神经状态 |
| 路由层级 | selector 在什么范围读取摘要、维护负载状态并作出激活决定 |
| 设备层级 | 节点、格子或区域如何映射到 CPU 与加速卡 |

三者不必一一对应。一个格子可以是语义专门化单元，格子内多个节点则只是共享或近似共享参数的容量副本；同一个设备也可以承载多个计算层级。

这个候选架构的主要吸引力是：

- 空间计算图保持 DAG，可按平面推进。
- 空间局部性限制单次通信范围。
- 稀疏发送激活限制昂贵节点计算和后续传播规模。
- 一个平面内可以把多个 batch、多个 token 和多个节点的工作打包后交给加速卡。
- 小规模、顺序敏感的控制递推可以交给擅长复杂控制流的 CPU。

但计算放置本身不能解决训练问题。hard selector 是否稳定、节点是否获得充分梯度、路由变化是否改变未来状态分布，仍由模型语义和训练方法决定。

## 2. 核心判断

不能把训练难度简单写成：

$$
\text{Transformer}<\text{Mamba}<\text{MoE}.
$$

更准确的比较如下。

| 架构 | 计算图与梯度 | 主要风险 |
| --- | --- | --- |
| Dense Transformer | 固定计算图，所有激活参数连续参与前向和反向 | attention logit、低精度数值、优化器和大规模系统稳定性 |
| Mamba / SSM | 固定且连续可微的递推，通常可用 scan 并行 | 递推状态数值稳定性、长程梯度、稳定参数化和高性能 scan kernel |
| 标准 MoE | hard Top-K 改变每个 token 的计算子图，只有选中专家获得主要任务梯度 | 路由漂移、专家饥饿、负载不均衡、selected-only feedback 和分布式通信 |
| 分层点阵 Tide | hard routing 可改变后续多个平面的完整传播路径，并可与节点状态和历史负载状态耦合 | 标准 MoE 风险之外，还增加长路径信用分配、路径分布漂移和状态/路径耦合 |

因此，Mamba 不一定在优化意义上比 Transformer 更难，MoE 也不必然产生 loss spike。但 hard routing 确实引入了一组 dense Transformer 和连续 SSM 没有的训练风险。若 Tide 的一次选择会改变后续几十个平面的路径，其训练问题一般比单层 MoE 更强。

## 3. 公开研究对路由漂移的结论

### 3.1 路由漂移真实存在

StableMoE 把 routing fluctuation 定义为：同一个验证输入在不同训练 checkpoint 被分配给不同目标专家。

其 BASE Layer 实验报告：

- 40.9% 的 token 在训练完成 20% 后仍改变目标专家。
- 29.1% 的 token 在训练完成一半后仍改变目标专家。
- 15.4% 的 token 在训练完成 80% 后仍改变目标专家。

StableMoE 的解释是：同一个输入先后更新不同专家，而最终推理只使用其中一个专家，因此梯度被分散，样本效率下降。其解决方案是先学习并蒸馏 router，然后冻结蒸馏后的 router。

“此前专家的训练结果完全失效”仍是过强表述。旧专家的参数不会消失，也可能继续服务相似输入；更准确的后果是：

1. 同一类输入的训练信用被分散到多个专家。
2. 新接手的专家需要适应新的输入分布。
3. router 决策边界附近的输入可能反复切换，产生额外梯度噪声。
4. 若大量输入同时迁移，某些专家会突然过载或突然失去数据，可能形成更明显的训练扰动。

### 3.2 专家专门化不是必然结果

公开研究给出了相互补充、但并不完全一致的观察。

- ST-MoE 观察到部分 encoder 专家具有专门化，但 decoder 专家的清晰专门化弱得多。
- DeepSeekMoE 认为传统 MoE 容易发生知识混杂和知识冗余，并以细粒度专家和 shared expert 促进组合式专门化。
- DeepSeek-V3 报告，相比逐序列强制均衡，batch-wise、低干扰的负载平衡允许更明显的领域专门化。
- OLMoE 从头训练 64 个细粒度专家、每 token 激活 8 个，观察到领域和词表专门化；但同一研究发现 Mixtral 的领域专门化较弱。
- OLMoE 的小规模消融中，固定 shared expert 略差于全部 routed experts；Qwen3 也不使用 shared expert。
- 2026 年的 Less is MoE 给出另一种警告：某些能力分散在多个专家中，但集中在 routed FFN 的少量内部维度，不能把一个完整专家直接等同于一个稳定领域模块。

因此，Tide 不应把“每个节点形成清晰的人类可命名领域”作为必要成功条件。更稳妥的目标是：节点形成对任务有用的组合式计算子空间，路由具有可复现的统计偏好，同时整体质量和计算效率提高。

### 3.3 MoE 不是 loss spike 的唯一来源

先进开源模型的公开报告表明，大规模 MoE 可以稳定训练，但需要同时控制路由、attention、优化器和低精度数值问题。

| 模型 | 公开的相关设计或观察 |
| --- | --- |
| DeepSeek-V3 | 1 个 shared expert、256 个 routed experts、每 token 激活 8 个；使用只影响 Top-K 选择、不改变专家输出权重的负载偏置；偏置更新速度在前 14.3T token 为 0.001，最后 500B token 为 0；报告没有不可恢复的 loss spike 或 rollback |
| GLM-4.5 | 使用 sigmoid gate、loss-free balance 和 QK-Norm；负载偏置在前 15T token 更新，之后冻结 |
| Kimi K2 | 384 个 routed experts、每 token 激活 8 个并保留 1 个 shared expert；15.5T token 训练中报告没有 loss spike；报告定位的主要不稳定来源是 attention-logit explosion，并用 QK-Clip 处理 |
| Qwen3 MoE | 128 个专家、每 token 激活 8 个，不使用 shared expert；使用 global-batch load balancing loss 促进专门化，并用 QK-Norm 控制 attention 稳定性 |
| OLMoE | 64 个专家、每 token 激活 8 个；使用 load balancing loss 和 router z-loss；5T token 训练曲线没有明显大 spike，并公开了训练日志 |

由此应区分：

- 路由漂移主要直接影响样本效率、专家输入分布和信用分配。
- 路由坍缩、容量溢出或大规模同步换路可能触发显著训练扰动。
- attention logit、状态数值、优化器、梯度尺度和低精度误差可以独立产生 spike。
- “MoE 训练发生 spike”不能自动推出“spike 来自 router”。

## 4. Tide 中应分别测量的三种路由变化

路由变化应在多个层级分别测量。节点级选择可以频繁变化，而格子级或更高区域级选择仍然稳定；这时专门化可能发生在格子或区域，而不是单个节点。后续指标和实现接口都不应预设“专家必然等于叶节点”。

### 4.1 参数变化引起的 checkpoint 漂移

固定同一条验证序列和同一初始状态，在不同训练 checkpoint 上比较节点选择。变化来自 router、上游节点或节点表示参数的更新。

这是 StableMoE 主要讨论的 routing fluctuation。

### 4.2 历史状态引起的序列内变化

即使所有参数冻结，相同内容出现在不同 token 位置或不同历史负载之后，也可能被送往不同节点。例如一个节点最近已被频繁激活，selector 会降低其优先级。

这是当前 Tide selector 有意引入的变化，用于序列时间维度的负载均衡。它不是训练漂移，也不一定破坏更高层级专门化。例如：

- 语义 router 可以稳定地选择某个格子。
- 格子内 allocator 可以根据历史激活次数，在多个节点之间轮换。
- 格子形成稳定计算专门化，格子内节点主要承担容量分片或近似同质副本。

但“近似同质副本”不能只看参数。若格子内节点共享 kernel 参数，却分别持有不同 KV cache、SSM state 或局部记忆，它们对同一输入仍可能产生不同输出，不能只按负载任意互换。纯负载轮换较安全的前提是：相关参数和语义状态都共享、同步、复制或能通过明确的状态分片规则访问。否则节点选择仍必须考虑其局部状态内容。

只有当节点拥有强烈不同的独立参数或状态，而负载控制又频繁压过语义分数时，节点级专门化才会明显被打散。因此应同时声明每个层级是“语义专家”“有状态分片”“无状态容量副本”“always-on backbone”还是混合角色。

### 4.3 batch、chunk 或并发请求引起的变化

若同一序列的路由取决于：

- 同一 batch 中还有哪些序列；
- 当前 chunk 的长度或切分方式；
- 同一设备正在服务哪些其他请求；
- 跨请求共享的实时硬件负载；

则相同序列可能因执行方式不同而改变模型输出。这不仅是训练稳定问题，还会破坏 batch invariance、chunk composition 和 `prefill = decode` 语义。

Tide 应禁止第三类变化进入模型语义。这是硬约束，而不是一种训练偏好：

> 对固定参数、固定单序列输入和固定单序列左边界状态，逐 token `decode`、任意合法 chunk 切分的 `prefill`、不同 batch 组合以及不同物理调度必须产生相同的语义 artifact。

全局硬件负载只能影响节点放置、kernel 合并、执行先后、通信批次和物理并行方式，不能改变语义路由结果。若负载历史影响语义选择，它必须是单序列状态或正式声明且在一次语义执行中固定的模型参数。CPU 可以批量计算多个序列的 selector，但必须为每个序列维护彼此独立的控制状态。

## 5. Tide 特有的训练风险

### 5.1 selected-only feedback

hard Top-K 的离散索引通常不直接求导。任务梯度主要经过被选中的节点和被选中 gate weight；未被选择的节点无法告诉 router：“选择我是否会更好”。

在标准 MoE 中，这已经会造成未选专家缺少任务反馈。在多平面 Tide 中，一个早期阶段的选择还会改变后续多个层级的输入，未选路径的反事实质量更难获得。

### 5.2 路径级分布漂移

第 $p$ 个平面的路由变化会改变第 $p+1$ 个平面的输入分布；第 $p+1$ 个平面的 router 和节点参数随之变化，又会继续改变更深平面。若有 96 个平面，这种变化可以沿整条路径放大。

### 5.3 长路径信用分配

若只在最终输出处计算损失，早期平面 selector 收到的学习信号要经过许多 hard choice、节点状态和局部 kernel。即使数值梯度仍能传播，信号也可能很弱且方差很大。

路径级分布漂移与长路径信用分配相互放大，但不是同一个问题：

| 问题 | 发生范围 | 即使另一问题不存在是否仍可发生 |
| --- | --- | --- |
| 路径级分布漂移 | 不同训练 checkpoint 或不同历史状态之间，下游输入分布不断变化 | 可以。一个很浅的 router 也可能频繁换路 |
| 长路径信用分配 | 一次固定前向/反向内部，最终损失必须穿过很长路径给早期计算分配信用 | 可以。完全固定的深网络也有长程梯度问题 |

层级化 backbone、短残差和周期性收拢可以同时缓解二者：公共路径缩短梯度距离，收拢点限制一次稀疏选择持续影响后续分布的长度。

### 5.4 与本节点激活无关的状态更新

当前设想已经避开最强的条件状态副作用：

1. 上游已激活节点向全部邻接后继发送消息。
2. 后继节点只要收到消息，就更新自己的长期状态。
3. 本节点是否激活只决定是否执行昂贵计算和继续向下游发送。

因此，本节点的状态更新不依赖本节点当前是否被 selector 激活。但它仍然不是“与所有路由无关”：上游哪些节点被激活，仍决定本节点会收到哪些消息。剩余风险是路由改变节点的入站消息分布，而不是本节点 selector 直接决定状态是否更新。

还必须定义节点在某个逻辑时刻没有收到消息时，状态是保持不变、执行 decay、推进空步，还是进行其他确定转移。该规则会直接进入 `prefill = decode` 语义。

### 5.5 激活饥饿、梯度饥饿与语义饥饿

激进的历史负载均衡，例如优先激活从未被激活的节点，可以消除“激活次数长期为零”，但不能自动消除以下问题：

| 类型 | 含义 | 激进负载均衡是否自动解决 |
| --- | --- | --- |
| 激活饥饿 | 节点很少被选中执行昂贵 kernel | 基本可以 |
| 梯度饥饿 | 节点虽然被选中，但输出权重很小、路径未影响损失或梯度被截断 | 不一定 |
| 语义饥饿 | 节点收到的样本不断变化，缺少重复、连贯的输入分布，无法形成有用计算 | 不能，甚至可能加重 |
| 优化器状态陈旧 | 参数长时间无有效梯度，动量和尺度统计失配 | 只能部分缓解 |

如果专门化预期发生在格子级，较安全的方案是：先按语义选择格子，再在格子内对真正可交换的节点做激进负载分配。这里的“可交换”至少要求相关参数和被读取状态等价。若格子内节点持有不同 KV/SSM 历史，即使参数共享，也不能只按“最少使用优先”任意选择。

### 5.6 层级发散与收拢

标准 MoE 的稀疏分支通常在一个 block 内立即求和并返回共同 residual stream，因此一次路由决定的生命周期很短。Tide 若让分支连续穿过许多平面而长期不收拢，路径分布漂移和信用分配都会更强。

建议把层级化 backbone 设计为反复出现的有限生命周期结构：

~~~text
高激活率主干
    -> 小倍率一级分支
        -> 可选的更稀疏二级分支
        -> 一级收拢点
    -> 主干收拢点
    -> 下一段
~~~

每次只做有界倍率发散，例如逐级从 1 扩展到 4、再到 16 或 32，而不是一次从 1 扩展到 512；同时显式给出分支最大寿命、每个父区域的激活预算和收拢位置。仅限制单级 fan-out 仍不足够：若分支持续不收拢，可能路径数仍随层数快速增长。

## 6. 建议的 selector 分解

建议明确分离神经状态、语义评分、负载控制和 selector 策略接口。

### 6.1 神经状态

记节点 $i$ 在 token 位置 $t$ 的神经状态为 $q_{i,t}$。它属于模型语义，可以参与连续可微的状态更新和节点计算。候选状态至少包括：

| 状态类型 | 典型内容 | 大小随历史增长 |
| --- | --- | --- |
| Attention memory | 本节点收到的消息对应的 K/V 记录、位置与 causal metadata | 通常增长，或受窗口/压缩策略限制 |
| SSM hidden state | Mamba/SSM 的固定维度递推张量 | 固定 |
| Linear-attention accumulator | 例如累计的 $\sum \phi(k)v^\top$ 与归一化统计 | 固定或低阶增长 |
| 有限窗口状态 | convolution buffer、最近消息环形缓冲、局部 delay line | 有界 |
| 可学习局部记忆 | 固定数量 memory slots、fast-weight 或其他局部存储 | 由设计决定 |

模型参数不属于这里的单序列神经状态；selector 的历史激活计数也应另列为控制负载状态。

### 6.2 语义分数

由可学习函数计算内容与节点的匹配程度：

$$
s_{i,t}=g_{\theta}(h_{i,t},q_{i,t}).
$$

这里 $h_{i,t}$ 表示节点收到的当前输入摘要。语义分数最好在加速卡上批量计算，以保留正常的自动微分路径。

语义分数必须在 `ActiveCompute` 之前可得，否则会形成“必须先执行昂贵 Attention/FFN，才能决定是否执行它”的循环。它可以读取入站消息、更新后的轻量状态、低秩 probe 或上一时刻摘要，但第一版不应依赖本次尚未执行的完整 Attention/FFN 输出。

### 6.3 控制负载状态

CPU 维护小型负载状态：

$$
c_{i,t+1}
=
\beta c_{i,t}
+
(1-\beta)\mathbf 1[i\in A_t].
$$

$c_{i,t}$ 只记录历史选择统计，不承载神经表示。建议对其停止梯度、限制数值范围并使用慢更新。

### 6.4 Selector 策略接口

实现架构不应把 selector 固定为一种 hard Top-K。一个 selector 至少应显式声明：

1. 读取哪个层级的语义分数、控制状态和静态拓扑约束。
2. 输出 hard mask、soft weight、稀疏连续 weight，还是多者组合。
3. 如何更新下一时刻的控制状态。
4. hard 决策在反向中使用停止梯度、straight-through estimator、soft surrogate，还是额外蒸馏目标。
5. 输出哪些可重放 artifact，例如候选集、分数、负载偏置、激活集和权重。

可比较的策略包括固定/hash、纯语义 Top-K、纯 quota、联合打分、softmax、sparsemax/entmax、训练软推理硬、以及多层级混合策略。

### 6.5 语义优先、负载优先与层级混合

原备忘给出的语义优先方案是：

先由语义分数产生较大的候选集合：

$$
C_t=\operatorname{TopM}(s_t).
$$

再只在语义候选内部做负载仲裁：

$$
A_t=
\operatorname{TopK}_{i\in C_t}
\left[
s_{i,t}-\lambda(c_{i,t}-\bar c_t)
\right],
\qquad K<M.
$$

其中 $\bar c_t$ 是当前候选区域的目标或平均负载。负载项只应在多个语义上可接受的节点之间调整，不应把一个 token 强行送给语义分数很低的节点。

不同顺序的权衡如下。

| 方案 | 形式 | 优点 | 风险 |
| --- | --- | --- | --- |
| 语义优先 | 先取语义 Top-M，再在其中均衡 | 保护任务质量和专门化 | 热门节点可能反复进入候选，负载自由度有限 |
| 负载优先 | 先取低负载候选，再按语义选择 | 最强地消除激活饥饿和设备偏斜 | 可能强迫语义不合适节点处理输入，增加漂移 |
| 联合打分 | 对 $s_{i,t}-\lambda c_{i,t}$ 直接 Top-K | 实现简单，平滑调节权衡 | $\lambda$ 难选；负载可能压过语义 |
| 容量约束 | 先排除超 quota 节点，再按语义选择 | 语义清晰、容量有硬上界 | 容量不足时需要确定 fallback |
| 层级混合 | 上层语义选择区域，下层在区域内负载分配 | 允许格子级专门化与节点级均衡并存 | 需要明确各层参数是否共享及各层状态归属 |

当前最值得优先实验的是层级混合：

~~~text
语义分数选择格子或高层分支
    -> 格子内 allocator 在少量节点间做负载分配
    -> 若叶节点是容量副本，则共享主体参数
    -> 若叶节点是独立专家，则保留较弱的节点语义分数
~~~

这样可以把“专门化发生在哪里”和“负载均衡发生在哪里”分开，而不是让一个 selector 同时解决两个相互冲突的目标。

格子级专门化可进一步采用两种状态组织：

| 组织方式 | 叶节点角色 | 负载均衡自由度 |
| --- | --- | --- |
| 格子共享语义状态 | KV/SSM/记忆属于格子，叶节点主要执行无状态或可复制 kernel | 较高，叶节点更接近容量副本 |
| 叶节点独立语义状态 | 每个叶节点持有自己的 KV/SSM/记忆 | 较低，selector 必须同时考虑状态相关性与负载 |

若首要目标是验证层级 routing 和训练稳定性，格子共享状态、节点执行 shard/replica kernel 是更容易的第一版。叶节点独立状态表达力更强，但会把节点重新变成有状态专家。

### 6.6 负载偏置不进入专家输出权重

节点输出可写成：

$$
y_t
=
B(h_t)
+
\sum_{i\in A_t}
\operatorname{softmax}_{A_t}(s_{i,t})
\Delta_i(h_{i,t},q_{i,t}).
$$

$B$ 是 always-on backbone，$\Delta_i$ 是被选择节点的稀疏残差。负载修正只决定 Top-K 成员，不进入 softmax 权重。这借鉴了 DeepSeek 的 loss-free balancing：硬件均衡信号不直接扭曲专家输出幅度。

## 7. 节点内部建议拆分

每个节点建议至少区分三个逻辑步骤。

### 7.1 `Observe / Update / Score`

所有收到上游消息的候选节点都执行廉价步骤：

- 聚合或读取当前入站消息。
- 更新有界、稳定的节点神经状态。
- 计算供 selector 使用的紧凑语义分数或摘要。

该步骤应能对一个 chunk 内的多个 token 做批量、scan 或 CPU 顺序处理，但不依赖本节点当前 token 的 hard activation 结果。

### 7.2 `Select`

CPU 按 token 逻辑顺序更新负载状态并产生紧凑 route list。它只处理候选标识符、少量分数和计数，不读取完整 hidden tensor。

### 7.3 `ActiveCompute / Emit`

加速卡根据 route list 对选中节点执行 packed Attention、FFN、SSM 或其他昂贵 kernel，并产生向下一平面的传播消息。

这种拆分的关键收益是：hard selector 主要控制昂贵残差和传播，而不是直接控制节点是否进行任何状态更新。收到消息并更新状态不等于一定获得有效任务梯度；只有该状态在当前或未来被读出并影响损失，梯度才会到达相应更新。

## 8. 稳定化原则

### 8.1 层级化 always-on backbone

always-on backbone 不应只理解为“每个平面一个 shared expert”。它可以形成多个嵌套层级：

- 少量最短、最高激活率的核心路径。
- 从核心路径生长出的一级残差分支。
- 从一级分支继续生长出的更稀疏、更专门的二级分支。
- 各级分支在预定位置重新汇入本级或上一级 backbone。
- 类似 LH hub 的高层节点可以常态激活，并为低层稀疏节点提供信息与梯度通路。

每个层级应配置：

| 配置 | 含义 |
| --- | --- |
| 激活策略 | always-on、soft、hard、quota 或混合 |
| fan-out 上界 | 一个父区域最多扩展多少子区域或节点 |
| 分支寿命 | 分支最多跨越多少计算阶段后必须收拢 |
| merge 规则 | residual add、加权和、拼接投影、SSM 更新或其他明确算子 |
| 参数关系 | 共享、共享主体加 adapter、完全独立 |
| 状态归属 | 状态属于叶节点、格子、hub 还是 backbone |

一个不会被 selector 切断的基础路径可以是：

- 恒等或线性残差；
- 共享 SSM；
- 公共基础块；
- shared expert；
- 共享主干加 node-specific adapter。

shared expert 不是已被所有模型证明最优的固定答案。这里保留 always-on 路径的主要目的，是防止路由变化同时切断信息流和训练梯度，而不是预先规定知识必须存入某个共享专家。

#### 8.1.1 前向跨平面 shortcut 与不等长路径

若一条跨平面边始终从较早阶段指向较晚阶段，它仍属于空间 DAG，不会因为“跨越多个平面”自动破坏 `prefill`。固定非负整数时延可以：

- 直接写入消息的逻辑到达时间；
- 或展开成若干只做延迟的中间节点。

真正需要定义的是：不同长度路径在何种逻辑时刻汇聚、节点按什么顺序更新状态、哪些消息对当前读出可见。只要这些规则固定、因果且节点窗口转导器满足时间分块组合律，不等长前向路径本身是可处理的。

工程上，等长路径加 residual 更容易做规则张量计算；带时间桶的不等长路径表达力更强，但需要 ragged inbox、watermark 和更复杂的 packed kernel。两者应作为可对比方案，而不是预先断言只有等长路径正确。

#### 8.1.2 反馈回路的边界

[[human-cortex-and-whole-brain-signal-propagation-survey]] 强调，真实脑网络包含并行分支、跨区 shortcut、丘脑中继和大量前馈/反馈闭环。这为 Tide 的多尺度 backbone、hub、旁路和选择性增益提供设计联想，但不构成数字模型应直接复制脑连接的证据。

对 Tide：

- 同 token、同内部时刻的反向边会重新引入空间环和 zero-delay 求解问题，暂不进入高性能主线。
- 带正时延、从 token $t$ 的高层状态影响 token $t+1$ 或更晚低层状态的反馈，可以在有限 chunk 上展开成 event DAG，但会引入时间递推，需要单独证明是否 scan-composable。
- 若只需要“先高层处理，再回到低层细化”的效果，可以在更晚平面复制一个低层类型节点，用前向 DAG 表达 refinement，而不必首先引入真实空间环。

因此，第一版可保留接口上的反馈能力，但 reference 配置优先采用前向 shortcut、延迟状态和后置 refinement。

#### 8.1.3 快路径、慢路径与固定读出周期

Tide 的自回归接口仍需要在固定外部周期提取或输出 token。不同内部路径具有不同时延时，必须从以下两种语义中明确选择：

| 语义 | 当前 token 的读出 | 慢分支的作用 |
| --- | --- | --- |
| deadline merge | 当前 token 必须等待所有被声明为可见的活跃分支在读出截止点前汇入 | 直接影响当前输出；物理关键路径受最慢活跃分支约束 |
| late-context update | 当前 token 由快 backbone 在固定截止点读出 | 未赶上截止点的慢分支只能更新未来 token 可见的状态，不能追溯修改当前输出 |

第一种更接近 conditional depth；第二种更接近“快速反射/初步输出 + 较慢上下文更新”。两者都可以定义成因果模型，但训练目标、事件 DAG、边界状态和 `prefill` 调度不同，不能混为一个模糊的“快慢路径”概念。

若希望保持固定 decode 周期且避免每个 token 等待最深路径，late-context update 更自然；代价是复杂分支学习的是未来上下文贡献，而不是对当前 token 的迟到修正。

late-context update 也不自动得到高性能 `prefill`。若慢分支只通过可结合 scan、固定 SSM 更新或其他可组合状态影响未来，它仍可能批量执行；若慢分支不可预测地改变下一个 token 的 hard routing，则会重新形成跨 token 控制链。

#### 8.1.4 小词表与减少平面数

“用 byte 级词表让简单词主要由 backbone 学会，复杂长句扩散到更深分支”是有价值的研究假设，但当前没有理论保证。

byte tokenization 的收益包括更小 embedding/output vocabulary、无 OOV 和更细粒度组合；代价是序列显著变长，selector 递推次数、状态更新次数以及 Attention/SSM 的时间维度成本都会增加。简单词也需要多个 byte token 才能完成，因此“简单内容必然走短路径”需要由训练目标、路由代价或辅助监督主动促成。

可比较的方案至少包括：

1. 纯 byte token。
2. 常规 BPE/SentencePiece token。
3. byte 输入后先做局部 patch/compression，再进入层级 backbone。
4. 固定平面数但允许 conditional depth。
5. 减少平面数、提高每平面节点容量或状态表达力。

平面数不应直接类比 GPT block 数。若层级 backbone、局部状态和分支计算已经提供足够有效深度，减少平面数完全可能；但应由 scaling experiment 决定。

### 8.2 长期状态采用与本节点激活无关的更新

原文的 `route-independent update` 容易误解。更准确的目标是：给定本节点已经收到的消息，其状态更新不再取决于本节点当前是否被激活。

记 $I_{i,t}$ 为节点 $i$ 在逻辑位置 $t$ 收到的消息集合，优先采用：

$$
q_{i,t+1}=U_i(q_{i,t},I_{i,t}),
$$

随后独立计算激活决定 $a_{i,t}$，并令：

$$
\operatorname{emit}_{i,t}
=
\begin{cases}
\operatorname{F}_i(q_{i,t+1},I_{i,t}), & a_{i,t}=1,\\
\varnothing, & a_{i,t}=0.
\end{cases}
$$

这正是当前设想：“收到即更新，激活才发送”。上游路由仍会改变 $I_{i,t}$，所以状态整体仍然是 path-dependent。

对不同状态，更新与激活计算可以进一步拆分：

| 状态 | 收到消息时执行 | 节点激活时执行 |
| --- | --- | --- |
| KV cache | 对消息做 K/V projection，附加逻辑位置并写入本节点 ragged cache | 计算 Q，读取本节点历史 K/V，执行 packed causal attention、输出投影和可选 FFN |
| SSM | 对收到消息执行输入投影和状态递推；若无消息则按定义保持或 decay | 从更新后的状态产生较昂贵输出、门控、FFN 和发送消息 |
| Linear attention | 更新固定维度 accumulator | 用 query 读取 accumulator 并产生输出 |

“收到即更新”把一部分成本从激活计算转移到了状态维护，并不等于免费。若每条收到消息都追加 K/V，则全图 cache 增长量近似为：

$$
N_{\mathrm{KV}}
\propto
\sum_{i,t}|I_{i,t}|.
$$

当每个已激活上游节点向 $d$ 个邻接后继发送时，单步新增记录量约与“激活发送数乘以 $d$”同阶。它仍受稀疏激活和有界度控制，但可能在长序列、多平面下成为主要内存成本。固定大小的 SSM 或 linear-attention state 在这一维度更容易控制。

对于 Attention，节点在一个 chunk 内收到的消息数一般不同，因此需要按 `(batch, node, logical time)` 整理 ragged KV。可先把所有 K/V projection 合并为大矩阵计算，再按节点写入 packed offset；被激活 query 再调用支持可变长度的 packed attention。

同一逻辑位置可能收到来自多个上游节点的多条消息。Attention 可以把它们作为带 source、logical time 和 message id 的多条 K/V 记录；SSM 等顺序敏感更新则必须规定先聚合、按固定来源次序更新，或使用可交换/可结合的联合更新。物理到达顺序不能决定语义结果。

训练时还需要区分：

- 当前训练 chunk 内 K/V 的正常反向图。
- 跨 chunk boundary state 是保留完整梯度、重计算，还是按 truncated BPTT detach。
- 一个节点虽然写入 K/V，但若在反向截断前从未被激活读取，这次写入可能没有任务梯度。
- 节点状态不能跨 optimizer step 直接复用旧权重生成的神经 activation，除非定义专门的 replay/recompute 语义。

若昂贵节点计算还要写长期状态，应先限制为有界、小幅、带衰减的状态增量，并单独验证其稳定性。

### 8.3 从 dense / soft 逐步退火到 hard sparse

不建议让随机初始化的 router 和节点直接进入高度稀疏 Top-K。可按以下方向逐步推进：

1. 先训练 always-on backbone。
2. 加入共享初始化的节点 adapter，初期全部或大比例激活。
3. 使用 soft gate、大 $K$ 或大 fan-out，让多个候选获得反馈。
4. 逐渐减小 $K$ 和 fan-out，增加 hard routing 比例。
5. 最后再加入历史负载状态和较强的时间均衡。

这与 EvoMoE 的 dense-to-sparse 思路一致，但 Tide 还需要同时控制多平面路径和节点状态。

### 8.4 降低 checkpoint 路由漂移

可选择或组合：

- router 使用小于节点 kernel 的学习率。
- 用 EMA teacher 或蒸馏 router 提供较稳定的选择目标。
- 训练后段冻结 router，或至少冻结负载偏置更新。
- 对 Top-K 边界加入 margin，减少接近并列时的频繁翻转。
- 使用 hysteresis：旧路径只在新路径明显更优时才切换。
- 初期使用 $K>1$，避免 Top-1 单次切换造成全部计算替换。

hysteresis 和 margin 都会减少探索，不能从训练开始就过强；应结合 route churn 和验证质量调整。

### 8.5 给未选择节点提供受控反馈

候选方法包括：

- 训练期使用比推理期稍大的 $K$。
- 以较小概率计算一个未选择的 shadow route，但不改变主前向输出。
- 对节点加入局部预测或 representation distillation loss。
- 在训练早期保留最低探索配额。
- 由 dense teacher 或较软 router 给出候选质量监督。

这些方法增加训练计算量，但直接缓解“router 不知道未选路径是否更好”的 selected-only feedback。

### 8.6 缩短长路径信用分配

可在少量中间平面加入训练期辅助读出或 teacher representation matching。辅助损失应在训练后期衰减，避免强行要求每个平面都形成完整语言模型表示。

### 8.7 利用空间邻接进行平滑初始化

相邻节点可以共享基础参数，只保留小型局部 adapter；也可以在训练早期对相邻 adapter 使用较弱的参数或输出平滑约束。这样路由在邻近节点间切换时，输出不会发生完全无关的跳变。

该方法可能有用，也可能抑制真正的专门化。比任意相邻节点 Laplacian 平滑更可控的第一选择是：同一语义格子内部共享主体参数，叶节点只保留小 adapter；跨格子不默认平滑。平滑约束应做消融，并在后期减弱或移除。

### 8.8 数值稳定性独立处理

- router score 和负载统计优先使用 FP32。
- 对 softmax router 考虑 router z-loss 或显式 logit 范数约束。
- Attention 使用 QK-Norm、QK-Clip 或其他明确控制 logit 范围的方法。
- SSM 状态使用稳定参数化、有界 gate、衰减和状态范数监控。
- 使用梯度裁剪，并分别记录 router、节点 kernel、状态更新和 embedding 的梯度尺度。

不能因为 route 指标稳定，就停止检查 attention、状态和低精度数值。

## 9. CPU 与加速卡的建议执行边界

在只有相邻平面边的最低复杂度模型中，合理的单平面执行流程是：

```text
前一平面完成当前 chunk
    -> 加速卡批量执行 Observe / Update / Score
    -> 一次传输紧凑候选分数和标识符到 CPU
    -> CPU 按 token 顺序扫描 selector 状态并生成 route list
    -> 一次传输 route list 到加速卡
    -> 加速卡按节点/格子打包 ActiveCompute / Emit
    -> 进入下一平面
```

必须避免：

```text
每个 token
    -> 加速卡等待 CPU
    -> CPU 选择
    -> 加速卡执行
    -> 再处理下一个 token
```

后者会把 host/device 同步延迟放入长度为 $L$ 的关键路径。

若加入只向前的跨平面 shortcut，调度单位应从“相邻平面”推广为“拓扑阶段”：

1. 一个阶段等待其所有拓扑前驱产生当前窗口所需的消息桶。
2. scheduler 按目标节点和逻辑到达时间合并相邻边与 shortcut 消息。
3. 加速卡执行本阶段的批量状态更新与评分。
4. CPU 完成本阶段各层级 selector 的顺序控制。
5. 加速卡执行激活计算并把消息投递到后续一个或多个阶段。

只要所有边严格向前，仍可按拓扑序处理。不同固定时延需要额外时间桶，但不要求退化为每 token 一次 host/device 同步。真正的反馈边则不能直接套用这一单次拓扑流程。

即使 selector 每个事件只处理少量标量，总事件数仍约为：

$$
O(PBL),
$$

其中 $P$ 是平面数，$B$ 是 batch size，$L$ 是 chunk 长度。随着节点计算越来越稀疏，CPU selector 反而可能成为 Amdahl 瓶颈。因此需要：

- 候选度数保持常数且较小。
- 每个平面批量扫描多个 batch 和 token。
- 使用紧凑连续内存和预分配 route buffer。
- CPU 选择与其他平面的加速卡计算双缓冲或流水重叠。
- 对 selector 单独测量每秒决策数，而不是只看其数据体积。

## 10. 建议的训练推进顺序

### 阶段 A：固定均衡路由

使用静态 hash、固定局部路径或预生成均衡路由，不训练 selector。

目标是验证：点阵拓扑、节点 kernel、状态更新和稀疏梯度覆盖本身能否训练。若这一阶段失败，问题不应归因于学习式 router。

### 阶段 B：token-local learned routing

加入只依赖当前节点输入和神经状态的可学习语义分数，不加入历史负载递推。

目标是隔离 learned routing 和 selected-only feedback 的影响。

### 阶段 C：慢速负载偏置

加入停止梯度、慢更新、幅度受限的负载修正；先在 optimizer step 或固定大窗口之间更新，并在一次 forward 内冻结。

目标是验证负载均衡收益和语义专门化损失之间的权衡。

### 阶段 D：单序列严格时间递推 selector

最后加入逐 token 更新的 selector 历史状态，并证明、测试其 chunk composition 和 `prefill = decode` artifact equality。

目标是判断精细时间均衡是否带来超过额外串行控制、路由变化和训练困难的收益。

不建议直接从阶段 D 开始训练完整 96 平面模型。否则一旦训练不稳定，很难区分根因。

## 11. 必须记录的训练指标

### 11.1 路由一致性

- 固定验证前缀在不同 checkpoint 的 Top-K Jaccard overlap。
- 每个 token 最后一次改变目标节点发生在训练的什么位置。
- 第 $K$ 与第 $K+1$ 个候选之间的 score margin。
- 邻近 checkpoint 的路径编辑距离。
- 不同平面的 route saturation 速度。

### 11.2 负载与死亡节点

- 每平面、每格子和每节点的激活次数。
- load coefficient of variation、Gini coefficient 和最大/平均负载比。
- 连续多个窗口未被激活的 dead node 比例。
- 节点收到状态更新但未执行昂贵 kernel 的比例。

### 11.3 梯度与输入分布

- 每节点获得非零任务梯度的频率。
- router、Observe/Update、ActiveCompute 的梯度范数。
- 每节点输入均值、方差、范数和主成分随训练的漂移。
- route change 与节点输入分布突变的相关性。

### 11.4 数值与状态稳定性

- attention 最大 logit。
- SSM 或其他持久状态的范数、谱或衰减统计。
- NaN、Inf、梯度裁剪触发率和低精度溢出。
- loss spike 与 route churn、load imbalance、attention logit、状态范数之间的时间相关性。

### 11.5 语义不变量

- 同一序列在不同 batch 同伴下路由和输出相同。
- 同一序列采用不同 chunk 切分时，节点状态、route list、消息和输出 artifact 相同。
- `prefill` 与逐 token `decode` 的节点级状态、选择和输出一致。
- 训练和推理使用相同 selector 语义；训练期额外 shadow route 不进入 reference output。

## 12. 当前最重要的设计结论

当前最值得优先固定的不是某一种具体负载算法，而是以下边界：

1. 语义分数、神经状态和负载控制状态是不同对象。
2. CPU allocator 只对紧凑候选做顺序仲裁，不承担大张量神经计算。
3. 负载历史只在语义候选内部做小幅调整，不能取代内容路由。
4. hard selector 主要控制昂贵残差和发送激活，不能轻易切断全部状态更新、信息路径和梯度路径。
5. 模型语义中的状态必须按序列隔离；跨请求硬件负载不能改变模型结果。
6. 完整模型应从固定路由、token-local router、慢负载偏置逐级推进到 stateful selector。
7. 专家或节点专门化应作为可测量的统计现象，而不是预先假设的领域模块划分。
8. 路由稳定性与数值稳定性必须独立监控。

## 13. 待继续讨论的问题

1. `Observe / Update` 是否对所有局部候选执行，还是只对收到实际消息的节点执行？
2. 未激活节点的神经状态应该如何更新，才能兼顾训练覆盖、计算稀疏和长期状态语义？
3. 每个平面的 always-on backbone 应是统一共享块、每格子共享块、SSM，还是只保留轻量残差？
4. 历史负载状态应在序列边界重置，还是作为可延续的单序列 boundary state？
5. 负载修正只作为 Top-K tie-breaker，还是允许在更大的语义候选集合内重新排序？
6. 是否需要训练期 shadow route，以及允许多少额外计算预算？
7. 中间平面辅助损失如何设计，才不会把所有节点强制训练成相同表示？
8. 节点和格子到 16 张 Ascend 卡的静态映射，是否足以吸收剩余负载波动，减少 selector 对模型语义的干预？
9. selector 的逐 token CPU scan 在多大 $B$、$L$ 和 $P$ 下开始成为关键路径？

## 14. 主要参考

- 本地背景报告：[[human-cortex-and-whole-brain-signal-propagation-survey]]
- StableMoE: [Stable Routing Strategy for Mixture of Experts](https://arxiv.org/abs/2204.08396)
- EvoMoE: [An Evolutional Mixture-of-Experts Training Framework via Dense-To-Sparse Gate](https://arxiv.org/abs/2112.14397)
- ST-MoE: [Designing Stable and Transferable Sparse Expert Models](https://arxiv.org/abs/2202.08906)
- DeepSeekMoE: [Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models](https://arxiv.org/abs/2401.06066)
- DeepSeek-V3: [Technical Report](https://arxiv.org/abs/2412.19437)
- Loss-Free Balancing: [Auxiliary-Loss-Free Load Balancing Strategy for Mixture-of-Experts](https://arxiv.org/abs/2408.15664)
- OLMoE: [Open Mixture-of-Experts Language Models](https://arxiv.org/abs/2409.02060)
- Qwen3: [Technical Report](https://arxiv.org/abs/2505.09388)
- Kimi K2: [Open Agentic Intelligence](https://arxiv.org/abs/2507.20534)
- GLM-4.5: [Agentic, Reasoning, and Coding Foundation Models](https://arxiv.org/abs/2508.06471)
- Graph of Tokens: [Improving Routing in Sparse Mixture of Experts with Graph of Tokens](https://arxiv.org/abs/2505.00792)
- STAR: [Rethinking MoE Routing as Structure-Aware Subspace Learning](https://arxiv.org/abs/2606.08814)
- MCF-MoE: [Multi-level Context Modeling for Consistent Expert Selection in Mixture-of-Experts](https://arxiv.org/abs/2607.16427)
- Less is MoE: [Trimming Experts in Domain-Specialist Language Models](https://arxiv.org/abs/2606.05538)
