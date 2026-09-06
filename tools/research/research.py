#!/usr/bin/env python3
"""Bounded local qualitative-autoresearch loop. No inference, network, credentials, or publishing."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import time
import uuid

from engine import analyze, digest

ROOT = Path(__file__).resolve().parents[2]
ENGINE = Path(__file__).with_name("engine.py")
CORPUS = "data/corpora/ZL3b-n.txt"
COMPARISON = "data/corpora/pg11.txt"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def write_json(path: Path, value, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def local_path(relative: str) -> Path:
    result = (ROOT / relative).resolve()
    if not result.is_relative_to(ROOT) or any(part.startswith(".git") for part in Path(relative).parts):
        raise ValueError("Paths must stay in the research checkout and outside Git internals")
    return result


def software_hashes() -> dict:
    return {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in (ENGINE, Path(__file__))}


def input_hashes() -> dict:
    hashes = {name: digest(local_path(name).read_bytes()) for name in (CORPUS, COMPARISON)}
    for name, manifest_name in ((CORPUS, "zl3b"), (COMPARISON, "alice-english")):
        manifest = json.loads(local_path(f"data/manifests/{manifest_name}.json").read_text())
        if hashes[name] != manifest["sha256"] or local_path(name).stat().st_size != manifest["byte_length"]:
            raise ValueError("Corpus bytes differ from the reviewed source manifest")
    return hashes


def prepare(args):
    if not (1 <= args.max_seconds <= 120):
        raise ValueError("Wall limit must be between 1 and 120 seconds per variant")
    branch = local_path(f"research/branches/{args.branch}.json")
    task = local_path(f"research/first-tasks/{args.task}.json")
    if not branch.is_file() or not task.is_file():
        raise ValueError("Select an existing published branch and task")
    task_record = json.loads(task.read_text())
    if args.branch not in task_record["branch_ids"]:
        raise ValueError("Task does not belong to the selected branch")
    protocol = {"schema_version": "1.0", "id": args.id, "created_at": now(), "registration_status": "local_frozen_before_this_run; not an independent timestamped preregistration", "branch_id": args.branch, "task_id": args.task, "claim_id": args.claim, "question": "How do declared uncertainty-space policies change five descriptive ZL3b baseline diagnostics?", "analysis": "five_baseline_suite", "variants": ["join", "split", "strict"], "seed": 408, "selection_rule": "Publish all three predeclared variants and all failed attempts; no best-run selection", "inputs": input_hashes(), "software": software_hashes(), "limits": {"max_runs": 3, "max_wall_seconds_per_run": args.max_seconds, "max_total_wall_seconds": args.max_seconds * 3, "max_input_bytes": 2000000, "max_output_bytes": 2000000, "model_calls": 0, "paid_inference": False}, "acceptance": "Inputs and engine hashes unchanged, all five outputs generated, controls and every registered variant included; scientific interpretation remains qualitative and reviewable", "ai_usage": {"status": "none", "tools": [], "reproducibility_notes": "This execution uses deterministic Python only. Disclose AI assistance to protocol/code/report authorship separately."}}
    protocol["protocol_sha256"] = digest(canonical(protocol))
    write_json(local_path(args.output), protocol, exclusive=True)
    print(json.dumps({"protocol": args.output, "sha256": protocol["protocol_sha256"], "variants": protocol["variants"]}))


def load_protocol(path: str) -> dict:
    protocol = json.loads(local_path(path).read_text(encoding="utf-8"))
    expected = protocol.pop("protocol_sha256")
    if digest(canonical(protocol)) != expected:
        raise ValueError("Frozen protocol was modified; create a new protocol and disclose it")
    protocol["protocol_sha256"] = expected
    if protocol["software"] != software_hashes() or protocol["inputs"] != input_hashes():
        raise ValueError("Code or input bytes differ from the frozen protocol")
    if protocol["variants"] != ["join", "split", "strict"] or protocol["limits"]["max_runs"] != 3:
        raise ValueError("Unsupported protocol; evaluator changes require a separate reviewed artifact")
    if sum(local_path(name).stat().st_size for name in protocol["inputs"]) > protocol["limits"]["max_input_bytes"]:
        raise ValueError("Input bytes exceed protocol limit")
    return protocol


def run(args):
    protocol = load_protocol(args.protocol)
    root = local_path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".run-lock"
    # Exclusive lock and an append-only attempt inventory prevent accidental parallel/repeated budget resets.
    with lock.open("x", encoding="ascii") as handle:
        handle.write(str(os.getpid()))
    try:
        prior = [json.loads(p.read_text()) for p in root.glob("*/run.json")]
        if any(x["protocol_sha256"] != protocol["protocol_sha256"] for x in prior):
            raise ValueError("Output directory already belongs to a different protocol")
        attempted = [x["variant"] for x in prior]
        used_wall = sum(x.get("elapsed_seconds") or protocol["limits"]["max_wall_seconds_per_run"] for x in prior)
        for variant in protocol["variants"]:
            if variant in attempted:
                continue
            if len(prior) >= protocol["limits"]["max_runs"]:
                raise ValueError("Iteration budget exhausted; no retries within this protocol")
            remaining = protocol["limits"]["max_total_wall_seconds"] - used_wall
            if remaining <= 0:
                raise ValueError("Total wall budget exhausted")
            run_id = now().replace(":", "").replace(".", "-") + "-" + uuid.uuid4().hex[:8]
            directory = root / run_id
            directory.mkdir()
            result_file = directory / "output.json"
            command = [sys.executable, str(Path(__file__)), "_execute", "--variant", variant, "--seed", str(protocol["seed"]), "--output", str(result_file.relative_to(ROOT))]
            record = {"schema_version": "1.0", "id": run_id, "parent_task": protocol["task_id"], "parent_claim": protocol["claim_id"], "protocol_sha256": protocol["protocol_sha256"], "variant": variant, "seed": protocol["seed"], "parameters": {"variant": variant}, "inputs": protocol["inputs"], "software": protocol["software"], "command": ["python", "tools/research/research.py", "_execute", "--variant", variant, "--seed", str(protocol["seed"]), "--output", str(result_file.relative_to(ROOT)).replace("\\", "/")], "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(), "platform": platform.platform(), "dependencies": "Python standard library only"}, "started_at": now(), "ended_at": None, "elapsed_seconds": None, "state": "started", "exit_code": None, "stdout": "stdout.txt", "stderr": "stderr.txt", "outputs": {}, "ai_usage": protocol["ai_usage"], "resource_usage": {"maximum_wall_seconds": min(remaining, protocol["limits"]["max_wall_seconds_per_run"]), "model_calls": 0, "network_requests": 0, "memory_limit": "Input/output bounded; trusted CPU engine only. No OS memory sandbox is claimed."}}
            write_json(directory / "run.json", record, exclusive=True)
            start = time.monotonic()
            try:
                with (directory / "stdout.txt").open("w", encoding="utf-8") as stdout, (directory / "stderr.txt").open("w", encoding="utf-8") as stderr:
                    proc = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=record["resource_usage"]["maximum_wall_seconds"], check=False)
                record["exit_code"] = proc.returncode
                record["state"] = "completed" if proc.returncode == 0 else "failed"
                if result_file.is_file():
                    if result_file.stat().st_size > protocol["limits"]["max_output_bytes"]:
                        record["state"] = "output_limit_exceeded"
                    record["outputs"] = {"output.json": digest(result_file.read_bytes())}
            except subprocess.TimeoutExpired:
                record["state"] = "timed_out"
            except KeyboardInterrupt:
                record["state"] = "interrupted"
                raise
            finally:
                record["elapsed_seconds"] = time.monotonic() - start
                record["ended_at"] = now()
                write_json(directory / "run.json", record)
                prior.append(record)
                used_wall += record["elapsed_seconds"]
            print(json.dumps({"id": run_id, "variant": variant, "state": record["state"], "elapsed_seconds": record["elapsed_seconds"]}))
            if record["state"] != "completed":
                raise ValueError("Run failed visibly; inspect the retained evidence before creating a disclosed follow-up protocol")
    finally:
        lock.unlink()


def compare(args):
    protocol = load_protocol(args.protocol)
    root = local_path(args.runs)
    records, summaries = [], []
    for file in sorted(root.glob("*/run.json")):
        record = json.loads(file.read_text())
        if record["protocol_sha256"] != protocol["protocol_sha256"] or record["inputs"] != protocol["inputs"] or record["software"] != protocol["software"]:
            raise ValueError("Incompatible run cannot enter this comparison")
        records.append(record)
        if record["state"] != "completed":
            summaries.append({"variant": record["variant"], "state": record["state"]})
            continue
        output_path = file.with_name("output.json")
        if digest(output_path.read_bytes()) != record["outputs"]["output.json"]:
            raise ValueError("Output checksum mismatch")
        output = json.loads(output_path.read_text())
        summaries.append({"variant": record["variant"], "state": record["state"], "retained_paragraph_tokens": output["integrity"]["paragraph_tokens_retained"], "mean_token_length": output["frequency"]["actual_full_paragraph_corpus"]["mean_encoded_token_length"], "conditional_entropy": output["entropy"]["comparison"]["voynich"]["next_symbol_given_previous_bits"], "section_nmi": output["clustering"]["section_nmi"]["observed"], "source_specific_hand_nmi": output["clustering"]["source_specific_hand_nmi"], "first_minus_nonfirst_length": output["position"]["actual"]["first_minus_nonfirst_mean_length"]})
    variants = [x["variant"] for x in records]
    if len(variants) != len(set(variants)) or set(variants) != set(protocol["variants"]):
        raise ValueError("Missing or repeated registered variants; publish all attempts")
    report = {"schema_version": "1.0", "protocol_sha256": protocol["protocol_sha256"], "created_at": now(), "status": "complete" if all(x["state"] == "completed" for x in records) else "partial", "all_run_ids": [x["id"] for x in records], "selection_rule": protocol["selection_rule"], "summaries": summaries, "interpretation": "Descriptive normalization sensitivity only; no metric is a translation accuracy or contribution score.", "registration": protocol["registration_status"]}
    write_json(local_path(args.output), report, exclusive=True)
    print(json.dumps(report))


def bundle(args):
    import re
    if args.github_id < 1 or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", args.github_login) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", args.id):
        raise ValueError("Supply a real GitHub numeric identity and safe contribution ID")
    protocol = load_protocol(args.protocol)
    comparison_path = local_path(args.comparison)
    comparison = json.loads(comparison_path.read_text())
    if comparison["protocol_sha256"] != protocol["protocol_sha256"]:
        raise ValueError("Comparison belongs to another protocol")
    ai = json.loads(local_path(args.ai_disclosure).read_text())
    if ai.get("status") not in ("none", "assisted", "primarily_generated") or not isinstance(ai.get("tools"), list):
        raise ValueError("Supply an honest AI disclosure matching the contribution schema")
    prefix = f"contributions/{args.id}"
    directory = local_path(prefix)
    directory.mkdir(parents=True, exist_ok=False)
    source_runs = local_path(args.runs)
    run_files = sorted(source_runs.glob("*/run.json"))
    run_ids = []
    for source in run_files:
        run_record = json.loads(source.read_text())
        if run_record["protocol_sha256"] != protocol["protocol_sha256"]:
            raise ValueError("Bundle includes a run from another protocol")
        run_ids.append(run_record["id"])
        for output, expected in run_record["outputs"].items():
            if output != "output.json" or digest(source.with_name(output).read_bytes()) != expected:
                raise ValueError("Bundle output checksum mismatch")
    if sorted(run_ids) != sorted(comparison["all_run_ids"]):
        raise ValueError("Bundle attempts do not match the reviewed comparison")
    # Copy every material run, including failure records. Full corpus stays in its licensed source path.
    copied = []
    for source in sorted(source_runs.glob("*/*")):
        if not source.is_file() or source.suffix not in (".json", ".txt"):
            continue
        target = directory / "runs" / source.relative_to(source_runs)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        copied.append(target.relative_to(ROOT).as_posix())
    (directory / "protocol.json").write_bytes(local_path(args.protocol).read_bytes())
    (directory / "comparison.json").write_bytes(comparison_path.read_bytes())
    (directory / "rights.md").write_text("# Rights and provenance\n\nOriginal run metadata and analysis outputs: CC BY 4.0, authored for voynich.win. Analysis code: Apache-2.0. ZL3b and GC2a hosted transliterations: CC0 according to https://voynich.nu/roadmap.html#copy ; see data/manifests and sources/catalog.json. Comparison source is Project Gutenberg eBook 11, public domain in the USA, with its complete source notice retained in data/corpora/pg11.txt. No manuscript scans or scholarly PDFs are copied into this bundle.\n", encoding="utf-8")
    manifest = {"schema_version": "1.0", "id": args.id, "kind": "research", "title": "Documented local normalization sensitivity run", "summary": "All three bounded registered variants of five descriptive Voynich baseline diagnostics, with controls and complete run records.", "branch_ids": [protocol["branch_id"]], "contributors": [{"github_id": args.github_id, "github_login": args.github_login, "roles": ["Investigation", "Software", "Validation"]}], "ai_usage": ai, "changes": [{"path": f"{prefix}/comparison.json", "improvement": "An inspectable comparison retaining every registered variant and failure."}], "outcomes": [], "claimed_total_points": 0, "rubric_version": "0.1", "conflicts": ["Author is responsible for these runs; no independent human reproduction is asserted."], "limitations": ["A routine rerun of designated seed baselines does not create new scoreable value.", "Inspect results and supply a distinct, evidenced family outcome before claiming credit.", "Local protocol freezing is not an independent public preregistration."], "rights_manifest": f"{prefix}/rights.md"}
    write_json(directory / "contribution.json", manifest, exclusive=True)
    write_json(directory / "bundle-inventory.json", {"files": {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in sorted(directory.rglob("*")) if p.is_file()}, "source_protocol_sha256": protocol["protocol_sha256"], "includes_all_registered_attempts": True}, exclusive=True)
    print(json.dumps({"manifest": f"{prefix}/contribution.json", "competitive_claim": 0, "next": "Run the public schema validator and grader estimate, inspect locally, then commit and open a GitHub PR yourself."}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--id", required=True)
    p.add_argument("--branch", default="statistical-structure")
    p.add_argument("--task", default="task-05-entropy-sensitivity")
    p.add_argument("--claim", default="claim-entropy-structure")
    p.add_argument("--max-seconds", type=int, default=60)
    p.add_argument("--output", required=True)
    p.set_defaults(action=prepare)
    p = commands.add_parser("run")
    p.add_argument("--protocol", required=True)
    p.add_argument("--output", required=True)
    p.set_defaults(action=run)
    p = commands.add_parser("compare")
    p.add_argument("--protocol", required=True)
    p.add_argument("--runs", required=True)
    p.add_argument("--output", required=True)
    p.set_defaults(action=compare)
    p = commands.add_parser("bundle")
    for name in ("id", "protocol", "runs", "comparison", "ai-disclosure", "github-login"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--github-id", type=int, required=True)
    p.set_defaults(action=bundle)
    p = commands.add_parser("_execute", help=argparse.SUPPRESS)
    p.add_argument("--variant", choices=["join", "split", "strict"], required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--output", required=True)
    def execute(args):
        start = time.process_time()
        output = analyze(local_path(CORPUS), local_path(COMPARISON), args.variant, args.seed)
        output["resource_usage"] = {"cpu_seconds": time.process_time() - start, "model_calls": 0}
        write_json(local_path(args.output), output, exclusive=True)
        print(json.dumps({"loci": output["integrity"]["loci"], "variant": args.variant, "status": "completed"}))
    p.set_defaults(action=execute)
    args = parser.parse_args()
    args.action(args)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        raise SystemExit(1)
