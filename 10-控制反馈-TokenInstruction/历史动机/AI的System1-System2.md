# 历史动机：AI 的 System1 + System2

> 早期历史动机材料，保留原始论证脉络；当前结论见 [[../当前主线总览|当前主线总览]]。

---
基于生成式大语言模型的AI技术，我们建议解耦成两个部分来看，这种解耦的分析，可以帮助我们避免因整体技术的快速进展，而忽视局部技术的可能缺陷，进而，可以帮助我们在对整体技术的上限产生怀疑时，看到可能本质的突破点。

1. System1：**基础模型**，是AI工作方式的核心基石，种类相对有限，更新较慢

    1. 主要功能：用于 **predict next token\[s\]** 的神经网络

    2. 技术点：Transformer\(attention, linear attention\)、Mamba\(RNN\)、Diffusion\(block wise\)等神经网络及其训推方法

2. System2：基于System1生长，类型多样且发展快速

    3. 主要作用：基于System1的功能，提升应用体验

    4. 技术点：围绕System1展开的一系列能力提升方法，这包括Prompting\(chain of thought\)、RAG\(vector retrieval\)、Agent\(tool calls, context engineering, multi agent\)等等

其中，System1和System2之间交互的**媒介**，是**Token**，更具体的说，是基础模型的词表中的词。
