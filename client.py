import asyncio
import os
import requests
from dotenv import load_dotenv
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
import json
import logging


#logging.basicConfig(level=logging.DEBUG)
#callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])


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
    #callback_manager=callback_manager,
    #verbose=True
)

# -- Path Setup --
script_dir = os.path.dirname(os.path.abspath(__file__))
math_server_path = os.path.join(script_dir, "math_server.py")
# Uncomment if you have an SSE server for weather or similar.
weather_server_url = "http://localhost:8000/sse"

# -- Ollama check helper --
def check_ollama_running(base_url: str = "http://127.0.0.1", port: int = 11434) -> bool:
    url = f"{base_url}:{port}/api/tags"
    print(f"DEBUG: Checking Ollama at URL: {url}")
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        print(f"DEBUG: Ollama is running and accessible at {url}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Ollama check failed: {e}")
        return False

async def run_app(user_question):
    print("DEBUG: Entering run_app with user_question =", user_question)
    print(f"DEBUG: Path for the math server {math_server_path}")
    print("DEBUG: About to enter MultiServerMCPClient context...")

    if not check_ollama_running():
        print("ERROR: Ollama is not running. Exiting.")
        return "Ollama is not running."

    try:
        print("DEBUG: Creating MultiServerMCPClient instance...")
        async with MultiServerMCPClient({
            # If you have an SSE server, you can add its configuration here.
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
            print("DEBUG: Successfully entered MultiServerMCPClient context")
            # Use the tools returned by the MCP server
            tools = client.get_tools()
            
            agent = create_react_agent(model, tools)
            print("DEBUG: Created ReAct agent. Invoking...")
            try:
                response = await asyncio.wait_for(agent.ainvoke({"messages": [HumanMessage(content=user_question)]}), timeout=60)
            except asyncio.TimeoutError:
                print("ERROR: Agent invocation timed out after 60 seconds.")
                return "Agent invocation timed out."
            
            print("DEBUG: Agent response received.")
            final_message = response["messages"][-1]
            print("DEBUG: Final response content:", final_message.content)
            return final_message.content

    except Exception as e:
        print("ERROR in run_app:", e)
        return "Encountered an error."

if __name__ == "__main__":
    user_question = "What's (3 + 5) x 12?"
    print("DEBUG: About to run run_app...")
    result = asyncio.run(run_app(user_question=user_question))
    print("DEBUG: run_app completed. Response:")
    print(result)