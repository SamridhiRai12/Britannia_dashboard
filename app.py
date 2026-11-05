"""
Britannia Industries Ltd. - five-year interactive financial dashboard
Run:  streamlit run app.py
"""
from __future__ import annotations

import html

import numpy as np
import pandas as pd
import streamlit as st

import charts as CH
import data as D
import utils as U
from calculations import METRICS, cagr, compute_metrics, fmt_value, validate_raw
from theme import css, palette

st.set_page_config(page_title="Britannia | Financial Dashboard", page_icon="\U0001F4CA", layout="wide",
                   initial_sidebar_state="expanded")

PAGES = ["Executive Overview", "Financial Performance", "Profitability Ratios", "Liquidity & Solvency",
         "Cash Flow Analysis", "Balance Sheet Analysis", "Compare Years", "Data, Sources & Method"]
BASIS_DESC = {"Consolidated": "Britannia Industries Ltd. with subsidiaries, associates and joint venture",
              "Standalone": "Britannia Industries Ltd. (parent company only)"}
PLOT_KW = U.stretch_kwargs(st.plotly_chart)
BTN_KW = U.stretch_kwargs(st.button)
ss = st.session_state

# --------------------------------------------------------------------------- #
# Session defaults
# --------------------------------------------------------------------------- #
ss.setdefault("dark", True)
ss.setdefault("nav", PAGES[0])
ss.setdefault("raw_frames", None)       # uploaded data (None -> built-in)
ss.setdefault("upload_notes", [])
ss.setdefault("uploader_n", 0)


def _revert_data():
    ss["raw_frames"] = None
    ss["upload_notes"] = []
    ss["uploader_n"] += 1
    reset_filters()


def reset_filters():
    """Restore every filter to its default (theme, page and uploaded data are kept)."""
    fys = ss.get("_fys") or D.FY_LABELS
    ss["basis"] = ss.get("_bases", ["Consolidated"])[0]
    ss["oi_op"] = False
    ss["fy_from"], ss["fy_to"], ss["focus_fy"] = fys[0], fys[-1], fys[-1]
    ss["metric"] = "revenue"
    ss["cmp_a"] = fys[-2] if len(fys) > 1 else fys[-1]
    ss["cmp_b"] = fys[-1]


# --------------------------------------------------------------------------- #
# Sidebar skeleton (containers keep a fixed visual order while code runs in another)
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("### Britannia Industries")
    st.caption("Five-year financial dashboard \u00b7 INR crore")
    c_theme = st.container()
    c_nav = st.container()
    c_filters = st.container()
    c_data = st.container()
    c_export = st.container()

c_theme.toggle("Dark mode", key="dark", help="Switch between the dark-blue and the white/light-blue theme.")
P = palette(ss["dark"])
st.markdown(css(P), unsafe_allow_html=True)
c_nav.radio("Navigate", PAGES, key="nav")


@st.cache_data(show_spinner=False)
def template_bytes() -> bytes:
    fr = D.build_raw_frames()
    return U.build_excel(fr, {b: compute_metrics(df) for b, df in fr.items()}, D.default_sources_table())


# --------------------------------------------------------------------------- #
# Data update (processed BEFORE loading data so the whole run uses the new data)
# --------------------------------------------------------------------------- #
with c_data.expander("Update data (Excel upload)"):
    st.caption("Upload a workbook with sheets 'Consolidated' and/or 'Standalone' (columns: line_item, FY2022 ...). "
               "Download the template below to see the exact layout.")
    up = st.file_uploader("Excel file (.xlsx)", type=["xlsx"], key=f"uploader_{ss['uploader_n']}")
    if up is not None:
        try:
            frames, notes = U.parse_upload(up)
            ss["raw_frames"], ss["upload_notes"] = frames, notes
            st.success(f"Loaded: {', '.join(frames)}. {len(notes)} data note(s) - see 'Data quality'.")
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:  # defensive: never crash the app on a bad file
            st.error(f"Unexpected error while reading the file: {exc}")
    st.download_button("Download Excel template", template_bytes(), "britannia_upload_template.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_tpl", **BTN_KW)
    if ss["raw_frames"] is not None:
        st.button("Revert to built-in data", on_click=_revert_data, key="btn_revert", **BTN_KW)

RAW = ss["raw_frames"] if ss["raw_frames"] is not None else D.build_raw_frames()
USING_UPLOAD = ss["raw_frames"] is not None
BASES = list(RAW)
ss["_bases"] = BASES

