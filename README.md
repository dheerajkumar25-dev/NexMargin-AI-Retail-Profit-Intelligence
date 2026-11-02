# NexMargin – AI-Powered Retail Profit Intelligence Platform

<p align="center">
  <strong>Turning Retail Data into Actionable Profit Intelligence</strong>
</p>

<p align="center">
  <a href="https://nexmargin-ai-retail-profit-intelligence.streamlit.app/"><strong>🚀 Live Demo</strong></a> •
  <a href="https://github.com/dheerajkumar25-dev/NexMargin-AI-Retail-Profit-Intelligence"><strong>💻 GitHub Repository</strong></a>
</p>

---

## Overview

**NexMargin** is an AI-powered retail analytics platform designed to help businesses understand profitability, identify profit leakage, and make data-driven decisions.

Unlike traditional sales dashboards that primarily focus on revenue, NexMargin emphasizes the relationship between revenue, discounts, costs, and profit.

The platform transforms retail transaction data into actionable business insights through interactive dashboards, customer analytics, product and regional performance analysis, forecasting, and an AI-powered business intelligence assistant.

## Live Application

**Try NexMargin:** https://nexmargin-ai-retail-profit-intelligence.streamlit.app/

The application is deployed using Streamlit Community Cloud.

## Key Features

### 1. Executive Overview
- Monitor total revenue, total profit, profit margin, and order metrics.
- Analyze customer health and retention.
- Track key business performance indicators.
- Apply date and regional filters for focused analysis.

### 2. Product Performance Analysis
- Evaluate product and category-level profitability.
- Identify products contributing to profit and losses.
- Analyze the impact of discounting on profitability.
- Compare sales performance across product segments.

### 3. Regional Profitability Analysis
- Compare business performance across geographical regions.
- Benchmark regional profit margins against overall performance.
- Identify above-average and below-average regions.
- Support data-driven regional business decisions.

### 4. Customer Analytics
- Analyze active customers and repeat customer behavior.
- Evaluate customer retention patterns.
- Monitor customer-level business performance.
- Understand customer contribution to overall profitability.

### 5. AI-Powered Business Intelligence
- Interact with retail data using a natural-language AI assistant.
- Generate business insights and analytical summaries.
- Explore potential reasons behind profit leakage.
- Receive actionable recommendations using the Groq LLM integration.

### 6. Forecasting and Reporting
- Explore future business performance using forecasting functionality.
- Generate analytical reports.
- Export reports for further business analysis and decision-making.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Dashboard Framework | Streamlit |
| Data Processing | Pandas, NumPy |
| Data Visualization | Plotly |
| Database | DuckDB, SQL |
| Machine Learning | Scikit-learn |
| Generative AI | Groq API, LLM |
| Report Generation | ReportLab, pypdf |
| Environment Management | Python venv, python-dotenv |
| Testing | Pytest |
| Version Control | Git, GitHub |
| Deployment | Streamlit Community Cloud |

## System Architecture

```text
              Retail Transaction Data
                        |
                        v
              Data Loading Pipeline
                        |
                        v
               Data Preprocessing
                        |
             +----------+----------+
             |                     |
             v                     v
       DuckDB / SQL          Analytics Engine
             |                     |
             +----------+----------+
                        |
                        v
               Business Intelligence
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
       Overview      Explore       Forecasting
          |             |             |
          +-------------+-------------+
                        |
                        v
                 Streamlit UI
                        |
             +----------+----------+
             |                     |
             v                     v
        AI Copilot             Reports
             |
             v
          Groq LLM
```

## Project Structure

```text
NexMargin/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
├── .streamlit/
│   └── config.toml
│
├── data/
│   ├── raw/
│   └── processed/
│
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── git_milestones.md
│   ├── interview_questions.md
│   └── methodology.md
│
├── scripts/
│   └── build_data.py
│
├── sql/
│   └── business_queries.sql
│
├── src/
│   └── nexmargin/
│       ├── analytics.py
│       ├── ai_copilot.py
│       ├── config.py
│       ├── database.py
│       ├── data_loader.py
│       ├── forecasting.py
│       ├── metrics.py
│       ├── preprocessing.py
│       ├── report_generator.py
│       ├── segmentation.py
│       │
│       ├── components/
│       │   ├── charts.py
│       │   ├── kpi_cards.py
│       │   ├── sidebar.py
│       │   ├── styling.py
│       │   └── tables.py
│       │
│       └── pages/
│           ├── overview.py
│           ├── explore.py
│           ├── copilot.py
│           └── reports.py
│
└── tests/
    ├── conftest.py
    ├── test_analytics.py
    ├── test_app.py
    ├── test_copilot.py
    ├── test_data.py
    ├── test_database.py
    ├── test_forecasting.py
    ├── test_metrics.py
    ├── test_reports.py
    └── test_segmentation.py
```

