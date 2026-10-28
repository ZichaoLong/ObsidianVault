"""Presentation content and notes. Figures are bound to the existing HB example.

The narrative source is ../design-introduction-script.md. These compact screen
texts, stop-specific notes and references are used by both HTML and PDF.
"""
SOURCES = {
    'design': ('设计需求与架构关系', '../../memos/design/design-requirements-and-architecture.md'),
    'hb': ('HB 实例 §2：三层图上的两次输入', '../../instances/hb-lattice-weighted-message.md#2-三层图上的分叉汇合与记忆'),
    'topology': ('HB 拓扑', '../../topologies/hb-lattice.md'),
    'boundary': ('HB 实例 §1.4：输入、读出与任务', '../../instances/hb-lattice-weighted-message.md#14-输入读出与任务'),
    'framework': ('TimedDAG §4—5：节点与区域选择', '../../timed-dag-region-selector-learning-note.md#4-节点的局部函数'),
    'memory': ('共同局部架构 §3：状态与记忆描述', '../../local-semantics/weighted-message/architecture-learning-note.md#3-状态与记忆描述'),
    'cost': ('共同局部架构 S.2：工作量', '../../local-semantics/weighted-message/architecture-learning-note.md#s2-工作量'),
    'choices': ('局部设计总览', '../../memos/design/weighted-message-design.md'),
    'lm': ('研究问题 §2.1：语言模型接入', '../../memos/training/weighted-message-research-questions.md#21-语言模型接入'),
    'review': ('既有实现审视 §3.3：填充行上的算术', '../../records/reviews/2026-10-28-ascend-implementation-review.md#33-常驻设备路径保留数学稀疏但仍执行填充行上的算术'),
    'full': ('TimedDAG §13.4：改变 Full 的依赖', '../../timed-dag-region-selector-learning-note.md#134-让完整输出改变后续状态或选择'),
}


def step(title, lede, view, body='', graph=None, notes='', **kw):
    return dict(title=title, lede=lede, view=view, body=body, graph=graph, notes=notes, **kw)


def scores(values, selected=None):
    return '<div class="score-row">' + ''.join(f'<div class="score-cell {"selected" if i==selected else ""}"><small>节点 {i}</small>{v}</div>' for i,v in enumerate(values)) + '</div>'


