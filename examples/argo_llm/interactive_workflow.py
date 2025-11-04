#!/usr/bin/env python3
"""Interactive Natural Language Workflow with Argo LLM.

This script demonstrates building and gapfilling a metabolic model using
natural language commands via Argo LLM integration.

Prerequisites:
- Argo-proxy running on localhost:8000
- ModelSEED database downloaded to ./data/database/
- A FASTA file with protein sequences (we'll use example data)

Usage:
    uv run python examples/argo_llm/interactive_workflow.py

Example conversation:
    User: "Build a model from the E. coli genome in data/genomes/ecoli.faa"
    LLM: [calls build_model tool with protein sequences from file]
    User: "Gapfill the model to grow on glucose minimal media"
    LLM: [calls gapfill_model tool]
    User: "Run FBA and tell me the growth rate"
    LLM: [calls run_fba tool and reports results]
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gem_flux_mcp.server import initialize_server, create_server
from gem_flux_mcp.argo.client import ArgoMCPClient
from gem_flux_mcp.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Available models in Argo
MODELS = {
    "gpt-4o": "argo:gpt-4o",                      # Fast, good for most tasks
    "gpt-5": "argo:gpt-5",                        # GPT-5 (latest reasoning model)
    "claude-sonnet-4": "argo:claude-sonnet-4",    # Claude Sonnet 4
}

# Working directory for file operations
WORKING_DIR = Path.cwd()


# =============================================================================
# Helper Functions
# =============================================================================


def print_banner(title: str):
    """Print a formatted banner."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}\n")


