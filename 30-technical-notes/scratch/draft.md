---
type: scratch-note
status: draft
tags:
  - technical-notes
  - scratch
  - geometry
  - transformer
cssclasses:
  - textbook-math
---

# 草稿

## 余弦相似性与欧氏距离的换算

考虑$\pmb{A}\in\mathbb{R}^{n\times d},\pmb{B}\in\mathbb{R}^{m\times d}$分别表示$n$个/$m$个$d$维样本组成的矩阵，记$a_i=\pmb{A}[i,:]^T,b_j=\pmb{B}[j,:]^T\in\mathbb{R}^d$，记各样本的欧氏几何重心为$\bar{a}=\frac1n\sum_i a_i,\bar{b}=\frac1m\sum_j b_j$，并可**将$\pmb{A},\pmb{B}$各样本各自减去样本集中的均值（即 $\hat{a}_i=a_i-\hat{a},\hat{b}_j=b_j-\hat{b}$）得到$\hat{\pmb{A}}=\pmb{A}-\pmb{\mathscr{1}}_{n\times1}\cdot\bar{a}^T,\hat{\pmb{B}}=\pmb{B}-\pmb{\mathscr{1}}_{m\times1}\cdot\bar{b}^T$**，其中$\pmb{\mathscr{1}}_{c_1\times c_2}\in\mathbb{R}^{c_1\times c_2}$表示元素全为1的矩阵。

$\pmb{A},\pmb{B}(or \hat{\pmb{A}},\hat{\pmb{B}})$两个样本集各样本两两之间的$\mathscr{l}_2$距离组成的矩阵为
$$
\begin{aligned}
\pmb{D}\in\mathbb{R}^{n\times m}
  &: D_{ij}\triangleq\pmb{D}[i,j]=\|a_i-b_j\| \\
  &\qquad=\sqrt{(a_i-b_j)^T\cdot(a_i-b_j)} \\
\hat{\pmb{D}}\in\mathbb{R}^{n\times m}
  &: \hat{D}_{ij}\triangleq\hat{\pmb{D}}[i,j]=\|\hat{a}_i-\hat{b}_j\| \\
  &\qquad=\sqrt{(\hat{a}_i-\hat{b}_j)^T\cdot(\hat{a}_i-\hat{b}_j)}
\end{aligned}
$$
记$\pmb{D}^{(2)},\hat{\pmb{D}}^{(2)}\in\mathbb{R}^{n\times m}$表示$\pmb{D},\hat{\pmb{D}}$逐元素取平方$\pmb{D}^{(2)}[i,j]=D_{ij}^2,\hat{\pmb{D}}^{(2)}[i,j]=\hat{D}_{i,j}^2$。

