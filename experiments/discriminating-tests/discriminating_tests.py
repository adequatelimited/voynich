#!/usr/bin/env python3
"""Two discriminating tests. Implements PROTOCOL.md exactly.

T1  illustration-linked vocabulary
    T1a same plant, two texts: herbal page <-> pharmaceutical row paragraph (S1/N1),
        plant label in herbal text (S2/N2)
    T1b similar plants by external plant identifications: herbal page <-> herbal page
        (S3 with label-shuffle null N3 and distance-matched null N4)
    positive control: Culpeper entries whose headwords share a token
T2  data-chosen re-segmentation (byte-pair merging) for every corpus; comparison at
    equal alphabet size and at equal merge count; association-based sensitivity

Usage: python discriminating_tests.py --repo ../.. --lab <dir with bibles/ and pg49513.txt> --out results/
Stdlib only; deterministic (seed 408).
"""
import argparse, json, math, random, re, sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import critique_lib as AC   # verbatim copy of experiments/adversarial-critique/adversarial_critique.py (PR #10), kept here so this branch is self-contained

SEED = 408
SAMPLE = 35000
N_PERM = 5000
N_MATCH = 200
MAX_MERGES = 60
TARGET_SIZES = (30, 40, 50, 60)

# ----------------------------------------------------------------- parsing --

HDR = re.compile(r'^<(f\d+[rv]\d*)>\s*<!([^>]*)>')
LOC = re.compile(r'^<(f(\d+)[rv]\d*)\.(\d+),([^>]*)>\s*(.*)$')

def load_annotated(path, comma_split=True):
    """pages: id -> {fnum, meta, loci: [(code, words)], plant_id: str|None, same_as: str|None}"""
    pages, order, cur = {}, [], None
    for line in open(path, encoding='utf-8', errors='replace'):
        line = line.rstrip('\n')
        m = HDR.match(line)
        if m:
            cur = m.group(1)
            pages[cur] = {'id': cur, 'fnum': int(re.match(r'f(\d+)', cur).group(1)),
                          'meta': dict(re.findall(r'\$([A-Z])=(\S+)', m.group(2))),
                          'loci': [], 'plant_id': None, 'same_as': None}
            order.append(cur)
            continue
        if line.startswith('# Plant ID') and cur:
            pages[cur]['plant_id'] = line[len('# Plant ID:'):].strip()
            continue
        if line.startswith('# Same plant as') and cur:
            pages[cur]['same_as'] = line[len('# Same plant as'):].strip()
            continue
        if line.startswith('#'):
            continue
        m = LOC.match(line)
        if not m:
            continue
        pid, code, text = m.group(1), m.group(4), m.group(5)
        ws = AC.clean_tokens(text, comma_split)
        pages[pid]['loci'].append((code, ws))      # keep empty loci: row structure depends on them
    return [pages[p] for p in order if any(ws for _, ws in pages[p]['loci'])]

def page_words(p, kinds=None):
    return [w for code, ws in p['loci'] for w in ws if kinds is None or code[1] in kinds]

def pharma_blocks(p):
    """Rows of a pharmaceutical page: a run of label loci followed by paragraph loci."""
    blocks, cur, seen_para = [], None, False
    for code, ws in p['loci']:
        is_label = code[1] == 'L'
        if is_label and (cur is None or seen_para):
            if cur: blocks.append(cur)
            cur = {'labels': [], 'para': []}; seen_para = False
        if cur is None:
            cur = {'labels': [], 'para': []}
        if is_label:
            cur['labels'].append((code, ws))
        else:
            cur['para'].extend(ws); seen_para = True
    if cur: blocks.append(cur)
    return blocks

# ------------------------------------------------------------- helpers ------

def jac(a, b):
    return len(a & b) / max(len(a | b), 1)

def edit1(a, b):
    if a == b: return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1: return False
    if la == lb:
        return sum(x != y for x, y in zip(a, b)) == 1
    if la > lb: a, b, la, lb = b, a, lb, la
    i = 0
    while i < la and a[i] == b[i]: i += 1
    return a[i:] == b[i+1:]

