"""
mcp中异步调用的模式
"""
import asyncio
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

async def run_mcp_client():
    # 初始化MCP客户端
    mcp_client = MultiServerMCPClient(
        {
            "tushareMcp": {
                "url": "https://api.tushare.pro/mcp/?token=9ecb767ab40b5023b62abd2ac9a272c93e9bf6f4c9a7bbdf51e22163",
                "transport": "http"
            }
        }
    )

    tools = await mcp_client.get_tools()
    for tool in tools:
        print(f"Tool Name: {tool.name}, Description: {tool.description}")

    agent = create_agent(
        model=init_chat_model(
            model="ollama:qwen2.5:7b-instruct-q4_K_M",
            temperature=0.7,
        ),
        tools=tools
    )

    # 使用agent进行异步调用
    response = await agent.ainvoke({"messages": [{"role": "user", "content": "获取上证指数的最新行情。"}]})

    print("Agent Response:", response)

if __name__ == "__main__":
    asyncio.run(run_mcp_client())

