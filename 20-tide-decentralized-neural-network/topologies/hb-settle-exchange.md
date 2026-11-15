---
type: topology-definition
status: active
tags: [tide, hb, settlegraph]
---

# HB-Settle：分阶段位交换图

本图为到达对齐的计算安排普通节点之间的多尺度交换。展开增加容量，最宽处连续交换不同地址位，收拢途中继续交换；不要求填满输入间隔内的输出相位。它与[原 HB-Lattice](hb-lattice.md)、[多跨度图的 Settle 绑定](hb-multiscale.md#4-端口与三种时间绑定)组成三个空间候选。三者均沿用当前 SettleGraph 的周期条件。

## 1. 层、节点与分区

取展开深度 $m\ge1$，总层数和每层位置数为

$$
M=3m+1,\qquad W_\ell=2^{\min(\ell,m,3m-\ell)},
\qquad 0\le\ell\le3m.
\tag{1}
$$

层 $m,\ldots,2m$ 等宽，提供 $m$ 轮最宽处的交换。每位置有 $n=2^q$ 个普通节点 $D_{\ell,p,i}$，$q\ge1$，$0\le p<W_\ell,0\le i<n$；它们组成一个区域。主候选没有 hub。可选增强在每位置增加 $h$ 个 hub $H_{\ell,p,a}$，$h\mid n$，另成一个区域。增强默认 $h=4$，普通图保持不变；本图不再引入其他角色或部分放置规则。

所有区域秩为 $r=\ell+1$；节点全序按 $(\ell,p,\mathrm{role},i)$，D 在 H 前。同位置 D 与 H 没有消息边。首层每个现存节点有一个入口，末层每个 D 有一个输出端口。

## 2. 普通节点的全部消息边

对层 $\ell\to\ell+1$，记

$$
\begin{aligned}
g_\ell&=\min(W_\ell,W_{\ell+1}),&
A_\ell&=W_\ell/g_\ell,& B_\ell&=W_{\ell+1}/g_\ell,\\
x&=\lfloor p/A_\ell\rfloor,& c_\ell&=\ell\bmod q.
\end{aligned}
\tag{2}
$$

粗组基础目标为 $\mathcal B^0_\ell(p)=\{B_\ell x+j:0\le j<B_\ell\}$。若 $g_\ell=1$，令 $\mathcal Q_\ell(p)=\mathcal B^0_\ell(p)$；若 $g_\ell>1$，令

$$
\begin{aligned}
b_\ell&=\ell\bmod\log_2 g_\ell,\\
\mathcal Q_\ell(p)&=\{B_\ell y+j:
 y\in\{x,x\mathbin{\mathrm{xor}}2^{b_\ell}\},\ 0\le j<B_\ell\}.
\end{aligned}
\tag{3}
$$

对每个源 $D_{\ell,p,i}$，放置全部笛卡尔积边

$$
D_{\ell,p,i}\longrightarrow D_{\ell+1,p',i'},\qquad
p'\in\mathcal Q_\ell(p),\quad
 i'\in\{i,i\mathbin{\mathrm{xor}}2^{c_\ell}\}.
\tag{4}
$$

面板将这一边族记作 DDX。端点去重，边身份由源与目标确定。等宽且宽度大于 1 时，每节点入度、出度都为 4；展开或收拢的相邻宽度比为 2，最大入度、出度均不超过 8。宽度为 1 时不计算模零的区域位。零位移边与粗组基础映射保证每节点都在某条入口至输出的路径上。

## 3. 交换能覆盖什么

在等宽 $W=2^m$ 段上，从起始层向后经过 $r$ 轮，设使用过的不同区域位有 $b$ 个、不同节点位有 $c$ 个。对每个目标 D，潜在前驱恰覆盖 $2^b$ 个源区域及 $2^{b+c}$ 个源节点。每轮可以分别选择翻转或不翻转两个位，因此所有已用位的子集都可出现；未用位保持，得到这两个计数。重复使用同一位不会继续增加该维度的覆盖。

式 (1) 的最宽段中，区域位依次为 $0,\ldots,m-1$，节点位按 $q$ 循环。因此最宽段结束时，每个 D 可接触该段入口全部 $2^m$ 个区域、各区的 $2^{\min(m,q)}$ 个节点。$W=8,n=16$ 的前三轮分别覆盖 2／4／8 个区域、4／16／64 个源节点；它仍没有覆盖全部 $8\times16$ 个节点。$W=16,n=16$ 的四轮则潜在覆盖全部 256 个源节点。

这是固定图的可达性。区域选择可删除实际传播，Agg 和状态会压缩内容，经过多个节点的处理也会改变内容；不能据此宣称每个节点最终拿到全部原始信息。扩宽后的分工、有效合作与重复加工仍是实验问题。XOR 远邻需要合适的设备放置，低图度数不保证物理近邻。

## 4. 可选 hub 的完整连线

令 $b=n/h$。沿用[多跨度图](hb-multiscale.md#3-每条消息边的端点)的固定种子和置换：$\rho_{\ell,p,p'}$ 为 collect，$\chi_{\ell+1,p'}$ 为 hook。只增加相邻层边：

| 边族 | 目标位置 | 端点编号 |
|---|---|---|
| DH1 | $p'\in\mathcal Q_\ell(p)$ | $D_i\to H_{\lfloor\rho_{\ell,p,p'}(i)/b\rfloor}$ |
| HH1 | $p'\in\mathcal Q_\ell(p)$ | $H_a\to H_{(a+\ell+p+p')\bmod h}$ |
| HD1 | $p'\in\mathcal B^0_\ell(p)$ | $H_a\to D_{\chi_{\ell+1,p'}(cb+\eta)}$ |

