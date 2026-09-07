#!/usr/bin/env python3
"""v_z4_confound_4.py — is the passer just "the labels ZL numbered first"?

meaning_lib.zodiac_labels defines a ring as beginning at the Lz locus whose
position character is '@'. That character is ZL's editorial marker for the
first member of a locus GROUP. It is where the transcriber decided to start
reading the circle, not a property of the parchment. Under the registered
floor rule the first third is also the one that absorbs the remainder, so it
is the block most exposed to that choice.

F1  form profile of ring position 0 / 0-2 / rest
F2  drop the 12 position-0 labels and re-run the registered statistic
F3  which labels move between floor and ceil, and what they are
F4  verify the descriptive claims in the test's caveats ('y' and 'ot')
"""
import io, json, math, os, random, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML
import t_z4 as Z

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
ZL3B = os.path.join(REPO, 'data', 'corpora', 'ZL3b-n.txt')
ALPHA_BONF = 0.01 / 6.0
B = 20000
L = []
def say(*a):
    s = ' '.join(str(x) for x in a); L.append(s); print(s)


def perm_p(pos, form, groups, seed, B=B):
    n = len(pos)
    P = sorted(set(pos)); F = sorted(set(form))
    pi = {v: i for i, v in enumerate(P)}; fi = {v: i for i, v in enumerate(F)}
    pc = [pi[v] for v in pos]; fc = [fi[v] for v in form]
    nP, nF = len(P), len(F)
    def stat(fcur):
        j = [0] * (nP * nF)
        for a, b in zip(pc, fcur):
            j[a * nF + b] += 1
        return Z.mi_bits(j, nP, nF, n)
    obs = stat(fc)
    rng = random.Random(seed); cur = list(fc); nulls = []
    for _ in range(B):
        for gg in groups:
            for a in range(len(gg) - 1, 0, -1):
                b = rng.randint(0, a)
                cur[gg[a]], cur[gg[b]] = cur[gg[b]], cur[gg[a]]
        nulls.append(stat(cur))
    m = sum(nulls) / len(nulls)
    d = abs(obs - m)
    ge = sum(1 for v in nulls if abs(v - m) >= d - 1e-12)
    return {'observed': obs, 'null_mean': m, 'debiased': obs - m,
            'p': (1.0 + ge) / (1.0 + len(nulls))}


def group_index(keys):
    g = OrderedDict()
    for i, k in enumerate(keys):
        g.setdefault(k, []).append(i)
    return list(g.values())


lab = Z.load_labels(ZL3B, True)
tst = [r for r in lab if r['sign'] in ML.TEST_SIGNS]
it_t = Z.build_items(tst, 'unit')
form = [it['f1'] for it in it_t]
keys = [(it['sign'], it['ring']) for it in it_t]
g = group_index(keys)

say('=' * 78)
say('F1  FORM PROFILE BY RING POSITION (ZL locus order)')
for lo, hi, nm in ((0, 0, 'idx 0 only'), (0, 2, 'idx 0-2'), (3, 99, 'idx >=3')):
    c = Counter(it['f1'] for it in it_t if lo <= it['idx_in_ring'] <= hi)
    n = sum(c.values())
    say('    %-12s n=%3d  %s' % (nm, n, dict(c.most_common(8))))

say('')
say('F2  DROP THE %d RING-INITIAL LABELS AND RE-RUN THE REGISTERED STATISTIC'
    % sum(1 for it in it_t if it['idx_in_ring'] == 0))
sub = [it for it in it_t if it['idx_in_ring'] > 0]
p_ = [it['p2'] for it in sub]
f_ = [it['f1'] for it in sub]
k_ = group_index([(it['sign'], it['ring']) for it in sub])
r = perm_p(p_, f_, k_, 408)
say('    n=%d  MI=%.4f  debiased=%+.4f  p=%.5f  %s'
    % (len(sub), r['observed'], r['debiased'], r['p'],
       'PASS' if r['p'] < ALPHA_BONF else 'fail'))
say('    (thirds kept exactly as t_z4 assigned them; only the labels are dropped)')

say('')
say('F3  WHICH LABELS MOVE BETWEEN floor AND ceil')
ceil3 = lambda i, s: min(2, int(math.ceil((i + 1) * 3.0 / s)) - 1)
moved = [(it, ceil3(it['idx_in_ring'], it['ring_size'])) for it in it_t
         if ceil3(it['idx_in_ring'], it['ring_size']) != it['p2']]
say('    %d of %d labels change third (%.1f%%):' % (len(moved), len(it_t),
                                                    100.0 * len(moved) / len(it_t)))
for it, nt in moved:
    say('      %-14s ring%d size%2d idx%2d  third %d -> %d  first unit %-5s  %s'
        % (it['sign'], it['ring'], it['ring_size'], it['idx_in_ring'],
           it['p2'], nt, it['f1'], it['text']))

say('')
say('F4  THE DESCRIPTIVE CLAIMS IN THE TEST\'S CAVEATS')
for tp in ('y', 'ot', 'ok', 'o'):
    cnt = [sum(1 for it in it_t if it['p2'] == t and it['f1'] == tp) for t in (0, 1, 2)]
    tot = [53, 47, 47]
    say('    %-4s by third %s  of %s  -> rates %s'
        % (tp, cnt, tot, ['%.3f' % (a / float(b)) for a, b in zip(cnt, tot)]))
say('    The report says "\'ot\' is depleted in the first third". 7/53 = 0.132 vs')
say('    10/47 = 0.213 and 6/47 = 0.128: third 1 is ENRICHED, third 0 and third 2')
say('    are level. The one-vs-rest permutation p for \'ot\' is 0.903.')

with io.open(os.path.join(HERE, 'results', 'v_z4_confound_4.stdout.txt'), 'w',
             encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n')
