"""Shape-count references and budget legality; no neural execution."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reference'))
from backbones import capacity as c


def main():
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
            for sharing,rank in c.SHARING:
                x=c.count(key,n,h,128,memory,sharing,rank)
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
    print('PASS: legal power-of-two budgets, KV closed-form counts, per-head adapters, references and active proxies')


if __name__=='__main__':
    main()
