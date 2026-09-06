"""Execute the declared narrow replication checks; never imply the full papers were reproduced."""
import datetime
import json
from pathlib import Path
import platform
import time
from engine import parse_ivtff, digest

ROOT = Path(__file__).resolve().parents[2]


def main():
    start = time.monotonic()
    counts = {}
    for name, expected_loci, expected_paragraphs in (("ZL3b-n.txt", 5385, 740), ("GC2a-n.txt", 5367, 775)):
        parsed = parse_ivtff(ROOT / "data/corpora" / name)
        loci = len(parsed["loci"])
        paragraphs = sum("<%>" in x["raw"] for x in parsed["loci"])
        if (loci, paragraphs) != (expected_loci, expected_paragraphs):
            raise ValueError(f"Published-count mismatch for {name}; inspect rather than silently updating the target")
        counts[name] = {"sha256": parsed["sha256"], "loci": loci, "paragraph_start_markers": paragraphs, "page_units": len(parsed["pages"]), "matches_targeted_source_counts": True}
    joined = None
    for file in (ROOT / "experiments/runs/launch-seed-v1").glob("*/output.json"):
        value = json.loads(file.read_text())
        if value["variant"] == "join":
            record = json.loads(file.with_name("run.json").read_text())
            if record["outputs"]["output.json"] != digest(file.read_bytes()):
                raise ValueError("Retained output checksum mismatch")
            joined = value
            break
    if joined is None:
        raise ValueError("Missing actual completed join-variant output")
    metrics = {k: v["next_symbol_given_previous_bits"] for k,v in joined["entropy"]["comparison"].items()}
    if not metrics["voynich"] < metrics["english_alice"] or not metrics["authored_plaintext"] < metrics["english_alice"]:
        raise ValueError("The bounded report's stated observed ordering does not hold")
    # Material metric values are read from actual outputs, never fabricated or rounded into a false receipt.
    entropy_file = ROOT / "research/replications/entropy.json"
    report = json.loads(entropy_file.read_text())
    report["actual_join_variant_bits_per_symbol"] = {"voynich_ZL3b": metrics["voynich"], "english_Alice": metrics["english_alice"], "authored_plaintext": metrics["authored_plaintext"]}
    entropy_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    result = {"schema_version": "1.0", "id": "replication-check-seed-v1", "status": "completed_bounded_checks", "executed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "command": "python tools/research/verify_replications.py", "python": platform.python_version(), "elapsed_seconds": time.monotonic() - start, "code_sha256": digest(Path(__file__).read_bytes()), "parser_sha256": digest(Path(__file__).with_name("engine.py").read_bytes()), "counts": counts, "actual_join_entropy_bits": metrics, "full_paper_replications": False, "independent_human_reproduction": False, "model_calls": 0}
    (ROOT / "research/replications/count-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