最后一行取 $c=(a+\ell+p+1)\bmod h$、$\eta=(7\ell+3p+p'+5)\bmod b$，每个 hub 对每个基础目标位置只发送一个探针。除此之外没有 hub 边。它让普通结果进入摘要，摘要在后续层交换并进入有限普通节点；所有边仍承载同一个 Full 广播值。删除所有 hub 及关联边精确恢复主普通图。

## 5. 时间、规模与求值

全部消息边时延为 $\delta=1=r_{\mathrm{dst}}-r_{\mathrm{src}}$。保持当前正典要求，取 $D=M+1>M$，输入日程 $\iota(t)=Dt+1$；节点对应时刻为 $\theta_{v,t}=Dt+r_v$。每条入口至节点的路径时延都为 $r_v-1$，所以同源消息对齐；每节点每输入位置至多一次作用。输入位置之间仍可通过节点记忆传递信息。

| 层数 | 宽度轮廓 | 位置数 | 无 hub 节点／边 | 加 4 hub 后节点／边 |
|---:|---|---:|---:|---:|
| 7 | 1,2,4,4,4,2,1 | 18 | 288 / 1152 | 360 / 1952 |
| 10 | 1,2,4,8,8,8,8,4,2,1 | 46 | 736 / 3200 | 920 / 5408 |
| 13 | 1,2,4,8,16,16,16,16,16,8,4,2,1 | 110 | 1760 / 7808 | 2200 / 13184 |

表中 $n=16$。无 hub 时 D 最大入出度为 8/8；增强图 D 为 9/12、H 为 20/6。$n=32,64$ 同样合法，节点位改按各自 $q$ 循环；固定 $h$ 时 DH 收集度随 $n/h$ 增长，须重新核对，不能沿用本表。

区域数为 $(1+\mathbf1[h>0])\sum_\ell W_\ell$。记 $Q_\ell=\sum_p|\mathcal Q_\ell(p)|$、$B_\ell^*=\sum_p|\mathcal B^0_\ell(p)|$，边数为

$$
|E|=\sum_{\ell=0}^{M-2}
 \left[2nQ_\ell+\mathbf1[h>0]\big((n+h)Q_\ell+hB_\ell^*\big)\right].
\tag{5}
$$

普通两端点、收集、hub 交换和探针分别贡献各项。参数 $h=0$ 时不求值 §4 中的 $n/h$。

[共同主绑定](../instances/hb-settle-weighted-message.md)给出状态和完整局部函数，可使用 Settle 的对齐求值，也满足严格区域分层整窗口定理的条件。[交互公式面板](../explorers/hb-timed/README.md)共用区域图、逐节点邻接和端点矩阵，并列三个 Settle 空间候选；[核对程序](../examples/hb_settle_checks.py)独立检查位覆盖、边数与时间绑定。
