"""
African Strategic Leverage & Commodity Control Lab (ASLC) v3
A Geoeconomic Bargaining Simulator for Africa–EU–China Supply Chains

Single-file Streamlit application. All data, models, visualizations, and UI
in one self-contained file. Works offline once loaded — no external API calls
required for core functionality.

v3 expands from 8 countries / 7 commodities  →  20 countries / 11 commodities.

Data sources (cited inline):
    - USGS Mineral Commodity Summaries 2025 (production, reserves, trade)
    - UN Comtrade / WITS World Bank (bilateral trade flows, buyer shares)
    - IMF Regional Economic Outlook: Sub-Saharan Africa Apr 2024
    - EU Critical Raw Materials Act 2024 (regulatory classification)
    - ICCO / Ghana COCOBOD (cocoa production & pricing)
    - ICO / USDA 2024-25 (coffee production & trade)
    - ICSID Case Database (ISDS precedent data)
    - UNCTAD Review of Maritime Transport 2024 (shipping / chokepoints)
    - WNA / IAEA Red Book 2024 (uranium)
    - Zambia Mines Ministry / Reuters (copper)
    - Company annual reports, EITI reports (financing, ownership)
    - Ghana Minerals Commission (gold)
    - Cobalt Institute / Gécamines (DRC copper/cobalt)
    - World Nuclear Association (uranium)

Author: Frederick Bishops
License: Research, policy analysis, and educational use
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import io
import math

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        SECTION 1 — CONFIGURATION                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

st.set_page_config(
    page_title="African Strategic Leverage & Commodity Control Lab",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Semantic theme tokens ─────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "app_bg": "#0D1518",
        "panel_bg": "#142126",
        "sidebar_bg": "#111D22",
        "border": "#27414A",
        "text_primary": "#E4ECEF",
        "text_secondary": "#BACAD0",
        "text_muted": "#8FA6AE",
        "accent": "#4FA6B3",
        "positive": "#57A870",
        "negative": "#C66666",
        "warning": "#C99654",
        "chart_bg": "#142126",
        "gridline": "#2A4048",
        "legend_text": "#C9D5DA",
        "rust": "#8E624A",
    },
    "light": {
        "app_bg": "#F3F6F7",
        "panel_bg": "#FFFFFF",
        "sidebar_bg": "#E7EEF1",
        "border": "#CFDCE1",
        "text_primary": "#14252B",
        "text_secondary": "#2C454F",
        "text_muted": "#5E747C",
        "accent": "#2E7380",
        "positive": "#2D7A48",
        "negative": "#A14343",
        "warning": "#9A6A2F",
        "chart_bg": "#FFFFFF",
        "gridline": "#DFE6E9",
        "legend_text": "#2C454F",
        "rust": "#8F5A42",
    },
}

def _inject_theme_css(tokens):
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="st-"] {{ font-family: 'Inter', -apple-system, sans-serif; }}
:root {{
    --app-bg: {tokens["app_bg"]};
    --panel-bg: {tokens["panel_bg"]};
    --sidebar-bg: {tokens["sidebar_bg"]};
    --border: {tokens["border"]};
    --text-primary: {tokens["text_primary"]};
    --text-secondary: {tokens["text_secondary"]};
    --text-muted: {tokens["text_muted"]};
    --accent: {tokens["accent"]};
    --positive: {tokens["positive"]};
    --negative: {tokens["negative"]};
    --warning: {tokens["warning"]};
    --legend-text: {tokens["legend_text"]};
}}
body, .stApp {{ background: var(--app-bg); color: var(--text-primary); }}

/* ── metric cards ── */
.m-card {{
    background: var(--panel-bg); border-radius: 10px; padding: 1rem 1.05rem;
    border: 1px solid var(--border); border-left: 3px solid var(--accent); margin-bottom: .65rem;
    min-height: 110px;
}}
.m-card .val {{
    font-size: clamp(1.2rem, 1.5vw, 1.55rem); font-weight: 650; color: var(--text-primary); line-height: 1.2;
    white-space: normal; overflow-wrap: anywhere;
}}
.m-card .lbl {{
    font-size: .77rem; color: var(--text-muted); text-transform: uppercase;
    letter-spacing: .05em; font-weight: 600; margin-bottom: .35rem; white-space: normal;
}}
.m-card .delta-pos {{ color: var(--positive); font-size: .93rem; margin-left: .4rem; }}
.m-card .delta-neg {{ color: var(--negative); font-size: .93rem; margin-left: .4rem; }}

/* ── analyst callouts ── */
.box-note, .box-warn, .box-info {{
    background: color-mix(in srgb, var(--panel-bg) 92%, var(--accent) 8%);
    border-radius: 8px; padding: .92rem 1rem; border: 1px solid var(--border); margin: .58rem 0;
    font-size: .91rem; color: var(--text-secondary);
}}
.box-info {{ border-left: 3px solid var(--accent); }}
.box-warn {{ border-left: 3px solid var(--warning); }}
.box-note {{ border-left: 3px solid var(--text-muted); }}

.page-title {{ font-size: 1.72rem; font-weight: 680; color: var(--text-primary); letter-spacing: -0.01em; margin-bottom: .2rem; }}
.page-subtitle {{ color: var(--text-secondary); margin-bottom: .95rem; font-size: .95rem; }}
.section-header {{ font-size: 1.1rem; font-weight: 620; color: var(--text-primary); margin-top: .8rem; margin-bottom: .35rem; }}
.insignia {{ color: var(--text-muted); font-size: .72rem; letter-spacing: .17em; text-transform: uppercase; opacity: .92; }}
.meta-line {{ color: var(--text-muted); font-size: .74rem; }}

/* tabs */
button[data-baseweb="tab"] {{ color: var(--text-secondary) !important; }}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: var(--text-primary) !important; border-bottom: 2px solid var(--accent) !important;
}}

/* inputs + sidebar legibility */
section[data-testid="stSidebar"] {{
    background-color: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border);
}}
section[data-testid="stSidebar"] * {{ color: var(--text-primary) !important; }}
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] .stCaption p {{
    color: var(--text-secondary) !important;
}}

/* ── risk badges ── */
.rbadge {{
    display: inline-block; padding: .12rem .55rem; border-radius: 4px;
    font-size: .8rem; font-weight: 600; color: #fff;
}}
.rbadge-critical {{ background: var(--negative); }}
.rbadge-high     {{ background: color-mix(in srgb, var(--warning) 85%, #8A4D00 15%); }}
.rbadge-moderate {{ background: var(--warning); color: #1b1f21; }}
.rbadge-limited  {{ background: var(--warning); }}
.rbadge-low      {{ background: var(--positive); }}
.rbadge-minimal  {{ background: color-mix(in srgb, var(--positive) 85%, #1e4f2f 15%); }}

/* ── source footnote ── */
.src {{ font-size: .78rem; color: var(--text-muted); margin-top: .3rem; }}

/* footer */
.footer {{
    text-align: center; color: var(--text-muted); font-size: .78rem;
    margin-top: 2.2rem; padding: 1rem 0; border-top: 1px solid var(--border);
}}
</style>
""", unsafe_allow_html=True)


def get_theme(mode):
    if mode == "Light":
        return THEMES["light"]
    if mode == "Dark":
        return THEMES["dark"]
    hour = datetime.utcnow().hour
    return THEMES["dark"] if hour >= 18 or hour < 7 else THEMES["light"]


DEFAULT_PLOTLY_MARGIN = dict(l=75, r=55, t=70, b=70)


def plotly_base(tokens):
    return dict(
        font=dict(family="Inter, -apple-system, sans-serif",
                  color=tokens["text_primary"], size=12),
        paper_bgcolor=tokens["chart_bg"],
        plot_bgcolor=tokens["chart_bg"],
        legend=dict(font=dict(color=tokens["legend_text"], size=11)),
    )


def plotly_layout(*, margin=None, **overrides):
    return {
        **PLOTLY_LAYOUT,
        "margin": margin or DEFAULT_PLOTLY_MARGIN,
        **overrides,
    }


def apply_theme(tokens):
    global C, CHART_SEQ, RISK_CLR, PLOTLY_LAYOUT
    C = {
        "teal": tokens["accent"],
        "rust": tokens["rust"],
        "dark_teal": "#466E78" if tokens == THEMES["dark"] else "#3A6973",
        "cyan_light": "#90B6BF" if tokens == THEMES["dark"] else "#A8C6CD",
        "mauve": "#8F6A78",
        "gold": "#B08F63",
        "olive": "#6D7F67",
        "brown": "#6C5A4A",
        "bg": tokens["app_bg"],
        "card": tokens["panel_bg"],
        "text": tokens["text_primary"],
        "muted": tokens["text_secondary"],
        "offblack": "#091717",
        "grid": tokens["gridline"],
    }
    CHART_SEQ = [C["teal"], C["rust"], C["dark_teal"], C["cyan_light"],
                 C["mauve"], C["gold"], C["olive"], C["brown"]]
    RISK_CLR = {
        "Critical": tokens["negative"],
        "High": tokens["warning"],
        "Moderate": "#B68B55",
        "Low": tokens["positive"],
        "Minimal": "#3F8E5A",
    }
    PLOTLY_LAYOUT = plotly_base(tokens)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECTION 2 — EMBEDDED DATA LAYER                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
# Every number is cited to a public source.  Where exact figures are not public,
# a proxy is used and flagged in the ASSUMPTION_REGISTER at the bottom.

# ── Countries database (20 countries) ─────────────────────────────────────────
COUNTRIES = {
    # ── Original 8 ──────────────────────────────────────────────────────────
    "Ghana": {
        "region": "West Africa", "gdp_bn": 75.5,               # World Bank 2023
        "population_mn": 33.5, "rating": "B- (S&P)",
        "ports": ["Tema", "Takoradi"], "corridor": "Gulf of Guinea",
        "eiti": True,
        "bits": ["UK", "Netherlands", "Germany", "China",
                 "South Africa", "Switzerland"],
    },
    "South Africa": {
        "region": "Southern Africa", "gdp_bn": 377.0,           # World Bank 2023
        "population_mn": 60.4, "rating": "BB- (S&P)",
        "ports": ["Durban", "Richards Bay", "Cape Town", "Saldanha"],
        "corridor": "Cape of Good Hope", "eiti": False,
        "bits": ["UK", "Netherlands", "Germany", "China",
                 "USA", "France", "Belgium"],
    },
    "DRC": {
        "region": "Central Africa", "gdp_bn": 65.2,             # World Bank 2023
        "population_mn": 102.3, "rating": "B- (Fitch)",
        "ports": ["Matadi", "Boma"],
        "corridor": "Lobito Corridor / Dar es Salaam", "eiti": True,
        "bits": ["Belgium", "France", "Germany", "China",
                 "South Korea", "USA"],
    },
    "Guinea": {
        "region": "West Africa", "gdp_bn": 21.0,                # World Bank 2023
        "population_mn": 14.2, "rating": "Not rated",
        "ports": ["Conakry", "Kamsar"], "corridor": "Gulf of Guinea",
        "eiti": True, "bits": ["France", "China", "USA", "Germany"],
    },
    "Gabon": {
        "region": "Central Africa", "gdp_bn": 21.1,             # World Bank 2023
        "population_mn": 2.4, "rating": "B+ (Fitch)",
        "ports": ["Owendo", "Port-Gentil"], "corridor": "Gulf of Guinea",
        "eiti": True, "bits": ["France", "China", "Belgium", "Germany"],
    },
    "Zimbabwe": {
        "region": "Southern Africa", "gdp_bn": 24.8,            # World Bank 2023
        "population_mn": 16.7, "rating": "Not rated",
        "ports": ["Landlocked → Beira (MZ), Durban (SA)"],
        "corridor": "Beira Corridor / North-South", "eiti": False,
        "bits": ["China", "South Africa", "UK", "Germany", "Netherlands"],
    },
    "Zambia": {
        "region": "Southern Africa", "gdp_bn": 29.8,            # World Bank 2023
        "population_mn": 20.6, "rating": "B- (Fitch)",
        "ports": ["Landlocked → Dar es Salaam, Durban, Lobito"],
        "corridor": "Lobito Corridor / Dar es Salaam", "eiti": True,
        "bits": ["China", "UK", "Netherlands", "South Africa", "USA"],
    },
    "Côte d'Ivoire": {
        "region": "West Africa", "gdp_bn": 78.8,                # World Bank 2023
        "population_mn": 28.9, "rating": "BB- (S&P)",
        "ports": ["Abidjan", "San-Pédro"], "corridor": "Gulf of Guinea",
        "eiti": True,
        "bits": ["France", "Netherlands", "UK", "China", "Germany"],
    },

    # ── 12 New countries ────────────────────────────────────────────────────
    "Nigeria": {
        "region": "West Africa", "gdp_bn": 477.0,               # World Bank / IMF 2023
        "population_mn": 223.0, "rating": "B- (Fitch)",
        "ports": ["Lagos/Apapa", "Bonny", "Port Harcourt"],
        "corridor": "Gulf of Guinea", "eiti": True,
        "bits": ["UK", "Netherlands", "Germany", "China",
                 "France", "USA", "South Africa"],
    },
    "Ethiopia": {
        "region": "East Africa", "gdp_bn": 164.0,               # World Bank 2023
        "population_mn": 126.0, "rating": "Not rated",
        "ports": ["Landlocked → Djibouti"],
        "corridor": "Djibouti Corridor", "eiti": True,
        "bits": ["China", "Netherlands", "France", "Germany",
                 "Italy", "South Korea"],
    },
    "Tanzania": {
        "region": "East Africa", "gdp_bn": 79.0,                # World Bank 2023
        "population_mn": 65.0, "rating": "Not rated",
        "ports": ["Dar es Salaam", "Tanga"],
        "corridor": "Central Corridor / TAZARA", "eiti": True,
        "bits": ["UK", "Netherlands", "Germany", "China",
                 "South Africa", "Canada"],
    },
    "Mozambique": {
        "region": "Southern Africa", "gdp_bn": 20.6,            # World Bank 2023
        "population_mn": 33.0, "rating": "CCC+ (S&P)",
        "ports": ["Maputo", "Beira", "Nacala"],
        "corridor": "Nacala Corridor / Beira Corridor", "eiti": True,
        "bits": ["Portugal", "UK", "France", "China",
                 "Germany", "USA"],
    },
    "Namibia": {
        "region": "Southern Africa", "gdp_bn": 12.6,            # World Bank 2023
        "population_mn": 2.6, "rating": "BB+ (Fitch)",
        "ports": ["Walvis Bay", "Lüderitz"],
        "corridor": "Trans-Kalahari Corridor", "eiti": True,
        "bits": ["Germany", "UK", "France", "China",
                 "South Africa", "Spain"],
    },
    "Niger": {
        "region": "West Africa", "gdp_bn": 17.4,                # World Bank 2023
        "population_mn": 27.0, "rating": "Not rated",
        "ports": ["Landlocked → Cotonou, Lomé"],
        "corridor": "Trans-Saharan / Gulf of Guinea",
        "eiti": True,  # Suspended after 2023 coup; source: EITI Secretariat
        "bits": ["France", "China", "Germany", "USA"],
    },
    "Mali": {
        "region": "West Africa", "gdp_bn": 20.5,                # World Bank 2023
        "population_mn": 23.0, "rating": "Not rated",
        "ports": ["Landlocked → Dakar (SN), Abidjan (CI)"],
        "corridor": "Dakar–Bamako Corridor", "eiti": True,
        "bits": ["France", "China", "Germany", "UK"],
    },
    "Angola": {
        "region": "Southern Africa", "gdp_bn": 92.0,            # World Bank 2023
        "population_mn": 36.0, "rating": "B- (Fitch)",
        "ports": ["Luanda", "Lobito", "Namibe"],
        "corridor": "Lobito Corridor", "eiti": True,
        "bits": ["Portugal", "UK", "France", "China",
                 "Germany", "USA", "Italy"],
    },
    "Uganda": {
        "region": "East Africa", "gdp_bn": 50.0,                # World Bank 2023
        "population_mn": 47.0, "rating": "B+ (Fitch)",
        "ports": ["Landlocked → Mombasa (KE), Dar es Salaam (TZ)"],
        "corridor": "Northern Corridor / Central Corridor", "eiti": True,
        "bits": ["UK", "Netherlands", "China", "South Africa",
                 "France", "Germany"],
    },
    "Kenya": {
        "region": "East Africa", "gdp_bn": 113.0,               # World Bank 2023
        "population_mn": 55.0, "rating": "B (Fitch)",
        "ports": ["Mombasa"],
        "corridor": "Northern Corridor", "eiti": False,
        "bits": ["UK", "Netherlands", "Germany", "France",
                 "China", "USA", "Italy"],
    },
    "Rwanda": {
        "region": "East Africa", "gdp_bn": 14.0,                # World Bank 2023
        "population_mn": 14.0, "rating": "B+ (Fitch)",
        "ports": ["Landlocked → Dar es Salaam (TZ), Mombasa (KE)"],
        "corridor": "Central Corridor", "eiti": True,
        "bits": ["Belgium", "Germany", "UK", "China",
                 "USA", "Netherlands"],
    },
    "Botswana": {
        "region": "Southern Africa", "gdp_bn": 19.4,            # World Bank 2023
        "population_mn": 2.6, "rating": "BBB+ (S&P)",
        "ports": ["Landlocked → Durban (SA), Walvis Bay (NA)"],
        "corridor": "North-South Corridor / Trans-Kalahari", "eiti": True,
        "bits": ["UK", "Germany", "Switzerland", "China",
                 "USA", "South Africa"],
    },
}

