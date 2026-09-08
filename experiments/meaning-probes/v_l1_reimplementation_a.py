#!/usr/bin/env python3
"""v_l1_reimplementation_a.py — ADVERSARIAL VERIFIER, lens = reimplementation.

Independent re-computation of L1 (label register vs running text) straight from
PROTOCOL.md + meaning_lib.py. Written WITHOUT reading t_l1.py or results/l1.json.

Protocol text being implemented (L1):
  Design    : within-page only; each label word compared only against text words
              of the SAME glyph-unit length on the SAME page.
  Statistic : for the 25 most frequent word-final glyph units (K = 25, frozen):
              within-page log-odds ratio label vs text, pooled Mantel-Haenszel.
  Null      : 10,000 permutations reassigning the label/text tag within page
              among length-matched words.
  Control   : Culpeper entry headings vs entry bodies, same statistic, same
              matching, at character level.
  Gate      : >= 3 units with |log-odds| >= 1 AND permutation p < 0.01 after
              Bonferroni over K = 25, AND pooled effect >= 25% of Culpeper's.
  Split     : L1 FIT = pages with EVEN folio number; TEST = pages with ODD
              folio number.  (PROTOCOL.md, "Held-out splits" table.)

Ambiguity readings taken (harder-to-pass reading chosen where it matters):
  A1. "the 25 most frequent word-final glyph units" — frequency is measured over
      the WHOLE label+text pool of the analysed pages (both splits pooled), so
      the unit list is one frozen list shared by FIT and TEST rather than being
      re-picked per split.  Sensitivity: the same run repeats the analysis with
      the list picked on the TEST pool only (reported as k_source='test').
  A2. "pooled effect" is summarised three ways (mean |logOR|, rms, max) over the
      K = 25 units; the ratio-to-control leg is reported under all three, and
      the STRICTEST (smallest ratio) is used for the headline verdict.
  A3. permutation p = (#{|stat_perm| >= |stat_obs|} + 1) / (nperm + 1), two-sided,
      then multiplied by 25 (Bonferroni), capped at 1.
  A4. a stratum contributes only if it holds >= 1 label word and >= 1 text word
      (an all-label or all-text stratum is uninformative under the within-stratum
      permutation null and its MH weight is zero anyway).

Stdlib only. Seed 408. Deterministic.
"""
import json, math, random, sys, os
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

REPO = "R:/Coding/LinearA/tmp/voynich_repo"
LAB = "R:/Coding/LinearA/tmp/voynich_lab"
ZL = REPO + "/data/corpora/ZL3b-n.txt"
GC = REPO + "/data/corpora/GC2a-n.txt"
CULP = LAB + "/pg49513.txt"
OUTDIR = REPO + "/experiments/meaning-probes/results"

SEED = 408
NPERM = 10000
K = 25
LOGODDS_MIN = 1.0
ALPHA = 0.01
RATIO_MIN = 0.25


# ------------------------------------------------------------------ strata ---
def build_strata(page_map, keep_page, seg):
    """page_map: page_id -> {'labels': [...], 'text': [...]}.
    seg(word) -> sequence of units.  Strata keyed (page, length).
    Returns list of stratum dicts and bookkeeping."""
    strata = []
    n_lab_used = n_txt_used = 0
    n_lab_all = n_txt_all = 0
    pages_used = set()
    for pid, d in page_map.items():
        if not keep_page(pid, d):
            continue
        n_lab_all += len(d['labels'])
        n_txt_all += len(d['text'])
        bylen = {}
        for w in d['labels']:
            u = seg(w)
            bylen.setdefault(len(u), ([], []))[0].append(u)
        for w in d['text']:
            u = seg(w)
            bylen.setdefault(len(u), ([], []))[1].append(u)
        for ln, (lab, txt) in sorted(bylen.items()):
            if not lab or not txt:
                continue
            strata.append({'key': (pid, ln), 'lab': lab, 'txt': txt})
            n_lab_used += len(lab)
            n_txt_used += len(txt)
            pages_used.add(pid)
    return {'strata': strata, 'n_lab_used': n_lab_used, 'n_txt_used': n_txt_used,
            'n_lab_all': n_lab_all, 'n_txt_all': n_txt_all,
            'n_strata': len(strata), 'n_pages': len(pages_used)}


