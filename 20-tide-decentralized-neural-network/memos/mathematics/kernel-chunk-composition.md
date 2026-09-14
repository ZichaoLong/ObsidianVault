---
type: mathematical-research-memo
status: retained-derivation
semantic-baseline: tide-core-2
---

# 常用 kernel 为什么可以按 chunk 计算

本页保留 map、causal attention、仿射递推和 linear attention 的简短正确性推导。它们是局部算子的例子，不单独证明整个带区域选择的图可批量执行；图级条件见 [chunk 教材](../../timed-dag-chunk-prefill-learning-note.md)。原始推导见 Git `133d638` 的 `tide-mathematical-foundations.md` 第一部分 §3。

## 1. 比较对象

一个有状态算子是确定函数 $T:X\times S\to Y\times S$。给定左状态 $s_b$ 和输入 $x_b,\ldots,x_{c-1}$，依次令

$$
(y_t,s_{t+1})=T(x_t,s_t),\qquad b\le t<c.
$$

chunk 实现必须返回相同的全部 $y_t$ 及 $s_c$。如果两个 chunk 实现都满足这个定义，把 $[a,c)$ 在 $b$ 处分开，第一次的终态作为第二次初态，归纳即得与一次运行相同；不是只比较最终一项输出。

以下等式先使用精确实数算术。实际浮点归约次序、随机 dropout、位置编码和掩码都是额外的实现条件。

## 2. Map：逐位置纯函数

若 $y_t=f(x_t)$ 且没有跨位置可变状态，整段结果就是

$$
(f(x_b),\ldots,f(x_{c-1})).
$$

矩阵批量实现只改变这些独立函数作用的执行顺序，逐坐标相等。Norm、固定参数投影、FFN 及不读取时间递推状态的 router 常属于这一类。读取某个“神经状态”的函数是否仍是 map，取决于该状态是否已独立确定，而非它是否叫 router。

## 3. Causal attention：一次算出带掩码的全部行

假设整个局部输入序列 $z_t$ 已确定，固定投影给出

$$
q_t=W_Qz_t,\quad k_t=W_Kz_t,\quad v_t=W_Vz_t.
$$

左边界 cache 保存所有允许读取的历史 $(k_i,v_i)$ 及其位置 $i<b$。本例采用包含当前位置的因果规则，定义

$$
y_t=\frac{\sum_{i\le t}\exp(q_t^\top k_i/\sqrt d)\,v_i}
{\sum_{i\le t}\exp(q_t^\top k_i/\sqrt d)}.
\tag{1}
$$

求和只覆盖参考算子允许的历史位置；本例每个位置存在一个键值对，分母严格为正。

decode 在位置 $t$ 追加 $(k_t,v_t)$，然后应用式 (1)。chunk 先计算区间内全部 Q/K/V，把旧 cache 与新 K/V 拼接，再对第 $t$ 行屏蔽 $i>t$ 的列。

**证明。** 第 $t$ 行可见的键值对与 decode 到达 $t$ 时完全相同，点积分数及分母也相同，所以输出行相同。最终两者都向旧 cache 追加 $b,\ldots,c-1$ 的 K/V，状态相同。□

边界条件包括位置/RoPE 一致、相同的窗口和 source mask、同刻多来源的规则，以及全部 Q/K/V 的自变量在批量调用前已知。一般图中的局部历史可以是不规则位置集合，但必须把式 (1) 的求和域换成同一个明确集合，不能按物理到达顺序拼出另一个历史。

因果 attention 有专门的 bulk 算法，并不因此拥有固定大小的历史摘要。其算术量、KV 存储和实际速度仍取决于长度与实现。

## 4. 仿射递推：把转移作为可组合的对象

考虑 $s_t\in\mathbb R^d$ 及

$$
s_{t+1}=A_ts_t+b_t.
$$

$A_t,b_t$ 必须能由本次已经给定的输入预先算出，不能先知道未知的 $s_t$ 才决定。用 $m_t=(A_t,b_t)$ 表示单步转移，定义“先 1 后 2”的组合

$$
(A_2,b_2)\star(A_1,b_1)
=(A_2A_1,A_2b_1+b_2).
\tag{2}
$$

三次组合的矩阵项都是 $A_3A_2A_1$，向量项都是 $A_3A_2b_1+A_3b_2+b_3$，故 $\star$ 结合；单位元是 $(I,0)$。

对每个位置取前缀组合 $(\bar A_t,\bar b_t)=m_t\star\cdots\star m_b$，则

$$
s_{t+1}=\bar A_ts_b+\bar b_t.
$$

**证明。** 单步成立；将 $A_{t+1}s_{t+1}+b_{t+1}$ 代入前缀表达式，恰得式 (2) 的组合。归纳证明所有状态相同。输出若是已知输入和这些状态的纯读出，也逐项相同。□

结合律允许平衡树式 prefix scan；要获得有意义的并行收益，还需 summary 紧凑、封闭且 combine 便宜。标量/对角递推每次组合成本为 $O(d)$，适合工作量 $O(Ld)$、组合深度 $O(\log L)$ 的 scan。任意稠密 $d\times d$ 矩阵的组合可能比逐步矩阵向量乘昂贵得多；稀疏矩阵相乘还可能变稠密。

“任何函数复合都结合”不能替代这些条件。把整段程序装进越来越长的闭包，只是换了记录方式。

## 5. Linear attention accumulator

令特征映射 $\phi$ 已固定，定义累计矩阵与累计向量

$$
C_{t+1}=C_t+\phi(k_t)v_t^\top,\qquad
r_{t+1}=r_t+\phi(k_t).
$$

一种读出是

$$
y_t=\frac{\phi(q_t)^\top C_{t+1}}
{\phi(q_t)^\top r_{t+1}+\varepsilon}.
$$

必须限定输入域或选择 $\phi,\varepsilon$，使分母不为零。加法结合，所以对新增矩阵和向量做 prefix sum，得到与顺序追加相同的每个 $C_{t+1},r_{t+1}$；纯读出因此相同，最终 accumulator 也相同。

这是该 linear-attention 算子自身的精确状态；没有证明它等于一般 softmax attention，或是任意 Transformer KV 的无损压缩。

## 6. 怎样组合成更大的模型

若有限算子链的每个局部 chunk 契约已证明，且状态不隐式交叉读写，则可以按层运行整段：第一层输出逐项相同；把它交给第二层，第二层前提相同；对有限层数归纳即可。

进入一般 TimedDAG 后，要另外处理完整时间纤维、区域选择、selector-history 和跨切面消息。仅有几个可以 scan 的 kernel，不足以忽略它们之间的控制依赖。反过来，控制递推顺序执行也不必然阻止独立的 Full 作用按节点打包；这两种并行问题由 [状态反馈与节点批](state-feedback-and-node-chunks.md) 区分。
