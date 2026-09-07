#!/usr/bin/env python3
"""t_z4.py — Z4, positional morphology of the zodiac nymph labels.

Pre-registration: experiments/meaning-probes/PROTOCOL.md, section "Z4".

    Statistic. Mutual information between position and form:
    positions = {rank block 1-10 / 11-20 / 21-30 within sign} x {thirds of the
    ring}, forms = {first glyph unit} x {last glyph unit}. Four combinations.
    Null. 10,000 permutations of rank within sign / within ring.
    Gate Z4. Any MI with permutation p < 0.01 after Bonferroni over the four
    combinations is reported as positional structure. Otherwise: none.

Plus, under the same gate and the same Bonferroni family (as a 5th and 6th
test), chi-square of the prefix inventory by rank block and of the suffix
inventory by rank block, with the same permutation null.

Stdlib only. Seed 408. Deterministic: same input -> same JSON.

--------------------------------------------------------------------------
AMBIGUITIES IN THE PRE-REGISTRATION AND THE READING TAKEN (harder one wins)
--------------------------------------------------------------------------
A1. "thirds of the ring". Taken literally over EVERY ring that carries a
    label, including short rings (4, 5, 1 labels) where a third is a coarse
    notion.  A restriction to rings with >= 6 labels is reported as a
    sensitivity, not as the gated number.
A2. "form" of a multi-word label locus.  The label is treated as ONE string:
    the glyph-unit sequence is the concatenation of the units of all its
    words.  first unit = first unit of the first word, last unit = last unit
    of the last word.  (253/294 loci are single-word anyway.)
A3. "two-sided p" for a non-negative statistic.  Taken as deviation from the
    null mean in EITHER direction:
        p = (1 + #{ |T_null - mean_null| >= |T_obs - mean_null| }) / (1 + B).
    This is strictly harder than the one-sided upper tail (it roughly doubles
    p for an upper-tail effect) and it is the only reading under which the
    word "two-sided" means anything for MI.
A4. Bonferroni family.  The task adds the two chi-square tests to the family,
    so the family is SIX, not four: alpha = 0.01 / 6 = 0.0016667.  Using six
    is harder than using four.
A5. FIT/TEST.  The gate is evaluated on the TEST signs only (Leo, Virgo,
    Libra, Scorpius, Sagittarius).  FIT is reported but never gated on.
A6. Permutation of a whole label.  f1 and f2 of one label move together under
    the permutation (the label is the unit that is relocated, not its
    letters).  Marginals of both position and form are therefore fixed, which
    is the correct exchangeability model here.
A7. The uncertain-space mark ",".  Primary = comma_split=True (the
    conservative reading fixed by the parser provenance).  comma_split=False
    is reported as a sensitivity.
A8. Level.  Primary = glyph-unit level (20 frozen T2 merges).  Raw EVA
    character level is the registered robustness check.
"""
import io
import json
import math
import os
import random
import sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
ZL3B = os.path.join(REPO, 'data', 'corpora', 'ZL3b-n.txt')
GC2A = os.path.join(REPO, 'data', 'corpora', 'GC2a-n.txt')
RESULTS = os.path.join(HERE, 'results')

SEED = ML.SEED            # 408
B = 10000                 # permutation draws
N_FAMILY = 6              # Bonferroni family: 4 MI + 2 chi-square
ALPHA = 0.01
ALPHA_BONF = ALPHA / N_FAMILY

_out_lines = []


def say(*a):
    s = ' '.join(str(x) for x in a)
    _out_lines.append(s)
    print(s)


# ============================================================ statistics ===

def mi_bits(joint, npos, nform, n):
    """Mutual information in bits from a flat joint count array of shape
    (npos, nform) laid out row-major, with n = total count."""
    rows = [0] * npos
    cols = [0] * nform
    for i in range(npos):
        base = i * nform
        for j in range(nform):
            c = joint[base + j]
            if c:
                rows[i] += c
                cols[j] += c
    tot = 0.0
    for i in range(npos):
        ri = rows[i]
        if not ri:
            continue
        base = i * nform
        for j in range(nform):
            c = joint[base + j]
            if c:
                tot += c * math.log2((c * n) / (ri * cols[j]))
    return tot / n


