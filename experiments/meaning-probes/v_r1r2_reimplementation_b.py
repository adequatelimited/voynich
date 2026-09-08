#!/usr/bin/env python3
"""Decomposition of the R1(b) exact-vs-relaxed reversal + independent R2 shape."""
import json, math, random, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML

SEED, NDRAW = 408, 10000
ZL = r'R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt'
GAL3 = ['cth', 'ckh', 'cph', 'cfh']; GAL1 = ['t', 'p', 'k', 'f']


def lead_gallows(w):
    for g in GAL3:
        if w.startswith(g): return g
    for g in GAL1:
        if w.startswith(g): return g
    return None


def two_sided(obs, draws):
    n = len(draws)
    return min(1.0, 2.0 * min((sum(1 for d in draws if d >= obs - 1e-12) + 1) / (n + 1),
                              (sum(1 for d in draws if d <= obs + 1e-12) + 1) / (n + 1)))


pages = ML.parse_pages(ZL, comma_split=True)
recipes = [p for p in pages.values() if p['meta'].get('I') == 'S']
recipesB = [p for p in recipes if p['meta'].get('L') == 'B']
vocab = set(ML.all_words(recipesB))

test_ids = set(p['id'] for p in recipesB if p['fnum'] % 2 == 0)
paras = ML.paragraphs(pages, page_ids=test_ids)
openers = [d['first_word'] for d in paras if d['first_word']]
gop = [w for w in openers if lead_gallows(w)]
ctrl = [w for d in paras for i, w in enumerate(d['words']) if i and lead_gallows(w)]
buck = defaultdict(list)
for w in ctrl: buck[(lead_gallows(w), len(w))].append(w)
lb = defaultdict(list)
for w in ctrl: lb[lead_gallows(w)].append(w)


def resid(w): return w[len(lead_gallows(w)):]
def att(w):
    r = resid(w); return 1 if (r and r in vocab) else 0


def relaxed_bucket(w):
    g, L = lead_gallows(w), len(w)
    for tol in (0, 1, 2):
        c = [x for x in lb[g] if abs(len(x) - L) <= tol]
        if c: return c
    return lb[g] or ctrl


kept = [w for w in gop if buck.get((lead_gallows(w), len(w)))]
drop = [w for w in gop if not buck.get((lead_gallows(w), len(w)))]

out = {'sha256': ML.sha256(ZL), 'n_gop': len(gop), 'n_kept': len(kept), 'n_drop': len(drop)}


def run(subset, bucket_fn, tag):
    rng = random.Random(SEED)
    obs = sum(att(w) for w in subset) / len(subset)
    bk = {w: bucket_fn(w) for w in set(subset)}
    draws = []
    for _ in range(NDRAW):
        draws.append(sum(att(rng.choice(bk[w])) for w in subset) / len(subset))
    mu = sum(draws) / NDRAW
    sd = math.sqrt(sum((d - mu) ** 2 for d in draws) / (NDRAW - 1))
    out[tag] = {'n': len(subset), 'obs': obs, 'ctrl_mean': mu, 'ctrl_sd': sd,
                'sd_units': (obs - mu) / sd if sd else None, 'p': two_sided(obs, draws)}


run(kept, lambda w: buck[(lead_gallows(w), len(w))], 'kept92_EXACTctrl')
run(kept, relaxed_bucket, 'kept92_RELAXEDctrl')      # isolates control relaxation
run(gop, relaxed_bucket, 'all120_RELAXEDctrl')       # the reported supplementary
run(drop, relaxed_bucket, 'drop28_RELAXEDctrl')      # the unmatchable tail alone

# is attestation length-dependent in the control pool?  If yes, relaxed matching
# of a long opener against shorter controls is biased.
by_len = defaultdict(list)
for w in ctrl: by_len[len(w)].append(att(w))
out['ctrl_attest_by_len'] = {str(L): {'n': len(v), 'rate': sum(v) / len(v)}
                             for L, v in sorted(by_len.items())}
out['opener_attest_by_len'] = {}
bl = defaultdict(list)
for w in gop: bl[len(w)].append(att(w))
out['opener_attest_by_len'] = {str(L): {'n': len(v), 'rate': sum(v) / len(v)}
                               for L, v in sorted(bl.items())}
out['drop_lengths'] = sorted(Counter(len(w) for w in drop).items())
# mean length of the relaxed controls actually available to the dropped openers
mlen = {}
for w in set(drop):
    c = relaxed_bucket(w)
    mlen[w] = {'len': len(w), 'ctrl_mean_len': sum(len(x) for x in c) / len(c),
               'ctrl_attest': sum(att(x) for x in c) / len(c)}
out['drop_relaxed_ctrl_detail'] = mlen

# ---------------------------------------------------------------- R2 shape
star_paras_all = [d for d in ML.paragraphs(pages, illus='S') if d['star']]
even = [d for d in star_paras_all if int(d['page'][1:].rstrip('rv0123456789') or 0) or True]
def fnum(pid):
    import re; return int(re.match(r'f(\d+)', pid).group(1))
test_star = [d for d in star_paras_all if fnum(d['page']) % 2 == 0]
out['R2'] = {'n_star_all': len(star_paras_all), 'n_star_TEST_even': len(test_star),
             'n_star_TEST_from_f58': sum(1 for d in test_star if d['page'].startswith('f58')),
             'points_dist': dict(Counter(d['star']['points'] for d in star_paras_all)),
             'tail_by_page_TEST': {}}
pg = defaultdict(list)
for d in test_star: pg[d['page']].append(1 if d['star']['tail'] else 0)
out['R2']['tail_by_page_TEST'] = {k: (len(v), sum(v)) for k, v in sorted(pg.items())}
out['R2']['n_pages_all_or_nothing_tail'] = sum(1 for v in pg.values() if sum(v) in (0, len(v)))
out['R2']['n_pages_TEST'] = len(pg)

Path('results').mkdir(exist_ok=True)
Path('results/v_r1r2_reimpl_b.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
print(json.dumps(out, indent=1))
