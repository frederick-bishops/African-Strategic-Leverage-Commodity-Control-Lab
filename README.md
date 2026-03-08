# CCLL — Commodity Control & Leverage Lab

A geoeconomic bargaining simulator that models Africa's strategic leverage over critical commodities vis-à-vis the EU and China. Built as a single-file Streamlit application.

## Overview

CCLL covers **7 African commodities** — Manganese, Bauxite, Cobalt, Lithium, Cocoa, Platinum Group Metals (PGMs), and Refined Petroleum — and quantifies leverage across six dimensions:

| Dimension | Description |
|-----------|-------------|
| Supply Concentration | Herfindahl–Hirschman Index of African production share |
| Demand Inelasticity | How difficult it is for importers to substitute the commodity |
| Stockpile Vulnerability | Months of global consumption held in reserves |
| Processing Control | Africa's share of downstream refining/processing |
| Revenue Dependency | Share of exporter GDP tied to the commodity |
| Geopolitical Alignment | Diplomatic positioning between EU and China |

### Features

- **Leverage Analysis** — Interactive radar charts and bar breakdowns for each commodity
- **Policy Simulator** — Model 7 policy interventions (export quotas, tariffs, joint ventures, etc.) and see projected shifts in leverage, GDP, and risk
- **Comparative Dashboard** — Side-by-side commodity comparison with customisable dimension weights
- **Second-Order Effects** — Trade-diversion, retaliation, and supply-chain disruption modelling
- **Data Export** — Download simulation results as CSV

## Data Sources

All baseline data is embedded directly in the code with inline source citations. Key references:

- **USGS Mineral Commodity Summaries 2024** — Production volumes, reserves
- **UN Comtrade / ITC Trade Map** — Trade flows, export shares
- **World Bank Commodity Markets Outlook** — Price benchmarks
- **IMF Direction of Trade Statistics** — Bilateral trade data
- **ICCO, IEA, IRENA** — Sector-specific production and demand data
- **S&P Global / Benchmark Mineral Intelligence** — Processing capacity data

## Deployment on Streamlit Community Cloud

### Prerequisites

- A GitHub account
- A [Streamlit Community Cloud](https://streamlit.io/cloud) account (free)

### Steps

1. **Push to GitHub**
   Create a new repository and push the contents of this folder:
   ```
   ccll-v2/
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
| plotly | 6.0.1 | Interactive charts (radar, bar, line) |
| pandas | 2.2.3 | Data manipulation and CSV export |
| numpy | 2.2.4 | Numerical computations |

## Architecture

The entire application is contained in a single file (`app.py`, ~1,877 lines) organised into sections:

1. **Data Layer** — Embedded dicts/lists with real-world calibrated values
2. **Model Layer** — Leverage scoring, policy simulation, second-order effects
3. **Visualisation Layer** — Plotly chart builders with brand theming
4. **UI Layer** — Streamlit page routing, sidebar, metric cards, interactivity

## License

MIT
