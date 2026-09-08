#!/usr/bin/env python3
"""Is the R1(b) 'no opener dropped' reversal real, or an artefact of matching
long openers to shorter controls?  Length-stratified check on every stratum."""
import json, math, random, re, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML

SEED, NDRAW = 408, 10000
ZL = r'R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt'
GAL3 = ['cth', 'ckh', 'cph', 'cfh']; GAL1 = ['t', 'p', 'k', 'f']


def lg(w):
    for g in GAL3:
        if w.startswith(g): return g
    for g in GAL1:
        if w.startswith(g): return g
    return None


pages = ML.parse_pages(ZL, comma_split=True)
recipes = [p for p in pages.values() if p['meta'].get('I') == 'S']
recipesB = [p for p in recipes if p['meta'].get('L') == 'B']
vocab = set(ML.all_words(recipesB))


def att(w):
    r = w[len(lg(w)):]
    return 1 if (r and r in vocab) else 0


def stratum(name, pgs):
    ids = set(p['id'] for p in pgs)
    paras = ML.paragraphs(pages, page_ids=ids)
    gop = [d['first_word'] for d in paras if d['first_word'] and lg(d['first_word'])]
    ctrl = [w for d in paras for i, w in enumerate(d['words']) if i and lg(w)]
    buck = defaultdict(list)
    for w in ctrl: buck[(lg(w), len(w))].append(w)
    lb = defaultdict(list)
    for w in ctrl: lb[lg(w)].append(w)

    def relaxed(w):
        g, L = lg(w), len(w)
        for tol in (0, 1, 2):
            c = [x for x in lb[g] if abs(len(x) - L) <= tol]
            if c: return c
        return lb[g] or ctrl

    kept = [w for w in gop if buck.get((lg(w), len(w)))]
    drop = [w for w in gop if not buck.get((lg(w), len(w)))]

    # how degenerate is the relaxed control for the dropped openers?
    deg = [len(set(relaxed(w))) for w in drop]

    # ---- per-length table (openers vs ALL gallows-initial controls) -----
    tab = {}
    ol = defaultdict(list); cl = defaultdict(list)
    for w in gop: ol[len(w)].append(att(w))
    for w in ctrl: cl[len(w)].append(att(w))
    for L in sorted(set(ol) | set(cl)):
        tab[L] = {'op_n': len(ol.get(L, [])), 'op_rate': (sum(ol[L]) / len(ol[L])) if ol.get(L) else None,
                  'ct_n': len(cl.get(L, [])), 'ct_rate': (sum(cl[L]) / len(cl[L])) if cl.get(L) else None}

    # ---- Mantel-Haenszel style: pool only lengths where BOTH exist ------
    # statistic = observed opener successes - expected under the control rate
    # of the same length; permutation null = relabel opener/control within length.
    strataL = [L for L in tab if tab[L]['op_n'] and tab[L]['ct_n']]
    obs_s = sum(sum(ol[L]) for L in strataL)
    n_op_s = sum(len(ol[L]) for L in strataL)
    exp_s = sum(len(ol[L]) * tab[L]['ct_rate'] for L in strataL)
    rng = random.Random(SEED)
    draws = []
    pool = {L: ol[L] + cl[L] for L in strataL}
    for _ in range(NDRAW):
        s = 0
        for L in strataL:
            p = pool[L][:]
            rng.shuffle(p)
            s += sum(p[:len(ol[L])])
        draws.append(s)
    mu = sum(draws) / NDRAW
    sd = math.sqrt(sum((d - mu) ** 2 for d in draws) / (NDRAW - 1))
    hi = (sum(1 for d in draws if d >= obs_s - 1e-9) + 1) / (NDRAW + 1)
    lo = (sum(1 for d in draws if d <= obs_s + 1e-9) + 1) / (NDRAW + 1)

    return {
        'n_gop': len(gop), 'n_kept': len(kept), 'n_drop': len(drop),
        'drop_relaxed_bucket_distinct_sizes': sorted(Counter(deg).items()),
        'n_drop_with_relaxed_bucket_under_5_distinct': sum(1 for d in deg if d < 5),
        'per_length': tab,
        'MH_length_stratified': {
            'lengths_pooled': strataL,
            'n_openers_pooled': n_op_s,
            'obs_attested': obs_s, 'expected_from_ctrl_rate': exp_s,
            'obs_rate': obs_s / n_op_s, 'exp_rate': exp_s / n_op_s,
            'null_mean': mu, 'null_sd': sd,
            'sd_units': (obs_s - mu) / sd if sd else None,
            'p_two_sided': min(1.0, 2 * min(hi, lo)),
        },
    }


out = {'sha256': ML.sha256(ZL)}
out['TEST_recipesB_even'] = stratum('t', [p for p in recipesB if p['fnum'] % 2 == 0])
out['FIT_recipesB_odd'] = stratum('f', [p for p in recipesB if p['fnum'] % 2 == 1])
out['ALL_recipesB'] = stratum('a', recipesB)

Path('results').mkdir(exist_ok=True)
Path('results/v_r1r2_reimpl_c.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
for k in ('TEST_recipesB_even', 'FIT_recipesB_odd', 'ALL_recipesB'):
    d = out[k]
    print('=== %s  gop=%d kept=%d drop=%d' % (k, d['n_gop'], d['n_kept'], d['n_drop']))
    print('  dropped openers whose relaxed bucket has <5 distinct words: %d' %
          d['n_drop_with_relaxed_bucket_under_5_distinct'],
          d['drop_relaxed_bucket_distinct_sizes'])
    print('  len | opener n/rate | control n/rate')
    for L, v in sorted(d['per_length'].items()):
        print('   %2s | %3s %s | %3s %s' % (
            L, v['op_n'], ('%.3f' % v['op_rate']) if v['op_rate'] is not None else '  -  ',
            v['ct_n'], ('%.3f' % v['ct_rate']) if v['ct_rate'] is not None else '  -  '))
    m = d['MH_length_stratified']
    print('  MH length-stratified: n=%d obs=%.4f exp=%.4f  %.2f SD  p=%.4f  (lengths %s)' % (
        m['n_openers_pooled'], m['obs_rate'], m['exp_rate'], m['sd_units'],
        m['p_two_sided'], m['lengths_pooled']))
    print()
