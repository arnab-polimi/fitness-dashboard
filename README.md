# ⚡ ApexFitness — Personal Fitness Intelligence Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3F4F75.svg)](https://plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> A modern, web-based running intelligence platform built with **Python**, **Streamlit**, and **Plotly**. Ingests and deduplicates Garmin Connect and Strava activity archives, computes cutting-edge physiological endurance telemetry (CTL/ATL/TSB, VDOT, Aerobic Decoupling, Efficiency Factor), and powers a transparent multi-signal injury-risk engine and natural language fitness insights.

---

## 📸 Key Features

- 📥 **Universal Activity Ingestion**: Drag-and-drop support for Garmin Connect (`Activities.csv`) and Strava Archive (`activities.csv`) exports.
- 🔄 **Intelligent Cross-Source Deduplication**: Identifies overlapping runs using fuzzy timestamp, distance, and duration matching, merging Garmin's granular telemetry (cadence, vertical oscillation, training effect) with Strava's social titles and perceived exertion.
- 📈 **Performance Management Chart (PMC)**: Exponentially Weighted Moving Averages for **Chronic Training Load (CTL / Fitness)**, **Acute Training Load (ATL / Fatigue)**, and **Training Stress Balance (TSB / Form)**.
- 🫀 **Cardiovascular & Aerobic Telemetry**:
  - **Efficiency Factor (EF)**: Tracks speed per heartbeat ($m/\text{min}$ per $\text{bpm}$) over time to measure mitochondrial adaptations.
  - **Aerobic Decoupling ($Pw:HR$)**: Quantifies cardiac drift on long runs to verify aerobic base depth.
  - **Polarized Zone Distribution**: Breakdown of training time across 5 Heart Rate Zones.
- 🛡️ **Transparent Training-Stress & Injury-Risk Indicator**: Multi-signal model assessing **Acute:Chronic Workload Ratio (ACWR)**, **7-Day Ramp Rate**, **Foster's Monotony & Strain**, **Consecutive Hard Days**, and **Biomechanical Cadence Anomalies**. *Clearly labeled as a training-load risk indicator, not a medical prediction.*
- 🧠 **"What is Happening to My Fitness?"**: Structured narrative engine explaining physiological adaptations, volume trends, and actionable coaching guidance.
- 🏁 **Race Performance Predictor**: Predicts 5K, 10K, Half Marathon, and Marathon times using Jack Daniels VDOT formulas and Pete Riegel power laws calibrated with your Chronic Training Load.
- 🌙 **Sleek Cyber-Dark UI**: Glassmorphism cards, glowing telemetry accents, and responsive Plotly visual analytics.

---

## 🏗️ Architecture & Project Structure

```
fitness-dashboard/
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
├── app.py                      # Main Streamlit application entrypoint
├── sample_data/                # Sample CSV datasets for instant preview
│   ├── sample_garmin_activities.csv
│   └── sample_strava_activities.csv
├── src/
│   ├── models/                 # Unified dataclasses and schemas
│   │   ├── activity.py         # Unified Activity schema
│   │   ├── user_profile.py     # Athlete profile and HR zones
│   │   └── metrics.py          # Daily load, risk signals, and insights
│   ├── db/                     # Database access layer
│   │   ├── database.py         # SQLite / DuckDB DatabaseManager
│   │   └── schema.py           # SQL DDL schemas and indexes
│   ├── ingestion/              # Parsers and deduplication
│   │   ├── garmin_parser.py    # Garmin Connect CSV parser
│   │   ├── strava_parser.py    # Strava archive CSV parser
│   │   ├── file_detector.py    # Automatic CSV format detector
│   │   └── deduplicator.py     # Cross-source deduplication engine
│   ├── analytics/              # Physiological & math models
│   │   ├── training_load.py    # Banister TRIMP, rTSS, hrTSS, EWMA CTL/ATL/TSB
│   │   ├── running_metrics.py  # VDOT, Efficiency Factor, Decoupling, Paces
│   │   ├── race_predictor.py   # 5K/10K/Half/Full Marathon predictor
│   │   └── injury_risk.py      # Multi-signal Training Stress Risk Engine
│   ├── insights/               # Narrative intelligence
│   │   └── engine.py           # "What is happening to my fitness?" generator
│   ├── ui/                     # UI components and Plotly charts
│   │   ├── theme.py            # Dark professional CSS styling
│   │   ├── components.py       # Reusable cards, banners, metric widgets
│   │   ├── charts.py           # Plotly chart builders
│   │   └── views/              # Tabbed views
│   │       ├── overview.py
│   │       ├── training_load_view.py
│   │       ├── cardiovascular_view.py
│   │       ├── injury_risk_view.py
│   │       ├── insights_view.py
│   │       ├── race_predictor_view.py
│   │       ├── activity_log_view.py
│   │       ├── import_view.py
│   │       └── settings_view.py
│   └── data/
│       └── synthetic_generator.py # Realistic 6-month dev dataset generator
└── tests/                      # Automated unit test suite
    ├── test_parsers.py
    ├── test_deduplicator.py
    ├── test_analytics.py
    ├── test_injury_risk.py
    └── test_db.py
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ installed.

### 2. Installation
Clone the repository and install requirements:
```bash
git clone https://github.com/yourusername/fitness-dashboard.git
cd fitness-dashboard
pip install -r requirements.txt
```

### 3. Run Application
Launch the Streamlit web dashboard:
```bash
streamlit run app.py
```
*(Or on Windows: `python -m streamlit run app.py`)*

The dashboard will open automatically at `http://localhost:8501`.

