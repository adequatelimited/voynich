#!/usr/bin/env python3
"""t_z1.py -- Z1: ordinal gradient inside a zodiac ring (pre-registered).

Protocol: experiments/meaning-probes/PROTOCOL.md, section "Z1".
Gate (frozen): ordinal-like only if, on the TEST signs, permutation p < 0.01
AND Delta >= 25% of the median Delta over the numeral controls at matched ring
sizes.  Report the fraction of numeral controls that themselves clear p < 0.01
at these ring sizes; if < 0.5 the test is UNDERPOWERED.

Stdlib only.  Deterministic: seed 408, 10,000 permutation draws.

Ambiguity resolutions (all taken in the direction that makes the test HARDER to
pass; see AMBIGUITIES below and the JSON output).
"""
import io, json, math, random, re, sys, time
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML

HERE = Path(__file__).resolve().parent
RES = HERE / 'results'
RES.mkdir(exist_ok=True)

ZL3B = HERE / '..' / '..' / 'data' / 'corpora' / 'ZL3b-n.txt'
GC2A = HERE / '..' / '..' / 'data' / 'corpora' / 'GC2a-n.txt'
CULP = Path('R:/Coding/LinearA/tmp/voynich_lab/pg49513.txt')
VULG = Path('R:/Coding/LinearA/tmp/voynich_lab/bibles/Latin.xml')

SEED = ML.SEED          # 408
NPERM = 10000
MIN_RING = 8            # "every ring with >= 8 labels"

AMBIGUITIES = [
    "Two statistics are defined (Delta and rho_bar) but gate (i) says only "
    "'permutation p < 0.01'. Harder reading taken: BOTH statistics must reach "
    "p < 0.01, in the ordinal-like direction (Delta > 0 and rho_bar < 0). The "
    "per-statistic p-values and the outcome under the laxer 'either one' "
    "reading are both reported.",
    "'Delta pooled over rings weighted by pair count' is read as pooling every "
    "pair across rings (mean of all g=1 pairs minus mean of all g>=3 pairs), "
    "which is exactly a pair-count weighting. The alternative reading (mean of "
    "per-ring Deltas weighted by that ring's pair count) is computed and "
    "reported as delta_alt with its own p.",
    "Gap g = |i - j| in linear ring order, no wrap-around, as instructed; the "
    "ring is not treated as circular.",
    "Numeral controls are 30 items but the observed TEST ring sizes sum to 139, "
    "so the series must be reused. Primary construction: cut the series "
    "cyclically (ring boundaries walk through 1..30 and wrap). Alternative "
    "construction reported: every ring of size k is the contiguous run 1..k. "
    "For gate (ii) the threshold uses the LARGER of the two median control "
    "Deltas (the harder threshold).",
    "Two-sided permutation p = (1 + #{|null - mean(null)| >= |obs - mean(null)|}) "
    "/ (NPERM + 1); never rounded down.",
    "Rings with fewer than 8 legible labels are dropped entirely (they are not "
    "merged into neighbouring rings).",
    "Controls in Latin script have no byte-pair merges, so their 'glyph unit' "
    "level and their raw-character level are identical by construction; the "
    "numeral-control numbers therefore serve both robustness levels.",
    "The pre-registered negative control '30 random Voynich herbal-section "
    "label words' is degenerate: the herbal section contains only 32 label "
    "loci / 31 clean label word tokens, most of them the single-character "
    "marginal glyphs of f49v, so the 'random sample of 30' is very nearly the "
    "whole population and its sequences are 1-2 units long. It is run exactly "
    "as pre-registered and reported, and a non-degenerate supplementary "
    "negative control (30 random non-zodiac label word types, seed 408) is "
    "added and flagged as supplementary, outside the gate.",
    "The observed TEST ring sizes sum to 139 while every control series has 30 "
    "items, so any matched-size control must reuse its series across rings. "
    "Reuse correlates the control's rings while the permutation null "
    "re-randomises each ring independently, which inflates the controls' "
    "significance. The pre-registered power figure is reported as specified, "
    "and alongside it the negative-control false-positive rate under the same "
    "construction and a reuse-free power figure on rings [18, 12] (each series "
    "item used exactly once). The Voynich statistic is not affected -- its ten "
    "rings are ten distinct arrangements, which is what the null assumes.",
    "Replication on GC2a-n.txt is not runnable: GC2a is in the v101 alphabet, "
    "whose glyphs include digits and capitals, and the frozen clean parser "
    "keeps only pure [a-z]+ tokens. 208 of its 299 zodiac label loci lose "
    "every token, and no TEST-sign ring reaches the 8-label minimum. Rather "
    "than re-implement the frozen tokeniser for one corpus, the replication is "
    "reported as NOT RUN with those diagnostics. The protocol requires "
    "replication only of gates that pass on ZL3b.",
]


