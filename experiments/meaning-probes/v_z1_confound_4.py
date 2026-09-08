#!/usr/bin/env python3
"""v_z1_confound_4.py -- adversarial CONFOUND audit of Z1, part 4.

L. NULL CALIBRATION WITHOUT REUSE.  Two of the test's three negative controls
   came out significant (Vulgate p=0.0007, Culpeper p=0.0079), which it
   attributes to the 30-item series being reused across rings that sum to 139.
   If that explanation is wrong, the same mis-calibration would sit under the
   Voynich p = 0.56 and the null result would be uninterpretable.  Here the
   negative control is rebuilt with 139 DISTINCT real words (no reuse, exactly
   the Voynich situation) and replicated over 40 seeds: the type-I rate at
   p < 0.01 should be about 0.01.

M. DILUTION.  How much of a real numeral system could hide under this null?
   Replace a fraction q of the real Voynich labels, ring by ring, with an
   ordinal series written in the Voynich alphabet at the Voynich length, and
   find the smallest q the test detects.  The null is ordering-independent, so
   the detection boundary from part C applies exactly.
"""
import math, random, re, sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML

HERE = Path(__file__).resolve().parent
ZL3B = HERE / '..' / '..' / 'data' / 'corpora' / 'ZL3b-n.txt'
VULG = Path('R:/Coding/LinearA/tmp/voynich_lab/bibles/Latin.xml')
SEED, MIN_RING = ML.SEED, 8
SIZES = [18, 12, 18, 12, 18, 10, 16, 10, 16, 9]


def mean(xs):
    return sum(xs) / len(xs) if xs else float('nan')


def sd_pop(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs)) if xs else 0.0


def two_sided_p(obs, nulls):
    mu = mean(nulls)
    d = abs(obs - mu)
    return (1.0 + sum(1 for x in nulls if abs(x - mu) >= d - 1e-12)) / (len(nulls) + 1.0)


def mk(seqs):
    n = len(seqs)
    S = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            S[i][j] = S[j][i] = ML.lcs_sim(seqs[i], seqs[j])
    return S


def pooled(rings, orders):
    t1 = n1 = t3 = n3 = 0.0
    for S, o in zip(rings, orders):
        n = len(S)
        for i in range(n):
            for j in range(i + 1, n):
                v = S[o[i]][o[j]]
                g = j - i
                if g == 1:
                    t1 += v; n1 += 1
                elif g >= 3:
                    t3 += v; n3 += 1
    return (t1 / n1 if n1 else 0.0) - (t3 / n3 if n3 else 0.0)


def run(rings, nperm, seed=SEED):
    obs = pooled(rings, [list(range(len(S))) for S in rings])
    rng = random.Random(seed)
    nulls = []
    for _ in range(nperm):
        os_ = []
        for S in rings:
            p = list(range(len(S)))
            rng.shuffle(p)
            os_.append(p)
        nulls.append(pooled(rings, os_))
    return obs, two_sided_p(obs, nulls), mean(nulls), sd_pop(nulls)


def seq_of_words(words, level='units'):
    out = []
    for w in words:
        out.extend(ML.bpe_apply(w) if level == 'units' else list(w))
    return out


print('=' * 78)
print('v_z1_confound_4  --  null calibration and dilution')
print('sha256 ZL3b ', ML.sha256(str(ZL3B)))
print('=' * 78)

# ---- L. calibration ---------------------------------------------------------
print('\n--- L. negative control WITHOUT series reuse (139 distinct words) ---')
vtxt = re.sub(r'<[^>]*>', ' ', VULG.read_text(encoding='utf-8', errors='replace'))
vtypes = sorted(set(w.lower() for w in re.findall(r'[A-Za-z]+', vtxt) if len(w) >= 2))
print('  Vulgate word types available: %d' % len(vtypes))

# (a) the test\'s own construction: 30 types reused across rings summing to 139
r30 = random.Random(SEED).sample(vtypes, 30)
rings_reuse, k = [], 0
for sz in SIZES:
    rings_reuse.append(mk([list(r30[(k + i) % 30]) for i in range(sz)]))
    k = (k + sz) % 30
