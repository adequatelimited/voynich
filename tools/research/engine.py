"""CPU-only, standard-library baseline engine. Units are encoded symbols, not inferred glyphs."""
from __future__ import annotations

import collections
import hashlib
import json
import math
import random
import re
from pathlib import Path

VERSION = "seed-1.0"
PAGE = re.compile(r"^<(?P<page>f(?:\d+[rv]\d*|Ros))>\s*(?P<text>.*)$")
LOCUS = re.compile(r"^<(?P<page>f(?:\d+[rv]\d*|Ros))\.(?P<number>\d+),(?P<code>[^>;]+)(?:;(?P<transcriber>[^>]+))?>\s*(?P<text>.*)$")
SYMBOL = re.compile(r"@[12]\d\d;|[a-zA-Z']")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_ivtff(path: Path) -> dict:
    raw = path.read_bytes()
    text = raw.decode("ascii")
    physical = text.splitlines()
    if not physical or not physical[0].startswith("#=IVTFF "):
        raise ValueError("Missing IVTFF header")
    header = physical[0].split()
    if header[2] != "2.0":
        raise ValueError("Only IVTFF 2.0 has been inspected")
    logical = []
    pending = ""
    for line_number, line in enumerate(physical[1:], 2):
        if len(line) > 2048:
            raise ValueError(f"Physical line exceeds IVTFF limit: {line_number}")
        if pending:
            if not line.startswith("/"):
                raise ValueError(f"Malformed continuation at {line_number}")
            pending += line[1:].rstrip()
        else:
            pending = line.rstrip()
        if pending.endswith("/"):
            pending = pending[:-1]
            continue
        logical.append((line_number, pending))
        pending = ""
    if pending:
        raise ValueError("Unterminated continuation")
    pages, loci, comments, seen = {}, [], [], set()
    current = None
    text_tags = {}
    for number, line in logical:
        if not line.strip() or line.startswith("#"):
            if line.startswith("#"):
                comments.append({"line": number, "raw": line})
            continue
        page = PAGE.match(line)
        if page:
            current = page["page"]
            if current in pages:
                raise ValueError(f"Duplicate page {current}")
            pages[current] = {"id": current, "variables": dict(re.findall(r"\$([A-Z])=(.)", page["text"])), "raw": line}
            text_tags = {}
            continue
        locus = LOCUS.match(line)
        if not locus or locus["page"] != current:
            raise ValueError(f"Unrecognized or misplaced data at line {number}")
        locus_id = f'{current}.{locus["number"]}'
        unique = (locus_id, locus["transcriber"])
        if unique in seen:
            raise ValueError(f"Duplicate locus/transcriber {unique}")
        seen.add(unique)
        for name, value in re.findall(r"<@([A-Z])=(.)>", locus["text"]):
            if value == "@":
                text_tags.pop(name, None)
            else:
                text_tags[name] = value
        variables = {**pages[current]["variables"], **text_tags}
        loci.append({"id": locus_id, "page": current, "number": int(locus["number"]), "code": locus["code"], "transcriber": locus["transcriber"], "raw": locus["text"], "line_number": number, "variables": variables})
    return {"header": physical[0], "alphabet": header[1], "sha256": digest(raw), "bytes": len(raw), "physical_lines": len(physical), "pages": pages, "loci": loci, "comments": comments}


