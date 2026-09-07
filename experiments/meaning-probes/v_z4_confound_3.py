#!/usr/bin/env python3
"""v_z4_confound_3.py — geometry vs. counting, and a corrected power table.

ZL records a clock position for every one of the 147 TEST zodiac labels. That
is where the label physically sits on the dial. t_z4's P2 ("thirds of the
ring") instead uses the ORDINAL INDEX of the label in ZL's locus list, divided
into three by count. The two are the same thing only if the labels are evenly
spaced. They are not.

E1  ring-relative ANGULAR third: measure each label's angle from its own ring's
    first label (so ZL's origin is kept, only the metric changes from
    "how many labels before me" to "how far round am I"), bin into 120-degree
    arcs. Power measured on the 8 numeral series the same way.
E2  absolute dial third (0-4h / 4-8h / 8-12h).
E3  fixed D2 count: numerals detected under each remainder convention.
E4  power of the 2/4/6-block variants, so D3 can be read.
E5  how uneven the spacing actually is.
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
g = group_index([(it['sign'], it['ring']) for it in it_t])


def angular_thirds(labels, k=3):
    """Angle of each label measured from the first label of its own ring,
    binned into k equal arcs. Direction taken as the one in which the ring's
    labels are numbered (majority sign of the successive clock deltas)."""
    byring = OrderedDict()
    for i, r in enumerate(labels):
        byring.setdefault((r['sign'], r['ring']), []).append(i)
    pos = [0] * len(labels)
    spread = []
    for key, mem in byring.items():
        cm = [labels[i]['clock_min'] for i in mem]
        if any(c is None for c in cm):
            for i in mem:
                pos[i] = -1
            continue
        # direction: clockwise if the cumulative clockwise step is smaller
        cw = sum((cm[j + 1] - cm[j]) % 720 for j in range(len(cm) - 1))
        ccw = sum((cm[j] - cm[j + 1]) % 720 for j in range(len(cm) - 1))
        sgn = 1 if cw <= ccw else -1
        base = cm[0]
        for i, c in zip(mem, cm):
            d = ((c - base) * sgn) % 720
            pos[i] = min(k - 1, int(d * k) // 720)
        gaps = sorted(((cm[j + 1] - cm[j]) * sgn) % 720 for j in range(len(cm) - 1))
        spread.append((key, len(mem), gaps[0], gaps[-1]))
    return pos, spread


say('=' * 78)
say('E5  IS THE RING EVENLY SPACED? (if it were, ordinal thirds == angular')
say('    thirds and the distinction below would not exist)')
_, spread = angular_thirds(tst)
for key, n, gmin, gmax in spread:
    say('    %-22s n=%2d  smallest gap %3d min  largest gap %3d min  (even = %d)'
        % ('%s/ring%d' % key, n, gmin, gmax, 720 // n))

say('')
say('=' * 78)
say('E1  RING-RELATIVE ANGULAR THIRD (same origin as t_z4, geometric metric)')
pos_a, _ = angular_thirds(tst)
assert all(p >= 0 for p in pos_a), 'missing clock'
ra = perm_p(pos_a, form, g, 408)
ra9 = perm_p(pos_a, form, g, 409)
nmove = sum(1 for a, it in zip(pos_a, it_t) if a != it['p2'])
say('    marginal %s   %d of %d labels land in a different third than under'
    % (dict(Counter(pos_a)), nmove, len(it_t)))
say('    t_z4\'s count-based thirds.')
say('    MI=%.4f  null_mean=%.4f  debiased=%+.4f  p(408)=%.5f %s  p(409)=%.5f %s'
    % (ra['observed'], ra['null_mean'], ra['debiased'], ra['p'],
       'PASS' if ra['p'] < ALPHA_BONF else 'fail', ra9['p'],
       'PASS' if ra9['p'] < ALPHA_BONF else 'fail'))

say('')
say('    power of the angular reading on the 8 numeral series (same layout):')
ctrl = ML.numeral_controls()
hits = []
for sysname, series in ctrl.items():
    nl = Z.numeral_layout(tst, series)
    itn = Z.build_items(nl, 'unit')
    f_ = [it['f1'] for it in itn]
    k_ = group_index([(it['sign'], it['ring']) for it in itn])
    pa, _ = angular_thirds(nl)
    rr = perm_p(pa, f_, k_, 408)
    hits.append((sysname, rr['debiased'], rr['p'], rr['p'] < ALPHA_BONF))
    say('      %-20s debiased=%+.4f  p=%.5f  %s'
        % (sysname, rr['debiased'], rr['p'], 'detected' if rr['p'] < ALPHA_BONF else '-'))
nang = sum(1 for h in hits if h[3])
say('    angular reading detects %d/8 numeral systems (t_z4 count-based: 3/8)' % nang)

say('')
say('=' * 78)
say('E2  ABSOLUTE DIAL THIRD (0-4h / 4-8h / 8-12h), no ring-specific origin')
pos_b = [min(2, (r['clock_min'] * 3) // 720) for r in tst]
rb = perm_p(pos_b, form, g, 408)
say('    marginal %s  MI=%.4f  debiased=%+.4f  p=%.5f  %s'
    % (dict(Counter(pos_b)), rb['observed'], rb['debiased'], rb['p'],
       'PASS' if rb['p'] < ALPHA_BONF else 'fail'))

say('')
say('=' * 78)
say('E3  CORRECTED POWER TABLE FOR THE THREE REMAINDER CONVENTIONS')
CONV = OrderedDict([
    ('floor(registered)', lambda i, s, k=3: min(k - 1, (i * k) // s)),
    ('midpoint',          lambda i, s, k=3: min(k - 1, int(math.floor((i + 0.5) * k / s)))),
    ('ceil',              lambda i, s, k=3: min(k - 1, int(math.ceil((i + 1) * k / s)) - 1)),
])
e3 = OrderedDict()
for nm, fn in CONV.items():
    hh = []
    for sysname, series in ctrl.items():
        itn = Z.build_items(Z.numeral_layout(tst, series), 'unit')
        f_ = [it['f1'] for it in itn]
        k_ = group_index([(it['sign'], it['ring']) for it in itn])
        p_ = [fn(it['idx_in_ring'], it['ring_size']) for it in itn]
        rr = perm_p(p_, f_, k_, 408)
        hh.append((sysname, rr['debiased'], rr['p'] < ALPHA_BONF))
    npass = sum(1 for h in hh if h[2])
    med = sorted(h[1] for h in hh)[len(hh) // 2]
    e3[nm] = {'detected': npass, 'median_debiased': med}
    say('    %-18s numerals detected %d/8  median debiased %+.4f  [%s]'
        % (nm, npass, med, ' '.join(s for s, _, ok in hh if ok)))

say('')
say('=' * 78)
say('E4  POWER OF THE k-BLOCK VARIANTS (so the k=2/4/6 failures can be read)')
e4 = OrderedDict()
for k in (2, 3, 4, 6):
    p_ = [min(k - 1, (it['idx_in_ring'] * k) // it['ring_size']) for it in it_t]
    rr = perm_p(p_, form, g, 408)
    hh = 0
    for sysname, series in ctrl.items():
        itn = Z.build_items(Z.numeral_layout(tst, series), 'unit')
        f_ = [it['f1'] for it in itn]
        k_ = group_index([(it['sign'], it['ring']) for it in itn])
        q_ = [min(k - 1, (it['idx_in_ring'] * k) // it['ring_size']) for it in itn]
        r2 = perm_p(q_, f_, k_, 408)
        hh += 1 if r2['p'] < ALPHA_BONF else 0
    e4[k] = {'ms_p': rr['p'], 'ms_debiased': rr['debiased'], 'numerals': hh}
    say('    k=%d  manuscript debiased=%+.4f p=%.5f %-4s   numerals detected %d/8'
        % (k, rr['debiased'], rr['p'],
           'PASS' if rr['p'] < ALPHA_BONF else 'fail', hh))

with io.open(os.path.join(HERE, 'results', 'v_z4_confound_3.json'), 'w',
             encoding='utf-8') as f:
    json.dump({'E1_angular_p408': ra['p'], 'E1_angular_p409': ra9['p'],
               'E1_angular_debiased': ra['debiased'],
               'E1_angular_power': nang,
               'E1_n_relabelled': nmove,
               'E2_dial_p': rb['p'], 'E3': e3, 'E4': e4}, f, indent=1, default=str)
with io.open(os.path.join(HERE, 'results', 'v_z4_confound_3.stdout.txt'), 'w',
             encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n')
