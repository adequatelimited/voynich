#!/usr/bin/env python3
"""v_r1r2_confound_1.py — adversarial CONFOUND audit of t_r1r2.py (R1/R2).

Read-only. Does not touch t_r1r2.py or results/r1r2.json.
Stdlib only, seed 408, 10000 draws.

Blocks:
  A  independent recomputation of R1(a) + the length confound
  B  parser dropping (illegible tokens) by position
  C  hand / Currier language / page composition of FIT vs TEST
  D  R1(b) anatomy: cell sparsity, length curve, what the relaxed match does
  E  R1(b) frequency confound: frequency-matched and type-matched controls
  F  R2 'tail' etc.: page confound + transcriber comment conventions
"""
import io, json, math, os, random, re, sys
from collections import Counter, OrderedDict, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results')
ZL = os.path.abspath(os.path.join(HERE, '..', '..', 'data', 'corpora', 'ZL3b-n.txt'))
NDRAW = 10000
SEED = ML.SEED

L = []
def say(*a):
    s = ' '.join(str(x) for x in a)
    L.append(s); print(s)

def fnum(pid):
    return int(re.match(r'f(\d+)', pid).group(1))

def gp(w):
    for g in ML.GALLOWS:
        if w.startswith(g):
            return g
    return None

def strip(w):
    g = gp(w)
    return (g, w[len(g):]) if g else (None, None)

def mean_sd(xs):
    n = len(xs); m = sum(xs)/n
    v = sum((x-m)**2 for x in xs)/(n-1) if n > 1 else 0.0
    return m, math.sqrt(v)

def z(obs, null):
    m, sd = mean_sd(null)
    return (obs-m)/sd if sd > 0 else 0.0

def p2(obs, null):
    m = sum(null)/len(null); d = abs(obs-m)
    k = sum(1 for x in null if abs(x-m) >= d-1e-12)
    return (1+k)/(len(null)+1)

OUT = OrderedDict()
OUT['inputs'] = {'ZL3b-n.txt': ML.sha256(ZL),
                 'meaning_lib.py': ML.sha256(os.path.join(HERE, 'meaning_lib.py')),
                 't_r1r2.py': ML.sha256(os.path.join(HERE, 't_r1r2.py')),
                 'results/r1r2.json': ML.sha256(os.path.join(RES, 'r1r2.json')),
                 'PROTOCOL.md': ML.sha256(os.path.join(HERE, 'PROTOCOL.md'))}
OUT['seed'] = SEED; OUT['n_draws'] = NDRAW

pages = ML.parse_pages(ZL, comma_split=True)

recB = {p['id'] for p in pages.values()
        if p['meta'].get('I') == 'S' and p['meta'].get('L') == 'B'
        and 103 <= p['fnum'] <= 116}
TESTids = {i for i in recB if fnum(i) % 2 == 0}
FITids = {i for i in recB if fnum(i) % 2 == 1}

def pools(ids):
    pars = ML.paragraphs(pages, page_ids=ids)
    pi = [d['first_word'] for d in pars if d['first_word']]
    pi_rec = [(d['first_word'], d['page']) for d in pars if d['first_word']]
    nonpi, allw = [], []
    for d in pars:
        allw.extend(d['words']); nonpi.extend(d['words'][1:])
    nil = ML.non_initial_line_words(pages, page_ids=ids)
    return pars, pi, pi_rec, nonpi, allw, nil

vocab = Counter()
for d in ML.paragraphs(pages, page_ids=recB):
    vocab.update(d['words'])

STRATA = OrderedDict([('TEST_even', TESTids), ('FIT_odd', FITids), ('ALL', recB)])