# ── Commodity database (11 commodities) ───────────────────────────────────────
# Structure per commodity:
#   cat          — category label
#   use          — strategic end-uses
#   prod_mt      — global production (in commodity's unit)
#   unit         — unit label
#   africa       — dict of African producers with share_pct, prod (native unit), reserves
#   af_share     — total African share of global production (%)
#   buyers       — dict buyer→share (fractions summing to ~1)
#   hhi          — Herfindahl–Hirschman Index of buyer concentration
#   sub          — (score 0-1, notes)  substitutability
#   stock        — (score 0-1, notes)  stockpiling feasibility
#   choke        — (score 0-1, routes, notes)  chokepoint sensitivity
#   proc         — (china%, africa%, eu%, notes)  processing capacity shares
#   fin          — (score 0-1, investors, cn_present, notes)  financing dependency
#   reg          — (crma, cbam, us_crit, dd, notes)  regulatory exposure booleans
#   price        — (benchmark, recent_usd, vol_pct)

COMMODITIES = {

    # ── MANGANESE ─────────────────────────────────────────────────────────────
    "Manganese": dict(
        cat="Critical Mineral",
        use="Steel production (90 %), EV battery cathodes, chemical industry",
        prod_mt=23_000_000, unit="metric tons",               # USGS MCS 2025
        africa={
            "South Africa": dict(share=36.0, prod=8_280_000,  # USGS MCS 2025
                                 res=640_000_000),
            "Gabon":        dict(share=14.0, prod=3_220_000,  # USGS MCS 2025
                                 res=69_000_000),
            "Ghana":        dict(share=4.5,  prod=1_035_000,  # USGS MCS 2025
                                 res=13_000_000),
        },
        af_share=54.5,
        buyers={"China": .62, "EU-27": .10, "India": .08,    # UN Comtrade 2023
                "Japan": .06, "South Korea": .05, "USA": .04,
                "Others": .05},
        hhi=0.41,
        sub=(0.30, "Limited substitutes in steel. Some battery chemistries "
             "can switch (NMC→LFP removes Mn). No viable substitute for "
             "ferroalloy production."),                        # USGS
        stock=(0.70, "Bulk commodity, large storage needed. China holds "
               "~3-6 months strategic reserves. US NDS has small stockpile."),
        choke=(0.45, ["Gulf of Guinea → Suez → East Asia",
                      "Cape of Good Hope → East Asia"],
               "Multiple route options reduce sensitivity. SA exports via "
               "Richards Bay; Ghana via Takoradi."),
        proc=(68, 12, 6, "China ~68 % of global Mn-alloy output. SA has "
              "Transalloys, Assmang. Very little processing in Ghana/Gabon."),
                                                               # CRU / USGS
        fin=(0.55, ["South32 (AU)", "Eramet (FR)", "MOIL (IN)"],
             True, "Ghana Manganese Co has significant foreign ownership. "
             "Gabon: COMILOG (Eramet 63.7 %)."),
        reg=(True, True, True, True,                           # EU CRMA 2024
             "On EU strategic raw-materials list. CBAM applies to Mn alloys. "
             "EU CSDDD creates supply-chain liability."),
        price=("Mn ore 44 % CIF Tianjin", 5.50, 35),
    ),

    # ── BAUXITE / ALUMINA ─────────────────────────────────────────────────────
    "Bauxite/Alumina": dict(
        cat="Critical Mineral",
        use="Aluminium production (primary), refractories, abrasives, chemicals",
        prod_mt=400_000_000, unit="metric tons",               # USGS MCS 2025
        africa={
            "Guinea": dict(share=23.0, prod=92_000_000,
                           res=7_400_000_000),                 # USGS MCS 2025
            "Ghana":  dict(share=1.5,  prod=6_000_000,
                           res=900_000_000),                   # USGS MCS 2025
        },
        af_share=24.5,
        buyers={"China": .72, "EU-27": .08, "India": .07,    # UN Comtrade 2023
                "UAE": .04, "Others": .09},
        hhi=0.53,
        sub=(0.15, "No viable substitute for bauxite in Al smelting. Recycled "
             "Al reduces primary demand but doesn't replace ore."),
        stock=(0.55, "Very bulky; high storage cost per unit value. "
               "China stockpiles alumina. Bauxite rarely stockpiled."),
        choke=(0.50, ["Guinea → transatlantic → China",
                      "Guinea → Suez → China"],
               "Kamsar port is a single-point-of-failure. 2021 Guinea coup "
               "disrupted flows."),
        proc=(54, 1.5, 9, "Near-zero alumina refining in Guinea/Ghana. "
              "China refines 54 % of global alumina. Massive value gap."),
        fin=(0.80, ["Rio Tinto (UK/AU)", "Alcoa (US)",
                    "SMB-Winning (CN/SG)", "Rusal (RU)"],
             True, "Guinea: SMB-Winning (Chinese-backed) is largest producer. "
             "Simandou JV (Rio Tinto / Chinalco)."),
        reg=(True, True, True, True,
             "Bauxite / alumina on EU CRM list. CBAM heavily impacts Al. "
             "Guinea coup (2021) tested due-diligence frameworks."),
        price=("Bauxite FOB Guinea", 55, 20),
    ),

    # ── COBALT ────────────────────────────────────────────────────────────────
    "Cobalt": dict(
        cat="Critical Mineral",
        use="Li-ion battery cathodes (NMC, NCA), superalloys, catalysts, magnets",
        prod_mt=230_000, unit="metric tons",                   # USGS MCS 2025
        africa={
            "DRC":     dict(share=73.0, prod=167_900,          # USGS MCS 2025
                            res=4_000_000),
            "Zambia":  dict(share=1.5,  prod=3_450,            # USGS MCS 2025
                            res=270_000),
            "Tanzania": dict(share=1.2, prod=2_760,            # USGS; minor cobalt
                             res=None),
        },
        af_share=75.7,
        buyers={"China": .78, "EU-27": .08, "Japan": .04,     # UN Comtrade 2023
                "South Korea": .04, "USA": .03, "Others": .03},
        hhi=0.62,
        sub=(0.35, "LFP chemistry eliminates Co (Tesla shift). NMC reducing "
             "Co content (NMC 811). Superalloy uses have limited subs."),
        stock=(0.80, "High value-to-weight; easy to stockpile. China, Japan "
               "hold strategic reserves. US NDS holds Co."),
        choke=(0.65, ["DRC → Dar es Salaam (road/rail)",
                      "DRC → Lobito Corridor (planned)",
                      "DRC → Durban"],
               "DRC landlocked for eastern mines. Lobito Corridor under "
               "construction (US/EU backed)."),
        proc=(73, 5, 10, "China refines ~73 % of global Co. DRC exports "
              "mainly concentrate / hydroxide. Umicore (BE), ERG (KZ)."),
        fin=(0.85, ["CMOC (CN)", "Glencore (CH)", "ERG (KZ)",
                    "Barrick Gold (CA)"],
             True, "Chinese firms (CMOC, Huayou, CATL) dominate DRC Co. "
             "Glencore operates Mutanda / KCC."),
        reg=(True, False, True, True,
             "Extremely high regulatory scrutiny: child-labour concerns, "
             "conflict-mineral regs. EU Battery Regulation requires DD. "
             "Dodd-Frank § 1502 adjacent."),
        price=("LME Cobalt cash", 24_000, 55),
    ),

    # ── LITHIUM ───────────────────────────────────────────────────────────────
    "Lithium": dict(
        cat="Critical Mineral",
        use="Batteries (EV, grid storage, consumer electronics), ceramics, glass",
        prod_mt=180_000, unit="metric tons LCE",               # USGS MCS 2025
        africa={
            "Zimbabwe": dict(share=4.5, prod=8_100,
                             res=310_000),                     # USGS MCS 2025
            "DRC":      dict(share=0.5, prod=900,
                             res=3_000_000),                   # USGS MCS 2025
        },
        af_share=5.0,
        buyers={"China": .70, "South Korea": .10, "Japan": .08,  # UN Comtrade 2023
                "EU-27": .05, "USA": .04, "Others": .03},
        hhi=0.52,
        sub=(0.10, "No commercial substitute for Li in Li-ion batteries. "
             "Na-ion emerging but lower energy density. Essential for "
             "energy transition."),
        stock=(0.75, "Moderate value-to-weight. China maintains strategic "
               "Li reserves. Australia / Chile main global suppliers."),
        choke=(0.50, ["Zimbabwe → Beira (MZ) → Asia",
                      "Zimbabwe → Durban → Asia"],
               "Zimbabwe landlocked. Rail / road to MZ or SA ports. "
               "Africa currently minor player vs AU / CL."),
        proc=(65, 2, 3, "China dominates Li refining (spodumene → carbonate "
              "/ hydroxide). Xinfeng building plant in Namibia. Almost no "
              "African refining."),
        fin=(0.90, ["Zhejiang Huayou (CN)", "Sinomine (CN)",
                    "Premier African Minerals (UK)"],
             True, "Zimbabwe Li sector heavily Chinese-invested. Gov banned "
             "raw Li ore exports 2022 to push local processing."),
        reg=(True, False, True, True,
             "Top of every critical-minerals list. IRA (US) requirements "
             "for FTA-country sourcing. EU CRMA strategic material."),
        price=("Li₂CO₃ CIF Asia", 12_000, 85),
    ),

    # ── COCOA ─────────────────────────────────────────────────────────────────
    "Cocoa": dict(
        cat="Strategic Agricultural Commodity",
        use="Chocolate, cocoa butter / powder (food), cosmetics",
        prod_mt=4_800_000, unit="metric tons",                 # ICCO 2024
        africa={
            "Côte d'Ivoire": dict(share=38.0, prod=1_824_000,  # ICCO 2024
                                   res=None),
            "Ghana":          dict(share=15.0, prod=720_000,    # COCOBOD 2024
                                   res=None),
            "Nigeria":        dict(share=5.0,  prod=240_000,    # ICCO 2024; #5 world producer
                                   res=None),
        },
        af_share=65.0,
        buyers={"EU-27": .45, "USA": .15, "Malaysia": .08,     # UN Comtrade 2023
                "Indonesia": .06, "China": .05, "Others": .21},
        hhi=0.26,                                              # UN Comtrade
        sub=(0.15, "No substitute for cocoa in chocolate. Compound chocolate "
             "uses vegetable fats but is inferior. Brand / taste loyalty "
             "is a moat."),
        stock=(0.35, "Perishable: 1-2 yr (beans), 6-12 mo (butter). "
               "Stocks-to-use ratio at historic lows (2024 crisis)."),
        choke=(0.35, ["Gulf of Guinea → Europe (short transatlantic)",
                      "Gulf of Guinea → Asia"],
               "Short route to main market (EU). Abidjan, Tema are major "
               "cocoa ports. Low maritime chokepoint risk."),
        proc=(3, 22, 40, "Netherlands is world's largest cocoa processor. "
              "Ghana / CI have growing grinding capacity (~22 %). "
              "EU dominates processing."),
        fin=(0.45, ["Cargill (US)", "Barry Callebaut (CH)",
                    "Olam (SG)", "Touton (FR)"],
             False, "COCOBOD (GH) and CCC (CI) are state marketing boards. "
             "Strong state role unlike minerals."),
        reg=(False, False, False, True,
             "EU Deforestation Regulation (EUDR) is the primary regulatory "
             "risk. Requires proof of zero-deforestation. Major burden for "
             "smallholders. Delayed to Dec 2025."),
        price=("ICE Cocoa London / NY", 8_000, 65),
    ),

    # ── REFINED PETROLEUM ─────────────────────────────────────────────────────
    "Refined Petroleum": dict(
        cat="Energy (Export & Dependency)",
        use="Transport fuel, industrial energy, power generation, petrochemicals",
        prod_mt=4_400_000_000, unit="bbl/day equiv.",
        africa={
            "Nigeria": dict(share=2.5, prod=1_400_000,         # OPEC 2024; ~1.4M bbl/day
                            res=None),
            "Angola":  dict(share=1.5, prod=1_100_000,         # OPEC 2024; ~1.1M bbl/day
                            res=None),
            "Ghana":   dict(share=0.2, prod=None, res=None),   # EIA / GPC; net importer
        },
        af_share=4.2,
        buyers={"China": .35, "India": .20, "EU-27": .18,      # OPEC / IEA 2024
                "USA": .12, "Others": .15},
        hhi=0.20,
        _net_exporters=["Nigeria", "Angola"],   # These two are major exporters
        _dependency=True,   # flag: Ghana still has dependency component
        _import_detail={
            "refined_import_pct": 70,                          # EIA / GPC (Ghana)
            "crude_prod_bbl_day": 150_000,                     # Ghana upstream
            "refinery_cap_bbl_day": 45_000,                    # Tema Oil Ref
            "suppliers": {"Europe": .35, "India": .25,
                          "China": .15, "Others": .25},
        },
        sub=(0.25, "EVs / renewables reduce long-term demand. Short-term: "
             "no substitute for jet fuel, heavy transport, petrochem."),
        stock=(0.50, "SPRs exist (US, IEA members). Ghana has limited "
               "storage. ECOWAS has no collective reserve. "
               "Nigeria / Angola have upstream buffer."),
        choke=(0.60, ["Persian Gulf → Suez → West Africa",
                      "India → Cape → West Africa",
                      "West Africa → Europe (Nigeria/Angola)"],
               "Multiple supply routes but all seaborne. Suez disruption "
               "(Houthis 2024) showed vulnerability."),
        proc=(17, 3.5, 14, "Africa has massive refining deficit. Dangote "
              "Refinery (NG, 650 k bbl/day) transformative if fully "
              "operational. Ghana's TOR small & unreliable."),
        fin=(0.30, ["Tullow Oil (UK)", "Eni (IT)",
                    "TotalEnergies (FR)", "NNPC (NG state)",
                    "Sonangol (AO state)"],
             False, "Nigeria's NNPC and Angola's Sonangol are state-owned. "
             "Mix of IOCs and national companies."),
        reg=(False, True, False, True,
             "Paris Agreement commitments. EU CBAM may affect refined "
             "product trade. ESG pressure on fossil fuels in Africa."),
        price=("Brent Crude proxy", 80, 40),
    ),

    # ── PLATINUM GROUP METALS ─────────────────────────────────────────────────
    "Platinum Group Metals": dict(
        cat="Critical Mineral",
        use="Catalytic converters, H₂ fuel cells, electronics, jewellery, "
            "industrial catalysts",
        prod_mt=190, unit="metric tons",                       # USGS MCS 2025
        africa={
            "South Africa": dict(share=72.0, prod=137,         # USGS MCS 2025
                                  res=63_000),
            "Zimbabwe":     dict(share=8.0,  prod=15,           # USGS MCS 2025
                                  res=1_200),
        },
        af_share=80.0,
        buyers={"EU-27": .22, "Japan": .20, "USA": .18,        # UN Comtrade 2023
                "China": .18, "South Korea": .08, "Others": .14},
        hhi=0.16,                                              # UN Comtrade
        sub=(0.25, "Limited subs for catalytic converters (Pd ↔ Pt partially). "
             "H₂ fuel cells need Pt. Jewellery: some substitution."),
        stock=(0.90, "Extremely high value-to-weight; easy to stockpile. "
               "Autocatalyst recycling is significant secondary source."),
        choke=(0.30, ["South Africa → direct to all major markets"],
               "SA has well-developed port infrastructure. Richards Bay, "
               "Durban. Low chokepoint risk."),
        proc=(8, 55, 15, "SA has the most integrated PGM processing chain "
              "in Africa. Anglo American Platinum, Sibanye-Stillwater, "
              "Impala operate refineries."),
        fin=(0.40, ["Anglo American Platinum (SA/UK)",
                    "Sibanye-Stillwater (SA)", "Impala Platinum (SA)"],
             False, "Unusually, PGMs are dominated by SA-headquartered "
             "companies. Lower foreign dependency than other African "
             "minerals."),
        reg=(True, False, True, True,
             "Critical for EU Green Deal (hydrogen strategy). US lists as "
             "critical mineral. SA has existing beneficiation requirements."),
        price=("LBMA Platinum Fix", 960, 30),  # USD / troy oz
    ),

    # ── GOLD ──────────────────────────────────────────────────────────────────
    "Gold": dict(
        cat="Precious Metal",
        use="Monetary reserves, jewellery (>50 %), electronics, dentistry, "
            "industrial applications",
        prod_mt=3_600, unit="metric tons",                     # USGS MCS 2024 / WGC
        africa={
            "Ghana":        dict(share=15.0, prod=140,          # Ghana Minerals Commission / USGS MCS 2024
                                 res=1_000),
            "Mali":         dict(share=2.8,  prod=100,          # Chamber of Mines of Mali 2024
                                 res=800),
            "South Africa": dict(share=2.7,  prod=98,           # Minerals Council SA / USGS 2024
                                 res=6_000),
            "Tanzania":     dict(share=1.5,  prod=55,           # USGS MCS 2024 / Tanzania MEM
                                 res=None),
            "Zimbabwe":     dict(share=1.3,  prod=49,           # Zimbabwe Gold 2024
                                 res=None),
            "Nigeria":      dict(share=0.1,  prod=3,            # Artisanal; NSDP / USGS
                                 res=None),
        },
        af_share=25.0,
        buyers={"EU (Switzerland hub)": .30, "China": .25,      # WGC / UN Comtrade 2023-24
                "India": .15, "UAE": .15, "USA": .10,
                "Others": .05},
        hhi=0.19,
        sub=(0.55, "Gold has monetary / reserve role but substitutable in "
             "industrial uses. Electronics can use silver or copper instead. "
             "Jewellery alternatives exist at lower prices."),
        stock=(0.25, "Massive above-ground stocks (~200,000 t globally). "
               "Central banks hold ~35,000 t. US, Germany, Italy, France "
               "are largest holders. Very hard to create scarcity."),
        choke=(0.40, ["Gulf of Guinea → Europe / UAE",
                      "Cape of Good Hope → Asia / Europe",
                      "East Africa → UAE hub"],
               "West African gold often flown (high value). UAE (Dubai) "
               "is a major routing hub. Smuggling is endemic."),
        proc=(8, 5, 15, "Africa has ~5 % of global refining (RAND refinery "
              "SA; Asahi Refining). Switzerland accounts for ~70 % of "
              "global gold refining. China and India also significant."),
        fin=(0.50, ["AngloGold Ashanti (SA/AU)", "Gold Fields (SA)",
                    "Barrick Gold (CA)", "Endeavour Mining (CA)"],
             True, "Chinese firms increasingly present in artisanal / "
             "small-scale mining. Ghana has PMMC (state buyer). "
             "Mali nationalized Loulo-Gounkoto (Barrick) in 2024."),
        reg=(False, False, True, True,
             "OECD Due Diligence Guidance for conflict minerals. US Dodd-Frank "
             "§ 1502 adjacent. OECD conflict-gold frameworks. "
             "EU Conflict Minerals Regulation (2021)."),
        price=("LBMA Gold PM Fix", 2_300, 18),                  # USD / troy oz; 2024 avg
    ),

    # ── COFFEE ────────────────────────────────────────────────────────────────
    "Coffee": dict(
        cat="Agricultural Commodity",
        use="Beverage consumption (primary), food flavouring, cosmetics, "
            "energy products",
        prod_mt=10_500_000,  # world ~175M bags × 60kg = ~10.5M metric tons
        unit="60 kg bags",                                     # ICO 2024/25
        africa={
            "Ethiopia":      dict(share=5.7,  prod=9_910_000,   # ICO / USDA 2024/25
                                  res=None),
            "Uganda":        dict(share=4.0,  prod=7_050_000,   # UCDA 2024
                                  res=None),
            "Côte d'Ivoire": dict(share=1.5,  prod=2_500_000,   # ICO 2024
                                  res=None),
            "Tanzania":      dict(share=0.8,  prod=1_300_000,   # ICO 2024
                                  res=None),
            "Kenya":         dict(share=0.5,  prod=850_000,     # ICO 2024; premium Arabica
                                  res=None),
            "Rwanda":        dict(share=0.2,  prod=350_000,     # ICO 2024
                                  res=None),
        },
        af_share=12.7,
        buyers={"EU-27": .60, "USA": .15, "Japan": .05,         # ICO / UN Comtrade 2023
                "China": .03, "Others": .17},
        hhi=0.40,
        sub=(0.70, "Coffee is culturally entrenched in consuming markets. "
             "Tea is partial substitute but different product. "
             "Limited substitution — moderate-high demand inelasticity."),
        stock=(0.45, "Perishable, limited strategic stocks. ICO buffer "
               "stock schemes historically failed. Roasters hold 1-3 mo. "
               "EUDR compliance stock builds could absorb volatility."),
        choke=(0.55, ["Djibouti → Suez → EU (Ethiopia)",
                      "Mombasa → Cape → EU (Kenya/Uganda/Rwanda)",
                      "Gulf of Guinea → EU (Côte d'Ivoire)"],
               "Ethiopia's entire export funnel through Djibouti. "
               "Mombasa handles East African bulk. "
               "EU Deforestation Regulation creates compliance chokepoint."),
        proc=(5, 7, 55, "Roasting / value-add dominated by EU/US brands. "
              "Africa has ~7 % of global roasting. Ethiopia ECX provides "
              "some price power. Nespresso / JDE Peet's dominate EU."),
        fin=(0.35, ["Nestlé (CH)", "JDE Peet's (NL)",
                    "Starbucks (US)", "Louis Dreyfus (NL/CH)"],
             False, "Coffee largely private-sector traded. Ethiopia ECX "
             "is state-regulated. Uganda: UCDA oversight. No Chinese "
             "strategic presence like in minerals."),
        reg=(False, False, False, True,
             "EU Deforestation Regulation (EUDR) 2023 — major compliance "
             "burden for African producers. Requires geolocation & zero-"
             "deforestation proof. Delayed to Dec 2025. ILO labour standards. "
             "EU CS3D (CSDDD) extends due diligence to agri supply chains."),
        price=("ICE Arabica NY (arabica reference)", 4.50, 30),  # USD/lb; 2024-25 highs
    ),

    # ── COPPER ────────────────────────────────────────────────────────────────
    "Copper": dict(
        cat="Industrial Metal",
        use="Electrical wiring, EV motors & batteries, power grids, "
            "construction, electronics",
        prod_mt=22_000_000, unit="metric tons",                # USGS MCS 2024
        africa={
            "DRC":          dict(share=12.0, prod=2_800_000,   # USGS MCS 2024 / Cobalt Institute
                                 res=31_000_000),
            "Zambia":       dict(share=3.7,  prod=820_000,     # Zambia MEM / Reuters 2024
                                 res=21_000_000),
            "South Africa": dict(share=0.3,  prod=60_000,      # USGS MCS 2024
                                 res=3_000_000),
        },
        af_share=16.0,
        buyers={"China": .55, "EU-27": .15, "Japan": .08,      # UN Comtrade 2023
                "South Korea": .06, "USA": .05, "Others": .11},
        hhi=0.33,
        sub=(0.25, "Critical for electrification, EVs, grid, no substitute "
             "at scale. Aluminium can substitute in some electrical uses "
             "but with performance penalty. Copper recycling significant "
             "but not sufficient for transition demand."),
        stock=(0.40, "LME / SHFE stocks relatively thin vs consumption. "
               "China holds strategic copper reserves. US SPR has no Cu. "
               "Market very sensitive to inventory signals."),
        choke=(0.65, ["DRC/Zambia → Lobito Corridor → Lobito (Angola)",
                      "DRC/Zambia → Dar es Salaam (Tanzania)",
                      "DRC/Zambia → Durban (South Africa)"],
               "DRC and Zambia are landlocked — enormous logistics cost. "
               "Lobito Corridor (US/EU $250M investment, 2023) is key. "
               "TAZARA rail is congested. Durban route adds 2,000 km."),
        proc=(45, 3, 12, "China has ~45 % of global copper smelting / "
              "refining. DRC/Zambia export mainly concentrate. "
              "Chambishi Copper Smelter (Zambia) is Chinese-owned. "
              "Very little African refined copper exports."),
        fin=(0.80, ["CMOC (CN)", "Glencore (CH)", "Ivanhoe (CA)",
                    "First Quantum (CA)", "Zijin Mining (CN)"],
             True, "Chinese firms dominate DRC/Zambia copper. CMOC is now "
             "world's largest cobalt producer. Ivanhoe's Kamoa-Kakula "
             "(DRC) world-class deposit. First Quantum in Zambia."),
        reg=(True, False, True, True,
             "EU CRMA lists copper as strategic material. IRA creates "
             "US demand for non-Chinese-sourced copper. CSDDD will apply "
             "due diligence obligations. Lobito Corridor as geopolitical "
             "counter to Belt-and-Road."),
        price=("LME Copper 3-month", 9_000, 25),               # USD/tonne; 2024 avg
    ),

    # ── URANIUM ───────────────────────────────────────────────────────────────
    "Uranium": dict(
        cat="Energy Mineral",
        use="Nuclear power fuel (primary), military applications, "
            "medical isotope production",
        prod_mt=60_000, unit="metric tons U",                  # WNA / IAEA Red Book 2024
        africa={
            "Namibia":      dict(share=12.0, prod=7_333,       # WNA / Ecofin 2024; #3 world
                                 res=275_000),
            "Niger":        dict(share=1.6,  prod=962,          # IAEA Red Book; declined post-2023 coup
                                 res=311_000),
            "South Africa": dict(share=0.6,  prod=370,          # USGS MCS 2024; by-product
                                 res=None),
        },
        af_share=14.2,
        buyers={"China": .40, "EU-27": .35, "USA": .12,        # WNA / Ecofin 2024
                "Japan": .08, "Others": .05},
        hhi=0.30,
        sub=(0.80, "Nuclear fuel rods have no short-term substitution. "
             "Long procurement cycles (2-5 yr). Reactor design locked in "
             "for 40-60 yr lifetime. Only alternative is non-nuclear power."),
        stock=(0.30, "Utilities hold 2-3 years of forward cover inventories. "
               "Uranium can be stockpiled. France, Japan, China hold "
               "substantial strategic inventories. Restocking pressure rising."),
        choke=(0.55, ["Walvis Bay → Cape → nuclear markets (Namibia)",
                      "Cotonou / Lomé → disrupted by Niger coup (2023)",
                      "France controls enrichment capacity (Orano)"],
               "Namibia's uranium flows through Walvis Bay. Niger's supply "
               "chain severely disrupted since July 2023 coup. "
               "Enrichment bottleneck: France/Russia/China dominate."),
        proc=(35, 0, 40, "Zero uranium conversion / enrichment in Africa. "
              "France (Orano) controls historical Niger refining. "
              "Russia (Rosatom) and China (CNNC) expanding enrichment. "
              "Namibia exports uranium oxide (U3O8 yellowcake only)."),
        fin=(0.60, ["Orano (FR state)", "CGN (CN state)",
                    "Paladin Energy (AU)", "Uranium One (RU)"],
             True, "77 % of Namibia's uranium exports go to China (CGN, "
             "CNNC). France historically dominant in Niger (Orano / "
             "Areva). Post-coup, France lost access. Geopolitical prize."),
        reg=(False, False, True, False,
             "US designates uranium as critical mineral. Nuclear Non-"
             "Proliferation Treaty framework governs trade. US Inflation "
             "Reduction Act supports nuclear restart, boosting demand. "
             "Namibia's EPL moratorium (2013-2017) shows sovereign risk."),
        price=("UxC U3O8 spot", 90, 25),                        # USD/lb; 2024 avg ~$85-95
    ),
}