STOP = set('''unreadable illegible hard read too many list here mostly small one like but leaves leaf
with wrong flower root roots species plant tree herba indian also only along mark red top has
climbing dwarf unreadable sp cf neill holm petersen stolfi voynich zandbergen manley mrs fsg
smaller some tongue ear eye apple fern flowers mint nettle'''.split())
STOP_CULP = set('''water garden wild common great small white black yellow sweet wood field marsh
herb tree stinking lesser greater true false english italian french spanish dutch
chapter their'''.split())   # 'chapter' + roman numerals added after run 1 (deviation recorded in REPORT.md)
ROMAN = re.compile(r'^[ivxlc]+$')

def name_tokens(s, stop):
    s = re.sub(r"\([^)]*\)|\[[^\]]*\]", ' ', s or '')       # drop parentheticals / brackets
    toks = []
    for t in re.split(r'[^a-zA-Z]+', s.lower()):
        if len(t) >= 4 and t not in stop and not ROMAN.match(t):
            if len(t) > 4 and t.endswith('s'): t = t[:-1]
            toks.append(t)
    return set(toks)

def same_name(a, b):
    if a == b: return True
    n = min(len(a), len(b))
    return n >= 6 and (a.startswith(b) or b.startswith(a))

def share_name(A, B):
    return any(same_name(a, b) for a in A for b in B)

# ------------------------------------------------------------------ T1a -----

REF = re.compile(r'(f\d+[rv]\d*)(?:\[(\d+),(\d+)\])?')

def t1a(pages, log):
    byid = {p['id']: p for p in pages}
    pharma = [p for p in pages if p['meta'].get('I') == 'P']
    pharma_rows = []      # (page id, row index, block, language)
    for p in pharma:
        for r, b in enumerate(pharma_blocks(p), 1):
            if b['para']:
                pharma_rows.append((p['id'], r, b, p['meta'].get('L')))
    herbal_all = [p for p in pages if p['meta'].get('I') == 'H']
    rng = random.Random(SEED)
    pairs, s2 = [], []
    for p in pages:
        if not p['same_as']: continue
        m = REF.search(p['same_as'])
        if not m: continue
        ref, row = m.group(1), m.group(2)
        target = byid.get(ref) or byid.get(ref + '1')
        if target is None:
            log(f'[T1a] {p["id"]} -> {ref}: page not found, skipped'); continue
        blocks = pharma_blocks(target)
        if row and int(row) <= len(blocks):
            blk = blocks[int(row) - 1]; rid = f'{target["id"]}[{row}]'
        else:
            blk = {'labels': [l for b in blocks for l in b['labels']], 'para': [w for b in blocks for w in b['para']]}
            rid = target['id']
            if row: log(f'[T1a] {p["id"]} -> {ref} row {row} beyond {len(blocks)} blocks: whole page used')
        H = set(page_words(p))
        R = set(blk['para'])
        if not R:
            log(f'[T1a] {p["id"]} -> {rid}: empty paragraph, skipped'); continue
        obs = jac(H, R)
        lang = p['meta'].get('L')
        nulls = [jac(H, set(b['para'])) for pid, r, b, L in pharma_rows
                 if not (pid == target['id'] and (not row or r == int(row))) and L == lang]
        lang_note = 'same-language rows'
        if not nulls:   # no pharmaceutical rows in this herbal page's Currier language: use all rows, flagged
            nulls = [jac(H, set(b['para'])) for pid, r, b, L in pharma_rows
                     if not (pid == target['id'] and (not row or r == int(row)))]
            lang_note = f'no rows in language {lang}; all rows used'
        pct = sum(1 for x in nulls if x >= obs) / max(len(nulls), 1)
        pairs.append({'herbal': p['id'], 'herbal_language': lang, 'ref': rid, 'jaccard': round(obs, 4), 'null_mean': round(sum(nulls)/len(nulls), 4),
                      'null_n': len(nulls), 'null_note': lang_note, 'pct_null_at_or_above': round(pct, 3), 'shared': sorted(H & R)[:12], '_nulls': nulls})
        labels = [w for code, ws in blk['labels'] if code.startswith('@Lf') or code[1:3] == 'Lf' for w in ws]
        if labels:
            hit = [w for w in labels if any(edit1(w, h) for h in H)]
            others = [set(page_words(q)) for q in herbal_all if q is not p and q['meta'].get('L') == lang]
            null_rate = sum(1 for O in others if any(any(edit1(w, h) for h in O) for w in labels)) / max(len(others), 1)
            s2.append({'herbal': p['id'], 'ref': rid, 'labels': labels, 'hits': hit, 'null_hit_rate': round(null_rate, 3)})
    obs_mean = sum(x['jaccard'] for x in pairs) / len(pairs)
    perm = []
    for _ in range(N_PERM):
        perm.append(sum(rng.choice(x['_nulls']) for x in pairs) / len(pairs))
    p_val = sum(1 for v in perm if v >= obs_mean) / N_PERM
    for x in pairs: del x['_nulls']
    res = {'pairs': pairs, 'n_pairs': len(pairs), 'S1_mean_jaccard': round(obs_mean, 4),
           'N1_perm_mean': round(sum(perm)/len(perm), 4), 'N1_perm_sd': round(math.sqrt(sum((v-sum(perm)/len(perm))**2 for v in perm)/len(perm)), 4),
           'N1_p': p_val, 'mean_percentile': round(sum(x['pct_null_at_or_above'] for x in pairs)/len(pairs), 3),
           'S2_label_tests': s2, 'S2_hits': sum(1 for x in s2 if x['hits']), 'S2_n': len(s2),
           'S2_expected_hits': round(sum(x['null_hit_rate'] for x in s2), 2)}
    log(f'[T1a] pairs={len(pairs)} S1={obs_mean:.4f} null={res["N1_perm_mean"]:.4f}±{res["N1_perm_sd"]:.4f} p={p_val:.4f} | S2 hits {res["S2_hits"]}/{len(s2)} expected {res["S2_expected_hits"]}')
    return res

