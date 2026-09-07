#!/usr/bin/env python3
"""v_l1_null-correctness_b.py -- is L1's permutation null the RIGHT null?

t_l1.py permutes the label/text tag over individual WORDS inside each
(page x glyph-unit-length) stratum. That null assumes words are exchangeable
within a stratum. But the two registers have very different granularity:

  * a label word comes from a label locus of typically 1-2 words;
  * a text word comes from a line/paragraph locus of ~10 words, and Voynich
    running text has strong local repetition (adjacent and near-adjacent words
    are correlated).

If words are clustered inside loci, the word-level permutation null is TOO
NARROW: it destroys the clustering as well as the register tag, so it
understates the sampling variance of the pooled log-odds and the p-values are
anticonservative.

PLACEBO NULL (register-swap): keep the real page structure, but build BOTH
groups out of running text. On each page, carve out as many contiguous runs of
text words as the page has label loci, with the same run lengths, each run from
a different text locus where possible. Those runs play "label"; the remaining
text words play "text". Then run the identical pipeline (length matching within
page, corrected Mantel-Haenszel pooled log-odds). Under this placebo there is
no register difference at all, so the spread of the resulting log-odds is the
honest null spread of the statistic -- with clustering left intact.

Compared against:
  (a) the word-level permutation null used by t_l1.py (same 25 units), and
  (b) a SCATTERED placebo, where the pseudo-label words are drawn as isolated
      words rather than runs -- this should agree with (a) and so isolates
      clustering as the cause of any difference.

Reports, per unit: SD under each null, and a placebo-calibrated two-sided p for
the observed log-odds. Then re-reads gate leg 1 under the placebo-calibrated p.
"""
import io, json, math, os, random, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

SEED = 408
K = 25
KAPPA = 1.0
REPO = 'R:/Coding/LinearA/tmp/voynich_repo'
ZL = REPO + '/data/corpora/ZL3b-n.txt'
OUT = REPO + '/experiments/meaning-probes/results'

LOG = []
def say(s=''):
    print(s); LOG.append(str(s))


# --------------------------------------------------------------- segment ----
class Seg(object):
    """word -> (n_units, final_unit_index, initial_unit_index) with caching."""
    def __init__(self, units_final, units_initial):
        self.fi = {u: i for i, u in enumerate(units_final)}
        self.ii = {u: i for i, u in enumerate(units_initial)}
        self.cache = {}

    def get(self, w):
        v = self.cache.get(w)
        if v is None:
            u = ML.bpe_apply(w)
            if not u:
                v = None
            else:
                v = (len(u), self.fi.get(u[-1], -1), self.ii.get(u[0], -1))
            self.cache[w] = v
        return v


def topk(words, pos, k=K):
    c = Counter()
    for w in words:
        u = ML.bpe_apply(w)
        if u:
            c[u[-1] if pos == 'final' else u[0]] += 1
    return [x for x, _ in c.most_common(k)]


# ---------------------------------------------------------------- strata ----
def strata_from_groups(groups, seg, which):
    """groups: [(pid, label_words, text_words)]. which: 1 final, 2 initial."""
    out = []
    for pid, lab, txt in groups:
        bl, bt = {}, {}
        for w in lab:
            v = seg.get(w)
            if v:
                bl.setdefault(v[0], []).append(v[which])
        for w in txt:
            v = seg.get(w)
            if v:
                bt.setdefault(v[0], []).append(v[which])
        for L, labs in sorted(bl.items()):
            txts = bt.get(L)
            if not txts:
                continue
            pool = labs + txts
            n, m1 = len(pool), len(labs)
            if m1 <= 0 or m1 >= n:
                continue
            out.append((n, m1, pool))
    return out


def logors(strata):
    """Corrected MH pooled log-OR per unit, straight from the strata (first m1
    entries of each pool are the label words). Cell by cell, no shortcuts."""
    R = [0.0] * K
    S = [0.0] * K
    for (n, m1, pool) in strata:
        tc = Counter(x for x in pool if x >= 0)
        ac = Counter(x for x in pool[:m1] if x >= 0)
        m0 = n - m1
        p1 = KAPPA * m1 / float(n)
        p0 = KAPPA * m0 / float(n)
        N = n + 2.0 * KAPPA
        for u, t in tc.items():
            if t == n:
                continue
            A = ac.get(u, 0)
            R[u] += (A + p1) * (m0 - t + A + p0) / N
            S[u] += (m1 - A + p1) * (t - A + p0) / N
    return [math.log(R[u] / S[u]) if (R[u] > 0 and S[u] > 0) else 0.0
            for u in range(K)]


def perm_null(strata, nperm, seed=SEED):
    """t_l1.py's null: reshuffle the label/text tag over WORDS inside each
    stratum."""
    rnd = random.Random(seed)
    draws = []
    for _ in range(nperm):
        st = []
        for (n, m1, pool) in strata:
            s = rnd.sample(pool, m1)
            rest = list(pool)
            # rebuild a pool whose first m1 entries are the sampled 'labels'
            c = Counter(s)
            other = []
            for x in rest:
                if c[x] > 0:
                    c[x] -= 1
                else:
                    other.append(x)
            st.append((n, m1, s + other))
        draws.append(logors(st))
    return draws


