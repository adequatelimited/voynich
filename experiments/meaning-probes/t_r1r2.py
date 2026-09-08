#!/usr/bin/env python3
"""t_r1r2.py — R1 (paragraph opener: word or ornament?) and R2 (do the stars
index the text?), exactly as pre-registered in PROTOCOL.md (this directory).

Stdlib only. Deterministic: every RNG seeded with meaning_lib.SEED = 408.
Data access is meaning_lib only; every statistic below is written here.

Ambiguity policy (the protocol's instruction): where the pre-registration admits
more than one reading, the reading that makes the test HARDER to pass is used
for the gate, and both readings are reported. Each such choice is recorded in
results['ambiguities'].
"""
import io, json, math, os, random, re, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results')
ZL = os.path.abspath(os.path.join(HERE, '..', '..', 'data', 'corpora', 'ZL3b-n.txt'))
GC = os.path.abspath(os.path.join(HERE, '..', '..', 'data', 'corpora', 'GC2a-n.txt'))
NDRAW = 10000
SEED = ML.SEED

_out_lines = []


def say(*a):
    s = ' '.join(str(x) for x in a)
    _out_lines.append(s)
    print(s)


# ------------------------------------------------------------------ helpers --

def fnum(pid):
    return int(re.match(r'f(\d+)', pid).group(1))


def gallows_prefix(w):
    """Leading gallows of an EVA word, benched forms (cth ckh cph cfh) checked
    BEFORE the single letters t p k f. ML.GALLOWS is already in that order."""
    for g in ML.GALLOWS:
        if w.startswith(g):
            return g
    return None


def strip_gallows(w):
    g = gallows_prefix(w)
    return (g, w[len(g):]) if g else (None, None)


def two_sided_p(obs, null):
    """Two-sided permutation/resample p, centred on the null mean."""
    m = sum(null) / len(null)
    d = abs(obs - m)
    k = sum(1 for x in null if abs(x - m) >= d - 1e-12)
    return (1 + k) / (len(null) + 1)


def one_sided_p_ge(obs, null):
    k = sum(1 for x in null if x >= obs - 1e-12)
    return (1 + k) / (len(null) + 1)


def mean_sd(xs):
    n = len(xs)
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    return m, math.sqrt(v)


def z_units(obs, null):
    m, sd = mean_sd(null)
    return (obs - m) / sd if sd > 0 else float('inf') if obs != m else 0.0


def top_share(words, k):
    c = Counter(words)
    n = sum(c.values())
    if n == 0:
        return 0.0
    return sum(v for _, v in c.most_common(k)) / n


def stats_block(words):
    c = Counter(words)
    return {'n': len(words), 'n_types': len(c),
            'top1_share': top_share(words, 1), 'top5_share': top_share(words, 5),
            'entropy_bits': ML.H(c),
            'top1_type': (c.most_common(1)[0][0] if c else None)}


# ------------------------------------------------------------ corpus slicing --

def stratum(pages, illus, lang=None, fmin=None, fmax=None, parity=None,
            page_ids=None):
    """Page ids of a stratum."""
    ids = []
    for p in pages.values():
        if page_ids is not None:
            if p['id'] in page_ids:
                ids.append(p['id'])
            continue
        if illus is not None and p['meta'].get('I') not in illus:
            continue
        if lang is not None and p['meta'].get('L') != lang:
            continue
        f = p['fnum']
        if fmin is not None and f < fmin:
            continue
        if fmax is not None and f > fmax:
            continue
        if parity == 'odd' and f % 2 != 1:
            continue
        if parity == 'even' and f % 2 != 0:
            continue
        ids.append(p['id'])
    return set(ids)


def para_and_pools(pages, page_ids):
    """Paragraph-initial words, non-paragraph-initial word tokens, all P-locus
    word tokens, and the paragraph-internal line-initial words, for a set of
    pages."""
    pars = ML.paragraphs(pages, page_ids=page_ids)
    pi = [d['first_word'] for d in pars if d['first_word']]
    allw, nonpi = [], []
    for d in pars:
        allw.extend(d['words'])
        nonpi.extend(d['words'][1:])
    nil = ML.non_initial_line_words(pages, page_ids=page_ids)
    return pars, pi, nonpi, allw, nil


# ------------------------------------------------------------------ R1 parts --

def r1_a(pi, nil, allw, rng):
    """(a) Gallows rate of paragraph-initial words vs two controls.
    Null: label permutation over the pooled words (the paragraph-initial set is
    re-drawn at random from the pool); difference of rates, reported in SD units
    of the null."""
    def rate(ws):
        return sum(1 for w in ws if gallows_prefix(w)) / len(ws) if ws else 0.0

    res = {'n_para_initial': len(pi), 'rate_para_initial': rate(pi),
           'n_nonpara_line_initial': len(nil), 'rate_nonpara_line_initial': rate(nil),
           'n_all_words': len(allw), 'rate_all_words': rate(allw),
           'gallows_hist_para_initial': dict(
               Counter(gallows_prefix(w) or '(none)' for w in pi).most_common())}
    n1 = len(pi)
    # control 1: paragraph-internal line-initial words. Disjoint from the
    # openers, so the null is a label permutation over the pooled two sets.
    pool = [1 if gallows_prefix(w) else 0 for w in pi] + \
           [1 if gallows_prefix(w) else 0 for w in nil]
    N, tot = len(pool), sum(1 for w in pi + nil if gallows_prefix(w))
    obs = res['rate_para_initial'] - res['rate_nonpara_line_initial']
    null = []
    for _ in range(NDRAW):
        s = sum(rng.sample(pool, n1))
        null.append(s / n1 - (tot - s) / (N - n1))
    res['vs_line_initial'] = {'diff': obs, 'null_mean': mean_sd(null)[0],
                              'null_sd': mean_sd(null)[1],
                              'sd_units': z_units(obs, null),
                              'p_two_sided': two_sided_p(obs, null),
                              'null_type': 'label permutation over openers+line-initials'}
    # control 2: ALL Recipes words. The openers are a subset of this pool, so
    # the null draws n1 words at random from the section and compares to the
    # section rate (the conservative construction: the section rate keeps the
    # openers in its denominator).
    bits = [1 if gallows_prefix(w) else 0 for w in allw]
    base = sum(bits) / len(bits) if bits else 0.0
    obs2 = res['rate_para_initial'] - base
    null2 = [sum(rng.sample(bits, n1)) / n1 - base for _ in range(NDRAW)]
    res['vs_all_words'] = {'diff': obs2, 'null_mean': mean_sd(null2)[0],
                           'null_sd': mean_sd(null2)[1],
                           'sd_units': z_units(obs2, null2),
                           'p_two_sided': two_sided_p(obs2, null2),
                           'null_type': 'random n-subsample of all section words'}
    return res


