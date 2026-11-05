"""
data.py - Britannia Industries Ltd. five-year financial dataset (FY2022 - FY2026)
=================================================================================
All amounts are in INR crore unless stated (EPS is in INR per share).

Source policy
-------------
Every figure was transcribed from the audited financial statements in Britannia's
annual reports. Each financial year uses the MOST RECENT report that contains it
(i.e. restated comparatives are preferred over the figures first published):

    FY2026, FY2025 -> Annual Report 2025-26   (FY2025 = comparative column)
    FY2024         -> Annual Report 2024-25   (comparative column)
    FY2023         -> Annual Report 2023-24   (comparative column)
    FY2022         -> Annual Report 2022-23   (comparative column; spot-checked
                                               against Annual Report 2021-22)

Sign conventions
----------------
* Expenses, capex, tax are positive numbers.  `exceptional` is an EXPENSE when
  positive and an INCOME when negative.  `chg_inventory` is as printed in the
  P&L (negative = inventory build, reduces expense).
* `cfo`, `cfi`, `cff` are signed as printed (outflow negative).  `capex` is
  stored as a positive outflow.
* Missing / not applicable values are `None` (-> NaN) and are shown as "n/a".
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FY_LABELS = ["FY2022", "FY2023", "FY2024", "FY2025", "FY2026"]
BASES = ["Consolidated", "Standalone"]
UNIT = "INR crore"

# --------------------------------------------------------------------------- #
# Line-item catalogue: key -> (description, statement, unit)
# --------------------------------------------------------------------------- #
LINE_ITEMS = {
    # ---- Statement of Profit & Loss
    "rev_sale_goods":   ("Sale of goods", "P&L", UNIT),
    "rev_other_op":     ("Other operating revenues", "P&L", UNIT),
    "revenue_ops":      ("Revenue from operations", "P&L", UNIT),
    "other_income":     ("Other income", "P&L", UNIT),
    "total_income":     ("Total income", "P&L", UNIT),
    "materials":        ("Cost of materials consumed", "P&L", UNIT),
    "purchases_sit":    ("Purchases of stock-in-trade", "P&L", UNIT),
    "chg_inventory":    ("Changes in inventories of FG, WIP and stock-in-trade", "P&L", UNIT),
    "employee":         ("Employee benefits expense", "P&L", UNIT),
    "finance_costs":    ("Finance costs", "P&L", UNIT),
    "dna":              ("Depreciation and amortisation expense", "P&L", UNIT),
    "other_expenses":   ("Other expenses", "P&L", UNIT),
    "total_expenses":   ("Total expenses", "P&L", UNIT),
    "share_assoc":      ("Share of profit/(loss) of associates & JV (consolidated only)", "P&L", UNIT),
    "exceptional":      ("Exceptional items - expense / (income)", "P&L", UNIT),
    "pbt":              ("Profit before tax", "P&L", UNIT),
    "tax":              ("Total tax expense", "P&L", UNIT),
    "pat":              ("Profit for the year", "P&L", UNIT),
    "pat_owners":       ("Profit attributable to owners of the Company", "P&L", UNIT),
    "eps":              ("Basic earnings per share (INR)", "P&L", "INR per share"),
    # ---- Balance sheet
    "ppe":                 ("Property, plant and equipment", "BS", UNIT),
    "cwip":                ("Capital work-in-progress", "BS", UNIT),
    "nc_investments":      ("Non-current investments (financial assets)", "BS", UNIT),
    "non_current_assets":  ("Total non-current assets", "BS", UNIT),
    "inventories":         ("Inventories", "BS", UNIT),
    "current_investments": ("Current investments", "BS", UNIT),
    "trade_receivables":   ("Trade receivables", "BS", UNIT),
    "cash":                ("Cash and cash equivalents", "BS", UNIT),
    "bank_balances":       ("Bank balances other than cash equivalents", "BS", UNIT),
    "current_assets":      ("Total current assets", "BS", UNIT),
    "total_assets":        ("Total assets", "BS", UNIT),
    "equity_total":        ("Total equity", "BS", UNIT),
    "equity_parent":       ("Equity attributable to owners of the parent", "BS", UNIT),
    "nc_borrowings":       ("Non-current borrowings", "BS", UNIT),
    "nc_lease":            ("Non-current lease liabilities", "BS", UNIT),
    "nc_liabilities":      ("Total non-current liabilities", "BS", UNIT),
    "c_borrowings":        ("Current borrowings", "BS", UNIT),
    "c_lease":             ("Current lease liabilities", "BS", UNIT),
    "trade_payables":      ("Trade payables (MSME + others)", "BS", UNIT),
    "current_liabilities": ("Total current liabilities", "BS", UNIT),
    "total_liabilities":   ("Total liabilities", "BS", UNIT),
    # ---- Cash-flow statement
    "cfo":         ("Net cash from operating activities", "CF", UNIT),
    "cfi":         ("Net cash from / (used in) investing activities", "CF", UNIT),
    "cff":         ("Net cash from / (used in) financing activities", "CF", UNIT),
    "capex":       ("Acquisition of PPE, CWIP & intangibles (capex)", "CF", UNIT),
    "fx_effect":   ("Effect of exchange-rate changes on cash", "CF", UNIT),
    "cash_open":   ("Cash & equivalents at start of year (net of overdraft)", "CF", UNIT),
    "cash_close":  ("Cash & equivalents at end of year (net of overdraft)", "CF", UNIT),
}
N = None  # shorthand for "missing / not applicable"

# values are listed in FY order: FY2022, FY2023, FY2024, FY2025, FY2026
_RAW = {
"Consolidated": {
 "rev_sale_goods":[13944.67,15984.90,16546.21,17535.02,18858.21],
 "rev_other_op":[191.59,315.65,223.06,407.65,293.38],
 "revenue_ops":[14136.26,16300.55,16769.27,17942.67,19151.59],
 "other_income":[222.83,215.86,214.18,227.09,224.03],
 "total_income":[14359.09,16516.41,16983.45,18169.76,19375.62],
 "materials":[7473.97,8326.70,8546.89,9859.45,10350.02],
 "purchases_sit":[1361.59,1337.13,941.48,809.35,805.23],
 "chg_inventory":[-75.26,-72.53,3.66,-64.75,-22.37],
 "employee":[542.26,658.38,708.70,704.59,823.80],
 "finance_costs":[144.29,169.10,164.00,138.80,112.76],
 "dna":[200.54,225.91,300.46,313.34,336.83],
 "other_expenses":[2632.19,3219.96,3398.70,3446.88,3650.48],
 "total_expenses":[12279.58,13864.65,14063.89,15207.66,16056.75],
 "share_assoc":[-0.20,5.41,-3.19,-10.74,-30.09],
 "exceptional":[0.98,-375.60,2.90,24.79,0.00],
 "pbt":[2078.33,3032.77,2913.47,2926.57,3288.78],
 "tax":[562.35,716.45,779.25,748.71,751.77],
 "pat":[1515.98,2316.32,2134.22,2177.86,2537.01],
 "pat_owners":[1524.82,2321.77,2139.81,2178.73,2533.49],
 "eps":[63.31,96.39,88.84,90.45,105.18],
 "ppe":[1584.05,2472.19,2602.94,2734.61,2672.98],
 "cwip":[535.68,105.00,187.54,89.20,39.04],
 "nc_investments":[926.55,1028.09,575.85,1270.17,1517.71],
 "non_current_assets":[3545.11,4606.49,4224.90,4924.87,5054.28],
 "inventories":[1367.49,1193.26,1181.22,1236.51,1345.93],
 "current_investments":[833.73,1800.99,1696.51,1111.64,1638.52],
 "trade_receivables":[331.93,328.94,393.33,448.61,469.21],
 "cash":[117.99,102.38,322.80,132.78,220.00],
 "bank_balances":[66.91,95.60,123.55,179.70,132.44],
 "current_assets":[3982.30,4746.23,4848.66,3913.68,4677.66],
 "total_assets":[7527.41,9352.72,9073.56,8838.55,9731.94],
 "equity_total":[2585.60,3564.50,3966.02,4381.32,5135.88],
 "equity_parent":[2558.10,3534.27,3941.52,4355.72,5106.56],
 "nc_borrowings":[706.99,1551.80,904.72,712.94,286.11],
 "nc_lease":[13.76,14.36,20.13,19.45,19.31],
 "nc_liabilities":[794.67,1653.82,1023.13,838.97,416.07],
 "c_borrowings":[1758.55,1428.71,1136.49,511.83,1071.72],
 "c_lease":[1.90,2.50,3.62,2.29,3.14],
 "trade_payables":[1322.81,1448.81,1627.48,1752.23,1896.41],
 "current_liabilities":[4147.14,4134.40,4084.41,3618.26,4179.99],
 "total_liabilities":[4941.81,5788.22,5107.54,4457.23,4596.06],
 "cfo":[1299.52,2526.21,2572.98,2490.62,2611.60],
 "cfi":[910.89,-1517.06,484.15,66.43,-757.27],
 "cff":[-2245.84,-1028.37,-2839.13,-2753.90,-1782.62],
 "capex":[550.18,711.46,552.87,374.85,205.57],
 "fx_effect":[3.30,10.06,1.29,2.64,15.89],
 "cash_open":[141.45,109.32,100.16,319.45,125.24],
 "cash_close":[109.32,100.16,319.45,125.24,212.84],
},
"Standalone": {
 "rev_sale_goods":[13169.04,15285.12,15938.87,16859.22,18119.45],
 "rev_other_op":[202.58,333.30,247.21,436.70,326.37],
 "revenue_ops":[13371.62,15618.42,16186.08,17295.92,18445.82],
 "other_income":[359.43,220.59,210.11,250.68,318.44],
 "total_income":[13731.05,15839.01,16396.19,17546.60,18764.26],
 "materials":[6366.31,7084.09,7394.74,8608.64,9045.68],
 "purchases_sit":[2183.41,2453.42,2033.36,1993.16,2028.01],
 "chg_inventory":[-73.96,-82.13,0.01,-67.96,-21.42],
 "employee":[413.56,520.55,565.28,554.70,667.47],
 "finance_costs":[133.46,154.95,151.40,137.10,110.80],
 "dna":[170.01,195.10,271.19,284.67,305.34],
 "other_expenses":[2393.14,2900.70,3121.87,3143.73,3335.04],
 "total_expenses":[11585.93,13226.68,13537.85,14654.04,15470.92],
 "share_assoc":[N,N,N,N,N],
 "exceptional":[0.00,-227.74,2.90,24.79,0.00],
 "pbt":[2145.12,2840.07,2855.44,2867.77,3293.34],
 "tax":[541.93,700.77,773.39,737.05,731.62],
 "pat":[1603.19,2139.30,2082.05,2130.72,2561.72],
 "pat_owners":[1603.19,2139.30,2082.05,2130.72,2561.72],
 "eps":[66.56,88.82,86.44,88.46,106.35],
 "ppe":[1327.41,2220.21,2365.04,2509.41,2426.37],
 "cwip":[535.27,104.47,187.48,81.97,38.35],
 "nc_investments":[1221.61,1525.18,1080.04,1801.03,2066.72],
 "non_current_assets":[3409.89,4217.76,3851.13,4583.29,4752.76],
 "inventories":[1251.64,1074.62,1075.44,1128.90,1219.92],
 "current_investments":[802.50,1798.47,1690.68,1071.12,1617.02],
 "trade_receivables":[253.85,278.42,347.05,379.63,404.74],
 "cash":[9.97,9.09,240.85,38.19,20.79],
 "bank_balances":[42.32,54.76,56.65,67.45,70.03],
 "current_assets":[3604.94,4420.70,4519.71,3436.43,4187.68],
 "total_assets":[7014.83,8638.46,8370.84,8019.72,8940.44],
 "equity_total":[2402.54,3181.15,3527.52,3886.55,4641.23],
 "equity_parent":[2402.54,3181.15,3527.52,3886.55,4641.23],
 "nc_borrowings":[698.52,1551.02,904.17,712.50,285.83],
 "nc_lease":[0.03,0.76,0.50,0.48,0.36],
 "nc_liabilities":[750.94,1611.93,970.24,785.04,358.99],
 "c_borrowings":[1479.62,1110.76,1132.97,504.05,1060.33],
 "c_lease":[0.57,1.17,2.00,0.65,1.26],
 "trade_payables":[1194.21,1308.76,1513.14,1592.40,1781.87],
 "current_liabilities":[3861.35,3845.38,3873.08,3348.13,3940.22],
 "total_liabilities":[4612.29,5457.31,4843.32,4133.17,4299.21],
 "cfo":[1206.09,2442.05,2233.73,2365.53,2546.74],
 "cfi":[930.63,-1386.44,507.77,183.16,-782.24],
 "cff":[-2211.71,-1047.82,-2509.74,-2751.35,-1781.90],
 "capex":[542.21,689.47,545.32,341.06,175.15],
 "fx_effect":[0.0,0.0,0.0,0.0,0.0],
 "cash_open":[76.29,1.30,9.09,240.85,38.19],
 "cash_close":[1.30,9.09,240.85,38.19,20.79],
},
}

# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #
# Direct PDF links could not be verified when this file was produced, so every
# link points to Britannia's corporate website (Investors section lists the
# annual reports).  Paste direct PDF URLs here to make links point to the PDFs.
BRITANNIA_SITE = "https://www.britannia.co.in/"
REPORTS = {
    "AR2022": {"label": "Annual Report 2021-22", "file": "Annual_Report_2021_22_6eb6f3ae88.pdf", "url": BRITANNIA_SITE},
    "AR2023": {"label": "Annual Report 2022-23", "file": "Annual_Report_2022_23_988ac4516b.pdf", "url": BRITANNIA_SITE},
    "AR2024": {"label": "Annual Report 2023-24", "file": "BRITANNIA_Annual_Report_2023_24_18_07_2024_Final_01_High_1_8d1bc38e58.pdf", "url": BRITANNIA_SITE},
    "AR2025": {"label": "Annual Report 2024-25", "file": "2_annual_report_25_V1_Digital_FIN_Hires_1_SAP_b1a1c4c085.pdf", "url": BRITANNIA_SITE},
    "AR2026": {"label": "Annual Report 2025-26", "file": "Britannia_Annual_Report_2025_26_High_Resolution_c738982760.pdf", "url": BRITANNIA_SITE},
}

# (basis, FY) -> (report key, PDF page of BS & P&L, PDF pages of cash-flow statement)
# Page numbers are PDF page indices of the uploaded files (not printed folios).
SOURCE_MAP = {
 ("Standalone","FY2026"):   ("AR2026","88","89-90"),
 ("Standalone","FY2025"):   ("AR2026","88","89-90"),
 ("Standalone","FY2024"):   ("AR2025","89","90-91"),
 ("Standalone","FY2023"):   ("AR2024","76","77-78"),
 ("Standalone","FY2022"):   ("AR2023","73","74-75"),
 ("Consolidated","FY2026"): ("AR2026","132","133-134"),
 ("Consolidated","FY2025"): ("AR2026","132","133-134"),
 ("Consolidated","FY2024"): ("AR2025","132","133-134"),
 ("Consolidated","FY2023"): ("AR2024","117","118-119"),
 ("Consolidated","FY2022"): ("AR2023","114","115-116"),
}

RESTATEMENT_NOTES = [
 "FY2025 cash flow was restated in the FY2026 report. Consolidated CFO 2,480.65 -> 2,490.62, CFI 84.36 -> 66.43, CFF (2,761.86) -> (2,753.90). Standalone CFO 2,373.15 -> 2,365.53, CFI 183.50 -> 183.16, CFF (2,759.31) -> (2,751.35). The dashboard uses the restated figures.",
 "FY2024 cash flow was restated in the FY2025 report. Consolidated CFI 475.50 -> 484.15, CFF (2,830.48) -> (2,839.13), capex 561.52 -> 552.87. Standalone CFI 506.76 -> 507.77, CFF (2,508.73) -> (2,509.74), capex 546.33 -> 545.32. Restated figures are used.",
 "FY2024 consolidated balance sheet: classification between investments in associates/JV and non-current investments changed (total non-current assets and total assets unchanged).",
 "FY2022 figures were taken from the FY2023 report's comparative column; key lines (revenue, PBT, PAT, CFO, total assets) agree with the FY2022 report.",
 "FY2022 growth rates are not available because FY2021 is outside the five-year dataset (shown as missing).",
 "Standalone cash flow has no FX line (set to 0). Standalone closing cash in the cash-flow statement is net of bank overdraft where applicable (FY2022: 1.30 vs 9.97 on the balance sheet).",
]


def build_raw_frames() -> dict[str, pd.DataFrame]:
    """Return {basis: DataFrame(index=FY label, columns=line-item keys)}."""
    frames = {}
    for basis, items in _RAW.items():
        df = pd.DataFrame({k: pd.Series(v, dtype="float64") for k, v in items.items()})
        df.index = FY_LABELS
        df.index.name = "FY"
        frames[basis] = df
    return frames


def to_long_dataframe(frames: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Tidy long-format table (used for financial_data.csv)."""
    frames = frames or build_raw_frames()
    rows = []
    for basis, df in frames.items():
        for fy in df.index:
            rep, p_pl, p_cf = SOURCE_MAP.get((basis, fy), ("", "", ""))
            rep_label = REPORTS.get(rep, {}).get("label", "User upload")
            for key in df.columns:
                desc, stmt, unit = LINE_ITEMS.get(key, (key, "", UNIT))
                page = p_cf if stmt == "CF" else p_pl
                v = df.loc[fy, key]
                rows.append({
                    "basis": basis, "fy": fy, "line_item": key, "description": desc,
                    "statement": stmt, "value": None if pd.isna(v) else float(v), "unit": unit,
                    "source_report": rep_label, "source_pdf_page": page,
                    "status": "missing" if pd.isna(v) else "reported",
                })
    return pd.DataFrame(rows)


def default_sources_table() -> pd.DataFrame:
    rows = []
    for (basis, fy), (rep, p_pl, p_cf) in SOURCE_MAP.items():
        r = REPORTS[rep]
        rows.append({"Basis": basis, "FY": fy, "Report": r["label"], "File": r["file"],
                     "BS & P&L (PDF page)": p_pl, "Cash flow (PDF pages)": p_cf, "Link": r["url"]})
    return pd.DataFrame(rows).sort_values(["Basis", "FY"], ascending=[True, False]).reset_index(drop=True)
