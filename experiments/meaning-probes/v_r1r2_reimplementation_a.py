#!/usr/bin/env python3
"""Independent reimplementation of R1 (and R2 shape) from PROTOCOL.md alone.

Written WITHOUT reading t_r1r2.py. Stdlib only. Seed 408, 10,000 draws.
"""
import json, math, random, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML

SEED = 408
NDRAW = 10000
ZL = r'R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt'

GAL3 = ['cth', 'ckh', 'cph', 'cfh']
GAL1 = ['t', 'p', 'k', 'f']


def lead_gallows(w):
    """Return the leading gallows string, or None. Benched forms tried first."""
    for g in GAL3:
        if w.startswith(g):
            return g
    for g in GAL1:
        if w.startswith(g):
            return g
    return None


def rate(seq):
    return sum(seq) / len(seq) if seq else float('nan')


def perm_two_group(a_vals, b_vals, rng, ndraw=NDRAW):
    """Label-permutation null on the difference of means. Returns
    (obs_diff, null_mean, null_sd, sd_units, p_two_sided)."""
    obs = rate(a_vals) - rate(b_vals)
    pool = list(a_vals) + list(b_vals)
    na = len(a_vals)
    n = len(pool)
    ge = 0
    diffs = []
    for _ in range(ndraw):
        rng.shuffle(pool)
        sa = sum(pool[:na])
        sb = sum(pool[na:])
        d = sa / na - sb / (n - na)
        diffs.append(d)
        if abs(d) >= abs(obs) - 1e-12:
            ge += 1
    mu = sum(diffs) / ndraw
    sd = math.sqrt(sum((d - mu) ** 2 for d in diffs) / (ndraw - 1))
    sdu = (obs - mu) / sd if sd > 0 else float('inf')
    p = (ge + 1) / (ndraw + 1)
    return obs, mu, sd, sdu, p


def two_sided_from_draws(obs, draws):
    n = len(draws)
    hi = sum(1 for d in draws if d >= obs - 1e-12)
    lo = sum(1 for d in draws if d <= obs + 1e-12)
    p = 2.0 * min((hi + 1) / (n + 1), (lo + 1) / (n + 1))
    return min(1.0, p)


