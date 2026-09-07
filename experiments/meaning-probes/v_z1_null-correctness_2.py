#!/usr/bin/env python3
"""V-Z1 part 2: (a) empirical type-I calibration of the Delta permutation test
at the OBSERVED Voynich ring configuration, (b) a reuse-free minimum-detectable-
effect power derivation that does not depend on the control-reuse construction,
(c) degenerate-ring / dropped-label diagnostics."""
import json, math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML

HERE = Path(__file__).resolve().parent
ZL3B = HERE / '..' / '..' / 'data' / 'corpora' / 'ZL3b-n.txt'
MIN_RING = 8


def seq_of_words(words, level='units'):
    out = []
    for w in words:
        out.extend(ML.bpe_apply(w) if level == 'units' else list(w))
    return out


def build(signs, level='units', comma=True):
    pages = ML.parse_pages(str(ZL3B), comma_split=comma)
    labels = ML.zodiac_labels(pages, comma_split=comma)
    by = ML.sign_rings(labels)
    rings = []
    for s in signs:
        for ring, recs in by.get(s, {}).items():
            if len(recs) >= MIN_RING:
                rings.append([seq_of_words(r['words'], level) for r in recs])
    return rings


class Fast(object):
    """My own fast Delta scaffold (independent of t_z1's Ring)."""
    def __init__(self, seqs):
        n = self.n = len(seqs)
        S = [[0.0] * n for _ in range(n)]
        tot = 0.0
        vals = []
        for i in range(n):
            for j in range(i + 1, n):
                s = ML.lcs_sim(seqs[i], seqs[j])
                S[i][j] = S[j][i] = s
                tot += s
                vals.append(s)
        self.S, self.total = S, tot
        self.m = n * (n - 1) // 2
        self.a = n - 1
        self.c = self.m - (n - 1) - (n - 2)
        self.sd_sim = math.sqrt(sum((v - tot / self.m) ** 2 for v in vals) / self.m)

    def d13(self, p):
        S = self.S
        s1 = sum(S[a][b] for a, b in zip(p, p[1:]))
        s2 = sum(S[a][b] for a, b in zip(p, p[2:]))
        return s1, self.total - s1 - s2


def delta_of(fs, perms):
    t1 = t3 = 0.0
    n1 = n3 = 0
    for f, p in zip(fs, perms):
        s1, s3 = f.d13(p)
        t1 += s1; n1 += f.a
        t3 += s3; n3 += f.c
    return t1 / n1 - t3 / n3


def p_centered(obs, nulls):
    mu = sum(nulls) / len(nulls)
    d = abs(obs - mu)
    return (1.0 + sum(1 for x in nulls if abs(x - mu) >= d - 1e-12)) / (len(nulls) + 1.0)


def main():
    rings = build(ML.TEST_SIGNS)
    fs = [Fast(r) for r in rings]
    ident = [list(range(f.n)) for f in fs]
    obs = delta_of(fs, ident)
    print('observed Delta (own fast path) = %+.8f' % obs)
    print('per-ring sd of pair similarities:',
          ' '.join('%.4f' % f.sd_sim for f in fs))
    print('any degenerate ring (sd == 0)?',
          any(f.sd_sim == 0 for f in fs))

    # ---------- (a) empirical type-I calibration ----------
    # Draw synthetic datasets FROM H0 (relabel each ring at random), run the
    # same test on each, and check the p-value distribution is uniform.
    print('')
    print('--- (a) type-I calibration: 400 H0 datasets x 999 permutations ---')
    rng = random.Random(408)
    ps = []
    for _ in range(400):
        data = []
        for f in fs:
            q = list(range(f.n)); rng.shuffle(q); data.append(q)
        o = delta_of(fs, data)
        nulls = []
        for _ in range(999):
            pp = []
            for f in fs:
                q = list(range(f.n)); rng.shuffle(q); pp.append(q)
            nulls.append(delta_of(fs, pp))
        ps.append(p_centered(o, nulls))
    for a in (0.01, 0.05, 0.10, 0.25, 0.50):
        print('   P(p <= %.2f) = %.4f   (nominal %.2f)'
              % (a, sum(1 for x in ps if x <= a + 1e-12) / len(ps), a))
    print('   mean p = %.4f (nominal 0.5)' % (sum(ps) / len(ps)))

    # ---------- (b) reuse-free minimum detectable effect ----------
    print('')
    print('--- (b) minimum detectable Delta at the OBSERVED configuration ---')
    rng2 = random.Random(408)
    nulls = []
    for _ in range(20000):
        pp = []
        for f in fs:
            q = list(range(f.n)); rng2.shuffle(q); pp.append(q)
        nulls.append(delta_of(fs, pp))
    mu = sum(nulls) / len(nulls)
    dev = sorted(abs(x - mu) for x in nulls)
    crit = dev[int(math.ceil(0.99 * len(dev))) - 1]
    mde = mu + crit
    j = json.load(open(HERE / 'results' / 'z1.json'))
    med = j['results']['gate']['numeral_median_delta_used']
    print('   null mean %+.6f ; |dev| 99th pct = %.6f' % (mu, crit))
    print('   smallest Delta reaching two-sided p < 0.01 = %+.6f' % mde)
    print('   that is %.1f%% of the numeral-control median Delta (%.5f)'
          % (100.0 * mde / med, med))
    print('   numeral controls as %% of that detection floor:')
    nc = j['results']['numeral_controls']
    for k, v in nc.items():
        if k.endswith('|cyclic'):
            print('     %-24s Delta %+.5f = %5.0f%% of the floor  -> %s'
                  % (k.split('|')[0], v['delta'], 100.0 * v['delta'] / mde,
                     'DETECTABLE' if v['delta'] >= mde else 'not detectable'))
    print('   observed Voynich Delta %+.6f = %.0f%% of the floor' % (obs, 100.0 * obs / mde))

    # ---------- (c) dropped labels / ring segmentation diagnostics ----------
    print('')
    print('--- (c) how many zodiac label loci are dropped for having no token? ---')
    pages = ML.parse_pages(str(ZL3B))
    tot = kept = 0
    for p in pages.values():
        for l in p['loci']:
            if l['type'] == 'L' and l['sub'] == 'z':
                tot += 1
                if l['words']:
                    kept += 1
    print('   Lz loci total %d, with >=1 clean token %d, dropped %d' % (tot, kept, tot - kept))

    # ---------- (d) does the pooled-vs-per-ring choice matter? ----------
    print('')
    print('--- (d) unweighted mean of per-ring Deltas (a third pooling) ---')
    ds = []
    for f in fs:
        s1, s3 = f.d13(list(range(f.n)))
        ds.append(s1 / f.a - s3 / f.c)
    print('   per-ring Deltas:', ' '.join('%+.4f' % x for x in ds))
    print('   unweighted mean = %+.6f ; rings with Delta > 0: %d of %d'
          % (sum(ds) / len(ds), sum(1 for x in ds if x > 0), len(ds)))
    rng3 = random.Random(408)
    nn = []
    for _ in range(10000):
        v = []
        for f in fs:
            q = list(range(f.n)); rng3.shuffle(q)
            s1, s3 = f.d13(q)
            v.append(s1 / f.a - s3 / f.c)
        nn.append(sum(v) / len(v))
    print('   p (centered, 10000 draws) = %.4f' % p_centered(sum(ds) / len(ds), nn))


if __name__ == '__main__':
    main()
