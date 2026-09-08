#!/usr/bin/env python3
"""Clean re-run of the generative-falsification pilots. Implements PROTOCOL.md exactly.

  * clean parser (critique), two uncertain-space treatments S (space) and M (merged)
  * pages split alternately into FIT / TEST halves
  * habit tables built from FIT words only; generators produce all 226 pages
  * model selection on FIT (family composite, family grids, seed 408); scoring on TEST
  * R5.1-R5.4 applied mechanically; A2' cipher grid with corrected gates (R6.1)

Usage: python clean_rerun.py --repo ../.. --lab <dir with bibles/ and pg49513.txt> --out results/
Stdlib only; deterministic.
"""
import argparse, json, math, random, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import critique_lib as AC   # verbatim copy of experiments/adversarial-critique/adversarial_critique.py (PR #10), kept here so this branch is self-contained
import family_generators as FG      # the pilots' generators, vendored unchanged

SEED = 408
SAMPLE = 35000
KEYS = ['ttr', 'H1', 'H2_given_1', 'zipf_slope', 'word_len_mean', 'last_char_H',
        'jaccard_adjacent', 'jaccard_distant', 'page_unique_share']
TOL = {'ttr': 0.02, 'H2_given_1': 0.15, 'last_char_H': 0.15, 'zipf_slope': 0.10,
       'word_len_mean': 0.3, 'jaccard_adjacent': 0.015, 'jaccard_distant': 0.015,
       'page_unique_share': 0.03, 'hapax_share_of_types': 0.03}
RESIDUE = {'H2_given_1': 'unmatched', 'last_char_H': 'unmatched', 'zipf_slope': 'unmatched',
           'jaccard_adjacent': 'matched', 'word_len_mean': 'matched'}   # the family's claim

# ------------------------------------------------------------ helpers -------

def composite(real, mm):
    d = 0.0
    for k in KEYS:
        if real.get(k) is None or mm.get(k) is None:
            continue
        scale = abs(real[k]) or 1.0
        d += ((real[k] - mm[k]) / scale) ** 2
    return round(math.sqrt(d), 4)

def matches(real, mm):
    out = {}
    for k, tol in TOL.items():
        if real.get(k) is None or mm.get(k) is None:
            out[k] = None
        else:
            out[k] = abs(real[k] - mm[k]) <= tol
    return out

def split_indices(n):
    return [i for i in range(n) if i % 2 == 0], [i for i in range(n) if i % 2 == 1]

def subset(triples, idx):
    return [triples[i] for i in idx]

def cut_into_pages(words, triples):
    out, k = [], 0
    for f, pid, ws in triples:
        out.append((f, pid, words[k:k+len(ws)])); k += len(ws)
    return out

# --------------------------------------------- M2 with exact-semantics speed-up

class Fenwick:
    def __init__(self, n):
        self.n = n; self.t = [0] * (n + 1)
    def add(self, i, v):           # 1-based
        while i <= self.n:
            self.t[i] += v; i += i & -i
    def find_first_exceeding(self, x):
        """smallest 1-based index i with prefix(i) > x (prefix sums non-decreasing)."""
        pos, rem = 0, x
        step = 1 << (self.n.bit_length())
        while step:
            nxt = pos + step
            if nxt <= self.n and self.t[nxt] <= rem:
                pos = nxt; rem -= self.t[nxt]
            step >>= 1
        return pos + 1