def matched_pools(nonpi, vocab):
    """Control pool of gallows-initial words from non-paragraph-initial
    positions, indexed by (gallows character, word length in EVA characters)."""
    cells = {}
    for w in nonpi:
        g, r = strip_gallows(w)
        if g is None:
            continue
        cells.setdefault((g, len(w)), []).append((w, r, 1 if r in vocab else 0))
    return cells


def r1_b_c(pi, nonpi, vocab, rng, label=''):
    """(b) ornament test + (c) lexical-opener test against the SAME matched
    control (matched on the specific gallows character and on word length)."""
    tgt = []
    for w in pi:
        g, r = strip_gallows(w)
        if g is None:
            continue
        tgt.append((w, g, r, 1 if r in vocab else 0))
    cells = matched_pools(nonpi, vocab)
    matchable = [t for t in tgt if (t[1], len(t[0])) in cells]
    unmatched = [t[0] for t in tgt if (t[1], len(t[0])) not in cells]

    res = {'n_para_initial': len(pi),
           'n_para_initial_gallows': len(tgt),
           'n_matchable': len(matchable),
           'n_unmatched_dropped': len(unmatched),
           'unmatched_examples': sorted(set(unmatched))[:20],
           'control_pool_size': sum(len(v) for v in cells.values()),
           'vocab_types': len(vocab)}

    # observed statistics -------------------------------------------------
    res['obs_attest_rate_all_gallows'] = (
        sum(t[3] for t in tgt) / len(tgt)) if tgt else 0.0
    obs_rate = (sum(t[3] for t in matchable) / len(matchable)) if matchable else 0.0
    res['obs_attest_rate_matchable'] = obs_rate
    dropped = [t for t in tgt if (t[1], len(t[0])) not in cells]
    res['obs_attest_rate_dropped_unmatched'] = (
        sum(t[3] for t in dropped) / len(dropped)) if dropped else None
    res['mean_len_matchable'] = (sum(len(t[0]) for t in matchable) / len(matchable)
                                 if matchable else None)
    res['mean_len_dropped'] = (sum(len(t[0]) for t in dropped) / len(dropped)
                               if dropped else None)
    obs_words = [t[0] for t in matchable]
    obs_res = [t[2] for t in matchable]
    res['obs_word_stats'] = stats_block(obs_words)
    res['obs_residue_stats'] = stats_block(obs_res)

    # 10,000 matched resamples -------------------------------------------
    keys = [(t[1], len(t[0])) for t in matchable]
    null_rate, null_w_t1, null_w_t5, null_w_H = [], [], [], []
    null_r_t1, null_r_t5, null_r_H = [], [], []
    for _ in range(NDRAW):
        drawn = [rng.choice(cells[k]) for k in keys]
        n = len(drawn) or 1
        null_rate.append(sum(d[2] for d in drawn) / n)
        ws = [d[0] for d in drawn]
        rs = [d[1] for d in drawn]
        cw, cr = Counter(ws), Counter(rs)
        tw = sum(cw.values()) or 1
        tr = sum(cr.values()) or 1
        null_w_t1.append(sum(v for _, v in cw.most_common(1)) / tw)
        null_w_t5.append(sum(v for _, v in cw.most_common(5)) / tw)
        null_w_H.append(ML.H(cw))
        null_r_t1.append(sum(v for _, v in cr.most_common(1)) / tr)
        null_r_t5.append(sum(v for _, v in cr.most_common(5)) / tr)
        null_r_H.append(ML.H(cr))

    m, sd = mean_sd(null_rate)
    res['control_attest_rate_mean'] = m
    res['control_attest_rate_sd'] = sd
    res['b_p_two_sided'] = two_sided_p(obs_rate, null_rate)
    res['b_sd_units'] = z_units(obs_rate, null_rate)
    res['b_obs_above_control'] = obs_rate >= m
    # Power of the ornament branch. It is a NON-REJECTION gate, so the size of
    # the difference it could have detected has to be stated with the pass.
    sn = sorted(null_rate)
    q = lambda f: sn[min(len(sn) - 1, max(0, int(round(f * (len(sn) - 1)))))]
    res['control_null_q025'] = q(0.025)
    res['control_null_q975'] = q(0.975)
    res['b_min_detectable_abs_diff_at_p05'] = max(m - q(0.025), q(0.975) - m)
    res['b_observed_abs_diff'] = abs(obs_rate - m)

    def cmp_block(obs, null):
        mm, ss = mean_sd(null)
        return {'obs': obs, 'control_mean': mm, 'control_sd': ss,
                'sd_units': z_units(obs, null), 'p_two_sided': two_sided_p(obs, null)}

    res['c'] = {
        'word_top1': cmp_block(res['obs_word_stats']['top1_share'], null_w_t1),
        'word_top5': cmp_block(res['obs_word_stats']['top5_share'], null_w_t5),
        'word_entropy': cmp_block(res['obs_word_stats']['entropy_bits'], null_w_H),
        'residue_top1': cmp_block(res['obs_residue_stats']['top1_share'], null_r_t1),
        'residue_top5': cmp_block(res['obs_residue_stats']['top5_share'], null_r_t5),
        'residue_entropy': cmp_block(res['obs_residue_stats']['entropy_bits'], null_r_H),
    }
    # one-sided p for the LEXICAL gate: is the top-1 share higher than control?
    res['c']['word_top1']['p_one_sided_ge'] = one_sided_p_ge(
        res['obs_word_stats']['top1_share'], null_w_t1)
    res['c']['residue_top1']['p_one_sided_ge'] = one_sided_p_ge(
        res['obs_residue_stats']['top1_share'], null_r_t1)

    # SUPPLEMENTARY (not pre-registered) robustness check on (b): exact
    # gallows+length matching leaves some openers with no control at all, and
    # those are the long ones. Here the length match is widened to +/-1, then
    # +/-2, then any length with the same gallows, so that every gallows opener
    # is used. Reported alongside, never used for the gate.
    def relaxed_cell(g, L):
        for tol in (0, 1, 2):
            pool = []
            for dl in range(-tol, tol + 1):
                pool.extend(cells.get((g, L + dl), []))
            if pool:
                return pool
        pool = []
        for (gg, _ll), v in cells.items():
            if gg == g:
                pool.extend(v)
        return pool or None

    rkeys, rtgt = [], []
    for t in tgt:
        pool = relaxed_cell(t[1], len(t[0]))
        if pool is not None:
            rkeys.append(pool)
            rtgt.append(t)
    if rtgt:
        robs = sum(t[3] for t in rtgt) / len(rtgt)
        rng2 = random.Random(SEED + 2)
        rnull = [sum(rng2.choice(p)[2] for p in rkeys) / len(rkeys)
                 for _ in range(NDRAW)]
        res['b_relaxed_match_SUPPLEMENTARY'] = {
            'n_matched': len(rtgt), 'obs_attest_rate': robs,
            'control_mean': mean_sd(rnull)[0], 'control_sd': mean_sd(rnull)[1],
            'sd_units': z_units(robs, rnull), 'p_two_sided': two_sided_p(robs, rnull)}

    # top-20 stripped residues, with free-word frequency in the section ----
    rc = Counter(t[2] for t in tgt)
    res['top20_residues'] = [
        {'residue': r, 'n_openers': c,
         'opener_share': c / len(tgt) if tgt else 0.0,
         'free_word_freq_in_section': vocab.get(r, 0),
         'attested_free': r in vocab}
        for r, c in rc.most_common(20)]
    res['top10_opener_words'] = [
        {'word': w, 'n': c, 'share': c / len(pi) if pi else 0.0}
        for w, c in Counter(pi).most_common(10)]
    return res


