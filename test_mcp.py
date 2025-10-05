#!/usr/bin/env python
"""Test MCP server protocol."""

import asyncio
import sys

async def test_server():
    # Import the server
    sys.path.insert(0, '/Users/apolak/agents/selenium-recorder-mcp')
    from src.server import app, handle_list_tools

    # Test list_tools directly
    print("Testing list_tools handler...")
    try:
        tools = await handle_list_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description[:50]}...")

        # Check Server object attributes
        print(f"\n🔍 Server object type: {type(app)}")
        print(f"🔍 Server attributes: {[attr for attr in dir(app) if not attr.startswith('_')]}")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)