SLIDES = [
    dict(chapter='01 · 从熟悉的计算出发', status='已确认目标', sources=['design'], steps=[
        step('Tide · 去中心化与稀疏化', '从输入到输出，理解内部计算怎样组织。', 'opening',
             notes='面向首次接触 Tide、了解顺序神经网络的听众。从熟悉的输入、计算、输出开始。画面中的计算框只是顺序计算示意，不代表 Tide 只能采用链式结构。'),
        step('扩大内部容量，约束每次参与', '在任务效果可比时，先减少参与节点和连接。', 'goals',
             notes='去中心化先聚焦模型的信息与决策局部性：单个节点直接通信的对象数保持有界，内部计算避免统一依赖固定主干或决策中心。设备部署和学习规则另议。全部区域参与可以接受，稀疏还可以发生在区内。')]),
    dict(chapter='02 · 固定端口与局部传播', status='条件推论', sources=['design','topology'], steps=[
        step('固定端口下，规模扩展需要多跳传播', '入口、出口保持固定；可达的内部节点继续增加。', 'expansion',
             notes='条件是固定端口配置、单节点直接收发对象数有界、结构上能受输入影响并影响输出的节点数继续增加。由有限跳数可达节点的计数上界，输入侧和输出侧的最大传播距离均需增长。不同模型可选不同的有限端口数，分别适用这个结论。此图表示多跳扩散与收拢，不指定唯一拓扑，也不要求每次输入访问全部容量。无界端口仅作范围外答疑，不引入接入适配方案。')]),
    dict(chapter='02 · 建立贯穿全场的小图', status='定义事实 · HB 实例', sources=['hb','topology'], steps=[
        step('四个区域，十二个节点', '入口 I → 左右两区 L／R → 出口 E。节点下标在每区内为 0、1、2。', 'graph',
             '<div class="eyebrow">固定的空间结构</div><div class="key">每区 3 个节点</div><p>同一张图连续处理两次输入。</p><div class="callout">先走完计算，再展开可替换设计。</div>', 'regions',
             notes='采用已有 HB 三层实例：b=2、h=1、n=3、N=2。入口与出口各一区，中间左右两区。接下来的画面保持节点位置和名称。'),
        step('每个节点只连接一组邻居', '每个相邻目标区：连接同编号和下一编号；下标按模 3 循环。', 'graph',
             '<div class="eyebrow">以 I₀ 为例</div><div class="key">I₀ → L₀、L₁<br>I₀ → R₀、R₁</div><div class="divider"></div><p>12 个静态节点<br>24 条静态内部边</p><p class="small">蓝线在本页仅表示 I₀ 的邻域。</p>', 'neighbors',
             notes='本页还没有输入，蓝线仅用于解释邻接。每条区域关系有 3×2=6 条节点边，四条区域关系共 24 条。一个应用输入稍后会注入三个固定图入口；经图读出形成一个应用输出。')]),
    dict(chapter='03 · 第一次输入', status='定义事实 · 具体绑定', sources=['hb','memory'], steps=[
        step('收到输入，先形成候选状态', '输入 h₀ = +1。消息写作（强度，内容），本次为（1，+1）。', 'graph',
             '<div class="eyebrow">逻辑时间 θ = 1</div><div class="history">I₀、I₁、I₂<br>都写入 +1</div><p>长期摘要都为 1。</p><div class="callout">先接收和记住，再决定谁执行完整计算。</div>', 'input0',
             notes='三个图入口都收到单位强度输入。当前采用 KV、时间摘要 sum、Read⁺。所有候选都形成新状态，Describe 读取本次写入后的状态。此时还没有区域控制和 Full。动画播放时间与逻辑时间是两个概念。'),
        step('区域选择 I₀ 执行 Full', '另外两个候选保留本次写入，当前不发送。', 'graph',
             '<div class="eyebrow">入口区评分</div>'+scores(['½','−¼','−2'],0)+'<p>控制：<b>（1，0，0）</b></p><div class="callout">本例 Full 原样输出当前内容；记忆参与评分。</div><p class="small">Read⁺ · 全部候选保留更新</p>', 'select0',
             notes='入口评分 s₀=1/2，s₁=3/4−M_{I₁,long}，s₂=−2。摘要为 1，因此评分为 (1/2,−1/4,−2)。正温度二次分配在 τ=1/8 下产生 (1,0,0)。I₁、I₂ 的写入被保留。本例 Full 的两条残差尺度为零，所以 G=u。')]),
    dict(chapter='03 · 传播与汇合', status='定义事实 · 具体绑定', sources=['hb'], steps=[
        step('一组局部发送，进入两个区域', 'I₀ 沿四条边发送；左右两区分别处理自己的候选。', 'graph',
             '<div class="eyebrow">逻辑时间 θ = 2</div><p><b>左区：</b>L₀、L₁ 收到<br>评分 2、1 → 选择 L₀</p><p><b>右区：</b>R₀、R₁ 收到<br>评分 0、1 → 选择 R₁</p><div class="callout">L₂、R₂ 本次没有接收。</div>', 'middle0',
             notes='I₀ 对每个目标区域广播到同编号和下一编号。左右两区先各自更新候选记忆，再在实际候选上使用评分。未接收的节点不参加本次选择。此时内部已产生 4 条消息，三个区域执行过 Full。'),
        step('两条路径，在出口区汇合', 'L₀ → E₀、E₁；R₁ → E₁、E₂。', 'graph',
             '<div class="eyebrow">逻辑时间 θ = 3</div><p>接收强度，按 E₀／E₁／E₂：</p><div class="key">（1，2，1）</div><p>聚合内容都为 +1。<br>写入权重都截断为 1。</p><div class="callout">出口区评分（0，2，0）<br>选择 E₁ 执行 Full。</div>', 'exit0',
             notes='E₁ 收到两条同内容消息，接收强度为 2；E₀、E₂ 各收到一条。聚合内容都为 +1。写入权重 w=min(1,r)，因此三个节点都按权重 1 写入。本页选择 E₁，下一页明确读出与外部残差。')]),
    dict(chapter='03 · 第一次计算完成', status='定义事实 · 输出边界', sources=['hb','boundary'], steps=[
        step('图的输出，形成应用表示', '三个图出口中，只有 E₁ 的端口产生（1，+1）。', 'graph',
             '<div class="eyebrow">读出与外部残差</div><p>图读出</p><div class="key equation">O₀ = +1</div><div class="divider"></div><p>y₀ = h₀ + O₀</p><div class="big-result equation">y₀ = +2</div><p class="small">标量语义例子；任务读出另行绑定。</p>', 'output0',
             notes='其余两个图出口缺席。ReadOut 汇总指定输出槽，得到 O₀=1；原实例取 Wout=αout=1，残差给出 y₀=2。这是一个应用输入到一个应用表示的完整计算。应用单输入单输出与图内部有三个固定入口、三个固定出口的边界分别说明。')]),
    dict(chapter='03 · 观察参与量', status='由本次路径直接计数', sources=['hb','cost'], steps=[
        step('全部区域参与，节点和连接仍可稀疏', '同一次输入中，候选准备、Full 与消息传播分别计量。', 'graph',
             '<div class="metric-row"><span>候选作用</span><strong>10</strong></div><div class="bar"><i style="width:83.333%"></i></div><div class="metric-row"><span>Full</span><strong class="gold">4</strong></div><div class="bar gold"><i style="width:33.333%"></i></div><div class="metric-row"><span>内部消息</span><strong>8</strong></div><div class="bar"><i style="width:33.333%"></i></div><p class="small">前两条以 12 个节点为参照；第三条以 24 条内部边为参照。</p>', 'output0',
             notes='候选数为 3+2+2+3=10；Full 每区一次，共 4；内部消息为 4+2+2=8，本次使用 8 条不同边。4/4 区域参与。每节点本次至多作用一次，所以本页的候选作用次数也等于不同候选节点数；其他运行须区分两者。外部注入 3 条和实际端口输出 1 条另计。少做 Full 仍留下准备、选择、记忆与通信成本。')]),
    dict(chapter='04 · 第二次输入与记忆', status='定义事实 · 跨次保留', sources=['hb','memory'], steps=[
        step('没有发送的 I₁，也保留了记忆', '第一轮结束后，节点状态留到下一次接收。', 'graph',
             '<div class="eyebrow">回看 I₁</div><div class="history">收到 +1<br>保存 [+1]</div><div class="divider"></div><p>第一轮控制为 0，<br>仍保留接收写入。</p><p class="small">绿色方块：节点已有记忆。<br>本页查看状态，不新增作用。</p>', 'memory0',
             notes='绿色标记显示第一次输入留下的记忆。I₁ 当时没有执行 Full，但它是接收候选，因此仍保留 +1。这里的列表只展示 KV value 历史，完整状态还包含时间、权重、key 和摘要等字段。'),
        step('再写入 −1，入口区的选择改变', '输入 h₁ = −1；I₁ 的长期摘要从 1 变为 0。', 'graph',
             '<div class="eyebrow">逻辑时间 θ = 6</div><div class="history">[+1，−1] → 摘要 0</div><p class="equation">s₁ = ¾ − M<sub>I₁,long</sub></p>'+scores(['½','¾','−2'],1)+'<p>本次选择 <b>I₁</b> 执行 Full。</p>', 'select1',
             notes='三个入口先写入 −1，长期摘要变为 0。I₁ 的评分从 −1/4 变为 3/4，因此在同样的二次分配规则下改由 I₁ 激活。此例展示记忆参与评分和两轮路径变化；不能推断删除第一条记忆一定改变第二次胜者，也不由此推断任务效果。')]),
    dict(chapter='04 · 新路径继续到输出', status='定义事实 · 第二次计算', sources=['hb'], steps=[
        step('不同的路径，留下不同的局部历史', 'I₁ 进入 L₁、L₂、R₁、R₂；左右区分别选择 L₁、R₂。', 'graph',
             '<div class="eyebrow">逻辑时间 θ = 7</div><p><b>L₁：此前收到过</b></p><div class="history">[+1，−1] → 0</div><div class="divider"></div><p><b>L₂：第一次收到</b></p><div class="history">[−1] → −1</div>', 'middle1',
             notes='左区在候选 1、2 上使用评分 1、0，选择 L₁；右区在候选 1、2 上使用评分 1、2，选择 R₂。L₁ 在时间 2 接收过但未激活，此时长期摘要为零；L₂ 到时间 7 才第一次接收，摘要为 −1。绿色方块也保留了本轮没有再次接收的旧状态。'),
        step('第二次计算完成：路径变了，计数相同', '出口接收强度变为（1，1，2）；仍选择 E₁ 输出。', 'graph',
             '<div class="eyebrow">逻辑时间 θ = 8</div><div class="key equation">O₁ = −1</div><div class="big-result equation">y₁ = −2</div><div class="divider"></div><p>候选 10 · Full 4<br>内部消息 8</p><p class="small">本例 Full 保留当前内容；历史通过评分影响路径。</p>', 'output1',
             notes='L₁ 发到 E₁、E₂；R₂ 发到 E₂、E₀。三个出口候选的内容都为 −1，分配仍选择 E₁，所以 O₁=−1、y₁=−2。两轮各自的候选/Full/消息为 10/4/8。两轮合计候选作用 20 次、不同候选节点 12 个；Full 8 次、不同激活节点 7 个。')]),
]

