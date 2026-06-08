# Diffusion Process in AI

## 连续扩散模型

考虑$\mathbb{R}^N$上的随机过程，其中$N$是输入数据的维度，例如对$n\times m$的图片而言，$N=n\times m$，
$$
\mathrm{d}\pmb{X}=\pmb{\mu}(\pmb{X},t)\mathrm{d}t+\pmb{\sigma}(\pmb{X},t)\mathrm{d}\pmb{W}_t, \pmb{X}\in\mathbb{R}^N,t\in[0,T]
$$
记上述过程的扩散协方差矩阵
$$
\pmb{D}(\pmb{X},t)=\frac12\pmb{\sigma}\cdot\pmb{\sigma}^T\in\mathbb{R}^{N\times N}
$$
$\pmb{X}$的概率密度函数$p(\pmb{X},t)$随时间变化，满足[Fokker-Planck(FP)方程(Kolmogorov前向方程)](https://en.wikipedia.org/wiki/Fokker–Planck_equation)
$$
\begin{split}
\frac{\partial p}{\partial t}
&=-\nabla\cdot(\pmb{\mu}p)+\nabla^2:(\pmb{D}p)
=-\sum_{i=1}^{N}\partial_{x_i}(\mu_ip)+\sum_{i=1}^N\sum_{j=1}^N\partial_{x_ix_j}(D_{ij}p) \\
&= -\nabla\cdot\pmb{J}, \text{ where }\pmb{J}=\pmb{\mu}p-\nabla\cdot(\pmb{D}p), \pmb{D}=\pmb{D}^T
\end{split}
$$
