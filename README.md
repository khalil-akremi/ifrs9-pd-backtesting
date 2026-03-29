# 🏦 IFRS 9 — Probability of Default Backtesting System

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-red?logo=streamlit)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

> End-to-end IFRS 9 Probability of Default (PD) backtesting system built on the 
> *Give Me Some Credit* dataset (Kaggle). Includes model development, validation, 
> explainability, Monte Carlo simulation, stress testing, a REST API and an 
> interactive dashboard.

---

## 📋 Table of Contents

- [Context](#context)
- [Architecture](#architecture)
- [Features](#features)
- [Results](#results)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Dashboard](#dashboard)
- [Tech Stack](#tech-stack)
- [Author](#author)

---

## 📖 Context

Under **IFRS 9** (effective January 2018), financial institutions must provision 
their credit assets based on Expected Credit Loss (ECL):

$$ECL = PD \times LGD \times EAD$$

This project focuses on the **PD component**, validating models across 
three IFRS 9 backtesting dimensions:

| Dimension | Tools | Status |
|---|---|---|
| **Discrimination** | AUC-ROC, Gini, KS, CAP/AR | ✅ Validated |
| **Calibration** | Brier Score, Hosmer-Lemeshow, Platt Scaling | ✅ Validated |
| **Stability** | Population Stability Index (PSI) | ✅ Validated |

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    IFRS 9 PD System                     │
├─────────────┬──────────────┬──────────────┬────────────┤
│   Notebook  │  FastAPI     │  Streamlit   │   Models   │
│   (Colab)   │  REST API    │  Dashboard   │   (.pkl)   │
├─────────────┴──────────────┴──────────────┴────────────┤
│              Docker Compose (coming soon)               │
└─────────────────────────────────────────────────────────┘
```

**Data flow :**
```
Kaggle Dataset → EDA & Cleaning → PD Modeling → Backtesting
                                                     ↓
Dashboard ← FastAPI ← Saved Models (.pkl) ← Calibration
```

---

## ✨ Features

### 🤖 PD Modeling
- **Logistic Regression** — IFRS 9 regulatory baseline
- **Scorecard WoE/IV** — industry standard with Weight of Evidence transformation
- **XGBoost** — best performance with gradient boosting

### 📊 IFRS 9 Backtesting
- Discrimination : AUC, Gini coefficient, KS test, CAP curve & Accuracy Ratio
- Calibration : Brier Score, decile analysis, Platt Scaling recalibration
- Stability : Population Stability Index (PSI) train vs test

### 🔬 Advanced Analytics
- **SHAP Values** — per-client explainability with waterfall charts
- **Monte Carlo ECL** — 10,000 scenario simulation with VaR & Expected Shortfall
- **Stress Testing** — Baseline / Adverse / Severely Adverse IFRS 9 scenarios

### 🚀 Production-Ready
- **FastAPI** REST API with 6 endpoints
- **Streamlit** interactive dashboard with 8 pages
- **PDF Report** generation — Model Validation Report & per-client scoring report

---

## 📈 Results

### Discrimination Metrics

| Model | AUC | Gini | KS | Status |
|---|---|---|---|---|
| Logistic Regression | 0.8596 | 0.7193 | 0.5611 | ✅ Excellent |
| Scorecard WoE/IV | 0.8468 | 0.6936 | 0.5347 | ✅ Excellent |
| **XGBoost** | **0.8689** | **0.7374** | **0.5861** | ✅ **Best** |

> Banking thresholds: AUC > 0.80, Gini > 0.60, KS > 0.40

### Calibration (after Platt Scaling)

| Model | Brier Score | Status |
|---|---|---|
| Logistic Regression | 0.0511 | ✅ Good |
| Scorecard WoE/IV | 0.0517 | ✅ Good |
| XGBoost | 0.0494 | ✅ Best |

### Stability (PSI)

| Model | PSI | Status |
|---|---|---|
| All models | < 0.001 | ✅ Stable |

---

## 📁 Project Structure
```
ifrs9-pd-backtesting/
│
├── 📓 notebook/
│   └── ifrs9_backtesting.ipynb     # Full analysis notebook
│
├── 🤖 models/                       # Serialized models
│   ├── calibrated_lr.pkl
│   ├── calibrated_woe.pkl
│   ├── calibrated_xgb.pkl
│   ├── scaler.pkl
│   ├── woe_maps.pkl
│   ├── woe_configs.pkl
│   ├── feature_names.pkl
│   └── metrics.pkl
│
├── 🚀 api/                          # FastAPI backend
│   ├── main.py                     # API endpoints
│   ├── predict.py                  # Prediction logic
│   ├── schemas.py                  # Pydantic schemas
│   └── requirements.txt
│
├── 📊 dashboard/                    # Streamlit frontend
│   ├── app.py                      # Main app
│   ├── requirements.txt
│   └── pages/
│       ├── home.py                 # Landing page
│       ├── predict.py              # Client prediction
│       ├── backtest.py             # Backtesting results
│       ├── portfolio.py            # Portfolio analysis
│       ├── shap_page.py            # SHAP explainability
│       ├── montecarlo_page.py      # Monte Carlo ECL
│       ├── stress_page.py          # Stress testing
│       └── report.py               # PDF generation
│
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/TON_USERNAME/ifrs9-pd-backtesting.git
cd ifrs9-pd-backtesting

# Install API dependencies
pip install -r api/requirements.txt

# Install Dashboard dependencies  
pip install -r dashboard/requirements.txt
```

### Download Models
Download the pre-trained models from [Google Drive](LINK) and place them in the `models/` folder.

### Run

**Terminal 1 — API:**
```bash
cd api
uvicorn main:app --reload
```

**Terminal 2 — Dashboard:**
```bash
cd dashboard
streamlit run app.py
```

- API : http://127.0.0.1:8000
- Dashboard : http://127.0.0.1:8501
- API Docs : http://127.0.0.1:8000/docs

---

## 🔌 API Documentation

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | API health check |
| POST | `/predict` | Single client PD prediction |
| POST | `/predict/batch` | Portfolio batch scoring |
| POST | `/shap` | SHAP explainability |
| POST | `/monte-carlo` | Monte Carlo ECL simulation |
| POST | `/stress-test` | IFRS 9 stress testing |
| GET | `/metrics` | Backtesting metrics |

### Example Request
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "RevolvingUtilizationOfUnsecuredLines": 0.35,
    "age": 45,
    "NumberOfTime30_59DaysPastDueNotWorse": 0,
    "DebtRatio": 0.40,
    "MonthlyIncome": 6500,
    "NumberOfOpenCreditLinesAndLoans": 8,
    "NumberOfTimes90DaysLate": 0,
    "NumberRealEstateLoansOrLines": 1,
    "NumberOfTime60_89DaysPastDueNotWorse": 0,
    "NumberOfDependents": 2
  }'
```

### Example Response
```json
{
  "PD_logistic": 0.0382,
  "PD_scorecard": 0.0511,
  "PD_xgboost": 0.0173,
  "PD_moyenne": 0.0355,
  "niveau_risque": "Faible",
  "ECL_estime": 1246.05,
  "interpretation": {
    "RevolvingUtilization": "✅ Utilisation faible du crédit",
    "age": "✅ Tranche d'âge neutre",
    "retards": "✅ Aucun retard de paiement",
    "revenu": "✅ Revenu mensuel correct"
  }
}
```

---

## 📊 Dashboard

The Streamlit dashboard provides 8 interactive pages:

| Page | Description |
|---|---|
| 🏠 Home | Key metrics & API status |
| 🔍 Prediction | Real-time PD scoring |
| 📊 Backtesting | AUC, Gini, KS, PSI results |
| 📁 Portfolio | Batch scoring & risk distribution |
| 🔬 SHAP | Per-client explainability |
| 📈 Monte Carlo | ECL distribution & VaR |
| ⚡ Stress Testing | IFRS 9 macroeconomic scenarios |
| 📄 PDF Report | Automated report generation |

---

## 🛠️ Tech Stack

### Machine Learning
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-orange)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-orange)
![SHAP](https://img.shields.io/badge/SHAP-0.44-blue)
![NumPy](https://img.shields.io/badge/NumPy-1.26-blue)
![Pandas](https://img.shields.io/badge/Pandas-2.2-blue)

### Backend
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)
![Uvicorn](https://img.shields.io/badge/Uvicorn-0.29-green)
![Pydantic](https://img.shields.io/badge/Pydantic-2.6-green)

### Frontend
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-red)
![Plotly](https://img.shields.io/badge/Plotly-5.20-purple)

### DevOps (Coming Soon)
![Docker](https://img.shields.io/badge/Docker-🐳-blue)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-⚙️-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-🐘-blue)
![MLflow](https://img.shields.io/badge/MLflow-📊-blue)

---

## 👨‍💻 Author

**Khalil Akremi**
- 2nd year Engineering Student — ESSAI (École Supérieure de la Statistique 
  et de l'Analyse de l'Information), Tunis
- Head of Pôle Formation — ASIA (Statistics & AI Student Association)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://linkedin.com/in/TON_PROFIL)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black?logo=github)](https://github.com/TON_USERNAME)

---

## 📄 License

This project is licensed under the MIT License.

---

*Built as part of an IFRS 9 course project at ESSAI — 2026*
