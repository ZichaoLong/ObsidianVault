#!/usr/bin/env python3
"""Build the self-contained HTML, speaker notes and editable SVG figures."""
from pathlib import Path
from html import escape
import importlib.util
import json
import sys

sys.dont_write_bytecode=True

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]


def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


content=module('intro_content',HERE/'content.py')
fig=module('intro_figures',BASE/'figures/src/design_introduction.py')


def phases(mode):
    descriptions=[('P','准备','聚合接收<br>候选状态与描述'),('S','选择','区域共同选择<br>返回激活者与控制'),('U','状态采用','确定计算快照<br>与下一持久状态'),('F','完整计算','激活者执行 Full<br>沿图输出')]
    blocks=''.join(f'<div class="phase {"focus" if mode and i==2 else ""}"><b>{letter}</b><h3>{label}</h3><p>{desc}</p></div>' for i,(letter,label,desc) in enumerate(descriptions))
    lower='<span>本例：候选新状态 q̃</span><b>→</b><span>计算快照 q<sup>cmp</sup> = q̃<br>下一状态 q<sup>next</sup> = q̃</span><b>→</b><span>Full 读取计算快照<br>未来接收使用下一状态</span>' if mode else '<span>节点分别持有状态</span><span>区域在候选描述上协调</span><span>沿正时延边传播</span>'
    return f'<div class="phase-grid">{blocks}</div><div class="state-strip">{lower}</div><div class="callout">{"Read⁺、全部候选保留更新，是当前带权绑定的选择。" if mode else "共同框架规定接口与依赖，具体绑定确定状态和函数。"}</div>'


def memory(mode):
    left='<div class="memory-list"><h3>本节点的状态</h3><div>过去接收留下的信息</div></div>' if mode==0 else '<div class="memory-list"><h3>KV 序列</h3><div>带时间与权重的条目</div></div><div class="memory-list"><h3>循环矩阵</h3><div>固定形状的累积状态</div></div>'
    return f'<div class="memory-layout"><div>{left}</div><div><div class="flow"><div class="flow-box accent"><strong>Mem</strong><span>取得记忆描述</span></div><div class="flow-arrow">→</div><div class="flow-box"><strong>Describe</strong><span>构造候选描述</span></div><div class="flow-arrow">→</div><div class="flow-box"><strong>SelStep</strong><span>区域共同选择</span></div></div><div class="underflow">当前接收：内容、强度等</div></div></div><div class="callout" style="margin-top:45px">{"接口提供相同职责；信息保留、读写成本与组合性质随模块变化。" if mode else "带权支线：Mem 提供历史信息，Describe 将其与当前接收组合。"}</div><p class="small" style="margin-top:23px">正典的节点状态与 Read 保持一般性；Mem 的两个通道属于带权支线。</p>'


def feedback(mode):
    items=[('上层目标','减少完整计算'),('机制选择','选择前形成描述'),('下层观察','候选写入、记忆查询<br>仍可能昂贵'),('重审设计','邻域、区域大小<br>描述复杂度')] if mode==0 else [('上层需要','让本地历史<br>参与选择'),('局部方案','KV 序列<br>或循环矩阵'),('下层差异','状态、查询方式<br>与成本不同'),('明确接口','Mem 读取历史<br>Describe 组合描述')]
    nodes='<div class="flow-arrow">→</div>'.join(f'<div class="feedback-node"><h3>{a}</h3><p>{b}</p></div>' for a,b in items)
    return f'<div class="feedback"><div class="feedback-line">{nodes}</div><div class="return-path"><b>← 用具体行为与代价，重新检查上层要求</b></div></div><div class="callout">{"例子中的准备 10 次、Full 4 次，必须分别观察；设备实际工作另计。" if mode==0 else "相容绑定可以替换；改变核心状态依赖，需要重新论证语义。"}</div>'


