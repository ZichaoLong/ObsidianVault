# 控制反馈：基础 Bet 与状态层源覆盖

迁移整理：2026-06-04

本页记录 Next Token、NRAM、双命题、primary bet、确定性/智能层与 test-time 状态层批次的源文件覆盖情况。

| 源文件 | sha256 | 迁移去向 | 迁移状态 |
| --- | --- | --- | --- |
| `status/控制反馈-NRAM与Next-Token关系-2026-05-27.md` | `3f8c4d220846a34aee11f7e371448042a99ed9966325a2f05aee7e9510868cd7` | [[../10-控制反馈-TokenInstruction/Next-Token与Token-Instruction\|Next Token 与 Token = Instruction]] | 已整合 |
| `status/控制反馈-双命题关系-2026-05-27.md` | `34240096c85a66aaddcab87d7a15d83191aade1d3982a419f84f7abaf42f9bc1` | [[../10-控制反馈-TokenInstruction/双命题与Primary-Bet层级\|双命题与 Primary Bet 层级]] | 已整合 |
| `plan/控制反馈-primary-bet-层级.md` | `59e44d84250cd109c3fa64b80d545336e2767d1a812520cf587e515d9fc55bbe` | [[../10-控制反馈-TokenInstruction/双命题与Primary-Bet层级\|双命题与 Primary Bet 层级]] | 已整合 |
| `status/控制反馈-确定性层与智能层-2026-05-27.md` | `d93d276ef76ed644781fc01ccc1a36edc1ecc647036a7a7080c2e58c436793df` | [[../10-控制反馈-TokenInstruction/确定性层-智能层-状态层次\|确定性层、智能层与 Test-Time 状态层次]] | 已整合 |
| `plan/控制反馈-test-time-state-hierarchy.md` | `b0f1a9a2f67d14154715501f7e96dd2d118323e8fc49f415c8864d2e4cd92da3` | [[../10-控制反馈-TokenInstruction/确定性层-智能层-状态层次\|确定性层、智能层与 Test-Time 状态层次]] | 已整合 |

## 备注

- 本批次强化了“Next Token 是基础 bet，Token=Instruction 是语义推广”的定位。
- 本批次同时保留了参数冻结优先、test-time 参数更新后置的实验边界。

