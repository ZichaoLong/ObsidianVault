---
type: survey
status: active
date: 2026-06-11
tags:
  - recursive-decomposition
  - memory
  - small-language-models
  - distillation
  - post-training
  - data-centric-training
  - agent
---

# 小模型研究谱系调研

> [!summary] 本页定位
> 本页调查“不讨论递归分解 + memory 时，小模型研究主要在做什么”。它作为 [[future-scenarios|未来研究候选场景]] 的外部参照：如果递归分解与 memory 要面向小模型，必须对标数据、蒸馏、后训练、领域专精、架构效率和系统部署这些已经很强的路线。

调查时间：2026-06-11。

## 一页版结论

所谓“小模型超过更大模型”，通常不是：

> 参数更少天然更聪明。

而是：

> 新小模型用更好的数据、更强教师、更强后训练、更窄任务、更长推理预算、更适配的架构或更完整的系统 scaffold，在某些 benchmark / 成本口径 / 任务域上超过旧的大模型或泛化大模型。

当前小模型研究的主线可分成八类：

| 路线 | 典型问题 | 代表工作 / 系统 |
| --- | --- | --- |
| 计算最优与过训练 | 小模型吃更多、更干净 tokens，是否比欠训练大模型更强 | Chinchilla、LLaMA、SmolLM2、OLMo |
| 数据中心训练 | 怎样构造高密度高质量数据 | Phi、SmolLM2、Qwen、Gemma |
| 蒸馏 | 怎样把大模型 / reasoning model 的能力压进小模型 | Distilling step-by-step、Gemma 2、DeepSeek-R1-Distill |
| 后训练与 RL | 小模型能否通过 SFT / DPO / RLVR / rejection sampling 学会更好的答题策略 | DeepSeek-R1-Distill、s1、TinyZero、LIMO、Qwen-Math |
| 领域专精 | 小模型在代码、数学、函数调用、医疗、法律等窄域超过泛化大模型 | StarCoder2、CodeGemma、Qwen2.5-Coder、Qwen2.5-Math |
| 架构与推理效率 | 同参数下如何更快、更省内存、更适合端侧 | MobileLLM、Gemma 3、GQA、sliding/local attention、Mamba/RWKV |
| 压缩与部署 | 如何把模型放到手机、浏览器、嵌入式、私有环境 | quantization、LoRA/QLoRA、GGUF、edge SLM |
| 系统化小模型 | 小模型不独立解决全部任务，而是作为 router、draft、critic、tool caller、retriever controller | SLM-default / LLM-fallback agents、speculative decoding、guardrails |

对递归分解 + memory 线的关键启发：

> 小模型路线证明了：一个方向不一定先证明“唯一正确机制”；更现实的是先证明数据更好生成、训练信号更干净、成本-质量曲线更好、系统可吸收、某些任务族稳定胜出。

## “小模型”的定义并不统一

论文和工程里对 small language model 没有统一参数界限。

常见口径：

- sub-billion：100M-1B，强调端侧和低延迟。
- small dense：1B-8B，强调本地部署、低成本推理、可频繁调用。
- mid-small：8B-14B，常被当成“便宜但有足够能力”的 agent worker。
- 30B 级：在某些 reasoning 论文里仍被当作“小于前沿大模型”的可控对象，例如 s1-32B。

因此阅读“小模型超过大模型”的推送时，必须先问：

- 小模型是多少参数？
- 大模型是哪一代？
- 是 dense 还是 MoE active parameters？
- 是 base、instruct、reasoning、distilled 还是 domain model？
- 是否使用 retrieval、tool、verifier、pass@k、multi-sample、test-time search？
- 成本口径是参数量、FLOPs、tokens、latency、dollar cost、energy，还是只看 accuracy？

## 为什么小模型会超过更大模型

### 1. 新小模型 vs 旧大模型

很多“超过大模型”其实是：

> 新训练 recipe 的小模型超过旧训练 recipe 的大模型。