# ============================================================ A: R1(a) ======
say('=' * 78)
say('A. R1(a) independent recomputation + the LENGTH confound')
say('=' * 78)
A = OrderedDict()
for nm, ids in STRATA.items():
    pars, pi, pi_rec, nonpi, allw, nil = pools(ids)
    rate = lambda ws: sum(1 for w in ws if gp(w))/len(ws) if ws else 0.0
    a = {'n_paragraphs': len(pars), 'n_openers': len(pi),
         'rate_openers': rate(pi), 'n_line_initial': len(nil),
         'rate_line_initial': rate(nil), 'n_all': len(allw),
         'rate_all': rate(allw),
         'mean_len_openers': sum(map(len, pi))/len(pi),
         'mean_len_line_initial': sum(map(len, nil))/len(nil),
         'mean_len_all': sum(map(len, allw))/len(allw)}
    # gallows rate as a function of word length in the whole-section token pool
    bylen = defaultdict(lambda: [0, 0])
    for w in allw:
        bylen[len(w)][0] += 1
        bylen[len(w)][1] += 1 if gp(w) else 0
    a['gallows_rate_by_length_allwords'] = {
        k: [v[0], round(v[1]/v[0], 4)] for k, v in sorted(bylen.items())}
    # LENGTH-MATCHED null for (a): draw each pseudo-opener from all section
    # tokens OF THE SAME LENGTH. If the opener effect were a length artefact
    # this null would reproduce it.
    bucket = defaultdict(list)
    for w in allw:
        bucket[len(w)].append(1 if gp(w) else 0)
    keys = [len(w) for w in pi if bucket[len(w)]]
    rng = random.Random(SEED)
    null = [sum(rng.choice(bucket[k]) for k in keys)/len(keys) for _ in range(NDRAW)]
    obs = sum(1 for w in pi if gp(w))/len(pi)
    a['length_matched_null'] = {'obs': obs, 'null_mean': mean_sd(null)[0],
                                'null_sd': mean_sd(null)[1], 'sd_units': z(obs, null),
                                'p_two_sided': p2(obs, null)}
    # same, restricted to line-initial tokens of the same length
    bucket2 = defaultdict(list)
    for w in nil:
        bucket2[len(w)].append(1 if gp(w) else 0)
    keys2 = [len(w) for w in pi if bucket2[len(w)]]
    rng = random.Random(SEED + 1)
    null2 = [sum(rng.choice(bucket2[k]) for k in keys2)/len(keys2) for _ in range(NDRAW)]
    obs2 = sum(1 for w in pi if bucket2[len(w)] and gp(w))/len(keys2)
    a['length_matched_null_vs_line_initial'] = {
        'n_used': len(keys2), 'obs': obs2, 'null_mean': mean_sd(null2)[0],
        'null_sd': mean_sd(null2)[1], 'sd_units': z(obs2, null2),
        'p_two_sided': p2(obs2, null2)}
    A[nm] = a
    say('%-9s openers %.4f (n=%d, meanlen %.2f) | line-init %.4f (n=%d, meanlen %.2f)'
        ' | all %.4f (n=%d, meanlen %.2f)' % (
            nm, a['rate_openers'], a['n_openers'], a['mean_len_openers'],
            a['rate_line_initial'], a['n_line_initial'], a['mean_len_line_initial'],
            a['rate_all'], a['n_all'], a['mean_len_all']))
    say('          LENGTH-MATCHED null (same-length section tokens): obs %.4f vs '
        '%.4f +/- %.4f -> %.1f SD p=%.5f' % (
            a['length_matched_null']['obs'], a['length_matched_null']['null_mean'],
            a['length_matched_null']['null_sd'], a['length_matched_null']['sd_units'],
            a['length_matched_null']['p_two_sided']))
    say('          LENGTH-MATCHED null (same-length LINE-INITIAL tokens): %.1f SD '
        'p=%.5f' % (a['length_matched_null_vs_line_initial']['sd_units'],
                    a['length_matched_null_vs_line_initial']['p_two_sided']))
say('')
say('  gallows rate by word length, all Recipes-B tokens:')
say('   ', json.dumps(A['ALL']['gallows_rate_by_length_allwords']))
OUT['A_r1a_length'] = A

# ==================================================== B: parser dropping ====
say('')
say('=' * 78)
say('B. Does the clean parser DROP tokens more often at paragraph-initial'
    ' position?  (illegible ?, extended @nnn, digits)')
say('=' * 78)
B = OrderedDict()
DROP = re.compile(r'[?@\d]')
def raw_tokens(text):
    t = re.sub(r'\{[^}]*\}', '', text)
    t = t.replace('<->', ' ')
    t = re.sub(r'<[^>]*>', '', t)
    t = re.sub(r'\[([^\]:]*):[^\]]*\]', r'\1', t)
    return [x for x in re.split(r'[.\s,]+', t) if x]

