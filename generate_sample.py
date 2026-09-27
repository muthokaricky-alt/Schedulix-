"""
generate_sample.py
-------------------
Generates a randomized set of processes (Process, Arrival Time, Burst Time, Priority)
and writes them to sample_data.xlsx, as required by the lab exercise.

Usage:
    python generate_sample.py                # 1500 processes -> sample_data.xlsx
    python generate_sample.py --n 500 --out my_data.xlsx --seed 42
"""

import argparse
import random
import pandas as pd


def generate(n: int, seed: int | None, max_arrival: int, max_burst: int, max_priority: int) -> pd.DataFrame:
    rng = random.Random(seed)
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "Process": f"P{i}",
            "Arrival Time": rng.randint(0, max_arrival),
            "Burst Time": rng.randint(1, max_burst),   # burst time must be >= 1
            "Priority": rng.randint(1, max_priority),
        })
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="Generate random CPU scheduling process data.")
    parser.add_argument("--n", type=int, default=1500, help="Number of processes (default: 1500)")
    parser.add_argument("--out", type=str, default="sample_data.xlsx", help="Output .xlsx path")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--max-arrival", type=int, default=1000, help="Max arrival time")
    parser.add_argument("--max-burst", type=int, default=50, help="Max burst time")
    parser.add_argument("--max-priority", type=int, default=10, help="Max priority value")
    args = parser.parse_args()

    df = generate(args.n, args.seed, args.max_arrival, args.max_burst, args.max_priority)
    df.to_excel(args.out, index=False)
    print(f"Wrote {len(df):,} processes to {args.out}")


if __name__ == "__main__":
    main()
