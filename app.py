"""DataSentinel — Enterprise Dark Data Observability & Quality Monitoring Dashboard
Streamlit runner: streamlit run app.py
"""
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.datasentinel.pipeline_monitor import run_pipeline
from src.datasentinel.reporting import failed_rows_df, issues_to_df, summary_json
from src.datasentinel.storage import get_runs

# Constants
DB_PATH = "datasentinel.db"
SAMPLE_PATH = "data/sales.csv"
RULES_CONFIG_PATH = "config/rules.json"

# Page Configuration
st.set_page_config(
    page_title="DataSentinel — Data Observability",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Enterprise Dark Theme CSS (#080D16, #0D1523, #111C2D, #172438, #38BDF8)
# -----------------------------------------------------------------------------
DARK_THEME_CSS = """
<style>
/* Main Container & Viewport Spacing */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    max-width: 1440px;
}

/* Sidebar Customization */
section[data-testid="stSidebar"] {
    background-color: #0D1523 !important;
    border-right: 1px solid #253449 !important;
    width: 320px !important;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1rem !important;
    padding-left: 0.9rem !important;
    padding-right: 0.9rem !important;
}

/* Streamlined Dark Header */
.ds-header {
    background: #111C2D;
    border: 1px solid #253449;
    border-radius: 8px;
    padding: 0.9rem 1.4rem;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
}

.ds-header-left {
    display: flex;
    align-items: center;
    gap: 0.85rem;
}

.ds-header-icon {
    font-size: 1.8rem;
    line-height: 1;
}

.ds-header-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: #F1F5F9 !important;
    margin: 0;
    line-height: 1.2;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.ds-header-tag {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    background: rgba(56, 189, 248, 0.15);
    color: #38BDF8 !important;
    border: 1px solid rgba(56, 189, 248, 0.35);
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
}

.ds-header-sub {
    font-size: 0.8rem;
    color: #94A3B8 !important;
    margin-top: 0.15rem;
}

.ds-header-meta {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    flex-wrap: wrap;
}

.ds-meta-badge {
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.3rem 0.65rem;
    border-radius: 4px;
    background: #172438;
    color: #94A3B8;
    border: 1px solid #253449;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
}

/* Tabs Styling - Clean Dark Navigation */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 1px solid #253449 !important;
    background: transparent !important;
    padding-bottom: 0px;
}

.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    color: #94A3B8 !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 0.9rem !important;
    border: none !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #F1F5F9 !important;
}

.stTabs [aria-selected="true"] {
    background-color: transparent !important;
    color: #38BDF8 !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #38BDF8 !important;
}

/* Dark KPI Metric Card */
.ds-kpi-card {
    background: #111C2D !important;
    border: 1px solid #253449 !important;
    border-radius: 8px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.ds-kpi-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94A3B8 !important;
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.35rem;
}

.ds-kpi-val {
    font-size: 1.45rem;
    font-weight: 700;
    color: #F1F5F9 !important;
    line-height: 1.15;
}

.ds-kpi-sub {
    font-size: 0.74rem;
    color: #64748B !important;
    margin-top: 0.3rem;
    display: flex;
    align-items: center;
    gap: 0.35rem;
}

/* Surface Container Card */
.ds-card {
    background: #111C2D !important;
    border: 1px solid #253449 !important;
    border-radius: 8px;
    padding: 1.1rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.ds-card-elevated {
    background: #172438 !important;
    border: 1px solid #253449 !important;
    border-radius: 6px;
    padding: 0.9rem;
    margin-bottom: 0.75rem;
}

.ds-card-title {
    font-size: 0.92rem;
    font-weight: 700;
    color: #F1F5F9 !important;
    margin-bottom: 0.15rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.ds-card-subtitle {
    font-size: 0.76rem;
    color: #94A3B8 !important;
    margin-bottom: 0.75rem;
}

/* Badges */
.ds-badge {
    display: inline-flex;
    align-items: center;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    line-height: 1.2;
}

.ds-badge-success {
    background: rgba(34, 197, 94, 0.15) !important;
    color: #22C55E !important;
    border: 1px solid rgba(34, 197, 94, 0.3);
}

.ds-badge-warning {
    background: rgba(245, 158, 11, 0.15) !important;
    color: #F59E0B !important;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.ds-badge-danger {
    background: rgba(248, 113, 113, 0.15) !important;
    color: #F87171 !important;
    border: 1px solid rgba(248, 113, 113, 0.3);
}

.ds-badge-neutral {
    background: #172438 !important;
    color: #94A3B8 !important;
    border: 1px solid #253449;
}

.ds-badge-sky {
    background: rgba(56, 189, 248, 0.15) !important;
    color: #38BDF8 !important;
    border: 1px solid rgba(56, 189, 248, 0.3);
}

/* Alert Notification Bars */
.ds-alert {
    padding: 0.75rem 0.95rem;
    border-radius: 6px;
    font-size: 0.82rem;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
}

.ds-alert-success {
    background: rgba(34, 197, 94, 0.1) !important;
    color: #22C55E !important;
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-left: 3px solid #22C55E;
}

.ds-alert-warning {
    background: rgba(245, 158, 11, 0.1) !important;
    color: #F59E0B !important;
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-left: 3px solid #F59E0B;
}

.ds-alert-danger {
    background: rgba(248, 113, 113, 0.1) !important;
    color: #F87171 !important;
    border: 1px solid rgba(248, 113, 113, 0.3);
    border-left: 3px solid #F87171;
}

/* Empty State Card */
.ds-empty-box {
    background: #111C2D !important;
    border: 1px dashed #253449 !important;
    border-radius: 8px;
    padding: 2.5rem 1.5rem;
    text-align: center;
    margin: 1.5rem 0;
}

.ds-empty-icon {
    font-size: 2rem;
    color: #38BDF8 !important;
    margin-bottom: 0.5rem;
}

.ds-empty-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #F1F5F9 !important;
    margin-bottom: 0.35rem;
}

.ds-empty-desc {
    font-size: 0.84rem;
    color: #94A3B8 !important;
    max-width: 520px;
    margin: 0 auto 1.2rem auto;
    line-height: 1.5;
}

/* JSON editor styling */
textarea[aria-label="Validation Rules (JSON)"] {
    font-family: Consolas, Monaco, monospace !important;
    font-size: 0.78rem !important;
    background-color: #080D16 !important;
    color: #F1F5F9 !important;
    border: 1px solid #253449 !important;
}
</style>
"""

st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Plotly Dark Theme Helper
# -----------------------------------------------------------------------------
def apply_dark_chart_theme(fig, height=270, title=""):
    """Enforces cohesive dark enterprise aesthetics on all Plotly visualizations."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(size=12, color="#F1F5F9", family="sans-serif"),
            x=0.01,
            y=0.96,
        ),
        margin=dict(l=16, r=16, t=36 if title else 16, b=16),
        height=height,
        paper_bgcolor="#111C2D",
        plot_bgcolor="#111C2D",
        font=dict(color="#94A3B8", size=11),
        hoverlabel=dict(
            bgcolor="#172438",
            bordercolor="#253449",
            font_size=11,
            font_color="#F1F5F9",
        ),
        xaxis=dict(
            gridcolor="#1F2E43",
            zerolinecolor="#253449",
            tickfont=dict(color="#94A3B8", size=10),
        ),
        yaxis=dict(
            gridcolor="#1F2E43",
            zerolinecolor="#253449",
            tickfont=dict(color="#94A3B8", size=10),
        ),
        legend=dict(
            font=dict(size=10, color="#94A3B8"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    return fig


# -----------------------------------------------------------------------------
# Fetch SQLite History for Real-Time Status in Header
# -----------------------------------------------------------------------------
history_runs = get_runs(DB_PATH)
latest_history_run = history_runs.iloc[-1] if not history_runs.empty else None

if latest_history_run is not None:
    l_status = latest_history_run["status"]
    if l_status == "SUCCESS":
        status_html = f'<span class="ds-badge ds-badge-success">● RUN #{latest_history_run["run_id"]} HEALTHY</span>'
    elif l_status == "QUALITY_FAILED":
        status_html = f'<span class="ds-badge ds-badge-warning">▲ RUN #{latest_history_run["run_id"]} QUALITY BREACH</span>'
    else:
        status_html = f'<span class="ds-badge ds-badge-danger">✖ RUN #{latest_history_run["run_id"]} FAILED</span>'
else:
    status_html = '<span class="ds-badge ds-badge-neutral">● SYSTEM READY</span>'

# -----------------------------------------------------------------------------
# Compact Enterprise Application Header
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="ds-header">
        <div class="ds-header-left">
            <div class="ds-header-icon">🛡️</div>
            <div>
                <div class="ds-header-title">
                    DataSentinel
                    <span class="ds-header-tag">DATA OBSERVABILITY</span>
                </div>
                <div class="ds-header-sub">Automated Data Quality & Pipeline Failure Monitoring</div>
            </div>
        </div>
        <div class="ds-header-meta">
            <div class="ds-meta-badge">
                {status_html}
            </div>
            <div class="ds-meta-badge">
                <span style="color: #38BDF8;">STORAGE:</span> SQLite (datasentinel.db)
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Compact Sidebar: Ingestion & Collapsed Advanced Rules
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="ds-card-title">DATA SOURCE</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload dataset (CSV, XLSX, XLS)",
        type=["csv", "xlsx", "xls"],
        help="Upload tabular data for schema validation and quality scoring.",
    )

    if uploaded_file is not None:
        active_source_name = uploaded_file.name
        file_size_kb = round(len(uploaded_file.getvalue()) / 1024, 1)
        st.markdown(
            f"""
            <div class="ds-card-elevated" style="margin-top: -0.2rem; margin-bottom: 0.6rem;">
                <div style="font-size: 0.78rem; font-weight: 600; color: #F1F5F9;">{uploaded_file.name}</div>
                <div style="font-size: 0.72rem; color: #94A3B8;">Size: {file_size_kb} KB • Format: {Path(uploaded_file.name).suffix.upper()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        active_source_name = "data/sales.csv"
        try:
            sample_size_kb = round(Path(SAMPLE_PATH).stat().st_size / 1024, 1)
        except Exception:
            sample_size_kb = 0.1
        st.markdown(
            f"""
            <div class="ds-card-elevated" style="margin-top: -0.2rem; margin-bottom: 0.6rem;">
                <div style="font-size: 0.78rem; font-weight: 600; color: #F1F5F9;">sales.csv <span class="ds-badge ds-badge-neutral" style="font-size: 0.65rem;">Sample</span></div>
                <div style="font-size: 0.72rem; color: #94A3B8;">Size: {sample_size_kb} KB • Built-in benchmark</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Collapsed Advanced Validation Rules Expander
    with st.expander("⚙️ Advanced Validation Rules", expanded=False):
        try:
            default_rules_content = Path(RULES_CONFIG_PATH).read_text(encoding="utf-8")
        except Exception:
            default_rules_content = '{\n  "required_columns": [],\n  "pass_threshold": 90\n}'

        rules_json_str = st.text_area(
            "Validation Rules (JSON)",
            value=default_rules_content,
            height=180,
            help="Define required columns, unique constraints, and numeric bounds in JSON.",
        )

        is_json_valid = False
        parsed_rules = {}
        try:
            parsed_rules = json.loads(rules_json_str)
            is_json_valid = True
            st.markdown(
                '<span class="ds-badge ds-badge-success">✓ Valid Rule Schema</span>',
                unsafe_allow_html=True,
            )
        except json.JSONDecodeError as err:
            st.markdown(
                f'<span class="ds-badge ds-badge-danger">✕ Syntax Error (Line {err.lineno})</span>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)
    run_btn = st.button(
        "⚡ Run Validation",
        type="primary",
        use_container_width=True,
        disabled=not is_json_valid,
    )


# -----------------------------------------------------------------------------
# Pipeline Execution Handler
# -----------------------------------------------------------------------------
def execute_validation_pipeline():
    """Runs data quality pipeline and preserves results in session state."""
    if not is_json_valid:
        st.sidebar.error("Validation blocked: Invalid JSON rule configuration.")
        return False

    with st.spinner("Analyzing schema, verifying rules & logging telemetry..."):
        source, dataset_name = (
            (uploaded_file, uploaded_file.name)
            if uploaded_file is not None
            else (SAMPLE_PATH, "sales.csv")
        )
        st.session_state["result"] = run_pipeline(source, parsed_rules, DB_PATH, dataset_name)
        st.session_state["executed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return True


if run_btn:
    execute_validation_pipeline()

res = st.session_state.get("result")


# -----------------------------------------------------------------------------
# 5 Dashboard Navigation Sections
# -----------------------------------------------------------------------------
tab_overview, tab_profiling, tab_validation, tab_monitoring, tab_reports = st.tabs(
    [
        "Overview",
        "Data Profiling",
        "Validation Results",
        "Pipeline Monitoring",
        "Reports & Export",
    ]
)


# -----------------------------------------------------------------------------
# Tab 4: Pipeline Monitoring (Always Accessible with Real SQLite History)
# -----------------------------------------------------------------------------
with tab_monitoring:
    st.markdown('<div class="ds-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="ds-card-title">Pipeline Run History & Drift Telemetry'
        '<span class="ds-badge ds-badge-neutral">Backend: SQLite</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ds-card-subtitle">Real audit trail of pipeline executions, tracking latency, schema drift, and data quality degradation.</div>',
        unsafe_allow_html=True,
    )

    history_df = get_runs(DB_PATH)

    if history_df.empty:
        st.markdown(
            """
            <div class="ds-empty-box">
                <div class="ds-empty-icon">📁</div>
                <div class="ds-empty-title">No Historical Runs Recorded</div>
                <div class="ds-empty-desc">Click "Run Validation" in the sidebar to execute the pipeline and log your first run.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # History Metrics Strip
        tot_runs = len(history_df)
        success_count = len(history_df[history_df["status"] == "SUCCESS"])
        overall_pass_rate = round((success_count / tot_runs) * 100, 1) if tot_runs else 0.0
        avg_lat = round(history_df["duration_sec"].mean(), 4) if "duration_sec" in history_df else 0.0
        last_rec = history_df.iloc[-1]
        last_stat = last_rec["status"]
        last_badge_cls = (
            "ds-badge-success"
            if last_stat == "SUCCESS"
            else ("ds-badge-warning" if last_stat == "QUALITY_FAILED" else "ds-badge-danger")
        )

        h1, h2, h3, h4 = st.columns(4)
        with h1:
            st.markdown(
                f'<div class="ds-kpi-card"><div class="ds-kpi-label">TOTAL RUNS</div>'
                f'<div class="ds-kpi-val">{tot_runs}</div>'
                f'<div class="ds-kpi-sub">Logged in database</div></div>',
                unsafe_allow_html=True,
            )
        with h2:
            st.markdown(
                f'<div class="ds-kpi-card"><div class="ds-kpi-label">PIPELINE PASS RATE</div>'
                f'<div class="ds-kpi-val">{overall_pass_rate}%</div>'
                f'<div class="ds-kpi-sub">{success_count} of {tot_runs} runs passed</div></div>',
                unsafe_allow_html=True,
            )
        with h3:
            st.markdown(
                f'<div class="ds-kpi-card"><div class="ds-kpi-label">AVERAGE LATENCY</div>'
                f'<div class="ds-kpi-val">{avg_lat}s</div>'
                f'<div class="ds-kpi-sub">Execution duration</div></div>',
                unsafe_allow_html=True,
            )
        with h4:
            st.markdown(
                f'<div class="ds-kpi-card"><div class="ds-kpi-label">LATEST RUN STATUS</div>'
                f'<div class="ds-kpi-val" style="font-size: 1.15rem;">Run #{last_rec["run_id"]}</div>'
                f'<div class="ds-kpi-sub"><span class="ds-badge {last_badge_cls}">{last_stat}</span></div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

        # Historical Trend Charts
        mc1, mc2 = st.columns(2)
        valid_history = history_df.dropna(subset=["score"])

        with mc1:
            if len(valid_history) > 0:
                fig_hist_score = go.Figure()
                fig_hist_score.add_trace(
                    go.Scatter(
                        x=valid_history["run_id"],
                        y=valid_history["score"],
                        mode="lines+markers",
                        name="Quality Score",
                        line=dict(color="#38BDF8", width=2.5),
                        marker=dict(size=6, color="#6366F1"),
                    )
                )
                fig_hist_score.add_hline(
                    y=90,
                    line_dash="dot",
                    line_color="#22C55E",
                    annotation_text="Pass Threshold (90%)",
                    annotation_position="bottom right",
                )
                fig_hist_score.update_yaxes(range=[0, 105], title="Quality Score (%)")
                fig_hist_score.update_xaxes(title="Run ID")
                apply_dark_chart_theme(fig_hist_score, height=270, title="Quality Score Trend Across Runs")
                st.plotly_chart(fig_hist_score, use_container_width=True)
            else:
                st.info("Insufficient scoring data for trend chart.")

        with mc2:
            if len(valid_history) > 0:
                fig_hist_vol = go.Figure()
                fig_hist_vol.add_trace(
                    go.Bar(
                        x=valid_history["run_id"],
                        y=valid_history["total_rows"],
                        name="Total Ingested",
                        marker_color="#253449",
                    )
                )
                fig_hist_vol.add_trace(
                    go.Bar(
                        x=valid_history["run_id"],
                        y=valid_history["failed_rows"],
                        name="Failed Rows",
                        marker_color="#F87171",
                    )
                )
                fig_hist_vol.update_layout(barmode="group")
                fig_hist_vol.update_xaxes(title="Run ID")
                fig_hist_vol.update_yaxes(title="Record Count")
                apply_dark_chart_theme(fig_hist_vol, height=270, title="Ingestion Volume vs. Failed Rows")
                st.plotly_chart(fig_hist_vol, use_container_width=True)
            else:
                st.info("Insufficient volume data for chart.")

        # Real Run Table
        st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)
        st.markdown("<b>Historical Pipeline Run Log:</b>", unsafe_allow_html=True)
        table_runs = history_df.sort_values("run_id", ascending=False).copy()
        table_runs["duration_sec"] = table_runs["duration_sec"].apply(
            lambda x: f"{x:.4f}s" if pd.notna(x) else "-"
        )
        table_runs["score"] = table_runs["score"].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "-"
        )
        table_runs = table_runs.rename(
            columns={
                "run_id": "Run #",
                "dataset": "Dataset",
                "status": "Status",
                "started_at": "Timestamp",
                "duration_sec": "Duration",
                "total_rows": "Total Rows",
                "failed_rows": "Failed Rows",
                "score": "Score",
                "error": "Execution Error",
            }
        )
        st.dataframe(table_runs, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Empty State: Prompt User to Run Validation
# -----------------------------------------------------------------------------
if res is None:
    with tab_overview:
        st.markdown(
            f"""
            <div class="ds-empty-box">
                <div class="ds-empty-icon">🛡️</div>
                <div class="ds-empty-title">Ready for Pipeline Validation</div>
                <div class="ds-empty-desc">
                    No active validation in memory. Upload your tabular dataset in the sidebar,
                    or run validation on the default benchmark (<code>data/sales.csv</code>).
                </div>
                <div class="ds-badge ds-badge-sky" style="margin-bottom: 1.2rem;">
                    Active Dataset: {active_source_name}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_left_pad, col_center_btn, col_right_pad = st.columns([1, 1.2, 1])
        with col_center_btn:
            if st.button("⚡ Run Validation Now", key="empty_run_action", type="primary", use_container_width=True):
                if execute_validation_pipeline():
                    st.rerun()

    for empty_tab in (tab_profiling, tab_validation, tab_reports):
        with empty_tab:
            st.markdown(
                """
                <div class="ds-empty-box">
                    <div class="ds-empty-title">Validation Data Required</div>
                    <div class="ds-empty-desc">
                        Execute pipeline validation in the sidebar to generate this view.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.stop()


# -----------------------------------------------------------------------------
# Handle Execution Failure (Pipeline Crash vs Data Quality Failure)
# -----------------------------------------------------------------------------
if res["status"] == "EXECUTION_FAILED":
    with tab_overview:
        st.markdown(
            f"""
            <div class="ds-alert ds-alert-danger">
                <div>
                    <b>⚠️ PIPELINE EXECUTION CRASHED (EXECUTION_FAILED)</b><br/>
                    The pipeline encountered an unrecoverable runtime exception during ingestion:<br/>
                    <code>{res['error']}</code><br/><br/>
                    <i>Note: This represents a system, format, or I/O failure, separate from data quality rule breaches.</i>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    for crash_tab in (tab_profiling, tab_validation, tab_reports):
        with crash_tab:
            st.error(f"Pipeline crashed during execution: {res['error']}")
    st.stop()


# -----------------------------------------------------------------------------
# Unpack Validated Results
# -----------------------------------------------------------------------------
df = res["df"]
summary = res["summary"]
issues = res["issues"]
alerts = res["alerts"]
issues_df = issues_to_df(issues)
score_val = summary["score"]
pass_threshold = parsed_rules.get("pass_threshold", 90) if is_json_valid else 90


# -----------------------------------------------------------------------------
# Tab 1: Overview Dashboard (Two-Column Enterprise Layout)
# -----------------------------------------------------------------------------
with tab_overview:
    # 1. Compact Row of 6 Dark KPI Cards
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    score_status = "PASS" if summary["passed"] else "FAIL"
    score_badge_cls = "ds-badge-success" if summary["passed"] else "ds-badge-warning"
    failed_pct = round((summary["failed_rows"] / summary["total_rows"] * 100), 1) if summary["total_rows"] else 0
    score_color = "#22C55E" if summary["passed"] else "#F59E0B"

    with k1:
        st.markdown(
            f"""
            <div class="ds-kpi-card">
                <div class="ds-kpi-label"><span>🛡️</span> QUALITY SCORE</div>
                <div class="ds-kpi-val" style="color: {score_color} !important;">{score_val}%</div>
                <div class="ds-kpi-sub">
                    <span class="ds-badge {score_badge_cls}">{score_status}</span> Target: {pass_threshold}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="ds-kpi-card">
                <div class="ds-kpi-label"><span>📊</span> TOTAL ROWS</div>
                <div class="ds-kpi-val">{summary['total_rows']:,}</div>
                <div class="ds-kpi-sub">Ingested records</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="ds-kpi-card">
                <div class="ds-kpi-label"><span>📐</span> TOTAL COLUMNS</div>
                <div class="ds-kpi-val">{summary['total_columns']}</div>
                <div class="ds-kpi-sub">Schema features</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k4:
        fail_color = "#F87171" if summary["failed_rows"] > 0 else "#22C55E"
        st.markdown(
            f"""
            <div class="ds-kpi-card">
                <div class="ds-kpi-label"><span>✖</span> FAILED ROWS</div>
                <div class="ds-kpi-val" style="color: {fail_color} !important;">{summary['failed_rows']:,}</div>
                <div class="ds-kpi-sub">{failed_pct}% of total records</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k5:
        issue_color = "#F59E0B" if summary["issue_count"] > 0 else "#22C55E"
        st.markdown(
            f"""
            <div class="ds-kpi-card">
                <div class="ds-kpi-label"><span>⚠️</span> ISSUES FOUND</div>
                <div class="ds-kpi-val" style="color: {issue_color} !important;">{summary['issue_count']}</div>
                <div class="ds-kpi-sub">Rule violations</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k6:
        run_status_badge = "ds-badge-success" if res["status"] == "SUCCESS" else "ds-badge-warning"
        st.markdown(
            f"""
            <div class="ds-kpi-card">
                <div class="ds-kpi-label"><span>⚡</span> PIPELINE STATUS</div>
                <div class="ds-kpi-val" style="font-size: 1.15rem; padding-top: 0.25rem;">
                    <span class="ds-badge {run_status_badge}">{res['status']}</span>
                </div>
                <div class="ds-kpi-sub">Latency: {res.get('duration', 0.0)}s</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)

    # 2. Balanced Two-Column Overview Layout (LEFT: Charts | RIGHT: Findings & Summary)
    col_overview_left, col_overview_right = st.columns([1.1, 0.9])

    with col_overview_left:
        # Quality Trend Chart (Real Historical Data)
        st.markdown('<div class="ds-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="ds-card-title">Quality Score Trajectory'
            '<span class="ds-badge ds-badge-sky">Historical Runs</span></div>',
            unsafe_allow_html=True,
        )

        all_runs = get_runs(DB_PATH).dropna(subset=["score"])
        if len(all_runs) > 0:
            fig_score_trend = go.Figure()
            fig_score_trend.add_trace(
                go.Scatter(
                    x=all_runs["run_id"],
                    y=all_runs["score"],
                    mode="lines+markers",
                    name="Score",
                    line=dict(color="#38BDF8", width=2.5),
                    marker=dict(size=6, color="#6366F1"),
                )
            )
            fig_score_trend.add_hline(
                y=pass_threshold,
                line_dash="dot",
                line_color="#22C55E",
                annotation_text=f"Threshold ({pass_threshold}%)",
                annotation_position="bottom right",
            )
            fig_score_trend.update_yaxes(range=[0, 105], title="Quality Score (%)")
            fig_score_trend.update_xaxes(title="Run ID")
            apply_dark_chart_theme(fig_score_trend, height=220)
            st.plotly_chart(fig_score_trend, use_container_width=True)
        else:
            st.info("No prior scoring runs available for trend.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Validation Issue Distribution Chart
        st.markdown('<div class="ds-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="ds-card-title">Rule Breach Breakdown by Severity</div>',
            unsafe_allow_html=True,
        )

        if not issues_df.empty:
            sev_summary = issues_df.groupby("severity")["count"].sum().reset_index()
            sev_color_map = {
                "Critical": "#F87171",
                "High": "#FB923C",
                "Medium": "#F59E0B",
                "Low": "#38BDF8",
            }
            fig_issues_bar = px.bar(
                sev_summary,
                x="severity",
                y="count",
                color="severity",
                color_discrete_map=sev_color_map,
                text="count",
            )
            fig_issues_bar.update_traces(textposition="outside")
            fig_issues_bar.update_xaxes(title="Severity Tier")
            fig_issues_bar.update_yaxes(title="Affected Records")
            apply_dark_chart_theme(fig_issues_bar, height=220)
            st.plotly_chart(fig_issues_bar, use_container_width=True)
        else:
            st.markdown(
                """
                <div style="text-align: center; padding: 2.2rem 1rem; color: #22C55E;">
                    <div style="font-size: 1.8rem;">✓</div>
                    <b>All Quality Rules Passed</b><br/>
                    <span style="font-size: 0.78rem; color: #94A3B8;">Zero issues or schema violations detected in this dataset.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_overview_right:
        # Latest Run Summary Card
        st.markdown('<div class="ds-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="ds-card-title">Latest Run Specification</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="ds-card-elevated" style="line-height: 1.7; font-size: 0.82rem; color: #94A3B8;">
                • <b style="color: #F1F5F9;">Target Dataset:</b> <code>{res['dataset']}</code><br/>
                • <b style="color: #F1F5F9;">Run Identifier:</b> #{res.get('run_id', '-')}<br/>
                • <b style="color: #F1F5F9;">Execution Latency:</b> {res.get('duration', 0.0)}s<br/>
                • <b style="color: #F1F5F9;">Pass Criteria:</b> Score ≥ {pass_threshold}% & No Structural Blockers<br/>
                • <b style="color: #F1F5F9;">Outcome:</b> <span class="ds-badge {'ds-badge-success' if summary['passed'] else 'ds-badge-warning'}">{res['status']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Observability Alerts (Schema Drift, Drop Alerts)
        if alerts:
            st.markdown("<b>Active Observability Alerts:</b>", unsafe_allow_html=True)
            for alert_text in alerts:
                st.markdown(
                    f"""
                    <div class="ds-alert ds-alert-warning">
                        <div><b>ALERT:</b> {alert_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
                <div class="ds-alert ds-alert-success" style="margin-bottom: 0.6rem;">
                    <div><b>✓ Schema & Volume Baseline:</b> No drift or unexpected score drops detected.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Highest-Severity Validation Findings
        st.markdown("<div style='height: 0.2rem;'></div>", unsafe_allow_html=True)
        st.markdown("<b>Highest-Severity Findings:</b>", unsafe_allow_html=True)

        if not issues_df.empty:
            for _, issue_row in issues_df.head(4).iterrows():
                sev_tag = (
                    "ds-badge-danger"
                    if issue_row["severity"] in ["Critical", "High"]
                    else "ds-badge-warning"
                )
                st.markdown(
                    f"""
                    <div class="ds-card-elevated" style="margin-bottom: 0.4rem; padding: 0.6rem 0.8rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <b style="color: #F1F5F9; font-size: 0.82rem;">{issue_row['check']}</b>
                            <span class="ds-badge {sev_tag}">{issue_row['severity']}</span>
                        </div>
                        <div style="font-size: 0.76rem; color: #94A3B8; margin-top: 0.2rem;">
                            Column: <code>{issue_row['column']}</code> • {issue_row['message']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<div style='font-size: 0.8rem; color: #22C55E;'>No issues to display.</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Tab 2: Data Profiling
# -----------------------------------------------------------------------------
with tab_profiling:
    st.markdown('<div class="ds-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="ds-card-title">Dataset Structure & Statistical Profiler</div>'
        '<div class="ds-card-subtitle">Detailed schema diagnostics, null value density, unique cardinality, and distributions.</div>',
        unsafe_allow_html=True,
    )

    tot_cells = df.shape[0] * df.shape[1]
    missing_cells = int(df.isna().sum().sum())
    completeness_rate = (
        round((1 - (missing_cells / tot_cells)) * 100, 2) if tot_cells else 100.0
    )
    duplicate_rows_cnt = int(df.duplicated().sum())

    dp1, dp2, dp3, dp4 = st.columns(4)
    with dp1:
        st.markdown(
            f'<div class="ds-kpi-card"><div class="ds-kpi-label">COMPLETENESS RATE</div>'
            f'<div class="ds-kpi-val">{completeness_rate}%</div>'
            f'<div class="ds-kpi-sub">Populated cells</div></div>',
            unsafe_allow_html=True,
        )
    with dp2:
        st.markdown(
            f'<div class="ds-kpi-card"><div class="ds-kpi-label">TOTAL NULL CELLS</div>'
            f'<div class="ds-kpi-val" style="color: {"#F59E0B" if missing_cells > 0 else "#22C55E"} !important;">{missing_cells:,}</div>'
            f'<div class="ds-kpi-sub">Across {df.shape[1]} columns</div></div>',
            unsafe_allow_html=True,
        )
    with dp3:
        st.markdown(
            f'<div class="ds-kpi-card"><div class="ds-kpi-label">DUPLICATE ROWS</div>'
            f'<div class="ds-kpi-val" style="color: {"#F59E0B" if duplicate_rows_cnt > 0 else "#22C55E"} !important;">{duplicate_rows_cnt}</div>'
            f'<div class="ds-kpi-sub">Exact row copies</div></div>',
            unsafe_allow_html=True,
        )
    with dp4:
        memory_usage_kb = round(df.memory_usage(deep=True).sum() / 1024, 2)
        st.markdown(
            f'<div class="ds-kpi-card"><div class="ds-kpi-label">IN-MEMORY FOOTPRINT</div>'
            f'<div class="ds-kpi-val">{memory_usage_kb} KB</div>'
            f'<div class="ds-kpi-sub">DataFrame size</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

    # Column Schema Health Table
    col_profile_rows = []
    for c in df.columns:
        n_null = int(df[c].isna().sum())
        p_null = round((n_null / len(df)) * 100, 2) if len(df) else 0.0
        n_unique = int(df[c].nunique())
        dtype_repr = str(df[c].dtype)
        col_profile_rows.append(
            {
                "Column Name": c,
                "Inferred Dtype": dtype_repr,
                "Non-Null Count": len(df) - n_null,
                "Null Count": n_null,
                "Null %": f"{p_null}%",
                "Unique Values": n_unique,
                "Completeness": f"{100 - p_null:.2f}%",
            }
        )

    profile_df = pd.DataFrame(col_profile_rows)
    st.markdown("<b>Column Health & Schema Specifications:</b>", unsafe_allow_html=True)
    st.dataframe(profile_df, use_container_width=True, hide_index=True)

    # Profiling Visualizations
    p_chart1, p_chart2 = st.columns(2)
    with p_chart1:
        null_rates = pd.DataFrame(
            {
                "Column": df.columns,
                "Null %": (df.isna().mean() * 100).round(2).values,
            }
        ).sort_values("Null %", ascending=True)

        fig_null_bars = px.bar(
            null_rates,
            x="Null %",
            y="Column",
            orientation="h",
            color="Null %",
            color_continuous_scale=["#38BDF8", "#F59E0B", "#F87171"],
            text="Null %",
        )
        fig_null_bars.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_null_bars.update_layout(coloraxis_showscale=False)
        fig_null_bars.update_xaxes(range=[0, max(100, null_rates["Null %"].max() + 10)])
        apply_dark_chart_theme(fig_null_bars, height=260, title="Missing Value Rate per Column (%)")
        st.plotly_chart(fig_null_bars, use_container_width=True)

    with p_chart2:
        card_rates = pd.DataFrame(
            {
                "Column": df.columns,
                "Unique Values": df.nunique().values,
            }
        ).sort_values("Unique Values", ascending=False)

        fig_card_bars = px.bar(
            card_rates,
            x="Column",
            y="Unique Values",
            text="Unique Values",
            color_discrete_sequence=["#38BDF8"],
        )
        fig_card_bars.update_traces(textposition="outside")
        apply_dark_chart_theme(fig_card_bars, height=260, title="Unique Cardinality Count per Column")
        st.plotly_chart(fig_card_bars, use_container_width=True)

    # Numeric Distribution
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)
        st.markdown("<b>Numeric Columns Summary Statistics:</b>", unsafe_allow_html=True)
        numeric_desc = df[num_cols].describe().T.reset_index().rename(columns={"index": "Column"})
        st.dataframe(numeric_desc.round(2), use_container_width=True, hide_index=True)

        sel_num_col = st.selectbox("Inspect distribution chart for numeric column:", num_cols)
        fig_dist = px.histogram(
            df,
            x=sel_num_col,
            marginal="box",
            color_discrete_sequence=["#38BDF8"],
            nbins=15,
        )
        apply_dark_chart_theme(fig_dist, height=250, title=f"Distribution & Outlier Plot: {sel_num_col}")
        st.plotly_chart(fig_dist, use_container_width=True)

    with st.expander("Inspect Raw Records", expanded=False):
        st.dataframe(df, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Tab 3: Validation Results
# -----------------------------------------------------------------------------
with tab_validation:
    st.markdown('<div class="ds-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="ds-card-title">Rule Validation Log & Impacted Records'
        f'<span class="ds-badge ds-badge-neutral">{len(issues)} Issues</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ds-card-subtitle">Granular audit log of failed validation rules, affected columns, and records.</div>',
        unsafe_allow_html=True,
    )

    if issues_df.empty:
        st.markdown(
            """
            <div class="ds-empty-box">
                <div class="ds-empty-title" style="color: #22C55E !important;">✓ All Validation Rules Passed</div>
                <div class="ds-empty-desc">No rule violations, missing values, duplicates, or out-of-range metrics were identified.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Severity Metric Cards
        counts_by_sev = summary["severity_counts"]
        sv1, sv2, sv3, sv4 = st.columns(4)
        with sv1:
            st.markdown(
                f'<div class="ds-kpi-card"><div class="ds-kpi-label">CRITICAL</div>'
                f'<div class="ds-kpi-val" style="color: #F87171 !important;">{counts_by_sev.get("Critical", 0)}</div>'
                f'<div class="ds-kpi-sub">Structural blockers</div></div>',
                unsafe_allow_html=True,
            )
        with sv2:
            st.markdown(
                f'<div class="ds-kpi-card"><div class="ds-kpi-label">HIGH SEVERITY</div>'
                f'<div class="ds-kpi-val" style="color: #FB923C !important;">{counts_by_sev.get("High", 0)}</div>'
                f'<div class="ds-kpi-sub">Nulls & duplicates</div></div>',
                unsafe_allow_html=True,
            )
        with sv3:
            st.markdown(
                f'<div class="ds-kpi-card"><div class="ds-kpi-label">MEDIUM SEVERITY</div>'
                f'<div class="ds-kpi-val" style="color: #F59E0B !important;">{counts_by_sev.get("Medium", 0)}</div>'
                f'<div class="ds-kpi-sub">Out-of-range values</div></div>',
                unsafe_allow_html=True,
            )
        with sv4:
            st.markdown(
                f'<div class="ds-kpi-card"><div class="ds-kpi-label">LOW SEVERITY</div>'
                f'<div class="ds-kpi-val" style="color: #38BDF8 !important;">{counts_by_sev.get("Low", 0)}</div>'
                f'<div class="ds-kpi-sub">Minor warnings</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

        # Filters
        f1, f2, f3 = st.columns(3)
        available_sevs = sorted(issues_df["severity"].unique())
        available_chks = sorted(issues_df["check"].unique())
        available_cols = sorted(issues_df["column"].unique())

        filter_sev = f1.multiselect("Filter Severity:", options=available_sevs, default=available_sevs)
        filter_chk = f2.multiselect("Filter Check:", options=available_chks, default=available_chks)
        filter_col = f3.multiselect("Filter Column:", options=available_cols, default=available_cols)

        filtered_issues_df = issues_df[
            issues_df["severity"].isin(filter_sev)
            & issues_df["check"].isin(filter_chk)
            & issues_df["column"].isin(filter_col)
        ]

        st.markdown("<b>Filtered Rule Breaches:</b>", unsafe_allow_html=True)
        display_breaches = filtered_issues_df.rename(
            columns={
                "severity": "Severity",
                "check": "Rule Check",
                "column": "Column",
                "count": "Violations",
                "message": "Audit Explanation",
            }
        )
        st.dataframe(display_breaches, use_container_width=True, hide_index=True)

        # Failed Records Drilldown
        st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)
        failed_records_table = failed_rows_df(df, summary)
        st.markdown(
            f"<b>Failed Records Inspector ({len(failed_records_table)} rows impacted):</b>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Rows failing multiple validation rules are counted only once in the overall Quality Score."
        )
        st.dataframe(failed_records_table, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Tab 5: Reports & Export
# -----------------------------------------------------------------------------
with tab_reports:
    st.markdown('<div class="ds-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="ds-card-title">Audit Reports & Data Export Center</div>'
        '<div class="ds-card-subtitle">Download machine-readable audit artifacts, CSV summaries, and JSON manifests.</div>',
        unsafe_allow_html=True,
    )

    # Executive Summary Card
    st.markdown(
        f"""
        <div class="ds-card-elevated" style="line-height: 1.7; font-size: 0.83rem; color: #94A3B8; margin-bottom: 1.2rem;">
            <b style="color: #F1F5F9; font-size: 0.95rem;">Executive Audit Summary</b><br/>
            • <b style="color: #F1F5F9;">Evaluated Dataset:</b> <code>{res['dataset']}</code><br/>
            • <b style="color: #F1F5F9;">Audit Status:</b> <span class="ds-badge {'ds-badge-success' if summary['passed'] else 'ds-badge-warning'}">{res['status']}</span><br/>
            • <b style="color: #F1F5F9;">Quality Score:</b> {score_val}% (Target Threshold: ≥ {pass_threshold}%)<br/>
            • <b style="color: #F1F5F9;">Record Volume:</b> {summary['total_rows']:,} Total | {summary['failed_rows']:,} Failed ({failed_pct}%)<br/>
            • <b style="color: #F1F5F9;">Total Violations:</b> {summary['issue_count']} rule breaches identified across {summary['total_columns']} columns.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Download Controls
    dl1, dl2, dl3 = st.columns(3)

    with dl1:
        st.markdown("<b>Validation Issues (CSV)</b>", unsafe_allow_html=True)
        st.caption("Tabular log of all rule violations and messages.")
        st.download_button(
            label="Download Issues CSV",
            data=issues_df.to_csv(index=False),
            file_name=f"datasentinel_issues_{Path(res['dataset']).stem}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with dl2:
        st.markdown("<b>Failed Records (CSV)</b>", unsafe_allow_html=True)
        st.caption("Invalid data rows for remediation.")
        st.download_button(
            label="Download Failed Rows CSV",
            data=failed_rows_df(df, summary).to_csv(index=True),
            file_name=f"failed_rows_{Path(res['dataset']).stem}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with dl3:
        st.markdown("<b>Audit Manifest (JSON)</b>", unsafe_allow_html=True)
        st.caption("Telemetry for CI/CD pipelines & alert hooks.")
        json_audit_str = summary_json(res)
        st.download_button(
            label="Download Audit JSON",
            data=json_audit_str,
            file_name=f"audit_summary_{Path(res['dataset']).stem}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
    with st.expander("🔍 View Raw JSON Audit Manifest", expanded=False):
        st.json(json.loads(json_audit_str))

    st.markdown("</div>", unsafe_allow_html=True)