for nm, ids in STRATA.items():
    n_par = n_par_first_dropped = 0
    n_line = n_line_first_dropped = 0
    tot_raw = tot_kept = 0
    for pid in sorted(ids):
        p = pages[pid]
        seen = False
        for l in p['loci']:
            if l['type'] != 'P':
                continue
            rt = raw_tokens(l['raw'])
            tot_raw += len(rt); tot_kept += len(l['words'])
            if not rt:
                continue
            bad = bool(DROP.search(rt[0])) or not re.fullmatch(r'[a-z]+', rt[0])
            if l['para_start']:
                seen = True
                n_par += 1
                n_par_first_dropped += 1 if bad else 0
            elif seen:
                n_line += 1
                n_line_first_dropped += 1 if bad else 0
    b = {'n_paragraph_first_loci': n_par,
         'n_paragraph_first_token_dropped': n_par_first_dropped,
         'frac_paragraph_first_dropped': n_par_first_dropped/n_par if n_par else None,
         'n_internal_line_loci': n_line,
         'n_internal_line_first_token_dropped': n_line_first_dropped,
         'frac_internal_line_first_dropped': n_line_first_dropped/n_line if n_line else None,
         'raw_tokens': tot_raw, 'kept_tokens': tot_kept,
         'kept_fraction': tot_kept/tot_raw if tot_raw else None}
    B[nm] = b
    say('%-9s paragraph-first token dropped %d/%d (%.3f) | internal-line-first '
        'dropped %d/%d (%.3f) | overall kept %.3f' % (
            nm, b['n_paragraph_first_token_dropped'], b['n_paragraph_first_loci'],
            b['frac_paragraph_first_dropped'] or 0,
            b['n_internal_line_first_token_dropped'], b['n_internal_line_loci'],
            b['frac_internal_line_first_dropped'] or 0, b['kept_fraction']))
OUT['B_parser_dropping'] = B

# ======================================= C: hand / language / page balance ==
say('')
say('=' * 78)
say('C. Scribe (hand $H), Currier language ($L) and page composition,'
    ' FIT vs TEST')
say('=' * 78)
C = OrderedDict()
for nm, ids in STRATA.items():
    hands = Counter(pages[i]['meta'].get('H') for i in ids)
    langs = Counter(pages[i]['meta'].get('L') for i in ids)
    pars = ML.paragraphs(pages, page_ids=ids)
    C[nm] = {'pages': sorted(ids, key=lambda i: (fnum(i), i)),
             'hands_by_page': dict(hands), 'langs_by_page': dict(langs),
             'hands_by_paragraph': dict(Counter(d['hand'] for d in pars)),
             'paragraphs_per_page': dict(Counter(d['page'] for d in pars))}
    say('%-9s pages=%d hands(page)=%s langs(page)=%s hands(par)=%s' % (
        nm, len(ids), dict(hands), dict(langs), C[nm]['hands_by_paragraph']))
OUT['C_hand_lang'] = C

# ================================================== D: R1(b) anatomy =======
say('')
say('=' * 78)
say('D. R1(b) anatomy: control-cell sparsity, attestation-vs-length curve,'
    ' and what the SUPPLEMENTARY relaxed match actually substitutes')
