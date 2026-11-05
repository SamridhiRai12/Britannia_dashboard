"""
calculations.py - derived metrics, ratios, growth rates and data validation.

Every metric is registered in METRICS with its unit, formula and explanation so
the dashboard's definitions page, tooltips and exports stay in sync.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

REQUIRED_KEYS = ["revenue_ops", "pat", "total_assets", "equity_total", "cfo"]


@dataclass(frozen=True)
class Metric:
    key: str
    label: str
    unit: str          # "cr" (INR crore), "%", "x", "INR"
    category: str
    formula: str
    note: str = ""


def _m(*a):
    return Metric(*a)


METRICS: dict[str, Metric] = {m.key: m for m in [
    # ---- Performance (INR crore)
    _m("revenue", "Revenue from operations", "cr", "Performance", "Sale of goods + Other operating revenues", "P&L"),
    _m("gross_profit", "Gross profit", "cr", "Performance", "Revenue - (Materials consumed + Purchases of stock-in-trade + Changes in inventories)", "Derived from P&L"),
    _m("ebitda", "EBITDA", "cr", "Performance", "(Total income - Total expenses) + Finance costs + D&A  [- Other income if 'exclude other income']", "Before exceptional items and share of associates"),
    _m("ebit", "EBIT", "cr", "Performance", "EBITDA - Depreciation & amortisation", "Same basis as EBITDA"),
    _m("pbt", "Profit before tax", "cr", "Performance", "As reported (after exceptional items)", "P&L"),
    _m("pat", "Net profit (PAT)", "cr", "Performance", "Profit for the year (consolidated: incl. non-controlling interests)", "P&L"),
    _m("pat_owners", "Net profit - owners", "cr", "Performance", "Profit attributable to owners of the Company", "P&L"),
    _m("total_expenses", "Total expenses", "cr", "Performance", "As reported", "P&L"),
    _m("other_income", "Other income", "cr", "Performance", "As reported", "P&L"),
    # ---- Margins / returns
    _m("gross_margin", "Gross profit margin", "%", "Profitability", "Gross profit / Revenue x 100"),
    _m("ebitda_margin", "EBITDA margin", "%", "Profitability", "EBITDA / Revenue x 100"),
    _m("ebit_margin", "EBIT margin", "%", "Profitability", "EBIT / Revenue x 100"),
    _m("net_margin", "Net profit margin", "%", "Profitability", "PAT / Revenue x 100"),
    _m("roe", "Return on equity (ROE)", "%", "Profitability", "PAT attributable to owners / Closing equity attributable to owners x 100", "Closing-balance basis"),
    _m("roa", "Return on assets (ROA)", "%", "Profitability", "PAT / Closing total assets x 100", "Closing-balance basis"),
    _m("roce", "Return on capital employed (ROCE)", "%", "Profitability", "EBIT / (Total assets - Current liabilities) x 100", "Closing-balance basis"),
    # ---- Liquidity & solvency
    _m("current_ratio", "Current ratio", "x", "Liquidity & Solvency", "Current assets / Current liabilities"),
    _m("quick_ratio", "Quick ratio", "x", "Liquidity & Solvency", "(Current assets - Inventories) / Current liabilities"),
    _m("debt_to_equity", "Debt-to-equity", "x", "Liquidity & Solvency", "Total debt / Total equity", "Total debt = borrowings + lease liabilities"),
    _m("interest_coverage", "Interest coverage", "x", "Liquidity & Solvency", "EBIT / Finance costs"),
    _m("liquid_assets", "Cash, bank & current investments", "cr", "Liquidity & Solvency", "Cash + Bank balances + Current investments", "BS"),
    _m("net_debt", "Net debt / (net cash)", "cr", "Liquidity & Solvency", "Total debt - (Cash + Bank balances + Current investments)", "Negative = net cash"),
    # ---- Cash flow
    _m("cfo", "Operating cash flow", "cr", "Cash flow", "Net cash from operating activities", "CF"),
    _m("cfi", "Investing cash flow", "cr", "Cash flow", "Net cash from/(used in) investing activities", "CF"),
    _m("cff", "Financing cash flow", "cr", "Cash flow", "Net cash from/(used in) financing activities", "CF"),
    _m("capex", "Capex", "cr", "Cash flow", "Acquisition of PPE, CWIP and intangibles", "CF"),
    _m("fcf", "Free cash flow", "cr", "Cash flow", "Operating cash flow - Capex"),
    _m("cfo_to_ebitda", "Cash conversion (CFO / EBITDA)", "%", "Cash flow", "CFO / EBITDA x 100"),
    _m("cfo_to_pat", "CFO / Net profit", "%", "Cash flow", "CFO / PAT x 100"),
    _m("fcf_to_pat", "FCF / Net profit", "%", "Cash flow", "FCF / PAT x 100"),
    _m("fcf_margin", "FCF margin", "%", "Cash flow", "FCF / Revenue x 100"),
    # ---- Balance sheet
    _m("total_assets", "Total assets", "cr", "Balance sheet", "As reported", "BS"),
    _m("total_equity", "Total equity", "cr", "Balance sheet", "As reported", "BS"),
    _m("total_liabilities", "Total liabilities", "cr", "Balance sheet", "As reported", "BS"),
    _m("borrowings", "Borrowings", "cr", "Balance sheet", "Non-current + Current borrowings", "BS"),
    _m("total_debt", "Total debt", "cr", "Balance sheet", "Borrowings + Lease liabilities", "BS"),
    _m("working_capital", "Working capital", "cr", "Balance sheet", "Current assets - Current liabilities", "BS"),
    # ---- Growth
    _m("revenue_growth", "Revenue growth (YoY)", "%", "Growth", "(Revenue t / Revenue t-1 - 1) x 100", "FY2022 missing (FY2021 not in dataset)"),
    _m("ebitda_growth", "EBITDA growth (YoY)", "%", "Growth", "(EBITDA t / EBITDA t-1 - 1) x 100"),
    _m("pat_growth", "Net profit growth (YoY)", "%", "Growth", "(PAT t / PAT t-1 - 1) x 100"),
    _m("eps", "Basic EPS", "INR", "Performance", "As reported", "P&L"),
]}

# Expense categories used by the expense analysis (key in derived frame -> label)
EXPENSE_COLS = {
    "exp_materials": "Raw materials consumed",
    "exp_trading": "Traded goods (net of inventory change)",
    "exp_employee": "Employee benefits",
    "exp_other": "Other expenses",
    "exp_dna": "Depreciation & amortisation",
    "exp_finance": "Finance costs",
}


def safe_div(a, b):
    """Element-wise a / b -> NaN when b is 0 / NaN (never raises)."""
    a = pd.to_numeric(a, errors="coerce")
    b = pd.to_numeric(b, errors="coerce")
    return a / b.where(b.abs() > 1e-12)


def validate_raw(df: pd.DataFrame, tol: float = 1.0) -> list[str]:
    """Accounting-identity checks. Returns human-readable warnings (empty = clean)."""
    w = []
    g = lambda k: df[k] if k in df else pd.Series(np.nan, index=df.index)
    chk = [
        ("Total assets = non-current + current assets", g("total_assets"), g("non_current_assets") + g("current_assets")),
        ("Total assets = equity + liabilities", g("total_assets"), g("equity_total") + g("total_liabilities")),
        ("Total liabilities = non-current + current", g("total_liabilities"), g("nc_liabilities") + g("current_liabilities")),
        ("Total income = revenue + other income", g("total_income"), g("revenue_ops") + g("other_income")),
        ("Revenue = goods + other operating", g("revenue_ops"), g("rev_sale_goods") + g("rev_other_op")),
        ("Total expenses = sum of expense lines", g("total_expenses"),
         g("materials") + g("purchases_sit") + g("chg_inventory") + g("employee") + g("finance_costs") + g("dna") + g("other_expenses")),
        ("PAT = PBT - tax", g("pat"), g("pbt") - g("tax")),
        ("PBT = Income - expenses + associates - exceptional", g("pbt"),
         g("total_income") - g("total_expenses") + g("share_assoc").fillna(0) - g("exceptional")),
        ("Net cash change = CFO + CFI + CFF", g("cash_close") - g("cash_open") - g("fx_effect").fillna(0),
         g("cfo") + g("cfi") + g("cff")),
    ]
    for name, a, b in chk:
        diff = (a - b).abs()
        for fy, d in diff.items():
            if pd.notna(d) and d > tol:
                w.append(f"{fy}: '{name}' off by {d:,.2f}")
    return w


def compute_metrics(raw: pd.DataFrame, other_income_operating: bool = False) -> pd.DataFrame:
    """Derive all dashboard metrics from raw line items (index = FY, ascending)."""
    r = raw.sort_index().copy()
    g = lambda k: pd.to_numeric(r[k], errors="coerce") if k in r else pd.Series(np.nan, index=r.index)
    d = pd.DataFrame(index=r.index)

    d["revenue"] = g("revenue_ops")
    cogs = g("materials") + g("purchases_sit") + g("chg_inventory")
    d["gross_profit"] = d["revenue"] - cogs
    op_profit = g("total_income") - g("total_expenses")           # before assoc. & exceptionals
    ebitda = op_profit + g("finance_costs") + g("dna")
    if not other_income_operating:
        ebitda = ebitda - g("other_income")
    d["ebitda"] = ebitda
    d["ebit"] = ebitda - g("dna")
    for k in ["pbt", "pat", "pat_owners", "total_expenses", "other_income", "eps"]:
        d[k] = g(k)
    d["finance_costs"] = g("finance_costs")

    # margins & returns
    d["gross_margin"] = safe_div(d["gross_profit"], d["revenue"]) * 100
    d["ebitda_margin"] = safe_div(d["ebitda"], d["revenue"]) * 100
    d["ebit_margin"] = safe_div(d["ebit"], d["revenue"]) * 100
    d["net_margin"] = safe_div(d["pat"], d["revenue"]) * 100
    d["roe"] = safe_div(d["pat_owners"], g("equity_parent")) * 100
    d["roa"] = safe_div(d["pat"], g("total_assets")) * 100
    cap_emp = g("total_assets") - g("current_liabilities")
    d["roce"] = safe_div(d["ebit"], cap_emp) * 100

    # balance sheet
    d["total_assets"] = g("total_assets")
    d["total_equity"] = g("equity_total")
    d["total_liabilities"] = g("total_liabilities")
    d["borrowings"] = g("nc_borrowings") + g("c_borrowings")
    d["lease_liabilities"] = g("nc_lease") + g("c_lease")
    d["total_debt"] = d["borrowings"] + d["lease_liabilities"]
    d["working_capital"] = g("current_assets") - g("current_liabilities")
    liquid = g("cash") + g("bank_balances") + g("current_investments")
    d["liquid_assets"] = liquid
    d["net_debt"] = d["total_debt"] - liquid

    # liquidity & solvency
    d["current_ratio"] = safe_div(g("current_assets"), g("current_liabilities"))
    d["quick_ratio"] = safe_div(g("current_assets") - g("inventories"), g("current_liabilities"))
    d["debt_to_equity"] = safe_div(d["total_debt"], d["total_equity"])
    d["interest_coverage"] = safe_div(d["ebit"], g("finance_costs"))

    # cash flow
    for k in ["cfo", "cfi", "cff", "capex", "fx_effect", "cash_open", "cash_close"]:
        d[k] = g(k)
    d["fcf"] = d["cfo"] - d["capex"]
    d["cfo_to_ebitda"] = safe_div(d["cfo"], d["ebitda"]) * 100
    d["cfo_to_pat"] = safe_div(d["cfo"], d["pat"]) * 100
    d["fcf_to_pat"] = safe_div(d["fcf"], d["pat"]) * 100
    d["fcf_margin"] = safe_div(d["fcf"], d["revenue"]) * 100

    # growth (first year stays NaN - prior year not in dataset)
    for src, dst in [("revenue", "revenue_growth"), ("ebitda", "ebitda_growth"), ("pat", "pat_growth")]:
        prev = d[src].shift(1)
        d[dst] = (safe_div(d[src], prev) - 1) * 100
        d.loc[prev.abs() <= 1e-12, dst] = np.nan
        d.loc[prev <= 0, dst] = np.nan   # growth off a non-positive base is not meaningful

    # expense analysis
    d["exp_materials"] = g("materials")
    d["exp_trading"] = g("purchases_sit") + g("chg_inventory")
    d["exp_employee"] = g("employee")
    d["exp_other"] = g("other_expenses")
    d["exp_dna"] = g("dna")
    d["exp_finance"] = g("finance_costs")

    # balance-sheet composition
    d["asset_ppe_cwip"] = g("ppe") + g("cwip")
    d["asset_investments"] = g("nc_investments") + g("current_investments")
    d["asset_inventories"] = g("inventories")
    d["asset_receivables"] = g("trade_receivables")
    d["asset_cash_bank"] = g("cash") + g("bank_balances")
    d["asset_other"] = g("total_assets") - (d["asset_ppe_cwip"] + d["asset_investments"]
                       + d["asset_inventories"] + d["asset_receivables"] + d["asset_cash_bank"])
    d["fund_equity"] = g("equity_total")
    d["fund_nc_liab"] = g("nc_liabilities")
    d["fund_c_liab"] = g("current_liabilities")
    return d


def cagr(first: float, last: float, years: int) -> float:
    if years <= 0 or pd.isna(first) or pd.isna(last) or first <= 0 or last <= 0:
        return float("nan")
    return ((last / first) ** (1 / years) - 1) * 100


def yoy_table(d: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """YoY % change for the given metric keys (rows = metrics, cols = FY)."""
    out = {}
    for k in keys:
        s = d[k]
        prev = s.shift(1)
        yo = (s - prev) / prev.abs() * 100
        yo[prev.abs() <= 1e-12] = np.nan
        out[METRICS[k].label if k in METRICS else k] = yo
    return pd.DataFrame(out).T


def fmt_value(v, unit: str, dec: int | None = None) -> str:
    """Format a number for display; missing -> 'n/a'."""
    if v is None or (isinstance(v, float) and np.isnan(v)) or pd.isna(v):
        return "n/a"
    if unit == "%":
        return f"{v:,.{1 if dec is None else dec}f}%"
    if unit == "x":
        return f"{v:,.{2 if dec is None else dec}f}x"
    if unit == "INR":
        return f"\u20b9{v:,.{2 if dec is None else dec}f}"
    return f"\u20b9{v:,.{0 if dec is None else dec}f} cr"
