#!/usr/bin/env python3
"""v_l1_confound_2.py -- adversarial confound battery for L1.

Reuses t_l1's own Family estimator verbatim (imported, not reimplemented) so
that every difference below is attributable to the DESIGN change, not to a
different statistic. Same seed (408), same 10,000 permutations, same K=25
frozen unit list (top-25 by frequency over all ZL3b word tokens).

Variants, all on the TEST split (odd folios), glyph-unit level:

  C1  baseline                       reproduce t_l1
  C2  text = locus-INITIAL words     labels are isolated one-word loci; every
                                     label is "line-initial". If the contrast is
                                     a position-in-line effect it dies here.
  C3  TYPE level (dedupe per page)   the text side has ttr 0.366 vs the label
                                     side's 0.786 and its top types are qok-
                                     words. Is the effect lexical or burstiness?
  C4  text = P loci only             drops circular/radial "text" (Cc, Ro, Ri),
                                     which is itself label-like list material.
  C5  drop illus=B pages             6 biological pages supply 319 of the 438
                                     qok-initial text tokens on 67 label words.
  C6  drop illus in {Z,A,C}          the nymph-label pages.
  C7  match on CHARACTER length      unit-length matching is not char-length
      (feature still glyph units)    matching; 'qok' costs 3 characters, and
                                     label words are short. Decouples the two.

Also, with no permutation: leave-one-page-out on the observed log-odds for
every unit that passes the gate leg in t_l1.
"""
import io, json, math, os, sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import meaning_lib as ML
import t_l1 as T

ZL = T.ZL
OUT = []
NPERM = int(os.environ.get('L1_NPERM', '10000'))


def say(s=''):
    print(s)
    OUT.append(str(s))


# ------------------------------------------------------------- group builders
def page_registers(pages, text_locus_types=('P', 'C', 'R'), locus_initial_only=False):
    """Per page: label words, text words, under a restricted definition of the
    text side. Mirrors ML.label_text_by_page but with switches."""
    out = OrderedDict()
    for p in pages.values():
        lab, txt = [], []
        for l in p['loci']:
            if l['type'] == 'L':
                lab.extend(l['words'])
            elif l['type'] in text_locus_types:
                if locus_initial_only:
                    if l['words']:
                        txt.append(l['words'][0])
                else:
                    txt.extend(l['words'])
        if lab and txt:
            out[p['id']] = {'labels': lab, 'text': txt,
                            'illus': p['meta'].get('I'),
                            'lang': p['meta'].get('L')}
    return out


def groups_from(pages, lt, parity='odd', drop_illus=(), dedupe=False):
    g = []
    for pid, d in lt.items():
        fn = pages[pid]['fnum']
        if parity == 'odd' and fn % 2 != 1:
            continue
        if parity == 'even' and fn % 2 != 0:
            continue
        if d['illus'] in drop_illus:
            continue
        lab, txt = d['labels'], d['text']
        if dedupe:
            lab = sorted(set(lab))
            txt = sorted(set(txt))
        g.append((pid, lab, txt))
    return g


def build_strata_charlen(groups, units, pos):
    """Feature = glyph unit at word start/end (as in t_l1), but the matching
    stratum is (page x CHARACTER length) instead of (page x unit length)."""
    idx = {u: i for i, u in enumerate(units)}
    out = []
    for gid, lab, txt in groups:
        bl, bt = {}, {}
        for w in lab:
            u = ML.bpe_apply(w)
            if u:
                bl.setdefault(len(w), []).append(
                    idx.get(u[-1] if pos == 'final' else u[0], -1))
        for w in txt:
            u = ML.bpe_apply(w)
            if u:
                bt.setdefault(len(w), []).append(
                    idx.get(u[-1] if pos == 'final' else u[0], -1))
        for L, labs in sorted(bl.items()):
            txts = bt.get(L)
            if not txts:
                continue
            out.append((len(labs) + len(txts), len(labs), list(labs) + list(txts)))
    return out


def run(name, groups, units, pos, charlen=False, nperm=NPERM):
    strata = (build_strata_charlen(groups, units, pos) if charlen
              else T.build_strata(groups, units, T.seg_glyph, pos))
    f = T.Family(name, units, strata)
    f.observed()
    f.permute(nperm=nperm, seed=ML.SEED)
    return f


WATCH = {'initial': ['qok', 'q', 'c', 'daiin', 'she', 'chedy', 'ot', 'o'],
         'final': ['n', 'daiin', 'chedy', 'eey', 'in']}


def report(f, pos, tag):
    m = f.meta()
    say('--- %s [%s]' % (tag, pos))
    say('    strata=%d  label=%d text=%d  pooled mean|lo|=%.4f  '
        'units passing (|lo|>=1 & bonf p<.01)=%d  bonf-sig=%d'
        % (m['n_strata'], m['n_label_words_matched'], m['n_text_words_matched'],
           m['pooled_effect_mean_abs_logodds'], m['n_units_passing'],
           m['n_units_bonferroni_significant']))
    rows = {r['unit']: r for r in f.rows()}
    passers = [r['unit'] for r in f.rows() if r['passes_unit_test']]
    say('    passers: %s' % (', '.join(passers) if passers else '(none)'))
    for u in WATCH[pos]:
        r = rows.get(u)
        if r is None:
            continue
        say('      %-6s lo=%7.3f  bonf p=%8.5f  lab=%4d txt=%5d  strata=%3d  %s'
            % (u, r['log_odds'], r['p_bonferroni'], r['n_label_words_with_unit'],
               r['n_text_words_with_unit'], r['n_informative_strata'],
               'PASS' if r['passes_unit_test'] else ''))
    say()
    return OrderedDict([('tag', tag), ('pos', pos), ('meta', m),
                        ('passers', passers),
                        ('watch', OrderedDict(
                            (u, rows[u]) for u in WATCH[pos] if u in rows))])


