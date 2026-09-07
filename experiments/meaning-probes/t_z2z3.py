#!/usr/bin/env python3
"""t_z2z3.py -- Z2 (same slot across signs) and Z3 (label inventory).

Pre-registered in experiments/meaning-probes/PROTOCOL.md.  Gates are frozen
there; nothing in this file adjusts a gate, a statistic, a null or a split.

Stdlib only.  Deterministic: seed 408 everywhere, 10,000 permutation draws.

--------------------------------------------------------------------------
AMBIGUITY RESOLUTIONS (every one taken in the direction that makes the test
HARDER to pass; all are recorded in the JSON under "ambiguities_resolved")
--------------------------------------------------------------------------
1.  p-value sidedness.  Z2 does not state a side; Z1 states "two-sided p".
    Two-sided is used (harder).  One-sided is also reported, never used for
    the gate.
2.  "the numeral controls' effect" -- Z1's analogous clause says "median D
    over the numeral controls".  The MEDIAN over the 8 series is used, on the
    CLEAN (undegraded) controls, which are the larger of the two control
    effects, so 25% of it is the higher bar.  The degraded (30% noise)
    controls are reported for sensitivity only and are never the denominator.
3.  Positive-control construction.  "measure whether the test recovers the
    known same-slot identity" is read as: the synthetic signs must actually
    CARRY same-slot identity under the convention being tested, i.e. numeral
    k is placed at the k-th distinct slot value of that convention, so that
    the same slot holds the same numeral in every synthetic sign.  This gives
    the LARGEST possible control effect, hence the highest 25% bar.
4.  Text representation of the numeral controls.  The identical pipeline is
    applied (the frozen 20 BPE merges are a deterministic string transform),
    so the glyph-unit Voynich statistic is compared against glyph-unit
    numeral controls.  Raw-character versions of both are reported as the
    protocol's robustness check.  Where the two disagree the gate verdict is
    reported for both and the conjunction is what is claimed.
5.  Convention B, "rings aligned outer-first".  In ZL3b the Lz locus groups
    are transcribed from outside inwards on every zodiac folio (the ZL
    comments read "outer ring / middle band / inner band"; the two folios
    with a partial top group, Scorpius and Sagittarius, put that group --
    which sits physically on top of, i.e. outside, the outer circle -- first).
    So ring index in manuscript order IS the outer-first rank.  The comment
    string that opens each ring group is recorded in the JSON so this can be
    checked.
6.  Convention C rounding.  floor(minutes/30 + 0.5) mod 24 (half-up), not
    Python's banker's round, so 02:45 -> slot 6 deterministically.
7.  Z2 "similarity" of a multi-word label.  The label's words are
    concatenated into one sequence (glyph units, or characters).  253 of the
    294 label loci are single words, so this affects a minority.
8.  Z3 "the same pages" -- the twelve zodiac folios, labels = Lz loci,
    running text = P/C/R loci on those folios.  The whole-manuscript version
    (all 54 pages carrying both) is also reported.
9.  GC2a replication.  The frozen clean parser drops any token containing a
    digit; GC2a is written in a v101-family alphabet that uses digits, so
    only 91 of the 294 label loci survive parsing and none carries a clock
    annotation.  The replication is run anyway and reported, with the
    coverage loss stated, and it is NOT treated as evidence in either
    direction.
"""
import hashlib, io, json, math, random, re, sys, statistics
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as M

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
RESULTS.mkdir(exist_ok=True)

ZL3B = r"R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt"
GC2A = r"R:/Coding/LinearA/tmp/voynich_repo/data/corpora/GC2a-n.txt"
CULP = r"R:/Coding/LinearA/tmp/voynich_lab/pg49513.txt"
VULG = r"R:/Coding/LinearA/tmp/voynich_lab/bibles/Latin.xml"

NPERM = 10000
SEED = M.SEED           # 408
CONVENTIONS = ['A', 'B', 'C']
CONV_DESC = {
    'A': 'index within sign, manuscript order',
    'B': '(ring rank outer-first, index within ring)',
    'C': 'clock position rounded to nearest 30 minutes',
}

OUT = []