# ── Policy definitions ─────────────────────────────────────────────────────────
POLICIES = {
    "Export Tax/Restriction": dict(
        id="export_tax",
        desc="Impose a tax or quota on raw commodity exports to capture more "
             "value domestically and incentivise local processing.",
        params={"tax_rate_pct":    (0, 80, 20, "Export Tax Rate (%)"),
                "phase_in_years":  (0, 5,  2,  "Phase-in Period (years)")},
        precedents=[
            "Indonesia: Nickel ore export ban (2020) — attracted Chinese "
            "smelter investment, became world's largest Ni processor. WTO "
            "ruled against ban but Indonesia maintained it.",
            "Zimbabwe: Raw lithium export ban (2022) — pushed for local "
            "processing but limited new investment (sanctions / governance).",
            "India: Iron ore export duty (2022, 50 %) — reduced exports but "
            "hurt small miners.",
            "Niger: Uranium leverage pre-coup — France dependency on SOMAIR. "
            "Coup (2023) disrupted flows; France suspended aid.",
            "Mali: New Mining Code (2023) — raised royalties, state "
            "participation; triggered Barrick Gold dispute at Loulo-Gounkoto.",
        ],
        wto="High — likely inconsistent with GATT Art. XI. But enforcement "
            "is slow and WTO dispute-settlement mechanism partly "
            "dysfunctional.",
    ),
    "Local Processing Mandate": dict(
        id="processing_mandate",
        desc="Require a minimum share of production to be processed "
             "domestically before export.",
        params={"proc_pct":   (0, 100, 30, "Min. Local Processing (%)"),
                "timeline_yr": (1, 10,  5,  "Implementation Timeline (yr)")},
        precedents=[
            "Indonesia: Down-streaming policy (2014-2020) — built significant "
            "smelting capacity. Nickel pig iron → stainless → EV batteries.",
            "South Africa: MPRDA beneficiation provisions — limited "
            "enforcement success.",
            "Tanzania: Mining Act 2017 — required local beneficiation, "
            "triggered investor disputes.",
            "DRC: 2018 Mining Code (10 % royalty on strategic minerals) "
            "and push for copper / cobalt beneficiation.",
            "Zambia: Push for copper beneficiation and smelter expansion "
            "post-debt restructuring (2023).",
        ],
        wto="Medium — may conflict with GATT / TRIMS. Resource-sovereignty "
            "arguments have legal basis.",
    ),
    "Offtake Agreement Requirements": dict(
        id="offtake",
        desc="Mandate that mining licences include offtake agreements "
             "guaranteeing a portion of output to domestic industry.",
        params={"domestic_pct": (0, 50, 15, "Domestic Offtake (%)"),
                "discount_pct": (0, 30, 10, "Partner Discount (%)")},
        precedents=[
            "Chile: Li contracts renegotiated for domestic supply at "
            "preferential rates.",
            "Australia: Critical-minerals offtake agreements with Japan, "
            "South Korea, EU as geopolitical diversification.",
            "DRC: Gécamines retains offtake rights in JV agreements.",
            "Ethiopia: ECX (Ethiopia Commodity Exchange) mandates export "
            "routing through state platform for coffee.",
        ],
        wto="Low-Medium — contractual terms within sovereign right. Less "
            "WTO exposure than export restrictions.",
    ),
    "Joint Venture Requirements": dict(
        id="jv",
        desc="Require foreign miners to partner with domestic entities "
             "(state or private) with minimum local equity.",
        params={"local_eq_pct": (0, 51, 20, "Min. Local Equity (%)"),
                "state_pct":    (0, 30, 10, "State Participation (%)")},
        precedents=[
            "Tanzania: 16 % free-carried interest (2017 Mining Act).",
            "DRC: 10 % free-carried + 5 % purchasable (2018 Mining Code).",
            "Ghana: Minerals & Mining Act requires 10 % free-carried interest.",
            "Indonesia: 51 % local ownership after 10 yr of operation.",
            "Angola: Sonangol retains majority stake in upstream blocks.",
            "Rwanda: State equity in mining concessions under revised code.",
        ],
        wto="Low — standard in mining codes globally. Challenge comes from "
            "BIT obligations, not WTO.",
    ),
    "Corridor Investment Linkage": dict(
        id="corridor",
        desc="Link mining concessions to infrastructure investment (rail, "
             "port, power) benefiting the broader economy.",
        params={"infra_pct":  (0, 15, 5,  "Infra Investment (% of revenue)"),
                "local_cont": (0, 60, 30, "Local Content Requirement (%)")},
        precedents=[
            "Guinea (Simandou): Rail + port infra tied to iron-ore concession "
            "(Rio Tinto / Chinalco). $15 B+ project.",
            "Lobito Corridor: US/EU-backed rail linking DRC/Zambia Cu/Co to "
            "Angola's Lobito port. $250M US investment (2023).",
            "Mozambique: Nacala Corridor tied to Vale's coal operations.",
            "Lamu Port–South Sudan–Ethiopia Transport (LAPSSET): Kenya-led "
            "corridor linking Lamu port to interior.",
            "East Africa SGR (Standard Gauge Railway): Kenya/Uganda/Rwanda "
            "linked to Mombasa port.",
        ],
        wto="Low — within sovereign regulatory space. Performance "
            "requirements may conflict with some BITs.",
    ),
    "Sanctions-Shock Scenario": dict(
        id="sanctions",
        desc="Model impact of sudden export restrictions by major buyers "
             "or geopolitical disruptions.",
        params={"disruption_pct": (0, 80, 30, "Supply Disruption (%)"),
                "duration_mo":    (1, 24, 6,  "Duration (months)")},
        precedents=[
            "China: Rare-earth export restrictions to Japan (2010) — "
            "triggered global diversification.",
            "Russia: Energy-supply disruptions to EU (2022) — massive "
            "reorientation of European energy policy.",
            "China: Gallium / germanium export controls (2023) — signalled "
            "willingness to weaponise mineral dominance.",
            "Niger coup (2023): Orano uranium operations disrupted; "
            "France lost reliable access to 15 % of EU uranium supply.",
        ],
        wto="Variable — may invoke GATT Art. XXI national-security "
            "exceptions. Mixed legality.",
    ),
    "Producer Cartel / Coordination": dict(
        id="cartel",
        desc="Coordinate with other African / global producers to set price "
             "floors, manage supply, or collectively negotiate.",
        params={"cartel_share": (20, 90, 50, "Cartel Market Share (%)"),
                "premium_pct":  (0,  50, 15, "Target Price Premium (%)")},
        precedents=[
            "OPEC: Successful oil cartel — unique due to commodity "
            "characteristics and Saudi swing capacity.",
            "Ghana / CI: Living Income Differential (LID) for cocoa — "
            "$400 / t premium. Mixed enforcement.",
            "Chile / AU: Informal lithium coordination discussed, "
            "not implemented.",
            "DRC / Zambia: Proposed 'battery belt' coordination on Co/Cu "
            "— 2022-24 discussions. DRC-Zambia-Zimbabwe corridor.",
            "African Coffee Alliance: Proposed coordination body for "
            "Ethiopia, Uganda, Kenya to negotiate with EU buyers.",
            "Uranium: Post-coup Niger / Namibia — no formal cartel but "
            "parallel buyer diversification to China creates leverage.",
        ],
        wto="Medium — not directly WTO-prohibited but faces antitrust "
            "scrutiny in buyer jurisdictions.",
    ),
}

