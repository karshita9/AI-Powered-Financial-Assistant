# 📊 AI-Powered Financial Assistant

An AI-powered web app that provides **financial insights**, **stock analysis**, and **recent news summaries** using multiple AI agents.



## Features

- Fetches **stock data** using [yfinance](https://pypi.org/project/yfinance/)
- Displays **candlestick charts** and **SMA20 trend lines** with [Plotly](https://plotly.com/python/)
- Provides **AI-powered summaries** of analyst recommendations and news
- Modular architecture with **multiple AI agents** for market data and web search
- Built with [Streamlit](https://streamlit.io/) for an interactive web UI



## Requirements

Install the dependencies using:

```bash
pip install -r requirements.txt

## 

1.Clone the repo:

git clone https://github.com/karshita9/AI-Powered-Financial-Assistant.git
cd AI-Powered-Financial-Assistant

2.Create a .env file with your API keys (do not push this file):

GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
PHI_API_KEY=your_phiapi_key

3.Run the app locally:

streamlit run app.py

4.Ask AI questions about any stock and see charts, trends, and summaries.

Folder Structure
AI-Powered-Financial-Assistant/
├─ app.py
├─ financial_agent.py
├─ requirements.txt
├─ .gitignore
└─ README.md

## License

This project is **for learning and personal use**. Do not share API keys publicly.
