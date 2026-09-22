# ⏱️ Schedulix — CPU Scheduling Simulator

A Streamlit web app for a 2nd-year OS lab exercise: upload an Excel file of randomly
generated processes and compare **FCFS**, **SJF**, **SRTF** (3 tie-break rules), and
**Round Robin**, with a Gantt chart and comparison table for each.

Repo: [github.com/muthokaricky-alt/Schedulix-](https://github.com/muthokaricky-alt/Schedulix-)

## Setup

```bash
git clone https://github.com/muthokaricky-alt/Schedulix-.git
cd Schedulix-
pip install -r requirements.txt
```

## 1. Generate the process data

The lab requires 1500 randomly generated processes in Excel.

```bash
python generate_sample.py --n 1500 --seed 7
```

This writes `sample_data.xlsx` with columns `Process`, `Arrival Time`, `Burst Time`,
`Priority`. Run `python generate_sample.py --help` to change the count, ranges, or
output path.

## 2. Run the app

```bash
streamlit run app.py
```

Then, in the browser tab that opens:

1. Upload `sample_data.xlsx` (or any file with the same columns) in the sidebar.
2. Set the Round Robin time quantum (default 4).
3. Click **Run Simulation**.

You'll get:

- Quick stats on the uploaded workload (process count, arrival range, burst time).
- A **comparison table** — average arrival, completion, turnaround, and waiting time,
  plus throughput, per algorithm — with the best result in each column highlighted.
- A callout naming the algorithm with the lowest average waiting time for this file.
- A **Gantt chart per algorithm** (tabbed), shown for the first N processes
  (adjustable slider — full 1500-process Gantt charts aren't human-readable, so
  charts render a legible subset while the comparison table still reflects the
  whole file).
- CSV downloads for the comparison table and for each algorithm's per-process results.

## Algorithms implemented

| Algorithm | Type | Tie-break |
|---|---|---|
| FCFS | Non-preemptive | Arrival time, then Process ID |
| SJF | Non-preemptive | Shortest burst; ties broken FCFS |
| SRTF (FCFS tie-break) | Preemptive | Shortest remaining time; ties broken FCFS |
| SRTF (High Priority tie-break) | Preemptive | Shortest remaining time; ties broken by **higher** priority integer |
| SRTF (Low Priority tie-break) | Preemptive | Shortest remaining time; ties broken by **lower** priority integer |
| Round Robin | Preemptive | Fixed time quantum, FIFO ready queue |

**Metrics** (n = number of processes):

- `Completion Time (CT)` — when a process finishes
- `Turnaround Time (TAT) = CT − Arrival Time`
- `Waiting Time (WT) = TAT − Burst Time`
- `Throughput = n / (max Completion Time − min Arrival Time)`

## Files

```
Schedulix/
├── app.py              # Streamlit UI ("Schedulix — CPU Scheduling Simulator")
├── scheduler.py         # Scheduling algorithms (event-driven, O(n log n))
├── generate_sample.py   # Random process generator (Excel output)
├── requirements.txt
├── sample_data.xlsx     # 1500 pre-generated processes (seed=7)
├── .gitignore
└── README.md
```

## Notes on the simulation approach

All algorithms are **event-driven** rather than simulated tick-by-tick, so 1500+
processes run in well under a second. Preemptive algorithms (SRTF, Round Robin) only
re-evaluate scheduling decisions at arrivals and completions, using a heap (SRTF) or
FIFO queue (Round Robin) — not a per-time-unit loop.

## Pushing to GitHub

If the repo above is already created and empty:

```bash
git init
git add .
git commit -m "Initial commit: Schedulix CPU scheduling simulator"
git branch -M main
git remote add origin https://github.com/muthokaricky-alt/Schedulix-.git
git push -u origin main
```
