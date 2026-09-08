#!/usr/bin/env python3
"""Independent adversarial reimplementation of Z2 + Z3 from PROTOCOL.md alone.

Written WITHOUT reading t_z2z3.py. Uses meaning_lib for data access only.
All statistics written from scratch here.
"""
import json, random, sys, hashlib
from collections import OrderedDict, Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ml

SEED = 408
NPERM = 10000
ZL = r"R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt"
GC = r"R:/Coding/LinearA/tmp/voynich_repo/data/corpora/GC2a-n.txt"

# ---------------------------------------------------------------- sequences

def seq_units(rec):
    """glyph-unit sequence of a whole label locus (all words concatenated)."""
    out = []
    for w in rec['words']:
        out.extend(ml.bpe_apply(w))
    return out

def seq_chars(rec):
    return list(''.join(rec['words']))

# ---------------------------------------------------------------- slots

def slot_A(rec):
    return ('A', rec['idx_in_sign'])

def slot_B(rec):
    # index within ring, rings aligned across signs by ring rank (manuscript
    # ring order as produced by meaning_lib = outer-first per ZL comments)
    return ('B', rec['ring'], rec['idx_in_ring'])

def slot_C(rec):
    if rec['clock_min'] is None:
        return None
    return ('C', int(round(rec['clock_min'] / 30.0)) % 24)

CONVS = OrderedDict([('A', slot_A), ('B', slot_B), ('C', slot_C)])

# ---------------------------------------------------------------- core stat

def build(records, seqfn, slotfn):
    """-> (signs list, per-item sign index, slot key, similarity matrix)"""
    items = []
    for r in records:
        s = slotfn(r)
        if s is None:
            continue
        items.append({'sign': r['sign'], 'slot': s, 'seq': seqfn(r)})
    n = len(items)
    sim = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            v = ml.lcs_sim(items[i]['seq'], items[j]['seq'])
            sim[i][j] = sim[j][i] = v
    return items, sim


def cross_totals(items, sim):
    """total sum + count of all cross-sign pairs (invariant under permutation)"""
    n = len(items)
    tot, cnt = 0.0, 0
    for i in range(n):
        for j in range(i + 1, n):
            if items[i]['sign'] != items[j]['sign']:
                tot += sim[i][j]
                cnt += 1
    return tot, cnt


def effect_from_slots(items, sim, slots, tot, cnt):
    """slots = list of slot keys parallel to items."""
    by = {}
    for idx, s in enumerate(slots):
        by.setdefault(s, []).append(idx)
    same_sum, same_cnt = 0.0, 0
    for s, idxs in by.items():
        for a in range(len(idxs)):
            ia = idxs[a]
            for b in range(a + 1, len(idxs)):
                ib = idxs[b]
                if items[ia]['sign'] != items[ib]['sign']:
                    same_sum += sim[ia][ib]
                    same_cnt += 1
    diff_cnt = cnt - same_cnt
    if same_cnt == 0 or diff_cnt == 0:
        return None, same_cnt
    return same_sum / same_cnt - (tot - same_sum) / diff_cnt, same_cnt


def run_test(records, seqfn, slotfn, nperm=NPERM, seed=SEED):
    items, sim = build(records, seqfn, slotfn)
    if len(items) < 4:
        return {'n_items': len(items), 'error': 'too few items'}
    tot, cnt = cross_totals(items, sim)
    slots = [it['slot'] for it in items]
    obs, same_cnt = effect_from_slots(items, sim, slots, tot, cnt)
    if obs is None:
        return {'n_items': len(items), 'error': 'no same-slot or no diff-slot pairs',
                'same_slot_pairs': same_cnt, 'cross_sign_pairs': cnt}
    # within-sign slot permutations: shuffle the slot labels among the items of
    # each sign (label set fixed, only slot assignment moves)
    bysign = {}
    for idx, it in enumerate(items):
        bysign.setdefault(it['sign'], []).append(idx)
    rng = random.Random(seed)
    nulls = []
    ge = 0
    for _ in range(nperm):
        perm = list(slots)
        for sg, idxs in bysign.items():
            vals = [slots[i] for i in idxs]
            rng.shuffle(vals)
            for i, v in zip(idxs, vals):
                perm[i] = v
        e, _sc = effect_from_slots(items, sim, perm, tot, cnt)
        if e is None:
            e = 0.0
        nulls.append(e)
        if abs(e) >= abs(obs) - 1e-15:
            ge += 1
    mean = sum(nulls) / len(nulls)
    var = sum((x - mean) ** 2 for x in nulls) / (len(nulls) - 1)
    sd = var ** 0.5
    return {'n_items': len(items), 'cross_sign_pairs': cnt,
            'same_slot_pairs': same_cnt,
            'effect': obs, 'p_two_sided': (ge + 1) / (nperm + 1),
            'null_mean': mean, 'null_sd': sd,
            'z': (obs - mean) / sd if sd > 0 else None}

