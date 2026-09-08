#!/usr/bin/env python3
"""t_l1.py -- L1: label register vs running text (pre-registered, PROTOCOL.md).

Within-page only. Words matched on glyph-unit LENGTH. For the K=25 most frequent
word-final glyph units (frozen, computed over the whole manuscript at the level
being tested): within-page log-odds ratio label vs text, pooled Mantel-Haenszel
style across (page x length) strata, with a permutation null that reassigns the
label/text tag within each (page, length) stratum.

Also run for word-INITIAL units, reported as a separate Bonferroni family.

FIT = even folio number.  TEST = odd folio number.  Gate is read off TEST.

Positive control: Culpeper's Complete Herbal, entry HEADINGS vs entry BODIES,
character level, same statistic, same length matching.

Stdlib only. Seed 408. 10,000 permutations. Deterministic.
"""
import io, json, math, os, random, re, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

# ------------------------------------------------------------------ config --
SEED = ML.SEED                # 408
NPERM = int(os.environ.get('L1_NPERM', '10000'))   # 10,000 unless smoke-testing
K = 25                        # frozen family size
BONF = 0.01 / K               # per-test alpha after Bonferroni over K=25
LOGODDS_MIN = 1.0             # |log-odds| threshold in the gate
RATIO_MIN = 0.25              # pooled effect >= 25% of Culpeper control

REPO = 'R:/Coding/LinearA/tmp/voynich_repo'
LAB = 'R:/Coding/LinearA/tmp/voynich_lab'
ZL = REPO + '/data/corpora/ZL3b-n.txt'
GC = REPO + '/data/corpora/GC2a-n.txt'
CULP = LAB + '/pg49513.txt'
OUTDIR = REPO + '/experiments/meaning-probes/results'

LOG = []


def say(s=''):
    print(s)
    LOG.append(str(s))


# ============================================================== statistics ==
# Mantel-Haenszel pooled odds ratio over strata i, each a 2x2 table
#
#                    has unit u      not
#   label word          a_i          b_i        (m1_i = a_i + b_i)
#   text  word          c_i          d_i        (m0_i = c_i + d_i)
#                    t_iu                        n_i
#
#   OR_MH = sum_i a_i d_i / n_i  /  sum_i b_i c_i / n_i
#
# PRIMARY estimator is the MH log-OR with a MARGINAL continuity correction:
# one pseudo-observation of "has unit u" and one of "has not", each split
# between the label row and the text row in proportion to that stratum's row
# sizes (kappa=1; add kappa*m1/n to both label cells and kappa*m0/n to both
# text cells).  This is exactly unbiased at the null table (OR = 1 when the
# table is at its expectation), unlike a flat Haldane-Anscombe +0.5, which on
# strata as unbalanced as these (2 heading words vs 60 body words) inflates
# every odds ratio upward by 1-2 log units.  It keeps every estimate finite for
# the observed data and for every permutation draw, and it shrinks slightly
# toward zero, so the |log-odds| >= 1 leg of the gate is if anything harder.
# The fully uncorrected MH log-OR is computed alongside and reported.
KAPPA = 1.0


