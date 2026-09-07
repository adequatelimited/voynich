#!/usr/bin/env python3
"""v_z4_null-correctness_splits.py — part 4: FIT / ring>=6 cross-checks."""
import os
import sys
import math
import random
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import meaning_lib as ML
mod = {'__file__': os.path.join(HERE, 'v_z4_null-correctness_family.py')}
exec(open(os.path.join(HERE, 'v_z4_null-correctness_family.py')).read()
     .split("say('=' * 78)")[0], mod)
build, flatten, run = mod['build'], mod['flatten'], mod['run']

ZL3B = os.path.abspath(os.path.join(HERE, '..', '..', 'data', 'corpora', 'ZL3b-n.txt'))
pages = ML.parse_pages(ZL3B, comma_split=True)
lab = ML.zodiac_labels(pages, comma_split=True)

for nm, sg in (('FIT', ML.FIT_SIGNS), ('TEST', ML.TEST_SIGNS)):
    it = build([r for r in lab if r['sign'] in sg], 'unit')
    P, A, Bf, S = flatten(it, 'P2')
    r = run(P, A, S, 409, 10000, 'MI')
    print('%-5s n=%3d MI=%.4f null=%.4f deb=%+.4f z=%+.2f p2=%.5f rings=%s'
          % (nm, len(P), r['obs'], r['mean'], r['obs'] - r['mean'], r['z'],
             r['p2'], [e - s for s, e in S]))

it = build([r for r in lab if r['sign'] in ML.TEST_SIGNS], 'unit')
it6 = [x for x in it if x['sz'] >= 6]
P, A, Bf, S = flatten(it6, 'P2')
r = run(P, A, S, 409, 10000, 'MI')
print('TEST ring>=6 n=%d p2=%.7f  alpha/4=%.7f alpha/6=%.7f  -> %s under /4, %s under /6'
      % (len(P), r['p2'], 0.01 / 4, 0.01 / 6,
         'PASS' if r['p2'] < 0.0025 else 'FAIL',
         'PASS' if r['p2'] < 0.01 / 6 else 'FAIL'))
