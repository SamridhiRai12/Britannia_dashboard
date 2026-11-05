"""charts.py - all Plotly figures used by the dashboard."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from calculations import METRICS, EXPENSE_COLS, yoy_table
from theme import style_fig

CR = "\u20b9%{y:,.0f} cr"


def _ax(fig, P, title_y=None, secondary=None):
    if title_y:
        fig.update_yaxes(title_text=title_y, title_font=dict(color=P["muted"]))
    return fig


def revenue_profit_trend(d, P):
    """Revenue (bars) with EBITDA and net profit (lines)."""
    fig = go.Figure()
    fig.add_bar(x=d.index, y=d["revenue"], name="Revenue", marker_color=P["series"][0], opacity=0.9,
                hovertemplate="Revenue: " + CR + "<extra></extra>")
    fig.add_scatter(x=d.index, y=d["ebitda"], name="EBITDA", mode="lines+markers",
                    line=dict(color=P["series"][2], width=3), hovertemplate="EBITDA: " + CR + "<extra></extra>")
    fig.add_scatter(x=d.index, y=d["pat"], name="Net profit", mode="lines+markers",
                    line=dict(color=P["series"][3], width=3), hovertemplate="Net profit: " + CR + "<extra></extra>")
    _ax(fig, P, "INR crore")
    return style_fig(fig, P, "Revenue and profit trend")


def ebitda_ebit_pat(d, P):
    fig = go.Figure()
    for i, (k, n) in enumerate([("ebitda", "EBITDA"), ("ebit", "EBIT"), ("pat", "Net profit")]):
        fig.add_scatter(x=d.index, y=d[k], name=n, mode="lines+markers", line=dict(width=3, color=P["series"][[2, 1, 3][i]]),
                        hovertemplate=n + ": " + CR + "<extra></extra>")
    _ax(fig, P, "INR crore")
    return style_fig(fig, P, "EBITDA, EBIT and net profit")


def margins(d, P, keys=("ebitda_margin", "net_margin"), title="EBITDA margin vs net profit margin"):
    fig = go.Figure()
    for i, k in enumerate(keys):
        fig.add_scatter(x=d.index, y=d[k], name=METRICS[k].label, mode="lines+markers+text",
                        text=[f"{v:.1f}%" if pd.notna(v) else "" for v in d[k]], textposition="top center",
                        line=dict(width=3, color=P["series"][i % 6]), textfont=dict(color=P["muted"], size=10),
                        hovertemplate=METRICS[k].label + ": %{y:.2f}%<extra></extra>")
    _ax(fig, P, "% of revenue")
    return style_fig(fig, P, title)


def metric_chart(d, key, P):
    """Selected metric as bars (+ YoY % line when the metric is an amount)."""
    m = METRICS[key]
    fmt = {"cr": "\u20b9%{y:,.0f} cr", "%": "%{y:.2f}%", "x": "%{y:.2f}x", "INR": "\u20b9%{y:.2f}"}[m.unit]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=d.index, y=d[key], name=m.label, marker_color=P["series"][0], hovertemplate=m.label + ": " + fmt + "<extra></extra>")
    if m.unit in ("cr", "INR"):
        prev = d[key].shift(1)
        yo = (d[key] - prev) / prev.abs() * 100
        fig.add_scatter(x=d.index, y=yo, name="YoY %", mode="lines+markers", line=dict(color=P["series"][2], width=3),
                        hovertemplate="YoY: %{y:.1f}%<extra></extra>", secondary_y=True)
        fig.update_yaxes(title_text="YoY %", secondary_y=True, showgrid=False)
    fig.update_yaxes(title_text={"cr": "INR crore", "%": "%", "x": "times", "INR": "INR"}[m.unit], secondary_y=False)
    return style_fig(fig, P, m.label + " - five-year view")


def ratio_comparison(d, keys, P, title, unit_label=""):
    """Grouped bars: one group per FY, one bar per ratio."""
    fig = go.Figure()
    for i, k in enumerate(keys):
        u = METRICS[k].unit
        t = "%{y:.1f}%" if u == "%" else "%{y:.2f}x"
        fig.add_bar(x=d.index, y=d[k], name=METRICS[k].label, marker_color=P["series"][i % 6],
                    hovertemplate=METRICS[k].label + ": " + t + "<extra></extra>")
    fig.update_layout(barmode="group")
    _ax(fig, P, unit_label)
    return style_fig(fig, P, title)


def liquidity_lines(d, P):
    fig = go.Figure()
    for i, k in enumerate(["current_ratio", "quick_ratio"]):
        fig.add_scatter(x=d.index, y=d[k], name=METRICS[k].label, mode="lines+markers", line=dict(width=3, color=P["series"][i]),
                        hovertemplate=METRICS[k].label + ": %{y:.2f}x<extra></extra>")
    fig.add_hline(y=1.0, line_dash="dot", line_color=P["muted"], annotation_text="1.0x", annotation_font_color=P["muted"])
    _ax(fig, P, "times")
    return style_fig(fig, P, "Current and quick ratio")


def solvency_chart(d, P):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=d.index, y=d["debt_to_equity"], name="Debt-to-equity", marker_color=P["series"][0],
                hovertemplate="D/E: %{y:.2f}x<extra></extra>")
    fig.add_scatter(x=d.index, y=d["interest_coverage"], name="Interest coverage", mode="lines+markers",
                    line=dict(color=P["series"][2], width=3), hovertemplate="Coverage: %{y:.1f}x<extra></extra>", secondary_y=True)
    fig.update_yaxes(title_text="D/E (x)", secondary_y=False)
    fig.update_yaxes(title_text="Interest cover (x)", secondary_y=True, showgrid=False)
    return style_fig(fig, P, "Leverage vs interest coverage")


def debt_cash_chart(d, P):
    fig = go.Figure()
    fig.add_bar(x=d.index, y=d["total_debt"], name="Total debt", marker_color=P["series"][0], hovertemplate="Debt: " + CR + "<extra></extra>")
    fig.add_bar(x=d.index, y=d["liquid_assets"], name="Cash, bank & current investments", marker_color=P["series"][3],
                hovertemplate="Liquid assets: " + CR + "<extra></extra>")
    fig.add_scatter(x=d.index, y=d["net_debt"], name="Net debt / (net cash)", mode="lines+markers",
                    line=dict(color=P["series"][2], width=3), hovertemplate="Net debt: " + CR + "<extra></extra>")
    fig.update_layout(barmode="group")
    _ax(fig, P, "INR crore")
    return style_fig(fig, P, "Debt vs liquid assets")


def cashflow_bars(d, P):
    fig = go.Figure()
    for i, (k, n) in enumerate([("cfo", "Operating"), ("cfi", "Investing"), ("cff", "Financing")]):
        fig.add_bar(x=d.index, y=d[k], name=n, marker_color=[P["series"][0], P["series"][2], P["series"][4]][i],
                    hovertemplate=n + ": " + CR + "<extra></extra>")
    fig.add_scatter(x=d.index, y=d["fcf"], name="Free cash flow", mode="lines+markers",
                    line=dict(color=P["series"][3], width=3), hovertemplate="FCF: " + CR + "<extra></extra>")
    fig.update_layout(barmode="group")
    _ax(fig, P, "INR crore")
    return style_fig(fig, P, "Cash flow by activity and free cash flow")


def cash_conversion(d, P):
    fig = go.Figure()
    for i, k in enumerate(["cfo_to_ebitda", "cfo_to_pat", "fcf_to_pat"]):
        fig.add_scatter(x=d.index, y=d[k], name=METRICS[k].label, mode="lines+markers", line=dict(width=3, color=P["series"][i]),
                        hovertemplate=METRICS[k].label + ": %{y:.1f}%<extra></extra>")
    fig.add_hline(y=100, line_dash="dot", line_color=P["muted"])
    _ax(fig, P, "%")
    return style_fig(fig, P, "Cash conversion")


def cashflow_waterfall(d, fy, P):
    """Opening cash -> CFO -> CFI -> CFF -> FX -> closing cash for one FY."""
    r = d.loc[fy]
    vals = [r["cash_open"], r["cfo"], r["cfi"], r["cff"], r["fx_effect"], r["cash_close"]]
    if any(pd.isna(v) for v in vals):
        return None
    fig = go.Figure(go.Waterfall(
        x=["Opening cash", "Operating", "Investing", "Financing", "FX effect", "Closing cash"],
        measure=["absolute", "relative", "relative", "relative", "relative", "total"],
        y=vals, text=[f"{v:,.0f}" for v in vals], textposition="outside",
        connector=dict(line=dict(color=P["muted"], width=1)),
        increasing=dict(marker=dict(color=P["pos"])), decreasing=dict(marker=dict(color=P["neg"])),
        totals=dict(marker=dict(color=P["series"][0])),
        hovertemplate="%{x}: \u20b9%{y:,.2f} cr<extra></extra>"))
    _ax(fig, P, "INR crore")
    fig.update_layout(hovermode="closest")
    return style_fig(fig, P, f"Cash flow waterfall - {fy}", legend=False)


def bs_composition(d, P):
    """Two stacked-bar panels: asset mix and funding mix."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Asset composition", "Funding composition"), horizontal_spacing=0.08)
    assets = [("asset_ppe_cwip", "PPE & CWIP"), ("asset_investments", "Investments"), ("asset_inventories", "Inventories"),
              ("asset_receivables", "Trade receivables"), ("asset_cash_bank", "Cash & bank"), ("asset_other", "Other assets")]
    fund = [("fund_equity", "Equity"), ("fund_nc_liab", "Non-current liabilities"), ("fund_c_liab", "Current liabilities")]
    for i, (k, n) in enumerate(assets):
        fig.add_bar(x=d.index, y=d[k], name=n, legendgroup="a", marker_color=P["series"][i % 6],
                    hovertemplate=n + ": " + CR + "<extra></extra>", row=1, col=1)
    for i, (k, n) in enumerate(fund):
        fig.add_bar(x=d.index, y=d[k], name=n, legendgroup="f", marker_color=[P["series"][0], P["series"][2], P["series"][5]][i],
                    hovertemplate=n + ": " + CR + "<extra></extra>", row=1, col=2)
    fig.update_layout(barmode="stack")
    fig = style_fig(fig, P, "Balance sheet composition", height=440)
    fig.update_layout(legend=dict(orientation="h", y=-0.2, font=dict(color=P["text"])))
    fig.update_annotations(font=dict(color=P["muted"], size=12))
    return fig