def normalize(raw: str, variant: str) -> tuple[list[list[str]], dict]:
    """Preserve uncertainty in source; make each derived exclusion/choice measurable."""
    if variant not in ("join", "split", "strict"):
        raise ValueError("Unknown normalization variant")
    stats = collections.Counter()
    stats["alternative_readings"] = len(re.findall(r"\[[^]]*\]", raw))
    stats["uncertain_spaces"] = raw.count(",")
    stats["unreadable_markers"] = raw.count("?")
    stats["drawing_breaks"] = raw.count("<->") + raw.count("<~>")
    raw = raw.replace("<->", ".").replace("<~>", ".")
    raw = re.sub(r"<[^>]*>", "", raw)
    raw = re.sub(r"\[[^]]*\]", lambda m: "?" if variant == "strict" else m[0][1:-1].split(":")[0], raw)
    raw = raw.replace("{", "").replace("}", "")
    raw = raw.replace(",", "." if variant == "split" else "?" if variant == "strict" else "")
    raw = re.sub(r"\s", "", raw)
    result = []
    for token in raw.split("."):
        if not token:
            continue
        symbols = SYMBOL.findall(token)
        if not symbols or "".join(symbols) != token:
            stats["excluded_tokens"] += 1
            continue
        if any(s.startswith("@") and not 128 <= int(s[1:4]) <= 255 for s in symbols):
            stats["excluded_tokens"] += 1
            continue
        # Case denotes ligature conventions, not an inferred phonemic distinction.
        result.append([s.lower() for s in symbols])
    stats["accepted_tokens"] = len(result)
    return result, dict(stats)


def entropy(counter: collections.Counter) -> float:
    n = sum(counter.values())
    return -sum((v / n) * math.log2(v / n) for v in counter.values()) if n else 0.0


def information(tokens: list[list[str]], include_boundaries: bool = False, symbol_limit: int | None = None) -> dict:
    unigrams, pairs = collections.Counter(), collections.Counter()
    remaining = symbol_limit if symbol_limit is not None else 10**12
    for token in tokens:
        seq = (["<B>"] + token + ["<E>"]) if include_boundaries else token
        seq = seq[:remaining]
        remaining -= len(seq)
        unigrams.update(seq)
        pairs.update(zip(seq, seq[1:]))
        if remaining <= 0:
            break
    contexts = collections.Counter()
    for (left, _), count in pairs.items():
        contexts[left] += count
    n = sum(pairs.values())
    conditional = -sum((count / n) * math.log2(count / contexts[left]) for (left, _), count in pairs.items()) if n else 0.0
    return {"symbols": sum(unigrams.values()), "bigrams": n, "alphabet_size": len(unigrams), "unigram_bits": entropy(unigrams), "next_symbol_given_previous_bits": conditional, "word_boundaries_included": include_boundaries, "estimator": "plug-in maximum likelihood; no finite-sample correction; no pairs cross tokens"}


def distribution(tokens: list[list[str]]) -> dict:
    types = collections.Counter(tuple(t) for t in tokens)
    lengths = collections.Counter(map(len, tokens))
    symbols = collections.Counter(s for token in tokens for s in token)
    n = len(tokens)
    mean = sum(k * v for k, v in lengths.items()) / n if n else 0
    variance = sum((k - mean) ** 2 * v for k, v in lengths.items()) / n if n else 0
    return {"tokens": n, "types": len(types), "type_token_ratio": len(types) / n if n else 0, "mean_encoded_token_length": mean, "population_sd_length": math.sqrt(variance), "length_histogram": dict(sorted(lengths.items())), "symbol_counts": dict(sorted(symbols.items())), "top_token_counts": [{"token": "".join(k), "count": v} for k, v in types.most_common(30)], "hapax_types": sum(v == 1 for v in types.values())}


def shuffled_tokens(tokens: list[list[str]], rng: random.Random) -> list[list[str]]:
    symbols = [s for t in tokens for s in t]
    rng.shuffle(symbols)
    output, pos = [], 0
    for token in tokens:
        output.append(symbols[pos:pos + len(token)])
        pos += len(token)
    return output


def synthetic(tokens: list[list[str]], rng: random.Random) -> list[list[str]]:
    """An authored, deliberately simple copy/mutate null. Not a replication of Timm."""
    vocabulary = [list(x) for x in ("daiin", "qokedy", "chedy", "ol", "ar", "shey")]
    alphabet = list("acdehiklnoqrstuy")
    output = []
    for i in range(len(tokens)):
        prior = output[max(0, i - 20):] or vocabulary
        word = list(rng.choice(prior))
        if rng.random() < .5:
            word[rng.randrange(len(word))] = rng.choice(alphabet)
        if rng.random() < .08 and len(word) < 12:
            word.append(rng.choice(alphabet))
        if rng.random() < .08 and len(word) > 1:
            word.pop()
        output.append(word)
    return output


