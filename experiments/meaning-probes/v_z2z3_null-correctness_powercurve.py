#!/usr/bin/env python3
"""Adversarial check #3: is 'measured power = 1.00' power AT THE OBSERVED
EFFECT SIZE, or only against a maximally-easy alternative?  Degradation sweep,
conv C / glyph-unit, TEST slot structure."""
import io, math, random, re, statistics, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import meaning_lib as M

ZL3B = r"R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt"
VULG = r"R:/Coding/LinearA/tmp/voynich_lab/bibles/Latin.xml"
SEED, NPERM = 408, 2000

pages = M.parse_pages(ZL3B)
labels = M.zodiac_labels(pages)

t = re.sub(r'<[^>]*>', ' ', io.open(VULG, encoding='utf-8', errors='replace').read())
pool = sorted({w for w in M.letters_only(M.words_en(t)) if 3 <= len(w) <= 12})
rng0 = random.Random(SEED)
if len(pool) > 4000:
    pool = sorted(rng0.sample(pool, 4000))


def slot_C(r):
    return None if r['clock_min'] is None else int(math.floor(r['clock_min'] / 30.0 + 0.5)) % 24


groups, slots = [], []
p = 0
for sg in M.TEST_SIGNS:
    grp = []
    for r in [x for x in labels if x['sign'] == sg]:
        s = slot_C(r)
        if s is None:
            continue
        slots.append(s)
        grp.append(p)
        p += 1
    groups.append(grp)
rank = {s: i for i, s in enumerate(sorted(set(slots)))}

same, allc = [], []
for gi in range(len(groups)):
    for gj in range(gi + 1, len(groups)):
        for a in groups[gi]:
            for b in groups[gj]:
                allc.append((a, b))
                if slots[a] == slots[b]:
                    same.append((a, b))


def evaluate(seqs, seed=SEED):
    n = len(seqs)
    S = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            v = M.lcs_sim(seqs[i], seqs[j])
            S[i][j] = S[j][i] = v
    tot = sum(S[a][b] for a, b in allc)

    def eff(asg):
        s = sum(S[asg[a]][asg[b]] for a, b in same)
        return s / len(same) - (tot - s) / (len(allc) - len(same))
    obs = eff(list(range(n)))
    rng = random.Random(seed)
    ge = 0
    for _ in range(NPERM):
        asg = list(range(n))
        for g in groups:
            v = [asg[q] for q in g]
            rng.shuffle(v)
            for q, x in zip(g, v):
                asg[q] = x
        if abs(eff(asg)) >= abs(obs) - 1e-15:
            ge += 1
    return obs, (1 + ge) / (NPERM + 1.0)


series = M.numeral_controls()['English']
print('conv C / glyph-unit / TEST slot structure; %d perms' % NPERM)
print('observed Voynich effect = +0.016007 ; 25%% gate bar = +0.17267\n')
print('%-10s %-10s %-10s %s' % ('degrade', 'effect', 'p2', 'clears 25% bar?'))
for deg in (0.0, 0.30, 0.50, 0.70, 0.80, 0.90, 0.95, 0.98):
    words = [series[rank[s] % len(series)] for s in slots]
    if deg > 0:
        r = random.Random(SEED + 1)
        idx = r.sample(range(len(words)), int(round(deg * len(words))))
        for i in idx:
            words[i] = pool[r.randrange(len(pool))]
    e, pv = evaluate([M.bpe_apply(w) for w in words])
    print('%-10.2f %+-10.5f %-10.4f %s' % (deg, e, pv, 'yes' if e >= 0.17267 else 'NO'))
