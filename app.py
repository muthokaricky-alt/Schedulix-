"""
app.py
------
Streamlit front-end for Schedulix — CPU Scheduling Simulator.

Run with:
    streamlit run app.py
"""

import io
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from scheduler import run_all, ALGORITHMS

APP_TITLE = "Schedulix — CPU Scheduling Simulator"

st.set_page_config(page_title="Schedulix", page_icon="⏱️", layout="wide")

# --------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }

    .schedulix-hero {
        background: linear-gradient(120deg, #4338ca 0%, #7c3aed 55%, #c026d3 100%);
        padding: 1.75rem 2rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .schedulix-hero h1 {
        color: white;
        font-size: 2.1rem;
        margin: 0 0 0.3rem 0;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    .schedulix-hero p {
        color: rgba(255,255,255,0.9);
        margin: 0;
        font-size: 1.0rem;
    }
    .schedulix-badge {
        display: inline-block;
        background: rgba(255,255,255,0.18);
        border: 1px solid rgba(255,255,255,0.35);
        border-radius: 999px;
        padding: 0.15rem 0.7rem;
        font-size: 0.78rem;
        margin-top: 0.7rem;
        margin-right: 0.4rem;
    }

    div[data-testid="stMetric"] {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.2);
        border-radius: 10px;
        padding: 0.8rem 1rem;
    }

    .winner-box {
        background: rgba(34,197,94,0.10);
        border: 1px solid rgba(34,197,94,0.35);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 1rem;
    }

    footer, #MainMenu { visibility: hidden; }
    .schedulix-footer {
        text-align: center;
        color: gray;
        font-size: 0.82rem;
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(128,128,128,0.2);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Hero header
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="schedulix-hero">
        <h1>⏱️ Schedulix</h1>
        <p>CPU Scheduling Simulator — upload a process table and compare FCFS, SJF,
        SRTF (3 tie-break rules), and Round Robin side by side, with Gantt charts.</p>
        <span class="schedulix-badge">FCFS</span>
        <span class="schedulix-badge">SJF</span>
        <span class="schedulix-badge">SRTF × 3</span>
        <span class="schedulix-badge">Round Robin</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Sidebar: inputs
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⏱️ Schedulix")
    st.caption("CPU Scheduling Simulator")
    st.divider()

    st.markdown("**1. Upload data**")
    uploaded = st.file_uploader("Excel file (.xlsx)", type=["xlsx"], label_visibility="collapsed")

    st.markdown("**2. Round Robin quantum**")
    quantum = st.number_input("Time quantum", min_value=1, value=4, step=1, label_visibility="collapsed")

    run_clicked = st.button("▶  Run Simulation", type="primary", use_container_width=True)

    st.divider()
    st.markdown("**Gantt chart view**")
    gantt_count = st.slider(
        "Processes to show (by Process ID order)",
        min_value=5, max_value=50, value=20,
    )

    st.divider()
    with st.expander("ℹ️ Expected file format"):
        st.markdown(
            "- `Process` *(optional — auto-generated as P1, P2, ... if missing)*\n"
            "- `Arrival Time`\n"
            "- `Burst Time`\n"
            "- `Priority`\n\n"
            "Column names are case-insensitive; order doesn't matter."
        )
        st.caption("No data handy? Run `python generate_sample.py` to make one.")

    st.divider()
    st.caption("[View on GitHub](https://github.com/muthokaricky-alt/Schedulix-)")

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def draw_gantt(gantt_segments, pids_to_show, title):
    segments = [seg for seg in gantt_segments if seg[0] in pids_to_show]
    if not segments:
        st.info("No segments to display for the selected processes in this window.")
        return

    pids_ordered = sorted(pids_to_show, key=lambda x: (len(x), x))
    y_pos = {pid: i for i, pid in enumerate(pids_ordered)}

    cmap = plt.get_cmap("tab20")
    color_for = {pid: cmap(i % 20) for i, pid in enumerate(pids_ordered)}

    fig, ax = plt.subplots(figsize=(12, max(2, 0.4 * len(pids_ordered))))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    for pid, start, end in segments:
        ax.barh(y_pos[pid], end - start, left=start, height=0.6,
                color=color_for[pid], edgecolor="black", linewidth=0.6)
        if end - start > 0:
            ax.text((start + end) / 2, y_pos[pid], f"{start}-{end}",
                    ha="center", va="center", fontsize=7)

    ax.set_yticks(list(y_pos.values()))
    ax.set_yticklabels(list(y_pos.keys()))
    ax.set_xlabel("Time")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def style_comparison(df: pd.DataFrame):
    fmt = {
        "Avg Arrival Time": "{:.2f}",
        "Avg Completion Time": "{:.2f}",
        "Avg Turnaround Time": "{:.2f}",
        "Avg Waiting Time": "{:.2f}",
        "Throughput": "{:.4f}",
    }
    styler = df.style.format(fmt)
    styler = styler.highlight_min(
        subset=["Avg Waiting Time", "Avg Turnaround Time", "Avg Completion Time"],
        color="#166534", props="color: #dcfce7; font-weight: 700; background-color: #166534;",
    )
    styler = styler.highlight_max(
        subset=["Throughput"],
        color="#166534", props="color: #dcfce7; font-weight: 700; background-color: #166534;",
    )
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

    st.subheader("📄 Uploaded data")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Processes", f"{len(raw_df):,}")
    at_col = next((c for c in raw_df.columns if c.strip().lower() in ("arrival time", "arrival", "at")), None)
    bt_col = next((c for c in raw_df.columns if c.strip().lower() in ("burst time", "burst", "bt")), None)
    if at_col is not None:
        c2.metric("Arrival range", f"{int(raw_df[at_col].min())}–{int(raw_df[at_col].max())}")
    if bt_col is not None:
        c3.metric("Avg burst time", f"{raw_df[bt_col].mean():.1f}")
        c4.metric("Total burst time", f"{int(raw_df[bt_col].sum()):,}")

    with st.expander("Preview first 20 rows", expanded=False):
        st.dataframe(raw_df.head(20), use_container_width=True)

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
        st.toast("Simulation complete", icon="✅")

    if "comparison_df" in st.session_state:
        comparison_df = st.session_state["comparison_df"]
        details = st.session_state["details"]

        best_row = comparison_df.loc[comparison_df["Avg Waiting Time"].idxmin()]
        st.markdown(
            f"""
            <div class="winner-box">
            🏆 <b>{best_row['Algorithm']}</b> has the lowest average waiting time
            (<b>{best_row['Avg Waiting Time']:.2f}</b>) across this workload —
            turnaround {best_row['Avg Turnaround Time']:.2f}, throughput {best_row['Throughput']:.4f}.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("📊 Algorithm comparison")
        st.dataframe(style_comparison(comparison_df), use_container_width=True, hide_index=True)
        st.caption("Green highlight = best result in that column (lowest time / highest throughput).")

        csv_buf = io.StringIO()
        comparison_df.to_csv(csv_buf, index=False)
        st.download_button(
            "⬇ Download comparison table (CSV)",
            data=csv_buf.getvalue(),
            file_name="scheduling_comparison.csv",
            mime="text/csv",
        )

        st.subheader("📈 Gantt charts")
        st.caption(
            "Full workloads (1000+ processes) are unreadable as a single Gantt chart, "
            "so charts render only the first N processes (by Process ID) — adjust the "
            "count in the sidebar. The comparison table above still reflects the entire file."
        )

        all_pids = sorted(details["FCFS"][0]["Process"].tolist(), key=lambda x: (len(x), x))
        pids_to_show = set(all_pids[:gantt_count])

        tabs = st.tabs(ALGORITHMS)
        for tab, algo_name in zip(tabs, ALGORITHMS):
            with tab:
                result_df, gantt = details[algo_name]
                draw_gantt(gantt, pids_to_show, f"{algo_name} — first {len(pids_to_show)} processes")
                with st.expander("Per-process results for this algorithm"):
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                    row_csv = io.StringIO()
                    result_df.to_csv(row_csv, index=False)
                    st.download_button(
                        f"⬇ Download {algo_name} results (CSV)",
                        data=row_csv.getvalue(),
                        file_name=f"{algo_name.split(' ')[0].lower()}_results.csv",
                        mime="text/csv",
                        key=f"dl_{algo_name}",
                    )
else:
    st.info("⬅ Upload an Excel file in the sidebar to get started.")
    ex1, ex2 = st.columns([1, 1])
    with ex1:
        st.markdown("**Expected columns** (case-insensitive, order doesn't matter)")
        st.markdown(
            "- `Process` *(optional — auto-generated as P1, P2, ... if missing)*\n"
            "- `Arrival Time`\n"
            "- `Burst Time`\n"
            "- `Priority`\n"
        )
    with ex2:
        st.markdown("**No data yet?**")
        st.code("python generate_sample.py --n 1500 --seed 7", language="bash")
        st.caption("Generates `sample_data.xlsx` with 1500 randomized processes.")

st.markdown(
    '<div class="schedulix-footer">Schedulix · '
    '<a href="https://github.com/muthokaricky-alt/Schedulix-" target="_blank">github.com/muthokaricky-alt/Schedulix-</a>'
    '</div>',
    unsafe_allow_html=True,
)
