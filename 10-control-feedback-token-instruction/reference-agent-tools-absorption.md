---
type: reference
status: active
cssclasses:
  - compact-evidence-table
tags:
  - control-feedback
  - agent-tools
  - explicit-state-semantics
  - local-state-access
  - reference
---

# Agent 工程对 A/B 弱版本的吸收

更新时间：2026-06-09

Codex 参照版本：[openai/codex@743f5aad38accd52da34bf4dcbdd1215a8c3ab9a](https://github.com/openai/codex/tree/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a)

结论：

> 公开可见的前沿 Agent SDK / runtime 已经吃掉了 A/B 分支的大量弱版本收益。A 的弱版本是 `typed tools`、结构化 tool call、trace/call id、运行时事件、approval、checkpoint/replay、trace grading、eval loop、局部 patch/diff；B 的弱版本是 search/retrieval/index/local read-write/resource discovery/tool discovery/checkpoint。它们都不应再包装成项目的新贡献。

A 分支剩下的可守命题应收缩为：

> 在强 `typed tools + logging + approval + checkpoint/replay + patch/diff + transaction-like runtime` 基线下，统一显式状态语义是否还能带来更好的可学习性、局部纠偏、反事实数据质量或跨工具迁移。

B 分支剩下的可守命题应收缩为：

> 在强 `retrieval + indexing + local tools + checkpoint/diff` 基线下，隐藏全局状态、固定观察预算、模型控制 selector、resolver 能力受控、reader 返回有界的局部状态访问接口，是否还能改善访问成本、长度泛化、局部修复范围或 selector 学习。

如果做不到，A 应降级为 agent trace/schema engineering 的 sanity check；B 应降级为 retrieval / memory / indexing engineering 的 sanity check。

## A：已被吸收的弱版本

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

## B：已被吸收的弱版本

| 可能收益 | 吸收层级 | 证据与影响 |
| --- | --- | --- |
| 局部搜索 / 定位 / 读取 | `I高 / R高 / P中 / L低` | 严肃 coding agent 已经常规使用 shell、`rg`、文件读写、MCP filesystem、数据库资源、代码索引和编辑器式跳转。Codex 的 shell tool 暴露命令执行接口，见 [shell_spec.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/shell_spec.rs#L205-L220)；MCP 例子包含 `filesystem/read_file`，见 [mcp.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/mcp.rs#L446-L455)。B 不能主张“支持局部读取”是新贡献。 |
| 延迟工具发现 / 主动选择反馈入口 | `I中高 / R高 / P中高 / L低` | Codex 有 `tool_search`：对 deferred tool metadata 做 BM25 搜索，并把匹配工具暴露给下一次模型调用；见 [tool_search_spec.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/tool_search_spec.rs#L49-L61)、[tool_search.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/tool_search.rs#L29-L47) 和 [tool_search.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/tool_search.rs#L112-L123)。这已经是“模型先生成 query，再取回候选反馈入口”的弱 B。 |
| 大工具集的按需暴露 | `I中高 / R高 / P中 / L低` | Codex 会把 MCP tools 分成 direct / deferred，并在条件满足时只暴露 search 入口，见 [mcp_tool_exposure.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/mcp_tool_exposure.rs#L18-L49)、[spec_plan.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/spec_plan.rs#L790-L814) 和 [spec_plan.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/spec_plan.rs#L840-L860)。这说明“不要一次性暴露全部可用工具/上下文”已经是现实工程压力下的设计。 |
| tool/resource metadata 作为 resolver 输入 | `I中高 / R高 / P中 / L低` | Codex 的 MCP 和 dynamic tools 会把工具名、描述、connector、namespace、schema properties 拼成 search text，见 [mcp.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/mcp.rs#L90-L114)、[mcp.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/mcp.rs#L260-L305)、[dynamic.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/dynamic.rs#L78-L87) 和 [dynamic.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/dynamic.rs#L216-L234)。这接近 B 中的 resolver，但对象是工具，而不是 workspace cell。 |
| MCP resources / templates / resource read | `I高 / R中高 / P中 / L低` | Codex 暴露 `list_mcp_resources`、`list_mcp_resource_templates`、`read_mcp_resource`，描述明确说 resources 可提供 files、database schemas、application-specific information，见 [mcp_resource_spec.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/mcp_resource_spec.rs#L6-L31)、[mcp_resource_spec.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/mcp_resource_spec.rs#L33-L59) 和 [mcp_resource_spec.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/mcp_resource_spec.rs#L61-L93)。这说明“按 URI/模板读取上下文资源”也已被工具生态吸收。 |
| 局部写入 / patch / diff / 可见状态变化 | `I中高 / R高 / P中 / L中低` | Codex 的 `apply_patch` 会 parse、verify、转换为 structured changes、执行并追踪 committed delta，见 [apply_patch.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/apply_patch.rs#L337-L435)、[runtimes/apply_patch.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/runtimes/apply_patch.rs#L57-L75)、[runtimes/apply_patch.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/runtimes/apply_patch.rs#L220-L266) 和 [events.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/events.rs#L588-L615)。B 不能把“局部修改文件”当作独立新点。 |
| rollout / resume / fork / history search | `I中 / R中高 / P高 / L中低` | Codex 有 `InitialHistory::Resumed/Forked`、`RolloutItem`，并持久化 `ToolSearchCall`、`ToolSearchOutput`、tool call output、patch end、turn lifecycle；见 [protocol.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L2321-L2334)、[protocol.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L2825-L2833)、[policy.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/rollout/src/policy.rs#L28-L63) 和 [policy.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/rollout/src/policy.rs#L74-L157)。这支持轨迹回看和后续数据利用，但不是完整 B 实验协议。 |
| 完整 B：隐藏全局状态、固定观察预算、模型控制 selector、resolver parity、bounded reader、局部 repair cost 评估 | `I低 / R低 / P低 / L低` | Codex 支持大量局部工具和检索入口，但通常不强制隐藏全局状态，不固定每步 observation budget，也没有把 selector / resolver / reader 作为实验变量分别记录。因此 Codex 不是完整 B，只是吸收了 B 的弱工程部件。 |

这张表的关键含义是：B 不能再把 `grep/read_file/search/index/patch` 当作对照组之外的“新机制”。强 B 必须把这些能力放进 baseline，并进一步控制信息边界、resolver 能力、返回粒度和成本账本。

## Codex 源码判断：A

Codex 已经不是“普通文本工具调用”。

- MCP tool 元数据、schema shaping 和 model-visible name normalization 已工程化，见 [tools.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/codex-mcp/src/tools.rs#L1-L56)。
- Agent runtime 有结构化事件流，见 [protocol.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L1118-L1133)。
- History 支持 resumed / forked，rollout item 支持 response item、compacted item、turn context 和 event msg，见 [protocol.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L2321-L2334) 与 [protocol.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/protocol.rs#L2825-L2833)。
- `apply_patch` 不只是自然语言命令，而是有 parse、verify、structured changes、status、delta，见 [apply_patch.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/core/src/tools/handlers/apply_patch.rs#L337-L435)。
- approval / guardian 已是结构化 runtime 状态，见 [approvals.rs](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/protocol/src/approvals.rs#L134-L170)。

但 Codex 也不是完整 event sourcing。根据 rollout persistence policy，[`PatchApplyEnd`、`McpToolCallEnd`、turn lifecycle 等会持久化](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/rollout/src/policy.rs#L74-L100)，而 [`PatchApplyBegin`、`PatchApplyUpdated`、`TurnDiff`、`ExecCommandBegin` 等默认不持久化](https://github.com/openai/codex/blob/743f5aad38accd52da34bf4dcbdd1215a8c3ab9a/codex-rs/rollout/src/policy.rs#L101-L157)。这说明“显式状态语义”在 runtime 层已被大量采纳，但还没有等同于统一、持久、模型可学习的 semantic transition layer。

## Codex 源码判断：B

Codex 已经不是“把所有工具和状态一次性塞进上下文”的系统。

- `tool_search` 是最接近 B 的弱类比：模型生成 query，runtime 用 BM25 搜索 deferred tool metadata，然后把匹配工具暴露给下一次模型调用。这是主动选择反馈入口，但对象是工具集合，不是 workspace cell。
- MCP resources/templates 说明外部上下文已经可以被列举、参数化、按 URI 读取。这是 local state access 的工程底座之一，但不等于固定预算下的局部状态访问协议。
- Shell、MCP filesystem、`apply_patch`、TurnDiff 等机制说明 Codex 已经支持局部定位、局部读取、局部写入和局部 diff。B 若只比较“有没有局部读写工具”，实验会赢得太便宜。
- Rollout 持久化会保存 `ToolSearchCall` / `ToolSearchOutput` 等 response item，但对 streaming patch update、TurnDiff 等事件不是完整持久化。这意味着 B 相关轨迹可用于分析，但还不是专门为 selector/resolver/reader credit assignment 设计的数据层。

因此，Codex 对 B 的吸收可以概括为：

> 弱 B 的工程部件已经存在：搜索、索引、资源读取、工具发现、局部 patch、diff、history。完整 B 尚不存在：它要求把全局状态隐藏、观察预算固定、selector/resolver/reader 分开、resolver 能力受控，并用成本与泛化指标裁决。

## 对 A 分支的直接含义

A 分支如果只验证 `typed tools`、trace、logging、transaction、replay 有好处，研究价值会很低，因为这些已经是前沿 Agent 的正常形态。

A 仍可做，但主命题必须是强版：

> 统一状态事件协议是否能把异构 tool traces 转成更适合学习、纠偏、反事实生成、跨任务迁移的数据结构，并在强 typed-tools runtime baseline 上仍有增量。

## 对 B 分支的直接含义

B 分支如果只验证 `grep/read_file/search/index/patch` 有好处，研究价值会很低，因为这些已经是前沿 Agent 的正常形态。

B 仍可做，但主命题必须是强版：

> 在强 retrieval/index/local-tool baseline 上，统一局部状态访问接口是否能在固定观察预算下，让模型更稳定地选择反馈信源，并改善访问成本、长度泛化、局部修复范围或 selector 学习。

B 的强 baseline 至少应包括：

- `grep` / `rg` / shell search。
- `read_file(path, range)` 或等价文件读取。
- BM25 / vector search。
- SQL / database index。
- tree-sitter / LSP / code index / editor jump。
- MCP resources / resource templates。
- learned retriever 或任务专用 resolver。
- 局部 patch / diff / checkpoint / replay。

B 要避免的伪胜利：

- 只赢没有检索、没有索引、没有局部读写的弱 baseline。
- 结果主要来自更强 resolver，而不是访问接口。
- meaningful address 把语义答案偷渡进接口。
- cell 粒度由人工任务设计贡献了全部收益。
- runtime/scaffold 成本吞掉了 token 或步数收益。
- 状态变长后 global fallback、unnecessary read 或 false-local-repair 爆炸。

如果强 retrieval/index/local-tool baseline 达到同等 Pareto 点，B 应承认被吸收，结论降级为：

> 局部状态访问不是独立底层原语，而是优秀 Agent runtime 会自然吸收的一组 retrieval / indexing / memory engineering 技术。

## 参考

- [OpenAI Function calling](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI Agents SDK Tracing](https://openai.github.io/openai-agents-python/tracing/)
- [OpenAI Agents SDK Results](https://openai.github.io/openai-agents-python/results/)
- [OpenAI Trace grading](https://platform.openai.com/docs/guides/trace-grading)
- [OpenAI Cookbook: Build an Agent Improvement Loop with Traces, Evals, and Codex](https://cookbook.openai.com/examples/agents_sdk/agent_improvement_loop)
- [Anthropic Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Anthropic Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- [Model Context Protocol: Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [Model Context Protocol: Resources](https://modelcontextprotocol.io/specification/2025-06-18/server/resources)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph time travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel)
