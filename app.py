"""
app.py
------
Streamlit front-end for Schedulix — CPU Scheduling Simulator.

Run with:
    streamlit run app.py

Theming note: the app uses a single, fixed light appearance with one accent
color (set in ACCENT below) applied consistently across native widgets and
our own markup, rather than offering an in-app light/dark switch — Streamlit
disables its own Settings → Theme option once any [theme] value is
customized, so a partial toggle isn't available without giving up the
custom accent entirely.
"""

import io
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import streamlit as st

from scheduler import run_all, export_workbook, ALGORITHMS

st.set_page_config(page_title="Schedulix", page_icon=None, layout="wide")

# --------------------------------------------------------------------------
# Theme detection — only needed for the matplotlib charts below, which are
# plain images and can't read Streamlit's live CSS variables the way our
# markup can. Native widgets don't need this; they theme themselves.
# --------------------------------------------------------------------------
try:
    IS_DARK = st.context.theme.type == "dark"
except Exception:
    IS_DARK = False

ACCENT = "#2dd4bf" if IS_DARK else "#0d9488"
ACCENT_TINT = "rgba(45, 212, 191, 0.16)" if IS_DARK else "rgba(13, 148, 136, 0.10)"
MPL_TEXT, MPL_GRID = ("#c9cdd3", "#33383f") if IS_DARK else ("#3f4650", "#dde1e6")