# ------------------------------------------------------------- placebo ------
def page_loci(pages, parity):
    """page -> (list of label-locus lengths, list of text loci as word lists)"""
    out = []
    for pid, p in pages.items():
        if p['fnum'] % 2 != parity:
            continue
        lab_lens, txt_loci = [], []
        nlab = 0
        for l in p['loci']:
            if l['type'] == 'L' and l['words']:
                lab_lens.append(len(l['words']))
                nlab += len(l['words'])
            elif l['type'] in ('P', 'C', 'R') and l['words']:
                txt_loci.append(list(l['words']))
        if lab_lens and txt_loci:
            out.append((pid, lab_lens, txt_loci))
    return out


def placebo_groups(pl, rnd, contiguous=True):
    """Carve pseudo-label runs out of running text, one run per real label
    locus, same run lengths, each run from a different text locus where the
    page has enough loci. Remaining text words are the pseudo-text."""
    groups = []
    for pid, lab_lens, txt_loci in pl:
        used = [set() for _ in txt_loci]
        order = list(range(len(txt_loci)))
        rnd.shuffle(order)
        plab = []
        oi = 0
        for j in lab_lens:
            placed = False
            for attempt in range(len(txt_loci) * 3):
                li = order[oi % len(order)]
                oi += 1
                loc = txt_loci[li]
                if len(loc) - len(used[li]) < j:
                    continue
                if contiguous:
                    starts = [s for s in range(0, len(loc) - j + 1)
                              if all((s + q) not in used[li] for q in range(j))]
                    if not starts:
                        continue
                    s = rnd.choice(starts)
                    idxs = list(range(s, s + j))
                else:
                    free = [q for q in range(len(loc)) if q not in used[li]]
                    if len(free) < j:
                        continue
                    idxs = rnd.sample(free, j)
                for q in idxs:
                    used[li].add(q)
                plab.extend(loc[q] for q in idxs)
                placed = True
                break
            if not placed:
                break
        ptxt = []
        for li, loc in enumerate(txt_loci):
            for q, w in enumerate(loc):
                if q not in used[li]:
                    ptxt.append(w)
        if plab and ptxt:
            groups.append((pid, plab, ptxt))
    return groups


def sd(xs):
    n = len(xs)
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) if n > 1 else 0.0


