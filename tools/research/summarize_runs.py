"""Publish bounded summaries; referencing a hash never claims inspection of the full artifact."""
import json
from pathlib import Path
from engine import digest

ROOT = Path(__file__).resolve().parents[2]


def without_distributions(value):
    # Scalars, histogram lengths and null diagnostics remain; detailed rows stay in hashed raw outputs.
    if isinstance(value, dict):
        return {k: without_distributions(v) for k,v in value.items() if k not in ("top_token_counts", "symbol_counts", "values", "assignments")}
    if isinstance(value, list):
        return [without_distributions(v) for v in value]
    return value


def main():
    summaries = []
    for output_file in sorted((ROOT / "experiments/runs/launch-seed-v1").glob("*/output.json")):
        output = json.loads(output_file.read_text())
        record_file = output_file.with_name("run.json")
        record = json.loads(record_file.read_text())
        if digest(output_file.read_bytes()) != record["outputs"]["output.json"]:
            raise ValueError("Raw output digest mismatch")
        summary = {"schema_version": "1.0", "id": f'run-summary-{output["variant"]}-v1', "run_id": record["id"], "protocol_sha256": record["protocol_sha256"], "state": record["state"], "variant": output["variant"], "seed": output["seed"], "inputs": record["inputs"], "software": record["software"], "registration": "Locally frozen before the retained three-variant execution; one earlier join-variant engineering smoke run was already inspected. Descriptive seed, not public preregistered confirmatory science.", "metrics": without_distributions({k: output[k] for k in ("integrity", "frequency", "entropy", "position", "clustering")}), "full_artifacts": [{"path": output_file.relative_to(ROOT).as_posix(), "sha256": digest(output_file.read_bytes()), "bytes": output_file.stat().st_size}, {"path": record_file.relative_to(ROOT).as_posix(), "sha256": digest(record_file.read_bytes()), "bytes": record_file.stat().st_size}], "summary_scope": "All scalar baseline metrics, length histograms, control metrics and aggregate null diagnostics. Token-frequency rows, symbol-frequency rows, individual null draws and per-page cluster assignments remain only in the linked complete outputs.", "inspection_limit": "This summary is an original derived artifact. Its hashes establish byte identity when verified, not semantic inspection, execution authenticity or safety of a referenced artifact. A reviewer must report unread evidence as uninspected.", "limitations": ["Encoded units are not recovered linguistic glyphs; source-specific section/hand labels are confounded by quire and layout.", "One English prose comparator and finite authored controls do not represent all languages or historical mechanisms.", "No independent human reproduction, official model grade, point award or accepted decipherment is claimed."], "competitive_points": 0}
        target = ROOT / f'experiments/summaries/{output["variant"]}-v1.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        encoded = (json.dumps(summary, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
        if len(encoded) >= 12000:
            raise ValueError(f"Compact summary exceeds 12 kB: {len(encoded)}")
        target.write_bytes(encoded)
        summaries.append({"variant": output["variant"], "path": target.relative_to(ROOT).as_posix(), "bytes": len(encoded), "sha256": digest(encoded)})
    for file in (ROOT / "experiments/baselines").glob("*.json"):
        card = json.loads(file.read_text())
        card["compact_summaries"] = summaries
        file.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summaries))


if __name__ == "__main__":
    main()
