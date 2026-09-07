#!/usr/bin/env python3
"""The family's generators, vendored UNCHANGED for the clean re-run.

Provenance (branch:path in this repository):
  gen_m2                      research/generative-doodler-pilot:experiments/generative-doodler/doodler.py
  build_habit, gen_m3         research/entry-doodler-pilot-clean:experiments/entry-doodler/entry_doodler.py
  layer_weights, make_template_word, gen_m4
                              research/m4-template-doodler-pilot:experiments/m4-template-doodler/m4_doodler.py
  split_word, build_table, gen_m5, build_rows, gen_m5b
                              research/m5-grille-pilot:experiments/m5-grille/m5_grille.py

Only the function bodies are copied; each takes the word list it derives its habit
tables from as an explicit argument (corpus_words / table / rows), so the caller decides
whether that is the whole corpus (the pilots) or the FIT half only (this re-run).
"""
import random
from collections import Counter

# ----------------------------------------------------------------- M2 ------

def gen_m2(rng, n_tokens, corpus_words, p_new, recency_exp, p_verbatim):
    """Schinner-style self-citation + Simon preferential reuse. Habit generator =
    char bigrams of corpus (the 'script habits' a doodler would have; no meanings)."""
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
    counts = Counter()
    types_seen = []
    loci = []
    for i in range(n_tokens):
        r = rng.random()
        if pool and r < p_verbatim:
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
            w = mutate(pool[-1-k])
        else:
            w = habit_word()
        words.append(w); pool.append(w)
        if w not in counts:
            types_seen.append(w)
        counts[w] += 1
        if len(pool) > 400:
            pool.pop(0)
        loci.append([w])
    return loci

# ----------------------------------------------------------------- M3 ------

def build_habit(corpus_words):
    starts = Counter(w[0] for w in corpus_words)
    trans = {}
    for w in corpus_words:
        for a, b in zip(w, w[1:] + ' '):
            trans.setdefault(a, Counter())[b] += 1
    lens = [len(w) for w in corpus_words]
    return starts, trans, lens, sorted(starts)

def gen_m3(pages, corpus_words, seed, drift, topic_size, p_reuse, p_mut, prime, carry):
    rng = random.Random(seed)
    starts, trans, lens, alpha = build_habit(corpus_words)
    global_types_set = set()

    def habit_word():
        w = rng.choices(alpha, [starts[c] for c in alpha])[0]
        target = rng.choice(lens)
        while len(w) < target:
            opts = trans.get(w[-1])
            if not opts: break
            chars, counts = zip(*opts.items())
            c = rng.choices(chars, counts)[0]
            if c == ' ': break
            w += c
        return w or 'a'

    def mutate(w):
        if len(w) < 3: return w
        i = rng.randrange(len(w))
        opts = trans.get(w[i-1]) if i > 0 else starts
        cands = [(c, n) for c, n in opts.items() if c != ' '] if opts else []
        if cands and rng.random() < 0.6:
            chars, counts = zip(*cands)
            return w[:i] + rng.choices(chars, counts)[0] + w[i+1:]
        return w[:i] + w[i+1:]

    global_types = []
    out_pages = []
    prev_topic = []
    for fnum, pid, real_ws in pages:
        recent = global_types[-500:] if global_types else []
        topic = []
        for t in prev_topic:
            if rng.random() < carry:
                topic.append(mutate(t) if rng.random() < drift else t)
        while len(topic) < topic_size:
            if recent and rng.random() < 0.8:
                base = recent[rng.randrange(len(recent))]
                topic.append(mutate(base) if rng.random() < drift + 0.3 else base)
            else:
                topic.append(habit_word())
        prev_topic = list(topic)
        counts = Counter()
        types_seen = []
        for t in topic:
            counts[t] += prime
            types_seen.append(t)
        ws = []
        for _ in range(len(real_ws)):
            r = rng.random()
            if r < p_reuse:
                bag = list(counts.items())
                tot = sum(c for _, c in bag)
                x = rng.randrange(tot); acc = 0; w = bag[-1][0]
                for t, c in bag:
                    acc += c
                    if acc > x: w = t; break
            elif r < p_reuse + p_mut:
                w = mutate(rng.choice(types_seen))
            else:
                w = habit_word()
            ws.append(w)
            if w not in counts: types_seen.append(w)
            counts[w] += 1
        for t in types_seen:
            if t not in global_types_set:
                global_types.append(t)
                global_types_set.add(t)
        out_pages.append((fnum, pid, ws))
    return out_pages

