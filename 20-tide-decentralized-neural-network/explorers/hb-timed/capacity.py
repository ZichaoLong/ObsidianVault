"""Backbone shape counts for instances/backbone-comparison.md.

No neural execution, state allocation, embeddings or task heads are counted.
The graph constructors supply actual source classes, including hub probes.
"""
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
import csv

import topology as ms
import settle_topology as st

NODE_SIZES = (8, 16, 32, 64, 128)
DIMENSIONS = (64, 128, 192, 256, 384, 512, 768)
BUDGETS = (1, 2, 4, 8, 16, 32, 64)
SHARING = (('independent', 0), ('shared', 8), ('shared', 4), ('shared', 16))


def budgets(n):
    return [k for k in BUDGETS if k <= n] + ['pool']


def make_profiles():
    result = {}
    def add(key, family, widths, label, **extra):
        result[key] = dict(key=key, family=family, widths=widths, depth=len(widths),
                           label=label, **extra)
    for depth in (4, 6, 8, 9, 10, 12, 16, 24, 32):
        add(f'fc-{depth}', 'fc', [1]*depth, f'FC {depth} 层')
    for depth in (3, 5, 7, 9, 11, 13):
        a = (depth-1)//2
        add(f'lattice-{depth}', 'lattice', [2**min(l, 2*a-l) for l in range(depth)],
            f'Lattice {depth} 层')
    for m in range(1, 7):
        add(f'exchange-{3*m+1}', 'exchange', st.exchange_widths(m),
            f'Exchange {3*m+1} 层', expansion=m, rounds=m)
    for m, rounds in ((1,3), (1,4), (1,5), (1,10), (2,5), (2,9)):
        add(f'exchange-m{m}-r{rounds}', 'exchange', st.exchange_widths(m, rounds),
            f'窄 Exchange m={m}, R={rounds}', expansion=m, rounds=rounds)
    for key, widths, extra in ms.PROFILES + ms.COMPACT_PROFILES:
        add('multiscale-'+key, 'multiscale', widths,
            ('窄多跨度 ' if key.startswith('compact') else '多跨度 ')+key,
            add_dd4=extra)
    for depth in (25, 33):
        add(f'multiscale-{depth}', 'multiscale', ms.extended_widths(depth),
            f'多跨度 {depth} 层 · 加长平台', add_dd4=False)
    return result


PROFILES = make_profiles()


@lru_cache(None)
def inventory(d, memory):
    """Each tuple names a mathematical matrix, not its packed implementation."""
    if d not in DIMENSIONS or memory not in ('K', 'S'):
        raise ValueError('choose a registered content dimension and K/S memory')
    s, a, heads = d//4, d//8, d//32
    matrices = [('Agg.A',a,d), ('Agg.B',d,a), ('feature',s,d),
                ('score.cat',s,d+4*s+3), ('score.loc',s,d), ('score.mem',s,2*s+2)]
    vectors = [('score.hidden',s), ('score.out',s),
               ('score.loc_bias',s), ('score.mem_bias',s)]
    if memory == 'K':
        matrices += [('KV',2*d,d)]
        # W^Q_(v,h) is a separate adapter per mathematical head.
        matrices += [(f'Q.{i}',32,d) for i in range(heads)]
    else:
        matrices += [('SSD.in',2*d+64+heads,d), ('SSD.read',s,d)]
        vectors += [('SSD.Alog',heads), ('SSD.dt_bias',heads), ('SSD.skip',heads),
                    ('SSD.norm',d), ('SSD.conv',5*(d+64))]
    matrices += [('out',d,d), ('FFN.gate',4*d,d),
                 ('FFN.up',4*d,d), ('FFN.down',d,4*d)]
    return matrices, vectors


@lru_cache(None)
def graph_inventory(profile, n, hubs):
    p = PROFILES[profile]
    if n not in NODE_SIZES or hubs not in (0,4):
        raise ValueError('unregistered region size or hub count')
    if p['family'] in ('fc','lattice') and hubs:
        raise ValueError('FC and original Lattice have no hub branch')
    widths = p['widths']
    if p['family'] == 'fc':
        nodes = [(l,0,'d',i) for l in range(len(widths)) for i in range(n)]
        classes = [{'ext' if l == 0 else 'DD'} for l,_,_,_ in nodes]
    else:
        if p['family'] == 'multiscale':
            graph = ms.construct(widths,n=n,h=4,probes=ms.probes_for(n),
                                 placement='all' if hubs else 'none',add_dd4=p['add_dd4'])
        else:
            graph = st.construct(widths,n=n,h=hubs,exchange=p['family']=='exchange')
        nodes,_,_,ins,_,_ = graph
        classes = [{k for _,k in parents} | ({'ext'} if nodes[u][0]==0 else set())
                   for u,parents in enumerate(ins)]
    groups = Counter((x[0],x[2]) for x in nodes)
    class_counts, class_groups = Counter(), defaultdict(set)
    for node, cs in zip(nodes, classes):
        class_counts[node[2]] += len(cs)
        class_groups[node[0],node[2]].update(cs)
    # Cache only counts, not graphs, for the larger n=128 / deep profiles.
    return groups, class_counts, class_groups


