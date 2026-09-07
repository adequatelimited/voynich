#!/usr/bin/env python3
"""Adversarial confound probes for Z2.  Read-only; imports the test's own
Design machinery so the statistic is byte-identical to the one under attack.

Every probe asks: could a confound be MASKING a real same-slot effect?

  A2  convention A recomputed on the FULL Lz locus sequence (the 5 loci the
      clean parser drops currently COMPRESS the index counter, shifting every
      later label in Libra by -2 and in Sagittarius by -1).
  Brev convention B with rings ranked inner-first (the ZL comment on f72v3
      says the 30 nymphs are counted "inner to outer", the opposite of the
      transcription order the test assumed).
  Aend index counted from the END of the sign.
  ROT  rotation-invariant version of A: best cyclic offset per sign pair,
      max-statistic permutation null (a per-sign numbering that starts at a
      different nymph in each sign is invisible to A, B and C).
  ROTC rotation-invariant version of C: best global clock offset per sign pair.
  W1   first word only (multi-word labels are concatenated by the test, which
      dilutes any slot signal carried by one word).
  SW   single-word labels only.
  CS   comma_split=False reading of the uncertain-space mark.

Power probes:
  MUT  numeral controls with per-character mutation of EVERY item (the test's
       controls make same-slot items byte-identical, which is the strongest
       possible signal; a real numbering with spelling variation is weaker).
  IMP  signal implantation into the REAL Voynich labels: force a fraction f of
       TEST labels to equal the same-slot label of the first sign, keeping all
       other material identical, and ask at what f the test fires.
"""
import sys, math, json, random, statistics
from collections import defaultdict, OrderedDict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import meaning_lib as M
import t_z2z3 as T          # imports only; main() is not run

ZL3B = T.ZL3B
NPERM = 10000
NPERM_SWEEP = 2000
SEED = M.SEED

pages = M.parse_pages(ZL3B)
labels = M.zodiac_labels(pages)
pages_nc = M.parse_pages(ZL3B, comma_split=False)
labels_nc = M.zodiac_labels(pages_nc, comma_split=False)

print('input sha256 ZL3b   ', M.sha256(ZL3B))
print('input sha256 lib    ', M.sha256(HERE / 'meaning_lib.py'))
print('input sha256 t_z2z3 ', M.sha256(HERE / 't_z2z3.py'))
print('nperm %d (sweeps %d), seed %d' % (NPERM, NPERM_SWEEP, SEED))

RES = OrderedDict()


# ------------------------------------------------- repaired index (drops) ---
def full_index_map(pages):
    """sign -> {(page, locus_n): true index among ALL Lz loci of that sign}
    and the same for ring-internal index, counting dropped loci."""
    out = {}
    for sign, folios in M.ZODIAC_SIGNS.items():
        idx = 0
        ring = -1
        iir = 0
        m = {}
        for fo in folios:
            p = pages.get(fo)
            if not p:
                continue
            for l in p['loci']:
                if l['type'] != 'L' or l['sub'] != 'z':
                    continue
                if l['pos'] == '@' or ring < 0:
                    ring += 1
                    iir = 0
                m[(fo, l['n'])] = (idx, ring, iir)
                idx += 1
                iir += 1
        out[sign] = m
    return out


FULL = full_index_map(pages)
NRINGS = {s: max(r for _, r, _ in m.values()) + 1 for s, m in FULL.items()}


def slot_alt(rec, mode):
    key = (rec['page'], rec['locus_n'])
    idx, ring, iir = FULL[rec['sign']][key]
    if mode == 'A2':
        return idx
    if mode == 'B2':                       # full-index ring/rank, outer first
        return (ring, iir)
    if mode == 'Brev':                     # inner-first ring rank
        return (NRINGS[rec['sign']] - 1 - ring, iir)
    if mode == 'Aend':
        n = len(FULL[rec['sign']])
        return n - 1 - idx
    raise ValueError(mode)


def build_alt(labels, signs, mode, rep):
    fn = T.REPS[rep]
    names, slots, items = [], [], []
    for sg in signs:
        recs = [r for r in labels if r['sign'] == sg]
        ss, ii = [], []
        for r in recs:
            ss.append(slot_alt(r, mode))
            ii.append(fn(r['words']))
        if ss:
            names.append(sg); slots.append(ss); items.append(ii)
    return T.Design(names, slots, items) if len(names) >= 2 else None