# ── Assumption register (14 entries) ──────────────────────────────────────────
ASSUMPTIONS = [
    ("A001", "Buyer Concentration",
     "Shares from UN Comtrade 2022-23 via WITS. Represent import value, "
     "not volume.", "Medium", "UN Comtrade / WITS"),
    ("A002", "Processing Capacity",
     "China's share estimated from USGS, CRU Group, academic literature. "
     "Exact facility-level data not public for all commodities.",
     "High", "USGS MCS 2025, CFR, IMF"),
    ("A003", "Substitutability",
     "Scored 0-1 via qualitative assessment of alternatives, transition "
     "timeline, cost penalty. Not a precise econometric estimate.",
     "Medium", "USGS, expert assessment"),
    ("A004", "Chokepoint Sensitivity",
     "Based on route dependency (Suez, Malacca, Cape) and alternatives. "
     "Uses distance proxies, not proprietary AIS vessel-tracking.",
     "Low-Medium", "UNCTAD Review of Maritime Transport 2024"),
    ("A005", "Financing Dependency",
     "Based on public ownership structures, EITI, annual reports. "
     "Undisclosed offtake agreements may be missed.",
     "Medium", "Company reports, EITI"),
    ("A006", "Regulatory Exposure",
     "Based on published EU/US legislation as of Mar 2026. "
     "Implementation / enforcement may evolve.",
     "Medium", "EU CRMA 2024, CSDDD, EUDR, US IRA, Dodd-Frank"),
    ("A007", "Price Data",
     "Indicative 2024 averages. Actual contract prices differ due to "
     "grade, delivery terms, long-term agreements.",
     "Low", "LME, ICE, LBMA, USGS, WNA"),
    ("A008", "Second-Order Effects",
     "Capital flight, smuggling, retaliation, ISDS risk calibrated to "
     "historical precedents (ID Ni ban, ZW Li ban, CI cocoa, NG oil). "
     "Scenario indicators, not forecasts.",
     "High", "Academic lit, WTO disputes, ICSID"),
    ("A009", "Production Shares",
     "From USGS MCS 2025, IMF. Some gov-reported; may miss artisanal "
     "/ informal production.",
     "Low-Medium", "USGS MCS 2025, IMF REO Apr 2024"),
    ("A010", "Cocoa as Strategic Commodity",
     "Included as 'strategic political commodity' following 2024 price "
     "crisis and Ghana/CI LID policy. Leverage dynamics differ from "
     "minerals.", "Medium", "ICCO, COCOBOD, World Bank CMO"),
    ("A011", "Gold Smuggling & Artisanal Mining",
     "Africa's official gold production is underestimated. Artisanal/small "
     "scale mining (ASM) adds 20-30 % unreported production in Ghana, "
     "Mali, DRC, Tanzania. Leverage scores assume official figures only.",
     "High", "OECD, Swissaid 2024, Ghana Minerals Commission"),
    ("A012", "Coffee Production Units",
     "Coffee production expressed in 60 kg bags (ICO standard). Global "
     "production ~175M bags/yr. Ethiopia and Uganda production from "
     "ICO/USDA 2024-25 estimates. Seasonal variation ±15 %.",
     "Medium", "ICO Statistical Report 2024-25, USDA FAS"),
    ("A013", "Copper / Cobalt — Lobito Corridor",
     "Lobito Corridor cost and completion timeline assumed from US/EU "
     "public commitments ($250M, completion 2025-26). Actual throughput "
     "impact on leverage is a 3-5 yr outlook item.",
     "High", "US State Dept, EU Global Gateway, Reuters 2023"),
    ("A014", "Uranium — Niger Post-Coup",
     "Niger production data is pre-coup (2022 IAEA Red Book). 2023 coup "
     "disrupted Orano operations; 2024 production significantly lower. "
     "Namibia production from WNA 2024. Both flagged as high-uncertainty.",
     "High", "IAEA Red Book 2024, WNA, Reuters 2023-24"),
]


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                     SECTION 3 — LEVERAGE MODEL                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

LEVER_DIMS = [
    "Buyer Diversification",
    "Substitutability Barrier",
    "Stockpiling Difficulty",
    "Chokepoint Control",
    "Processing Capacity",
    "Financial Independence",
    "Regulatory Leverage",
]

LEVER_WEIGHTS = {
    "Buyer Diversification":   0.15,
    "Substitutability Barrier": 0.20,
    "Stockpiling Difficulty":   0.10,
    "Chokepoint Control":       0.10,
    "Processing Capacity":      0.20,
    "Financial Independence":   0.15,
    "Regulatory Leverage":      0.10,
}


def _clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def compute_leverage(cdata, country=None):
    """Return dict with 'dims' (7-dim scores), 'composite', 'af_share', 'c_share'."""
    hhi   = cdata.get("hhi", 0)
    sub   = cdata["sub"][0]
    stk   = cdata["stock"][0]
    chk   = cdata["choke"][0]
    af_pr = cdata["proc"][1]     # africa processing %
    cn_pr = cdata["proc"][0]     # china processing %
    fin   = cdata["fin"][0]
    reg   = cdata["reg"]

    dims = {}
    dims["Buyer Diversification"]   = _clamp((1 - hhi) * 80 + 20)
    dims["Substitutability Barrier"] = _clamp((1 - sub) * 100)
    dims["Stockpiling Difficulty"]   = _clamp((1 - stk) * 100)
    dims["Chokepoint Control"]       = _clamp(chk * 100)
    dims["Processing Capacity"]      = _clamp(af_pr * 1.5 + (100 - cn_pr) * 0.3)
    dims["Financial Independence"]   = _clamp((1 - fin) * 100)
    reg_cnt = sum([reg[0], reg[1], reg[2], reg[3]])
    dims["Regulatory Leverage"]      = _clamp(reg_cnt * 20 + 15)

    # round all
    dims = {k: round(v, 1) for k, v in dims.items()}

    af_share = cdata.get("af_share", 0)
    is_dep   = cdata.get("_dependency", False)

    # For Refined Petroleum: if selected country is a net exporter, use full multiplier
    if is_dep and country and country in cdata.get("_net_exporters", []):
        multiplier = 1.0 + af_share / 200
    elif is_dep:
        multiplier = 0.3
    else:
        multiplier = 1.0 + af_share / 200

    raw = sum(dims[k] * LEVER_WEIGHTS[k] for k in LEVER_DIMS)
    composite = _clamp(raw * multiplier)

    c_share = 0
    if country:
        c_share = cdata.get("africa", {}).get(country, {}).get("share", 0)

    return dict(dims=dims, composite=round(composite, 1),
                af_share=af_share, c_share=c_share,
                raw=round(raw, 1), multiplier=round(multiplier, 3))


def interpret_leverage(score):
    if score >= 75:
        return ("High", "#2E7D32",
                "Strong structural leverage. Policy interventions likely "
                "credible with manageable blowback.",
                "Consider graduated measures (processing mandates, JV "
                "requirements) with clear sequencing. Build coalitions "
                "with co-producers.")
    if score >= 55:
        return ("Moderate", "#F57F17",
                "Meaningful but conditional leverage. Success depends on "
                "execution quality and managing second-order risks.",
                "Prioritise leverage-building (processing investment, buyer "
                "diversification) before deploying restrictive policies. "
                "Phased approach recommended.")
    if score >= 35:
        return ("Limited", "#E65100",
                "Leverage exists but is significantly constrained. "
                "Unilateral action carries high blowback / circumvention risk.",
                "Focus on structural improvements: attract diverse investors, "
                "develop infrastructure. Multilateral approaches preferred.")
    return ("Minimal", "#B71C1C",
            "Very limited leverage. Structural dependencies constrain "
            "policy options significantly.",
            "Prioritise long-term reforms: human capital, diverse investors, "
            "infrastructure. Avoid confrontational postures.")


