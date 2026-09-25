"""
scheduler.py
------------
Core CPU scheduling algorithms for the OS lab exercise.

Each algorithm takes a list of Process records (id, arrival_time, burst_time, priority)
and returns:
    - a results DataFrame with per-process CT / TAT / WT
    - a summary dict with averages + throughput
    - a Gantt chart list of (process_id, start_time, end_time) segments

All simulations are event-driven (not per-time-tick), so they comfortably handle
thousands of processes.
"""

import heapq
from collections import deque
from dataclasses import dataclass
import pandas as pd


@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int


def _load_processes(df: pd.DataFrame) -> list[Process]:
    """Normalize an uploaded DataFrame into a list of Process objects."""
    cols = {c.lower().strip(): c for c in df.columns}

    def pick(*names):
        for n in names:
            if n in cols:
                return cols[n]
        raise ValueError(f"Could not find a column for any of {names}. "
                          f"Found columns: {list(df.columns)}")

    pid_col = pick("process", "process id", "processid", "pid", "id")
    at_col = pick("arrival time", "arrival", "at")
    bt_col = pick("burst time", "burst", "bt")
    pr_col = pick("priority", "pr")

    procs = []
    for i, row in df.iterrows():
        pid = str(row[pid_col]) if pd.notna(row[pid_col]) else f"P{i + 1}"
        procs.append(Process(
            pid=pid,
            arrival=int(row[at_col]),
            burst=int(row[bt_col]),
            priority=int(row[pr_col]),
        ))
    return procs


def _summarize(records: list[dict], gantt: list[tuple], total_processes: int) -> tuple[pd.DataFrame, dict]:
    result_df = pd.DataFrame(records).sort_values("Process").reset_index(drop=True)
    avg_arrival = result_df["Arrival Time"].mean()
    avg_completion = result_df["Completion Time"].mean()
    avg_turnaround = result_df["Turnaround Time"].mean()
    avg_waiting = result_df["Waiting Time"].mean()

    makespan = result_df["Completion Time"].max() - result_df["Arrival Time"].min()
    throughput = total_processes / makespan if makespan > 0 else 0.0

    summary = {
        "Avg Arrival Time": round(avg_arrival, 2),
        "Avg Completion Time": round(avg_completion, 2),
        "Avg Turnaround Time": round(avg_turnaround, 2),
        "Avg Waiting Time": round(avg_waiting, 2),
        "Throughput": round(throughput, 4),
    }
    return result_df, summary


# --------------------------------------------------------------------------
# FCFS - First Come First Served (non-preemptive)
# --------------------------------------------------------------------------
def run_fcfs(processes: list[Process]):
    order = sorted(processes, key=lambda p: (p.arrival, p.pid))
    time = 0
    records = []
    gantt = []
    for p in order:
        start = max(time, p.arrival)
        end = start + p.burst
        gantt.append((p.pid, start, end))
        tat = end - p.arrival
        wt = tat - p.burst
        records.append({
            "Process": p.pid, "Arrival Time": p.arrival, "Burst Time": p.burst,
            "Completion Time": end, "Turnaround Time": tat, "Waiting Time": wt,
        })
        time = end
    df, summary = _summarize(records, gantt, len(processes))
    return df, summary, gantt


# --------------------------------------------------------------------------
# SJF - Shortest Job First (non-preemptive), ties broken FCFS
# --------------------------------------------------------------------------
def run_sjf(processes: list[Process]):
    arrivals = sorted(processes, key=lambda p: (p.arrival, p.pid))
    n = len(arrivals)
    ptr = 0
    time = 0
    heap = []  # (burst, arrival, pid, Process)
    records = []
    gantt = []
    completed = 0

    while completed < n:
        while ptr < n and arrivals[ptr].arrival <= time:
            p = arrivals[ptr]
            heapq.heappush(heap, (p.burst, p.arrival, p.pid, p))
            ptr += 1
        if not heap:
            time = arrivals[ptr].arrival
            continue
        burst, arrival, pid, p = heapq.heappop(heap)
        start = time
        end = start + p.burst
        gantt.append((p.pid, start, end))
        tat = end - p.arrival
        wt = tat - p.burst
        records.append({
            "Process": p.pid, "Arrival Time": p.arrival, "Burst Time": p.burst,
            "Completion Time": end, "Turnaround Time": tat, "Waiting Time": wt,
        })
        time = end
        completed += 1

    df, summary = _summarize(records, gantt, n)
    return df, summary, gantt


