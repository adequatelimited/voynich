#!/usr/bin/env python3
"""Adversarial power probes for Z2.

The test's own controls place BYTE-IDENTICAL numerals at the same slot of every
synthetic sign, so 'measured power = 1.00' is power against a perfectly regular,
variation-free numbering.  Two harder power questions:

MUT  numeral controls where EVERY item is independently mutated at a
     per-character rate r (a numbering with orthographic variation).  At what r
     does the test stop firing, and what effect size does it show there?

IMP  signal implantation into the REAL Voynich labels: for a fraction f of the
     positions in signs 2..5, overwrite the label with the label occupying the
     same slot in sign 1.  Everything else -- the vocabulary, the length
     distribution, the high similarity floor -- is the manuscript's own.  The
     smallest f that reaches p < 0.01 is the smallest same-slot numbering the
     test could actually have found in this material.
"""
import sys, math, json, random, statistics
from collections import OrderedDict, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import meaning_lib as M
import t_z2z3 as T

NPERM = 2000
SEED = M.SEED
pages = M.parse_pages(T.ZL3B)
labels = M.zodiac_labels(pages)
RES = OrderedDict()
print('input sha256 ZL3b', M.sha256(T.ZL3B))
print('nperm %d, seed %d  (2000 draws resolves p to 1/2001 = 0.0005)' % (NPERM, SEED))

ALPHA = 'abcdefghiklmnopqrstuvxyz'


def mutate(s, rate, rng):
    if rate <= 0:
        return s
    return ''.join(rng.choice(ALPHA) if rng.random() < rate else c for c in s)


def build_numeral_mut(labels, signs, conv, rep, series, rate, seed=SEED):
    fn = T.REPS[rep]
    names, slotlists = [], []
    for sg in signs:
        recs = [r for r in labels if r['sign'] == sg]
        ss = [T.slot_of(r, conv) for r in recs]
        ss = [s for s in ss if s is not None]
        if ss:
            names.append(sg); slotlists.append(ss)
    if len(names) < 2:
        return None
    allslots = sorted({s for ss in slotlists for s in ss},
                      key=lambda x: (x if isinstance(x, tuple) else (x,)))
    rank = {s: i for i, s in enumerate(allslots)}
    rng = random.Random(seed + 17)
    items = []
    for ss in slotlists:
        items.append([fn([mutate(series[rank[s] % len(series)], rate, rng)])
                      for s in ss])
    return T.Design(names, slotlists, items)


print('\n' + '=' * 74)
print('PROBE 4  numeral controls with per-character mutation of EVERY item')
print('=' * 74)
numerals = M.numeral_controls()
for conv in ('A', 'C'):
    print('  convention %s, glyph-unit level' % conv)
    for rate in (0.0, 0.10, 0.20, 0.30, 0.40, 0.50):
        effs, ps = [], []
        for nm, series in numerals.items():
            d = build_numeral_mut(labels, M.TEST_SIGNS, conv, 'unit', series, rate)
            r = d.run(NPERM, SEED)
            effs.append(r['effect']); ps.append(r['p_two_sided'])
        med = statistics.median(effs)
        frac = sum(1 for p in ps if p < 0.01) / len(ps)
        RES['MUT_%s_%.2f' % (conv, rate)] = {'median_effect': med,
                                             'frac_p_lt_0.01': frac,
                                             'effects': effs, 'ps': ps}
        print('    mutation rate %.0f%%  median effect %+.5f  min %+.5f  max %+.5f  '
              'power(p<0.01) %.2f' % (100 * rate, med, min(effs), max(effs), frac))

print('\n' + '=' * 74)
print('PROBE 5  signal implantation into the real Voynich TEST labels')
print('=' * 74)


def build_implant(labels, signs, conv, rep, f, seed=SEED):
    fn = T.REPS[rep]
    recs_by_sign = OrderedDict()
    for sg in signs:
        rs = [r for r in labels if r['sign'] == sg and T.slot_of(r, conv) is not None]
        if rs:
            recs_by_sign[sg] = rs
    names = list(recs_by_sign)
    donor = names[0]
    donor_by_slot = {}
    for r in recs_by_sign[donor]:
        donor_by_slot.setdefault(T.slot_of(r, conv), r['words'])
    rng = random.Random(seed + 99)
    slots, items, nimp = [], [], 0
    for sg in names:
        ss, ii = [], []
        for r in recs_by_sign[sg]:
            s = T.slot_of(r, conv)
            w = r['words']
            if sg != donor and s in donor_by_slot and rng.random() < f:
                w = donor_by_slot[s]; nimp += 1
            ss.append(s); ii.append(fn(w))
        slots.append(ss); items.append(ii)
    return T.Design(names, slots, items), nimp


for conv in ('A', 'C'):
    print('  convention %s, glyph-unit level  (observed manuscript effect %s)'
          % (conv, {'A': '-0.00498', 'C': '+0.01601'}[conv]))
    for f in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50):
        d, nimp = build_implant(labels, M.TEST_SIGNS, conv, 'unit', f)
        r = d.run(NPERM, SEED)
        RES['IMP_%s_%.2f' % (conv, f)] = {'f': f, 'n_implanted': nimp,
                                          'effect': r['effect'],
                                          'p_two_sided': r['p_two_sided'],
                                          'z': r['z']}
        print('    f=%.2f  %3d labels overwritten  effect %+.5f  z=%+.2f  p2=%.4f  %s'
              % (f, nimp, r['effect'], r['z'], r['p_two_sided'],
                 'FIRES' if r['p_two_sided'] < 0.01 else '.'))

json.dump(RES, open(HERE / 'results' / '_v_z2z3_confound_3.json', 'w'),
          indent=1, default=str)
print('\nwrote results/_v_z2z3_confound_3.json')
