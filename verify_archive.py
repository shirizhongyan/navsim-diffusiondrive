#!/usr/bin/env python3
"""Rebuild scores and collision changes, or verify the archived evidence hashes."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


EXPECTED = {
    "diffusiondrive_agent_eval": 88.0685,
    "human_agent_eval": 94.5514,
    "finetune_hardmining_v1_eval": 87.5205,
    "finetune_v2_eval_epoch00": 88.0127,
    "finetune_v2_eval_epoch01": 87.8845,
    "finetune_v2_eval_epoch02": 87.8995,
    "finetune_v2_eval_epoch03": 87.9573,
}


def read_scores(file):
    with file.open(newline="") as stream:
        rows = [row for row in csv.DictReader(stream) if row["token"] != "average"]
    if len({row["token"] for row in rows}) != len(rows):
        raise ValueError(f"Duplicate scene tokens: {file}")
    if len(rows) != 12146 or any(row["valid"] != "True" for row in rows):
        raise ValueError(f"Incomplete/invalid evaluation: {file}")
    return {row["token"]: row for row in rows}


def build_summary(root):
    baseline_file = next(
        (root / "results/diffusiondrive_agent_eval/2026.09.14.19.36.40").glob("*.csv")
    )
    baseline = read_scores(baseline_file)
    summaries = []
    for name, expected in EXPECTED.items():
        candidates = sorted((root / "results" / name).glob("*/*.csv"))
        if len(candidates) != 1:
            raise ValueError(f"Expected one complete score CSV for {name}")
        file = candidates[0]
        rows = read_scores(file)
        if rows.keys() != baseline.keys():
            raise ValueError(f"Different scene set: {name}")
        score = sum(float(row["score"]) for row in rows.values()) / len(rows) * 100
        if abs(score - expected) > 0.0001:
            raise ValueError(f"Unexpected PDMS for {name}: {score}")
        summaries.append({
            "run": name, "scenes": len(rows), "pdms": score,
            "collision_failures": sum(
                float(row["no_at_fault_collisions"]) < 1 for row in rows.values()
            ),
            "baseline_collision_scenes_fixed": sum(
                float(baseline[token]["no_at_fault_collisions"]) < 1
                and float(row["no_at_fault_collisions"]) == 1
                for token, row in rows.items()
            ),
            "new_collision_scenes": sum(
                float(baseline[token]["no_at_fault_collisions"]) == 1
                and float(row["no_at_fault_collisions"]) < 1
                for token, row in rows.items()
            ),
            "evidence": str(file.relative_to(root)),
        })
    return {
        "scoring": "Mean of valid scene scores x 100; excludes the CSV average row.",
        "scope": "Single archived evaluation per checkpoint, not multi-seed uncertainty.",
        "runs": summaries,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    summary_file = root / "results/archive_summary.json"
    content = json.dumps(build_summary(root), ensure_ascii=False, indent=2) + "\n"
    manifest_file = root / "results/archive_manifest.json"
    if args.write:
        summary_file.write_text(content)
        entries = []
        for file in sorted((root / "results").rglob("*")):
            if not file.is_file() or file.name in ("archive_manifest.json", "cleanup_receipt.json"):
                continue
            entries.append({
                "path": str(file.relative_to(root)),
                "bytes": file.stat().st_size,
                "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
            })
        manifest_file.write_text(json.dumps({"files": entries}, indent=2) + "\n")
    else:
        if summary_file.read_text() != content:
            raise ValueError("Archived summary does not match scene-level scores")
        manifest = json.loads(manifest_file.read_text())
        for entry in manifest["files"]:
            file = root / entry["path"]
            if file.stat().st_size != entry["bytes"]:
                raise ValueError(f"Size mismatch: {file}")
            if hashlib.sha256(file.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError(f"SHA-256 mismatch: {file}")
    print("Verified 7 complete evaluations, 85022 scene outcomes and evidence hashes.")


if __name__ == "__main__":
    main()
