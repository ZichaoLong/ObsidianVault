---
type: technical-note
status: active
tags:
  - technical-notes
  - attention
  - model-architecture
  - recurrent-memory
cssclasses:
  - textbook-math
configurations_checked: 2026-09-29
updated: 2026-10-13
---

# 注意力与循环记忆：模型配置对照

配置核对日期：**2026-09-29**。本版于 2026-10-13 从完整调查中拆出并整理排版，日期指向各配置的核对时点。

机制、公式与受控实验见 [[30-technical-notes/attention-position-memory|局部性、位置机制与循环记忆]]。本页按模块记录架构选择；后续更新时，同时记录模型版本、来源与配置核对日期。

阅读顺序：[[#1. 按模块读表|读表约定]] → [[#2. 模型概览|模型概览]] → [[#3. 各模型配置与来源|配置明细]] → [[#4. 公开实现中的核对要点|实现要点]] → [[#5. 用于理解结构差异的较早实例|较早实例]]。

## 1. 按模块读表

**Kimi K3 使用循环记忆：其文本主干包含 69 层 KDA 和 24 层全局 MLA。KDA 通过门控状态更新与短卷积处理顺序；全局 MLA 采用 NoPE。其文本主干的这些序列模块不施加 RoPE，但仍有隐式顺序结构。**

不能用一个模型级的“RoPE／NoPE”标签代替模块组成。下面将循环记忆放在模型名后的第一列，并分别给出局部注意力、全局注意力的位置机制。读表约定如下：

- **循环记忆**指沿 token 时间轴更新固定大小状态的模块，例如 KDA、Gated DeltaNet、Mamba-2。此处不把普通 KV cache、注意力输出门控或跨网络深度的残差连接称为循环记忆。
- **局部注意力**指有局部窗口或局部块约束的注意力计算。“无独立局部注意力”不等于没有局部计算：短卷积仍可提供局部顺序结构，全局注意力也能读取邻近 token。
- **NoPE**描述对应主注意力的匹配方式：本层不额外施加显式位置旋转或位置偏置。其输入仍可能包含上游循环、卷积或其他层形成的位置表示。辅助索引器是否使用位置参数另行注明。
- **RoPE 百分比**是该注意力头中旋转的 Q/K 维数占总 Q/K 维数的比例，不是使用 RoPE 的层数比例；部分 RoPE 中未旋转的维度也不保证不含上游位置信息。
- **全局稀疏读取**允许候选来自长历史，但只读取选中的 token 或块；**压缩全局读取**访问汇聚后的历史记录。两者均须与读取全部历史记录的稠密 full attention 区分。

表中只统计文本主干，不统计视觉编码器和额外多 token 预测（MTP）支路。历史存储指推理中请求相关的缓存，不含模型权重与临时工作区；具体缓存布局还依赖推理实现。

## 2. 模型概览

以下配置核对至 **2026-09-29**，记录架构选择，不作能力排名。“有／无”只修饰所在列的模块；局部与全局机制若在同层组合，不应将两列层数相加。

GDN 指 Gated DeltaNet；旋转百分比指对应 Q/K 的旋转维度比例。概览中的“全局”描述候选范围，DSA、QSA、CSA、MSA 等是否稀疏或压缩，详见各模型明细。循环模块的短卷积、窗口大小、缓存布局和来源同样保留在明细中。

| 模型 | 循环记忆 | 局部注意力 | 全局注意力 | 历史存储 |
|---|---|---|---|---|
| [[#3.1 Kimi K3\|Kimi K3]] | 69 KDA | 无独立层 | 24 MLA；NoPE | 状态＋全局记录 |
| [[#3.2 GLM-5.3-Flash\|GLM-5.3-Flash]] | 34 KDA | 无独立层 | 11 DSA；主注意力 NoPE | 状态＋全局记录 |
| [[#3.3 Nemotron 3 Ultra\|Nemotron 3 Ultra]] | 48 Mamba-2 | 无独立层 | 12 全局；NoPE | 状态＋全局 KV |
| [[#3.4 Qwen3.8-2.4T-A95B\|Qwen3.8-2.4T-A95B]] | 69 GDN | 无独立层 | 23 全局；25% RoPE | 状态＋全局 KV |
| [[#3.5 Qwen3.8-Flash-Next\|Qwen3.8-Flash-Next]] | 36 GDN | 无独立层 | 12 QSA；25% RoPE | 状态＋全局记录 |
| [[#3.6 Gemma 4 31B\|Gemma 4 31B]] | 无 | 50 滑窗；RoPE | 10 全局；25% RoPE | 局部＋全局记录 |
| [[#3.7 Step-3.7-Flash\|Step-3.7-Flash]] | 无 | 33 滑窗；100% RoPE | 12 全局；50% RoPE | 局部＋全局 KV |
| [[#3.8 DeepSeek-V4-Pro-0813\|DeepSeek-V4-Pro-0813]] | 无 | 局部分支；12.5% RoPE | CSA/HCA；12.5% RoPE | 局部＋压缩记录 |
| [[#3.9 DeepSeek-V4.1-Flash\|DeepSeek-V4.1-Flash]] | 无 | 40 层局部；12.5% RoPE | 38 层 CSA2；12.5% RoPE | 局部＋共享全局记录 |
| [[#3.10 MiniMax M3\|MiniMax M3]] | 无 | 57 层含局部块；50% RoPE | 3 稠密＋57 MSA；50% RoPE | 全局 KV＋索引 |
| [[#3.11 GLM-5.3\|GLM-5.3]] | 无 | 无独立层 | 78 MLA/DSA；25% RoPE | 全局潜在 KV |
| [[#3.12 Mistral Medium 3.5 128B\|Mistral Medium 3.5 128B]] | 无 | 无独立层 | 88 全局；RoPE＋YaRN | 全局 KV |

因此，Kimi K3 这一行应读作：**有循环记忆＋没有独立局部注意力层＋有全局 NoPE 注意力**。其中“没有独立局部注意力”与“不施加 RoPE”，都不能推出“没有顺序机制”。它也不是只有循环状态的模型：24 层全局 MLA 仍保留随上下文增长的历史记录。

## 3. 各模型配置与来源

### 3.1 Kimi K3

配置来源：[Kimi K3](https://huggingface.co/moonshotai/Kimi-K3/blob/main/config.json)。

- **循环记忆**：**有：69 层 KDA**；门控状态更新＋核宽 4 的短卷积；KDA 不施加 RoPE。
- **局部注意力**：**无独立局部注意力层**；KDA 的短卷积属于另一种局部计算。
- **全局注意力**：**有：24 层全局 MLA；NoPE**，读取逐 token 历史记录。
- **历史存储**：KDA 固定状态＋卷积缓存；MLA 保留全局逐 token 记录，可用潜在 KV 压缩。

### 3.2 GLM-5.3-Flash

配置来源：[GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash/blob/main/config.json)。

- **循环记忆**：**有：34 层 KDA**；门控状态更新＋核宽 4 的短卷积；KDA 不施加 RoPE。
- **局部注意力**：**无独立局部注意力层**；有 KDA 短卷积与索引池的局部分组。
- **全局注意力**：**有：11 层 DSA 全局稀疏注意力；主 Q/K 为 NoPE**；索引池另有池内位置参数，见下文。
- **历史存储**：KDA 固定状态＋卷积缓存；全局潜在 KV 记录＋索引缓存。

### 3.3 Nemotron 3 Ultra

配置来源：[Nemotron 3 Ultra](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16/blob/main/config.json)。

- **循环记忆**：**有：48 个 Mamba-2 模块**；选择性状态更新＋核宽 4 的卷积；不施加 RoPE。
- **局部注意力**：**无独立局部注意力层**；Mamba-2 中有局部卷积。
- **全局注意力**：**有：12 个全局注意力模块；NoPE**。
- **历史存储**：Mamba-2 固定状态＋卷积缓存；全局 KV。

### 3.4 Qwen3.8-2.4T-A95B

配置来源：[Qwen3.8-2.4T-A95B](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B)。

- **循环记忆**：**有：69 层 Gated DeltaNet**；门控 Delta 更新＋核宽 4 的短卷积；循环模块不施加 RoPE。
- **局部注意力**：**无独立局部注意力层**；循环模块中有短卷积。
- **全局注意力**：**有：23 层全局 gated attention；25% RoPE**，旋转 64/256 维。
- **历史存储**：循环固定状态＋卷积缓存；全局 KV。

### 3.5 Qwen3.8-Flash-Next

配置来源：[Qwen3.8-Flash-Next，架构预览](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)。

- **循环记忆**：**有：36 层 Gated DeltaNet**；门控 Delta 更新＋核宽 4 的短卷积；循环模块不施加 RoPE。
- **局部注意力**：**无独立滑窗注意力层**；有短卷积及 QSA 微块组织。
- **全局注意力**：**有：12 层 QSA 全局稀疏注意力；25% RoPE**，旋转 64/256 维；按微块选择历史。
- **历史存储**：循环固定状态＋卷积缓存；用于稀疏读取的全局 KV 与索引记录。

### 3.6 Gemma 4 31B

配置来源：[Gemma 4 31B](https://huggingface.co/google/gemma-4-31B-it/blob/main/config.json)。

- **循环记忆**：**无循环记忆模块**。
- **局部注意力**：**有：50 层滑窗注意力**，$W=1024$；局部 RoPE。
- **全局注意力**：**有：10 层全局注意力；25% Proportional RoPE**。
- **历史存储**：局部 KV＋全局记录；全局层采用统一 K/V。

### 3.7 Step-3.7-Flash

配置来源：[Step-3.7-Flash](https://huggingface.co/stepfun-ai/Step-3.7-Flash/blob/main/config.json)。

- **循环记忆**：**无循环记忆模块**。
- **局部注意力**：**有：33 层滑窗注意力**，$W=512$；**100% RoPE**。
- **全局注意力**：**有：12 层全局注意力；50% RoPE**。
- **历史存储**：局部 KV＋全局 KV。

### 3.8 DeepSeek-V4-Pro-0813

配置来源：[DeepSeek-V4-Pro-0813](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813/blob/main/config.json)。

- **循环记忆**：**无 GDN／KDA／SSM 类循环记忆模块**。
- **局部注意力**：**有：窗口 128 的局部分支**；**12.5% RoPE**，旋转 64/512 维。
- **全局注意力**：**有：CSA／HCA 压缩全局读取**；**12.5% RoPE**；分别采用稀疏选取或对高压缩率记录读取。
- **历史存储**：局部 KV＋跨 token 压缩后的全局记录；记录数量仍随上下文增长。

### 3.9 DeepSeek-V4.1-Flash

配置来源：[DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/main/config.json)。

- **循环记忆**：**无 GDN／KDA／SSM 类循环记忆模块**。
- **局部注意力**：**有：全部 40 层均有窗口 128 的局部注意力**；**12.5% RoPE**。
- **全局注意力**：**有：后 38 层加入 CSA2 全局稀疏读取**；**12.5% RoPE**；结合记录压缩和跨层缓存共享。
- **历史存储**：局部 KV＋全局记录与索引；全局部分结合压缩、共享和量化，仍不是固定总容量的循环状态。

### 3.10 MiniMax M3

配置来源：[MiniMax M3](https://huggingface.co/MiniMaxAI/MiniMax-M3/blob/main/config.json)。

- **循环记忆**：**无循环记忆模块**。
- **局部注意力**：**有：后 57 层 MSA 含局部块读取**；**50% RoPE**；局部块与全局选块在同一注意力中组合。
- **全局注意力**：**有：前 3 层稠密全局注意力，后 57 层 MSA 全局选块**；**50% RoPE**，旋转 64/128 维。
- **历史存储**：全局 KV 与块索引；每次读取稀疏不等于只缓存局部历史。

### 3.11 GLM-5.3

配置来源：[GLM-5.3](https://huggingface.co/zai-org/GLM-5.3/blob/main/config.json)。

- **循环记忆**：**无循环记忆模块**。
- **局部注意力**：**无独立滑窗注意力层**。
- **全局注意力**：**有：78 层 MLA／DSA 全局稀疏注意力；25% RoPE**，旋转 64/256 维。
- **历史存储**：全局逐 token 潜在 KV 记录＋索引缓存。

### 3.12 Mistral Medium 3.5 128B

配置来源：[Mistral Medium 3.5 128B](https://huggingface.co/mistralai/Mistral-Medium-3.5-128B/blob/main/config.json)。

- **循环记忆**：**无循环记忆模块**。
- **局部注意力**：**无独立滑窗注意力层**。
- **全局注意力**：**有：88 层全局注意力；RoPE＋YaRN**。
- **历史存储**：全局 KV。

## 4. 公开实现中的核对要点

**Kimi K3：字段名含 `rope` 不等于实际旋转。** [官方实现](https://huggingface.co/moonshotai/Kimi-K3/blob/main/modeling_kimi_linear.py)要求 `mla_use_nope=True`，令 `rotary_emb=None`，直接拼接 Q/K 分量而不调用位置旋转。配置中的 `qk_rope_head_dim=64` 保留了分量尺寸命名，不能据此把其 MLA 判为部分 RoPE。同一实现分别保存 `recurrent_states`、`conv_states` 和注意力 KV，清楚区分了循环状态与全局历史记录。MLA 的参考实现可能缓存展开后的 KV，优化实现则可利用潜在表示压缩；这不改变它保留逐 token 记录的性质。

**GLM-5.3-Flash：主注意力 NoPE 不等于辅助模块没有任何位置参数。** [文本主干实现](https://github.com/huggingface/transformers/blob/main/src/transformers/models/glm5_next/modeling_glm5_next.py)中，主注意力的 `qk_rope_head_dim=0`；索引器的池化压缩另有 `index_kpool_compress_ape`，用于区分池内位置。KDA 的循环更新与短卷积同样提供顺序结构。因此应写“主注意力 NoPE”，而不是“全模型没有位置机制”。

**Nemotron 3 Ultra：注意力 NoPE 根据实际计算路径判断。** [Nemotron-H 实现](https://github.com/huggingface/transformers/blob/main/src/transformers/models/nemotron_h/modeling_nemotron_h.py)的注意力前向直接使用投影后的 Q/K，不施加 RoPE；配置中存在 `rope_theta` 等默认字段不能反推实际使用。表中 48∶12 只比较 Mamba-2 与注意力模块，另有 48 个独立 MoE 模块，不能把它误读成 60 个与其他模型完全同构的 Transformer block。

**Qwen3.8-Flash-Next：`full_attention` 的配置标签不代表稠密 full attention。** [模型卡](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)明确将这些层定义为 QSA，按微块进行稀疏读取。其全局候选范围与每次实际读取的记录数是两个量。该版本是架构预览，列入表中用于展示组合选择。

**Step 与 Gemma：局部层和全局层的旋转比例不同。** [Step 官方实现](https://huggingface.co/stepfun-ai/Step-3.7-Flash/blob/main/modeling_step3p7.py)按层读取 `partial_rotary_factors`；空的 `use_rope_layers` 列表不表示关闭所有 RoPE。Step 配置列出了额外预测支路，主干应只统计前 45 层。Gemma 4 则分别配置局部 RoPE 和全局 Proportional RoPE；表中 25% 是全局旋转维度比例，不是全局层占比。

**DeepSeek 与 MiniMax：局部、全局可以在同一个层中组合。** [DeepSeek-V4.1 报告](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/main/DeepSeek_V41_Tech_Report.pdf)明确说明：前两层只有局部注意力，其余层结合局部 KV 与选中的全局记录；CSA2 编码器分支压缩率为 2，解码器分支为 1，并共享部分全局 KV 与索引。MiniMax 的局部块与全局选块同属 MSA，不能算成额外 57 个局部层。记录压缩、跨层缓存共享与 Engram 类参数记忆也不能直接归为沿 token 时间轴更新的固定循环状态。

同系列的其他已核对配置包括：[Gemma 4 26B-A4B](https://huggingface.co/google/gemma-4-26B-A4B-it/blob/main/config.json)为 25 层局部＋5 层全局，位置方案与表中 31B 相同；[Nemotron 3.5 Lightning](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16/blob/main/config.json)为 23 个 Mamba-2＋6 个全局 NoPE 注意力模块，另有 23 个 MoE 模块。

## 5. 用于理解结构差异的较早实例

这些实例保留用于与前文论文对应；它们不是对当前旗舰版本的替代描述。

### 5.1 Mistral 7B v0.1

配置来源：[Mistral 7B v0.1](https://huggingface.co/mistralai/Mistral-7B-v0.1/blob/main/config.json)。

- **循环记忆**：**无**。
- **局部注意力**：**有**：$W=4096$，RoPE。
- **全局注意力**：**无独立全局层**。
- **历史存储**：局部 KV。

### 5.2 Gemma 3

配置来源：Gemma 3 [R21]。

- **循环记忆**：**无**。
- **局部注意力**：**有**：通常每组五层局部 RoPE。
- **全局注意力**：**有**：通常每组一层全局 RoPE，频率与局部不同。
- **历史存储**：局部 KV＋全局 KV。

### 5.3 SmolLM3

配置来源：[SmolLM3](https://huggingface.co/HuggingFaceTB/SmolLM3-3B/blob/main/config.json)。

- **循环记忆**：**无**。
- **局部注意力**：**无独立局部层**。
- **全局注意力**：**有**：全部为全局注意力，每四层中一层 NoPE，其余使用 RoPE。
- **历史存储**：全局 KV。

### 5.4 DeepSeek-V3

配置来源：DeepSeek-V3 [R22]。

- **循环记忆**：**无**。
- **局部注意力**：**无独立局部层**。
- **全局注意力**：**有**：全局 MLA，解耦的内容／RoPE 分量。
- **历史存储**：全局逐 token 潜在 KV 记录。

### 5.5 Griffin

配置来源：Griffin [R20]。

- **循环记忆**：**有**：门控循环模块与短卷积。
- **局部注意力**：**有**：局部 RoPE 注意力。
- **全局注意力**：**无全局注意力层**。
- **历史存储**：固定状态＋卷积缓存＋局部 KV。

### 5.6 Kimi Linear

配置来源：Kimi Linear [R12]。

- **循环记忆**：**有**：KDA 与短卷积，KDA∶全局 MLA 为 3∶1。
- **局部注意力**：**无独立局部层**。
- **全局注意力**：**有**：全局 MLA，NoPE。
- **历史存储**：固定状态＋卷积缓存＋全局记录。

### 5.7 Nemotron 3 Super

配置来源：[Nemotron 3 Super](https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Super-Technical-Report.pdf)。

- **循环记忆**：**有**：Mamba-2。
- **局部注意力**：**无独立局部层**。
- **全局注意力**：**有**：全局注意力，报告明确省略位置嵌入。
- **历史存储**：固定状态＋卷积缓存＋全局 KV。

Gemma 与 SmolLM3 展示改变访问范围或位置机制，同时保留逐 token 记录；Griffin 与 Kimi 展示循环状态可与局部记录或全局记录组合；Kimi、Nemotron 与 Qwen 展示循环混合结构仍可分别选择全局 NoPE 或部分 RoPE。DeepSeek 等模型又引入压缩后仍可寻址的历史记录，历史表示不止“完整 KV／固定状态”两个端点。

分析一个新架构时，应分别记录各模块的 $\mathcal V_t$、$P_{ts}$，以及历史保留为记录还是通过 $\Phi(t,s)$／$\Psi(s,t)$ 合并进状态，再用干预实验判断实际分工。模型采用某种组合是有效性的证据，不能单独证明该组合最优。现有公开结果尚未在旗舰规模、匹配数据与计算预算的条件下覆盖“局部 RoPE＋全局 NoPE”“循环记忆＋全局 NoPE”“三者组合”及全局部分 RoPE 等全部对照。

## 引用与原稿

- [R12] Kimi Linear: An Expressive, Efficient Attention Architecture。
- [R20] Griffin: Mixing Gated Linear Recurrences with Local Attention for Efficient Language Models。
- [R21] Gemma 3 Technical Report。
- [R22] DeepSeek-V3 Technical Report。

历史完整版本：[[90-archive/attention-position-memory/attention-position-memory-2026-09-29|2026-09-29 原稿]]。

[R12]: https://arxiv.org/abs/2510.26692
[R20]: https://arxiv.org/abs/2402.19427
[R21]: https://arxiv.org/abs/2503.19786
[R22]: https://arxiv.org/abs/2412.19437
