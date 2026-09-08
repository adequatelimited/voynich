#!/usr/bin/env python3
"""Smoke test for meaning_lib: structural counts only, no statistics."""
import sys
from collections import Counter
sys.path.insert(0, '.')
import meaning_lib as ML

CORPUS = sys.argv[1] if len(sys.argv) > 1 else '../../data/corpora/ZL3b-n.txt'
pages = ML.parse_pages(CORPUS)
print('sha256', ML.sha256(CORPUS))
print('pages', len(pages))

lab = ML.zodiac_labels(pages)
print('zodiac label loci with words:', len(lab))
for s in ML.ZODIAC_SIGNS:
    rs = [r for r in lab if r['sign'] == s]
    rings = Counter(r['ring'] for r in rs)
    print(f'  {s:12s} n={len(rs):3d} rings={[rings[k] for k in sorted(rings)]}')
types = Counter(r['text'] for r in lab)
print('distinct label strings:', len(types), 'of', len(lab))
print('top repeated:', types.most_common(8))

pars = ML.paragraphs(pages, illus='S')
print('recipe paragraphs:', len(pars))
stars = [p['star'] for p in pars if p['star']]
print('  with star comment:', len(stars),
      'points hist:', Counter(s['points'] for s in stars))
print('  first words:', [p['first_word'] for p in pars[:8]])

ni = ML.non_initial_line_words(pages, illus='S')
print('recipe non-initial line-first words:', len(ni))

lt = ML.label_text_by_page(pages)
print('pages with both labels and text:', len(lt),
      'label tokens', sum(len(v['labels']) for v in lt.values()),
      'text tokens', sum(len(v['text']) for v in lt.values()))

print('bpe:', [ML.bpe_apply(w) for w in ['daiin', 'chedy', 'qokeedy', 'otalar', 'okaram']])
print('lcs_sim otalar/otalam:', round(ML.lcs_sim(ML.bpe_apply('otalar'), ML.bpe_apply('otalam')), 3))
print('numeral controls:', {k: v[:4] for k, v in ML.numeral_controls().items()})