print('\n' + '=' * 74)
print('PROBE 1  alternative slot conventions (masking checks)')
print('=' * 74)
print('  the frozen conventions of the protocol, for reference:')
for conv in 'ABC':
    for rep in ('unit', 'char'):
        d = T.build_voynich_design(labels, M.TEST_SIGNS, conv, rep)
        r = d.run(NPERM, SEED)
        print('   conv %-4s %-4s TEST  pairs %4d  effect %+.5f  z=%+.2f  p2=%.4f'
              % (conv, rep, r['n_same_pairs'], r['effect'], r['z'], r['p_two_sided']))
        RES['frozen_%s_%s' % (conv, rep)] = r

for mode, desc in (('A2', 'index within sign counting the 5 parser-dropped loci'),
                   ('B2', 'ring rank outer-first, index counting dropped loci'),
                   ('Brev', 'ring rank INNER-first (ZL comment reading)'),
                   ('Aend', 'index counted from the end of the sign')):
    print('  %s  %s' % (mode, desc))
    for rep in ('unit', 'char'):
        for split, signs in (('FIT', M.FIT_SIGNS), ('TEST', M.TEST_SIGNS)):
            d = build_alt(labels, signs, mode, rep)
            r = d.run(NPERM, SEED)
            print('   %-5s %-4s %-4s  pairs %4d  effect %+.5f  z=%+.2f  p2=%.4f'
                  % (mode, rep, split, r['n_same_pairs'], r['effect'], r['z'],
                     r['p_two_sided']))
            RES['%s_%s_%s' % (mode, rep, split)] = r


# ----------------------------------------------- rotation-invariant probes --
def rot_stat(groups_items, sim, groups_pos, assign):
    """max-over-cyclic-offset mean similarity, averaged over sign pairs,
    minus the overall cross-sign mean similarity."""
    G = len(groups_pos)
    tot, ntot = 0.0, 0
    best_sum, npair = 0.0, 0
    for i in range(G):
        for j in range(i + 1, G):
            gi, gj = groups_pos[i], groups_pos[j]
            ni, nj = len(gi), len(gj)
            for a in gi:
                for b in gj:
                    tot += sim[assign[a]][assign[b]]
                    ntot += 1
            m = min(ni, nj)
            best = None
            for d in range(nj):
                s = 0.0
                for k in range(m):
                    s += sim[assign[gi[k]]][assign[gj[(k + d) % nj]]]
                v = s / m
                if best is None or v > best:
                    best = v
            best_sum += best
            npair += 1
    return best_sum / npair - tot / ntot


