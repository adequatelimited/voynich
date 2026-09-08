#!/usr/bin/env python3
"""v_l1_confound_3.py -- two remaining confound probes for L1.

D1  Fully SYMMETRIC position control: label side = first word of each L locus,
    text side = first word of each P/C/R locus. Both registers are then measured
    at exactly the same position (locus-initial), so nothing in the contrast can
    be a position-in-line effect.

D2  Merge-artefact x position: the same locus-initial position control at RAW
    EVA CHARACTER level. t_l1 reports that at character level only 'q' initial
    survives; if that survivor is itself a position effect, then nothing in the
    word-initial family survives independently of the frozen 20-merge list.

D3  Is the qok- deficit a 'qok' fact or an 'any long frequent B-word' fact?
    Recompute the word-initial family with the text side restricted to text
    TYPES that occur exactly once on their page (hapax-on-page), which removes
    the frequency channel entirely.

Same estimator (imported from t_l1), same seed, same 10,000 permutations.
"""
import io, json, os, sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import meaning_lib as ML
import t_l1 as T
import v_l1_confound_2 as V2

ZL = T.ZL
OUT = []
NPERM = int(os.environ.get('L1_NPERM', '10000'))


def say(s=''):
    print(s)
    OUT.append(str(s))


def first_word_registers(pages):
    out = OrderedDict()
    for p in pages.values():
        lab, txt = [], []
        for l in p['loci']:
            if not l['words']:
                continue
            if l['type'] == 'L':
                lab.append(l['words'][0])
            elif l['type'] in ('P', 'C', 'R'):
                txt.append(l['words'][0])
        if lab and txt:
            out[p['id']] = {'labels': lab, 'text': txt,
                            'illus': p['meta'].get('I'), 'lang': p['meta'].get('L')}
    return out


def hapax_text_registers(pages):
    """Text side = only those text word tokens whose type occurs exactly once
    on that page. Label side unchanged."""
    out = OrderedDict()
    for p in pages.values():
        lab, txt = [], []
        for l in p['loci']:
            if l['type'] == 'L':
                lab.extend(l['words'])
            elif l['type'] in ('P', 'C', 'R'):
                txt.extend(l['words'])
        c = Counter(txt)
        txt = [w for w in txt if c[w] == 1]
        if lab and txt:
            out[p['id']] = {'labels': lab, 'text': txt,
                            'illus': p['meta'].get('I'), 'lang': p['meta'].get('L')}
    return out


def main():
    res = OrderedDict([('verifier', 'v_l1_confound_3'), ('seed', ML.SEED),
                       ('n_permutations', NPERM),
                       ('inputs', OrderedDict([
                           ('ZL3b-n.txt', ML.sha256(ZL)),
                           ('meaning_lib.py', ML.sha256(HERE + '/meaning_lib.py')),
                           ('t_l1.py', ML.sha256(HERE + '/t_l1.py')),
                           ('results/l1.json',
                            ML.sha256(HERE + '/results/l1.json'))]))])
    for k, v in res['inputs'].items():
        say('  sha256 %-18s %s' % (k, v))
    say()

    pages = ML.parse_pages(ZL, comma_split=True)
    words_all = ML.all_words(pages)
    ug, uc = {}, {}
    for pos in ('final', 'initial'):
        ug[pos], _ = T.top_k_units(words_all, T.seg_glyph, pos)
        uc[pos], _ = T.top_k_units(words_all, T.seg_char, pos)

    lt_first = first_word_registers(pages)
    lt_hapax = hapax_text_registers(pages)
    lt_full = V2.page_registers(pages)

    grp_first = V2.groups_from(pages, lt_first)
    grp_hapax = V2.groups_from(pages, lt_hapax)
    grp_full = V2.groups_from(pages, lt_full)

    res['runs'] = []

    def go(tag, grp, units, seg, pos):
        strata = T.build_strata(grp, units, seg, pos)
        f = T.Family('%s|%s' % (tag, pos), units, strata)
        f.observed()
        f.permute(nperm=NPERM, seed=ML.SEED)
        m = f.meta()
        say('--- %s [%s]' % (tag, pos))
        say('    strata=%d label=%d text=%d pooled mean|lo|=%.4f  passers(|lo|>=1 '
            '& bonf p<.01)=%d' % (m['n_strata'], m['n_label_words_matched'],
                                  m['n_text_words_matched'],
                                  m['pooled_effect_mean_abs_logodds'],
                                  m['n_units_passing']))
        rows = f.rows()
        say('    passers: %s' % (', '.join(r['unit'] for r in rows
                                           if r['passes_unit_test']) or '(none)'))
        watch = (['qok', 'q', 'c', 'daiin', 'ot'] if pos == 'initial'
                 else ['n', 'daiin', 'chedy', 'eey', 'in'])
        if seg is T.seg_char:
            watch = ['q', 'c', 'd', 'o', 's', 'y', 'a'] if pos == 'initial' \
                else ['y', 'n', 'l', 'r', 's', 'm']
        for r in rows:
            if r['unit'] in watch:
                say('      %-6s lo=%7.3f  bonf p=%8.5f  lab=%4d txt=%5d '
                    ' strata=%3d %s' % (r['unit'], r['log_odds'],
                                        r['p_bonferroni'],
                                        r['n_label_words_with_unit'],
                                        r['n_text_words_with_unit'],
                                        r['n_informative_strata'],
                                        'PASS' if r['passes_unit_test'] else ''))
        say()
        res['runs'].append(OrderedDict([
            ('tag', tag), ('pos', pos), ('meta', m),
            ('passers', [r['unit'] for r in rows if r['passes_unit_test']]),
            ('watch', [r for r in rows if r['unit'] in watch])]))
        return f

    say('=' * 78)
    say('D1 SYMMETRIC position control: first word of every locus, both sides')
    say('    pages=%d label tokens=%d text tokens=%d'
        % (len(grp_first), sum(len(g[1]) for g in grp_first),
           sum(len(g[2]) for g in grp_first)))
    say('=' * 78)
    for pos in ('final', 'initial'):
        go('D1 symmetric first-word', grp_first, ug[pos], T.seg_glyph, pos)

    say('=' * 78)
    say('D2 RAW EVA CHARACTER level: baseline vs the same symmetric position '
        'control')
    say('=' * 78)
    for pos in ('initial', 'final'):
        go('D2a rawchar baseline', grp_full, uc[pos], T.seg_char, pos)
        go('D2b rawchar symmetric first-word', grp_first, uc[pos], T.seg_char, pos)

    say('=' * 78)
    say('D3 text side = page-hapax tokens only (frequency channel removed)')
    say('    pages=%d label tokens=%d text tokens=%d'
        % (len(grp_hapax), sum(len(g[1]) for g in grp_hapax),
           sum(len(g[2]) for g in grp_hapax)))
    say('=' * 78)
    for pos in ('final', 'initial'):
        go('D3 page-hapax text', grp_hapax, ug[pos], T.seg_glyph, pos)

    with io.open(HERE + '/results/v_l1_confound_3.json', 'w',
                 encoding='utf-8') as fh:
        fh.write(json.dumps(res, indent=2, ensure_ascii=False))
    with io.open(HERE + '/results/v_l1_confound_3.stdout.txt', 'w',
                 encoding='utf-8') as fh:
        fh.write('\n'.join(OUT) + '\n')


if __name__ == '__main__':
    main()