# ------------------------------------------------------------------ T1b -----

def similarity_test(items, rng, log, tag):
    """items: list of dict(id, fnum, lang, names:set, words:set). S3/N3/N4."""
    items = [it for it in items if it['names']]
    n = len(items)
    def sim_pairs(name_sets):
        return [(i, j) for i in range(n) for j in range(i+1, n) if share_name(name_sets[i], name_sets[j])]
    names = [it['names'] for it in items]
    pairs = sim_pairs(names)
    if not pairs:
        log(f'[{tag}] no similar pairs'); return None
    obs = sum(jac(items[i]['words'], items[j]['words']) for i, j in pairs) / len(pairs)
    # EXPLORATORY (not in PROTOCOL): size-corrected sharing = observed shared types / expected
    # under independence given both set sizes and the pooled vocabulary V.
    V = len(set().union(*[it['words'] for it in items]))
    def lift(a, b):
        A, B = items[a]['words'], items[b]['words']
        return len(A & B) * V / max(len(A) * len(B), 1)
    obs_lift = sum(lift(i, j) for i, j in pairs) / len(pairs)
    sizes = [len(it['words']) for it in items]
    from collections import Counter as _C
    cluster = _C()
    for i, j in pairs:
        for a in names[i]:
            for b in names[j]:
                if same_name(a, b): cluster[a if len(a) <= len(b) else b] += 1
    lift_perm, lift_perm4 = [], []
    # N3: shuffle name sets within language
    perm = []
    by_lang = defaultdict(list)
    for idx, it in enumerate(items): by_lang[it['lang']].append(idx)
    for _ in range(N_PERM):
        shuffled = list(names)
        for L, idxs in by_lang.items():
            vals = [names[i] for i in idxs]; rng.shuffle(vals)
            for i, v in zip(idxs, vals): shuffled[i] = v
        pp = sim_pairs(shuffled)
        if pp:
            perm.append(sum(jac(items[i]['words'], items[j]['words']) for i, j in pp) / len(pp))
            lift_perm.append(sum(lift(i, j) for i, j in pp) / len(pp))
    pm = sum(perm)/len(perm); psd = math.sqrt(sum((v-pm)**2 for v in perm)/len(perm))
    p3 = sum(1 for v in perm if v >= obs) / len(perm)
    # N4: distance-matched
    matched_means, per_pair = [], []
    cand_cache = {}
    for i, j in pairs:
        d = abs(items[i]['fnum'] - items[j]['fnum'])
        cands = [k for k in range(n) if k != i and k != j and items[k]['lang'] == items[i]['lang']
                 and abs(abs(items[k]['fnum'] - items[i]['fnum']) - d) <= 3 and not share_name(names[i], names[k])]
        cand_cache[(i, j)] = cands
        if cands:
            per_pair.append(sum(jac(items[i]['words'], items[k]['words']) for k in cands) / len(cands))
    perm4 = []
    for _ in range(N_PERM):
        vals, lvals = [], []
        for i, j in pairs:
            c = cand_cache[(i, j)]
            if c:
                k = rng.choice(c)
                vals.append(jac(items[i]['words'], items[k]['words'])); lvals.append(lift(i, k))
        if vals: perm4.append(sum(vals)/len(vals)); lift_perm4.append(sum(lvals)/len(lvals))
    obs_lift4 = sum(lift(i, j) for i, j in pairs if cand_cache[(i, j)]) / max(1, sum(1 for pr in pairs if cand_cache[pr]))
    lm = sum(lift_perm)/len(lift_perm); lsd = math.sqrt(sum((v-lm)**2 for v in lift_perm)/len(lift_perm))
    lm4 = sum(lift_perm4)/len(lift_perm4); lsd4 = math.sqrt(sum((v-lm4)**2 for v in lift_perm4)/len(lift_perm4))
    exploratory = {'vocab_V': V, 'set_size_mean': round(sum(sizes)/len(sizes), 1), 'set_size_min_max': (min(sizes), max(sizes)),
                   'lift_observed': round(obs_lift, 3), 'lift_N3_mean': round(lm, 3), 'lift_N3_sd': round(lsd, 3),
                   'lift_N3_p': round(sum(1 for v in lift_perm if v >= obs_lift)/len(lift_perm), 4),
                   'lift_observed_matched_subset': round(obs_lift4, 3), 'lift_N4_mean': round(lm4, 3), 'lift_N4_sd': round(lsd4, 3),
                   'lift_N4_p': round(sum(1 for v in lift_perm4 if v >= obs_lift4)/len(lift_perm4), 4),
                   'largest_name_clusters': cluster.most_common(12)}
    pm4 = sum(perm4)/len(perm4); psd4 = math.sqrt(sum((v-pm4)**2 for v in perm4)/len(perm4))
    obs4 = sum(jac(items[i]['words'], items[j]['words']) for i, j in pairs if cand_cache[(i, j)]) / max(1, sum(1 for pr in pairs if cand_cache[pr]))
    p4 = sum(1 for v in perm4 if v >= obs4) / len(perm4)
    res = {'n_items': n, 'n_similar_pairs': len(pairs),
           'similar_pairs': [(items[i]['id'], items[j]['id'], sorted(a for a in names[i] for b in names[j] if same_name(a, b))[:3]) for i, j in pairs][:60],
           'S3_mean_jaccard': round(obs, 4),
           'N3_perm_mean': round(pm, 4), 'N3_perm_sd': round(psd, 4), 'N3_p': round(p3, 4), 'N3_z': round((obs-pm)/psd, 2) if psd else None,
           'N4_pairs_with_candidates': sum(1 for pr in pairs if cand_cache[pr]),
           'S3_on_matched_subset': round(obs4, 4), 'N4_matched_mean': round(pm4, 4), 'N4_sd': round(psd4, 4), 'N4_p': round(p4, 4),
           'N4_z': round((obs4-pm4)/psd4, 2) if psd4 else None,
           'detectable_excess_at_p05': round(1.645*psd, 4), 'exploratory_lift': exploratory}
    log(f'[{tag}] items={n} pairs={len(pairs)} S3={obs:.4f} N3 {pm:.4f}±{psd:.4f} p={p3:.4f} | N4 {pm4:.4f}±{psd4:.4f} p={p4:.4f} | lift {obs_lift:.3f} N3 {lm:.3f} p={exploratory["lift_N3_p"]} N4 {lm4:.3f} p={exploratory["lift_N4_p"]} | clusters {cluster.most_common(5)}')
    return res

