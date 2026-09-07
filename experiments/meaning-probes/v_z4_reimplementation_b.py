#!/usr/bin/env python3
"""v_z4_reimplementation_b.py -- p-definition diagnosis + high-precision rerun.

The reported p-values for the five flat statistics are far from my one-sided
upper-tail p. Hypothesis: the registered run used a TWO-SIDED symmetric
absolute-deviation-from-null-mean p. Test that hypothesis by computing three p
definitions from ONE null distribution per statistic, and see which reproduces
the reported numbers.

Also: high-precision (B=200,000) rerun of the single passer under both
definitions, and a numeral positive-control replication of the power claim.
"""
import json, math, random, sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML
from v_z4_reimplementation_a import (mutual_information, chisq, build_records,
                                     group_index, marginals, ZL, GC)

B = 10000
SEED = 408


def null_dist(recs, pos_field, form_field, stat_fn, B=B, seed=SEED):
    if pos_field == 'block':
        groups = group_index(recs, lambda r: r['sign'])
    else:
        groups = group_index(recs, lambda r: (r['sign'], r['ring']))
    pos = [r[pos_field] for r in recs]
    form = [r[form_field] for r in recs]
    obs = stat_fn(pos, form)
    rng = random.Random(seed)
    null = []
    work = list(pos)
    for _ in range(B):
        for idxs in groups.values():
            vals = [pos[i] for i in idxs]
            rng.shuffle(vals)
            for i, v in zip(idxs, vals):
                work[i] = v
        null.append(stat_fn(work, form))
    return obs, null


def three_ps(obs, null):
    B = len(null)
    mean = sum(null) / B
    eps = 1e-12
    up = sum(1 for v in null if v >= obs - eps)
    dn = sum(1 for v in null if v <= obs + eps)
    dev = abs(obs - mean)
    two_abs = sum(1 for v in null if abs(v - mean) >= dev - eps)
    var = sum((v - mean) ** 2 for v in null) / (B - 1)
    return {
        'observed': obs, 'null_mean': mean, 'null_sd': math.sqrt(var),
        'debiased': obs - mean,
        'p_one_sided_upper_plain': up / B,
        'p_one_sided_upper_addone': (up + 1) / (B + 1),
        'p_two_sided_min2x': min(1.0, 2.0 * min(up, dn) / B),
        'p_two_sided_absdev_plain': two_abs / B,
        'p_two_sided_absdev_addone': (two_abs + 1) / (B + 1),
    }