def body(s):
    v=s['view']
    if v=='graph':
        legend='' if s['graph'] in ('regions','neighbors') else '<div class="legend"><span><i class="dot ring"></i>本轮候选</span><span><i class="dot"></i>已执行 Full</span><span><i class="dot mem"></i>已有记忆</span><span><i class="dot line"></i>本轮消息</span></div>'
        return f'<div class="graph-layout"><div class="graph-area">{fig.graph(s["graph"])}{legend}</div><div class="side">{s["body"]}</div></div>'
    if v=='opening':
        return '<div class="central"><div style="font-size:57px;line-height:1.45;font-weight:650;margin:8px 0 17px">让更大的内部容量，<br>通过<span class="blue">局部计算</span>完成输入到输出。</div><p style="font-size:27px;color:var(--muted);margin:12px 0 25px">先沿熟悉的计算过程，逐步建立节点、区域与记忆。</p><div class="chain-wrap">'+fig.chain()+'</div></div>'
    if v=='goals':
        return '<div class="two-cols"><div class="goal"><div class="number">01 / 去中心化</div><h2>信息与决策在局部形成</h2><p>单节点直接通信对象数有界。<br>内部避免统一依赖固定主干<br>或决策中心。</p><div class="callout">设备部署和学习规则另议。</div></div><div class="goal"><div class="number">02 / 稀疏化</div><h2>减少参与节点与连接</h2><p>在任务效果可比时，优先减少<br>完整计算与消息传播。</p><div class="callout">经过全部区域可以接受，<br>每个区域内部仍可稀疏参与。</div></div></div>'
    if v=='expansion':
        return '<div class="spread-layout"><div>'+fig.expansion()+'<div class="callout">扩大可达内部节点规模，需要逐步扩散与收拢。</div></div><div><div class="eyebrow">条件同时成立</div><div class="condition"><b>1</b> 固定入口与出口数量</div><div class="condition"><b>2</b> 直接收发对象数有界</div><div class="condition"><b>3</b> 扩大输入到输出的可达容量</div><p class="small" style="margin-top:28px">不同模型可另选有限端口数；<br>分别考察固定配置下的扩展。</p></div></div>'
    if v=='phases':return phases(s['mode'])
    if v=='memory':return memory(s['mode'])
    if v=='layers':
        return '<div class="layer-list"><div class="layer"><small>共同框架</small><h2>什么对象、什么依赖</h2><p>节点与区域<br>状态、接口、作用顺序</p></div><div class="layer"><small>拓扑</small><h2>连向哪里、何时到达</h2><p>节点连接、区域划分<br>端口与时间</p></div><div class="layer"><small>局部语义</small><h2>具体怎样计算</h2><p>载荷、状态与描述<br>选择和输出函数</p></div></div><div class="callout" style="margin-top:34px">本场的一套绑定：HB 拓扑 ＋ 带权消息 ＋ KV／sum ＋ 二次分配 ＋ 给定边界。</div>'
    if v=='choices':
        return '<table class="comparison"><thead><tr><th>选择位置</th><th>比较的构造</th><th>要重新判断</th></tr></thead><tbody><tr><td>拓扑与区域</td><td>HB ／ 全连接分层<br><span class="small">分别考察增宽与增深</span></td><td>直接邻居、协调范围<br>候选数量、传播深度</td></tr><tr><td>记忆与描述</td><td>KV：摘要 sum ／ 查询 qry<br>相容的循环记忆</td><td>保留哪些信息<br>读取与存储成本</td></tr><tr><td>评分与发送</td><td>独立 ／ 区域 Attention 评分<br>二次分配 ／ 硬选择等</td><td>额外协调、激活数量<br>发送总量、连续性</td></tr></tbody></table><p class="small" style="margin:22px 23px">发送总强度、激活节点数和设备成本分别计量；框架也容纳稠密参照。</p>'
    if v=='feedback':return feedback(s['mode'])
    if v=='experiment':
        return '<div class="flow"><div class="flow-box"><strong>token 嵌入</strong><span>hₜ</span></div><div class="flow-arrow">→</div><div class="flow-box accent"><strong>Tide</strong><span>输出表示 yₜ</span></div><div class="flow-arrow">→</div><div class="flow-box"><strong>词表分布</strong><span>预测下一 token</span></div></div><div class="evidence"><div><h3>例子已说明</h3><p>局部状态与区域选择<br>两次完整计算与稀疏路径</p></div><div><h3>任务实验仍需回答</h3><p>本地历史是否改善选择<br>可比效果下是否降低总工作</p></div></div><div class="callout">声明数据、上下文与效果容差，再比较节点、连接、Full、消息和实际成本。</div>'
    if v=='appendix':
        return '<div class="appendix"><div><div class="block"><h3>图与时间</h3><p>b = 2，h = 1，n = 3，N = 2<br>偏移 {0, 1}；D = 5<br>两轮逻辑时间：1／2／3，6／7／8</p></div><div class="block"><h3>记忆与内容</h3><p>KV · sum · Read⁺<br>全部候选保留写入；Full：G = u<br>应用残差：yₜ = hₜ + Oₜ</p></div></div><div><div class="block"><h3>区域选择</h3><p>独立评分 · 正温度二次分配<br>k = 1，η = 0，τ = 1/8；容量 K = 3</p><p class="small">评分间隔使本例恰好一位激活；<br>k = 1 本身不普遍保证只激活一位。</p></div><div class="block"><h3>边界与统计</h3><p>每轮内部：10 候选／4 Full／8 消息<br>外部另计：3 次注入／1 次端口输出</p></div></div></div>'
    raise ValueError(v)