def gen_m2_fast(rng, n_tokens, corpus_words, p_new, recency_exp, p_verbatim):
    """Identical random draws and identical selection to FG.gen_m2; the O(types) linear
    scan of the verbatim pick is replaced by a Fenwick tree over insertion order.
    Equivalence is asserted at start-up (self_check_m2)."""
    starts = Counter(w[0] for w in corpus_words)
    trans = {}
    for w in corpus_words:
        for a, b in zip(w, w[1:] + ' '):
            trans.setdefault(a, Counter())[b] += 1
    len_choices = [len(w) for w in corpus_words]
    alpha = sorted(starts)

    def habit_word():
        w = rng.choices(alpha, [starts[c] for c in alpha])[0]
        target = rng.choice(len_choices)
        while len(w) < target:
            opts = trans.get(w[-1])
            if not opts:
                break
            chars, counts = zip(*opts.items())
            c = rng.choices(chars, counts)[0]
            if c == ' ':
                break
            w += c
        return w or 'a'

    def mutate(w):
        op = rng.random()
        if op < 0.55 and len(w) > 2:
            i = rng.randrange(len(w))
            opts = trans.get(w[i-1]) if i > 0 else starts
            if opts:
                chars, counts = zip(*opts.items())
                cands = [(c, n) for c, n in zip(chars, counts) if c != ' ']
                if cands:
                    chars, counts = zip(*cands)
                    c = rng.choices(chars, counts)[0]
                    return w[:i] + c + w[i+1:]
            return w
        if op < 0.70:
            i = rng.randrange(len(w)+1)
            opts = trans.get(w[i-1]) if i > 0 else starts
            cands = [(c, n) for c, n in opts.items() if c != ' '] if opts else []
            if cands:
                chars, counts = zip(*cands)
                return w[:i] + rng.choices(chars, counts)[0] + w[i:]
            return w
        if op < 0.82 and len(w) > 3:
            i = rng.randrange(len(w))
            return w[:i] + w[i+1:]
        if pool:
            other = pool[rng.randrange(len(pool))]
            if len(w) > 2 and len(other) > 2:
                cut1 = min(len(w)-1, 1 + rng.choices((0,1,2,3), (4,5,3,1))[0])
                cut2 = min(len(other)-1, 1 + rng.choices((0,1,2,3), (4,5,3,1))[0])
                return (w[:cut1] + other[cut2:]) if rng.random() < 0.5 else (other[:cut2] + w[cut1:])
        return w

    words, pool = [], []
    index = {}                       # type -> insertion index (1-based)
    types_seen = []
    fw = Fenwick(n_tokens + 1)
    tot = 0
    for i in range(n_tokens):
        r = rng.random()
        if pool and r < p_verbatim:
            x = rng.randrange(tot)
            w = types_seen[fw.find_first_exceeding(x) - 1]
        elif pool and r < p_verbatim + (1 - p_new):
            k = min(len(pool)-1, int(rng.expovariate(recency_exp/100.0)))
            w = mutate(pool[-1-k])
        else:
            w = habit_word()
        words.append(w); pool.append(w)
        if w not in index:
            types_seen.append(w); index[w] = len(types_seen)
        fw.add(index[w], 1); tot += 1
        if len(pool) > 400:
            pool.pop(0)
    return words

def self_check_m2(corpus_words):
    a = [w for ws in FG.gen_m2(random.Random(SEED), 3000, corpus_words, 0.1, 1.0, 0.6) for w in ws]
    b = gen_m2_fast(random.Random(SEED), 3000, corpus_words, 0.1, 1.0, 0.6)
    assert a == b, 'gen_m2_fast diverges from the vendored gen_m2'
    return True

# ------------------------------------------------------------ models --------

def model_grid(name, all_triples, fit_words):
    """Yield (tag, generated_pages) for every configuration in the family's grid."""
    n_tokens = sum(len(ws) for _, _, ws in all_triples)
    if name == 'M2':
        for p_new in (0.05, 0.1, 0.2):
            for rec in (0.5, 1.0, 2.0):
                for pv in (0.4, 0.6, 0.75):
                    words = gen_m2_fast(random.Random(SEED), n_tokens, fit_words, p_new, rec, pv)
                    yield f'pnew={p_new},rec={rec},verbatim={pv}', cut_into_pages(words, all_triples)
    elif name == 'M3':
        for carry in (0.3, 0.5, 0.7):
            for topic_size in (30, 60):
                for prime in (2, 5):
                    for p_reuse in (0.6, 0.7):
                        yield (f'carry={carry},topic={topic_size},prime={prime},reuse={p_reuse}',
                               FG.gen_m3(all_triples, fit_words, SEED, 0.3, topic_size, p_reuse, 0.1, prime, carry))
    elif name == 'M4':
        for carry in (0.2, 0.3, 0.5):
            for topic_size in (30, 60):
                for p_reuse in (0.6, 0.7):
                    yield (f'carry={carry},topic={topic_size},reuse={p_reuse}',
                           FG.gen_m4(all_triples, fit_words, SEED, carry, topic_size, 2, p_reuse, 0.1))
    elif name == 'M5':
        for K in (40, 80, 120):
            table = FG.build_table(fit_words, K)
            for carry in (0.3, 0.5):
                for p_reuse in (0.6, 0.7):
                    yield (f'K={K},carry={carry},reuse={p_reuse}',
                           FG.gen_m5(all_triples, table, SEED, carry, p_reuse, 0.1))
    elif name == 'M5b':
        for K in (1000, 3000):
            rows = FG.build_rows(fit_words, K)
            for (o1, o2) in ((0, 0), (1, 0), (0, 2), (2, 5)):
                for p_reuse in (0.6, 0.7):
                    yield (f'K={K},o=({o1},{o2}),reuse={p_reuse}',
                           FG.gen_m5b(all_triples, rows, SEED, 0.3, p_reuse, 0.1, o1, o2))