def t1b(pages, log):
    rng = random.Random(SEED)
    items = [{'id': p['id'], 'fnum': p['fnum'], 'lang': p['meta'].get('L', '?'),
              'names': name_tokens(p['plant_id'], STOP), 'words': set(page_words(p))}
             for p in pages if p['plant_id'] and p['meta'].get('I') == 'H']
    res = similarity_test(items, rng, log, 'T1b')
    res['name_tokens'] = {it['id']: sorted(it['names']) for it in items}
    return res

def positive_control(lab, log):
    rng = random.Random(SEED)
    entries = AC.culpeper_entries(lab / 'pg49513.txt')
    items = [{'id': f'{i}:{name}', 'fnum': i, 'lang': 'en', 'names': name_tokens(name, STOP_CULP),
              'words': set(AC.letters_only(ws))} for i, name, ws in entries]
    return similarity_test(items, rng, log, 'control')

# ------------------------------------------------------------------ T2 ------

def merge_curve(words, mode='freq', max_merges=MAX_MERGES):
    sym = [list(w) for w in words]
    rec, merges = [], []
    def record(k):
        h1, h2 = AC.seq_stats(sym)
        pair = Counter(); first = Counter()
        for w in sym:
            for a, b in zip(w, w[1:]): pair[(a, b)] += 1; first[a] += 1
        hp = AC.H(pair); hf = AC.H(first)
        size = len(set(s for w in sym for s in w))
        rec.append({'k': k, 'alphabet': size, 'H1': round(h1, 3), 'H2_given_1': round(h2, 3), 'H2_internal': round(hp - hf, 3)})
        return pair, first
    pair, first = record(0)
    for k in range(1, max_merges + 1):
        total = sum(len(w) for w in sym)
        if mode == 'freq':
            best = max(pair.items(), key=lambda kv: (kv[1], kv[0]))[0]
        else:
            second = Counter()
            for (a, b), c in pair.items(): second[b] += c
            cands = [((a, b), min(c/first[a], c/second[b]), c) for (a, b), c in pair.items() if c >= 0.001*total]
            if not cands: break
            best = max(cands, key=lambda t: (t[1], t[2], t[0]))[0]
        a, b = best; new = a + b
        merges.append(new)
        for w in sym:
            i, out = 0, []
            while i < len(w):
                if i+1 < len(w) and w[i] == a and w[i+1] == b: out.append(new); i += 2
                else: out.append(w[i]); i += 1
            w[:] = out
        pair, first = record(k)
    return rec, merges

