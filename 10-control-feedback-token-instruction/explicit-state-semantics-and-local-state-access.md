---
type: supplement
status: active
tags:
  - control-feedback
  - token-instruction
  - explicit-state-semantics
  - local-state-access
---

# 显式状态语义与局部状态访问：分支 A/B 细节补充

这份笔记是 `from-historical-motivation-to-research-branches.md` 的细节补充，专门解释分支 A 与分支 B 的区别、对照组、强基线和合流条件。

核心结论：

> 分支 A 研究“动作语义是否清楚”；分支 B 研究“模型每一步能看到多少状态”。A 是语义/轨迹轴，B 是信息访问/可见性轴。

## 1. 最容易混淆的点

A/B 不能写成粗糙的：

> TapeWalker Load/Store vs Regex/Grep/SQL/Tools

这种比较会把多个变量混在一起：

- 工具能力。
- resolver 能力。
- 状态语义。
- 局部可见性。
- workspace 粒度。
- runtime/scaffold 成本。

更正确的拆法是：

- A：在工具能力相近时，比较动作语义组织方式。
- B：在 resolver 能力相近时，比较状态访问粒度和可见性。
- A+B：比较二者组合后是否产生不可被强 typed tools 或强 retrieval/indexing 吸收的交互收益。

## 2. 分支 A：显式状态语义

分支 A 研究：

> 状态、读、写、提交、可见性、回放、诊断，是否能成为稳定运行时事件对象。

它关心的是系统做了什么，是否能被稳定表达成清楚的状态事件。

典型状态事件包括：

- `address`
- `read`
- `write`
- `patch`
- `commit`
- `rollback`
- `verify`
- `replay`
- `diagnose`

A 不要求模型只能看到局部状态。模型可以看到完整 JSON、大块文件、完整上下文，仍然可以研究 A。

因此：

- A 不是局部访问实验。
- A 不是省 token 实验。
- A 不是检索实验。
- A 是事件语义和轨迹结构实验。

## 3. A 到底是谁和谁比

A 不是简单比较：

> TapeWalker Load/Store vs Regex/Grep/SQL

而是比较：

> 统一显式状态事件接口 vs 异质 typed tools 接口。

强 typed tools baseline 可以长这样：

```text
grep(query, trace_id)
read_file(path, range, trace_id)
edit_file(path, range, patch, tx_id)
sql(query, trace_id)
run_check(target, trace_id)
commit(tx_id)
rollback(tx_id)
```

这个 baseline 已经有：

- 结构化 schema。
- trace id。
- logging。
- transaction。
- typed arguments。

所以它不是弱 baseline。

A 的显式状态语义版本可能长这样：

```text
ADDRESS(intent, scope) -> address
READ(address) -> cell
WRITE(address, patch) -> delta
VERIFY(scope, predicate) -> result
COMMIT(delta)
ROLLBACK(delta)
DIAGNOSE(event_id)
```

注意：A 的 runtime 背后仍然可以使用 grep、SQL、LSP、文件系统、数据库或任何 resolver。区别在于，模型面对的主接口不是一堆异质 tools，而是统一的状态事件语言。

所以 A 想赢的不是：

> 不用 regex 也能查到东西。

而是：

> 在工具能力相近甚至相同的情况下，统一状态事件接口是否让模型更容易学习、归因、纠偏和生成可训练轨迹。

## 4. A 怎么算赢

A 不能只靠任务成功率赢，也不能只靠日志更整齐赢。

A 的合理胜利条件包括：

- 同样任务、同样模型、同样信息预算下，局部修复成功率更高。
- 错误更稳定地归因到 `address/read/write/commit/verify/infer`。
- 平均恢复步数更少。
- 同类错误复发率更低。
- 轨迹更容易训练 student model。
- 反事实样本更容易构造。
- 计入 schema/logging/transaction 成本后，仍有优势。

如果 `standard tools + typed schema + trace id + logging + transaction` 已经能达到同等效果，则 A 没有独立增量。

这里有一个关键边界：

> 如果 strong typed tools baseline 也把所有工具调用统一成 `address/read/write/commit/verify` 事件，并且模型也用这套事件做决策，那么它其实已经变成 A。

