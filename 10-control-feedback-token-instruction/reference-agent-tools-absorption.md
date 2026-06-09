---
type: reference
status: active
cssclasses:
  - compact-evidence-table
tags:
  - control-feedback
  - agent-tools
  - explicit-state-semantics
  - reference
---

# Agent 工程对 A 弱版本的吸收

更新时间：2026-06-09

Codex 参照版本：[openai/codex@743f5aad38accd52da34bf4dcbdd1215a8c3ab9a](https://github.com/openai/codex/tree/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a)

结论：

> 公开可见的前沿 Agent SDK / runtime 已经吃掉了 A 分支的大部分弱版本收益。`typed tools`、结构化 tool call、trace/call id、运行时事件、approval、checkpoint/replay、trace grading、eval loop、局部 patch/diff 这些都不应再包装成项目的新贡献。

A 分支剩下的可守命题应收缩为：

> 在强 `typed tools + logging + approval + checkpoint/replay + patch/diff + transaction-like runtime` 基线下，统一状态事件协议是否还能带来更好的可学习性、局部纠偏、反事实数据质量或跨工具迁移。

如果做不到，A 应降级为 agent trace/schema engineering 的 sanity check。

## 证据表

| 可能收益 | 吸收层级 | 证据与影响 |
| --- | --- | --- |
| typed action schema | `I高 / R高 / P中 / L中低` | OpenAI function calling 使用 JSON Schema，并支持 `strict` 模式；Anthropic tool use 有 `input_schema` 与 strict tool use；MCP tool definition 包含 `inputSchema` / `outputSchema`。`typed tools vs tools` 只能做 Stage 0 sanity check，不能当主贡献。 |
| 稳定 tool call 生命周期 | `I高 / R高 / P中高 / L中低` | OpenAI function call / function output 通过 `call_id` 关联；Anthropic `tool_use` / `tool_result` 形成工具调用闭环；Codex 有 [Event / EventMsg](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L1118-L1133)、[exec begin/end](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L3102-L3169)、[patch begin/update/end](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L3244-L3269) 等结构。“事件对象”本身已是工程现实。 |
| trace / logging / call correlation | `I高 / R高 / P中高 / L中` | OpenAI Agents SDK tracing 默认记录 LLM generation、tool call、handoff、guardrail；OpenAI trace grading 把 agent trace 作为可打分对象；Codex 的事件结构含 turn/call 关联字段。A 不能只证明“有 trace 更好”。 |
| replay-ready history / resume / fork | `I高 / R高 / P高 / L中` | OpenAI Agents SDK 暴露 replay-ready next-turn input、run state、interruptions；LangGraph checkpoint 支持 replay / update_state / fork / time travel；Codex 有 [InitialHistory::Resumed/Forked](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L2321-L2334) 与 [RolloutItem](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L2825-L2833)。“可回放/可恢复”已被强 runtime 部分吸收。 |
| 显式状态变更 / diff / commit-ish 事件 | `I中高 / R中高 / P中 / L中低` | Codex `apply_patch` 会解析和验证 patch，并发出结构化 changes / status / delta；见 [apply_patch.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/apply_patch.rs#L337-L435) 与 [tools/events.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/events.rs#L227-L254)。LangGraph 也有 checkpoint writes / pending writes。在 coding / graph agent 中已经很接近 A，强基线必须包含 diff / transaction-like runtime。 |
| approval / safety / guardrail 状态 | `I高 / R高 / P中 / L中低` | OpenAI Agents SDK 有 guardrail spans、pending approvals 和 resumable state；Codex `GuardianAssessmentAction` 覆盖 command、execve、apply_patch、network、MCP tool、permission request，见 [approvals.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/approvals.rs#L134-L170)。`verify/commit/deny` 这类状态语义已部分工程化。 |
| 错误归因 / 诊断 | `I中 / R中 / P中 / L中低` | OpenAI trace grading 给 agent trace 打结构化分数/标签；Codex 有 guardian status、patch failed/declined、tool error、sandbox denied 等结构化失败状态。还有空间，但必须证明比现有 trace grading / runtime event 更可归因。 |
| 可纠偏 / repair loop | `I中 / R中 / P中高 / L中` | OpenAI cookbook 已给出 traces + feedback + evals + Codex 的 agent improvement loop；LangGraph 可从 checkpoint resume/fork；Codex 支持 resume/fork/rollback 语义。“数据飞轮”已部分被主流吃掉，但公开证据更多说明 eval / improvement workflow，而不是证明事件级继续训练闭环已完全解决。 |
| 反事实样本构造 | `I中低 / R中 / P中高 / L中低` | replay/fork/time travel 提供基础，但自动生成高质量反事实 repair 样本还不是通用标准能力。这是 A 可争取的剩余点之一。 |
| 统一 `address / read / write / verify / commit / rollback / diagnose` 作为模型可学习控制语义 | `I中低 / R中低 / P中低 / L低` | 现有系统有很多局部事件语义，但分散在 tool、runtime、trace、approval、patch、checkpoint 中，并非统一模型接口。这里才是 A 最后可守的点，且必须用强基线检验，不可预设。 |

表中 `I/R/P/L` 分别表示 `Interface`、`Runtime`、`Persistence / replay`、`Learning / data flywheel`。公开文档和源码能比较清楚地证明 interface、runtime、replay 正在被吸收；但不能直接证明闭源 frontier agent 已经把事件级归因、局部修复、反事实样本和继续训练闭环全部解决。

## Codex 源码判断

Codex 已经不是“普通文本工具调用”。

- MCP tool 元数据、schema shaping 和 model-visible name normalization 已工程化，见 [tools.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/codex-mcp/src/tools.rs#L1-L56)。
- Agent runtime 有结构化事件流，见 [protocol.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L1118-L1133)。
- History 支持 resumed / forked，rollout item 支持 response item、compacted item、turn context 和 event msg，见 [protocol.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L2321-L2334) 与 [protocol.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L2825-L2833)。
- `apply_patch` 不只是自然语言命令，而是有 parse、verify、structured changes、status、delta，见 [apply_patch.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/apply_patch.rs#L337-L435)。
- approval / guardian 已是结构化 runtime 状态，见 [approvals.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/approvals.rs#L134-L170)。

但 Codex 也不是完整 event sourcing。根据 rollout persistence policy，[`PatchApplyEnd`、`McpToolCallEnd`、turn lifecycle 等会持久化](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/rollout/src/policy.rs#L74-L100)，而 [`PatchApplyBegin`、`PatchApplyUpdated`、`TurnDiff`、`ExecCommandBegin` 等默认不持久化](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/rollout/src/policy.rs#L101-L157)。这说明“显式状态语义”在 runtime 层已被大量采纳，但还没有等同于统一、持久、模型可学习的 semantic transition layer。

## 对 A 分支的直接含义

A 分支如果只验证 `typed tools`、trace、logging、transaction、replay 有好处，研究价值会很低，因为这些已经是前沿 Agent 的正常形态。

A 仍可做，但主命题必须是强版：

> 统一状态事件协议是否能把异构 tool traces 转成更适合学习、纠偏、反事实生成、跨任务迁移的数据结构，并在强 typed-tools runtime baseline 上仍有增量。

A 的可输裁决：

- 如果只赢 freeform tools，不赢 strong typed tools runtime，A 只是复现现代 Agent 工程常识。
- 如果赢 strong typed tools runtime，但收益主要来自更短格式、更低 action entropy、更强 validator，也不能说明统一状态语义成立。
- 如果能在相同工具能力、相近 schema 信息、相近可见状态量下，提升 event-level attribution、local repair、counterfactual validity、student sample efficiency，A 才有独立研究价值。
- 如果 strong typed tools runtime 通过自然工程改造达到同等收益，应承认 A 被吸收，并把结论改写为“优秀 Agent runtime 会收敛到状态事件层”。

## 对 B 分支的借鉴意义

这轮调查对 B 分支同样有约束作用：B 也不能把“能局部读取”或“有检索工具”当作新贡献。

前沿 Agent runtime 已经给 B 提供了强基线：

- OpenAI / Anthropic / MCP 的 tool calling 已允许模型调用检索、文件读取、SQL、浏览器、外部 connector 等局部观察工具。
- Codex 中 shell/read 类命令、MCP filesystem `read_file`、`rg`、`apply_patch`、MCP tools、tool search、deferred tools 等机制，已经让模型通过工具选择局部信息源。
- LangGraph 的 checkpoint / state / update_state / time travel 表明 graph runtime 可以把状态切成可恢复、可修改、可分支的对象。
- Codex `apply_patch` 已经把“局部修改 + 验证 + diff + 可能的 committed delta”工程化，这对 B 的局部写入与局部修复很有参考价值。

因此，B 的强基线不是 full-context agent，而是：

```text
typed retrieval / indexing / editing tools
+ BM25 / vector / SQL / LSP / tree-sitter / learned retriever
+ call id / trace / checkpoint
+ patch / diff / validation
```

B 的剩余特殊点应收缩为：

> 在强检索、强索引、强局部工具已经存在的条件下，模型是否能在隐藏全局状态中主动控制局部反馈信源，并通过受约束寻址改善访问成本、长度泛化、局部修复范围和 false-local-repair rate。

这意味着 B 必须借鉴 A 的审视方式，把“局部访问”拆开：

| 组件 | 已被工程吸收的弱版本 | B 剩余要检验的强版本 |
| --- | --- | --- |
| selector | 模型选择调用哪个工具、生成 query/path/range | 在固定 observation budget 下，模型是否学会稳定选择下一步最有价值的局部反馈信源。 |
| resolver | BM25、vector search、SQL、LSP、tree-sitter、代码索引 | resolver 能力相近时，接口形态是否改变控制成本与泛化，而不是 resolver 强弱主导结果。 |
| reader | 工具返回文件片段、搜索结果、数据库行、AST 节点 | 返回粒度、上下文量、cell 边界如何影响修复成功率和全局一致性。 |
| writer | `apply_patch`、edit tool、transaction-like commit | 局部写入是否能在隐藏全局状态下保持 invariant，并降低恢复步数。 |
| verifier | test、lint、validator、guardrail | 验证反馈是否足够局部，能否避免把任务退回全局重新解释。 |

B 的关键消融：

- meaningful address vs opaque address：地址名是否偷渡语义。
- oracle resolver vs learned resolver：收益来自访问接口还是 resolver 智能。
- local cell vs large chunk vs full context：收益来自局部性还是更多上下文。
- fixed observation budget：不固定预算时，B 会退化成普通检索系统评测。
- distant dependency / global invariant：防止局部访问牺牲全局一致性。
- scaffold cost：索引、workspace 切分、address schema、adapter 的成本必须计入。

B 的可能失败条件：

- 如果 BM25 / vector / SQL / LSP / learned retriever 加 typed tools 已达到同等成本和成功率，B 应降级为 retrieval / indexing engineering。
- 如果收益来自人工 cell 设计或 meaningful address，而不是模型学到的局部反馈控制，B 的机制命题不成立。
- 如果局部访问降低 token 但显著增加 false-local-repair 或 global invariant violation，不能算赢。
- 如果必须依赖全局 re-scan / full-context repair 才能稳定成功，B 没有证明小颗粒闭环优势。

## 参考

- [OpenAI Function calling](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI Agents SDK Tracing](https://openai.github.io/openai-agents-python/tracing/)
- [OpenAI Agents SDK Results](https://openai.github.io/openai-agents-python/results/)
- [OpenAI Trace grading](https://platform.openai.com/docs/guides/trace-grading)
- [OpenAI Cookbook: Build an Agent Improvement Loop with Traces, Evals, and Codex](https://cookbook.openai.com/examples/agents_sdk/agent_improvement_loop)
- [Anthropic Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Anthropic Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- [Model Context Protocol: Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph time travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel)