def at_size(rec, target):
    """Linear interpolation of H2|1 at a target alphabet size (None if never reached)."""
    if rec[0]['alphabet'] >= target:
        return rec[0]['H2_given_1'], 'initial_alphabet_already_larger'
    for prev, cur in zip(rec, rec[1:]):
        if cur['alphabet'] >= target:
            if cur['alphabet'] == prev['alphabet']: return cur['H2_given_1'], cur['k']
            f = (target - prev['alphabet']) / (cur['alphabet'] - prev['alphabet'])
            return round(prev['H2_given_1'] + f*(cur['H2_given_1'] - prev['H2_given_1']), 3), cur['k']
    return None, 'not_reached'

def t2(corpora, log):
    out = {'freq': {}, 'assoc': {}}
    for mode in ('freq', 'assoc'):
        for name, words in corpora.items():
            rec, merges = merge_curve(words, mode)
            out[mode][name] = {'curve': rec, 'first_merges': merges[:25]}
            log(f'[T2 {mode}] {name}: k0 H2|1 {rec[0]["H2_given_1"]} size {rec[0]["alphabet"]} -> k{rec[-1]["k"]} H2|1 {rec[-1]["H2_given_1"]} size {rec[-1]["alphabet"]}')
    langs = [n for n in corpora if n not in ('Voynich_S', 'Voynich_M', 'Culpeper', 'Alice')]
    summary = {}
    for mode in ('freq', 'assoc'):
        summary[mode] = {'by_size': {}, 'by_k': {}, 'crossover_size': {}}
        for t in TARGET_SIZES:
            row = {n: at_size(out[mode][n]['curve'], t) for n in corpora}
            lang_vals = [(row[n][0], n) for n in langs if row[n][0] is not None]
            low = min(lang_vals) if lang_vals else (None, None)
            for v in ('Voynich_S', 'Voynich_M'):
                row[f'gap_{v}'] = round(low[0] - row[v][0], 3) if (low[0] is not None and row[v][0] is not None) else None
            row['lowest_language'] = low
            summary[mode]['by_size'][t] = row
        for k in (0, 5, 10, 20, 30, 40, 60):
            row = {}
            for n in corpora:
                c = out[mode][n]['curve']
                row[n] = c[k]['H2_given_1'] if k < len(c) else None
            lang_vals = [(row[n], n) for n in langs if row[n] is not None]
            low = min(lang_vals) if lang_vals else (None, None)
            for v in ('Voynich_S', 'Voynich_M'):
                row[f'gap_{v}'] = round(low[0] - row[v], 3) if (low[0] is not None and row[v] is not None) else None
            row['lowest_language'] = low
            summary[mode]['by_k'][k] = row
        for v in ('Voynich_S', 'Voynich_M'):
            cross = None
            for step in out[mode][v]['curve']:
                lows = []
                for n in langs:
                    val, _ = at_size(out[mode][n]['curve'], step['alphabet'])
                    if val is not None: lows.append(val)
                if lows and step['H2_given_1'] >= min(lows):
                    cross = {'alphabet': step['alphabet'], 'k': step['k'], 'voynich': step['H2_given_1'], 'lowest_language': round(min(lows), 3)}; break
            summary[mode]['crossover_size'][v] = cross
    out['summary'] = summary
    return out

