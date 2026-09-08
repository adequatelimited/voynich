#!/usr/bin/env python3
"""v_z4_confound_2.py — the decisive confound: the unregistered remainder rule
inside "thirds of the ring".

PROTOCOL.md registers "thirds of the ring". No TEST ring has a size divisible
by 3 except the three 18-label rings and the 9- and 12-label ones; sizes are
[4,4,9,10,10,12,12,16,16,18,18,18]. For 10 and 16 the three thirds cannot be
equal and SOMEONE has to decide where the remainder goes. t_z4 chose
floor(3*i/s), which puts the remainder in the FIRST third (marginal 53/47/47).

Three equally natural readings are compared, all on the same items, same null,
same seed, several seeds, and — crucially — each one's POWER is measured on the
same 8 numeral series, so that a failure under one convention cannot be blamed
on that convention being intrinsically blind.

  floor     third(i) = min(2, 3i // s)                 remainder -> first third
  midpoint  third(i) = min(2, floor(3(i+0.5)/s))       remainder -> middle third
  ceil      third(i) = min(2, ceil(3(i+1)/s) - 1)      remainder -> last third

Also: MI at 2 and 4 blocks, and clock-position coverage.
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
    rng = random.Random(seed)
    cur = list(fc); nulls = []
    for _ in range(B):
        for g in groups:
            for a in range(len(g) - 1, 0, -1):
                b = rng.randint(0, a)
                cur[g[a]], cur[g[b]] = cur[g[b]], cur[g[a]]
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


CONV = OrderedDict([
    ('floor(registered)', lambda i, s, k=3: min(k - 1, (i * k) // s)),
    ('midpoint',          lambda i, s, k=3: min(k - 1, int(math.floor((i + 0.5) * k / s)))),
    ('ceil',              lambda i, s, k=3: min(k - 1, int(math.ceil((i + 1) * k / s)) - 1)),
])

lab = Z.load_labels(ZL3B, True)
tst = [r for r in lab if r['sign'] in ML.TEST_SIGNS]
fit = [r for r in lab if r['sign'] in ML.FIT_SIGNS]
it_t = Z.build_items(tst, 'unit')
form = [it['f1'] for it in it_t]
keys = [(it['sign'], it['ring']) for it in it_t]
g = group_index(keys)

say('=' * 78)
say('D1  "THIRDS OF THE RING": WHERE DOES THE REMAINDER GO?')
say('    TEST ring sizes %s' % sorted({(it["sign"], it["ring"]): it["ring_size"]
                                       for it in it_t}.values()))
say('    B = %d draws per cell (2x the registered B, to take Monte-Carlo noise')
say('    off the table); seeds 408 and 409 both shown.')
say('')
say('    %-18s %-14s %9s %10s %9s  %s'
    % ('convention', 'marginal', 'MI', 'debiased', 'p(408)', 'p(409)'))
d1 = OrderedDict()
for nm, fn in CONV.items():
    p_ = [fn(it['idx_in_ring'], it['ring_size']) for it in it_t]
    r8 = perm_p(p_, form, g, 408)
    r9 = perm_p(p_, form, g, 409)
    d1[nm] = {'p408': r8['p'], 'p409': r9['p'], 'debiased': r8['debiased'],
              'marginal': dict(Counter(p_))}
    mk = lambda p: 'PASS' if p < ALPHA_BONF else 'fail'
    say('    %-18s %-14s %9.4f %+10.4f %9.5f %s / %.5f %s'
        % (nm, '/'.join(str(Counter(p_)[i]) for i in (0, 1, 2)),
           r8['observed'], r8['debiased'], r8['p'], mk(r8['p']), r9['p'], mk(r9['p'])))

say('')
say('D2  IS THAT DIFFERENCE A PROPERTY OF THE CONVENTION OR OF THE MANUSCRIPT?')
say('    Same three conventions, same null, run on the 8 numeral positive')
say('    controls laid out in the identical sign/ring geometry. If a convention')
say('    were intrinsically blind, it would miss the numerals too.')
ctrl = ML.numeral_controls()
d2 = OrderedDict()
for nm, fn in CONV.items():
    hits = []
    for sysname, series in ctrl.items():
        itn = Z.build_items(Z.numeral_layout(tst, series), 'unit')
        f_ = [it['f1'] for it in itn]
        k_ = group_index([(it['sign'], it['ring']) for it in itn])
        p_ = [fn(it['idx_in_ring'], it['ring_size']) for it in itn]
        rr = perm_p(p_, f_, k_, 408)
        hits.append((sysname, rr['debiased'], rr['p'], rr['p'] < ALPHA_BONF))
    npass = sum(1 for _, _, _, ok in hits)
    med = sorted(h[1] for h in hits)[len(hits) // 2]
    d2[nm] = {'n_detected': npass, 'median_debiased': med,
              'detail': [(a, b, c) for a, b, c, _ in hits]}
    say('    %-18s numerals detected %d/8   median debiased %+.4f   [%s]'
        % (nm, npass, med, ' '.join(s for s, _, _, ok in hits if ok)))

say('')
say('D3  NUMBER OF BLOCKS (the protocol says "thirds"; 2 and 4 for reference)')
d3 = OrderedDict()
for k in (2, 3, 4, 6):
    p_ = [min(k - 1, (it['idx_in_ring'] * k) // it['ring_size']) for it in it_t]
    rr = perm_p(p_, form, g, 408)
    d3[k] = rr['p']
    say('    %d blocks (floor): MI=%.4f  debiased=%+.4f  p=%.5f  %s'
        % (k, rr['observed'], rr['debiased'], rr['p'],
           'PASS' if rr['p'] < ALPHA_BONF else 'fail'))

say('')
say('D4  CLOCK POSITIONS (an independent, non-ordinal reading of "position in')
say('    the ring" that ZL records directly)')
nclock = sum(1 for r in tst if r['clock'])
say('    TEST labels carrying a clock annotation: %d / %d' % (nclock, len(tst)))
if nclock >= 100:
    sub = [(r, it) for r, it in zip(tst, it_t) if r['clock_min'] is not None]
    p_ = [min(2, (r['clock_min'] * 3) // 720) for r, _ in sub]
    f_ = [it['f1'] for _, it in sub]
    k_ = group_index([(it['sign'], it['ring']) for _, it in sub])
    rr = perm_p(p_, f_, k_, 408)
    say('    MI(clock third of the dial; first unit) n=%d  debiased=%+.4f  p=%.5f  %s'
        % (len(sub), rr['debiased'], rr['p'],
           'PASS' if rr['p'] < ALPHA_BONF else 'fail'))
    d3['clock'] = rr['p']
else:
    say('    too few to test on equal terms; not run.')

say('')
say('D5  THE SAME THREE CONVENTIONS ON THE FIT SIGNS (out-of-sample)')
it_f = Z.build_items(fit, 'unit')
form_f = [it['f1'] for it in it_f]
g_f = group_index([(it['sign'], it['ring']) for it in it_f])
for nm, fn in CONV.items():
    p_ = [fn(it['idx_in_ring'], it['ring_size']) for it in it_f]
    rr = perm_p(p_, form_f, g_f, 408)
    say('    %-18s FIT n=%d  debiased=%+.4f  p=%.5f  %s'
        % (nm, len(it_f), rr['debiased'], rr['p'],
           'PASS' if rr['p'] < ALPHA_BONF else 'fail'))

with io.open(os.path.join(HERE, 'results', 'v_z4_confound_2.json'), 'w',
             encoding='utf-8') as f:
    json.dump({'D1': d1, 'D2': d2, 'D3': d3}, f, indent=1, default=str)
with io.open(os.path.join(HERE, 'results', 'v_z4_confound_2.stdout.txt'), 'w',
             encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n')
