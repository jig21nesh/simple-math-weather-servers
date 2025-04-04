from mcp.server.fastmcp import FastMCP
import sys

mcp = FastMCP("Math")

@mcp.tool(description="Add two numbers. The request should contain two numbers and output the sum.")
def add(a: int, b: int) -> int:
    print(f"DEBUG: Add method was called with a={a} and b={b}", file=sys.stderr)
    return a + b

@mcp.tool(description="Multiply two numbers")
def multiply(a: int, b: int) -> int:
    print(f"DEBUG: Multiply method was called with a={a} and b={b}", file=sys.stderr)
    return a * b

if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    except Exception as e:
        print(f"[ERROR] math_server exception: {e}", flush=True)