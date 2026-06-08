# Transformer and Beyond

为了让文章各部分的表述更准确，下面将使用数学符号、公式来表达各个网络架构的计算方式，由于内容中涉及的符号、上下标较多，为了方便理解及避免混淆，这里事先进行统一说明：

1. 用大写粗体字母表示<font color=red>矩阵</font>，例如$\pmb{A},\pmb{B}$。
2. 用小写粗体字母表示<font color=red>向量</font>，例如$\pmb{x},\pmb{h}$，且<font color=red>默认</font>情况下它们表示<font color=red>行向量</font>，因此向量-矩阵乘法通常是矩阵右乘，例如$\pmb{x}\in\mathbb{R}^d,\pmb{A}\in\mathbb{R}^{d\times d'}$，$\pmb{xA}\in\mathbb{R}^{d'}$，该向量-矩阵乘法计算结果也是行向量，这一约定与通常的PyTorch实现相匹配。
3. <font color=red>按行拼接</font>用方括号及分号表示：例如，输入序列$\pmb{u}^{[i_1]},\pmb{u}^{[i_2]},\cdots,\pmb{u}^{[i_T]}\in\mathbb{R}^d$组成$T$行的矩阵$\pmb{U}=[\pmb{u}^{[i_1]};\pmb{u}^{[i_2]};\cdots;\pmb{u}^{[i_T]}]\in\mathbb{R}^{T\times d}$；
   <font color=red>按列拼接</font>用方括号及逗号表示：例如$d$维向量$\pmb{x}=[\pmb{x}_1,\cdots,\pmb{x}_d]\in\mathbb{R}^d$，多个$T\times *$维矩阵的拼接$\pmb{X}=[\pmb{X}^{[i_1]},\cdots,\pmb{X}^{[i_h]}]\in\mathbb{R}^{T\times \sum_{1}^{h} *}$。
4. 用<font color=red>下标</font>表示<font color=red>矩阵或张量的索引</font>，下标维度与索引维度对应，下标表示方法遵从Matlab/Julia表示约定从1开始（非此类情况会进行说明）。例如，对向量$\pmb{x}$，用$\pmb{x}_k\in\mathbb{R}$表示它的第$k$个元素；对矩阵$\pmb{X}=[\pmb{x}^{[i_1]};\pmb{x}^{[i_2]};\cdots;\pmb{x}^{[i_T]}]\in\mathbb{R}^{T\times d}$，可用$\pmb{X}_{t}=\pmb{X}_{t,:}\in\mathbb{R}^d$表示$\pmb{x}^{[i_t]}$，用$\pmb{X}_{s:t}=\pmb{X}_{s:t,:}\in\mathbb{R}^{(t-s+1)\times d}$表示$[\pmb{x}^{[i_s]};\pmb{x}^{[i_{s+1}]};\cdots;\pmb{x}^{[i_t]}]$，。
5. 用[<font color=red>上标</font>]表示<font color=red>矩阵或张量的属性</font>。
   - 例如，针对一个输入序列$\pmb{X}\in\mathbb{R}^{T\times d}$，可能需要经过Query,Key,Value三个权重矩阵的线性变换，那么这三个权重矩阵可分别表示为$\pmb{W}^{[Q]},\pmb{W}^{[K]},\pmb{W}^{[V]}$；
   - 对于具有$N$层、每层具有$m$个注意头的多头注意力机制，在上标中增加对应属性描述即可，例如第$n\in\{1,\cdots,N\}$层，第$k\in\{1,\cdots,m\}$个注意力头，对应权重矩阵$\pmb{W}^{[Q,n,k]},\pmb{W}^{[K,n,k]},\pmb{W}^{[V,n,k]}$；
   - 由于张量较少有幂运算，在不引起混淆的情况下，可以省略方括号$[]$，例如前面例子中的$\pmb{x}^{[1]},\cdots,\pmb{x}^{[T]}$可写作$\pmb{x}^1,\cdots,\pmb{x}^T$。“集合+上标”不易混淆，一般不作说明，如$\mathbb{R}^d,\mathbb{R}^{T\times d},\mathbb{C}^{d\times d}$表示对应数域的向量、张量空间，其中$\mathbb{R},\mathbb{C}$分别表示实数集、复数集。