def gap_analysis(cdata, country=None):
    lv  = compute_leverage(cdata, country)
    out = []
    feas_map = {
        "Buyer Diversification":   "Medium (trade diplomacy)",
        "Substitutability Barrier": "Low (geologically determined)",
        "Stockpiling Difficulty":   "Low (commodity physics)",
        "Chokepoint Control":       "Low (geography)",
        "Processing Capacity":      "High (investment, 5-10 yr)",
        "Financial Independence":   "Medium (investor diversification)",
        "Regulatory Leverage":      "Medium (institutional capacity)",
    }
    for d in LEVER_DIMS:
        gap = 100 - lv["dims"][d]
        out.append(dict(
            dim=d, score=lv["dims"][d], gap=round(gap, 1),
            w_impact=round(gap * LEVER_WEIGHTS[d], 1),
            feasibility=feas_map[d],
        ))
    out.sort(key=lambda x: x["w_impact"], reverse=True)
    return out


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECTION 4 — POLICY SIMULATOR                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _risk_level(s):
    if s >= 70: return "Critical"
    if s >= 50: return "High"
    if s >= 30: return "Moderate"
    if s >= 15: return "Low"
    return "Minimal"


def _risk_badge_html(level):
    cls = level.lower()
    valid = {"critical", "high", "moderate", "limited", "low", "minimal"}
    if cls not in valid:
        cls = "moderate"
    return f'<span class="rbadge rbadge-{cls}">{level}</span>'


def simulate_policy(cdata, leverage, policy_id, params):
    """Run policy simulation.  Returns dict with modified dims, first-order
    effects, second-order risks, composite change."""
    dims   = {k: v for k, v in leverage["dims"].items()}  # copy
    af_sh  = cdata.get("af_share", 0)
    sub    = cdata["sub"][0]
    fin    = cdata["fin"][0]
    cn_pr  = cdata["proc"][0]
    hhi    = cdata.get("hhi", 0)
    cn_inv = cdata["fin"][2]  # chinese_investment_present

    first = {}

    # ── first-order & dim modifications per policy ────────────────────────────

    if policy_id == "export_tax":
        t = params.get("tax_rate_pct", 20)
        ph = params.get("phase_in_years", 2)
        rev = t * af_sh / 100 * (1 - sub * 0.5)
        pr_eff = t * 0.3 * (1 - sub) * (af_sh / 50)
        first = {
            "Government Revenue": f"+{rev:.1f} % (tax collected)",
            "Export Volume":      f"−{t * 0.4 * (1 + sub):.1f} % (demand reduction)",
            "Global Price":       f"+{pr_eff:.1f} % (supply tightening)",
            "Processing Signal":  ("Strong" if t > 30 else "Moderate"
                                   if t > 15 else "Weak") +
                                  " incentive for local processing",
            "Timeline":           f"{ph}–{ph+2} yr for full impact",
        }
        dims["Processing Capacity"]    = _clamp(dims["Processing Capacity"] + t * 0.3)
        dims["Regulatory Leverage"]    = _clamp(dims["Regulatory Leverage"] + 10)
        dims["Financial Independence"] = _clamp(dims["Financial Independence"] - t * 0.15)
        intensity = t

    elif policy_id == "processing_mandate":
        p = params.get("proc_pct", 30)
        tl = params.get("timeline_yr", 5)
        first = {
            "Value-Add Capture": f"+{p * 0.8:.0f} % domestic value retention",
            "Employment":        f"+{p*200:.0f}–{p*500:.0f} direct processing jobs (est.)",
            "Capex Required":    f"${p*50:.0f} M–${p*200:.0f} M",
            "Energy Demand":     f"+{p*0.5:.0f} % industrial energy need",
            "Export Volume (ST)": f"−{p*0.3:.0f} % while capacity builds",
            "Timeline":          f"{tl} yr to full implementation",
        }
        dims["Processing Capacity"]    = _clamp(dims["Processing Capacity"] + p * 0.5)
        dims["Financial Independence"] = _clamp(dims["Financial Independence"] - p * 0.1)
        intensity = p

    elif policy_id == "offtake":
        dp = params.get("domestic_pct", 15)
        disc = params.get("discount_pct", 10)
        first = {
            "Domestic Supply": f"{dp} % of output reserved for local industry",
            "Revenue Impact":  f"−{disc*dp/100:.1f} % (discount on domestic share)",
            "Industrial Linkage": ("Strong" if dp > 20 else "Moderate"
                                   if dp > 10 else "Weak") +
                                  " downstream catalyst",
            "Buyer Diversification": f"+{dp*0.2:.0f} pts",
        }
        dims["Buyer Diversification"] = _clamp(dims["Buyer Diversification"] + dp * 0.3)
        dims["Processing Capacity"]   = _clamp(dims["Processing Capacity"] + dp * 0.2)
        intensity = dp

    elif policy_id == "jv":
        le = params.get("local_eq_pct", 20)
        sp = params.get("state_pct", 10)
        first = {
            "Local Ownership":    f"{le} % minimum ({sp} % state)",
            "Revenue Retention":  f"+{(le+sp)*0.3:.1f} % more value in-country",
            "Governance Influence": ("Board seats + veto" if le >= 30
                                     else "Board representation" if le >= 15
                                     else "Minority observer"),
            "Investment Deterrent": ("Significant" if le > 40 else "Moderate"
                                     if le > 25 else "Manageable"),
        }
        dims["Financial Independence"] = _clamp(dims["Financial Independence"] + le * 0.2)
        dims["Processing Capacity"]    = _clamp(dims["Processing Capacity"] + sp * 0.1)
        intensity = le

    elif policy_id == "corridor":
        ip = params.get("infra_pct", 5)
        lc = params.get("local_cont", 30)
        first = {
            "Infrastructure":   f"{ip} % of mining revenue → infrastructure",
            "Local Content":    f"{lc} % procurement from domestic suppliers",
            "Spillover":        ("High" if ip > 8 else "Moderate" if ip > 3
                                 else "Limited") + " multiplier effects",
            "Logistics":        f"−{ip*2:.0f} % transport-cost reduction (est.)",
            "Timeline":         "3–10 yr for infra completion",
        }
        dims["Chokepoint Control"]  = _clamp(dims["Chokepoint Control"] + ip * 2)
        dims["Processing Capacity"] = _clamp(dims["Processing Capacity"] + lc * 0.1)
        intensity = ip

    elif policy_id == "sanctions":
        dp = params.get("disruption_pct", 30)
        dur = params.get("duration_mo", 6)
        first = {
            "Supply Disruption":  f"{dp} % of exports disrupted for {dur} mo",
            "Price Spike":        f"+{dp*1.5*(1-sub):.0f} % (est.)",
            "Revenue Loss (ST)":  f"−{dp*0.7:.0f} % during disruption",
            "Buyer Urgency":      ("Extreme" if dp > 50 else "High" if dp > 25
                                   else "Moderate"),
            "Strategic Signal":   f"Commodity value {'dramatically' if dp > 40 else 'significantly'} demonstrated",
        }
        dims["Buyer Diversification"] = _clamp(dims["Buyer Diversification"] + dp * 0.3)
        dims["Regulatory Leverage"]   = _clamp(dims["Regulatory Leverage"] + dp * 0.2)
        dims["Financial Independence"]= _clamp(dims["Financial Independence"] - dp * 0.3)
        intensity = dp

    elif policy_id == "cartel":
        cs = params.get("cartel_share", 50)
        pm = params.get("premium_pct", 15)
        n_prod = len(cdata.get("africa", {}))
        first = {
            "Market Control":    f"{cs} % of global supply coordinated",
            "Price Premium":     f"+{pm} % above market",
            "Revenue Increase":  f"+{pm*cs/100*(1-sub*0.5):.1f} % (if maintained)",
            "Viability":         ("High" if cs > 60 and sub < 0.3 else "Moderate"
                                  if cs > 40 else "Low"),
            "Coordination":      ("Manageable" if n_prod <= 3 else "Difficult") +
                                 f" ({n_prod} key producers)",
        }
        dims["Buyer Diversification"] = _clamp(dims["Buyer Diversification"] + pm * 0.2)
        dims["Regulatory Leverage"]   = _clamp(dims["Regulatory Leverage"] + cs * 0.15)
        intensity = pm
    else:
        intensity = 0

    # round dims
    dims = {k: round(v, 1) for k, v in dims.items()}

    # ── second-order risks ────────────────────────────────────────────────────
    cap_flight = _clamp(fin * 40 + intensity * 0.3
                        + (15 if policy_id in ("export_tax", "jv") else 0)
                        - (10 if policy_id == "corridor" else 0))
    smuggling  = _clamp(
        (intensity * 0.8 + 10) if policy_id in ("export_tax", "processing_mandate")
        else (intensity * 0.5 + 15 if policy_id == "cartel" else 10))
    retaliation = _clamp(hhi * 50 + intensity * 0.3
                         + (15 if cn_inv and policy_id in ("export_tax", "jv") else 0)
                         + (25 if policy_id == "sanctions" else 0))
    isds_base  = (25 + intensity * 0.4 + fin * 20
                  if policy_id in ("export_tax", "jv", "processing_mandate")
                  else 15 + intensity * 0.2 if policy_id == "offtake" else 10)
    isds       = _clamp(isds_base)
    demand_d   = _clamp(sub * 60 + intensity * 0.3 + (100 - af_sh) * 0.3)
    diplomatic = _clamp(intensity * 0.5 + hhi * 30
                        + (15 if cn_inv else 0))

    second = {
        "Capital Flight":     (round(cap_flight), _risk_level(cap_flight)),
        "Smuggling Incentive": (round(smuggling),  _risk_level(smuggling)),
        "Retaliation":        (round(retaliation), _risk_level(retaliation)),
        "ISDS Risk":          (round(isds),        _risk_level(isds)),
        "Demand Destruction":  (round(demand_d),   _risk_level(demand_d)),
        "Diplomatic Friction": (round(diplomatic), _risk_level(diplomatic)),
    }

    # ── recalculate composite with same multiplier ────────────────────────────
    raw_orig = sum(leverage["dims"][k] * LEVER_WEIGHTS[k] for k in LEVER_DIMS)
    mult = leverage["composite"] / raw_orig if raw_orig > 0 else 1.0
    raw_new  = sum(dims[k] * LEVER_WEIGHTS[k] for k in LEVER_DIMS)
    new_comp = _clamp(raw_new * mult)

    return dict(
        orig_dims=leverage["dims"], mod_dims=dims,
        orig_comp=leverage["composite"], new_comp=round(new_comp, 1),
        delta=round(new_comp - leverage["composite"], 1),
        first=first, second=second,
    )


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                   SECTION 5 — VISUALIZATION BUILDERS                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _polar_layout(title, h=460):
    return plotly_layout(
        title=dict(text=title, font=dict(size=15, color=C["text"])),
        margin=dict(l=120, r=110, t=80, b=80),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(size=10, color=C["muted"]),
                            gridcolor=C["grid"]),
            angularaxis=dict(tickfont=dict(size=10, color=C["text"]),
                             gridcolor=C["grid"]),
            bgcolor=C["card"]),
        showlegend=False, height=h)


def fig_radar(lv, name, country=None):
    cats = list(lv["dims"].keys())
    vals = list(lv["dims"].values())
    cats_c, vals_c = cats + [cats[0]], vals + [vals[0]]
    fig = go.Figure(go.Scatterpolar(
        r=vals_c, theta=cats_c, fill="toself",
        fillcolor="rgba(32,128,141,.22)",
        line=dict(color=C["teal"], width=2.5),
        hovertemplate="%{theta}: %{r:.1f}/100<extra></extra>"))
    t = f"Leverage Vector: {name}" + (f" ({country})" if country else "")
    fig.update_layout(**_polar_layout(t))
    return fig


def fig_radar_compare(results):
    fig = go.Figure()
    for i, (nm, lv) in enumerate(results.items()):
        cats = list(lv["dims"].keys())
        vals = list(lv["dims"].values())
        clr = CHART_SEQ[i % len(CHART_SEQ)]
        r, g, b = int(clr[1:3], 16), int(clr[3:5], 16), int(clr[5:7], 16)
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself", fillcolor=f"rgba({r},{g},{b},.08)",
            line=dict(color=clr, width=2),
            name=f"{nm} ({lv['composite']})",
            hovertemplate=f"{nm}<br>%{{theta}}: %{{r:.1f}}/100<extra></extra>"))
    fig.update_layout(**_polar_layout("Comparative Leverage", h=620))
    fig.update_layout(showlegend=True,
        legend=dict(orientation="h", y=-0.2, xanchor="center", x=0.5,
                    font=dict(size=10)))
    return fig


def fig_buyers(cdata, name):
    buyers = {k: v for k, v in cdata.get("buyers", {}).items()
              if isinstance(v, (int, float))}
    if not buyers:
        return None
    df = pd.DataFrame({"Buyer": list(buyers.keys()),
                        "Share": [v * 100 for v in buyers.values()]})
    df = df.sort_values("Share", ascending=True)
    colors = [C["rust"] if b == "China" else C["teal"] for b in df["Buyer"]]
    fig = go.Figure(go.Bar(
        x=df["Share"], y=df["Buyer"], orientation="h",
        marker=dict(color=colors), text=[f"{v:.0f} %" for v in df["Share"]],
        textposition=["outside" if v > 12 else "inside" for v in df["Share"]],
        hovertemplate="%{y}: %{x:.1f} %<extra></extra>"))
    fig.update_layout(**plotly_layout(
        title=dict(text=f"Buyer Concentration: {name} (HHI {cdata.get('hhi',0):.2f})",
                   font=dict(size=13)),
        xaxis=dict(title="Import Share (%)",
                   range=[0, max(df["Share"])*1.3],
                   gridcolor=C["grid"]),
        yaxis=dict(title="", automargin=True), margin=dict(l=180, r=70, t=70, b=45),
        height=max(360, len(df)*36), showlegend=False))
    return fig