# --------------------------------------------------------------------------- #
# Filters
# --------------------------------------------------------------------------- #
with c_filters:
    st.markdown("---")
    st.markdown("**Filters**")
    if ss.get("basis") not in BASES:
        ss["basis"] = BASES[0]
    st.selectbox("Statement basis", BASES, key="basis",
                 help="Consolidated = Britannia + subsidiaries, associates & JV. Standalone = parent company only.")
    BASIS = ss["basis"]
    FYS = sorted(RAW[BASIS].index)
    ss["_fys"] = FYS
    for k, dflt in [("fy_from", FYS[0]), ("fy_to", FYS[-1])]:
        if ss.get(k) not in FYS:
            ss[k] = dflt
    ca, cb = st.columns(2)
    ca.selectbox("From FY", FYS, key="fy_from", help="First year shown in trend charts.")
    cb.selectbox("To FY", FYS, key="fy_to", help="Last year shown in trend charts.")
    lo, hi = sorted([ss["fy_from"], ss["fy_to"]])
    RANGE = [f for f in FYS if lo <= f <= hi]
    if ss.get("focus_fy") not in RANGE:
        ss["focus_fy"] = RANGE[-1]
    st.selectbox("Financial year (KPIs & snapshots)", RANGE[::-1], key="focus_fy",
                 help="KPI cards, ratio tiles, waterfall and expense mix show this year.")
    if ss.get("metric") not in METRICS:
        ss["metric"] = "revenue"
    st.selectbox("Metric explorer", list(METRICS), key="metric", format_func=lambda k: METRICS[k].label,
                 help="Pick any metric; it is charted on 'Financial Performance'.")
    if ss.get("cmp_a") not in FYS:
        ss["cmp_a"] = FYS[-2] if len(FYS) > 1 else FYS[-1]
    if ss.get("cmp_b") not in FYS:
        ss["cmp_b"] = FYS[-1]
    cc, cd = st.columns(2)
    cc.selectbox("Compare: year A", FYS, key="cmp_a")
    cd.selectbox("Compare: year B", FYS, key="cmp_b")
    st.checkbox("Treat other income as operating", key="oi_op",
                help="Off (default): EBITDA/EBIT exclude other income (mostly treasury income). "
                     "On: include it. Affects EBITDA, EBIT, margins, ROCE and interest cover.")
    st.button("Reset filters", on_click=reset_filters, key="btn_reset", **BTN_KW)

FY = ss["focus_fy"]
OI = bool(ss["oi_op"])
METRIC_ALL = {b: compute_metrics(df, OI) for b, df in RAW.items()}
DA = METRIC_ALL[BASIS]                      # all years
D_ = DA.loc[RANGE]                          # selected range
SRC = D.default_sources_table() if not USING_UPLOAD else pd.DataFrame(
    [{"Basis": b, "FY": f, "Report": "User upload", "File": "uploaded workbook", "BS & P&L (PDF page)": "-",
      "Cash flow (PDF pages)": "-", "Link": ""} for b in BASES for f in sorted(RAW[b].index)])


@st.cache_data(show_spinner=False)
def excel_bytes(raw, oi, sources, fys):
    return U.build_excel(raw, {b: compute_metrics(df, oi) for b, df in raw.items()}, sources, list(fys))


# --------------------------------------------------------------------------- #
# Sidebar exports
# --------------------------------------------------------------------------- #
with c_export:
    st.markdown("---")
    st.markdown("**Download data**")
    try:
        st.download_button("Excel (all sheets)", excel_bytes(RAW, OI, SRC, tuple(RANGE)), "britannia_financials.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_xlsx_side", **BTN_KW)
        csv = U.metrics_long({BASIS: D_}).to_csv(index=False).encode("utf-8")
        st.download_button("CSV (metrics, current view)", csv, f"britannia_{BASIS.lower()}_metrics.csv", "text/csv",
                           key="dl_csv_side", **BTN_KW)
    except Exception as exc:
        st.warning(f"Export unavailable: {exc}")


# --------------------------------------------------------------------------- #
# UI helpers
# --------------------------------------------------------------------------- #
def header(title: str, sub: str):
    st.markdown(f'<span class="badge">{BASIS}</span><span class="badge">{RANGE[0]} - {RANGE[-1]}</span>'
                f'<span class="badge">INR crore</span>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="page-title">{html.escape(title)}</h1><div class="page-sub">{html.escape(sub)} '
                f'<em>({html.escape(BASIS_DESC[BASIS])})</em></div>', unsafe_allow_html=True)


