# 🛒 FunnelIQ — E-Commerce Conversion Funnel Optimization

> A Masters-level Business Analytics project analyzing real e-commerce clickstream data to identify checkout funnel drop-off points, quantify conversion loss by segment, and build a machine learning model to predict session abandonment.

---

## 📌 Project Overview

Cart abandonment costs e-commerce businesses an estimated $18 billion annually. The gap between a user viewing a product and completing a purchase is rarely random — it follows patterns driven by price sensitivity, category behavior, session timing, and browsing depth. This project uses real behavioral data to identify exactly where and why users drop off, then builds a predictive model to flag high-risk sessions before they abandon.

**Business questions answered:**
- What is the conversion rate at each stage of the funnel — and where is the biggest leak?
- Which product categories, brands, and price tiers have the worst cart abandonment?
- What time-of-day and day-of-week patterns drive conversion vs abandonment?
- Can we predict which cart sessions will convert — and what are the strongest signals?
- What specific UX interventions would recover the most lost conversions?

---

## 🗂️ Repository Structure

```
funneliq-ecommerce-funnel-analytics/
│
├── README.md
├── data/
│   └── 2019-Oct.csv              ← REES46 dataset (download from Kaggle)
│
├── notebooks/
│   ├── 01_data_prep.py           ← clean, build funnel, load to SQLite
│   ├── 02_sql_analysis.py        ← run all SQL queries
│   ├── 03_eda.py                 ← 8 EDA charts
│   └── 04_ml_model.py            ← drop-off predictor + SHAP analysis
│
├── sql/
│   ├── 01_schema.sql
│   ├── 02_funnel_dropoff.sql
│   ├── 03_segment_analysis.sql
│   └── 04_time_patterns.sql
│
└── outputs/
    ├── eda_charts.png
    ├── ml_results.png
    └── FunnelIQ_Insights_Brief.pdf
```

---

## 📊 Dataset

**Source:** REES46 eCommerce Behavior Data — real clickstream data from a multi-category online store.

**Download:** https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store

**File used:** `2019-Oct.csv` (~2.3M rows, October 2019)

| Column | Description |
|---|---|
| `event_time` | UTC timestamp |
| `event_type` | view / cart / purchase |
| `product_id` | unique product identifier |
| `category_code` | product category (e.g. electronics.smartphone) |
| `brand` | brand name |
| `price` | product price (USD) |
| `user_id` | unique user identifier |
| `user_session` | session ID (resets after inactivity) |

---

## 🔍 Key Findings

1. **View → Cart is the biggest drop-off point** — only ~11% of viewing sessions add to cart, representing the largest conversion leak in the funnel.

2. **Electronics and appliances have the highest abandonment rates** — high price points correlate with longer consideration cycles and higher cart abandonment.

3. **Sessions between 10am–2pm convert at 2× the rate of late-night sessions** — timing-based interventions (urgency messaging, limited-time offers) are most effective during peak browsing hours.

4. **The ML model identifies 3 key abandonment signals** — session duration under 3 minutes, avg cart price above $200, and single-category browsing are the strongest predictors of non-conversion.

5. **Targeting the top predicted-abandonment segment with a checkout nudge projects a 12–16% conversion lift** based on model precision and industry A/B test benchmarks.

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| Data Processing | Python (pandas, numpy) |
| Database | SQLite |
| SQL Analysis | Standard ANSI SQL |
| Visualization | matplotlib, seaborn |
| ML Model | scikit-learn (Logistic Regression), XGBoost |
| Explainability | SHAP |
| Reporting | reportlab (PDF) |

---

## 🚀 How to Run

```bash
# Clone the repo
git clone https://github.com/yourusername/funneliq-ecommerce-funnel-analytics.git
cd funneliq-ecommerce-funnel-analytics

# Download dataset from Kaggle and place in data/
# https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store

# Install dependencies
pip install pandas numpy matplotlib seaborn scikit-learn xgboost shap reportlab

# Run modules in order
python notebooks/01_data_prep.py
python notebooks/02_sql_analysis.py
python notebooks/03_eda.py
python notebooks/04_ml_model.py
```

---

## 💼 Business Context

This project mirrors the analytical scope of a **Business Analytics & AI** role focused on conversion optimization. The core workflow — funnel analysis → segment identification → predictive modeling → intervention recommendation — is the standard playbook used by growth analytics teams at e-commerce companies.

The ML model component elevates this beyond standard funnel reporting: rather than describing what happened, it predicts what will happen next, enabling proactive intervention before a session abandons.

---

*Built as a Masters-level portfolio project for Business Analytics & AI.*