def run_rot(labels, signs, rep, nperm=NPERM, seed=SEED, mode='A'):
    """mode 'A': cyclic offsets over manuscript index.
       mode 'C': best global clock offset (30-min steps) per sign pair."""
    fn = T.REPS[rep]
    groups_items, groups_slots = [], []
    for sg in signs:
        recs = [r for r in labels if r['sign'] == sg]
        if mode == 'C':
            recs = [r for r in recs if r['clock_min'] is not None]
        groups_items.append([fn(r['words']) for r in recs])
        groups_slots.append([T.slot_of(r, 'C') if mode == 'C' else i
                             for i, r in enumerate(recs)])
    items, groups_pos = [], []
    p = 0
    for gi in groups_items:
        grp = []
        for it in gi:
            items.append(it); grp.append(p); p += 1
        groups_pos.append(grp)
    n = p
    sim = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            v = M.lcs_sim(items[i], items[j])
            sim[i][j] = v; sim[j][i] = v

    if mode == 'C':
        def stat(assign):
            G = len(groups_pos)
            tot, ntot, best_sum, npair = 0.0, 0, 0.0, 0
            for i in range(G):
                for j in range(i + 1, G):
                    gi, gj = groups_pos[i], groups_pos[j]
                    si = [groups_slots[i][k] for k in range(len(gi))]
                    sj = [groups_slots[j][k] for k in range(len(gj))]
                    allsum, alln = 0.0, 0
                    for a in gi:
                        for b in gj:
                            allsum += sim[assign[a]][assign[b]]; alln += 1
                    tot += allsum; ntot += alln
                    best = None
                    for d in range(24):
                        s, c = 0.0, 0
                        for x, a in enumerate(gi):
                            for y, b in enumerate(gj):
                                if (sj[y] + d) % 24 == si[x]:
                                    s += sim[assign[a]][assign[b]]; c += 1
                        if c:
                            v = s / c - (allsum - s) / (alln - c) if alln > c else 0.0
                            if best is None or v > best:
                                best = v
                    if best is not None:
                        best_sum += best; npair += 1
            return best_sum / npair if npair else 0.0
    else:
        def stat(assign):
            return rot_stat(groups_items, sim, groups_pos, assign)

    ident = list(range(n))
    obs = stat(ident)
    rng = random.Random(seed)
    a = list(range(n))
    ge = 0
    nulls = []
    for _ in range(nperm):
        for grp in groups_pos:
            vals = [a[q] for q in grp]
            rng.shuffle(vals)
            for q, v in zip(grp, vals):
                a[q] = v
        e = stat(a)
        nulls.append(e)
        if e >= obs - 1e-15:
            ge += 1
    mu = statistics.fmean(nulls); sd = statistics.pstdev(nulls)
    return {'n_items': n, 'stat': obs, 'null_mean': mu, 'null_sd': sd,
            'z': (obs - mu) / sd if sd else None,
            'p_one_sided_upper': (1 + ge) / (nperm + 1.0), 'nperm': nperm}


print('\n' + '=' * 74)
print('PROBE 2  rotation invariance (a per-sign numbering with a different')
print('         starting nymph is invisible to conventions A, B and C)')
print('=' * 74)
for mode in ('A', 'C'):
    for rep in ('unit', 'char'):
        r = run_rot(labels, M.TEST_SIGNS, rep, nperm=NPERM_SWEEP, mode=mode)
        print('  ROT-%s %-4s TEST  best-offset stat %+.5f  null %+.5f+-%.5f  '
              'z=%+.2f  p(upper)=%.4f'
              % (mode, rep, r['stat'], r['null_mean'], r['null_sd'], r['z'],
                 r['p_one_sided_upper']))
        RES['ROT%s_%s_TEST' % (mode, rep)] = r


# --------------------------------------------------- representation probes --
print('\n' + '=' * 74)
print('PROBE 3  representation / parser readings')
print('=' * 74)


def build_custom(labels, signs, conv, rep, wordsel):
    fn = T.REPS[rep]
    names, slots, items = [], [], []
    for sg in signs:
        recs = [r for r in labels if r['sign'] == sg]
        ss, ii = [], []
        for r in recs:
            s = T.slot_of(r, conv)
            ws = wordsel(r)
            if s is None or not ws:
                continue
            ss.append(s); ii.append(fn(ws))
        if ss:
            names.append(sg); slots.append(ss); items.append(ii)
    return T.Design(names, slots, items) if len(names) >= 2 else None


for name, sel, lab in (('W1  first word only', lambda r: r['words'][:1], labels),
                       ('SW  single-word labels only',
                        lambda r: r['words'] if len(r['words']) == 1 else [], labels),
                       ('CS  comma_split=False', lambda r: r['words'], labels_nc)):
    for conv in 'ABC':
        for rep in ('unit',):
            d = build_custom(lab, M.TEST_SIGNS, conv, rep, sel)
            if d is None:
                print('  %-28s conv %s %-4s  no design' % (name, conv, rep)); continue
            r = d.run(NPERM, SEED)
            print('  %-28s conv %s %-4s n=%3d pairs %4d effect %+.5f p2=%.4f'
                  % (name, conv, rep, r['n_items'], r['n_same_pairs'],
                     r['effect'], r['p_two_sided']))
            RES['%s_%s_%s' % (name.split()[0], conv, rep)] = r

json.dump(RES, open(HERE / 'results' / '_v_z2z3_confound_2.json', 'w'),
          indent=1, default=str)
print('\nwrote results/_v_z2z3_confound_2.json')