class Family(object):
    """One (corpus slice, position) family: strata + the frozen K units."""

    def __init__(self, name, units, strata_raw):
        # strata_raw: list of (n, m1, pool)  where pool is a list of length n
        # holding the unit index (0..K-1) of each word, or -1 for 'other'.
        self.name = name
        self.units = units                # list of K unit strings
        self.K = len(units)
        self.strata = []                  # (n, m1, pool, coef) coef: u -> tuple
        self.CR = [0.0] * self.K          # corrected numerator constant
        self.CS = [0.0] * self.K          # corrected denominator constant
        self.CSu = [0.0] * self.K         # uncorrected denominator constant
        self.nstrata_u = [0] * self.K     # informative strata per unit
        self.nlab_u = [0] * self.K        # label words carrying the unit
        self.ntxt_u = [0] * self.K        # text words carrying the unit
        self.n_label_words = 0
        self.n_text_words = 0
        for (n, m1, pool) in strata_raw:
            if m1 <= 0 or m1 >= n:
                continue                  # no contrast inside this stratum
            self.n_label_words += m1
            self.n_text_words += n - m1
            tc = Counter(u for u in pool if u >= 0)
            m0 = n - m1
            inv2 = 1.0 / (n + 2.0 * KAPPA)      # 1 / N'
            inv = 1.0 / n
            p1 = KAPPA * m1 / float(n)          # added to both label cells
            p0 = KAPPA * m0 / float(n)          # added to both text cells
            coef = {}
            for u in range(self.K):
                t = tc.get(u, 0)
                if t == 0 or t == n:
                    # Uninformative stratum for this unit: under the plain MH
                    # estimator it contributes exactly 0 to both numerator and
                    # denominator (a_i*d_i = b_i*c_i = 0 identically). The
                    # continuity correction is therefore applied only to
                    # informative strata, so that it regularises small counts
                    # instead of piling OR=1 pseudo-mass in from strata that
                    # carry no information about unit u at all.
                    continue
                # constants (the A_i = 0 part of each stratum's contribution)
                self.CR[u] += p1 * (m0 - t + p0) * inv2
                self.CS[u] += (m1 + p1) * (t + p0) * inv2
                self.CSu[u] += m1 * t * inv
                self.nstrata_u[u] += 1
                alab = sum(1 for x in pool[:m1] if x == u)
                self.nlab_u[u] += alab
                self.ntxt_u[u] += t - alab
                coef[u] = (inv2,
                           (m0 - t + p0 + p1) * inv2,
                           (m1 + p1 + t + p0) * inv2,
                           inv,
                           (m0 - t) * inv,
                           (t + m1) * inv,
                           t, p1, p0)
            self.strata.append((n, m1, pool, coef))

    # ---- accumulate the four running sums from a vector of a_i counts ----
    def _accumulate(self, draws):
        """draws: iterable of (coef, counts_dict). Returns (R,S,Ru,Su)."""
        Kk = self.K
        R = [0.0] * Kk
        S = [0.0] * Kk
        Ru = [0.0] * Kk
        Su = [0.0] * Kk
        for coef, cnt in draws:
            for u, A in cnt.items():
                if u < 0:
                    continue
                c = coef.get(u)
                if c is None:               # t_iu == n: no contrast, skip
                    continue
                AA = float(A * A)
                Af = float(A)
                R[u] += AA * c[0] + Af * c[1]
                S[u] += AA * c[0] - Af * c[2]
                Ru[u] += Af * c[4] + AA * c[3]
                Su[u] += AA * c[3] - Af * c[5]
        return R, S, Ru, Su

    def logors_from(self, R, S, Ru, Su):
        cor, unc = [], []
        for u in range(self.K):
            num = self.CR[u] + R[u]
            den = self.CS[u] + S[u]
            cor.append(math.log(num / den) if (num > 0 and den > 0) else 0.0)
            nu = Ru[u]
            du = self.CSu[u] + Su[u]
            if nu > 1e-12 and du > 1e-12:
                unc.append(math.log(nu / du))
            elif nu <= 1e-12 and du > 1e-12:
                unc.append(float('-inf'))
            elif du <= 1e-12 and nu > 1e-12:
                unc.append(float('inf'))
            else:
                unc.append(0.0)
        return cor, unc

    def observed(self):
        # observed: the first m1 entries of each pool are that stratum's label words
        counts = [Counter(pool[:m1]) for (n, m1, pool, coef) in self.strata]
        draws = [(st[3], c) for st, c in zip(self.strata, counts)]
        R, S, Ru, Su = self._accumulate(draws)
        cor, unc = self.logors_from(R, S, Ru, Su)
        self.obs_cor, self.obs_unc = cor, unc
        self.se_cor = self._se(counts)
        self._verify(counts, cor, unc)          # decomposition vs brute force
        return cor, unc

    def _verify(self, counts, cor, unc):
        """Brute-force the same pooled log-ORs cell by cell and assert that the
        fast sparse decomposition used inside the permutation loop agrees."""
        for u in range(self.K):
            R = S = Ru = Su = 0.0
            for st, cnt in zip(self.strata, counts):
                n, m1, pool, coef = st
                if u not in coef:
                    continue                    # uninformative stratum
                t = coef[u][6]
                m0 = n - m1
                p1 = KAPPA * m1 / float(n)
                p0 = KAPPA * m0 / float(n)
                A = cnt.get(u, 0)
                N = n + 2.0 * KAPPA
                R += (A + p1) * (m0 - t + A + p0) / N
                S += (m1 - A + p1) * (t - A + p0) / N
                Ru += A * (m0 - t + A) / float(n)
                Su += (m1 - A) * (t - A) / float(n)
            if R > 0 and S > 0:
                ref = math.log(R / S)
                assert abs(ref - cor[u]) < 1e-9, (self.name, u, ref, cor[u])
            else:
                # unit has no informative stratum in this slice
                assert self.nstrata_u[u] == 0 and cor[u] == 0.0, (self.name, u)
            if Ru > 1e-12 and Su > 1e-12:
                refu = math.log(Ru / Su)
                assert abs(refu - unc[u]) < 1e-9, (self.name, u, refu, unc[u])

    def _se(self, pool_a):
        """Robins-Breslow-Greenland SE of ln(OR_MH), on the corrected tables."""
        Kk = self.K
        se = []
        for u in range(Kk):
            sPR = sPS_QR = sQS = 0.0
            R = S = 0.0
            for (st, cnt) in zip(self.strata, pool_a):
                n, m1, pool, coef = st
                if u not in coef:
                    continue                    # uninformative stratum
                t = coef[u][6]
                m0 = n - m1
                p1 = KAPPA * m1 / float(n)
                p0 = KAPPA * m0 / float(n)
                A = cnt.get(u, 0)
                a = A + p1
                b = m1 - A + p1
                c = t - A + p0
                d = m0 - t + A + p0
                N = n + 2.0 * KAPPA
                Ri = a * d / N
                Si = b * c / N
                P = (a + d) / N
                Q = (b + c) / N
                R += Ri
                S += Si
                sPR += P * Ri
                sPS_QR += P * Si + Q * Ri
                sQS += Q * Si
            if R > 0 and S > 0:
                v = sPR / (2 * R * R) + sPS_QR / (2 * R * S) + sQS / (2 * S * S)
                se.append(math.sqrt(v))
            else:
                se.append(float('nan'))
        return se

    def permute(self, nperm=NPERM, seed=SEED):
        rnd = random.Random(seed)
        Kk = self.K
        obs = [abs(x) for x in self.obs_cor]
        obsu = [abs(x) for x in self.obs_unc]
        ge = [0] * Kk
        geu = [0] * Kk
        eps = 1e-12
        strata = self.strata
        sample = rnd.sample
        for _ in range(nperm):
            draws = []
            for (n, m1, pool, coef) in strata:
                cnt = Counter(sample(pool, m1))
                draws.append((coef, cnt))
            R, S, Ru, Su = self._accumulate(draws)
            cor, unc = self.logors_from(R, S, Ru, Su)
            for u in range(Kk):
                if abs(cor[u]) >= obs[u] - eps:
                    ge[u] += 1
                if abs(unc[u]) >= obsu[u] - eps:
                    geu[u] += 1
        self.p_cor = [(g + 1.0) / (nperm + 1.0) for g in ge]
        self.p_unc = [(g + 1.0) / (nperm + 1.0) for g in geu]
        return self.p_cor

    # ------------------------------------------------------------ summary --
    def pooled_effect(self):
        return sum(abs(x) for x in self.obs_cor) / self.K

    def pooled_rms(self):
        return math.sqrt(sum(x * x for x in self.obs_cor) / self.K)

    def pooled_max(self):
        return max(abs(x) for x in self.obs_cor)

    def rows(self):
        out = []
        for u in range(self.K):
            out.append(OrderedDict([
                ('unit', self.units[u]),
                ('n_informative_strata', self.nstrata_u[u]),
                ('n_label_words_with_unit', self.nlab_u[u]),
                ('n_text_words_with_unit', self.ntxt_u[u]),
                ('log_odds', round(self.obs_cor[u], 4)),
                ('se', (None if self.se_cor[u] != self.se_cor[u]
                        else round(self.se_cor[u], 4))),
                ('log_odds_uncorrected', ('inf' if self.obs_unc[u] == float('inf')
                                          else '-inf' if self.obs_unc[u] == float('-inf')
                                          else round(self.obs_unc[u], 4))),
                ('p_perm_uncorrected', round(self.p_unc[u], 6)),
                ('p_perm', round(self.p_cor[u], 6)),
                ('p_bonferroni', round(min(1.0, self.p_cor[u] * self.K), 6)),
                ('sig_bonf_p01', bool(self.p_cor[u] * self.K < 0.01)),
                ('passes_unit_test', bool(abs(self.obs_cor[u]) >= LOGODDS_MIN
                                          and self.p_cor[u] * self.K < 0.01)),
            ]))
        out.sort(key=lambda r: r['log_odds'])
        return out

    def n_units_passing(self):
        return sum(1 for u in range(self.K)
                   if abs(self.obs_cor[u]) >= LOGODDS_MIN
                   and self.p_cor[u] * self.K < 0.01)

    def n_units_passing_uncorrected(self):
        """Same gate leg read off the UNCORRECTED MH log-OR, so the reader can
        see whether the continuity correction changes the verdict."""
        return sum(1 for u in range(self.K)
                   if abs(self.obs_unc[u]) >= LOGODDS_MIN
                   and self.p_unc[u] * self.K < 0.01)

    def n_units_bonf_sig(self):
        """Units significant after Bonferroni, ignoring the magnitude leg."""
        return sum(1 for u in range(self.K) if self.p_cor[u] * self.K < 0.01)

    def pooled_effect_uncorrected(self):
        v = [abs(x) for x in self.obs_unc if not math.isinf(x)]
        return sum(v) / len(v) if v else 0.0

    def meta(self):
        return OrderedDict([
            ('name', self.name),
            ('n_strata', len(self.strata)),
            ('n_label_words_matched', self.n_label_words),
            ('n_text_words_matched', self.n_text_words),
            ('pooled_effect_mean_abs_logodds', round(self.pooled_effect(), 4)),
            ('pooled_effect_rms', round(self.pooled_rms(), 4)),
            ('pooled_effect_max', round(self.pooled_max(), 4)),
            ('pooled_effect_mean_abs_logodds_uncorrected',
             round(self.pooled_effect_uncorrected(), 4)),
            ('n_units_bonferroni_significant', self.n_units_bonf_sig()),
            ('n_units_passing', self.n_units_passing()),
            ('n_units_passing_uncorrected_estimator',
             self.n_units_passing_uncorrected()),
        ])