6. <font color=red>逐元素四则运算及einops求四则运算</font>
   - "$+,-,\odot,\div$"表示两个张量之间，逐元素加、减、乘(Hadamard积)、除。运算的两个张量对应维度要满足类似于[Numpy/PyTorch的Broadcasting机制](https://pytorch.org/docs/stable/notes/broadcasting.html)的要求：例如对向量及矩阵$\pmb{x}\in\mathbb{R}^d,\pmb{A},\pmb{B}\in\mathbb{R}^{T\times d}$，可定义$\pmb{A}\odot\pmb{B},\pmb{A}+\pmb{B}\in\mathbb{R}^{T\times d},\pmb{A}-\pmb{x},\pmb{A}\odot\pmb{x}\in\mathbb{R}^{T\times d}$。
   - 一类更广泛的运算符号$'\text{einsum notation}'\over{+/-/\odot/\div}$，可用于定义einops类型的加、减、乘、除，一般仅使用einops乘，且可适用于多个张量之间的运算，具体可参考[einops.einsum](https://einops.rocks/)。
7. <font color=red>内积、点积"$\cdot$" </font>：可用于表示向量、矩阵之间的乘法，在不混淆的情况下，可省略"$\cdot$"符号，例如$\pmb{x},\pmb{y}\in\mathbb{R}^d,\pmb{A}\in\mathbb{R}^{T\times d},\pmb{B}\in\mathbb{R}^{d\times l}: \pmb{x}\cdot\pmb{y},\pmb{x}\cdot\pmb{A},\pmb{xA}\in\mathbb{R}^T,\pmb{A}\cdot\pmb{B},\pmb{AB}\in\mathbb{R}^{T\times l}$。
8. <font color=red>多张量混合表示</font>：一些情况下，可能需要用一个符号表示多个张量，例如把模型运行过程的上下文状态张量放入一个集合中表示，可以用Calligraphic花写字体，例如$\mathcal{A,B,C,S}$。

## 原始Encoder-Decoder架构的Transformer

原始Transformer论文 [Attention is All you Need (neurips.cc)](https://proceedings.neurips.cc/paper_files/paper/2017/file/3f5ee243547dee91fbd053c1c4a845aa-Paper.pdf)

**一些参考** [原始Transformer论文的代码](https://github.com/tensorflow/tensor2tensor)，[PyTorch自带Transformer实现文档及代码](https://pytorch.org/docs/stable/generated/torch.nn.Transformer.html#torch.nn.Transformer)

在Transformer及各种语言模型中，输入的词元(Token)序列可经过嵌入模块转化成词向量序列，因此，我们可以用矩阵$\pmb{U}=[\pmb{u}^{[1]};\cdots;\pmb{u}^{[T]}]\in\mathbb{R}^{T\times d}$表示原始输入序列，其中$d$是词元嵌入维度，$T$是输入序列长度。

### 注意力机制

注意力机制涉及到查询(Query)、键(Key)、值(Value)，在自注意力中，这三者可通过对隐层输入序列$\pmb{X}\in\mathbb{R}^{T\times d}$进行线性变换得到。记线性变换的参数为${\color{orange}\pmb{W}^{[Q]},\pmb{W}^{[K]}}\in\mathbb{R}^{d\times d'},{\color{orange}\pmb{W}^{[V]}}\in\mathbb{R}^{d\times d^{[V]}}$，则$\pmb{Q},\pmb{K},\pmb{V}$的分别是
$$
\pmb{Q}=\pmb{X}\cdot{\color{orange}\pmb{W}^{[Q]}}=[\pmb{Q}_1;\cdots;\pmb{Q}_T],
\pmb{K}=\pmb{X}\cdot{\color{orange}\pmb{W}^{[K]}}=[\pmb{K}_1;\cdots;\pmb{K}_T]\in\mathbb{R}^{T\times d'},
\pmb{V}=\pmb{X}\cdot{\color{orange}\pmb{W}^{[V]}}=[\pmb{V}_1;\cdots;\pmb{V}_T]\in\mathbb{R}^{T\times d^{[V]}},
$$
上述从$\pmb{X}$到$Q,K,V$的线性变换以及之后提到的线性变换也可引入bias，这里省略。

#### 单头注意力

**单查询注意力** 给定单个查询(Query) $\pmb{q}\in\{\pmb{Q}_1,\cdots,\pmb{Q}_T\}$，注意力机制Attention计算该Query与所有Key之间的相似性，并作为权重用于各Value的加权求和
$$
\label{eq:attention-classical-form}
\text{Attention}(\pmb{q};\pmb{K},\pmb{V})=\text{Softmax}(\frac{\pmb{q}\cdot\pmb{K}^\text{T}}{\sqrt{d'}})\cdot\pmb{V}=\sum_t \alpha_t\pmb{V}_t\in\mathbb{R}^{d^{[V]}},
$$
这里$\text{Softmax}(\pmb{a})=\frac{[e^{\pmb{a}_1},\cdots,e^{\pmb{a}_T}]}{\sum_i e^{\pmb{a}_i}},\alpha_t=
\frac{\text{exp}(\pmb{q}\cdot\pmb{K}_t/\sqrt{d'})}{\sum_s\text{exp}(\pmb{q}\cdot\pmb{K}_s/\sqrt{d'})}$。其中，计算第$t$个Key的注意力权重$\pmb{q}\cdot\pmb{K}_t$也可替换为更一般的相似性函数$\frac{\pmb{q}\cdot\pmb{K}_t}{\sqrt{d'}}\triangleq\text{sim}(\pmb{q},\pmb{K}_t)$，
$$
\text{Attention}(\pmb{q};\pmb{K},\pmb{V})=\text{Softmax}([\text{sim}(\pmb{q},\pmb{K}_t)]_t)\cdot\pmb{V}\in\mathbb{R}^{d^{[V]}}.
$$
以序列中的某个输入$\pmb{X}_t$作为单查询的单头自注意力则可以记作
$$
\text{Attention}(\pmb{X}_t;\pmb{X})\triangleq\text{Attention}(\pmb{Q}_t;\pmb{K},\pmb{V}).
$$
上述自注意力机制没有序列位置的距离信息，若希望引入位置信息，一种方式是再自注意力中引入相对位置编码，例如[ALiBi位置编码](https://arxiv.org/abs/2108.12409)，
$$
\text{Attention}^{[\text{ALiBi}]}(\pmb{X}_t;\pmb{X})=\text{Softmax}([\text{sim}(\pmb{Q}_t,\pmb{K}_s)-\lambda|t-s|]_{s})\cdot\pmb{V}\in\mathbb{R}^{d^{[V]}}.
$$
实际端到端的运行中，可根据是否在原始输入中引入绝对(相对)位置编码（参考后续Transformer [Encoder-Decoder](#transformer-encoder-decoder)），如[RoPE](https://arxiv.org/abs/2104.09864)，来决定是否在Attention计算中引入例如ALiBi位置编码，因此后续对Attention的讨论中，省略位置编码相关的部分。

**序列自注意力** 基于上述单查询Attention公式，关于输入序列的完整的自注意力可以简单写作（用内积计算注意力权重相似度）
$$
\begin{split}
\text{FullAttention}(\pmb{X}) &= 
[\text{Attention}(\pmb{Q}_1;\pmb{K},\pmb{V});\text{Attention}(\pmb{Q}_2;\pmb{K},\pmb{V});\cdots,\text{Attention}(\pmb{Q}_T;\pmb{K},\pmb{V})]
\\
&= \text{Softmax}\left(\frac{1}{\sqrt{d'}}
\left[
\begin{array}{cccc}
\pmb{Q}_1\cdot\pmb{K}_1, & \pmb{Q}_1\cdot\pmb{K}_2, & \cdots, & \pmb{Q}_1\cdot\pmb{K}_T \\
\pmb{Q}_2\cdot\pmb{K}_1, & \pmb{Q}_2\cdot\pmb{K}_2, & \cdots, & \pmb{Q}_2\cdot\pmb{K}_T \\
\vdots,                  & \vdots,                  & \ddots, & \vdots                  \\
\pmb{Q}_T\cdot\pmb{K}_1, & \pmb{Q}_T\cdot\pmb{K}_2, & \cdots, & \pmb{Q}_T\cdot\pmb{K}_T \\
\end{array}
\right]
\right)
\cdot\left[\begin{array}{c}
\pmb{V}_1\\
\pmb{V}_2\\
\vdots\\
\pmb{V}_T
\end{array}\right] \\
&= \text{Softmax}(\frac{\pmb{Q}\cdot\pmb{K}^T}{\sqrt{d'}})\cdot\pmb{V} = \text{Softmax}\left(
\left[
\text{sim}(\pmb{Q}_i,\pmb{K}_j)
\right]_{i,j\in\{1,\cdots,T\}}
\right)\cdot\pmb{V}
\in\mathbb{R}^{T\times d^{[V]}},
\end{split}
$$
这里 $\text{Softmax}(\pmb{A})=[\text{Softmax}(\pmb{A}_1);\text{Softmax}(\pmb{A}_2);\cdots]$。

更一般的是掩码注意力MaskedAttention，对给定的输入序列$\pmb{X}\in\mathbb{R}^{T\times d}$，Attention掩玛矩阵为$\pmb{M}\in\mathbb{R}^{T\times T}$，通常$\pmb{M}$的元素为$0$或$1$，掩玛注意力机制为
$$
\text{MaskedAttention}(\pmb{X})=\text{Softmax}\left(\pmb{M}\odot\left[\text{sim}(\pmb{Q}_i,\pmb{K}_j)\right]_{i,j\in\{1,\cdots,T\}}\right)\cdot\pmb{V}.
$$
完整注意力可理解为元素全为$1$的掩码矩阵下的掩码注意力，也可叫做双向注意力，对自然语言处理任务，通常在编码器中使用，将整个输入序列进行编码。对于需要满足前后序列的因果关系的任务而言，例如用于逐个输出目标序列元素的解码器，一般设置$\pmb{M}$为下三角矩阵以表达因果关系，原始Transformer解码器所用的掩码$\pmb{M}$即为下三角全为$1$的矩阵，此情形也常被称为因果注意力。出于计算性能、模型效果考虑，还可将掩玛设置为[因果]滑动窗口稀疏掩玛、[因果]$\Lambda$形稀疏掩玛等。典型的不同掩玛设置，以$T=7$为例
$$
\pmb{M}^{[\text{Causal}]}=\left[
\begin{array}{ccccccc}
{\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{black}1}, & {\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{gray }0} \\
{\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}
\end{array}
\right],
\pmb{M}^{[\text{Causal,SWA}^{[3]}]}=\left[
\begin{array}{ccccccc}
{\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{black}1}, & {\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{gray }0}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{gray }0}, & {\color{gray }0}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{gray }0} \\
{\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{black}1}, & {\color{black}1}, & {\color{black}1}
\end{array}
\right],
\pmb{M}^{[\text{Causal},\Lambda^{[2]}]}=\left[
\begin{array}{ccccccc}
{\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{black}1}, & {\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{black}1}, & {\color{black}1}, & {\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{black}1}, & {\color{gray }0}, & {\color{black}1}, & {\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{black}1}, & {\color{black}1}, & {\color{gray }0}, & {\color{gray }0} \\
{\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{black}1}, & {\color{black}1}, & {\color{gray }0} \\
{\color{black}1}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }0}, & {\color{gray }1}, & {\color{black}1}, & {\color{black}1}
\end{array}
\right].
$$
当掩码$\pmb{M}$为因果掩码$\pmb{M}^{[\text{Causal}]}$时，上述序列单头自注意力实际就是
$$
\pmb{Y}=\left[\begin{array}{c}
\text{Attention}(\pmb{X}_1;\pmb{X}_{1:1})\\
\text{Attention}(\pmb{X}_2;\pmb{X}_{1:2})\\
\cdots\\
\text{Attention}(\pmb{X}_T;\pmb{X}_{1:T})
\end{array}
\right]\in\mathbb{R}^{T\times d}
$$

#### 多头注意力(Multi-Head Attention, MHA)

对于具有$m$个独立注意头（互不共享参数）的MHA，最终MHA模块的输出由各单注意头按列拼接，然后作线性变换再输出，最终的线性变换参数记作${\color{orange}\pmb{W}^{[O]}}\in\mathbb{R}^{md^{[V]}\times d}$，

以序列最末位输入$\pmb{X}_T$作为单查询的多头自注意力为例
$$
\pmb{Y}_T=\text{MHA}(\pmb{X}_T;\pmb{X})=[\text{Attention}^{[1]}(\pmb{X}_T;\pmb{X}),\cdots,\text{Attention}^{[m]}(\pmb{X}_T;\pmb{X})]\cdot{\color{orange}\pmb{W}^{[O]}}\in\mathbb{R}^d
$$
带掩码的序列多头自注意力则为
$$
\pmb{Y}=\text{MHA}^{[M]}(\pmb{X})=[\text{MaskedAttention}^{[1]}(\pmb{X}),\cdots,\text{MaskedAttention}^{[m]}(\pmb{X})]\cdot{\color{orange}\pmb{W}^{[O]}}\in\mathbb{R}^{T\times d}.
$$
通常，可将各单注意头$\pmb{V}$维度设置为$d^{[V]}=d/m$，许多当前LLM实现中也将$\pmb{Q},\pmb{K}$维度设置为$d'=d/m$。当掩码$\pmb{M}$为因果掩码$\pmb{M}^{[\text{Causal}]}$时，上述序列多头自注意力实际就是
$$
\pmb{Y}=\left[\begin{array}{c}
\text{MHA}(\pmb{X}_1;\pmb{X}_{1:1})\\
\text{MHA}(\pmb{X}_2;\pmb{X}_{1:2})\\
\cdots\\
\text{MHA}(\pmb{X}_T;\pmb{X}_{1:T})
\end{array}
\right]\in\mathbb{R}^{T\times d}
$$

### 前馈网络模块(Feed Forward Network, FFN)

FFN通常将给定的输入$\pmb{x}\in\mathbb{R}^d$映射到相同维度的向量$\pmb{y}\in\mathbb{R}^d$，例如可取作具有一个隐藏层的MLP，其参数为${\color{orange}\pmb{W}^{[U]}}\in\mathbb{R}^{d\times d^{[U]}},{\color{orange}\pmb{W}^{[D]}}\in\mathbb{R}^{d^{[U]}\times d},{\color{orange}\pmb{b}^{[U]}}\in\mathbb{R}^{d^{[U]}},{\color{orange}\pmb{b}^{[D]}}\in\mathbb{R}^d$，激活函数$\sigma$可取ReLU,SiLU,GELU等，原始Transformer取为ReLU
$$
\pmb{y}=\text{FFN}(\pmb{x})=\sigma(\pmb{x}\cdot\pmb{W}^{[U]}+b^{[U]})\cdot\pmb{W}^{[D]}+b^{[D]}\in\mathbb{R}^d,
$$
对于输入序列$\pmb{X}\in\mathbb{R}^{T\times d}$,
$$
\text{FFN}(\pmb{X})=[\text{FFN}(\pmb{X}_1);\text{FFN}(\pmb{X}_2);\cdots,\text{FFN}(\pmb{X}_T)]\in\mathbb{R}^{T\times d}.
$$

### 归一化

归一化函数主要作用是让模型的前传反传信号更稳定，改善模型函数性质，从而使得训练过程更稳定。下面是两种常用的归一化方法

- 层归一化(Layer Normalization, LN)，原始Transformer使用的是这种层归一化：层归一化具有参数${\color{orange}\pmb{\gamma},\pmb{\beta}}\in\mathbb{R}^d$，对于输入向量$\pmb{x}\in\mathbb{R}^d$，其计算过程为
  $$
  \text{LN}(\pmb{x})=\frac{\pmb{x}-\mu}{\sigma}\odot{\color{orange}\pmb{\gamma}}+{\color{orange}\pmb{\beta}}, \text{ where }\mu=\frac{\sum_i\pmb{x}_i}{d},\sigma=\sqrt{\frac{1}{d}\sum_i(\pmb{x}_i-\mu)^2}.
  $$

- 均方根层归一化(Root Mean Square Layer Normalization, RMSNorm)：RMSNorm具有参数${\color{orange}\pmb{\gamma}}\in\mathbb{R}^d$，对于输入向量$\pmb{x}\in\mathbb{R}^d$，其计算过程为
  $$
  \text{RMSNorm}(\pmb{x})=\frac{\pmb{x}}{\sqrt{\frac{1}{d}\sum_i\pmb{x}_i^2}}\odot{\color{orange}\pmb{\gamma}}.
  $$

对于序列输入，只需依次将归一化函数LN或RMSNorm作用在序列元素上，并类似于FFN拼接各输出结果即可。

### 编码器(Encoder)

编码器$\text{Encoder}$的输入是$\pmb{X}\in\mathbb{R}^{T\times d}$，输出$\text{Encoder}(\pmb{X})\in\mathbb{R}^{T\times d}$，其计算过程是
$$
\begin{split}
\pmb{X}' &= \pmb{X}+\text{FullMHA}(\text{LN}^{[1]}(\pmb{X})) \\ 
\text{Encoder}(\pmb{X}) &= \pmb{X}'+\text{FFN}(\text{LN}^{[2]}(\pmb{X}'))\\
\end{split}
$$

### 解码器(Decoder)

解码器$\text{Decoder}$的输入是$\pmb{X}\in\mathbb{R}^{T\times d}$，生成也就是解码输出单个隐层词向量表示$\text{Decoder}(\pmb{X}_T;\pmb{X}_{1:T-1})\triangleq\text{Decoder}(\pmb{X})\in\mathbb{R}^d$，对于通常的因果解码器其计算过程是
$$
\begin{split}
\pmb{X} &= \text{LN}^{[1]}(\pmb{X}) \\
\pmb{X}'_T &= \pmb{X}_T+\text{MHA}(\pmb{X}_T;\pmb{X}_{1:T})\in\mathbb{R}^d \\
\text{Decoder}(\pmb{X}) &= \pmb{X}'_T+\text{FFN}(\text{LN}^{[2]}(\pmb{X}'_T))\in\mathbb{R}^d,
\end{split}
$$
在训练中，常常将整个序列的解码表示同时输出，
$$
\begin{split}
\pmb{X}' &= \pmb{X}+\text{MHA}^{[M]}(\text{LN}^{[1]}(\pmb{X})) \\
\text{Decoder}^{[\text{Train}]}(\pmb{X}) &= \pmb{X}'+\text{FFN}(\text{LN}^{[2]}(\pmb{X}'))\in\mathbb{R}^{T\times d},
\end{split}
$$

### <span id=transformer-encoder-decoder>原始Transformer的Encoder-Decoder架构</span>

具体架构示意图可参考原始Transformer论文，下面使用公式说明其计算方式。

对于长度为$T$的输入词向量序列$\pmb{U}^{[\text{en}]}=[\pmb{u}^{[1,\text{en}]};\pmb{u}^{[2,\text{en}]};\cdots;\pmb{u}^{[T,\text{en}]}]\in\mathbb{R}^{T\times d}$，可能经过某种位置编码(Positional encoding)处理，转化为$\pmb{X}^{[\text{en}]}=[\pmb{x}^{[1,\text{en}]};\cdots;\pmb{x}^{[T,\text{en}]}]$，这里引入位置编码的方式，例如可能是
$$
\pmb{x}^{[t,\text{en}]}=\pmb{u}^{[t,\text{en}]}+W^{[PE,t,\text{en}]}
\text{ or }
\pmb{x}^{[t,\text{en}]}=\pmb{u}^{[t,\text{en}]}\pmb{R}^{[\theta,t,\text{en}]}.
$$
原始Transformer具有$N$个相同架构(不共享参数)的编码器及$N$个相同架构(不共享参数)的解码器。在上述位置编码步骤之后，Transformer的计算先经过编码阶段，再经过解码阶段。

**编码阶段** 第$n\in\{1,\cdots,N\}$层$\text{Encoder}^{[n]}$的输入$\pmb{X}^{[n-1,\text{en}]}$，输出$\pmb{X}^{[n,\text{en}]}=\text{Encoder}^{[n]}(\pmb{X}^{[n-1,\text{en}]})\in\mathbb{R}^{T\times d}$。最后一个编码器的输出$\pmb{X}^{[N,\text{en}]}$记作$\pmb{Z}$，编码阶段最终效果为将输入$\pmb{X}^{[0,\text{en}]}(=\pmb{X}^{[\text{en}]})$映射为$\pmb{Z}$。

**解码阶段** 解码阶段将被循环执行，每次循环新增生成一个输出。循环至第$t\in\{1,\cdots,T'\}$步时，第$n\in\{1,\cdots,N\}$层$\text{Decoder}^{[n]}$的输入是$[\pmb{Z};\pmb{X}^{[n-1,\text{de}]}_{1:t}]$，输出$\pmb{X}^{[n,\text{de}]}_t=\text{Decoder}^{[n]}([\pmb{Z};\pmb{X}^{[n-1,\text{de}]}_{1:t}])\in\mathbb{R}^d$。这里$\pmb{X}^{[0,\text{de}]}_{2:}$的每一行均由最后一层$\text{Decoder}$的输出$\pmb{X}^{[N,\text{de}]}_{t}$变换得到：

1. 将$\pmb{X}^{[N,\text{de}]}_{t}$经过输出词元分类器（如OutputEmbedding+Softmax）映射至词嵌入$\pmb{v}^{[t]}$及词元。
2. 将上述步骤生成的词元经过嵌入模块映射到词向量$\pmb{u}^{[t+1,\text{de}]}$。$\pmb{u}^{[*,\text{en}]}$是编码器的输入词向量序列，而$\pmb{u}^{[*,\text{de}]}$是解码器的输入词向量序列。
3. 将词向量$\pmb{u}^{[t+1,\text{de}]}$经过位置编码处理得到$\pmb{X}^{[0,\text{de}]}_{t+1}$。

注意，这里对解码阶段的[第一个词元设置](https://www.tensorflow.org/text/tutorials/transformer)特别进行说明：这里约定$\pmb{u}^{[1,\text{de}]}$是一个固定起始词元（例如记作\<start\>）对应的词向量，将这个词向量同样经过位置编码可得到$\pmb{X}^{[0,\text{de}]}_1$。在推理阶段，循环的停止时刻$T'$通常是取决于输出某种终止词元（例如可能记作\<EOS\>）时终止循环。

解码器的具体执行，也可参考下面的[Decoder-Only架构GPT](#decoder-only-gpt)一章中的图文说明。

## <span id=decoder-only-gpt>Decoder-Only架构GPT</span>

Decoder-Only架构舍弃了Encoder，仅包含Decoder，其典型代表是GPT系列

- GPT-1: [Improving Language Understanding by Generative Pre-Training (openai.com)](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf)
- GPT-2: [Language Models are Unsupervised Multitask Learners (openai.com)](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)
- GPT-3: [Language Models are Few-Shot Learners (neurips.cc)](https://papers.nips.cc/paper_files/paper/2020/file/1457c0d6bfcb4967418bfb8ac142f64a-Paper.pdf)

对于一个具有$N$个$\text{Decoder}$的GPT架构，沿用此前的变量名、函数记号及含义

- 输入输出词嵌入向量：$\pmb{u}^{[t]},\pmb{v}^{[t]}$
- 隐层变量：$\pmb{X}^{[n]}_{t}$，这里由于$\pmb{X}$的各行分别表示不同时间的隐层变量，因此与其他量不同，$t$放在隐层变量$\pmb{X}$下标处
- 解码器：$\text{Decoder}^{[n]}$
- 其他：词元$\text{token}^{[t]}$，位置编码(Positional encoding)，$\text{Softmax}$

GPT在广义上也可理解为具有[输入-状态-输出概念的RNN](https://arxiv.org/abs/2407.04620v1)，用$\pmb{\mathcal{S}}^{[t]}$表示其总体隐藏状态，则GPT的执行过程可用下面的流程图及公式表示

![[assets/fig/gpt-diagram.png]]

$$
\label{eq:gpt-form}
\begin{split}
\text{GPT-Update: } & {\color{blue}\pmb{\mathcal{S}}^{[T]}}={\color{blue}\pmb{\mathcal{S}}^{[T-1]}}.\text{append}(\pmb{X}_T^{[\ast]}) \\
\text{GPT-Output: } & \pmb{v}^{[T]}=\text{OutEmb}(\pmb{X}_T^{[N]}),
\end{split}
$$
其中，在上述Decoder-Only Transformer架构中，更新隐藏状态${\color{blue}\pmb{\mathcal{S}}^{[T]}}$时，只需计算新的$\pmb{X}_T^{[\ast]}$，$\text{Attention}$所用的键值对(Key-Value pair) $\pmb{X}_T^{[n]}\cdot{\color{orange}\pmb{W}^{[K,n]}},\pmb{X}_T^{[n]}\cdot{\color{orange}\pmb{W}^{[V,n]}}$也可保存，供后续$t>T$推理时使用而无需重复计算，这就是所谓的KV-Cache技术。

GPT架构的一个解读可参考博客[The GPT-3 Architecture, on a Napkin](https://dugas.ch/artificial_curiosity/GPT_architecture.html)。

GPT架构的一个易读实现可参考[karpathy/nanoGPT: The simplest, fastest repository for training/finetuning medium-sized GPTs. (github.com)](https://github.com/karpathy/nanoGPT)。

从前面的讨论可以看到，GPT的**参数量**为
$$
\text{Number}_{\text{params}}=O\left(N\cdot \big[m\cdot d\cdot(d'+d^{[V]})+d\cdot d^{[U]}\big]\right)
$$
基于已有的$T$个$\text{token}$生成下一个$\text{token}$的**计算量**为
$$
\label{eq:gpt-inference-cost}
\text{Inference}_{\text{cost}}=O\left(N\cdot \big[m\cdot (T+d)\cdot(d'+d^{[V]})+d\cdot d^{[U]}\big]\right)=O(\text{Number}_{\text{params}})+O(TNd)
$$
其中典型超参数设置$N=12$(GPT 125M)或$N=96$(GPT 175B)，中间维度$d=O(1000) \text{ or }O(10000), d'=d^{[V]}=d/m, d^{[U]}=4d$。

## 一些扩展讨论

根据$\eqref{eq:gpt-inference-cost}$，GPT的推理下一个token的复杂度随上下文序列长$T$线性增长，进一步，对一个序列长为$T$的训练数据，每个词元都可对应一个训练样本并生成其对应的perplexity损失函数值，因此训练复杂度随$T$平方增长，这种高复杂度极大的限制了上下文序列长度。

早期的[RNN技术](https://en.wikipedia.org/wiki/Recurrent_neural_network)，一般的说，对于一个输入序列信号$\{\pmb{u}^{[t]}\}_{1\leq t\leq T}$，RNN在每个时刻的处理流程可表达为**更新隐藏状态+输出信号**两个步骤

![[assets/fig/rnn-diagram.png]]
$$
\label{eq:rnn-form}
\begin{split}
\text{RNN Update: } & {\color{blue}\pmb{\mathcal{S}}^{[T]}}=\text{Update}^{[\text{RNN}]}({\color{blue}\pmb{\mathcal{S}}^{[T-1]}},\pmb{u}^{[T]}) \\
\text{RNN Output: } & \pmb{v}^{[T]}=\text{Output}^{[\text{RNN}]}({\color{blue}\pmb{\mathcal{S}}^{[T]}},\pmb{u}^{[T]}),
\end{split}
$$

其中$\text{Update}^{[\text{RNN}]}$可以是一个简单或复杂的函数，复杂的做法，例如可以是非线性方程的求解过程（只要能求训练所需的梯度或采用无梯度训练方法），而$\text{Output}^{[RNN]}$则可以取得较为简单（概念上，复杂计算都可放入$\text{Update}^{[\text{RNN}]}$中），例如由一个线性变换+非线性激活层组成。经典的RNN技术，隐层状态${\color{blue}\pmb{\mathcal{S}}^{[T]}}$维度固定，更新与输出$\text{Update}^{[\text{RNN}]},\text{Output}^{[RNN]}$是固定计算量的函数，因此RNN关于序列长度$T$的推理、训练复杂度是$O(1),O(T)$。

对比$\eqref{eq:gpt-form}$与$\eqref{eq:rnn-form}$，我们可以知道，采用因果掩码注意力的GPT本质上也是一种RNN，而导致GPT推理、训练复杂度为$O(T),O(T^2)$的原因是：${\color{blue}\pmb{\mathcal{S}}^{[T]}}$维度随$T$线性增长且$\text{Update},\text{Output}$的计算要遍历${\color{blue}\pmb{\mathcal{S}}^{[T]}}$。要解决GPT的$O(T)$推理复杂度问题，可以归结为如下问题：

**如何在能够保持上下文信息的同时让$\text{Update},\text{Output}$的计算量与$T$无关或为$\log(T)$量级**

## RNN型Transformer变种

许多尝试改良、替换Transformer的工作都借助了早期RNN的想法，侧重于让隐层状态${\color{blue}\pmb{\mathcal{S}}^{[T]}}$维度保持不变，因此$\text{Update},\text{Output}$的计算量自然与$T$无关。但对于一般的RNN，还有一个重要障碍：无法序列并行计算，每个时刻的隐藏状态依赖于前面所有的Token顺序计算。而从Linear Attention及之后的一系列工作，则属于特殊的RNN，可以进行序列并行计算。总体来说，它们的工作方式符合下面的架构：每个block的隐藏状态${\color{blue}\pmb{\mathcal{S}}^{[n,T]}}$依赖于上一时刻对应block的隐藏状态${\color{blue}\pmb{\mathcal{S}}^{[n-1,T]}}$及当前时刻上一block的输出$\pmb{X}^{[n-1]}_T$，
$$
\begin{split}
{\color{blue}\pmb{\mathcal{S}}^{[n,T]}}&={\color{blue}\pmb{\mathcal{S}}^{[n-,T]}}\circ\pmb{X}_T^{[n-1]}\\
&={\color{blue}\pmb{\mathcal{S}}^{[n,0]}}\circ\pmb{X}_1^{[n-1]}\circ\pmb{X}_2^{[n-1]}\circ\cdots\circ\pmb{X}_T^{[n-1]}
\end{split}
$$
类似于通常RNN的依时间顺序计算是采用第一个等式所对应的公式，而为了适配训练任务，希望一次处理长为$T$的序列，只要二元运算$\circ$满足结合律，即可基于第二个等式对应的公式，并行的计算${\color{blue}\pmb{\mathcal{S}}^{[1,T]}}$,再计算${\color{blue}\pmb{\mathcal{S}}^{[2,T]}},\cdots,{\color{blue}\pmb{\mathcal{S}}^{[N,T]}}$等等，而当前主流的方案如Mamba、RWKV、Kimi Linear等都符合这条约束。

![[assets/fig/sequence-parallel-rnn-diagram.png]]

### Linear Attention

本小结介绍RNN型Transformer变种的早期代表性工作 [Transformers are RNNs: Fast Autoregressive Transformers with Linear Attention (mlr.press)](https://proceedings.mlr.press/v119/katharopoulos20a/katharopoulos20a.pdf)

这篇文章是较早期提出“采用Causal掩码注意力的Transformer，本质上也是一种RNN”这一观点的工作。

Linear Attention的计算方式与原始Transformer的区别是，将$\eqref{eq:attention-classical-form}$的
$\alpha_t=\frac{\text{exp}(\frac{\pmb{q}\cdot\pmb{K}_t}{\sqrt{d'}})}{(\text{归一化变量})}$改成核函数形式$\frac{\pmb{\phi}(\pmb{q})\cdot\pmb{\phi}(\pmb{K}_t)}{(\text{归一化变量})}$，这里$\pmb{\phi}(\pmb{q})\in\mathbb{R}^{d'}$，
$$
\begin{split}
\text{Attention}^{[\text{Linear}]}(\pmb{q};\pmb{K},\pmb{V})
&=\sum_t\frac{\pmb{\phi}(\pmb{q})\cdot\pmb{\phi}(\pmb{K}_t)}{\pmb{\phi}(\pmb{q})\cdot\sum_s\pmb{\phi}(\pmb{K}_{s})}\cdot\pmb{V}_t\\
&=\frac{\big(\pmb{\phi}(\pmb{q})\cdot[\pmb{\phi}(\pmb{K})]^\text{T}\big)\cdot\pmb{V}}{\pmb{\phi}(\pmb{q})\cdot\sum_t\pmb{\phi}(\pmb{K}_{t})}=\frac{\pmb{\phi}(\pmb{q})\cdot\big(\big[\pmb{\phi}(\pmb{K})\big]^\text{T}\cdot\pmb{V}\big)}{\pmb{\phi}(\pmb{q})\cdot\sum_t\pmb{\phi}(\pmb{K}_{t})} \\
&=\frac{\pmb{\phi}(\pmb{q})\cdot\big({\color{blue}\sum_t\pmb{\phi}(\pmb{K}_t)\cdot\pmb{V}_t}\big)}{\pmb{\phi}(\pmb{q})\cdot{\color{blue}\sum_t\pmb{\phi}(\pmb{K}_{t})}}\in\mathbb{R}^{d^{[V]}} \\
\text{其中 }{\color{blue}\big[\pmb{\phi}(\pmb{K})\big]^\text{T}\cdot\pmb{V}} &= {\color{blue}\big[\pmb{\phi}(\pmb{K})\big]_{1:T-1}^\text{T}\cdot\pmb{V}_{1:T-1}}+\pmb{\phi}(\pmb{K}_T)^{[\text{T}]}\cdot\pmb{V}_T\in\mathbb{R}^{d'\times d^{[V]}},\\
{\color{blue}\sum_{t=1}^T\pmb{\phi}(\pmb{K}_t)} &= {\color{blue}\sum_{t=1}^{T-1}\pmb{\phi}(\pmb{K}_t)}+\pmb{\phi}(\pmb{K}_{T-1})\in\mathbb{R}^{d'},
\end{split}
$$

$\text{Attention}^{[\text{Linear}]}(\pmb{q};\pmb{K},\pmb{V})$的计算可随着$T$增量更新，一种最简化的做法是
$$
\text{Attention}^{[Linear]}(\pmb{q};\pmb{K},\pmb{V})=\frac{\pmb{q}\cdot({\color{blue}\pmb{K}^\text{T}\cdot\pmb{V}})}{{\color{blue}\pmb{1}\cdot\pmb{K}}\cdot\pmb{q}^\text{T}}.
$$


在每一层，Linear Attention将上下文信息压缩至固定维度的RNN隐藏状态${\color{blue}\pmb{\phi}(\pmb{K})^\text{T}\cdot\pmb{V}}\in\mathbb{R}^{d'\times d^{[V]}},{\color{blue}\sum_t\pmb{\phi}(\pmb{K}_t)}\in\mathbb{R}^{d'}$，与经典RNN一样，推理、训练复杂度为$O(1),O(T)$，而原始的Attention存储token wise的上下文信息$\pmb{K},\pmb{V}\in\mathbb{R}^{T\times\ast}$。

### 基于State Spaces Modeling的Mamba架构

Mamba架构的$\text{Decoder}$与Transformer完全不同，具体来说，假设第$n$层$\text{Decoder}^{[\text{Mamba},n]}$的输入是$\pmb{X}_t^{[n]}\in\mathbb{R}^d$，输出
$$
\begin{split}
\pmb{X}^{[n+1]}_t &= \text{Decoder}^{[\text{Mamba},n]}(\pmb{X}^{[n]}_t) \\
&= \pmb{X}^{[n]}_t+\text{Mixer}^{[\text{Mamba,n}]}(\text{RMSNorm}^{[n]}(\pmb{X}^{[n]}_t))\in\mathbb{R}^{d}
\end{split}
$$
其中，记$\pmb{X}^{[n,mi]}_t=\text{RMSNorm}^{[n]}(\pmb{X}^{[n]}_t)$，则$\delta\pmb{X}^{[n]}_t=\text{Mixer}^{[\text{Mamba},n]}(\pmb{X}^{[n,mi]}_t)$的计算过程是
$$
\begin{split}
{\color{blue}\pmb{X}^{[n,mem]}_t} &= \text{Linear}(\pmb{X}^{[n,mi]}_t),\pmb{r}^{[n,t]}=\text{Linear}(\pmb{X}^{[n,mi]}_t)\in\mathbb{R}^{d^{[in]}}\\
\pmb{X}^{[n,in]}_t &= \text{SiLU}\big({\color{orange}\pmb{c}^{[1]}}\odot{\color{blue}\pmb{X}^{[n,mem]}_t}+{\color{orange}\pmb{c}^{[2]}}\odot{\color{blue}\pmb{X}^{[n,mem]}_{t-1}}+\cdots+{\color{orange}\pmb{c}^{[K]}}\odot{\color{blue}\pmb{X}^{[n,mem]}_{t-K+1}}\big)\in\mathbb{R}^{d^{[in]}}, \text{ where }{\color{orange}\pmb{c}^{[k]}}\in\mathbb{R}^{d^{[in]}},\\
\delta\pmb{X}^{[n]}_t &= \text{Linear}(\text{SSM}^{[n]}(\pmb{X}^{[n,in]}_t)\odot\text{SiLU}(\pmb{r}^{[n,t]}))\in\mathbb{R}^{d}
\end{split}
$$
这里$\text{SiLU}$是SiLU激活函数，计算$\pmb{X}^{[n,in]}_t$需要提取过去时刻的相应变量${\color{blue}\pmb{X}^{[n,mem]}_{t-K+1:t}}$，针对每个维度作卷积核大小为$K$的卷积操作。$\text{SSM}^{[n]}$即所谓的状态空间模型，具有参数$\pmb{A}=-\exp({\color{orange}logA})\in\mathbb{R}^{d^{[in]}\times d^{[state]}},{\color{orange}\pmb{D}}\in\mathbb{R}^{d^{[in]}}$，以及隐藏状态${\color{blue}\pmb{H}^{[n]}_{t-1}}\in\mathbb{R}^{d^{[in]}\times d^{[state]}}$，其计算方式如下
$$
\begin{split}
\pmb{\Delta} &= \frac1\beta\log\big(1+\exp(\beta\cdot\text{Linear}^{[rankdt]}(\pmb{X}^{[n,in]}_t))\big)\in\mathbb{R}^{d^{[in]}}\\
\pmb{B} &= \text{Linear}(\pmb{X}^{[n,in]}_t),\pmb{C}=\text{Linear}(\pmb{X}^{[n,in]}_t)\in\mathbb{R}^{d^{[state]}} \\
{\color{blue}\pmb{H}^{[n]}_t} &= \pmb{\Delta}{\text{din,din dstate}\to\text{din dstate}\over\odot}\big(\pmb{A}\odot{\color{blue}\pmb{H}^{[n]}_{t-1}}\big)+\big(\pmb{\Delta}\odot\pmb{X}^{[n,in]}_t\big){\text{din,dstate}\to\text{din dstate}\over\odot}\pmb{B}\in\mathbb{R}^{d^{[in]}\times d^{[state]}} \\
\text{SSM}^{[n]}(\pmb{X}^{[n,in]}_t) &= \pmb{C}^{\text{T}}\cdot({\color{blue}\pmb{H}^{[n]}_t})^{\text{T}}+\pmb{X}^{[n,in]}_t\odot{\color{orange}\pmb{D}}\in\mathbb{R}^{d^{[in]}}.
\end{split}
$$
原始论文[[2312.00752] Mamba: Linear-Time Sequence Modeling with Selective State Spaces (arxiv.org)](https://arxiv.org/abs/2312.00752)，[[2405.21060] Transformers are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality (arxiv.org)](https://arxiv.org/abs/2405.21060)包含许多与实现无关的内容，以上细节讨论主要参考下面的mamba-minimal实现。

- [johnma2006/mamba-minimal: Simple, minimal implementation of the Mamba SSM in one file of PyTorch. (github.com)](https://github.com/johnma2006/mamba-minimal/tree/master)
- [alxndrTL/mamba.py: A simple and efficient Mamba implementation in pure PyTorch and MLX. (github.com)](https://github.com/alxndrTL/mamba.py)
- [state-spaces/mamba: Mamba SSM architecture (github.com)](https://github.com/state-spaces/mamba)

### RWKV架构

RWKV架构也是一种固定隐藏变量维度的RNN，各个版本的实现可参考论文及代码

- [ChatRWKV/RWKV_in_150_lines.py at main · BlinkDL/ChatRWKV (github.com)](https://github.com/BlinkDL/ChatRWKV/blob/main/RWKV_in_150_lines.py)
- [ChatRWKV/rwkv_pip_package at main · BlinkDL/ChatRWKV](https://github.com/BlinkDL/ChatRWKV/tree/main/rwkv_pip_package)
- [BlinkDL/RWKV-LM: RWKV ](https://github.com/BlinkDL/RWKV-LM/tree/main)
- [[2305.13048v2] RWKV: Reinventing RNNs for the Transformer Era (arxiv.org)](https://arxiv.org/abs/2305.13048v2)
- [[2404.05892] Eagle and Finch: RWKV with Matrix-Valued States and Dynamic Recurrence (arxiv.org)](https://arxiv.org/abs/2404.05892)

具体来说，假设第$n$层$\text{Decoder}^{[\text{RWKV},n]}$的输入是$\pmb{X}_t^{[n]}\in\mathbb{R}^d$，输出$\pmb{X}^{[n+1]}_t=\text{Decoder}^{[\text{RWKV},n]}(\pmb{X}^{[n]}_t)\in\mathbb{R}^d$，RWKV的各个版本遵循如下计算方式，区别在于$\text{TimeMixer},\text{ChannelMixer}$内部实现的不同
$$
\begin{split}
\pmb{X}'^{[n]}_t &= \text{Norm}^{[n,1]}(\pmb{X}^{[n]}_t) \\
\pmb{X}''^{[n]}_t &= \pmb{X}^{[n]}_t+\text{TimeMixer}^{[\text{RWKV,n}]}(\pmb{X}'^{[n]}_t)\in\mathbb{R}^{d}\\
\pmb{X}'''^{[n]}_t &= \text{Norm}^{[n,2]}(\pmb{X}''^{[n]}_t) \\
\pmb{X}^{[n+1]}_t &= \pmb{X}''^{[n]}_t+\text{ChannelMixer}^{[\text{RWKV,n}]}(\pmb{X}'''^{[n]}_t)\in\mathbb{R}^{d}
\end{split}
$$

#### RWKV-v4

RWKV-v4的实现与论文描述大致一致，但在一些细节处可能有些许差异，我们下面介绍论文中的版本，$\text{TimeMixer},\text{ChannelMixer}$的计算过程是
$$
\begin{split}
\pmb{r}^{[\text{Time}]} &= {\color{orange}\pmb{W}^{[\text{Time},n,r]}}\cdot\big({\color{orange}\pmb{\mu}^{[\text{Time},n,r]}}\odot\pmb{X}'^{[n]}_t+(1-{\color{orange}\pmb{\mu}^{[\text{Time},n,r]}})\odot{\color{blue}\pmb{X}'^{[n]}_{t-1}}\big)\in\mathbb{R}^{d} \\
\pmb{k}^{[\text{Time}]} &= {\color{orange}\pmb{W}^{[\text{Time},n,k]}}\cdot\big({\color{orange}\pmb{\mu}^{[\text{Time},n,k]}}\odot\pmb{X}'^{[n]}_t+(1-{\color{orange}\pmb{\mu}^{[\text{Time},n,k]}})\odot{\color{blue}\pmb{X}'^{[n]}_{t-1}}\big)\in\mathbb{R}^{d} \\
\pmb{v}^{[\text{Time}]} &= {\color{orange}\pmb{W}^{[\text{Time},n,v]}}\cdot\big({\color{orange}\pmb{\mu}^{[\text{Time},n,v]}}\odot\pmb{X}'^{[n]}_t+(1-{\color{orange}\pmb{\mu}^{[\text{Time},n,v]}})\odot{\color{blue}\pmb{X}'^{[n]}_{t-1}}\big)\in\mathbb{R}^{d} \\
\pmb{wkv} &= \frac{e^{-{\color{orange}\pmb{w}}}\odot{\color{blue}\pmb{a}^{[n,t-1]}}+e^{{\color{orange}\pmb{u}}+\pmb{k}^{[\text{Time}]}}\odot\pmb{v}^{[\text{Time}]}}{e^{-{\color{orange}\pmb{w}}}\odot{\color{blue}\pmb{b}^{[n,t-1]}}+e^{{\color{orange}\pmb{u}}+\pmb{k}^{[\text{Time}]}}}\in\mathbb{R}^d \\
{\color{blue}\pmb{a}^{[n,t]}} &= e^{-{\color{orange}\pmb{w}}}\odot{\color{blue}\pmb{a}^{[n,t-1]}}+e^{\pmb{k}^{[\text{Time}]}}\odot\pmb{v}^{[\text{Time}]}\in\mathbb{R}^d \\
{\color{blue}\pmb{b}^{[n,t]}} &= e^{-{\color{orange}\pmb{w}}}\odot{\color{blue}\pmb{b}^{[n,t-1]}}+e^{\pmb{k}^{[\text{Time}]}}\in\mathbb{R}^d \\
\text{TimeMixer}^{[\text{RWKV},n]}(\pmb{X}'^{[n]}_t) &= {\color{orange}\pmb{W}^{[\text{Time},n,o]}}\cdot(\sigma(\pmb{r}^{[\text{Time}]})\odot\pmb{wkv})\in\mathbb{R}^d \\
\pmb{r}^{[\text{Channel}]} &= {\color{orange}\pmb{W}^{[\text{Channel},n,r]}}\cdot\big({\color{orange}\pmb{\mu}^{[\text{Channel},n,r]}}\odot\pmb{X}'''^{[n]}_t+(1-{\color{orange}\pmb{\mu}^{[\text{Channel},n,r]}})\odot{\color{blue}\pmb{X}'''^{[n]}_{t-1}}\big)\in\mathbb{R}^{d} \\
\pmb{k}^{[\text{Channel}]} &= {\color{orange}\pmb{W}^{[\text{Channel},n,k]}}\cdot\big({\color{orange}\pmb{\mu}^{[\text{Channel},n,k]}}\odot\pmb{X}'''^{[n]}_t+(1-{\color{orange}\pmb{\mu}^{[\text{Channel},n,k]}})\odot{\color{blue}\pmb{X}'''^{[n]}_{t-1}}\big)\in\mathbb{R}^{d} \\
\text{ChannelMixer}^{[\text{RWKV},n]}(\pmb{X}'''^{[n]}_t) &= \sigma(\pmb{r}^{[\text{Channel}]})\odot({\color{orange}\pmb{W}^{[\text{Channel},n,v]}}\cdot\text{ReLU}(\pmb{k}^{[\text{Channel}]})^2)\in\mathbb{R}^{d}
\end{split}
$$
在RWKV-5,RWKV-6中，则将$\pmb{wkv}$所涉及的RNN隐藏变量由$\pmb{a}^{[n,t]},\pmb{b}^{[n,t]}\in\mathbb{R}^d$改为$\pmb{k}^\text{T}\cdot\pmb{v}\in\mathbb{R}^{d\times d}$并考虑使用MultiHead，这类似于Linear Attention，但加上了time decay机制，这里不再详细讨论。

### Kimi Linear及其他有意思的文章

一些其他有意思的文章，这里仅列出，不再详细讨论

- [[2510.26692] Kimi Linear: An Expressive, Efficient Attention Architecture](https://arxiv.org/abs/2510.26692)
- [GitHub - MoonshotAI/Kimi-Linear](https://github.com/MoonshotAI/Kimi-Linear)
- [[2407.04620] Learning to (Learn at Test Time): RNNs with Expressive Hidden States (arxiv.org)](https://arxiv.org/abs/2407.04620)
- [[2407.01178] $\text{Memory}^3$: Language Modeling with Explicit Memory (arxiv.org)](https://arxiv.org/abs/2407.01178)
- [[2406.06484] Parallelizing Linear Transformers with the Delta Rule over Sequence Length (arxiv.org)](https://arxiv.org/abs/2406.06484)
- [[2407.04153] Mixture of A Million Experts (arxiv.org)](https://web3.arxiv.org/abs/2407.04153)