def fig_processing(commodities):
    rows = []
    for nm, cd in commodities.items():
        rows.append(dict(Commodity=nm, Africa=cd["proc"][1],
                         China=cd["proc"][0], EU=cd["proc"][2]))
    df = pd.DataFrame(rows)
    fig = go.Figure()
    for col, clr in [("Africa", C["teal"]), ("China", C["rust"]),
                      ("EU", C["dark_teal"])]:
        fig.add_trace(go.Bar(
            name=col, x=df["Commodity"], y=df[col],
            marker=dict(color=clr),
            text=[f"{v:.0f} %" for v in df[col]], textposition="outside",
            hovertemplate=f"{col}<br>%{{x}}: %{{y:.1f}} %<extra></extra>"))
    fig.update_layout(**plotly_layout(
        title=dict(text="Processing Capacity Gap: Africa vs China vs EU",
                   font=dict(size=13)),
        barmode="group",
        xaxis=dict(title="", tickangle=-30, automargin=True),
        yaxis=dict(title="Share of Global Processing (%)",
                   gridcolor=C["grid"]),
        legend=dict(orientation="h", y=1.05, xanchor="right", x=1),
        margin=dict(l=75, r=60, t=80, b=120), height=480))
    return fig


def fig_heatmap(results):
    comms = list(results.keys())
    z = [[results[c]["dims"][d] for d in LEVER_DIMS] for c in comms]
    fig = go.Figure(go.Heatmap(
        z=z, x=LEVER_DIMS, y=comms,
        colorscale=[[0,RISK_CLR["Critical"]],[.35,RISK_CLR["High"]],
                    [.55,RISK_CLR["Moderate"]],[.8,RISK_CLR["Low"]],[1,RISK_CLR["Minimal"]]],
        text=[[f"{v:.0f}" for v in row] for row in z],
        texttemplate="%{text}", hovertemplate=
        "Commodity: %{y}<br>Dimension: %{x}<br>Score: %{z:.1f}<extra></extra>",
        colorbar=dict(title="Score", ticksuffix="/100")))
    fig.update_layout(**plotly_layout(
        title=dict(text="Leverage Heatmap", font=dict(size=13)),
        xaxis=dict(title="", tickangle=-35, automargin=True), yaxis=dict(title="", automargin=True),
        height=max(400, len(comms) * 38)))
    return fig


def fig_sankey(cdata, name):
    producers = cdata.get("africa", {})
    buyers = {k: v for k, v in cdata.get("buyers", {}).items()
              if isinstance(v, (int, float))}
    if not producers or not buyers:
        return None
    nodes, src, tgt, vals, link_clr = [], [], [], [], []
    pnames = list(producers.keys())
    for p in pnames:
        nodes.append(p)
    c_idx = len(nodes)
    nodes.append(name)
    bnames = list(buyers.keys())
    for b in bnames:
        nodes.append(b)
    for i, (pn, pd) in enumerate(producers.items()):
        src.append(i); tgt.append(c_idx)
        vals.append(pd.get("share", 1))
        link_clr.append("rgba(79,166,179,.35)")
    for j, (bn, bs) in enumerate(buyers.items()):
        src.append(c_idx); tgt.append(c_idx + 1 + j)
        vals.append(bs * 100)
        if bn == "China":
            link_clr.append("rgba(143,90,66,.45)")
        elif "EU" in bn:
            link_clr.append("rgba(70,110,120,.45)")
        else:
            link_clr.append("rgba(120,149,157,.45)")
    ncol = []
    for n in nodes:
        if n in pnames:    ncol.append(C["teal"])
        elif n == name:    ncol.append(C["gold"])
        elif n == "China": ncol.append(C["rust"])
        elif "EU" in n:    ncol.append(C["dark_teal"])
        else:              ncol.append(C["cyan_light"])
    fig = go.Figure(go.Sankey(
        node=dict(pad=15, thickness=20, label=nodes, color=ncol,
                  line=dict(color="rgba(0,0,0,.08)", width=.5)),
        link=dict(source=src, target=tgt, value=vals, color=link_clr)))
    fig.update_layout(**plotly_layout(
        title=dict(text=f"Trade Flow: {name} (Africa → Global)",
                   font=dict(size=13)), height=420))
    return fig


def fig_gap(gap_data):
    df = pd.DataFrame(gap_data)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["score"], y=df["dim"], orientation="h",
        name="Current", marker=dict(color=C["teal"])))
    fig.add_trace(go.Bar(x=df["gap"], y=df["dim"], orientation="h",
        name="Gap to 100", marker=dict(color="rgba(168,75,47,.25)"),
        text=[f"Δ{w:.0f}" for w in df["w_impact"]], textposition="outside"))
    fig.update_layout(**plotly_layout(
        title=dict(text="Leverage Gap Analysis (by weighted impact)",
                   font=dict(size=13)),
        barmode="stack",
        xaxis=dict(title="Score 0-100", range=[0, 115], gridcolor=C["grid"]),
        yaxis=dict(title="", automargin=True),
        legend=dict(orientation="h", y=1.05, xanchor="right", x=1),
        margin=dict(l=210, r=60, t=75, b=60), height=420))
    return fig


def fig_policy_radar(orig, mod, title):
    cats = list(orig.keys())
    ov = [orig[c] for c in cats] + [orig[cats[0]]]
    mv = [mod[c] for c in cats] + [mod[cats[0]]]
    cc = cats + [cats[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=ov, theta=cc, fill="toself",
        fillcolor="rgba(46,86,93,.12)",
        line=dict(color=C["muted"], width=2, dash="dot"), name="Before"))
    fig.add_trace(go.Scatterpolar(r=mv, theta=cc, fill="toself",
        fillcolor="rgba(32,128,141,.18)",
        line=dict(color=C["teal"], width=2.5), name="After"))
    fig.update_layout(**_polar_layout(f"Leverage Impact: {title}"))
    fig.update_layout(showlegend=True,
        legend=dict(orientation="h", y=-0.2, xanchor="center", x=0.5,
                    font=dict(size=10)))
    return fig


def fig_risk_bars(second):
    items = sorted(second.items(), key=lambda x: x[1][0], reverse=True)
    names = [i[0] for i in items]
    scores = [i[1][0] for i in items]
    colors = [RISK_CLR.get(i[1][1], "#999") for i in items]
    fig = go.Figure(go.Bar(
        x=scores, y=names, orientation="h",
        marker=dict(color=colors),
        text=[str(s) for s in scores], textposition=["outside" if s > 12 else "inside" for s in scores],
        hovertemplate="%{y}: %{x}/100<extra></extra>"))
    fig.update_layout(**plotly_layout(
        title=dict(text="Second-Order Risk Assessment", font=dict(size=13)),
        xaxis=dict(title="Risk Score 0-100", range=[0, 110],
                   gridcolor=C["grid"]),
        yaxis=dict(title="", automargin=True), margin=dict(l=220, r=60, t=75, b=60),
        height=420, showlegend=False))
    return fig


def fig_scenario_compare(scenarios):
    names = [s["name"] for s in scenarios]
    orig  = [s["orig"] for s in scenarios]
    newc  = [s["new"]  for s in scenarios]
    risk  = [s["risk"] for s in scenarios]
    fig = make_subplots(rows=1, cols=2,
        subplot_titles=("Leverage Score Change", "Avg Risk Score"),
        horizontal_spacing=.16)
    fig.add_trace(go.Bar(x=names, y=orig, name="Before",
        marker=dict(color=C["muted"])), row=1, col=1)
    fig.add_trace(go.Bar(x=names, y=newc, name="After",
        marker=dict(color=C["teal"])), row=1, col=1)
    fig.add_trace(go.Bar(x=names, y=risk, showlegend=False,
        marker=dict(color=[RISK_CLR["High"] if r > 50
                           else RISK_CLR["Moderate"] if r > 30
                           else RISK_CLR["Low"] for r in risk]),
        text=[f"{r:.0f}" for r in risk], textposition="outside"),
        row=1, col=2)
    fig.update_layout(**plotly_layout(
        title=dict(text="Scenario Comparison", font=dict(size=13)),
        barmode="group", height=460, margin=dict(l=70, r=40, t=90, b=110),
        legend=dict(orientation="h", y=-0.12, xanchor="center", x=.25)))
    fig.update_yaxes(title_text="Composite Score",
                     gridcolor=C["grid"], row=1, col=1)
    fig.update_yaxes(title_text="Risk 0-100",
                     gridcolor=C["grid"], row=1, col=2)
    return fig


def fig_country_profile(country_name):
    """Spider chart for country profile across commodities."""
    cdata_c = COUNTRIES.get(country_name, {})
    # Identify which commodities the country appears in
    present = {}
    for cname, cd in COMMODITIES.items():
        sh = cd.get("africa", {}).get(country_name, {}).get("share", 0)
        if sh > 0:
            present[cname] = sh
    if not present:
        return None
    fig = go.Figure(go.Bar(
        x=list(present.keys()),
        y=list(present.values()),
        marker=dict(color=[C["teal"] if i % 2 == 0 else C["dark_teal"] for i, _ in enumerate(present)]),
        text=[f"{v:.1f} %" for v in present.values()],
        textposition="outside",
        hovertemplate="%{x}: %{y:.1f} % of global production<extra></extra>"))
    fig.update_layout(**plotly_layout(
        title=dict(text=f"{country_name} — Share of Global Production by Commodity",
                   font=dict(size=13)),
        xaxis=dict(title="", tickangle=-30, automargin=True),
        yaxis=dict(title="Global Production Share (%)",
                   gridcolor=C["grid"]),
        margin=dict(l=70, r=40, t=75, b=95), height=400))
    return fig


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                   SECTION 6 — EXPORT HELPERS                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


def make_leverage_csv(lv, name, country):
    rows = []
    for d in LEVER_DIMS:
        rows.append(dict(Commodity=name, Country=country or "All",
                         Dimension=d, Score=lv["dims"][d],
                         Weight=LEVER_WEIGHTS[d],
                         Weighted=round(lv["dims"][d]*LEVER_WEIGHTS[d], 2)))
    rows.append(dict(Commodity=name, Country=country or "All",
                     Dimension="COMPOSITE", Score=lv["composite"],
                     Weight=1.0, Weighted=lv["composite"]))
    return pd.DataFrame(rows)


def make_policy_csv(result, name, policy):
    rows = []
    for k, v in result["first"].items():
        rows.append(dict(Commodity=name, Policy=policy,
                         Type="First-Order", Metric=k, Value=v))
    for k, (sc, lv) in result["second"].items():
        rows.append(dict(Commodity=name, Policy=policy,
                         Type="Second-Order", Metric=k,
                         Value=f"{sc}/100 ({lv})"))
    rows.append(dict(Commodity=name, Policy=policy,
                     Type="Leverage", Metric="Composite",
                     Value=f"{result['orig_comp']} → {result['new_comp']} "
                           f"({result['delta']:+.1f})"))
    return pd.DataFrame(rows)


def make_report_txt(name, cdata, lv, policy_results=None, country=None):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    L = []
    L.append("=" * 78)
    L.append("AFRICAN STRATEGIC LEVERAGE & COMMODITY CONTROL LAB (ASLC) v3.0")
    L.append("Geoeconomic Bargaining Scenario Report")
    L.append("=" * 78)
    L.append(f"\nGenerated: {now}")
    L.append(f"Commodity: {name}")
    if country:
        L.append(f"Country Focus: {country}")
    L.append("\nDISCLAIMER: Scenario analysis tool with explicit assumptions.")
    L.append("Not a forecast. See Assumption Register for methodology.\n")
    L.append("-" * 78)
    L.append("1. COMMODITY OVERVIEW")
    L.append("-" * 78)
    L.append(f"Category:        {cdata['cat']}")
    L.append(f"Strategic Use:   {cdata['use']}")
    prod = cdata["prod_mt"]
    L.append(f"Global Prod.:    {prod:,.0f} {cdata['unit']}" if prod else "")
    L.append(f"African Share:   {cdata['af_share']:.1f} %")
    for pn, pd_item in cdata.get("africa", {}).items():
        p = pd_item.get("prod")
        ps = f"{p:,.0f}" if p else "N/A"
        L.append(f"  - {pn}: {pd_item.get('share',0):.1f} % ({ps} {cdata['unit']})")
    L.append("\n" + "-" * 78)
    L.append("2. LEVERAGE VECTOR")
    L.append("-" * 78)
    L.append(f"Composite: {lv['composite']}/100")
    for d in LEVER_DIMS:
        s = lv["dims"][d]
        bar = "█" * int(s / 5) + "░" * (20 - int(s / 5))
        L.append(f"  {d:<28s} [{bar}] {s:.1f}")
    if policy_results:
        for pr in policy_results:
            L.append("\n" + "-" * 78)
            L.append(f"3. POLICY: {pr['name']}")
            L.append("-" * 78)
            r = pr["result"]
            L.append(f"Leverage: {r['orig_comp']} → {r['new_comp']} "
                     f"({r['delta']:+.1f})")
            L.append("\nFirst-Order:")
            for k, v in r["first"].items():
                L.append(f"  * {k}: {v}")
            L.append("\nSecond-Order Risks:")
            for k, (sc, lev) in r["second"].items():
                L.append(f"  ! {k}: {sc}/100 ({lev})")
    L.append("\n" + "-" * 78)
    L.append("SOURCES")
    L.append("-" * 78)
    for src in ["USGS MCS 2025", "UN Comtrade / WITS",
                "IMF REO SSA Apr 2024", "EU CRMA 2024",
                "EITI Reports", "ICSID Case DB",
                "ICCO / COCOBOD", "ICO / USDA 2024-25",
                "WNA / IAEA Red Book 2024",
                "UNCTAD Maritime Transport 2024"]:
        L.append(f"  - {src}")
    L.append("\n" + "=" * 78)
    return "\n".join(L)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                       SECTION 7 — HTML HELPERS                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def metric_card(label, value, delta=None, border_color=None):
    bc = border_color or C["teal"]
    dh = ""
    if delta is not None:
        sign = "+" if delta > 0 else ""
        cls  = "delta-pos" if delta > 0 else "delta-neg"
        dh = f'<span class="{cls}">{sign}{delta:.1f}</span>'
    st.markdown(
        f'<div class="m-card" style="border-left-color:{bc}">'
        f'<div class="lbl">{label}</div>'
        f'<div class="val">{value}{dh}</div></div>',
        unsafe_allow_html=True)


def source_note(text):
    st.markdown(f'<p class="src">{text}</p>', unsafe_allow_html=True)


