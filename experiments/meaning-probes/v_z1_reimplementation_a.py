#!/usr/bin/env python3
"""Independent reimplementation of Z1 from PROTOCOL.md + meaning_lib only.

Adversarial verifier, lens = reimplementation. Written WITHOUT reading t_z1.py.
"""
import json, random, sys
from collections import OrderedDict
sys.path.insert(0, r"R:/Coding/LinearA/tmp/voynich_repo/experiments/meaning-probes")
import meaning_lib as ml

ZL = r"R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt"
SEED = 408
NPERM = 10000
MIN_RING = 8

# --------------------------------------------------------------- statistics --

def gaps_cyclic(n, i, j):
    d = abs(i - j)
    return min(d, n - d)

def gaps_linear(n, i, j):
    return abs(i - j)

def pair_list(seqs, gapfn):
    """seqs: list of glyph-unit sequences in ring order.
    Returns list of (gap, i, j) for all unordered pairs."""
    n = len(seqs)
    out = []
    for i in range(n):
        for j in range(i + 1, n):
            out.append((gapfn(n, i, j), i, j))
    return out

def sim_matrix(seqs):
    n = len(seqs)
    M = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            s = ml.lcs_sim(seqs[i], seqs[j])
            M[i][j] = s
            M[j][i] = s
    return M