def unit_of(u, family):
    if not u:
        return None
    return u[-1] if family == 'final' else u[0]


def compile_strata(S, keylist, family):
    """Turn strata into integer arrays for fast permutation.
    For each stratum: m1 (#label), m0 (#text), n, and the list of unit-indices
    of ALL n words (label first then text, order irrelevant), plus T_u totals."""
    kidx = {k: i for i, k in enumerate(keylist)}
    comp = []
    for s in S:
        allu = [unit_of(u, family) for u in s['lab']] + [unit_of(u, family) for u in s['txt']]
        codes = [kidx.get(x, -1) for x in allu]
        m1 = len(s['lab'])
        m0 = len(s['txt'])
        n = m1 + m0
        T = [0] * len(keylist)
        for c in codes:
            if c >= 0:
                T[c] += 1
        obs_a = [0] * len(keylist)
        for c in codes[:m1]:
            if c >= 0:
                obs_a[c] += 1
        comp.append({'codes': codes, 'm1': m1, 'm0': m0, 'n': n, 'T': T, 'obs_a': obs_a})
    return comp


def mh_from_counts(comp, a_by_stratum, ku):
    """MH pooled log odds ratio for unit index ku.
    a = label-with-unit, b = m1-a, c = T-a, d = m0-(T-a)."""
    num = den = 0.0
    for st, a_arr in zip(comp, a_by_stratum):
        a = a_arr[ku]
        m1, m0, n, T = st['m1'], st['m0'], st['n'], st['T'][ku]
        c = T - a
        b = m1 - a
        d = m0 - c
        num += a * d / n
        den += b * c / n
    return num, den


def logor(num, den):
    if num <= 0 and den <= 0:
        return None
    if num <= 0:
        return float('-inf')
    if den <= 0:
        return float('inf')
    return math.log(num / den)


def run_family(S, family, keylist, nperm=NPERM, seed=SEED):
    """Observed MH log-odds per unit + permutation two-sided p per unit."""
    comp = compile_strata(S, keylist, family)
    Kn = len(keylist)

    # observed
    obs = []
    for ku in range(Kn):
        num, den = mh_from_counts(comp, [st['obs_a'] for st in comp], ku)
        obs.append((num, den, logor(num, den)))

    # baseline for a==0 strata:  den contribution m1*T/n, num contribution 0
    base_den = [0.0] * Kn
    for st in comp:
        n, m1 = st['n'], st['m1']
        for ku in range(Kn):
            T = st['T'][ku]
            if T:
                base_den[ku] += m1 * T / n

    obs_abs = []
    for ku in range(Kn):
        v = obs[ku][2]
        obs_abs.append(abs(v) if v is not None and math.isfinite(v) else float('inf'))

    ge = [0] * Kn
    rng = random.Random(seed)
    for _ in range(nperm):
        num = [0.0] * Kn
        den = list(base_den)
        for st in comp:
            n, m1, m0 = st['n'], st['m1'], st['m0']
            codes = st['codes']
            pick = rng.sample(range(n), m1)
            cnt = {}
            for i in pick:
                c = codes[i]
                if c >= 0:
                    cnt[c] = cnt.get(c, 0) + 1
            for ku, a in cnt.items():
                T = st['T'][ku]
                cc = T - a
                b = m1 - a
                d = m0 - cc
                num[ku] += a * d / n
                den[ku] += (b * cc / n) - (m1 * T / n)
        for ku in range(Kn):
            v = logor(num[ku], den[ku])
            av = abs(v) if v is not None and math.isfinite(v) else float('inf')
            if v is None:
                av = 0.0
            if av >= obs_abs[ku]:
                ge[ku] += 1

    rows = []
    for ku, u in enumerate(keylist):
        p_raw = (ge[ku] + 1) / (nperm + 1)
        p_bonf = min(1.0, p_raw * Kn)
        lo = obs[ku][2]
        # support counts
        nl = nt = 0
        for st in comp:
            nl += st['obs_a'][ku]
            nt += st['T'][ku] - st['obs_a'][ku]
        rows.append({'unit': u, 'logodds': (None if lo is None else (lo if math.isfinite(lo) else ('inf' if lo > 0 else '-inf'))),
                     'p_raw': p_raw, 'p_bonf': p_bonf,
                     'n_label_words': nl, 'n_text_words': nt,
                     'mh_num': obs[ku][0], 'mh_den': obs[ku][1]})
    return rows


