#!/usr/bin/env python3
"""v_l1_reimplementation_b.py — verifier, lens = reimplementation (part 2).

Naive (loop-over-strata, no algebraic expansion) recomputation of the TEST's
SECONDARY estimator: the marginal continuity-corrected MH log-OR described in
the comment block of t_l1.py (kappa = 1, add kappa*m1/n to both label cells and
kappa*m0/n to both text cells, on informative strata only, N' = n + 2*kappa).

Purpose: t_l1.py computes this through a quadratic coefficient expansion; an
error there would be invisible in its own output. This recomputes the observed
values the slow, obvious way and diffs them, and re-runs the permutation null
for the corrected statistic on the manuscript TEST word-final family so the
two headline passers ('daiin', 'n') can be checked.

Also recomputes the pooled-effect summaries under both estimators.
Stdlib only. Seed 408.
"""
import json, math, random, sys, os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

REPO = "R:/Coding/LinearA/tmp/voynich_repo"
LAB = "R:/Coding/LinearA/tmp/voynich_lab"
ZL = REPO + "/data/corpora/ZL3b-n.txt"
CULP = LAB + "/pg49513.txt"
OUT = REPO + "/experiments/meaning-probes/results"
SEED, NPERM, K, KAPPA = 408, 10000, 25, 1.0


def top_k(words, seg, pos, k=K):
    c = Counter()
    for w in words:
        u = seg(w)
        if u:
            c[u[-1] if pos == 'final' else u[0]] += 1
    return [x for x, _ in c.most_common(k)]


def strata_of(groups, units, seg, pos):
    idx = {u: i for i, u in enumerate(units)}
    out = []
    for gid, lab, txt in groups:
        bl, bt = {}, {}
        for w in lab:
            u = seg(w)
            if u:
                bl.setdefault(len(u), []).append(idx.get(u[-1] if pos == 'final' else u[0], -1))
        for w in txt:
            u = seg(w)
            if u:
                bt.setdefault(len(u), []).append(idx.get(u[-1] if pos == 'final' else u[0], -1))
        for L, labs in sorted(bl.items()):
            tx = bt.get(L)
            if not tx:
                continue
            pool = list(labs) + list(tx)
            out.append((len(pool), len(labs), pool))
    return [s for s in out if 0 < s[1] < s[0]]


def logor_naive(strata, ku, assign, corrected):
    """assign: list per stratum of the multiset of unit codes assigned to the
    LABEL row (a list of length m1). Returns pooled log-OR or +-inf/None."""
    num = den = 0.0
    for (n, m1, pool), lab_codes in zip(strata, assign):
        t = sum(1 for x in pool if x == ku)
        if t == 0 or t == n:
            continue
        m0 = n - m1
        a = sum(1 for x in lab_codes if x == ku)
        b = m1 - a
        c = t - a
        d = m0 - c
        if corrected:
            p1 = KAPPA * m1 / float(n)
            p0 = KAPPA * m0 / float(n)
            N2 = n + 2.0 * KAPPA
            num += (a + p1) * (d + p0) / N2
            den += (b + p1) * (c + p0) / N2
        else:
            num += a * d / float(n)
            den += b * c / float(n)
    if num > 0 and den > 0:
        return math.log(num / den)
    if num <= 0 and den <= 0:
        return 0.0
    return float('-inf') if num <= 0 else float('inf')


def run(strata, units, nperm=NPERM, seed=SEED, corrected=True):
    obs_assign = [pool[:m1] for (n, m1, pool) in strata]
    obs = [logor_naive(strata, ku, obs_assign, corrected) for ku in range(len(units))]
    obs_abs = [abs(x) for x in obs]
    ge = [0] * len(units)
    rng = random.Random(seed)
    for _ in range(nperm):
        assign = []
        for (n, m1, pool) in strata:
            assign.append([pool[i] for i in rng.sample(range(n), m1)])
        for ku in range(len(units)):
            if abs(logor_naive(strata, ku, assign, corrected)) >= obs_abs[ku]:
                ge[ku] += 1
    return obs, [min(1.0, (g + 1) / (nperm + 1.0) * len(units)) for g in ge]


