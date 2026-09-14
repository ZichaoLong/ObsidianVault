---
type: training-research-memo
status: hypotheses-and-diagnostics
semantic-baseline: tide-core-3
---

# 学习风险与诊断：稀疏路径究竟增加了什么困难

本页保留旧架构长文第三部分与第四部分 §8 中的学习问题。它不是训练配方，不证明任何特定模型一定收敛。原文与更细讨论可追溯 Git `133d638`。

## 1. 四个问题应分开

| 问题 | 来源 | 不能混同的结论 |
| --- | --- | --- |
| Hard choice 不连续 | Top-K 成员在分数边界变化 | 不代表每次变化都造成大输出误差 |
| Selected-only feedback | 未选分支的 Full 没有被执行，缺少该读出的直接反事实任务反馈 | 不等于未选分支没有状态更新或任何梯度 |
| 路径分布漂移 | 参数/历史变化使同类输入进入不同下游分布 | 静态稀疏或固定路由也可以没有这种漂移 |
| 长程信用分配 | 影响经过深层、控制链或长期状态才进入 loss | 不只发生于稀疏模型 |

同一序列在不同训练 checkpoint 换路，是参数漂移；固定参数下因历史不同而换路，可以是模型意图；因 batch 同伴或设备负载不同而换路，则改变了参考语义，应先修正实现。

## 2. 路由变化的频率、幅度和持续时间

固定输入、边界状态和分支参数，令有限候选集合中第 $i$ 个分支的向量贡献为 $v_i$，active set 为 $A$，merge 为 $M$。若

