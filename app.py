"""
Critical Commodities Leverage Lab (CCLL)
A Geoeconomic Bargaining Simulator for Africa–EU–China Supply Chains

Single-file Streamlit application. All data, models, visualizations, and UI
in one self-contained file. Works offline once loaded — no external API calls
required for core functionality.

Data sources (cited inline):
    - USGS Mineral Commodity Summaries 2025 (production, reserves, trade)
    - UN Comtrade / WITS World Bank (bilateral trade flows, buyer shares)
    - IMF Regional Economic Outlook: Sub-Saharan Africa Apr 2024
    - EU Critical Raw Materials Act 2024 (regulatory classification)
    - ICCO / Ghana COCOBOD (cocoa production & pricing)
    - ICSID Case Database (ISDS precedent data)
    - UNCTAD Review of Maritime Transport 2024 (shipping / chokepoints)
    - Company annual reports, EITI reports (financing, ownership)

Author: Generated with Perplexity Computer
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
    page_title="CCLL — Critical Commodities Leverage Lab",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Brand palette ─────────────────────────────────────────────────────────────
C = {
    "teal":       "#20808D",  # primary accent
    "rust":       "#A84B2F",  # secondary / China highlight
    "dark_teal":  "#1B474D",
    "cyan_light": "#BCE2E7",
    "mauve":      "#944454",
    "gold":       "#FFC553",
    "olive":      "#848456",
    "brown":      "#6E522B",
    "bg":         "#FCFAF6",  # off-white background
    "card":       "#F3F3EE",  # card / sidebar background
    "text":       "#13343B",  # body text
    "muted":      "#2E565D",  # secondary text
    "offblack":   "#091717",
}

CHART_SEQ = [C["teal"], C["rust"], C["dark_teal"], C["cyan_light"],
             C["mauve"], C["gold"], C["olive"], C["brown"]]

RISK_CLR = {"Critical": "#B71C1C", "High": "#E65100",
            "Moderate": "#F57F17", "Low": "#2E7D32", "Minimal": "#1B5E20"}

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, -apple-system, sans-serif", color=C["text"]),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=40, t=50, b=40),
)

# ── Inject custom CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="st-"] { font-family: 'Inter', -apple-system, sans-serif; }

/* ── metric cards ── */
.m-card {
    background: #F3F3EE; border-radius: 10px; padding: 1.1rem 1.2rem;
    border-left: 4px solid #20808D; margin-bottom: .7rem;
}
.m-card .val {
    font-size: 1.85rem; font-weight: 700; color: #13343B; line-height: 1.15;
}
.m-card .lbl {
    font-size: .78rem; color: #2E565D; text-transform: uppercase;
    letter-spacing: .06em; font-weight: 600; margin-bottom: 2px;
}
.m-card .delta-pos { color: #2E7D32; font-size: .95rem; margin-left: .4rem; }
.m-card .delta-neg { color: #B71C1C; font-size: .95rem; margin-left: .4rem; }

/* ── callout boxes ── */
.box-info {
    background: #E8F5E9; border-radius: 8px; padding: 1rem;
    border-left: 4px solid #2E7D32; margin: .6rem 0; font-size: .93rem;
}
.box-warn {
    background: #FFF3E0; border-radius: 8px; padding: 1rem;
    border-left: 4px solid #E65100; margin: .6rem 0; font-size: .93rem;
}
.box-note {
    background: #F3F3EE; border-radius: 8px; padding: .85rem;
    border-left: 4px solid #FFC553; margin: .6rem 0; font-size: .9rem;
}

/* ── risk badges ── */
.rbadge {
    display: inline-block; padding: .12rem .55rem; border-radius: 4px;
    font-size: .8rem; font-weight: 600; color: #fff;
}
.rbadge-critical { background: #B71C1C; }
.rbadge-high     { background: #E65100; }
.rbadge-moderate { background: #F57F17; color: #13343B; }
.rbadge-low      { background: #2E7D32; }
.rbadge-minimal  { background: #1B5E20; }

/* ── source footnote ── */
.src { font-size: .78rem; color: #2E565D; margin-top: .3rem; }

/* sidebar tweak */
section[data-testid="stSidebar"] { background-color: #F3F3EE; }

/* footer */
.footer {
    text-align: center; color: #2E565D; font-size: .78rem;
    margin-top: 2.5rem; padding: 1rem 0; border-top: 1px solid #E5E3D4;
}
</style>
""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECTION 2 — EMBEDDED DATA LAYER                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
# Every number is cited to a public source.  Where exact figures are not public,
# a proxy is used and flagged in the ASSUMPTION_REGISTER at the bottom.

COUNTRIES = {
    "Ghana": {
        "region": "West Africa", "gdp_bn": 75.5,                       # World Bank 2023
        "population_mn": 33.5, "rating": "B- (S&P)",
        "ports": ["Tema", "Takoradi"], "corridor": "Gulf of Guinea",
        "eiti": True,
        "bits": ["UK", "Netherlands", "Germany", "China", "South Africa", "Switzerland"],
    },
    "South Africa": {
        "region": "Southern Africa", "gdp_bn": 377.0,
        "population_mn": 60.4, "rating": "BB- (S&P)",
        "ports": ["Durban", "Richards Bay", "Cape Town", "Saldanha"],
        "corridor": "Cape of Good Hope", "eiti": False,
        "bits": ["UK", "Netherlands", "Germany", "China", "USA", "France", "Belgium"],
    },
    "DRC": {
        "region": "Central Africa", "gdp_bn": 65.2,
        "population_mn": 102.3, "rating": "B- (Fitch)",
        "ports": ["Matadi", "Boma"],
        "corridor": "Lobito Corridor / Dar es Salaam", "eiti": True,
        "bits": ["Belgium", "France", "Germany", "China", "South Korea", "USA"],
    },
    "Guinea": {
        "region": "West Africa", "gdp_bn": 21.0,
        "population_mn": 14.2, "rating": "Not rated",
        "ports": ["Conakry", "Kamsar"], "corridor": "Gulf of Guinea",
        "eiti": True, "bits": ["France", "China", "USA", "Germany"],
    },
    "Gabon": {
        "region": "Central Africa", "gdp_bn": 21.1,
        "population_mn": 2.4, "rating": "B+ (Fitch)",
        "ports": ["Owendo", "Port-Gentil"], "corridor": "Gulf of Guinea",
        "eiti": True, "bits": ["France", "China", "Belgium", "Germany"],
    },
    "Zimbabwe": {
        "region": "Southern Africa", "gdp_bn": 24.8,
        "population_mn": 16.7, "rating": "Not rated",
        "ports": ["Landlocked → Beira (MZ), Durban (SA)"],
        "corridor": "Beira Corridor / North-South", "eiti": False,
        "bits": ["China", "South Africa", "UK", "Germany", "Netherlands"],
    },
    "Zambia": {
        "region": "Southern Africa", "gdp_bn": 29.8,
        "population_mn": 20.6, "rating": "B- (Fitch)",
        "ports": ["Landlocked → Dar es Salaam, Durban, Lobito"],
        "corridor": "Lobito Corridor / Dar es Salaam", "eiti": True,
        "bits": ["China", "UK", "Netherlands", "South Africa", "USA"],
    },
    "Côte d'Ivoire": {
        "region": "West Africa", "gdp_bn": 78.8,
        "population_mn": 28.9, "rating": "BB- (S&P)",
        "ports": ["Abidjan", "San-Pédro"], "corridor": "Gulf of Guinea",
        "eiti": True,
        "bits": ["France", "Netherlands", "UK", "China", "Germany"],
    },
}

# ── Commodity database ────────────────────────────────────────────────────────
# Structure per commodity:
#   cat          — category label
#   use          — strategic end-uses
#   prod_mt      — global production (metric tons)
#   unit         — unit label
#   africa       — dict of African producers with share_pct, prod_mt, reserves_mt
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
            "Gabon":        dict(share=14.0, prod=3_220_000,
                                 res=69_000_000),
            "Ghana":        dict(share=4.5,  prod=1_035_000,
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
    "Bauxite / Alumina": dict(
        cat="Critical Mineral",
        use="Aluminium production (primary), refractories, abrasives, chemicals",
        prod_mt=400_000_000, unit="metric tons",               # USGS MCS 2025
        africa={
            "Guinea": dict(share=23.0, prod=92_000_000,
                           res=7_400_000_000),                 # USGS MCS 2025
            "Ghana":  dict(share=1.5,  prod=6_000_000,
                           res=900_000_000),
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
            "DRC":    dict(share=73.0, prod=167_900,
                           res=4_000_000),
            "Zambia": dict(share=1.5,  prod=3_450,
                           res=270_000),
        },
        af_share=74.5,
        buyers={"China": .78, "EU-27": .08, "Japan": .04,
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
                             res=3_000_000),
        },
        af_share=5.0,
        buyers={"China": .70, "South Korea": .10, "Japan": .08,
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
            "Côte d'Ivoire": dict(share=38.0, prod=1_824_000,
                                   res=None),                  # ICCO 2024
            "Ghana":          dict(share=15.0, prod=720_000,
                                   res=None),                  # COCOBOD
        },
        af_share=60.0,
        buyers={"EU-27": .45, "USA": .15, "Malaysia": .08,
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

    # ── REFINED PETROLEUM (dependency commodity) ──────────────────────────────
    "Refined Petroleum": dict(
        cat="Energy Dependency",
        use="Transport fuel, industrial energy, power generation, petrochemicals",
        prod_mt=4_400_000_000, unit="bbl/day equiv.",
        africa={
            "Ghana": dict(share=0.2, prod=None, res=None),
            # Ghana produces ~150 k bbl/day crude but imports ~70 % of
            # refined fuel needs.  EIA / Ghana Petroleum Commission.
        },
        af_share=0.2,
        buyers={},  # N/A — Ghana is a NET IMPORTER
        hhi=0.0,
        _dependency=True,  # flag: this models vulnerability, not leverage
        _import_detail={
            "refined_import_pct": 70,                          # EIA / GPC
            "crude_prod_bbl_day": 150_000,
            "refinery_cap_bbl_day": 45_000,                    # Tema Oil Ref
            "suppliers": {"Europe": .35, "India": .25,
                          "China": .15, "Others": .25},
        },
        sub=(0.25, "EVs / renewables reduce long-term demand. Short-term: "
             "no substitute for jet fuel, heavy transport, petrochem."),
        stock=(0.50, "SPRs exist (US, IEA members). Ghana has limited "
               "storage. ECOWAS has no collective reserve."),
        choke=(0.60, ["Persian Gulf → Suez → West Africa",
                      "India → Cape → West Africa",
                      "Europe → West Africa"],
               "Multiple supply routes but all seaborne. Suez disruption "
               "(Houthis 2024) showed vulnerability."),
        proc=(17, 3.5, 14, "Africa has massive refining deficit. Dangote "
              "Refinery (NG, 650 k bbl/day) transformative if fully "
              "operational. Ghana's TOR small & unreliable."),
        fin=(0.30, ["Tullow Oil (UK)", "Eni (IT)",
                    "Springfield (GH)", "GNPC (state)"],
             False, "Ghana upstream relatively diverse. GNPC has state "
             "participation. Challenge is downstream / refining."),
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
            "South Africa": dict(share=72.0, prod=137,
                                  res=63_000),
            "Zimbabwe":     dict(share=8.0,  prod=15,
                                  res=1_200),
        },
        af_share=80.0,
        buyers={"EU-27": .22, "Japan": .20, "USA": .18,
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
}

# ── Policy definitions ────────────────────────────────────────────────────────
POLICIES = {
    "Export Tax / Restriction": dict(
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
            "Angola's Lobito port.",
            "Mozambique: Nacala Corridor tied to Vale's coal operations.",
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
            "DRC / Zambia: Proposed 'battery belt' coordination on Co/Cu.",
        ],
        wto="Medium — not directly WTO-prohibited but faces antitrust "
            "scrutiny in buyer jurisdictions.",
    ),
}

# ── Assumption register ───────────────────────────────────────────────────────
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
     "Low-Medium", "UNCTAD Review of Maritime Transport"),
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
     "Low", "LME, ICE, LBMA, USGS"),
    ("A008", "Second-Order Effects",
     "Capital flight, smuggling, retaliation, ISDS risk calibrated to "
     "historical precedents (ID Ni ban, ZW Li ban, CI cocoa). "
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
    multiplier = 0.3 if is_dep else (1.0 + af_share / 200)

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
    return dict(
        **PLOTLY_LAYOUT,
        title=dict(text=title, font=dict(size=15)),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(size=9, color=C["muted"]),
                            gridcolor="rgba(46,86,93,.12)"),
            angularaxis=dict(tickfont=dict(size=10, color=C["text"]),
                             gridcolor="rgba(46,86,93,.12)"),
            bgcolor="rgba(0,0,0,0)"),
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
    fig.update_layout(**_polar_layout("Comparative Leverage", h=500))
    fig.update_layout(showlegend=True,
        legend=dict(orientation="h", y=-0.12, xanchor="center", x=0.5,
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
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f} %<extra></extra>"))
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text=f"Buyer Concentration: {name} (HHI {cdata.get('hhi',0):.2f})",
                   font=dict(size=13)),
        xaxis=dict(title="Import Share (%)",
                   range=[0, max(df["Share"])*1.3],
                   gridcolor="rgba(46,86,93,.08)"),
        yaxis=dict(title=""), height=340, showlegend=False)
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
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="Processing Capacity Gap: Africa vs China vs EU",
                   font=dict(size=13)),
        barmode="group",
        xaxis=dict(title="", tickangle=-30),
        yaxis=dict(title="Share of Global Processing (%)",
                   gridcolor="rgba(46,86,93,.08)"),
        legend=dict(orientation="h", y=1.05, xanchor="right", x=1),
        height=430)
    return fig


def fig_heatmap(results):
    comms = list(results.keys())
    z = [[results[c]["dims"][d] for d in LEVER_DIMS] for c in comms]
    fig = go.Figure(go.Heatmap(
        z=z, x=LEVER_DIMS, y=comms,
        colorscale=[[0,"#B71C1C"],[.25,"#E65100"],
                    [.5,"#F57F17"],[.75,"#2E7D32"],[1,"#1B5E20"]],
        text=[[f"{v:.0f}" for v in row] for row in z],
        texttemplate="%{text}", hovertemplate=
        "Commodity: %{y}<br>Dimension: %{x}<br>Score: %{z:.1f}<extra></extra>",
        colorbar=dict(title="Score", ticksuffix="/100")))
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="Leverage Heatmap", font=dict(size=13)),
        xaxis=dict(title="", tickangle=-35), yaxis=dict(title=""),
        height=400)
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
        link_clr.append("rgba(32,128,141,.35)")
    for j, (bn, bs) in enumerate(buyers.items()):
        src.append(c_idx); tgt.append(c_idx + 1 + j)
        vals.append(bs * 100)
        if bn == "China":
            link_clr.append("rgba(168,75,47,.45)")
        elif "EU" in bn:
            link_clr.append("rgba(27,71,77,.45)")
        else:
            link_clr.append("rgba(188,226,231,.45)")
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
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text=f"Trade Flow: {name} (Africa → Global)",
                   font=dict(size=13)), height=400)
    return fig


def fig_gap(gap_data):
    df = pd.DataFrame(gap_data)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["score"], y=df["dim"], orientation="h",
        name="Current", marker=dict(color=C["teal"])))
    fig.add_trace(go.Bar(x=df["gap"], y=df["dim"], orientation="h",
        name="Gap to 100", marker=dict(color="rgba(168,75,47,.25)"),
        text=[f"Δ{w:.0f}" for w in df["w_impact"]], textposition="outside"))
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="Leverage Gap Analysis (by weighted impact)",
                   font=dict(size=13)),
        barmode="stack",
        xaxis=dict(title="Score 0-100", range=[0, 115],
                   gridcolor="rgba(46,86,93,.08)"),
        yaxis=dict(title=""),
        legend=dict(orientation="h", y=1.05, xanchor="right", x=1),
        height=380)
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
        legend=dict(orientation="h", y=-0.1, xanchor="center", x=0.5,
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
        text=[str(s) for s in scores], textposition="outside",
        hovertemplate="%{y}: %{x}/100<extra></extra>"))
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="Second-Order Risk Assessment", font=dict(size=13)),
        xaxis=dict(title="Risk Score 0-100", range=[0, 110],
                   gridcolor="rgba(46,86,93,.08)"),
        yaxis=dict(title=""), height=370, showlegend=False)
    return fig


def fig_scenario_compare(scenarios):
    names = [s["name"] for s in scenarios]
    orig  = [s["orig"] for s in scenarios]
    newc  = [s["new"]  for s in scenarios]
    risk  = [s["risk"] for s in scenarios]
    fig = make_subplots(rows=1, cols=2,
        subplot_titles=("Leverage Score Change", "Avg Risk Score"),
        horizontal_spacing=.15)
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
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="Scenario Comparison", font=dict(size=13)),
        barmode="group", height=400,
        legend=dict(orientation="h", y=-0.12, xanchor="center", x=.25))
    fig.update_yaxes(title_text="Composite Score",
                     gridcolor="rgba(46,86,93,.08)", row=1, col=1)
    fig.update_yaxes(title_text="Risk 0-100",
                     gridcolor="rgba(46,86,93,.08)", row=1, col=2)
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
    L.append("CRITICAL COMMODITIES LEVERAGE LAB (CCLL)")
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
                "ICCO / COCOBOD", "UNCTAD Maritime Transport 2024"]:
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


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                       SECTION 8 — SIDEBAR & NAV                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

with st.sidebar:
    st.markdown("### ⚖️ CCLL")
    st.markdown("**Critical Commodities Leverage Lab**")
    st.caption("Geoeconomic Bargaining Simulator")
    st.divider()

    page = st.radio("Navigate", [
        "🏠 Overview",
        "🔍 Leverage Analysis",
        "🎯 Policy Simulator",
        "📊 Comparative Dashboard",
        "📋 Assumptions",
        "ℹ️ About",
    ], label_visibility="collapsed")

    st.divider()
    st.markdown("#### Commodity")
    sel_comm = st.selectbox("Select", list(COMMODITIES.keys()),
                            key="g_comm", label_visibility="collapsed")
    avail_c = list(COMMODITIES[sel_comm].get("africa", {}).keys())
    if avail_c:
        sel_country = st.selectbox("Focus Country",
                                   ["All Producers"] + avail_c,
                                   key="g_cntry")
        sel_country = None if sel_country == "All Producers" else sel_country
    else:
        sel_country = None
        st.caption("No African producers in database.")

    st.divider()
    st.markdown(
        '<div class="box-note"><b>⚠️ Scenario Tool</b><br>'
        'Not a forecast. All outputs are scenario-based with explicit '
        'assumptions. See <i>Assumptions</i> page.</div>',
        unsafe_allow_html=True)
    st.divider()
    st.caption("Data: USGS MCS 2025 · UN Comtrade · IMF · EU CRMA 2024")
    st.caption("Updated: March 2026")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                     SECTION 9 — PAGE: OVERVIEW                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if page == "🏠 Overview":
    st.markdown(
        '<div style="font-size:2rem;font-weight:700;color:#13343B;'
        'letter-spacing:-.02em">Critical Commodities Leverage Lab</div>',
        unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:1rem;color:#2E565D;margin-bottom:1.2rem">'
        'A geoeconomic scenario tool modelling how much leverage African '
        'states hold in critical commodity supply chains — and what policy '
        'packages convert resource endowments into credible bargaining '
        'power without self-harm.</div>', unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Commodities", len(COMMODITIES))
    with k2: st.metric("Countries",   len(COUNTRIES))
    with k3: st.metric("Policies",    len(POLICIES))
    with k4: st.metric("Risk Dims",   6)
    st.divider()

    # ── Commodity table ───────────────────────────────────────────────────────
    st.markdown("### Commodity Overview")
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
    st.dataframe(tdf, use_container_width=True, hide_index=True)
    source_note("Sources: USGS MCS 2025 · UN Comtrade 2023 · ICCO 2024")

    st.divider()
    st.markdown("### The Processing Gap")
    st.caption("Africa produces critical raw materials but captures minimal "
               "processing value. China dominates midstream across nearly "
               "all commodities.")
    st.plotly_chart(fig_processing(COMMODITIES), use_container_width=True)

    st.divider()
    st.markdown("### Leverage Landscape")
    all_lev = {nm: compute_leverage(cd) for nm, cd in COMMODITIES.items()}
    st.plotly_chart(fig_heatmap(all_lev), use_container_width=True)

    st.divider()
    st.markdown("### Geopolitical Context: Africa – EU – China")
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown("##### 🇨🇳 China")
        st.markdown(
            "- Controls ~60-90 % of processing for most critical minerals\n"
            "- Largest buyer of African raw materials\n"
            "- Willing to weaponise mineral dominance "
            "(gallium / germanium 2023)\n")
        source_note("CFR 2026 · Africa Center for Strategic Studies")
    with g2:
        st.markdown("##### 🇪🇺 European Union")
        st.markdown(
            "- Critical Raw Materials Act (2024) anchors diversification\n"
            "- CBAM affects processed exports\n"
            "- CSDDD creates supply-chain liability\n"
            "- EUDR impacts cocoa trade\n")
        source_note("SWP Berlin 2025 · EU CRMA 2024")
    with g3:
        st.markdown("##### 🌍 African States")
        st.markdown(
            "- Hold ~30 % of global critical-mineral reserves (IMF)\n"
            "- Growing strategic confidence and industrial ambitions\n"
            "- Key challenge: moving up the value chain\n"
            "- Lobito Corridor expanding logistics\n")
        source_note("IMF REO SSA Apr 2024 · African Business Nov 2025")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  SECTION 10 — PAGE: LEVERAGE ANALYSIS                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "🔍 Leverage Analysis":
    cdata = COMMODITIES[sel_comm]
    lv    = compute_leverage(cdata, sel_country)
    level, lclr, interp_text, rec_text = interpret_leverage(lv["composite"])

    st.markdown(
        f'<div style="font-size:1.8rem;font-weight:700;color:#13343B">'
        f'Leverage Analysis: {sel_comm}</div>', unsafe_allow_html=True)
    if sel_country:
        st.caption(f"Country focus: {sel_country}")

    m1, m2, m3, m4 = st.columns(4)
    with m1: metric_card("Composite Leverage", f"{lv['composite']}/100",
                         border_color=lclr)
    with m2: metric_card("Level", level, border_color=lclr)
    with m3: metric_card("African Prod. Share", f"{lv['af_share']:.1f} %")
    with m4:
        if sel_country:
            metric_card(f"{sel_country} Share", f"{lv['c_share']:.1f} %")
        else:
            metric_card("Buyer HHI", f"{cdata['hhi']:.2f}")

    box_cls = "box-info" if level in ("High", "Moderate") else "box-warn"
    st.markdown(
        f'<div class="{box_cls}"><b>{level} Leverage:</b> {interp_text}'
        f'<br><br><b>Recommendation:</b> {rec_text}</div>',
        unsafe_allow_html=True)
    st.divider()

    tab_r, tab_t, tab_g, tab_p = st.tabs([
        "🕸️ Radar", "📦 Trade Flows", "📊 Gap Analysis", "📄 Profile"])

    with tab_r:
        cr, cd_col = st.columns([3, 2])
        with cr:
            st.plotly_chart(fig_radar(lv, sel_comm, sel_country),
                            use_container_width=True)
        with cd_col:
            st.markdown("#### Breakdown")
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
        st.markdown("#### Leverage Gap Analysis")
        st.caption("Ranked by potential gain × weight.")
        gaps = gap_analysis(cdata, sel_country)
        st.plotly_chart(fig_gap(gaps), use_container_width=True)
        st.dataframe(pd.DataFrame(gaps).rename(columns={
            "dim": "Dimension", "score": "Score", "gap": "Gap",
            "w_impact": "Weighted Impact", "feasibility": "Feasibility"}),
            use_container_width=True, hide_index=True)

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
            st.markdown(f"- EU CRM Act Listed: {'✅' if r[0] else '❌'}")
            st.markdown(f"- EU CBAM Relevant: {'✅' if r[1] else '❌'}")
            st.markdown(f"- US Critical Mineral: {'✅' if r[2] else '❌'}")
            st.markdown(f"- EU Due Diligence: {'✅' if r[3] else '❌'}")
            st.caption(r[4])
            st.markdown("##### Financing")
            st.markdown(f"Dependency: **{cdata['fin'][0]:.2f}**")
            st.markdown(f"Chinese Investment: "
                        f"{'✅' if cdata['fin'][2] else '❌'}")
            st.markdown(f"Investors: {', '.join(cdata['fin'][1])}")

    st.divider()
    st.markdown("#### Export")
    e1, e2 = st.columns(2)
    with e1:
        csv = make_leverage_csv(lv, sel_comm, sel_country)
        st.download_button("📥 Leverage CSV", _csv_bytes(csv),
            f"ccll_leverage_{sel_comm.lower().replace(' ','_').replace('/','_')}.csv",
            "text/csv")
    with e2:
        rpt = make_report_txt(sel_comm, cdata, lv, country=sel_country)
        st.download_button("📥 Full Report (TXT)", rpt.encode("utf-8"),
            f"ccll_report_{sel_comm.lower().replace(' ','_').replace('/','_')}.txt",
            "text/plain")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  SECTION 11 — PAGE: POLICY SIMULATOR                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "🎯 Policy Simulator":
    cdata = COMMODITIES[sel_comm]
    lv    = compute_leverage(cdata, sel_country)

    st.markdown(
        '<div style="font-size:1.8rem;font-weight:700;color:#13343B">'
        'Policy Move Simulator</div>', unsafe_allow_html=True)
    st.caption("Model policy interventions and assess second-order risks.")
    st.markdown(f"**Commodity:** {sel_comm}" +
                (f" | **Country:** {sel_country}" if sel_country else ""))

    tab_single, tab_compare = st.tabs(["🔧 Single Policy",
                                        "📊 Scenario Comparison"])

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
            with st.expander("📚 Precedents"):
                for p in pol["precedents"]:
                    st.markdown(f"- {p}")
            st.markdown(
                f'<div class="box-warn"><b>WTO / Legal Risk:</b> '
                f'{pol["wto"]}</div>', unsafe_allow_html=True)

        with sc2:
            res = simulate_policy(cdata, lv, pol["id"], params)
            rm1, rm2, rm3 = st.columns(3)
            with rm1: st.metric("Before", f"{res['orig_comp']}/100")
            with rm2: st.metric("After",  f"{res['new_comp']}/100",
                                delta=f"{res['delta']:+.1f}")
            avg_r = np.mean([v[0] for v in res["second"].values()])
            with rm3: st.metric("Avg Risk", f"{avg_r:.0f}/100")

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
                with st.expander(f"{_risk_badge_html(rl)} {rn}: {rs}/100"):
                    st.markdown(f"Risk level: **{rl}** ({rs}/100)")

            st.divider()
            pcsv = make_policy_csv(res, sel_comm, sel_pol)
            st.download_button("📥 Policy CSV", _csv_bytes(pcsv),
                f"ccll_policy_{pol['id']}.csv", "text/csv",
                key="dl_single_pol")

    with tab_compare:
        st.markdown("#### Multi-Scenario Comparison")
        st.caption("Configure up to 4 scenarios side by side.")
        n_sc = st.number_input("Scenarios", 2, 4, 3, key="n_sc")
        scenarios = []
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
                         use_container_width=True, hide_index=True)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                SECTION 12 — PAGE: COMPARATIVE DASHBOARD                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "📊 Comparative Dashboard":
    st.markdown(
        '<div style="font-size:1.8rem;font-weight:700;color:#13343B">'
        'Comparative Dashboard</div>', unsafe_allow_html=True)

    sel_comms = st.multiselect("Select Commodities",
        list(COMMODITIES.keys()),
        default=list(COMMODITIES.keys())[:4])

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
                    f"({_risk_badge_html(lvl)})",
                    unsafe_allow_html=True)

        st.divider()
        st.markdown("### Dimension Heatmap")
        st.plotly_chart(fig_heatmap(comp), use_container_width=True)

        st.divider()
        st.markdown("### Processing Comparison")
        comp_data = {nm: COMMODITIES[nm] for nm in sel_comms}
        st.plotly_chart(fig_processing(comp_data), use_container_width=True)

        st.divider()
        st.markdown("### Trade Flows")
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
        st.download_button("📥 Comparison CSV",
            _csv_bytes(pd.DataFrame(export_rows)),
            "ccll_comparison.csv", "text/csv")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                 SECTION 13 — PAGE: ASSUMPTIONS                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "📋 Assumptions":
    st.markdown(
        '<div style="font-size:1.8rem;font-weight:700;color:#13343B">'
        'Assumption Register</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="box-info"><b>Why this matters:</b> Presenting '
        'scenarios as forecasts invites attack. This register makes every '
        'assumption explicit and stress-testable, supporting the tool\'s '
        'framing as a <em>resilience and bargaining realism</em> '
        'platform.</div>', unsafe_allow_html=True)

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
    st.download_button("📥 Assumptions CSV", _csv_bytes(adf),
                       "ccll_assumptions.csv", "text/csv")

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
        ("UNCTAD Maritime Transport", "Shipping / chokepoints",
         "https://unctad.org/topic/transport-and-trade-logistics"),
    ]:
        st.markdown(f"- **[{name}]({url})**: {desc}")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECTION 14 — PAGE: ABOUT                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

elif page == "ℹ️ About":
    st.markdown(
        '<div style="font-size:1.8rem;font-weight:700;color:#13343B">'
        'About & Methodology</div>', unsafe_allow_html=True)
    st.markdown("""
### What CCLL Does

The Critical Commodities Leverage Lab is a **scenario analysis tool** — not a
forecasting engine — that models how much leverage African states hold in
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

### Framing

This tool is framed around **resilience, bargaining realism, and policy
risk trade-offs** — not as advice for coercion.

### Limitations

1. Processing-capacity data is approximated (see Assumption A002)
2. Contract terms are often confidential (A005)
3. Political dynamics not modelled quantitatively
4. Price elasticities simplified
5. Coalition dynamics modelled simply

### Stack

- **UI:** Streamlit · **Charts:** Plotly · **Data:** Pandas / NumPy
- **All data embedded** — no external API calls required
    """)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          FOOTER                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

st.markdown(
    '<div class="footer">Critical Commodities Leverage Lab (CCLL) v2.0 · '
    'Geoeconomic scenario tool · '
    'Data: USGS · UN Comtrade · IMF · EU CRMA · '
    'Not a forecasting engine — see Assumptions</div>',
    unsafe_allow_html=True)
