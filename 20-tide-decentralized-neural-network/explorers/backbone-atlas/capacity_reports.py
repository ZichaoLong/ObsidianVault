"""Serialize backbone counts for the atlas, CSV and Markdown range table."""
import csv
from decimal import Decimal

from backbones.capacity import (
    BOUND_PROFILES, BUDGETS, DIMENSIONS, NODE_SIZES, PROFILES, SHARING,
    VARIANTS, active, budgets, count,
)


FIELDS = ['profile','n','h','d','memory','sharing','rank',
          'nodes_D','nodes_H','total','base','D','H']
PROFILE_FIELDS = ['spatial_profile','family','timing','depth','widths',
                  'positions','max_width','expansion','rounds','input_period']
PARAMETER_COLUMNS = {'total':'total_M', 'base':'base_M',
                     'D':'private_D_M', 'H':'private_H_M'}


def millions(value):
    """Keep exact scalar counts and power-of-two budget fractions in decimal M."""
    scaled = Decimal(value) / 1_000_000
    return format(scaled, '.6f' if value == int(value) else 'f')


def build(out):
    """Write reproducible tables; the page uses the same compact row data."""
    rows = []
    csv_fields = ['profile', 'agg_mode'] + PROFILE_FIELDS + FIELDS[1:9] + list(PARAMETER_COLUMNS.values())
    csv_fields += ['within_256M'] + [f'active_k{k}_M' for k in BUDGETS] + ['active_pool_M']
    with (out/'capacity.csv').open('w',newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=csv_fields)
        writer.writeheader()
        for key,p in PROFILES.items():
            bindings = [b for b in BOUND_PROFILES.values() if b['spatial_profile'] == key]
            for n in NODE_SIZES:
                for h in ((0,4) if p['family'] in ('exchange','multiscale') else (0,)):
                    for d in DIMENSIONS:
                        for memory in (('K','S','X') if h else ('K','S')):
                            for sharing,rank in SHARING:
                                x = count(key,n,h,d,memory,sharing,rank)
                                values = dict(n=n,h=h,d=d,memory=memory,
                                              sharing=sharing,rank=rank,**x)
                                for binding in bindings:
                                    row = dict(profile=binding['key'], **values)
                                    # Embedded JSON retains raw counts for exact filtering.
                                    rows.append([row[name] for name in FIELDS])
                                    exported = {name:row[name] for name in FIELDS if name not in PARAMETER_COLUMNS}
                                    exported['agg_mode'] = 'source_residual'
                                    exported.update({name:binding.get(name,'') for name in PROFILE_FIELDS})
                                    exported['widths'] = ';'.join(map(str,binding['widths']))
                                    exported.update({column:millions(x[name]) for name,column in PARAMETER_COLUMNS.items()})
                                    exported['within_256M'] = x['total'] <= 256_000_000
                                    exported.update({f'active_k{k}_M':millions(active(x,n,k)) if k<=n else '' for k in BUDGETS})
                                    exported['active_pool_M'] = millions(x['total'])
                                    writer.writerow(exported)
    write_summary(out)
    return dict(fields=FIELDS,rows=rows,profiles=BOUND_PROFILES,variants=VARIANTS,
                parameter_unit='scalar',agg_mode='source_residual',node_sizes=NODE_SIZES,
                dimensions=DIMENSIONS,budgets=BUDGETS)


def write_summary(out):
    lines = ['# 主干参数与尺寸阶梯（生成表）','',
             '维护定义：[统一比较绑定](../../../instances/backbone-comparison.md)。主干可训练参数；M=10^6，不计边界、任务头或状态。',
             '全部行采用 agg_mode=source_residual。接收自注意力的额外参数与准备成本见[比较绑定 §5.1](../../../instances/backbone-comparison.md#51-接收自注意力的参数与准备成本)。',
             '', '完整 CSV 的参数列以 _M 结尾，单位同为百万参数；空的 active_k 列表示 k>n，不能作为配置使用。',
             'profile 同时标识空间轮廓与时间绑定；spatial_profile 保留同端点对照关系。多跨度 Timed／Settle 分别列出，参数计数相同。',
             'CSV 使用各候选主周期；Timed 与 Settle 同周期的设置可在面板中另选。候选取舍与新变体的参考见[主干记录](../../../instances/backbone-design.md)，跨层意图见[研究意图与探索路径](../../../memos/design/design-requirements-and-architecture.md)。',
             '', '以下为 independent；普通 K，有 hub 时取 X。每格为 d=64 / 128 / 192 / 256 的参数 M。更大维度、region_shared／layer_shared 和 S 均在 CSV 及面板中。','',
             '| 拓扑与时间 | 层数 | n | D / H 节点 | 参数 M |',
             '|---|---:|---:|---:|---|']
    for p in BOUND_PROFILES.values():
        key = p['spatial_profile']
        for n in (8,16,32):
            for h in ((0,4) if p['family'] in ('exchange','multiscale') else (0,)):
                xs = [count(key,n,h,d,'X' if h else 'K') for d in (64,128,192,256)]
                lines.append(f"| {p['label']} | {p['depth']} | {n} | {xs[0]['nodes_D']} / {xs[0]['nodes_H']} | "+
                             ' / '.join(f"{x['total']/1e6:.2f}" for x in xs)+' |')
    lines += ['', '## 三档参数对照','',
              '固定 n=32、d=128；共享适配秩为 8，有 hub 时取 X，否则取 K。单位 M，完整尺寸及秩见 CSV。', '',
              '| 空间图 | hub | independent | region_shared | layer_shared |',
              '|---|---:|---:|---:|---:|']
    for key,h in [('fc-8',0),('lattice-7',0),('exchange-m1-r5',4),('multiscale-compact-9',4),('multiscale-9',4)]:
        values=[count(key,32,h,128,'X' if h else 'K',sharing,8)['total']
                for sharing in ('independent','region_shared','layer_shared')]
        lines.append(f"| {PROFILES[key]['label']} | {h} | "+' | '.join(f'{v/1e6:.3f}' for v in values)+' |')
    lines += ['', 'FC 每层一区，两共享档在相同秩下等价；CSV 保留各档标识供筛选，实验无需重复。区域共享按真实区域及各组实际来源类计数，不由一个固定倍率推算。三档参数量不保证严格有序。',
              '', '## 预算阶梯','', '| n | 合法 k | k/n（%） |', '|---:|---|---|']
    for n in NODE_SIZES:
        ks = budgets(n)
        lines.append(f"| {n} | "+', '.join(map(str,ks))+' | '+
                     ', '.join('100 (pool)' if k=='pool' else f'{100*k/n:g}' for k in ks)+' |')
    lines += ['', 'k=n 的 quad 与 pool 是不同分配函数；相同的活跃代理不表示数值等价。',
              '降低 k 不降低总参数；活跃代理为 base+(k/n)D+H，共享基座去重，假定 H 均参与。准备阶段仍可能访问其他节点参数。',
              '宽图、更深图与超过 256M 的行全部保留；候选整体覆盖规模及比例，不要求每个小实例达到约 3%。']
    (out/'capacity-summary.md').write_text('\n'.join(lines)+'\n')
