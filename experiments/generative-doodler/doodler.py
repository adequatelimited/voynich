#!/usr/bin/env python3
"""Generative-mechanism comparison for the Voynich corpus ("the doodler test").

Question: can a content-free generative process (no lexicon, no meaning) reproduce
the quantitative fingerprint of the Voynich text?

Models:
  M0 random-chars   : null baseline, empirical word lengths, uniform letters
  M1 syllable-table : Rugg-style grille analogue; words built from a small fixed
                      syllable table with biased cell probabilities
  M2 self-citation  : Schinner-style; each word is either invented by a fixed
                      char-bigram "habit" generator or copied from a recent word
                      with a small mutation. No content anywhere.

Corpus: data/corpora/ZL3b-n.txt (repo-pinned bytes), IVTFF comments stripped,
same cleaning rules as the Artheon lab clean corpus (documented in README there).

Usage: python doodler.py --corpus ../../data/corpora/ZL3b-n.txt --out results/
Stdlib only. Deterministic under --seed.
"""
import argparse, json, math, random, re, sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------- corpus ----

def load_corpus(path):
    """Parse IVTFF transliteration -> list of (locus, [words])."""
    loci = []
    for line in open(path, encoding='utf-8', errors='replace'):
        line = line.rstrip('\n')
        if line.startswith('#') or not line.strip():
            continue
        m = re.match(r'<([^>]+)>\s*(.*)$', line)
        if not m:
            continue
        locus, text = m.groups()
        if text.strip().startswith('<!'):      # page property line
            continue
        text = re.sub(r'<![^>]*>', '', text)  # inline editorial comments
        text = re.sub(r'\{[^}]*\}', '', text) # transcription comments
        words = []
        for w in re.split(r'[.\s]+', text):
            w = re.sub(r'[@,;!?\'"<>]', '', w)
            w = re.sub(r'\d', '', w)          # extended-glyph codes -> drop digits residue
            if w:
                words.append(w)
        if words:
            loci.append((locus, words))
    return loci

# ---------------------------------------------------------------- metrics ---

def char_stats(words):
    text = ' '.join(words)
    n = len(text)
    uni = Counter(text)
    h1 = -sum(c / n * math.log2(c / n) for c in uni.values())
    bi = Counter(text[i:i+2] for i in range(len(text) - 1))
    nb = sum(bi.values())
    h2 = -sum(c / nb * math.log2(c / nb) for c in bi.values())
    return h1, h2 - h1

def zipf_slope(words):
    c = Counter(words)
    freqs = sorted(c.values(), reverse=True)
    xs, ys = [], []
    for r, f in enumerate(freqs, 1):
        if 10 <= r <= 1000 and f > 0:
            xs.append(math.log10(r)); ys.append(math.log10(f))
    if len(xs) < 10:
        return None
    mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
    num = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    den = sum((x-mx)**2 for x in xs)
    return num/den  # ideal Zipf ~ -1.0

