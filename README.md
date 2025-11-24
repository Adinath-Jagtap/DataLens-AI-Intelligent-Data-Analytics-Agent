# 📊 DataLens AI - Intelligent Data Analytics Agent

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange)
![Gemini](https://img.shields.io/badge/Google-Gemini%20AI-purple)
![License](https://img.shields.io/badge/License-MIT-green)

An autonomous AI-powered data analytics system that transforms raw datasets (CSV/Excel) into professional visualizations and interactive dashboards. Built with Google's Gemini API, this agent intelligently analyzes data, performs automated cleaning, and generates comprehensive visual insights.

## 🚀 Workflow Pipeline

**Setup Environment** → **Initialize Gemini AI** → **Load Data** → **AI-Powered Analysis & Cleaning** → **Generate Visualizations & Dashboard**

## 🎯 Core Capabilities

- **🤖 AI-Driven Intelligence**: Leverages Gemini API for automated data quality assessment and insights generation
- **📁 Interactive Data Upload**: Seamless file upload widget supporting CSV and Excel formats
- **🧹 Automated Cleaning**: Generates and applies intelligent cleaning code based on data profiling
- **📊 Smart Outlier Handling**: Uses statistical capping methods to preserve data integrity
- **🏭 Production-Ready Output**: Delivers ML-ready datasets with proper encoding and standardization
- **📈 Professional Visualizations**: Creates publication-quality charts and interactive dashboards

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Jupyter Notebook/Google Colab
- Google Gemini API Key

### Installation
```bash
# Install required dependencies
pip install pandas numpy matplotlib seaborn plotly scikit-learn ipywidgets jsonschema \
            google-generativeai google-auth google-auth-oauthlib openpyxl xlrd jupyterlab
```

## 📋 Quick Start

### 1. Environment Setup
```python
# Cell 1: Install all required dependencies
!pip install pandas numpy matplotlib seaborn plotly scikit-learn ipywidgets jsonschema \
            google-generativeai google-auth google-auth-oauthlib openpyxl xlrd jupyterlab --quiet
```

### 2. Initialize Gemini AI
```python
# Cell 3-4: Configure API and initialize client
from google.colab import userdata
import google.genai as genai

api_key = userdata.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
```

### 3. Load Your Dataset
```python
# Cell 5: Upload and analyze data
df = upload_dataset()  # Interactive CSV/Excel upload
dataset_summary = generate_dataset_summary(df)  # AI-ready analysis
```

### 4. AI-Powered Data Cleaning
```python
# Cell 6-7: Automated cleaning analysis
cleaning_prompt = build_cleaning_prompt(dataset_summary)
cleaning_output = ask_gemini_cleaning(cleaning_prompt)
```

### 5. Generate Visualizations & Dashboard
```python
# Cell 10-14: Create professional charts
viz_code = prompt_gemini(viz_prompt)
exec(viz_code)  # Execute AI-generated visualization code

# Cell 15-17: Build interactive dashboard
dashboard_code = prompt_gemini(dash_prompt)
exec(dashboard_code)
```

## 🎨 Features

### Automated Data Analysis
- **Comprehensive Dataset Summary**: Statistical metrics, missing value analysis, data type profiling
- **Intelligent Quality Assessment**: AI-powered data quality evaluation using Gemini API
- **Column-wise Analysis**: Detailed examination of each column with numeric and categorical insights

### Smart Data Cleaning
- **Missing Value Detection**: Automatic identification and handling of null values
- **Outlier Management**: 99th percentile statistical capping for numerical columns
- **Data Normalization**: Automated column name standardization and value scaling
- **Categorical Encoding**: One-hot encoding for machine learning readiness
- **Negative Value Handling**: Automatic conversion of negative values to absolute

### Professional Visualization Suite
- **10 Chart Types**: Histograms, bar charts, line charts, scatter plots, box plots, heatmaps, pie charts, correlation matrices
- **Interactive Dashboard**: Real-time filtering with KPI cards, multi-select widgets, and auto-updating charts
- **Publication Quality**: Professional styling with titles, axis labels, and legends

### AI-Powered Intelligence
- **Gemini Integration**: Advanced AI analysis for data insights and recommendations
- **Automated Code Generation**: AI-generated Python code for cleaning and visualization
- **Predictive Reporting**: Automated data analysis reports with business intelligence insights

## 📊 Output Deliverables

1. **Cleaned Dataset**: ML-ready data with proper encoding and standardization
2. **10 Professional Visualizations**: Comprehensive chart suite for data exploration
3. **Interactive Dashboard**: Real-time analytics with filters and KPI metrics
4. **Predictive Analysis Report**: Automated insights and business recommendations
5. **Data Quality Report**: Comprehensive data health assessment

## 🔧 Technical Architecture

### Libraries & Frameworks
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib, seaborn, plotly
- **Machine Learning**: scikit-learn
- **AI Integration**: google-generativeai
- **Interactive Widgets**: ipywidgets
- **Validation**: jsonschema

### AI Models Used
- **Gemini 2.5 Pro**: Advanced data analysis and cleaning recommendations
- **Gemini 2.5 Flash**: Fast visualization code generation

## 🛡️ Security Features

- **Secure API Handling**: Gemini API keys stored in Colab secrets
- **No Hardcoded Credentials**: Secure authentication practices
- **Data Privacy**: Local processing without external data transmission

## 📈 Use Cases

- **Business Intelligence**: Sales analysis, performance tracking, KPI monitoring
- **Data Science**: Automated ETL pipelines, feature engineering, model preparation
- **Research Analytics**: Statistical analysis, trend identification, pattern recognition
- **Reporting Automation**: Automated report generation with professional visuals

## 🚨 Notes

- Requires Google Colab environment for optimal performance
- Gemini API key must be configured in Colab secrets
- Supports CSV and Excel file formats
- Automatic dependency installation and version checking

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

---

**Built with ❤️ using Google Gemini AI and Python Data Science Stack**
