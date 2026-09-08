#!/usr/bin/env python3
"""v_z4_reimplementation_c.py -- checks on the registered run's own code path.

1. The registered script runs the P2 (ring-third) statistics with seed 408+1=409,
   not the registered seed 408. Recompute the passer at seed 408 through the
   test's OWN mi_focus, and across seeds, under both Bonferroni families.
2. Family size: PROTOCOL.md says "Bonferroni over the four combinations"
   (threshold 0.0025). The registered run used six (0.0016667). Report the
   verdict under both.
3. Jackknife: is the single passer carried by one ring?
4. GC2a coverage numbers.

Imports t_z4 (does not modify it; main() is guarded).
"""
import json, math, random, sys, os
from collections import Counter, OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import meaning_lib as ML
import t_z4 as T

B = 10000
THR6 = 0.01 / 6
THR4 = 0.01 / 4

lines = []
def P(s=''):
    lines.append(s); print(s)


def main():
    lab = T.load_labels(T.ZL3B, True)
    tst = T.split(lab, ML.TEST_SIGNS)
    items = T.build_items(tst, 'unit')
    out = {'sha256': {'ZL3b': ML.sha256(T.ZL3B), 'GC2a': ML.sha256(T.GC2A),
                      'meaning_lib.py': ML.sha256(str(HERE / 'meaning_lib.py')),
                      't_z4.py': ML.sha256(str(HERE / 't_z4.py'))}}

    P('=== 1. seed used for the passing statistic ===')
    P('t_z4.analyse() calls run_position(..., P1, seed) and run_position(..., P2, seed+1).')
    P('The passer MI_P2_F1 therefore runs on seed 409, not the registered 408.')
    seeds = [408, 409] + list(range(410, 424))
    rows = []
    for s in seeds:
        r = T.mi_focus(items, 'P2', 'f1', s, B)
        rows.append({'seed': s, 'p': r['p_two_sided'], 'obs': r['observed'],
                     'debiased': r['debiased'],
                     'pass6': r['p_two_sided'] < THR6,
                     'pass4': r['p_two_sided'] < THR4})
        P(f"  seed {s}: p = {r['p_two_sided']:.5f}   debiased {r['debiased']:+.5f}   "
          f"family6 {'PASS' if rows[-1]['pass6'] else 'fail'}   "
          f"family4 {'PASS' if rows[-1]['pass4'] else 'fail'}")
    n6 = sum(1 for r in rows if r['pass6'])
    n4 = sum(1 for r in rows if r['pass4'])
    P(f"  -> {n6}/{len(rows)} seeds clear the 6-family threshold {THR6:.7f}")
    P(f"  -> {n4}/{len(rows)} seeds clear the protocol-literal 4-family threshold {THR4:.7f}")
    out['seed_sweep_MI_P2_F1'] = rows
    out['seed_sweep_pass_counts'] = {'family6': n6, 'family4': n4, 'n_seeds': len(rows)}

    P('')
    P('=== 2. high-precision p through the test\'s own mi_focus, B=200000 ===')
    hp = {}
    for s in (408, 409):
        r = T.mi_focus(items, 'P2', 'f1', s, 200000)
        hp[str(s)] = {'p': r['p_two_sided'], 'se': r['mc_se_of_p'],
                      'observed': r['observed'], 'debiased': r['debiased']}
        P(f"  seed {s}: p = {r['p_two_sided']:.6f} (MC SE {r['mc_se_of_p']:.6f})  "
          f"obs {r['observed']:.4f}  debiased {r['debiased']:+.4f}")
        P(f"           vs family6 {THR6:.7f} -> {'clears' if r['p_two_sided'] < THR6 else 'MISSES'}"
          f" ; vs family4 {THR4:.7f} -> {'clears' if r['p_two_sided'] < THR4 else 'MISSES'}")
    out['high_precision_own_code'] = hp

    P('')
    P('=== 3. jackknife: drop one ring at a time from the TEST set ===')
    rings = sorted(set((it['sign'], it['ring']) for it in items))
    P(f"  {len(rings)} rings on TEST; sizes: "
      f"{[sum(1 for it in items if (it['sign'],it['ring'])==k) for k in rings]}")
    jk = []
    for k in rings:
        sub = [it for it in items if (it['sign'], it['ring']) != k]
        r = T.mi_focus(sub, 'P2', 'f1', 409, B)
        jk.append({'dropped_ring': f'{k[0]}#{k[1]}', 'n': len(sub),
                   'p': r['p_two_sided'], 'debiased': r['debiased'],
                   'pass6': r['p_two_sided'] < THR6, 'pass4': r['p_two_sided'] < THR4})
        P(f"  drop {k[0]:12s} ring{k[1]}  n={len(sub):3d}  p={r['p_two_sided']:.5f}  "
          f"deb {r['debiased']:+.4f}  "
          f"f6 {'PASS' if jk[-1]['pass6'] else 'fail'}  f4 {'PASS' if jk[-1]['pass4'] else 'fail'}")
    out['jackknife_drop_ring'] = jk
    P(f"  -> passes family6 in {sum(1 for j in jk if j['pass6'])}/{len(jk)} leave-one-ring-out sets")
    P(f"  -> passes family4 in {sum(1 for j in jk if j['pass4'])}/{len(jk)} leave-one-ring-out sets")

    P('')
    P('=== 3b. jackknife: drop one SIGN at a time from the TEST set ===')
    jks = []
    for sg in ML.TEST_SIGNS:
        sub = [it for it in items if it['sign'] != sg]
        r = T.mi_focus(sub, 'P2', 'f1', 409, B)
        jks.append({'dropped_sign': sg, 'n': len(sub), 'p': r['p_two_sided'],
                    'debiased': r['debiased'], 'pass6': r['p_two_sided'] < THR6,
                    'pass4': r['p_two_sided'] < THR4})
        P(f"  drop {sg:12s} n={len(sub):3d}  p={r['p_two_sided']:.5f}  deb {r['debiased']:+.4f}  "
          f"f6 {'PASS' if jks[-1]['pass6'] else 'fail'}  f4 {'PASS' if jks[-1]['pass4'] else 'fail'}")
    out['jackknife_drop_sign'] = jks

    P('')
    P('=== 4. GC2a coverage ===')
    for nm, path in (('ZL3b', T.ZL3B), ('GC2a', T.GC2A)):
        pg = ML.parse_pages(path, comma_split=True)
        folios = [f for fs in ML.ZODIAC_SIGNS.values() for f in fs]
        loci = [l for f in folios if f in pg for l in pg[f]['loci']
                if l['type'] == 'L' and l['sub'] == 'z']
        wl = sum(1 for l in loci if l['words'])
        lab2 = T.load_labels(path, True)
        t2 = T.split(lab2, ML.TEST_SIGNS)
        P(f"  {nm}: {len(loci)} Lz loci, {wl} survive clean parser, "
          f"{len(lab2)} label records, {len(t2)} on TEST")
        out[f'coverage_{nm}'] = {'Lz_loci': len(loci), 'survive': wl,
                                 'records': len(lab2), 'TEST': len(t2)}

    P('')
    P('=== 5. what drives the passer: first-unit x ring-third on TEST ===')
    c = Counter((it['f1'], it['p2']) for it in items)
    firsts = sorted(set(it['f1'] for it in items), key=lambda f: -sum(c.get((f, t), 0) for t in (0, 1, 2)))
    tot = [sum(c.get((f, t), 0) for f in firsts) for t in (0, 1, 2)]
    P(f"  third totals: {tot}")
    for f in firsts:
        row = [c.get((f, t), 0) for t in (0, 1, 2)]
        if sum(row) >= 5:
            exp = [sum(row) * tot[t] / sum(tot) for t in (0, 1, 2)]
            P(f"  {f:6s} obs {row}  exp {[round(e,1) for e in exp]}")

    (HERE / 'results' / 'v_z4_reimplementation_c.json').write_text(
        json.dumps(out, indent=2, sort_keys=True, default=str), encoding='utf-8')
    (HERE / 'results' / 'v_z4_reimplementation_c.stdout.txt').write_text(
        '\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