def metrics(loci):
    words = [w for _, ws in loci for w in ws]
    n = len(words)
    types = len(set(words))
    lens = [len(w) for w in words]
    first_h = -sum(c/n * math.log2(c/n) for c in Counter(w[0] for w in words).values())
    last_h  = -sum(c/n * math.log2(c/n) for c in Counter(w[-1] for w in words).values())
    h1, h2c = char_stats(words)
    repeats = sum(1 for i in range(1, n) if words[i] == words[i-1]) / max(n-1, 1)
    # vocabulary growth: types at half the tokens
    half = set(words[:n//2])
    line_initials = Counter(ws[0] for _, ws in loci)
    top_line_initial = line_initials.most_common(1)[0][1] / len(loci)
    return {
        'tokens': n, 'types': types, 'ttr': round(types/n, 4),
        'H1': round(h1, 3), 'H2_given_1': round(h2c, 3),
        'zipf_slope': round(zipf_slope(words), 3) if zipf_slope(words) else None,
        'heaps_half': round(len(half)/types, 3),
        'word_len_mean': round(sum(lens)/len(lens), 2),
        'word_len_std': round(math.sqrt(sum((l-sum(lens)/len(lens))**2 for l in lens)/len(lens)), 2),
        'first_char_H': round(first_h, 3), 'last_char_H': round(last_h, 3),
        'immediate_repeat_rate': round(repeats, 4),
        'top_line_initial_share': round(top_line_initial, 4),
    }

# ---------------------------------------------------------------- models ----

def gen_m0(rng, n_tokens, alphabet, len_dist):
    return [[ ''.join(rng.choice(alphabet) for _ in range(rng.choice(len_dist))) ]
            for _ in range(n_tokens)]

SYL_ONSET  = ['q','k','t','p','f','s','sh','ch','d','l','r','m','n','y','g','b']
SYL_NUCL   = ['a','e','i','o','u','y','ai','ee','ey']
SYL_CODA   = ['l','r','n','m','s','dy','y','', '', '']

def gen_m1(rng, n_tokens, len_dist):
    # grille bias: a few cells dominate (Zipf-ish table usage)
    w_on  = [1/(i+1) for i in range(len(SYL_ONSET))]
    w_nu  = [1/(i+1) for i in range(len(SYL_NUCL))]
    w_co  = [1/(i+1) for i in range(len(SYL_CODA))]
    out = []
    for _ in range(n_tokens):
        target = max(1, rng.choice(len_dist))
        w = ''
        while len(w) < target:
            w += rng.choices(SYL_ONSET, w_on)[0] + rng.choices(SYL_NUCL, w_nu)[0] + rng.choices(SYL_CODA, w_co)[0]
        out.append([w[:target+2]])
    return out

def gen_m2(rng, n_tokens, corpus_words, p_new, recency_exp, p_verbatim):
    """Schinner-style self-citation + Simon preferential reuse. Habit generator =
    char bigrams of corpus (the 'script habits' a doodler would have; no meanings)."""
    # habit model: first-order char chain from corpus words
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
        if op < 0.55 and len(w) > 2:      # context-consistent substitution
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
        if op < 0.70:                      # insert a bigram-consistent char
            i = rng.randrange(len(w)+1)
            opts = trans.get(w[i-1]) if i > 0 else starts
            cands = [(c, n) for c, n in opts.items() if c != ' '] if opts else []
            if cands:
                chars, counts = zip(*cands)
                return w[:i] + rng.choices(chars, counts)[0] + w[i:]
            return w
        if op < 0.82 and len(w) > 3:       # delete
            i = rng.randrange(len(w))
            return w[:i] + w[i+1:]
        # affix swap with another recent word, cuts near edges (word-grammar habits)
        if pool:
            other = pool[rng.randrange(len(pool))]
            if len(w) > 2 and len(other) > 2:
                cut1 = min(len(w)-1, 1 + rng.choices((0,1,2,3), (4,5,3,1))[0])
                cut2 = min(len(other)-1, 1 + rng.choices((0,1,2,3), (4,5,3,1))[0])
                return (w[:cut1] + other[cut2:]) if rng.random() < 0.5 else (other[:cut2] + w[cut1:])
        return w

    words, pool = [], []                   # pool = recent history
    counts = Counter()                     # global type counts (preferential reuse)
    types_seen = []
    loci = []
    for i in range(n_tokens):
        r = rng.random()
        if pool and r < p_verbatim:
            # Simon-style preferential verbatim reuse: pick proportional to count
            tot = sum(counts.values())
            x = rng.randrange(tot)
            acc = 0
            w = words[-1]
            for t in types_seen:
                acc += counts[t]
                if acc > x:
                    w = t
                    break
        elif pool and r < p_verbatim + (1 - p_new):
            k = min(len(pool)-1, int(rng.expovariate(recency_exp/100.0)))
            w = mutate(pool[-1-k])                       # mutate a recent word
        else:
            w = habit_word()                             # invent from habits
        words.append(w); pool.append(w)
        if w not in counts:
            types_seen.append(w)
        counts[w] += 1
        if len(pool) > 400:
            pool.pop(0)
        loci.append([w])
    return loci

# ------------------------------------------------------------------ run -----

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--seed', type=int, default=1904)
    args = ap.parse_args()

    loci = load_corpus(args.corpus)
    corpus_words = [w for _, ws in loci for w in ws]
    n_tokens = len(corpus_words)
    len_dist = [len(w) for w in corpus_words]
    alphabet = sorted(set(''.join(corpus_words)))
    real = metrics(loci)

    results = {'corpus_source': str(args.corpus), 'seed': args.seed,
               'real': real, 'models': {}}

    rng = random.Random(args.seed)
    m0 = [[w] for ws in gen_m0(random.Random(args.seed), n_tokens, alphabet, len_dist) for w in ws]
    results['models']['M0_random'] = metrics([(f'm{i}', ws) for i, ws in enumerate(m0)])

    m1 = gen_m1(random.Random(args.seed), n_tokens, len_dist)
    results['models']['M1_syllable_table'] = metrics([(f'm{i}', ws) for i, ws in enumerate(m1)])

    grid = []
    for p_new in (0.05, 0.1, 0.2):
        for rec in (0.5, 1.0, 2.0):
            for pv in (0.4, 0.6, 0.75):
                grid.append((p_new, rec, pv))
    best = None
    for p_new, rec, pv in grid:
        m2 = gen_m2(random.Random(args.seed), n_tokens, corpus_words, p_new, rec, pv)
        mm = metrics([(f'm{i}', ws) for i, ws in enumerate(m2)])
        # composite distance on the headline stats
        keys = ['ttr', 'H1', 'H2_given_1', 'zipf_slope', 'word_len_mean',
                'first_char_H', 'last_char_H', 'immediate_repeat_rate', 'heaps_half']
        dist = 0.0
        for k in keys:
            if real[k] is None or mm[k] is None: continue
            scale = abs(real[k]) if real[k] else 1.0
            dist += ((real[k]-mm[k])/scale) ** 2
        dist = math.sqrt(dist)
        tag = f'pnew={p_new},rec={rec},verbatim={pv}'
        results['models'][f'M2_selfcite[{tag}]'] = mm | {'composite_distance': round(dist, 4)}
        if best is None or dist < best[0]:
            best = (dist, tag)
    results['best_m2'] = best[1]

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out/'results.json').write_text(json.dumps(results, indent=1))
    print(json.dumps({'real': real, 'best_m2': best[1],
                      'best_m2_metrics': results['models'][f'M2_selfcite[{best[1]}]']}, indent=1))

if __name__ == '__main__':
    main()
