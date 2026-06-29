#!/usr/bin/env python
"""Test script to check what tools are exported by the MCP server"""

import asyncio
import sys
import json
from pathlib import Path

async def test_mcp_tools():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    
    print("=" * 60)
    print("DEBUG: MCP Tools Test")
    print("=" * 60)
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server_fastmcp.py"],
    )
    
    print("\n1. Starting MCP server...")
    read, write = await stdio_client(server_params).__aenter__()
    
    try:
        print("2. Creating session...")
        session = await ClientSession(read, write).__aenter__()
        
        try:
            print("3. Initializing...")
            await session.initialize()
            
            print("\n4. Available tools:")
            result = await session.list_tools()
            print(f"   Found {len(result.tools)} tools:")
            for tool in result.tools:
                print(f"     - {tool.name}: {tool.description}")
                if tool.inputSchema:
                    print(f"       Schema: {json.dumps(tool.inputSchema, indent=8)[:200]}...")
            
            print("\n5. Testing search_products tool...")
            if any(t.name == 'search_products' for t in result.tools):
                result = await session.call_tool('search_products', {'query': '8GB RAM'})
                print(f"   Result type: {type(result)}")
                print(f"   Result content: {str(result)[:300]}...")
            else:
                print("   search_products tool not found!")
                
        finally:
            await session.__aexit__(None, None, None)
    finally:
        await stdio_client(server_params).__aexit__(None, None, None)

asyncio.run(test_mcp_tools())