def say(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    OUT.append(s)


# ===================================================== representation utils ==

def seq_unit(words):
    out = []
    for w in words:
        out.extend(M.bpe_apply(w))
    return out


def seq_char(words):
    return list(''.join(words))


REPS = OrderedDict([('unit', seq_unit), ('char', seq_char)])


# ============================================================ slot mapping ==

def slot_of(rec, conv):
    if conv == 'A':
        return rec['idx_in_sign']
    if conv == 'B':
        return (rec['ring'], rec['idx_in_ring'])
    if conv == 'C':
        cm = rec['clock_min']
        if cm is None:
            return None
        return int(math.floor(cm / 30.0 + 0.5)) % 24
    raise ValueError(conv)


# ============================================================ Z2 machinery ==

class Design(object):
    """Positions grouped by sign, each position carrying a fixed slot value and
    an item (a sequence).  Within-sign permutation shuffles which item sits at
    which position of that sign; the slot multiset of each sign is therefore
    invariant, so the same-slot cross-sign pair COUNT is invariant and only the
    same-slot similarity SUM has to be recomputed per draw."""

    def __init__(self, sign_names, sign_slots, sign_items):
        self.sign_names = list(sign_names)
        self.sign_slots = [list(s) for s in sign_slots]
        self.sign_items = [list(s) for s in sign_items]
        self.groups = []            # list of lists of global positions
        self.slot = []
        self.items = []
        p = 0
        for g, slots in enumerate(self.sign_slots):
            grp = []
            for k, s in enumerate(slots):
                self.slot.append(s)
                self.items.append(self.sign_items[g][k])
                grp.append(p)
                p += 1
            self.groups.append(grp)
        self.n = p
        # similarity matrix over items (indexed by initial position)
        self.sim = [[0.0] * self.n for _ in range(self.n)]
        for i in range(self.n):
            for j in range(i + 1, self.n):
                v = M.lcs_sim(self.items[i], self.items[j])
                self.sim[i][j] = v
                self.sim[j][i] = v
        # cross-sign position pairs, split into same-slot / all
        self.same_pairs = []
        self.n_cross = 0
        self.s_cross = 0.0
        for gi in range(len(self.groups)):
            for gj in range(gi + 1, len(self.groups)):
                for p1 in self.groups[gi]:
                    for p2 in self.groups[gj]:
                        self.n_cross += 1
                        self.s_cross += self.sim[p1][p2]
                        if self.slot[p1] == self.slot[p2]:
                            self.same_pairs.append((p1, p2))
        self.n_same = len(self.same_pairs)

    def effect(self, a):
        if self.n_same == 0 or self.n_cross - self.n_same == 0:
            return None
        sim = self.sim
        s = 0.0
        for p1, p2 in self.same_pairs:
            s += sim[a[p1]][a[p2]]
        m_same = s / self.n_same
        m_diff = (self.s_cross - s) / (self.n_cross - self.n_same)
        return m_same - m_diff, m_same, m_diff

    def run(self, nperm=NPERM, seed=SEED):
        ident = list(range(self.n))
        obs = self.effect(ident)
        if obs is None:
            return {'n_items': self.n, 'n_same_pairs': self.n_same,
                    'n_cross_pairs': self.n_cross, 'effect': None,
                    'note': 'no same-slot cross-sign pairs; test not defined'}
        eff, m_same, m_diff = obs
        rng = random.Random(seed)
        a = list(range(self.n))
        ge_two, ge_one = 0, 0
        nulls = []
        for _ in range(nperm):
            for grp in self.groups:
                vals = [a[p] for p in grp]
                rng.shuffle(vals)
                for p, v in zip(grp, vals):
                    a[p] = v
            e = self.effect(a)[0]
            nulls.append(e)
            if abs(e) >= abs(eff) - 1e-15:
                ge_two += 1
            if e >= eff - 1e-15:
                ge_one += 1
        mu = statistics.fmean(nulls)
        sd = statistics.pstdev(nulls)
        return {
            'n_items': self.n, 'n_signs': len(self.groups),
            'n_same_pairs': self.n_same, 'n_cross_pairs': self.n_cross,
            'mean_sim_same_slot': m_same, 'mean_sim_diff_slot': m_diff,
            'effect': eff,
            'null_mean': mu, 'null_sd': sd,
            'z': (eff - mu) / sd if sd > 0 else None,
            'p_two_sided': (1 + ge_two) / (nperm + 1.0),
            'p_one_sided': (1 + ge_one) / (nperm + 1.0),
            'nperm': nperm, 'seed': seed,
        }


def build_voynich_design(labels, signs, conv, rep):
    fn = REPS[rep]
    names, slots, items = [], [], []
    for sg in signs:
        recs = [r for r in labels if r['sign'] == sg]
        ss, ii = [], []
        for r in recs:
            s = slot_of(r, conv)
            if s is None:
                continue
            ss.append(s)
            ii.append(fn(r['words']))
        if len(ss) >= 1:
            names.append(sg)
            slots.append(ss)
            items.append(ii)
    if len(names) < 2:
        return None
    return Design(names, slots, items)


def build_numeral_design(labels, signs, conv, rep, series, degrade=0.0,
                         noise_pool=None, seed=SEED):
    """Five synthetic signs carrying the SAME numeral series, laid out on the
    observed per-sign slot structure of `signs` under `conv`.  Numeral k is
    placed at the k-th distinct slot value of the convention (ambiguity 3), so
    same-slot identity holds by construction."""
    fn = REPS[rep]
    names, slotlists = [], []
    for sg in signs:
        recs = [r for r in labels if r['sign'] == sg]
        ss = [slot_of(r, conv) for r in recs]
        ss = [s for s in ss if s is not None]
        if ss:
            names.append(sg)
            slotlists.append(ss)
    if len(names) < 2:
        return None
    allslots = sorted({s for ss in slotlists for s in ss},
                      key=lambda x: (x if isinstance(x, tuple) else (x,)))
    rank = {s: i for i, s in enumerate(allslots)}
    strings = []
    for ss in slotlists:
        strings.append([series[rank[s] % len(series)] for s in ss])
    if degrade > 0.0:
        rng = random.Random(seed + 1)
        flat = [(g, k) for g, ss in enumerate(strings) for k in range(len(ss))]
        nrep = int(round(degrade * len(flat)))
        for g, k in rng.sample(flat, nrep):
            strings[g][k] = noise_pool[rng.randrange(len(noise_pool))]
    items = [[fn([w]) for w in ss] for ss in strings]
    return Design(names, slotlists, items)


# ================================================================== inputs ==

def vulgate_types(path, lo=3, hi=12, cap=4000):
    t = io.open(path, encoding='utf-8', errors='replace').read()
    t = re.sub(r'<[^>]*>', ' ', t)
    ws = M.letters_only(M.words_en(t))
    types = sorted({w for w in ws if lo <= len(w) <= hi})
    rng = random.Random(SEED)
    if len(types) > cap:
        types = sorted(rng.sample(types, cap))
    return types


# ====================================================================== Z2 ==

def run_z2(tag, labels, noise_pool):
    res = {'transcription': tag, 'conventions': {}}
    numerals = M.numeral_controls()
    for conv in CONVENTIONS:
        cres = {'description': CONV_DESC[conv], 'reps': {}}
        for rep in REPS:
            rr = {}
            for split, signs in (('FIT', M.FIT_SIGNS), ('TEST', M.TEST_SIGNS)):
                d = build_voynich_design(labels, signs, conv, rep)
                rr[split] = d.run() if d is not None else {'effect': None,
                                                           'note': 'no design'}
            # numeral power calibration on the TEST slot structure
            ctl = {'clean': {}, 'degraded30': {}}
            for nm, series in numerals.items():
                for key, deg in (('clean', 0.0), ('degraded30', 0.30)):
                    d = build_numeral_design(labels, M.TEST_SIGNS, conv, rep,
                                             series, degrade=deg,
                                             noise_pool=noise_pool)
                    ctl[key][nm] = d.run() if d is not None else {'effect': None}
            summary = {}
            for key in ('clean', 'degraded30'):
                effs = [v['effect'] for v in ctl[key].values()
                        if v.get('effect') is not None]
                ps = [v['p_two_sided'] for v in ctl[key].values()
                      if v.get('p_two_sided') is not None]
                summary[key] = {
                    'median_effect': statistics.median(effs) if effs else None,
                    'max_effect': max(effs) if effs else None,
                    'min_effect': min(effs) if effs else None,
                    'n_series': len(effs),
                    'frac_p_lt_0.01': (sum(1 for p in ps if p < 0.01) / len(ps)
                                       if ps else None),
                }
            rr['numeral_controls'] = ctl
            rr['numeral_summary'] = summary
            # gate arithmetic
            te = rr['TEST'].get('effect')
            med = summary['clean']['median_effect']
            ratio = (te / med) if (te is not None and med not in (None, 0)) else None
            rr['gate'] = {
                'test_p_two_sided': rr['TEST'].get('p_two_sided'),
                'test_effect': te,
                'clean_control_median_effect': med,
                'effect_ratio_to_control': ratio,
                'passes_p': (rr['TEST'].get('p_two_sided') is not None
                             and rr['TEST']['p_two_sided'] < 0.01),
                'passes_effect': (ratio is not None and ratio >= 0.25),
                'passes': (rr['TEST'].get('p_two_sided') is not None
                           and rr['TEST']['p_two_sided'] < 0.01
                           and ratio is not None and ratio >= 0.25),
                'measured_power_frac_controls_p_lt_0.01':
                    summary['clean']['frac_p_lt_0.01'],
            }
            cres['reps'][rep] = rr
        res['conventions'][conv] = cres
    # overall gate: pass under at least one convention (primary rep = unit)
    res['gate_Z2'] = {}
    for rep in REPS:
        passed = [c for c in CONVENTIONS
                  if res['conventions'][c]['reps'][rep]['gate']['passes']]
        powers = [res['conventions'][c]['reps'][rep]['gate']
                  ['measured_power_frac_controls_p_lt_0.01']
                  for c in CONVENTIONS]
        res['gate_Z2'][rep] = {'conventions_passing': passed,
                               'passes': bool(passed),
                               'measured_power_by_convention':
                                   dict(zip(CONVENTIONS, powers))}
    return res


# ====================================================================== Z3 ==

def z3_inventory(tag, pages, labels):
    r = {'transcription': tag}
    strings = [x['text'] for x in labels]
    r['n_label_loci'] = len(strings)
    r['n_distinct_label_strings'] = len(set(strings))
    r['distinct_over_total'] = len(set(strings)) / len(strings) if strings else None
    r['gate_Z3_fixed_inventory_threshold'] = 0.5
    r['gate_Z3_passes'] = (r['distinct_over_total'] is not None
                           and r['distinct_over_total'] < 0.5)
    words = [w for x in labels for w in x['words']]
    r['n_label_word_tokens'] = len(words)
    r['n_label_word_types'] = len(set(words))
    r['label_word_TTR'] = len(set(words)) / len(words) if words else None

    # repeats: within-sign vs across-sign
    by_str = defaultdict(list)
    for x in labels:
        by_str[x['text']].append(x)
    reps = []
    for s, xs in sorted(by_str.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(xs) < 2:
            continue
        signs = [x['sign'] for x in xs]
        reps.append({
            'string': s, 'count': len(xs),
            'n_distinct_signs': len(set(signs)),
            'scope': ('within-sign only' if len(set(signs)) == 1
                      else ('across-sign only' if len(set(signs)) == len(signs)
                            else 'both')),
            'occurrences': [{'sign': x['sign'], 'page': x['page'],
                             'locus': x['locus_n'], 'ring': x['ring'],
                             'idx_in_sign': x['idx_in_sign'],
                             'clock': x['clock']} for x in xs],
        })
    r['repeated_label_strings'] = reps
    r['n_repeated_strings'] = len(reps)
    r['n_strings_shared_by_ge2_signs'] = sum(1 for x in reps if x['n_distinct_signs'] >= 2)
    r['n_strings_shared_by_ge3_signs'] = sum(1 for x in reps if x['n_distinct_signs'] >= 3)
    r['n_strings_repeated_within_sign_only'] = sum(1 for x in reps if x['scope'] == 'within-sign only')

    # word-level repeats across signs (secondary)
    w_by_sign = defaultdict(set)
    for x in labels:
        for w in x['words']:
            w_by_sign[w].add(x['sign'])
    r['n_label_word_types_in_ge2_signs'] = sum(1 for v in w_by_sign.values() if len(v) >= 2)
    r['n_label_word_types_in_ge3_signs'] = sum(1 for v in w_by_sign.values() if len(v) >= 3)

    # glyph units in labels vs running text, zodiac pages
    zpages = [f for fs in M.ZODIAC_SIGNS.values() for f in fs]
    lab_words_by_page = defaultdict(list)
    for x in labels:
        lab_words_by_page[x['page']].extend(x['words'])
    txt_words_by_page = defaultdict(list)
    for fo in zpages:
        p = pages.get(fo)
        if not p:
            continue
        for l in p['loci']:
            if l['type'] in ('P', 'C', 'R'):
                txt_words_by_page[fo].extend(l['words'])
    lab_all = [w for v in lab_words_by_page.values() for w in v]
    txt_all = [w for v in txt_words_by_page.values() for w in v]
    lu = Counter(u for w in lab_all for u in M.bpe_apply(w))
    tu = Counter(u for w in txt_all for u in M.bpe_apply(w))
    r['zodiac_pages'] = {
        'n_pages': len([f for f in zpages if f in pages]),
        'n_label_tokens': len(lab_all), 'n_text_tokens': len(txt_all),
        'n_distinct_glyph_units_labels': len(lu),
        'n_distinct_glyph_units_text': len(tu),
        'n_shared': len(set(lu) & set(tu)),
        'units_only_in_labels': sorted(set(lu) - set(tu)),
        'units_only_in_text': sorted(set(tu) - set(lu)),
        'label_unit_tokens': sum(lu.values()), 'text_unit_tokens': sum(tu.values()),
    }

    # whole-manuscript label/text page split (secondary)
    lt = M.label_text_by_page(pages)
    la = [w for v in lt.values() for w in v['labels']]
    ta = [w for v in lt.values() for w in v['text']]
    lu2 = Counter(u for w in la for u in M.bpe_apply(w))
    tu2 = Counter(u for w in ta for u in M.bpe_apply(w))
    r['all_pages_with_both'] = {
        'n_pages': len(lt), 'n_label_tokens': len(la), 'n_text_tokens': len(ta),
        'n_distinct_glyph_units_labels': len(lu2),
        'n_distinct_glyph_units_text': len(tu2),
        'n_shared': len(set(lu2) & set(tu2)),
        'units_only_in_labels': sorted(set(lu2) - set(tu2)),
        'units_only_in_text': sorted(set(tu2) - set(lu2)),
    }

    # TTR against 1000 length-matched resamples of running text, same pages
    r['ttr_resample'] = ttr_resample(lab_words_by_page, txt_words_by_page)
    return r


def ttr_resample(lab_by_page, txt_by_page, ndraw=1000, seed=SEED):
    by_len = {}
    for pg, ws in txt_by_page.items():
        d = defaultdict(list)
        for w in ws:
            d[len(M.bpe_apply(w))].append(w)
        by_len[pg] = d
    targets = []          # (page, glyph-unit length)
    for pg, ws in lab_by_page.items():
        for w in ws:
            targets.append((pg, len(M.bpe_apply(w))))
    obs_words = [w for ws in lab_by_page.values() for w in ws]
    obs_ttr = len(set(obs_words)) / len(obs_words) if obs_words else None
    rng = random.Random(seed)
    fallbacks = 0
    plans = []
    for pg, L in targets:
        d = by_len.get(pg, {})
        if L in d and d[L]:
            plans.append(d[L])
        elif d:
            best = min(d.keys(), key=lambda k: (abs(k - L), k))
            fallbacks += 1
            plans.append(d[best])
        else:
            fallbacks += 1
            plans.append(None)
    plans = [p for p in plans if p is not None]
    ttrs = []
    for _ in range(ndraw):
        samp = [pool[rng.randrange(len(pool))] for pool in plans]
        ttrs.append(len(set(samp)) / len(samp))
    mu = statistics.fmean(ttrs)
    sd = statistics.pstdev(ttrs)
    ge = sum(1 for t in ttrs if t >= obs_ttr)
    le = sum(1 for t in ttrs if t <= obs_ttr)
    return {'label_TTR': obs_ttr, 'n_label_tokens': len(plans),
            'resample_mean_TTR': mu, 'resample_sd_TTR': sd,
            'resample_min': min(ttrs), 'resample_max': max(ttrs),
            'z': (obs_ttr - mu) / sd if sd > 0 else None,
            'p_one_sided_label_higher': (1 + ge) / (ndraw + 1.0),
            'p_one_sided_label_lower': (1 + le) / (ndraw + 1.0),
            'p_two_sided': min(1.0, 2 * min((1 + ge), (1 + le)) / (ndraw + 1.0)),
            'ndraw': ndraw, 'seed': seed,
            'exact_length_match_failures': fallbacks}


# ==================================================================== main ==

def main():
    inputs = OrderedDict()
    for k, p in (('ZL3b-n.txt', ZL3B), ('GC2a-n.txt', GC2A),
                 ('pg49513.txt', CULP), ('Latin.xml', VULG)):
        inputs[k] = {'path': p, 'sha256': M.sha256(p)}
    inputs['meaning_lib.py'] = {'path': str(HERE / 'meaning_lib.py'),
                                'sha256': M.sha256(HERE / 'meaning_lib.py')}
    inputs['PROTOCOL.md'] = {'path': str(HERE / 'PROTOCOL.md'),
                             'sha256': M.sha256(HERE / 'PROTOCOL.md')}

    say('=' * 74)
    say('Z2 / Z3  --  meaning-probes, seed %d, %d permutation draws' % (SEED, NPERM))
    say('=' * 74)
    for k, v in inputs.items():
        say('  input %-16s sha256 %s' % (k, v['sha256']))

    noise_pool = vulgate_types(VULG)
    say('  noise pool for degraded controls: %d Latin Vulgate types (len 3-12)'
        % len(noise_pool))

    pages = M.parse_pages(ZL3B)
    labels = M.zodiac_labels(pages)
    say('')
    say('ZL3b zodiac labels: %d loci over %d signs' % (len(labels),
        len({x['sign'] for x in labels})))
    ring_comments = []
    for sign, folios in M.ZODIAC_SIGNS.items():
        for fo in folios:
            p = pages.get(fo)
            if not p:
                continue
            for l in p['loci']:
                if l['type'] == 'L' and l['sub'] == 'z' and l['pos'] == '@':
                    ring_comments.append({'sign': sign, 'page': fo,
                                          'locus': l['n'],
                                          'comment': l['comment']})
    sr = M.sign_rings(labels)
    per_sign = OrderedDict((s, OrderedDict((str(r), len(v)) for r, v in rings.items()))
                           for s, rings in sr.items())
    for s, rings in per_sign.items():
        say('  %-12s rings %s  total %d' % (s, dict(rings), sum(rings.values())))

    # ---- Z2 -------------------------------------------------------------
    say('')
    say('-' * 74)
    say('Z2  same slot across signs')
    say('-' * 74)
    z2 = run_z2('ZL3b', labels, noise_pool)
    for conv in CONVENTIONS:
        say('')
        say('convention %s  (%s)' % (conv, CONV_DESC[conv]))
        for rep in REPS:
            rr = z2['conventions'][conv]['reps'][rep]
            for split in ('FIT', 'TEST'):
                d = rr[split]
                if d.get('effect') is None:
                    say('  %-4s %-5s  not defined (%s)' % (rep, split, d.get('note')))
                    continue
                say('  %-4s %-5s n=%3d  same-slot pairs %4d  same %.4f  diff %.4f  '
                    'effect %+.5f  z=%+.2f  p2=%.4f'
                    % (rep, split, d['n_items'], d['n_same_pairs'],
                       d['mean_sim_same_slot'], d['mean_sim_diff_slot'],
                       d['effect'], d['z'], d['p_two_sided']))
            ns = rr['numeral_summary']
            say('  %-4s numeral controls (clean)     median effect %+.5f  '
                'power(p<0.01) %.2f' % (rep, ns['clean']['median_effect'],
                                        ns['clean']['frac_p_lt_0.01']))
            say('  %-4s numeral controls (30%% noise) median effect %+.5f  '
                'power(p<0.01) %.2f' % (rep, ns['degraded30']['median_effect'],
                                        ns['degraded30']['frac_p_lt_0.01']))
            g = rr['gate']
            say('  %-4s GATE: p=%.4f (<0.01? %s)   effect/control = %s (>=0.25? %s)  '
                '-> %s' % (rep, g['test_p_two_sided'], g['passes_p'],
                           ('%.3f' % g['effect_ratio_to_control'])
                           if g['effect_ratio_to_control'] is not None else 'n/a',
                           g['passes_effect'],
                           'PASS' if g['passes'] else 'FAIL'))
    for rep in REPS:
        say('')
        say('Z2 GATE (%s level): %s  conventions passing: %s' %
            (rep, 'PASS' if z2['gate_Z2'][rep]['passes'] else 'FAIL',
             z2['gate_Z2'][rep]['conventions_passing'] or 'none'))

    # ---- Z3 -------------------------------------------------------------
    say('')
    say('-' * 74)
    say('Z3  inventory')
    say('-' * 74)
    z3 = z3_inventory('ZL3b', pages, labels)
    say('  label loci                 %d' % z3['n_label_loci'])
    say('  distinct label strings     %d' % z3['n_distinct_label_strings'])
    say('  distinct/total             %.4f   (gate: < 0.5 -> %s)'
        % (z3['distinct_over_total'], 'PASS' if z3['gate_Z3_passes'] else 'FAIL'))
    say('  label word tokens/types    %d / %d  (TTR %.4f)'
        % (z3['n_label_word_tokens'], z3['n_label_word_types'], z3['label_word_TTR']))
    say('  repeated label strings     %d  (>=2 signs: %d, >=3 signs: %d, '
        'within-sign only: %d)'
        % (z3['n_repeated_strings'], z3['n_strings_shared_by_ge2_signs'],
           z3['n_strings_shared_by_ge3_signs'],
           z3['n_strings_repeated_within_sign_only']))
    say('  label word types in >=2 signs %d, >=3 signs %d'
        % (z3['n_label_word_types_in_ge2_signs'], z3['n_label_word_types_in_ge3_signs']))
    zp = z3['zodiac_pages']
    say('  zodiac pages: %d label tokens vs %d text tokens; distinct glyph units '
        '%d (labels) vs %d (text), %d shared'
        % (zp['n_label_tokens'], zp['n_text_tokens'],
           zp['n_distinct_glyph_units_labels'], zp['n_distinct_glyph_units_text'],
           zp['n_shared']))
    say('    units only in labels: %s' % (zp['units_only_in_labels'] or 'none'))
    say('    units only in text  : %s' % (zp['units_only_in_text'] or 'none'))
    ap = z3['all_pages_with_both']
    say('  all %d pages with both: %d vs %d tokens; units %d vs %d, %d shared'
        % (ap['n_pages'], ap['n_label_tokens'], ap['n_text_tokens'],
           ap['n_distinct_glyph_units_labels'], ap['n_distinct_glyph_units_text'],
           ap['n_shared']))
    t = z3['ttr_resample']
    say('  label TTR %.4f vs length-matched running text %.4f +- %.4f  '
        '(z=%+.2f, p2=%.4f, %d draws, %d exact-length misses)'
        % (t['label_TTR'], t['resample_mean_TTR'], t['resample_sd_TTR'],
           t['z'], t['p_two_sided'], t['ndraw'], t['exact_length_match_failures']))
    say('  repeated label strings, full list:')
    for x in z3['repeated_label_strings']:
        say('    %-22s x%d  %-18s %s' % (
            x['string'], x['count'], x['scope'],
            ', '.join('%s/%s#%d' % (o['sign'], o['page'], o['locus'])
                      for o in x['occurrences'])))

    # ---- replication ----------------------------------------------------
    say('')
    say('-' * 74)
    say('Replication on GC2a-n.txt')
    say('-' * 74)
    gpages = M.parse_pages(GC2A)
    glabels = M.zodiac_labels(gpages)
    cov = len(glabels) / len(labels)
    say('  GC2a zodiac label loci surviving the frozen clean parser: %d '
        '(%.1f%% of the %d in ZL3b)' % (len(glabels), 100 * cov, len(labels)))
    say('  GC2a labels carrying a clock annotation: %d -> convention C is empty'
        % sum(1 for x in glabels if x['clock']))
    say('  CAUSE: the clean parser drops any token containing a digit; GC2a is')
    say('  written in a v101-family alphabet that uses digits as glyphs. The')
    say('  surviving subset is the digit-free tail, not a random sample. The')
    say('  replication below is reported but is NOT evidence in either direction.')
    z2g = run_z2('GC2a', glabels, noise_pool)
    for conv in CONVENTIONS:
        for rep in REPS:
            rr = z2g['conventions'][conv]['reps'][rep]
            d = rr['TEST']
            if d.get('effect') is None:
                say('  conv %s %-4s TEST: not defined (%s)' % (conv, rep, d.get('note')))
            else:
                say('  conv %s %-4s TEST: n=%d same-slot pairs %d effect %+.5f p2=%.4f'
                    % (conv, rep, d['n_items'], d['n_same_pairs'], d['effect'],
                       d['p_two_sided']))
    z3g = z3_inventory('GC2a', gpages, glabels)
    say('  GC2a Z3: %d loci, %d distinct, distinct/total %.4f -> gate %s'
        % (z3g['n_label_loci'], z3g['n_distinct_label_strings'],
           z3g['distinct_over_total'],
           'PASS' if z3g['gate_Z3_passes'] else 'FAIL'))

    # ---- verdicts -------------------------------------------------------
    say('')
    say('=' * 74)
    v2 = z2['gate_Z2']['unit']
    say('GATE Z2 (glyph-unit level, primary): %s' % ('PASS' if v2['passes'] else 'FAIL'))
    say('  measured power of the test (fraction of the 8 clean numeral controls')
    say('  reaching p<0.01 at the observed TEST slot structure): %s'
        % {c: v2['measured_power_by_convention'][c] for c in CONVENTIONS})
    say('GATE Z3 (fixed inventory, distinct/total < 0.5): %s  (observed %.4f)'
        % ('PASS' if z3['gate_Z3_passes'] else 'FAIL', z3['distinct_over_total']))
    say('=' * 74)

    out = {
        'key': 'z2z3',
        'protocol': 'experiments/meaning-probes/PROTOCOL.md',
        'seed': SEED, 'nperm': NPERM,
        'inputs': inputs,
        'ambiguities_resolved': [
            'p-value two-sided (Z2 silent; Z1 says two-sided) - harder reading',
            'gate denominator = MEDIAN effect over the 8 CLEAN numeral controls '
            '(degraded controls reported for sensitivity only) - harder reading',
            'positive controls built so that same-slot identity holds under the '
            'convention being tested (numeral k at the k-th distinct slot value), '
            'maximising the control effect and so the 25% bar - harder reading',
            'numeral controls run through the identical representation pipeline '
            '(the frozen 20 BPE merges applied to the numeral strings too); raw '
            'character level reported as the protocol robustness check',
            'convention B ring rank = ring index in manuscript order, which the '
            'ZL ring comments confirm is outer-first on every zodiac folio',
            'convention C rounding is half-up: floor(minutes/30+0.5) mod 24',
            'multi-word labels concatenated into one sequence',
            'Z3 "same pages" = the twelve zodiac folios (labels Lz, text P/C/R); '
            'the whole-manuscript version also reported',
            'GC2a replication run with the frozen clean parser as-is; it keeps '
            'only 91/294 label loci and 0 clocks, and is reported as '
            'uninterpretable rather than as a failed replication',
        ],
        'zodiac_structure': {'per_sign_ring_sizes': per_sign,
                             'ring_group_comments': ring_comments,
                             'FIT_signs': M.FIT_SIGNS, 'TEST_signs': M.TEST_SIGNS},
        'Z2': z2,
        'Z3': z3,
        'replication_GC2a': {'coverage_vs_ZL3b': cov,
                             'n_label_loci': len(glabels),
                             'n_with_clock': sum(1 for x in glabels if x['clock']),
                             'Z2': z2g, 'Z3': z3g},
        'verdict': {
            'Z2_gate': 'PASS' if z2['gate_Z2']['unit']['passes'] else 'FAIL',
            'Z2_gate_char_level': 'PASS' if z2['gate_Z2']['char']['passes'] else 'FAIL',
            'Z3_gate': 'PASS' if z3['gate_Z3_passes'] else 'FAIL',
        },
    }
    (RESULTS / 'z2z3.json').write_text(json.dumps(out, indent=2, sort_keys=False,
                                                  default=str), encoding='utf-8')
    (RESULTS / 'z2z3.stdout.txt').write_text('\n'.join(OUT) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