async def setup_client(model_name: str = "gpt-4o"):
    """Initialize MCP server and Argo client."""
    print_section("Initializing MCP Server & Argo Client")

    # Initialize MCP server
    print("1. Initializing MCP server...")
    try:
        initialize_server()
        mcp_server = create_server()
        print("   ✓ MCP server initialized")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        print("\n   Make sure ModelSEED database is downloaded:")
        print("   - data/database/compounds.tsv")
        print("   - data/database/reactions.tsv")
        print("   - data/templates/*.json")
        return None, None

    # Create Argo client
    print(f"\n2. Creating Argo client (model: {model_name})...")
    model = MODELS.get(model_name, MODELS["gpt-4o"])

    try:
        client = ArgoMCPClient(
            mcp_server=mcp_server,
            argo_base_url="http://localhost:8000/v1",
            model=model,
            max_tools_per_call=6  # Limit to avoid payload issues
        )
        print("   ✓ Client created")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        print("\n   Make sure argo-proxy is running:")
        print("   $ argo-proxy")
        return None, None

    # Initialize client (load tools)
    print("\n3. Loading MCP tools...")
    try:
        await client.initialize()
        tools = client.get_available_tools()
        print(f"   ✓ Loaded {len(tools)} tools")
        print(f"   Tools: {', '.join(tools)}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return None, None

    print(f"\n✓ Setup complete! Using model: {model}")
    return mcp_server, client


async def chat_interactive(client: ArgoMCPClient, system_prompt: str):
    """Interactive chat loop with the LLM."""
    print_section("Interactive Chat Mode")
    print("Type your questions or commands. Type 'exit' or 'quit' to end.\n")
    print("Example commands:")
    print("  - 'What is the formula for glucose?'")
    print("  - 'Create a media with glucose and oxygen'")
    print("  - 'List available models'")
    print("  - 'Build a model from protein sequences MKLAVLGL...'")
    print()

    conversation_active = True

    while conversation_active:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()

            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            # Send to LLM
            print("\nAssistant: ", end="", flush=True)

            try:
                response = await client.chat(
                    user_input,
                    system_prompt=system_prompt if client.messages == [] else None
                )
                print(response)

            except Exception as e:
                print(f"\n✗ Error: {e}")
                logger.error(f"Chat error: {e}", exc_info=True)

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break

        except EOFError:
            print("\n\nGoodbye!")
            break


async def run_scripted_workflow(client: ArgoMCPClient):
    """Run a scripted workflow for demonstration."""
    print_section("Scripted Workflow: Model Building & Gapfilling")

    system_prompt = f"""You are a metabolic modeling expert assistant using the Gem-Flux MCP tools.

Working directory: {WORKING_DIR}

When users mention files, assume they are relative to the working directory unless an absolute path is given.

You have access to ModelSEED database lookups, media creation, model building, gapfilling, and FBA tools.

Be concise and technical in your responses."""

    # Step 1: Database lookup
    print("\n1. Looking up compound information...")
    response = await client.chat(
        "What is the molecular formula and mass of glucose (cpd00027)?",
        system_prompt=system_prompt,
        reset_history=True
    )
    print(f"   Assistant: {response}")

    # Step 2: Search for compounds
    print("\n2. Searching for compounds...")
    response = await client.chat(
        "Find compounds with 'ATP' in their name"
    )
    print(f"   Assistant: {response}")

    # Step 3: Create media
    print("\n3. Creating growth media...")
    response = await client.chat(
        """Create a minimal media called 'glucose_minimal' with:
        - Glucose (cpd00027)
        - Water (cpd00001)
        - Oxygen (cpd00007)
        - Phosphate (cpd00009)
        - Ammonia (cpd00013)
        """
    )
    print(f"   Assistant: {response}")

    # Step 4: List media
    print("\n4. Listing available media...")
    response = await client.chat("What media have we created?")
    print(f"   Assistant: {response}")

    print("\n✓ Workflow complete!")
    print("\nNext steps you could try:")
    print("  - Build a model from protein sequences")
    print("  - Gapfill a model on the media we created")
    print("  - Run FBA simulation")


async def test_multiple_models(mcp_server):
    """Test with multiple models to compare behavior."""
    print_banner("Multi-Model Comparison")

    test_query = "What is the molecular formula of glucose (compound cpd00027)?"
    results = {}

    for model_name, model_id in MODELS.items():
        print(f"\nTesting {model_name}...")

        try:
            client = ArgoMCPClient(
                mcp_server=mcp_server,
                argo_base_url="http://localhost:8000/v1",
                model=model_id,
                max_tools_per_call=6
            )

            await client.initialize()

            response = await client.chat(test_query, reset_history=True)
            results[model_name] = {"success": True, "response": response}
            print(f"   ✓ {model_name}: {response[:100]}...")

        except Exception as e:
            results[model_name] = {"success": False, "error": str(e)}
            print(f"   ✗ {model_name}: {str(e)[:100]}...")

    # Print summary
    print_section("Model Comparison Summary")
    for model_name, result in results.items():
        status = "✓" if result["success"] else "✗"
        print(f"{status} {model_name}: {'Working' if result['success'] else 'Failed'}")

    return results


# =============================================================================
# Main Entry Point
# =============================================================================


async def main():
    """Main entry point."""
    print_banner("Gem-Flux MCP: Interactive Natural Language Workflow")
    print(f"Working directory: {WORKING_DIR}")
    print(f"Available models: {', '.join(MODELS.keys())}")

    # Parse command line arguments
    mode = "interactive"  # Default mode
    model_name = "gpt-4o"  # Default model

    if len(sys.argv) > 1:
        mode = sys.argv[1]

    if len(sys.argv) > 2:
        model_name = sys.argv[2]

    # Setup client
    mcp_server, client = await setup_client(model_name)

    if not client:
        return

    # System prompt with working directory context
    system_prompt = f"""You are a metabolic modeling expert assistant using the Gem-Flux MCP tools.

Working directory: {WORKING_DIR}
Data directory: {WORKING_DIR / 'data'}

When users mention files, assume they are relative to the working directory unless an absolute path is given.

You have access to:
- ModelSEED database lookups (compounds, reactions)
- Media creation and management
- Metabolic model building from protein sequences
- Model gapfilling for growth on specific media
- Flux Balance Analysis (FBA) simulations

Be concise, technical, and helpful. When working with files, always use absolute paths."""

    # Run based on mode
    if mode == "interactive":
        await chat_interactive(client, system_prompt)

    elif mode == "scripted":
        await run_scripted_workflow(client)

    elif mode == "test-models":
        await test_multiple_models(mcp_server)

    else:
        print(f"Unknown mode: {mode}")
        print("Valid modes: interactive, scripted, test-models")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)
