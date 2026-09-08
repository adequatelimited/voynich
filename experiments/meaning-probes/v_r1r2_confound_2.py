#!/usr/bin/env python3
"""v_r1r2_confound_2.py — second confound block for R1(b).

G1  exact gallows+length matching but with the control pool taken from the WHOLE
    Recipes-B section (both halves) instead of the split half. This keeps the
    pre-registered EXACT matching (so no short-control artefact) while cutting
    the number of openers that have to be dropped.
G2  page-stratified matching: control drawn only from the SAME PAGE.
G3  per-page opener vs control attestation (how page-clustered is (b)?)
G4  type-drawn control AND control length >= opener length: both the frequency
    weighting and the short-control artefact removed at once.
G5  attestation vocabulary that excludes the word's own page.
Read-only. seed 408, 10000 draws.
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
    s = ' '.join(str(x) for x in a); L.append(s); print(s)

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

def zz(obs, null):
    m, sd = mean_sd(null)
    return (obs-m)/sd if sd > 0 else 0.0

def p2(obs, null):
    m = sum(null)/len(null); d = abs(obs-m)
    k = sum(1 for x in null if abs(x-m) >= d-1e-12)
    return (1+k)/(len(null)+1)

pages = ML.parse_pages(ZL, comma_split=True)
recB = {p['id'] for p in pages.values()
        if p['meta'].get('I') == 'S' and p['meta'].get('L') == 'B'
        and 103 <= p['fnum'] <= 116}
TESTids = {i for i in recB if fnum(i) % 2 == 0}
FITids = {i for i in recB if fnum(i) % 2 == 1}
STRATA = OrderedDict([('TEST_even', TESTids), ('FIT_odd', FITids), ('ALL', recB)])

vocab = Counter()
vocab_by_page = defaultdict(Counter)
for d in ML.paragraphs(pages, page_ids=recB):
    vocab.update(d['words'])
    vocab_by_page[d['page']].update(d['words'])

def openers_and_nonpi(ids):
    pars = ML.paragraphs(pages, page_ids=ids)
    op = [(d['first_word'], d['page']) for d in pars if d['first_word']]
    non = [(w, d['page']) for d in pars for w in d['words'][1:]]
    return op, non

OP, NON = {}, {}
for nm, ids in STRATA.items():
    OP[nm], NON[nm] = openers_and_nonpi(ids)

def attested(r, page=None, exclude_own_page=False):
    if exclude_own_page:
        n = vocab[r] - vocab_by_page[page][r]
        return 1 if n > 0 else 0
    return 1 if vocab[r] > 0 else 0

def run_match(tgt, cellfn, seed, ndraw=NDRAW):
    """tgt: list of (word, page, gallows, residue, attested_flag).
    cellfn(t) -> list of (word, residue, attested_flag) or None."""
    keys, used = [], []
    for t in tgt:
        pool = cellfn(t)
        if pool:
            keys.append(pool); used.append(t)
    if not used:
        return None
    obs = sum(t[4] for t in used)/len(used)
    rng = random.Random(seed)
    null = [sum(rng.choice(p)[2] for p in keys)/len(keys) for _ in range(ndraw)]
    m, sd = mean_sd(null)
    return {'n_matched': len(used), 'n_dropped': len(tgt)-len(used),
            'obs': obs, 'control_mean': m, 'control_sd': sd,
            'sd_units': zz(obs, null), 'p_two_sided': p2(obs, null),
            'mean_opener_len': sum(len(t[0]) for t in used)/len(used),
            'mean_control_len': sum(
                sum(len(x[0]) for x in p)/len(p) for p in keys)/len(keys)}

def fmt(tag, r):
    if r is None:
        return '%s  (no matches)' % tag
    return ('%s n=%d (dropped %d) obs %.4f vs ctrl %.4f +/- %.4f -> %+.2f SD '
            'p=%.4f  [len opener %.2f / control %.2f]' % (
                tag, r['n_matched'], r['n_dropped'], r['obs'], r['control_mean'],
                r['control_sd'], r['sd_units'], r['p_two_sided'],
                r['mean_opener_len'], r['mean_control_len']))

OUT = OrderedDict()
OUT['inputs'] = {'ZL3b-n.txt': ML.sha256(ZL),
                 'meaning_lib.py': ML.sha256(os.path.join(HERE, 'meaning_lib.py')),
                 't_r1r2.py': ML.sha256(os.path.join(HERE, 't_r1r2.py')),
                 'results/r1r2.json': ML.sha256(os.path.join(RES, 'r1r2.json'))}
OUT['seed'] = SEED; OUT['n_draws'] = NDRAW

# whole-section control pools ------------------------------------------------
sec_cells_tok = defaultdict(list)
sec_cells_typ = defaultdict(list)
seen = set()
for w, pg in NON['ALL']:
    g, r = strip(w)
    if g is None:
        continue
    sec_cells_tok[(g, len(w))].append((w, r, attested(r)))
    if w not in seen:
        seen.add(w)
        sec_cells_typ[(g, len(w))].append((w, r, attested(r)))

G = OrderedDict()
for nm in STRATA:
    tgt = []
    for w, pg in OP[nm]:
        g, r = strip(w)
        if g is None:
            continue
        tgt.append((w, pg, g, r, attested(r)))
    # half-local pools
    loc_tok = defaultdict(list); loc_typ = defaultdict(list)
    loc_page = defaultdict(list)
    s2 = set()
    for w, pg in NON[nm]:
        g, r = strip(w)
        if g is None:
            continue
        loc_tok[(g, len(w))].append((w, r, attested(r)))
        loc_page[(pg, g, len(w))].append((w, r, attested(r)))
        if w not in s2:
            s2.add(w); loc_typ[(g, len(w))].append((w, r, attested(r)))

    say('')
    say('=' * 78)
    say('STRATUM', nm, ' gallows openers:', len(tgt))
    say('=' * 78)

    r0 = run_match(tgt, lambda t: loc_tok.get((t[2], len(t[0]))), SEED + 21)
    say(fmt('  [reference] pre-registered exact match, half-local token pool:', r0))

    # G1 whole-section control pool, exact matching
    r1 = run_match(tgt, lambda t: sec_cells_tok.get((t[2], len(t[0]))), SEED + 22)
    say(fmt('  G1 exact match, WHOLE-SECTION token pool               :', r1))
    r1t = run_match(tgt, lambda t: sec_cells_typ.get((t[2], len(t[0]))), SEED + 23)
    say(fmt('  G1t exact match, WHOLE-SECTION TYPE pool                :', r1t))

    # G2 page-stratified
    r2 = run_match(tgt, lambda t: loc_page.get((t[1], t[2], len(t[0]))), SEED + 24)
    say(fmt('  G2 exact match, control from the SAME PAGE only         :', r2))

    # G4 type-drawn AND control length >= opener length
    def relaxed_typ_minlen(t):
        g, ln = t[2], len(t[0])
        for tol in (0, 1, 2, 3, 4):
            pool = []
            for dl in range(0, tol + 1):
                pool.extend(loc_typ.get((g, ln + dl), []))
            if pool:
                return pool
        pool = []
        for (gg, ll), v in loc_typ.items():
            if gg == g and ll >= ln:
                pool.extend(v)
        return pool or None
    r4 = run_match(tgt, relaxed_typ_minlen, SEED + 25)
    say(fmt('  G4 TYPE pool + control length >= opener length          :', r4))

    def relaxed_typ_minlen_sec(t):
        g, ln = t[2], len(t[0])
        for tol in (0, 1, 2, 3, 4):
            pool = []
            for dl in range(0, tol + 1):
                pool.extend(sec_cells_typ.get((g, ln + dl), []))
            if pool:
                return pool
        pool = []
        for (gg, ll), v in sec_cells_typ.items():
            if gg == g and ll >= ln:
                pool.extend(v)
        return pool or None
    r4s = run_match(tgt, relaxed_typ_minlen_sec, SEED + 26)
    say(fmt('  G4s same, WHOLE-SECTION type pool (0 openers dropped)   :', r4s))

    # G5 attestation excluding the word's own page, both sides
    sec_tok_x = defaultdict(list)
    for w, pg in NON['ALL']:
        g, r = strip(w)
        if g is None:
            continue
        sec_tok_x[(g, len(w))].append((w, r, attested(r, pg, True)))
    tgt_x = [(t[0], t[1], t[2], t[3], attested(t[3], t[1], True)) for t in tgt]
    r5 = run_match(tgt_x, lambda t: sec_tok_x.get((t[2], len(t[0]))), SEED + 27)
    say(fmt('  G5 exact match, attestation must be OFF the own page    :', r5))

    # G3 per-page breakdown
    per_page = defaultdict(lambda: [0, 0])
    for t in tgt:
        per_page[t[1]][0] += 1; per_page[t[1]][1] += t[4]
    pp = {p: [v[0], round(v[1]/v[0], 3)] for p, v in
          sorted(per_page.items(), key=lambda kv: fnum(kv[0]))}
    say('  G3 opener residue attestation per page: %s' % json.dumps(pp))

    G[nm] = {'reference_preregistered': r0, 'G1_section_token_pool': r1,
             'G1t_section_type_pool': r1t, 'G2_same_page': r2,
             'G4_type_pool_minlen_local': r4, 'G4s_type_pool_minlen_section': r4s,
             'G5_offpage_attestation': r5, 'G3_per_page_opener_attestation': pp}

OUT['G'] = G

with io.open(os.path.join(RES, 'v_r1r2_confound_2.json'), 'w', encoding='utf-8') as f:
    json.dump(OUT, f, indent=1, ensure_ascii=False)
with io.open(os.path.join(RES, 'v_r1r2_confound_2.stdout.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n')
print('\nwrote results/v_r1r2_confound_2.json')
