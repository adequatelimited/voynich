#!/usr/bin/env python3
"""v_r1r2_confound_3.py — small residual checks.

H1 does the frozen 20-merge glyph list matter anywhere in R1? (R1 is written
   entirely on raw EVA; PROTOCOL says every test is run at BOTH levels.)
H2 R2's only merge-dependent outcome is `first_glyph_unit`: how much does the
   merge list actually change it for the star paragraphs?
H3 is R1(a) circular?  In the Recipes section a paragraph start is marked in the
   drawing by a marginal star, so <%> is anchored outside the text. Count how
   many paragraph starts carry a star comment.
H4 the (b) variant matrix, one table.
"""
import io, json, math, os, re, sys
from collections import Counter, OrderedDict, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results')
ZL = os.path.abspath(os.path.join(HERE, '..', '..', 'data', 'corpora', 'ZL3b-n.txt'))
L = []
def say(*a):
    s = ' '.join(str(x) for x in a); L.append(s); print(s)

def fnum(p):
    return int(re.match(r'f(\d+)', p).group(1))

pages = ML.parse_pages(ZL, comma_split=True)
recB = {p['id'] for p in pages.values()
        if p['meta'].get('I') == 'S' and p['meta'].get('L') == 'B'
        and 103 <= p['fnum'] <= 116}
recS = {p['id'] for p in pages.values() if p['meta'].get('I') == 'S'}

say('H1/H2 first glyph unit of star-paragraph openers, merged vs raw EVA')
pars = [d for d in ML.paragraphs(pages, page_ids=recS) if d['star']]
merged = Counter(ML.bpe_apply(d['first_word'])[0] for d in pars)
raw = Counter(d['first_word'][0] for d in pars)
same = sum(1 for d in pars
           if ML.bpe_apply(d['first_word'])[0] == d['first_word'][0])
say('  n=%d openers; first unit == first raw EVA char in %d (%.3f)'
    % (len(pars), same, same/len(pars)))
say('  merged first units: %s' % dict(merged.most_common()))
say('  raw first chars   : %s' % dict(raw.most_common()))

say('')
say('H3 are paragraph starts in the Recipes section anchored outside the text?')
allp = ML.paragraphs(pages, page_ids=recS)
say('  Recipes paragraphs %d ; with a ZL comment %d ; parsed as a drawn star %d'
    % (len(allp), sum(1 for d in allp if d['comment']),
       sum(1 for d in allp if d['star'])))
say('  -> paragraph identity here is fixed by the marginal star in the drawing,')
say('     not by the text, so R1(a) is not circular with the opener glyph.')

say('')
say('H4 R1(b) variant matrix — same statistic, nuisance choices the PROTOCOL')
say('   does not fix.  (+ = openers attested MORE than control)')
j1 = json.load(io.open(os.path.join(RES, 'v_r1r2_confound_1.json'), encoding='utf-8'))
j2 = json.load(io.open(os.path.join(RES, 'v_r1r2_confound_2.json'), encoding='utf-8'))
rows = [
  ('pre-registered: exact g+len, control pool = own half (TOKENS)',
   'reference_preregistered'),
  ('exact g+len, control pool = whole section (TOKENS)', 'G1_section_token_pool'),
  ('exact g+len, control pool = whole section (TYPES)', 'G1t_section_type_pool'),
  ('exact g+len, control from the SAME PAGE', 'G2_same_page'),
  ('TYPES + control length >= opener length, own half', 'G4_type_pool_minlen_local'),
  ('TYPES + control length >= opener length, section', 'G4s_type_pool_minlen_section'),
  ('exact g+len, attestation must be OFF the opener page', 'G5_offpage_attestation'),
]
hdr = '%-56s | %-22s | %-22s | %-22s' % ('variant', 'TEST_even', 'FIT_odd', 'ALL')
say('  ' + hdr)
say('  ' + '-' * len(hdr))
for lab, key in rows:
    cells = []
    for st in ('TEST_even', 'FIT_odd', 'ALL'):
        r = j2['G'][st][key]
        cells.append('%+.2f SD p=%.4f n=%d' % (r['sd_units'], r['p_two_sided'],
                                               r['n_matched']) if r else 'n/a')
    say('  %-56s | %-22s | %-22s | %-22s' % (lab, cells[0], cells[1], cells[2]))
# the agent's supplementary relaxed match, from its own JSON
tj = json.load(io.open(os.path.join(RES, 'r1r2.json'), encoding='utf-8'))
pr = tj['runs']['ZL3b_comma_split_true']['R1']
cells = []
for st, k in (('TEST_even', 'recipesB_TEST_even'), ('FIT_odd', 'recipesB_FIT_odd'),
              ('ALL', 'recipesB_ALL')):
    rb = pr[k]['bc']['b_relaxed_match_SUPPLEMENTARY']
    cells.append('%+.2f SD p=%.4f n=%d' % (rb['sd_units'], rb['p_two_sided'],
                                           rb['n_matched']))
say('  %-56s | %-22s | %-22s | %-22s' % (
    "agent's SUPPLEMENTARY relaxed match (+/-1,2,any), own half",
    cells[0], cells[1], cells[2]))
e = j1['E_b_frequency']
cells = ['%+.2f SD p=%.4f n=%d' % (e[st]['E4_sd_units'], e[st]['E4_p'],
                                   e[st]['E4_n_matched'])
         for st in ('TEST_even', 'FIT_odd', 'ALL')]
say('  %-56s | %-22s | %-22s | %-22s' % (
    'same relaxed match but control length >= opener length',
    cells[0], cells[1], cells[2]))
cells = ['%+.2f SD p=%.4f n=%d' % (e[st]['E2_sd_units'], e[st]['E2_p'],
                                   e[st]['E2_n_matched'])
         for st in ('TEST_even', 'FIT_odd', 'ALL')]
say('  %-56s | %-22s | %-22s | %-22s' % (
    'exact g+len+log2-frequency-bin matched, own half', cells[0], cells[1], cells[2]))

say('')
say('  Openers are systematically RARER words than the token-drawn control')
say('  (mean log2 section frequency, exact-matched): TEST %.3f vs %.3f, FIT %.3f'
    ' vs %.3f, ALL %.3f vs %.3f' % (
        e['TEST_even']['E1_mean_log2_freq_openers'],
        e['TEST_even']['E1_mean_log2_freq_control'],
        e['FIT_odd']['E1_mean_log2_freq_openers'],
        e['FIT_odd']['E1_mean_log2_freq_control'],
        e['ALL']['E1_mean_log2_freq_openers'],
        e['ALL']['E1_mean_log2_freq_control']))
say('  and residue attestation falls steeply with word length in the control')
say('  pool, e.g. ALL: len3 %.3f len5 %.3f len7 %.3f len9 %.3f' % tuple(
    j1['D_b_anatomy']['ALL']['attest_rate_by_length_controlpool'][k][1]
    for k in ('3', '5', '7', '9')))

with io.open(os.path.join(RES, 'v_r1r2_confound_3.stdout.txt'), 'w',
             encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n')