def run_r1_stratum(pages, page_ids, vocab, name, seed=SEED):
    rng = random.Random(seed)
    pars, pi, nonpi, allw, nil = para_and_pools(pages, page_ids)
    out = {'name': name, 'n_pages': len(page_ids), 'n_paragraphs': len(pars),
           'pages': sorted(page_ids, key=lambda i: (fnum(i), i))}
    if not pi:
        out['empty'] = True
        return out
    out['a'] = r1_a(pi, nil, allw, rng)
    rng = random.Random(seed + 1)
    out['bc'] = r1_b_c(pi, nonpi, vocab, rng, name)
    out['gate'] = r1_gate(out)
    return out


def r1_gate(st):
    a, bc = st['a'], st['bc']
    sd_line = a['vs_line_initial']['sd_units']
    sd_all = a['vs_all_words']['sd_units']
    a_ok_both = (sd_line >= 3.0) and (sd_all >= 3.0)          # harder reading
    a_ok_either = (sd_line >= 3.0) or (sd_all >= 3.0)
    b_ok_strict = bc['b_p_two_sided'] > 0.05                   # harder reading
    b_ok_literal = (bc['b_p_two_sided'] > 0.05) or bc['b_obs_above_control']
    lex_word = (bc['obs_word_stats']['top1_share'] >= 0.10 and
                bc['c']['word_top1']['p_one_sided_ge'] < 0.01)
    lex_res = (bc['obs_residue_stats']['top1_share'] >= 0.10 and
               bc['c']['residue_top1']['p_one_sided_ge'] < 0.01)
    return {
        'a_sd_vs_line_initial': sd_line, 'a_sd_vs_all_words': sd_all,
        'a_ok_both_controls_3sd': a_ok_both, 'a_ok_either_control_3sd': a_ok_either,
        'b_p_two_sided': bc['b_p_two_sided'],
        'b_ok_strict_indistinguishable': b_ok_strict,
        'b_ok_literal_indistinguishable_or_above': b_ok_literal,
        'ORNAMENTAL_primary_harder': bool(a_ok_both and b_ok_strict),
        'ORNAMENTAL_literal': bool(a_ok_either and b_ok_literal),
        'lexical_top1_word_share': bc['obs_word_stats']['top1_share'],
        'lexical_top1_word_p': bc['c']['word_top1']['p_one_sided_ge'],
        'lexical_top1_residue_share': bc['obs_residue_stats']['top1_share'],
        'lexical_top1_residue_p': bc['c']['residue_top1']['p_one_sided_ge'],
        'LEXICAL': bool(lex_word or lex_res),
    }


# ------------------------------------------------------------------------ R2 --

def chi2_2xC(mask_group, cat_masks, n_total, n_group):
    """Chi-square of a 2 x C table where group membership is a bitmask and each
    category is a bitmask over the same paragraph indices."""
    n_other = n_total - n_group
    if n_group == 0 or n_other == 0:
        return 0.0
    chi = 0.0
    for cm in cat_masks:
        a = bin(mask_group & cm).count('1')
        tot = bin(cm).count('1')
        b = tot - a
        for obsv, n_row in ((a, n_group), (b, n_other)):
            exp = tot * n_row / n_total
            if exp > 0:
                chi += (obsv - exp) ** 2 / exp
    return chi