def main():
    out = {'sha256': {'ZL3b-n.txt': ML.sha256(ZL)}, 'seed': SEED, 'ndraw': NDRAW}
    pages = ML.parse_pages(ZL, comma_split=True)

    # ---- strata -------------------------------------------------------
    recipes = [p for p in pages.values() if p['meta'].get('I') == 'S']
    recipes_B = [p for p in recipes if p['meta'].get('L') == 'B']
    out['n_recipes_pages'] = len(recipes)
    out['n_recipes_B_pages'] = len(recipes_B)
    out['recipes_pages'] = sorted(p['id'] for p in recipes)
    out['recipes_nonB_pages'] = sorted(p['id'] for p in recipes if p['meta'].get('L') != 'B')

    def strat(pgs, parity):
        return [p for p in pgs if p['fnum'] % 2 == parity]

    strata = {
        'TEST_recipesB_even': strat(recipes_B, 0),
        'FIT_recipesB_odd': strat(recipes_B, 1),
        'ALL_recipesB': recipes_B,
        'TEST_recipesALL_even': strat(recipes, 0),
        'FIT_recipesALL_odd': strat(recipes, 1),
    }
    out['strata_pages'] = {k: sorted(p['id'] for p in v) for k, v in strata.items()}

    # section-wide attestation vocabulary = all words in Recipes-B section
    section_words = ML.all_words(recipes_B)
    section_vocab = set(section_words)
    out['n_section_words_recipesB'] = len(section_words)
    out['n_section_types_recipesB'] = len(section_vocab)

    res = {}
    for sname, pgs in strata.items():
        ids = set(p['id'] for p in pgs)
        paras = ML.paragraphs(pages, page_ids=ids)
        openers = [d['first_word'] for d in paras if d['first_word']]
        internal = ML.non_initial_line_words(pages, page_ids=ids)
        allw = ML.all_words(pgs)

        rng = random.Random(SEED)
        gal_op = [1 if lead_gallows(w) else 0 for w in openers]
        gal_in = [1 if lead_gallows(w) else 0 for w in internal]
        gal_all = [1 if lead_gallows(w) else 0 for w in allw]

        a1 = perm_two_group(gal_op, gal_in, random.Random(SEED))
        a2 = perm_two_group(gal_op, gal_all, random.Random(SEED))

        entry = {
            'n_paragraphs': len(paras),
            'n_openers': len(openers),
            'n_internal_line_initial': len(internal),
            'n_all_words': len(allw),
            'a_rate_openers': rate(gal_op),
            'a_rate_internal': rate(gal_in),
            'a_rate_allwords': rate(gal_all),
            'a_vs_internal': {'diff': a1[0], 'null_mean': a1[1], 'null_sd': a1[2],
                              'sd_units': a1[3], 'p': a1[4]},
            'a_vs_allwords': {'diff': a2[0], 'null_mean': a2[1], 'null_sd': a2[2],
                              'sd_units': a2[3], 'p': a2[4]},
        }

        # ---- (b) ornament test -----------------------------------------
        gopeners = [w for w in openers if lead_gallows(w)]
        # control pool: gallows-initial words NOT in paragraph-initial position,
        # drawn from the same stratum's paragraph text.
        ctrl_pool = []
        for d in paras:
            for i, w in enumerate(d['words']):
                if i == 0:
                    continue
                if lead_gallows(w):
                    ctrl_pool.append(w)
        buckets = defaultdict(list)
        for w in ctrl_pool:
            buckets[(lead_gallows(w), len(w))].append(w)

        def residue(w):
            return w[len(lead_gallows(w)):]

        def attested(w):
            r = residue(w)
            return 1 if (r and r in section_vocab) else 0

        # exact matching (pre-registered)
        kept, dropped = [], []
        for w in gopeners:
            if buckets.get((lead_gallows(w), len(w))):
                kept.append(w)
            else:
                dropped.append(w)
        obs_exact = rate([attested(w) for w in kept]) if kept else float('nan')

        rng = random.Random(SEED)
        draws = []
        for _ in range(NDRAW):
            s = 0
            for w in kept:
                c = rng.choice(buckets[(lead_gallows(w), len(w))])
                s += attested(c)
            draws.append(s / len(kept))
        mu = sum(draws) / NDRAW
        sd = math.sqrt(sum((d - mu) ** 2 for d in draws) / (NDRAW - 1))
        p_exact = two_sided_from_draws(obs_exact, draws)

        # relaxed matching (supplementary): length +/-1, +/-2, then any length
        len_buckets = defaultdict(list)
        for w in ctrl_pool:
            len_buckets[lead_gallows(w)].append(w)

        def relaxed_bucket(w):
            g, L = lead_gallows(w), len(w)
            for tol in (0, 1, 2):
                cand = [c for c in len_buckets[g] if abs(len(c) - L) <= tol]
                if cand:
                    return cand
            return len_buckets[g] if len_buckets[g] else ctrl_pool

        rb = {w: relaxed_bucket(w) for w in set(gopeners)}
        obs_all = rate([attested(w) for w in gopeners])
        rng = random.Random(SEED)
        draws_r = []
        for _ in range(NDRAW):
            s = 0
            for w in gopeners:
                s += attested(rng.choice(rb[w]))
            draws_r.append(s / len(gopeners))
        mur = sum(draws_r) / NDRAW
        sdr = math.sqrt(sum((d - mur) ** 2 for d in draws_r) / (NDRAW - 1))
        p_rel = two_sided_from_draws(obs_all, draws_r)

        entry['b_exact'] = {
            'n_gallows_openers': len(gopeners), 'n_matched': len(kept),
            'n_dropped': len(dropped),
            'mean_len_kept': (sum(len(w) for w in kept) / len(kept)) if kept else None,
            'mean_len_dropped': (sum(len(w) for w in dropped) / len(dropped)) if dropped else None,
            'attest_dropped': rate([attested(w) for w in dropped]) if dropped else None,
            'obs_attest': obs_exact, 'ctrl_mean': mu, 'ctrl_sd': sd,
            'sd_units': (obs_exact - mu) / sd if sd > 0 else None, 'p': p_exact,
            'ctrl_pool_size': len(ctrl_pool),
        }
        entry['b_relaxed'] = {
            'n': len(gopeners), 'obs_attest': obs_all, 'ctrl_mean': mur,
            'ctrl_sd': sdr, 'sd_units': (obs_all - mur) / sdr if sdr > 0 else None,
            'p': p_rel,
        }

        # ---- (c) lexical opener test -----------------------------------
        c_op = Counter(openers)
        c_res = Counter(residue(w) for w in kept)
        top1_op = c_op.most_common(1)[0] if c_op else ('', 0)
        top1_res = c_res.most_common(1)[0] if c_res else ('', 0)
        # null: matched control resamples, top-1 share
        rng = random.Random(SEED)
        top1_draws = []
        for _ in range(NDRAW):
            cc = Counter()
            for w in kept:
                cc[rng.choice(buckets[(lead_gallows(w), len(w))])] += 1
            top1_draws.append(cc.most_common(1)[0][1] / len(kept))
        obs_top1_share = top1_op[1] / len(openers)
        p_top1 = (sum(1 for d in top1_draws if d >= obs_top1_share - 1e-12) + 1) / (NDRAW + 1)
        entry['c_lexical'] = {
            'top1_opener_type': top1_op[0], 'top1_opener_n': top1_op[1],
            'top1_opener_share': obs_top1_share,
            'top5_opener_share': sum(n for _, n in c_op.most_common(5)) / len(openers),
            'top1_residue_type': top1_res[0], 'top1_residue_n': top1_res[1],
            'top1_residue_share': (top1_res[1] / len(kept)) if kept else None,
            'ctrl_top1_share_mean': sum(top1_draws) / NDRAW,
            'p_one_sided_ge': p_top1,
            'entropy_openers_bits': ML.H(c_op),
            'gate_pass_lexical': bool(obs_top1_share >= 0.10 and p_top1 < 0.01),
        }
        entry['gate_a_pass_3sd'] = bool(a1[3] >= 3.0 and a2[3] >= 3.0)
        entry['gate_b_ornamental_nonrej'] = bool(p_exact > 0.05)
        res[sname] = entry

    out['R1'] = res
    return out


if __name__ == '__main__':
    o = main()
    Path('results').mkdir(exist_ok=True)
    Path('results/v_r1r2_reimpl_a.json').write_text(json.dumps(o, indent=1), encoding='utf-8')
    print(json.dumps(o, indent=1))