def section(title: str, note: str = ""):
    st.markdown(f'<div class="section-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    if note:
        st.markdown(f'<div class="section-note">{html.escape(note)}</div>', unsafe_allow_html=True)


def plot(fig, key: str):
    if fig is None:
        st.info("This chart needs values that are missing for the selected year.")
        return
    st.plotly_chart(fig, theme=None, key=key, config={"displaylogo": False}, **PLOT_KW)


def prev_fy(fy: str):
    i = FYS.index(fy)
    return FYS[i - 1] if i > 0 else None


def card(key: str, label: str | None = None, invert: bool = False) -> str:
    """KPI card for the focus FY with change vs the previous FY (colour = good/bad, arrow = sign)."""
    m = METRICS[key]
    v = DA.loc[FY, key]
    p = prev_fy(FY)
    delta, tone, arrow = "", "flat", ""
    if p is None:
        delta = "prior year not in dataset"
    else:
        pv = DA.loc[p, key]
        if pd.isna(v) or pd.isna(pv):
            delta = f"vs {p}: n/a"
        else:
            if m.unit == "cr":
                ch = (v - pv) / abs(pv) * 100 if pv else float("nan")
                delta = f"{ch:+.1f}% vs {p}"
            elif m.unit == "%":
                ch = v - pv
                delta = f"{ch:+.1f} pp vs {p}"
            else:
                ch = v - pv
                delta = f"{ch:+.2f}x vs {p}"
            if pd.notna(ch) and abs(ch) > 1e-9:
                arrow = "up" if ch > 0 else "down"
                tone = "up" if (ch > 0) != invert else "down"
    return U.kpi_card(label or m.label, fmt_value(v, m.unit, 1 if m.unit == "%" else None), delta, tone,
                      f"{FY} \u00b7 {BASIS}", tip=f"{m.label}: {m.formula}", arrow=arrow)


def cards(specs, per_row=4):
    for i in range(0, len(specs), per_row):
        cols = st.columns(per_row)
        for col, spec in zip(cols, specs[i:i + per_row]):
            key, kw = (spec if isinstance(spec, tuple) else (spec, {}))
            col.markdown(card(key, **kw), unsafe_allow_html=True)


def table(keys, d=None):
    st.markdown(U.html_table(U.metrics_table(D_ if d is None else d, keys)), unsafe_allow_html=True)


def formulas(keys):
    with st.expander("Formulas and explanations"):
        rows = pd.DataFrame({"Formula": [METRICS[k].formula for k in keys], "Note": [METRICS[k].note or "-" for k in keys]},
                            index=[METRICS[k].label for k in keys])
        rows.index.name = "Metric"
        st.markdown(U.html_table(rows), unsafe_allow_html=True)


def source_line(statement: str):
    rep, p_pl, p_cf = D.SOURCE_MAP.get((BASIS, FY), ("", "-", "-"))
    if USING_UPLOAD:
        st.caption("Source: user-uploaded workbook.")
        return
    r = D.REPORTS[rep]
    pages = p_cf if statement == "CF" else p_pl
    st.caption(f"Source ({FY}, {BASIS.lower()} {dict(PL='statement of profit & loss', BS='balance sheet', CF='cash-flow statement').get(statement, 'statements')}): "
               f"{r['label']}, PDF page {pages}.")


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
def page_overview():
    header("Executive Overview", f"Snapshot for {FY} with year-on-year change.")
    cards([("revenue", {}), ("ebitda", {}), ("pat", {}), ("total_assets", {}),
           ("total_debt", {"invert": True}), ("cfo", {}), ("revenue_growth", {}), ("pat_growth", {})])
    if FY == FYS[0]:
        st.caption("Growth for the first year is missing because the prior year is outside the five-year dataset.")
    c1, c2 = st.columns([3, 2])
    with c1:
        plot(CH.revenue_profit_trend(D_, P), "ov_rev")
    with c2:
        plot(CH.margins(D_, P), "ov_margin")
    section("Key takeaways", "Computed from the selected basis and year range.")
    pts = []
    if len(RANGE) > 1:
        n = len(RANGE) - 1
        rc, pc = cagr(D_["revenue"].iloc[0], D_["revenue"].iloc[-1], n), cagr(D_["pat"].iloc[0], D_["pat"].iloc[-1], n)
        pts.append(f"Revenue grew from {fmt_value(D_['revenue'].iloc[0], 'cr')} ({RANGE[0]}) to {fmt_value(D_['revenue'].iloc[-1], 'cr')} "
                   f"({RANGE[-1]}), a CAGR of {rc:.1f}%; net profit CAGR was {pc:.1f}%.")
        dm = D_["ebitda_margin"].iloc[-1] - D_["ebitda_margin"].iloc[0]
        pts.append(f"EBITDA margin moved from {D_['ebitda_margin'].iloc[0]:.1f}% to {D_['ebitda_margin'].iloc[-1]:.1f}% ({dm:+.1f} pp).")
    nd = DA.loc[FY, "net_debt"]
    if pd.notna(nd):
        pts.append(f"In {FY} Britannia held a net cash position of {fmt_value(-nd, 'cr')}." if nd < 0
                   else f"In {FY} net debt stood at {fmt_value(nd, 'cr')} (debt less cash, bank balances and current investments).")
    fcf, pat = DA.loc[FY, "fcf"], DA.loc[FY, "pat"]
    if pd.notna(fcf) and pd.notna(pat) and pat:
        pts.append(f"Free cash flow in {FY} was {fmt_value(fcf, 'cr')}, or {fcf / pat * 100:.0f}% of net profit.")
    raw = RAW[BASIS]
    for fy in RANGE:
        ex, pbt = raw.loc[fy, "exceptional"], raw.loc[fy, "pbt"]
        if pd.notna(ex) and pd.notna(pbt) and pbt and abs(ex) / abs(pbt) > 0.02:
            pts.append(f"{fy} profit includes an exceptional {'income' if ex < 0 else 'expense'} of {fmt_value(abs(ex), 'cr')} "
                       f"({abs(ex) / abs(pbt) * 100:.0f}% of PBT), which distorts growth comparisons.")
    for t in pts:
        st.markdown(f'<div class="insight">{html.escape(t)}</div>', unsafe_allow_html=True)
    section("Summary table")
    table(["revenue", "ebitda", "pat", "total_assets", "total_debt", "cfo", "revenue_growth", "pat_growth"])
    source_line("PL")


def page_performance():
    header("Financial Performance", "Revenue, profitability, expenses and growth.")
    section("Metric explorer", "Choose any metric in the sidebar's 'Metric explorer' dropdown.")
    plot(CH.metric_chart(D_, ss["metric"], P), "perf_metric")
    m = METRICS[ss["metric"]]
    st.caption(f"{m.label} = {m.formula}. {m.note}")
    section("Revenue, EBITDA and EBIT")
    c1, c2 = st.columns(2)
    with c1:
        plot(CH.revenue_profit_trend(D_, P), "perf_rev")
    with c2:
        plot(CH.ebitda_ebit_pat(D_, P), "perf_ebitda")
    section("Expense analysis", "Interest and depreciation are shown separately from operating costs.")
    c1, c2 = st.columns([3, 2])
    with c1:
        plot(CH.expense_stack(D_, P), "perf_exp")
    with c2:
        plot(CH.expense_donut(DA, FY, P), "perf_donut")
    section("Year-on-year growth analysis")
    c1, c2 = st.columns(2)
    with c1:
        plot(CH.growth_comparison(D_, P), "perf_growth")
    with c2:
        plot(CH.yoy_heatmap(D_, P), "perf_heat")
    table(["revenue", "revenue_growth", "gross_profit", "ebitda", "ebitda_growth", "ebit", "pat", "pat_growth", "eps"])
    source_line("PL")


def page_profitability():
    header("Profitability Ratios", f"Margins and returns; tiles show {FY}.")
    keys = ["gross_margin", "ebitda_margin", "ebit_margin", "net_margin", "roe", "roa", "roce"]
    cards([(k, {}) for k in keys[:4]])
    cards([(k, {}) for k in keys[4:]], per_row=4)
    c1, c2 = st.columns(2)
    with c1:
        plot(CH.margins(D_, P, ("gross_margin", "ebitda_margin", "ebit_margin", "net_margin"), "Margin trends"), "pr_margins")
    with c2:
        plot(CH.ratio_comparison(D_, ["roe", "roa", "roce"], P, "Return ratios", "%"), "pr_returns")
    plot(CH.ratio_comparison(D_, keys, P, "Financial ratio comparison across years", "%"), "pr_all")
    table(keys)
    formulas(keys)
    source_line("PL")


def page_liquidity():
    header("Liquidity & Solvency", f"Short-term coverage and leverage; tiles show {FY}.")
    cards([("current_ratio", {}), ("quick_ratio", {}), ("debt_to_equity", {"invert": True}), ("interest_coverage", {})])
    c1, c2 = st.columns(2)
    with c1:
        plot(CH.liquidity_lines(D_, P), "lq_lines")
    with c2:
        plot(CH.solvency_chart(D_, P), "lq_solv")
    plot(CH.debt_cash_chart(D_, P), "lq_debt")
    table(["current_ratio", "quick_ratio", "debt_to_equity", "interest_coverage", "total_debt", "liquid_assets", "net_debt", "working_capital"])
    formulas(["current_ratio", "quick_ratio", "debt_to_equity", "interest_coverage", "net_debt"])
    source_line("BS")


def page_cashflow():
    header("Cash Flow Analysis", f"Cash generation, deployment and conversion; snapshots show {FY}.")
    cards([("cfo", {}), ("cfi", {}), ("cff", {}), ("fcf", {})])
    c1, c2 = st.columns(2)
    with c1:
        plot(CH.cashflow_bars(D_, P), "cf_bars")
    with c2:
        plot(CH.cash_conversion(D_, P), "cf_conv")
    plot(CH.cashflow_waterfall(DA, FY, P), "cf_wf")
    table(["cfo", "cfi", "cff", "capex", "fcf", "cfo_to_ebitda", "cfo_to_pat", "fcf_to_pat", "fcf_margin"])
    formulas(["fcf", "cfo_to_ebitda", "cfo_to_pat", "fcf_to_pat", "fcf_margin"])
    st.caption("FY2024 and FY2025 use the restated cash-flow figures from the following year's report (see Data quality).")
    source_line("CF")


def page_balance_sheet():
    header("Balance Sheet Analysis", f"Assets, funding and working capital; tiles show {FY}.")
    cards([("total_assets", {}), ("total_equity", {}), ("total_liabilities", {}), ("borrowings", {"invert": True}),
           ("working_capital", {})])
    plot(CH.bs_trend(D_, P), "bs_trend")
    plot(CH.bs_composition(D_, P), "bs_comp")
    table(["total_assets", "total_equity", "total_liabilities", "borrowings", "total_debt", "working_capital"])
    source_line("BS")


def page_compare():
    a, b = ss["cmp_a"], ss["cmp_b"]
    header("Compare Years", f"{a} versus {b} (choose years in the sidebar).")
    if a == b:
        st.warning("Years A and B are the same - pick two different years in the sidebar.")
    keys = ["revenue", "gross_profit", "ebitda", "ebit", "pat", "total_assets", "total_equity", "total_debt", "working_capital", "cfo", "fcf",
            "gross_margin", "ebitda_margin", "net_margin", "roe", "roa", "roce", "current_ratio", "quick_ratio", "debt_to_equity", "interest_coverage"]
    rows = []
    for k in keys:
        m, va, vb = METRICS[k], DA.loc[a, k], DA.loc[b, k]
        if pd.notna(va) and pd.notna(vb):
            if m.unit == "cr":
                ch = f"{vb - va:+,.0f}"
                pc = f"{(vb - va) / abs(va) * 100:+.1f}%" if va else "n/a"
            else:
                ch, pc = f"{vb - va:+.2f}{' pp' if m.unit == '%' else 'x'}", "-"
        else:
            ch, pc = "n/a", "n/a"
        rows.append([m.label, fmt_value(va, m.unit, 2 if m.unit != "cr" else 0), fmt_value(vb, m.unit, 2 if m.unit != "cr" else 0), ch, pc])
    t = pd.DataFrame(rows, columns=["Metric", a, b, "Change", "Change %"]).set_index("Metric")
    st.markdown(U.html_table(t), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        plot(CH.compare_bars(DA, a, b, ["revenue", "ebitda", "pat", "cfo", "fcf"], P, "Amounts (INR crore)"), "cmp_amt")
    with c2:
        plot(CH.compare_bars(DA, a, b, ["gross_margin", "ebitda_margin", "net_margin", "roe", "roa", "roce"], P, "Margins and returns (%)"), "cmp_pct")


def page_data():
    header("Data, Sources & Method", "Where every figure comes from, how ratios are defined, and data-quality checks.")
    t1, t2, t3, t4, t5 = st.tabs(["Sources & links", "Raw data", "Definitions", "Data quality", "Export"])
    with t1:
        if USING_UPLOAD:
            st.info("Showing user-uploaded data. Source columns are not available for uploaded workbooks.")
        else:
            st.markdown("Every FY uses the **latest report that contains it** (restated comparatives preferred). "
                        "Page numbers are PDF page indices of the annual-report files. Links open Britannia's website; "
                        "replace `REPORTS[...]['url']` in `data.py` with direct PDF links if you host the files.")
            reps = pd.DataFrame([{"Report": r["label"], "File": r["file"], "Link": r["url"]} for r in D.REPORTS.values()]).set_index("Report")
            st.markdown(U.html_table(reps, link_cols=("Link",)), unsafe_allow_html=True)
        st.markdown("&nbsp;", unsafe_allow_html=True)
        s = SRC[SRC["Basis"] == BASIS].drop(columns=["Basis"]).set_index("FY")
        st.markdown(U.html_table(s, link_cols=("Link",)), unsafe_allow_html=True)
        st.caption("Metric sources: P&L items from the statement of profit and loss, balance-sheet items from the balance sheet, "
                   "cash-flow items from the statement of cash flows; every derived metric lists its formula under 'Definitions'.")
    with t2:
        raw = RAW[BASIS].loc[RANGE]
        t = raw.T
        out = pd.DataFrame({fy: [fmt_value(v, "INR" if k == "eps" else "cr", 2) for k, v in t[fy].items()] for fy in t.columns}, index=t.index)
        out.insert(0, "Statement", [D.LINE_ITEMS.get(k, ("", "", ""))[1] for k in out.index])
        out.index = [D.LINE_ITEMS.get(k, (k,))[0] for k in out.index]
        out.index.name = f"Line item ({BASIS})"
        st.markdown(U.html_table(out, max_height=620), unsafe_allow_html=True)
        st.caption("EPS is in INR per share. 'n/a' = not reported / not applicable (e.g. associates on a standalone basis).")
    with t3:
        defs = pd.DataFrame({"Category": [m.category for m in METRICS.values()], "Unit": [m.unit for m in METRICS.values()],
                             "Formula": [m.formula for m in METRICS.values()], "Note": [m.note or "-" for m in METRICS.values()]},
                            index=[m.label for m in METRICS.values()])
        defs.index.name = "Metric"
        st.markdown(U.html_table(defs, max_height=620), unsafe_allow_html=True)
        st.caption("Ratios use closing balances (no averaging). EBITDA/EBIT exclude other income, exceptional items and share of associates "
                   "unless 'Treat other income as operating' is ticked.")
    with t4:
        for b in BASES:
            warn = validate_raw(RAW[b])
            if warn:
                st.warning(f"{b}: {len(warn)} check(s) failed")
                for w in warn:
                    st.write("- " + w)
            else:
                st.success(f"{b}: all accounting-identity checks passed (balance sheet balances, expenses sum, PBT/PAT bridge, cash movement).")
        miss = {b: int(RAW[b].isna().sum().sum()) for b in BASES}
        st.write("Missing values:", ", ".join(f"{b}: {n}" for b, n in miss.items()))
        if USING_UPLOAD:
            for n in ss["upload_notes"]:
                st.write("- " + n)
        else:
            st.markdown("**Restatements and notes**")
            for n in D.RESTATEMENT_NOTES:
                st.markdown(f"- {n}")
    with t5:
        st.download_button("Excel workbook (metrics, raw data, sources, definitions)", excel_bytes(RAW, OI, SRC, tuple(RANGE)),
                           "britannia_financials.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_xlsx_page", **BTN_KW)
        st.download_button("CSV - derived metrics (both bases, all years)", U.metrics_long(METRIC_ALL).to_csv(index=False).encode("utf-8"),
                           "britannia_metrics.csv", "text/csv", key="dl_csv_metrics", **BTN_KW)
        st.download_button("CSV - raw line items (long format)", D.to_long_dataframe(RAW).to_csv(index=False).encode("utf-8"),
                           "britannia_raw_line_items.csv", "text/csv", key="dl_csv_raw", **BTN_KW)


ROUTER = {PAGES[0]: page_overview, PAGES[1]: page_performance, PAGES[2]: page_profitability, PAGES[3]: page_liquidity,
          PAGES[4]: page_cashflow, PAGES[5]: page_balance_sheet, PAGES[6]: page_compare, PAGES[7]: page_data}
try:
    ROUTER[ss["nav"]]()
except Exception as exc:            # keep the app alive and explain what went wrong
    st.error(f"Something went wrong while rendering this page: {exc}")
    st.exception(exc)
