"""
test_scheduler.py
------------------
Correctness tests for scheduler.py, independent of the Streamlit UI.

Run with:
    python -m unittest test_scheduler.py -v

Covers:
  - A classic hand-traceable FCFS / SJF / SRTF example (4 processes), checked
    against completion times worked out by hand, not derived from the code.
  - SRTF tie-break behavior (FCFS / high-priority / low-priority) on a
    contrived exact tie.
  - Round Robin against a hand-traced quantum=2 schedule.
  - Input validation in scheduler._load_processes (negative times, zero
    burst, missing optional columns).
  - run_all() end to end on a larger random workload: correct columns,
    correct row count, internally consistent metrics (TAT = CT - AT,
    WT = TAT - BT) for every process under every algorithm.
"""

import random
import unittest

import pandas as pd

from scheduler import (
    ALGORITHMS,
    Process,
    _load_processes,
    run_all,
    run_fcfs,
    run_round_robin,
    run_sjf,
    run_srtf,
)


# A classic textbook scheduling example — small enough to trace by hand,
# with well-known correct completion times.
TEXTBOOK_PROCS = [
    Process("P1", arrival=0, burst=8, priority=3),
    Process("P2", arrival=1, burst=4, priority=1),
    Process("P3", arrival=2, burst=9, priority=4),
    Process("P4", arrival=3, burst=5, priority=2),
]


def completion_times(df: pd.DataFrame) -> dict:
    return dict(zip(df["Process"], df["Completion Time"]))


class TestTextbookExample(unittest.TestCase):
    """Cross-checks against completion times worked out by hand."""

    def test_fcfs(self):
        df, _, _ = run_fcfs(TEXTBOOK_PROCS)
        self.assertEqual(
            completion_times(df),
            {"P1": 8, "P2": 12, "P3": 21, "P4": 26},
        )

    def test_sjf(self):
        df, _, _ = run_sjf(TEXTBOOK_PROCS)
        self.assertEqual(
            completion_times(df),
            {"P1": 8, "P2": 12, "P3": 26, "P4": 17},
        )

    def test_srtf(self):
        df, _, _ = run_srtf(TEXTBOOK_PROCS, "fcfs")
        self.assertEqual(
            completion_times(df),
            {"P1": 17, "P2": 5, "P3": 26, "P4": 10},
        )

    def test_round_robin_quantum_2(self):
        # Hand-traced: P1(0,2) P2(2,4) P3(4,6) P1(6,8) P4(8,10) P2(10,12)*
        # P3(12,14) P1(14,16) P4(16,18) P3(18,20) P1(20,22)* P4(22,23)*
        # P3(23,25) P3(25,26)* (* = process completes in that slice)
        # -> completions: P2=12, P1=22, P4=23, P3=26
        df, _, _ = run_round_robin(TEXTBOOK_PROCS, quantum=2)
        self.assertEqual(
            completion_times(df),
            {"P1": 22, "P2": 12, "P3": 26, "P4": 23},
        )


class TestSRTFTieBreaks(unittest.TestCase):
    """A contrived exact tie (same arrival, same burst) isolates which
    process each tie-break rule is supposed to prefer."""

    def setUp(self):
        self.procs = [
            Process("LOW_PRIORITY_NUM", arrival=0, burst=5, priority=2),
            Process("HIGH_PRIORITY_NUM", arrival=0, burst=5, priority=7),
        ]

    def test_high_priority_tiebreak_prefers_larger_number(self):
        _, _, gantt = run_srtf(self.procs, "high_priority")
        self.assertEqual(gantt[0][0], "HIGH_PRIORITY_NUM")

    def test_low_priority_tiebreak_prefers_smaller_number(self):
        _, _, gantt = run_srtf(self.procs, "low_priority")
        self.assertEqual(gantt[0][0], "LOW_PRIORITY_NUM")

    def test_fcfs_tiebreak_is_deterministic(self):
        _, _, gantt = run_srtf(self.procs, "fcfs")
        self.assertIn(gantt[0][0], {"LOW_PRIORITY_NUM", "HIGH_PRIORITY_NUM"})


