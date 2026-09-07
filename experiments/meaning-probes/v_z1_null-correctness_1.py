#!/usr/bin/env python3
"""Adversarial verification of t_z1.py -- lens: null-correctness.
Independent, naive re-implementation. No reuse of t_z1 machinery except
meaning_lib data access.
"""
import json, math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML

HERE = Path(__file__).resolve().parent
ZL3B = HERE / '..' / '..' / 'data' / 'corpora' / 'ZL3b-n.txt'
MIN_RING = 8


# ---------- my own rank / spearman, written from scratch ----------
def ranks_avg(v):
    n = len(v)
    idx = sorted(range(n), key=lambda i: v[i])
    r = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and v[idx[j + 1]] == v[idx[i]]:
            j += 1
        avg = sum(range(i + 1, j + 2)) / float(j - i + 1)
        for k in range(i, j + 1):
            r[idx[k]] = avg
        i = j + 1
    return r


def pearson(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    dx = math.sqrt(sum((a - mx) ** 2 for a in x))
    dy = math.sqrt(sum((b - my) ** 2 for b in y))
    return num / (dx * dy) if dx > 0 and dy > 0 else 0.0


def spearman(x, y):
    return pearson(ranks_avg(x), ranks_avg(y))


# ---------- naive per-ring statistic ----------
def ring_pairs(seqs):
    """Return list of (gap, sim) for every unordered pair, naive O(n^2) LCS."""
    n = len(seqs)
    out = []
    for i in range(n):
        for j in range(i + 1, n):
            out.append((j - i, ML.lcs_sim(seqs[i], seqs[j])))
    return out


def stats_naive(ring_orders):
    """ring_orders: list of rings, each a list of sequences IN ORDER."""
    g1, g3 = [], []
    rhos = []
    per_ring = []
    for seqs in ring_orders:
        pr = ring_pairs(seqs)
        gs = [g for g, s in pr]
        ss = [s for g, s in pr]
        a = [s for g, s in pr if g == 1]
        c = [s for g, s in pr if g >= 3]
        g1 += a
        g3 += c
        rhos.append(spearman(gs, ss))
        per_ring.append((len(pr), (sum(a) / len(a) - sum(c) / len(c)) if a and c else 0.0))
    delta = sum(g1) / len(g1) - sum(g3) / len(g3)
    wsum = sum(m for m, d in per_ring)
    delta_alt = sum(m * d for m, d in per_ring) / wsum
    return delta, delta_alt, sum(rhos) / len(rhos), len(g1), len(g3)


def two_sided_p_centered(obs, nulls):
    mu = sum(nulls) / len(nulls)
    d = abs(obs - mu)
    c = sum(1 for x in nulls if abs(x - mu) >= d - 1e-12)
    return (1.0 + c) / (len(nulls) + 1.0)


def two_sided_p_doubled(obs, nulls):
    """The other standard two-sided rule: 2*min(one-sided), capped at 1."""
    n = len(nulls)
    hi = (1.0 + sum(1 for x in nulls if x >= obs - 1e-12)) / (n + 1.0)
    lo = (1.0 + sum(1 for x in nulls if x <= obs + 1e-12)) / (n + 1.0)
    return min(1.0, 2.0 * min(hi, lo)), hi, lo


def seq_of_words(words, level):
    out = []
    for w in words:
        out.extend(ML.bpe_apply(w) if level == 'units' else list(w))
    return out


def voynich_rings(signs, level, comma):
    pages = ML.parse_pages(str(ZL3B), comma_split=comma)
    labels = ML.zodiac_labels(pages, comma_split=comma)
    by = ML.sign_rings(labels)
    rings, meta = [], []
    for s in signs:
        for ring, recs in by.get(s, {}).items():
            if len(recs) >= MIN_RING:
                rings.append([seq_of_words(r['words'], level) for r in recs])
                meta.append((s, ring, len(recs)))
    return rings, meta


def permute_null(rings, nperm, seed):
    rng = random.Random(seed)
    nd, nda, nr = [], [], []
    base = [list(r) for r in rings]
    for _ in range(nperm):
        perm = []
        for r in base:
            c = list(r)
            rng.shuffle(c)
            perm.append(c)
        d, da, rho, _, _ = stats_naive(perm)
        nd.append(d); nda.append(da); nr.append(rho)
    return nd, nda, nr


def main():
    print('=' * 78)
    print('V-Z1 null-correctness: independent naive recomputation')
    print('=' * 78)

    rings, meta = voynich_rings(ML.TEST_SIGNS, 'units', True)
    print('TEST rings:', meta)
    print('sizes', [len(r) for r in rings], 'sum', sum(len(r) for r in rings))
    d, da, rho, n1, n3 = stats_naive(rings)
    print('OBSERVED (naive): Delta=%+.8f delta_alt=%+.8f rho_bar=%+.8f  n_g1=%d n_g3=%d'
          % (d, da, rho, n1, n3))

    j = json.load(open(HERE / 'results' / 'z1.json'))
    g = j['results']['gate']
    print('t_z1 JSON       : Delta=%+.8f delta_alt=%+.8f rho_bar=%+.8f'
          % (g['delta'], g['delta_alt'], g['rho_bar']))
    print('  match Delta   : %s (diff %.2e)' % (abs(d - g['delta']) < 1e-12, abs(d - g['delta'])))
    print('  match alt     : %s' % (abs(da - g['delta_alt']) < 1e-12))
    print('  match rho_bar : %s (diff %.2e)' % (abs(rho - g['rho_bar']) < 1e-12,
                                                abs(rho - g['rho_bar'])))

    # independent null, DIFFERENT rng stream (own shuffle order) and 2 seeds
    for seed in (408, 20260907):
        nd, nda, nr = permute_null(rings, 10000, seed)
        mu = sum(nd) / len(nd)
        sd = math.sqrt(sum((x - mu) ** 2 for x in nd) / len(nd))
        mur = sum(nr) / len(nr)
        sdr = math.sqrt(sum((x - mur) ** 2 for x in nr) / len(nr))
        p_c = two_sided_p_centered(d, nd)
        p_d, hi, lo = two_sided_p_doubled(d, nd)
        pr_c = two_sided_p_centered(rho, nr)
        pr_d, rhi, rlo = two_sided_p_doubled(rho, nr)
        print('')
        print('--- own permutation null, seed %d, 10000 draws ---' % seed)
        print('  Delta   null mean %+.6f sd %.6f  z=%+.3f' % (mu, sd, (d - mu) / sd))
        print('    p two-sided (centered, t_z1 rule) = %.4f' % p_c)
        print('    p two-sided (2*min one-sided)     = %.4f   [right %.4f  left %.4f]'
              % (p_d, hi, lo))
        print('  rho_bar null mean %+.6f sd %.6f  z=%+.3f' % (mur, sdr, (rho - mur) / sdr))
        print('    p two-sided (centered)            = %.4f' % pr_c)
        print('    p two-sided (2*min one-sided)     = %.4f   [right %.4f  left %.4f]'
              % (pr_d, rhi, rlo))
        print('  delta_alt p (centered)              = %.4f'
              % two_sided_p_centered(da, nda))

    # ---- is the null mean of Delta supposed to be 0? diagnose the pooling ----
    print('')
    print('--- why is the Delta null mean non-zero? ---')
    tot_w1 = tot_w3 = 0.0
    num1 = num3 = 0.0
    for seqs in rings:
        pr = ring_pairs(seqs)
        mean_ring = sum(s for _, s in pr) / len(pr)
        n = len(seqs)
        a = n - 1
        c = len(pr) - (n - 1) - (n - 2)
        num1 += a * mean_ring; tot_w1 += a
        num3 += c * mean_ring; tot_w3 += c
    print('  analytic E[Delta] under within-ring permutation = %+.8f'
          % (num1 / tot_w1 - num3 / tot_w3))
    print('  (matches the simulated null mean; the pooled Delta is a biased')
    print('   estimator because g=1 and g>=3 weight the rings differently.')
    print('   The permutation p is centred on this mean, so the TEST is valid.)')

    # bias-corrected effect size, and what it does to gate (ii)
    an = num1 / tot_w1 - num3 / tot_w3
    print('  bias-corrected Voynich Delta = %+.6f' % (d - an))

    print('')
    print('--- gate (ii) re-derivation with bias-corrected control Deltas ---')
    nums = ML.numeral_controls()
    sizes = [len(r) for r in rings]

    def cut_cyclic(series, sizes):
        out, k = [], 0
        for sz in sizes:
            out.append([series[(k + i) % len(series)] for i in range(sz)])
            k = (k + sz) % len(series)
        return out

    corr = []
    for name, series in nums.items():
        cr = [[list(w) for w in ring] for ring in cut_cyclic(series, sizes)]
        dd, _, rr, _, _ = stats_naive(cr)
        # analytic null mean for this control
        n1w = n3w = a1 = a3 = 0.0
        for seqs in cr:
            pr = ring_pairs(seqs)
            mr = sum(s for _, s in pr) / len(pr)
            n = len(seqs)
            aa = n - 1; cc = len(pr) - (n - 1) - (n - 2)
            a1 += aa * mr; n1w += aa
            a3 += cc * mr; n3w += cc
        an_c = a1 / n1w - a3 / n3w
        corr.append((name, dd, dd - an_c))
        print('  %-20s Delta=%+.5f  bias-corrected=%+.5f' % (name, dd, dd - an_c))
    raw_med = sorted(x[1] for x in corr)
    bc_med = sorted(x[2] for x in corr)
    med_raw = 0.5 * (raw_med[3] + raw_med[4])
    med_bc = 0.5 * (bc_med[3] + bc_med[4])
    print('  median raw = %.5f -> 25%% = %.5f  ; Voynich raw %+.5f -> %s'
          % (med_raw, 0.25 * med_raw, d, 'MET' if d >= 0.25 * med_raw else 'NOT MET'))
    print('  median bias-corrected = %.5f -> 25%% = %.5f ; Voynich bc %+.5f -> %s'
          % (med_bc, 0.25 * med_bc, d - an,
             'MET' if (d - an) >= 0.25 * med_bc else 'NOT MET'))

    # ---- control construction: how many DISTINCT rings does cut_cyclic make? --
    print('')
    print('--- cut_cyclic duplication diagnostic at sizes %s ---' % sizes)
    starts, k = [], 0
    for sz in sizes:
        starts.append((k, sz)); k = (k + sz) % 30
    print('  (start,size) per ring:', starts)
    print('  distinct rings: %d of %d' % (len(set(starts)), len(starts)))


if __name__ == '__main__':
    main()
