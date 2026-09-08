#!/usr/bin/env python3
"""Why does R1(b) flip sign between length-only and gallows+length matching?"""
import sys, json
from collections import defaultdict, Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML
ZL = r'R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt'
GAL3 = ['cth', 'ckh', 'cph', 'cfh']; GAL1 = ['t', 'p', 'k', 'f']
def lg(w):
    for g in GAL3:
        if w.startswith(g): return g
    for g in GAL1:
        if w.startswith(g): return g
    return None
pages = ML.parse_pages(ZL, comma_split=True)
recipesB = [p for p in pages.values() if p['meta'].get('I') == 'S' and p['meta'].get('L') == 'B']
vocab = set(ML.all_words(recipesB))
def att(w):
    r = w[len(lg(w)):]; return 1 if (r and r in vocab) else 0
for name, pgs in [('TEST_even', [p for p in recipesB if p['fnum'] % 2 == 0]),
                  ('FIT_odd', [p for p in recipesB if p['fnum'] % 2 == 1]),
                  ('ALL', recipesB)]:
    ids = set(p['id'] for p in pgs)
    paras = ML.paragraphs(pages, page_ids=ids)
    gop = [d['first_word'] for d in paras if d['first_word'] and lg(d['first_word'])]
    ctrl = [w for d in paras for i, w in enumerate(d['words']) if i and lg(w)]
    print('=== %s   openers=%d  controls=%d' % (name, len(gop), len(ctrl)))
    print('  mean opener len %.2f   mean control len %.2f' % (
        sum(len(w) for w in gop)/len(gop), sum(len(w) for w in ctrl)/len(ctrl)))
    o = defaultdict(list); c = defaultdict(list)
    for w in gop: o[lg(w)].append(att(w))
    for w in ctrl: c[lg(w)].append(att(w))
    print('  gallows | opener n/rate | control n/rate | ctrl mean len')
    for g in sorted(set(o) | set(c)):
        cl = [len(w) for w in ctrl if lg(w) == g]
        print('   %-4s | %3d %s | %3d %s | %s' % (
            g, len(o.get(g, [])), ('%.3f' % (sum(o[g])/len(o[g]))) if o.get(g) else '  -  ',
            len(c.get(g, [])), ('%.3f' % (sum(c[g])/len(c[g]))) if c.get(g) else '  -  ',
            ('%.2f' % (sum(cl)/len(cl))) if cl else '-'))
    print()
