"""Backbone shape counts for instances/backbone-comparison.md.

No neural execution, state allocation, embeddings or task heads are counted.
The graph constructors supply actual source classes, including hub probes.
"""
from collections import Counter, defaultdict
from functools import lru_cache
from . import multiscale as ms
from . import settle_graphs as st

NODE_SIZES = (8, 16, 32, 64, 128)
DIMENSIONS = (64, 128, 192, 256, 384, 512, 768)
BUDGETS = (1, 2, 4, 8, 16, 32, 64)
SHARING = (('independent', 0),
           ('region_shared', 8), ('region_shared', 4), ('region_shared', 16),
           ('layer_shared', 8), ('layer_shared', 4), ('layer_shared', 16))


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

VARIANTS = {
    'fc-settle': dict(family='fc', timing='settle', label='FC · Settle'),
    'lattice-settle': dict(family='lattice', timing='settle', label='HB-Lattice · Settle'),
    'exchange-settle': dict(family='exchange', timing='settle', label='HB-Exchange · Settle'),
    'multiscale-timed': dict(family='multiscale', timing='timed', label='HB-Multiscale · Timed'),
    'multiscale-settle': dict(family='multiscale', timing='settle', label='HB-Multiscale · Settle'),
}


def make_bound_profiles():
    """Bind native input schedules without duplicating spatial constructors.

    The same-period Timed comparison remains an optional schedule of Timed;
    the catalog records its native period 4 and the alternative Settle period.
    """
    result = {}
    for spatial_key, p in PROFILES.items():
        settle_period = p['depth'] + (2 if p['family'] in ('fc', 'lattice') else 1)
        for timing in (('timed', 'settle') if p['family'] == 'multiscale' else ('settle',)):
            key = f'{spatial_key}-{timing}'
            result[key] = dict(p, key=key, spatial_profile=spatial_key,
                               variant=f"{p['family']}-{timing}", timing=timing,
                               label=f"{p['label']} · {timing.title()}",
                               positions=sum(p['widths']), max_width=max(p['widths']),
                               input_period=4 if timing == 'timed' else settle_period,
                               settle_period=settle_period)
    return result


BOUND_PROFILES = make_bound_profiles()


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
    # The registered comparisons use group partition: each (layer, position,
    # role) is an actual region. Mixed/singleton bindings are not counted here.
    groups = Counter(tuple(x[:3]) for x in nodes)
    class_counts, class_groups = Counter(), defaultdict(set)
    for node, cs in zip(nodes, classes):
        class_counts[node[2]] += len(cs)
        class_groups[tuple(node[:3])].update(cs)
    # Cache only counts, not graphs, for the larger n=128 / deep profiles.
    return groups, class_counts, class_groups


@lru_cache(None)
def sharing_inventory(profile, n, hubs, sharing):
    regions, class_counts, region_classes = graph_inventory(profile, n, hubs)
    if sharing != 'layer_shared':
        return regions, class_counts, region_classes
    groups, class_groups = Counter(), defaultdict(set)
    for (layer, position, role), number in regions.items():
        groups[layer, role] += number
        class_groups[layer, role].update(region_classes[layer, position, role])
    return groups, class_counts, class_groups


def count(profile, n, hubs, d, memory='K', sharing='independent', rank=8):
    if memory not in ('K','S','X') or sharing not in ('independent','region_shared','layer_shared'):
        raise ValueError('unknown memory or parameter binding')
    if sharing != 'independent' and rank not in (4,8,16):
        raise ValueError('adapter rank must be 4, 8 or 16')
    groups, class_counts, class_groups = sharing_inventory(profile,n,hubs,sharing)
    base, private = 0, Counter()
    nodes = Counter()
    for group,number in groups.items():
        role = group[-1]
        kind = 'S' if memory=='S' or (memory=='X' and role=='h') else 'K'
        matrices, vectors = inventory(d,kind)
        nodes[role] += number
        reg = 2*(d//4)**2+2*(d//4)
        if sharing != 'independent':
            base += sum(a*b for _,a,b in matrices)+sum(x for _,x in vectors)
            base += len(class_groups[group])*(d//8)+reg
            private[role] += number*(sum(min(rank,a,b)*(a+b) for _,a,b in matrices)+1)
        else:
            base += reg
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


def incoming_attention_increment(profile, n, hubs, d, sharing='independent',
                                 rank=8, attention_width=64):
    """Extra parameters for one incoming_self_attention block on every node.

    Q/K/V are three packed mathematical matrices; O is the fourth.
    Original source residuals remain in count(). No memory or region heads
    are added here. The atlas's existing rows continue to use source_residual.
    """
    if d not in DIMENSIONS:
        raise ValueError('choose a registered content dimension')
    if type(attention_width) is not int or attention_width <= 0:
        raise ValueError('attention width must be a positive integer')
    if sharing not in ('independent', 'region_shared', 'layer_shared'):
        raise ValueError('unknown parameter binding')
    if sharing != 'independent' and rank not in (4, 8, 16):
        raise ValueError('adapter rank must be 4, 8 or 16')
    groups, class_counts, class_groups = sharing_inventory(profile, n, hubs, sharing)
    base, private, nodes = 0, Counter(), Counter()
    matrix_size = 4*d*attention_width
    adapter_size = 4*min(rank, d, attention_width)*(d+attention_width)
    for group, number in groups.items():
        role = group[-1]
        nodes[role] += number
        if sharing == 'independent':
            private[role] += number*matrix_size
        else:
            base += matrix_size+len(class_groups[group])*d
            private[role] += number*adapter_size
    if sharing == 'independent':
        for role, number in class_counts.items():
            private[role] += number*d
    return dict(total=base+sum(private.values()), base=base,
                D=private['d'], H=private['h'],
                nodes_D=nodes['d'], nodes_H=nodes['h'])