def run_r2(pages, page_ids, name, seed=SEED, ndraw=NDRAW):
    pars = [d for d in ML.paragraphs(pages, page_ids=page_ids) if d['star']]
    out = {'name': name, 'n_star_paragraphs': len(pars)}
    if len(pars) < 8:
        out['empty'] = True
        return out
    # outcomes -----------------------------------------------------------
    first_unit = [ML.bpe_apply(d['first_word'])[0] for d in pars]
    lengths = [len(d['words']) for d in pars]
    freq50 = [w for w, _ in Counter(
        [w for d in pars for w in d['words']]).most_common(50)]
    cats = sorted(set(first_unit))
    cat_masks = []
    for c in cats:
        m = 0
        for i, u in enumerate(first_unit):
            if u == c:
                m |= 1 << i
        cat_masks.append(m)
    type_masks = []
    for t in freq50:
        m = 0
        for i, d in enumerate(pars):
            if t in d['words']:
                m |= 1 << i
        type_masks.append(m)

    n = len(pars)
    preds = OrderedDict()
    pts = [1 if (d['star']['points'] == 8) else (0 if d['star']['points'] == 7 else None)
           for d in pars]
    preds['points_8_vs_7'] = pts
    preds['dotted'] = [1 if d['star']['dotted'] else 0 for d in pars]
    preds['tail'] = [1 if d['star']['tail'] else 0 for d in pars]

    tests = []
    pred_data = {}
    pages_of = [d['page'] for d in pars]
    for pname, lab in preds.items():
        idx = [i for i, v in enumerate(lab) if v is not None]
        sub_lab = [lab[i] for i in idx]
        k = sum(sub_lab)
        n_sub = len(idx)
        if k == 0 or k == n_sub:
            continue
        sub_mask_all = 0
        for i in idx:
            sub_mask_all |= 1 << i
        # restrict outcome masks to the sub-population
        c_masks = [m & sub_mask_all for m in cat_masks]
        t_masks = [m & sub_mask_all for m in type_masks]
        lens = {i: lengths[i] for i in idx}
        sum_all = sum(lens.values())

        def group_mask(sel):
            m = 0
            for i in sel:
                m |= 1 << i
            return m

        obs_sel = [i for i, v in zip(idx, sub_lab) if v == 1]
        obs_mask = group_mask(obs_sel)

        def stat_chi(mask):
            return chi2_2xC(mask, c_masks, n_sub, k)

        def stat_len(mask, sel):
            s = sum(lens[i] for i in sel)
            return abs(s / k - (sum_all - s) / (n_sub - k))

        def stat_type(mask, tm):
            a = bin(mask & tm).count('1')
            tot = bin(tm).count('1')
            return abs(a / k - (tot - a) / (n_sub - k))

        obs = {'first_glyph_unit_chi2': stat_chi(obs_mask),
               'length_mean_diff': stat_len(obs_mask, obs_sel),
               'types': [stat_type(obs_mask, tm) for tm in t_masks]}
        pred_data[pname] = {'idx': idx, 'lab': sub_lab, 'k': k, 'n_sub': n_sub,
                            'c_masks': c_masks, 't_masks': t_masks, 'lens': lens,
                            'sum_all': sum_all, 'obs': obs}

        rng = random.Random(seed)
        cnt_chi = cnt_len = 0
        cnt_types = [0] * len(t_masks)
        for _ in range(ndraw):
            sel = rng.sample(idx, k)
            gm = group_mask(sel)
            if stat_chi(gm) >= obs['first_glyph_unit_chi2'] - 1e-12:
                cnt_chi += 1
            if stat_len(gm, sel) >= obs['length_mean_diff'] - 1e-12:
                cnt_len += 1
            for j, tm in enumerate(t_masks):
                if stat_type(gm, tm) >= obs['types'][j] - 1e-12:
                    cnt_types[j] += 1
        d = ndraw + 1
        tests.append({'predictor': pname, 'outcome': 'first_glyph_unit',
                      'stat': 'chi2', 'value': obs['first_glyph_unit_chi2'],
                      'p': (1 + cnt_chi) / d, 'n': n_sub, 'k_group1': k})
        tests.append({'predictor': pname, 'outcome': 'paragraph_length_words',
                      'stat': 'abs_mean_diff', 'value': obs['length_mean_diff'],
                      'p': (1 + cnt_len) / d, 'n': n_sub, 'k_group1': k})
        for j, t in enumerate(freq50):
            tests.append({'predictor': pname, 'outcome': 'type:' + t,
                          'stat': 'abs_rate_diff', 'value': obs['types'][j],
                          'p': (1 + cnt_types[j]) / d, 'n': n_sub, 'k_group1': k})

    tests.sort(key=lambda t: (t['p'], -t['value']))

    # ---- diagnostic: how page-clustered is each star attribute? ------------
    clustering = {}
    for pname, pd in pred_data.items():
        per_page = {}
        for i, v in zip(pd['idx'], pd['lab']):
            a = per_page.setdefault(pages_of[i], [0, 0])
            a[0] += 1
            a[1] += v
        homog = sum(1 for a in per_page.values() if a[1] == 0 or a[1] == a[0])
        # Cramer's V between the attribute and the page identity
        n_sub, k = pd['n_sub'], pd['k']
        chi = 0.0
        for a in per_page.values():
            for obsv, n_row in ((a[1], k), (a[0] - a[1], n_sub - k)):
                exp = a[0] * n_row / n_sub
                if exp > 0:
                    chi += (obsv - exp) ** 2 / exp
        clustering[pname] = {
            'n_pages': len(per_page),
            'n_pages_homogeneous': homog,
            'frac_pages_homogeneous': homog / len(per_page) if per_page else None,
            'cramers_v_with_page': math.sqrt(chi / n_sub) if n_sub else None,
            'per_page_rate': {p: a[1] / a[0] for p, a in sorted(per_page.items())}}

    # ---- SUPPLEMENTARY (not pre-registered): the same statistic under a
    # page-stratified permutation, for the ten largest uncorrected effects.
    # The registered null permutes star annotations freely over paragraphs, so
    # it credits any page-level confound to the star. This one does not.
    supp = []
    for t in tests[:10]:
        pd = pred_data.get(t['predictor'])
        if pd is None:
            continue
        by_page = {}
        for i, v in zip(pd['idx'], pd['lab']):
            by_page.setdefault(pages_of[i], []).append((i, v))
        rng = random.Random(seed + 7)
        oc = t['outcome']
        if oc.startswith('type:'):
            tm = pd['t_masks'][freq50.index(oc[5:])]
        cnt = 0
        for _ in range(ndraw):
            sel = []
            for pg, items in by_page.items():
                labs = [v for _, v in items]
                rng.shuffle(labs)
                sel.extend(i for (i, _), v in zip(items, labs) if v == 1)
            kk = len(sel) or 1
            gm = 0
            for i in sel:
                gm |= 1 << i
            if oc == 'first_glyph_unit':
                val = chi2_2xC(gm, pd['c_masks'], pd['n_sub'], kk)
            elif oc == 'paragraph_length_words':
                s = sum(pd['lens'][i] for i in sel)
                val = abs(s / kk - (pd['sum_all'] - s) / max(1, pd['n_sub'] - kk))
            else:
                a = bin(gm & tm).count('1')
                tot = bin(tm).count('1')
                val = abs(a / kk - (tot - a) / max(1, pd['n_sub'] - kk))
            if val >= t['value'] - 1e-12:
                cnt += 1
        supp.append({'predictor': t['predictor'], 'outcome': t['outcome'],
                     'value': t['value'], 'p_registered_null': t['p'],
                     'p_page_stratified_null': (1 + cnt) / (ndraw + 1)})

    n_tests = len(tests)
    thr_actual = 0.01 / n_tests if n_tests else 0.0
    thr_proto53 = 0.01 / 53
    p_floor = 1.0 / (ndraw + 1)
    out.update({
        'n_tests_run': n_tests,
        'bonferroni_threshold_actual_tests': thr_actual,
        'bonferroni_threshold_protocol_53': thr_proto53,
        'permutation_p_floor': p_floor,
        'threshold_below_p_floor': thr_actual < p_floor,
        'survivors_actual_bonferroni': [t for t in tests if t['p'] < thr_actual],
        'survivors_protocol53_bonferroni': [t for t in tests if t['p'] < thr_proto53],
        'n_uncorrected_p_lt_0.05': sum(1 for t in tests if t['p'] < 0.05),
        'expected_false_positives_at_0.05': 0.05 * n_tests,
        'largest_uncorrected_effects_top10': tests[:10],
        'page_clustering_of_star_attributes': clustering,
        'SUPPLEMENTARY_page_stratified_null_top10': supp,
        'freq50_types': freq50,
        'first_glyph_unit_categories': cats,
        'star_summary': {
            'points': dict(Counter(d['star']['points'] for d in pars)),
            'dotted': sum(1 for d in pars if d['star']['dotted']),
            'tail': sum(1 for d in pars if d['star']['tail']),
        },
    })
    return out


