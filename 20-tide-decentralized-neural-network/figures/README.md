# Tide 教学图集

先用结构图认识节点、区域与消息流，再用 P/S/U/F 简图解释一次区域选择。详图用于查阅状态、控制与返回值。

| 图片 | 用途 | 数学定义 |
|---|---|---|
| [节点、区域与消息流](tide-structure.png) | DAG 的发散、汇合、跨区连接与节点局部流程 | [TimedDAG §2—6](../timed-dag-region-selector-learning-note.md#2-固定结构时间节点图端口与区域划分) |
| [P/S/U/F 简图](PSUF-simple.png) | 共同选择、候选状态保留与激活后的发送 | [TimedDAG §5](../timed-dag-region-selector-learning-note.md#5-区域候选集合选择函数选择历史与状态采用) |
| [P/S/U/F 详图](PSUF-complete.png) | 计算快照、下一状态、控制与完整输出 | [共同接口索引](../reference/semantic-interface-index.md#局部函数) |

图中的节点名称只用于对应示例。结构图与 P/S/U/F 图表达正典的一般语义；某个局部架构的附加约束由相应教材定义。

## 生成图片

安装 [Python 依赖](requirements.txt)，并安装 Noto Sans CJK 字体。在仓库根目录运行：

```bash
python3 20-tide-decentralized-neural-network/figures/render.py --group legacy
```

`--output-dir` 可将结果写到其他目录。三份可编辑脚本位于 [src/legacy](src/legacy/)。恢复出处、字体与原图校验记录见 [PROVENANCE.md](PROVENANCE.md)。