def pooled(rows):
    vals = [abs(r['logodds']) for r in rows
            if isinstance(r['logodds'], float) and math.isfinite(r['logodds'])]
    if not vals:
        return {'mean': 0.0, 'rms': 0.0, 'max': 0.0, 'n': 0}
    return {'mean': sum(vals) / len(vals),
            'rms': math.sqrt(sum(v * v for v in vals) / len(vals)),
            'max': max(vals), 'n': len(vals)}


def passers(rows):
    out = []
    for r in rows:
        lo = r['logodds']
        if not isinstance(lo, float) or not math.isfinite(lo):
            continue
        if abs(lo) >= LOGODDS_MIN and r['p_bonf'] < ALPHA:
            out.append(r)
    return out


def topK(page_map, keep_page, seg, family, k=K):
    c = Counter()
    for pid, d in page_map.items():
        if not keep_page(pid, d):
            continue
        for w in d['labels'] + d['text']:
            u = seg(w)
            x = unit_of(u, family)
            if x is not None:
                c[x] += 1
    return [u for u, _ in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:k]], dict(c.most_common(40))


# ================================================================== main ====
def main():
    out = {'verifier': 'v_l1_reimplementation_a', 'lens': 'reimplementation',
           'seed': SEED, 'nperm': NPERM, 'K': K,
           'sha256': {'ZL3b-n.txt': ML.sha256(ZL), 'GC2a-n.txt': ML.sha256(GC),
                      'pg49513.txt': ML.sha256(CULP),
                      'meaning_lib.py': ML.sha256(REPO + '/experiments/meaning-probes/meaning_lib.py'),
                      'PROTOCOL.md': ML.sha256(REPO + '/experiments/meaning-probes/PROTOCOL.md')}}

    pages = ML.parse_pages(ZL, comma_split=True)
    pmap = ML.label_text_by_page(pages)
    fnum = {pid: pages[pid]['fnum'] for pid in pmap}
    out['n_pages_with_both'] = len(pmap)
    out['pages_with_both'] = sorted(pmap.keys())
    out['fit_pages'] = sorted([p for p in pmap if fnum[p] % 2 == 0])
    out['test_pages'] = sorted([p for p in pmap if fnum[p] % 2 == 1])

    seg = lambda w: ML.bpe_apply(w)

    keep_fit = lambda pid, d: fnum[pid] % 2 == 0
    keep_test = lambda pid, d: fnum[pid] % 2 == 1
    keep_all = lambda pid, d: True

    # ---- K = 25 unit lists (reading A1: frozen over the whole pool) ----
    key_final_all, freq_final_all = topK(pmap, keep_all, seg, 'final')
    key_init_all, freq_init_all = topK(pmap, keep_all, seg, 'initial')
    key_final_test, _ = topK(pmap, keep_test, seg, 'final')
    key_init_test, _ = topK(pmap, keep_test, seg, 'initial')
    key_final_fit, _ = topK(pmap, keep_fit, seg, 'final')
    out['K_lists'] = {'final_allpool': key_final_all, 'final_testpool': key_final_test,
                      'final_fitpool': key_final_fit,
                      'initial_allpool': key_init_all, 'initial_testpool': key_init_test}
    out['freq_final_top40'] = freq_final_all
    out['freq_initial_top40'] = freq_init_all

    res = {}
    for split, keep in (('TEST', keep_test), ('FIT', keep_fit)):
        S = build_strata(pmap, keep, seg)
        res[split] = {'n': {k: v for k, v in S.items() if k != 'strata'}}
        for family, klist_name, klist in (('final', 'allpool', key_final_all),
                                          ('initial', 'allpool', key_init_all)):
            rows = run_family(S['strata'], family, klist)
            pas = passers(rows)
            res[split][family] = {'k_source': klist_name, 'rows': rows,
                                  'pooled': pooled(rows),
                                  'n_pass': len(pas),
                                  'passers': [{'unit': r['unit'], 'logodds': r['logodds'],
                                               'p_bonf': r['p_bonf'],
                                               'lab': r['n_label_words'], 'txt': r['n_text_words']}
                                              for r in pas]}
        # sensitivity: unit list picked on the TEST pool only
        rows_t = run_family(S['strata'], 'final', key_final_test)
        res[split]['final_testpoolK'] = {'k_source': 'testpool', 'n_pass': len(passers(rows_t)),
                                         'pooled': pooled(rows_t),
                                         'passers': [{'unit': r['unit'], 'logodds': r['logodds'],
                                                      'p_bonf': r['p_bonf']} for r in passers(rows_t)]}
    out['manuscript'] = res

    # ------------------------------------------------ Culpeper control ------
    ents = ML.culpeper_entries(CULP)
    cmap = OrderedDict()
    for i, head, body in ents:
        hw = ML.words_en(head)
        if hw and body:
            cmap['e%d' % i] = {'labels': hw, 'text': body}
    cseg = lambda w: list(w)
    keep_c = lambda pid, d: True
    ck_final, _ = topK(cmap, keep_c, cseg, 'final')
    ck_init, _ = topK(cmap, keep_c, cseg, 'initial')
    CS = build_strata(cmap, keep_c, cseg)
    ctl = {'n_entries': len(cmap), 'n': {k: v for k, v in CS.items() if k != 'strata'},
           'K_final': ck_final, 'K_initial': ck_init}
    for family, klist in (('final', ck_final), ('initial', ck_init)):
        rows = run_family(CS['strata'], family, klist)
        pas = passers(rows)
        ctl[family] = {'rows': rows, 'pooled': pooled(rows), 'n_pass': len(pas),
                       'passers': [{'unit': r['unit'], 'logodds': r['logodds'],
                                    'p_bonf': r['p_bonf'], 'lab': r['n_label_words'],
                                    'txt': r['n_text_words']} for r in pas]}
    out['culpeper'] = ctl

    # ------------------------------------------------------- gate verdict ---
    g = {}
    for split in ('TEST', 'FIT'):
        m = out['manuscript'][split]['final']
        c = out['culpeper']['final']['pooled']
        ratios = {k: (m['pooled'][k] / c[k] if c[k] else None) for k in ('mean', 'rms', 'max')}
        leg1 = m['n_pass'] >= 3
        strict = min(v for v in ratios.values() if v is not None)
        leg2 = strict >= RATIO_MIN
        g[split] = {'leg1_units_passing': m['n_pass'], 'leg1_pass': leg1,
                    'pooled_ratio': ratios, 'strictest_ratio': strict,
                    'leg2_pass_strict': leg2,
                    'gate_pass': bool(leg1 and leg2)}
    g['control_leg1_units_passing'] = out['culpeper']['final']['n_pass']
    out['gate'] = g

    # -------------------------------------------- FIT/TEST stability --------
    for family in ('final', 'initial'):
        a = {r['unit']: r['logodds'] for r in out['manuscript']['FIT'][family]['rows']}
        b = {r['unit']: r['logodds'] for r in out['manuscript']['TEST'][family]['rows']}
        pairs = [(a[u], b[u]) for u in a
                 if isinstance(a[u], float) and isinstance(b[u], float)
                 and math.isfinite(a[u]) and math.isfinite(b[u])]
        n = len(pairs)
        if n > 2:
            mx = sum(p[0] for p in pairs) / n
            my = sum(p[1] for p in pairs) / n
            sxy = sum((p[0] - mx) * (p[1] - my) for p in pairs)
            sxx = sum((p[0] - mx) ** 2 for p in pairs)
            syy = sum((p[1] - my) ** 2 for p in pairs)
            r = sxy / math.sqrt(sxx * syy) if sxx and syy else None
        else:
            r = None
        sign = sum(1 for p in pairs if (p[0] > 0) == (p[1] > 0))
        out.setdefault('stability', {})[family] = {'pearson_r': r, 'sign_agree': sign, 'n': n}

    with open(OUTDIR + '/v_l1_reimpl_a.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, default=str)

    # ------------------------------------------------------------ stdout ---
    L = []
    P = lambda s='': (L.append(s), print(s))
    P("=== v_l1_reimplementation_a — independent recomputation of L1 ===")
    P("sha256 ZL3b-n.txt  = " + out['sha256']['ZL3b-n.txt'])
    P("sha256 pg49513.txt = " + out['sha256']['pg49513.txt'])
    P("sha256 meaning_lib = " + out['sha256']['meaning_lib.py'])
    P("")
    P("pages with both label and text loci: %d" % out['n_pages_with_both'])
    P("split (PROTOCOL: FIT = EVEN folio, TEST = ODD folio)")
    P("  FIT  pages: %d   TEST pages: %d" % (len(out['fit_pages']), len(out['test_pages'])))
    for split in ('TEST', 'FIT'):
        n = out['manuscript'][split]['n']
        P("  %-4s label words used %d / %d  | text words used %d / %d | strata %d | pages %d"
          % (split, n['n_lab_used'], n['n_lab_all'], n['n_txt_used'], n['n_txt_all'],
             n['n_strata'], n['n_pages']))
    P("")
    P("K=25 word-final units (all-pool): " + ', '.join(key_final_all))
    P("K=25 word-final units (TEST-pool): " + ', '.join(key_final_test))
    P("K=25 word-init  units (all-pool): " + ', '.join(key_init_all))
    P("")
    for split in ('TEST', 'FIT'):
        for family in ('final', 'initial'):
            d = out['manuscript'][split][family]
            P("%s / word-%s : %d units pass (|logOR|>=1 & Bonf p<0.01); pooled mean|logOR| %.4f rms %.4f max %.4f"
              % (split, family, d['n_pass'], d['pooled']['mean'], d['pooled']['rms'], d['pooled']['max']))
            for r in d['passers']:
                P("    %-8s logOR %+8.3f  Bonf p %.4f   lab %d / txt %d"
                  % (r['unit'], r['logodds'], r['p_bonf'], r['lab'], r['txt']))
        P("  sensitivity (K picked on TEST pool), word-final: %d pass"
          % out['manuscript'][split]['final_testpoolK']['n_pass'])
    P("")
    P("Culpeper control: %d entries, %d heading words / %d body words used, %d strata"
      % (ctl['n_entries'], ctl['n']['n_lab_used'], ctl['n']['n_txt_used'], ctl['n']['n_strata']))
    for family in ('final', 'initial'):
        d = ctl[family]
        P("  control / char-%s : %d units pass; pooled mean|logOR| %.4f rms %.4f max %.4f"
          % (family, d['n_pass'], d['pooled']['mean'], d['pooled']['rms'], d['pooled']['max']))
        for r in d['passers']:
            P("    %-4s logOR %+8.3f  Bonf p %.4f  lab %d / txt %d"
              % (r['unit'], r['logodds'], r['p_bonf'], r['lab'], r['txt']))
    P("")
    for split in ('TEST', 'FIT'):
        gg = out['gate'][split]
        P("GATE L1 on %s : leg1 %d units (need >=3) -> %s ; leg2 ratios mean %.3f rms %.3f max %.3f (need >=0.25, strictest %.3f) -> %s ; GATE %s"
          % (split, gg['leg1_units_passing'], 'PASS' if gg['leg1_pass'] else 'FAIL',
             gg['pooled_ratio']['mean'], gg['pooled_ratio']['rms'], gg['pooled_ratio']['max'],
             gg['strictest_ratio'], 'PASS' if gg['leg2_pass_strict'] else 'FAIL',
             'PASS' if gg['gate_pass'] else 'FAIL'))
    P("control itself on leg1: %d units pass" % out['gate']['control_leg1_units_passing'])
    P("")
    for family in ('final', 'initial'):
        s = out['stability'][family]
        P("FIT/TEST stability word-%s : pearson r = %s, sign agreement %d/%d"
          % (family, ('%.3f' % s['pearson_r']) if s['pearson_r'] is not None else 'NA',
             s['sign_agree'], s['n']))
    with open(OUTDIR + '/v_l1_reimpl_a.stdout.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