say('=' * 78)
D = OrderedDict()
for nm, ids in STRATA.items():
    pars, pi, pi_rec, nonpi, allw, nil = pools(ids)
    cells = defaultdict(list)
    for w in nonpi:
        g, r = strip(w)
        if g is None:
            continue
        cells[(g, len(w))].append((w, r, 1 if r in vocab else 0))
    tgt = []
    for w in pi:
        g, r = strip(w)
        if g is None:
            continue
        tgt.append((w, g, r, 1 if r in vocab else 0))
    matched = [t for t in tgt if (t[1], len(t[0])) in cells]
    dropped = [t for t in tgt if (t[1], len(t[0])) not in cells]
    # cell sparsity for the matched openers
    sizes = [len(cells[(t[1], len(t[0]))]) for t in matched]
    ntypes = [len(set(x[0] for x in cells[(t[1], len(t[0]))])) for t in matched]
    # attestation vs length in the control pool
    curve = defaultdict(lambda: [0, 0])
    for (g, ln), v in cells.items():
        for w, r, a in v:
            curve[ln][0] += 1; curve[ln][1] += a
    curve = {k: [v[0], round(v[1]/v[0], 4)] for k, v in sorted(curve.items())}
    # relaxed match: what length does the control actually have?
    def relaxed_pool(g, ln):
        for tol in (0, 1, 2):
            pool = []
            for dl in range(-tol, tol+1):
                pool.extend(cells.get((g, ln+dl), []))
            if pool:
                return pool
        pool = []
        for (gg, _l), v in cells.items():
            if gg == g:
                pool.extend(v)
        return pool or None
    rng = random.Random(SEED + 2)
    dl_all, dl_dropped = [], []
    for t in tgt:
        pool = relaxed_pool(t[1], len(t[0]))
        if pool is None:
            continue
        ml = sum(len(x[0]) for x in pool)/len(pool)
        dl_all.append(ml - len(t[0]))
        if (t[1], len(t[0])) not in cells:
            dl_dropped.append((t[0], len(t[0]), round(ml, 2),
                               round(sum(x[2] for x in pool)/len(pool), 3)))
    d = {'n_gallows_openers': len(tgt), 'n_matched_exact': len(matched),
         'n_dropped_exact': len(dropped),
         'mean_control_cell_tokens': sum(sizes)/len(sizes) if sizes else None,
         'median_control_cell_tokens': sorted(sizes)[len(sizes)//2] if sizes else None,
         'frac_openers_whose_cell_has_1_token': (
             sum(1 for s in sizes if s == 1)/len(sizes) if sizes else None),
         'frac_openers_whose_cell_has_le3_types': (
             sum(1 for s in ntypes if s <= 3)/len(ntypes) if ntypes else None),
         'attest_rate_by_length_controlpool': curve,
         'mean_control_minus_opener_length_relaxed': (
             sum(dl_all)/len(dl_all) if dl_all else None),
         'relaxed_substitution_for_exact_dropped_openers': dl_dropped[:40],
         'mean_control_minus_opener_length_relaxed_for_dropped': (
             sum(x[2]-x[1] for x in dl_dropped)/len(dl_dropped) if dl_dropped else None),
         'opener_attest_matched': (sum(t[3] for t in matched)/len(matched)
                                   if matched else None),
         'opener_attest_dropped': (sum(t[3] for t in dropped)/len(dropped)
                                   if dropped else None)}
    D[nm] = d
    say('%-9s gallows openers %d  exact-matched %d  dropped %d' % (
        nm, d['n_gallows_openers'], d['n_matched_exact'], d['n_dropped_exact']))
    say('          control cell size for matched openers: mean %.1f median %s ; '
        '%.3f of openers sit in a 1-token cell ; %.3f in a <=3-type cell' % (
            d['mean_control_cell_tokens'], d['median_control_cell_tokens'],
            d['frac_openers_whose_cell_has_1_token'],
            d['frac_openers_whose_cell_has_le3_types']))
    say('          relaxed match hands the DROPPED openers a control that is on '
        'average %.2f EVA chars SHORTER/LONGER than the opener' % (
            d['mean_control_minus_opener_length_relaxed_for_dropped'] or 0.0))
    say('          control-pool residue attestation by opener length: %s' %
        json.dumps(d['attest_rate_by_length_controlpool']))
OUT['D_b_anatomy'] = D

# ============================== E: R1(b) FREQUENCY confound ================
say('')
say('=' * 78)
say('E. R1(b) FREQUENCY confound. The pre-registered control is drawn from')
say('   TOKEN positions, so it is frequency-weighted; the openers are one per')
say('   paragraph and far more type-diverse. Frequent words have frequent')
say('   residues. Below: (E1) how big the frequency gap is, (E2) the same test')
say('   with the control additionally matched on the word\'s own section')
say('   frequency band, (E3) the same test with a TYPE-drawn control.')
say('=' * 78)
E = OrderedDict()
def fbin(f):
    return int(math.floor(math.log(max(f, 1), 2)))

for nm, ids in STRATA.items():
    pars, pi, pi_rec, nonpi, allw, nil = pools(ids)
    cells = defaultdict(list)
    for w in nonpi:
        g, r = strip(w)
        if g is None:
            continue
        cells[(g, len(w))].append((w, r, 1 if r in vocab else 0))
    tgt = []
    for w in pi:
        g, r = strip(w)
        if g is None:
            continue
        tgt.append((w, g, r, 1 if r in vocab else 0))
    matched = [t for t in tgt if (t[1], len(t[0])) in cells]

    # ---- E1 frequency gap under the pre-registered exact matching
    rng = random.Random(SEED + 11)
    keys = [(t[1], len(t[0])) for t in matched]
    obs_lf = sum(math.log(vocab[t[0]], 2) for t in matched)/len(matched)
    ctrl_lf = []
    for _ in range(2000):
        drawn = [rng.choice(cells[k]) for k in keys]
        ctrl_lf.append(sum(math.log(max(vocab[d[0]], 1), 2) for d in drawn)/len(drawn))
    m_lf, sd_lf = mean_sd(ctrl_lf)
    obs_hapaxish = sum(1 for t in matched if vocab[t[0]] <= 2)/len(matched)
    rng = random.Random(SEED + 12)
    ctrl_hap = []
    for _ in range(2000):
        drawn = [rng.choice(cells[k]) for k in keys]
        ctrl_hap.append(sum(1 for d in drawn if vocab[d[0]] <= 2)/len(drawn))

    # ---- E2 control matched on gallows + length + log2 frequency bin
    cells_f = defaultdict(list)
    for w in nonpi:
        g, r = strip(w)
        if g is None:
            continue
        cells_f[(g, len(w), fbin(vocab[w]))].append((w, r, 1 if r in vocab else 0))
    m2 = [t for t in tgt if (t[1], len(t[0]), fbin(vocab[t[0]])) in cells_f]
    k2 = [(t[1], len(t[0]), fbin(vocab[t[0]])) for t in m2]
    obs2 = sum(t[3] for t in m2)/len(m2) if m2 else None
    rng = random.Random(SEED + 13)
    null2 = [sum(rng.choice(cells_f[k])[2] for k in k2)/len(k2)
             for _ in range(NDRAW)] if m2 else []

    # ---- E3 TYPE-drawn control (each gallows-initial non-opener TYPE once),
    #        matched on gallows + length only
    cells_t = defaultdict(list)
    seen = set()
    for w in nonpi:
        if w in seen:
            continue
        seen.add(w)
        g, r = strip(w)
        if g is None:
            continue
        cells_t[(g, len(w))].append((w, r, 1 if r in vocab else 0))
    m3 = [t for t in tgt if (t[1], len(t[0])) in cells_t]
    k3 = [(t[1], len(t[0])) for t in m3]
    obs3 = sum(t[3] for t in m3)/len(m3) if m3 else None
    rng = random.Random(SEED + 14)
    null3 = [sum(rng.choice(cells_t[k])[2] for k in k3)/len(k3)
             for _ in range(NDRAW)] if m3 else []

    # ---- E4 relaxed matching (the agent's supplementary) but with the control
    #        ALSO frequency-binned, i.e. the reversal with the length artefact
    #        left in but frequency removed -- and relaxed matching with the
    #        control restricted to length >= opener length (removes the
    #        "short control" artefact).
    def relaxed_pool(cc, g, ln, minlen=None):
        for tol in (0, 1, 2):
            pool = []
            for dl in range(-tol, tol+1):
                if minlen is not None and ln+dl < minlen:
                    continue
                pool.extend(cc.get((g, ln+dl), []))
            if pool:
                return pool
        pool = []
        for (gg, ll), v in cc.items():
            if gg == g and (minlen is None or ll >= minlen):
                pool.extend(v)
        return pool or None
    rk, rt = [], []
    for t in tgt:
        pool = relaxed_pool(cells, t[1], len(t[0]), minlen=len(t[0]))
        if pool is not None:
            rk.append(pool); rt.append(t)
    obs4 = sum(t[3] for t in rt)/len(rt) if rt else None
    rng = random.Random(SEED + 15)
    null4 = [sum(rng.choice(p)[2] for p in rk)/len(rk) for _ in range(NDRAW)] if rt else []

    e = {
      'E1_mean_log2_freq_openers': obs_lf,
      'E1_mean_log2_freq_control': m_lf, 'E1_control_sd': sd_lf,
      'E1_sd_units': z(obs_lf, ctrl_lf), 'E1_p': p2(obs_lf, ctrl_lf),
      'E1_frac_openers_freq_le2': obs_hapaxish,
      'E1_frac_control_freq_le2': mean_sd(ctrl_hap)[0],
      'E1_frac_le2_sd_units': z(obs_hapaxish, ctrl_hap),
      'E2_n_matched': len(m2), 'E2_n_dropped': len(tgt)-len(m2),
      'E2_obs': obs2, 'E2_control_mean': mean_sd(null2)[0] if null2 else None,
      'E2_control_sd': mean_sd(null2)[1] if null2 else None,
      'E2_sd_units': z(obs2, null2) if null2 else None,
      'E2_p': p2(obs2, null2) if null2 else None,
      'E3_n_matched': len(m3), 'E3_obs': obs3,
      'E3_control_mean': mean_sd(null3)[0] if null3 else None,
      'E3_control_sd': mean_sd(null3)[1] if null3 else None,
      'E3_sd_units': z(obs3, null3) if null3 else None,
      'E3_p': p2(obs3, null3) if null3 else None,
      'E4_n_matched': len(rt), 'E4_obs': obs4,
      'E4_control_mean': mean_sd(null4)[0] if null4 else None,
      'E4_control_sd': mean_sd(null4)[1] if null4 else None,
      'E4_sd_units': z(obs4, null4) if null4 else None,
      'E4_p': p2(obs4, null4) if null4 else None,
    }
    E[nm] = e
    say('%-9s E1 mean log2 section-freq: openers %.3f vs matched control %.3f '
        '+/- %.3f -> %.1f SD (p=%.4f); frac freq<=2: openers %.3f vs ctrl %.3f '
        '(%.1f SD)' % (nm, e['E1_mean_log2_freq_openers'],
                       e['E1_mean_log2_freq_control'], e['E1_control_sd'],
                       e['E1_sd_units'], e['E1_p'], e['E1_frac_openers_freq_le2'],
                       e['E1_frac_control_freq_le2'], e['E1_frac_le2_sd_units']))
    say('          E2 gallows+length+FREQ-BIN matched: n=%d (dropped %d) obs %.4f '
        'vs %.4f +/- %.4f -> %.2f SD p=%.4f' % (
            e['E2_n_matched'], e['E2_n_dropped'], e['E2_obs'] or 0,
            e['E2_control_mean'] or 0, e['E2_control_sd'] or 0,
            e['E2_sd_units'] or 0, e['E2_p'] or 0))
    say('          E3 TYPE-drawn control (gallows+length): n=%d obs %.4f vs %.4f '
        '+/- %.4f -> %.2f SD p=%.4f' % (
            e['E3_n_matched'], e['E3_obs'] or 0, e['E3_control_mean'] or 0,
            e['E3_control_sd'] or 0, e['E3_sd_units'] or 0, e['E3_p'] or 0))
    say('          E4 relaxed match with control length >= opener length '
        '(kills the short-control artefact): n=%d obs %.4f vs %.4f -> %.2f SD '
        'p=%.4f' % (e['E4_n_matched'], e['E4_obs'] or 0,
                    e['E4_control_mean'] or 0, e['E4_sd_units'] or 0, e['E4_p'] or 0))
OUT['E_b_frequency'] = E

# ============================================ F: R2 page / transcriber ======
say('')
say('=' * 78)
say('F. R2: is "tail" (and dotted/points) a property of the STAR or of the')
say('   PAGE / of the transcriber\'s commenting habit?')
say('=' * 78)
recS = {p['id'] for p in pages.values() if p['meta'].get('I') == 'S'}
F = OrderedDict()
for nm, ids in (('TEST_even', {i for i in recS if fnum(i) % 2 == 0}),
                ('FIT_odd', {i for i in recS if fnum(i) % 2 == 1}),
                ('ALL', recS)):
    pars = [d for d in ML.paragraphs(pages, page_ids=ids) if d['star']]
    per_page = defaultdict(lambda: Counter())
    for d in pars:
        s = d['star']
        per_page[d['page']]['n'] += 1
        per_page[d['page']]['tail'] += 1 if s['tail'] else 0
        per_page[d['page']]['dotted'] += 1 if s['dotted'] else 0
        per_page[d['page']]['pt8'] += 1 if s['points'] == 8 else 0
        per_page[d['page']]['pt7'] += 1 if s['points'] == 7 else 0
        per_page[d['page']]['uncertain'] += 1 if s['uncertain'] else 0
    tbl = {p: {'n': c['n'], 'tail': c['tail'], 'dotted': c['dotted'],
               'pt8': c['pt8'], 'pt7': c['pt7'], 'uncertain': c['uncertain']}
           for p, c in sorted(per_page.items(), key=lambda kv: fnum(kv[0]))}
    F[nm] = {'n_star_paragraphs': len(pars), 'per_page': tbl,
             'pages_all_or_nothing_tail': sum(
                 1 for c in tbl.values() if c['tail'] in (0, c['n'])),
             'pages_all_or_nothing_dotted': sum(
                 1 for c in tbl.values() if c['dotted'] in (0, c['n'])),
             'pages_all_or_nothing_pt8': sum(
                 1 for c in tbl.values() if c['pt8'] in (0, c['n'])),
             'n_pages': len(tbl),
             'lang_of_pages': {p: pages[p]['meta'].get('L') for p in tbl},
             'hand_of_pages': {p: pages[p]['meta'].get('H') for p in tbl}}
    say('%-9s star paragraphs %d over %d pages; pages all-or-nothing: tail %d/%d '
        'dotted %d/%d 8-point %d/%d' % (
            nm, len(pars), len(tbl), F[nm]['pages_all_or_nothing_tail'], len(tbl),
            F[nm]['pages_all_or_nothing_dotted'], len(tbl),
            F[nm]['pages_all_or_nothing_pt8'], len(tbl)))
say('')
say('  per-page star attribute table (ALL Recipes pages):')
for p, c in F['ALL']['per_page'].items():
    say('    %-7s n=%-3d tail=%-3d dotted=%-3d 8pt=%-3d 7pt=%-3d unc=%-3d lang=%s hand=%s'
        % (p, c['n'], c['tail'], c['dotted'], c['pt8'], c['pt7'], c['uncertain'],
           pages[p]['meta'].get('L'), pages[p]['meta'].get('H')))

# transcriber commenting habit: raw comment wording, per page
say('')
say('  raw ZL comment wording per page (distinct comment strings, first 3):')
wording = OrderedDict()
for pid in sorted(recS, key=fnum):
    cs = []
    for l in pages[pid]['loci']:
        if l['type'] == 'P' and l['para_start'] and l['comment']:
            cs.append(l['comment'])
    u = sorted(set(cs))
    wording[pid] = {'n_para_start_with_comment': len(cs),
                    'n_distinct': len(u), 'examples': u[:3]}
    say('    %-7s %d comments, %d distinct | %s' % (
        pid, len(cs), len(u), ' || '.join(x[:60] for x in u[:3])))
F['comment_wording_by_page'] = wording

# how many para_start loci carry NO comment at all (star annotation missing)
miss = OrderedDict()
for nm, ids in (('TEST_even', {i for i in recS if fnum(i) % 2 == 0}),
                ('FIT_odd', {i for i in recS if fnum(i) % 2 == 1}),
                ('ALL', recS)):
    pars = ML.paragraphs(pages, page_ids=ids)
    n = len(pars)
    nc = sum(1 for d in pars if d['comment'])
    ns = sum(1 for d in pars if d['star'])
    npts = sum(1 for d in pars if d['star'] and d['star']['points'] is not None)
    nunc = sum(1 for d in pars if d['star'] and d['star']['uncertain'])
    miss[nm] = {'n_paragraphs': n, 'with_any_comment': nc, 'with_star': ns,
                'with_point_count': npts, 'star_marked_uncertain': nunc}
    say('  %-9s paragraphs %d | with comment %d | parsed as star %d | with point '
        'count %d | transcriber marked uncertain %d' % (nm, n, nc, ns, npts, nunc))
F['star_annotation_coverage'] = miss
OUT['F_r2_page_transcriber'] = F

# does 'tail' predict paragraph LENGTH once page is held fixed? (the agent's
# claim is that every tail effect is the page; verify with a within-page
# stratified permutation for the top registered effect, recomputed here)
say('')
say('  cross-check: within-page variance of "tail" on TEST pages')
tp = {i for i in recS if fnum(i) % 2 == 0}
pars = [d for d in ML.paragraphs(pages, page_ids=tp) if d['star']]
bypage = defaultdict(list)
for d in pars:
    bypage[d['page']].append(1 if d['star']['tail'] else 0)
for p, v in sorted(bypage.items(), key=lambda kv: fnum(kv[0])):
    say('    %-7s tail %d/%d' % (p, sum(v), len(v)))
OUT['F_tail_by_page_TEST'] = {p: [sum(v), len(v)] for p, v in bypage.items()}

with io.open(os.path.join(RES, 'v_r1r2_confound_1.json'), 'w', encoding='utf-8') as f:
    json.dump(OUT, f, indent=1, ensure_ascii=False)
with io.open(os.path.join(RES, 'v_r1r2_confound_1.stdout.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n')
print('\nwrote results/v_r1r2_confound_1.json')