---

## 🧪 Testing

Run the full pytest suite:
```bash
python -m pytest -v
```

---

## 📊 Scientific & Mathematical Formulations

### 1. Banister TRIMP (Training Impulse)
$$\text{TRIMP} = D \times \Delta\text{HR} \times y \times e^{b \cdot \Delta\text{HR}}$$
- $D$: Duration in minutes.
- $\Delta\text{HR} = \frac{\text{HR}_{\text{avg}} - \text{HR}_{\text{rest}}}{\text{HR}_{\text{max}} - \text{HR}_{\text{rest}}}$ (Heart Rate Reserve fraction).
- $b = 1.92$ (males) or $1.86$ (females), $y = 0.64$ (males) or $0.86$ (females).

### 2. Running Training Stress Score (rTSS)
$$\text{rTSS} = \left( \frac{t \times \text{IF}^2}{3600} \right) \times 100 \quad \text{where} \quad \text{IF} = \frac{\text{vLT}}{\text{Pace}_{\text{avg}}}$$

### 3. EWMA Fitness, Fatigue & Form
- **Fitness (CTL)**: $CTL_t = CTL_{t-1} + (TSS_t - CTL_{t-1}) \cdot (1 - e^{-1/42})$
- **Fatigue (ATL)**: $ATL_t = ATL_{t-1} + (TSS_t - ATL_{t-1}) \cdot (1 - e^{-1/7})$
- **Form (TSB)**: $TSB_t = CTL_t - ATL_t$

### 4. Jack Daniels VDOT / VO2max
$$\text{VO}_2 = -4.60 + 0.182258 \cdot v + 0.000104 \cdot v^2 \quad (v = \text{m/min})$$
$$\%VO_{2\text{max}} = 0.8 + 0.1894393 \cdot e^{-0.0115 \cdot t} + 0.2989558 \cdot e^{-0.05 \cdot t}$$
$$\text{VDOT} = \frac{\text{VO}_2}{\%VO_{2\text{max}}}$$

### 5. Multi-Signal Training-Stress & Injury-Risk Model
1. **Acute:Chronic Workload Ratio (ACWR - 30% weight)**: $0.8 \le \text{ACWR} \le 1.3$ (Sweet spot).
2. **7-Day Ramp Rate (20% weight)**: Weekly CTL climb capped at $\le 5$ TSS/week.
3. **Foster's Monotony & Strain (20% weight)**: $\text{Monotony} = \frac{\mu}{\sigma} \le 1.5$.
4. **Consecutive High-Load Days (15% weight)**: Days with TSS $\ge 60$.
5. **Biomechanical Cadence & Decoupling (15% weight)**: Cadence drop $>4\%$ or Decoupling $>8\%$.

> ⚠️ **DISCLAIMER**: The Training-Stress & Injury-Risk Indicator is an operational load monitoring tool based on physiological training variance. It is **NOT** a medical diagnostic tool or clinical injury predictor. Always listen to your body and consult qualified healthcare professionals.

---

## 📄 License
MIT License. Built for runners, coaches, and sports science enthusiasts.