# --------------------------------------------------------------------------
# Light-touch styling — sizing and structure only. Color for our own markup
# (the logo, table highlights, callout, charts) comes from the ACCENT
# constant above, computed once in Python — not from Streamlit's internal
# CSS variables, which aren't a stable public API and can silently disagree
# with what native widgets (like the primary button) actually render.
# --------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    .stApp {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}

    .block-container {{ padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1120px; }}

    h1, h2, h3 {{ letter-spacing: -0.02em; font-weight: 600; }}
    h3 {{ margin-top: 2.75rem; margin-bottom: 0.8rem; }}

    .brand {{ font-size: 2rem; font-weight: 700; letter-spacing: -0.03em; }}
    .accent-text {{ color: {ACCENT}; }}
    .tagline {{ font-size: 0.95rem; opacity: 0.55; margin-top: 0.1rem; }}

    hr {{ opacity: 0.15; }}

    /* Metrics read as a clean spec row — thin vertical rules between
       columns, no boxed cards — instead of four separate bordered tiles. */
    div[data-testid="column"] div[data-testid="stMetric"] {{
        background: transparent;
        border: none;
        border-left: 1px solid rgba(128,128,128,0.18);
        border-radius: 0;
        padding: 0 1.3rem;
    }}
    div[data-testid="column"]:first-child div[data-testid="stMetric"] {{
        border-left: none;
        padding-left: 0;
    }}
    div[data-testid="stMetricLabel"] {{
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.7rem;
        opacity: 0.55;
    }}

    /* The control bar reads as a section framed by hairlines, not a boxed
       card — consistent with the rest of the page's whitespace-led layout. */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border: none !important;
        border-top: 1px solid rgba(128,128,128,0.18) !important;
        border-bottom: 1px solid rgba(128,128,128,0.18) !important;
        border-radius: 0 !important;
        padding: 1.3rem 0;
    }}

    /* Primary CTA gets a single, deliberate pill treatment — used once,
       not on every button, so it still reads as a considered choice. */
    div[data-testid="stButton"] button[kind="primary"] {{
        border-radius: 980px;
        font-weight: 600;
        padding: 0.5rem 1.4rem;
        transition: transform 0.12s ease, filter 0.15s ease;
    }}
    div[data-testid="stButton"] button[kind="primary"]:hover {{ filter: brightness(0.95); }}
    div[data-testid="stButton"] button[kind="primary"]:active {{ transform: scale(0.97); }}

    /* Tabs read by weight/opacity rather than a heavy underline bar — the
       active algorithm stands out, the rest recede instead of competing. */
    button[data-baseweb="tab"] {{
        font-weight: 500;
        opacity: 0.55;
        transition: opacity 0.15s ease;
    }}
    button[data-baseweb="tab"]:hover {{ opacity: 0.85; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ opacity: 1; font-weight: 600; }}

    /* Expander headers get the same quiet hover cue as tabs, for the same
       reason — a considered detail, not a decorative one. */
    div[data-testid="stExpander"] summary {{
        transition: opacity 0.15s ease;
    }}
    div[data-testid="stExpander"] summary:hover {{ opacity: 0.7; }}

    /* Links (sidebar GitHub link, footer) get an animated underline instead
       of the browser default — a small, deliberate touch rather than none. */
    a {{
        color: {ACCENT};
        text-decoration: none;
        border-bottom: 1px solid transparent;
        transition: border-color 0.15s ease;
    }}
    a:hover {{ border-bottom-color: {ACCENT}; }}

    /* Keyboard-focus ring, visible only for keyboard navigation (not mouse
       clicks) — accessibility that doesn't add visual noise for most users. */
    button:focus-visible, a:focus-visible, input:focus-visible {{
        outline: 2px solid {ACCENT};
        outline-offset: 2px;
    }}

    /* Selection and scrollbars carry the accent too, so the brand shows up
       in incidental interactions, not just the obvious ones. */
    ::selection {{ background: {ACCENT_TINT}; }}
    * {{ scrollbar-width: thin; scrollbar-color: rgba(128,128,128,0.35) transparent; }}
    ::-webkit-scrollbar {{ height: 8px; width: 8px; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(128,128,128,0.35); border-radius: 4px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}

    .callout {{
        border-top: 1px solid rgba(128,128,128,0.18);
        border-bottom: 1px solid rgba(128,128,128,0.18);
        padding: 1.1rem 0;
        margin: 1.6rem 0;
        font-size: 1rem;
    }}
    .callout b {{ color: {ACCENT}; font-weight: 600; }}

    .schedulix-footer {{
        opacity: 0.5;
        font-size: 0.8rem;
        letter-spacing: 0.02em;
        text-align: center;
        margin-top: 3rem;
        padding-top: 1.2rem;
        border-top: 1px solid rgba(128,128,128,0.18);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="brand">Schedu<span class="accent-text">lix</span></div>',
            unsafe_allow_html=True)
st.markdown('<div class="tagline">CPU Scheduling Simulator</div>', unsafe_allow_html=True)
st.divider()

st.markdown(
    "Upload a process table and see which algorithm wins on waiting time, "
    "turnaround time, and throughput."
)

# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("**Upload data**")
    uploaded = st.file_uploader("Excel file (.xlsx)", type=["xlsx"], label_visibility="collapsed")

    st.divider()
    with st.expander("Expected file format"):
        st.markdown(
            "- `Process` — optional, auto-generated as P1, P2, ... if missing\n"
            "- `Arrival Time`\n"
            "- `Burst Time`\n"
            "- `Priority` — optional, defaults to 0\n\n"
            "Column names are case-insensitive; order doesn't matter."
        )
        st.caption("No data yet? Run `python generate_sample.py` to make one.")

    st.divider()
    st.caption("[View on GitHub](https://github.com/muthokaricky-alt/Schedulix-)")

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _thousands(ax, axis="x"):
    fmt = FuncFormatter(lambda v, _: f"{v:,.0f}")
    (ax.xaxis if axis == "x" else ax.yaxis).set_major_formatter(fmt)


ALGO_BLURBS = {
    "FCFS": (
        "Processes run in the order they arrive, uninterrupted until completion. "
        "Simple and fair by arrival order, but one long process can make everything "
        "behind it wait — the convoy effect."
    ),
    "SJF": (
        "At every decision point, whichever ready process has the shortest burst "
        "time runs next, uninterrupted once started. Minimizes average waiting time "
        "in theory, but can starve a long process indefinitely if shorter jobs keep "
        "arriving ahead of it."
    ),
    "SRTF (FCFS tie-break)": (
        "The preemptive version of SJF: whichever ready process has the least "
        "remaining time runs, and a new arrival can interrupt the current one if "
        "it's shorter. When two processes tie on remaining time, the one that "
        "arrived first runs first."
    ),
    "SRTF (High Priority tie-break)": (
        "Same preemptive shortest-remaining-time logic as SRTF, but when two "
        "processes tie on remaining time, the one with the higher priority number "
        "runs first."
    ),
    "SRTF (Low Priority tie-break)": (
        "Same preemptive shortest-remaining-time logic as SRTF, but when two "
        "processes tie on remaining time, the one with the lower priority number "
        "runs first."
    ),
    "Round Robin": (
        "Each process gets a fixed time slice (the quantum); if it isn't finished, "
        "it goes to the back of the queue. Guarantees every process makes regular "
        "progress, at the cost of more context switches and — under heavy load, as "
        "with quantum 4 across 1500 processes — a much longer turnaround per process."
    ),
}


def draw_gantt(gantt_segments, pid_order, title):
    """pid_order: list of process IDs in the order they should appear
    top-to-bottom (earliest arrival first), not lexicographic ID order —
    ID has no relationship to execution time, so sorting by ID scatters
    a handful of processes across the entire simulated timeline instead
    of showing a readable, contiguous slice of it."""
    pids_to_show = set(pid_order)
    segments = [seg for seg in gantt_segments if seg[0] in pids_to_show]
    if not segments:
        st.info("No segments to display for the selected processes in this window.")
        return

    y_pos = {pid: i for i, pid in enumerate(pid_order)}
    cmap = plt.get_cmap("tab20")
    color_for = {pid: cmap(i % 20) for i, pid in enumerate(pid_order)}

    fig, ax = plt.subplots(figsize=(12, max(2, 0.42 * len(pid_order))))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    # A thin gap in the page background color between adjacent segments of
    # the same process reads as clean separation without resorting to
    # rounded "pill" bars, which get noisy once Round Robin produces many
    # short slices per process.
    gap_color = "#ffffff" if not IS_DARK else "#0e1117"
    for pid, start, end in segments:
        ax.barh(y_pos[pid], end - start, left=start, height=0.62,
                color=color_for[pid], edgecolor=gap_color, linewidth=0.8)
        if end - start > 0:
            ax.text((start + end) / 2, y_pos[pid], f"{start}-{end}",
                    ha="center", va="center", fontsize=7, color=MPL_TEXT)

    ax.set_yticks(list(y_pos.values()))
    ax.set_yticklabels(list(y_pos.keys()), color=MPL_TEXT, fontsize=9)
    ax.invert_yaxis()

    # Zoom to the window this algorithm actually uses for these processes,
    # rather than a fixed range shared across tabs — some algorithms finish
    # the same processes far sooner (or, for Round Robin under heavy load,
    # far later) than others, and a shared axis would waste most of it.
    starts = [s for _, s, _ in segments]
    ends = [e for _, _, e in segments]
    pad = max(1, (max(ends) - min(starts)) * 0.03)
    ax.set_xlim(min(starts) - pad, max(ends) + pad)

    ax.set_xlabel("Time", color=MPL_TEXT, fontsize=9)
    ax.set_title(title, fontsize=11, fontweight="600", color=MPL_TEXT, loc="left")
    ax.tick_params(colors=MPL_TEXT, labelsize=8)
    ax.grid(axis="x", linestyle="-", alpha=0.5, color=MPL_GRID)
    _thousands(ax)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def draw_comparison_bar(comparison_df: pd.DataFrame):
    ordered = comparison_df.sort_values("Avg Waiting Time")
    fig, ax = plt.subplots(figsize=(9, max(1.8, 0.5 * len(ordered))))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    colors = [ACCENT if i == 0 else MPL_GRID for i in range(len(ordered))]
    bars = ax.barh(ordered["Algorithm"], ordered["Avg Waiting Time"], color=colors, height=0.55)
    max_val = ordered["Avg Waiting Time"].max()
    for bar, val in zip(bars, ordered["Avg Waiting Time"]):
        ax.text(val + max_val * 0.015, bar.get_y() + bar.get_height() / 2, f"{val:,.1f}",
                va="center", fontsize=8.5, color=MPL_TEXT)

    ax.invert_yaxis()
    ax.set_xlim(0, max_val * 1.18)
    ax.set_xlabel("Average waiting time (lower is better)", color=MPL_TEXT, fontsize=9)
    ax.tick_params(colors=MPL_TEXT, labelsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(axis="x", linestyle="-", alpha=0.5, color=MPL_GRID)
    _thousands(ax)
    fig.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def style_comparison(df: pd.DataFrame):
    fmt = {
        "Avg Arrival Time": "{:.2f}",
        "Avg Completion Time": "{:.2f}",
        "Avg Turnaround Time": "{:.2f}",
        "Avg Waiting Time": "{:.2f}",
        "Throughput": "{:.4f}",
    }
    highlight_props = f"background-color: {ACCENT_TINT}; color: {ACCENT}; font-weight: 600;"
    styler = df.style.format(fmt)
    styler = styler.highlight_min(
        subset=["Avg Waiting Time", "Avg Turnaround Time", "Avg Completion Time"],
        props=highlight_props,
    )
    styler = styler.highlight_max(subset=["Throughput"], props=highlight_props)
    return styler


# --------------------------------------------------------------------------
# Main flow
# --------------------------------------------------------------------------
if uploaded is not None:
    try:
        raw_df = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Could not read the Excel file: {e}")
        st.stop()

    st.subheader("Uploaded data")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Processes", f"{len(raw_df):,}")
    at_col = next((c for c in raw_df.columns if c.strip().lower() in ("arrival time", "arrival", "at")), None)
    bt_col = next((c for c in raw_df.columns if c.strip().lower() in ("burst time", "burst", "bt")), None)
    if at_col is not None:
        c2.metric("Arrival range", f"{int(raw_df[at_col].min())}–{int(raw_df[at_col].max())}")
    if bt_col is not None:
        c3.metric("Avg burst time", f"{raw_df[bt_col].mean():.1f}")
        c4.metric("Total burst time", f"{int(raw_df[bt_col].sum()):,}")

    with st.expander("Preview first 20 rows"):
        st.dataframe(raw_df.head(20), width="stretch", hide_index=True)

    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 3, 2])
        with c1:
            quantum = st.number_input("Round Robin quantum", min_value=1, value=4, step=1)
        with c2:
            gantt_count = st.slider("Gantt chart width (processes shown)", min_value=5, max_value=50, value=20)
        with c3:
            st.write("")
            run_clicked = st.button("Run simulation", type="primary", width="stretch")

    if run_clicked:
        with st.spinner(f"Simulating {len(raw_df):,} processes across {len(ALGORITHMS)} algorithms..."):
            try:
                comparison_df, details = run_all(raw_df, quantum=int(quantum))
            except Exception as e:
                st.error(f"Simulation failed: {e}")
                st.stop()

        st.session_state["comparison_df"] = comparison_df
        st.session_state["details"] = details
        st.session_state["raw_df"] = raw_df

    if "comparison_df" in st.session_state:
        comparison_df = st.session_state["comparison_df"]
        details = st.session_state["details"]

        best_row = comparison_df.loc[comparison_df["Avg Waiting Time"].idxmin()]
        st.markdown(
            f"""
            <div class="callout">
            <b>{best_row['Algorithm']}</b> has the lowest average waiting time
            ({best_row['Avg Waiting Time']:.2f}) for this workload — turnaround
            {best_row['Avg Turnaround Time']:.2f}, throughput {best_row['Throughput']:.4f}.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Algorithm comparison")
        st.dataframe(style_comparison(comparison_df), width="stretch", hide_index=True)
        st.caption("Highlighted = best result in that column (lowest time / highest throughput).")

        draw_comparison_bar(comparison_df)

        dl1, dl2 = st.columns(2)
        with dl1:
            csv_buf = io.StringIO()
            comparison_df.to_csv(csv_buf, index=False)
            st.download_button(
                "Download comparison table (CSV)",
                data=csv_buf.getvalue(),
                file_name="scheduling_comparison.csv",
                mime="text/csv",
                width="stretch",
            )
        with dl2:
            workbook_bytes = export_workbook(comparison_df, details)
            st.download_button(
                "Download full results (Excel, all algorithms)",
                data=workbook_bytes,
                file_name="scheduling_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )

        st.subheader("Gantt charts")
        st.caption(
            "Full workloads (1000+ processes) aren't readable as a single Gantt chart, "
            "so charts show the first N processes to arrive — adjust the width above. "
            "Each tab auto-zooms to the time window those processes actually use under "
            "that algorithm; the comparison table still reflects the entire file. A "
            "sparse, spread-out chart under SJF/SRTF or Round Robin is real scheduling "
            "behavior — shorter jobs cutting in line (starvation) or the constant "
            "context-switching of round-robin at this scale — not a rendering issue."
        )

        fcfs_results = details["FCFS"][0]
        pid_order = (
            fcfs_results.sort_values(["Arrival Time", "Process"])["Process"]
            .tolist()[:gantt_count]
        )

        tabs = st.tabs(ALGORITHMS)
        for tab, algo_name in zip(tabs, ALGORITHMS):
            with tab:
                result_df, gantt = details[algo_name]
                st.caption(ALGO_BLURBS.get(algo_name, ""))
                draw_gantt(gantt, pid_order, f"{algo_name} — first {len(pid_order)} processes to arrive")
                with st.expander("Per-process results"):
                    st.dataframe(result_df, width="stretch", hide_index=True)
                    row_csv = io.StringIO()
                    result_df.to_csv(row_csv, index=False)
                    st.download_button(
                        f"Download {algo_name} results (CSV)",
                        data=row_csv.getvalue(),
                        file_name=f"{algo_name.split(' ')[0].lower()}_results.csv",
                        mime="text/csv",
                        key=f"dl_{algo_name}",
                    )
else:
    st.subheader("Get started")
    ex1, ex2 = st.columns(2)
    with ex1:
        st.markdown("**Expected columns**")
        st.markdown(
            "- `Process` — optional, auto-generated as P1, P2, ... if missing\n"
            "- `Arrival Time`\n"
            "- `Burst Time`\n"
            "- `Priority` — optional, defaults to 0\n"
        )
    with ex2:
        st.markdown("**No data yet?**")
        st.code("python generate_sample.py --n 1500 --seed 7", language="bash")
        st.caption("Generates sample_data.xlsx with 1500 randomized processes.")

st.markdown('<div class="schedulix-footer">Schedulix ©</div>', unsafe_allow_html=True)