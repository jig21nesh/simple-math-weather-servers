# 🧠 MCP + LangChain + Ollama Tool Agent

This project demonstrates building a ReAct-style agent using 
[LangChain](https://github.com/langchain-ai/langchain), 
[LangGraph](https://github.com/langchain-ai/langgraph), and 
[MCP](https://github.com/langchain-ai/mcp), paired with a locally running 
[Ollama](https://ollama.com) LLM.

The agent invokes tools like `add` and `multiply` via a subprocess MCP server (`math_server.py`) using `stdio` transport.

---

## ✅ Features

- **MultiServerMCPClient Integration:** Launch and communicate with a math server using the MCP protocol.
- **ReAct Agent:** Use a ReAct agent to decide when to call tools based on user queries.
- **Tool Invocation:** Demonstrates tool calls (e.g., `add` and `multiply`) via a math server.
- **Verbose Logging & Callbacks:** Uses LangChain's callback manager to stream intermediate outputs and chain-of-thought.


---

## 📦 Requirements

- Python 3.9+
- [`ollama`](https://ollama.com) installed and running
- Python dependencies:

```bash

pip install -r requirements.txt

```

## 🛠 Troubleshooting Journey Summary

Below is a concise summary of the debugging path we took to get the ReAct agent and MCP tool integration working:

- **Initial Symptom:**
  - Agent appeared to hang during `ainvoke()`, with no tools executing or response returned.

- **Custom `MultiServerMCPClient` Investigation:**
  - Built a subclass to monitor subprocess readiness via `MATH_SERVER_READY`.
  - Realized manual buffering and reading from `stderr` was error-prone or ineffective.

- **Print Stream Confusion:**
  - MCP server was using `stdout`, while the custom client was waiting for readiness on `stderr`.
  - Fix: Added `-u` for unbuffered mode and printed readiness message directly to `stdout`.

- **Tool Registration Debugging:**
  - Discovered that `client.get_tools()` was returning an empty list.
  - Resolved by ensuring the MCP server correctly registered functions with `@mcp.tool(description="...")`.

- **Code Execution Deadlocks:**
  - Found that manually calling `get_tools()` outside of the async context led to unexpected hangs.
  - Fix: Used `async with MultiServerMCPClient(...)` context block and relied on built-in async lifecycle.

- **Server Command Fix:**
  - Originally used just `["math_server.py"]`; updated to `["-u", "math_server.py"]` for unbuffered I/O.

- **Simplification for Sanity Checks:**
  - Removed SSE/weather server from the config to reduce variables while testing just the math server.

- **Callback and Timeout Enhancements:**
  - Enabled `StreamingStdOutCallbackHandler` to view thought/tool/output progression live.
  - Wrapped `agent.ainvoke()` in `asyncio.wait_for()` to surface timeouts clearly.

- **Environment Fixes:**
  - Cleared proxy-related environment variables to ensure Ollama wasn't blocked by corporate proxies.

- **Successful Outcome:**
  - Agent correctly invoked `add` and `multiply` tools from `math_server.py` and returned accurate final answers.


---

## 📚 References

Here are key resources and documentation links that helped during development and debugging:

- **LangChain MCP Overview**  
  https://github.com/langchain-ai/langchain/tree/master/libs/mcp

- **LangChain MCP Adapters (Tool Loading)**  
  https://github.com/langchain-ai/langchain/tree/master/libs/mcp-adapters

- **LangGraph `create_react_agent` Docs**  
  https://docs.langchain.com/langgraph/agents/react/

- **LangChain Agents & Tool Usage**  
  https://docs.langchain.com/docs/components/agents/agent-types/react

- **Ollama REST API Docs**  
  https://github.com/ollama/ollama/blob/main/docs/api.md

- **Other Git Repo**
  https://github.com/tam159/generative_ai/blob/981decfa995ac50350f9f3b058639fd440013d1b/llm/notebook/mcp/mcp_adapters_client.ipynb
  https://github.com/dimz119/learn-langchain/blob/a8466a6945ba583009f55b3dcb2d9b4e5d936e2c/mcp/math_server.py
  https://medium.com/the-ai-forum/understanding-model-context-protocol-a-deep-dive-into-multi-server-langchain-integration-3d038247e0bd
  