def run_treatment(label, pages, log):
    all_triples = AC.as_triples(pages)
    fit_idx, test_idx = split_indices(len(all_triples))
    fit_real = AC.full_metrics(subset(all_triples, fit_idx))
    test_real = AC.full_metrics(subset(all_triples, test_idx))
    all_real = AC.full_metrics(all_triples)
    fit_words = [w for _, _, ws in subset(all_triples, fit_idx) for w in ws]
    res = {'treatment': label, 'pages': len(all_triples), 'fit_pages': len(fit_idx), 'test_pages': len(test_idx),
           'real': {'fit': fit_real, 'test': test_real, 'all': all_real}, 'models': {}}
    for name in ('M2', 'M3', 'M4', 'M5', 'M5b'):
        t0 = time.time()
        best = None; grid = {}
        for tag, gen in model_grid(name, all_triples, fit_words):
            m_fit = AC.full_metrics(subset(gen, fit_idx))
            d_fit = composite(fit_real, m_fit)
            grid[tag] = {'fit_composite': d_fit}
            if best is None or d_fit < best[0]:
                best = (d_fit, tag, gen, m_fit)
        d_fit, tag, gen, m_fit = best
        m_test = AC.full_metrics(subset(gen, test_idx))
        m_all = AC.full_metrics(gen)
        d_test = composite(test_real, m_test)
        mt = matches(test_real, m_test)
        res['models'][name] = {
            'selected': tag, 'grid_size': len(grid), 'grid': grid,
            'fit_composite': d_fit, 'test_composite': d_test, 'all_composite': composite(all_real, m_all),
            'test_metrics': m_test, 'fit_metrics': m_fit, 'all_metrics': m_all,
            'test_matches': mt, 'test_match_count': sum(1 for v in mt.values() if v),
            'R5_3': 'OVERFIT' if d_test > 1.25 * d_fit else 'GENERALISES',
            'sample': ' '.join(gen[1][2][:10]),
            'seconds': round(time.time() - t0, 1),
        }
        log(f'[{label}] {name} best={tag} fit={d_fit} test={d_test} matches={res["models"][name]["test_match_count"]}/9 ({res["models"][name]["seconds"]}s)')
    return res

# ------------------------------------------------------------ A2' -----------

def cipher_grid(plain_words, groups, abbrev, k, seed=SEED):
    rng = random.Random(seed)
    rank = AC.letter_ranks(plain_words)
    n = len(groups)
    def enc(ch):
        i = rank[ch]
        if k == 1:
            return groups[i % n][0]
        opts = [groups[(i + 26 * j) % n] for j in range(k)]
        gs, ws = zip(*opts)
        return rng.choices(gs, ws)[0]
    out = []
    for w in plain_words:
        if abbrev:
            w = w[0] + ''.join(c for c in w[1:] if c not in 'aeiou')
        out.append(''.join(enc(c) for c in w))
    return out

def gates(ref, m):
    return {
        'ttr': abs(m['ttr'] - ref['ttr']) <= 0.03,
        'H2_given_1': m['H2_given_1'] <= ref['H2_given_1'] + 0.20,
        'last_char_H': m['last_char_H'] <= ref['last_char_H'] + 0.20,
        'word_len_mean': abs(m['word_len_mean'] - ref['word_len_mean']) <= 1.0,
        'zipf_slope': abs(m['zipf_slope'] - ref['zipf_slope']) <= 0.15,
    }