def spearman(x, y):
    """Spearman rho with average ranks for ties."""
    n = len(x)
    if n < 3:
        return None
    def ranks(v):
        idx = sorted(range(n), key=lambda k: v[k])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[idx[j + 1]] == v[idx[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[idx[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(x), ranks(y)
    mx = sum(rx) / n; my = sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)

def stats_from_perm(rings_pairs, rings_sims, perms):
    """rings_pairs: list of pair lists (gap,i,j) per ring (positions).
    rings_sims: list of sim matrices indexed by LABEL id.
    perms: list of permutations mapping position -> label index.
    Returns (Delta, rho_bar)."""
    s1 = 0.0; n1 = 0
    s3 = 0.0; n3 = 0
    rhos = []
    for pairs, M, perm in zip(rings_pairs, rings_sims, perms):
        gs = []; ss = []
        for (g, i, j) in pairs:
            s = M[perm[i]][perm[j]]
            gs.append(g); ss.append(s)
            if g == 1:
                s1 += s; n1 += 1
            elif g >= 3:
                s3 += s; n3 += 1
        r = spearman(gs, ss)
        if r is not None:
            rhos.append(r)
    delta = (s1 / n1 if n1 else 0.0) - (s3 / n3 if n3 else 0.0)
    rho_bar = sum(rhos) / len(rhos) if rhos else 0.0
    return delta, rho_bar

def run_z1(ring_seqs, nperm=NPERM, seed=SEED, cyclic=True):
    """ring_seqs: list of lists of glyph-unit sequences (one list per ring)."""
    gapfn = gaps_cyclic if cyclic else gaps_linear
    rings_pairs = [pair_list(s, gapfn) for s in ring_seqs]
    rings_sims = [sim_matrix(s) for s in ring_seqs]
    ident = [list(range(len(s))) for s in ring_seqs]
    obs_d, obs_r = stats_from_perm(rings_pairs, rings_sims, ident)
    rng = random.Random(seed)
    nd = []; nr = []
    for _ in range(nperm):
        perms = []
        for s in ring_seqs:
            p = list(range(len(s)))
            rng.shuffle(p)
            perms.append(p)
        d, r = stats_from_perm(rings_pairs, rings_sims, perms)
        nd.append(d); nr.append(r)
    def two_sided(obs, null):
        m = sum(null) / len(null)
        c = sum(1 for v in null if abs(v - m) >= abs(obs - m))
        return (c + 1.0) / (len(null) + 1.0), c / float(len(null)), m, \
               (sum((v - m) ** 2 for v in null) / len(null)) ** 0.5
    pd_add1, pd_raw, md, sd = two_sided(obs_d, nd)
    pr_add1, pr_raw, mr, sr = two_sided(obs_r, nr)
    return {
        'n_rings': len(ring_seqs),
        'ring_sizes': [len(s) for s in ring_seqs],
        'n_labels': sum(len(s) for s in ring_seqs),
        'n_pairs': sum(len(p) for p in rings_pairs),
        'delta': obs_d, 'p_delta_add1': pd_add1, 'p_delta_raw': pd_raw,
        'null_delta_mean': md, 'null_delta_sd': sd,
        'rho_bar': obs_r, 'p_rho_add1': pr_add1, 'p_rho_raw': pr_raw,
        'null_rho_mean': mr, 'null_rho_sd': sr,
    }

def mean_sims(ring_seqs, cyclic=True):
    gapfn = gaps_cyclic if cyclic else gaps_linear
    s1 = []; s3 = []
    for seqs in ring_seqs:
        n = len(seqs)
        for i in range(n):
            for j in range(i + 1, n):
                g = gapfn(n, i, j)
                s = ml.lcs_sim(seqs[i], seqs[j])
                if g == 1: s1.append(s)
                elif g >= 3: s3.append(s)
    return sum(s1) / len(s1), sum(s3) / len(s3)

# ------------------------------------------------------------------- data ----

def voynich_rings(comma_split=True, level='units'):
    pages = ml.parse_pages(ZL, comma_split=comma_split)
    labels = ml.zodiac_labels(pages, comma_split=comma_split)
    sr = ml.sign_rings(labels)
    out = {}
    for sign, rings in sr.items():
        for ring, recs in rings.items():
            if len(recs) < MIN_RING:
                continue
            seqs = []
            for r in recs:
                if level == 'units':
                    u = []
                    for w in r['words']:
                        u.extend(ml.bpe_apply(w))
                    seqs.append(u)
                else:
                    seqs.append(list(''.join(r['words'])))
            out.setdefault(sign, []).append(seqs)
    return out

def control_rings(series, sizes, mode='cyclic'):
    """Cut a 30-item series into rings of exactly `sizes`, wrapping."""
    seqs = [list(ml.bpe_apply(s)) if False else list(s) for s in series]
    rings = []
    pos = 0
    for sz in sizes:
        r = [seqs[(pos + k) % len(seqs)] for k in range(sz)]
        rings.append(r)
        pos = (pos + sz) % len(seqs) if mode == 'cyclic' else 0
    return rings

# ------------------------------------------------------------------- main ----

def main():
    res = OrderedDict()
    res['sha256'] = {'ZL3b-n.txt': ml.sha256(ZL)}

    vr = voynich_rings()
    test_rings = [r for s in ml.TEST_SIGNS for r in vr.get(s, [])]
    fit_rings = [r for s in ml.FIT_SIGNS for r in vr.get(s, [])]
    sizes = [len(r) for r in test_rings]
    print('TEST ring sizes:', sizes, 'total labels', sum(sizes))
    print('FIT  ring sizes:', [len(r) for r in fit_rings], 'total labels',
          sum(len(r) for r in fit_rings))

    for name, rings, cyc in [('TEST_cyclic', test_rings, True),
                             ('TEST_linear', test_rings, False),
                             ('FIT_cyclic', fit_rings, True)]:
        r = run_z1(rings, cyclic=cyc)
        m1, m3 = mean_sims(rings, cyclic=cyc)
        r['mean_sim_g1'] = m1; r['mean_sim_g3plus'] = m3
        res[name] = r
        print(name, json.dumps(r, indent=1))

    # raw character level
    vrc = voynich_rings(level='chars')
    test_c = [r for s in ml.TEST_SIGNS for r in vrc.get(s, [])]
    r = run_z1(test_c, cyclic=True)
    res['TEST_chars_cyclic'] = r
    print('TEST_chars_cyclic', json.dumps(r, indent=1))

    # comma_split=False
    vrf = voynich_rings(comma_split=False)
    test_f = [r for s in ml.TEST_SIGNS for r in vrf.get(s, [])]
    r = run_z1(test_f, cyclic=True)
    res['TEST_commaFalse'] = r
    print('TEST_commaFalse', json.dumps(r, indent=1))

    # numeral controls at matched ring sizes
    ctrl = OrderedDict()
    for nm, series in ml.numeral_controls().items():
        rings = control_rings(series, sizes, mode='cyclic')
        rr = run_z1(rings, cyclic=True)
        m1, m3 = mean_sims(rings, cyclic=True)
        rr['mean_sim_g1'] = m1; rr['mean_sim_g3plus'] = m3
        ctrl[nm] = rr
        print('CTRL', nm, 'delta=%.5f p=%.4f rho=%.4f p=%.4f g1=%.4f g3=%.4f' %
              (rr['delta'], rr['p_delta_add1'], rr['rho_bar'], rr['p_rho_add1'], m1, m3))
    res['numeral_controls'] = ctrl
    ds = sorted(v['delta'] for v in ctrl.values())
    med = (ds[len(ds)//2 - 1] + ds[len(ds)//2]) / 2.0 if len(ds) % 2 == 0 else ds[len(ds)//2]
    res['numeral_median_delta'] = med
    res['gate_ii_fraction'] = res['TEST_cyclic']['delta'] / med
    npow_both = sum(1 for v in ctrl.values()
                    if v['p_delta_add1'] < 0.01 and v['p_rho_add1'] < 0.01
                    and v['delta'] > 0 and v['rho_bar'] < 0)
    npow_delta = sum(1 for v in ctrl.values() if v['p_delta_add1'] < 0.01 and v['delta'] > 0)
    res['power_both'] = npow_both / 8.0
    res['power_delta'] = npow_delta / 8.0
    print('numeral median delta = %.5f ; TEST delta / median = %.4f' %
          (med, res['gate_ii_fraction']))
    print('power both = %.2f  power delta = %.2f' % (res['power_both'], res['power_delta']))

    open(r"R:/Coding/LinearA/tmp/voynich_repo/experiments/meaning-probes/v_z1_reimpl_a.json",
         'w').write(json.dumps(res, indent=1))

main()
