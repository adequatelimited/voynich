#!/usr/bin/env python3
"""v_l1_null-correctness_a.py -- adversarial re-derivation of L1.

Independent implementation: strata built from meaning_lib, MH pooled log-OR
brute-forced cell by cell (no algebraic decomposition), permutation null
written from scratch.

Checks:
  1. reproduce the observed per-unit log-odds in results/l1.json
  2. reproduce p_perm for a few units
  3. NULL FLOOR of the leg-2 pooled statistic (mean |log-odds| over K=25):
     what does the permutation null itself produce for that number, in each
     corpus?  Leg 2 compares Voynich TEST (466 label / 3098 text words) with
     Culpeper (1359 / 56938).  mean|.| is upward-biased by estimation noise,
     and the two families have very different precision.
"""
import io, json, math, os, random, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

SEED = 408
K = 25
KAPPA = 1.0
REPO = 'R:/Coding/LinearA/tmp/voynich_repo'
LAB = 'R:/Coding/LinearA/tmp/voynich_lab'
ZL = REPO + '/data/corpora/ZL3b-n.txt'
CULP = LAB + '/pg49513.txt'
OUT = REPO + '/experiments/meaning-probes/results'

LOG = []
def say(s=''):
    print(s); LOG.append(str(s))


# ---------------------------------------------------------------- building --
def topk(words, seg, pos, k=K):
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
            txts = bt.get(L)
            if not txts:
                continue
            pool = list(labs) + list(txts)
            n, m1 = len(pool), len(labs)
            if m1 <= 0 or m1 >= n:
                continue
            out.append((n, m1, pool))
    return out


# ------------------------------------------------------------- estimator ----
def mh_logor_bruteforce(strata, counts, u):
    """Corrected MH log-OR for unit u, cell by cell. counts[i] = Counter of the
    label sample in stratum i.  Uninformative strata (t=0 or t=n) skipped, as in
    t_l1.py."""
    R = S = 0.0
    for (n, m1, pool), cnt in zip(strata, counts):
        t = sum(1 for x in pool if x == u)
        if t == 0 or t == n:
            continue
        m0 = n - m1
        p1 = KAPPA * m1 / float(n)
        p0 = KAPPA * m0 / float(n)
        N = n + 2.0 * KAPPA
        A = cnt.get(u, 0)
        a = A + p1
        b = m1 - A + p1
        c = t - A + p0
        d = m0 - t + A + p0
        R += a * d / N
        S += b * c / N
    if R > 0 and S > 0:
        return math.log(R / S)
    return 0.0


def observed_counts(strata):
    return [Counter(pool[:m1]) for (n, m1, pool) in strata]


def precompute(strata):
    """Per unit: list of (index, n, m1, t) for informative strata only."""
    info = {}
    for i, (n, m1, pool) in enumerate(strata):
        tc = Counter(x for x in pool if x >= 0)
        for u, t in tc.items():
            if t == n:
                continue
            info.setdefault(u, []).append((i, n, m1, t))
    return info


def logors_fast(strata, info, counts):
    """Same corrected MH log-OR, computed from a per-unit index. Independent of
    t_l1.py's decomposition; validated against mh_logor_bruteforce below."""
    out = [0.0] * K
    for u in range(K):
        R = S = 0.0
        for (i, n, m1, t) in info.get(u, []):
            m0 = n - m1
            p1 = KAPPA * m1 / float(n)
            p0 = KAPPA * m0 / float(n)
            N = n + 2.0 * KAPPA
            A = counts[i].get(u, 0)
            R += (A + p1) * (m0 - t + A + p0) / N
            S += (m1 - A + p1) * (t - A + p0) / N
        out[u] = math.log(R / S) if (R > 0 and S > 0) else 0.0
    return out


def run(name, strata, units, nperm, seed=SEED, want_p=True):
    info = precompute(strata)
    cnts = observed_counts(strata)
    obs = logors_fast(strata, info, cnts)
    # validate the fast path against a literal cell-by-cell brute force
    for u in range(K):
        bf = mh_logor_bruteforce(strata, cnts, u)
        assert abs(bf - obs[u]) < 1e-9, (name, u, bf, obs[u])
    pooled_obs = sum(abs(x) for x in obs) / K
    rnd = random.Random(seed)
    ge = [0] * K
    pooled_null = []
    aobs = [abs(x) for x in obs]
    for _ in range(nperm):
        cs = [Counter(rnd.sample(pool, m1)) for (n, m1, pool) in strata]
        lo = logors_fast(strata, info, cs)
        pooled_null.append(sum(abs(x) for x in lo) / K)
        if want_p:
            for u in range(K):
                if abs(lo[u]) >= aobs[u] - 1e-12:
                    ge[u] += 1
    p = [(g + 1.0) / (nperm + 1.0) for g in ge]
    mu = sum(pooled_null) / len(pooled_null)
    sd = math.sqrt(sum((x - mu) ** 2 for x in pooled_null) / (len(pooled_null) - 1))
    pooled_null.sort()
    q = lambda f: pooled_null[min(len(pooled_null) - 1, int(f * len(pooled_null)))]
    return OrderedDict([
        ('name', name), ('units', units), ('logodds', obs), ('p_perm', p),
        ('pooled_obs', pooled_obs), ('pooled_null_mean', mu),
        ('pooled_null_sd', sd), ('pooled_null_q025', q(0.025)),
        ('pooled_null_q975', q(0.975)), ('nperm', nperm),
        ('n_label', sum(m1 for (n, m1, p_) in strata)),
        ('n_text', sum(n - m1 for (n, m1, p_) in strata)),
        ('n_strata', len(strata)),
    ])