def bs_trend(d, P):
    fig = go.Figure()
    for i, (k, n) in enumerate([("total_assets", "Total assets"), ("total_equity", "Total equity"),
                                ("total_liabilities", "Total liabilities"), ("borrowings", "Borrowings"), ("working_capital", "Working capital")]):
        fig.add_scatter(x=d.index, y=d[k], name=n, mode="lines+markers", line=dict(width=3, color=P["series"][i % 6]),
                        hovertemplate=n + ": " + CR + "<extra></extra>")
    _ax(fig, P, "INR crore")
    return style_fig(fig, P, "Balance sheet trends")


def growth_comparison(d, P):
    fig = go.Figure()
    for i, k in enumerate(["revenue_growth", "pat_growth"]):
        fig.add_bar(x=d.index, y=d[k], name=METRICS[k].label, marker_color=P["series"][[0, 3][i]],
                    text=[f"{v:.1f}%" if pd.notna(v) else "n/a" for v in d[k]], textposition="outside",
                    hovertemplate=METRICS[k].label + ": %{y:.1f}%<extra></extra>")
    fig.update_layout(barmode="group")
    _ax(fig, P, "YoY %")
    return style_fig(fig, P, "Revenue growth vs net profit growth")


def expense_stack(d, P):
    fig = go.Figure()
    for i, (k, n) in enumerate(EXPENSE_COLS.items()):
        fig.add_bar(x=d.index, y=d[k], name=n, marker_color=P["series"][i % 6], hovertemplate=n + ": " + CR + "<extra></extra>")
    fig.update_layout(barmode="stack")
    _ax(fig, P, "INR crore")
    return style_fig(fig, P, "Expense breakdown by year", height=420)


