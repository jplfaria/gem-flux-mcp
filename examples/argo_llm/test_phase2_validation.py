"""Quick Phase 2 Validation Test.

Tests the 3 failed Phase 1 tests with Phase 2 enhanced prompts:
1. get_compound_name (Phase 1: Failed)
2. build_media (Phase 1: Failed)
3. gapfill_model (Phase 1: Failed)

Goal: Validate that Phase 2 prompts improve success rate without regression.
"""

import asyncio
import sys
from pathlib import Path
from gem_flux_mcp.server import initialize_server, create_server
from gem_flux_mcp.argo.client import ArgoMCPClient
from production_config import get_production_config, get_phase2_enhanced_prompt


# Test queries targeting Phase 1 failures
TEST_QUERIES = [
    {
        "name": "get_compound_name",
        "query": "What is the name of compound cpd00027?",
        "expected_keywords": ["glucose", "d-glucose"],
        "description": "Test get_compound_name tool (Phase 1: FAILED)"
    },
    {
        "name": "build_media",
        "query": "Create a media called 'phase2_test_media' with compounds cpd00001, cpd00009, and cpd00027",
        "expected_keywords": ["media", "created", "built"],
        "description": "Test build_media tool (Phase 1: FAILED)"
    },
    {
        "name": "gapfill_model",
        "query": "Build a model named 'phase2_gapfill_test' with sequence MKKYTCTVCGYIYNPEDGDPDNGVNPGTDFKDIPDDWVCPLCGVGKDQFEEVEE, then create media 'phase2_minimal' with compounds cpd00001, cpd00009, cpd00027, then gapfill the model on that media",
        "expected_keywords": ["gapfill", "reactions", "added"],
        "description": "Test gapfill_model workflow (Phase 1: FAILED)"
    },
]


def validate_response(response: str, expected_keywords: list) -> bool:
    """Check if response contains expected keywords."""
    response_lower = response.lower()
    return any(keyword.lower() in response_lower for keyword in expected_keywords)


async def test_phase2_prompts():
    """Run Phase 2 validation tests."""

    print("="*80)
    print("PHASE 2 VALIDATION TEST")
    print("="*80)
    print(f"Testing {len(TEST_QUERIES)} queries that failed in Phase 1")
    print("Using Claude Sonnet 4 with Phase 2 enhanced prompts\n")

    # Initialize MCP server
    print("Initializing MCP server...")
    initialize_server()
    mcp_server = create_server()
    print("✓ MCP server initialized\n")

    # Get Phase 2 configuration
    print("Loading Phase 2 configuration (enhanced prompts)...")
    config = get_production_config(
        model_name="claude-sonnet-4",
        use_phase2_prompt=True  # Use Phase 2 enhanced prompts
    )
    print(f"✓ Phase 2 config loaded\n")

    # Create Argo client with Phase 2 config
    print("Creating Argo MCP client...")
    client = ArgoMCPClient(
        mcp_server=mcp_server,
        argo_base_url="http://localhost:8000/v1",
        argo_api_key="not-needed",
        **config["client_params"]  # Unpack client parameters
    )
    print("✓ Client created\n")

    # Get system prompt for chat()
    system_prompt = config.get("system_prompt", None)

    # Initialize client
    print("Initializing client (loading tools)...")
    await client.initialize()
    print(f"✓ Loaded {len(client.get_available_tools())} tools\n")

    # Run tests
    results = []
    passed = 0
    failed = 0

    print("="*80)
    print("RUNNING TESTS")
    print("="*80)

    for i, test in enumerate(TEST_QUERIES, 1):
        print(f"\n[Test {i}/{len(TEST_QUERIES)}] {test['name']}")
        print(f"Description: {test['description']}")
        print(f"Query: {test['query'][:80]}{'...' if len(test['query']) > 80 else ''}")
        print("-"*80)

        try:
            # Run query with Phase 2 system prompt
            response = await client.chat(
                test['query'],
                system_prompt=system_prompt,
                reset_history=True
            )

            # Validate response
            success = validate_response(response, test['expected_keywords'])

            if success:
                print(f"✅ PASS - Response contains expected keywords")
                passed += 1
                results.append({"test": test['name'], "status": "PASS"})
            else:
                print(f"❌ FAIL - Expected keywords not found")
                print(f"Expected one of: {test['expected_keywords']}")
                print(f"Got: {response[:200]}...")
                failed += 1
                results.append({"test": test['name'], "status": "FAIL"})

        except Exception as e:
            print(f"❌ ERROR - {str(e)}")
            failed += 1
            results.append({"test": test['name'], "status": "ERROR", "error": str(e)})

    # Print summary
    print("\n" + "="*80)
    print("PHASE 2 VALIDATION RESULTS")
    print("="*80)

    for result in results:
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")

    print(f"\nTotal: {len(TEST_QUERIES)} tests")
    print(f"Passed: {passed} ({passed/len(TEST_QUERIES)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(TEST_QUERIES)*100:.1f}%)")

    print("\n" + "="*80)
    print("COMPARISON TO PHASE 1")
    print("="*80)
    print("Phase 1 (default prompts): 0/3 passed (0%)")
    print(f"Phase 2 (enhanced prompts): {passed}/3 passed ({passed/3*100:.1f}%)")

    if passed > 0:
        print(f"\n✅ Phase 2 shows improvement: +{passed} tests passing")
    else:
        print(f"\n⚠️  Phase 2 did not improve these specific tests")
        print("   However, Phase 2 may still improve overall success rate")

    print("="*80)

    return passed, failed


if __name__ == "__main__":
    try:
        passed, failed = asyncio.run(test_phase2_prompts())

        # Exit with appropriate code
        if failed == 0:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)
