#!/usr/bin/env python3
"""v_z4_null-correctness_decision.py — part 3.

Given a high-precision estimate of the true permutation tail probability q for
MI(ring third; first unit) on TEST, what is the probability that the REGISTERED
procedure (B = 10000, p = (1+ge)/10001) declares a pass?  Exact binomial.

Also: the +1 correction at B = 10000 biases the reported p upward by ~1/(B+1);
this is comparable to the entire margin by which the statistic clears.
"""
import io
import json
import math
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import meaning_lib as ML

OUT = []


def say(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


def binom_cdf(k, n, p):
    """P(X <= k), X ~ Bin(n, p), in log space for stability."""
    lp, l1p = math.log(p), math.log1p(-p)
    lgam = math.lgamma
    tot = 0.0
    for i in range(0, k + 1):
        lt = (lgam(n + 1) - lgam(i + 1) - lgam(n - i + 1)
              + i * lp + (n - i) * l1p)
        tot += math.exp(lt)
    return tot


B = 10000
ALPHA6 = 0.01 / 6.0
ALPHA4 = 0.01 / 4.0

say('=' * 78)
say('V-Z4 part 3 — what the registered procedure would decide, on average')
say('=' * 78)
say('')
say('High-precision estimates of the true permutation tail probability q for')
say('MI(ring third; first glyph unit), ZL3b TEST signs, glyph-unit level:')
say('  t_z4 diagnostic  B=200000 seed 409   ge=329  raw rate q = %.6f' % (329 / 200000.))
say('     (that stream REUSES seed 409, so its first 10000 draws ARE the')
say('      registered draws; it is not independent of the gated number)')
say('  this verifier B=200000 seeds 10408/20408/30408/40408  ge=333')
say('     raw rate q = %.6f  (SE %.6f)'
    % (333 / 200000., math.sqrt((333 / 200000.) * (1 - 333 / 200000.) / 200000)))
q_all = (329 + 333) / 400000.
se_all = math.sqrt(q_all * (1 - q_all) / 400000)
say('  pooled 400000 draws: ge=662  q_hat = %.6f  (SE %.6f)' % (q_all, se_all))
say('  95%% CI for q: [%.6f, %.6f]' % (q_all - 1.96 * se_all, q_all + 1.96 * se_all))
say('')

say('The reported p is (1+ge)/(1+B) with B=10000.  Its expectation is')
say('  E[p] = (1 + B q)/(1 + B) = %.6f  for q = %.6f' % ((1 + B * q_all) / (1 + B), q_all))
_marg = ALPHA6 - 0.0015998400159984
say('i.e. the +1 correction alone adds %.6f to the reported p, which is %.1f times'
    % ((1 - q_all) / (1 + B), ((1 - q_all) / (1 + B)) / _marg))
say('the %.5f margin by which the registered run cleared the threshold.' % _marg)
say('')

say('Largest ge that still clears each threshold at B=10000:')
for name, a in (('Bonferroni/6 (family of six, used by t_z4)', ALPHA6),
                ('Bonferroni/4 (family of four, as PROTOCOL registers)', ALPHA4)):
    kmax = -1
    while (1.0 + kmax + 1) / (1.0 + B) < a:
        kmax += 1
    pr = binom_cdf(kmax, B, q_all)
    say('  %-52s ge <= %2d' % (name, kmax))
    say('    P(registered run declares PASS) = P(Bin(10000, %.6f) <= %d) = %.3f'
        % (q_all, kmax, pr))
say('')
say('  Sensitivity of that pass probability to q inside its 95%% CI '
    '(family of six):')
kmax6 = -1
while (1.0 + kmax6 + 1) / (1.0 + B) < ALPHA6:
    kmax6 += 1
for qq, lbl in ((q_all - 1.96 * se_all, 'q lower 95%'),
                (q_all, 'q point est'),
                (q_all + 1.96 * se_all, 'q upper 95%')):
    say('    %-12s q=%.6f -> P(PASS) = %.3f' % (lbl, qq, binom_cdf(kmax6, B, qq)))
say('')
say('OBSERVED seed behaviour (t_z4 diagnostic, seeds 409-418, one of which -- 409 --')
say('IS the registered stream): 6/10 pass.  Excluding the registered stream: 5/9.')
say('That is what a pass probability near 0.4-0.6 looks like.')
say('')

say('Cross-check of the reported p against the Bonferroni threshold arithmetic:')
say('  registered p  = 16/10001 = %.10f' % (16 / 10001.))
say('  next p up     = 17/10001 = %.10f' % (17 / 10001.))
say('  alpha/6       =          %.10f' % ALPHA6)
say('  -> the pass required ge <= 15; the unbiased expectation of ge is %.1f.'
    % (B * q_all))
say('')

# --- spot check that the power calibration uses the same machinery ---------
J = json.load(io.open(os.path.join(HERE, 'results', 'z4.json'), encoding='utf-8'))
say('Spot check of the power calibration bookkeeping (unit level, TEST signs):')
ctrl = list(ML.numeral_controls().keys())
for t in ('MI_P1_F1', 'MI_P2_F1', 'CHI2_prefix_by_rankblock'):
    hits = [s for s in ctrl if J['power_numerals']['unit']['TEST'][s][t]['passes_bonf']]
    say('  %-26s %d/8 detected: %s' % (t, len(hits), ', '.join(hits)))
    say('    reported n_pass = %d, fraction %.3f'
        % (J['power_summary']['unit']['TEST'][t]['n_pass'],
           J['power_summary']['unit']['TEST'][t]['fraction']))
say('')
say('Manuscript debiased effects on TEST vs those controls:')
for t in ('MI_P1_F1', 'MI_P1_F2', 'MI_P2_F1', 'MI_P2_F2',
          'CHI2_prefix_by_rankblock', 'CHI2_suffix_by_rankblock'):
    d = J['primary_ZL3b_unit']['TEST'][t]
    vals = sorted(J['power_numerals']['unit']['TEST'][s][t]['debiased'] for s in ctrl)
    say('  %-26s manuscript %+9.4f   numeral true median %+9.4f  p=%.5f'
        % (t, d['debiased'], 0.5 * (vals[3] + vals[4]), d['p_two_sided']))

with io.open(os.path.join(HERE, 'results', 'v_z4_null-correctness_decision.stdout.txt'),
             'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT) + '\n')
