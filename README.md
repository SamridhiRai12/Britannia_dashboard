# Britannia Industries Ltd. - 5-Year Interactive Financial Dashboard

Streamlit + Pandas + Plotly dashboard covering **FY2022 - FY2026** (years ended 31 March), built from the
audited statements in Britannia's annual reports. Amounts are in **INR crore**; EPS is in INR.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. Optional checks: `python tests/test_data.py` (data + calculations, no Streamlit needed)
and `python -m pytest -q tests/test_app.py` (renders every page with Streamlit's `AppTest`).

## Project structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI: sidebar, filters, pages, exports, upload |
| `data.py` | The dataset (consolidated + standalone), line-item catalogue, sources, restatement notes |
| `calculations.py` | Derived metrics, ratios, growth, validation checks, metric definitions |
| `charts.py` | Plotly figures |
| `theme.py` | Dark/light palettes, CSS, Plotly styling |
| `utils.py` | HTML tables/KPI cards, Excel export, Excel upload parser, Streamlit-version helper |
| `financial_data.csv` | Raw line items in tidy long format (with source report and PDF page) |
| `britannia_financials.xlsx` | Same data as an Excel workbook; also the upload template |
| `tests/` | Data-integrity and smoke tests |
| `.streamlit/config.toml` | Base theme and server settings |

## Features

* Pages: Executive Overview, Financial Performance, Profitability Ratios, Liquidity & Solvency, Cash Flow, Balance Sheet, Compare Years, Data/Sources/Method.
* Sidebar filters: statement basis (consolidated / standalone), FY range, focus FY, metric explorer, two-year comparison, other-income treatment, **Reset filters**.
* KPI cards (revenue, EBITDA, net profit, total assets, total debt, operating cash flow, revenue growth, net profit growth) update with the focus year, basis and EBITDA setting.
* Charts: revenue & profit trend, EBITDA/net margin, ratio comparisons, cash-flow waterfall, balance-sheet composition, revenue vs profit growth, expense breakdown, YoY growth heatmap.
* Dark / light toggle in the sidebar.
* Downloads: Excel (metrics, raw data, sources, definitions) and CSV.
* **Excel upload**: replace or extend the data (see below).

## Data and sources

* **Consolidated** = Britannia Industries Ltd. with subsidiaries, associates and joint venture. **Standalone** = parent company only. Every page shows which basis is active; both are in the dataset.
* Each year uses the **latest annual report that contains it**, so restated comparatives are preferred:
  FY2026 and FY2025 -> Annual Report 2025-26; FY2024 -> 2024-25; FY2023 -> 2023-24; FY2022 -> 2022-23 (spot-checked against 2021-22).
* The *Data, Sources & Method* page lists the report, file and **PDF page** for every year and basis, plus the formulas.
* Restatements: FY2024 and FY2025 cash-flow lines were restated in the following year's report (details on the *Data quality* tab). The dashboard uses restated figures.
* Missing data is shown as `n/a`. FY2022 growth rates are missing because FY2021 is outside the dataset. Standalone "share of associates" is not applicable.
* **Links**: the source links open Britannia's corporate website (`https://www.britannia.co.in/`). Direct PDF URLs could not be verified when this project was built, so none were invented. To link straight to the PDFs, edit `REPORTS[...]["url"]` in `data.py`.
* Page numbers refer to PDF page indices of the report files used, not printed page folios.

## Ratio conventions

All ratios use year-end balances (no averaging). Full formulas are in the app (Definitions tab) and `calculations.py`.

* EBITDA = (Total income - Total expenses) + Finance costs + D&A **- Other income** (default). Ticking *Treat other income as operating* keeps other income in. Exceptional items and share of associates are always excluded.
* Gross profit = Revenue - (materials consumed + purchases of stock-in-trade + changes in inventories).
* ROE = PAT attributable to owners / equity attributable to owners; ROA = PAT / total assets; ROCE = EBIT / (total assets - current liabilities).
* Quick ratio = (current assets - inventories) / current liabilities. Total debt = borrowings + lease liabilities. Net debt = total debt - (cash + bank balances + current investments).
* Free cash flow = operating cash flow - capex (acquisition of PPE, CWIP and intangibles).

## Updating data with Excel

1. Download the template from the sidebar (**Update data -> Download Excel template**) or use `britannia_financials.xlsx`.
2. Edit the `Raw_Consolidated` / `Raw_Standalone` sheets (rename them to `Consolidated` / `Standalone` if you wish; names containing those words are detected). Keep the `line_item` keys; add FY columns such as `FY2027`.
3. Upload in the sidebar. Blank cells become *missing*. The *Data quality* tab reports any accounting-identity mismatches. **Revert to built-in data** restores the original dataset.

## Deploying to Streamlit Community Cloud

1. Push this folder to a GitHub repository (keep `app.py` at the repository root).
2. On https://share.streamlit.io choose **New app**, select the repository, branch and `app.py`.
3. Streamlit Cloud installs `requirements.txt` automatically. No secrets or external services are needed.

## Notes and limitations

* Fonts load from Google Fonts; offline, the app falls back to system fonts.
* Dark/light styling is applied with CSS on top of Streamlit's theme; minor third-party widget details can differ between Streamlit versions.
* This is an analytical tool, not investment advice. Re-check figures against the source reports before relying on them.
