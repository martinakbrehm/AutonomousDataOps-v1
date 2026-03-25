"""Simple demo script that reads a small CSV, performs basic cleaning,
and writes a cleaned CSV. This avoids heavy dependencies so it runs
with only the Python standard library.

Run: python -m examples.run_demo
"""
from pathlib import Path
import csv


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "sample_data.csv"
OUTPUT = ROOT / "sample_data.cleaned.csv"


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def clean_rows(rows):
    # simple cleaning: drop rows where all fields are empty
    cleaned = []
    for r in rows:
        if any((v or "").strip() for v in r.values()):
            cleaned.append({k: (v or "").strip() for k, v in r.items()})
    return cleaned


def write_rows(path: Path, rows):
    if not rows:
        print("No rows to write.")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows):
    print(f"Read {len(rows)} rows")
    if rows:
        print("Sample row:")
        sample = rows[0]
        for k, v in sample.items():
            print(f"  {k}: {v}")


def main():
    print("Running demo: examples/run_demo.py")
    if not INPUT.exists():
        print(f"Missing sample CSV at {INPUT}")
        return
    rows = read_rows(INPUT)
    summarize(rows)
    cleaned = clean_rows(rows)
    print(f"After cleaning: {len(cleaned)} rows")
    write_rows(OUTPUT, cleaned)
    print(f"Cleaned CSV written to: {OUTPUT}")


if __name__ == "__main__":
    main()
