import asyncio
import sys

from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters

from langchain_ollama import ChatOllama
from langchain_mcp_adapters.tools import load_mcp_tools

from langchain.agents import create_agent


async def main():

    server_params = StdioServerParameters(
        command=sys.executable, args=["mcp_server_fastmcp.py"]
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            tools = await load_mcp_tools(session)

            llm = ChatOllama(model="qwen3:1.7b")

            agent = create_agent(model=llm, tools=tools)

            while True:

                try:
                    query = input("\nQuestion: ")
                except EOFError:
                    break

                result = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": query}]}
                )

                print("\nAnswer:")
                print(result)


if __name__ == "__main__":
    asyncio.run(main())
