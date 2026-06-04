# 历史动机：AI 的时间 Scaling Law 理论佐证

> 这是从 `llm-notes` 迁移的早期历史动机材料。它保留原始论证脉络，不代表当前收缩后的执行主线；当前结论见 [[../当前主线总览|当前主线总览]]。

来源：`/home/zlong/llm/llm-notes/content/thesis/AI的时间 Scaling Law 的一些理论佐证.md`

---
这篇文档的起点，是来自北京大学[王立威](http://www.liweiwang-pku.com/)老师的一次理论工作报告。报告内容介绍了如何基于电路复杂性理论，来理解纯[System1](https://clouddocs.huawei.com/wapp/public/f577d929-9414-47f4-b2d2-bca672e805d0)工作模式的限制，以及为何System1+CoT\[7\]（Chain of Thought）比直接输出答案更强大\[4\]。

# 1. 电路复杂性理论视角：为何CoT可以提升System1能力？

## 1.1. 直观理解

我们首先对这一系列相关工作\[3,4,5,6\]的主要思想给一个简化的阐述：如果一个待求解问题，其求解过程包含较长的时序依赖关系，例如

1. 长数学表达式求值，例如，可转化为树形结构布尔表达式求值的问题；

2. 解线性方程组的高斯消元法，或者针对三对角矩阵的简化高斯消元，也就是Thomas算法；

3. 复杂State Tracking问题，例如，给定棋盘开局以及若干个棋子移动步骤，求棋盘终局；

假设希望System1（Transformer/Mamba）在预测下一个Token（word）的工作模式下求解上述问题，那么

* 若不使用CoT，也就是对给定的输入问题，限制输出Token数为某个固定常数，则无法解决。

* 若允许使用CoT，也就是允许不限制Token数量，一步步的展开了解决，那么理论上已经具备了求解可能性。

注意，我们总是可以付出更多参数容量和训练数据量\-\-\-可能存储代价相对于问题长度是指数级\[4\]\-\-\-让System1记住许多特殊Case，从而能快速直接输出答案。但这与上述结论并不相悖，上述结论强调的是通用性：你永远无法让System1用常数个输出Token，通用的解决这类问题。

一个更通俗的类比是组合逻辑与时序逻辑：使用了CoT的Transformer，就像是时序逻辑，有了反馈回路，可以更新记录状态，从而获得比组合逻辑更强的计算能力。

## 1.2. 更严谨的解释

我们在此从教科书\[1,2\]及论文\[3,4,5,6\]搬运了相对更严谨的理论描述，供有兴趣的读者参考。

**定义**👉\[**电路**\] 电路$C$由一系列“与”\(fan\-in 2 fan\-out 1\)、“或”\(fan\-in 2 fan\-out 1\)、“非”\(fan\-in 1 fan\-out 1\)门组成，输入长度$n$的 0\-1 布尔串$x$，并输出布尔串$C(x)$。

**定义**👉**\[电路族、一致电路族**\] 一系列无穷电路组成的集合$\{C_n\}_{n\in\mathbb{N}}$称为一个电路族；如果存在一个将布尔串$1^n$映射到$C_n$的隐式对数空间可计算函数，则称这个电路族是一致电路族。简单理解就是，定义电路族的复杂度本身应该是可控的。

**定义**👉\[**电路的复杂度和高度**\] 电路$C$的复杂性指它含有的门的个数，记作$|C|$；若把电路看做有向无环图，则输入到输出的最长路径称为电路的高度。

**定义**👉\[**高度函数**\] 如果对每个$n$，$C_n$的高度不超过$H(n)$，则称函数$H$是电路族$\{C_n\}_{n\in\mathbb{N}}$的高度函数。而一个算法的本质不可并行的部分，就体现在电路高度上。

**定义**👉\[**按电路复杂度给问题难度分类**$\text{SIZE}(S(n))$\-\-\-更形式化的说，用多复杂的电路可判定给定布尔串集合\] 对某个函数$S:\mathbb{N}\to\mathbb{N}$，如果一类问题，能用复杂度满足$|C_n|\leq S(n)$的电路族$\{C_n\}_{n\in\mathbb{N}}$解决该类问题，那么称这类问题在类别$\text{SIZE}(S(n))$中。

**定义**👉\[**可高效并行计算问题类**$NC^d$\] 可用高度函数为$O(\log^d(n))$的一致电路族解决的问题类，记作$NC^d$；高效并行计算类定义为$NC=\cup_{d}NC^d$。

**定义**👉\[$NC^d$**问题类的变种**$AC^d$\] 如果允许电路的“与、或”门，由2输入变成任意多值输入，则$NC^d$变为$AC^d$。可以证明$NC^d\subset AC^d\subset NC^{d+1}$。

**定义**👉\[$TC^0$**问题类**\] 在$AC^0$问题类被使用的电路可能性中，增加“MAJORITY”门，这个门可接受任意多值输入，作用是当一半或以上输入值为1时，输出1，否则输出0。




$\lor: or，\land: and, \lnot: not$

![[attachments/llm-notes/AI的时间-Scaling-Law-的一些理论佐证-01.png]]

![[attachments/llm-notes/AI的时间-Scaling-Law-的一些理论佐证-02.png]]



**定理**🤜$AC^0\subsetneq TC^0\subseteq NC^1\subseteq NC^2\subseteq \cdots \subseteq NC^d \subseteq \cdots \subseteq P$。



注意，$TC^0\neq NC^1$是否成立还是开放问题，但通常认为是成立的，否则会导致一些重要问题类坍塌。

对于$NC^d$的层级，如果某个$\exist\ d\in\mathbb{N},\ s.t.\ NC^d=NC^{d+1}$，则可以证明$NC^d=NC^{d+1}=\cdots=NC$，整个$NC$类会坍塌至$NC^d$。当前被广泛相信的是，任何一个$NC^d$层级不会坍塌。

**定理**🤜\[**Transformer可解问题类**\]\[3,6\] 如果Transformer内部使用的计算精度为$\log(n)$，其中$n$是输入序列Token数，则Transformer直接可解问题类在$TC^0$中。

**定理**🤜\[**Mamba可解问题类**\]\[5\] 如果Mamba内部使用的计算精度为log⁡\(𝑛\)，其中𝑛是输入序列Token数，则Mamba直接可解问题类在$TC^0$中。

**定理**🤜\[4,6\] 如果$TC^0\neq NC^1$，则Transformer + CoT可求解长串数学表达式求值、线性方程组求解、复杂State Tracking等复杂问题，但不借助CoT的Transformer无法直接求解。



其中，线性方程组求解的已知最高度并行的算法（Csanky,1976）不在$NC^1$中，常用的高斯消元法甚至不在$NC$中。

# 2. 展开的联想：AI的时间Scaling Law

仔细审视前面的讨论，我们会发现，这些理论实际上还传达了这样一个朴素的直觉：

`如果你愿意付出更多的计算代价、迭代反馈次数，那么你可以解决更多的问题，`

也就是Test Time Scaling Law。在更大的范围上，复杂性阶梯的广泛存在性，也佐证了这一点。举例来说，从易到难的大的问题类比如有：

1. 高度可并行电路可求解问题类$NC^0,AC^0,TC^0,NC$，如整数乘除法、矩阵乘法、矩阵行列式。

2. 多项式时间可求解$P$、多项式时间可验证$NP$问题类，如素数判定、图同构、蛋白质折叠、布尔可满足性SAT。

3. 指数时间计算问题类$EXPTIME$，如围棋、国际象棋。

4. 图灵可识别但不可判定问题类$RECOGNIZABLE/recursively\ enumerable$，如图灵停机问题、图灵机等价性判定、ZFC公理体系下的命题证真或证伪（哥德尔不完备性定理）。这类问题中，即使是描述极短的问题，也可能只有长解决方案（如费马大定理）甚至至今没有证真或证伪（如黎曼猜想）。

对时间Scaling Law的一个更直接的佐证，是时间层次定理\[1,2,8\]\(Time Hierarchy Theorem\)。与多数图灵不可判定问题的证明类似，时间层次定理的证明，通常也是借助对角线法，这都蕴含着这样一个根本直觉，即时间Scaling Law的背后是：

`问题数（例如对标不可数）远比解决方案数（例如对标可数）更丰富：通过对角线构造，我们总能找到一个新的、不属于现有资源能解决的问题。`

事实上，在不同的设定下，我们还可以找到时间层次定理的不同版本，但总体来说，我们所关心的计算模型，例如原始的单带/多带图灵机或是更接近现代计算机的Random Access Memory图灵机，都有着相应的时间层次定理。

下面，针对图灵机/RAM图灵机，我们列出时间可构造函数以及时间复杂度问题类的定义，

**定义**👉\[**时间可构造函数**\] 若有图灵机在$O(T(n))$时间内计算函数$1^n\to[T(n)]$，则称$T(n)$是时间可构造的。

**定义**👉\[$\text{TIME}(T(n)),\text{TIME}^{\text{exact}}(T(n))$，**按时间函数区分复杂度的问题类**\] 如果$L\subset \{0,1\}^*$是可判定问题，若存在判定$L$的图灵机$\mathbb{M}$以及常数$c>0$，使得对任意$x\in L$，记$|x|$为$x$的长度，$\mathbb{M}$在$cT(|x|)$步内停机，则称$L\in\text{TIME}(T(n))$。**如果要求在**$T(|x|)$时间内停机，而不考虑常数系数$c$，那我们把相应的问题类记作$\text{TIME}^{\text{exact}}(T(n))$。**我们通常所说的复杂性问题类**$P$**就是**$P=\cup_{c\geq1}\text{TIME}(n^c)$**。**



简单理解时间可构造函数就是，时间函数$T(|x|)$本身的计算时间，不应该超过$T(|x|)$。进一步，如果是完全时间可构造函数，则应当能构造一个恰好用$T(|x|)$时间停机的“时钟图灵机”。我们通常见到的函数如$n^k,n!,2^n$都是完全时间可构造函数。

基于上述定义，可以理解下面的时间层次定理：如果你付出相应的时间代价，那么一定可以解决新的问题。

**定理**🤜\[1\] \[**原始图灵机的时间层次定理**\] 若 $f,g$是时间可构造的且$f(n)\log(n)=o(g(n))$，则

$\text{TIME}(f(n))\subsetneq\text{TIME}(g(n))$。

**定理**🤜\[9\] \[**RAM图灵机的时间层次定理**\] 如果RAM的每条指令的执行时间关于操作数的长度（位宽）是对数，那么，对于任何时间可构造函数$T_2(n)\geq n\log(n)$，如果另一个函数$T_1(n)$满足$\liminf_{n\to\infty}\frac{T_1(n)}{T_2(n)}=0$，则

$\text{TIME}(T_2(n))\subsetneq\text{TIME}(T_1(n))$。

**定理**🤜\[10\] \[**RAM图灵机的时间层次定理**\] 如果RAM的每条指令的执行时间关于操作数的长度（位宽）是常数，那么，对于任何完全时间可构造函数$T(n)\geq n$，存在常数$c>0$，使得

$\text{TIME}^{\text{exact}}(T(n))\subsetneq\text{TIME}^{\text{exact}}(c\cdot T(n))$。



# 写在最后

既然问题的可能性相比于解决方案是如此丰富，我们自然的会思考，或质疑：在实际应用中，当你想解决某种通用子问题时，即便不是上述理论所能明确分类的典型问题，指望固定计算解决可能也会碰到本质天花板？是否不如拆分成多个更熟练的步骤，既不违背时间Scaling Law约束，又能获得小颗粒度闭环验证、分而治之的好处？例如

* 通用的代码定位检索问题。自动编程工具中，基于ReAct模式的定位检索正在兴起，预期整体技术将逐渐承担更多的任务；固定计算的一次检索工具不会是全部，它们也不一定会消失，而是不断的基础化、工具化。

* AI的外挂记忆技术。就像人类查阅记忆，AI的外挂记忆或许也要做好准备，对于一个查询请求，可能需要借助多次内部迭代，甚至与用户的多次迭代，才能输出良好答案。

# 参考文献

1. 傅育熙. 计算复杂性理论. 清华大学出版社, 2023.

2. Arora, Sanjeev, and Boaz Barak. Computational complexity: a modern approach. Cambridge University Press, 2009.

3. Merrill, William, and Ashish Sabharwal. "The parallelism tradeoff: Limitations of log\-precision transformers." Transactions of the Association for Computational Linguistics 11 \(2023\): 531\-545.

4. Feng, Guhao, et al. "Towards revealing the mystery behind chain of thought: a theoretical perspective." Advances in Neural Information Processing Systems 36 \(2024\).

5. Merrill, William, Jackson Petty, and Ashish Sabharwal. "The illusion of state in state\-space models." arXiv preprint arXiv:2404.08819 \(2024\).

6. Strobl, Lena, et al. "What formal languages can transformers express? a survey." Transactions of the Association for Computational Linguistics 12 \(2024\): 543\-561.

7. Wei, Jason, et al. "Chain\-of\-thought prompting elicits reasoning in large language models." Advances in neural information processing systems 35 \(2022\): 24824\-24837.

8. https://en.wikipedia.org/wiki/Time\_hierarchy\_theorem

9. Cook, Stephen A., and Robert A. Reckhow. "Time\-bounded random access machines." Proceedings of the fourth annual ACM symposium on Theory of computing. 1972.

10. Sudborough, Ivan Hal, and A. Zalcberg. "On families of languages defined by time\-bounded random access machines." SIAM Journal on Computing 5.2 \(1976\): 217\-230.
