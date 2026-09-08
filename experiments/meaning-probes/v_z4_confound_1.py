#!/usr/bin/env python3
"""v_z4_confound_1.py — adversarial confound audit of Z4's single passing
statistic, MI(ring third; first glyph unit) on the TEST signs.

Does NOT modify t_z4.py or results/z4.json. Writes nothing except stdout and
its own scratch JSON.

Confounds probed:
  C0  reproduce the reported number; check the seed actually used
  C1  registered seed. PROTOCOL says "seed 408". t_z4.analyse() runs P2 with
      seed+1 = 409. Does the verdict depend on which of the two is used?
  C2  label length. Is `first glyph unit` a proxy for how long the label is,
      and is length itself associated with ring third?
  C3  editorial ring origin. ZL chooses where each ring starts (the '@' locus).
      A circle has no start. Rotation null: rotate each ring by a uniform
      offset, keeping the cyclic order intact. Power of that null measured on
      the same 8 numeral series.
  C4  the clean parser's dropped loci. zodiac_labels() silently closes the gap
      left by an illegible locus, so every later label's ring index shifts.
      Recompute thirds from the FULL Lz locus sequence (drops keep their slot).
  C5  fragility: leave-one-sign-out, leave-one-ring-out.
  C6  the frozen 20 merges. Is the effect a property of the merge partition or
      of the raw string? Test first-1, first-2, first-3 raw characters.
  C7  which cells carry it; is a single form type (post-hoc 'y') doing the work,
      and what is its multiplicity-corrected p?
  C8  ring-third boundary convention (floor vs nearest).
"""
import io, json, math, os, random, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML
import t_z4 as Z

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
ZL3B = os.path.join(REPO, 'data', 'corpora', 'ZL3b-n.txt')
B = 10000
ALPHA_BONF = 0.01 / 6.0

L = []
def say(*a):
    s = ' '.join(str(x) for x in a)
    L.append(s); print(s)


# ---------------------------------------------------------------- helpers --
def mi_of(pos, form):
    n = len(pos)
    P = sorted(set(pos)); F = sorted(set(form))
    pi = {v: i for i, v in enumerate(P)}; fi = {v: i for i, v in enumerate(F)}
    j = [0] * (len(P) * len(F))
    for a, b in zip(pos, form):
        j[pi[a] * len(F) + fi[b]] += 1
    return Z.mi_bits(j, len(P), len(F), n)


def perm_p(pos, form, groups, seed, B=B):
    """groups: list of index lists; permute `form` within each group.
    Integer-coded fast path; identical statistic to mi_of()."""
    n = len(pos)
    P = sorted(set(pos)); F = sorted(set(form))
    pi = {v: i for i, v in enumerate(P)}; fi = {v: i for i, v in enumerate(F)}
    pc = [pi[v] for v in pos]; fc = [fi[v] for v in form]
    nP, nF = len(P), len(F)

    def stat(fcur):
        j = [0] * (nP * nF)
        for a, b in zip(pc, fcur):
            j[a * nF + b] += 1
        return Z.mi_bits(j, nP, nF, n)

    obs = stat(fc)
    rng = random.Random(seed)
    cur = list(fc)
    nulls = []
    for _ in range(B):
        for g in groups:
            for a in range(len(g) - 1, 0, -1):
                b = rng.randint(0, a)
                cur[g[a]], cur[g[b]] = cur[g[b]], cur[g[a]]
        nulls.append(stat(cur))
    m = sum(nulls) / len(nulls)
    d = abs(obs - m)
    ge = sum(1 for v in nulls if abs(v - m) >= d - 1e-12)
    sd = math.sqrt(sum((v - m) ** 2 for v in nulls) / (len(nulls) - 1))
    return {'observed': obs, 'null_mean': m, 'debiased': obs - m,
            'z': (obs - m) / sd if sd else 0.0,
            'p': (1.0 + ge) / (1.0 + len(nulls)), 'B': B, 'seed': seed}


def group_index(keys):
    g = OrderedDict()
    for i, k in enumerate(keys):
        g.setdefault(k, []).append(i)
    return list(g.values())


def items_from(labels, level='unit'):
    return Z.build_items(labels, level)


def vecs(items):
    pos = [it['p2'] for it in items]
    form = [it['f1'] for it in items]
    keys = [(it['sign'], it['ring']) for it in items]
    return pos, form, keys


