---
type: index
status: active
tags:
  - tide
  - decentralized-nn
---

# TIDE / 去中心化神经网络

> [!summary] 本页定位
> 本页集中保存 TIDE 线的 [[#TIDE：当前计划与 Defense|目标、计划与防守边界]]，以及 [[#从链表、星型到去中心化 Graph 神经网络|架构动机]]。当前工程架构状态见 [[current-architecture-state]]。

## 一页版结论

- TIDE 的核心目标是构建前向隐藏态只做有界度局部通信的自回归神经动力系统。
- 稀疏性和局部通信是两个不同维度，不能在第一步同时硬化，否则失败原因不可诊断。
- 当前工程顺序应是 `dense local updates -> block sparse active subgraph -> hard routing -> async updates`。
- 内外时钟、节点接口、序列并行、batch 并行和节点并行必须作为架构一等公民。
- 当前 `~/llm/tide` 已收敛到一版 LH role-aware phase runtime 骨架，具体状态见 [[current-architecture-state]]。
- PyTorch 适合先验证可训练性与接口形状；LibTorch / 自定义算子更适合作为后续性能实现路径。

## 最小可验证 Demo

第一版 demo 不应追求完整去中心化系统，而应验证：

| 目标 | 最小要求 |
| --- | --- |
| 可训练 | loss 能稳定下降，并能在小数据上生成正常 token。 |
| 局部通信 | 节点只访问有界邻居消息，不依赖全局 attention 汇聚。 |
| 序列并行 | prefill / training 阶段节点内部能处理 token 序列，而不是退化成 RNN。 |
| 时钟语义 | 明确 external step 与 internal tick，能描述 DAG 与有环图差异。 |
| 可扩展接口 | 后续能引入节点稀疏、batch 稀疏、sequence/memory 稀疏。 |

## 读者路径

| 读者目标 | 建议阅读 |
| --- | --- |
| 快速理解目标 | [[#TIDE / 去中心化神经网络：概览]] |
| 理解当前工程架构 | [[current-architecture-state]] |
| 理解 prefill / decode 等价性的数学定义 | [[step-transition-mathematical-specification]] |
| 理解 StepTransition 的实现约束 | [[step-transition-implementation-specification]] |
| 判断下一步怎么做 | [[#TIDE：当前计划与 Defense]] |
| 理解架构动机 | [[#从链表、星型到去中心化 Graph 神经网络]] |

---

## TIDE / 去中心化神经网络：概览

TIDE 是 `Token Inference Decentralized Engine`。当前目标表述：

> 构建一种前向隐藏态只做有界度局部通信的自回归神经动力系统，并逐步证明它能稳定训练、可分区执行、支持稀疏化。

### 主题地图

- 目标与约束。
- 内外时钟。
- 节点接口。
- 局部通信与稀疏化。
- DAG / 有环图训练与推理。
- StepTransition 数学规范与 prefill / decode 等价性：[[step-transition-mathematical-specification]]。
- StepTransition 实现规范与 LH-like runtime 约束：[[step-transition-implementation-specification]]。
- PyTorch / LibTorch / 自定义算子路线。
- TIDE Challenge / Defense。
- 当前 C++/LibTorch 架构状态：[[current-architecture-state]]。

---

## TIDE：当前计划与 Defense

### 目标

构建一种前向隐藏态只做有界度局部通信的自回归神经动力系统，并逐步证明它能：

- 稳定训练。
- 可分区执行。
- 支持稀疏化。

> [!summary] 执行判断
> 先做可训练、可验证的 `dense local updates`，再抽出图语义与 memory 语义，最后逐步引入稀疏、路由和异步执行。

### 推进顺序

1. `dense local updates`
2. `block sparse active subgraph`
3. batch 维度 `selective activity`
4. sequence / memory 维度 `selective activity`
5. `soft routing`
6. `hard routing`
7. 异步与去中心化执行

关键点是：真正的稀疏化要后置。否则无法判断失败来自架构本身，还是来自离散路由不可训。

### 关键约束

- 训练和推理都要支持。
- 有环图和无环图都要支持。
- 稀疏性必须是独立策略层。
- 内外时钟必须是一等公民。

### 里程碑

- 先跑通 dense 版本。
- 再抽出图语义和 memory 语义。
- 再引入稀疏和路由。
- 最后再谈更强的去中心化执行。

### Defense

TIDE 不只是 runtime 工程。它试图把这些东西统一成可验证的模型接口：

- 局部通信。
- 内外时钟。
- 稀疏性。
- 图结构。

当前工程工作确实很重，但这不等于研究命题无效；它说明命题需要更强的阶段性切片。

有环图和无环图必须分开验证，否则会把训练稳定性、通信结构和执行语义混在一起。

### 当前最需要补的东西

- 一个最小架构命题。
- 一个能强行区分 Transformer / Mamba / 图执行路线的任务。
- 一个明确的稀疏化推进顺序。

### 当前工程下一步

1. 先实现 PyTorch 原型，验证节点接口、内外时钟、dense local updates 与训练闭环。
2. 再把 graph runtime 与 node module 解耦，保证后续能替换为稀疏执行或 C++/LibTorch 实现。
3. 再加入节点激活日志、message trace 和 memory trace，确保失败可诊断。
4. 最后再推进节点稀疏、路由、异步更新和性能实现。

### 目前防御立场

- 先承认：工程复杂度会吞没研究注意力。
- 再坚持：架构接口必须先设计好，否则后续稀疏与分区都无法落地。
- 最后聚焦：先做可验证的 dense local updates，再逐步引入稀疏与路由。

## 从链表、星型到去中心化 Graph 神经网络

> [!summary] 核心动机
> MoE 让计算变稀疏，但通信仍是中心化的 `all -> one -> all -> one`。TIDE 想探索有界度局部通信的 Graph 神经网络，以突破中心化通信瓶颈。

为了解决原始 Transformer 每个 Token 计算都要加载全量参数的问题，人们发明了 MoE（Mixture of Experts），并以 DeepSeek-V3 为标志，证明了极致稀疏（<5%）下取得优良模型性能的可行性。

但这不是模型架构的终点。当前稀疏模型，如 MoE，仍存在一个根本悖论：计算是稀疏的，但通信模式依然是中心化的。

具体来说：

- Transformer 的通信模式是链表：attention -> ffn -> attention -> ffn。
- MoE 的通信模式是星型：attention -> [MoE] -> attention -> [MoE]。
- Transformer 没有任何稀疏性。
- MoE 具有稀疏性，但 `all -> one -> all -> one` 通信模式会限制其更低的物理性能极限。

![[assets/images/linked-list-transformer-star-moe-decentralized-graph-nn-01.png|48%]] ![[assets/images/linked-list-transformer-star-moe-decentralized-graph-nn-02.png|48%]]

自然想法是把拓扑变成去中心化 Graph，从而消除 All-to-One 通信瓶颈，接近榨干物理极限。

### 要点一：节点激活也要去中心化

如果激活选择依赖复杂模块输入输出状态，节点激活也要去中心化。

基于控制反馈线的 `Token[Instruction]=Opcode+Operands` 直觉，Graph 神经网络仍需保持 token 进 token 出的输入输出工作方式，并具有先后时序关系。

后续可以设置多个输入节点与多个输出节点；当前主流 LLM 则是单输入、单输出。

### 要点二：Graph 需要输入到输出的固定路由路径

Graph 的设计约束应包含一条从输入到输出的固定路由路径，其他路径是支线。

满足这两个要点后，就可以设计 Graph 神经网络，使 token 一个接一个输入网络，一个接一个输出。

通过 LibTorch C++、gather、scatter 等实现，可以支持：

- 空间并行：不同节点并行执行。
- batch 并行：同一节点内处理 batch。
- 自动构图与梯度反传：借助 LibTorch。

原始伪代码：

```python
for token in input_tokens:
    input_signal = embed(token)
    for i in range(route_len_from_input_node_to_output_node):
        for node in graph: # C++ 中用 openmp 并行执行
            emit(node_signal)
        for node in graph: # C++ 中用 openmp 并行执行
            receive(node_signal)
    output_token = output(output_node)
```

### 附录：原始吞吐记录

这部分是早期实验记录，保留为历史参考。

| ms/per token/step |          |     |        | 56Core CPU |     |     |     | 7*T4 GPU 15GB / [8.5B 8*V100 32GB] |      |     |     |
| ----------------- | -------- | --- | ------ | ---------- | --- | --- | --- | ---------------------------------- | ---- | --- | --- |
| Size              | Node     | Dim | Batch  | 1          | 16  | 256 | 512 | 1                                  | 16   | 256 | 512 |
| 1B                | 7168/64  | 128 | Grad   | 140        | 50  | 27  | 24  | 350                                | 156  | 60  | 48  |
|                   |          |     | NoGrad | 130        | 34  | 5   | 2.5 | 320                                | 120  | 17  | 9   |
| 8.5B              | 57344/64 | 128 | Grad   | 1350       | 543 | 234 | 136 | 3600                               | 1200 | 273 |     |
|                   |          |     | NoGrad | 1000       | 375 | 54  | 29  | 3600                               | 906  | 109 | 57  |

| ms/per token/step |        |      |        | 56Core CPU |     |   |      | 7*T4 GPU 15GB |   |      |      |
| ----------------- | ------ | ---- | ------ | ---------- | --- | - | ---- | -------------- | - | ---- | ---- |
| Size              | Node   | Dim  | Batch  | 1          | 16  |   | 512  | 16             |   | 512  | 2048 |
| 0.58B             | 224/32 | 512  | Grad   | 15         | 2.5 |   | 0.57 | 6.9            |   | 1.4  | 1    |
|                   |        |      | NoGrad | 15         |     |   | 0.3  |                |   | 0.65 | 0.35 |
| 2.2B              | 224/32 | 1024 | Grad   | 25         | 5.6 |   | 1.17 | 8.8            |   | 1.8  | 1.2  |
|                   |        |      | NoGrad | 25         |     |   | 0.88 |                |   | 0.88 | 0.56 |
| 8.8B              | 224/32 | 2048 | Grad   | 85         |     |   | 3.6  | 9.1            |   | 2.8  |      |
|                   |        |      | NoGrad | 85         |     |   | 3.3  |                |   | 1.46 | 0.95 |

| ms/per token/step |                   |   |        | 56Core CPU |     |   |     | 7*T4 GPU 15GB |    |   |     |
| ----------------- | ----------------- | - | ------ | ---------- | --- | - | --- | -------------- | -- | - | --- |
| Qwen 7B           |                   |   | Batch  | 1          | 16  |   | 512 | 1              | 16 |   | 512 |
| 44input+56output  |                   |   | NoGrad | 210        | 56  |   | 29  | 46             | 21 |   | 6.4 |
| 34input+66output  |                   |   | NoGrad |            |     |   |     | 51             | 24 |   | 6.7 |

### 要点三：时间锚点与序列并行

早期吞吐结果没有实现序列并行，这对训练不友好。

问题暴露在两层循环：

```python
for token in input_tokens:
    for i in range(route_len_from_input_node_to_output_node):
```

要实现序列并行，关键是加入时间戳：

```text
t = token_id * route_len_from_input_node_to_output_node + i
```

每个节点（attention + ffn 块）处理信息时，应感知接收到的 graph 上游节点信号的时间戳。对 FFN 这较好处理；对 attention 或 linear attention 则要尤为小心。
