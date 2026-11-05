"""theme.py - colour palettes, global CSS (dark/light) and Plotly layout helpers."""
from __future__ import annotations

DARK = dict(
    mode="dark", bg="#0A1628", surface="#0F1F3A", card="#13284A", border="#243B63",
    text="#EAF1FB", muted="#97ABC8", grid="rgba(151,171,200,0.16)",
    accent="#4F8CFF", pos="#34D399", neg="#F87171", warn="#FBBF24",
    series=["#4F8CFF", "#8FBFFF", "#FBBF24", "#34D399", "#B794F6", "#FB923C"],
)
LIGHT = dict(
    mode="light", bg="#F6F9FD", surface="#FFFFFF", card="#FFFFFF", border="#D6E0EE",
    text="#0B2545", muted="#586B86", grid="rgba(11,37,69,0.10)",
    accent="#1D4ED8", pos="#059669", neg="#DC2626", warn="#D97706",
    series=["#0B2F6B", "#2563EB", "#60A5FA", "#D97706", "#059669", "#7C3AED"],
)


def palette(dark: bool) -> dict:
    return DARK if dark else LIGHT


def css(P: dict) -> str:
    """Global stylesheet. Fonts load from Google Fonts (falls back to system fonts offline)."""
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');
:root {{
  --bg:{P['bg']}; --surface:{P['surface']}; --card:{P['card']}; --border:{P['border']};
  --text:{P['text']}; --muted:{P['muted']}; --accent:{P['accent']};
  --pos:{P['pos']}; --neg:{P['neg']}; --warn:{P['warn']};
}}
.stApp {{ background:var(--bg); color:var(--text); font-family:'Inter',system-ui,sans-serif; }}
[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stSidebar"] {{ background:var(--surface); border-right:1px solid var(--border); }}
.block-container {{ padding-top:2.2rem; padding-bottom:3rem; max-width:1400px; }}
.stApp h1,.stApp h2,.stApp h3,.stApp h4 {{ font-family:'DM Serif Display',Georgia,serif; color:var(--text); letter-spacing:.2px; }}
.stApp p, .stApp li, .stApp label, [data-testid="stWidgetLabel"] p,
[data-testid="stMarkdownContainer"] p, [data-testid="stCaptionContainer"] {{ color:var(--text); }}
[data-testid="stCaptionContainer"], .stApp small {{ color:var(--muted) !important; }}
[data-testid="stSidebar"] * {{ color:var(--text); }}
/* inputs */
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, [data-testid="stFileUploaderDropzone"] {{
  background:var(--card) !important; border-color:var(--border) !important; color:var(--text) !important; }}
div[data-baseweb="select"] span, div[data-baseweb="select"] input {{ color:var(--text) !important; }}
div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li, div[data-baseweb="menu"] {{
  background:var(--card) !important; color:var(--text) !important; }}
div[data-baseweb="popover"] li:hover {{ background:var(--surface) !important; }}
.stButton > button, .stDownloadButton > button {{
  background:var(--card); color:var(--text); border:1px solid var(--border); border-radius:8px; font-weight:500; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color:var(--accent); color:var(--accent); }}
button[data-baseweb="tab"] {{ color:var(--muted); }}
button[data-baseweb="tab"][aria-selected="true"] {{ color:var(--accent); }}
[data-testid="stExpander"] {{ background:var(--card); border:1px solid var(--border); border-radius:10px; }}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {{ color:var(--text); }}
hr {{ border-color:var(--border); }}
a {{ color:var(--accent) !important; }}

/* page header */
.page-title {{ font-family:'DM Serif Display',Georgia,serif; font-size:2.1rem; line-height:1.15; margin:0; color:var(--text); }}
.page-sub {{ color:var(--muted); margin:.25rem 0 1rem 0; font-size:.95rem; }}
.badge {{ display:inline-block; padding:2px 10px; border-radius:999px; font-size:.72rem; font-weight:600;
  letter-spacing:.6px; text-transform:uppercase; border:1px solid var(--accent); color:var(--accent); margin-right:6px; }}
.section-title {{ font-family:'DM Serif Display',Georgia,serif; font-size:1.35rem; color:var(--text);
  margin:1.6rem 0 .2rem 0; padding-bottom:.35rem; border-bottom:2px solid var(--accent); display:inline-block; }}
.section-note {{ color:var(--muted); font-size:.85rem; margin:.2rem 0 .6rem 0; }}

/* KPI cards */
.kpi {{ background:var(--card); border:1px solid var(--border); border-left:4px solid var(--accent);
  border-radius:12px; padding:14px 16px 12px 16px; margin-bottom:12px; min-height:128px; }}
.kpi-label {{ color:var(--muted); font-size:.74rem; font-weight:600; letter-spacing:.9px; text-transform:uppercase; }}
.kpi-value {{ font-family:'Space Grotesk',sans-serif; font-size:1.75rem; font-weight:700; color:var(--text); margin:.25rem 0 .1rem 0; }}
.kpi-delta {{ font-size:.82rem; font-weight:600; }}
.kpi-delta.up {{ color:var(--pos); }} .kpi-delta.down {{ color:var(--neg); }} .kpi-delta.flat {{ color:var(--muted); }}
.kpi-sub {{ color:var(--muted); font-size:.72rem; margin-top:.25rem; }}

/* tables */
.tbl-wrap {{ overflow-x:auto; border:1px solid var(--border); border-radius:10px; background:var(--card); }}
table.fin {{ width:100%; border-collapse:collapse; font-size:.86rem; }}
table.fin th {{ background:var(--surface); color:var(--muted); text-transform:uppercase; font-size:.7rem; letter-spacing:.7px;
  text-align:right; padding:9px 12px; border-bottom:1px solid var(--border); white-space:nowrap; }}
table.fin th:first-child, table.fin td:first-child {{ text-align:left; }}
table.fin td {{ padding:8px 12px; border-bottom:1px solid var(--border); text-align:right; color:var(--text);
  font-variant-numeric:tabular-nums; }}
table.fin tr:last-child td {{ border-bottom:none; }}
table.fin td.na {{ color:var(--warn); font-style:italic; }}
table.fin td.neg {{ color:var(--neg); }}
.insight {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:10px 14px; margin:6px 0; font-size:.92rem; }}
.formula {{ font-family:'Space Grotesk',monospace; font-size:.82rem; color:var(--accent); }}
</style>
"""


def style_fig(fig, P: dict, title: str | None = None, height: int = 400, legend: bool = True):
    """Apply the dashboard look to a Plotly figure."""
    fig.update_layout(
        title=dict(text=title, x=0.01, xanchor="left", font=dict(size=15, color=P["text"], family="Inter")) if title else None,
        height=height, margin=dict(l=10, r=10, t=55 if title else 20, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=P["text"], family="Inter, sans-serif", size=12),
        colorway=P["series"], hovermode="x unified", showlegend=legend,
        legend=dict(orientation="h", y=-0.18, x=0, font=dict(color=P["text"])),
        hoverlabel=dict(bgcolor=P["card"], font=dict(color=P["text"]), bordercolor=P["border"]),
    )
    fig.update_xaxes(showgrid=False, linecolor=P["border"], tickfont=dict(color=P["muted"]))
    fig.update_yaxes(gridcolor=P["grid"], zeroline=False, tickfont=dict(color=P["muted"]))
    return fig