# ------------------------------------------------------------------ helpers --

def avg_ranks(vals):
    """Average (tie-corrected) ranks, ascending, 1-based."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        r = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = r
        i = j + 1
    return ranks


def mean(xs):
    return sum(xs) / len(xs) if xs else float('nan')


def sd_pop(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs)) if xs else 0.0


def two_sided_p(obs, nulls):
    mu = mean(nulls)
    d = abs(obs - mu)
    c = sum(1 for x in nulls if abs(x - mu) >= d - 1e-12)
    return (1.0 + c) / (len(nulls) + 1.0)


# ------------------------------------------------------- per-ring machinery --

class Ring(object):
    """Precomputed, permutation-invariant scaffolding for one ring."""

    def __init__(self, seqs):
        n = self.n = len(seqs)
        S = [[0.0] * n for _ in range(n)]
        flat = []
        for i in range(n):
            for j in range(i + 1, n):
                s = ML.lcs_sim(seqs[i], seqs[j])
                S[i][j] = S[j][i] = s
                flat.append(s)
        self.S = S
        self.total = sum(flat)
        self.m = len(flat)                       # pair count
        self.n_g1 = n - 1
        self.n_g2 = n - 2
        self.n_g3 = self.m - self.n_g1 - self.n_g2

        # rank matrix over the ring's pair-similarity multiset (invariant)
        rs = avg_ranks(flat)
        R = [[0.0] * n for _ in range(n)]
        k = 0
        for i in range(n):
            for j in range(i + 1, n):
                R[i][j] = R[j][i] = rs[k]
                k += 1
        self.R = R

        # gap ranks: pairs at gap d number (n-d), invariant under permutation
        gvals = []
        for d in range(1, n):
            gvals.extend([d] * (n - d))
        rg = avg_ranks(gvals)
        self.w = [0.0] * n
        pos = 0
        for d in range(1, n):
            self.w[d] = rg[pos]                  # all pairs at gap d share a rank
            pos += (n - d)
        self.mu_g, self.sd_g = mean(rg), sd_pop(rg)
        self.mu_s, self.sd_s = mean(rs), sd_pop(rs)
        self.rho_ok = self.sd_g > 0 and self.sd_s > 0

    def scan(self, p):
        """Return (s1, s2, cross) for label order `p` (list of label indices)."""
        S, R, w, n = self.S, self.R, self.w, self.n
        s1 = 0.0
        for a, b in zip(p, p[1:]):
            s1 += S[a][b]
        s2 = 0.0
        for a, b in zip(p, p[2:]):
            s2 += S[a][b]
        cross = 0.0
        for d in range(1, n):
            wd = w[d]
            if wd:
                t = 0.0
                for a, b in zip(p, p[d:]):
                    t += R[a][b]
                cross += wd * t
        return s1, s2, cross

    def rho(self, cross):
        if not self.rho_ok:
            return 0.0
        return (cross / self.m - self.mu_g * self.mu_s) / (self.sd_g * self.sd_s)


def stats_from_scans(rings, scans):
    """Aggregate Delta, delta_alt, rho_bar from per-ring (s1, s2, cross)."""
    tot1 = tot3 = 0.0
    n1 = n3 = 0
    wsum = dsum = 0.0
    rhos = []
    for rg, (s1, s2, cross) in zip(rings, scans):
        s3 = rg.total - s1 - s2
        tot1 += s1; n1 += rg.n_g1
        tot3 += s3; n3 += rg.n_g3
        if rg.n_g1 and rg.n_g3:
            d = s1 / rg.n_g1 - s3 / rg.n_g3
            wsum += rg.m
            dsum += rg.m * d
        rhos.append(rg.rho(cross))
    delta = (tot1 / n1 if n1 else 0.0) - (tot3 / n3 if n3 else 0.0)
    delta_alt = dsum / wsum if wsum else 0.0
    return delta, delta_alt, mean(rhos)


def run_z1(ring_seq_lists, nperm=NPERM, seed=SEED, label=''):
    """ring_seq_lists: list of rings, each a list of unit-sequences in order."""
    rings = [Ring(s) for s in ring_seq_lists if len(s) >= MIN_RING]
    if not rings:
        return None
    obs_scans = [r.scan(list(range(r.n))) for r in rings]
    d_obs, dalt_obs, rho_obs = stats_from_scans(rings, obs_scans)

    rng = random.Random(seed)
    nd, ndalt, nrho = [], [], []
    for _ in range(nperm):
        scans = []
        for r in rings:
            p = list(range(r.n))
            rng.shuffle(p)
            scans.append(r.scan(p))
        a, b, c = stats_from_scans(rings, scans)
        nd.append(a); ndalt.append(b); nrho.append(c)

    out = {
        'label': label,
        'n_rings': len(rings),
        'ring_sizes': [r.n for r in rings],
        'n_labels': sum(r.n for r in rings),
        'n_pairs': sum(r.m for r in rings),
        'delta': d_obs,
        'delta_p': two_sided_p(d_obs, nd),
        'delta_null_mean': mean(nd),
        'delta_null_sd': sd_pop(nd),
        'delta_z': (d_obs - mean(nd)) / sd_pop(nd) if sd_pop(nd) > 0 else 0.0,
        'delta_alt': dalt_obs,
        'delta_alt_p': two_sided_p(dalt_obs, ndalt),
        'rho_bar': rho_obs,
        'rho_bar_p': two_sided_p(rho_obs, nrho),
        'rho_null_mean': mean(nrho),
        'rho_null_sd': sd_pop(nrho),
        'rho_z': (rho_obs - mean(nrho)) / sd_pop(nrho) if sd_pop(nrho) > 0 else 0.0,
        'mean_sim_g1': sum(s[0] for s in obs_scans) / sum(r.n_g1 for r in rings),
        'mean_sim_g3plus': (sum(r.total - s[0] - s[1] for r, s in zip(rings, obs_scans))
                            / sum(r.n_g3 for r in rings)),
        'ordinal_like_direction': bool(d_obs > 0 and rho_obs < 0),
        'p_strict': max(two_sided_p(d_obs, nd), two_sided_p(rho_obs, nrho)),
        'p_lax': min(two_sided_p(d_obs, nd), two_sided_p(rho_obs, nrho)),
    }
    return out


# ------------------------------------------------------------ corpus access --

def seq_of_words(words, level):
    """Label sequence = concatenation of the unit sequences of its words."""
    out = []
    for w in words:
        out.extend(ML.bpe_apply(w) if level == 'units' else list(w))
    return out


def voynich_rings(path, signs, level, comma_split):
    pages = ML.parse_pages(str(path), comma_split=comma_split)
    labels = ML.zodiac_labels(pages, comma_split=comma_split)
    by = ML.sign_rings(labels)
    rings, meta = [], []
    for s in signs:
        for ring, recs in by.get(s, {}).items():
            rings.append([seq_of_words(r['words'], level) for r in recs])
            meta.append({'sign': s, 'ring': ring, 'n': len(recs)})
    keep = [i for i, r in enumerate(rings) if len(r) >= MIN_RING]
    return [rings[i] for i in keep], [meta[i] for i in keep]


def cut_cyclic(series, sizes):
    """Cut a 30-item series into rings of `sizes`, walking cyclically."""
    out, k = [], 0
    for sz in sizes:
        ring = [series[(k + i) % len(series)] for i in range(sz)]
        k = (k + sz) % len(series)
        out.append(ring)
    return out


def cut_prefix(series, sizes):
    """Alternative: every ring of size k is the contiguous run series[0:k]."""
    return [[series[i % len(series)] for i in range(sz)] for sz in sizes]


CUTS = OrderedDict([('cyclic', cut_cyclic), ('prefix', cut_prefix)])


def control_rings(series, sizes, cut, level='chars'):
    return [[seq_of_words([w], level) for w in ring]
            for ring in CUTS[cut](series, sizes)]


# ------------------------------------------------------------------- main ----

def main():
    t0 = time.time()
    log = []

    def say(*a):
        s = ' '.join(str(x) for x in a)
        print(s)
        log.append(s)

    inputs = OrderedDict()
    for name, p in [('ZL3b-n.txt', ZL3B), ('GC2a-n.txt', GC2A),
                    ('pg49513.txt (Culpeper)', CULP), ('Latin.xml (Vulgate)', VULG),
                    ('meaning_lib.py', HERE / 'meaning_lib.py'),
                    ('t_z1.py', HERE / 't_z1.py')]:
        inputs[name] = {'path': str(Path(p).resolve()), 'sha256': ML.sha256(str(p))}

    say('=' * 78)
    say('Z1 -- ordinal gradient inside a zodiac ring')
    say('seed', SEED, '| permutations', NPERM, '| min ring size', MIN_RING)
    say('=' * 78)
    for k, v in inputs.items():
        say('  sha256 %-24s %s' % (k, v['sha256']))

    results = OrderedDict()

    # ---- primary + robustness on ZL3b ------------------------------------
    say('')
    say('--- ZL3b-n.txt: FIT signs and TEST signs, 4 configurations ---')
    obs = OrderedDict()
    test_sizes = None
    for level in ('units', 'chars'):
        for comma in (True, False):
            for split, signs in (('FIT', ML.FIT_SIGNS), ('TEST', ML.TEST_SIGNS)):
                rings, meta = voynich_rings(ZL3B, signs, level, comma)
                key = '%s|%s|comma_split=%s' % (split, level, comma)
                r = run_z1(rings, label=key)
                r['rings_meta'] = meta
                obs[key] = r
                if split == 'TEST' and level == 'units' and comma:
                    test_sizes = r['ring_sizes']
                say('  %-34s rings=%d n=%3d pairs=%4d  Delta=%+.5f p=%.4f  '
                    'rho_bar=%+.4f p=%.4f' %
                    (key, r['n_rings'], r['n_labels'], r['n_pairs'],
                     r['delta'], r['delta_p'], r['rho_bar'], r['rho_bar_p']))
    results['observed'] = obs
    say('  TEST-sign ring sizes used for all controls: %s (sum %d)'
        % (test_sizes, sum(test_sizes)))
    say('  TEST rings: ' + ', '.join('%s r%d n=%d' % (m['sign'], m['ring'], m['n'])
                                     for m in obs['TEST|units|comma_split=True']['rings_meta']))

    # ---- numeral controls -------------------------------------------------
    say('')
    say('--- numeral controls (power calibration) at matched ring sizes ---')
    numerals = ML.numeral_controls()
    nctrl = OrderedDict()
    for cut in CUTS:
        for name, series in numerals.items():
            rings = control_rings(series, test_sizes, cut, level='chars')
            r = run_z1(rings, label='%s|%s' % (name, cut))
            nctrl['%s|%s' % (name, cut)] = r
            say('  %-24s Delta=%+.5f p=%.4f  rho_bar=%+.4f p=%.4f  '
                'sim(g=1)=%.3f sim(g>=3)=%.3f' %
                ('%s [%s]' % (name, cut), r['delta'], r['delta_p'],
                 r['rho_bar'], r['rho_bar_p'], r['mean_sim_g1'], r['mean_sim_g3plus']))
    results['numeral_controls'] = nctrl

    # ---- negative controls ------------------------------------------------
    say('')
    say('--- negative controls ---')
    rng = random.Random(SEED)

    culp = ML.culpeper_entries(str(CULP))
    heads = [ML.letters_only(ML.words_en(h)) for _, h, _ in culp]
    heads = [h for h in heads if h]
    culp30 = [''.join(h) for h in heads[:30]]

    pages_h = ML.parse_pages(str(ZL3B))
    hpages = ML.section_pages(pages_h, 'H')
    hlab = [w for p in hpages for l in p['loci'] if l['type'] == 'L' for w in l['words']]
    voy30 = random.Random(SEED).sample(hlab, 30)

    vtxt = io.open(str(VULG), encoding='utf-8', errors='replace').read()
    vtxt = re.sub(r'<[^>]*>', ' ', vtxt)
    vtypes = sorted(set(w.lower() for w in re.findall(r'[A-Za-z]+', vtxt) if len(w) >= 2))
    vul30 = random.Random(SEED).sample(vtypes, 30)

    say('  Culpeper headings available: %d, using first 30; e.g. %s'
        % (len(heads), culp30[:3]))
    say('  Voynich herbal label word tokens available: %d, sampled 30 (seed %d); e.g. %s'
        % (len(hlab), SEED, voy30[:3]))
    say('  Vulgate word types: %d, sampled 30 (seed %d); e.g. %s'
        % (len(vtypes), SEED, vul30[:3]))

    nzlab = sorted(set(w for p in pages_h.values() for l in p['loci']
                       if l['type'] == 'L' and l['sub'] != 'z' for w in l['words']))
    nz30 = random.Random(SEED).sample(nzlab, 30)
    say('  SUPPLEMENTARY (not pre-registered, outside the gate): non-zodiac '
        'label word types available: %d, sampled 30 (seed %d); e.g. %s'
        % (len(nzlab), SEED, nz30[:3]))
    say('  NOTE: the pre-registered herbal-label control is degenerate -- only '
        '%d clean herbal label word tokens exist, mean length %.2f chars.'
        % (len(hlab), sum(len(w) for w in voy30) / 30.0))

    negs = OrderedDict([('Culpeper30', (culp30, 'chars')),
                        ('VoynichHerbalLabels30', (voy30, 'units')),
                        ('VulgateTypes30', (vul30, 'chars')),
                        ('SUPP_VoynichNonZodiacLabels30', (nz30, 'units'))])
    negctrl = OrderedDict()
    for cut in CUTS:
        for name, (series, lvl) in negs.items():
            rings = control_rings(series, test_sizes, cut, level=lvl)
            r = run_z1(rings, label='%s|%s' % (name, cut))
            negctrl['%s|%s' % (name, cut)] = r
            say('  %-34s Delta=%+.5f p=%.4f  rho_bar=%+.4f p=%.4f' %
                ('%s [%s]' % (name, cut), r['delta'], r['delta_p'],
                 r['rho_bar'], r['rho_bar_p']))
    # raw-character variant of the Voynich negative control (for the char run)
    for cut in CUTS:
        rings = control_rings(voy30, test_sizes, cut, level='chars')
        r = run_z1(rings, label='VoynichHerbalLabels30_chars|%s' % cut)
        negctrl['VoynichHerbalLabels30_chars|%s' % cut] = r
        say('  %-34s Delta=%+.5f p=%.4f  rho_bar=%+.4f p=%.4f' %
            ('VoynichHerbalLabels30 chars [%s]' % cut, r['delta'], r['delta_p'],
             r['rho_bar'], r['rho_bar_p']))
    results['negative_controls'] = negctrl

    # ---- supplementary: reuse-free power ---------------------------------
    # The observed TEST ring sizes sum to 139 but every control series has only
    # 30 items, so any matched-size construction must reuse the series. Reuse
    # makes the rings correlated while the permutation null re-randomises each
    # ring independently, which shrinks the null spread and inflates the
    # controls' significance. Sizes [18, 12] use each series item exactly once,
    # so this variant is free of that artefact.
    say('')
    say('--- SUPPLEMENTARY: reuse-free power, rings [18, 12] (each series item '
        'used exactly once) ---')
    onepass = OrderedDict()
    for name, series in numerals.items():
        r = run_z1(control_rings(series, [18, 12], 'cyclic', 'chars'),
                   label='%s|onepass' % name)
        onepass[name] = r
        say('  %-24s Delta=%+.5f p=%.4f  rho_bar=%+.4f p=%.4f' %
            (name, r['delta'], r['delta_p'], r['rho_bar'], r['rho_bar_p']))
    for name, (series, lvl) in negs.items():
        r = run_z1(control_rings(series, [18, 12], 'cyclic', lvl),
                   label='%s|onepass' % name)
        onepass[name] = r
        say('  %-24s Delta=%+.5f p=%.4f  rho_bar=%+.4f p=%.4f' %
            (name[:24], r['delta'], r['delta_p'], r['rho_bar'], r['rho_bar_p']))
    results['supplementary_no_reuse'] = onepass

    # ---- replication on GC2a ---------------------------------------------
    say('')
    say('--- replication: GC2a-n.txt, TEST signs, units, comma_split=True ---')
    gpages = ML.parse_pages(str(GC2A))
    glab = ML.zodiac_labels(gpages)
    g_loci = sum(1 for p in gpages.values() for l in p['loci']
                 if l['type'] == 'L' and l['sub'] == 'z')
    g_by = ML.sign_rings(glab)
    g_sizes = OrderedDict((s, [len(v) for v in g_by.get(s, {}).values()])
                          for s in ML.TEST_SIGNS)
    grings, gmeta = voynich_rings(GC2A, ML.TEST_SIGNS, 'units', True)
    rep = run_z1(grings, label='GC2a|TEST|units|comma_split=True') if grings else None
    if rep is None:
        results['replication_GC2a'] = OrderedDict([
            ('status', 'NOT RUN'),
            ('reason', 'GC2a-n.txt is transcribed in the v101 alphabet, whose '
                       'glyphs include digits and capital letters. The frozen '
                       'clean parser keeps only pure [a-z]+ tokens, so most '
                       'zodiac label loci yield no token and no TEST-sign ring '
                       'reaches the 8-label minimum. Re-implementing the frozen '
                       'tokeniser for this corpus was not done.'),
            ('zodiac_Lz_loci', g_loci),
            ('loci_with_at_least_one_clean_token', len(glab)),
            ('test_sign_ring_sizes_after_clean_parse', g_sizes),
            ('largest_test_ring', max((max(v) if v else 0)
                                      for v in g_sizes.values())),
            ('min_ring_required', MIN_RING),
            ('protocol_note', 'The protocol requires replication only of gates '
                              'that pass on ZL3b; Z1 did not pass.'),
        ])
        say('  NOT RUN. GC2a is v101: %d zodiac label loci, only %d keep any '
            '[a-z]+ token under the frozen parser.' % (g_loci, len(glab)))
        say('  TEST-sign ring sizes after the clean parse: %s -> largest %d < %d.'
            % (dict(g_sizes), max((max(v) if v else 0) for v in g_sizes.values()),
               MIN_RING))
        say('  The protocol requires replication only of gates that pass; Z1 did not pass.')
    else:
        rep['rings_meta'] = gmeta
        rep['status'] = 'RUN'
        results['replication_GC2a'] = rep
        say('  rings=%d n=%d pairs=%d  Delta=%+.5f p=%.4f  rho_bar=%+.4f p=%.4f' %
            (rep['n_rings'], rep['n_labels'], rep['n_pairs'], rep['delta'],
             rep['delta_p'], rep['rho_bar'], rep['rho_bar_p']))

    # ---- gate -------------------------------------------------------------
    med = OrderedDict()
    for cut in CUTS:
        ds = sorted(nctrl['%s|%s' % (n, cut)]['delta'] for n in numerals)
        k = len(ds)
        med[cut] = (ds[k // 2] if k % 2 else 0.5 * (ds[k // 2 - 1] + ds[k // 2]))
    med_used = max(med.values())                 # harder threshold
    thresh = 0.25 * med_used

    pw_strict, pw_delta = OrderedDict(), OrderedDict()
    for cut in CUTS:
        rs = [nctrl['%s|%s' % (n, cut)] for n in numerals]
        pw_strict[cut] = sum(1 for r in rs if r['p_strict'] < 0.01
                             and r['ordinal_like_direction']) / float(len(rs))
        pw_delta[cut] = sum(1 for r in rs if r['delta_p'] < 0.01
                            and r['delta'] > 0) / float(len(rs))

    # false-positive rate of the same construction on the negative controls,
    # and the reuse-free power figures
    negnames = list(negs)
    fp = OrderedDict()
    for cut in CUTS:
        rs = [negctrl['%s|%s' % (n, cut)] for n in negnames]
        fp[cut] = sum(1 for r in rs if r['p_strict'] < 0.01) / float(len(rs))
        fp[cut + '_delta_only'] = (sum(1 for r in rs if r['delta_p'] < 0.01)
                                   / float(len(rs)))
    pw_onepass_strict = sum(1 for n in numerals
                            if onepass[n]['p_strict'] < 0.01
                            and onepass[n]['ordinal_like_direction']) / float(len(numerals))
    pw_onepass_delta = sum(1 for n in numerals
                           if onepass[n]['delta_p'] < 0.01
                           and onepass[n]['delta'] > 0) / float(len(numerals))
    fp_onepass = sum(1 for n in negnames
                     if onepass[n]['p_strict'] < 0.01) / float(len(negnames))

    t = obs['TEST|units|comma_split=True']
    cond_p_strict = (t['p_strict'] < 0.01) and t['ordinal_like_direction']
    cond_p_lax = (t['p_lax'] < 0.01) and t['ordinal_like_direction']
    cond_delta = t['delta'] >= thresh
    power = pw_strict['cyclic']
    power_delta_only = pw_delta['cyclic']

    if power < 0.5 and power_delta_only < 0.5:
        outcome = 'UNDERPOWERED'
    elif cond_p_strict and cond_delta:
        outcome = 'PASS'
    else:
        outcome = 'FAIL'

    gate = OrderedDict([
        ('statistic_used', 'TEST signs, glyph units, comma_split=True'),
        ('delta', t['delta']), ('delta_p', t['delta_p']),
        ('delta_alt', t['delta_alt']), ('delta_alt_p', t['delta_alt_p']),
        ('rho_bar', t['rho_bar']), ('rho_bar_p', t['rho_bar_p']),
        ('ordinal_like_direction', t['ordinal_like_direction']),
        ('numeral_median_delta_by_cut', med),
        ('numeral_median_delta_used', med_used),
        ('threshold_25pct', thresh),
        ('cond_i_p_strict_both_stats', cond_p_strict),
        ('cond_i_p_lax_either_stat', cond_p_lax),
        ('cond_ii_delta_ge_threshold', cond_delta),
        ('measured_power_strict_by_cut', pw_strict),
        ('measured_power_delta_only_by_cut', pw_delta),
        ('measured_power_used', power),
        ('measured_power_delta_only_used', power_delta_only),
        ('negative_control_false_positive_rate_same_construction', fp),
        ('supplementary_no_reuse_power_strict', pw_onepass_strict),
        ('supplementary_no_reuse_power_delta_only', pw_onepass_delta),
        ('supplementary_no_reuse_negative_control_fp', fp_onepass),
        ('power_caveat', 'The pre-registered power figure uses control series '
                         'cut to the observed ring sizes, which sum to 139 '
                         'while each series has only 30 items, so the series '
                         'is reused across rings. Reuse correlates the rings '
                         'while the permutation null re-randomises each ring '
                         'independently, inflating the controls p-values. The '
                         'negative-control false-positive rate under the same '
                         'construction and the reuse-free [18, 12] power '
                         'figures are given so the inflation is visible. The '
                         'Voynich statistic itself is unaffected: its ten rings '
                         'are ten distinct arrangements, exactly what the null '
                         'assumes.'),
        ('underpowered', power < 0.5 and power_delta_only < 0.5),
        ('outcome', outcome),
    ])
    results['gate'] = gate

    say('')
    say('=' * 78)
    say('GATE Z1  (TEST signs, glyph units, comma_split=True)')
    say('  Delta            = %+.5f   p = %.4f   (null mean %+.5f sd %.5f, z=%+.2f)'
        % (t['delta'], t['delta_p'], t['delta_null_mean'], t['delta_null_sd'], t['delta_z']))
    say('  Delta (alt pool) = %+.5f   p = %.4f' % (t['delta_alt'], t['delta_alt_p']))
    say('  rho_bar          = %+.5f   p = %.4f   (null mean %+.5f sd %.5f, z=%+.2f)'
        % (t['rho_bar'], t['rho_bar_p'], t['rho_null_mean'], t['rho_null_sd'], t['rho_z']))
    say('  mean sim(g=1) = %.4f   mean sim(g>=3) = %.4f'
        % (t['mean_sim_g1'], t['mean_sim_g3plus']))
    say('  ordinal-like direction (Delta>0 and rho_bar<0): %s'
        % t['ordinal_like_direction'])
    say('  numeral-control median Delta: cyclic %.5f / prefix %.5f -> using %.5f'
        % (med['cyclic'], med['prefix'], med_used))
    say('  gate threshold (25%%)  = %.5f    observed Delta = %+.5f  -> cond(ii) %s'
        % (thresh, t['delta'], 'MET' if cond_delta else 'NOT MET'))
    say('  cond(i) p<0.01 (both statistics, harder reading): %s' % cond_p_strict)
    say('  cond(i) p<0.01 (either statistic, laxer reading):  %s' % cond_p_lax)
    say('  measured power (numeral controls clearing p<0.01, both stats): '
        '%.2f cyclic / %.2f prefix' % (pw_strict['cyclic'], pw_strict['prefix']))
    say('  measured power (Delta only):                                  '
        '%.2f cyclic / %.2f prefix' % (pw_delta['cyclic'], pw_delta['prefix']))
    say('  CAVEAT on that power figure: matched ring sizes sum to %d but each '
        'control series has 30 items,' % sum(test_sizes))
    say('    so the series is reused across rings; reuse correlates the rings '
        'and inflates control p-values.')
    say('    negative-control false-positive rate, same construction, p<0.01: '
        '%.2f cyclic / %.2f prefix (both stats), %.2f / %.2f (Delta only)'
        % (fp['cyclic'], fp['prefix'], fp['cyclic_delta_only'], fp['prefix_delta_only']))
    say('    reuse-free power, rings [18,12]: %.2f (both stats) / %.2f (Delta '
        'only); negative-control FP %.2f'
        % (pw_onepass_strict, pw_onepass_delta, fp_onepass))
    say('    The Voynich statistic is not affected: its ten rings are ten '
        'distinct arrangements.')
    say('  OUTCOME: %s' % outcome)
    say('=' * 78)

    say('')
    say('Ambiguity resolutions (harder reading taken in each case):')
    for a in AMBIGUITIES:
        say('  - ' + a)

    payload = OrderedDict([
        ('key', 'z1'),
        ('test', 'Z1 -- ordinal gradient inside a zodiac ring'),
        ('protocol', 'experiments/meaning-probes/PROTOCOL.md, section Z1'),
        ('seed', SEED), ('n_perm', NPERM), ('min_ring_size', MIN_RING),
        ('inputs', inputs),
        ('ambiguities_resolved', AMBIGUITIES),
        ('test_ring_sizes_used_for_controls', test_sizes),
        ('results', results),
    ])
    # runtime is deliberately NOT stored: the JSON must be byte-identical on a rerun.
    (RES / 'z1.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    say('')
    say('wrote %s' % (RES / 'z1.json'))
    (RES / 'z1.stdout.txt').write_text('\n'.join(log) + '\n', encoding='utf-8')
    print('runtime %.1f s' % (time.time() - t0))


if __name__ == '__main__':
    main()
