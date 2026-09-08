#!/usr/bin/env python3
"""Adversarial probes for Z3 (inventory) and its two reported side-findings.

Z3a  distinct/total 0.878 -- robustness to the parser readings and to the unit
     of counting (string vs word vs glyph-unit sequence).
Z3b  'labels use a strict SUBSET of the running-text glyph inventory (38 vs 40,
     0 label-only units)'.  Confound: labels are 344 tokens, text is 947.  A
     smaller sample sees fewer types by rarefaction alone.  Rarefy the text to
     the label token count and ask how remarkable 38 / 0 actually are.
Z3c  'label TTR 0.805 vs length-matched running-text resamples 0.661, z=+8.19'.
     Confound: the resample is FREQUENCY-WEIGHTED, so it inherits running
     text's repetition of its frequent words.  Repeat the resample drawing
     uniformly over the TYPES available in each page x length cell, which
     removes the frequency skew and keeps only the vocabulary-breadth question.
     Also report the ceiling on the achievable resample TTR.
"""
import sys, json, random, statistics
from collections import Counter, defaultdict, OrderedDict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import meaning_lib as M
import t_z2z3 as T

SEED = M.SEED
NDRAW = 1000
pages = M.parse_pages(T.ZL3B)
labels = M.zodiac_labels(pages)
pages_nc = M.parse_pages(T.ZL3B, comma_split=False)
labels_nc = M.zodiac_labels(pages_nc)
RES = OrderedDict()
print('input sha256 ZL3b', M.sha256(T.ZL3B), '  seed', SEED)

# ---------------------------------------------------------------- Z3a ------
print('\n== Z3a  distinct/total under every reading ==')
for tag, labs in (('comma_split=True (frozen)', labels),
                  ('comma_split=False', labels_nc)):
    strings = [x['text'] for x in labs]
    words = [w for x in labs for w in x['words']]
    useq = ['|'.join(u for w in x['words'] for u in M.bpe_apply(w)) for x in labs]
    print('  %-26s loci %d  distinct strings %d (%.4f)  words %d/%d (%.4f)  '
          'glyph-unit seqs distinct %d (%.4f)'
          % (tag, len(strings), len(set(strings)), len(set(strings)) / len(strings),
             len(set(words)), len(words), len(set(words)) / len(words),
             len(set(useq)), len(set(useq)) / len(useq)))
    RES['Z3a_' + tag] = {'distinct_over_total': len(set(strings)) / len(strings)}
# per-sign restart check: how many types would a 30-numeral restart predict?
print('  a per-sign restart of ~30 numerals over 10 signs predicts '
      'distinct/total ~= 30/294 = 0.102; observed 0.878')
bysign = defaultdict(list)
for x in labels:
    bysign[x['sign']].append(x['text'])
print('  within-sign distinct/total per sign: %s'
      % {s: round(len(set(v)) / len(v), 3) for s, v in bysign.items()})

# ---------------------------------------------------------------- Z3b ------
print('\n== Z3b  glyph-unit inventory: rarefaction confound ==')
zpages = [f for fs in M.ZODIAC_SIGNS.values() for f in fs]
lab_words = [w for x in labels for w in x['words']]
txt_words = []
for fo in zpages:
    p = pages.get(fo)
    if not p:
        continue
    for l in p['loci']:
        if l['type'] in ('P', 'C', 'R'):
            txt_words.extend(l['words'])
lab_units = [u for w in lab_words for u in M.bpe_apply(w)]
txt_units = [u for w in txt_words for u in M.bpe_apply(w)]
LU, TU = set(lab_units), set(txt_units)
print('  labels %d word tokens / %d unit tokens, %d distinct units'
      % (len(lab_words), len(lab_units), len(LU)))
print('  text   %d word tokens / %d unit tokens, %d distinct units'
      % (len(txt_words), len(txt_units), len(TU)))