# ======================================================== corpus assembly ==

def seg_glyph(w):
    return ML.bpe_apply(w)


def seg_char(w):
    return list(w)


def top_k_units(words, seg, pos, k=K):
    c = Counter()
    for w in words:
        u = seg(w)
        if not u:
            continue
        c[u[-1] if pos == 'final' else u[0]] += 1
    return [x for x, _ in c.most_common(k)], c


def build_strata(groups, units, seg, pos):
    """groups: list of (gid, label_words, text_words).
    Returns list of (n, m1, pool) with the first m1 entries of pool being the
    label words (so `observed` can read them off directly)."""
    idx = {u: i for i, u in enumerate(units)}
    out = []
    for gid, lab, txt in groups:
        by_len_lab, by_len_txt = {}, {}
        for w in lab:
            u = seg(w)
            if u:
                by_len_lab.setdefault(len(u), []).append(
                    idx.get(u[-1] if pos == 'final' else u[0], -1))
        for w in txt:
            u = seg(w)
            if u:
                by_len_txt.setdefault(len(u), []).append(
                    idx.get(u[-1] if pos == 'final' else u[0], -1))
        for L, labs in sorted(by_len_lab.items()):
            txts = by_len_txt.get(L)
            if not txts:
                continue
            pool = list(labs) + list(txts)
            out.append((len(pool), len(labs), pool))
    return out


