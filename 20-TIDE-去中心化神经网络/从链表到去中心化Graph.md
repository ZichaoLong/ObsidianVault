# 从链表、星型到去中心化 Graph 神经网络

迁移整理：2026-06-04

> 这是 TIDE 线的早期架构动机材料，保留原始论证脉络；当前执行计划见 [[当前计划与Defense]]。

为了解决原始 Transformer 每个 Token 计算都要加载全量参数的问题，人们发明了 MoE（Mixture of Experts），并以 DeepSeek-V3 为标志，证明了极致稀疏（<5%）下取得优良模型性能的可行性。

但这不是模型架构的终点。当前稀疏模型，如 MoE，仍存在一个根本悖论：计算是稀疏的，但通信模式依然是中心化的。

具体来说：

- Transformer 的通信模式是链表：attention -> ffn -> attention -> ffn。
- MoE 的通信模式是星型：attention -> [MoE] -> attention -> [MoE]。
- Transformer 没有任何稀疏性。
- MoE 具有稀疏性，但 `all -> one -> all -> one` 通信模式会限制其更低的物理性能极限。

![[attachments/llm-notes/从链表-Transformer-、星型-MoE-到去中心化Graph神经网络-01.png]]

![[attachments/llm-notes/从链表-Transformer-、星型-MoE-到去中心化Graph神经网络-02.png]]

自然想法是把拓扑变成去中心化 Graph，从而消除 All-to-One 通信瓶颈，接近榨干物理极限。

## 要点一：节点激活也要去中心化

如果激活选择依赖复杂模块输入输出状态，节点激活也要去中心化。

基于控制反馈线的 `Token[Instruction]=Opcode+Operands` 直觉，Graph 神经网络仍需保持 token 进 token 出的输入输出工作方式，并具有先后时序关系。

后续可以设置多个输入节点与多个输出节点；当前主流 LLM 则是单输入、单输出。

## 要点二：Graph 需要输入到输出的固定路由路径

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

## 原始吞吐记录

这部分是早期实验记录，保留为历史参考。

| ms/per token/step | | | | 56Core CPU | | | | 7*T4 GPU 15GB / [8.5B 8*V100 32GB] | | | |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Size | Node | Dim | Batch | 1 | 16 | 256 | 512 | 1 | 16 | 256 | 512 |
| 1B | 7168/64 | 128 | Grad | 140 | 50 | 27 | 24 | 350 | 156 | 60 | 48 |
| | | | NoGrad | 130 | 34 | 5 | 2.5 | 320 | 120 | 17 | 9 |
| 8.5B | 57344/64 | 128 | Grad | 1350 | 543 | 234 | 136 | 3600 | 1200 | 273 | |
| | | | NoGrad | 1000 | 375 | 54 | 29 | 3600 | 906 | 109 | 57 |

| ms/per token/step | | | | 56Core CPU | | | | 7*T4 GPU 15GB | | | |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Size | Node | Dim | Batch | 1 | 16 | | 512 | 16 | | 512 | 2048 |
| 0.58B | 224/32 | 512 | Grad | 15 | 2.5 | | 0.57 | 6.9 | | 1.4 | 1 |
| | | | NoGrad | 15 | | | 0.3 | | | 0.65 | 0.35 |
| 2.2B | 224/32 | 1024 | Grad | 25 | 5.6 | | 1.17 | 8.8 | | 1.8 | 1.2 |
| | | | NoGrad | 25 | | | 0.88 | | | 0.88 | 0.56 |
| 8.8B | 224/32 | 2048 | Grad | 85 | | | 3.6 | 9.1 | | 2.8 | |
| | | | NoGrad | 85 | | | 3.3 | | | 1.46 | 0.95 |

| ms/per token/step | | | | 56Core CPU | | | | 7*T4 GPU 15GB | | | |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B | | | Batch | 1 | 16 | | 512 | 1 | 16 | | 512 |
| 44input+56output | | | NoGrad | 210 | 56 | | 29 | 46 | 21 | | 6.4 |
| 34input+66output | | | NoGrad | | | | | 51 | 24 | | 6.7 |

## 要点三：时间锚点与序列并行

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

## 覆盖来源

- `/home/zlong/llm/llm-notes/content/scratch/从链表(Transformer)、星型(MoE)到去中心化Graph神经网络.md`