def known_plaintext(n: int) -> list[list[str]]:
    """Original controlled English grammar with two topics; no external text or claims."""
    sentences = ["the careful reader compares each symbol with the drawing", "a green plant has narrow leaves and a pale root", "the bright star moves above the circular map", "another researcher records an uncertain mark before testing a claim"]
    words = " ".join(sentences).split()
    return [list(words[i % len(words)]) for i in range(n)]


def meaningful_text(path: Path) -> list[list[str]]:
    text = path.read_text(encoding="utf-8-sig")
    start = re.search(r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*", text)
    end = re.search(r"\*\*\* END OF THE PROJECT GUTENBERG EBOOK", text)
    if not start or not end or start.end() >= end.start():
        raise ValueError("Gutenberg body delimiters are missing")
    return [list(word) for word in re.findall(r"[a-z]+", text[start.end():end.start()].lower())]


def position_metrics(lines: list[list[list[str]]]) -> dict:
    good = [line for line in lines if len(line) >= 2]
    first = [len(line[0]) for line in good]
    last = [len(line[-1]) for line in good]
    other = [len(t) for line in good for t in line[1:]]
    pairs = [(a, b) for line in good for a, b in zip(line, line[1:])]
    repeats = sum(a == b for a, b in pairs)
    mean = lambda xs: sum(xs) / len(xs) if xs else 0
    return {"eligible_loci": len(good), "first_minus_nonfirst_mean_length": mean(first) - mean(other), "first_mean_length": mean(first), "last_mean_length": mean(last), "adjacent_token_pairs": len(pairs), "adjacent_identical_pairs": repeats, "adjacent_repeat_rate": repeats / len(pairs) if pairs else 0}


def null_summary(observed: float, values: list[float]) -> dict:
    # Two-sided tail count about the sampled-null mean; descriptive finite randomization diagnostic.
    mean = sum(values) / len(values)
    tail = sum(abs(v - mean) >= abs(observed - mean) for v in values)
    return {"observed": observed, "null_mean": mean, "null_min": min(values), "null_max": max(values), "replicates": len(values), "two_sided_tail_fraction_plus_one": (tail + 1) / (len(values) + 1), "values": values, "inference": "diagnostic only; 39 null draws and multiple exploratory metrics do not establish a manuscript-wide discovery"}


def nmi(a: list, b: list) -> float:
    n = len(a)
    ca, cb, cab = collections.Counter(a), collections.Counter(b), collections.Counter(zip(a, b))
    mi = sum(v / n * math.log2(v * n / (ca[x] * cb[y])) for (x, y), v in cab.items())
    denominator = entropy(ca) + entropy(cb)
    return 2 * mi / denominator if denominator else 0


def cluster_pages(loci: list[dict], normalized: dict, seed: int) -> dict:
    page_tokens, labels, hands, quires = collections.defaultdict(list), {}, {}, {}
    for locus in loci:
        if not locus["code"][1:].startswith("P"):
            continue
        page = locus["page"]
        page_tokens[page].extend(normalized[locus["id"]])
        labels[page] = locus["variables"].get("I", "unknown")
        hands.setdefault(page, set()).add(locus["variables"].get("H", "unknown"))
        quires[page] = locus["variables"].get("Q", "unknown")
    pages = sorted(p for p, words in page_tokens.items() if len(words) >= 50)
    counts = collections.Counter(labels[p] for p in pages)
    pages = [p for p in pages if counts[labels[p]] >= 3]
    names = sorted({s for p in pages for t in page_tokens[p] for s in t})
    vectors = []
    for page in pages:
        counter = collections.Counter(s for t in page_tokens[page] for s in t)
        norm = math.sqrt(sum(v*v for v in counter.values()))
        vectors.append([counter[s] / norm for s in names])
    k = min(8, len(set(labels[p] for p in pages)))
    if len(pages) < 2 * k or k < 2:
        return {"status": "blocked", "reason": "Insufficient labeled pages"}
    rng = random.Random(seed)
    centers = [list(vectors[i]) for i in rng.sample(range(len(pages)), k)]
    assignments = [-1] * len(pages)
    iterations = 0
    for iterations in range(1, 51):
        new = [min(range(k), key=lambda c: sum((x-y)**2 for x, y in zip(v, centers[c]))) for v in vectors]
        if new == assignments:
            break
        assignments = new
        for c in range(k):
            members = [v for v, a in zip(vectors, assignments) if a == c]
            if members:
                centers[c] = [sum(v[j] for v in members) / len(members) for j in range(len(names))]
    section = [labels[p] for p in pages]
    observed = nmi(assignments, section)
    permuted = []
    within_quire = []
    groups = collections.defaultdict(list)
    for i, p in enumerate(pages):
        groups[quires[p]].append(i)
    for _ in range(39):
        shuffled = list(section)
        rng.shuffle(shuffled)
        permuted.append(nmi(assignments, shuffled))
        stratified = list(section)
        for indices in groups.values():
            values = [section[i] for i in indices]
            rng.shuffle(values)
            for i, val in zip(indices, values):
                stratified[i] = val
        within_quire.append(nmi(assignments, stratified))
    hand_indices = [i for i,p in enumerate(pages) if len(hands[p]) == 1 and next(iter(hands[p])) in "12345"]
    hand_values = [next(iter(hands[pages[i]])) for i in hand_indices]
    hand_nmi = nmi([assignments[i] for i in hand_indices], hand_values) if hand_indices else None
    return {"status": "executed", "method": "deterministic Lloyd k-means on L2-normalized encoded-symbol unigram frequencies; Euclidean distance; one fixed initialization", "pages": len(pages), "minimum_tokens_per_page": 50, "minimum_pages_per_section": 3, "k": k, "iterations": iterations, "section_counts": dict(collections.Counter(section)), "section_nmi": null_summary(observed, permuted), "within_quire_section_nmi": null_summary(observed, within_quire), "source_specific_hand_nmi": hand_nmi, "single_hand_labeled_pages": len(hand_indices), "excluded_mixed_or_unknown_hand_pages": len(pages) - len(hand_indices), "assignments": [{"page": p, "cluster": a, "section_ZL_I": labels[p], "hand_ZL_H": sorted(hands[p]), "quire_ZL_Q": quires[p]} for p,a in zip(pages,assignments)], "limitations": ["Labels are ZL3b metadata, not verified ground truth; H tags follow IVTFF's Davis-hand convention, not Currier C tags.", "Section, quire, hand and neighboring pages are confounded. Within-quire shuffling can have little power when labels are constant.", "No LDA/LSA/NMF reproduction or semantic identification is claimed; one initialization is a fixed baseline, not a selected optimum.", "Foldout panels are transcription units; related physical sides are not independent samples."]}


def analyze(corpus_path: Path, comparison_path: Path, variant: str, seed: int) -> dict:
    corpus = parse_ivtff(corpus_path)
    if not corpus["alphabet"].startswith("Eva"):
        raise ValueError("This baseline normalization is only declared for EVA")
    normalized, normalization = {}, collections.Counter()
    for locus in corpus["loci"]:
        normalized[locus["id"]], stats = normalize(locus["raw"], variant)
        normalization.update(stats)
    paragraphs = [l for l in corpus["loci"] if l["code"][1:].startswith("P") and l["code"][0] != "!"]
    tokens = [token for locus in paragraphs for token in normalized[locus["id"]]]
    if len(tokens) < 10000:
        raise ValueError("Actual corpus too small for declared baseline")
    comparison = meaningful_text(comparison_path)
    count = min(len(tokens), len(comparison), 20000)
    matched = {"voynich": tokens[:count], "english_alice": comparison[:count], "authored_plaintext": known_plaintext(count)}
    matched["symbol_shuffle"] = shuffled_tokens(matched["voynich"], random.Random(seed))
    matched["copy_mutate_pseudotext"] = synthetic(matched["voynich"], random.Random(seed))
    minimum_symbols = min(sum(map(len, value)) for value in matched.values())
    frequency = {"actual_full_paragraph_corpus": distribution(tokens), "matched_token_count": count, "comparison": {k: distribution(v) for k,v in matched.items()}}
    info = {"matched_symbol_count_without_boundaries": minimum_symbols, "comparison": {k: information(v, False, minimum_symbols) for k,v in matched.items()}, "boundary_sensitivity": {k: information(v, True) for k,v in matched.items()}, "limitations": ["Encoded EVA characters are not graphemes; English uses lowercase a-z runs. Differences do not identify a language or cipher.", "Only one English novel is sampled, by a fixed prefix. Corpus-genre, script and position differences remain.", "Boundary sensitivity uses the same token count but has different symbol counts; compare within an explicitly stated convention."]}
    # P0 omits separate title fragments Pt; loci are still not guaranteed physical lines.
    lines = [normalized[l["id"]] for l in paragraphs if l["code"][1:] == "P0"]
    position = position_metrics(lines)
    nulls = []
    rng = random.Random(seed)
    for _ in range(39):
        permuted = []
        for line in lines:
            shuffled = list(line)
            rng.shuffle(shuffled)
            permuted.append(shuffled)
        nulls.append(position_metrics(permuted))
    position_result = {"scope": "ZL paragraph loci of subtype P0, with >=2 retained tokens; no cross-locus token pairs", "actual": position, "within_locus_shuffle": {key: null_summary(position[key], [x[key] for x in nulls]) for key in ("first_minus_nonfirst_mean_length", "adjacent_repeat_rate")}, "limitations": ["A transcription locus need not equal a complete physical manuscript line.", "Uncertain-token exclusions can create apparent adjacency; compare strict/join/split variants.", "Diagnostic randomizations preserve each locus's token multiset, not a historical production process."]}
    all_raw = "\n".join(l["raw"] for l in corpus["loci"])
    integrity = {"input_sha256": corpus["sha256"], "input_bytes": corpus["bytes"], "header": corpus["header"], "physical_lines": corpus["physical_lines"], "transcription_page_units": len(corpus["pages"]), "loci": len(corpus["loci"]), "paragraph_loci": len(paragraphs), "locus_type_counts": dict(collections.Counter(l["code"][1:] for l in corpus["loci"])), "normalization": dict(normalization), "raw_alternative_reading_groups": len(re.findall(r"\[[^]]*\]", all_raw)), "raw_uncertain_spaces": all_raw.count(","), "paragraph_tokens_retained": len(tokens), "duplicate_loci": 0, "locus_page_mismatches": 0, "official_physical_leaf_count": 102, "official_scans_count": None, "limitations": ["102 physical leaves is Yale's catalog description; transcription page units, sides, foldout panels and scans are separate counts.", "No image validation or complete alignment with a second independent reading has yet occurred.", "Commentary is preserved in the CC0 source, excluded from numerical text and not imported as factual plant identifications."]}
    return {"schema_version": "1.0", "engine_version": VERSION, "variant": variant, "seed": seed, "corpus_sha256": corpus["sha256"], "comparison_sha256": digest(comparison_path.read_bytes()), "integrity": integrity, "frequency": frequency, "entropy": info, "position": position_result, "clustering": cluster_pages(corpus["loci"], normalized, seed), "scientific_status": "executed_descriptive_seed_baseline", "competitive_points": 0}