def main():
    nperm_v = int(os.environ.get('NPV', '10000'))
    nperm_c = int(os.environ.get('NPC', '2000'))

    say('=' * 78)
    say('v_l1 null-correctness: independent re-derivation + leg-2 null floor')
    say('=' * 78)

    # ------------------------------------------------------------ Voynich --
    pages = ML.parse_pages(ZL, comma_split=True)
    lt = ML.label_text_by_page(pages)
    words_all = ML.all_words(pages)
    g_odd = [(pid, d['labels'], d['text']) for pid, d in lt.items()
             if pages[pid]['fnum'] % 2 == 1]
    g_even = [(pid, d['labels'], d['text']) for pid, d in lt.items()
              if pages[pid]['fnum'] % 2 == 0]
    say('pages odd=%d even=%d' % (len(g_odd), len(g_even)))

    res = OrderedDict()
    for pos in ('final', 'initial'):
        un = topk(words_all, ML.bpe_apply, pos)
        st = strata_of(g_odd, un, ML.bpe_apply, pos)
        r = run('ZL3b_test_odd_' + pos, st, un, nperm_v)
        res['voy_' + pos] = r
        say('')
        say('--- ZL3b TEST odd, %s : %d strata, %d label / %d text words'
            % (pos, r['n_strata'], r['n_label'], r['n_text']))
        for u in sorted(range(K), key=lambda i: r['logodds'][i]):
            say('    %-8s logodds=%8.4f  p_perm=%.5f  bonf=%.5f' %
                (un[u], r['logodds'][u], r['p_perm'][u], min(1, r['p_perm'][u] * K)))
        say('    pooled mean|logodds| OBS = %.4f' % r['pooled_obs'])
        say('    pooled mean|logodds| NULL mean = %.4f  sd=%.4f  95%% [%.4f, %.4f]'
            % (r['pooled_null_mean'], r['pooled_null_sd'],
               r['pooled_null_q025'], r['pooled_null_q975']))
        say('    excess over null floor = %.4f' %
            (r['pooled_obs'] - r['pooled_null_mean']))

    # ----------------------------------------------------------- Culpeper --
    ent = ML.culpeper_entries(CULP)
    cg, callw = [], []
    for i, head, body in ent:
        hw = ML.words_en(head)
        if not hw or not body:
            continue
        cg.append(('e%d' % i, hw, body))
        callw.extend(hw); callw.extend(body)
    say('')
    say('Culpeper entries=%d words=%d' % (len(cg), len(callw)))
    seg_char = lambda w: list(w)
    for pos in ('final', 'initial'):
        un = topk(callw, seg_char, pos)
        st = strata_of(cg, un, seg_char, pos)
        r = run('culpeper_' + pos, st, un, nperm_c, want_p=False)
        res['culp_' + pos] = r
        say('')
        say('--- Culpeper %s : %d strata, %d head / %d body words'
            % (pos, r['n_strata'], r['n_label'], r['n_text']))
        say('    pooled mean|logodds| OBS = %.4f' % r['pooled_obs'])
        say('    pooled mean|logodds| NULL mean = %.4f  sd=%.4f  95%% [%.4f, %.4f]'
            % (r['pooled_null_mean'], r['pooled_null_sd'],
               r['pooled_null_q025'], r['pooled_null_q975']))
        say('    excess over null floor = %.4f' %
            (r['pooled_obs'] - r['pooled_null_mean']))

    # -------------------------------------------------------------- leg 2 --
    say('')
    say('=' * 78)
    say('LEG 2 RECOMPUTED')
    say('=' * 78)
    for pos in ('final', 'initial'):
        v, c = res['voy_' + pos], res['culp_' + pos]
        raw = v['pooled_obs'] / c['pooled_obs']
        ev = v['pooled_obs'] - v['pooled_null_mean']
        ec = c['pooled_obs'] - c['pooled_null_mean']
        say('  %s : raw ratio = %.4f' % (pos, raw))
        say('     null floors: voynich %.4f  culpeper %.4f'
            % (v['pooled_null_mean'], c['pooled_null_mean']))
        say('     null-corrected ratio (excess/excess) = %.4f / %.4f = %s'
            % (ev, ec, ('%.4f' % (ev / ec)) if ec > 0 else 'n/a'))
        say('     -> leg 2 (>=0.25) raw %s ; null-corrected %s'
            % ('PASS' if raw >= 0.25 else 'FAIL',
               'PASS' if (ec > 0 and ev / ec >= 0.25) else 'FAIL'))

    with io.open(os.path.join(OUT, 'v_l1_null-correctness_a.json'), 'w',
                 encoding='utf-8') as fh:
        fh.write(json.dumps(res, indent=1, ensure_ascii=False))
    with io.open(os.path.join(OUT, 'v_l1_null-correctness_a.stdout.txt'), 'w',
                 encoding='utf-8') as fh:
        fh.write('\n'.join(LOG) + '\n')


if __name__ == '__main__':
    main()