# ================================================================= C0 / C1 ==
lab = Z.load_labels(ZL3B, True)
tst = [r for r in lab if r['sign'] in ML.TEST_SIGNS]
fit = [r for r in lab if r['sign'] in ML.FIT_SIGNS]
it_t = items_from(tst)

say('=' * 74)
say('C0  reproduce  MI(ring third; first glyph unit), TEST, ZL3b, unit level')
pos, form, keys = vecs(it_t)
g = group_index(keys)
r409 = perm_p(pos, form, g, 409)
say('  n=%d  rings=%d  prefix types=%d' % (len(it_t), len(g), len(set(form))))
say('  seed 409 (the seed t_z4 actually used for P2): MI=%.4f  debiased=%+.4f  p=%.5f  %s'
    % (r409['observed'], r409['debiased'], r409['p'],
       'PASS' if r409['p'] < ALPHA_BONF else 'FAIL'))
exact = Z.mi_focus(it_t, 'P2', 'f1', 409, B)
say('  exact replay through t_z4.mi_focus(seed=409): MI=%.6f p=%.5f (reported 0.0015998)'
    % (exact['observed'], exact['p_two_sided']))
say('  NOTE my own RNG stream differs from t_z4\'s, so p differs in the last')
say('  digits; the observed statistic is identical, which is the thing that')
say('  matters. Every number below uses my stream consistently.')

say('')
say('C1  THE REGISTERED SEED. PROTOCOL: "Permutation tests use 10,000 draws')
say('    and seed 408 unless stated." t_z4.analyse() calls run_position(...,')
say('    seed+1) for P2, i.e. seed 409. Re-run the same statistic at 408:')
r408 = perm_p(pos, form, g, 408)
say('  seed 408 (the registered seed): p=%.5f  %s'
    % (r408['p'], 'PASS' if r408['p'] < ALPHA_BONF else 'FAIL'))
seedtab = []
for sd in range(400, 440):
    rr = perm_p(pos, form, g, sd, B=B)
    seedtab.append((sd, rr['p'], rr['p'] < ALPHA_BONF))
npass = sum(1 for _, _, ok in seedtab if ok)
say('  40 seeds 400..439 at the registered B=10000: %d/%d clear the threshold'
    % (npass, len(seedtab)))
say('  p range over those seeds: %.5f .. %.5f'
    % (min(p for _, p, _ in seedtab), max(p for _, p, _ in seedtab)))

# ==================================================================== C2 ====
say('')
say('=' * 74)
say('C2  LENGTH CONFOUND')
lens = [len(Z.label_seq(r, 'unit')) for r in tst]
rawlens = [len(''.join(r['words'])) for r in tst]
# association of length with ring third
say('  mean glyph-unit length by ring third:')
for t in (0, 1, 2):
    v = [l for l, it in zip(lens, it_t) if it['p2'] == t]
    say('    third %d  n=%3d  mean units %.3f  mean raw chars %.3f'
        % (t, len(v), sum(v) / len(v),
           sum(rl for rl, it in zip(rawlens, it_t) if it['p2'] == t) / len(v)))
rlen = perm_p(pos, [min(l, 6) for l in lens], g, 409)
say('  MI(ring third; glyph-unit length capped at 6): MI=%.4f debiased=%+.4f p=%.5f'
    % (rlen['observed'], rlen['debiased'], rlen['p']))
rlenr = perm_p(pos, [min(l, 9) for l in rawlens], g, 409)
say('  MI(ring third; raw char length capped at 9):   MI=%.4f debiased=%+.4f p=%.5f'
    % (rlenr['observed'], rlenr['debiased'], rlenr['p']))
# length-stratified null: permute only among labels of equal length within ring
keys_ls = [((it['sign'], it['ring']), min(l, 6)) for it, l in zip(it_t, lens)]
g_ls = [x for x in group_index(keys_ls) if len(x) > 1]
nfree = sum(len(x) for x in g_ls)
rls = perm_p(pos, form, g_ls, 409)
say('  length-stratified null (permute only within ring x equal length):')
say('    %d of %d labels are exchangeable at all (%d blocks of size>1)'
    % (nfree, len(it_t), len(g_ls)))