def chi2_stat(joint, npos, nform, n):
    """Pearson chi-square of the same contingency table (all cells, zeros
    included).  Distributional validity is irrelevant: the null is the
    permutation null, not the chi-square distribution."""
    rows = [0] * npos
    cols = [0] * nform
    for i in range(npos):
        base = i * nform
        for j in range(nform):
            c = joint[base + j]
            if c:
                rows[i] += c
                cols[j] += c
    tot = 0.0
    for i in range(npos):
        ri = rows[i]
        if not ri:
            continue
        base = i * nform
        for j in range(nform):
            e = ri * cols[j] / n
            if e <= 0:
                continue
            d = joint[base + j] - e
            tot += d * d / e
    return tot


def two_sided_p(obs, nulls):
    """A3: deviation from the null mean in either direction, +1 smoothing."""
    m = sum(nulls) / len(nulls)
    d = abs(obs - m)
    ge = sum(1 for v in nulls if abs(v - m) >= d - 1e-12)
    return (1.0 + ge) / (1.0 + len(nulls)), m


# ====================================================== item construction ==

def label_seq(rec, level):
    """A2: the label locus as ONE sequence (units or raw EVA characters)."""
    seq = []
    for w in rec['words']:
        seq.extend(ML.bpe_apply(w) if level == 'unit' else list(w))
    return seq