# ----------------------------------------------------------------- main -----

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True); ap.add_argument('--lab', required=True); ap.add_argument('--out', required=True)
    args = ap.parse_args()
    repo, lab, out = Path(args.repo), Path(args.lab), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    logf = open(out / 'stdout.txt', 'w', encoding='utf-8')
    def log(s): print(s, flush=True); logf.write(s + '\n'); logf.flush()
    corpus = repo / 'data/corpora/ZL3b-n.txt'
    R = {'protocol': 'PROTOCOL.md', 'seed': SEED, 'corpus_sha256': AC.sha256(corpus), 'verdicts': {}}

    # ---- T1
    pages_S = load_annotated(corpus, True)
    pages_M = load_annotated(corpus, False)
    R['T1'] = {'S': {'T1a': t1a(pages_S, log), 'T1b': t1b(pages_S, log)},
               'M': {'T1a': t1a(pages_M, log), 'T1b': t1b(pages_M, log)},
               'control': positive_control(lab, log)}
    c = R['T1']['control']; a = R['T1']['S']['T1a']; b = R['T1']['S']['T1b']
    control_ok = c is not None and c['N3_p'] < 0.01
    t1a_sig = a['N1_p'] < 0.05
    t1b_sig = b is not None and b['N3_p'] < 0.05 and b['N4_p'] < 0.05
    if not control_ok: v = 'UNDERPOWERED'
    elif t1a_sig and t1b_sig: v = 'ILLUSTRATION-LINKED VOCABULARY DETECTED'
    elif not t1a_sig and not t1b_sig: v = 'NO ILLUSTRATION-LINKED VOCABULARY AT THIS POWER'
    else: v = 'INCONCLUSIVE'
    R['verdicts']['R7'] = v
    R['verdicts']['R7_detail'] = {'control_p': c['N3_p'] if c else None, 'T1a_p': a['N1_p'], 'T1b_N3_p': b['N3_p'] if b else None, 'T1b_N4_p': b['N4_p'] if b else None}

    # ---- T2
    corpora = {'Voynich_S': [w for p in pages_S for w in page_words(p)][:SAMPLE],
               'Voynich_M': [w for p in pages_M for w in page_words(p)][:SAMPLE]}
    for xml in sorted((lab / 'bibles').glob('*.xml')):
        corpora[xml.stem] = AC.letters_only(AC.load_bible(xml))[:SAMPLE]
    corpora['Culpeper'] = AC.letters_only(AC.words_en(AC.pg_body(lab / 'pg49513.txt'), 1))[:SAMPLE]
    corpora['Alice'] = AC.letters_only(AC.words_en(AC.pg_body(repo / 'data/corpora/pg11.txt'), 1))[:SAMPLE]
    R['T2'] = t2(corpora, log)
    gaps = [R['T2']['summary']['freq']['by_size'][t]['gap_Voynich_S'] for t in TARGET_SIZES]
    gaps = [g for g in gaps if g is not None]
    R['verdicts']['R8.1'] = 'SEGMENTATION-DEPENDENT' if gaps and min(gaps) < 0.30 else 'INTRINSIC'
    R['verdicts']['R8_gaps_by_size_S'] = dict(zip([str(t) for t in TARGET_SIZES], [R['T2']['summary']['freq']['by_size'][t]['gap_Voynich_S'] for t in TARGET_SIZES]))
    R['verdicts']['R8.2_crossover'] = R['T2']['summary']['freq']['crossover_size']
    (out / 'results.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8')
    log(json.dumps(R['verdicts'], indent=1))
    logf.close()

if __name__ == '__main__':
    main()