def main():
    rep = {'verifier': 'v_l1_reimplementation_b'}
    L = []
    P = lambda s='': (L.append(s), print(s))

    t = json.load(open(OUT + '/l1.json', encoding='utf-8'))

    # ---------------- observed corrected values, naive, all four families ----
    pages = ML.parse_pages(ZL, comma_split=True)
    lt = ML.label_text_by_page(pages)
    allw = ML.all_words(pages)
    g_test = [(pid, d['labels'], d['text']) for pid, d in lt.items()
              if pages[pid]['fnum'] % 2 == 1]
    ents = ML.culpeper_entries(CULP)
    cg, callw = [], []
    for i, h, b in ents:
        hw = ML.words_en(h)
        if hw and b:
            cg.append(('e%d' % i, hw, b)); callw.extend(hw); callw.extend(b)

    seg_g = lambda w: ML.bpe_apply(w)
    seg_c = lambda w: list(w)

    jobs = [
        ('TEST word-final', g_test, allw, seg_g, 'final',
         t['primary_ZL3b']['test_odd']['final']['units']),
        ('TEST word-initial', g_test, allw, seg_g, 'initial',
         t['primary_ZL3b']['test_odd']['initial']['units']),
        ('Culpeper char-final', cg, callw, seg_c, 'final',
         t['culpeper_control']['final']['units']),
        ('Culpeper char-initial', cg, callw, seg_c, 'initial',
         t['culpeper_control']['initial']['units']),
    ]
    rep['observed_corrected_diff'] = {}
    for name, groups, aw, seg, pos, trows in jobs:
        units = top_k(aw, seg, pos)
        S = strata_of(groups, units, seg, pos)
        obs_assign = [pool[:m1] for (n, m1, pool) in S]
        mine = {units[ku]: logor_naive(S, ku, obs_assign, True) for ku in range(len(units))}
        mine_u = {units[ku]: logor_naive(S, ku, obs_assign, False) for ku in range(len(units))}
        theirs = {r['unit']: r['log_odds'] for r in trows}
        worst, bad = 0.0, []
        for u, v in mine.items():
            if u not in theirs:
                bad.append((u, 'missing')); continue
            d = abs(v - theirs[u])
            worst = max(worst, d)
            if d > 5e-4:
                bad.append((u, v, theirs[u]))
        P('%-22s naive-corrected vs t_l1 log_odds: max abs diff %.6f ; K-list identical: %s'
          % (name, worst, set(mine) == set(theirs)))
        if bad:
            P('    MISMATCH: %s' % bad[:8])
        # pooled summaries, both estimators
        fin = [abs(v) for v in mine.values()]
        finu = [abs(v) for v in mine_u.values() if math.isfinite(v)]
        P('    pooled mean|logOR| corrected %.4f (t_l1 %s) ; uncorrected over %d finite units %.4f (t_l1 %s)'
          % (sum(fin) / len(fin),
             {'TEST word-final': t['primary_ZL3b']['test_odd']['final'],
              'TEST word-initial': t['primary_ZL3b']['test_odd']['initial'],
              'Culpeper char-final': t['culpeper_control']['final'],
              'Culpeper char-initial': t['culpeper_control']['initial']}[name]['pooled_effect_mean_abs_logodds'],
             len(finu), sum(finu) / len(finu),
             {'TEST word-final': t['primary_ZL3b']['test_odd']['final'],
              'TEST word-initial': t['primary_ZL3b']['test_odd']['initial'],
              'Culpeper char-final': t['culpeper_control']['final'],
              'Culpeper char-initial': t['culpeper_control']['initial']}[name]['pooled_effect_mean_abs_logodds_uncorrected']))
        # who passes leg 1 under each estimator, using t_l1's own p-values
        pc = {r['unit']: r['p_bonferroni'] for r in trows}
        pu = {r['unit']: min(1.0, r['p_perm_uncorrected'] * 25) for r in trows}
        passc = [u for u in mine if abs(mine[u]) >= 1 and pc.get(u, 1) < 0.01]
        passu = [u for u in mine_u if math.isfinite(mine_u[u]) and abs(mine_u[u]) >= 1 and pu.get(u, 1) < 0.01]
        P('    leg-1 passers  corrected: %s (%d)   uncorrected: %s (%d)'
          % (sorted(passc), len(passc), sorted(passu), len(passu)))
        rep['observed_corrected_diff'][name] = {
            'max_abs_diff_vs_t_l1': worst,
            'pass_corrected': sorted(passc), 'pass_uncorrected': sorted(passu)}

    # -------- permutation re-run of the CORRECTED statistic, TEST final -----
    P()
    units = top_k(allw, seg_g, 'final')
    S = strata_of(g_test, units, seg_g, 'final')
    obs, pb = run(S, units, corrected=True)
    P('independent permutation of the CORRECTED statistic, TEST word-final:')
    trow = {r['unit']: r for r in t['primary_ZL3b']['test_odd']['final']['units']}
    npass = 0
    for ku, u in enumerate(units):
        if abs(obs[ku]) >= 1 or trow[u]['passes_unit_test']:
            ok = abs(obs[ku]) >= 1 and pb[ku] < 0.01
            npass += 1 if ok else 0
            P('   %-8s logOR %+7.3f (t_l1 %+7.3f)  Bonf p %.4f (t_l1 %.4f)  pass=%s (t_l1 %s)'
              % (u, obs[ku], trow[u]['log_odds'], pb[ku], trow[u]['p_bonferroni'],
                 ok, trow[u]['passes_unit_test']))
    P('   units passing under corrected estimator: %d (t_l1 reports %d)'
      % (npass, t['gate']['final_units_passing_TEST']))
    rep['corrected_perm_TEST_final_npass'] = npass

    json.dump(rep, open(OUT + '/v_l1_reimpl_b.json', 'w', encoding='utf-8'), indent=1)
    open(OUT + '/v_l1_reimpl_b.stdout.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