# ---------------------------------------------------------------- driver -----

def build_vocab(pages, page_ids):
    """Free-word frequency table of the section (all word tokens on the pages
    of the whole section, both FIT and TEST folios)."""
    pars = ML.paragraphs(pages, page_ids=page_ids)
    c = Counter()
    for d in pars:
        c.update(d['words'])
    return c


def coverage_stats(pages, page_ids):
    """How much of the raw transcription survives the frozen clean parser on
    these pages. GC2a is written in a v101-family alphabet that uses digits and
    upper case as glyphs, and clean_tokens drops any such token; this is the
    number that says whether a replication on it means anything."""
    raw_n = kept_n = 0
    for pid in page_ids:
        for l in pages[pid]['loci']:
            if l['type'] != 'P':
                continue
            t = re.sub(r'\{[^}]*\}', '', l['raw'])
            t = t.replace('<->', ' ')
            t = re.sub(r'<[^>]*>', '', t)
            raw_n += len([x for x in re.split(r'[.\s,]+', t) if x])
            kept_n += len(l['words'])
    return {'raw_tokens': raw_n, 'kept_tokens': kept_n,
            'kept_fraction': kept_n / raw_n if raw_n else None}


def run_corpus(path, comma_split, tag):
    pages = ML.parse_pages(path, comma_split=comma_split)
    res = {'corpus': os.path.basename(path), 'comma_split': comma_split,
           'sha256': ML.sha256(path)}

    # --- R1 primary stratum: Recipes ($I=S), Currier B, f103r-f116r --------
    recB = stratum(pages, 'S', lang='B', fmin=103, fmax=116)
    res['parser_coverage_recipesB'] = coverage_stats(pages, recB)
    res['n_star_comments_in_recipes'] = sum(
        1 for d in ML.paragraphs(pages, illus='S') if d['star'])
    vocab_recB = build_vocab(pages, recB)
    res['recipes_vocab_tokens'] = sum(vocab_recB.values())
    res['recipes_vocab_types'] = len(vocab_recB)
    r1 = OrderedDict()
    for split, ids in (('ALL', recB),
                       ('FIT_odd', {i for i in recB if fnum(i) % 2 == 1}),
                       ('TEST_even', {i for i in recB if fnum(i) % 2 == 0})):
        r1['recipesB_' + split] = run_r1_stratum(pages, ids, vocab_recB,
                                                 'recipesB_' + split)
    # out-of-sample: f58r/f58v, Currier A
    ids58 = stratum(pages, None, page_ids={'f58r', 'f58v'})
    if ids58:
        v58 = build_vocab(pages, ids58)
        r1['f58_langA_oos'] = run_r1_stratum(pages, ids58, v58, 'f58_langA_oos')
    # second stratum: the whole Herbal section ($I=H)
    herb = stratum(pages, 'H')
    vocab_h = build_vocab(pages, herb)
    r1['herbal_ALL'] = run_r1_stratum(pages, herb, vocab_h, 'herbal_ALL')
    r1['herbal_TEST_even'] = run_r1_stratum(
        pages, {i for i in herb if fnum(i) % 2 == 0}, vocab_h, 'herbal_TEST_even')
    res['R1'] = r1

    # --- R2 -----------------------------------------------------------------
    r2 = OrderedDict()
    recS = stratum(pages, 'S')
    r2['recipes_TEST_even'] = run_r2(pages, {i for i in recS if fnum(i) % 2 == 0},
                                     'recipes_TEST_even')
    r2['recipes_FIT_odd'] = run_r2(pages, {i for i in recS if fnum(i) % 2 == 1},
                                   'recipes_FIT_odd')
    r2['recipes_ALL'] = run_r2(pages, recS, 'recipes_ALL')
    res['R2'] = r2
    return res