def voynich_groups(path, comma_split, parity):
    """parity: 'even' (FIT), 'odd' (TEST), or 'all'."""
    pages = ML.parse_pages(path, comma_split=comma_split)
    lt = ML.label_text_by_page(pages)
    groups = []
    for pid, d in lt.items():
        fnum = pages[pid]['fnum']
        if parity == 'even' and fnum % 2 != 0:
            continue
        if parity == 'odd' and fnum % 2 != 1:
            continue
        groups.append((pid, d['labels'], d['text']))
    return pages, groups


def run_family(name, groups, all_words, seg, pos, nperm=NPERM):
    units, _ = top_k_units(all_words, seg, pos)
    strata = build_strata(groups, units, seg, pos)
    fam = Family(name, units, strata)
    fam.observed()
    fam.permute(nperm=nperm)
    return fam


# ============================================================== Culpeper ====

def retention(path):
    """How much of a transcription survives clean_tokens' `[a-z]+` filter.

    ZL3b is EVA (all lower-case latin). GC2a is Glen Claston's v101 alphabet,
    which uses digits and upper-case letters as glyphs; clean_tokens drops any
    token containing a digit and keeps only pure-lower-case tokens, so on GC2a
    it silently discards most of the corpus AND the surviving subset is a
    biased sample. The frozen T2 merges (ch dy ai ok ...) are EVA merges too.
    This function measures the damage so the replication can be judged."""
    kept = dropped = 0
    for raw in io.open(path, encoding='utf-8', errors='replace'):
        m = LOC_RE.match(raw.rstrip('\n'))
        if not m:
            continue
        text = m.group(1)
        text = re.sub(r'\{[^}]*\}', '', text)
        text = text.replace('<->', ' ')
        text = re.sub(r'<[^>]*>', '', text)
        text = re.sub(r'\[([^\]:]*):[^\]]*\]', r'\1', text)
        for w in re.split(r'[.\s,]+', text):
            if not w:
                continue
            if re.fullmatch(r'[a-z]+', w) and not re.search(r'[?@\d]', w):
                kept += 1
            else:
                dropped += 1
    tot = kept + dropped
    return OrderedDict([('tokens_seen', tot), ('tokens_kept', kept),
                        ('tokens_dropped', dropped),
                        ('retention', round(kept / float(tot), 4) if tot else 0.0)])