SLIDES += [
    dict(chapter='05 · 回看共同框架', status='定义事实 · 框架与绑定', sources=['framework','memory'], steps=[
        step('一次区域作用，有四个阶段', '从刚才的完整例子，提取共同的状态与计算依赖。', 'phases', mode=0,
             notes='P 聚合接收、形成候选状态并读取描述；S 根据候选描述与区域历史共同选择；U 为每个候选确定计算快照和下一持久状态；F 只对激活者执行 Full。P/S/U/F 是作用阶段，不是物理设备上的时间测量。'),
        step('状态采用，连接当前计算与未来作用', '本例所有候选保留接收更新；激活者再执行 Full。', 'phases', mode=1,
             notes='一般正典允许不同的状态采用规则。本例带权绑定采用 Read⁺，q_cmp=q_next=q_tilde，所有候选保留接收更新。Full 读取计算快照，而不是直接替换下一持久状态。若要让本次 Full 输出直接回写下一状态，需要重新论证相应语义。')]),
    dict(chapter='05 · 局部语义中的记忆接口', status='定义事实＋设计解释', sources=['memory','choices'], steps=[
        step('Mem 为选择提供本地历史信息', '先从记忆取得描述，再与当前接收组合。', 'memory', mode=0,
             notes='Mem 属于带权消息支线，供 Describe 使用。它提供两个描述向量和两个统计量，实际含义由记忆模块定义。Describe 将这些信息与当前接收组合，送入 SelStep。正典 Read 与节点状态保持更一般的定义。'),
        step('替换记忆，需要保持接口相容', 'KV 序列、循环矩阵有不同的写入和读取方式。', 'memory', mode=1,
             notes='上层希望选择能参考本地历史；下层不同模块有不同状态形状和检索方式。Mem/Describe 的分工允许在明确相容条件下连接描述与区域选择。这是当前设计解释，不据此声称接口最早就是按此历史顺序形成。替换模块后须检查信息、状态成本和组合性质。')]),
    dict(chapter='05 · 共同职责与可替换位置', status='定义事实＋设计取舍', sources=['framework','choices'], steps=[
        step('共同框架、拓扑与局部语义各有职责', '给定相容的函数、参数和边界，才形成一个完整模型。', 'layers',
             notes='共同框架规定节点、区域、状态、接口和依赖；拓扑选择连接、区域划分和时间；局部语义规定实际载荷、状态、描述、选择与输出函数。带权消息是一条局部支线，KV、循环记忆、评分与发送规则在其中分别选择。'),
        step('同一个目标，可以由多种构造回应', '比较时明确替换的位置，保留其余绑定，重新判断条件与代价。', 'choices',
             notes='HB 固定局部参数、增加深度可以保持直接通信与区域协调范围有界；全连接须区分固定宽度增深和增加宽度。Mem 的 sum/qry、循环记忆影响读写成本与历史信息；评分与发送影响协调范围、支持数和连续性。独立评分之后仍可有区域共同分配。')]),
    dict(chapter='06 · 上下层相互牵引', status='设计解释 · 代价与反馈', sources=['design','cost','review'], steps=[
        step('少做 Full，也会暴露准备成本', '上层目标提出约束；具体行为告诉我们哪里仍然昂贵。', 'feedback', mode=0,
             notes='本例 Full 只有 4 次，但候选准备有 10 次。若 Upd、Mem 查询或 Describe 已占主要工作，就需一起重审邻域、区域粒度和描述复杂度。既有实现审视还记录未活动填充行执行算术的情况，因此数学参与量与设备成本分别计量。本场未新增性能测量。'),
        step('记忆模块的差异，推动接口分工', '上下层通过明确的信息依赖和实际代价反复校准。', 'feedback', mode=1,
             notes='上层提出历史参与选择的需要；局部模块揭示序列和矩阵状态、摘要和查询的差异，推动把状态读取与候选描述分开论证。更换相容绑定可以处理部分取舍；若改变核心依赖则需要新的语义论证。这条图表达当前设计解释，不声称已证实历史形成顺序。')]),
    dict(chapter='06 · 下一步的验证', status='实验选择＋待验证判断', sources=['lm','design'], steps=[
        step('在可比任务效果下，比较参与与成本', '实验优先：Next Token 预测，应用边界采用单输入单输出。', 'experiment',
             notes='语言模型接入使用 token 嵌入 h_t、Tide 表示 y_t 和另行声明的词表读出。固定数据与上下文等比较条件，声明效果容差，再统计参与节点/边、Full、消息以及实际工作。标量例子只核对机制；本地记忆是否改善选择、稀疏是否以可比质量降低成本，需要完整任务证据。')]),
    dict(chapter='附页 · 算例条件备查', status='具体绑定 · 可复核', sources=['hb','boundary'], steps=[
        step('本场使用的一套完整绑定', '全部数字来自同一个 HB 三层实例；展示中的简写与参数在此对齐。', 'appendix',
             notes='完整参数以 HB 实例 §2 为准。b=2,h=1,n=3,N=2；偏移{0,1}；D=5。KV、sum、Read⁺、全部候选保留更新；独立评分、固定增益1、quad、k=1、η=0、τ=1/8、正典容量K=3。d=d_s=H_att=d_h=r_a=1、ε=1；聚合残差0；共享基座[0;√2]、适配器0、摘要投影√2；无限窗口、无旋转、距离偏置0，短期率log2/5、长期率0。评分隐藏宽度2，其余宽度按原例；Full的Attention与前馈残差尺度0，G=u。Wout=αout=1。正温度下恰好一位激活由评分间隔和分配条件得到，不由k=1单独保证。')]),
]