def main():
    NPLA = int(os.environ.get('NPLA', '2000'))
    NPERM = int(os.environ.get('NPERM', '2000'))

    pages = ML.parse_pages(ZL, comma_split=True)
    lt = ML.label_text_by_page(pages)
    words_all = ML.all_words(pages)
    uf = topk(words_all, 'final')
    ui = topk(words_all, 'initial')
    seg = Seg(uf, ui)

    say('=' * 78)
    say('v_l1 null-correctness B: word-permutation null vs register-swap placebo')
    say('=' * 78)
    say('placebo draws=%d   word-permutation draws=%d   seed=%d'
        % (NPLA, NPERM, SEED))

    res = OrderedDict()
    for parity, tag in ((1, 'TEST_odd'), (0, 'FIT_even')):
        groups = [(pid, d['labels'], d['text']) for pid, d in lt.items()
                  if pages[pid]['fnum'] % 2 == parity]
        pl = page_loci(pages, parity)
        say('')
        say('###### %s : %d pages with both registers (%d in placebo pool)'
            % (tag, len(groups), len(pl)))
        nlab_loci = sum(len(x[1]) for x in pl)
        say('       label loci=%d, mean label-locus length=%.2f words'
            % (nlab_loci,
               sum(sum(x[1]) for x in pl) / float(nlab_loci)))
        say('       text loci=%d, mean text-locus length=%.2f words'
            % (sum(len(x[2]) for x in pl),
               sum(sum(len(t) for t in x[2]) for x in pl)
               / float(sum(len(x[2]) for x in pl))))

        for which, pos, units in ((1, 'final', uf), (2, 'initial', ui)):
            st_obs = strata_from_groups(groups, seg, which)
            obs = logors(st_obs)

            pdraws = perm_null(st_obs, NPERM)
            rndA = random.Random(SEED)
            cdraws, sdraws = [], []
            nfail = 0
            for _ in range(NPLA):
                g = placebo_groups(pl, rndA, contiguous=True)
                s = strata_from_groups(g, seg, which)
                if not s:
                    nfail += 1
                    continue
                cdraws.append(logors(s))
            rndB = random.Random(SEED + 1)
            for _ in range(NPLA):
                g = placebo_groups(pl, rndB, contiguous=False)
                s = strata_from_groups(g, seg, which)
                if s:
                    sdraws.append(logors(s))

            say('')
            say('--- %s %s  (%d strata, %d label / %d text words)'
                % (tag, pos, len(st_obs),
                   sum(m1 for (n, m1, p_) in st_obs),
                   sum(n - m1 for (n, m1, p_) in st_obs)))
            say('    %-8s %9s | %8s %8s | %8s %8s | %9s %9s'
                % ('unit', 'log-odds', 'mu_perm', 'mu_clus', 'sd_perm',
                   'sd_clus', 'p_perm', 'p_placebo'))
            rows = []
            for u in sorted(range(K), key=lambda i: obs[i]):
                xs_p = [d[u] for d in pdraws]
                xs_c = [d[u] for d in cdraws]
                xs_s = [d[u] for d in sdraws]
                sp, sc, ss = sd(xs_p), sd(xs_c), sd(xs_s)
                a = abs(obs[u])
                pp = (sum(1 for x in xs_p if abs(x) >= a - 1e-12) + 1.0) / (len(xs_p) + 1.0)
                pc = (sum(1 for x in xs_c if abs(x) >= a - 1e-12) + 1.0) / (len(xs_c) + 1.0)
                ps = (sum(1 for x in xs_s if abs(x) >= a - 1e-12) + 1.0) / (len(xs_s) + 1.0)
                mup = sum(xs_p) / len(xs_p)
                muc = sum(xs_c) / len(xs_c)
                say('    %-8s %9.4f | %8.4f %8.4f | %8.4f %8.4f | %9.5f %9.5f'
                    % (units[u], obs[u], mup, muc, sp, sc, pp, pc))
                rows.append(OrderedDict([
                    ('unit', units[u]), ('log_odds', round(obs[u], 4)),
                    ('mean_word_perm', round(mup, 4)),
                    ('mean_cluster_placebo', round(muc, 4)),
                    ('sd_word_perm', round(sp, 4)),
                    ('sd_scatter_placebo', round(ss, 4)),
                    ('sd_cluster_placebo', round(sc, 4)),
                    ('p_word_perm', round(pp, 6)),
                    ('p_scatter_placebo', round(ps, 6)),
                    ('p_cluster_placebo', round(pc, 6)),
                    ('bonf_p_word_perm', round(min(1, pp * K), 6)),
                    ('bonf_p_cluster_placebo', round(min(1, pc * K), 6)),
                    ('passes_perm', bool(a >= 1.0 and pp * K < 0.01)),
                    ('passes_placebo', bool(a >= 1.0 and pc * K < 0.01)),
                ]))
            infl = [r['sd_cluster_placebo'] / r['sd_word_perm']
                    for r in rows if r['sd_word_perm'] > 1e-9]
            infl.sort()
            say('    variance inflation sd_cluster/sd_perm: median %.3f  '
                'min %.3f  max %.3f'
                % (infl[len(infl) // 2], infl[0], infl[-1]))
            npass_p = sum(1 for r in rows if r['passes_perm'])
            npass_c = sum(1 for r in rows if r['passes_placebo'])
            say('    gate leg 1 units: word-permutation null = %d ; '
                'cluster-placebo null = %d   (need >= 3)' % (npass_p, npass_c))
            # false positives generated by the procedure itself
            fp = [sum(1 for u in range(K) if abs(d[u]) >= 1.0) for d in cdraws]
            fp.sort()
            say('    units with |log-odds| >= 1 in a typical PLACEBO draw: '
                'median %d, 95th pct %d, max %d'
                % (fp[len(fp) // 2], fp[int(0.95 * len(fp))], fp[-1]))
            pool_c = [sum(abs(x) for x in d) / K for d in cdraws]
            pool_c.sort()
            say('    placebo pooled mean|log-odds|: median %.4f  95th pct %.4f'
                '   (observed %.4f)'
                % (pool_c[len(pool_c) // 2], pool_c[int(0.95 * len(pool_c))],
                   sum(abs(x) for x in obs) / K))
            res['%s_%s' % (tag, pos)] = OrderedDict([
                ('n_strata', len(st_obs)), ('rows', rows),
                ('median_variance_inflation', round(infl[len(infl) // 2], 4)),
                ('n_pass_word_perm', npass_p),
                ('n_pass_cluster_placebo', npass_c),
                ('placebo_median_units_ge1', fp[len(fp) // 2]),
                ('placebo_p95_units_ge1', fp[int(0.95 * len(fp))]),
                ('observed_pooled', round(sum(abs(x) for x in obs) / K, 4)),
                ('placebo_median_pooled', round(pool_c[len(pool_c) // 2], 4)),
                ('placebo_p95_pooled', round(pool_c[int(0.95 * len(pool_c))], 4)),
            ])

    with io.open(os.path.join(OUT, 'v_l1_null-correctness_b.json'), 'w',
                 encoding='utf-8') as fh:
        fh.write(json.dumps(res, indent=1, ensure_ascii=False))
    with io.open(os.path.join(OUT, 'v_l1_null-correctness_b.stdout.txt'), 'w',
                 encoding='utf-8') as fh:
        fh.write('\n'.join(LOG) + '\n')


if __name__ == '__main__':
    main()
