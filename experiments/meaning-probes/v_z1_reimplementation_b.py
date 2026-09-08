#!/usr/bin/env python3
"""Linear-gap arms of the reimplementation, to diff every reported number."""
import json, sys
sys.path.insert(0, r"R:/Coding/LinearA/tmp/voynich_repo/experiments/meaning-probes")
import meaning_lib as ml

src = open(r"R:/Coding/LinearA/tmp/voynich_repo/experiments/meaning-probes/v_z1_reimplementation_a.py").read()
src = src.replace("\nmain()\n", "\n")
g = {'__name__': 'reimpl_a'}
exec(compile(src, 'v_z1_reimplementation_a.py', 'exec'), g)
run_z1 = g['run_z1']; mean_sims = g['mean_sims']; voynich_rings = g['voynich_rings']
control_rings = g['control_rings']

out = {}
vr = voynich_rings()
test_rings = [r for s in ml.TEST_SIGNS for r in vr.get(s, [])]
fit_rings = [r for s in ml.FIT_SIGNS for r in vr.get(s, [])]
sizes = [len(r) for r in test_rings]

vrc = voynich_rings(level='chars')
test_c = [r for s in ml.TEST_SIGNS for r in vrc.get(s, [])]

for name, rings in [('FIT_linear', fit_rings), ('TEST_chars_linear', test_c)]:
    r = run_z1(rings, cyclic=False)
    m1, m3 = mean_sims(rings, cyclic=False)
    r['mean_sim_g1'] = m1; r['mean_sim_g3plus'] = m3
    out[name] = r
    print(name, 'delta %.5f p %.4f | rho %.5f p %.4f | rings %d labels %d pairs %d' %
          (r['delta'], r['p_delta_add1'], r['rho_bar'], r['p_rho_add1'],
           r['n_rings'], r['n_labels'], r['n_pairs']))

# numeral controls, LINEAR gap, matched sizes
ctrl = {}
for nm, series in ml.numeral_controls().items():
    rings = control_rings(series, sizes, mode='cyclic')
    rr = run_z1(rings, cyclic=False)
    m1, m3 = mean_sims(rings, cyclic=False)
    ctrl[nm] = {'delta': rr['delta'], 'p': rr['p_delta_add1'], 'rho': rr['rho_bar'],
                'p_rho': rr['p_rho_add1'], 'g1': m1, 'g3': m3}
    print('CTRL-lin', nm, 'delta=%.5f p=%.4f rho=%.4f p=%.4f g1=%.4f g3=%.4f' %
          (rr['delta'], rr['p_delta_add1'], rr['rho_bar'], rr['p_rho_add1'], m1, m3))
out['numeral_controls_linear'] = ctrl
ds = sorted(v['delta'] for v in ctrl.values())
med = (ds[3] + ds[4]) / 2.0
out['median_linear'] = med
print('linear median delta %.5f ; TEST(lin) 0.006117 / med = %.4f' % (med, 0.0061171 / med))
npow = sum(1 for v in ctrl.values() if v['p'] < 0.01 and v['p_rho'] < 0.01
           and v['delta'] > 0 and v['rho'] < 0)
print('power both (linear) = %d/8' % npow)
open(r"R:/Coding/LinearA/tmp/voynich_repo/experiments/meaning-probes/v_z1_reimpl_b.json",
     'w').write(json.dumps(out, indent=1))
