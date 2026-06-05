# 笔记

## 信息论概念

### <span id=shannon-entropy>[**Shannon熵**](https://en.wikipedia.org/wiki/Entropy_(information_theory))</span>

$H(\pmb{X})$可用于描述随机变量$\pmb{X}$的不确定性，表示消息[随机变量$\pmb{X}$的一次观测值]带来的<font color=red>信息量</font>[[自信息](https://en.wikipedia.org/wiki/Information_content)$-\log_b(P(\pmb{X}))$，$P(\pmb{X})$越小代表信息量越大]的期望值，也可理解为针对概率分布$P(\pmb{X})$进行编码[参考[Huffman coding](https://en.wikipedia.org/wiki/Huffman_coding)、[Arithmetic coding](https://en.wikipedia.org/wiki/Arithmetic_coding)]的<font color=red>编码长度期望值</font>下限[参考[AI & 无损压缩科普博客](https://zhuanlan.zhihu.com/p/651212186)]
$$
\label{eq:shannon-entropy}
H(\pmb{X})=E(-\log_b(P(\pmb{X})))=-\sum_{\pmb{X}} P(\pmb{X})\log_b(P(\pmb{X})),
\tag{Shannon-Entropy}
$$
其中取$b=e$时，熵(信息量)单位为nat，取$b=2$时，熵(信息量)单位为bit。

### <span id=KL-divergence>[**相对熵, KL散度(Kullback-Leibler divergence)**](https://en.wikipedia.org/wiki/Kullback–Leibler_divergence)</span>

定义在同一集合$X$上的两个概率分布$P,Q$的相对熵即KL散度定义为
$$
\label{eq:relative-entropy}
D_{KL}(P\|Q)=-\int_XP(x)\log\frac{Q(x)}{P(x)}dx=-\sum_X P(X)\log\frac{Q(X)}{P(X)}
\tag{Relative-Entropy}
$$
KL散度具有非负性，等号成立当且仅当$P=Q$
$$
D_{KL}(P\|Q)\geq0,
$$
<font size=2>注：非负性[证明1]由$\ln x\leq x-1$可得$\sum P\ln(Q/P)\leq\sum P(Q/P-1)=0$。[证明2]由于$\log z$关于$z\in\mathbb{R}^+$是上凸函数，记$z_X=Q(X)/P(X)$，由[Jensen不等式](https://en.wikipedia.org/wiki/Jensen's_inequality)，不严格的推导可得$-D_{KL}(P\|Q)=\sum_XP(X)\log z_X\leq\log(\sum_XP(X)\cdot z_X)=\log\sum_XQ(X)=0$。</font>

但KL散度并不能作为概率分布之间的度量：它既不保证对称性[$D_{KL}(P\|Q)=D_{KL}(Q\|P)$]，也[不保证满足三角不等式](https://math.stackexchange.com/questions/2354584/substitute-for-triangle-inequality-for-kullback-leibler-divergence)[$D_{KL}(P\|Q)\leq D_{KL}(P\|R)+D_{KL}(R\|Q)$]。

[**Pinsker不等式(Pinsker's Inequality)**](https://en.wikipedia.org/wiki/Pinsker%27s_inequality) 指出[全变差距离](https://en.wikipedia.org/wiki/Total_variation_distance_of_probability_measures)具有由KL散度$\eqref{eq:relative-entropy}$表示的上界。对$X$上的两个概率测度$P,Q$，其全变差距离$\delta(P,Q)=\frac12\int_X|P(x)-Q(x)|dx=\int_{P(x)>Q(x)}[P(x)-Q(x)]dx=\int_{P(x)<Q(x)}[Q(x)-P(x)]dx$，与KL散度($b=e$, 熵单位nats)满足不等式
$$
\label{eq:pinsker-inequality}
\delta(P,Q)\leq \sqrt{\frac12D_{KL}(P\|Q)}
\tag{Pinsker's Inequality}
$$
不等式反向不一定成立，例如对任意$\varepsilon>0$，取$P_\varepsilon(0)=\varepsilon,P_\varepsilon(1)=1-\varepsilon,Q(0)=0,Q(1)=1$，则$\delta(P,Q)=\varepsilon$但$D_{KL}(P\|Q)=\infty$。可取仅与$Q$有关的常数$\alpha_Q$，例如$\alpha_Q=\min_{x\in X:Q(x)>0}Q(x)$，则能建立反方向的不等式
$$
\sqrt{\frac12D_{KL}(P\|Q)}\leq\frac1{\sqrt{\alpha_Q}}\delta(P,Q)
$$
<font size=2>注: $\eqref{eq:pinsker-inequality}$可证明如下(By [John Pollard](https://en.wikipedia.org/wiki/John_Pollard_(mathematician))), 记$r(x)=\frac{P(x)}{Q(x)}-1\geq-1$, 则$D_{KL}(P\|Q)=E_Q[(1+r(x))\ln(1+r(x))-r(x)]\geq\frac12E_Q\frac{r^2(x)}{1+r(x)/3}\geq\frac12\frac{E_Q^2(|r(x)|)}{E_Q(1+r(x)/3)}=2\delta^2(P,Q)$。</font>

### [交叉熵(Cross entropy)](https://en.wikipedia.org/wiki/Cross-entropy)

$H(P,Q)$表示<font color=red>基于一个“错误”概率分布</font>$Q$[相对于真实概率分布$P$]进行编码的编码位长度的期望值，
$$
\label{eq:cross-entropy}
\begin{split}
H(P,Q) &= E_{P}(-\log Q)=-\sum_{\pmb{X}}P(\pmb{X})\log(Q(\pmb{X})) \\
&= H(P)+D_{KL}(P\|Q)
\end{split}
\tag{Cross-Entropy}
$$
它是$P$本身的熵加上$P,Q$的相对熵，这说明，基于“正确”概率分布$Q=P$进行编码可得到最小编码长度期望值。

### 熵 & 信息

#### [条件熵(Conditional entropy)](https://en.wikipedia.org/wiki/Conditional_entropy)

继[定义了熵](#shannon-entropy)之后，还可两个随机变量$\pmb{X},\pmb{Y}$的条件熵，也就是<font color=red>假设已知</font>$\pmb{X}$<font color=red>时</font>$\pmb{Y}$<font color=red>的新增信息量</font>，定义为
$$
\label{eq:conditional-entropy}
\begin{split}
H(\pmb{Y}|\pmb{X}) &= H(\pmb{X},\pmb{Y})-H(\pmb{X}) \\
&= E_{x\sim P(\pmb{X})}H(\pmb{Y}|\pmb{X}=x)
\end{split}
\tag{Conditional-Entropy}
$$
其中$H(\pmb{X})=H(P(\pmb{X}))$，以及$H(\pmb{X},\pmb{Y})=H(P(\pmb{X},\pmb{Y}))$是联合熵。由于$H(\pmb{Y}|\pmb{X}=x)\geq0,\forall x$，因此根据上述公式的第二个等号有$H(\pmb{Y}|\pmb{X})\geq0$。进一步我们还可以定义多个随机变量的联合熵$H(\pmb{X},\pmb{Y},\pmb{Z},\cdots)=H(P(\pmb{X},\pmb{Y},\pmb{Z},\cdots))$。变量的联合熵满足链式关系
$$
H(\pmb{X}_1,\cdots,\pmb{X}_n)=\sum_{i=1}^nH(\pmb{X}_i|\pmb{X}_1,\cdots,\pmb{X}_{i-1})
$$
其中$H(\pmb{X}_i|\pmb{X}_1,\cdots,\pmb{X}_{i-1})$的更啰嗦但可减少误解的写法是$H\big(\pmb{X}_i|(\pmb{X}_1,\cdots,\pmb{X}_{i-1})\big)$，其中$\tilde{X}_{i-1}=(\pmb{X}_1,\cdots,\pmb{X}_{i-1})$表示联合随机变量。

等式$H(\pmb{X},\pmb{Y})=H(\pmb{X})+H(\pmb{Y}|\pmb{X})$的<font color=red>直观解读</font>为：联合随机变量$(\pmb{X},\pmb{Y})$的信息量$H(\pmb{X},\pmb{Y})$，也就是联合熵，等于$\pmb{X}$的信息量$H(\pmb{X})$+假设已知$\pmb{X}$时$\pmb{Y}$的新增信息量$H(\pmb{Y}|\pmb{X})$。

#### [互信息(Mutual information)](https://en.wikipedia.org/wiki/Mutual_information)与[条件互信息(Conditional mutual information)](https://en.wikipedia.org/wiki/Conditional_mutual_information)

两个随机变量$\pmb{X},\pmb{Y}$的互信息，也就是它们<font color=red>共享的信息量</font>，定义为
$$
\label{eq:mutual-information}
\begin{split}
I(\pmb{X};\pmb{Y}) &= H(\pmb{X})+H(\pmb{Y})-H(\pmb{X},\pmb{Y}) \\
&=H(\pmb{X},\pmb{Y})-H(\pmb{X}|\pmb{Y})-H(\pmb{X}|\pmb{Y})\\
&=H(\pmb{X})-H(\pmb{X}|\pmb{Y})=H(\pmb{Y})-H(\pmb{Y}|\pmb{X}) \\
&=D_{KL}(P(\pmb{X},\pmb{Y})\|P(\pmb{X})\cdot P(\pmb{Y}))=E_{\pmb{X},\pmb{Y}}\big(\log\frac{P(\pmb{X},\pmb{Y})}{P(\pmb{X})\cdot P(\pmb{Y})}\big) \\
\end{split}
\tag{Mutual-Information}
$$
当$\pmb{X},\pmb{Y}$相互独立即$P(\pmb{X},\pmb{Y})=P(\pmb{X})\cdot P(\pmb{Y})$时，其互信息达到最小值0。等式$H(\pmb{Y})=I(\pmb{X};\pmb{Y})+H(\pmb{Y}|\pmb{X})$的<font color=red>直观解读</font>为：$\pmb{Y}$的信息量$H(\pmb{Y})$，等于$\pmb{X},\pmb{Y}$的共享信息量$I(\pmb{X};\pmb{Y})$+假设已知$\pmb{X}$时$\pmb{Y}$的新增信息量$H(\pmb{Y}|\pmb{X})$。

条件互信息$I(\pmb{X};\pmb{Y}|\pmb{Z})$，也就是<font color=red>假设已知</font>$\pmb{Z}$<font color=red>时</font>$\pmb{X},\pmb{Y}$<font color=red>共享的信息量</font>，定义为
$$
\label{eq:conditional-mutual-information}
\begin{split}
I(\pmb{X};\pmb{Y}|\pmb{Z})&=H(\pmb{X}|\pmb{Z})+H(\pmb{Y}|\pmb{Z})-H(\pmb{X},\pmb{Y}|\pmb{Z})\\
&=H(\pmb{X}|\pmb{Z})-H(\pmb{X}|\pmb{Y},\pmb{Z})\\
&=E_{\pmb{z}\sim P(\pmb{Z})}I\big((\pmb{X}|\pmb{Z}=\pmb{z});(\pmb{Y}|\pmb{Z}=\pmb{z})\big)
\end{split}
\tag{Conditional-Mutual-Information}
$$

等式$H(\pmb{X}|\pmb{Z})=H(\pmb{X}|\pmb{Y},\pmb{Z})+I(\pmb{X};\pmb{Y}|\pmb{Z})$的<font color=red>直观解读</font>为：已知$\pmb{Z}$时$\pmb{X}$的新增信息量，等于已知$\pmb{Y},\pmb{Z}$时$\pmb{X}$的新增信息量+已知$\pmb{Z}$时$\pmb{X},\pmb{Y}$的共享信息量。

条件互信息满足如下的链式分解，有两种表述
$$
\label{eq:chain-rule-for-mutual-information}
\begin{split}
I(\pmb{X};\pmb{Y},\pmb{Z}) &= I(\pmb{X};\pmb{Z})+I(\pmb{X};\pmb{Y}|\pmb{Z})\\
&=I(\pmb{X};\pmb{Y})+I(\pmb{X};\pmb{Z}|\pmb{Y}) \\
I(\pmb{X};\pmb{Y}|\pmb{Z}) &= I(\pmb{X};\pmb{Y})-\big(I(\pmb{X};\pmb{Z})-I(\pmb{X};\pmb{Z}|\pmb{Y})\big)\\
&=I(\pmb{X};\pmb{Y})-\big(I(\pmb{Y};\pmb{Z})-I(\pmb{Y};\pmb{Z}|\pmb{X})\big)
\end{split}
\tag{Chain-Rule-for-Mutual-Information}
$$
只需使用条件熵与互信息之间的等式关系即可证明上述链式分解，其<font color=red>直观解读</font>（以第一个表述的第一个等号为例）为：$\pmb{X}$与联合随机变量$\pmb{Y},\pmb{Z}$的共享信息量，等于$\pmb{X}$与$\pmb{Z}$的共享信息量+已知$\pmb{Z}$时$\pmb{X}$与$\pmb{Y}$的共享信息量。

对于多个变量，可推广至定义[交互信息](https://en.wikipedia.org/wiki/Interaction_information)，及条件联合互信息
$$
\begin{split}
I(\pmb{X}_1;\cdots;\pmb{X}_{n+1})&=I(\pmb{X}_1;\cdots;\pmb{X}_{n})-I(\pmb{X}_1;\cdots;\pmb{X}_{n}|\pmb{X}_{n+1})\\
I(\pmb{X}_1;\cdots;\pmb{X}_n|\pmb{X}_{n+1})&=\sum_{i=1}^nH(\pmb{X}_i|\pmb{X}_{n+1})-H(\pmb{X}_1,\cdots,\pmb{X}_n|\pmb{X}_{n+1})\\
&=D_{KL}\bigg(P\big((\pmb{X}_1;\cdots;\pmb{X}_{n})|\pmb{X}_{n+1}\big)\|P(\pmb{X}_1|\pmb{X}_{n+1})\otimes\cdots\otimes P(\pmb{X}_n|\pmb{X}_{n+1})\bigg)\\
\end{split}
$$

#### 信息论基本公式与Venn图运算的一一对应关系

- 联合熵 v.s. 并集
  $$
  H(\pmb{X},\pmb{Y})\ v.s.\ A\cup B
  $$

- 条件熵 v.s. 差集
  $$
  H(\pmb{X}|\pmb{Y})=H(\pmb{X})-H(\pmb{Y})+H(\pmb{X},\pmb{Y})\ v.s.\ A/B=A-B+A\cup B
  $$
  
- 互信息 v.s. 交集
  $$
  \begin{split}
  I(\pmb{X};\pmb{Y})=H(\pmb{X})+H(\pmb{Y})-H(\pmb{X},\pmb{Y})\ &v.s. \ A\cap B=A+B-A\cup B\\
  I(\pmb{X};\pmb{Y}|\pmb{Z})=H(\pmb{X}|\pmb{Z})+H(\pmb{Y}|\pmb{Z})-H(\pmb{X},\pmb{Y}|\pmb{Z})\ &v.s.\ (A\cap B)/ C=A/C+B/C-(A\cup B)/C
  \end{split}
  $$

与Venn图的代数结构略有区别的是，信息论中通常不讨论补运算。但基于上述对应关系，仍然可以大大帮助我们理解和推导信息论中的基本运算，基于上述对应关系中的公式，可以得到$\eqref{eq:mutual-information},\eqref{eq:conditional-mutual-information},\eqref{eq:chain-rule-for-mutual-information}$中的剩下所有运算关系，并对应其<font color=red>直观解读</font>。

<font size=2>需注意，两个随机变量的互信息$I(\pmb{X};\pmb{Y})$或关于第三个变量的条件互信息$I(\pmb{X};\pmb{Y}|\pmb{Z})$，按照定义$I(\pmb{X};\pmb{Y})=H(\pmb{X})+H(\pmb{Y})-H(\pmb{X},\pmb{Y})$,$H(\pmb{X}|\pmb{Z})+H(\pmb{Y}|\pmb{Z})-H(\pmb{X},\pmb{Y}|\pmb{Z})$可解读为Venn图，但对于多个随机变量时的交互信息不再能如此解读。事实上，互信息、条件联合互信息、交互信息与Venn图的联系，是通过熵、联合熵、条件熵来建立，转化之后即可使用Venn图的运算法则和理解。</font>

### [JS 散度(Jensen–Shannon divergence)](https://en.wikipedia.org/wiki/Jensen–Shannon_divergence)

是KL散度的变种，定义如下
$$
\label{eq:js-divergence}
\begin{split}
D_{JS}(P\|Q) &= \frac12D_{KL}(P\|M)+\frac12D_{KL}(Q\|M) \\
 &= H(M)-\frac{H(P)+H(Q)}2,\text{ where } M=\frac{P+Q}2 \\
\end{split}
\tag{JS-Divergence}
$$
JS散度开根号后可作为概率分布之间的度量：

1. 非负性：$\sqrt{D_{JS}(P\|Q)}$显然满足;
2. 对称性：$\sqrt{D_{JS}(P\|Q)}=\sqrt{D_{JS}(Q\|P)}$;
3. 三角不等式：$\sqrt{D_{JS}(P\|Q)}\leq\sqrt{D_{JS}(P\|R)}+\sqrt{D_{JS}(R\|Q)}$。
   <font size=2>注：可先证明$L:\mathbb{R}^+\times\mathbb{R}^+\to\mathbb{R}^+, L(p,q)=p\ln\frac{2p}{p+q}+q\ln\frac{2q}{p+q}$满足$\sqrt{L(p,q)}\leq\sqrt{L(p,r)}+\sqrt{L(r,q)}$，再结合Minkowski不等式，即可证明该性质。参考[Endres, Dominik Maria, and Johannes E. Schindelin. "A new metric for probability distributions." *IEEE Transactions on Information theory* 49.7 (2003): 1858-1860.](https://research-repository.st-andrews.ac.uk/bitstream/handle/10023/1591/Endres2003-IEEETransInfTheory49-NewMetric.pdf;jsessionid=7EA22DA7E50A8672DC247B1AAEFC62F2?sequence=1)</font>

更一般的，可用JS散度同时比较多个概率分布之间的相似性
$$
\begin{split}
D_{JS}^{\pi_1,\cdots,\pi_n}(P_1,\cdots,P_n) &= \sum_iD_{KL}(P_i\|M) \\
&= H(M)-\sum_i\pi_iH(P_i)
\end{split}
$$
$D_{JS}(P\|Q)$是上述一般定义的特殊情况$D_{JS}(P\|Q)=D_{JS}^{1/2,1/2}(P,Q)$。

<font size=2>注：JS散度可作为全变分度量的下界，若其对数基底使用$b=2$，则$D_{JS}(P\|Q)\leq\|P-Q\|_{l_1}\leq1$，一般的有$D_{JS}(P_1,\cdots,P_n)\leq\log_2n$，对于其他基底，将不等式右边改成$\log_bn$即可。</font>

*梯度消失问题*：需注意，当$P,Q$没有重叠部分时，JS散度为常数$D_{JS}(P\|Q)=\log2$，这意味着基于JS散度，固定$P$希望更新$Q$将不能获得有效梯度。

### [Bregman 散度(Bregman divergence)](https://en.wikipedia.org/wiki/Bregman_divergence)

也叫Bregman距离，通过一个[严格凸函数(Strictly convex function)](https://en.wikipedia.org/wiki/Convex_function)来定义。假设$F:\Omega\to\mathbb{R}$是一个连续可微的严格凸函数，则由生成函数$F$所定义的点$\pmb{p},\pmb{q}$之间的Bregman距离为
$$
D_F(\pmb{p},\pmb{q})=F(\pmb{p})-F(\pmb{q})-<\nabla_{\pmb{q}}F(\pmb{q}),\pmb{p}-\pmb{q}>\left(\approx (\pmb{p}-\pmb{q})^T\cdot\nabla^2_{\pmb{q}}F(\pmb{q})\cdot(\pmb{p}-\pmb{q})\text{ when }\pmb{p}\approx\pmb{q}\right)
$$
则$D_F(\pmb{p},\pmb{q})\geq0$，且由$F$的严格凸性，等号成立当且仅当$\pmb{p}=\pmb{q}$。

1. 使得$D_F$满足度量的对称性的唯一可能是$F$是正定二次型，这时$\sqrt{D_F}$就是仿射变换下的欧氏度量。
2. 取$F$为负[熵](#shannon-entropy)函数$F(\pmb{p})=\sum_ip_i\ln p_i$，此时Bregman散度$D_F$就是广义的[KL散度](#KL-divergence)，$D_F(\pmb{p},\pmb{q})=\sum_{i}p_i\ln\frac{p_i}{q_i}-\sum_ip_i+\sum_iq_i$，当$\pmb{p},\pmb{q}$表示离散概率，于是$\sum_ip_i=\sum_iq_i=1$时，$D_F$就是通常意义的KL散度。
3. 取$F(\pmb{p})=-\sum_i\ln p_i$，此时Bregman散度$D_F$是[Itakura–Saito距离](https://en.wikipedia.org/wiki/Itakura–Saito_distance)，$D_F(\pmb{p},\pmb{q})=\sum_i(\frac{p_i}{q_i}-\ln\frac{p_i}{q_i}-1)$。

### [Fisher 信息(Fisher information)](https://en.wikipedia.org/wiki/Fisher_information)

#### 标量参数$\theta$

Fisher信息 $\mathcal{I}_{X}(\theta)$是衡量观测所得的随机变量$X$携带的关于未知参数$\theta$的信息量，其中$X$的概率分布依赖于参数$\theta$。对于标量参数$\theta\in\mathbb{R}$，Fisher信息量为
$$
\mathcal{I}_X(\theta)=E\left[\big(\frac{\partial\mathcal{L}}{\partial\theta}\big)^2|\theta\right]=-E\left[\frac{\partial^2\mathcal{L}}{\partial\theta^2}|\theta\right]
$$
其中，$\mathcal{L}$是$X$关于参数$\theta$的[对数似然函数](https://en.wikipedia.org/wiki/Likelihood_function#Log-likelihood)，当$X$的概率密度函数$P(X;\theta)$已知时即为$\mathcal{L}(X;\theta)=\ln P(X;\theta)$。基于上述定义的公式，可自然推广到$\pmb{X}$表示$n$个独立同分布的$X$的情形$\pmb{X}=[X_1,\cdots,X_n]$，$\mathcal{I}_{\pmb{X}}(\theta)=n\mathcal{I}_X(\theta)$。

<font size=2>注：上述定义中第2项与第3项的恒等性，可基于$E\left[\frac{\partial\ln P(X;\theta)}{\partial\theta}|\theta\right]=\partial_\theta \int P\mathrm{d}X=\partial_\theta1=0$，以及$E\left[\frac{\partial_\theta^2P(X;\theta)}{P(X;\theta)}|\theta\right]=\partial_\theta^2\int P\mathrm{d}X=\partial_\theta^21=0$来化简证明。</font>

Fisher信息量可从下面的两个角度进行定量且直观的理解：

1. 它表示了无偏估计$\theta$的精度下界，即[Cramér–Rao不等式(CRLB)](https://en.wikipedia.org/wiki/Cramér–Rao_bound)，任何一个无偏估计公式/方法$\hat{\theta}(X)$，其估计方差满足
   $$
   Var(\hat{\theta}(X))\geq\frac1{\mathcal{I}_X(\theta)}
   \tag{Cramér–Rao Inequality}
   $$
   等号成立的等价条件是存在函数$a,g$使得$\partial_\theta\mathcal{L}=\mathcal{I}_X(\theta)\cdot[\hat{\theta}(X)-\theta]$，这限定了只有少数分布类型可以达成等号成立。例如，[1]对于正态分布$X\sim N(\mu,\sigma^2)$，取无偏估计量$\hat{\theta}(\pmb{X})=\frac1n\sum_{i=1}^nX_i$，$\partial_\theta\mathcal{L}=\frac{n}{\sigma^2}(\hat{\theta}-\mu)$；[2]对于伯努利分布，$P(X=1)=\theta,P(X=0)=1-\theta$，无偏估计量$\hat{\theta}(\pmb{X})=\frac1n\sum_{i=1}^nX_i$，$\partial_\theta\mathcal{L}=\frac{n}{p(1-p)}(\hat{\theta}-p)$。

   <font size=2>Cramér–Rao不等式的证明：事实上，由无偏条件有$\int(\hat{\theta}-\theta)P(X;\theta)\mathrm{d}X=0$，于是$0=\frac{\partial}{\partial\theta}\int(\hat{\theta}-\theta)P\mathrm{d}X=-\int P\mathrm{d}X+\int(\hat{\theta}-\theta)\frac{\partial P}{\partial\theta}\mathrm{d}X$，因此$\int(\hat{\theta}-\theta)\frac{\partial P}{\partial\theta}\mathrm{d}X=1$。进一步，由[Cauchy–Schwarz不等式](https://en.wikipedia.org/wiki/Cauchy–Schwarz_inequality)，$Var(\hat{\theta}(X))\cdot\mathcal{I}_X(\theta)=\left[\int(\hat{\theta}(X)-\theta)^2P(X;\theta)\mathrm{d}X\right]\cdot\left[\int\big(\frac{\partial_\theta P}{P}\big)^2P(X;\theta)\mathrm{d}X\right]\geq\big(\int(\hat{\theta}-\theta)\frac{\partial P}{\partial\theta}\mathrm{d}X\big)^2=1$，也就是$Var(\hat{\theta}(X))\geq\frac1{\mathcal{I}_X(\theta)}$。</font>

2. 给定$X$观测值区分$\theta$与$\theta+\delta\theta$，其敏感度可通过两个分布$P(X;\theta),P(X;\theta+\delta\theta)$之间的距离来度量，
   $$
   D_{KL}\big(P(X;\theta)\|P(X;\theta+\delta\theta)\big)\approx\delta\theta^2\cdot I_X(\theta)
   $$
   <font size=2>注：对$D_{KL}\big(P(X;\theta)\|P(X;\theta+\delta\theta)\big)$沿$\theta$维度进行Taylor展开，则$D_{KL}= -\int P(X;\theta)\ln\frac{P(X;\theta+\delta\theta)}{P(X;\theta)}\mathrm{d}X
   \approx -\delta\theta\cdot\int P\partial_\theta\mathcal{L}\mathrm{d}X-\frac12\delta\theta^2\cdot\int P\partial_\theta^2\mathcal{L}\mathrm{d}X=-\delta\theta\cdot(\cdots)+\frac12\delta\theta^2\cdot I_X(\theta)$，而$\int P(X;\theta)\partial_\theta\mathcal{L}(X;\theta)\mathrm{d}X=\int \partial_\theta P(X;\theta)\mathrm{d}X=\partial_\theta\int P\mathrm{d}X=\partial_\theta1=0$，即一阶项为0。所以$D_{KL}\big(P(X;\theta)\|P(X;\theta+\delta\theta)\big)=\frac12\delta\theta^2\cdot I_X(\theta)$。</font>

<font size=2>注：纯直观的讲，</font>

1. <font size=2>记得分函数为$S(X;\theta)=\frac{\partial\mathcal{L}}{\partial\theta}$，它意味着给定观测值$X$应该如何调整参数的更新方向。[1]在最大似然估计点$\hat{\theta}$处的得分为0；[2]给定$\theta$，对观测值$X$求得分函数的期望为$E(S(X;\theta)|\theta)=0$；[3]给定观测值$X$，$S(X;\theta)$代表该观测值推动调整参数$\theta$的力度和方向。因此给定$\theta$，如果$S(X;\theta)$方差值也就是Fisher信息量$\mathcal{I}(\theta)=E\left[S(X;\theta)^2|\theta\right]$越大，意味着，此时观测值更可能提供越多关于$\theta$的信息。</font>
2. <font size=2>$\mathcal{I}(\theta)=-E\left[\frac{\partial^2\mathcal{L}}{\partial\theta^2}|\theta\right]$与对数似然函数[图](https://en.wikipedia.org/wiki/Graph_of_a_function)（此时也叫支撑曲线）的曲率相关。曲率越大，意味着图在此处越尖锐，意味着极大似然函数越容易形成尖峰，即此处的$\theta$对观测数据敏感度较高。</font>

#### 向量参数$\theta$

对于向量参数$\pmb{\theta}\in\mathbb{R}^N$，对应[Fisher信息矩阵](https://en.wikipedia.org/wiki/Fisher_information#Matrix_form)$\pmb{\mathcal{I}}_X(\pmb{\theta})\in\mathbb{R}^{N\times N}$，其各元素为
$$
\mathcal{I}_{X,ij}(\pmb{\theta})=E\left[\big(\partial_{\theta_i}\ln P(X;\pmb{\theta})\big)\big(\partial_{\theta_j}\ln P(X;\pmb{\theta})\big)|\pmb{\theta}\right]=-E\left[\partial_{\theta_i\theta_j}\ln P(X;\pmb{\theta})|\pmb{\theta}\right]
$$
$\pmb{\mathcal{I}}_X(\pmb{\theta})$是一个半正定矩阵，且成立矩阵形式的[Cramér–Rao不等式(CRLB)](https://en.wikipedia.org/wiki/Cramér–Rao_bound)，
$$
\pmb{Cov}(\hat{\theta})\succsim\pmb{\mathcal{I}}_X(\pmb{\theta})^{-1}
$$
也就是$\pmb{Cov}(\hat{\theta})-\pmb{\mathcal{I}}_X(\pmb{\theta})^{-1}$是半正定矩阵。标量情形的KL散度度量关系也同样成立，
$$
D_{KL}\big(P(X;\pmb{\theta})\|P(X;\pmb{\theta}+\delta\pmb{\theta})\big)\approx\frac12\delta\pmb{\theta}^T\cdot\pmb{\mathcal{I}}\cdot\delta\pmb{\theta}
$$
Fisher信息矩阵的上述半正定性及其与KL散度的联系，为其提供了在信息几何领域中的基础作用。

### [数据处理不等式(Data processing inequality, DPI)](https://en.wikipedia.org/wiki/Data_processing_inequality)

其基本直觉是，数据处理之后，不会新增信息，这一直觉的具体数学表述是数据处理不等式。考虑三个随机变量，$\pmb{X},\pmb{Y},\pmb{Z}$，其中$\pmb{X},\pmb{Z}$是关于给定$\pmb{Y}$条件独立的，即$P(\pmb{Z}|\pmb{Y})=P(\pmb{Z}|\pmb{X},\pmb{Y}),P(\pmb{X}|\pmb{Y})=P(\pmb{X}|\pmb{Z},\pmb{Y}),P(\pmb{X},\pmb{Y},\pmb{Z})=P(\pmb{X}|\pmb{Y})P(\pmb{Z}|\pmb{Y})P(\pmb{Y})$，记作$(\pmb{X}\perp\!\!\!\perp\pmb{Z}|\pmb{Y})$，则无法从$\pmb{Z}$中获得比$\pmb{Y}$更多的关于$\pmb{X}$的信息，数据处理不等式即如下互信息$\eqref{eq:mutual-information}$不等式
$$
\label{eq:dpi}
I(\pmb{X};\pmb{Y})\geq I(\pmb{X};\pmb{Z})
\tag{Data-Processing-Inequality}
$$
例如这三个随机变量构成Markov链$\pmb{X}\to\pmb{Y}\to\pmb{Z}$时就满足条件独立性，此时比如$\pmb{Y}$是$\pmb{X}$的某种观测，而$\pmb{Z}$的值取决于中介$\pmb{Y}$。

<font size=2>事实上，按照条件独立性，可知$I(\pmb{X};\pmb{Z}|\pmb{Y})=0$，又由互信息的链式关系$I(\pmb{X};\pmb{Y},\pmb{Z})=I(\pmb{X};\pmb{Y})+I(\pmb{X};\pmb{Z}|\pmb{Y})=I(\pmb{X};\pmb{Z})+I(\pmb{X};\pmb{Y}|\pmb{Z})$可知$I(\pmb{X};\pmb{Y})=I(\pmb{X};\pmb{Z})+I(\pmb{X};\pmb{Y}|\pmb{Z})$，由$I(\pmb{X};\pmb{Y}|\pmb{Z})\geq0$可证明上述不等式。</font>

### 其他

[Tsallis熵](https://en.wikipedia.org/wiki/Tsallis_entropy) 给定概率分布$P$，其Tsallis熵定义为
$$
\label{eq:tsallis-entropy}
S_q(P)=k\cdot\frac{1}{q-1}\big(1-\sum_i p_i^q\big)
\tag{Tsallis-Entropy}
$$
其中$k$是常数，$q\geq1$是熵指数(entropic-index)，取$k$为Boltzmann常数$k=k_B$，$S_1(P)$即Boltzmann-Gibbs熵，
$$
S_{BG}(P)=S_1(P)\triangleq\lim_{q\to1^+}S_q(P)=-k\sum_ip_i\ln p_i
$$
[**Wasserstein度量(Wasserstein metric)**](https://en.wikipedia.org/wiki/Wasserstein_metric) $W_p(P,Q)$的直观物理含义是“将按照$P$分布的沙堆搬运成按照$Q$分布的最小代价”。前面提到，使用JS散度用于度量两个概率分布$P,Q$的距离，若$P,Q$没有重合的部分，则会有梯度消失的问题。Wasserstein度量$W_p(P,Q)$可解决此问题
$$
\label{eq:wasserstein-metric}
W_p(P,Q)=\big(\inf_{\gamma\in\Gamma(P,Q)}E_{(\pmb{x},\pmb{y})\sim\gamma}d(\pmb{x},\pmb{y})^p\big)^{\frac1p},
\tag{Wasserstein-Metric}
$$
其中$\Gamma(P,Q)$表示边缘分布分别为$P,Q$的$(\pmb{x},\pmb{y})$的联合分布的集合
$$
\int_{\pmb{y}}\gamma(\pmb{x},\pmb{y})\mathrm{d}\pmb{y}=P(\pmb{x}),\int_{\pmb{x}}\gamma(\pmb{x},\pmb{y})\mathrm{d}\pmb{x}=Q(\pmb{y}),\ \forall\gamma\in\Gamma(P,Q).
$$
对于$p=1$的情形，可特别关注，借助对定义$W_p(P,Q)$的线性规划问题取对偶，可导出*Kantorovich duality theorem*
$$
\label{eq:kantorovich-duality}
\begin{split}
W_1(P,Q)&=\sup_{\|f\|_L\leq1} \int f(\pmb{x})(P(\pmb{x})-Q(\pmb{x}))\mathrm{d}\pmb{x} \\
&= \sup_{\|f\|_L\leq1}E_{\pmb{x}\sim P}f(\pmb{x})-E_{\pmb{y}\sim Q}f(\pmb{y})
\end{split}
\tag{Kantorovich-Duality}
$$
其中$\|\cdot\|_L$表示Lipschits范数，该形式正是[Wasserstein GAN](https://en.wikipedia.org/wiki/Wasserstein_GAN)所借助的形式。

值得一提的是，对于一维情形，$W_1$可通过概率密度函数(PDF)$P,Q$的累积分布函数(CDF)直接计算(参考[scipy.stats.wasserstein_distance — SciPy Manual](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wasserstein_distance.html)及[1509.02237 (arxiv.org)](https://arxiv.org/pdf/1509.02237.pdf))
$$
\label{eq:w1-calculate}
W_1(P,Q)=\int_{-\infty}^{\infty}|P(\pmb{X}<x)-Q(\pmb{X}<x)|\mathrm{d}x.
\tag{W1-Calculate}
$$
[Radon变换](https://en.wikipedia.org/wiki/Radon_transform) 定义在超平面的表征$(\pmb{\alpha},s)$上，被广泛应用于X射线断层扫描。$d$维函数$f:\mathbb{R}^d\to\mathbb{R}$的Radon变换定义为
$$
\label{eq:radon-transform}
\mathscr{R}f(\pmb{\alpha},s)=\int_{\pmb{x}\cdot\pmb{\alpha}=s}f(\pmb{x})\mathrm{d}\sigma(\pmb{x})
\tag{Radon-Transform}
$$
其中$\pmb{\alpha}\in\mathbb{S}^{d-1},s\in\mathbb{R}$，$\sigma(\pmb{x})$是超平面$\sum^{(\pmb{\alpha},s)}_n=\pmb{x}\cdot\pmb{\alpha}=s$上的自然测度。对于$d=2$的情形，可用方向角度$\theta$代替二维单位向量$\pmb{\alpha}$讨论。

[Sliced Wasserstein Distance](https://link.springer.com/article/10.1007/s10851-014-0506-3) 借助Radon变换定义为
$$
\label{eq:sw-distance}
SW_p(P,Q)=\big[\int_{\pmb{\alpha}\in\mathrm{S}^{d-1}}W_p^p\big(\mathscr{R}P(\pmb{\alpha},\cdot),\mathscr{R}Q(\pmb{\alpha},\cdot)\big)\mathrm{d}S\big]^{\frac1p}, \mathrm{d}S=|\mathrm{d}\pmb{S}|
\tag{SW-Distance}
$$
其中一维Wasserstein距离按照前面讨论，可借助累积分布函数计算。

高维概率测度的随机切片可能会导致距离被低估(例如考虑两个单位协方差矩阵的高斯概率密度函数，参考[Wasserstein distance相关阅读笔记](https://zhuanlan.zhihu.com/p/351752536))，可定义Max-Sliced Wasserstein Distance解决此问题
$$
\label{eq:max-sw-distance}
maxSW_p(P,Q)=\max_{\pmb{\alpha}\in\mathbb{S}^{d-1}}W_p\big(\mathscr{R}P(\pmb{\alpha},\cdot),\mathscr{R}Q(\pmb{\alpha},\cdot)\big)
\tag{Max-SW-Distance}
$$

[Hamming距离](https://en.wikipedia.org/wiki/Hamming_distance) 表示两个等长字符串对应位置不相等的字符数，也可用于二进制数的距离度量。

## [四元数与3D旋转](https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation)

### [3D旋转矩阵](https://en.wikipedia.org/wiki/Rotation_matrix#Rotation_matrix_from_axis_and_angle)

依据[Mozzi-Chasles定理](https://en.wikipedia.org/wiki/Chasles'_theorem_(kinematics))，3维刚体运动可表示为"平移+单轴旋转"，这一定理的直接推论是，绕一点的多次单轴旋转可以合并为一次单轴旋转。对于旋转的这个论断，可以基于立体几何推导得到，也可从线性代数的结论直接得到。

<font size=2>注：[1]原点位置不随旋转发生变化，考虑$x,y$方向的单位向量$\pmb{i},\pmb{j}$向量及旋转后的终点状态$\tilde{\pmb{i}},\tilde{\pmb{j}}$，画垂直平分面，将得到一条经过原点的交线，即为合并旋转轴；[2]旋转变换对应$\mathbb{R}^{3\times3}$中行列式为1的正交矩阵，必有一个实数根为1，旋转轴为对应特征向量。</font>

可以直接从立体几何推导，3维空间绕旋转轴$\pmb{n}\in S^2$旋转角度$\theta\in\mathbb{R}$的线性变换可表示为
$$
\label{eq:3d-rotation-matrix}
\pmb{A}=(\cos\theta)I+(\sin\theta)[\pmb{n}]_\times+(1-\cos\theta)(\pmb{n}\otimes\pmb{n})
\tag{3D-Rotation-Matrix}
$$
其中$[\pmb{n}]_\times$表示$\pmb{n}$的[叉积矩阵](https://en.wikipedia.org/wiki/Cross_product#Conversion_to_matrix_multiplication)，$\pmb{n}\otimes\pmb{n}$表示外积，$I$是单位矩阵。用$\varepsilon_{jkl}$表示[Levi-Civita符号](https://en.wikipedia.org/wiki/Levi-Civita_symbol)($\varepsilon_{123}=1$)，该线性变换对应的矩阵元素值为
$$
R_{jk}=\left\{\begin{array}{ll}
\cos^2\frac\theta2+\sin^2\frac\theta2(2n_j^2-1), & \text{if }j=k\\
2n_jn_k\sin^2\frac\theta2=\varepsilon_{jkl}n_l\sin\theta, & \text{if }j\neq k
\end{array}\right.
$$


### [四元数(Quaternion)](https://en.wikipedia.org/wiki/Quaternion)

类似于复数的虚数单位$\pmb{i}^2=-1$，可定义三个虚数单位$\pmb{i},\pmb{j},\pmb{k}$，满足如下性质
$$
\begin{array}{l}
\pmb{i}^2=\pmb{j}^2=\pmb{k}^2=\pmb{ijk}=-1.\\
\pmb{ij}=\pmb{k},\pmb{ji}=-\pmb{k};\\
\pmb{jk}=\pmb{i},\pmb{kj}=-\pmb{i};\\
\pmb{ki}=\pmb{j},\pmb{ik}=-\pmb{j}.
\end{array}
$$
四元数集合记作$\mathbb{H}=\{h=a+\pmb{u}\triangleq a+b\pmb{i}+c\pmb{j}+d\pmb{k},\text{where }\pmb{u}=b\pmb{i}+c\pmb{j}+d\pmb{k}: \forall a,b,c,d\in\mathbb{R}\}$，这里$a,\pmb{u}$分别称作四元数$h$的标量部分和向量部分，也称作标量四元数、向量四元数。可依据普通的加法及乘法分配率定义四元数的**加法、乘法**，用标量向量表示四元数$p=a+\pmb{u},q=t+\pmb{v}$的加法乘法法则为，
$$
\begin{split}
p+q&=(a+t)+(\pmb{u}+\pmb{v})\\
pq&=(at-\pmb{u}\cdot\pmb{v})+a\pmb{v}+b\pmb{u}+\pmb{u}\times\pmb{v},(\text{注意到} \pmb{uv}=\pmb{u}\times\pmb{v}-\pmb{u}\cdot\pmb{v})
\end{split}
$$
从上式可看出四元数的乘法不满足交换律，其本质原因来自向量叉积的不可交换。

此外，对于四元数$h=a+b\pmb{i}+c\pmb{j}+d\pmb{k}=a+\pmb{u}$，可定义其**共轭**$h^*$，**绝对值**$|h|$，**乘法逆**$h^{-1}$，
$$
\begin{split}
h^*&=a-b\pmb{i}-c\pmb{j}-d\pmb{k}=a-\pmb{v},\\
|h|&=\sqrt{h\cdot h^*}=\sqrt{h^*\cdot h}=\sqrt{a^2+b^2+c^2+d^2},\\
h^{-1}&=\frac{h^*}{|h|^2}.
\end{split}
$$
容易证明，对于任两个四元数$p,q$都有$|pq|=|p||q|$。

进一步，记四元数$h=a+\pmb{u}=a+\pmb{n}|\pmb{u}|=|h|(\cos\varphi+\pmb{n}\sin\varphi)$，容易证明单位向量四元数$\pmb{n}$满足$\pmb{n}^2=-1$，也可作为虚数单位，于是可推导四元数$h$的**指数**$e^h$，**对数**$\ln(h)$，及其**指数表示**，
$$
\begin{split}
e^h&=\sum_{l=0}^\infty\frac{h^l}{l!}=e^a(\cos|\pmb{u}|+\pmb{n}\sin|\pmb{u}|),\\
\ln(h)&=\ln|h|+\pmb{n}\varphi,\\
h&=|h|e^{\varphi\pmb{n}}=|h|(\cos\varphi+\pmb{n}\sin\varphi).
\end{split}
$$

### 四元数与3D旋转的联系

一方面，给定旋转轴及旋转角$\pmb{n}\in S^2,\theta\in\mathbb{R}$，由$\eqref{eq:3d-rotation-matrix}$可得旋转所对应的线性变换$\pmb{A}$；

另一方面，令四元数$q=e^{\frac\theta2\pmb{n}}=\cos\frac\theta2+\pmb{n}\sin\frac\theta2$，注意到对任意的向量四元数$\pmb{a},\pmb{b}$，有$\pmb{ab}=\pmb{a}\times\pmb{b}-\pmb{a}\cdot\pmb{b}$以及$\pmb{a}\times(\pmb{b}\times\pmb{c})=\pmb{b}(\pmb{a}\cdot\pmb{c})-\pmb{c}(\pmb{a}\cdot\pmb{b})$，容易证明对向量四元数$\pmb{u}$的线性变换
$$
L^q[\mathbb{R}^3\to\mathbb{H}]:L^q(\pmb{u})=q\pmb{u}q^{-1}
$$


实际上可表示为
$$
\label{eq:quaternion-and-3d-rotaion}
L(q)\pmb{u}=0+\pmb{Au},
\tag{Quaternion-And-3D-Rotation}
$$
这是四元数与3D旋转变换之间的直接联系。





其他

Graph-based Clustering, Spectral Clustering, Graph Laplacian, Minimum Spanning Tree(edge length distribution), Locality Sensetive Hashing(LSH), Vector Indexing, Hierarchical Navigable Small World Graphs, Inverted File Indexes, PageRank

Linear Transformer/Mamba/RWKV/Delta Rule, MHA/GQA/MQA/MLA