def run_ciphers(refs, fit_words_by_treatment, plaintexts, log):
    out = {'trials': [], 'hits': []}
    for label, fit_words in fit_words_by_treatment.items():
        groups = AC.build_cipher_tables(fit_words)['groups']
        ref = refs[label]
        for pname, pw in plaintexts.items():
            for abbrev in (False, True):
                for k in (1, 2, 3):
                    ct = cipher_grid(pw, groups, abbrev, k)
                    m = AC.core_metrics(ct)
                    g = gates(ref, m)
                    trial = {'treatment': label, 'plaintext': pname, 'abbrev': abbrev, 'k': k,
                             'metrics': {x: m[x] for x in ['types', 'ttr', 'hapax_share_of_types', 'H2_given_1', 'last_char_H', 'word_len_mean', 'zipf_slope']},
                             'gates': g, 'pass': all(g.values()), 'sample': ' '.join(ct[:6])}
                    out['trials'].append(trial)
                    if trial['pass']:
                        out['hits'].append(f'{label}/{pname}/abbrev={abbrev}/k={k}')
                    log(f"[A2' {label}] {pname} abbrev={abbrev} k={k} ttr={m['ttr']} H2={m['H2_given_1']} fin={m['last_char_H']} len={m['word_len_mean']} zipf={m['zipf_slope']} pass={trial['pass']}")
    out['R6_1'] = 'RESIDUE NON-DISCRIMINATING (device vs cipher)' if out['hits'] else 'NOT REPRODUCED BY 12 UNTUNED CIPHERS'
    return out

# ------------------------------------------------------------ main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True); ap.add_argument('--lab', required=True); ap.add_argument('--out', required=True)
    args = ap.parse_args()
    repo, lab, out = Path(args.repo), Path(args.lab), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    logf = open(out / 'stdout.txt', 'w', encoding='utf-8')
    def log(s):
        print(s, flush=True); logf.write(s + '\n'); logf.flush()

    corpus = repo / 'data/corpora/ZL3b-n.txt'
    R = {'protocol': 'PROTOCOL.md', 'seed': SEED, 'tolerances': TOL, 'corpus_sha256': AC.sha256(corpus), 'treatments': {}}
    pages_S = AC.clean_load(corpus, comma_split=True)
    pages_M = AC.clean_load(corpus, comma_split=False)
    self_check_m2([w for p in pages_S for w in p['words']][:20000])
    log('gen_m2_fast equivalence check passed (3000 tokens, identical output)')

    for label, pages in (('S', pages_S), ('M', pages_M)):
        R['treatments'][label] = run_treatment(label, pages, log)

    # ---- verdicts R5.1-R5.4
    V = {}
    for label in ('S', 'M'):
        T = R['treatments'][label]
        V[label] = {'R5_1_match_counts': {n: m['test_match_count'] for n, m in T['models'].items()},
                    'R5_3': {n: m['R5_3'] for n, m in T['models'].items()},
                    'R5_4_test_ranking': sorted(T['models'], key=lambda n: T['models'][n]['test_composite'])}
    S = R['treatments']['S']
    best_name = min(S['models'], key=lambda n: S['models'][n]['test_composite'])
    mt = S['models'][best_name]['test_matches']
    V['R5_2'] = {'best_model_S': best_name,
                 'residue': {k: ('MATCHED' if mt[k] else 'UNMATCHED') for k in RESIDUE},
                 'family_claim': RESIDUE}
    R['verdicts'] = V

    # ---- A2'
    refs, fitw = {}, {}
    for label, pages in (('S', pages_S), ('M', pages_M)):
        words = [w for p in pages for w in p['words']]
        refs[label] = AC.core_metrics(words[:SAMPLE])
        idx_fit, _ = split_indices(len(pages))
        fitw[label] = [w for i in idx_fit for w in pages[i]['words']]
    culp = AC.truncate_triples([(i, n, AC.letters_only(ws)) for i, n, ws in AC.culpeper_entries(lab / 'pg49513.txt')], SAMPLE)
    plaintexts = {'Latin': AC.letters_only(AC.load_bible(lab / 'bibles' / 'Latin.xml'))[:SAMPLE],
                  'Culpeper': [w for _, _, ws in culp for w in ws]}
    R['A2prime'] = {'manuscript_refs': refs} | run_ciphers(refs, fitw, plaintexts, log)
    R['verdicts']['R6_1'] = R['A2prime']['R6_1']

    (out / 'results.json').write_text(json.dumps(R, indent=1, ensure_ascii=False))
    log(json.dumps(R['verdicts'], indent=1))
    logf.close()

if __name__ == '__main__':
    main()
