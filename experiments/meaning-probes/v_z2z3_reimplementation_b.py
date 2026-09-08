#!/usr/bin/env python3
"""Sensitivity probes for the two diffs found vs t_z2z3.py, plus adversarial
variants: conv-C rounding rules, one-sided p, comma_split reading, and a
length-matched TTR resample."""
import json, random, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ml
from v_z2z3_reimplementation_a import (build, cross_totals, effect_from_slots,
                                       run_test, seq_units, seq_chars,
                                       numeral_records, slot_A, slot_B)

ZL = r"R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt"
SEED, NPERM = 408, 10000


def mk_slot_C(mode):
    def f(rec):
        cm = rec['clock_min']
        if cm is None:
            return None
        if mode == 'banker':
            b = int(round(cm / 30.0))
        elif mode == 'halfup':
            b = int((cm + 15) // 30)
        elif mode == 'floor':
            b = int(cm // 30)
        return ('C', b % 24)
    return f


def main():
    pages = ml.parse_pages(ZL)
    labels = ml.zodiac_labels(pages)
    test = [r for r in labels if r['sign'] in ml.TEST_SIGNS]
    fit = [r for r in labels if r['sign'] in ml.FIT_SIGNS]

    # how many clocks are exactly on a 15-min tie?
    ties = [r['clock'] for r in labels if r['clock_min'] is not None
            and r['clock_min'] % 30 == 15]
    print('clock ties (xx:15 / xx:45): %d of %d labels with clocks'
          % (len(ties), sum(1 for r in labels if r['clock_min'] is not None)))
    print('  TEST ties:', sum(1 for r in test if r['clock_min'] is not None and r['clock_min'] % 30 == 15))
    print('  FIT  ties:', sum(1 for r in fit if r['clock_min'] is not None and r['clock_min'] % 30 == 15))

    print()
    for mode in ('banker', 'halfup', 'floor'):
        fn = mk_slot_C(mode)
        for level, seqfn in (('glyph', seq_units), ('char', seq_chars)):
            r = run_test(test, seqfn, fn)
            # control median
            effs = []
            npass = 0
            for name, series in ml.numeral_controls().items():
                nr = numeral_records(test, fn, series)
                c = run_test(nr, seqfn, fn)
                effs.append(c['effect'])
                npass += c['p_two_sided'] < 0.01
            effs.sort()
            med = (effs[3] + effs[4]) / 2
            print('convC[%s] %-5s TEST: same=%d eff=%+.5f p2=%.4f z=%+.2f | ctrl med=%.4f (%d/8) ratio=%+.4f'
                  % (mode, level, r['same_slot_pairs'], r['effect'], r['p_two_sided'],
                     r['z'], med, npass, r['effect'] / med))

    # one-sided p for the best cell (convC char TEST, banker + halfup)
    print()
    for mode in ('banker', 'halfup'):
        fn = mk_slot_C(mode)
        items, sim = build(test, seq_chars, fn)
        tot, cnt = cross_totals(items, sim)
        slots = [it['slot'] for it in items]
        obs, sc = effect_from_slots(items, sim, slots, tot, cnt)
        bysign = {}
        for i, it in enumerate(items):
            bysign.setdefault(it['sign'], []).append(i)
        rng = random.Random(SEED)
        ge = 0
        for _ in range(NPERM):
            perm = list(slots)
            for sg, idxs in bysign.items():
                vals = [slots[i] for i in idxs]
                rng.shuffle(vals)
                for i, v in zip(idxs, vals):
                    perm[i] = v
            e, _ = effect_from_slots(items, sim, perm, tot, cnt)
            if e >= obs - 1e-15:
                ge += 1
        print('convC[%s] char TEST one-sided p = %.4f (gate needs <0.01)'
              % (mode, (ge + 1) / (NPERM + 1)))

    # comma_split=False reading
    print()
    pages2 = ml.parse_pages(ZL, comma_split=False)
    labels2 = ml.zodiac_labels(pages2, comma_split=False)
    test2 = [r for r in labels2 if r['sign'] in ml.TEST_SIGNS]
    s2 = [r['text'] for r in labels2]
    print('comma_split=False: Z3 distinct/total = %d/%d = %.4f'
          % (len(set(s2)), len(s2), len(set(s2)) / len(s2)))
    for cn, fn in (('A', slot_A), ('B', slot_B), ('C', mk_slot_C('halfup'))):
        for level, seqfn in (('glyph', seq_units), ('char', seq_chars)):
            r = run_test(test2, seqfn, fn)
            print('  comma=False conv %s %-5s TEST: eff=%+.5f p=%.4f' % (cn, level, r['effect'], r['p_two_sided']))

    # length-matched TTR resample (each label word matched by a text word of the
    # same glyph-unit length on the zodiac pages)
    zf = set(f for fs in ml.ZODIAC_SIGNS.values() for f in fs)
    lab, txt = [], []
    for fo in zf:
        p = pages.get(fo)
        if not p:
            continue
        for l in p['loci']:
            if l['type'] == 'L':
                lab.extend(l['words'])
            elif l['type'] in ('P', 'C', 'R'):
                txt.extend(l['words'])
    bylen = {}
    for w in txt:
        bylen.setdefault(len(ml.bpe_apply(w)), []).append(w)
    need = [len(ml.bpe_apply(w)) for w in lab]
    fails = sum(1 for L in need if L not in bylen)
    lab_ttr = len(set(lab)) / len(lab)
    rng = random.Random(SEED)
    vals = []
    for _ in range(1000):
        s = []
        for L in need:
            pool = bylen.get(L)
            if pool is None:
                pool = txt
            s.append(rng.choice(pool))
        vals.append(len(set(s)) / len(s))
    m = sum(vals) / len(vals)
    sd = (sum((x - m) ** 2 for x in vals) / (len(vals) - 1)) ** 0.5
    print()
    print('TTR length-matched (with replacement): label=%.4f mean=%.4f sd=%.4f z=%+.2f  (fails=%d)'
          % (lab_ttr, m, sd, (lab_ttr - m) / sd, fails))
    # token-count-matched, without replacement (my original, harder reading)
    rng = random.Random(SEED)
    vals2 = [len(set(rng.sample(txt, len(lab)))) / len(lab) for _ in range(1000)]
    m2 = sum(vals2) / len(vals2)
    sd2 = (sum((x - m2) ** 2 for x in vals2) / (len(vals2) - 1)) ** 0.5
    print('TTR token-count-matched (no replacement): label=%.4f mean=%.4f sd=%.4f z=%+.2f'
          % (lab_ttr, m2, sd2, (lab_ttr - m2) / sd2))
    # length-matched, without replacement within length stratum
    rng = random.Random(SEED)
    vals3 = []
    from collections import Counter as C
    need_c = C(need)
    ok = all(need_c[L] <= len(bylen.get(L, [])) for L in need_c)
    if ok:
        for _ in range(1000):
            s = []
            for L, k in need_c.items():
                s.extend(rng.sample(bylen[L], k))
            vals3.append(len(set(s)) / len(s))
        m3 = sum(vals3) / len(vals3)
        sd3 = (sum((x - m3) ** 2 for x in vals3) / (len(vals3) - 1)) ** 0.5
        print('TTR length-matched (no replacement): mean=%.4f sd=%.4f z=%+.2f'
              % (m3, sd3, (lab_ttr - m3) / sd3))
    else:
        print('TTR length-matched without replacement not possible (stratum too small)')


if __name__ == '__main__':
    main()
