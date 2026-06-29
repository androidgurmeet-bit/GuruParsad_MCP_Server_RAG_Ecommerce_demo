#!/usr/bin/env python
"""Debug script to test the agent directly"""

import asyncio
import sys
import json
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_agent():
    from contextlib import AsyncExitStack
    from langchain.agents import create_agent
    from langchain_core.messages import AIMessage, ToolMessage
    from langchain_mcp_adapters.tools import load_mcp_tools
    from langchain_ollama import ChatOllama
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    
    print("=" * 60)
    print("DEBUG: Agent Test")
    print("=" * 60)
    
    async with AsyncExitStack() as stack:
        print("\n1. Loading MCP tools...")
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["mcp_server_fastmcp.py"],
        )
        read, write = await stack.enter_async_context(stdio_client(server_params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        
        print("2. Getting available tools...")
        tools = await load_mcp_tools(session)
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"     - {tool.name}: {tool.description[:50]}...")
        
        print("\n3. Creating agent...")
        llm = ChatOllama(model="qwen3:1.7b")
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=(
                "You are an ecommerce assistant. When users ask about products, RAM, storage, prices, stock, "
                "specifications, or any product details, ALWAYS use the search_products tool first to find matching "
                "products. Never use rag_query for product searches - use search_products instead. "
                "The search_products tool returns structured data with product IDs and prices. "
                "Keep your final answer concise and user-friendly."
            ),
        )
        
        print("\n4. Running agent with query...")
        query = "Which phones have 8GB RAM and what are their prices?"
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": query}]}
        )
        
        print("\n5. Agent result:")
        messages = result.get("messages", [])
        print(f"   Total messages: {len(messages)}")
        
        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__
            print(f"\n   Message {i}: {msg_type}")
            if isinstance(msg, AIMessage):
                print(f"     Content: {str(msg.content)[:100]}...")
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    print(f"     Tool calls: {msg.tool_calls}")
            elif isinstance(msg, ToolMessage):
                print(f"     Content: {str(msg.content)[:100]}...")
                print(f"     Tool: {msg.name if hasattr(msg, 'name') else 'N/A'}")
            else:
                print(f"     Content: {str(msg.content)[:100]}...")

asyncio.run(test_agent())