say('    MI=%.4f  null_mean=%.4f  debiased=%+.4f  p=%.5f  %s'
    % (rls['observed'], rls['null_mean'], rls['debiased'], rls['p'],
       'PASS' if rls['p'] < ALPHA_BONF else 'FAIL'))
say('    NOTE: this null is strictly weaker (fewer exchangeable items), so a')
say('    failure here is NOT by itself proof of a length confound.')

# ==================================================================== C3 ====
say('')
say('=' * 74)
say('C3  EDITORIAL RING ORIGIN — rotation null')
say('  ZL fixes where each ring starts (locus with pos char "@"). A drawn ring')
say('  has no intrinsic first label. Under a rotation null the cyclic order of')
say('  the labels is preserved exactly and only the origin is randomised.')


def rotation_p(items, seed, B=B):
    keys = [(it['sign'], it['ring']) for it in items]
    g = group_index(keys)
    # each group is already in ring order? enforce it
    g = [sorted(x, key=lambda i: items[i]['idx_in_ring']) for x in g]
    form = [it['f1'] for it in items]

    def thirds(offsets):
        pos = [0] * len(items)
        for grp, off in zip(g, offsets):
            s = len(grp)
            for k, i in enumerate(grp):
                pos[i] = min(2, (((k + off) % s) * 3) // s)
        return pos
    obs = mi_of(thirds([0] * len(g)), form)
    rng = random.Random(seed)
    nulls = []
    for _ in range(B):
        offs = [rng.randrange(len(x)) for x in g]
        nulls.append(mi_of(thirds(offs), form))
    m = sum(nulls) / len(nulls)
    d = abs(obs - m)
    ge = sum(1 for v in nulls if abs(v - m) >= d - 1e-12)
    return {'observed': obs, 'null_mean': m, 'debiased': obs - m,
            'p': (1.0 + ge) / (1.0 + len(nulls))}


rot = rotation_p(it_t, 409)
say('  observed MI=%.4f   rotation-null mean=%.4f   debiased=%+.4f   p=%.5f  %s'
    % (rot['observed'], rot['null_mean'], rot['debiased'], rot['p'],
       'PASS' if rot['p'] < ALPHA_BONF else 'FAIL'))
say('  power of the rotation null on the 8 numeral series in the same layout:')
ctrl = ML.numeral_controls()
rotpow = OrderedDict()
for nm, series in ctrl.items():
    itn = items_from(Z.numeral_layout(tst, series))
    rr = rotation_p(itn, 409)
    rotpow[nm] = rr
    say('    %-20s MI=%.4f  null_mean=%.4f  debiased=%+.4f  p=%.5f  %s'
        % (nm, rr['observed'], rr['null_mean'], rr['debiased'], rr['p'],
           'detected' if rr['p'] < ALPHA_BONF else '-'))
nrot = sum(1 for v in rotpow.values() if v['p'] < ALPHA_BONF)
say('  rotation-null power: %d/8 numeral systems detected' % nrot)

# ==================================================================== C4 ====
say('')
say('=' * 74)
say('C4  DROPPED ILLEGIBLE LOCI SHIFT THE RING INDEX')
pages = ML.parse_pages(ZL3B, comma_split=True)


def labels_keeping_slots(pages):
    """As ML.zodiac_labels, but a locus whose words vanish under the clean
    parser still consumes its slot in the ring, so the surviving labels keep
    their true circular position."""
    out = []
    for sign, folios in ML.ZODIAC_SIGNS.items():
        ring = -1; idx_in_sign = 0
        for fo in folios:
            p = pages.get(fo)
            if p is None:
                continue
            for l in p['loci']:
                if l['type'] != 'L' or l['sub'] != 'z':
                    continue
                if l['pos'] == '@' or ring < 0:
                    ring += 1; idx_in_ring = 0
                if l['words']:
                    out.append({'sign': sign, 'page': fo, 'locus_n': l['n'],
                                'ring': ring, 'idx_in_ring': idx_in_ring,
                                'idx_in_sign': idx_in_sign,
                                'clock': l['clock'], 'clock_min': None,
                                'words': l['words'],
                                'text': ' '.join(l['words']),
                                'n_words': len(l['words']),
                                'slot_size_marker': True})
                    idx_in_sign += 1
                idx_in_ring += 1        # <-- dropped loci keep their slot
        # ring sizes must be the full slot count; recomputed below
    return out


# count drops and their position
drops = OrderedDict()
for sign, folios in ML.ZODIAC_SIGNS.items():
    ring = -1
    for fo in folios:
        p = pages.get(fo)
        if p is None:
            continue
        for l in p['loci']:
            if l['type'] != 'L' or l['sub'] != 'z':
                continue
            if l['pos'] == '@' or ring < 0:
                ring += 1; idx = 0
            drops.setdefault((sign, ring), []).append(1 if l['words'] else 0)
            idx += 1
ndrop_test = sum(v.count(0) for k, v in drops.items() if k[0] in ML.TEST_SIGNS)
ntot_test = sum(len(v) for k, v in drops.items() if k[0] in ML.TEST_SIGNS)
say('  TEST signs: %d Lz loci, %d dropped by the clean parser (%.1f%%)'
    % (ntot_test, ndrop_test, 100.0 * ndrop_test / ntot_test))
# where in the ring do drops fall (using full-slot thirds)?
dc = Counter()
for k, v in drops.items():
    if k[0] not in ML.TEST_SIGNS:
        continue
    s = len(v)
    for i, keep in enumerate(v):
        if not keep:
            dc[min(2, (i * 3) // s)] += 1
say('  dropped loci by full-slot ring third: %s' % dict(dc))

lab_slots = labels_keeping_slots(pages)
tst_slots = [r for r in lab_slots if r['sign'] in ML.TEST_SIGNS]
# ring size must count ALL slots, not only survivors
full_size = {k: len(v) for k, v in drops.items()}
it_s = []
for r in tst_slots:
    seq = Z.label_seq(r, 'unit')
    if not seq:
        continue
    s = full_size[(r['sign'], r['ring'])]
    it_s.append({'sign': r['sign'], 'ring': r['ring'],
                 'idx_in_ring': r['idx_in_ring'], 'ring_size': s,
                 'p2': min(2, (r['idx_in_ring'] * 3) // s),
                 'f1': seq[0], 'f2': seq[-1]})
pos_s = [it['p2'] for it in it_s]
form_s = [it['f1'] for it in it_s]
g_s = group_index([(it['sign'], it['ring']) for it in it_s])
rs = perm_p(pos_s, form_s, g_s, 409)
say('  thirds recomputed with dropped loci keeping their slot:')
say('    n=%d  MI=%.4f  null_mean=%.4f  debiased=%+.4f  p=%.5f  %s'
    % (len(it_s), rs['observed'], rs['null_mean'], rs['debiased'], rs['p'],
       'PASS' if rs['p'] < ALPHA_BONF else 'FAIL'))
nmoved = sum(1 for a, b in zip(it_t, it_s) if a['p2'] != b['p2'])
say('    %d of %d labels change ring third under this reading' % (nmoved, len(it_s)))

# ==================================================================== C5 ====
say('')
say('=' * 74)
say('C5  FRAGILITY')
say('  leave-one-sign-out (TEST signs):')
loso = OrderedDict()
for s in ML.TEST_SIGNS:
    sub = [r for r in tst if r['sign'] != s]
    its = items_from(sub)
    p_, f_, k_ = vecs(its)
    rr = perm_p(p_, f_, group_index(k_), 409)
    loso[s] = rr
    say('    drop %-12s n=%3d  debiased=%+.4f  p=%.5f  %s'
        % (s, len(its), rr['debiased'], rr['p'],
           'PASS' if rr['p'] < ALPHA_BONF else 'FAIL'))
say('  leave-one-ring-out (12 TEST rings):')
lororesults = []
rings = sorted({(it['sign'], it['ring']) for it in it_t})
for rk in rings:
    sub = [r for r in tst if (r['sign'], r['ring']) != rk]
    its = items_from(sub)
    p_, f_, k_ = vecs(its)
    rr = perm_p(p_, f_, group_index(k_), 409)
    lororesults.append((rk, len(its), rr['p'], rr['p'] < ALPHA_BONF))
    say('    drop %-22s n=%3d  debiased=%+.4f  p=%.5f  %s'
        % ('%s/ring%d' % rk, len(its), rr['debiased'], rr['p'],
           'PASS' if rr['p'] < ALPHA_BONF else 'FAIL'))
say('  leave-one-ring-out: %d of %d drops still clear the threshold'
    % (sum(1 for _, _, _, ok in lororesults if ok), len(lororesults)))

# ==================================================================== C6 ====
say('')
say('=' * 74)
say('C6  IS IT THE FROZEN MERGE LIST? first n raw EVA characters as the form')
for k in (1, 2, 3):
    f_ = [''.join(r['words'])[:k] for r in tst]
    rr = perm_p(pos, f_, g, 409)
    say('  first %d raw char(s): types=%2d  MI=%.4f  debiased=%+.4f  p=%.5f  %s'
        % (k, len(set(f_)), rr['observed'], rr['debiased'], rr['p'],
           'PASS' if rr['p'] < ALPHA_BONF else 'FAIL'))
say('  (t_z4 registered robustness check = first 1 raw char, p=0.08259)')

# ==================================================================== C7 ====
say('')
say('=' * 74)
say('C7  WHICH CELLS CARRY IT — per-form-type contribution and its multiplicity')
types = sorted(set(form))
say('  one-vs-rest permutation p for every prefix type (same null, seed 409):')
percell = []
for tp in types:
    ind = [1 if x == tp else 0 for x in form]
    if sum(ind) < 3:
        continue
    rr = perm_p(pos, ind, g, 409)
    cnt = [sum(1 for a, b in zip(pos, ind) if a == t and b) for t in (0, 1, 2)]
    percell.append((tp, sum(ind), cnt, rr['p']))
for tp, n, cnt, p in sorted(percell, key=lambda x: x[3]):
    say('    %-8s n=%3d  by third %s  p=%.5f  %s'
        % (tp, n, cnt, p, '<-- ' if p < 0.05 else ''))
say('  %d types tested; a Bonferroni-corrected 0.01 over them is %.5f'
    % (len(percell), 0.01 / len(percell)))

# ==================================================================== C8 ====
say('')
say('=' * 74)
say('C8  RING-THIRD BOUNDARY CONVENTION')


def third_round(i, s):
    return min(2, int(round(i * 3.0 / s - 1e-9)))


def third_ceil(i, s):
    return min(2, int(math.ceil((i + 1) * 3.0 / s)) - 1)


for nm, fn in (('floor (registered)', lambda i, s: min(2, (i * 3) // s)),
               ('nearest', third_round),
               ('ceil', third_ceil)):
    p_ = [fn(it['idx_in_ring'], it['ring_size']) for it in it_t]
    rr = perm_p(p_, form, g, 409)
    say('  %-20s marginal %s  MI=%.4f  debiased=%+.4f  p=%.5f  %s'
        % (nm, dict(Counter(p_)), rr['observed'], rr['debiased'], rr['p'],
           'PASS' if rr['p'] < ALPHA_BONF else 'FAIL'))

# =============================================================== survivor ===
say('')
say('=' * 74)
say('C9  SURVIVORSHIP / SAMPLE SHAPE')
sz = Counter()
for it in it_t:
    sz[(it['sign'], it['ring'])] = it['ring_size']
say('  TEST ring sizes: %s' % sorted(sz.values()))
say('  FIT n=%d, TEST n=%d; Capricorn and Aquarius are lost, so 10 of 12 signs')
say('  survive and the "rank block 21-30" cell is thin everywhere.')

out = {'C1_seed408_p': r408['p'], 'C1_seed409_p': r409['p'],
       'C1_seeds_400_439_pass': npass,
       'C2_len_mi_p': rlen['p'], 'C2_rawlen_mi_p': rlenr['p'],
       'C2_length_stratified_p': rls['p'],
       'C3_rotation_p': rot['p'],
       'C3_rotation_power': {k: v['p'] for k, v in rotpow.items()},
       'C4_slotkeeping_p': rs['p'], 'C4_n_moved': nmoved,
       'C4_drops_by_third': dict(dc),
       'C5_loso': {k: v['p'] for k, v in loso.items()},
       'C5_loro_pass': sum(1 for _, _, _, ok in lororesults if ok),
       'C7_percell': [(t, n, c, p) for t, n, c, p in percell]}
with io.open(os.path.join(HERE, 'results', 'v_z4_confound_1.json'), 'w',
             encoding='utf-8') as f:
    json.dump(out, f, indent=1, default=str)
with io.open(os.path.join(HERE, 'results', 'v_z4_confound_1.stdout.txt'), 'w',
             encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n')
