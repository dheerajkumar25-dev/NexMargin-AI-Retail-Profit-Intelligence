# NexMargin

### AI-Powered Retail Profit Intelligence Platform

NexMargin is an interactive retail analytics platform designed to help businesses understand sales performance, identify profit leakage, and make data-driven decisions.

Built with Python and Streamlit, it combines business analytics, customer segmentation, product performance analysis, regional profitability benchmarking, revenue forecasting, and an AI-powered business copilot in one dashboard.

---

## Key Features

### 1. Business Overview
- Track total revenue, profit, profit margin, and orders.
- Compare current and previous periods.
- Analyze monthly business performance.
- View customer health metrics and business insights.

### 2. Product Performance Analysis
- Identify top-performing products.
- Analyze revenue and profit contribution.
- Find low-margin products.
- Classify products into performance categories:
  - High Performer
  - Revenue Driver
  - Hidden Gem
  - Underperformer

### 3. Customer Analytics
- Analyze customer purchase frequency.
- Measure repeat customer rate.
- Evaluate customer concentration.
- Perform RFM-based customer segmentation.
- Analyze annual customer retention.

### 4. Discount & Profitability Analysis
- Analyze profitability across discount bands.
- Identify loss-making transactions.
- Investigate discount-related profit leakage.

### 5. Regional Analysis
- Compare revenue and profit across regions.
- Analyze regional profit margins.
- Benchmark regional margins against overall business performance.

### 6. AI Business Copilot
- Ask business-related questions.
- Generate AI-assisted business explanations.
- Retrieve insights using application analytics.
- Support fallback responses when the AI service is unavailable.

### 7. Forecasting & Reports
- Generate monthly revenue forecasts.
- Evaluate forecasting performance against a baseline.
- Generate business summaries.
- Export reports and analytical data.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Dashboard | Streamlit |
| Data Processing | Pandas, NumPy |
| Database | DuckDB |
| Query Language | SQL |
| Visualization | Plotly |
| Machine Learning | Scikit-learn |
| AI Integration | Groq API |
| PDF Generation | ReportLab |
| Testing | Pytest |

---

## System Architecture

```text
             Retail Dataset
                   |
                   v
          Data Preprocessing
                   |
                   v
          Processed Dataset
                   |
          +--------+--------+
          |        |        |
          v        v        v
       Python   DuckDB   Forecasting
       Metrics    SQL    & Segmentation
          |        |        |
          +--------+--------+
                   |
                   v
            Analytics Layer
                   |
          +--------+--------+
          |        |        |
          v        v        v
       Overview Explore  AI Copilot
          |        |        |
          +--------+--------+
                   |
                   v
             Reports & Exports
```

---

## Project Structure

```text
NexMargin/
|
|-- app.py
|-- requirements.txt
|-- .env.example
|-- .gitignore
|
|-- data/
|   |-- raw/
|   |-- processed/
|
|-- docs/
|   |-- architecture.md
|   |-- data_dictionary.md
|   |-- methodology.md
|   |-- git_milestones.md
|   |-- interview_questions.md
|
|-- scripts/
|   |-- build_data.py
|
|-- sql/
|   |-- business_queries.sql
|
|-- src/
|   |-- nexmargin/
|       |-- analytics.py
|       |-- ai_copilot.py
|       |-- config.py
|       |-- database.py
|       |-- data_loader.py
|       |-- forecasting.py
|       |-- formatting.py
|       |-- metrics.py
|       |-- preprocessing.py
|       |-- report_generator.py
|       |-- segmentation.py
|       |
|       |-- components/
|       |-- pages/
|
|-- tests/
    |-- conftest.py
    |-- helpers.py
    |-- test_analytics.py
    |-- test_app.py
    |-- test_copilot.py
    |-- test_data.py
    |-- test_database.py
    |-- test_forecasting.py
    |-- test_metrics.py
    |-- test_reports.py
    |-- test_segmentation.py
```

---

## Installation & Setup

### Prerequisites

- Python 3.13
- Git
- VS Code (recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/dheerajkumar25-dev/NexMargin-AI-Retail-Profit-Intelligence.git

cd NexMargin-AI-Retail-Profit-Intelligence
```

### 2. Create a Virtual Environment

**Windows PowerShell**

```powershell
py -3.13 -m venv .venv

.\.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip

pip install -r requirements.txt
```

### 4. Prepare the Dataset

```bash
python scripts/build_data.py
```

This runs the project's data preparation pipeline and generates the processed dataset.

### 5. Start the Application

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal:

```text
http://localhost:8501
```

---

## AI Configuration

NexMargin supports optional AI-powered explanations through the Groq API.

To enable the AI integration:

1. Create a Groq API key.
2. Copy `.env.example` to `.env`.
3. Add your API key to the `.env` file.
4. Restart the application.

Example configuration:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

**Security:** Never upload your `.env` file or expose your API key on GitHub.

The application can also use its fallback functionality when an API key is not configured.

---

## Running Tests

NexMargin uses pytest for automated testing.

Run the complete test suite:

```bash
pytest -q
```

Run a specific test module:

```bash
pytest -q tests/test_analytics.py
```

The tests cover:

- Data preprocessing and validation
- Business metrics and analytics
- Database and SQL queries
- Product and regional analysis
- Customer segmentation
- Forecasting
- AI Copilot behaviour
- Report generation
- Streamlit application functionality

---

## Analytical Methodology

- **Data Processing:** Clean and validate retail transaction data before analysis.
- **Business Metrics:** Use shared Python functions for consistent KPI calculations.
- **Database Queries:** Use DuckDB and approved parameterised SQL queries.
- **Product Analysis:** Evaluate product performance using revenue and profit margins.
- **Customer Segmentation:** Apply RFM-based scoring to understand customer behaviour.
- **Regional Benchmarking:** Compare regional profit margins with the overall business margin.
- **Forecasting:** Evaluate revenue forecasts against a baseline.
- **AI Explanations:** Use calculated business results as the basis for AI-assisted explanations.

For additional details, see the documentation in the `docs/` directory.

---

## Data Source & Limitations

The project uses sample retail transaction data for analytical demonstration.

The dataset is intended for learning, experimentation, and business analytics practice. Forecasts and customer classifications should be interpreted in the context of the available historical data.

The project is not intended to replace financial accounting systems or provide guaranteed business forecasts.

---

## Future Improvements

- Additional forecasting models.
- More advanced customer retention analysis.
- Support for multiple retail datasets.
- Improved dashboard customisation.
- Additional business intelligence features.

---

## Author

**Dheeraj Kumar**

B.Tech – Electronics and Communication Engineering

IIIT Bhagalpur

[GitHub](https://github.com/dheerajkumar25-dev)

---

**NexMargin — Turning Retail Data into Clearer Profit Decisions.**