def expense_donut(d, fy, P):
    r = d.loc[fy]
    labels = list(EXPENSE_COLS.values())
    values = [max(r[k], 0) if pd.notna(r[k]) else 0 for k in EXPENSE_COLS]
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.58, sort=False,
                           marker=dict(colors=P["series"], line=dict(color=P["bg"], width=2)),
                           textinfo="percent", hovertemplate="%{label}<br>\u20b9%{value:,.0f} cr (%{percent})<extra></extra>"))
    fig.update_layout(hovermode="closest")
    return style_fig(fig, P, f"Expense mix - {fy}", height=420)


def yoy_heatmap(d, P, keys=("revenue", "gross_profit", "ebitda", "ebit", "pat", "total_assets", "total_equity", "total_debt", "cfo", "fcf")):
    z = yoy_table(d, list(keys))
    text = z.map(lambda v: f"{v:.1f}%" if pd.notna(v) else "n/a") if hasattr(z, "map") else z.applymap(lambda v: f"{v:.1f}%" if pd.notna(v) else "n/a")
    cs = [[0, P["neg"]], [0.5, P["card"]], [1, P["pos"]]]
    fig = go.Figure(go.Heatmap(z=z.values, x=list(z.columns), y=list(z.index), text=text.values, texttemplate="%{text}",
                               colorscale=cs, zmid=0, zmin=-40, zmax=40, xgap=3, ygap=3, colorbar=dict(title="YoY %", tickfont=dict(color=P["muted"])),
                               hovertemplate="%{y}<br>%{x}: %{text}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_layout(hovermode="closest")
    return style_fig(fig, P, "Year-on-year growth heatmap (grey/n/a = prior year not in dataset)", height=420, legend=False)


def compare_bars(d, fy_a, fy_b, keys, P, title):
    fig = go.Figure()
    for fy, c in [(fy_a, P["series"][1]), (fy_b, P["series"][0])]:
        fig.add_bar(x=[METRICS[k].label for k in keys], y=[d.loc[fy, k] for k in keys], name=fy, marker_color=c,
                    hovertemplate="%{x}: %{y:,.2f}<extra>" + fy + "</extra>")
    fig.update_layout(barmode="group")
    return style_fig(fig, P, title)