$\hat{\pmb{A}},\hat{\pmb{B}}$两个样本集各样本两两之间的"余弦相似性"组成的矩阵为
$$
\hat{\pmb{A}}\cdot\hat{\pmb{B}}^T
$$
于是，类似于[Multidimensional Scaling(MDS)](https://en.wikipedia.org/wiki/Multidimensional_scaling)，**可以得到$\hat{\pmb{A}},\hat{\pmb{B}}$这两组样本之间余弦相似性与样本之间欧氏$\mathscr{l}_2$距离之间的换算关系**。
$$
\color{red}
\begin{split}
-\hat{\pmb{A}}\cdot\hat{\pmb{B}}^T&=\frac12(\pmb{I}_n-\frac1n\pmb{J}_n)\cdot\pmb{D}^{(2)}\cdot(\pmb{I}_m-\frac1m\pmb{J}_m)\\
&=\frac12(\pmb{I}_n-\frac1n\pmb{J}_n)\cdot\hat{\pmb{D}}^{(2)}\cdot(\pmb{I}_m-\frac1m\pmb{J}_m)
\end{split}\tag{1}
$$
^eq-mds-ab
其中，$\pmb{I}_s\in\mathbb{R}^{s\times s}$中的单位矩阵，$\pmb{J}_s=\pmb{\mathscr{1}}_{s\times s}\in\mathbb{R}^{s\times s}$是元素全为1的方阵。

***公式 [[#^eq-mds-ab|MDS 换算公式]] 的证明***

记$\pmb{X}=\frac12(\pmb{I}_n-\frac1n\pmb{J}_n)\cdot\pmb{D}^{(2)}\cdot(\pmb{I}_m-\frac1m\pmb{J}_m),X_{kl}\triangleq\pmb{X}[k,l]$，于是$\pmb{X}=\frac12\pmb{D}^{(2)}-\frac1{2n}\pmb{J}_n\cdot\pmb{D}^{(2)}-\frac1{2m}\pmb{D}^{(2)}\cdot\pmb{J}_m+\frac1{2nm}\pmb{J}_n\cdot\pmb{D}^{(2)}\cdot\pmb{J}_m$，
$$
\begin{aligned}
X_{kl}
  &=\frac12D_{kl}^2-\frac1{2n}\sum_{i=0}^{n-1}D_{il}^2
    -\frac1{2m}\sum_{j=0}^{m-1}D_{kj}^2
    +\frac1{2nm}\sum_{i=0,j=0}^{n-1,m-1}D_{ij}^2 \\
  &= \frac12(\|a_k\|^2+\|b_l\|^2-2a_k^T\cdot b_l) \\
  &\quad-\frac1{2n}\left(\sum_{i=0}^{n-1}\|a_i\|^2+n\|b_l\|^2-2na^T\cdot b_l\right) \\
  &\quad-\frac1{2m}\left(m\|a_k\|^2+\sum_{j=0}^{m-1}\|b_j\|^2-2ma_k^T\cdot b\right) \\
  &\quad+\frac1{2nm}\left(m\sum_{i=0}^{n-1}\|a_i\|^2+n\sum_{j=0}^{m-1}\|b_j\|^2
       -2\sum_{i,j}a_i^T\cdot b_j\right), \\
  &\quad\text{where }\frac1{nm}\sum_{i,j}a_i^T\cdot b_j=a^T\cdot b \\
  &=-a_k^T\cdot b_l+a^T\cdot b_l+a_k^T\cdot b-a^T\cdot b \\
  &=-(a_k-a)^T\cdot(b_l-b) \\
  &=-\hat{\pmb{A}}[k,:]\cdot\hat{\pmb{B}}[l,:]^T
\end{aligned}
$$
因此 $\pmb{X}=-\hat{\pmb{A}}\cdot\hat{\pmb{B}}^T$。

同理，可证明$\frac12(\pmb{I}_n-\frac1n\pmb{J}_n)\cdot\hat{\pmb{D}}^{(2)}\cdot(\pmb{I}_m-\frac1m\pmb{J}_m)=-\hat{\pmb{A}}\cdot\hat{\pmb{B}}^T$。

***证毕。***

直观理解公式 [[#^eq-mds-ab|MDS 换算公式]]，
$$
\begin{aligned}
\hat{\pmb{A}}[k,:]\cdot\hat{\pmb{B}}[l,:]^T
  &=-\frac12\hat{D}_{kl}^2 \\
  &\quad+{\color{blue}\frac12E_{\hat{a}\sim\hat{\pmb{A}}}
      \|\hat{a}-\hat{b}_l\|^2
      +\frac12E_{\hat{b}\sim\hat{\pmb{B}}}
      \|\hat{a}_k-\hat{b}\|^2}
      -\text{Constant}
\end{aligned}
\tag{2}
$$
^eq-mds-heuristic
上式**蓝色字体**部分，例如当$k,l$是固定数，当$n,m\to\infty$时，可能可以近似为常数。

## 与LLM Transformer Attention的不严格联系

记Attention模块的输入为$H\in\mathbb{R}^{n\times d}$，例如$n=2048,d=12288$，经过三个线性层分别计算$Q,K,V\in\mathbb{R}^{n\times d'}$，$d'$是Multi Heads Attention中单个Head的输出特征维数，一般来说$d'=\frac{d}{\text{heads num}}$，例如$\text{heads num}=96,d'=128$，
$$
\begin{split}
Q&=H\cdot W_Q^T+\pmb{\mathscr{1}}_{n\times1}\cdot b_Q^T \\
K&=H\cdot W_K^T+\pmb{\mathscr{1}}_{n\times1}\cdot b_K^T \\
V&=H\cdot W_V^T+\pmb{\mathscr{1}}_{n\times1}\cdot b_V^T \\
\end{split}
$$
其中$W_Q,W_K,W_V\in\mathbb{R}^{d'\times d}$，$b_Q,b_K,b_V\in\mathbb{R}^{d'\times1}$。

- 注意力的计算，$S=\text{softmax}(\frac{Q\cdot K^T}{\sqrt{d'}})$，如果偏置向量$b_Q,b_K$分别使得$Q,K$各行之均值(即各token特征之均值)接近0：$Q\approx\hat{Q},K\approx\hat{K}$，则依据[[#^eq-mds-heuristic|MDS 直观公式]]可知$Q\cdot K^T\approx\hat{Q}\cdot\hat{K}^T=-\frac12D_{Q,K}^{(2)}+\text{something}$。
- 使用$Q,K$的Fourier变换$FFT(Q),FFT(K)$代替$Q,K$计算$\text{softmax}(\frac{FFT(Q)\cdot FFT(K)^*}{\sqrt{d'}})$，1.Fourier系数矩阵乘法与原信号矩阵乘法的关系；2.Fourier系数的$\mathscr{l}_2$距离等于原信号的$\mathscr{l}_2$距离，可能有助于分析两者的区别。这部分较复杂，先到这。
