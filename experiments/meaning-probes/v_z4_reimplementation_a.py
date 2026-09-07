#!/usr/bin/env python3
"""v_z4_reimplementation_a.py -- INDEPENDENT reimplementation of Z4 from PROTOCOL.md.

Written without reading t_z4.py. Stdlib only. Seed 408. 10,000 draws.

Protocol Z4 (verbatim):
  Statistic. Mutual information between position and form:
  positions = {rank block 1-10 / 11-20 / 21-30 within sign} x {thirds of the ring},
  forms = {first glyph unit} x {last glyph unit}. Four combinations.
  Null. 10,000 permutations of rank within sign / within ring.
  Gate Z4. Any MI with permutation p < 0.01 after Bonferroni over the four
  combinations is reported as positional structure. Otherwise: none.

Ambiguity readings taken (harder-to-pass reading chosen):
  * Bonferroni denominator: protocol literally says four combinations -> 0.0025.
    The registered run used a six-member family (4 MI + 2 chi-square) -> 0.0016667.
    I report BOTH and use 0.0016667 (harder) as the primary threshold.
  * p is one-sided upper tail on MI (structure can only raise MI); computed as
    (#{null >= obs} + 1) / (B + 1), the conservative add-one form. The plain
    count/B form is also reported.
  * Label with several words: first glyph unit = first unit of first word;
    last glyph unit = last unit of last word.
  * Gate is evaluated on the TEST signs (Leo, Virgo, Libra, Scorpius, Sagittarius).
"""
import json, math, random, sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML

REPO = Path('R:/Coding/LinearA/tmp/voynich_repo')
ZL = REPO / 'data/corpora/ZL3b-n.txt'
GC = REPO / 'data/corpora/GC2a-n.txt'
B = 10000
SEED = 408


# ------------------------------------------------------------------ helpers --
def mutual_information(xs, ys):
    n = len(xs)
    if n == 0:
        return 0.0
    joint = Counter(zip(xs, ys))
    mx = Counter(xs)
    my = Counter(ys)
    mi = 0.0
    for (x, y), c in joint.items():
        pxy = c / n
        mi += pxy * math.log2(pxy / ((mx[x] / n) * (my[y] / n)))
    return mi


def chisq(xs, ys):
    n = len(xs)
    if n == 0:
        return 0.0
    joint = Counter(zip(xs, ys))
    mx = Counter(xs)
    my = Counter(ys)
    tot = 0.0
    for x in mx:
        for y in my:
            e = mx[x] * my[y] / n
            o = joint.get((x, y), 0)
            tot += (o - e) ** 2 / e
    return tot


