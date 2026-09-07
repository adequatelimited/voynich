#!/usr/bin/env python3
"""(1) type-I error of the script's (b) null using its ACTUAL Monte-Carlo p,
   (2) corrected (b) p for every stratum under the conditionally-exact
       within-cell label permutation."""
import math, os, random, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

HERE = os.path.dirname(os.path.abspath(__file__))
ZL = os.path.abspath(os.path.join(HERE, '..', '..', 'data', 'corpora', 'ZL3b-n.txt'))
pages = ML.parse_pages(ZL, comma_split=True)
def fn(i): return int(re.match(r'f(\d+)', i).group(1))

def gpre(w):
    for g in ML.GALLOWS:
        if w.startswith(g): return g
    return None
def strip(w):
    g = gpre(w); return (g, w[len(g):]) if g else (None, None)
def msd(xs):
    n=len(xs); m=sum(xs)/n
    return m, math.sqrt(sum((x-m)**2 for x in xs)/(n-1) if n>1 else 0.0)
def p2(obs, null):
    m=sum(null)/len(null); d=abs(obs-m)
    return (1+sum(1 for x in null if abs(x-m)>=d-1e-12))/(len(null)+1)

recB = {p['id'] for p in pages.values()
        if p['meta'].get('I')=='S' and p['meta'].get('L')=='B' and 103<=p['fnum']<=116}
herb = {p['id'] for p in pages.values() if p['meta'].get('I')=='H'}
STR = {'recipesB_TEST_even': {i for i in recB if fn(i)%2==0},
       'recipesB_FIT_odd':   {i for i in recB if fn(i)%2==1},
       'recipesB_ALL':       recB,
       'herbal_ALL':         herb,
       'herbal_TEST_even':   {i for i in herb if fn(i)%2==0},
       'f58_langA_oos':      {'f58r','f58v'}}
VOCABS = {}
for nm, ids in STR.items():
    base = recB if nm.startswith('recipesB') else (herb if nm.startswith('herbal') else ids)
    c = Counter()
    for d in ML.paragraphs(pages, page_ids=base): c.update(d['words'])
    VOCABS[nm] = c

def build(ids, vocab):
    pars = ML.paragraphs(pages, page_ids=ids)
    pi, nonpi = [], []
    for d in pars:
        if d['first_word']: pi.append(d['first_word'])
        nonpi.extend(d['words'][1:])
    tgt=[]
    for w in pi:
        g,r = strip(w)
        if g is not None: tgt.append((w,g,r,1 if r in vocab else 0))
    cells={}
    for w in nonpi:
        g,r = strip(w)
        if g is None: continue
        cells.setdefault((g,len(w)),[]).append((w,r,1 if r in vocab else 0))
    return tgt, cells

print('#'*74)
print('# 1. TYPE-I ERROR of the script\'s (b) null, using the script\'s own')
print('#    Monte-Carlo p (10,000 with-replacement cell draws), on data where')
print('#    H0 is TRUE by construction (labels permuted inside each cell).')
print('#'*74)
for nm in ('recipesB_TEST_even','recipesB_FIT_odd'):
    tgt, cells = build(STR[nm], VOCABS[nm])
    matched=[t for t in tgt if (t[1],len(t[0])) in cells]
    keys=[(t[1],len(t[0])) for t in matched]
    kc=Counter(keys)
    bags={k:[c[2] for c in cells[k]]+[t[3] for t in matched if (t[1],len(t[0]))==k]
          for k in kc}
    rng=random.Random(408)
    NSIM, ND = 400, 4000
    hits05=hits01=hits001=0
    for _ in range(NSIM):
        nop={}; nct={}
        for k,nk in kc.items():
            b=list(bags[k]); rng.shuffle(b)
            nop[k]=b[:nk]; nct[k]=b[nk:] or b[:1]
        obs=sum(sum(nop[k]) for k in kc)/len(matched)
        null=[]
        for _ in range(ND):
            s=0
            for k,nk in kc.items():
                c=nct[k]
                for _ in range(nk): s+=c[rng.randrange(len(c))]
            null.append(s/len(matched))
        p=p2(obs,null)
        if p<0.05: hits05+=1
        if p<0.01: hits01+=1
        if p<0.001: hits001+=1
    print('%-20s %d H0-true datasets: script-null rejects at nominal '
          '0.05 -> %.3f | 0.01 -> %.3f | 0.001 -> %.4f   (correct: .050/.010/.0010)'
          % (nm, NSIM, hits05/NSIM, hits01/NSIM, hits001/NSIM))

print()
print('#'*74)
print('# 2. CORRECTED (b): conditionally-exact within-cell label permutation.')
print('#    Same H0, same matching, same 10,000 draws -- only the null is fixed.')
print('#'*74)
print('%-20s %-8s %5s  %-28s   %-28s' % ('stratum','match','n','SCRIPT bootstrap null','EXACT within-cell perm'))
for nm in ('recipesB_TEST_even','recipesB_FIT_odd','recipesB_ALL',
           'herbal_ALL','herbal_TEST_even','f58_langA_oos'):
    tgt, cells = build(STR[nm], VOCABS[nm])
    if not tgt: continue
    def relpool(g,L):
        for tol in (0,1,2):
            ks=[(g,L+dl) for dl in range(-tol,tol+1) if (g,L+dl) in cells]
            if ks: return tuple(sorted(set(ks)))
        ks=tuple(sorted(k for k in cells if k[0]==g))
        return ks or None
    for mode in ('exact','relaxed'):
        sub, kk = [], []
        for t in tgt:
            if mode=='exact':
                k=(t[1],len(t[0]))
                if k not in cells: continue
                key=(k,)
            else:
                key=relpool(t[1],len(t[0]))
                if key is None: continue
            sub.append(t); kk.append(key)
        if not sub: continue
        obs=sum(t[3] for t in sub)/len(sub)
        # script's bootstrap
        rng=random.Random(1234)
        pools=[ [c[2] for k in key for c in cells[k]] for key in kk]
        nb=[sum(p_[rng.randrange(len(p_))] for p_ in pools)/len(pools) for _ in range(10000)]
        mb,sb=msd(nb); pb=p2(obs,nb)
        # exact within-cell permutation
        strata={}
        for t,key in zip(sub,kk): strata.setdefault(key,[]).append(t[3])
        rng=random.Random(1234)
        bags={key:[c[2] for k in key for c in cells[k]]+v for key,v in strata.items()}
        ne=[]
        for _ in range(10000):
            s=0
            for key,v in strata.items():
                b=bags[key]; s+=sum(rng.sample(b,len(v)))
            ne.append(s/len(sub))
        me,se=msd(ne); pe=p2(obs,ne)
        print('%-20s %-8s %5d  obs=%.4f ctrl=%.4f z=%+6.2f p=%.4f   ctrl=%.4f z=%+5.2f p=%.4f  %s'
              % (nm, mode, len(sub), obs, mb, (obs-mb)/sb if sb else 0, pb,
                 me, (obs-me)/se if se else 0, pe,
                 ('ORN passes' if pe>0.05 else 'ORN FAILS')))