这不是 TapeWalker 名称上的失败，而是说明 A 的思想已被 baseline 吸收。此时不能再声称 TapeWalker 有额外增量。

## 5. A 的例子

任务：修复一个大 JSON 中的余额一致性错误。

普通 Agent 可能输出：

```text
我发现 user[17].balance 不对，先看 transactions，然后修改 balance，再检查一下。
```

普通 typed tools 可能执行：

```text
read_file(path="users.json", range="user[17]", trace_id="t1")
edit_file(path="users.json", range="user[17].balance", patch="930", tx_id="tx42")
run_check(target="user[17]", trace_id="t2")
commit(tx_id="tx42")
```

A 的显式状态语义可能表达为：

```text
DIAGNOSE invariant_violation: user[17].balance != sum(tx)
READ address: users[17].transactions
WRITE address: users[17].balance, value: 930
VERIFY scope: users[17], predicate: balance_consistency
COMMIT tx_42
```

这个差异不是能不能读文件，而是事件语义是否统一、可回放、可归因、可纠偏。

## 6. 分支 B：局部状态访问

分支 B 研究：

> 模型是否只能通过受约束的地址访问隐藏全局状态的局部片段，而不能每一步直接看到完整全局状态。

B 关心的是信息边界。

在 B 中，global state 藏在环境里。模型每一步只能看到：

```text
goal
last event
loaded local cells
small scratchpad
runtime observation
```

如果模型想知道别的信息，必须主动生成地址并读取：

```text
LOAD users[17]
LOAD users[17].transactions
LOAD ledger.page[931]
```

因此：

- B 不是事件语义实验。
- B 不是日志实验。
- B 不是“工具格式更规整”实验。
- B 是可见状态和访问粒度实验。

## 7. B 到底是谁和谁比

B 比的是状态可见性和访问粒度，不是简单比较哪个 resolver 更强。

这里要区分三个概念：

| 概念 | 作用 | 例子 |
| --- | --- | --- |
| resolver | 找到相关位置 | BM25、vector search、SQL index、LSP、tree-sitter、oracle resolver |
| access interface | 决定模型一次能看到多少状态 | full context、大 chunk、小 cell、精确 address |
| write/update semantics | 决定模型如何修改状态 | edit_file、patch cell、store address、commit delta |

B 的准确问题是：

> 在 resolver 能力相近时，局部状态访问接口是否比全局读取或粗粒度检索有更好的控制成本、修复成本和长度泛化？

可以有这些访问模式：

| 组别 | 模型看到什么 | 代表机制 |
| --- | --- | --- |
| Full-context | 每步看到完整状态或大块状态 | 长上下文 / full read |
| Search/RAG | 模型发 query，系统返回 top-k chunks | BM25 / vector search |
| Structured resolver | 模型用 SQL/LSP/tree-sitter 定位结构对象 | SQL / code index |
| Local Load/Store | 模型生成 address，只读写局部 cell | TapeWalker 风格接口 |
| Local Load/Store + A | 局部访问，并且所有读写提交都是显式状态事件 | 完整候选接口 |

## 8. B 怎么算赢

B 的关键不是“也能局部访问”，而是：

- 状态变长时，访问 token 成本增长更慢。
- 错误修复只需读取小范围 cell。
- 全局扫描次数更少。
- 大上下文重解释次数更少。
- 更长 JSON/AST/ledger/graph 上泛化更好。
- 在相近 resolver 命中率下，控制步数不爆炸。

B 的强对手不是普通 tools，而是：

- BM25。
- vector search。
- tree-sitter / LSP。
- SQL / index。
- 代码索引。
- 编辑器跳转。
- learned retriever。
- 任务专用 resolver。

因此，B 不能把强 retrieval/indexing 排除在外。更准确地说：

> retriever/index 可以是 address resolver。B 要证明的是，在 resolver 能力相近时，局部状态访问接口是否让控制成本、修复成本、长度泛化更好。

## 9. B 的两层实验

B 应拆成两层实验，避免把 resolver 强弱和局部访问接口混在一起。