Chinchilla 结论指出，在固定训练 compute 下，过去很多大模型参数过多、训练 token 不足；更小但训练更充分的模型可能更强。LLaMA 也沿用类似思想，训练 7B-65B 模型时使用大量 tokens，使 LLaMA-13B 在多个 benchmark 上超过 GPT-3 175B 的一些结果。

这类结果不说明小模型突破了 scaling law，而是说明：

- 旧大模型欠训练。
- 训练数据质量和 token 数非常重要。
- 参数量不是唯一坐标。

参考：

- [Chinchilla / Training Compute-Optimal Large Language Models](https://arxiv.org/abs/2203.15556)
- [LLaMA: Open and Efficient Foundation Language Models](https://arxiv.org/abs/2302.13971)

### 2. 小模型 + 高密度数据

Phi 系列、SmolLM2、Qwen 等都强调数据中心路线。

核心做法：

- 大量过滤低质量网页。
- 合成 textbook-like data。
- 合成 reasoning / code / math / instruction data。
- 严格去重和 benchmark contamination control。
- 分阶段训练，先通用后专业。
- 在小模型上“过训练”，用更多 token 换更高能力。

Phi-3 technical report 的定位是 highly capable local language model，强调 3.8B 参数的 Phi-3-mini 可在若干 benchmark 上接近或超过更大模型。Phi-4 继续强调 synthetic data、organic data、curriculum 和 post-training。SmolLM2 则是 Hugging Face 的 data-centric small model 路线，1.7B 模型训练到约 11T tokens，并强调小模型也可以通过高质量语料显著增强。

参考：

- [Phi-3 Technical Report](https://arxiv.org/abs/2404.14219)
- [Phi-4 Technical Report](https://arxiv.org/abs/2412.08905)
- [SmolLM2: When Smol Goes Big](https://arxiv.org/abs/2502.02737)
- [Qwen2.5 Technical Report](https://arxiv.org/abs/2412.15115)

### 3. 小模型 + 大模型蒸馏

蒸馏是小模型提升最常见的原因之一。

蒸馏对象可以是：

- final answer。
- chain-of-thought / rationale。
- tool-use trace。
- preference pair。
- verifier feedback。
- rejection-sampled high-quality answer。
- reasoning model 的长思考轨迹。

Distilling step-by-step 证明了用 rationales 作为额外监督，小模型可以用更少标注数据超过更大模型的某些 task-specific 结果。Gemma 2 technical report 明确使用 knowledge distillation，尤其让较小模型从较大模型学习。DeepSeek-R1-Distill 则把 R1 的 reasoning traces 蒸馏到 Qwen / Llama 系列小模型上，形成 1.5B、7B、8B、14B、32B、70B 等 distilled models。

蒸馏带来的“超过”要谨慎解释：

> 小模型可能不是独立发现能力，而是压缩了 teacher 的行为分布。

这不降低工程价值，但会影响研究归因。

参考：

- [Distilling Step-by-Step](https://arxiv.org/abs/2305.02301)
- [Gemma 2 Technical Report](https://arxiv.org/abs/2408.00118)
- [DeepSeek-R1](https://arxiv.org/abs/2501.12948)

### 4. 小模型 + 后训练 / RL / Test-Time Scaling

小模型 post-training 现在非常活跃。

主要路线：

- SFT：高质量 instruction / reasoning data。
- DPO / preference tuning：让输出更符合偏好。
- RLHF / RLVR：用 reward 或 verifier 训练。
- rejection sampling：生成大量候选，只保留高质量样本。
- budget forcing：让模型在 test time 多思考。
- self-improvement：模型生成、验证、再训练。

DeepSeek-R1 展示了 RL 对 reasoning behavior 的塑造，并发布 distilled small models。TinyZero 复现了小模型也可通过 RL 在 Countdown 等任务上学出 self-verification / search-like 行为。s1 用少量高质量样本和 budget forcing，让 32B 模型在若干 reasoning benchmark 上接近或超过强 reasoning baseline。LIMO 进一步强调少量高质量 reasoning examples 可诱导强数学推理能力。

关键点：

> 这类小模型提升常常不是 base model 能力，而是后训练和推理策略共同作用。

参考：

- [DeepSeek-R1](https://arxiv.org/abs/2501.12948)
- [s1: Simple Test-Time Scaling](https://arxiv.org/abs/2501.19393)
- [TinyZero GitHub](https://github.com/Jiayi-Pan/TinyZero)
- [LIMO](https://arxiv.org/abs/2502.03387)

### 5. 小模型 + 领域专精

小模型最容易超过大模型的场景是窄域。

典型领域：

- code。
- math。
- tool calling / function calling。
- SQL。
- medical / legal / finance。
- guardrail / moderation。
- retrieval reranking。
- summarization in fixed schema。

StarCoder2 显示 3B/7B/15B code models 在 The Stack v2 和 permissive data 上训练后，较小 code model 可超过旧更大 code model。CodeGemma 提供 2B / 7B code-focused variants。Qwen2.5-Coder、Qwen2.5-Math 则把小模型放进代码/数学专用数据与后训练 pipeline。

这类结果的合理解释：

- 任务分布更窄。
- 数据更密集。
- 输出格式更稳定。
- benchmark 更贴近训练目标。
- 小模型容量足以覆盖领域内高频模式。

参考：

- [StarCoder2](https://arxiv.org/abs/2402.19173)
- [CodeGemma](https://arxiv.org/abs/2406.11409)
- [Qwen2.5-Coder](https://arxiv.org/abs/2409.12186)
- [Qwen2.5-Math](https://arxiv.org/abs/2409.12122)

### 6. 小模型 + 架构效率

小模型研究不只在数据和训练，也在架构。

目标：

- 同参数更强。
- 同能力更低延迟。
- 更小 KV cache。
- 更长上下文。
- 更适合端侧硬件。
- 更适合 speculative decoding 的 draft model。

代表方向：

- MobileLLM：研究 sub-billion 模型的结构，强调 depth / width / embedding sharing 等设计对端侧模型很关键。
- Gemma 3：使用 local / global attention pattern、long context、multi-modal variants 等工程设计。
- GQA / MQA：降低 KV cache 成本。
- sliding window / local attention：降低长上下文成本。
- Mamba / RWKV 等 sequence model：用线性或 recurrent-like 结构替代全 attention 的一部分成本。

这里的“超过”通常不是单纯 benchmark accuracy，而是：

- latency 更低。
- memory footprint 更小。
- throughput 更高。
- local deployment feasible。

参考：

- [MobileLLM](https://arxiv.org/abs/2402.14905)
- [Gemma 3 Technical Report](https://arxiv.org/abs/2503.19786)
- [Mamba](https://arxiv.org/abs/2312.00752)

### 7. 小模型 + 压缩 / 适配 / 端侧部署

这条线关注 deployment，不一定声称小模型更聪明。

常见技术：

- quantization：INT8、INT4、AWQ、GPTQ、GGUF 等。
- pruning / sparsity。
- LoRA / QLoRA。
- knowledge editing / adapter。
- on-device inference runtime。
- distillation to edge-specific model。

研究价值在于：

- privacy。
- offline。
- latency。
- cost。
- personalization。
- fleet-scale serving。

在这种场景里，“小模型超过大模型”的含义常是：

> 在端侧、低延迟、固定内存、隐私约束下，小模型是唯一可行或成本更优的方案。

参考：

- [QLoRA](https://arxiv.org/abs/2305.14314)
- [AWQ](https://arxiv.org/abs/2306.00978)

### 8. 小模型 + 系统角色化

小模型在 agent / system 中常常不是主模型，而是高频局部模块。

典型角色：

- router：决定是否需要大模型。
- draft model：speculative decoding。
- verifier / critic：检查格式、schema、简单逻辑。
- tool caller：生成结构化函数调用。
- retriever controller：改写 query、过滤候选。
- guardrail：安全/合规/PII 检查。
- summarizer / compressor：压缩上下文。
- memory retriever reranker：判断 memory 是否有用。

NVIDIA 等产业讨论中有一个常见观点：agentic system 里的许多高频子任务不需要每次调用最大模型，小模型可以默认执行，失败或高不确定时 fallback 到大模型。

这对本线很重要：

> 递归分解 + memory 若要工程化，小模型很可能不是最终 solver，而是 cheap worker、retriever、reranker、verifier、repair proposer 和 router。

参考：

- [Small Language Models are the Future of Agentic AI](https://arxiv.org/abs/2506.02153)
- [Speculative Decoding](https://arxiv.org/abs/2211.17192)

## 代表模型与技术路线

### Phi 系列

Phi 系列核心标签是：

- small but capable。
- synthetic data。
- textbook-quality data。
- high-quality filtered web。
- local deployment。
- post-training。

Phi-3-mini 3.8B 是典型案例：微软技术报告称它在若干 benchmark 上可 rival 更大模型，如 Mixtral 8x7B / GPT-3.5 级别指标。Phi-4 继续强调数据质量、合成数据、curriculum、post-training，并报告在数学 reasoning 等任务上的强表现。

适合抽象出的研究点：

- 小模型容量有限时，数据密度非常关键。
- synthetic data 不是低质量替代品，而是可控能力注入工具。
- 小模型可以成为某些能力的高效载体。

### SmolLM / SmolLM2

SmolLM2 是 data-centric small language model 的代表。

关键点：

- 提供 135M、360M、1.7B 等尺度。
- 1.7B 使用约 11T tokens 训练。
- 数据包含 FineWeb-Edu、DCLM、The Stack、数学和代码数据、指令数据等。
- 强调小模型也可以通过 curated / overtrained 数据达到很强能力。

适合抽象出的研究点：

- 小模型不是“少数据”模型。
- 小模型可能更依赖极高质量和极大 token/token-per-parameter 比例。
- 如果递归分解 / memory 要训练小模型，数据生成和过滤是核心问题。

### Gemma 2 / Gemma 3

Gemma 2 代表蒸馏 + 高效 dense family：

- 2B、9B、27B。
- 使用 knowledge distillation。
- 在小模型上强调性能-成本 Pareto。

Gemma 3 进一步强调：

- 1B、4B、12B、27B。
- 128k context。
- local / global attention pattern。
- multimodal variants。
- 更适合实际部署。

适合抽象出的研究点：

- 小模型和架构效率不可分。
- 蒸馏是小模型强能力的重要来源。
- 长上下文小模型不一定要解决全部 reasoning，但可承担边缘任务和局部任务。

### Qwen 系列小模型

Qwen2.5 / Qwen3 提供多个小尺度 dense models，并有 Coder、Math 等专门系列。

关键特点：

- 尺度完整：0.5B、1.5B、3B、7B、14B、32B 等。
- 通用、代码、数学、reasoning 多条线并行。
- Coder 和 Math 系列显示领域专精非常重要。
- Qwen3 引入 thinking / non-thinking 模式，强调推理模式可控。

适合抽象出的研究点：

- 小模型不只是一条曲线，而是一个 family。
- 领域专用小模型可能是 agent 系统里的 worker pool。
- 若做递归分解 + memory，小模型可按角色训练：decomposer、solver、verifier、retriever、arbiter。

### DeepSeek-R1-Distill

DeepSeek-R1-Distill 是 reasoning 蒸馏路线的代表。

关键特点：

- 使用 R1 生成 reasoning data。
- 蒸馏到 Qwen / Llama 小模型。
- 小模型在数学、代码和 reasoning benchmark 上获得显著提升。

适合抽象出的研究点：

- 小模型可学习“思考格式”和纠错习惯。
- 这给递归分解 + memory 一个直接启发：verified subproblem traces 可以成为小模型训练数据。
- 但必须区分：小模型能力来自机制，还是来自 teacher data。

### s1 / LIMO / TinyZero

这些工作代表“小数据 + 后训练 + test-time compute”的研究张力。

共同点：

- 不一定追求最大训练数据。
- 强调样本质量、训练配方和推理预算。
- 试图说明 reasoning behavior 可被少量高质量样本诱导。

适合抽象出的研究点：

- 对本线而言，高质量 verified traces 可能比大量 raw traces 更有用。
- 递归分解 / memory 的价值之一可能是产生更干净的训练数据，而不是直接提高当前推理。

## 常见误读

### 误读 1：小模型超过大模型，所以 scaling law 失效

更准确：

> 小模型通常是在更新数据、更强后训练、更窄任务或更高推理预算下超过某个旧大模型。

Scaling law 不是只看 parameter count。训练 compute、token 数、数据质量、后训练和 test-time compute 都是变量。

### 误读 2：小模型更适合推理

更准确：

> 小模型可能更适合频繁调用、低延迟、局部任务、端侧部署，但复杂推理仍常依赖 teacher、verifier、search 或大模型 fallback。

### 误读 3：小模型蒸馏成功说明小模型自己学会了所有能力

更准确：

> 蒸馏成功说明 teacher behavior 可被压缩到小模型的一部分任务分布中，不等于小模型独立具备 teacher 的全部泛化能力。

### 误读 4：benchmark 超过就是通用超过

更准确：

> 小模型常在窄 benchmark 或 domain-specific benchmark 上赢，但开放域、长尾、鲁棒性、多跳真实任务仍可能输。

### 误读 5：参数少就一定便宜

更准确：

> 如果小模型需要更多 sampling、更多 tool calls、更长 chain-of-thought、更复杂 verifier，最终 cost 未必低。

因此必须报告：

- input tokens。
- output tokens。
- calls。
- pass@k。
- verifier calls。
- wall-clock。
- memory footprint。
- dollar cost。
- energy / device constraint。

## 对递归分解 + memory 的启发

### 启发 1：小模型是低成本实验载体

D² / recursive decomposition 往往需要多次模型调用。小模型适合做：

- 多策略并行。
- multi-agent ensemble。
- candidate generation。
- cheap verifier / critic。
- memory retriever / reranker。
- repeated local repair。

如果用大模型做这些，成本太高；小模型能让机制实验更快、更便宜。

### 启发 2：小模型更需要结构化中间对象

小模型上下文理解、长程依赖、世界知识和鲁棒性弱于大模型。

因此它们更依赖：

- 明确 schema。
- 可验证子问题。
- 局部任务边界。
- typed memory。
- 强 verifier。
- fallback policy。

这和 `verified subproblem memory` 很贴近。

### 启发 3：小模型训练需要高质量轨迹

小模型容量有限，低质量 agent traces 可能污染严重。

递归分解 + memory 如果能产生：

- verified subproblem。
- successful local repair。
- failure type。
- reusable lemma / helper / schedule。
- clean trace。

这些数据可能比普通 agent log 更适合训练小模型。

这给本线一个现实价值：

> 即使机制本身不直接超过最强 Agent，它也可能成为小模型数据 flywheel 的清洗器和结构化数据生成器。

### 启发 4：小模型适合做 worker，不一定做 master

在一个递归分解 + memory 系统里，小模型可承担：

| 角色 | 小模型任务 |
| --- | --- |
| selector | 判断下一步展开哪个子问题 |
| retriever | 根据 proof state / profile / code context 找 memory |
| reranker | 判断 memory 是否有用 |
| verifier helper | 做快速格式、schema、局部一致性检查 |
| repair proposer | 基于 failure memory 提出局部修复 |
| compressor | 把 trace 压缩成 memory item |
| router | 决定是否升级到大模型 |

这比让小模型直接求解全部复杂任务更现实。

### 启发 5：小模型可以作为机制裁决的 stress test

如果某机制只在大模型上工作，很难知道是机制有效，还是大模型本身强。

小模型更弱，反而可能暴露：

- 结构化输入是否真的降低学习难度。
- memory 是否真的降低搜索成本。
- local repair 是否真的比 global retry 更省。
- verifier feedback 是否能被模型利用。

因此，小模型适合做机制研究的“放大镜”。

## 对本线的候选实验

### 实验 A：小模型 D² 曲线

问题：

> structural diversity + entropy routing 的收益是否随模型规模变化？

模型：

- 1.5B。
- 3B。
- 7B。
- 14B。
- 32B。

对照：

- CoT。
- self-consistency。
- same-prompt x3。
- structural diversity x3。
- entropy routing。
- fixed arbitration。

指标：

- accuracy。
- cost-normalized accuracy。
- all-wrong rate。
- at-least-one-correct rate。
- entropy calibration。
- arbitration benefit。
- token / latency cost。

裁决：

> 如果结构化分解对小模型收益更大，说明它可能是小模型能力补偿机制；如果随模型变大收益消失，则应收缩为小模型工程增强。

### 实验 B：小模型 worker vs 大模型 worker

问题：

> 在 recursive subproblem system 中，哪些角色可以由小模型稳定承担？

角色：

- decomposer。
- retriever。
- reranker。
- verifier helper。
- local repair proposer。
- arbiter。

对照：

- all large model。
- all small model。
- small worker + large fallback。
- small worker + verifier。
- small worker + verified memory。

指标：

- task success。
- calls。
- fallback rate。
- local repair success。
- harmful memory rate。
- latency。
- cost。

裁决：

> 如果小模型在部分角色上达到接近大模型的效果，并显著降低成本，这比“全小模型解题”更可落地。

### 实验 C：Verified traces 蒸馏小模型

问题：

> verified subproblem memory / local repair traces 是否比 raw agent traces 更适合训练小模型？

训练数据：

- raw CoT。
- raw agent trace。
- verified subproblem trace。
- failure + repair trace。
- generated lemma / helper / schedule memory。

模型：

- 1B-7B 小模型。

指标：

- imitation loss。
- exact action accuracy。
- verifier pass rate。
- local repair success。
- heldout family transfer。
- harmful behavior / hallucinated memory use。

裁决：

> 如果 verified traces 在同等 token 数下训练出更高 verifier pass rate 或更强 heldout repair，小模型研究就能反向支撑本线的数据价值。

### 实验 D：SLM-default / LLM-fallback memory agent

问题：

> 小模型作为默认 controller，大模型只在高不确定或失败时介入，是否形成更好的 cost-quality Pareto？

流程：

```text
small model proposes next subproblem / memory / repair
-> verifier checks
-> if fail or uncertain, escalate to large model
-> verified outcome writes memory
```

指标：

- success。
- cost per solved task。
- large-model call rate。
- verification failure rate。
- memory reuse rate。
- user-visible latency。

裁决：

> 如果大部分局部步骤可由小模型完成，递归分解 + memory 线可自然对接小模型系统化部署。

## 与 Lean / Kernel / Code 方向的关系

| 场景 | 小模型可承担的角色 |
| --- | --- |
| Lean | proof-state retriever、lemma usefulness reranker、next tactic proposer、failure classifier |
| Kernel | cost model、optimization memory retriever、failure classifier、patch / schedule proposer |
| Code / Algorithm | helper retriever、repair pattern classifier、property-test proposer、local patch proposer |
| Math D² | decomposer、solver、arbiter、entropy router |

这说明小模型不是一个独立于未来场景的第四主战场，而更像横向能力载体：

> 每个未来场景都可以问：哪些局部角色可以由小模型承担，哪些必须由大模型或 verifier 承担？

## 强基线与失败条件

### 强基线

小模型实验至少要对标：

- 同等参数量但不同数据的小模型。
- 同等推理成本的大模型。
- teacher distilled baseline。
- same prompt self-consistency。
- domain specialist model。
- small model + RAG。
- small model + verifier。
- small model + large fallback。
- quantized larger model。

### 成本账本

必须记录：

- model parameters。
- active parameters。
- training tokens。
- pretraining / post-training data source。
- whether distilled。
- input tokens。
- output tokens。
- calls。
- pass@k / sampling budget。
- verifier calls。
- wall-clock。
- GPU / device memory。
- dollar cost。
- energy / edge feasibility。

### 失败条件

应承认失败的情况：

- 小模型收益只来自 teacher distillation，无法证明机制增量。
- 任务太窄，只能说明 domain specialization。
- 成本账本显示小模型多次调用后并不便宜。
- 小模型无法稳定使用 memory，harmful retrieval 上升。
- 小模型 local repair 不如大模型 global retry。
- verified trace 训练不优于普通 trace 或 teacher CoT。
- 小模型 worker 需要频繁 fallback，系统复杂度吞掉收益。

## 当前裁决

小模型研究对本线的意义不是：

> 小模型本身就是递归分解 + memory 的证明。

而是：

> 小模型提供了一个现实牵引：如果 verified subproblem memory 能产生更干净的训练数据、更低成本的局部控制、更好的 worker specialization 和更清晰的 cost-quality Pareto，它就有可能被小模型系统吸收。

当前最建议的结合点：

1. 先做小模型 D² 曲线，确认 structural diversity / entropy routing 是否对小模型更有用。
2. 再做 small worker + large fallback，确认小模型能否承担 retriever / reranker / verifier helper / repair proposer。
3. 最后做 verified traces 蒸馏，确认本线是否能产生比 raw agent logs 更适合小模型学习的数据。

不要一开始就主张：

> 小模型 + 递归分解 + memory 会超过所有大模型。

更合理的主张是：

> 小模型是检验递归分解 + memory 是否具有数据效率、局部控制和系统成本优势的高性价比实验场。

## 参考

### Scaling / data-centric training

- [Training Compute-Optimal Large Language Models / Chinchilla](https://arxiv.org/abs/2203.15556)
- [LLaMA: Open and Efficient Foundation Language Models](https://arxiv.org/abs/2302.13971)
- [Phi-3 Technical Report](https://arxiv.org/abs/2404.14219)
- [Phi-4 Technical Report](https://arxiv.org/abs/2412.08905)
- [SmolLM2: When Smol Goes Big](https://arxiv.org/abs/2502.02737)
- [Qwen2.5 Technical Report](https://arxiv.org/abs/2412.15115)

### Distillation / reasoning post-training

- [Distilling Step-by-Step](https://arxiv.org/abs/2305.02301)
- [Gemma 2 Technical Report](https://arxiv.org/abs/2408.00118)
- [DeepSeek-R1](https://arxiv.org/abs/2501.12948)
- [s1: Simple Test-Time Scaling](https://arxiv.org/abs/2501.19393)
- [LIMO](https://arxiv.org/abs/2502.03387)
- [TinyZero GitHub](https://github.com/Jiayi-Pan/TinyZero)

### Domain models

- [StarCoder2](https://arxiv.org/abs/2402.19173)
- [CodeGemma](https://arxiv.org/abs/2406.11409)
- [Qwen2.5-Coder](https://arxiv.org/abs/2409.12186)
- [Qwen2.5-Math](https://arxiv.org/abs/2409.12122)

### Architecture / deployment

- [MobileLLM](https://arxiv.org/abs/2402.14905)
- [Gemma 3 Technical Report](https://arxiv.org/abs/2503.19786)
- [Mamba](https://arxiv.org/abs/2312.00752)
- [QLoRA](https://arxiv.org/abs/2305.14314)
- [AWQ](https://arxiv.org/abs/2306.00978)
- [Speculative Decoding](https://arxiv.org/abs/2211.17192)

### Agentic small model framing

- [Small Language Models are the Future of Agentic AI](https://arxiv.org/abs/2506.02153)
