import asyncio
import os
import requests
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

load_dotenv()

# -- Proxy Config Fix --
os.environ["no_proxy"] = "localhost,127.0.0.1"
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("https_proxy", None)

# -- ChatOllama config --
model = ChatOllama(
    model="llama3.2:3b-instruct-fp16",
    temperature=0.0,
    max_new_tokens=500,
    base_url="http://127.0.0.1:11434",
)

# -- Path Setup --
script_dir = os.path.dirname(os.path.abspath(__file__))
math_server_path = os.path.join(script_dir, "math_server.py")
weather_server_url = "http://localhost:8000/sse"

# -- Ollama check helper --
def check_ollama_running(base_url: str = "http://127.0.0.1", port: int = 11434) -> bool:
    url = f"{base_url}:{port}/api/tags"
    #print(f"DEBUG: Checking Ollama at URL: {url}")
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        #print(f"DEBUG: Ollama is running and accessible at {url}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Ollama check failed: {e}")
        return False

async def run_app(user_question):
    #print("\n======================================================")
    #print("DEBUG: Entering run_app with user_question =", user_question)
    #print("======================================================")

    if not check_ollama_running():
        #print("ERROR: Ollama is not running. Exiting.")
        return "Ollama is not running."

    try:
        #print("DEBUG: Creating MultiServerMCPClient instance...")
        async with MultiServerMCPClient({
            "weather": {
                "url": weather_server_url,
                "transport": "sse",
            },
            "math": {
                "command": "python",
                "args": ["-u", math_server_path],
                "transport": "stdio",
            },
        }) as client:
            #print("DEBUG: Successfully entered MultiServerMCPClient context")
            tools = client.get_tools()
            #print("DEBUG: Registered tools:", [tool.name for tool in tools])

            agent = create_react_agent(model, tools)
            #print("DEBUG: Created ReAct agent. Invoking...")

            try:
                response = await asyncio.wait_for(
                    agent.ainvoke({"messages": [HumanMessage(content=user_question)]}),
                    timeout=60
                )
            except asyncio.TimeoutError:
                print("ERROR: Agent invocation timed out.")
                return "Agent invocation timed out."

            final_message = response["messages"][-1]
            print("✅ Final response:", final_message.content)
            return final_message.content

    except Exception as e:
        print("ERROR in run_app:", e)
        return "Encountered an error."



async def run_all_questions(user_questions):
    for question in user_questions:
        print(f"\n🧠 Asking: {question}")
        result = await run_app(user_question=question)
        print("DEBUG: run_app completed. Response:")
        print(result)
        await asyncio.sleep(1)

# -- Entry Point --
if __name__ == "__main__":
    user_questions = [
        "What's (3 + 5) x 12?",                            # should invoke add & multiply
        "Can you add 20 and 15 for me?",                   # should invoke add
        "Could you multiply 7 by 8?",                      # should invoke multiply
        "What's the weather like in Melbourne today?",     # should invoke get_forecast (requires lat/lon)
        "Are there any weather warnings in NSW?",          # should invoke get_alerts
        "What's the forecast looking like for Brisbane?",  # another get_forecast
        "How much is 144 divided by 12?",                  # should NOT match any tool, fallback to LLM
    ]   

    asyncio.run(run_all_questions(user_questions))