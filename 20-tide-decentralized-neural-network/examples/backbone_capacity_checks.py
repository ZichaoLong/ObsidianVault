"""Shape-count references and budget legality; no neural execution."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reference'))
from backbones import capacity as c


def check_aggregation_profiles():
    # A complete FC count has one source embedding per node and one head per
    # layer, so the widened model has an independent closed-form oracle.
    depth,n=4,8
    for d in c.DIMENSIONS:
        wide=c.aggregation_config(d,'incoming_wide')
        assert wide['agg_hidden_width']==wide['agg_attention_width']==d
        assert wide['agg_attention_heads']*wide['agg_attention_head_dim']==d
        expected=n*depth*(23.125*d*d+2.25*d+1+2*d)+depth*(2*(d//4)**2+2*(d//4))
        assert c.count('fc-4',n,0,d,agg_profile='incoming_wide')['total']==expected
        for agg_profile in c.AGG_PROFILES:
            a=c.aggregation_config(d,agg_profile)
            assert a['agg_attention_width']==a['agg_attention_heads']*a['agg_attention_head_dim']
            if agg_profile!='incoming_wide':
                assert a['agg_hidden_width']==d//8
        # Compare both memory families and every rank. In particular d=64,
        # rank=16 changes the MLP's effective adapter rank from 8 to 16.
        for memory in ('K','S'):
            for sharing,rank in c.SHARING:
                old=c.count('fc-4',n,0,d,memory,sharing,rank)
                new=c.count('fc-4',n,0,d,memory,sharing,rank,'incoming_wide')
                matrix_delta=23*d*d//4
                embedding_delta=15*d//8
                if sharing=='independent':
                    assert new['base']==old['base']
                    delta=n*depth*(matrix_delta+embedding_delta)
                else:
                    assert new['base']-old['base']==depth*(matrix_delta+embedding_delta)
                    adapter_delta=12*rank*d-2*min(rank,d//8)*(d+d//8)
                    assert new['D']-old['D']==n*depth*adapter_delta
                    delta=depth*(matrix_delta+embedding_delta)+n*depth*adapter_delta
                assert new['total']-old['total']==delta
                assert new['nodes_D']==old['nodes_D']==n*depth and new['nodes_H']==0

    # Light profiles agree exactly with the previously verified attention-only
    # increment, including hub source classes and both sharing scopes.
    for key,n,h in [('fc-4',8,0),('lattice-3',8,0),
                    ('exchange-m1-r5',8,4),('multiscale-compact-9',8,4)]:
        for memory in (('K','S','X') if h else ('K','S')):
            for sharing,rank in c.SHARING:
                old=c.count(key,n,h,128,memory,sharing,rank)
                for width in (64,128):
                    new=c.count(key,n,h,128,memory,sharing,rank,f'incoming_light_{width}')
                    extra=c.incoming_attention_increment(key,n,h,128,sharing,rank,width)
                    for field in ('total','base','D','H'):
                        assert new[field]==old[field]+extra[field],(key,memory,sharing,rank,width,field)
                    assert new['nodes_D']==old['nodes_D'] and new['nodes_H']==old['nodes_H']


def main():
    check_aggregation_profiles()
    for n in c.NODE_SIZES:
        ks=c.budgets(n)
        assert ks[-1]=='pool'
        assert all(k<=n and k&(k-1)==0 for k in ks[:-1])
        assert 3 not in ks and 10 not in ks
    assert c.budgets(8)==[1,2,4,8,'pool']
    assert c.budgets(128)==[1,2,4,8,16,32,64,'pool']
    for d in c.DIMENSIONS:
        matrices,vectors=c.inventory(d,'K')
        total=sum(a*b for _,a,b in matrices)+sum(x for _,x in vectors)+1
        assert total==17.375*d*d+2.25*d+1
        private=sum(min(8,a,b)*(a+b) for _,a,b in matrices)+1
        assert private==d*d/4+230*d+41
        assert sum(name.startswith('Q.') for name,_,_ in matrices)==d//32
    # Independent FC is also countable without constructing any endpoint graph.
    d,n,depth=128,8,8
    expected=n*depth*(17.375*d*d+2.25*d+1+d//8)+depth*(2*(d//4)**2+2*(d//4))
    assert c.count('fc-8',n,0,d)['total']==expected
    # One region per FC layer makes both sharing scopes identical, including
    # regional heads, actual source embeddings and every adapter rank.
    for agg_profile in c.AGG_PROFILES:
        for memory in ('K','S'):
            for rank in (4,8,16):
                for depth in (4,8,32):
                    assert c.count(f'fc-{depth}',8,0,128,memory,'region_shared',rank,agg_profile)==c.count(f'fc-{depth}',8,0,128,memory,'layer_shared',rank,agg_profile)
    # Three-layer Lattice has four regions (1,2,1), with one source class in
    # each region. Splitting its middle layer adds exactly one complete base
    # (matrices, vectors, source embedding and regional query), no adapters.
    d,n,rank=128,8,8
    matrices,vectors=c.inventory(d,'K')
    one_base=sum(a*b for _,a,b in matrices)+sum(x for _,x in vectors)+d//8+2*(d//4)**2+2*(d//4)
    private=4*n*(sum(min(rank,a,b)*(a+b) for _,a,b in matrices)+1)
    region=c.count('lattice-3',n,0,d,'K','region_shared',rank)
    layer=c.count('lattice-3',n,0,d,'K','layer_shared',rank)
    assert region['base']==4*one_base and layer['base']==3*one_base
    assert region['D']==layer['D']==private and region['H']==layer['H']==0
    assert region['total']-layer['total']==one_base
    references=[('multiscale-compact-9',8,0,128,36.513),
                ('multiscale-compact-9',32,4,128,162.936),
                ('exchange-m1-r10',32,4,128,244.954)]
    # These are the preceding discussion's values, rounded to 0.001M.
    for key,n,h,d,expected_M in references:
        x=c.count(key,n,h,d,'X' if h else 'K')
        assert round(x['total']/1e6,3)==expected_M,(key,x['total'])
    for key,n,h in [('fc-4',8,0),('lattice-7',16,0),
                    ('exchange-m1-r5',32,4),('multiscale-compact-9',32,4)]:
        for memory in (('K','S','X') if h else ('K','S')):
            for rank in (4,8,16):
                region=c.count(key,n,h,128,memory,'region_shared',rank)
                layer=c.count(key,n,h,128,memory,'layer_shared',rank)
                assert region['D']==layer['D'] and region['H']==layer['H']
                assert region['base']>=layer['base']
                if not key.startswith('fc-'):
                    assert region['base']>layer['base']
            for agg_profile in c.AGG_PROFILES:
                for sharing,rank in c.SHARING:
                    x=c.count(key,n,h,128,memory,sharing,rank,agg_profile)
                    assert x['total']==x['base']+x['D']+x['H']
                    values=[c.active(x,n,k) for k in c.budgets(n)]
                    assert values==sorted(values) and values[-1]==x['total']
                    if n<=64:
                        assert c.active(x,n,n)==c.active(x,n,'pool')
                    try:
                        c.active(x,n,3)
                    except ValueError:
                        pass
                    else:
                        raise AssertionError('non-power-of-two budget accepted')
    print('PASS: four reception profiles, complete light/wide counts, adapter rank changes, three parameter bindings, FC equivalence, regional-base growth, KV closed-form counts, references and active proxies')


if __name__=='__main__':
    main()