def build_records(path, comma_split=True, level='unit'):
    pages = ML.parse_pages(path, comma_split=comma_split)
    labels = ML.zodiac_labels(pages, comma_split=comma_split)
    # ring sizes per (sign, ring)
    ring_sizes = Counter((r['sign'], r['ring']) for r in labels)
    recs = []
    for r in labels:
        words = r['words']
        if level == 'unit':
            first_units = ML.bpe_apply(words[0])
            last_units = ML.bpe_apply(words[-1])
            first = first_units[0]
            last = last_units[-1]
        else:
            first = words[0][0]
            last = words[-1][-1]
        n_ring = ring_sizes[(r['sign'], r['ring'])]
        third = min(2, (r['idx_in_ring'] * 3) // n_ring) if n_ring else 0
        block = min(2, r['idx_in_sign'] // 10)
        recs.append({
            'sign': r['sign'], 'ring': r['ring'],
            'idx_in_ring': r['idx_in_ring'], 'idx_in_sign': r['idx_in_sign'],
            'n_ring': n_ring,
            'third': third, 'block': block,
            'first': first, 'last': last,
            'text': r['text'],
        })
    return recs


def group_index(recs, key):
    """key -> list of record indices, in manuscript order."""
    g = OrderedDict()
    for i, r in enumerate(recs):
        g.setdefault(key(r), []).append(i)
    return g


def run_stat(recs, pos_field, form_field, stat_fn, B=B, seed=SEED):
    """Permutation test.

    Null: 'permutations of rank within sign / within ring'.
    - block  -> permute the block labels among the records of the same SIGN
    - third  -> permute the third labels among the records of the same RING
    (both are exactly permuting the record's rank/position inside its group).
    """
    if pos_field == 'block':
        groups = group_index(recs, lambda r: r['sign'])
    else:
        groups = group_index(recs, lambda r: (r['sign'], r['ring']))
    pos = [r[pos_field] for r in recs]
    form = [r[form_field] for r in recs]
    obs = stat_fn(pos, form)
    rng = random.Random(seed)
    null = []
    work = list(pos)
    for _ in range(B):
        for idxs in groups.values():
            vals = [pos[i] for i in idxs]
            rng.shuffle(vals)
            for i, v in zip(idxs, vals):
                work[i] = v
        null.append(stat_fn(work, form))
    ge = sum(1 for v in null if v >= obs - 1e-12)
    mean = sum(null) / len(null)
    var = sum((v - mean) ** 2 for v in null) / (len(null) - 1)
    return {
        'observed': obs,
        'null_mean': mean,
        'null_sd': math.sqrt(var),
        'debiased': obs - mean,
        'p_addone': (ge + 1) / (B + 1),
        'p_plain': ge / B,
        'n_ge': ge,
    }


def marginals(recs, field):
    c = Counter(r[field] for r in recs)
    return {str(k): c[k] for k in sorted(c)}


# --------------------------------------------------------------------- main --
def main():
    out = {'test': 'z4_reimplementation_verify', 'seed': SEED, 'B': B,
           'sha256': {}, 'readings': {}}
    for name, p in [('ZL3b-n.txt', ZL), ('GC2a-n.txt', GC),
                    ('meaning_lib.py', Path(__file__).resolve().parent / 'meaning_lib.py'),
                    ('PROTOCOL.md', Path(__file__).resolve().parent / 'PROTOCOL.md')]:
        out['sha256'][name] = ML.sha256(p)

    out['readings']['bonferroni_protocol_literal_4'] = 0.01 / 4
    out['readings']['bonferroni_registered_family_6'] = 0.01 / 6
    out['readings']['p_form'] = '(count>=obs + 1)/(B+1) primary; count/B also given'
    out['readings']['split'] = {'FIT': ML.FIT_SIGNS, 'TEST': ML.TEST_SIGNS}

    recs_all = build_records(ZL, comma_split=True, level='unit')
    test = [r for r in recs_all if r['sign'] in ML.TEST_SIGNS]
    fit = [r for r in recs_all if r['sign'] in ML.FIT_SIGNS]
    out['n_labels_all'] = len(recs_all)
    out['n_labels_test'] = len(test)
    out['n_labels_fit'] = len(fit)
    out['n_rings_test'] = len(set((r['sign'], r['ring']) for r in test))
    out['n_first_types_test'] = len(set(r['first'] for r in test))
    out['n_last_types_test'] = len(set(r['last'] for r in test))
    out['marginal_block_test'] = marginals(test, 'block')
    out['marginal_third_test'] = marginals(test, 'third')

    combos = [('block', 'first'), ('block', 'last'),
              ('third', 'first'), ('third', 'last')]
    out['MI_TEST'] = {}
    for pos, form in combos:
        k = f'MI({pos};{form})'
        out['MI_TEST'][k] = run_stat(test, pos, form, mutual_information)
    out['CHI_TEST'] = {}
    for pos, form in [('block', 'first'), ('block', 'last')]:
        k = f'chi2({form} inventory x {pos})'
        out['CHI_TEST'][k] = run_stat(test, pos, form, chisq)

    out['MI_FIT'] = {}
    for pos, form in combos:
        out['MI_FIT'][f'MI({pos};{form})'] = run_stat(fit, pos, form, mutual_information)

    # robustness: raw EVA character level, TEST
    recs_raw = build_records(ZL, comma_split=True, level='raw')
    test_raw = [r for r in recs_raw if r['sign'] in ML.TEST_SIGNS]
    out['MI_TEST_rawEVA'] = {}
    for pos, form in combos:
        out['MI_TEST_rawEVA'][f'MI({pos};{form})'] = run_stat(test_raw, pos, form,
                                                             mutual_information)

    # robustness: comma_split=False, TEST, unit level
    recs_cs = build_records(ZL, comma_split=False, level='unit')
    test_cs = [r for r in recs_cs if r['sign'] in ML.TEST_SIGNS]
    out['MI_TEST_commasplit_False'] = {}
    for pos, form in combos:
        out['MI_TEST_commasplit_False'][f'MI({pos};{form})'] = run_stat(
            test_cs, pos, form, mutual_information)

    # gate evaluation
    fam6 = {}
    for k, v in out['MI_TEST'].items():
        fam6[k] = v['p_addone']
    for k, v in out['CHI_TEST'].items():
        fam6[k] = v['p_addone']
    thr6 = 0.01 / 6
    thr4 = 0.01 / 4
    out['gate'] = {
        'family6_threshold': thr6,
        'family4_threshold': thr4,
        'passers_family6': sorted(k for k, p in fam6.items() if p < thr6),
        'passers_family4_MIonly': sorted(k for k, v in out['MI_TEST'].items()
                                         if v['p_addone'] < thr4),
    }

    # seed stability of any passer at B=10000
    out['seed_stability'] = {}
    for k in out['gate']['passers_family6'] or ['MI(third;first)']:
        pos, form = ('third', 'first')
        if k.startswith('MI('):
            pos, form = k[3:-1].split(';')
        ps = []
        for s in [408, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            r = run_stat(test, pos, form, mutual_information, B=B, seed=s)
            ps.append(round(r['p_addone'], 5))
        out['seed_stability'][k] = {'seeds': [408, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                                    'p_addone': ps,
                                    'n_below_thr6': sum(1 for p in ps if p < thr6)}

    # first-unit x third contingency on TEST, for inspection
    ct = Counter((r['first'], r['third']) for r in test)
    firsts = sorted(set(r['first'] for r in test))
    out['contingency_first_x_third_TEST'] = {
        f: [ct.get((f, t), 0) for t in (0, 1, 2)] for f in firsts}

    resdir = Path(__file__).resolve().parent / 'results'
    resdir.mkdir(exist_ok=True)
    (resdir / 'v_z4_reimplementation_a.json').write_text(
        json.dumps(out, indent=2, sort_keys=True), encoding='utf-8')

    lines = []
    def P(s=''):
        lines.append(s); print(s)
    P('=== Z4 INDEPENDENT REIMPLEMENTATION (verifier) ===')
    P(f"ZL3b sha256      : {out['sha256']['ZL3b-n.txt']}")
    P(f"GC2a sha256      : {out['sha256']['GC2a-n.txt']}")
    P(f"meaning_lib sha  : {out['sha256']['meaning_lib.py']}")
    P(f"labels all/FIT/TEST: {out['n_labels_all']}/{out['n_labels_fit']}/{out['n_labels_test']}")
    P(f"rings on TEST    : {out['n_rings_test']}   first-unit types {out['n_first_types_test']}  last-unit types {out['n_last_types_test']}")
    P(f"block marginal   : {out['marginal_block_test']}")
    P(f"third marginal   : {out['marginal_third_test']}")
    P('')
    P('TEST signs, glyph-unit level, comma_split=True:')
    P(f"{'statistic':34s} {'obs':>9s} {'nullmean':>9s} {'debias':>9s} {'p+1':>9s} {'p_plain':>9s}")
    for k, v in list(out['MI_TEST'].items()) + list(out['CHI_TEST'].items()):
        P(f"{k:34s} {v['observed']:9.4f} {v['null_mean']:9.4f} {v['debiased']:+9.4f} "
          f"{v['p_addone']:9.5f} {v['p_plain']:9.5f}")
    P('')
    P(f"Bonferroni (protocol literal, 4 combos): {thr4:.7f}")
    P(f"Bonferroni (registered family of 6)    : {thr6:.7f}")
    P(f"passers, family of 6: {out['gate']['passers_family6']}")
    P(f"passers, MI-only family of 4: {out['gate']['passers_family4_MIonly']}")
    P('')
    P('FIT signs (same statistics):')
    for k, v in out['MI_FIT'].items():
        P(f"{k:34s} {v['observed']:9.4f} {v['null_mean']:9.4f} {v['debiased']:+9.4f} {v['p_addone']:9.5f}")
    P('')
    P('Robustness -- raw EVA character level, TEST:')
    for k, v in out['MI_TEST_rawEVA'].items():
        P(f"{k:34s} {v['observed']:9.4f} {v['null_mean']:9.4f} {v['debiased']:+9.4f} {v['p_addone']:9.5f}")
    P('')
    P('Robustness -- comma_split=False, TEST, units:')
    for k, v in out['MI_TEST_commasplit_False'].items():
        P(f"{k:34s} {v['observed']:9.4f} {v['null_mean']:9.4f} {v['debiased']:+9.4f} {v['p_addone']:9.5f}")
    P('')
    for k, v in out['seed_stability'].items():
        P(f"seed stability {k}: p over seeds {v['p_addone']}")
        P(f"  {v['n_below_thr6']}/11 below the 6-family threshold {thr6:.7f}")
    P('')
    P('first-unit x ring-third contingency (TEST):')
    for f, row in sorted(out['contingency_first_x_third_TEST'].items(),
                         key=lambda kv: -sum(kv[1])):
        P(f"  {f:6s} {row}")
    (resdir / 'v_z4_reimplementation_a.stdout.txt').write_text('\n'.join(lines) + '\n',
                                                               encoding='utf-8')


if __name__ == '__main__':
    main()