LOC_RE = re.compile(r'^<f\d+[rv]\d*\.\d+,[^>]*>\s*(.*)$')


def culpeper_groups(path):
    entries = ML.culpeper_entries(path)
    groups, allw = [], []
    for i, head, body in entries:
        hw = ML.words_en(head)
        if not hw or not body:
            continue
        groups.append(('e%d' % i, hw, body))
        allw.extend(hw)
        allw.extend(body)
    return groups, allw


# ================================================================== driver ==

def fam_block(fam):
    b = fam.meta()
    b['units'] = fam.rows()
    return b


def print_family(fam, note=''):
    m = fam.meta()
    say('--- %s %s' % (fam.name, note))
    say('    strata=%d  label words matched=%d  text words matched=%d'
        % (m['n_strata'], m['n_label_words_matched'], m['n_text_words_matched']))
    say('    pooled mean|log-odds|=%.4f  rms=%.4f  max=%.4f'
        % (m['pooled_effect_mean_abs_logodds'], m['pooled_effect_rms'],
           m['pooled_effect_max']))
    say('    units Bonferroni-significant=%d ; units passing gate leg 1 '
        '(|lo|>=1 AND bonf p<0.01)=%d ; same on uncorrected estimator=%d'
        % (m['n_units_bonferroni_significant'], m['n_units_passing'],
           m['n_units_passing_uncorrected_estimator']))
    say('    %-10s %9s %8s %10s %12s %11s %s' %
        ('unit', 'log-odds', 'SE', 'p_perm', 'p_bonf', 'lo_uncorr', 'pass'))
    for r in fam.rows():
        say('    %-10s %9.3f %8s %10.5f %12.5f %11s %s' %
            (r['unit'], r['log_odds'],
             ('%.3f' % r['se']) if r['se'] is not None else '   n/a',
             r['p_perm'], r['p_bonferroni'],
             r['log_odds_uncorrected'],
             'YES' if r['passes_unit_test'] else ''))
    say()


