<div align="center">

# 📊 DataLens AI
### Intelligent Data Analytics Agent

<img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/Jupyter-Notebook-orange?style=for-the-badge&logo=jupyter&logoColor=white" alt="Jupyter"/>
<img src="https://img.shields.io/badge/Google-Gemini%20AI-purple?style=for-the-badge&logo=google&logoColor=white" alt="Gemini"/>

---

**An autonomous AI-powered data analytics system that transforms raw datasets (CSV/Excel) into professional visualizations and interactive dashboards. Built with Google's Gemini API, this agent intelligently analyzes data, performs automated cleaning, and generates comprehensive visual insights.**

[🚀 Live Demo (V1)](https://huggingface.co/spaces/adinathjagtap/ai-data-analysis-agent) • [📺 Video Demo](https://youtube.com) • [📖 Documentation](#-quick-start)

**Capstone Project Submission for Google's 5-Day AI Agents Intensive Course**

</div>

---

## 📖 Table of Contents

- [Workflow Pipeline](#-workflow-pipeline)
- [Core Capabilities](#-core-capabilities)
- [Installation & Setup](#%EF%B8%8F-installation--setup)
- [Quick Start](#-quick-start)
- [Features](#-features)
- [Output Deliverables](#-output-deliverables)
- [Technical Architecture](#-technical-architecture)
- [Use Cases](#-use-cases)
- [Project Structure](#-project-structure)
- [Notes](#-notes)
- [License](#-license)

---

## 🔄 Workflow Pipeline

<div align="center">

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Setup           │ -> │  Initialize      │ -> │  Load            │
│  Environment     │    │  Gemini AI       │    │  Data            │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                                          |
                                                          v
┌──────────────────┐    ┌──────────────────────────────────────────┐
│  Generate        │ <- │  AI-Powered Analysis & Cleaning          │
│  Visualizations  │    │                                          │
│  & Dashboard     │    └──────────────────────────────────────────┘
└──────────────────┘
```

</div>

---

## 🎯 Core Capabilities

<table>
<tr>
<td width="33%" align="center">

### 🤖 AI-Driven Intelligence
Leverages Gemini API for automated data quality assessment and insights generation

</td>
<td width="33%" align="center">

### 📁 Interactive Data Upload
Seamless file upload widget supporting CSV and Excel formats

</td>
<td width="33%" align="center">

### 🧹 Automated Cleaning
Generates and applies intelligent cleaning code based on data profiling

</td>
</tr>
<tr>
<td width="33%" align="center">

### 📊 Smart Outlier Handling
Uses statistical capping methods to preserve data integrity

</td>
<td width="33%" align="center">

### 🏭 Production-Ready Output
Delivers ML-ready datasets with proper encoding and standardization

</td>
<td width="33%" align="center">

### 📈 Professional Visualizations
Creates publication-quality charts and interactive dashboards

</td>
</tr>
</table>

---

## 🛠️ Installation & Setup

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.8+ |
| Jupyter Notebook | Latest |
| Google Colab | Recommended |
| Gemini API Key | Required |

### Installation

```bash
pip install pandas numpy matplotlib seaborn plotly scikit-learn ipywidgets \
            jsonschema google-generativeai google-auth google-auth-oauthlib \
            openpyxl xlrd jupyterlab
```

---

## 📋 Quick Start

<details open>
<summary><b>Step 1: Environment Setup</b></summary>

```python
# Cell 1: Install all required dependencies
!pip install pandas numpy matplotlib seaborn plotly scikit-learn ipywidgets \
            jsonschema google-generativeai google-auth google-auth-oauthlib \
            openpyxl xlrd jupyterlab --quiet
```

</details>

<details open>
<summary><b>Step 2: Initialize Gemini AI</b></summary>

```python
# Cell 3-4: Configure API and initialize client
from google.colab import userdata
import google.genai as genai

api_key = userdata.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
```

</details>

<details open>
<summary><b>Step 3: Load Your Dataset</b></summary>

```python
# Cell 5: Upload and analyze data
df = upload_dataset()  # Interactive CSV/Excel upload
dataset_summary = generate_dataset_summary(df)  # AI-ready analysis
```

</details>

<details open>
<summary><b>Step 4: AI-Powered Data Cleaning</b></summary>

```python
# Cell 6-7: Automated cleaning analysis
cleaning_prompt = build_cleaning_prompt(dataset_summary)
cleaning_output = ask_gemini_cleaning(cleaning_prompt)
```

</details>

<details open>
<summary><b>Step 5: Generate Visualizations & Dashboard</b></summary>

```python
# Cell 10-14: Create professional charts
viz_code = prompt_gemini(viz_prompt)
exec(viz_code)  # Execute AI-generated visualization code

# Cell 15-17: Build interactive dashboard
dashboard_code = prompt_gemini(dash_prompt)
exec(dashboard_code)
```

</details>

---

## 🎨 Features

### 🔍 Automated Data Analysis

<table>
<tr>
<td>

**Comprehensive Dataset Summary**
- Statistical metrics
- Missing value analysis
- Data type profiling

</td>
<td>

**Intelligent Quality Assessment**
- AI-powered data quality evaluation using Gemini API

</td>
<td>

**Column-wise Analysis**
- Detailed examination of each column
- Numeric and categorical insights

</td>
</tr>
</table>

### 🧹 Smart Data Cleaning

| Feature | Description |
|---------|-------------|
| **Missing Value Detection** | Automatic identification and handling of null values |
| **Outlier Management** | 99th percentile statistical capping for numerical columns |
| **Data Normalization** | Automated column name standardization and value scaling |
| **Categorical Encoding** | One-hot encoding for machine learning readiness |
| **Negative Value Handling** | Automatic conversion of negative values to absolute |

### 📊 Professional Visualization Suite

<div align="center">

| **10 Chart Types** | **Interactive Dashboard** | **Publication Quality** |
|:------------------:|:-------------------------:|:-----------------------:|
| Histograms, bar charts, line charts, scatter plots, box plots, heatmaps, pie charts, correlation matrices | Real-time filtering with KPI cards, multi-select widgets, and auto-updating charts | Professional styling with titles, axis labels, and legends |

</div>

### 🤖 AI-Powered Intelligence

```
┌─────────────────────────────────────────────────────────────┐
│  Gemini Integration                                         │
│  • Advanced AI analysis for data insights                   │
│  • Recommendations generation                               │
├─────────────────────────────────────────────────────────────┤
│  Automated Code Generation                                  │
│  • AI-generated Python code for cleaning                    │
│  • AI-generated visualization code                          │
├─────────────────────────────────────────────────────────────┤
│  Predictive Reporting                                       │
│  • Automated data analysis reports                          │
│  • Business intelligence insights                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Output Deliverables

<div align="center">

| # | Deliverable | Description |
|:-:|-------------|-------------|
| 1️⃣ | **Cleaned Dataset** | ML-ready data with proper encoding and standardization |
| 2️⃣ | **10 Professional Visualizations** | Comprehensive chart suite for data exploration |
| 3️⃣ | **Interactive Dashboard** | Real-time analytics with filters and KPI metrics |
| 4️⃣ | **Predictive Analysis Report** | Automated insights and business recommendations |
| 5️⃣ | **Data Quality Report** | Comprehensive data health assessment |

</div>

---

## 🔧 Technical Architecture

<div align="center">

### Libraries & Frameworks

</div>

<table>
<tr>
<td width="50%">

**Data Processing**
- `pandas`
- `numpy`

**Visualization**
- `matplotlib`
- `seaborn`
- `plotly`

**Machine Learning**
- `scikit-learn`

</td>
<td width="50%">

**AI Integration**
- `google-generativeai`

**Interactive Widgets**
- `ipywidgets`

**Validation**
- `jsonschema`

</td>
</tr>
</table>

<div align="center">

### AI Models Used

| Model | Purpose |
|-------|---------|
| **Gemini 2.5 Pro** | Advanced data analysis and cleaning recommendations |
| **Gemini 2.5 Flash** | Fast visualization code generation |

</div>

---

## 🛡️ Security Features

<div align="center">

| Feature | Implementation |
|---------|----------------|
| ✅ **Secure API Handling** | Gemini API keys stored in Colab secrets |
| ✅ **No Hardcoded Credentials** | Secure authentication practices |
| ✅ **Data Privacy** | Local processing without external data transmission |

</div>

---

## 📈 Use Cases

<table>
<tr>
<td width="50%">

### 💼 Business Intelligence
- Sales analysis
- Performance tracking
- KPI monitoring

### 🔬 Data Science
- Automated ETL pipelines
- Feature engineering
- Model preparation

</td>
<td width="50%">

### 📊 Research Analytics
- Statistical analysis
- Trend identification
- Pattern recognition

### 📋 Reporting Automation
- Automated report generation
- Professional visuals

</td>
</tr>
</table>

---

## 📚 Project Structure

```
datalens-ai/
└── DataLens_AI_v2.ipynb    # Version 2 notebook trained on Google Colab
```

<div align="center">

**Repository contains Version 2 code**

**Version 1 deployed at:** [Hugging Face Space](https://huggingface.co/spaces/adinathjagtap/ai-data-analysis-agent)

</div>

---

## 🚨 Notes

> ⚠️ **Important Information**

- Requires Google Colab environment for optimal performance
- Gemini API key must be configured in Colab secrets
- Supports CSV and Excel file formats
- Automatic dependency installation and version checking

---

## 📄 License

```
MIT License - feel free to use this project for personal or commercial purposes.
```

---

<div align="center">

## 🎓 Google's 5-Day AI Agents Intensive Course

**Capstone Project Submission**

This project was built as a capstone submission for Google's 5-Day AI Agents Intensive Course

[📺 Watch Video Demo](https://youtube.com) • [🚀 Try Live Demo](https://huggingface.co/spaces/adinathjagtap/ai-data-analysis-agent)

---

### Built with ❤️ using Google Gemini AI and Python Data Science Stack

![Built with Gemini](https://img.shields.io/badge/Built%20with-Google%20Gemini%20AI-purple?style=for-the-badge)
![Python Stack](https://img.shields.io/badge/Python-Data%20Science%20Stack-blue?style=for-the-badge)

</div>