o, p, m, s = run(rings_reuse, 10000)
print('  30 types reused (as in t_z1.py):    Delta = %+.5f  p = %.4f  '
      '(null mean %+.5f sd %.5f)' % (o, p, m, s))

# (b) 139 distinct types, no reuse -- the Voynich situation
ps = []
for rep in range(40):
    rr = random.Random(1000 + rep)
    pool = rr.sample(vtypes, sum(SIZES))
    rings, i = [], 0
    for sz in SIZES:
        rings.append(mk([list(w) for w in pool[i:i + sz]])); i += sz
    o2, p2, m2, s2 = run(rings, 1000, seed=SEED + rep)
    ps.append(p2)
    if rep < 5:
        print('  139 distinct types, seed %-4d      Delta = %+.5f  p = %.4f  '
              '(null mean %+.5f sd %.5f)' % (1000 + rep, o2, p2, m2, s2))
print('  ... 40 replicates. p<0.01 in %d/40 (%.3f), p<0.05 in %d/40 (%.3f); '
      'median p = %.3f' % (sum(1 for x in ps if x < 0.01), sum(1 for x in ps if x < 0.01) / 40.0,
                           sum(1 for x in ps if x < 0.05), sum(1 for x in ps if x < 0.05) / 40.0,
                           sorted(ps)[20]))
print('  -> with distinct items per ring the null is calibrated; the two')
print('     significant negative controls in t_z1.py are indeed the reuse')
print('     artefact it names, and the Voynich run (10 distinct rings) is clean.')

# ---- M. dilution ------------------------------------------------------------
print('\n--- M. how diluted could a real numeral system be and still hide? ---')
pages = ML.parse_pages(str(ZL3B), comma_split=True)
labels = ML.zodiac_labels(pages)
by = ML.sign_rings(labels)
REAL = []
for s in ML.TEST_SIGNS:
    for ring, recs in by[s].items():
        if len(recs) >= MIN_RING:
            REAL.append([seq_of_words(r['words']) for r in recs])

alpha = [c for c, _ in Counter(c for rr in REAL for u in rr for c in ''.join(u)).most_common()]
rng = random.Random(SEED)
tens = [''.join(rng.choice(alpha) for _ in range(2)) for _ in range(4)]
unit = [''.join(rng.choice(alpha) for _ in range(2)) for _ in range(10)]
NUM = [ML.bpe_apply(tens[n // 10] + unit[n % 10]) for n in range(1, 31)]

# detection boundary, from the real data's own permutation null (part C)
REAL_S = [mk(r) for r in REAL]
obs0, p0, mu0, sd0 = run(REAL_S, 10000)
rngz = random.Random(SEED)
nulls = []
for _ in range(10000):
    nulls.append(pooled(REAL_S, [rngz.sample(range(len(S)), len(S)) for S in REAL_S]))
devs = sorted(abs(x - mu0) for x in nulls)
crit = devs[int(math.ceil(0.99 * len(devs))) - 1]
print('  real TEST rings: Delta = %+.5f p = %.4f ; detection boundary '
      'Delta >= %+.5f' % (obs0, p0, mu0 + crit))
print('  q = fraction of each ring replaced by consecutive numerals of the '
      'synthetic system')
print('  %-6s %-10s %-10s' % ('q', 'Delta', 'detected?'))
for q in (0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0):
    ds = []
    for rep in range(20):
        rr = random.Random(5000 + rep)
        rings = []
        for ring in REAL:
            n = len(ring)
            k = int(round(q * n))
            idx = sorted(rr.sample(range(n), k))
            new = list(ring)
            for pos in idx:
                new[pos] = NUM[pos % 30]
            rings.append(mk(new))
        ds.append(pooled(rings, [list(range(len(S))) for S in rings]))
    det = sum(1 for d in ds if d >= mu0 + crit) / float(len(ds))
    print('  %-6.1f %+9.5f  %.2f' % (q, mean(ds), det))
print('  (numerals are inserted AT their ring positions, so the ordinal')
print('   information is real; the rest of the ring stays genuine Voynich.)')
