#!/usr/bin/env python3
"""
Baseline Test: Capture exact tool outputs before prompts centralization.

This script tests key MCP tools and saves their outputs as JSON snapshots.
After implementing centralized prompts, we'll run this again and compare
outputs to ensure zero functional changes.
"""

import json
import asyncio
from pathlib import Path

# Test small workflow to capture interpretation and next_steps outputs


async def test_tools():
    """Test MCP tools and capture outputs."""
    from gem_flux_mcp.server import initialize_server
    from gem_flux_mcp.tools.compound_lookup import search_compounds
    from gem_flux_mcp.tools.media_builder import build_media
    from gem_flux_mcp.tools.list_media import list_media

    results = {}

    print("Initializing server...")
    initialize_server()

    # Test 1: search_compounds
    print("\n1. Testing search_compounds...")
    result = await search_compounds(query="glucose", limit=3)
    results["search_compounds"] = result
    print(f"   ✓ Found {result['num_results']} compounds")
    print(f"   ✓ Has next_steps: {'next_steps' in result}")

    # Test 2: list_media
    print("\n2. Testing list_media...")
    result = await list_media()
    results["list_media"] = result
    print(f"   ✓ Found {result['total_media']} media")
    print(f"   ✓ Has next_steps: {'next_steps' in result}")

    # Test 3: build_media
    print("\n3. Testing build_media...")
    result = await build_media(
        compounds=["cpd00001", "cpd00009", "cpd00027"],  # Water, Phosphate, Glucose
        default_uptake=100.0
    )
    results["build_media"] = result
    print(f"   ✓ Created media: {result['media_id']}")
    print(f"   ✓ Has next_steps: {'next_steps' in result}")

    return results


async def main():
    """Main test runner."""
    print("=" * 80)
    print("BASELINE TEST: Tool Outputs")
    print("=" * 80)
    print()
    print("Purpose: Capture exact tool outputs before prompts centralization")
    print()

    try:
        results = await test_tools()

        # Save to JSON
        output_file = Path("baseline_tests/BASELINE_TOOL_OUTPUTS.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print()
        print("=" * 80)
        print("✓ Baseline outputs saved to:", output_file)
        print("=" * 80)

        # Summary
        print()
        print("Summary:")
        for tool_name, output in results.items():
            has_next_steps = "next_steps" in output
            has_interpretation = "interpretation" in output
            print(f"  {tool_name}:")
            print(f"    - has next_steps: {has_next_steps}")
            print(f"    - has interpretation: {has_interpretation}")
            if has_next_steps:
                print(f"    - next_steps count: {len(output['next_steps'])}")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
