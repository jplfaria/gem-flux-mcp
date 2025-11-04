"""Production Example: Using Argo MCP Client with Recommended Configuration.

This example demonstrates how to use the production-ready configuration
for the Argo MCP client based on Phase 1 testing results.

Usage:
    python production_example.py
"""

import asyncio
from gem_flux_mcp.server import initialize_server, create_server
from gem_flux_mcp.argo.client import ArgoMCPClient
from production_config import get_production_config, get_default_system_prompt, print_deployment_info


async def main():
    """Run production example with Claude Sonnet 4."""

    # Print deployment info
    print_deployment_info("claude-sonnet-4")

    # Step 1: Initialize MCP server with tools
    print("Step 1: Initializing MCP server...")
    initialize_server()
    mcp_server = create_server()
    print("✓ MCP server initialized\n")

    # Step 2: Get production configuration
    print("Step 2: Loading production configuration...")
    config = get_production_config(
        model_name="claude-sonnet-4",
        custom_system_prompt=get_default_system_prompt()
    )
    print(f"✓ Configuration loaded for {config['model']}\n")

    # Step 3: Create Argo client with production config
    print("Step 3: Creating Argo MCP client...")
    client = ArgoMCPClient(
        mcp_server=mcp_server,
        argo_base_url="http://localhost:8000/v1",
        argo_api_key="not-needed",
        **config  # Unpack production config
    )
    print("✓ Client created\n")

    # Step 4: Initialize client (load tools)
    print("Step 4: Initializing client (loading tools)...")
    await client.initialize()
    print(f"✓ Loaded {len(client.get_available_tools())} tools\n")

    # Step 5: Run example queries
    print("="*80)
    print("EXAMPLE QUERIES")
    print("="*80)

    # Example 1: Simple compound search
    print("\n[Example 1] Searching for glucose...")
    response = await client.chat(
        "What is the ModelSEED ID for glucose?",
        reset_history=True
    )
    print(f"Response: {response}\n")

    # Example 2: Build and analyze a model
    print("\n[Example 2] Building a small test model...")
    response = await client.chat(
        "Build a model named 'production_test' with these sequences: "
        "MKKYTCTVCGYIYNPEDGDPDNGVNPGTDFKDIPDDWVCPLCGVGKDQFEEVEE",
        reset_history=True
    )
    print(f"Response: {response[:200]}...\n")

    # Example 3: List available tools
    print("\n[Example 3] Available tools:")
    tools = client.get_available_tools()
    for i, tool in enumerate(tools, 1):
        print(f"  {i}. {tool}")

    print("\n" + "="*80)
    print("Production example completed successfully!")
    print("="*80)


async def run_with_fallback():
    """Example with fallback strategy: Claude Sonnet 4 → GPT-4o."""

    print("\n" + "="*80)
    print("FALLBACK STRATEGY EXAMPLE")
    print("="*80)

    # Initialize server
    initialize_server()
    mcp_server = create_server()

    # Try primary model (Claude Sonnet 4)
    try:
        print("\nTrying primary model: Claude Sonnet 4...")
        config = get_production_config("claude-sonnet-4")
        client = ArgoMCPClient(
            mcp_server=mcp_server,
            argo_base_url="http://localhost:8000/v1",
            **config
        )
        await client.initialize()
        print("✓ Primary model available\n")

        response = await client.chat("What is glucose?", reset_history=True)
        print(f"Response: {response}\n")

    except Exception as e:
        print(f"✗ Primary model failed: {e}")
        print("\nFalling back to secondary model: GPT-4o...")

        # Fallback to GPT-4o
        config = get_production_config("gpt-4o")
        client = ArgoMCPClient(
            mcp_server=mcp_server,
            argo_base_url="http://localhost:8000/v1",
            **config
        )
        await client.initialize()
        print("✓ Secondary model available\n")

        response = await client.chat("What is glucose?", reset_history=True)
        print(f"Response: {response}\n")


async def interactive_mode():
    """Interactive mode for testing queries."""

    print("\n" + "="*80)
    print("INTERACTIVE MODE")
    print("="*80)
    print("Type 'quit' to exit\n")

    # Initialize
    initialize_server()
    mcp_server = create_server()

    config = get_production_config("claude-sonnet-4")
    client = ArgoMCPClient(
        mcp_server=mcp_server,
        argo_base_url="http://localhost:8000/v1",
        **config
    )
    await client.initialize()

    print(f"✓ Ready with {config['model']}\n")

    # Interactive loop
    while True:
        try:
            user_input = input("Query> ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if not user_input:
                continue

            response = await client.chat(user_input)
            print(f"\n{response}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    import sys

    # Check for interactive mode flag
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_mode())
    elif len(sys.argv) > 1 and sys.argv[1] == "fallback":
        asyncio.run(run_with_fallback())
    else:
        asyncio.run(main())
