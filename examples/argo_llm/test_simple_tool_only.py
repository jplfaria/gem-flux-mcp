#!/usr/bin/env python3
"""Test Argo LLM with a single simple tool to diagnose the 400 error."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gem_flux_mcp.server import initialize_server, create_server
from gem_flux_mcp.argo.client import ArgoMCPClient
from gem_flux_mcp.logging import get_logger

logger = get_logger(__name__)


async def main():
    """Test with limited tools."""
    print("=" * 60)
    print("Diagnostic: Testing Argo with Limited Tools")
    print("=" * 60)
    print()

    # Initialize MCP server
    print("1. Initializing MCP server...")
    try:
        initialize_server()
        mcp_server = create_server()
        print("   ✓ MCP server initialized")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return

    print()

    # Create Argo client
    print("2. Creating Argo client...")
    client = ArgoMCPClient(
        mcp_server=mcp_server,
        argo_base_url="http://localhost:8000/v1",
        model="argo:gpt-4o"
    )
    print("   ✓ Client created")
    print()

    # Initialize and load tools
    print("3. Loading MCP tools...")
    await client.initialize()
    all_tools = client.get_available_tools()
    print(f"   ✓ Loaded {len(all_tools)} tools total")
    print(f"   Tools: {', '.join(all_tools)}")
    print()

    # Show converted tool schemas
    print("4. Examining converted tools...")
    for i, tool in enumerate(client.openai_tools[:3]):  # Show first 3
        print(f"\n   Tool {i+1}: {tool['function']['name']}")
        print(f"   Description: {tool['function']['description'][:100]}...")
        params = tool['function']['parameters']
        print(f"   Parameters: {list(params['properties'].keys())}")
        print(f"   Required: {params['required']}")
        print(f"   JSON size: {len(json.dumps(tool))} bytes")

    print(f"\n   Total tools JSON size: {len(json.dumps(client.openai_tools))} bytes")
    print()

    # Test 1: Try with ALL tools (reproduce error)
    print("=" * 60)
    print("Test 1: With ALL 11 tools (expect 400 error)")
    print("=" * 60)
    try:
        response = await client.chat(
            "What is compound cpd00027?",
            reset_history=True
        )
        print(f"✓ Success: {response}")
    except Exception as e:
        print(f"✗ Error (as expected): {str(e)[:200]}")

    print()

    # Test 2: Try with just compound lookup tools (reduced set)
    print("=" * 60)
    print("Test 2: With Just 2 Simple Tools")
    print("=" * 60)

    # Manually filter to just 2 simple tools
    simple_tool_names = ["get_compound_name", "get_reaction_name"]
    original_tools = client.openai_tools
    client.openai_tools = [
        tool for tool in original_tools
        if tool['function']['name'] in simple_tool_names
    ]

    print(f"   Using only: {[t['function']['name'] for t in client.openai_tools]}")
    print(f"   Reduced JSON size: {len(json.dumps(client.openai_tools))} bytes")
    print()

    try:
        response = await client.chat(
            "What is the name of compound cpd00027?",
            reset_history=True
        )
        print(f"✓ Success: {response}")
    except Exception as e:
        print(f"✗ Error: {str(e)[:200]}")

    print()

    # Test 3: Try with NO tools (just chat)
    print("=" * 60)
    print("Test 3: With NO Tools (Just Chat)")
    print("=" * 60)

    client.openai_tools = []

    try:
        response = await client.chat(
            "What is 2+2?",
            reset_history=True
        )
        print(f"✓ Success: {response}")
    except Exception as e:
        print(f"✗ Error: {str(e)[:200]}")

    print()
    print("=" * 60)
    print("Diagnostic Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
