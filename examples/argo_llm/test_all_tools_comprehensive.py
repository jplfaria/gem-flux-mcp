#!/usr/bin/env python3
"""Comprehensive test of ALL MCP tools with natural language prompts.

This script tests every single tool individually, then runs multi-tool workflows
to ensure the Argo LLM integration is production-ready for demos.

Usage:
    uv run python examples/argo_llm/test_all_tools_comprehensive.py

    # Test with different models
    uv run python examples/argo_llm/test_all_tools_comprehensive.py gpt-5
    uv run python examples/argo_llm/test_all_tools_comprehensive.py claude-sonnet-4
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gem_flux_mcp.server import initialize_server, create_server
from gem_flux_mcp.argo.client import ArgoMCPClient
from gem_flux_mcp.logging import get_logger

logger = get_logger(__name__)

# Available models
MODELS = {
    "gpt-4o": "argo:gpt-4o",
    "gpt-5": "argo:gpt-5",
    "claude-sonnet-4": "argo:claude-sonnet-4",
}

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text: str):
    """Print a bold header."""
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{text:^80}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")


def print_section(text: str):
    """Print a section header."""
    print(f"\n{BOLD}{text}{RESET}")
    print(f"{'-' * 80}")


def print_test(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {test_name}")
    if details:
        print(f"     {details}")


async def setup_client(model_name: str = "gpt-4o"):
    """Initialize MCP server and Argo client."""
    print_section("Setup: Initializing MCP Server & Argo Client")

    # Initialize MCP server
    try:
        initialize_server()
        mcp_server = create_server()
        print(f"{GREEN}✓{RESET} MCP server initialized")
    except Exception as e:
        print(f"{RED}✗{RESET} Failed to initialize MCP server: {e}")
        return None, None

    # Create Argo client
    model = MODELS.get(model_name, MODELS["gpt-4o"])
    try:
        client = ArgoMCPClient(
            mcp_server=mcp_server,
            argo_base_url="http://localhost:8000/v1",
            model=model,
            max_tools_per_call=6
        )
        print(f"{GREEN}✓{RESET} Argo client created (model: {model})")
    except Exception as e:
        print(f"{RED}✗{RESET} Failed to create Argo client: {e}")
        return None, None

    # Initialize client
    try:
        await client.initialize()
        tools = client.get_available_tools()
        print(f"{GREEN}✓{RESET} Loaded {len(tools)} MCP tools")
        print(f"     Tools: {', '.join(tools)}")
    except Exception as e:
        print(f"{RED}✗{RESET} Failed to initialize client: {e}")
        return None, None

    return mcp_server, client


async def test_individual_tools(client: ArgoMCPClient):
    """Test each tool individually with natural language prompts."""
    print_header("INDIVIDUAL TOOL TESTS")

    results = []

    # Test 1: get_compound_name
    print_section("Test 1: get_compound_name - Look up compound information")
    try:
        response = await client.chat(
            "What is the molecular formula and mass of glucose (cpd00027)?",
            reset_history=True
        )
        passed = "C6H12O6" in response or "C6H12O6" in response
        print_test("get_compound_name", passed, f"Response: {response[:100]}...")
        results.append(("get_compound_name", passed))
    except Exception as e:
        print_test("get_compound_name", False, f"Error: {e}")
        results.append(("get_compound_name", False))

    # Test 2: search_compounds
    print_section("Test 2: search_compounds - Search for compounds by name")
    try:
        response = await client.chat(
            "Find all compounds with 'ATP' in their name",
            reset_history=True
        )
        passed = "cpd00002" in response or "ATP" in response
        print_test("search_compounds", passed, f"Response: {response[:100]}...")
        results.append(("search_compounds", passed))
    except Exception as e:
        print_test("search_compounds", False, f"Error: {e}")
        results.append(("search_compounds", False))

    # Test 3: get_reaction_name
    print_section("Test 3: get_reaction_name - Look up reaction information")
    try:
        response = await client.chat(
            "What is the equation for reaction rxn00001?",
            reset_history=True
        )
        passed = "rxn00001" in response
        print_test("get_reaction_name", passed, f"Response: {response[:100]}...")
        results.append(("get_reaction_name", passed))
    except Exception as e:
        print_test("get_reaction_name", False, f"Error: {e}")
        results.append(("get_reaction_name", False))

    # Test 4: search_reactions
    print_section("Test 4: search_reactions - Search for reactions by name")
    try:
        response = await client.chat(
            "Find reactions related to 'glycolysis'",
            reset_history=True
        )
        passed = "rxn" in response.lower() or "reaction" in response.lower()
        print_test("search_reactions", passed, f"Response: {response[:100]}...")
        results.append(("search_reactions", passed))
    except Exception as e:
        print_test("search_reactions", False, f"Error: {e}")
        results.append(("search_reactions", False))

    # Test 5: build_media
    print_section("Test 5: build_media - Create growth media")
    try:
        response = await client.chat(
            """Create a minimal media called 'test_glucose_media' with:
            - Glucose (cpd00027) at 10 mmol/gDW/hr
            - Water (cpd00001) at 1000 mmol/gDW/hr
            - Oxygen (cpd00007) at 20 mmol/gDW/hr
            - Phosphate (cpd00009) at 10 mmol/gDW/hr
            - Ammonia (cpd00013) at 10 mmol/gDW/hr""",
            reset_history=True
        )
        passed = "test_glucose_media" in response or "media" in response.lower()
        print_test("build_media", passed, f"Response: {response[:150]}...")
        results.append(("build_media", passed))
    except Exception as e:
        print_test("build_media", False, f"Error: {e}")
        results.append(("build_media", False))

    # Test 6: list_media
    print_section("Test 6: list_media - List available media")
    try:
        response = await client.chat(
            "What media have we created in this session?",
            reset_history=False  # Continue conversation
        )
        passed = "test_glucose_media" in response or "media" in response.lower()
        print_test("list_media", passed, f"Response: {response[:100]}...")
        results.append(("list_media", passed))
    except Exception as e:
        print_test("list_media", False, f"Error: {e}")
        results.append(("list_media", False))

    # Test 7: build_model
    print_section("Test 7: build_model - Build metabolic model from sequences")
    try:
        # Use a small example sequence
        response = await client.chat(
            """Build a model called 'test_small_model' from these protein sequences:
            MKLAVLGAAGIGSTVAYGAANQALKLGDRVAIEPTDTVLGQALLKREGADVAQVSTGAG
            MKRTAIIAGLGMFGQMMASVAKKAAQQGADVVIAAPASNANAQAAQQIGFDKAGADVGA""",
            reset_history=True
        )
        passed = "model" in response.lower() and ("test_small_model" in response or "built" in response.lower())
        print_test("build_model", passed, f"Response: {response[:150]}...")
        results.append(("build_model", passed))
    except Exception as e:
        print_test("build_model", False, f"Error: {e}")
        results.append(("build_model", False))

    # Test 8: list_models
    print_section("Test 8: list_models - List available models")
    try:
        response = await client.chat(
            "What models have we created in this session?",
            reset_history=False
        )
        passed = "test_small_model" in response or "model" in response.lower()
        print_test("list_models", passed, f"Response: {response[:100]}...")
        results.append(("list_models", passed))
    except Exception as e:
        print_test("list_models", False, f"Error: {e}")
        results.append(("list_models", False))

    # Test 9: gapfill_model
    print_section("Test 9: gapfill_model - Gapfill model for growth")
    try:
        response = await client.chat(
            "Gapfill the test_small_model to grow on test_glucose_media",
            reset_history=False
        )
        passed = "gapfill" in response.lower() or "reaction" in response.lower()
        print_test("gapfill_model", passed, f"Response: {response[:150]}...")
        results.append(("gapfill_model", passed))
    except Exception as e:
        print_test("gapfill_model", False, f"Error: {e}")
        results.append(("gapfill_model", False))

    # Test 10: run_fba
    print_section("Test 10: run_fba - Run Flux Balance Analysis")
    try:
        response = await client.chat(
            "Run FBA on test_small_model with test_glucose_media and tell me the growth rate",
            reset_history=False
        )
        passed = "growth" in response.lower() or "objective" in response.lower()
        print_test("run_fba", passed, f"Response: {response[:150]}...")
        results.append(("run_fba", passed))
    except Exception as e:
        print_test("run_fba", False, f"Error: {e}")
        results.append(("run_fba", False))

    # Test 11: delete_model
    print_section("Test 11: delete_model - Delete a model")
    try:
        response = await client.chat(
            "Delete the test_small_model",
            reset_history=False
        )
        passed = "delete" in response.lower() or "removed" in response.lower()
        print_test("delete_model", passed, f"Response: {response[:100]}...")
        results.append(("delete_model", passed))
    except Exception as e:
        print_test("delete_model", False, f"Error: {e}")
        results.append(("delete_model", False))

    return results


async def test_multi_tool_workflows(client: ArgoMCPClient):
    """Test workflows that use multiple tools in succession."""
    print_header("MULTI-TOOL WORKFLOW TESTS")

    results = []

    # Workflow 1: Database exploration workflow
    print_section("Workflow 1: Database Exploration")
    print("Steps: search_compounds → get_compound_name → search_reactions")
    try:
        response = await client.chat(
            """I want to understand ATP metabolism. First, find all ATP-related compounds,
            then get detailed info on ATP itself (cpd00002), then find reactions involving ATP.""",
            reset_history=True
        )
        passed = "cpd00002" in response and ("reaction" in response.lower() or "rxn" in response)
        print_test("Database exploration workflow", passed, f"Response length: {len(response)} chars")
        results.append(("Workflow: Database exploration", passed))
    except Exception as e:
        print_test("Database exploration workflow", False, f"Error: {e}")
        results.append(("Workflow: Database exploration", False))

    # Workflow 2: Media creation workflow
    print_section("Workflow 2: Media Creation & Validation")
    print("Steps: search_compounds → build_media → list_media")
    try:
        response = await client.chat(
            """Create a complete minimal media for E. coli growth:
            1. First check what compounds we need (glucose, ammonia, phosphate, water, oxygen)
            2. Create the media with proper concentrations
            3. Show me all media we've created""",
            reset_history=True
        )
        passed = "media" in response.lower()
        print_test("Media creation workflow", passed, f"Response length: {len(response)} chars")
        results.append(("Workflow: Media creation", passed))
    except Exception as e:
        print_test("Media creation workflow", False, f"Error: {e}")
        results.append(("Workflow: Media creation", False))

    # Workflow 3: Complete model building workflow
    print_section("Workflow 3: Complete Model Building Pipeline")
    print("Steps: build_model → list_models → build_media → gapfill_model → run_fba")
    try:
        response = await client.chat(
            """Let's build a complete metabolic model:
            1. Build a model called 'workflow_test_model' from these sequences:
               MKLAVLGAAGIGSTVAYGAANQALKLGDRVAIEPTDTVLGQALLKREGADVAQVSTGAG
            2. List all models to confirm it was created
            3. Create a minimal media called 'workflow_media' with glucose, water, oxygen
            4. Gapfill the model on this media
            5. Run FBA and tell me the growth rate""",
            reset_history=True
        )
        passed = "growth" in response.lower() or "fba" in response.lower()
        print_test("Complete model building workflow", passed, f"Response length: {len(response)} chars")
        results.append(("Workflow: Complete model pipeline", passed))
    except Exception as e:
        print_test("Complete model building workflow", False, f"Error: {e}")
        results.append(("Workflow: Complete model pipeline", False))

    # Workflow 4: Model comparison workflow
    print_section("Workflow 4: Model Comparison & Management")
    print("Steps: list_models → build_model (x2) → list_models → delete_model")
    try:
        response = await client.chat(
            """Let's manage multiple models:
            1. Show me what models we have
            2. Build a model called 'model_a' with sequence MKLAVLGAAGIGSTVAYGAA
            3. Build a model called 'model_b' with sequence MKRTAIIAGLGMFGQMMASA
            4. List all models again
            5. Delete model_a""",
            reset_history=True
        )
        passed = "model" in response.lower() and ("delete" in response.lower() or "removed" in response.lower())
        print_test("Model comparison workflow", passed, f"Response length: {len(response)} chars")
        results.append(("Workflow: Model management", passed))
    except Exception as e:
        print_test("Model comparison workflow", False, f"Error: {e}")
        results.append(("Workflow: Model management", False))

    return results