$$
\|M(z)-M(z')\|\le L_M\sum_i\|z_i-z_i'\|,
$$

把全部分支槽值组成 $z_A=(\mathbf1[i\in A]v_i)_i$，那么

$$
\|M(z_A)-M(z_{A'})\|
\le L_M\sum_{i\in A\triangle A'}\|v_i\|.
\tag{1}
$$

**推导。** 两个 active set 的共同节点和共同未选节点贡献差为零，只剩对称差中的项；代入 Lipschitz 条件即可。

因此 active-set overlap、小 residual 和稳定 merge 可以限制固定输入上的换路扰动。式中 $A\triangle A'$ 是恰好属于一个集合的节点组成的对称差。若换路还使共同选中节点的归一化权重或状态改变，就要把这些槽的变化一起计入，不能只保留对称差项。只增加候选数量，不会自动缩小一次 Top-1 切换的影响。式 (1) 不证明训练中路由会少换，也不控制同时改变参数后的完整 checkpoint 漂移。

可分别记录切换频率 $C$、跳变量 $J$ 和控制身份持续时间 $H$。旧稿提出的 $C\cdot J\cdot H$ 只是一种需要归一化并实验检验的风险代理，不是风险定律。

## 3. 信用分配中的三种距离

| 距离 | 含义 |
| --- | --- |
| 数值依赖距离 | 中间表示到 loss 的前向依赖链长度 |
| 控制寿命 | 一次选择在固定 merge 前持续限制可达分支多久 |
| 状态读写延迟 | 某次输入写入私有状态，到未来读出它相隔多久 |

标准 block-local MoE 在本子层出口结束显式分支身份，但贡献仍能影响后续层、KV 与未来 token。具有私有 receiver state 的图额外引入“本次写入、很久以后才读”的信用链。

在一条可微标量链 $z_{i+1}=f_i(z_i)$ 上，梯度含 $\prod_i f_i'(z_i)$；一般向量图则有 Jacobian 乘积与分支求和。存在短残差路径，不保证它的数值梯度足够大。Hard Top-K 的成员映射在分数边界之外局部不变，边界处通常不连续；普通导数不能直接提供“换成另一个成员会怎样”的反馈。截断 BPTT 可能直接切断较早状态写入的任务反馈。

在默认 Next 保存本次计算状态时，BO 让未选候选也保留输入更新，扩大状态写入覆盖；自定义 Next 还可能清理或改写它。BO 不改变该步是否收到输入，也不能自动保证这些写入未来被使用，或在反向截断以前获得梯度。

## 4. 饥饿与数值稳定性

激活次数均衡至少不能替代另外三项：有效梯度覆盖、稳定的任务相关输入覆盖、优化器状态的新鲜度。把拥有不同私有状态的节点强行轮换，可能改善次数统计而破坏内容适配。

Attention logit、SSM 状态谱/范数、低精度溢出、优化器和梯度尺度也能独立导致 loss spike。route churn 与 spike 同时发生只说明相关，不能直接归因。

## 5. 可选训练干预及其代价

| 干预 | 想改善什么 | 应保留的对照或代价 |
| --- | --- | --- |
| Soft/dense 到 hard sparse | 早期候选反馈覆盖 | 更多训练计算；不规定所有实验都必须退火 |
| 小 router 学习率、EMA、蒸馏或冻结 | checkpoint 换路 | 探索减少，可能固化错误划分 |
| Margin/hysteresis | 边界抖动 | 跨时间 hysteresis 是模型状态，须进入 continuation |
| 少量 shadow branch | 未选路径反事实 | 额外计算与 estimator 偏差 |
| 中间辅助读出或 teacher representation loss | 缩短监督距离 | 过强时迫使各层学相同表示 |
| 共享主体、小 adapter、局部平滑 | 降低切换幅度 | 可能压制专门化，应做无平滑对照 |

训练数据 replay、旧 route/hidden/logits 的一致性约束可以不改变推理函数。推理时主动重演内部轨迹则增加模型依赖，不能用同一个 replay 名称掩盖。

一个可选训练目标是

$$
\mathcal L=\mathcal L_{\mathrm{final}}
+\sum_r\alpha_r\|P_rh_r-\mathrm{stopgrad}(h_r^{\mathrm{teacher}})\|^2
+\sum_r\beta_r\mathcal L_{\mathrm{aux},r}.
$$

这里 $r$ 索引已声明的辅助观测位置，$P_r$ 把中间表示 $h_r$ 投影到教师表示的空间；$\alpha_r,\beta_r\ge0$ 是损失权重，$\mathrm{stopgrad}$ 表示不沿教师目标反传。中间投影与辅助头可以只在训练时存在；主 loss 仍端到端反传。辅助监督不自动为未选 hard 索引提供反事实梯度。具体权重、衰减及 shadow 路径是否进入某个训练目标，须由实验契约声明。

## 6. 最小诊断账本

1. **语义**：同一输入/边界下 chunk、decode、不同 batch 的输出、状态、选择及消息是否一致。
2. **机制使用**：Receive/Update/Read/Emit 覆盖；写到读的延迟；freeze、clear、shuffle、no-read 对照。
3. **选择**：Top-K overlap、route churn、边界 margin、负载偏斜与死节点。
4. **梯度**：Upd、Next、selector 与 Full 的有效梯度覆盖、范数和反向截断边界。
5. **数值**：attention logit、状态范数、NaN/Inf、裁剪与溢出。
6. **质量与成本**：相同数据暴露、FLOPs 或设备时间下的质量，训练与推理成本分别报告。

参数量、训练 token、FLOPs、墙钟和显存通常无法同时严格匹配，应给互补比较。机制 knockout 也可能改变分布；应说明对照是否重新训练、预算是否匹配，而不是把一次清零后的退化直接当作收益证明。

## 7. 外部研究如何使用

[StableMoE](https://arxiv.org/abs/2204.08396) 研究 checkpoint 间路由变化；[ST-MoE](https://arxiv.org/abs/2202.08906)、[OLMoE](https://arxiv.org/abs/2409.02060) 展示专门化及训练稳定性的具体条件；[DeepSeekMoE](https://arxiv.org/abs/2401.06066) 与 [loss-free balancing](https://arxiv.org/abs/2408.15664) 提供粒度和负载机制；[EvoMoE](https://arxiv.org/abs/2112.14397) 提供 dense-to-sparse 思路。

这些文献不是 Tide 长路径、私有状态或 BO 的验证结果。脑科学的稀疏与信用分配另见 [脑科学启发](../background/neuroscience-model-ideas.md)；这里不据此声称数字模型天然稳定。
