---
type: historical-note
status: archived
tags:
  - control-feedback
  - token-instruction
  - load-store
  - historical-motivation
---

# 历史动机：Token[Instruction] = Opcode + Operands

> [!note] 历史定位
> 这篇是 `Token = Instruction` 早期完整论证草稿，包含许多后来被 challenge 收缩的表述；当前执行立场见 [[10-控制反馈-TokenInstruction/当前主线总览|当前主线总览]]，问题展开见 [[10-控制反馈-TokenInstruction/问题展开地图|问题展开地图]]。

## 1. 总览

基于生成式大模型的AI---以OpenAI的ChatGPT为起点---展现出了令人惊艳的智能。然而，它们又在一些看似简单的任务上，有些不尽如人意。那么，AI少的那一点“灵气”，是什么？我们有下面的基本观点

`当前AI基础模型，缺少快速、自主控制反馈信源的能力`

针对这一观点，要回答下面三个问题

1. 快速、自主控制反馈信源的能力，是什么意思？

2. AI基础模型，为什么有必要具备快速、自主控制反馈信源的能力？

3. 如何让AI基础模型具备快速、自主控制反馈信源的能力？是否有可行方案？

这篇文档，我们就要：

1. 首先，通过对照、分析人类与AI解决问题的过程，基于来自人类智能与控制论的直觉，回答第1个“是什么”、第2个“必要性”的问题。我们还将穿插在文档中，澄清例如Sparse Attention、ReAct模式、编辑标签Token、外挂记忆等技术与自主控制反馈信源能力的关系。

2. 其次，抛出我们认为最重要的一个理论联系，这一联系提供了桥梁，让我们可以从计算理论、计算机工程实践的角度，更清晰地定义、回答上述第1、2个问题，并得到第3个“怎么做”问题的线索。有必要在此给出概要：

受到计算机体系结构领域中的指令、指令集概念的启发，我们认为 AI [[10-控制反馈-TokenInstruction/历史动机/AI的System1-System2|System1 + System2]] 的交互媒介，即Token，不止可以是数据（或单词），同时也可以是指令(Instruction)，包含操作码(Opcode)和操作数(Operands)两部分，

Token[Instruction]=Opcode+Operands

我们常见的预测下一个Token[Instruction]，可看做是 `Opcode == Append, Operands = [Word]`。由此，对第1个“是什么”的问题回答如下：

1. 首先，不同于具有固定结构化指令序列的计算机程序，AI System1的核心工作是**生成指令**，如果把System1看做控制器，则生成的控制信号就是指令。我们定义一类事物的**自主性**，实际就是指这类事物应作为**System1的输出件**，由**System1生成**，而非由System1内部的固定计算过程（如Sparse Attention）或System2的固定流程（如Append）决定。

2. 进一步，为了AI System1生成的各类非 `Append` 指令能正常工作，需引入对标计算机内存的工作空间概念。这促使我们明确 System1 的**工作空间、Context、内部状态**这三个概念的含义，它们在只有 `Append` 指令的情形下是同一个东西，但现在它们是不同的。System1在每一步根据当前状态生成的不同的指令，将以不同的方式改变System1内部状态，以不同的方式读写外部工作空间。

3. 紧接而来的问题是，System1预测指令所需的反馈信号来自哪里？System1如何预测各指令操作数的地址？生成工作空间的“**地址**”就是我们所说的**自主控制反馈信源**，是支撑高效**分而治之、小颗粒闭环、动态规划等能力**的关键，在“Token=Instruction”的语境下可表述为：

> [!summary] 早期核心观点
> `System1` 需生成多类指令，特别是生成 `Load/Store` 指令所需的、操作数在工作空间中的地址。

有了更正式的定义后，第2个“必要性”的问题，我们将给出从理论中找到的对照和佐证。