def main():
    res = OrderedDict()
    res['verifier'] = 'v_l1_confound_2 (lens: confound)'
    res['seed'] = ML.SEED
    res['n_permutations'] = NPERM
    res['inputs'] = OrderedDict([
        ('ZL3b-n.txt', ML.sha256(ZL)),
        ('meaning_lib.py', ML.sha256(os.path.join(HERE, 'meaning_lib.py'))),
        ('t_l1.py', ML.sha256(os.path.join(HERE, 't_l1.py'))),
        ('results/l1.json', ML.sha256(os.path.join(HERE, 'results', 'l1.json'))),
    ])
    for k, v in res['inputs'].items():
        say('  sha256 %-18s %s' % (k, v))
    say()

    pages = ML.parse_pages(ZL, comma_split=True)
    words_all = ML.all_words(pages)
    units = {}
    for pos in ('final', 'initial'):
        units[pos], _ = T.top_k_units(words_all, T.seg_glyph, pos)
    say('frozen K=25 final units  : %s' % ' '.join(units['final']))
    say('frozen K=25 initial units: %s' % ' '.join(units['initial']))
    say()

    lt_full = page_registers(pages)
    lt_locini = page_registers(pages, locus_initial_only=True)
    lt_ponly = page_registers(pages, text_locus_types=('P',))

    variants = [
        ('C1 baseline (odd folios, unit-length strata)',
         groups_from(pages, lt_full), False),
        ('C2 text = locus-INITIAL words only',
         groups_from(pages, lt_locini), False),
        ('C3 TYPE level: both sides deduplicated within page',
         groups_from(pages, lt_full, dedupe=True), False),
        ('C4 text = paragraph (P) loci only',
         groups_from(pages, lt_ponly), False),
        ('C5 drop illus=B (biological) pages',
         groups_from(pages, lt_full, drop_illus=('B',)), False),
        ('C6 drop illus in {Z,A,C} (nymph/astro/cosmo label pages)',
         groups_from(pages, lt_full, drop_illus=('Z', 'A', 'C')), False),
        ('C7 strata matched on CHARACTER length',
         groups_from(pages, lt_full), True),
        ('C8 TYPE level AND text = locus-INITIAL words (both controls at once)',
         groups_from(pages, lt_locini, dedupe=True), False),
        ('C9 TYPE level on the FIT half (even folios) -- does it hold there too',
         groups_from(pages, lt_full, parity='even', dedupe=True), False),
        ('C10 TYPE level, all pages (FIT+TEST pooled)',
         groups_from(pages, lt_full, parity='all', dedupe=True), False),
    ]

    res['variants'] = []
    for tag, grp, charlen in variants:
        say('=' * 78)
        say(tag)
        say('    pages used: %d ; label tokens %d ; text tokens %d'
            % (len(grp), sum(len(g[1]) for g in grp), sum(len(g[2]) for g in grp)))
        say('=' * 78)
        for pos in ('final', 'initial'):
            f = run('%s|%s' % (tag.split()[0], pos), grp, units[pos], pos,
                    charlen=charlen)
            res['variants'].append(report(f, pos, tag))

    # ------------------------------------------- leave-one-page-out leverage --
    say('=' * 78)
    say('LEAVE-ONE-PAGE-OUT on the observed log-odds (no permutation)')
    say('=' * 78)
    base_grp = groups_from(pages, lt_full)
    loo = OrderedDict()
    for pos, watch in (('initial', ['qok', 'q', 'c', 'daiin']),
                       ('final', ['n', 'daiin'])):
        strata = T.build_strata(base_grp, units[pos], T.seg_glyph, pos)
        full = T.Family('loo_full_%s' % pos, units[pos], strata)
        full.observed()
        idx = {u: i for i, u in enumerate(units[pos])}
        say('-- %s' % pos)
        for u in watch:
            i = idx[u]
            base = full.obs_cor[i]
            worst = None
            vals = []
            for drop in [g[0] for g in base_grp]:
                sub = [g for g in base_grp if g[0] != drop]
                st = T.build_strata(sub, units[pos], T.seg_glyph, pos)
                fm = T.Family('x', units[pos], st)
                fm.observed()
                v = fm.obs_cor[i]
                vals.append((drop, v))
                if worst is None or abs(v) < abs(worst[1]):
                    worst = (drop, v)
            vals.sort(key=lambda x: abs(x[1]))
            say('   %-6s full lo=%7.3f | most-influential drops: %s'
                % (u, base, ', '.join('%s->%.3f' % v for v in vals[:4])))
            say('          still |lo|>=1 after dropping any single page: %s'
                % ('YES' if abs(worst[1]) >= 1.0 else
                   'NO (drop %s -> %.3f)' % worst))
            loo['%s|%s' % (pos, u)] = OrderedDict([
                ('full', round(base, 4)),
                ('min_abs_after_drop', round(worst[1], 4)),
                ('min_abs_page', worst[0]),
                ('robust_to_single_page_drop', bool(abs(worst[1]) >= 1.0)),
            ])
        say()
    res['leave_one_page_out'] = loo

    with io.open(os.path.join(HERE, 'results', 'v_l1_confound_2.json'), 'w',
                 encoding='utf-8') as fh:
        fh.write(json.dumps(res, indent=2, ensure_ascii=False))
    with io.open(os.path.join(HERE, 'results', 'v_l1_confound_2.stdout.txt'),
                 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(OUT) + '\n')


if __name__ == '__main__':
    main()
