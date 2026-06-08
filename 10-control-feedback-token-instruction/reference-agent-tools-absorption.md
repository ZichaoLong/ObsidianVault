---
type: reference
status: active
tags:
  - control-feedback
  - agent-tools
  - explicit-state-semantics
  - reference
---

# Agent 工程对 A 弱版本的吸收

更新时间：2026-06-08

Codex 参照版本：[openai/codex@743f5aad38accd52da34bf4dcbdd1215a8c3ab9a](https://github.com/openai/codex/tree/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a)

结论：

> 前沿 Agent 工程已经吃掉了 A 分支的大部分弱版本收益。`typed tools`、结构化 tool call、trace/call id、运行时事件、approval、checkpoint/replay、trace grading、eval loop、局部 patch/diff 这些都不应再包装成项目的新贡献。

A 分支剩下的可守命题应收缩为：

> 在强 `typed tools + logging + approval + checkpoint/replay + patch/diff + transaction` 基线下，统一显式状态语义是否还能带来更好的可学习性、局部纠偏、反事实数据质量或跨工具迁移。

如果做不到，A 应降级为 agent trace/schema engineering 的 sanity check。

## 证据表

| 可能收益 | 前沿 Agent 是否已拿到 | 证据 | 对 A 的影响 |
| --- | --- | --- | --- |
| typed action schema | 高 | OpenAI function calling 使用 JSON Schema，并支持 `strict` 模式；Anthropic tool use 有 `input_schema` 与 strict tool use；MCP tool definition 包含 `inputSchema` / `outputSchema`。 | `typed tools vs tools` 只能做 Stage 0 sanity check，不能当主贡献。 |
| 稳定 tool call 生命周期 | 高 | OpenAI function call / function output 通过 `call_id` 关联；Anthropic `tool_use` / `tool_result` 形成工具调用闭环；Codex 有 [Event / EventMsg](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L1118-L1133)、[exec begin/end](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L3102-L3169)、[patch begin/update/end](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L3244-L3269) 等结构。 | “事件对象”本身已是工程现实。 |
| trace / logging / call correlation | 高 | OpenAI Agents SDK tracing 默认记录 LLM generation、tool call、handoff、guardrail；OpenAI trace grading 把 agent trace 作为可打分对象；Codex 的事件结构含 turn/call 关联字段。 | A 不能只证明“有 trace 更好”。 |
| replay-ready history / resume / fork | 高 | OpenAI Agents SDK 暴露 replay-ready next-turn input、run state、interruptions；LangGraph checkpoint 支持 replay / update_state / fork / time travel；Codex 有 [InitialHistory::Resumed/Forked](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L2321-L2334) 与 [RolloutItem](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L2825-L2833)。 | “可回放/可恢复”已被强 runtime 部分吸收。 |
| 显式状态变更 / diff / commit-ish 事件 | 中高 | Codex `apply_patch` 会解析和验证 patch，并发出结构化 changes / status / delta；见 [apply_patch.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/apply_patch.rs#L337-L435) 与 [tools/events.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/events.rs#L227-L254)。LangGraph 也有 checkpoint writes / pending writes。 | 在 coding / graph agent 中已经很接近 A。强基线必须包含 diff/transaction。 |
| approval / safety / guardrail 状态 | 高 | OpenAI Agents SDK 有 guardrail spans、pending approvals 和 resumable state；Codex `GuardianAssessmentAction` 覆盖 command、execve、apply_patch、network、MCP tool、permission request，见 [approvals.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/approvals.rs#L134-L170)。 | `verify/commit/deny` 这类状态语义已部分工程化。 |
| 错误归因 / 诊断 | 中 | OpenAI trace grading 给 agent trace 打结构化分数/标签；Codex 有 guardian status、patch failed/declined、tool error、sandbox denied 等结构化失败状态。 | 还有空间，但必须证明比现有 trace grading / runtime event 更可归因。 |
| 可纠偏 / repair loop | 中 | OpenAI cookbook 已给出 traces + feedback + evals + Codex 的 agent improvement loop；LangGraph 可从 checkpoint resume/fork；Codex 支持 resume/fork/rollback 语义。 | “数据飞轮”也已部分被主流吃掉。A 要证明更低噪声、更局部、更可训练。 |
| 反事实样本构造 | 中低 | replay/fork/time travel 提供基础，但自动生成高质量反事实 repair 样本还不是通用标准能力。 | 这是 A 可争取的剩余点之一。 |
| 统一 `address/read/write/verify/commit/rollback/diagnose` 作为模型可学习控制语义 | 低到中 | 现有系统有很多局部事件语义，但分散在 tool、runtime、trace、approval、patch、checkpoint 中，并非统一模型接口。 | 这是 A 最后可守的点，但必须用强基线检验，不可预设。 |

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
