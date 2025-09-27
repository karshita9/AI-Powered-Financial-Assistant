import openai
from phi.agent import Agent
import phi.api
from phi.model.openai import OpenAIChat
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
from dotenv import load_dotenv
from phi.model.groq import Groq
from phi.playground import Playground, serve_playground_app
import os

# Load environment variables from .env file
load_dotenv()
phi.api.key = os.getenv("OPENAI_API_KEY")  

# Web search agent to find financial information
web_search_agent = Agent(
    name="web search agent",
    role="Search the web for financial information",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[DuckDuckGo()],
    instructions=["Always include sources in your answers."],  
    show_tools_calls=True,
    markdown=True,
)

# Financial data agent to provide stock prices and financial metrics
financial_data_agent = Agent(
    name="financial data agent",
    role="Provide financial data and analysis",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[
        YFinanceTools(
            stock_price=True, 
            analyst_recommendations=True, 
            stock_fundamentals=True, 
            company_news=True
        ),
    ],
    instructions=["Use tables to display data."],  # ✅ put in list
    show_tools_calls=True,
    markdown=True,
)
multi_ai_agent = Agent(
    name="Financial Assistant",   
    role="Provide financial insights and web-based financial news.",
    team=[web_search_agent, financial_data_agent],
    model=Groq(id="llama-3.3-70b-versatile"),
    instructions=[
        "Always include sources",
        "Use tables to display data",
        "Never mention multiple agents, answer as one assistant."
    ],
    show_tool_calls=True,
    markdown=True,
)


# Create Playground app with both agents
app = Playground(agents=[multi_ai_agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("playground:app", reload=True)