def main():
    res = OrderedDict()
    res['test'] = 'L1'
    res['protocol'] = 'experiments/meaning-probes/PROTOCOL.md'
    res['seed'] = SEED
    res['n_permutations'] = NPERM
    res['K'] = K
    res['bonferroni_alpha'] = BONF
    res['inputs'] = OrderedDict([
        ('ZL3b-n.txt', ML.sha256(ZL)),
        ('GC2a-n.txt', ML.sha256(GC)),
        ('pg49513.txt', ML.sha256(CULP)),
        ('meaning_lib.py', ML.sha256(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'meaning_lib.py'))),
    ])
    res['estimator'] = ('Mantel-Haenszel pooled log odds ratio over '
                        '(page x glyph-unit-length) strata, Haldane-Anscombe '
                        'corrected (0.5 added to every cell of every stratum) '
                        'so the estimate is finite for observed data and for '
                        'every permutation draw; uncorrected MH log-OR also '
                        'reported. Correction shrinks effects toward 0, i.e. it '
                        'makes the |log-odds|>=1 leg of the gate harder.')

    say('=' * 78)
    say('L1 -- label register vs running text')
    say('=' * 78)
    for k, v in res['inputs'].items():
        say('  sha256 %-16s %s' % (k, v))
    say()

    # ---------------------------------------------------- positive control --
    say('### POSITIVE CONTROL: Culpeper, entry headings vs entry bodies '
        '(character level)')
    cg, callw = culpeper_groups(CULP)
    say('    entries used: %d ; total words: %d' % (len(cg), len(callw)))
    culp_fin = run_family('culpeper_final_char', cg, callw, seg_char, 'final')
    culp_ini = run_family('culpeper_initial_char', cg, callw, seg_char, 'initial')
    print_family(culp_fin)
    print_family(culp_ini)
    res['culpeper_control'] = OrderedDict([
        ('n_entries', len(cg)),
        ('final', fam_block(culp_fin)),
        ('initial', fam_block(culp_ini)),
    ])
    culp_pooled_fin = culp_fin.pooled_effect()
    culp_pooled_ini = culp_ini.pooled_effect()

    # ------------------------------------------------------- primary: ZL3b --
    say('### PRIMARY: ZL3b-n, glyph units, comma_split=True')
    pages_all, groups_all = voynich_groups(ZL, True, 'all')
    words_all = ML.all_words(pages_all)
    say('    manuscript word tokens (all loci): %d' % len(words_all))
    say('    pages carrying both label and text loci: %d' % len(groups_all))
    n_even = sum(1 for g in groups_all if pages_all[g[0]]['fnum'] % 2 == 0)
    say('    FIT (even folio) pages: %d ; TEST (odd folio) pages: %d'
        % (n_even, len(groups_all) - n_even))
    say()

    _, groups_fit = voynich_groups(ZL, True, 'even')
    _, groups_test = voynich_groups(ZL, True, 'odd')

    fam = OrderedDict()
    for tag, grp in (('fit_even', groups_fit), ('test_odd', groups_test),
                     ('all_pages', groups_all)):
        for pos in ('final', 'initial'):
            f = run_family('ZL3b_%s_%s' % (tag, pos), grp, words_all,
                           seg_glyph, pos)
            fam[(tag, pos)] = f
            print_family(f)

    res['primary_ZL3b'] = OrderedDict()
    for (tag, pos), f in fam.items():
        res['primary_ZL3b'].setdefault(tag, OrderedDict())[pos] = fam_block(f)

    # --------------------------------------------------------- robustness --
    say('### ROBUSTNESS')
    rob = OrderedDict()

    say('-- raw EVA character level, ZL3b, comma_split=True, TEST (odd folios)')
    for pos in ('final', 'initial'):
        f = run_family('ZL3b_test_odd_rawchar_%s' % pos, groups_test,
                       words_all, seg_char, pos)
        print_family(f)
        rob.setdefault('raw_char_test_odd', OrderedDict())[pos] = fam_block(f)

    say('-- comma_split=False, ZL3b, glyph units, TEST (odd folios)')
    pages_ns, groups_test_ns = voynich_groups(ZL, False, 'odd')
    words_ns = ML.all_words(pages_ns)
    for pos in ('final', 'initial'):
        f = run_family('ZL3b_test_odd_nocomma_%s' % pos, groups_test_ns,
                       words_ns, seg_glyph, pos)
        print_family(f)
        rob.setdefault('comma_split_false_test_odd',
                       OrderedDict())[pos] = fam_block(f)
    res['robustness'] = rob

    # -------------------------------------------------------- replication --
    say('### REPLICATION: GC2a-n, glyph units, comma_split=True')
    pages_gc_all, groups_gc_all = voynich_groups(GC, True, 'all')
    words_gc = ML.all_words(pages_gc_all)
    _, groups_gc_test = voynich_groups(GC, True, 'odd')
    _, groups_gc_fit = voynich_groups(GC, True, 'even')
    say('    GC2a pages with both registers: %d (FIT %d / TEST %d)'
        % (len(groups_gc_all), len(groups_gc_fit), len(groups_gc_test)))
    ret_zl = retention(ZL)
    ret_gc = retention(GC)
    say('    token retention under clean_tokens: ZL3b %.1f%% (%d/%d) ; '
        'GC2a %.1f%% (%d/%d)'
        % (100 * ret_zl['retention'], ret_zl['tokens_kept'],
           ret_zl['tokens_seen'], 100 * ret_gc['retention'],
           ret_gc['tokens_kept'], ret_gc['tokens_seen']))
    say('    *** GC2a-n is Glen Claston v101, not EVA: its glyphs include '
        'digits and upper case. clean_tokens keeps only pure-lower-case')
    say('        tokens, and the frozen T2 merges (ch dy ai ok ...) are EVA '
        'merges with no meaning in v101. The GC2a numbers below are')
    say('        therefore computed on a small, biased residue of that '
        'transcription and DO NOT constitute a replication.')
    repl = OrderedDict()
    repl['validity'] = OrderedDict([
        ('valid_replication', False),
        ('reason', 'GC2a-n.txt is the Glen Claston v101 transcription '
                   'alphabet (digits and upper-case letters are glyphs). '
                   'meaning_lib.clean_tokens keeps only tokens matching '
                   '[a-z]+ and drops any token containing a digit, so most of '
                   'the corpus is discarded and the surviving residue is a '
                   'biased sub-sample. The frozen T2 byte-pair merges are EVA '
                   'merges and do not segment v101. The statistics below are '
                   'reported for completeness only.'),
        ('token_retention_ZL3b', ret_zl),
        ('token_retention_GC2a', ret_gc),
        ('label_words_ZL3b_all_pages', sum(len(g[1]) for g in groups_all)),
        ('label_words_GC2a_all_pages', sum(len(g[1]) for g in groups_gc_all)),
    ])
    gc_fams = {}
    for pos in ('final', 'initial'):
        f = run_family('GC2a_test_odd_%s' % pos, groups_gc_test, words_gc,
                       seg_glyph, pos)
        gc_fams[pos] = f
        print_family(f)
        repl[pos] = fam_block(f)
    res['replication_GC2a'] = repl

    # -------------------------------------------------------------- gate ---
    tf = fam[('test_odd', 'final')]
    ti = fam[('test_odd', 'initial')]
    pooled_ratio_fin = (tf.pooled_effect() / culp_pooled_fin
                        if culp_pooled_fin > 0 else 0.0)
    pooled_ratio_ini = (ti.pooled_effect() / culp_pooled_ini
                        if culp_pooled_ini > 0 else 0.0)
    ratio_rms_fin = (tf.pooled_rms() / culp_fin.pooled_rms()
                     if culp_fin.pooled_rms() > 0 else 0.0)
    ratio_max_fin = (tf.pooled_max() / culp_fin.pooled_max()
                     if culp_fin.pooled_max() > 0 else 0.0)

    leg1_fin = tf.n_units_passing() >= 3
    leg2_fin = pooled_ratio_fin >= RATIO_MIN
    gate_fin = bool(leg1_fin and leg2_fin)
    leg1_ini = ti.n_units_passing() >= 3
    leg2_ini = pooled_ratio_ini >= RATIO_MIN
    gate_ini = bool(leg1_ini and leg2_ini)

    # measured power of the procedure: how many units the control itself
    # detects at the same thresholds.
    power_fin = culp_fin.n_units_passing()
    power_ini = culp_ini.n_units_passing()

    res['gate'] = OrderedDict([
        ('family_gated', 'word-final glyph units, TEST = odd folios (the '
                         'pre-registered family); word-initial units reported '
                         'as a separate family of the same size'),
        ('final_units_passing_TEST', tf.n_units_passing()),
        ('final_leg1_ge3_units', bool(leg1_fin)),
        ('voynich_pooled_effect_final_TEST', round(tf.pooled_effect(), 4)),
        ('culpeper_pooled_effect_final', round(culp_pooled_fin, 4)),
        ('pooled_ratio_final', round(pooled_ratio_fin, 4)),
        ('pooled_ratio_final_rms', round(ratio_rms_fin, 4)),
        ('pooled_ratio_final_max', round(ratio_max_fin, 4)),
        ('final_leg2_ratio_ge_025', bool(leg2_fin)),
        ('GATE_L1_final', gate_fin),
        ('initial_units_passing_TEST', ti.n_units_passing()),
        ('pooled_ratio_initial', round(pooled_ratio_ini, 4)),
        ('GATE_L1_initial_secondary', gate_ini),
        ('control_units_passing_final', power_fin),
        ('control_units_passing_initial', power_ini),
        ('control_max_abs_logodds_final', round(culp_fin.pooled_max(), 4)),
        ('control_max_abs_logodds_initial', round(culp_ini.pooled_max(), 4)),
        ('control_units_bonferroni_significant_final',
         culp_fin.n_units_bonf_sig()),
        ('measured_power_note',
         'The gate leg "|log-odds| >= 1" is calibrated against the positive '
         'control: the number of control units that themselves clear it is '
         'the measured power of that leg. %d of %d clear it on word-final '
         'characters (control max |log-odds| = %.3f), so a real name-vs-'
         'running-text contrast in English, under this within-entry, '
         'length-matched design, does %s produce the magnitude the gate asks '
         'for.' % (power_fin, K, culp_fin.pooled_max(),
                   'not' if power_fin == 0 else 'sometimes')),
        ('gate_final_uncorrected_estimator',
         bool(tf.n_units_passing_uncorrected() >= 3 and leg2_fin)),
        ('final_units_passing_TEST_uncorrected',
         tf.n_units_passing_uncorrected()),
        ('replication_units_passing_final', gc_fams['final'].n_units_passing()),
        ('replication_units_passing_initial',
         gc_fams['initial'].n_units_passing()),
        ('replication_is_valid', False),
    ])

    # FIT / TEST stability of the per-unit effects (not a gate, a diagnostic)
    def stability(a, b):
        xs, ys = a.obs_cor, b.obs_cor
        n = len(xs)
        mx = sum(xs) / n
        my = sum(ys) / n
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        dy = math.sqrt(sum((y - my) ** 2 for y in ys))
        r = num / (dx * dy) if dx > 0 and dy > 0 else 0.0
        agree = sum(1 for x, y in zip(xs, ys) if (x > 0) == (y > 0))
        return round(r, 4), agree, n

    st_f = stability(fam[('fit_even', 'final')], tf)
    st_i = stability(fam[('fit_even', 'initial')], ti)
    res['fit_test_stability'] = OrderedDict([
        ('final_pearson_r', st_f[0]), ('final_sign_agreement', '%d/%d' % st_f[1:]),
        ('initial_pearson_r', st_i[0]), ('initial_sign_agreement', '%d/%d' % st_i[1:]),
    ])

    say('=' * 78)
    say('GATE L1')
    say('=' * 78)
    say('  Positive control (Culpeper, word-final chars):')
    say('    units clearing |log-odds|>=1 and Bonferroni p<0.01 : %d / %d'
        % (power_fin, K))
    say('    units Bonferroni-significant (any magnitude)        : %d / %d'
        % (culp_fin.n_units_bonf_sig(), K))
    say('    largest |log-odds| anywhere in the control          : %.4f'
        % culp_fin.pooled_max())
    say('    pooled mean|log-odds| : %.4f' % culp_pooled_fin)
    say('    -> MEASURED POWER of the "|log-odds| >= 1" leg: %d/%d.'
        % (power_fin, K))
    say('  Voynich TEST (odd folios), word-final glyph units:')
    say('    units clearing |log-odds|>=1 and Bonferroni p<0.01 : %d  (need >=3) -> %s'
        % (tf.n_units_passing(), 'PASS' if leg1_fin else 'FAIL'))
    say('    pooled mean|log-odds| : %.4f  = %.1f%% of control (need >=25%%) -> %s'
        % (tf.pooled_effect(), 100 * pooled_ratio_fin,
           'PASS' if leg2_fin else 'FAIL'))
    say('    [alt summaries: rms ratio %.3f, max ratio %.3f]'
        % (ratio_rms_fin, ratio_max_fin))
    say('    same leg 1 on the UNCORRECTED MH estimator: %d units -> gate %s'
        % (tf.n_units_passing_uncorrected(),
           'PASS' if (tf.n_units_passing_uncorrected() >= 3 and leg2_fin)
           else 'FAIL'))
    say('  GATE L1 (word-final family, TEST) : %s'
        % ('PASS' if gate_fin else 'FAIL'))
    say('  Secondary family (word-initial glyph units, TEST): units passing %d,'
        ' pooled ratio %.3f -> %s'
        % (ti.n_units_passing(), pooled_ratio_ini,
           'PASS' if gate_ini else 'FAIL'))
    say('  FIT/TEST stability of per-unit log-odds: final r=%.3f (signs agree '
        '%d/%d) ; initial r=%.3f (signs agree %d/%d)'
        % (st_f[0], st_f[1], st_f[2], st_i[0], st_i[1], st_i[2]))
    say('  Replication on GC2a: NOT VALID (v101 alphabet vs an EVA-only '
        'parser and EVA-only merges) -- see results/l1.json '
        '"replication_GC2a.validity".')
    say()

    # candidate grammatical endings / name-side endings, TEST set
    def sides(f):
        rows = f.rows()
        key = lambda r: (r['unit'], r['log_odds'], r['p_bonferroni'],
                         r['n_label_words_with_unit'],
                         r['n_text_words_with_unit'])
        neg = [key(r) for r in rows if r['log_odds'] < 0]
        pos = [key(r) for r in rows if r['log_odds'] > 0]
        pos.sort(key=lambda x: -x[1])
        return neg, pos

    for label, f in (('word-final, TEST', tf), ('word-initial, TEST', ti)):
        neg, pos = sides(f)
        say('  %s -- text-heavy side (candidate grammatical material, '
            'log-odds < 0, most negative first):' % label)
        for u, lo, pb, nl, nt in neg[:12]:
            say('      %-8s %7.3f   bonf p=%.5f   support: %d label / %d text'
                ' words carry it' % (u, lo, pb, nl, nt))
        say('  %s -- label-heavy side (candidate name material, log-odds > 0):'
            % label)
        for u, lo, pb, nl, nt in pos[:12]:
            say('      %-8s %7.3f   bonf p=%.5f   support: %d label / %d text'
                ' words carry it' % (u, lo, pb, nl, nt))
        say()

    if not os.path.isdir(OUTDIR):
        os.makedirs(OUTDIR)
    with io.open(os.path.join(OUTDIR, 'l1.json'), 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(res, indent=2, ensure_ascii=False))
    with io.open(os.path.join(OUTDIR, 'l1.stdout.txt'), 'w',
                 encoding='utf-8') as fh:
        fh.write('\n'.join(LOG) + '\n')
    print('\nwrote %s/l1.json and %s/l1.stdout.txt' % (OUTDIR, OUTDIR))


if __name__ == '__main__':
    main()
