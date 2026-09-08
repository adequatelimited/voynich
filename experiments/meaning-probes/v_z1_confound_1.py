#!/usr/bin/env python3
"""v_z1_confound_1.py -- adversarial CONFOUND audit of Z1, part 1: the data.

Questions asked here (no statistics yet, just what the rings actually are):
  1. Ring segmentation: does meaning_lib's '@' rule reproduce the ZL comments
     (outer / inner / central)?  How many Lz loci per ring block, and how many
     are dropped for having no clean token?
  2. Ring ORDER: the whole test depends on idx_in_ring being manuscript ring
     order.  ZL records a clock position for many zodiac labels.  Does locus
     order agree with clock order?  If not, the 'gap' variable is wrong.
  3. Dropped loci: does dropping correlate with position in the ring, and does
     it contract gaps (a dropped locus makes a true g=2 pair look like g=1)?
  4. Label geometry: glyph-unit length, char length, words per locus, alphabet
     size -- against the numeral controls the power claim rests on.
  5. Page-level confounds: hand ($H), Currier language ($L), section for every
     zodiac page.
"""
import re, sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML

HERE = Path(__file__).resolve().parent
ZL3B = HERE / '..' / '..' / 'data' / 'corpora' / 'ZL3b-n.txt'

pages = ML.parse_pages(str(ZL3B), comma_split=True)

print('sha256 ZL3b  ', ML.sha256(str(ZL3B)))
print('sha256 lib   ', ML.sha256(str(HERE / 'meaning_lib.py')))
print()

# ---------------------------------------------------------------- 5. pages --
print('=== zodiac page metadata (hand / language / illustration) ===')
for sign, folios in ML.ZODIAC_SIGNS.items():
    for fo in folios:
        p = pages.get(fo)
        if p is None:
            print('  %-12s %-8s MISSING' % (sign, fo)); continue
        m = p['meta']
        print('  %-12s %-8s $I=%s $L=%s $H=%s $Q=%s  loci=%d' %
              (sign, fo, m.get('I'), m.get('L'), m.get('H'), m.get('Q'),
               len(p['loci'])))
print()

# ------------------------------------------- 1/3. rings, drops, ZL comments --
print('=== ring blocks as meaning_lib segments them (all 10 signs) ===')
print('  sign / folio / ring : kept  dropped  | ZL comment on first locus')
rows = []
for sign, folios in ML.ZODIAC_SIGNS.items():
    ring = -1
    for fo in folios:
        p = pages.get(fo)
        if p is None:
            continue
        blocks = []
        for l in p['loci']:
            if l['type'] != 'L' or l['sub'] != 'z':
                continue
            if l['pos'] == '@' or not blocks:
                blocks.append([])
            blocks[-1].append(l)
        for b in blocks:
            ring += 1
            kept = [l for l in b if l['words']]
            drop = [l for l in b if not l['words']]
            drop_pos = []
            for i, l in enumerate(b):
                if not l['words']:
                    drop_pos.append(i)
            rows.append((sign, fo, ring, len(kept), len(drop), drop_pos,
                         b[0]['comment']))
            print('  %-12s %-7s r%-2d : %3d  %3d %-18s | %s' %
                  (sign, fo, ring, len(kept), len(drop),
                   ('drop@' + ','.join(map(str, drop_pos))) if drop_pos else '',
                   (b[0]['comment'] or '')[:60]))
print()

TEST = set(ML.TEST_SIGNS)
tot_drop = sum(r[4] for r in rows if r[0] in TEST)
tot_keep = sum(r[3] for r in rows if r[0] in TEST)
print('  TEST signs: %d loci kept, %d dropped for having no clean [a-z]+ token'
      % (tot_keep, tot_drop))
print('  Every dropped locus CONTRACTS the gaps of all later pairs in its ring:')
print('  a true gap-2 pair spanning a dropped locus is scored as gap 1.')
print()

# ------------------------------------------------------------- 2. ordering --
labels = ML.zodiac_labels(pages)
by = ML.sign_rings(labels)
print('=== ring ORDER: does locus order agree with the ZL clock position? ===')
print('  sign / ring : n  n_with_clock  monotone_in_clock?  clock sequence')
bad = 0
for sign in ML.ZODIAC_SIGNS:
    for ring, recs in by.get(sign, {}).items():
        cl = [r['clock_min'] for r in recs]
        have = [c for c in cl if c is not None]
        mono = 'n/a'
        if len(have) >= 3:
            # circular monotone check: at most one descent going round
            desc = sum(1 for a, b in zip(have, have[1:]) if b < a)
            mono = 'YES' if desc <= 1 else 'NO(%d descents)' % desc
            if desc > 1:
                bad += 1
        star = '  <<<' if mono.startswith('NO') else ''
        print('  %-12s r%-2d : %2d  %2d  %-16s %s%s' %
              (sign, ring, len(recs), len(have), mono,
               ','.join(r['clock'] or '--' for r in recs)[:70], star))
print('  rings whose locus order is NOT monotone in clock: %d' % bad)
print()

# --------------------------------------------------------- 4. label geometry --
def geom(seqs, name):
    L = [len(s) for s in seqs]
    alpha = set()
    for s in seqs:
        alpha.update(s)
    print('  %-28s n=%3d  len mean=%.2f min=%d max=%d  alphabet=%d' %
          (name, len(L), sum(L) / len(L), min(L), max(L), len(alpha)))
    return L, alpha


def seq_of_words(words, level):
    out = []
    for w in words:
        out.extend(ML.bpe_apply(w) if level == 'units' else list(w))
    return out


print('=== label geometry vs the numeral controls the power claim uses ===')
test_recs = [r for r in labels if r['sign'] in TEST]
test_recs = [r for r in test_recs
             if len(by[r['sign']][r['ring']]) >= 8]
geom([seq_of_words(r['words'], 'units') for r in test_recs],
     'Voynich TEST (glyph units)')
geom([seq_of_words(r['words'], 'chars') for r in test_recs],
     'Voynich TEST (raw chars)')
for name, series in ML.numeral_controls().items():
    geom([list(w) for w in series], 'numeral: ' + name)
print()
print('  words per label locus (TEST):',
      dict(sorted(Counter(r['n_words'] for r in test_recs).items())))
print('  distinct label strings (TEST): %d of %d'
      % (len(set(r['text'] for r in test_recs)), len(test_recs)))
print()

# how much of the ring is a single repeated string?
print('=== most repeated TEST label strings ===')
for s, c in Counter(r['text'] for r in test_recs).most_common(6):
    print('  %-28s x%d' % (s, c))
