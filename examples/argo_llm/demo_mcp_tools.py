#!/usr/bin/env python3
"""Demo of Argo LLM integration with real MCP metabolic modeling tools.

This script demonstrates natural language interaction with the full Gem-Flux
MCP server, including database lookups, media creation, and model building.

Prerequisites:
- Argo-proxy running on localhost:8000
- ModelSEED database downloaded to ./data/database/
- ModelSEED templates downloaded to ./data/templates/

Run with: uv run python examples/argo_llm/demo_mcp_tools.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gem_flux_mcp.server import initialize_server, create_server
from gem_flux_mcp.argo.client import ArgoMCPClient
from gem_flux_mcp.logging import get_logger

logger = get_logger(__name__)


async def test_database_lookups(client: ArgoMCPClient):
    """Test natural language database queries."""
    print("=" * 60)
    print("Test 1: Database Lookups via Natural Language")
    print("=" * 60)
    print()

    questions = [
        "What is the molecular formula of glucose (compound cpd00027)?",
        "What compounds contain the word 'glucose' in their name?",
        "Tell me about the reaction rxn00001",
    ]

    for question in questions:
        print(f"User: {question}")
        response = await client.chat(question)
        print(f"Assistant: {response}")
        print()


async def test_media_creation(client: ArgoMCPClient):
    """Test media creation via natural language."""
    print("=" * 60)
    print("Test 2: Media Creation via Natural Language")
    print("=" * 60)
    print()

    question = (
        "Create a minimal growth media called 'test_media' with glucose (cpd00027), "
        "water (cpd00001), and oxygen (cpd00007)"
    )

    print(f"User: {question}")
    response = await client.chat(question)
    print(f"Assistant: {response}")
    print()


async def test_list_operations(client: ArgoMCPClient):
    """Test listing operations via natural language."""
    print("=" * 60)
    print("Test 3: Listing Available Resources")
    print("=" * 60)
    print()

    questions = [
        "What media compositions are available?",
        "List the models I've created",
    ]

    for question in questions:
        print(f"User: {question}")
        response = await client.chat(question)
        print(f"Assistant: {response}")
        print()


async def test_conversation_context(client: ArgoMCPClient):
    """Test multi-turn conversation with context."""
    print("=" * 60)
    print("Test 4: Multi-Turn Conversation with Context")
    print("=" * 60)
    print()

    # Reset conversation for clean test
    client.reset_conversation()

    questions = [
        "What is the formula for cpd00027?",
        "What is that compound's mass?",  # Uses context from previous
        "Search for reactions involving that compound",  # Uses context again
    ]

    for question in questions:
        print(f"User: {question}")
        response = await client.chat(question)
        print(f"Assistant: {response}")
        print()


async def main():
    """Main entry point."""
    print("=" * 60)
    print("Argo LLM + MCP Tools Integration Demo")
    print("=" * 60)
    print()

    # Step 1: Initialize MCP server
    print("1. Initializing MCP server...")
    try:
        initialize_server()
        mcp_server = create_server()
        print("   ✓ MCP server initialized")
    except Exception as e:
        print(f"   ✗ MCP server initialization failed: {e}")
        print("\n   Make sure ModelSEED database is downloaded:")
        print("   - data/database/compounds.tsv")
        print("   - data/database/reactions.tsv")
        print("   - data/templates/*.json")
        return

    print()

    # Step 2: Create Argo client
    print("2. Creating Argo MCP client...")
    try:
        client = ArgoMCPClient(
            mcp_server=mcp_server,
            argo_base_url="http://localhost:8000/v1",
            model="argo:gpt-4o"
        )
        print("   ✓ Client created")
    except Exception as e:
        print(f"   ✗ Client creation failed: {e}")
        print("\n   Make sure argo-proxy is running:")
        print("   $ argo-proxy")
        return

    print()

    # Step 3: Initialize client (load tools)
    print("3. Loading and converting MCP tools...")
    try:
        await client.initialize()
        tools = client.get_available_tools()
        print(f"   ✓ Loaded {len(tools)} tools")
        print(f"   Available tools: {', '.join(tools[:5])}...")
    except Exception as e:
        print(f"   ✗ Tool initialization failed: {e}")
        return

    print()

    # Step 4: Run tests
    print("4. Running natural language tests...")
    print()

    try:
        # Test 1: Database lookups
        await test_database_lookups(client)

        # Test 2: Media creation
        await test_media_creation(client)

        # Test 3: List operations
        await test_list_operations(client)

        # Test 4: Multi-turn conversation
        await test_conversation_context(client)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ Test error: {e}")
        return

    # Summary
    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print()
    print("Key Capabilities Demonstrated:")
    print("✓ Natural language database queries")
    print("✓ Tool calling with real MCP tools")
    print("✓ Media creation via natural language")
    print("✓ Listing operations")
    print("✓ Multi-turn conversation with context")
    print()
    print("Next Steps:")
    print("- Try more complex queries")
    print("- Test model building workflows")
    print("- Experiment with gapfilling via natural language")


if __name__ == "__main__":
    asyncio.run(main())