def rank_block(rank1):
    """P1: rank block within sign, 1-10 / 11-20 / 21-30 (1-based rank)."""
    return min(2, (rank1 - 1) // 10)


def ring_third(idx0, ring_size):
    """P2: thirds of the ring (0-based index within the ring)."""
    return min(2, (idx0 * 3) // ring_size)


def build_items(labels, level):
    """One record per label locus with its two positions and two forms."""
    ringsz = Counter((r['sign'], r['ring']) for r in labels)
    items = []
    for r in labels:
        seq = label_seq(r, level)
        if not seq:
            continue
        items.append({
            'sign': r['sign'], 'ring': r['ring'],
            'rank1': r['idx_in_sign'] + 1,
            'idx_in_ring': r['idx_in_ring'],
            'ring_size': ringsz[(r['sign'], r['ring'])],
            'p1': rank_block(r['idx_in_sign'] + 1),
            'p2': ring_third(r['idx_in_ring'], ringsz[(r['sign'], r['ring'])]),
            'f1': seq[0], 'f2': seq[-1],
            'text': r['text'],
        })
    return items


# ======================================================= permutation core ==

def run_position(items, posdef, seed, B=B):
    """All statistics for one position definition, sharing one permutation
    stream (permuting a label relocates its f1 and f2 together, A6).

    posdef 'P1': groups = signs, slots ordered by rank within sign.
    posdef 'P2': groups = (sign, ring), slots ordered by index within ring.
    """
    if posdef == 'P1':
        keyf = lambda it: it['sign']
        ordf = lambda it: it['rank1']
        posf = lambda it: it['p1']
    else:
        keyf = lambda it: (it['sign'], it['ring'])
        ordf = lambda it: it['idx_in_ring']
        posf = lambda it: it['p2']

    groups = OrderedDict()
    for i, it in enumerate(items):
        groups.setdefault(keyf(it), []).append(i)
    for k in groups:
        groups[k].sort(key=lambda i: ordf(items[i]))

    pos_flat, idx_flat, segs = [], [], []
    for k, mem in groups.items():
        s = len(idx_flat)
        for i in mem:
            pos_flat.append(posf(items[i]))
            idx_flat.append(i)
        segs.append((s, len(idx_flat)))

    n = len(idx_flat)
    f1_lex = sorted({items[i]['f1'] for i in idx_flat})
    f2_lex = sorted({items[i]['f2'] for i in idx_flat})
    f1_id = {v: j for j, v in enumerate(f1_lex)}
    f2_id = {v: j for j, v in enumerate(f2_lex)}
    F1, F2 = len(f1_lex), len(f2_lex)
    f1_flat = [f1_id[items[i]['f1']] for i in idx_flat]
    f2_flat = [f2_id[items[i]['f2']] for i in idx_flat]
    npos = 3

    def joints(perm):
        j1 = [0] * (npos * F1)
        j2 = [0] * (npos * F2)
        for k in range(n):
            p = pos_flat[k]
            src = perm[k]
            j1[p * F1 + f1_flat[src]] += 1
            j2[p * F2 + f2_flat[src]] += 1
        return j1, j2

    ident = list(range(n))
    oj1, oj2 = joints(ident)
    obs = {
        ('MI', 'F1'): mi_bits(oj1, npos, F1, n),
        ('MI', 'F2'): mi_bits(oj2, npos, F2, n),
        ('CHI2', 'F1'): chi2_stat(oj1, npos, F1, n),
        ('CHI2', 'F2'): chi2_stat(oj2, npos, F2, n),
    }

    rng = random.Random(seed)
    nulls = {k: [] for k in obs}
    perm = list(range(n))
    for _ in range(B):
        for (s, e) in segs:                      # Fisher-Yates inside a group
            for a in range(e - 1, s, -1):
                b = rng.randint(s, a)
                perm[a], perm[b] = perm[b], perm[a]
        j1, j2 = joints(perm)
        nulls[('MI', 'F1')].append(mi_bits(j1, npos, F1, n))
        nulls[('MI', 'F2')].append(mi_bits(j2, npos, F2, n))
        nulls[('CHI2', 'F1')].append(chi2_stat(j1, npos, F1, n))
        nulls[('CHI2', 'F2')].append(chi2_stat(j2, npos, F2, n))

    res = {}
    for k, o in obs.items():
        p, m = two_sided_p(o, nulls[k])
        sd = math.sqrt(sum((v - m) ** 2 for v in nulls[k]) / (len(nulls[k]) - 1))
        res['%s_%s' % k] = {
            'observed': o, 'null_mean': m, 'null_sd': sd,
            'debiased': o - m,
            'z': ((o - m) / sd) if sd > 0 else 0.0,
            'p_two_sided': p,
            'p_bonf6': min(1.0, p * N_FAMILY),
            'passes_bonf': (p < ALPHA_BONF),
            'B': B,
        }
    res['_n'] = n
    res['_n_groups'] = len(segs)
    res['_n_form1_types'] = F1
    res['_n_form2_types'] = F2
    res['_pos_marginal'] = dict(Counter(pos_flat))
    return res


def mi_focus(items, posdef, formkey, seed, draws):
    """Permutation p for ONE (position, form) MI only — used for the
    Monte-Carlo-stability diagnostics, which are NOT part of the gate."""
    if posdef == 'P1':
        keyf, ordf, posf = (lambda it: it['sign'], lambda it: it['rank1'],
                            lambda it: it['p1'])
    else:
        keyf, ordf, posf = (lambda it: (it['sign'], it['ring']),
                            lambda it: it['idx_in_ring'], lambda it: it['p2'])
    groups = OrderedDict()
    for i, it in enumerate(items):
        groups.setdefault(keyf(it), []).append(i)
    for k in groups:
        groups[k].sort(key=lambda i: ordf(items[i]))
    pos_flat, idx_flat, segs = [], [], []
    for k, mem in groups.items():
        s = len(idx_flat)
        for i in mem:
            pos_flat.append(posf(items[i]))
            idx_flat.append(i)
        segs.append((s, len(idx_flat)))
    n = len(idx_flat)
    lex = sorted({items[i][formkey] for i in idx_flat})
    fid = {v: j for j, v in enumerate(lex)}
    f_flat = [fid[items[i][formkey]] for i in idx_flat]
    F = len(lex)

    def mi_of(perm):
        j = [0] * (3 * F)
        for k in range(n):
            j[pos_flat[k] * F + f_flat[perm[k]]] += 1
        return mi_bits(j, 3, F, n)

    obs = mi_of(list(range(n)))
    rng = random.Random(seed)
    perm = list(range(n))
    nulls = []
    for _ in range(draws):
        for (s, e) in segs:
            for a in range(e - 1, s, -1):
                b = rng.randint(s, a)
                perm[a], perm[b] = perm[b], perm[a]
        nulls.append(mi_of(perm))
    p, m = two_sided_p(obs, nulls)
    return {'observed': obs, 'null_mean': m, 'debiased': obs - m,
            'p_two_sided': p, 'draws': draws, 'seed': seed,
            'mc_se_of_p': math.sqrt(max(p, 1.0 / draws) * (1 - p) / draws),
            'passes_bonf': p < ALPHA_BONF}


def analyse(labels, level, seed=SEED, B=B, ring_min=1):
    """Six statistics: MI(P1,F1) MI(P1,F2) MI(P2,F1) MI(P2,F2) and the two
    chi-squares on the P1 (rank block) tables."""
    items = build_items(labels, level)
    if ring_min > 1:
        items2 = [it for it in items if it['ring_size'] >= ring_min]
    else:
        items2 = items
    r1 = run_position(items, 'P1', seed, B)
    r2 = run_position(items2, 'P2', seed + 1, B)
    out = OrderedDict()
    out['MI_P1_F1'] = r1['MI_F1']
    out['MI_P1_F2'] = r1['MI_F2']
    out['MI_P2_F1'] = r2['MI_F1']
    out['MI_P2_F2'] = r2['MI_F2']
    out['CHI2_prefix_by_rankblock'] = r1['CHI2_F1']
    out['CHI2_suffix_by_rankblock'] = r1['CHI2_F2']
    out['_meta'] = {
        'n_labels_P1': r1['_n'], 'n_signs': r1['_n_groups'],
        'n_labels_P2': r2['_n'], 'n_rings': r2['_n_groups'],
        'n_prefix_types': r1['_n_form1_types'],
        'n_suffix_types': r1['_n_form2_types'],
        'rankblock_marginal': r1['_pos_marginal'],
        'ringthird_marginal': r2['_pos_marginal'],
        'ring_min': ring_min,
    }
    return out


TESTS6 = ['MI_P1_F1', 'MI_P1_F2', 'MI_P2_F1', 'MI_P2_F2',
          'CHI2_prefix_by_rankblock', 'CHI2_suffix_by_rankblock']


def report(tag, res):
    say('  %-46s %10s %10s %10s %9s %9s %s'
        % (tag, 'observed', 'null_mean', 'debiased', 'z', 'p', 'bonf6<0.01?'))
    for t in TESTS6:
        d = res[t]
        say('  %-46s %10.4f %10.4f %+10.4f %+9.2f %9.5f %s'
            % (t, d['observed'], d['null_mean'], d['debiased'], d['z'],
               d['p_two_sided'], 'PASS' if d['passes_bonf'] else 'no'))


# =========================================================== the corpora ===

def load_labels(path, comma_split=True):
    pages = ML.parse_pages(path, comma_split=comma_split)
    return ML.zodiac_labels(pages, comma_split=comma_split)


def split(labels, signs):
    return [r for r in labels if r['sign'] in signs]


# ================================================== power calibration =====

def numeral_layout(labels, series):
    """The 8 numeral series arranged in the OBSERVED sign/ring layout: label
    at rank k of a sign is replaced by the numeral for k.  Positions are
    unchanged, so P1/P2 are identical to the manuscript's."""
    out = []
    for r in labels:
        k = r['idx_in_sign']
        w = series[k] if k < len(series) else series[-1]
        q = dict(r)
        q['words'] = [w]
        q['text'] = w
        out.append(q)
    return out


# ================================================================= main ===

def main():
    os.makedirs(RESULTS, exist_ok=True)
    say('Z4 — positional morphology of the zodiac labels')
    say('seed=%d  B=%d  Bonferroni family=%d  alpha=%.6f'
        % (SEED, B, N_FAMILY, ALPHA_BONF))
    say('')

    inputs = OrderedDict()
    for p in (ZL3B, GC2A, os.path.join(HERE, 'meaning_lib.py')):
        inputs[os.path.relpath(p, REPO).replace('\\', '/')] = ML.sha256(p)
    for k, v in inputs.items():
        say('input %-40s %s' % (k, v))
    say('')

    J = OrderedDict()
    J['key'] = 'z4'
    J['title'] = 'Z4 — positional morphology (MI between label position and label form)'
    J['protocol'] = 'experiments/meaning-probes/PROTOCOL.md, section Z4'
    J['seed'] = SEED
    J['permutation_draws'] = B
    J['bonferroni_family'] = N_FAMILY
    J['alpha'] = ALPHA
    J['alpha_bonferroni'] = ALPHA_BONF
    J['inputs_sha256'] = inputs
    J['definitions'] = {
        'P1': 'rank block within sign: ranks 1-10 -> 0, 11-20 -> 1, 21-30 -> 2',
        'P2': 'thirds of the ring: floor(3 * idx_in_ring / ring_size), capped at 2',
        'F1': 'first glyph unit of the label locus (all its words concatenated)',
        'F2': 'last glyph unit of the label locus',
        'MI': 'I(position; form) in bits',
        'null_P1': 'permute rank within sign (label moves whole: f1,f2 together)',
        'null_P2': 'permute index within ring (label moves whole)',
        'p': 'two-sided: |T_null - mean_null| >= |T_obs - mean_null|, +1 smoothed',
        'debiased_effect': 'observed MI minus null-mean MI (small-sample MI bias)',
        'chi2': 'Pearson chi-square of the same rank-block contingency table, '
                'permutation null (prefix inventory = F1, suffix inventory = F2)',
    }
    J['ambiguities_resolved'] = [
        'A1 thirds of every ring including short ones (>=6 restriction only as sensitivity)',
        'A2 multi-word label treated as one concatenated sequence',
        'A3 two-sided p = deviation from null mean in either direction',
        'A4 Bonferroni family = 6 (4 MI + 2 chi-square), not 4',
        'A5 gate evaluated on TEST signs only',
        'A6 f1 and f2 of one label permute together',
        'A7 primary comma_split=True; comma_split=False reported as sensitivity',
        'A8 primary glyph-unit level; raw EVA level as registered robustness',
    ]

    # ---------------------------------------------------------- primary --
    lab = load_labels(ZL3B, True)
    say('ZL3b-n: %d zodiac label loci with words' % len(lab))
    fit, tst = split(lab, ML.FIT_SIGNS), split(lab, ML.TEST_SIGNS)
    say('  FIT signs %s  n=%d' % (','.join(ML.FIT_SIGNS), len(fit)))
    say('  TEST signs %s  n=%d' % (','.join(ML.TEST_SIGNS), len(tst)))
    say('')

    main_res = OrderedDict()
    for name, sub in (('FIT', fit), ('TEST', tst), ('ALL', lab)):
        say('ZL3b glyph-unit level — %s' % name)
        r = analyse(sub, 'unit')
        report(name, r)
        say('')
        main_res[name] = r
    J['primary_ZL3b_unit'] = main_res

    # observed contingency tables on TEST (small, useful to eyeball)
    it_t = build_items(tst, 'unit')
    tab = OrderedDict()
    for pk in ('p1', 'p2'):
        for fk in ('f1', 'f2'):
            c = Counter((it[pk], it[fk]) for it in it_t)
            d = OrderedDict()
            for (b, f), v in sorted(c.items(), key=lambda kv: (kv[0][0], -kv[1])):
                d.setdefault('%s_%d' % ('rankblock' if pk == 'p1' else 'ringthird', b),
                             OrderedDict())[f] = v
            tab['%s_x_%s' % ('rankblock' if pk == 'p1' else 'ringthird',
                             'prefix' if fk == 'f1' else 'suffix')] = d
    J['observed_TEST_tables_unit'] = tab
    say('observed TEST table  ringthird x prefix (the one statistic that moves):')
    for k, v in tab['ringthird_x_prefix'].items():
        say('  %-12s %s' % (k, dict(v)))
    say('')

    # ------------------------------------------------- robustness: raw ----
    raw_res = OrderedDict()
    for name, sub in (('FIT', fit), ('TEST', tst)):
        say('ZL3b RAW EVA character level — %s' % name)
        r = analyse(sub, 'raw')
        report(name, r)
        say('')
        raw_res[name] = r
    J['robustness_ZL3b_raw'] = raw_res

    # ------------------------------------- sensitivity: comma_split=False -
    labF = load_labels(ZL3B, False)
    sens = OrderedDict()
    for name, signs in (('TEST', ML.TEST_SIGNS),):
        say('ZL3b glyph-unit, comma_split=False — %s' % name)
        r = analyse(split(labF, signs), 'unit')
        report(name, r)
        say('')
        sens[name] = r
    J['sensitivity_comma_split_False_unit'] = sens

    # ------------------------------------ sensitivity: rings with >= 6 ----
    say('ZL3b glyph-unit, P2 restricted to rings with >= 6 labels — TEST')
    r6 = analyse(tst, 'unit', ring_min=6)
    report('TEST(ring>=6)', r6)
    say('')
    J['sensitivity_ring_min6_unit'] = {'TEST': r6}

    # ------------------------------------------------------ replication --
    cov = OrderedDict()
    for nm, path in (('ZL3b', ZL3B), ('GC2a', GC2A)):
        pg = ML.parse_pages(path, comma_split=True)
        folios = [f for fs in ML.ZODIAC_SIGNS.values() for f in fs]
        loci = [l for f in folios if f in pg for l in pg[f]['loci']
                if l['type'] == 'L' and l['sub'] == 'z']
        cov[nm] = {'Lz_loci': len(loci),
                   'Lz_loci_with_parsable_words': sum(1 for l in loci if l['words']),
                   'note': 'clean_tokens keeps only /^[a-z]+$/ tokens'}
        say('coverage %s: %d Lz loci, %d survive the clean parser'
            % (nm, cov[nm]['Lz_loci'], cov[nm]['Lz_loci_with_parsable_words']))
    J['transcription_coverage'] = cov
    say('  GC2a-n is the Glen Claston v101 alphabet (upper case + digits), not EVA;')
    say('  the clean parser and the EVA-derived glyph-unit merges do not apply to it,')
    say('  so the GC2a replication below is a coverage-crippled check, not a fair one.')
    say('')

    lab2 = load_labels(GC2A, True)
    say('GC2a-n: %d zodiac label loci with words' % len(lab2))
    rep = OrderedDict()
    for name, signs in (('FIT', ML.FIT_SIGNS), ('TEST', ML.TEST_SIGNS)):
        sub = split(lab2, signs)
        say('GC2a glyph-unit level — %s (n=%d)' % (name, len(sub)))
        r = analyse(sub, 'unit')
        report(name, r)
        say('')
        rep[name] = r
    J['replication_GC2a_unit'] = rep

    # ------------------------------------------------ power calibration --
    say('POWER CALIBRATION — 8 numeral series in the observed sign/ring layout')
    say('(what a real compositional numeral system looks like on this layout)')
    say('')
    pw = OrderedDict()
    ctrl = ML.numeral_controls()
    for level in ('unit', 'raw'):
        pw[level] = OrderedDict()
        for name, signs in (('FIT', ML.FIT_SIGNS), ('TEST', ML.TEST_SIGNS)):
            base = split(lab, signs)
            pw[level][name] = OrderedDict()
            say('numeral controls, %s level, %s signs' % (level, name))
            for sysname, series in ctrl.items():
                r = analyse(numeral_layout(base, series), level)
                pw[level][name][sysname] = r
                say('  %-20s' % sysname)
                report(sysname, r)
            say('')

    # measured power: fraction of the 8 numeral systems that clear the gate
    power = OrderedDict()
    for level in ('unit', 'raw'):
        power[level] = OrderedDict()
        for name in ('FIT', 'TEST'):
            d = OrderedDict()
            for t in TESTS6:
                hits = sum(1 for s in ctrl
                           if pw[level][name][s][t]['passes_bonf'])
                d[t] = {'n_pass': hits, 'n_systems': len(ctrl),
                        'fraction': hits / float(len(ctrl)),
                        'median_debiased': sorted(
                            pw[level][name][s][t]['debiased'] for s in ctrl)[len(ctrl) // 2]}
            power[level][name] = d
    J['power_numerals'] = pw
    J['power_summary'] = power

    say('MEASURED POWER (numeral positive controls clearing Bonferroni p<0.01)')
    for level in ('unit', 'raw'):
        for name in ('FIT', 'TEST'):
            for t in TESTS6:
                d = power[level][name][t]
                say('  %-4s %-4s %-30s %d/%d  median debiased effect %.4f'
                    % (level, name, t, d['n_pass'], d['n_systems'],
                       d['median_debiased']))
    say('')

    # -------------------------------- Monte-Carlo stability diagnostics --
    # NOT part of the gate. The gate uses B=10000 and seed 408/409 exactly as
    # registered. These numbers only say how reproducible that verdict is.
    gated0 = main_res['TEST']
    best = min(TESTS6, key=lambda t: gated0[t]['p_two_sided'])
    say('MONTE-CARLO STABILITY OF THE SMALLEST p ON TEST (%s) — diagnostic only'
        % best)
    diag = OrderedDict()
    diag['gated_statistic'] = best
    diag['gated_p'] = gated0[best]['p_two_sided']
    pg_ = gated0[best]['p_two_sided']
    diag['gated_p_mc_se'] = math.sqrt(pg_ * (1 - pg_) / B)
    diag['bonferroni_threshold'] = ALPHA_BONF
    say('  registered run: p = %.5f, Monte-Carlo SE = %.5f, threshold = %.6f'
        % (pg_, diag['gated_p_mc_se'], ALPHA_BONF))

    if best.startswith('MI_'):
        _, pk, fk = best.split('_')
        pkey = pk
        fkey = 'f1' if fk == 'F1' else 'f2'
        items_t = build_items(tst, 'unit')
        seeds = list(range(409, 419))
        per_seed = []
        for sd in seeds:
            r = mi_focus(items_t, pkey, fkey, sd, B)
            per_seed.append({'seed': sd, 'p': r['p_two_sided'],
                             'passes_bonf': r['passes_bonf']})
            say('    seed %d  p=%.5f  %s' % (sd, r['p_two_sided'],
                                             'pass' if r['passes_bonf'] else 'fail'))
        diag['seed_sensitivity_B10000'] = per_seed
        diag['seed_sensitivity_pass_fraction'] = (
            sum(1 for d in per_seed if d['passes_bonf']) / float(len(per_seed)))
        big = mi_focus(items_t, pkey, fkey, 409, 200000)
        diag['high_precision_B200000'] = big
        say('  high-precision rerun (B=200000, not the registered B): p = %.6f '
            '(MC SE %.6f) -> %s the Bonferroni threshold'
            % (big['p_two_sided'], big['mc_se_of_p'],
               'clears' if big['passes_bonf'] else 'MISSES'))
        say('  seed sensitivity at the registered B: %d of %d seeds clear it'
            % (sum(1 for d in per_seed if d['passes_bonf']), len(per_seed)))
    J['mc_stability_diagnostic'] = diag
    say('')

    # ----------------------------------------------------------- gate ----
    gated = main_res['TEST']
    passers = [t for t in TESTS6 if gated[t]['passes_bonf']]
    minp = min(gated[t]['p_two_sided'] for t in TESTS6)
    powfrac = min(power['unit']['TEST'][t]['fraction'] for t in TESTS6)
    powmax = max(power['unit']['TEST'][t]['fraction'] for t in TESTS6)

    gate = OrderedDict()
    gate['stratum'] = 'ZL3b-n, TEST signs, glyph-unit level, comma_split=True'
    gate['rule'] = ('any of the 6 statistics with two-sided permutation '
                    'p < 0.01/6 = %.6f' % ALPHA_BONF)
    gate['min_p_over_family'] = minp
    gate['passing_tests'] = passers
    gate['outcome'] = 'PASS' if passers else 'FAIL'
    gate['power_fraction_range_over_family'] = [powfrac, powmax]
    if passers:
        t0 = passers[0]
        gate['robustness_of_passing_statistic'] = {
            'statistic': t0,
            'ZL3b_unit_TEST_p': gated[t0]['p_two_sided'],
            'ZL3b_unit_FIT_p': main_res['FIT'][t0]['p_two_sided'],
            'ZL3b_unit_ALL_p': main_res['ALL'][t0]['p_two_sided'],
            'ZL3b_raw_TEST_p': raw_res['TEST'][t0]['p_two_sided'],
            'ZL3b_unit_TEST_ring_min6_p': r6[t0]['p_two_sided'],
            'ZL3b_unit_TEST_comma_split_False_p': sens['TEST'][t0]['p_two_sided'],
            'GC2a_unit_TEST_p': rep['TEST'][t0]['p_two_sided'],
            'numeral_systems_detecting_it_TEST_unit':
                [s for s in ctrl if pw['unit']['TEST'][s][t0]['passes_bonf']],
        }
    J['gate'] = gate

    say('GATE Z4: %s' % gate['outcome'])
    say('  smallest p over the family of 6 on TEST = %.5f (Bonferroni threshold %.6f)'
        % (minp, ALPHA_BONF))
    if passers:
        say('  passing: %s' % ', '.join(passers))
    else:
        say('  no statistic in the family reaches the Bonferroni threshold;')
        say('  Z4 reports NO positional structure in the labels.')
    say('  positive-control power on the same layout: %d/8 to %d/8 of the numeral'
        % (round(powfrac * 8), round(powmax * 8)))
    say('  systems are detected across the six statistics (unit level, TEST signs).')

    with io.open(os.path.join(RESULTS, 'z4.json'), 'w', encoding='utf-8') as f:
        json.dump(J, f, indent=1, sort_keys=False, default=str)
    with io.open(os.path.join(RESULTS, 'z4.stdout.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(_out_lines) + '\n')


if __name__ == '__main__':
    main()