## Dataset

NexMargin uses the **Sample Superstore dataset**, containing retail transaction information.

| Attribute | Details |
|---|---|
| Dataset | Sample Superstore |
| Total Raw Records | 9,994 |
| Cleaned Records | 9,993 |
| Data Period | January 2014 – December 2017 |
| Currency | US Dollars |
| Data Source | Public GitHub dataset mirror |

### Data Processing Pipeline

The application performs the following operations:

1. Downloads the raw CSV dataset when it is not available locally.
2. Removes duplicate records and validates important fields.
3. Handles invalid dates, quantities, discounts, and sales values.
4. Identifies loss-making transactions and flags profit outliers.
5. Generates a cleaned dataset and data quality report.

**Data Note:** The source dataset does not contain a cost column. Cost is derived as:

```python
cost = sales - profit
```

The original dataset currency is retained in US dollars without conversion.

## Installation and Setup

### Prerequisites

- Python 3.12 or later (Python 3.13 used during development).
- Git.
- Groq API key for AI-powered functionality.

### 1. Clone the Repository

```bash
git clone https://github.com/dheerajkumar25-dev/NexMargin-AI-Retail-Profit-Intelligence.git

cd NexMargin-AI-Retail-Profit-Intelligence
```

### 2. Create a Virtual Environment

**Windows:**

```powershell
py -3.13 -m venv .venv

.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
NEXMARGIN_CURRENCY=$
```

The Groq API key is optional for dashboard functionality but required for AI-powered features.

Never commit your actual `.env` file or API credentials to GitHub.

For Streamlit Community Cloud, configure the same variables through the application's Secrets settings.

### 5. Build the Dataset

```bash
python scripts/build_data.py
```

This downloads the raw dataset and generates the processed dataset and quality report.

The application can also build the processed dataset automatically when it is missing.

### 6. Run the Application

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal, usually:

```text
http://localhost:8501
```

## Running Tests

Run the project test suite using:

```bash
pytest -q
```

To run individual test modules:

```bash
pytest -q tests/test_analytics.py

pytest -q tests/test_database.py

pytest -q tests/test_forecasting.py
```

## Deployment

NexMargin is deployed using **Streamlit Community Cloud**.

**Live URL:**

https://nexmargin-ai-retail-profit-intelligence.streamlit.app/

Deployment workflow:

1. Push project changes to the GitHub repository.
2. Connect the repository to Streamlit Community Cloud.
3. Configure the main application file as `app.py`.
4. Add required environment variables through Streamlit Secrets.
5. Deploy and access the application through its public URL.

## Business Value

NexMargin focuses on answering important retail business questions:

- Are sales increasing while profitability is declining?
- Which products or categories contribute most to losses?
- Are excessive discounts affecting profit margins?
- Which geographical regions perform below the overall benchmark?
- How effectively does the business retain customers?
- What actions can management take to improve profitability?

By connecting business metrics with analytical insights, NexMargin helps transform raw retail transactions into more informed business decisions.

## Limitations

- The project uses historical Sample Superstore data rather than live enterprise retail transactions.
- The dataset is limited to the 2014–2017 period.
- AI-generated recommendations depend on the configured LLM service and should be reviewed before business decisions.
- Forecasts are analytical estimates, not guaranteed future results.
- The dataset's original licensing terms have not been independently verified.

## Future Improvements

- Integration with live retail databases and APIs.
- Advanced demand and profit forecasting.
- More granular customer lifetime value analysis.
- Automated profit leakage alerts.
- Enhanced scenario and what-if analysis.
- Support for larger enterprise datasets.

## Author

**Dheeraj Kumar**

B.Tech – Electronics and Communication Engineering  
Indian Institute of Information Technology, Bhagalpur

- GitHub: https://github.com/dheerajkumar25-dev
- Project Repository: https://github.com/dheerajkumar25-dev/NexMargin-AI-Retail-Profit-Intelligence

---

<p align="center">
  <strong>Built with Python, Data Analytics, Machine Learning and Generative AI.</strong>
</p>

<p align="center">
  <a href="https://nexmargin-ai-retail-profit-intelligence.streamlit.app/">Explore NexMargin Live 🚀</a>
</p>