### 9.1 固定 resolver，比访问接口

例如都使用 oracle resolver 或同一个 LSP resolver 找到候选地址，然后比较：

```text
返回大 chunk
返回局部 cell
返回局部 cell + 可写 address
返回局部 cell + commit/rollback
```

这一层回答 B 的核心问题：

> 局部访问接口本身是否有价值？

### 9.2 固定访问接口，比 resolver

例如都使用 local cell access，但 resolver 分别是：

```text
oracle address
BM25
vector
SQL index
tree-sitter/LSP
learned retriever
```

这一层回答工程问题：

> 什么 resolver 最适合承载 B？

如果第一层不成立，B 的核心主张不成立。如果第一层成立但第二层很弱，说明 B 需要更好的 resolver 才能落地。

## 10. B 的例子

任务：修复一个大 JSON 中的余额一致性错误。

Full-context 模式：

```text
模型每一步都看到完整 JSON 或大块 JSON。
```

Search/RAG 模式：

```text
模型发 query: "user 17 balance transactions"
系统返回 top-k chunks。
```

Structured resolver 模式：

```text
模型发 SQL 或结构化 query:
SELECT transactions FROM users WHERE id = 17;
```

Local Load/Store 模式：

```text
目标：修复 balance inconsistency。
模型不知道完整 JSON。
模型先决定读哪里：
LOAD users[17]
然后读：
LOAD users[17].transactions
再 patch：
STORE users[17].balance = 930
```

这个差异不是事件语义是否更漂亮，而是模型是否必须主动控制局部信息访问。

## 11. A/B 的 2x2 关系

A 和 B 是两个正交变量。

| | 无显式状态语义 | 有显式状态语义 |
| --- | --- | --- |
| 无局部访问 | typed tools 强基线 | A：显式状态语义 |
| 有局部访问 | retrieval/index 强基线 | A+B：完整候选接口 |

四个象限的含义：

| 象限 | 含义 |
| --- | --- |
| 无 A，无 B | 普通 Agent 或 typed tools，状态可大块可见，事件语义不完整。 |
| 有 A，无 B | 事件语义清楚，但模型仍可看大上下文。 |
| 无 A，有 B | 模型只能局部访问，但事件语义可能只是普通 retrieval/query。 |
| 有 A，有 B | 模型局部访问状态，并且每次访问、修改、提交都有显式状态语义。 |

最重要的边界：

- 只做 A，不能声称验证局部状态访问。
- 只做 B，不能声称验证显式状态语义。
- A+B 才接近完整 `Load/Store` 主张。

## 12. 结果解释

如果 A 成功、B 失败：

> 这条线更像 `agent trace / schema engineering`，不足以支撑局部访问原语。

如果 B 成功、A 失败：

> 这条线更像 `active retrieval / memory system`，不足以支撑显式状态语义。

如果 A 成功、B 成功，但 A+B 没有额外收益：

> 两个机制可以被现有系统分别吸收，`Load/Store` 作为统一低层原语仍未站住。

如果 A+B 在强基线下仍有交互收益：

> 才能开始主张统一状态访问接口可能有独立价值。

交互收益可以体现为：

- 更好地址选择。
- 更少全局重解释。
- 更低恢复步数。
- 更干净训练轨迹。
- 更稳定局部修复策略。
- 更好的长度泛化。
- 更低总成本 Pareto。

## 13. 与 TapeWalker 的关系

TapeWalker 当前可以看作一个候选实现，而不是命题本身。

更准确地说：

- TapeWalker 的 `Load/Store` 原语可能承载 A。
- TapeWalker 的 workspace/local cell 机制可能承载 B。
- TapeWalker 的完整接口可能承载 A+B。

但研究命题不能写成：

> TapeWalker 赢其他工具。

更稳的命题是：

> 在强 typed tools、强 logging、强 transaction、强 retrieval/indexing 对手下，TapeWalker 所代表的统一状态访问接口是否仍能产生学习、归因、纠偏或成本优势？

如果强对手吸收了 TapeWalker 的核心结构，并达到同等效果，那说明方向可能被吸收，而不是名字本身胜出。