def main():
    os.makedirs(RESULTS, exist_ok=True)
    out = OrderedDict()
    out['key'] = 'r1r2'
    out['protocol'] = 'experiments/meaning-probes/PROTOCOL.md (frozen)'
    out['seed'] = SEED
    out['n_draws'] = NDRAW
    out['inputs'] = {
        'ZL3b-n.txt': {'path': ZL, 'sha256': ML.sha256(ZL)},
        'GC2a-n.txt': {'path': GC, 'sha256': ML.sha256(GC)},
        'meaning_lib.py': {'path': os.path.join(HERE, 'meaning_lib.py'),
                           'sha256': ML.sha256(os.path.join(HERE, 'meaning_lib.py'))},
        'PROTOCOL.md': {'path': os.path.join(HERE, 'PROTOCOL.md'),
                        'sha256': ML.sha256(os.path.join(HERE, 'PROTOCOL.md'))},
    }
    out['ambiguities'] = [
        "R1(a) '(a) exceeds the control by >= 3 SD' names two controls "
        "(paragraph-internal line-initial words; all Recipes words). Harder "
        "reading taken: >= 3 SD against BOTH. Both are reported.",
        "R1(b) 'indistinguishable from or above the matched control (p>0.05)'. "
        "Harder reading taken for the primary gate: the ornament branch needs "
        "p_two_sided > 0.05 (indistinguishable). The literal reading "
        "(p>0.05 OR rate above control mean) is reported as ORNAMENTAL_literal.",
        "R1(b) 'attested elsewhere in the section as a free word': attestation "
        "vocabulary is every word token of the whole stratum section (both FIT "
        "and TEST folios), residue counted as attested if it occurs as a free "
        "word type anywhere in it. Control words are matched on the specific "
        "gallows string and on EVA character length and drawn only from "
        "non-paragraph-initial token positions of the same split.",
        "R1 lexical gate 'permutation p < 0.01' for the >=10% type: computed as "
        "the one-sided p of the observed top-1 type share against the same "
        "matched-control resample distribution used in (b)/(c).",
        "R2 'Bonferroni over the 53 tests': the design named (3 predictors x "
        "(1 opening glyph unit + 1 length + 50 types)) actually yields 156 "
        "tests per stratum. Harder reading taken: Bonferroni over the number of "
        "tests actually run. The protocol's literal 53 is also reported. NOTE "
        "the power limit: 0.01/156 = 6.4e-5 lies BELOW the 10,000-draw "
        "permutation p floor of 1/10001 = 1.0e-4, so under the harder reading "
        "no test CAN be declared a survivor at 10,000 draws; 0.01/53 = 1.9e-4 "
        "is attainable. Both are reported, and any test sitting at the p floor "
        "is flagged.",
        "R2 stratum: PROTOCOL's split table assigns R2 the same FIT/TEST split "
        "as R1, so TEST (even Recipes folios) is primary; FIT and ALL are also "
        "reported.",
        "R1 second stratum (Herbal $I=H) has no split defined in the protocol; "
        "the whole section is reported, with the even-folio half also shown.",
    ]

    say('=' * 78)
    say('R1 / R2 — meaning-probes pass. seed', SEED, ' draws', NDRAW)
    say('=' * 78)

    runs = OrderedDict()
    runs['ZL3b_comma_split_true'] = run_corpus(ZL, True, 'ZL3b')
    runs['ZL3b_comma_split_false'] = run_corpus(ZL, False, 'ZL3b')
    runs['GC2a_comma_split_true'] = run_corpus(GC, True, 'GC2a')
    out['runs'] = runs

    # ---------------------------------------------------------- summary ------
    prim = runs['ZL3b_comma_split_true']
    for key in ('recipesB_TEST_even', 'recipesB_FIT_odd', 'recipesB_ALL',
                'herbal_ALL', 'herbal_TEST_even', 'f58_langA_oos'):
        st = prim['R1'].get(key)
        if not st or st.get('empty'):
            continue
        a, bc, g = st['a'], st['bc'], st['gate']
        say('')
        say('--- R1 stratum:', key, ' paragraphs:', st['n_paragraphs'])
        say('  (a) gallows rate: para-initial %.4f (n=%d) | line-initial %.4f (n=%d) '
            '| all words %.4f (n=%d)' % (
                a['rate_para_initial'], a['n_para_initial'],
                a['rate_nonpara_line_initial'], a['n_nonpara_line_initial'],
                a['rate_all_words'], a['n_all_words']))
        say('      vs line-initial: diff %+.4f = %.1f SD (p=%.5f)' % (
            a['vs_line_initial']['diff'], a['vs_line_initial']['sd_units'],
            a['vs_line_initial']['p_two_sided']))
        say('      vs all words   : diff %+.4f = %.1f SD (p=%.5f)' % (
            a['vs_all_words']['diff'], a['vs_all_words']['sd_units'],
            a['vs_all_words']['p_two_sided']))
        say('  (b) residue attested as free word: openers %.4f (n=%d matched) | '
            'matched control %.4f +/- %.4f -> %.2f SD, two-sided p=%.4f' % (
                bc['obs_attest_rate_matchable'], bc['n_matchable'],
                bc['control_attest_rate_mean'], bc['control_attest_rate_sd'],
                bc['b_sd_units'], bc['b_p_two_sided']))
        say('      power of (b): |obs-ctrl| = %.4f ; smallest difference this n '
            'could reject at p<0.05 = %.4f ; %d of %d gallows openers had no '
            'length+gallows match and were dropped (attested %s, mean len %.1f '
            'vs %.1f kept)' % (
                bc['b_observed_abs_diff'], bc['b_min_detectable_abs_diff_at_p05'],
                bc['n_unmatched_dropped'], bc['n_para_initial_gallows'],
                ('%.4f' % bc['obs_attest_rate_dropped_unmatched']
                 if bc['obs_attest_rate_dropped_unmatched'] is not None else 'n/a'),
                bc['mean_len_dropped'] or 0.0, bc['mean_len_matchable'] or 0.0))
        rb = bc.get('b_relaxed_match_SUPPLEMENTARY')
        if rb:
            say('      SUPPLEMENTARY (b) with +/-1,2,any length fallback so no opener '
                'is dropped: n=%d openers %.4f vs control %.4f -> %.2f SD, p=%.4f'
                % (rb['n_matched'], rb['obs_attest_rate'], rb['control_mean'],
                   rb['sd_units'], rb['p_two_sided']))
        say('  (c) opener words   top1 %.4f (ctrl %.4f, p=%.4f) top5 %.4f (ctrl %.4f) '
            'H %.3f (ctrl %.3f, p=%.4f)' % (
                bc['c']['word_top1']['obs'], bc['c']['word_top1']['control_mean'],
                bc['c']['word_top1']['p_two_sided'],
                bc['c']['word_top5']['obs'], bc['c']['word_top5']['control_mean'],
                bc['c']['word_entropy']['obs'], bc['c']['word_entropy']['control_mean'],
                bc['c']['word_entropy']['p_two_sided']))
        say('  (c) residues       top1 %.4f (ctrl %.4f, p=%.4f) top5 %.4f (ctrl %.4f) '
            'H %.3f (ctrl %.3f, p=%.4f)' % (
                bc['c']['residue_top1']['obs'], bc['c']['residue_top1']['control_mean'],
                bc['c']['residue_top1']['p_two_sided'],
                bc['c']['residue_top5']['obs'], bc['c']['residue_top5']['control_mean'],
                bc['c']['residue_entropy']['obs'],
                bc['c']['residue_entropy']['control_mean'],
                bc['c']['residue_entropy']['p_two_sided']))
        say('  top-5 residues:', ', '.join(
            '%s x%d (free %d)' % (r['residue'], r['n_openers'],
                                  r['free_word_freq_in_section'])
            for r in bc['top20_residues'][:5]))
        say('  GATE: ORNAMENTAL(harder)=%s  ORNAMENTAL(literal)=%s  LEXICAL=%s' % (
            g['ORNAMENTAL_primary_harder'], g['ORNAMENTAL_literal'], g['LEXICAL']))

    gcr = runs['GC2a_comma_split_true']
    say('')
    say('--- GC2a replication status')
    say('   clean-parser coverage on the Recipes-B pages: ZL3b %d/%d tokens kept '
        '(%.3f) vs GC2a %d/%d (%.3f)' % (
            prim['parser_coverage_recipesB']['kept_tokens'],
            prim['parser_coverage_recipesB']['raw_tokens'],
            prim['parser_coverage_recipesB']['kept_fraction'],
            gcr['parser_coverage_recipesB']['kept_tokens'],
            gcr['parser_coverage_recipesB']['raw_tokens'],
            gcr['parser_coverage_recipesB']['kept_fraction']))
    say('   GC2a is a v101-family alphabet: digits and upper case are glyphs, the '
        'frozen clean parser drops every token containing them, and the EVA '
        'gallows set t/p/k/f/cth/ckh/cph/cfh has no counterpart in the surviving '
        'subset. R1 numbers on GC2a below are NOT evidence in either direction.')
    say('   GC2a star comments found in the Recipes section: %d -> R2 cannot be '
        'replicated at all.' % gcr['n_star_comments_in_recipes'])

    for label, run in (('ZL3b comma_split=False', runs['ZL3b_comma_split_false']),
                       ('GC2a (see status above; not evidence)', gcr)):
        st = run['R1'].get('recipesB_TEST_even')
        if st and not st.get('empty'):
            g = st['gate']
            say('')
            say('--- R1 %s, recipesB_TEST_even: a-SD line/all = %.1f / %.1f ; '
                'b p=%.4f (%.4f vs %.4f) ; ORN(harder)=%s ORN(literal)=%s LEX=%s' % (
                    label, g['a_sd_vs_line_initial'], g['a_sd_vs_all_words'],
                    g['b_p_two_sided'], st['bc']['obs_attest_rate_matchable'],
                    st['bc']['control_attest_rate_mean'],
                    g['ORNAMENTAL_primary_harder'], g['ORNAMENTAL_literal'],
                    g['LEXICAL']))

    for key in ('recipes_TEST_even', 'recipes_FIT_odd', 'recipes_ALL'):
        r = prim['R2'][key]
        if r.get('empty'):
            continue
        say('')
        say('--- R2 stratum:', key, ' star paragraphs:', r['n_star_paragraphs'],
            ' tests:', r['n_tests_run'])
        say('   Bonferroni thresholds: actual %.2e | protocol-53 %.2e | p floor %.2e'
            % (r['bonferroni_threshold_actual_tests'],
               r['bonferroni_threshold_protocol_53'], r['permutation_p_floor']))
        say('   survivors (actual Bonferroni): %d ; (protocol-53): %d ; '
            'uncorrected p<0.05: %d (expected by chance %.1f)' % (
                len(r['survivors_actual_bonferroni']),
                len(r['survivors_protocol53_bonferroni']),
                r['n_uncorrected_p_lt_0.05'], r['expected_false_positives_at_0.05']))
        for t in r['largest_uncorrected_effects_top10'][:5]:
            say('     %-16s %-28s %s=%.4f p=%.4f' % (
                t['predictor'], t['outcome'], t['stat'], t['value'], t['p']))
        say('   star attribute vs page identity (Cramer V / share of pages that are '
            'all-or-nothing for it):')
        for pn, cl in r['page_clustering_of_star_attributes'].items():
            say('     %-16s V=%.3f  homogeneous pages %d/%d' % (
                pn, cl['cramers_v_with_page'], cl['n_pages_homogeneous'],
                cl['n_pages']))
        say('   SUPPLEMENTARY (not pre-registered) same effects under a '
            'page-stratified null:')
        for s in r['SUPPLEMENTARY_page_stratified_null_top10'][:5]:
            say('     %-16s %-28s p_registered=%.4f -> p_within_page=%.4f' % (
                s['predictor'], s['outcome'], s['p_registered_null'],
                s['p_page_stratified_null']))

    tb = prim['R1']['recipesB_TEST_even']['bc']
    fb = prim['R1']['recipesB_FIT_odd']['bc']
    out['verdict'] = {
        'headline':
            'R1(a) PASSES enormously (paragraph openers are gallows-initial at '
            '%.3f vs %.3f for paragraph-internal line-initial words, %.1f SD). '
            'R1 ORNAMENTAL passes the frozen gate on the pre-registered TEST '
            'stratum (b p=%.3f), but the pass is fragile: exact gallows+length '
            'matching found no control for %d of the %d gallows openers on TEST '
            'and those dropped openers are the long ones (attested %.2f). With '
            'no opener dropped (supplementary relaxed matching) TEST reverses to '
            '%.2f SD, p=%.4f, matching the FIT half (%.2f SD, p=%.4f) and the '
            'pooled section. R1 LEXICAL fails decisively: the commonest opener '
            'type is %.1f%% of openers (gate needs 10%%) and openers are MORE '
            'diverse than the matched control, not less. R2: nothing survives '
            'Bonferroni on TEST under either reading, as registered.' % (
                prim['R1']['recipesB_TEST_even']['a']['rate_para_initial'],
                prim['R1']['recipesB_TEST_even']['a']['rate_nonpara_line_initial'],
                prim['R1']['recipesB_TEST_even']['a']['vs_line_initial']['sd_units'],
                tb['b_p_two_sided'], tb['n_unmatched_dropped'],
                tb['n_para_initial_gallows'],
                tb['obs_attest_rate_dropped_unmatched'],
                tb['b_relaxed_match_SUPPLEMENTARY']['sd_units'],
                tb['b_relaxed_match_SUPPLEMENTARY']['p_two_sided'],
                fb['b_relaxed_match_SUPPLEMENTARY']['sd_units'],
                fb['b_relaxed_match_SUPPLEMENTARY']['p_two_sided'],
                100 * tb['obs_word_stats']['top1_share']),
        'GC2a_replication_status':
            'NOT RUNNABLE as like-for-like: v101-family alphabet, clean parser '
            'keeps %.1f%% of Recipes-B tokens (ZL3b %.1f%%), EVA gallows set does '
            'not exist in the surviving subset, and the transcription carries 0 '
            'star comments so R2 has no annotations to permute. Numbers are '
            'recorded in runs.GC2a_comma_split_true but are not evidence.' % (
                100 * gcr['parser_coverage_recipesB']['kept_fraction'],
                100 * prim['parser_coverage_recipesB']['kept_fraction']),
        'R1_TEST_even_ZL3b': prim['R1']['recipesB_TEST_even']['gate'],
        'R1_herbal_ZL3b': prim['R1']['herbal_ALL']['gate'],
        'R1_TEST_even_GC2a': runs['GC2a_comma_split_true']['R1']['recipesB_TEST_even']['gate'],
        'R1_TEST_even_ZL3b_nocomma': runs['ZL3b_comma_split_false']['R1']['recipesB_TEST_even']['gate'],
        'R2_TEST_even_ZL3b_survivors_actual': len(
            prim['R2']['recipes_TEST_even']['survivors_actual_bonferroni']),
        'R2_TEST_even_ZL3b_survivors_proto53': len(
            prim['R2']['recipes_TEST_even']['survivors_protocol53_bonferroni']),
    }

    say('')
    say('=' * 78)
    say('VERDICT')
    say(out['verdict']['headline'])
    say('')
    say('GC2a: ' + out['verdict']['GC2a_replication_status'])
    say('=' * 78)

    with io.open(os.path.join(RESULTS, 'r1r2.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, sort_keys=False, ensure_ascii=False)
    with io.open(os.path.join(RESULTS, 'r1r2.stdout.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(_out_lines) + '\n')
    print('\nwrote', os.path.join(RESULTS, 'r1r2.json'))


if __name__ == '__main__':
    main()