# --------------------------------------------------------------------------
# SRTF - Shortest Remaining Time First (preemptive), 3 tie-break variants
#   tie_break: "fcfs" | "high_priority" | "low_priority"
#     fcfs           -> ties broken by earlier arrival, then process id
#     high_priority  -> higher priority integer wins
#     low_priority   -> lower priority integer wins
# --------------------------------------------------------------------------
def run_srtf(processes: list[Process], tie_break: str = "fcfs"):
    arrivals = sorted(processes, key=lambda p: (p.arrival, p.pid))
    n = len(arrivals)
    ptr = 0
    time = 0
    remaining = {p.pid: p.burst for p in processes}
    completion = {}
    heap = []  # (remaining_time, tiebreak_key, arrival, pid)
    gantt = []
    completed = 0

    def tie_key(p: Process):
        if tie_break == "high_priority":
            return -p.priority
        if tie_break == "low_priority":
            return p.priority
        return 0  # plain fcfs -> arrival/pid below already sort it

    while completed < n:
        while ptr < n and arrivals[ptr].arrival <= time:
            p = arrivals[ptr]
            heapq.heappush(heap, (remaining[p.pid], tie_key(p), p.arrival, p.pid, p))
            ptr += 1
        if not heap:
            time = arrivals[ptr].arrival
            continue

        rem, tk, arrival, pid, p = heapq.heappop(heap)
        next_arrival = arrivals[ptr].arrival if ptr < n else None
        run_for = rem if next_arrival is None else min(rem, next_arrival - time)
        run_for = max(run_for, 1)  # guard against zero-length slices

        start = time
        end = time + run_for
        gantt.append((p.pid, start, end))
        time = end
        remaining[p.pid] -= run_for

        if remaining[p.pid] <= 0:
            completion[p.pid] = time
            completed += 1
        else:
            heapq.heappush(heap, (remaining[p.pid], tie_key(p), p.arrival, p.pid, p))

    records = []
    for p in processes:
        end = completion[p.pid]
        tat = end - p.arrival
        wt = tat - p.burst
        records.append({
            "Process": p.pid, "Arrival Time": p.arrival, "Burst Time": p.burst,
            "Completion Time": end, "Turnaround Time": tat, "Waiting Time": wt,
        })

    df, summary = _summarize(records, gantt, n)
    return df, summary, gantt


# --------------------------------------------------------------------------
# Round Robin (preemptive, fixed time quantum)
# --------------------------------------------------------------------------
def run_round_robin(processes: list[Process], quantum: int):
    arrivals = sorted(processes, key=lambda p: (p.arrival, p.pid))
    n = len(arrivals)
    ptr = 0
    time = 0
    remaining = {p.pid: p.burst for p in processes}
    completion = {}
    queue = deque()
    gantt = []
    completed = 0

    # seed: jump to first arrival, load all processes arriving at that instant
    if ptr < n:
        time = arrivals[ptr].arrival
    while ptr < n and arrivals[ptr].arrival <= time:
        queue.append(arrivals[ptr])
        ptr += 1

    while completed < n:
        if not queue:
            if ptr < n:
                time = arrivals[ptr].arrival
                while ptr < n and arrivals[ptr].arrival <= time:
                    queue.append(arrivals[ptr])
                    ptr += 1
            continue

        p = queue.popleft()
        run_for = min(quantum, remaining[p.pid])
        start = time
        end = time + run_for
        gantt.append((p.pid, start, end))
        time = end
        remaining[p.pid] -= run_for

        # enqueue anyone who arrived during this slice, in arrival/id order
        while ptr < n and arrivals[ptr].arrival <= time:
            queue.append(arrivals[ptr])
            ptr += 1

        if remaining[p.pid] <= 0:
            completion[p.pid] = time
            completed += 1
        else:
            queue.append(p)

    records = []
    for p in processes:
        end = completion[p.pid]
        tat = end - p.arrival
        wt = tat - p.burst
        records.append({
            "Process": p.pid, "Arrival Time": p.arrival, "Burst Time": p.burst,
            "Completion Time": end, "Turnaround Time": tat, "Waiting Time": wt,
        })

    df, summary = _summarize(records, gantt, n)
    return df, summary, gantt


# --------------------------------------------------------------------------
# Orchestration: run every algorithm and build the comparison table
# --------------------------------------------------------------------------
ALGORITHMS = [
    "FCFS",
    "SJF",
    "SRTF (FCFS tie-break)",
    "SRTF (High Priority tie-break)",
    "SRTF (Low Priority tie-break)",
    "Round Robin",
]


def run_all(df: pd.DataFrame, quantum: int = 4):
    """Run every algorithm against the uploaded DataFrame.

    Returns:
        comparison_df: one row per algorithm with the averaged metrics
        details: dict[algorithm_name] -> (result_df, gantt_segments)
    """
    processes = _load_processes(df)

    runs = {
        "FCFS": run_fcfs(processes),
        "SJF": run_sjf(processes),
        "SRTF (FCFS tie-break)": run_srtf(processes, "fcfs"),
        "SRTF (High Priority tie-break)": run_srtf(processes, "high_priority"),
        "SRTF (Low Priority tie-break)": run_srtf(processes, "low_priority"),
        "Round Robin": run_round_robin(processes, quantum),
    }

    rows = []
    details = {}
    for name in ALGORITHMS:
        result_df, summary, gantt = runs[name]
        rows.append({"Algorithm": name, **summary})
        details[name] = (result_df, gantt)

    comparison_df = pd.DataFrame(rows)
    return comparison_df, details
