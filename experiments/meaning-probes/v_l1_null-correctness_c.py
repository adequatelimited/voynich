#!/usr/bin/env python3
"""v_l1_null-correctness_c.py -- what the passing units actually rest on.

For each unit that clears gate leg 1 on TEST, list the individual words behind
it: which page, which locus, which type. A permutation p is exact only for the
sharp null of word-level exchangeability; if the label-side evidence is one word
type repeated inside one locus, the exact p is still exact but the effective
number of independent observations is 1, not 7.

Also: Bonferroni family accounting, and a check of the report's claims against
results/l1.json.
"""
import io, json, os, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

REPO = 'R:/Coding/LinearA/tmp/voynich_repo'
ZL = REPO + '/data/corpora/ZL3b-n.txt'
OUT = REPO + '/experiments/meaning-probes/results'
LOG = []
def say(s=''):
    print(s); LOG.append(str(s))

pages = ML.parse_pages(ZL, comma_split=True)

TARGETS = [('final', 'n'), ('final', 'daiin'),
           ('initial', 'qok'), ('initial', 'q'),
           ('initial', 'c'), ('initial', 'daiin')]

for pos, unit in TARGETS:
    say('=' * 74)
    say('TEST (odd folios): words whose %s glyph unit is %r' % (pos, unit))
    lab_rows, txt_rows = [], []
    for pid, p in pages.items():
        if p['fnum'] % 2 != 1:
            continue
        has_lab = any(l['type'] == 'L' and l['words'] for l in p['loci'])
        has_txt = any(l['type'] in ('P', 'C', 'R') and l['words'] for l in p['loci'])
        if not (has_lab and has_txt):
            continue
        for l in p['loci']:
            if l['type'] == 'L':
                bucket = lab_rows
            elif l['type'] in ('P', 'C', 'R'):
                bucket = txt_rows
            else:
                continue
            for w in l['words']:
                u = ML.bpe_apply(w)
                if not u:
                    continue
                if (u[-1] if pos == 'final' else u[0]) == unit:
                    bucket.append((pid, l['n'], l['code'], w, len(u)))
    say('  LABEL side: %d tokens, %d distinct types, %d distinct loci, '
        '%d distinct pages'
        % (len(lab_rows), len(set(r[3] for r in lab_rows)),
           len(set((r[0], r[1]) for r in lab_rows)),
           len(set(r[0] for r in lab_rows))))
    for r in lab_rows[:20]:
        say('     %-8s locus %3d %-4s  %-14s len=%d' % r)
    say('  TEXT side: %d tokens, %d distinct types, %d distinct pages'
        % (len(txt_rows), len(set(r[3] for r in txt_rows)),
           len(set(r[0] for r in txt_rows))))
    say('     top text types: %s'
        % Counter(r[3] for r in txt_rows).most_common(6))
    say('     text length distribution: %s'
        % sorted(Counter(r[4] for r in txt_rows).items()))
    say('     label length distribution: %s'
        % sorted(Counter(r[4] for r in lab_rows).items()))
    say()

# ---------------------------------------------------------- family counting --
d = json.load(io.open(os.path.join(OUT, 'l1.json'), encoding='utf-8'))
say('=' * 74)
say('BONFERRONI FAMILY ACCOUNTING')
say('=' * 74)
say('  protocol pre-registers ONE family: word-final glyph units, K=25.')
say('  t_l1.py additionally reports a word-INITIAL family of 25 on the same')
say('  TEST split and corrects it over 25, not over the 50 tests actually run')
say('  on TEST. Raw p and Bonferroni p under K=25 vs K=50:')
for pos in ('final', 'initial'):
    for r in d['primary_ZL3b']['test_odd'][pos]['units']:
        if r['p_perm'] * 25 < 0.01 or r['p_perm'] * 50 < 0.02:
            say('    %-7s %-8s raw p=%.5f   x25=%.5f %s   x50=%.5f %s'
                % (pos, r['unit'], r['p_perm'], r['p_perm'] * 25,
                   'sig' if r['p_perm'] * 25 < 0.01 else '   ',
                   r['p_perm'] * 50,
                   'sig' if r['p_perm'] * 50 < 0.01 else '   '))
say()
say('  minimum attainable raw p with 10,000 draws = 1/10001 = %.6f' % (1 / 10001.0))
say('  gate needs Bonferroni p < 0.01 -> raw p < 0.0004 -> at most 3 of 10,000')
say('  draws may equal or exceed the observed value. Only 4 attainable p-levels')
say('  sit below the gate threshold.')
say()

say('=' * 74)
say('REPORT CLAIMS vs results/l1.json')
say('=' * 74)
g = d['gate']
say('  report: "Culpeper word-initial control: 0 of 25 clear it"')
say('  json  : gate.control_units_passing_initial = %d'
    % g['control_units_passing_initial'])
for r in d['culpeper_control']['initial']['units']:
    if r['passes_unit_test']:
        say('          passing control unit %-3r log-odds=%.3f bonf p=%.5f'
            % (r['unit'], r['log_odds'], r['p_bonferroni']))
say()
say('  json.estimator field says: %r' % d['estimator'][:120])
say('  ...but t_l1.py KAPPA correction adds kappa*m1/n to the two label cells')
say('  and kappa*m0/n to the two text cells (a MARGINAL correction), not 0.5')
say('  to every cell. The JSON estimator string is wrong.')
say()
say('  n_units_bonferroni_significant, TEST final = %d (chedy is NOT among them)'
    % d['primary_ZL3b']['test_odd']['final']['n_units_bonferroni_significant'])

with io.open(os.path.join(OUT, 'v_l1_null-correctness_c.stdout.txt'), 'w',
             encoding='utf-8') as fh:
    fh.write('\n'.join(LOG) + '\n')
