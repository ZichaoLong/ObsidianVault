# Tide 教学图集

先用结构图认识节点、区域与消息流，再用 P/S/U/F 简图解释一次区域作用。接着用带权消息图和两个算例讲清局部计算，按需要展开具体记忆与发送规则。

[首次展示脚本](../presentations/design-introduction-script.md)以 HB 三层图的两次输入贯穿主线，并说明这些素材的接入位置。该脚本统一使用 HB 实例的参数；本图集中区域分配和两次接收图各有自己的数值条件。

## 整体结构与一次区域作用

| 图片 | 用途 | 数学定义 |
|---|---|---|
| [节点、区域与消息流](tide-structure.png) | DAG 的发散、汇合、跨区连接与节点局部流程 | [TimedDAG §2—6](../timed-dag-region-selector-learning-note.md#2-固定结构时间节点图端口与区域划分) |
| [P/S/U/F 简图](PSUF-simple.png) | 共同选择、候选状态保留与激活后的发送 | [TimedDAG §5](../timed-dag-region-selector-learning-note.md#5-区域候选集合选择函数选择历史与状态采用) |
| [P/S/U/F 详图](PSUF-complete.png) | 计算快照、下一状态、控制与完整输出 | [共同接口索引](../reference/semantic-interface-index.md#局部函数) |

图中的节点名称只用于对应示例。结构图与 P/S/U/F 图表达正典的一般语义；某个局部架构的附加约束由相应教材定义。

## 带权消息与两个算例

这组图采用[带权消息局部架构](../local-semantics/weighted-message/architecture-learning-note.md)。蓝色表示当前内容与传播，绿色表示记忆，金色表示区域描述与控制。

### 一次接收到发送

先由 Agg 形成接收，再执行 Upd。图中采用 Read$^+$，描述读取新状态；全部候选保留接收更新。区域给出正控制后，Full 计算完整内容，并在每条出边复制同一带权载荷。

[PNG](weighted-message-flow.png) · [可编辑 SVG](weighted-message-flow.svg) · [定义：共同架构 §2—4](../local-semantics/weighted-message/architecture-learning-note.md#2-接收聚合)

![带权消息的一次处理](weighted-message-flow.png)

### 区域怎样分配发送强度

沿用教材的三个候选：接收权重与发送上限均为 $(1,1,0)$，评分为 $(2,1,100)$。区域头给出总量 $B=1.4$，二次分配在温度 $2$ 得到 $(0.95,0.45,0)$。总强度为 $1.4$，激活节点数为 $2$。

[PNG](region-allocation.png) · [可编辑 SVG](region-allocation.svg) · [定义与数值：区域分配 §2.5](../local-semantics/weighted-message/region-allocation-learning-note.md#25-三个候选的一次计算)

![区域怎样分配发送强度](region-allocation.png)

### 收到时记住，激活时发送

沿用 KV 教材的两次接收例子。Read$^+$ 和 sum 描述给出长期摘要；硬选择每次激活最高正分节点。节点 $b$ 第一次未激活，仍保留 $+1$；第二次收到 $-1$ 后，两条记忆共同影响它的评分与完整内容。

[PNG](remember-before-send.png) · [可编辑 SVG](remember-before-send.svg) · [定义、参数与数值：KV §5.2](../local-semantics/weighted-message/kv-memory-learning-note.md#52-未激活时保留的记忆)

![收到时记住，激活时发送](remember-before-send.png)

## 记忆模块

四张图按 Upd、Mem、G 的顺序展开。图中描述均采用 Read$^+$；其他快照模式由共同架构定义。循环记忆图展示 state 描述，sum 候选从独立摘要取得描述。图中的 $N_d$ 对应教材的归一化函数 $\mathcal N_d$。

| 图 | 主要问题 | 定义出处 |
|---|---|---|
| KV：[PNG](kv-memory.png)／[SVG](kv-memory.svg) | 带时间的条目怎样保存，怎样用于描述与完整 Attention 读取 | [KV §1](../local-semantics/weighted-message/kv-memory-learning-note.md#1-状态与接收写入)、[§3—4](../local-semantics/weighted-message/kv-memory-learning-note.md#3-记忆描述) |
| 仿射与 Delta：[PNG](affine-delta-memory.png)／[SVG](affine-delta-memory.svg) | 外积叠加与预测误差修正怎样填入同一更新接口 | [基础循环 §1—3](../local-semantics/weighted-message/recurrent-memory/affine-delta-learning-note.md#1-状态与逻辑时间) |
| Gated DeltaNet：[PNG](gated-delta-memory.png)／[SVG](gated-delta-memory.svg) | 短卷积与门怎样形成误差写入；每头 RMS 后怎样调制输出 | [Gated DeltaNet §2](../local-semantics/weighted-message/recurrent-memory/gated-delta-learning-note.md#2-投影与接收更新)、[§3](../local-semantics/weighted-message/recurrent-memory/gated-delta-learning-note.md#3-矩阵读取记忆描述与完整内容) |
| SSD：[PNG](ssd-memory.png)／[SVG](ssd-memory.svg) | 输入步长怎样控制保留与写入；直通项、输出门与全宽 RMS 怎样组合 | [SSD §2](../local-semantics/weighted-message/recurrent-memory/ssd-learning-note.md#2-投影门与写入)、[§3](../local-semantics/weighted-message/recurrent-memory/ssd-learning-note.md#3-矩阵读取记忆描述与完整内容) |

基础循环保存 short、long 两种时间尺度的矩阵；Gated DeltaNet 与 SSD 保存多头矩阵，state 描述的 short 通道使用时间摘要，long 通道使用矩阵查询。各模块的接收门参与记忆更新，区域控制 $c_v$ 决定后续发送。

## 发送规则与逻辑时间

| 图 | 主要问题 | 定义出处与图中条件 |
|---|---|---|
| 发送规则：[PNG](sending-rules.png)／[SVG](sending-rules.svg) | 区域总量、共同阈值、节点上限与 Attention 份额分别起什么作用 | [区域分配 §4.1—4.2](../local-semantics/weighted-message/region-allocation-learning-note.md#41-约束分配)；图中比较六种发送规则，其他候选见教材 |
| 温度与激活数量：[PNG](temperature-support.png)／[SVG](temperature-support.svg) | 同样的总强度怎样对应不同数量的激活节点 | [区域分配 §5.5](../local-semantics/weighted-message/region-allocation-learning-note.md#55-分配与饱和)；节点增益与固定阈值分配，quad，单位上限，$t=(4,3,2,1)$，$k=2$ |
| 固定逻辑时间槽：[PNG](logical-time-slots.png)／[SVG](logical-time-slots.svg) | 缺失接收与弱接收怎样进入短卷积，其他历史怎样保持原坐标 | [短卷积 §1](../local-semantics/weighted-message/recurrent-memory/causal-convolution-learning-note.md#1-缓存卷积与写入)、[§2.2—3](../local-semantics/weighted-message/recurrent-memory/causal-convolution-learning-note.md#22-与通常短卷积的对应)；标量、间距 $2$、三抽头系数 $(1,2,3)$、零偏置 |

Attention 的最终控制按各自公式形成：直接 Attention 满足 $c_v\le\mu_v$；固定总强度和总量缩放 Attention 允许单个分量超过 $\mu_v$。温度图使用指定的 quad 算例，三次总和均为 $2$，激活数量依次为 $4,3,2$。

## 生成与修改

使用 Python 3.10 或更高版本，安装 [Python 依赖](requirements.txt)、Cairo、Noto Sans CJK 和 DejaVu Sans 字体。默认字体路径记录在 [drawing.py](src/drawing.py) 中。在仓库根目录运行：

```bash
python3 -m pip install -r 20-tide-decentralized-neural-network/figures/requirements.txt
python3 20-tide-decentralized-neural-network/figures/render.py
```

也可以只生成一组或一张：

```bash
python3 20-tide-decentralized-neural-network/figures/render.py --group legacy
python3 20-tide-decentralized-neural-network/figures/render.py --group local
python3 20-tide-decentralized-neural-network/figures/render.py --only kv-memory
```

`--output-dir` 可将结果写到其他目录。局部语义图同时导出 2400 × 1350 的 PNG 和可编辑 SVG；SVG 保留文字、形状与定义引用。编辑 SVG 可直接制作演示变体；持续修改宜同步到生成脚本，重新运行会覆盖同名输出。

| 源码 | 维护内容 |
|---|---|
| [src/legacy/](src/legacy/) | 结构图与 P/S/U/F 两图的独立 Pillow 脚本 |
| [local_figures.py](src/local_figures.py) | 带权消息流程与两个算例 |
| [memory_figures.py](src/memory_figures.py) | KV、仿射／Delta、Gated DeltaNet、SSD |
| [control_time_figures.py](src/control_time_figures.py) | 发送规则、温度和固定时间槽 |
| [drawing.py](src/drawing.py) | 配色、字体、SVG 文字、形状与 PNG 导出 |
| [catalog.py](src/catalog.py) | 图名注册与定义路径；具体出处及条件与各绘图函数相邻保存 |

完整重绘后，可加 `--record-provenance` 更新[局部图校验记录](local-provenance.json)，包含每张图的定义章节、条件、教材与源码哈希、字体、渲染版本及输出哈希。来源和复现核验记录见 [PROVENANCE.md](PROVENANCE.md)。
