
from dotenv import load_dotenv
import os

from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo

load_dotenv()

# --- Safety check (will print True if the key is loaded) ---
print("GROQ key loaded:", os.getenv("GROQ_API_KEY") is not None)

# Agent that searches the web (hidden from users)
web_search_agent = Agent(
    name="web search agent",
    role="Search the web for financial information",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[DuckDuckGo()],
    instructions=["Always include the sources/links you used."],
    show_tool_calls=False,   # hide tool call logs
    markdown=True,
)

# Agent that fetches market data (hidden from users)
financial_data_agent = Agent(
    name="financial data agent",
    role="Provide financial data and analysis",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[
        YFinanceTools(
            stock_price=True,
            analyst_recommendations=True,
            stock_fundamentals=True,
            company_news=True,
        ),
    ],
    instructions=["Use concise tables for numeric data."],
    show_tool_calls=False,   # hide tool call logs
    markdown=True,
)

# === Your single public-facing assistant ===
multi_ai_agent = Agent(
    name="Financial Assistant",
    role="I provide clean, concise financial insights with sources.",
    team=[web_search_agent, financial_data_agent],
    model=Groq(id="llama-3.3-70b-versatile"),
    instructions=[
        "You are the final assistant. Do not expose or output any function calls.",
        "Never return <function=...>. Summarize results as natural text only.",
        "You may internally query your sub-agents, but the user should only see clean text.",
        "Always include sources when you use web/news.",
        "Prefer small tables for metrics.",
        "Keep it readable: bullets for details + short summary.",
    ],
    allow_functions=False,   # 🚨 turn off explicit function calls
    show_tool_calls=False,   # hide noisy tool logs
    markdown=True,
)



if __name__ == "__main__":
    # quick local smoke test
    multi_ai_agent.print_response(
        "Summarize analyst recommendations and share the latest news for NVDA",
        stream=True,
    )