def page_header(title, subtitle):
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def analyst_callout(title, text, tone="info"):
    cls = "box-info" if tone == "info" else "box-warn" if tone == "warn" else "box-note"
    st.markdown(f'<div class="{cls}"><b>{title}</b><br>{text}</div>', unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                       SECTION 8 — SIDEBAR & NAV                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

with st.sidebar:
    theme_mode = st.selectbox("Theme", ["Dark", "Light", "Auto"], index=0, key="theme_mode")
    TOK = get_theme(theme_mode)
    apply_theme(TOK)
    _inject_theme_css(TOK)

    st.caption("Analytical navigation")
    st.divider()

    page = st.radio("Navigate", [
        "Overview",
        "Leverage Analysis",
        "Policy Simulator",
        "Comparative Dashboard",
        "Country Explorer",
        "Assumptions",
        "About",
    ], label_visibility="collapsed")

    if page not in ("Assumptions", "About"):
        st.divider()
        sel_comm = st.selectbox("Commodity Focus", list(COMMODITIES.keys()),
                                key="g_comm")
        avail_c = list(COMMODITIES[sel_comm].get("africa", {}).keys())
        if avail_c:
            sel_country = st.selectbox("Focus Country",
                                       ["All Producers"] + avail_c,
                                       key="g_cntry")
            sel_country = None if sel_country == "All Producers" else sel_country
        else:
            sel_country = None
            st.caption("No African producers in database.")
    else:
        sel_comm = list(COMMODITIES.keys())[0]
        sel_country = None

    st.divider()
    analyst_callout(
        "Scenario tool notice",
        "All outputs are scenario-based with explicit assumptions. "
        "Use the Assumptions page for confidence qualifiers and model boundaries.",
        "note",
    )
    st.divider()
    st.markdown('<div class="meta-line">Data window: 2023–2025 public releases</div>', unsafe_allow_html=True)
    st.markdown('<div class="meta-line">Sources: USGS · UN Comtrade · IMF · EU CRMA · ICO · WNA</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
    st.markdown('<div class="insignia">Designing Decision Systems</div>', unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                     SECTION 9 — PAGE: OVERVIEW                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if page == "Overview":
    page_header(
        "African Strategic Leverage & Commodity Control Lab",
        "Analytical instrument for assessing structural exposure, leverage drivers, and policy-relevant intervention logic across African commodity systems.",
    )
    analyst_callout(
        "Analytical Summary",
        "Highest leverage emerges where African production concentration intersects low substitutability and constrained buyer alternatives. Policy relevance depends on whether processing capacity can be captured without destabilizing trade channels.",
        "note",
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Commodities", len(COMMODITIES))
    with k2: st.metric("Countries",   len(COUNTRIES))
    with k3: st.metric("Policies",    len(POLICIES))
    with k4: st.metric("Risk Dims",   6)
    st.divider()

    # ── Commodity table ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Exposure Profile</div>', unsafe_allow_html=True)
    rows = []
    for nm, cd in COMMODITIES.items():
        rows.append({
            "Commodity": nm, "Category": cd["cat"],
            "Global Production": f"{cd['prod_mt']:,.0f} {cd['unit']}" if cd["prod_mt"] else "—",
            "African Share %": cd["af_share"],
            "Substitutability": cd["sub"][0],
            "Buyer HHI": cd["hhi"],
            "China Proc %": cd["proc"][0],
            "Africa Proc %": cd["proc"][1],
        })
    tdf = pd.DataFrame(rows)
    st.dataframe(
        tdf,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Category": st.column_config.TextColumn(width="medium"),
            "Global Production": st.column_config.TextColumn(width="medium"),
        },
    )
    source_note("Sources: USGS MCS 2025 · UN Comtrade 2023 · ICCO 2024 · ICO 2024 · WNA 2024")

    st.divider()
    st.markdown('<div class="section-header">Key Evidence</div>', unsafe_allow_html=True)
    st.caption("Africa produces critical raw materials but captures minimal "
               "processing value. China dominates midstream across nearly "
               "all commodities.")
    st.plotly_chart(fig_processing(COMMODITIES), use_container_width=True)

    st.divider()
    st.markdown('<div class="section-header">Scenario Comparison</div>', unsafe_allow_html=True)
    all_lev = {nm: compute_leverage(cd) for nm, cd in COMMODITIES.items()}
    st.plotly_chart(fig_heatmap(all_lev), use_container_width=True)

    st.divider()
    st.markdown('<div class="section-header">Decision Support Context</div>', unsafe_allow_html=True)
    # Quick country table
    crows = []
    for cn, cd in COUNTRIES.items():
        comms_present = [cm for cm, cdata in COMMODITIES.items()
                         if cn in cdata.get("africa", {})]
        crows.append({
            "Country": cn,
            "Region": cd["region"],
            "GDP ($B)": cd["gdp_bn"],
            "Pop (M)": cd["population_mn"],
            "Rating": cd["rating"],
            "EITI": "Yes" if cd["eiti"] else "No",
            "Key Commodities": ", ".join(comms_present) if comms_present else "—",
        })
    cdf = pd.DataFrame(crows)
    st.dataframe(cdf, use_container_width=True, hide_index=True)
    source_note("Sources: World Bank 2023 · IMF REO SSA 2024 · Fitch / S&P ratings · EITI Secretariat")

    st.divider()
    st.markdown('<div class="section-header">Policy Implications</div>', unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown("##### China")
        st.markdown(
            "- Controls ~40-75 % of processing for most critical minerals\n"
            "- Largest buyer of African raw materials\n"
            "- Willing to weaponise mineral dominance "
            "(gallium / germanium 2023)\n"
            "- 77 % of Namibia's uranium exports (CGN)\n"
            "- Dominates DRC/Zambia copper and cobalt\n")
        source_note("CFR 2026 · Africa Center for Strategic Studies")
    with g2:
        st.markdown("##### European Union")
        st.markdown(
            "- Critical Raw Materials Act (2024) anchors diversification\n"
            "- CBAM affects processed exports\n"
            "- CSDDD creates supply-chain liability\n"
            "- EUDR impacts cocoa and coffee trade\n"
            "- #1 buyer of African coffee (60 %)\n"
            "- Lobito Corridor (EU Global Gateway)\n")
        source_note("SWP Berlin 2025 · EU CRMA 2024")
    with g3:
        st.markdown("##### African States")
        st.markdown(
            "- Hold ~30 % of global critical-mineral reserves (IMF)\n"
            "- Growing strategic confidence and industrial ambitions\n"
            "- Key challenge: moving up the value chain\n"
            "- Lobito Corridor expanding logistics\n"
            "- Ethiopia + Uganda = 80 % of African coffee exports\n"
            "- Niger coup (2023) reset uranium geopolitics\n")
        source_note("IMF REO SSA Apr 2024 · African Business Nov 2025")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  SECTION 10 — PAGE: LEVERAGE ANALYSIS                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "Leverage Analysis":
    cdata = COMMODITIES[sel_comm]
    lv    = compute_leverage(cdata, sel_country)
    level, lclr, interp_text, rec_text = interpret_leverage(lv["composite"])

    page_header(
        f"Leverage Analysis: {sel_comm}",
        "Briefing view of structural exposure, leverage decomposition, and decision rationale for the selected commodity.",
    )
    if sel_country:
        st.caption(f"Country focus: {sel_country}")

    # Show unit note for non-standard commodities
    if cdata["unit"] == "60 kg bags":
        st.markdown(
            '<div class="box-note"><b>Coffee note:</b> Production expressed '
            'in 60 kg bags (ICO standard). 1 bag = 60 kg. Global production '
            '~175 million bags/year.</div>', unsafe_allow_html=True)
    elif cdata["unit"] == "metric tons U":
        st.markdown(
            '<div class="box-note"><b>Uranium note:</b> Production in metric '
            'tons of uranium (tU). Price benchmark in USD/lb U3O8 (yellowcake). '
            '1 tU = ~2.597 lb U3O8.</div>', unsafe_allow_html=True)
    elif cdata["unit"] == "metric tons" and sel_comm == "Gold":
        st.markdown(
            '<div class="box-note"><b>Gold note:</b> Production in metric tons. '
            'Price in USD/troy oz. 1 metric ton = 32,150 troy oz.</div>',
            unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns([1.3, 1, 1.2, 1.2])
    with m1: metric_card("Composite Leverage", f"{lv['composite']}/100",
                         border_color=lclr)
    with m2: metric_card("Level", level, border_color=lclr)
    with m3: metric_card("African Prod. Share", f"{lv['af_share']:.1f} %")
    with m4:
        if sel_country:
            metric_card(f"{sel_country} Share", f"{lv['c_share']:.1f} %")
        else:
            metric_card("Buyer HHI", f"{cdata['hhi']:.2f}")

    analyst_callout(
        f"Decision Rationale — {level} leverage",
        f"{interp_text}<br><br><b>Intervention logic:</b> {rec_text}",
        "info" if level in ("High", "Moderate") else "warn",
    )
    st.divider()

    tab_r, tab_t, tab_g, tab_p = st.tabs([
        "Exposure Profile", "Trade Flow Evidence", "Key Drivers", "Commodity Profile"])

    with tab_r:
        cr, cd_col = st.columns([3, 2])
        with cr:
            st.plotly_chart(fig_radar(lv, sel_comm, sel_country),
                            use_container_width=True)
        with cd_col:
            st.markdown("#### Driver Summary")
            for d in LEVER_DIMS:
                st.markdown(f"**{d}**: {lv['dims'][d]:.1f}/100")
                st.progress(lv["dims"][d] / 100)
            st.divider()
            st.markdown("#### Weights")
            for d, w in LEVER_WEIGHTS.items():
                st.markdown(f"- {d}: **{w:.0%}**")

    with tab_t:
        st.markdown("#### Trade Flow")
        sf = fig_sankey(cdata, sel_comm)
        if sf:
            st.plotly_chart(sf, use_container_width=True)
        else:
            st.info("Trade-flow diagram not available (net-importer commodity).")
        bf = fig_buyers(cdata, sel_comm)
        if bf:
            st.plotly_chart(bf, use_container_width=True)

    with tab_g:
        st.markdown("#### Key Drivers")
        st.caption("Ranked by potential gain × weight.")
        gaps = gap_analysis(cdata, sel_country)
        st.plotly_chart(fig_gap(gaps), use_container_width=True)
        st.dataframe(pd.DataFrame(gaps).rename(columns={
            "dim": "Dimension", "score": "Score", "gap": "Gap",
            "w_impact": "Weighted Impact", "feasibility": "Feasibility"}),
            use_container_width=True, hide_index=True,
            column_config={
                "Dimension": st.column_config.TextColumn(width="large"),
                "Feasibility": st.column_config.TextColumn(width="medium"),
            })

    with tab_p:
        st.markdown(f"#### {sel_comm} — Full Profile")
        p1, p2 = st.columns(2)
        with p1:
            st.markdown("##### Production & Reserves")
            prod = cdata["prod_mt"]
            st.markdown(f"**Global:** {prod:,.0f} {cdata['unit']}" if prod
                        else "**Global:** N/A")
            st.markdown(f"**Use:** {cdata['use']}")
            st.markdown(f"**African Share:** {cdata['af_share']:.1f} %")
            st.markdown("##### African Producers")
            for pn, pd_item in cdata["africa"].items():
                p_val = pd_item.get("prod")
                r_val = pd_item.get("res")
                ps = f"{p_val:,.0f}" if p_val else "N/A"
                rs = f", reserves {r_val:,.0f}" if r_val else ""
                st.markdown(f"- **{pn}**: {pd_item['share']} % "
                            f"({ps} {cdata['unit']}{rs})")
            st.markdown("##### Substitutability")
            st.markdown(f"Score: **{cdata['sub'][0]:.2f}** "
                        f"(0 = irreplaceable, 1 = easily replaced)")
            st.caption(cdata["sub"][1])
        with p2:
            st.markdown("##### Processing Capacity")
            st.markdown(f"- China: **{cdata['proc'][0]} %**")
            st.markdown(f"- Africa: **{cdata['proc'][1]} %**")
            st.markdown(f"- EU: **{cdata['proc'][2]} %**")
            st.caption(cdata["proc"][3])
            st.markdown("##### Regulatory Exposure")
            r = cdata["reg"]
            st.markdown(f"- EU CRM Act Listed: {'Yes' if r[0] else 'No'}")
            st.markdown(f"- EU CBAM Relevant: {'Yes' if r[1] else 'No'}")
            st.markdown(f"- US Critical Mineral: {'Yes' if r[2] else 'No'}")
            st.markdown(f"- EU Due Diligence: {'Yes' if r[3] else 'No'}")
            st.caption(r[4])
            st.markdown("##### Financing")
            st.markdown(f"Dependency: **{cdata['fin'][0]:.2f}**")
            st.markdown(f"Chinese Investment: "
                        f"{'Yes' if cdata['fin'][2] else 'No'}")
            st.markdown(f"Investors: {', '.join(cdata['fin'][1])}")
            st.markdown("##### Price Reference")
            bm, px_, vol = cdata["price"]
            st.markdown(f"**Benchmark:** {bm}")
            st.markdown(f"**Indicative:** {px_:,} (2024 avg)")
            st.markdown(f"**Volatility:** ~{vol} % annualised")

    st.divider()
    st.markdown("#### Export")
    e1, e2 = st.columns(2)
    with e1:
        csv = make_leverage_csv(lv, sel_comm, sel_country)
        st.download_button("Export Leverage Data (CSV)", _csv_bytes(csv),
            f"aslc_leverage_{sel_comm.lower().replace(' ','_').replace('/','_')}.csv",
            "text/csv")
    with e2:
        rpt = make_report_txt(sel_comm, cdata, lv, country=sel_country)
        st.download_button("Download Briefing Report (TXT)", rpt.encode("utf-8"),
            f"aslc_report_{sel_comm.lower().replace(' ','_').replace('/','_')}.txt",
            "text/plain")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  SECTION 11 — PAGE: POLICY SIMULATOR                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "Policy Simulator":
    cdata = COMMODITIES[sel_comm]
    lv    = compute_leverage(cdata, sel_country)

    page_header(
        "Policy Simulator",
        "Compare intervention pathways, quantify second-order risk, and preserve decision traceability across scenarios.",
    )
    st.markdown(f"**Commodity:** {sel_comm}" +
                (f" | **Country:** {sel_country}" if sel_country else ""))

    tab_single, tab_compare = st.tabs(["Single Policy", "Scenario Comparison"])

    with tab_single:
        sc1, sc2 = st.columns([1, 2])
        with sc1:
            sel_pol = st.selectbox("Policy Instrument", list(POLICIES.keys()))
            pol = POLICIES[sel_pol]
            st.markdown(f"**{pol['desc']}**")
            st.markdown("#### Parameters")
            params = {}
            for pk, (lo, hi, df, lb) in pol["params"].items():
                params[pk] = st.slider(lb, lo, hi, df, key=f"sp_{pk}")
            with st.expander("Policy Precedents"):
                for p in pol["precedents"]:
                    st.markdown(f"- {p}")
            analyst_callout("Legal exposure note", pol["wto"], "warn")

        with sc2:
            res = simulate_policy(cdata, lv, pol["id"], params)
            rm1, rm2, rm3 = st.columns(3)
            with rm1: metric_card("Before", f"{res['orig_comp']}/100")
            with rm2: metric_card("After", f"{res['new_comp']}/100",
                                  delta=res["delta"])
            avg_r = np.mean([v[0] for v in res["second"].values()])
            with rm3: metric_card("Avg Risk", f"{avg_r:.0f}/100")

            st.plotly_chart(
                fig_policy_radar(res["orig_dims"], res["mod_dims"], sel_pol),
                use_container_width=True)

            st.markdown("#### First-Order Effects")
            for k, v in res["first"].items():
                st.markdown(f"**{k}:** {v}")
            st.divider()

            st.markdown("#### Second-Order Risks")
            st.plotly_chart(fig_risk_bars(res["second"]),
                            use_container_width=True)
            for rn, (rs, rl) in res["second"].items():
                with st.expander(f"{rn}: {rs}/100"):
                    st.markdown(f"Risk level: **{rl}** ({rs}/100)")

            st.divider()
            pcsv = make_policy_csv(res, sel_comm, sel_pol)
            st.download_button("Export Policy Scenario Data (CSV)", _csv_bytes(pcsv),
                f"aslc_policy_{pol['id']}.csv", "text/csv",
                key="dl_single_pol")

    with tab_compare:
        st.markdown("#### Scenario Comparison")
        st.caption("Configure up to 4 scenarios side by side.")
        n_sc = st.number_input("Scenarios", 2, 4, 3, key="n_sc")
        scenarios = []
        config_panel = st.container()
        with config_panel:
            cols_sc = st.columns(int(n_sc))
            for i, col in enumerate(cols_sc):
                with col:
                    st.markdown(f"**Scenario {i+1}**")
                    sp = st.selectbox("Policy", list(POLICIES.keys()),
                        key=f"sc_pol_{i}",
                        index=min(i, len(POLICIES) - 1))
                    spol = POLICIES[sp]
                    sprm = {}
                    for pk, (lo, hi, df, lb) in spol["params"].items():
                        sprm[pk] = st.slider(lb, lo, hi, df,
                                             key=f"sc_{i}_{pk}")
                    sr = simulate_policy(cdata, lv, spol["id"], sprm)
                    ar = np.mean([v[0] for v in sr["second"].values()])
                    scenarios.append(dict(name=sp[:22], orig=sr["orig_comp"],
                        new=sr["new_comp"], risk=ar))
        st.divider()
        if scenarios:
            st.plotly_chart(fig_scenario_compare(scenarios),
                            use_container_width=True)
            comp_rows = []
            for s in scenarios:
                comp_rows.append({
                    "Scenario": s["name"],
                    "Before": s["orig"], "After": s["new"],
                    "Δ": f"{s['new']-s['orig']:+.1f}",
                    "Avg Risk": f"{s['risk']:.0f}",
                    "Net": f"{(s['new']-s['orig']) - s['risk']*0.3:.1f}",
                })
            st.dataframe(pd.DataFrame(comp_rows),
                         use_container_width=True, hide_index=True,
                         column_config={
                             "Scenario": st.column_config.TextColumn(width="medium"),
                             "Avg Risk": st.column_config.TextColumn(width="small"),
                         })


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                SECTION 12 — PAGE: COMPARATIVE DASHBOARD                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "Comparative Dashboard":
    page_header(
        "Comparative Dashboard",
        "Cross-commodity comparison of leverage structure, exposure concentration, and scenario implication.",
    )

    sel_comms = st.multiselect("Select Commodities",
        list(COMMODITIES.keys()),
        default=list(COMMODITIES.keys())[:5])

    if not sel_comms:
        st.warning("Select at least one commodity.")
    else:
        comp = {nm: compute_leverage(COMMODITIES[nm]) for nm in sel_comms}

        st.markdown("### Composite Leverage Scores")
        rc1, rc2 = st.columns([2, 1])
        with rc1:
            st.plotly_chart(fig_radar_compare(comp),
                            use_container_width=True)
        with rc2:
            st.markdown("#### Rankings")
            ranked = sorted(comp.items(), key=lambda x: x[1]["composite"],
                            reverse=True)
            for rank, (nm, lv) in enumerate(ranked, 1):
                lvl = interpret_leverage(lv["composite"])[0]
                st.markdown(
                    f"**{rank}. {nm}** — {lv['composite']}/100 "
                    f"{_risk_badge_html(lvl)}",
                    unsafe_allow_html=True)

        st.divider()
        st.markdown("### Dimension Heatmap")
        st.plotly_chart(fig_heatmap(comp), use_container_width=True)

        st.divider()
        st.markdown("### Processing Comparison")
        comp_data = {nm: COMMODITIES[nm] for nm in sel_comms}
        st.plotly_chart(fig_processing(comp_data), use_container_width=True)

        st.divider()
        st.markdown("### Trade Flows (first 3 selected)")
        tcols = st.columns(min(len(sel_comms), 3))
        for i, nm in enumerate(sel_comms[:3]):
            with tcols[i % 3]:
                sf = fig_sankey(COMMODITIES[nm], nm)
                if sf:
                    st.plotly_chart(sf, use_container_width=True)

        st.divider()
        export_rows = []
        for nm, lv in comp.items():
            row = {"Commodity": nm, "Composite": lv["composite"]}
            row.update(lv["dims"])
            export_rows.append(row)
        st.download_button("Export Comparative Results (CSV)",
            _csv_bytes(pd.DataFrame(export_rows)),
            "aslc_comparison.csv", "text/csv")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                 SECTION 13 — PAGE: COUNTRY EXPLORER (NEW)                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "Country Explorer":
    page_header(
        "Country Explorer",
        "Country-level structural exposure, production footprint, and leverage relevance across strategic commodities.",
    )

    _countries_list = list(COUNTRIES.keys())
    _sidebar_c = st.session_state.get("g_cntry", "All Producers")
    _def_idx = _countries_list.index(_sidebar_c) if _sidebar_c in _countries_list else 0
    sel_c = st.selectbox("Select Country", _countries_list, index=_def_idx, key="exp_cntry")
    cinfo = COUNTRIES[sel_c]

    # Country summary cards
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1: metric_card("GDP", f"${cinfo['gdp_bn']:.0f}B")
    with cc2: metric_card("Population", f"{cinfo['population_mn']:.0f}M")
    with cc3: metric_card("Sovereign Rating", cinfo["rating"])
    with cc4: metric_card("EITI Member", "Yes" if cinfo["eiti"] else "No",
                           border_color=C["teal"] if cinfo["eiti"] else C["rust"])

    st.divider()
    ci1, ci2 = st.columns(2)
    with ci1:
        st.markdown("##### Infrastructure & Corridors")
        st.markdown(f"**Region:** {cinfo['region']}")
        st.markdown(f"**Ports / Exit:** {', '.join(cinfo['ports'])}")
        st.markdown(f"**Corridor:** {cinfo['corridor']}")
    with ci2:
        st.markdown("##### Investment Treaties (BITs)")
        st.markdown(", ".join(cinfo["bits"]))
        st.caption("Source: UNCTAD BIT database / ICSID")

    st.divider()
    st.markdown("### Commodity Footprint")

    # Find all commodities where this country is a producer
    country_comms = {}
    for cname, cd in COMMODITIES.items():
        entry = cd.get("africa", {}).get(sel_c, None)
        if entry and entry.get("share", 0) > 0:
            lv = compute_leverage(cd, sel_c)
            country_comms[cname] = {
                "share": entry["share"],
                "prod": entry.get("prod"),
                "res": entry.get("res"),
                "unit": cd["unit"],
                "composite_leverage": lv["composite"],
                "leverage_level": interpret_leverage(lv["composite"])[0],
            }

    if not country_comms:
        st.info(f"{sel_c} does not appear as a significant producer in the "
                "current commodity database. This may reflect data gaps "
                "for early-stage or artisanal production.")
    else:
        ccf = fig_country_profile(sel_c)
        if ccf:
            st.plotly_chart(ccf, use_container_width=True)

        # Table of commodity leverage
        crows_t = []
        for cname, cinfo_c in country_comms.items():
            p_val = cinfo_c["prod"]
            r_val = cinfo_c["res"]
            ps = f"{p_val:,.0f}" if p_val else "N/A"
            rs = f"{r_val:,.0f}" if r_val else "N/A"
            crows_t.append({
                "Commodity": cname,
                "Global Share (%)": cinfo_c["share"],
                f"Production ({cinfo_c['unit']})": ps,
                "Reserves": rs,
                "Composite Leverage": cinfo_c["composite_leverage"],
                "Level": cinfo_c["leverage_level"],
            })
        st.dataframe(
            pd.DataFrame(crows_t),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Level": st.column_config.TextColumn(width="medium"),
                "Commodity": st.column_config.TextColumn(width="medium"),
            },
        )

        st.divider()
        st.markdown("### Per-Commodity Leverage Deep Dive")
        sel_cc = st.selectbox("Commodity", list(country_comms.keys()),
                              key="exp_comm")
        if sel_cc:
            cdata_cc = COMMODITIES[sel_cc]
            lv_cc = compute_leverage(cdata_cc, sel_c)
            lvl_cc, lclr_cc, interp_cc, rec_cc = interpret_leverage(
                lv_cc["composite"])

            ea, eb = st.columns(2)
            with ea:
                metric_card("Composite Leverage",
                            f"{lv_cc['composite']}/100",
                            border_color=lclr_cc)
                metric_card("Level", lvl_cc, border_color=lclr_cc)
            with eb:
                metric_card(f"{sel_c} Share",
                            f"{lv_cc['c_share']:.1f} % of global")
                metric_card("African Total", f"{lv_cc['af_share']:.1f} %")

            st.markdown(
                f'<div class="box-info"><b>{lvl_cc} Leverage:</b> '
                f'{interp_cc}<br><br><b>Recommendation:</b> {rec_cc}'
                f'</div>', unsafe_allow_html=True)

            st.plotly_chart(fig_radar(lv_cc, sel_cc, sel_c),
                            use_container_width=True)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                 SECTION 14 — PAGE: ASSUMPTIONS                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "Assumptions":
    page_header(
        "Assumption Register",
        "Transparency layer documenting confidence qualifiers, data proxies, and structural modelling constraints.",
    )
    analyst_callout(
        "Analytical annotation",
        "Presenting scenarios as forecasts weakens interpretability. This register keeps each assumption explicit and stress-testable.",
        "info",
    )

    adf = pd.DataFrame(ASSUMPTIONS,
        columns=["ID", "Category", "Assumption", "Impact", "Source"])
    cats = ["All"] + sorted(adf["Category"].unique().tolist())
    filt = st.selectbox("Filter by Category", cats)
    display = adf if filt == "All" else adf[adf["Category"] == filt]

    for _, r in display.iterrows():
        with st.expander(f"**{r['ID']}** — {r['Category']}"):
            st.markdown(f"**Assumption:** {r['Assumption']}")
            st.markdown(f"**Impact:** {r['Impact']}")
            st.markdown(f"**Source:** {r['Source']}")
    st.divider()
    st.download_button("Export Assumption Register (CSV)", _csv_bytes(adf),
                       "aslc_assumptions.csv", "text/csv")

    st.divider()
    st.markdown("### Data Sources")
    for name, desc, url in [
        ("USGS MCS 2025", "Production, reserves, trade",
         "https://pubs.usgs.gov/publication/mcs2025"),
        ("UN Comtrade / WITS", "Bilateral trade flows",
         "https://wits.worldbank.org/"),
        ("IMF REO SSA", "Macro context, mineral reserves",
         "https://www.imf.org/en/Publications/REO/SSA"),
        ("EU CRMA 2024", "Strategic raw-materials classification",
         "https://single-market-economy.ec.europa.eu/sectors/raw-materials"),
        ("EITI", "Extractive-industry transparency",
         "https://eiti.org/"),
        ("ICSID Case Database", "ISDS precedents",
         "https://icsid.worldbank.org/cases/case-database"),
        ("ICCO / COCOBOD", "Cocoa production & pricing",
         "https://www.icco.org/"),
        ("ICO Statistical Report 2024-25", "Coffee production & trade",
         "https://www.ico.org/new_historical.asp"),
        ("WNA / IAEA Red Book 2024", "Uranium production & reserves",
         "https://www.world-nuclear.org/information-library"),
        ("UNCTAD Maritime Transport", "Shipping / chokepoints",
         "https://unctad.org/topic/transport-and-trade-logistics"),
        ("World Bank Open Data", "Country GDP, population",
         "https://data.worldbank.org/"),
        ("Ghana Minerals Commission", "Gold production data",
         "https://www.mincom.gov.gh/"),
        ("Cobalt Institute", "DRC cobalt / copper data",
         "https://www.cobaltinstitute.org/"),
    ]:
        st.markdown(f"- **[{name}]({url})**: {desc}")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECTION 15 — PAGE: ABOUT                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "About":
    page_header(
        "About & Methodology",
        "Methodological framing, leverage construction logic, and known scope limitations for briefing use.",
    )
    st.markdown("""
### What ASLC Does

The African Strategic Leverage & Commodity Control Lab is a **scenario analysis tool** that models how much leverage African states hold in
critical commodity supply chains, and what policy packages convert resource
endowments into credible bargaining power without self-harm.

### Leverage Vector (7 Dimensions)

| Dimension | Measures | Higher = |
|-----------|---------|----------|
| **Buyer Diversification** | How concentrated are buyers? | More diverse buyers → more leverage |
| **Substitutability Barrier** | Can buyers switch? | Harder to substitute → more leverage |
| **Stockpiling Difficulty** | Can buyers build reserves? | Harder to stockpile → more urgency |
| **Chokepoint Control** | Geography creates bottlenecks? | More sensitivity → more leverage |
| **Processing Capacity** | Does Africa process or just export? | More processing → more leverage |
| **Financial Independence** | How dependent on foreign capital? | Less dependent → more freedom |
| **Regulatory Leverage** | Does EU/US regulation create openings? | More attention → opportunity |

### Policy Simulator

Seven instruments with configurable parameters, each producing first-order
effects and six second-order risk dimensions (capital flight, smuggling,
retaliation, ISDS, demand destruction, diplomatic friction).

### Calibration

Calibrated against historical precedents:
- Indonesia nickel ore export ban (2020)
- Zimbabwe raw lithium export ban (2022)
- China rare-earth restrictions (2010) and Ga/Ge controls (2023)
- Ghana / Côte d'Ivoire Living Income Differential for cocoa
- Tanzania Mining Act 2017 and investor disputes
- Niger coup (2023) → uranium supply disruption
- Mali new Mining Code (2023) → Barrick Gold dispute
- DRC 2018 Mining Code royalty restructuring

### Framing

This tool is framed around **resilience, bargaining realism, and policy
risk trade-offs**.

### Limitations

1. Processing-capacity data is approximated (see Assumption A002)
2. Contract terms are often confidential (A005)
3. Political dynamics not modelled quantitatively
4. Price elasticities simplified
5. Coalition dynamics modelled simply
6. Artisanal / informal mining significantly undercounts production (A011)
7. Post-coup Niger production data is uncertain (A014)

### Stack

- **UI:** Streamlit 1.44.1 · **Charts:** Plotly 6.0.1 · **Data:** Pandas 2.2.3 / NumPy 2.2.4
- **All data embedded** — no external API calls required
    """)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          FOOTER                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

st.markdown(
    '<div class="footer">African Strategic Leverage & Commodity Control Lab (ASLC) v3.0 · '
    '20 Countries · 11 Commodities · '
    'Geoeconomic scenario tool · '
    'Data: USGS · UN Comtrade · IMF · EU CRMA · ICO · WNA · '
    'Not a forecasting engine — see Assumptions</div>',
    unsafe_allow_html=True)
