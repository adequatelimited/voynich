#!/usr/bin/env python3
"""v_l1_confound_1.py -- descriptive composition of the L1 label/text split.

No statistics yet. Just: which pages, which sections, which locus types, which
Currier language, which hand supply the label side and the text side of L1 on
the TEST (odd folio) split, and where the q-/qok-/c-/daiin- initial contrast
and the n-final / daiin-final contrast actually live.
"""
import io, os, re, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

ZL = 'R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt'
OUT = []


def say(s=''):
    print(s)
    OUT.append(str(s))


def main():
    pages = ML.parse_pages(ZL, comma_split=True)
    lt = ML.label_text_by_page(pages)
    say('pages with both registers: %d' % len(lt))

    # ---- per page composition, with locus-type breakdown of the text side --
    say()
    say('%-8s %5s %4s %4s %6s %6s   %s' %
        ('page', 'illus', 'lang', 'hand', 'nlab', 'ntxt', 'text-locus-types / label-locus-subcodes'))
    tot = OrderedDict()
    perpage = OrderedDict()
    for pid, d in lt.items():
        p = pages[pid]
        tc, ls = Counter(), Counter()
        for l in p['loci']:
            if l['type'] == 'L':
                ls[l['type'] + (l['sub'] or '-')] += len(l['words'])
            elif l['type'] in ('P', 'C', 'R'):
                tc[l['type'] + (l['sub'] or '-')] += len(l['words'])
        par = 'ODD/TEST' if p['fnum'] % 2 else 'EVEN/FIT'
        perpage[pid] = dict(illus=p['meta'].get('I'), lang=p['meta'].get('L'),
                            hand=p['meta'].get('H'), fnum=p['fnum'], par=par,
                            nlab=len(d['labels']), ntxt=len(d['text']),
                            tc=tc, ls=ls)
        say('%-8s %5s %4s %4s %6d %6d   %s | %s' %
            (pid + ('*' if p['fnum'] % 2 else ''), p['meta'].get('I'),
             p['meta'].get('L'), p['meta'].get('H'),
             len(d['labels']), len(d['text']),
             ' '.join('%s=%d' % kv for kv in sorted(tc.items())),
             ' '.join('%s=%d' % kv for kv in sorted(ls.items()))))
    say('(* = odd folio = TEST split)')

    # ---- section totals on each split ---------------------------------------
    say()
    for par in ('ODD/TEST', 'EVEN/FIT'):
        agg = OrderedDict()
        for pid, r in perpage.items():
            if r['par'] != par:
                continue
            k = (r['illus'], r['lang'])
            a = agg.setdefault(k, [0, 0, 0])
            a[0] += 1; a[1] += r['nlab']; a[2] += r['ntxt']
        say('%s section x language composition:' % par)
        for k, a in sorted(agg.items(), key=lambda x: -x[1][1]):
            say('    illus=%-3s lang=%-3s  pages=%2d  label words=%4d  text words=%5d'
                % (k[0], k[1], a[0], a[1], a[2]))
        say()

    # ---- where the initial units live, per page ----------------------------
    def ini(w):
        u = ML.bpe_apply(w)
        return u[0] if u else None

    def fin(w):
        u = ML.bpe_apply(w)
        return u[-1] if u else None

    for pos, f, targets in (('initial', ini, ['qok', 'q', 'c', 'daiin']),
                            ('final', fin, ['n', 'daiin', 'chedy', 'eey'])):
        say('=== %s units, per-page raw counts (TEST pages only) ===' % pos)
        say('%-8s %6s %6s   %s' % ('page', 'nlab', 'ntxt',
                                   '  '.join('%s(lab/txt)' % t for t in targets)))
        gl = Counter(); gt = Counter(); nl = nt = 0
        for pid, d in lt.items():
            if pages[pid]['fnum'] % 2 == 0:
                continue
            cl = Counter(f(w) for w in d['labels'])
            ct = Counter(f(w) for w in d['text'])
            gl.update(cl); gt.update(ct)
            nl += len(d['labels']); nt += len(d['text'])
            say('%-8s %6d %6d   %s' % (pid, len(d['labels']), len(d['text']),
                '  '.join('%d/%d' % (cl.get(t, 0), ct.get(t, 0)) for t in targets)))
        say('%-8s %6d %6d   %s' % ('TOTAL', nl, nt,
            '  '.join('%d/%d' % (gl.get(t, 0), gt.get(t, 0)) for t in targets)))
        say()

    # ---- what ARE the n-final label words? ---------------------------------
    say('=== word-final "n": every word contributing, TEST pages ===')
    for pid, d in lt.items():
        if pages[pid]['fnum'] % 2 == 0:
            continue
        lw = [w for w in d['labels'] if fin(w) == 'n']
        tw = [w for w in d['text'] if fin(w) == 'n']
        if lw or tw:
            say('  %-8s labels: %s | text: %s' % (pid, lw, tw))
    say()
    say('=== word-final "daiin": TEST label words ===')
    for pid, d in lt.items():
        if pages[pid]['fnum'] % 2 == 0:
            continue
        lw = [w for w in d['labels'] if fin(w) == 'daiin']
        if lw:
            say('  %-8s %s' % (pid, lw))
    say()
    say('=== word-initial q/qok/c/daiin: TEST label words ===')
    for pid, d in lt.items():
        if pages[pid]['fnum'] % 2 == 0:
            continue
        lw = [w for w in d['labels'] if ini(w) in ('q', 'qok', 'c', 'daiin')]
        if lw:
            say('  %-8s %s' % (pid, lw))

    # ---- token vs type: how repetitive is the text side? --------------------
    say()
    say('=== repetition on each side (TEST pages) ===')
    tl, tt = [], []
    for pid, d in lt.items():
        if pages[pid]['fnum'] % 2 == 0:
            continue
        tl += d['labels']; tt += d['text']
    say('  label words: %d tokens, %d types, ttr=%.3f'
        % (len(tl), len(set(tl)), len(set(tl)) / float(len(tl))))
    say('  text  words: %d tokens, %d types, ttr=%.3f'
        % (len(tt), len(set(tt)), len(set(tt)) / float(len(tt))))
    say('  most frequent text tokens: %s' % Counter(tt).most_common(15))
    say('  most frequent label tokens: %s' % Counter(tl).most_common(10))

    with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'results', 'v_l1_confound_1.stdout.txt'),
                 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(OUT) + '\n')


if __name__ == '__main__':
    main()