# ---------------------------------------------------------------- controls

def numeral_records(records, slotfn, series):
    """Replace each label's text by the numeral whose rank equals its slot rank,
    keeping the observed sign/slot structure."""
    keep = [r for r in records if slotfn(r) is not None]
    slots = sorted({slotfn(r) for r in keep})
    rank = {s: i for i, s in enumerate(slots)}
    out = []
    for r in keep:
        i = rank[slotfn(r)] % len(series)
        nr = dict(r)
        nr['words'] = [series[i]]
        out.append(nr)
    return out


def ctrl_seq_chars(rec):
    return list(''.join(rec['words']))

# ---------------------------------------------------------------- main

def main():
    pages = ml.parse_pages(ZL)
    labels = ml.zodiac_labels(pages)
    fit = [r for r in labels if r['sign'] in ml.FIT_SIGNS]
    test = [r for r in labels if r['sign'] in ml.TEST_SIGNS]

    res = {'sha256': {'ZL3b-n.txt': ml.sha256(ZL), 'GC2a-n.txt': ml.sha256(GC)},
           'n_labels_total': len(labels), 'n_fit': len(fit), 'n_test': len(test),
           'seed': SEED, 'nperm': NPERM}

    print('labels total=%d  FIT=%d  TEST=%d' % (len(labels), len(fit), len(test)))
    print('FIT signs =', ml.FIT_SIGNS)
    print('TEST signs =', ml.TEST_SIGNS)

    res['z2'] = {}
    for split_name, recs in (('TEST', test), ('FIT', fit)):
        res['z2'][split_name] = {}
        for cname, fn in CONVS.items():
            for level, seqfn in (('glyph', seq_units), ('char', seq_chars)):
                r = run_test(recs, seqfn, fn)
                res['z2'][split_name]['%s_%s' % (cname, level)] = r
                print('Z2 %-4s conv %s %-5s: %s' % (split_name, cname, level,
                      json.dumps({k: (round(v, 5) if isinstance(v, float) else v)
                                  for k, v in r.items()})))

    # power calibration: numeral controls laid on TEST slot structure
    res['power'] = {}
    for cname, fn in CONVS.items():
        for level, seqfn in (('glyph', seq_units), ('char', ctrl_seq_chars)):
            effects, npass = [], 0
            per = {}
            for name, series in ml.numeral_controls().items():
                nr = numeral_records(test, fn, series)
                r = run_test(nr, seqfn, fn)
                per[name] = {'effect': r.get('effect'), 'p': r.get('p_two_sided')}
                if r.get('effect') is not None:
                    effects.append(r['effect'])
                    if r['p_two_sided'] < 0.01:
                        npass += 1
            effects.sort()
            med = effects[len(effects) // 2] if effects else None
            if effects and len(effects) % 2 == 0:
                med = (effects[len(effects) // 2 - 1] + effects[len(effects) // 2]) / 2
            res['power']['%s_%s' % (cname, level)] = {
                'median_effect': med, 'n_pass_p01': npass, 'n_series': len(effects),
                'per_series': per}
            print('POWER conv %s %-5s: median effect=%s  %d/%d at p<0.01'
                  % (cname, level, round(med, 5) if med else med, npass, len(effects)))

    # gate Z2 evaluation
    res['gate_z2'] = {}
    for cname in CONVS:
        for level in ('glyph', 'char'):
            k = '%s_%s' % (cname, level)
            t = res['z2']['TEST'][k]
            med = res['power'][k]['median_effect']
            ratio = (t['effect'] / med) if (t.get('effect') is not None and med) else None
            res['gate_z2'][k] = {'p': t.get('p_two_sided'), 'effect': t.get('effect'),
                                 'ctrl_median': med, 'ratio': ratio,
                                 'pass': bool(t.get('p_two_sided') is not None
                                              and t['p_two_sided'] < 0.01
                                              and ratio is not None and ratio >= 0.25)}
            print('GATE Z2 %s: p=%s effect=%s ratio=%s pass=%s' % (
                k, t.get('p_two_sided'), round(t['effect'], 5) if t.get('effect') is not None else None,
                round(ratio, 4) if ratio is not None else None, res['gate_z2'][k]['pass']))

    # ---------------- Z3
    strings = [r['text'] for r in labels]
    distinct = len(set(strings))
    words = [w for r in labels for w in r['words']]
    z3 = {'n_label_loci': len(strings), 'distinct_strings': distinct,
          'ratio': distinct / len(strings),
          'gate_pass_fixed_inventory': (distinct / len(strings)) < 0.5,
          'word_tokens': len(words), 'word_types': len(set(words)),
          'word_ttr': len(set(words)) / len(words)}
    cnt = Counter(strings)
    rep = {s: c for s, c in cnt.items() if c > 1}
    signs_of = {}
    for r in labels:
        signs_of.setdefault(r['text'], set()).add(r['sign'])
    z3['n_repeated_strings'] = len(rep)
    z3['n_shared_by_ge2_signs'] = sum(1 for s in rep if len(signs_of[s]) >= 2)
    z3['n_shared_by_ge3_signs'] = sum(1 for s in rep if len(signs_of[s]) >= 3)
    z3['max_repeat'] = max(cnt.values())
    z3['max_repeat_string'] = cnt.most_common(1)[0][0]
    res['z3'] = z3
    print('Z3 distinct/total = %d/%d = %.4f  gate(<0.5) pass=%s'
          % (distinct, len(strings), distinct / len(strings), z3['gate_pass_fixed_inventory']))
    print('Z3 word types/tokens = %d/%d TTR=%.4f' % (z3['word_types'], z3['word_tokens'], z3['word_ttr']))
    print('Z3 repeated=%d  shared>=2 signs=%d  >=3 signs=%d  max repeat=%d (%s)'
          % (z3['n_repeated_strings'], z3['n_shared_by_ge2_signs'],
             z3['n_shared_by_ge3_signs'], z3['max_repeat'], z3['max_repeat_string']))

    # Z3 glyph inventory labels vs running text, zodiac folios
    zfolios = set(f for fs in ml.ZODIAC_SIGNS.values() for f in fs)
    lab_u, txt_u = Counter(), Counter()
    lab_tok, txt_tok = 0, 0
    for fo in zfolios:
        p = pages.get(fo)
        if not p:
            continue
        for l in p['loci']:
            for w in l['words']:
                for u in ml.bpe_apply(w):
                    if l['type'] == 'L':
                        lab_u[u] += 1
                    elif l['type'] in ('P', 'C', 'R'):
                        txt_u[u] += 1
            if l['type'] == 'L':
                lab_tok += len(l['words'])
            elif l['type'] in ('P', 'C', 'R'):
                txt_tok += len(l['words'])
    res['z3_inventory'] = {'label_units': len(lab_u), 'text_units': len(txt_u),
                           'shared': len(set(lab_u) & set(txt_u)),
                           'label_only': sorted(set(lab_u) - set(txt_u)),
                           'text_only': sorted(set(txt_u) - set(lab_u)),
                           'label_tokens': lab_tok, 'text_tokens': txt_tok}
    print('Z3 inventory: labels %d units / %d tokens; text %d units / %d tokens; shared %d; text-only %s; label-only %s'
          % (len(lab_u), lab_tok, len(txt_u), txt_tok, len(set(lab_u) & set(txt_u)),
             sorted(set(txt_u) - set(lab_u)), sorted(set(lab_u) - set(txt_u))))

    # Z3 TTR vs 1000 length-matched running-text resamples
    lab_words = []
    txt_words = []
    for fo in zfolios:
        p = pages.get(fo)
        if not p:
            continue
        for l in p['loci']:
            if l['type'] == 'L':
                lab_words.extend(l['words'])
            elif l['type'] in ('P', 'C', 'R'):
                txt_words.extend(l['words'])
    n = len(lab_words)
    lab_ttr = len(set(lab_words)) / n
    rng = random.Random(SEED)
    samples = []
    for _ in range(1000):
        s = rng.sample(txt_words, n) if n <= len(txt_words) else None
        if s is None:
            break
        samples.append(len(set(s)) / n)
    if samples:
        m = sum(samples) / len(samples)
        sd = (sum((x - m) ** 2 for x in samples) / (len(samples) - 1)) ** 0.5
        ge = sum(1 for x in samples if abs(x - m) >= abs(lab_ttr - m))
        res['z3_ttr'] = {'label_ttr': lab_ttr, 'resample_mean': m, 'resample_sd': sd,
                         'z': (lab_ttr - m) / sd if sd else None,
                         'p_two_sided': (ge + 1) / (len(samples) + 1),
                         'n_label_words': n, 'n_text_words': len(txt_words)}
        print('Z3 TTR label=%.4f resample mean=%.4f sd=%.4f z=%.2f p=%.4f'
              % (lab_ttr, m, sd, (lab_ttr - m) / sd, (ge + 1) / (len(samples) + 1)))

    out = Path(__file__).resolve().parent / 'results' / 'v_z2z3_reimplementation_a.json'
    out.write_text(json.dumps(res, indent=1), encoding='utf-8')
    print('wrote', out)


if __name__ == '__main__':
    main()
