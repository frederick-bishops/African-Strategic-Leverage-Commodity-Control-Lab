# ASLC — African Strategic Leverage & Commodity Control Lab

A geoeconomic bargaining simulator that models Africa's strategic leverage over critical commodities vis-à-vis the EU and China. Built as a single-file Streamlit application.

## Overview

ASLC covers **11 commodities** across **20 African countries** and quantifies leverage across seven dimensions:

| Dimension | Description |
|-----------|-------------|
| Buyer Diversification | How spread out the buyer base is (EU vs China vs others) |
| Substitutability Barrier | How difficult it is for importers to substitute the commodity |
| Stockpiling Difficulty | Months of global consumption held in reserves |
| Chokepoint Control | Africa's control over critical logistics corridors |
| Processing Capacity | Africa's share of downstream refining/processing |
| Financial Independence | Degree of financial autonomy from commodity-linked debt |
| Regulatory Leverage | Strength of policy tools (export bans, beneficiation mandates, etc.) |

### Commodities

| Category | Commodities |
|----------|-------------|
| Industrial Metals | Manganese, Bauxite/Alumina, Cobalt, Lithium, Copper |
| Energy | Refined Petroleum, Uranium |
| Precious Metals | Platinum Group Metals, Gold |
| Agricultural | Cocoa, Coffee |

### Countries (20)

Ghana, South Africa, DRC, Guinea, Gabon, Zimbabwe, Zambia, Côte d'Ivoire, Nigeria, Ethiopia, Tanzania, Mozambique, Namibia, Niger, Mali, Angola, Uganda, Kenya, Rwanda, Botswana

### Features

- **Leverage Analysis** — Interactive radar charts and bar breakdowns per commodity, with country-level focus
- **Policy Simulator** — Model 7 policy interventions (export quotas, tariffs, joint ventures, etc.) and see projected shifts in leverage, GDP, and risk
- **Comparative Dashboard** — Side-by-side commodity comparison with customisable dimension weights
- **Country Explorer** — Per-country commodity footprint and infrastructure profile
- **Second-Order Effects** — Trade-diversion, retaliation, and supply-chain disruption modelling
- **Data Export** — Download simulation results as CSV

## Data Sources

All baseline data is embedded directly in the code with inline source citations. Key references:

- **USGS Mineral Commodity Summaries 2024** — Production volumes, reserves
- **UN Comtrade / ITC Trade Map** — Trade flows, export shares
- **World Bank Commodity Markets Outlook** — Price benchmarks, GDP data
- **IMF Direction of Trade Statistics** — Bilateral trade data
- **ICCO** — Cocoa production and pricing
- **ICO / USDA** — Coffee production and trade
- **IEA, IRENA** — Energy sector data
- **World Nuclear Association / IAEA Red Book** — Uranium production and reserves
- **S&P Global / Benchmark Mineral Intelligence** — Processing capacity
- **World Gold Council** — Gold production by country
- **OPEC** — Petroleum production quotas and output

## Deployment on Streamlit Community Cloud

### Steps

1. **Push to GitHub**
   Create a new repository and push the contents of this folder:
   ```
   ccll-v3/
   ├── app.py
   ├── requirements.txt
   ├── .streamlit/
   │   └── config.toml
   └── README.md
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click **"New app"**
   - Select your repository, branch (`main`), and set the main file path to `app.py`

3. **⚠️ Select Python 3.12**
   - Before clicking **"Deploy"**, expand **"Advanced settings"**
   - Set the Python version to **3.12**
   - Streamlit Cloud defaults to Python 3.13, but some dependencies (notably NumPy 2.2.4) may not have pre-built wheels for 3.13 yet. Using 3.12 ensures all packages install without issues.

4. **No secrets required** — the app is fully self-contained with no external API calls.

### Local Development

```bash
# Create a virtual environment (Python 3.12 recommended)
python3.12 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Tech Stack

| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | 1.44.1 | Web framework and UI |
| plotly | 6.0.1 | Interactive charts (radar, bar, line, sankey) |
| pandas | 2.2.3 | Data manipulation and CSV export |
| numpy | 2.2.4 | Numerical computations |

## Architecture

The entire application is contained in a single file (`app.py`, ~2,476 lines) organised into sections:

1. **Configuration** — Page config, brand palette, custom CSS
2. **Country Profiles** — 20 countries with GDP, ports, BITs, credit ratings
3. **Commodity Database** — 11 commodities with production data, leverage vectors, policy precedents
4. **Policy Definitions** — 7 policy instruments with parameter ranges and second-order effects
5. **Assumptions Register** — 14 documented assumptions with sources and impact notes
6. **Models** — Leverage scoring, policy simulation, gap analysis, second-order effects
7. **Visualisations** — Plotly chart builders with brand theming
8. **Export** — CSV and TXT report generators
9. **UI** — Streamlit page routing, sidebar, metric cards, 7 pages

## License

MIT