def main():
    out = {'sha256': {'ZL3b-n.txt': ML.sha256(ZL), 'GC2a-n.txt': ML.sha256(GC)}}
    recs = build_records(ZL, comma_split=True, level='unit')
    test = [r for r in recs if r['sign'] in ML.TEST_SIGNS]

    lines = []
    def P(s=''):
        lines.append(s); print(s)

    P('=== p-definition diagnosis, TEST signs, glyph units, B=10000, seed 408 ===')
    P(f"{'statistic':30s} {'obs':>8s} {'debias':>8s} {'1sidUp':>9s} {'2s_min2x':>9s} {'2s_absdev':>10s}")
    diag = {}
    specs = [('MI(block;first)', 'block', 'first', mutual_information),
             ('MI(block;last)', 'block', 'last', mutual_information),
             ('MI(third;first)', 'third', 'first', mutual_information),
             ('MI(third;last)', 'third', 'last', mutual_information),
             ('chi2(first x block)', 'block', 'first', chisq),
             ('chi2(last x block)', 'block', 'last', chisq)]
    for name, pos, form, fn in specs:
        obs, null = null_dist(test, pos, form, fn)
        d = three_ps(obs, null)
        diag[name] = d
        P(f"{name:30s} {d['observed']:8.4f} {d['debiased']:+8.4f} "
          f"{d['p_one_sided_upper_plain']:9.5f} {d['p_two_sided_min2x']:9.5f} "
          f"{d['p_two_sided_absdev_plain']:10.5f}")
    out['p_definitions_TEST'] = diag

    P('')
    P('reported by the test agent, for comparison:')
    rep = {'MI(block;first)': 0.92231, 'MI(block;last)': 0.41126,
           'MI(third;first)': 0.00160, 'MI(third;last)': 0.11929,
           'chi2(first x block)': 0.96830, 'chi2(last x block)': 0.53185}
    for k, v in rep.items():
        d = diag[k]
        P(f"  {k:30s} reported {v:9.5f}   absdev_plain {d['p_two_sided_absdev_plain']:9.5f}"
          f"   absdev+1 {d['p_two_sided_absdev_addone']:9.5f}")

    # high-precision rerun of the single passer, several seeds
    P('')
    P('=== high-precision rerun, MI(third;first), TEST, B=200000 ===')
    hp = {}
    for s in (408, 999):
        obs, null = null_dist(test, 'third', 'first', mutual_information,
                              B=200000, seed=s)
        d = three_ps(obs, null)
        hp[str(s)] = d
        se_up = math.sqrt(d['p_one_sided_upper_plain'] * (1 - d['p_one_sided_upper_plain']) / 200000)
        se_2s = math.sqrt(d['p_two_sided_absdev_plain'] * (1 - d['p_two_sided_absdev_plain']) / 200000)
        P(f"  seed {s}: one-sided p={d['p_one_sided_upper_plain']:.6f} (SE {se_up:.6f})  "
          f"two-sided absdev p={d['p_two_sided_absdev_plain']:.6f} (SE {se_2s:.6f})")
        P(f"           null mean {d['null_mean']:.5f} sd {d['null_sd']:.5f} debiased {d['debiased']:+.5f}")
    out['high_precision'] = hp
    thr6, thr4 = 0.01 / 6, 0.01 / 4
    P(f"  Bonferroni thresholds: 6-family {thr6:.7f}, 4-family {thr4:.7f}")

    # power replication: numeral series in the observed TEST geometry
    P('')
    P('=== power replication: 8 numeral systems in the observed TEST geometry ===')
    geom = [(r['sign'], r['ring'], r['idx_in_ring'], r['idx_in_sign'],
             r['n_ring'], r['third'], r['block']) for r in test]
    nums = ML.numeral_controls()
    power = {}
    for pos, form in [('block', 'first'), ('block', 'last'),
                      ('third', 'first'), ('third', 'last')]:
        det, effs = 0, []
        for nm, series in nums.items():
            # lay the numeral series out in the observed geometry: within each
            # sign, label at rank k gets numeral k+1 (mod 30).
            synth = []
            for (sign, ring, iir, iis, nring, third, block) in geom:
                w = series[iis % 30]
                u = ML.bpe_apply(w)
                synth.append({'sign': sign, 'ring': ring, 'idx_in_ring': iir,
                              'idx_in_sign': iis, 'n_ring': nring,
                              'third': third, 'block': block,
                              'first': u[0], 'last': u[-1]})
            obs, null = null_dist(synth, pos, form, mutual_information)
            d = three_ps(obs, null)
            effs.append(d['debiased'])
            if d['p_two_sided_absdev_plain'] < thr6:
                det += 1
        effs.sort()
        med = effs[len(effs) // 2] if len(effs) % 2 else (effs[len(effs)//2-1]+effs[len(effs)//2])/2
        power[f'MI({pos};{form})'] = {'detected': det, 'of': len(nums),
                                      'median_debiased': med}
        P(f"  MI({pos};{form}):  detected {det}/8   median debiased {med:+.4f} bits")
    out['power'] = power

    resdir = Path(__file__).resolve().parent / 'results'
    (resdir / 'v_z4_reimplementation_b.json').write_text(
        json.dumps(out, indent=2, sort_keys=True), encoding='utf-8')
    (resdir / 'v_z4_reimplementation_b.stdout.txt').write_text('\n'.join(lines) + '\n',
                                                               encoding='utf-8')


if __name__ == '__main__':
    main()