# ----------------------------------------------------------------- M4 ------

CORE   = ['t','p','k','f','cth','cph','ckh','cfh']
MANTLE = ['ch','sh','ee']
CRUST  = ['d','l','r','s','n','x','i','m','g']
CIRCLES = ['a','o','y']

def layer_weights(corpus_words):
    cw, mw, rw, circ_end = Counter(), Counter(), Counter(), Counter()
    for w in corpus_words:
        for L, C in ((CORE, cw), (MANTLE, mw), (CRUST, rw)):
            for g in L:
                if g in w:
                    C[g] += w.count(g)
        if w and w[-1] in CIRCLES:
            circ_end[w[-1]] += 1
    return cw, mw, rw, circ_end

def make_template_word(rng, cw, mw, rw, circ_end, p_circle=0.35, p_final_y=0.40):
    def pick(C, pool):
        items = [(g, C.get(g, 1)) for g in pool]
        gs, ws = zip(*items)
        return rng.choices(gs, ws)[0]
    core = pick(cw, CORE) if rng.random() < 0.8 else ''
    if core and rng.random() < 0.35:
        core += 'e'
    m_left = pick(mw, MANTLE) if rng.random() < 0.45 else ''
    m_right = pick(mw, MANTLE) if rng.random() < 0.35 else ''
    c_left = pick(rw, CRUST) if rng.random() < 0.35 else ''
    c_right = pick(rw, CRUST) if rng.random() < 0.55 else ''
    seq = [x for x in (c_left, m_left, core, m_right, c_right) if x]
    out = ''
    for piece in seq:
        if rng.random() < p_circle:
            out += rng.choices(CIRCLES, [3, 4, 1])[0]
        out += piece
    if not out:
        out = 'o'
    if rng.random() < p_final_y:
        gs, ws = zip(*circ_end.items())
        out += rng.choices(gs, ws)[0]
    return out

def gen_m4(pages, corpus_words, seed, carry, topic_size, prime, p_reuse, p_mut):
    rng = random.Random(seed)
    cw, mw, rw, circ_end = layer_weights(corpus_words)
    def tword(): return make_template_word(rng, cw, mw, rw, circ_end)
    def mutate(w):
        u = tword()
        if len(w) > 3 and len(u) > 3:
            cut = rng.randrange(1, len(w))
            cut2 = rng.randrange(1, len(u))
            return (w[:cut] + u[cut2:]) if rng.random() < 0.5 else (u[:cut2] + w[cut:])
        return u
    global_types, global_set, out_pages, prev_topic = [], set(), [], []
    for fnum, pid, real_ws in pages:
        recent = global_types[-500:]
        topic = [mutate(t) if rng.random() < 0.3 else t
                 for t in prev_topic if rng.random() < carry]
        while len(topic) < topic_size:
            if recent and rng.random() < 0.8:
                topic.append(mutate(recent[rng.randrange(len(recent))]))
            else:
                topic.append(tword())
        prev_topic = list(topic)
        counts = Counter(topic * prime)
        types_seen = list(dict.fromkeys(topic))
        ws = []
        for _ in range(len(real_ws)):
            r = rng.random()
            if r < p_reuse:
                bag = list(counts.items())
                tot = sum(c for _, c in bag)
                x = rng.randrange(tot); acc = 0; w = bag[-1][0]
                for t, c in bag:
                    acc += c
                    if acc > x: w = t; break
            elif r < p_reuse + p_mut:
                w = mutate(rng.choice(types_seen))
            else:
                w = tword()
            ws.append(w)
            if w not in counts: types_seen.append(w)
            counts[w] += 1
        for t in types_seen:
            if t not in global_set:
                global_set.add(t); global_types.append(t)
        out_pages.append((fnum, pid, ws))
    return out_pages

# ----------------------------------------------------------------- M5 ------

CORE5   = ['cth','cph','ckh','cfh','t','p','k','f']
MANTLE5 = ['ch','sh','ee']

def split_word(w):
    for pool in (CORE5, MANTLE5):
        best = None
        for g in pool:
            i = w.find(g)
            if i >= 0 and (best is None or i < best[0]):
                best = (i, g)
        if best:
            i, g = best
            return w[:i], g, w[i+len(g):]
    if w:
        return '', w[0], w[1:]
    return '', '', ''

def build_table(corpus_words, K):
    left, core, right = Counter(), Counter(), Counter()
    for w in corpus_words:
        l, c, r = split_word(w)
        left[l] += 1; core[c] += 1; right[r] += 1
    def topk(C):
        items = C.most_common(K)
        return [g for g, _ in items], [n for _, n in items]
    return topk(left), topk(core), topk(right)