print('  label-only %s   text-only %s' % (sorted(LU - TU) or 'none', sorted(TU - LU)))
rng = random.Random(SEED)
ndist, nlabonly = [], []
for _ in range(NDRAW):
    samp = rng.sample(txt_words, len(lab_words))
    su = {u for w in samp for u in M.bpe_apply(w)}
    ndist.append(len(su))
    nlabonly.append(len(su - TU))          # always 0 by construction; sanity
# the informative rarefaction: how many units does a label-sized text sample miss
missing = []
for _ in range(NDRAW):
    samp = rng.sample(txt_words, len(lab_words))
    su = {u for w in samp for u in M.bpe_apply(w)}
    missing.append(len(TU - su))
print('  text rarefied to %d word tokens: distinct units mean %.2f (sd %.2f, '
      'range %d-%d); units of the full text missed: mean %.2f'
      % (len(lab_words), statistics.fmean(ndist), statistics.pstdev(ndist),
         min(ndist), max(ndist), statistics.fmean(missing)))
print('  => at this sample size a text sample itself shows %.1f units, vs %d in '
      'the labels; the "labels are a subset" statement is a %d-unit alphabet '
      'seen twice, not a restricted register.'
      % (statistics.fmean(ndist), len(LU), len(TU)))
RES['Z3b'] = {'label_units': len(LU), 'text_units': len(TU),
              'rarefied_text_units_mean': statistics.fmean(ndist),
              'rarefied_text_units_sd': statistics.pstdev(ndist)}

# ---------------------------------------------------------------- Z3c ------
print('\n== Z3c  TTR resample: frequency-weighted vs type-uniform ==')
lab_by_page = defaultdict(list)
for x in labels:
    lab_by_page[x['page']].extend(x['words'])
txt_by_page = defaultdict(list)
for fo in zpages:
    p = pages.get(fo)
    if not p:
        continue
    for l in p['loci']:
        if l['type'] in ('P', 'C', 'R'):
            txt_by_page[fo].extend(l['words'])
by_len = {}
for pg, ws in txt_by_page.items():
    d = defaultdict(list)
    for w in ws:
        d[len(M.bpe_apply(w))].append(w)
    by_len[pg] = d
plans_tok, plans_typ = [], []
for pg, ws in lab_by_page.items():
    for w in ws:
        L = len(M.bpe_apply(w))
        d = by_len.get(pg, {})
        if not d:
            continue
        pool = d[L] if (L in d and d[L]) else d[min(d, key=lambda k: (abs(k - L), k))]
        plans_tok.append(pool)
        plans_typ.append(sorted(set(pool)))
obs = [w for ws in lab_by_page.values() for w in ws]
obs_ttr = len(set(obs)) / len(obs)


def resample(plans, seed=SEED):
    rng = random.Random(seed)
    out = []
    for _ in range(NDRAW):
        s = [p[rng.randrange(len(p))] for p in plans]
        out.append(len(set(s)) / len(s))
    return out


for tag, plans in (('frequency-weighted (the test\'s null)', plans_tok),
                   ('type-uniform (frequency skew removed)', plans_typ)):
    t = resample(plans)
    mu, sd = statistics.fmean(t), statistics.pstdev(t)
    ge = sum(1 for v in t if v >= obs_ttr)
    print('  %-38s mean TTR %.4f +- %.4f  (label %.4f, z=%+.2f, '
          'p(label higher)=%.4f)'
          % (tag, mu, sd, obs_ttr, (obs_ttr - mu) / sd, (1 + ge) / (NDRAW + 1.0)))
    RES['Z3c_' + tag] = {'mean': mu, 'sd': sd, 'z': (obs_ttr - mu) / sd,
                         'p_label_higher': (1 + ge) / (NDRAW + 1.0)}
print('  label TTR %.4f; ceiling achievable by the resample design %.4f'
      % (obs_ttr,
         sum(min(c, len(set(plans_tok[i]))) for i, c in
             [(i, 1) for i in range(len(plans_tok))]) / len(plans_tok)))

json.dump(RES, open(HERE / 'results' / '_v_z2z3_confound_4.json', 'w'),
          indent=1, default=str)
print('\nwrote results/_v_z2z3_confound_4.json')