def count(profile, n, hubs, d, memory='K', sharing='independent', rank=8):
    if memory not in ('K','S','X') or sharing not in ('independent','shared'):
        raise ValueError('unknown memory or parameter binding')
    if sharing == 'shared' and rank not in (4,8,16):
        raise ValueError('adapter rank must be 4, 8 or 16')
    groups, class_counts, class_groups = graph_inventory(profile,n,hubs)
    base, private = 0, Counter()
    nodes = Counter()
    for (layer,role),number in groups.items():
        kind = 'S' if memory=='S' or (memory=='X' and role=='h') else 'K'
        matrices, vectors = inventory(d,kind)
        nodes[role] += number
        reg = 2*(d//4)**2+2*(d//4)
        if sharing == 'shared':
            base += sum(a*b for _,a,b in matrices)+sum(x for _,x in vectors)
            base += len(class_groups[layer,role])*(d//8)+reg
            private[role] += number*(sum(min(rank,a,b)*(a+b) for _,a,b in matrices)+1)
        else:
            base += (number//(n if role=='d' else hubs))*reg
            private[role] += number*(sum(a*b for _,a,b in matrices)+sum(x for _,x in vectors)+1)
    if sharing == 'independent':
        for role,number in class_counts.items():
            private[role] += number*(d//8)
    return dict(total=base+sum(private.values()),base=base,D=private['d'],H=private['h'],
                nodes_D=nodes['d'],nodes_H=nodes['h'])


def active(x, n, k):
    if k not in budgets(n):
        raise ValueError('budget must be a legal power of two or pool')
    return x['base'] + (1 if k=='pool' else k/n)*x['D'] + x['H']


FIELDS = ['profile','n','h','d','memory','sharing','rank',
          'nodes_D','nodes_H','total','base','D','H']


def build(out):
    """Write reproducible tables; the page uses the same compact row data."""
    rows = []
    csv_fields = FIELDS + ['within_256M'] + [f'active_k{k}' for k in BUDGETS] + ['active_pool']
    with (out/'capacity.csv').open('w',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=csv_fields)
        writer.writeheader()
        for key,p in PROFILES.items():
            for n in NODE_SIZES:
                for h in ((0,4) if p['family'] in ('exchange','multiscale') else (0,)):
                    for d in DIMENSIONS:
                        for memory in (('K','S','X') if h else ('K','S')):
                            for sharing,rank in SHARING:
                                x = count(key,n,h,d,memory,sharing,rank)
                                row = dict(profile=key,n=n,h=h,d=d,memory=memory,
                                           sharing=sharing,rank=rank,**x)
                                rows.append([row[name] for name in FIELDS])
                                row['within_256M'] = x['total'] <= 256_000_000
                                row.update({f'active_k{k}':active(x,n,k) if k<=n else '' for k in BUDGETS})
                                row['active_pool'] = x['total']
                                writer.writerow(row)
    write_summary(out)
    return dict(fields=FIELDS,rows=rows,profiles=PROFILES,node_sizes=NODE_SIZES,
                dimensions=DIMENSIONS,budgets=BUDGETS)


def write_summary(out):
    lines = ['# 主干参数与尺寸阶梯（生成表）','',
             '维护定义：[统一比较绑定](../../../instances/backbone-comparison.md)。主干可训练参数；M=10^6，不计边界、任务头或状态。',
             '', '完整 CSV 的参数单位是标量个数；空的 active_k 列表示 k>n，不能作为配置使用。',
             '', '以下为 independent；普通 K，有 hub 时取 X。每格为 d=64 / 128 / 192 / 256 的参数 M。更大维度、shared 和 S 均在 CSV 及面板中。','',
             '| 空间图 | 层数 | n | D / H 节点 | 参数 M |',
             '|---|---:|---:|---:|---|']
    for key,p in PROFILES.items():
        for n in (8,16,32):
            for h in ((0,4) if p['family'] in ('exchange','multiscale') else (0,)):
                xs = [count(key,n,h,d,'X' if h else 'K') for d in (64,128,192,256)]
                lines.append(f"| {p['label']} | {p['depth']} | {n} | {xs[0]['nodes_D']} / {xs[0]['nodes_H']} | "+
                             ' / '.join(f"{x['total']/1e6:.2f}" for x in xs)+' |')
    lines += ['', '## 预算阶梯','', '| n | 合法 k | k/n（%） |', '|---:|---|---|']
    for n in NODE_SIZES:
        ks = budgets(n)
        lines.append(f"| {n} | "+', '.join(map(str,ks))+' | '+
                     ', '.join('100 (pool)' if k=='pool' else f'{100*k/n:g}' for k in ks)+' |')
    lines += ['', 'k=n 的 quad 与 pool 是不同分配函数；相同的活跃代理不表示数值等价。',
              '降低 k 不降低总参数；活跃代理为 base+(k/n)D+H，共享基座去重，假定 H 均参与。准备阶段仍可能访问其他节点参数。',
              '宽图、更深图与超过 256M 的行全部保留；候选整体覆盖规模及比例，不要求每个小实例达到约 3%。']
    (out/'capacity-summary.md').write_text('\n'.join(lines)+'\n')


if __name__ == '__main__':
    destination = Path(__file__).resolve().parent/'generated'
    destination.mkdir(exist_ok=True)
    data = build(destination)
    print(f"Counted {len(data['rows'])} backbone configurations")
