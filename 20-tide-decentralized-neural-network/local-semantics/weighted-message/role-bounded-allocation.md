---
type: mathematical-learning-note
status: active
tags: [tide, local-semantics, regional-allocation]
---

# 带角色上下界的二次发送分配

本候选给部分节点保留有限发送份额，同时让其余份额按评分竞争。它扩展[区域分配](region-allocation-learning-note.md)的节点约束，不改变正典接口，也不修改既有发送函数。角色是固定的节点属性；节点只有实际收到输入才进入本次候选集，hub 标签不会自行产生输入。

## 1. 从接收到一次完整返回

沿用[共同架构](architecture-learning-note.md)的消息、聚合、Mem、当前特征和 Read。固定区域的一次候选集 $C$，取正温度 $\tau$、整数 $1\le k\le|\mathcal R_j|$，以及有限增益上界 $\gamma_{\max}\ge1$。每个候选计算

$$
w_v=\min(1,(r_v^{\mathrm{in}})_+),\qquad
\mu_v=\min(1,\gamma_v(r_v^{\mathrm{in}})_+),\qquad
1\le\gamma_v\le\gamma_{\max}.
$$

本篇首先固定增益，评分采用[拼接评分](region-allocation-learning-note.md#31-拼接评分)及独立区域评分。给定角色边界函数，Describe 返回

$$
d_v=(w_v,\mu_v,s_v^{\mathrm{loc}},\ell_v,u_v),\qquad
0\le\ell_v\le u_v\le\mu_v\le1.
\tag{1}
$$

这里 $u_v$ 是**发送上界**；与共同架构中同字母的聚合内容向量区分，后文不在同一公式中混用。描述空间是满足式 (1) 及 $w_v\le\mu_v\le\gamma_{\max}w_v$ 的元组空间。评分使用本次 Read 指定的状态。

普通节点取 $(\ell_v,u_v)=(0,\mu_v)$。Hub 有两种明确待遇：

$$
\begin{array}{ll}
\text{固定通过：}&\ell_h=u_h=\mu_h,\\
\text{有限保底：}&\ell_h=\beta_h\mu_h,\quad
 u_h=\min(\mu_h,\alpha_h k),\quad 0<\beta_h\le1,\quad\alpha_h>0.
\end{array}
\tag{2}
$$

$\alpha_h$ 表示预算份额，$\gamma_h$ 表示接收增益，二者不同。上述上界始终不超过 $\mu_h$。常亮在这里指**正接收时发送强度为正**，不指自主心跳。

只对实际 $C$ 求和。沿用节点增益候选的原总量下界 $b=\min(1,\sum_v\mu_v)$，定义

$$
U=\min(k,\sum_vu_v),\qquad
L=\max\left(\sum_v\ell_v,\min(b,U)\right).
\tag{3}
$$

要求 $\sum_v\ell_v\le U$。给定固定阈值 $\eta\in\mathbb R$，令 $t_v=s_v^{\mathrm{loc}}-\eta$，求

$$
c=\arg\max\left\{\sum_v t_vc_v-\frac\tau2\sum_vc_v^2:
 \ell_v\le c_v\le u_v,\quad L\le\sum_vc_v\le U\right\}.
\tag{4}
$$

返回 $\mathcal A=\{v\in C:c_v>0\}$ 及
$\operatorname{SelStep}_{j,C}(*,\theta,(d_v)_v)=(\mathcal A,(c_v)_v,*)$。
取 $Y_j=\{*\},K_j=|\mathcal R_j|$；$k$ 仍约束发送总和，不能作为激活节点数的上界。Full 与 Next 使用共同架构，全部候选保留接收更新。

例如，候选为一个 hub 和两个普通节点，上限 $\mu=(1,1,1)$，$k=2$，hub 取 $\beta=1/4,\alpha=1/2$。于是 $\ell=(1/4,0,0),u=(1,1,1),L=1,U=2$。取 $\tau=1,\eta=0,s=(-2,1,0.8)$，解为 $(0.25,0.975,0.775)$：hub 即使分数低仍发送，普通节点分享剩余强度。如果 hub 本次缺席，则只在两个普通候选上求解，得到 $(1,0.8)$；没有读取缺席 hub 的旧描述，也没有为它占用当前预算。

## 2. 可行性与两个可选接口

### 2.1 对所有合法输入保证可行

不能等遇到某组接收才发现保底超过预算。设区域中的固定通过 hub 集为 $H_f$、有限保底 hub 集为 $H_b$。一组便于配置的充分条件是

$$
|H_f|+\sum_{h\in H_b}\beta_h\le k,\qquad
\beta_h\le\alpha_h k\quad(h\in H_b).
\tag{5}
$$

因为 $0\le\mu_h\le1$，式 (5) 保证逐节点 $\ell\le u$ 及所有候选子集的 $\sum\ell\le k$。再由 $\sum\ell\le\sum u$ 得式 (3) 可行。更一般的边界函数可以使用更紧的证明，但须覆盖所有合法描述，不能依赖训练时通常不会触发冲突。

例如四 hub 独立成区，取 $k=2,\beta=1/4,\alpha=1/2$，满足式 (5)。四个固定通过 hub 则要求 $k\ge4$；这时四个控制均为 $\mu_h$，它们之间已没有分配权衡。单 hub 区取 $k=1$ 与固定通过，数值上就是既有 constrained 单候选的 $c_h=\mu_h$。

混合区取 $k=k_D+k_H$，hub 保底条件仍按该区完整 $k$ 检查。即使 $k$ 留有余量，也不能保证每次普通节点都得到份额：实际总量、当前候选和评分共同决定结果。若有额外的普通组最低份额要求，需要另定义组约束；本候选没有暗含这一要求。

### 2.2 共同评分与指定总量

式 (1) 可扩展为 $(w,\mu,x^{\mathrm{sel}},K^{\mathrm{sel}},s^{\mathrm{loc}},\ell,u)$。采用[区域 Attention 评分](region-allocation-learning-note.md#36-区域-attention-评分)，固定 query_weight=received，用 $w$ 汇集 query，并将所得 $s_v$ 代入式 (4)。普通与 hub 的 Mem 只需具有相同描述宽度，可以来自不同记忆。完整内容仍只通过消息传播。

还可固定 $\rho\in[0,1]$，取

$$B=L+\rho(U-L),\qquad \sum_v c_v=B,\tag{6}$$

替换式 (4) 的总量区间。若使用上下文头，则给描述增添[区域证据](region-allocation-learning-note.md#34-区域证据) $z_v^{\mathrm{reg}}$，按原教材以 $w$ 汇集，统计项用 $\sum w,\sum\mu$，取 $\rho=\sigma(H_j(f_j^{\mathrm{reg}}))$，其余式 (6) 保持。原下界也可明确选 $b=\min(1,\sum w)$；必须与所选描述、总量头一同记录。式 (3) 将旧下界截到可用容量，避免有限 hub 上界令原下界不可达。

主实例采用式 (4)、原下界 $\min(1,\sum\mu)$ 和固定阈值，不要求实现这组总量头。其他正则、角色约束下的硬选择均不由本篇自动定义。

## 3. 求解、唯一性与零边界

可行集非空、紧且凸，$\tau>0$ 时目标严格凹，故分配唯一。其标量响应是

$$
c_v(\lambda)=\operatorname{clip}((t_v-\lambda)/\tau,\ell_v,u_v),
\qquad S(\lambda)=\sum_vc_v(\lambda).
\tag{7}
$$

区间模式先算 $S(0)$：若在 $[L,U]$ 内则 $\lambda=0$；若超过 $U$，用 $\lambda\ge0$ 解 $S(\lambda)=U$；若低于 $L$，用 $\lambda\le0$ 解 $S(\lambda)=L$。指定总量模式直接解 $S(\lambda)=B$，不限制符号。$S$ 连续单调不增。可用断点 $t_v-\tau u_v,t_v-\tau\ell_v$ 扫描或二分；乘子可不唯一，但控制唯一。总量等于 $\sum\ell$ 或 $\sum u$ 时直接返回对应边界族。

空候选返回空族。全零接收强制 $\ell=u=0$；加入零接收候选不改变其他控制。对固定有限参数和正温度，连续的接收、边界及有效评分给出连续分配：平移 $x=c-\ell$ 后，可行集变为 $0\le x\le u-\ell$，总量上下界减去 $\sum\ell$，目标线性系数变为 $t-\tau\ell$；因此可直接应用[区域教材附录 A.1](region-allocation-learning-note.md#a1-约束解的连续性)的恢复列证明。弱接收坐标的 $c\le\mu\le\gamma_{\max}w$ 趋零，且它对 query／证据的贡献趋零；得到共同架构的零消息中性和有限时间连续性条件。

令所有节点 $\ell=0,u=\mu$，式 (3)—(4) 精确恢复 quad、constrained。角色保底下的零温解通常仍含小数控制，既有单位强度硬化结论不能直接挪用。

## 4. 光滑分支导数与边界约定

令 $F,A_-,A_+$ 分别为严格内部、严格下界、严格上界坐标，先消去固定坐标 $\ell=u$。在分支不变时，$dc_v=d\ell_v$ 于 $A_-$，$dc_v=du_v$ 于 $A_+$。内部坐标满足

$$dc_v=(dt_v-d\lambda-c_vd\tau)/\tau.\tag{8}$$

总和约束松弛时 $d\lambda=0$。总和固定在当前 $S_*=L,U$ 或 $B$ 且 $|F|>0$ 时，

$$
d\lambda=\frac{\sum_{F}(dt_v-c_vd\tau)
 +\tau(\sum_{A_-}d\ell_v+\sum_{A_+}du_v-dS_*)}{|F|}.
\tag{9}
$$

固定通过坐标先取 $dc_h=d\mu_h$，其微分加入式 (9) 的边界和。再沿式 (2)、(3)、评分和区域头应用链式法则；$S_*$ 不是无条件常数。式 (8)—(9) 给出完整的方向微分，也可转置实现反向。没有内部坐标的开分支上，各控制直接随相应边界变化；等式总量与边界同时自由扰动时须重新判定分支，不能除以零。

在 clip 断点、总量松紧交界、min/max 并列处，经典导数可能不存在。参考约定是：先消去固定通过坐标；min/max 并列取书写顺序中的第一分支；若 $S(0)$ 恰在区间边界先取松弛分支；clip 恰碰端点取边界分支。若等式约束分支因此没有内部坐标，返回该面上的边界微分，并声明只对保持该面的扰动有效。这是确定的训练约定，不宣称是所有方向的真实导数；需要任意方向的精确导数时，重新求相应方向的活动约束。前向解不受这些约定影响。

数值核对见[角色分配程序](../../examples/role_bounded_allocation_checks.py)：独立活动集求解、旧规则退化、零／缺席、可行性和光滑分支有限差分。

## 5. 配置对应

新增 selection_mode=role_bounded_quad，allocation_temperature=$\tau>0$，read_mode=+／-／0；local_score 与 region_score 复用原定义。bound_role=ordinary／pass／floor_cap 分别对应式 (2) 及普通边界，角色固定于节点。beta、alpha 只用于 floor_cap；固定通过不读取这两个参数。默认 total_mode=interval、lower_base=mu、send_gain=fixed、eta=$0$、query_weight=received。

扩展模式 total_mode=fraction 使用 total_fraction，或 region_control_mode=context 的证据与头；lower_base=received 使用 $\min(1,\sum w)$。本篇只定义 quad，正典容量始终取全区节点数。既有配置与默认值保持；新参数须显式绑定后才能称为本候选。