对于第3个问题，更具体地说，要如何改造System1/System2来适配，让AI具备快速自主控制反馈信源的能力？多模态、空间智能、强化学习、Transformer、Mamba对这个能力有何作用？这些问题在原始写作中指向[一篇后续外部文档](https://clouddocs.huawei.com/wapp/doc/d9669789-9d2c-411d-8ec3-8fe313720b91)，当前收缩后的执行版本见 [[10-控制反馈-TokenInstruction/当前计划与Defense|当前计划与 Defense]]。

## 2. 控制 & 反馈：人类 vs. AI

### 2.1. 预热发散思考：从几个任务的解决过程谈起

我们的思考是从分析AI及人类对几类任务的解决过程开始：一类任务，AI远超人类；二类任务，AI与人类各有千秋；三类任务，人类强于AI。这里暂时不讨论AI持续学习的必要性和技术路径，而是带着这样一个问题去反复质问人类的解决过程的每一步：

“人类在得到下一个单词的过程中，会做什么？会想什么？能否直接写对这个单词而不用修改？”

“如果不能，人类的下一步，又会做什么？得到什么输入？想什么？”

“作为人类的你能做到最少移动目光几次？每一次移动目光，是为了确认什么？最少编辑你的草稿纸几次？”

这里仅给出两个具体的一类任务，更多参考问题见 [[#A. 典型问题|附录]]。

* 函数收敛的否命题。

定义，函数 $f(x):\mathbb{R}\to\mathbb{R}$ 在点 $x_0$ 收敛到 $f_0$ 是指，$\forall\varepsilon>0,\exists\delta>0$，对任意满足 $|x-x_0|<\delta$ 的 $x$，都有 $|f(x)-f_0|<\varepsilon$。

证明，函数 $f(x):\mathbb{R}\to\mathbb{R}$ 在点 $x_0$ 不收敛到 $f_0$ 是指，$\exists\varepsilon>0,\forall\delta>0$，存在满足 $|x-x_0|<\delta$ 的 $x$，使得 $|f(x)-f_0|>\varepsilon$。

* Thomas算法可快速求解三对角矩阵的线性方程组，请确定以下C语言实现中倒数第3行的循环下标上界 $n$。

```cpp
void thomas(const int X, double x[restrict X],
            const double a[restrict X], const double b[restrict X],
            const double c[restrict X], double scratch[restrict X]) {
    /*
     solves Ax = d, where A is a tridiagonal matrix consisting of vectors a, b, c
     X = number of equations
     x[] = initially contains the input, d, and returns x. indexed from [0, ..., X - 1]
     a[] = subdiagonal, indexed from [1, ..., X - 1]
     b[] = main diagonal, indexed from [0, ..., X - 1]
     c[] = superdiagonal, indexed from [0, ..., X - 2]
     scratch[] = scratch space of length X, provided by caller, allowing a, b, c to be const
     not performed in this example: manual expensive common subexpression elimination
     */
    scratch[0] = c[0] / b[0];
    x[0] = x[0] / b[0];

    /* loop from 1 to X - 1 inclusive */
    for (int ix = 1; ix < X; ix++) {
        if (ix < X-1){
        scratch[ix] = c[ix] / (b[ix] - a[ix] * scratch[ix - 1]);
        }
        x[ix] = (x[ix] - a[ix] * x[ix - 1]) / (b[ix] - a[ix] * scratch[ix - 1]);
    }

    /* loop from n to 0 inclusive */
    for (int ix = n; ix >= 0; ix--) // 答案是 n=X-2
        x[ix] -= scratch[ix] * x[ix + 1];
}
```

从AI的System1+System2解决问题的过程及结果可以看出，不论是哪些任务，随着答案长度增加，即使是先进AI模型System1，也会出现错误、冗余，并进一步可能产生误差累积，而最终无法得到正确答案。当问题类型确定时，则可以对System2进行针对性的设计以得到改进。

那么，对于各类任务，特别是长难任务，人类的解决方式与AI到底有何区别？已有的针对特定问题类的改进技术，它们是否有什么共性本质？

### 2.2. 人类与AI的控制反馈过程

#### 2.2.1. 人类

人类的每一次目光左右移动、对上下文或图像的观察及编辑，都是一次自主控制反馈闭环的实例。而有耐心的人类在做这些问题时，总是愿意在每个不确信的环节付出更多的迭代闭环，从而得到最终的正确答案。

事实上，大多数人类从来都不太擅长一次性解决问题。如果我们从控制论(Cybernetics)的角度去理解人类的解决过程，那么

* 在外部视角看，人类的解决方案里，“迭代+闭环验证”总是出现在**嵌套的大小颗粒度**的各个步骤及子步骤中。

* 在人类视角看，人类的每个迭代步骤，是首先**自主输出多种控制信号**，各信号将被解码为各动作，各动作执行效果是，

    * 对内：**获得反馈信号**，然后更新内部状态；或者

    * 对外：“执行某个笔划”或“发某个音”等，然后产生结果。

这里的“自主”的含义，直观来说就是：可以选择输出某类控制信号，也可能选择不，还可能选择多次输出，总之不被强迫每个步骤一定要“看”、“写”等等。

#### 2.2.2. AI

而当前的AI技术，特别是加持了System2的AI，理论上已图灵完备[5]。因此，似乎只要接上合适的接口，人类所拥有的任何控制方式，理论上AI都可以有：例如，AI领域早有诸多与迭代、闭环、修改相关的工作，例如ReAct模式[3]、在词表中增加编辑标签[2]使得System1/2具有编辑能力，Tool Calls支持等。我们不在本文详细介绍这些工作，而是为直接厘清当前主流AI技术与人类的重要区别，给出如下观察，

* **System1可输出的基本控制信号**的可选集合是词表$Vocab=\{X | X 在System1词表中\}$。

* 对于当前主流的使用**Full Attention**或类Linear Attention的System1，在不讨论在线更新神经网络参数的情况下，其控制反馈过程的结果，即**依据反馈信号更新后的System1的状态**，**也就是System1的Context**，主要取决于以下三种方式：

    * **原生的Token Append**：如果控制信号是单词型Token X，那么在最终Context Tokens序列末尾追加上X。

    * **广义Tool Calls+Context Engineering**：如果控制信号是以下形式之一，则最终Context状态取决于总体控制信号的语义及外部上下文工程的具体设置。

        1. 基本控制信号中的特殊标签Token，如 `<backspace>`。

        2. 连续若干个基本控制信号，也就是连续若干个单词型Token组成的Tool Call语句。

    * 其他，如隐层激活编辑：这包括了KV Cache编辑以及其他神经网络隐层状态编辑。

### 2.3. 基于直觉回答问题1、2

#### 2.3.1. 问题1的回答

基于上述思考以及对AI现状的理解，可得到对`文档开头第1个问题`的回答

* 与人类不同，AI大部分**反馈信源并非自主获取**：可用于自主获取外部反馈信号---例如使用上下文某一段或外部数据库某文档作为反馈信号---的特殊标签Token、Tool Call在所有控制信号中仅是少数。

* 与人类不同，AI的**迭代颗粒度**更大，且许多Tool Calls依赖固定的上下文工程来更新状态。

#### 2.3.2. 问题2的回答

针对`文档开头第2个问题`，控制论中有着一个基本共识，说明了“**快速**”反馈闭环的重要性：对于多数情况，特别是开放环境，我们更倾向于反馈信号频率能达到基本下限、且噪声可控的闭环控制，其稳定性常常优于开环控制。

除了“快速”之外，“**自主性**”呢？也就是为什么对反馈信源的选择要自主可控制呢？我们在后续将从计算复杂性理论领域找出更好的证据，这里先从人类工作模式获得直觉：快速、自主控制反馈信源能力，带来的自然好处是，

`对各类通用问题可以`**`智能地分而治之求解、小颗粒闭环验证，不用被迫马上给出答案`**

### 2.4. Defense

关于快速、自主地控制反馈信源，我们可能马上会有如下疑问。

* 问：**Sparse Attention**算不算自主控制反馈信源？毕竟训练过的Sparse Attention模块，可用来选择具体对哪些Tokens着重计算注意力。

    * 答：不是，至少只说用Sparse Attention替代Full Attention不是。Sparse Attention更像是Full Attention的平替，它还是**System1内部的前馈计算**，计算完了之后，System1**必须**对外输出一个Token然后常常再Append这个Token。  
而人类是靠控制信号对应的动作，决定读取哪些文字或图像，这里一个显性区别是：人类可以自主控制外部反馈信号来源，或比如闭眼思考以屏蔽外部反馈信号，而不是**必须一通固定操作**之后**必须输出某个Token**。

* 问：**Tool Calls**是自主控制反馈对吧？我用某种方式让System1**缩短Tool Call语句的间隔**，就快速了？

    * 答：是的，没错。由于Tool Calls的概念可涵盖的范围是如此之广，因此完全可以说，自主控制反馈就是Tool Calls的一种。只是，我们这篇文档更强调

        * 用于自主控制反馈信源---读写上下文、外部数据---的那一类特殊Tool。

        * 是否有一个公认的基本Tool集合能让System1用得趁手，而不总是通过上下文学习、Context Engineering来实现自主控制反馈信源？

    * 答：关于颗粒度，截止到2025年，为了增加AI的可靠性，有许多Agent相关的工作尝试减小ReAct模式的迭代、验证颗粒度。

这两个话题，已经触及到我们即将要讨论的核心内容，我们在后文进行说明。多说一句，我们可以对此延伸推演看看。在System1基于Attention的大前提假设下，由于其原生的状态更新方式是Append Token，这不容易高效支持快速自主控制反馈信源：

1. 如果是编辑Context中某些Token，则需要重新计算编辑位后的KV Cache，这会增加额外的计算量；

2. 如果是把工具返回的Tokens追加至Context，那可能导致Context长度快速增长，这一方面会增加对注意力计算这种软筛选算法的信号干扰，另一方面也增加了计算量。

当然，即使有这些潜在不足，其最终的效果，也取决于各种底层基础设施以及上层算法（例如AI的memory管理，上下文管理，追加Token时仅保留摘要内容等技术）的持续改进和博弈，这里不再详细讨论。

* 问：RAG，**外挂记忆**，这类Tool，算不算自主控制反馈信源？

    * 答：算。我们对文档开头第3个问题的回答，就可以理解为一种外挂记忆的实现方式。我们期望的是一种强调快速、自主性的实现方式。

* 问：隐层状态编辑，是自主控制反馈信源吗？

    * 答：不是，隐层状态编辑是一种拿到反馈信号之后的更新方式，强调的是状态更新，而自主控制反馈信源，强调的是信号获取。你可以主动/被动获取反馈信号之后，再看采用哪种更新方式，更新的具体操作常常也跟System1选用的神经网络架构有关。而你所说的隐层状态编辑就算是一种更新方式可选项。

在下一节会对各概念进行更正式的定义，届时以上问题也可得到更清晰的回答。

## 3. Token[Instruction]=Opcode+Operands

那么，要如何让人工智能，获得类似于人类的快速、自主控制反馈信源的能力？

人工智能，一定要靠输出单词型Token来自定义工具、调用工具吗？*未必？但当前主要就是这么干的？*

人类获取反馈的时候，每一次动眼睛耳朵，都是靠说一段话来调用眼睛耳朵吗？*显然不是*

给大语言模型装上眼睛耳朵手脚，用多模态+具身，解决问题？是否存在更深层的理解，更便宜的方式？*其他可能性？*

对于纯文本，AI不可能有别的控制反馈方式了吗？*问题是怎么个其他可能性法？方案呢？能执行吗？*

AI控制反馈回路的System1内部状态，一定要是整个Context吗？*我也希望不是，特别是不希望只能Append*

解决方案无法一蹴而就在本文得到，还需要摸着石头过河。但幸运的是，我们在互相碰撞思想时，Dr. Liao揭示了一个更底层的联系：

> **你说的单词，在使用存储程序概念的通用计算机里，叫做数据，你想要的控制反馈方式，叫做指令。**
> **在主流通用计算机，冯诺依曼架构中，他们都会存储在Memory里，这本身也意味着，指令和数据，具有某些共通本质。**

这个联系，让我们得以重新理解Token的含义，这个新的理解，同样也与神经科学中的**预测编码假说**[1]遥相呼应：Token可以不止是**单词（数据）**，也可以是**指令**，System1每一步不止是**预测单词**，还可以**预测指令(Instruction)**，包含操作码(Opcode)和操作数(Operands)两部分，

Token[Instruction]=Opcode+Operands

因此，我们常见的预测下一个Token[Instruction]，可看做是'Opcode==Append, Operands=[Word]'。这个联系，给我们提供了将AI与计算机做类比的一个锚点，**智能及其工作方式等一系列概念的定义**也因此变得清晰。

### 3.1. 智能及其工作方式中的关键概念

#### 3.1.1. 基础知识：程序的概念

这一小节我们要介绍关于“程序”、“通用程序”概念的基础知识。

在计算机领域中，有着两个核心概念：**指令集，**存储结构。其中，存储结构与数据搬运代价、通信效率密切相关，我们暂时不做详细讨论。我们要讨论的是指令集，它决定了最基础问题的计算复杂度、计算机的通用性。

* 对于计算机而言，硬件与软件交互的媒介是指令/指令集。

    * 指令以下是硬件，硬件指令执行速度快，但不易修改，迭代周期长。

    * 指令以上是软件，软件更易修改，软件应用的可能性无比丰富。但软件所需的每个功能又必须调用指令甚至是大量指令完成，因此有必要抽象出好的指令集。

* 与之类比，System1和System2交互的媒介是Token。AI可以输出指令，也就是Token。而AI的词表，则可称之为AI的操作码（Opcode）集及操作数（Operands）集，操作码与操作数的所有合法二元搭配是**AI的指令集**，这也是AI可用的最小粒度Tool集：

    * 对下，指令集对接着更新较慢的System1核心实体，也就是神经网络和基础设施，需要与System1进行良好适配。

    * 对上，指令集是日新月异的System2生态生长的基础，影响着各种应用问题所需的功能、工具是否能得到高效映射。

在计算机术语里，（1）**程序**，指一段**固定**的结构化的**指令序列**；计算机，是用来执行程序的装置；**可计算**问题就是指可通过执行一段程序解决的问题---或更严格的定义，叫做“语言的识别”，本文不详细讨论；（2）**通用程序**就是能解释执行其他程序的程序；通用计算机是执行通用程序的装置；操作系统、虚拟机程序都是通用程序；通用性就是图灵完备性。

那么，理解了“可计算”、“程序”、“通用程序”之后，又如何理解“智能可求解”、“通用智能”？

#### 3.1.2. 智能的本质：具有自主性[=生成指令]+可学习的程序

这一小节我们要对智能给出更清晰且具有实践指导意义的定义。

按照丘奇-图灵论题，我们知道“计算”的概念与图灵机、Lambda演算、元胞自动机等计算模型相互定义，“可计算”的概念定义了人类可计算问题类的上限。因此，完全可以认为，“智能可求解”、“通用智能”概念上被“可计算”、“通用程序”所包含。因此，不同于以往的对**智能**的定义[4]，在“Token=Instruction”的语境下，我们可以站在“**通用程序**”的肩膀上定义“**通用智能**”：

**定义：通用智能** = 具有**自主性**的**可学习**通用程序 = **可生成指令（Token）**的**可学习**通用程序



于是，我们要研究通用智能，落脚点就在于：1.**可学习**；2.**计算通用性**；3.**自主性**；以及永恒的话题4.**性能**。前三项定义了通用智能，第四项“性能”则是计算机与智能都需持续演进的方向。在后文，我们将参考现代计算机理论模型，着重讨论计算通用性和性能，这里则对智能相比于程序的特殊点，也就是可学习和自主性，进行说明。

* **可学习**：涉及到网络架构、数据、学习策略，学习方式也与AI的指令集相关，暂时不做明确定义和讨论。

* **自主性**：我们把一类事物称为有自主性的，如果它是**System1生成的输出件**，即我们把自主性定义在System1/2之间的交界面上。与之相对的，例如，System1内部的固定前馈计算或System2的固定操作，都没有自主性。**生成非固定指令序列 vs. 固定指令序列**，这正是**智能**与**程序**的重要本质区别，智能的指令序列应当允许是非固定、自主控制的。

于是，System1的核心工作就是“**生成指令**”。智能的自主性要求，它允许了当前任务可花费不止一步完成，也就是按需迭代式地多次生成、执行指令。

既然智能的本质是可生成指令且可学习的程序，那么System1可能会生成哪些指令，生成的指令如何能正确执行？

#### 3.1.3. System1的工作空间 & Context & 内部状态

这一小节我们要讨论清楚，为了各指令的正常工作，System1的工作方式应如何适配。

我们可以选择一种高性能但同时又不引入过多工程复杂性的指令集作为参考，为此我们把注意力投向最接近现代CPU的理论模型**RASP**（Random Access Stored Program）[6-d]，这是一种构建于**RAM**（Random Access Machine）[6-c]之上的高性能通用计算机理论模型。与通用图灵机[6-abefg]不同，RASP明确采用了可直接&间接寻址的Memory概念，并抽象出了三大类核心指令：（1）算术指令，（2）条件跳转，（3）寻址指令。其中，算术指令、条件跳转决定了RASP的计算通用性，而寻址指令则对计算性能至关重要。

由于智能的自主性要求，其指令序列是由System1生成的，因此可认为智能自带条件跳转。因此，只需考虑如何支持另外两种指令的正常工作。

为了让寻址指令和算术指令正常工作，需要引入对标计算机的内存的概念，我们称之为AI System1的**工作空间**。过去，AI System1的**工作空间、Context、内部状态**，常常几乎等同为一个东西，也就是整个上下文Token序列以及KV Cache。现在要指出，他们是不同的概念，例如，

1. 'Load'从工作空间读取数据，工作空间可以是一个存储明文有地址编号的读写带；

2. 算术指令、'Store'指令，就像通常的Tool Calls，修改工作空间；

3. 任何指令的执行都会更改System1的状态。System1的状态，例如可能是RNN的state，也可以是KV Cache；

4. Context是所有指令的历史记录。

需要说明的是，这里我们仅澄清这三个概念的差别，并鼓励它们采用不同的表征以得到更高性能。但不代表任何实现中，都必须要用三种不同的数据结构或信息实体来实现这些概念。例如，可以在初步探索中，先借助已有AI混合实现。更具体的设置，也就是`文档开头第3个问题`的详细回答，还需要更进一步试错才能得到，这里不再详细讨论。

综上，这一小节梳理了支撑RASP三大类指令正常工作的一系列相关概念。于是，有一个自然的问题是，算术指令和寻址指令，对于System1来说是必要的吗？

#### 3.1.4. 性能的关键：自主控制反馈信源[=生成工作空间地址]

这一小节，我们就要对`文档开头观点`中的“自主控制反馈信源”进行更正式的阐述，并回答上一小节末尾的问题。

回顾上一小节，我们提到，RASP抽象出了算术、跳转、寻址三大类指令。对AI而言，可生成指令的System1自动具备跳转能力。此外，容易看出，如果System1能够正确的使用Load/Store，那么System1可以快速生成合适的Tool Call以调用逻辑运算、加减乘除等算术指令。因此，我们最后着重评估**以Load/Store类指令为代表的直接 & 间接寻址能力**对于System1是否必要。

对计算机而言，**寻址能力对性能的影响**至关重要[6-l]：如果缺少直接 & 间接寻址能力，将导致许多问题的计算性能产生严重的、**多项式（不小于平方）级别的劣化**。对这一复杂度鸿沟的直观理解就是，只要地址是对的，RASP就可以用这些指令在常数或对数（地址空间大小的对数，如64位地址访问）的时间内访问到合适的数据，但原始的图灵机则需要一格一格移动读写头，每移动一格消耗相同的计算时间，才能访问到指定地址的数据。

考虑到Load/Store对程序性能的重要性，我们有理由相信，Load/Store对AI也是必要的，

**`Load/Store`**`在AI指令集中，应与word类Token一样，是`**`一等公民`**`。`

**`Load/Store`**`带来的下一个单词的不易预测、复杂性，是重要的学习来源---这个表述，还需要打磨。`

`交界面，是把 M x N 复杂度编程 M + N 复杂度的必经之路，要控制 AI 内部的复杂度，需要交界面。Load/Store放在交界面，是否有自举智能？---这个表述，还需要打磨，真正的理论问题是什么？`

下面展开讨论。

我们所说的AI的“自主控制反馈信源”，就是**生成地址**。

事实上，既然System1的核心工作是“生成指令”，那为了让System1生成“好的”指令，紧接而来的关键问题是：（1）生成指令的操作数地址是多少？（2）生成“好的”指令，需要的反馈信源哪里来？

这两个问题都指向，生成良好指令的关键是生成良好的Load/Store指令Operands地址，也就是自主控制反馈信源。即使是对于固定指令序列的计算机程序，指令操作数地址的计算也可以是复杂且不平凡的，对AI而言更是如此：AI可以且应当使用非固定的指令序列得到数据地址，

**`生成指令操作数的工作空间地址`**`：这个过程与生成指令是`**`互相递归`**`的，按需多次生成指令以获得地址`

可以展望，一旦有了生成地址能力，AI可获得许多方面的能力提升，例如，（1）可以发展AI对于工作空间的读写能力，AI的状态可以不必是整个工作空间；（2）由**生成指令及地址的能力**，可自然诱导出AI对于长难问题的**递归分解处理、动态规划能力**；（3）AI对大地址空间的操作能力，即我们所说的处理超长上下文或无限上下文的能力。

至此，我们对“自主控制反馈信源”做出了更正式的解释，也就是“生成地址”。我们还直观论述了生成地址能力的必要性和好处，在下面，就要更正式的讨论其必要性。

### 3.2. 必要性：来自计算复杂性理论的证据

这一节，我们就要基于计算复杂度理论的经典结果，用更正式的理论对照及佐证，来讨论“自主控制反馈信源”也就是“寻址能力”、“自主性要求”的必要性，即回答`文档开头第2个问题`。

#### 3.2.1. 寻址能力必要性的直接证据

我们在这里要介绍和对比三种计算模型，（1）Write-Once图灵机，（2）原始图灵机，（3）RASP。

其中，**原始的图灵机**[6-abefg]主要用于纯理论研究，但在其中也包含了几个对后续实际计算机工程有启发的概念，**状态转移函数** & **一个无限长读写带**：图灵机的工作过程就是，读写头根据自己的状态以及读到的读写带上的字符，由状态转移函数决定如何修改当前字符以及决定读写头在读写带上向左或向右移动。相关的变种，还有多带图灵机，也就是具有$k>1$个读写带及读写头数量的图灵机，称为$k$**- 带图灵机**。

![[assets/images/控制反馈：Token-Instruction-=Opcode+Operands-01.png]]




![[assets/images/控制反馈：Token-Instruction-=Opcode+Operands-02.png]]



而**write-once图灵机**[6-efh]，与原始图灵机的区别是，增加了一项**限制**：**每一个读写格，可以反复读，但只能写入一次**。研究write-once图灵机的现实意义来自只写一次存储，例如早期计算机的读写带是纸带，每个位置只能打孔一次。如果把Context看做读写带，那么**主要生成“Append Operands(word)”的System1就像是某种write-once图灵机，甚至是比write-once更受限的图灵机**。这里“更受限”是指，write-once图灵机并不限制写入的读写格必须是下一个，也可以跳格，但“Append Operands"写入的永远是下一个。

最后是**RAM/RASP**[6-cd]，它有无限个带地址的寄存器。RASP之于RAM就像通用图灵机之于图灵机，区别在于RASP相比通用原始图灵机**高效**得多，而**高性能的关键就是寻址能力**。

下面，是一些更严格的，关于几种计算模型的性能的理论阐述，供读者参考。

首先，是write-once图灵机与原始图灵机的对比，

**结论**🤜[6-efhij][**用write-once模拟原始图灵机**] 可以设计单带write-once图灵机，使得原始单带图灵机的$t$步操作，在这台write-once图灵机上可以用$O(t^2)$步模拟。对于更小（状态数少、转移函数简单）的通用write-once图灵机，模拟成本可能更高。



这里，为了克服write-once图灵机只能写入一次的难题，同时也为了模拟算法有通用性，教科书中使用快照复制法进行模拟，每当原始图灵机需要进行写操作时，就在write-once图灵机中复制一份相关的内容。

其次，是原始图灵机与多带图灵机的对比，两者有着十分本质的区别。多带图灵机天然可更好的支持数据匹配操作，可以一定程度避免读写头的折返跑，

**结论**🤜[6-abefgk][**用原始图灵机模拟多带图灵机**] 可以设计单带图灵机，使得2-带图灵机的$t$步操作，在这台单带图灵机上可以用$O(t^2)$步模拟。这个复杂度界最优的，例如回文问题，不可能用少于$O(t^2)$的复杂度求解。2-带图灵机可用$O(t\log(t))$步模拟k-带图灵机的$t$步操作。



进一步，是多带图灵机与RAM/RASP的对比，两者同样有着本质的区别。RASP更高性能的来源，同样是因为进一步避免了读写头的折返跑，

**结论**🤜[6-abcdl][**用多带图灵机模拟RAM**] 可以设计多带图灵机，对于RAM上的$t$步操作，如果每次寻址所消耗的时间是$\log(n)$，其中$n$是寻址空间大小，则在这台多带图灵机上可以用$O(t^2)$步模拟RAM，反向模拟则几乎没有性能损耗。且由于RAM上的时间层次定理[6-l]，可知这个复杂度界是最优的。



以上三个结论，共同揭示了write-once图灵机与RASP之间有着巨大的、不小于平方级时间复杂度的性能鸿沟。这正是AI有必要掌握Load/Store所代表的寻址能力的直接证据！

#### 3.2.2. 自主性要求的间接证据

电路复杂性理论及各类计算模型的时间层次定理等理论，引申出的时间Scaling Law，告诉我们，要解决通用的问题，就必须要做好付出无限迭代次数的准备。证明过程中的对角线法蕴含着背后的基本认知：

`问题的数量，远远比固定程序的数量多。`

`给定长度，对应问题的数量可能是长度的超多项式级。`

`不对问题自主分而治之求解、小颗粒闭环验证，可能就要付出超多项式级的记忆存储代价。`

如果对某种可能性数量巨大的问题类，试图用一个固定算法解决，那可能需要付出远超多项式级的存储代价：需要记住的case过多，人们总是很容易构造出同类新问题来攻击这套固定算法。

而我们所讨论的反馈信源，也就是“地址”，或许（这只是猜测，没有严格定义和证明）至少在某个长度尺度上，就不应该是使用固定算法所能得到的，更正式的表述是

`地址获取问题，是可判定（一定停机）的吗？如果可判定，那地址获取问题，属于什么复杂性类？`

因此，如果承认或相信地址获取问题的不平凡性，特别是可能的不可判定性---例如数学证明问题、项目目标分解问题，都算广义的地址获取问题---那应当让System1动态输出反馈信源的地址，这就是我们所强调的**自带递归性**的“**自主性要求**”的间接证据。

这方面的更具体阐述，原始写作中指向[旧外部文档](https://clouddocs.huawei.com/wapp/doc/ba1805df-7ae8-4bea-a092-c08a182b818c)。

### 3.3. 其他展开的思考

* AI的“学习”是否应该是自主的？也就是，要不要让System1生成指令来触发System1的学习更新，而不是按照某个固定流程，如预训练，更新System1？

* 是否应该通过如多通道机制，让神经网络分别输出'Append'、'Load'、'Store'等类型Token？Append型Token，是否应该在AI的指令集中占据绝对优势地位？

* 能否像Lamdba演算一般，让AI进行显式地递归地任务分解？这与CoT的顺序计算不同，这是一种自顶向下分解或由后往前倒推解决问题的思路。

* 存储层次结构：AI从System1到System2的各个工作层级，生成及调用工具、处理工具反馈信号，所需要的通信带宽是多少？

* 当前System1的大部分训练数据，更倾向于一次尽可能解决好问题，而非借助System2多轮迭代并联合训练。那么，如何让System1可以训练好多轮迭代数据？

* 现代计算机的优秀工程技术，仅供参考做发散联想：（1）指令流水线、乱序执行、分支预测：这与AI中的block-wise diffusion有些类似，并行的生成多个Tokens而非顺序挨个生成Token，但如果出错，要从某个点重来；（2）多核并发+多机并行：多个AI之间紧密协作+AI群之间的协作通讯。

### 3.4. Defense

* 问：Transformer、GPT，是通用智能吗？

    * 答：通用性---在一些假设下图灵完备[5]；自主性---指令都由System1生成（每次Append不同的Operands也算）而不是固定序列；可学习---不用多说，这些模型就是非自主地学习出来的。因此，可说它们就是通用智能。

    * 追问：Transformer、GPT，性能高效吗？

        * 答：不能生成Load/Store，只能用Agent、Tool Calls模拟Load/Store，我认为不。

* 问：Multi-Agent也能达到Load/Store的能力？比如，对一个超长的Context，我们可以考虑一个简单的Multi-Agent系统，每个Agent负责其中一部分，最后一个Agent负责解决问题。最后的Agent需要什么数据时，它就按需去问前面的Agent；前面的Agent互相之间，也允许按需通信。这就是一种自主Load/Store了？

    * 答：当然是，确实就是。这相当于建了一张Agent的Graph，主模型自主寻址的实现方式是在**Graph上由各节点的AI自行导航的游走**。当然，这种过程，也可以只让一个模型通过Load/Store指令来干，寻址的自主性要求，就是为了处理不能一次生成正确数据地址的情形。大胆猜测，这种迭代式的，由一个模型主导在工作空间Context上游走的工作方式，即Load/Store，或许相比于Multi-Agent在Graph上游走的方式，可训练性更容易？

* 问：那么，让一个模型通过Load/Store指令干活，相比于Multi-Agent干活，有何优劣？

    * 答：可能最大的优劣对比是，

        * 首先，每个Agent内部也需要寻址，只是Full Attention威力强大，在一定的尺度下对一些问题可以进行暴力解决。但如果从最细粒度就支持递归寻址，原则上能带来最佳的分而治之、小颗粒闭环能力，在最底层支持动态规划等以空间换时间的方案。

        * 其次，训练System1使用Load/Store，与训练使用Tool Call本质类似，既然要训练Tool Call，为何不训练Load/Store？

        * 另一方面，当前Multi-Agent的研究如火如荼，所以可能Multi-Agent有广大用户、开发者支撑的数据飞轮先发优势。Load/Store需要有一个第一步证明。

* 问：如果要让**System1输出Load/Store指令**，那这个控制反馈回路里，**System1的状态**是什么？

    * 答：我们前面提到过 System1 的**工作空间、Context、内部状态**这三个概念的变化。因此，System1状态最好不再是整个Context，例如使用类RNN方式表示内部状态。当然，早期验证阶段，站在已有的优秀大模型的基础上先开发探索，可以考虑把Context与状态和工作空间不做严格拆分。

## 4. 总结

这篇文档中，我们从AI与人的工作模式出发，分析了AI的特性：AI缺少“快速自主控制反馈信源的能力”。其中，把Token看做是指令，那么也就是，AI System1缺少“生成各类指令，特别是Load/Store所需的操作数地址”的能力。我们还从直觉与理论两方面论证了这种能力的必要性。

但最终这一方向能否在AI技术发展的势中生存下去，首要取决于`文档开头第3个问题`能否得到解决：

`能否设计神经网络，以及如何构造训练数据，借助什么算法，使System1掌握Load/Store指令？`

这些问题在原始写作中另有[旧外部文档](https://clouddocs.huawei.com/wapp/share/d9669789-9d2c-411d-8ec3-8fe313720b91)承接；当前执行版见 [[10-控制反馈-TokenInstruction/当前计划与Defense|当前计划与 Defense]]。

## 参考文档

1. 压缩即智能 & 预测Next Token；生物的预测编码假说 & 用Token表示一切输入输出信号：

    1. 预测编码假说：https://en.wikipedia.org/wiki/Predictive_coding

    2. Friston, Karl. "The free-energy principle: a unified brain theory?." Nature reviews neuroscience 11.2 (2010): 127-138.

2. 如果输出某个单词Token万一不对怎么办？编辑标签Token？

    3. Cundy, Chris, and Stefano Ermon. "Sequencematch: Imitation learning for autoregressive sequence modelling with backtracking." arXiv preprint arXiv:2306.05426 (2023).

    4. Physics of Language Models：https://physics.allen-zhu.com

    5. Cao, Zhiyu, et al. "Incomplete Utterance Rewriting with Editing Operation Guidance and Utterance Augmentation." arXiv preprint arXiv:2503.16043 (2025).

    6. Yang, Chenxiao, et al. "Pencil: Long thoughts with short memory." arXiv preprint arXiv:2503.14337 (2025).

3. ReAct模式，闭环

    7. Yao, Shunyu, et al. "React: Synergizing reasoning and acting in language models." International Conference on Learning Representations (ICLR). 2023.

    8. Kim, Jeonghye, et al. "ReflAct: World-Grounded Decision Making in LLM Agents via Goal-State Reflection." arXiv preprint arXiv:2505.15182 (2025).

    9. https://www.emergentmind.com/topics/react-style-agents

4. 通用智能的定义

    10. (数学化定义、在各种环境中实现目标的能力)Legg, Shane, and Marcus Hutter. "Universal intelligence: A definition of machine intelligence." Minds and machines 17 (2007): 391-444.

    11. (按性能深度和能力广度的分级定义)Morris, Meredith Ringel, et al. "Levels of AGI for Operationalizing Progress on the Path to AGI." arXiv preprint arXiv:2311.02462 (2023).

5. LLM的图灵完备性

    12. (Prompting+外挂 memory 模拟 15 states 2 symbols 通用图灵机 U15,2)Schuurmans, Dale. "Memory augmented large language models are computationally universal." arXiv preprint arXiv:2301.04589

    13. (2027 rules 262 symbols (2,2)-Lag system 模拟图灵机 U15,2)Schuurmans, Dale, Hanjun Dai, and Francesco Zanini. "Autoregressive large language models are computationally universal." arXiv preprint arXiv:2410.03170

    14. (特定有理数网络参数, 可模拟通用图灵机)Siegelmann, Hava T., and Eduardo D. Sontag. "On the computational power of neural nets." Proceedings of the fifth annual workshop on Computational learning theory. 1992.

6. 不同变种的图灵机计算模型对比

    15. https://en.wikipedia.org/wiki/Turing_machine

    16. https://en.wikipedia.org/wiki/Universal_Turing_machine

    17. https://en.wikipedia.org/wiki/Random-access_machine

    18. https://en.wikipedia.org/wiki/Random-access_stored-program_machine

    19. Sipser, Michael. "Introduction to the Theory of Computation." ACM Sigact News 27.1 (1996): 27-29.

    20. Arora, Sanjeev, and Boaz Barak. Computational complexity: a modern approach. Cambridge University Press, 2009.

    21. Hopcroft, John E., Rajeev Motwani, and Jeffrey D. Ullman. "Introduction to automata theory, languages, and computation." Acm Sigact News 32.1 (2001): 60-65.

    22. https://en.wikipedia.org/wiki/Wang_B-machine

    23. Neary, Turlough, et al. "Wang’s B machines are efficiently universal, as is Hasenjaeger’s small universal electromechanical toy." Journal of Complexity 30.5 (2014): 634-646.

    24. Woods, Damien, and Turlough Neary. "The complexity of small universal Turing machines: A survey." Theoretical Computer Science 410.4-5 (2009): 443-450.

    25. Hennie, Fred C., and Richard Edwin Stearns. "Two-tape simulation of multitape Turing machines." Journal of the ACM (JACM) 13.4 (1966): 533-546.

    26. Cook, Stephen A., and Robert A. Reckhow. "Time-bounded random access machines." Proceedings of the fourth annual ACM symposium on Theory of computing. 1972.

    27. Irani, Sandy, Moni Naor, and Ronitt Rubinfeld. "On the time and space complexity of computation using write-once memory or is pen really much worse than pencil?." Mathematical systems theory 25.2 (1992): 141-159.

## 附录

### A. 典型问题

下面是一些典型问题，供有兴趣的读者参考

一类任务：AI远超人类

1. 翻译为英文：人不一定是最优通用智能，但在AI彻底超过人之前，人的工作机制是构建AI不容忽视的参考对象。

2. 做数学题：证明勾股定理。

3. 写程序：解线性方程组。

二类任务：AI与人类各有千秋

4. 请参考链接[https://zhuanlan.zhihu.com/p/452976375]，证明威尔逊定理。这是初等数论中的非常基本的定理。

5. 写程序：一份代码中，判断某个具有较多参数的函数调用是否合格。

三类任务：人类强于AI

6. 数学题问答（IMO 2025 P1）：平面上一条直线被称为“阳光的”，如果它不与$x$轴，$y$轴，以及直线 $x+y=0$平行。给定一个整数 $n\geq0$。请确定所有非负整数 $k$，使得平面上存在 $n$ 条不同的直线满足如下条件：

    1. 对于每一对满足 $a+b\leq n$ 的正整数 $a,b$，点 $(a,b)$ 至少在其中一条直线上。

    2. 恰好有 $k$ 条直线是阳光的。

7. 对于一个中等大小软件项目，自动编程的时候，能不能全程自己决定什么时候读、写哪个文件的哪一部分？

很显然，所有这些问题，对于大部分人，哪怕是得到了非常良好训练的数学工作者或者程序员，也无法保证说出来的下一个单词一定是对的而不需要任何修改。

相反，对于一类任务，当前市面上的先进大语言模型，即便不借助任何额外的System2功能，System1仅凭借强大的多层Attention+FFN计算以及参数记忆能力，也都可以每字不差的输出答案。AI在这方面的能力远超人类。

这一优势，在二类任务里不再明显。即使是领域内广泛熟知的基本定理，随着答案长度增加，部分先进模型在输出答案时也会出现错误、冗余。

进一步，对于三类任务，我们很快就会发现：对于复杂、开放的（俗称模型没见过的）问题，System1很快会在输出答案的过程中，出现漏洞、产生误差累积，而最终无法得到正确答案。