def main():
    generated=BASE/'figures/design-introduction'
    generated.mkdir(exist_ok=True)
    for stage in ('regions','neighbors','input0','select0','middle0','exit0','output0','memory0','input1','select1','middle1','output1'):
        (generated/f'hb-{stage}.svg').write_text(fig.graph(stage))
    (generated/'sequential.svg').write_text(fig.chain())
    (generated/'bounded-propagation.svg').write_text(fig.expansion())
    frames=[];metadata=[];notes=['# Tide 展示讲者备注\n','由 [content.py](content.py) 生成；讲述主线见[脚本](../design-introduction-script.md)。\n']
    for i,slide in enumerate(content.SLIDES):
        notes.append(f'## {i+1}. {slide["steps"][0]["title"]}\n')
        refs=[dict(label=content.SOURCES[k][0],href=content.SOURCES[k][1]) for k in slide['sources']]
        for j,s in enumerate(slide['steps']):
            idx=len(frames); html=body(s)
            html=html.replace('arrow-blue',f'arrow-blue-{idx}').replace('arrow-ink',f'arrow-ink-{idx}')
            source_label=' · '.join(r['label'] for r in refs)
            footer=f'<footer class="footer"><span class="ref">依据：{escape(source_label)}</span><span class="folio">{i+1:02d} / {len(content.SLIDES):02d} &nbsp; · &nbsp; {j+1}/{len(slide["steps"])}</span></footer>'
            frames.append(f'<section class="frame {"active" if idx==0 else ""}" data-slide="{i}" data-step="{j}" aria-label="{escape(s["title"],quote=True)}"><div class="kicker"><span><strong>TIDE</strong> {escape(slide["chapter"])}</span><span class="status">{escape(slide["status"])}</span></div><h1>{s["title"]}</h1><p class="lede">{s["lede"]}</p><div class="content">{html}</div>{footer}</section>')
            metadata.append(dict(slide=i,step=j,title=s['title'],notes=s['notes'],refs=refs,graph=s['graph'],view=s['view']))
            notes += [f'### 停点 {i+1}.{j+1}：{s["title"]}\n',s['notes']+'\n']
        notes.append('出处：'+'；'.join(f'[{r["label"]}]({r["href"]})' for r in refs)+'。\n')
    css=(HERE/'deck.css').read_text(); js=(HERE/'deck.js').read_text()
    data=json.dumps(metadata,ensure_ascii=False).replace('</','<\\/')
    output=f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><link rel="icon" href="data:,"><title>Tide · 去中心化与稀疏化</title><style>{css}</style></head>
<body><main id="viewport"><div id="stage">{''.join(frames)}</div></main>
<div class="controls"><div class="control-buttons"><button id="prev" aria-label="上一步">← 上一步</button><button id="next" aria-label="下一步">下一步 →</button><span id="position"></span></div><span class="shortcut">← → 逐步推进 · N 备注 · G 目录</span><div class="control-buttons"><button id="replay">重看本页</button><button id="toc">目录</button><button id="notes">备注与出处</button><button id="fullscreen">全屏</button></div></div>
<dialog id="notes-dialog"><button class="close" data-close>关闭</button><h2 id="notes-title"></h2><p id="notes-body"></p><h3>定义出处</h3><ul id="notes-sources"></ul></dialog>
<dialog id="toc-dialog"><button class="close" data-close>关闭</button><h2>展示目录</h2><div id="toc-list" class="toc-list"></div></dialog><div id="live" class="sr-only" aria-live="polite"></div>
<script id="frame-data" type="application/json">{data}</script><script>{js}</script></body></html>'''
    (HERE/'index.html').write_text(output)
    (HERE/'speaker-notes.md').write_text('\n'.join(notes))
    print(f'Built {len(content.SLIDES)} scenes / {len(frames)} stops; HTML {len(output.encode()):,} bytes')


if __name__=='__main__':
    main()