def gen_m5(pages, table, seed, carry, p_reuse, p_swap, topic_size=60, prime=2):
    rng = random.Random(seed)
    (Lg, Lw), (Cg, Cw), (Rg, Rw) = table
    def grille_word():
        return rng.choices(Lg, Lw)[0] + rng.choices(Cg, Cw)[0] + rng.choices(Rg, Rw)[0]
    def resample_fragment(w):
        third = max(1, len(w)//3)
        i = rng.randrange(0, len(w), third) if len(w) > third else 0
        frag = rng.choice((rng.choices(Lg, Lw)[0], rng.choices(Cg, Cw)[0], rng.choices(Rg, Rw)[0]))
        out = w[:i] + frag + w[i+third:]
        return out if out else w
    global_types, global_set, out_pages, prev_topic = [], set(), [], []
    for fnum, pid, real_ws in pages:
        recent = global_types[-500:]
        topic = [resample_fragment(t) if rng.random() < 0.3 else t
                 for t in prev_topic if rng.random() < carry]
        while len(topic) < topic_size:
            if recent and rng.random() < 0.8:
                topic.append(resample_fragment(recent[rng.randrange(len(recent))]))
            else:
                topic.append(grille_word())
        prev_topic = list(topic)
        counts = Counter(topic * prime)
        types_seen = list(dict.fromkeys(topic))
        ws = []
        for _ in range(len(real_ws)):
            r = rng.random()
            if r < p_reuse:
                bag = list(counts.items())
                tot = sum(c for _, c in bag)
                x = rng.randrange(tot); acc = 0; w = bag[-1][0]
                for t, c in bag:
                    acc += c
                    if acc > x: w = t; break
            elif r < p_reuse + p_swap:
                w = resample_fragment(rng.choice(types_seen))
            else:
                w = grille_word()
            ws.append(w)
            if w not in counts: types_seen.append(w)
            counts[w] += 1
        for t in types_seen:
            if t not in global_set:
                global_set.add(t); global_types.append(t)
        out_pages.append((fnum, pid, ws))
    return out_pages

def build_rows(corpus_words, K):
    rows = Counter()
    for w in corpus_words:
        rows[split_word(w)] += 1
    common = rows.most_common(K)
    return [list(t) for t, _ in common], [n for _, n in common]

def gen_m5b(pages, rows_packed, seed, carry, p_reuse, p_swap, o1, o2, topic_size=60, prime=2):
    rng = random.Random(seed)
    rows, wts = rows_packed
    L = [r[0] for r in rows]; C = [r[1] for r in rows]; R = [r[2] for r in rows]
    N = len(rows)
    def grille_word():
        r = rng.choices(range(N), wts)[0]
        return L[r] + C[(r + o1) % N] + R[(r + o2) % N]
    def resample_fragment(w):
        third = max(1, len(w)//3)
        i = rng.randrange(0, len(w), third) if len(w) > third else 0
        r = rng.choices(range(N), wts)[0]
        frag = rng.choice((L[r], C[r], R[r]))
        out = w[:i] + frag + w[i+third:]
        return out if out else w
    global_types, global_set, out_pages, prev_topic = [], set(), [], []
    for fnum, pid, real_ws in pages:
        recent = global_types[-500:]
        topic = [resample_fragment(t) if rng.random() < 0.3 else t
                 for t in prev_topic if rng.random() < carry]
        while len(topic) < topic_size:
            if recent and rng.random() < 0.8:
                topic.append(resample_fragment(recent[rng.randrange(len(recent))]))
            else:
                topic.append(grille_word())
        prev_topic = list(topic)
        counts = Counter(topic * prime)
        types_seen = list(dict.fromkeys(topic))
        ws = []
        for _ in range(len(real_ws)):
            r = rng.random()
            if r < p_reuse:
                bag = list(counts.items())
                tot = sum(c for _, c in bag)
                x = rng.randrange(tot); acc = 0; w = bag[-1][0]
                for t, c in bag:
                    acc += c
                    if acc > x: w = t; break
            elif r < p_reuse + p_swap:
                w = resample_fragment(rng.choice(types_seen))
            else:
                w = grille_word()
            ws.append(w)
            if w not in counts: types_seen.append(w)
            counts[w] += 1
        for t in types_seen:
            if t not in global_set:
                global_set.add(t); global_types.append(t)
        out_pages.append((fnum, pid, ws))
    return out_pages