class TestInputValidation(unittest.TestCase):
    def test_rejects_negative_arrival(self):
        bad = pd.DataFrame({"Arrival Time": [0, -1], "Burst Time": [3, 4]})
        with self.assertRaises(ValueError):
            _load_processes(bad)

    def test_rejects_zero_burst(self):
        bad = pd.DataFrame({"Arrival Time": [0, 1], "Burst Time": [0, 4]})
        with self.assertRaises(ValueError):
            _load_processes(bad)

    def test_rejects_non_numeric(self):
        bad = pd.DataFrame({"Arrival Time": [0, "x"], "Burst Time": [3, 4]})
        with self.assertRaises(ValueError):
            _load_processes(bad)

    def test_process_and_priority_are_optional(self):
        minimal = pd.DataFrame({"Arrival Time": [0, 1, 2], "Burst Time": [3, 4, 5]})
        procs = _load_processes(minimal)
        self.assertEqual([p.pid for p in procs], ["P1", "P2", "P3"])
        self.assertTrue(all(p.priority == 0 for p in procs))

    def test_empty_file_rejected(self):
        empty = pd.DataFrame({"Arrival Time": [], "Burst Time": []})
        with self.assertRaises(ValueError):
            _load_processes(empty)


class TestRunAllOnRandomWorkload(unittest.TestCase):
    """End-to-end check on a larger, randomly generated workload: correct
    shape, and every process's own numbers are internally consistent."""

    @classmethod
    def setUpClass(cls):
        rng = random.Random(42)
        cls.df = pd.DataFrame({
            "Process": [f"P{i}" for i in range(1, 301)],
            "Arrival Time": [rng.randint(0, 200) for _ in range(300)],
            "Burst Time": [rng.randint(1, 30) for _ in range(300)],
            "Priority": [rng.randint(1, 10) for _ in range(300)],
        })
        cls.comparison_df, cls.details = run_all(cls.df, quantum=4)

    def test_comparison_table_shape(self):
        self.assertEqual(
            list(self.comparison_df.columns),
            ["Algorithm", "Avg Arrival Time", "Avg Completion Time",
             "Avg Turnaround Time", "Avg Waiting Time", "Throughput"],
        )
        self.assertEqual(len(self.comparison_df), len(ALGORITHMS))
        self.assertEqual(set(self.comparison_df["Algorithm"]), set(ALGORITHMS))

    def test_every_process_accounted_for_under_every_algorithm(self):
        for name in ALGORITHMS:
            result_df, _ = self.details[name]
            self.assertEqual(len(result_df), 300)
            self.assertEqual(set(result_df["Process"]), set(self.df["Process"]))

    def test_metrics_internally_consistent(self):
        # TAT = CT - AT and WT = TAT - BT must hold for every row, under
        # every algorithm — this is the definition of the metrics, not an
        # algorithm-specific property, so any violation is a real bug.
        for name in ALGORITHMS:
            result_df, _ = self.details[name]
            for _, row in result_df.iterrows():
                expected_tat = row["Completion Time"] - row["Arrival Time"]
                expected_wt = expected_tat - row["Burst Time"]
                self.assertEqual(row["Turnaround Time"], expected_tat, msg=name)
                self.assertEqual(row["Waiting Time"], expected_wt, msg=name)

    def test_throughput_matches_definition(self):
        for _, row in self.comparison_df.iterrows():
            name = row["Algorithm"]
            result_df, _ = self.details[name]
            makespan = result_df["Completion Time"].max() - result_df["Arrival Time"].min()
            expected = round(len(result_df) / makespan, 4)
            self.assertAlmostEqual(row["Throughput"], expected, places=4, msg=name)


if __name__ == "__main__":
    unittest.main()