async def main():
    """Main entry point."""
    print_header("COMPREHENSIVE MCP TOOL TESTING")
    print(f"Testing all tools individually + multi-tool workflows")
    print(f"Working directory: {Path.cwd()}")

    # Parse model from command line
    model_name = sys.argv[1] if len(sys.argv) > 1 else "gpt-4o"
    if model_name not in MODELS:
        print(f"{RED}Unknown model: {model_name}{RESET}")
        print(f"Available models: {', '.join(MODELS.keys())}")
        return

    print(f"Using model: {BOLD}{model_name}{RESET}")

    # Setup
    mcp_server, client = await setup_client(model_name)
    if not client:
        print(f"\n{RED}Setup failed! Cannot continue.{RESET}")
        return

    # System prompt
    system_prompt = f"""You are a metabolic modeling expert assistant using Gem-Flux MCP tools.

Working directory: {Path.cwd()}

You have access to:
- Database tools: get_compound_name, search_compounds, get_reaction_name, search_reactions
- Media tools: build_media, list_media
- Model tools: build_model, list_models, delete_model
- Analysis tools: gapfill_model, run_fba

Be concise and technical. Always execute the requested operations."""

    # Run individual tool tests
    individual_results = await test_individual_tools(client)

    # Run workflow tests
    workflow_results = await test_multi_tool_workflows(client)

    # Print summary
    print_header("TEST SUMMARY")

    all_results = individual_results + workflow_results
    passed = sum(1 for _, p in all_results if p)
    total = len(all_results)
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"\n{BOLD}Individual Tool Tests:{RESET}")
    for name, result in individual_results:
        status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
        print(f"  {status} {name}")

    print(f"\n{BOLD}Workflow Tests:{RESET}")
    for name, result in workflow_results:
        status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
        print(f"  {status} {name}")

    print(f"\n{BOLD}Overall Results:{RESET}")
    print(f"  Total tests: {total}")
    print(f"  Passed: {GREEN}{passed}{RESET}")
    print(f"  Failed: {RED}{total - passed}{RESET}")
    print(f"  Success rate: {GREEN if percentage >= 80 else RED}{percentage:.1f}%{RESET}")

    if percentage >= 80:
        print(f"\n{GREEN}{BOLD}🎉 Ready for demo! All critical functionality working.{RESET}")
    else:
        print(f"\n{YELLOW}{BOLD}⚠️  Some tests failed. Review results before demo.{RESET}")

    print(f"\n{BOLD}Next steps:{RESET}")
    print(f"  1. Run interactive mode: uv run python examples/argo_llm/interactive_workflow.py interactive {model_name}")
    print(f"  2. Test with other models: {', '.join(m for m in MODELS if m != model_name)}")
    print(f"  3. Practice demo scenarios\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Interrupted.{RESET}")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n{RED}Fatal error: {e}{RESET}")
        sys.exit(1)
