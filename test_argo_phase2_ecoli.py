#!/usr/bin/env python3
"""Test Phase 2 improvements with Argo using Claude Sonnet 4.5.

This test runs the E. coli workflow to validate Phase 2 improvements:
- Real pathway data from ModelSEED database
- Workflow guidance via next_steps
- Biological interpretation in tool outputs

Expected improvements:
- Claude understands workflow without asking "what next?"
- Claude mentions real pathway names
- Claude provides biological context in explanations
"""

import asyncio
import sys
from pathlib import Path
from gem_flux_mcp.server import initialize_server, create_server
from gem_flux_mcp.argo.client import ArgoMCPClient


# The test prompt from test guides
ECOLI_WORKFLOW_PROMPT = """I want to build a genome-scale metabolic model for E. coli and analyze its growth on glucose.

The protein sequences are in: examples/ecoli_proteins.fasta

Please:
1. Build a draft model using the GramNegative template with RAST annotation
2. Gapfill it for growth on glucose minimal aerobic media
3. Run FBA to predict the growth rate
4. Explain what you learned about the model's metabolism

Important: Pay attention to the tool outputs - they include guidance on next steps and biological interpretation. Use this information to guide your workflow.
"""


def analyze_response_for_phase2_features(response: str) -> dict:
    """Analyze response for Phase 2 improvement indicators.

    Returns dict with:
    - workflow_autonomous: Did Claude proceed through steps without asking?
    - mentions_pathways: Did Claude mention pathway names?
    - real_pathway_names: Did Claude use real pathway names (not generic)?
    - biological_context: Did Claude provide biological interpretation?
    - mentions_growth_improvement: Did Claude reference growth improvement?
    - mentions_quality: Did Claude explain model quality?
    """
    response_lower = response.lower()

    # Check for "what next?" patterns (bad sign)
    asking_next = any(phrase in response_lower for phrase in [
        "what should i do next",
        "what next",
        "should i proceed",
        "shall i continue",
    ])

    # Check for pathway mentions
    mentions_pathways = any(word in response_lower for word in [
        "pathway", "pathways", "glycolysis", "pentose", "tca"
    ])

    # Check for real pathway names (Phase 2 database names)
    # Real ModelSEED pathway names contain: "/", specific IDs like "PWY", exact DB names
    real_pathways = any(phrase in response for phrase in [
        "Glycolysis / Gluconeogenesis",  # Real DB name
        "Pentose Phosphate Pathway",      # Real DB name (title case)
        "-PWY",                           # ModelSEED pathway IDs
        "rn00010",                        # KEGG pathway IDs
    ])

    # Check for biological context
    biological_terms = any(phrase in response_lower for phrase in [
        "aerobic respiration",
        "anaerobic",
        "fast growth",
        "moderate growth",
        "slow growth",
        "carbon source",
        "metabolism",
        "high-quality model",
        "extensive reaction coverage",
    ])

    # Check for growth improvement mention
    growth_improvement = any(phrase in response_lower for phrase in [
        "growth improved",
        "0.0 to",
        "before gapfilling",
        "after gapfilling",
    ])

    # Check for quality assessment
    quality_mention = any(phrase in response_lower for phrase in [
        "high-quality",
        "good draft model",
        "extensive reaction coverage",
        "minimal gapfilling",
        "moderate gapfilling",
        "extensive gapfilling",
    ])

    return {
        "workflow_autonomous": not asking_next,
        "mentions_pathways": mentions_pathways,
        "real_pathway_names": real_pathways,
        "biological_context": biological_terms,
        "mentions_growth_improvement": growth_improvement,
        "mentions_quality": quality_mention,
    }


async def test_ecoli_workflow_phase2():
    """Run E. coli workflow test with Claude Sonnet 4.5."""

    print("=" * 80)
    print("ARGO TEST: PHASE 2 E. COLI WORKFLOW")
    print("=" * 80)
    print("Model: Claude Sonnet 4.5 (experimental)")
    print("Purpose: Validate Phase 2 improvements (next_steps, interpretation, real pathways)")
    print("=" * 80)
    print()

    # Initialize MCP server
    print("1. Initializing MCP server...")
    initialize_server()
    mcp_server = create_server()
    print("   ✓ MCP server initialized")
    print()

    # Create Argo client with Claude Sonnet 4.5
    print("2. Creating Argo client with Claude Sonnet 4.5...")
    client = ArgoMCPClient(
        mcp_server=mcp_server,
        argo_base_url="http://localhost:8000/v1",
        argo_api_key="not-needed",
        model="argo:claudesonnet45",  # Claude Sonnet 4.5 experimental
        temperature=None,
        top_p=0.9,
        max_tokens=4096,
        max_tool_calls=10,
        max_tools_per_call=6,
    )
    print("   ✓ Client created")
    print()

    # Initialize client
    print("3. Initializing client (loading MCP tools)...")
    await client.initialize()
    tools = client.get_available_tools()
    print(f"   ✓ Loaded {len(tools)} tools")
    print()

    # Check examples/ecoli_proteins.fasta exists
    fasta_path = Path("examples/ecoli_proteins.fasta")
    if not fasta_path.exists():
        print(f"   ⚠️  WARNING: {fasta_path} not found")
        print(f"   Test may fail if Claude cannot find the file")
    else:
        print(f"   ✓ Found {fasta_path}")
    print()

    # Run E. coli workflow
    print("4. Running E. coli workflow...")
    print("-" * 80)
    print("PROMPT:")
    print(ECOLI_WORKFLOW_PROMPT)
    print("-" * 80)
    print()

    print("Sending to Claude Sonnet 4.5... (this may take 5-7 minutes)")
    print()

    try:
        response = await client.chat(
            ECOLI_WORKFLOW_PROMPT,
            reset_history=True
        )

        print("=" * 80)
        print("CLAUDE RESPONSE:")
        print("=" * 80)
        print(response)
        print("=" * 80)
        print()

        # Analyze response for Phase 2 features
        print("=" * 80)
        print("PHASE 2 FEATURE ANALYSIS")
        print("=" * 80)

        analysis = analyze_response_for_phase2_features(response)

        print("\nWorkflow Autonomy:")
        if analysis["workflow_autonomous"]:
            print("  ✅ Claude proceeded autonomously (no 'what next?' questions)")
        else:
            print("  ❌ Claude asked 'what next?' - workflow guidance not working")

        print("\nPathway Data Quality:")
        if analysis["real_pathway_names"]:
            print("  ✅ Claude used real pathway names from database")
        elif analysis["mentions_pathways"]:
            print("  ⚠️  Claude mentioned pathways but may be using generic names")
        else:
            print("  ❌ Claude did not mention pathways")

        print("\nBiological Context:")
        if analysis["biological_context"]:
            print("  ✅ Claude provided biological interpretation")
        else:
            print("  ❌ Claude did not provide biological context")

        print("\nGrowth Understanding:")
        if analysis["mentions_growth_improvement"]:
            print("  ✅ Claude understood growth improvement (0.0 → X)")
        else:
            print("  ⚠️  Claude did not mention growth improvement")

        print("\nModel Quality Assessment:")
        if analysis["mentions_quality"]:
            print("  ✅ Claude explained model quality")
        else:
            print("  ⚠️  Claude did not explain model quality")

        # Overall assessment
        print("\n" + "=" * 80)
        print("OVERALL ASSESSMENT")
        print("=" * 80)

        score = sum(analysis.values())
        max_score = len(analysis)

        print(f"\nPhase 2 Feature Score: {score}/{max_score} ({score/max_score*100:.0f}%)")

        if score >= 5:
            print("\n✅ EXCELLENT - Phase 2 improvements working well!")
        elif score >= 3:
            print("\n⚠️  PARTIAL - Some Phase 2 improvements working")
        else:
            print("\n❌ POOR - Phase 2 improvements not effective")

        print("\nKey Observations:")
        for feature, present in analysis.items():
            status = "✓" if present else "✗"
            print(f"  {status} {feature}")

        print("\n" + "=" * 80)

        return analysis, response

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None, None


async def main():
    """Main entry point."""
    try:
        analysis, response = await test_ecoli_workflow_phase2()

        if analysis is None:
            print("\n❌ Test failed with error")
            return 1

        # Exit code based on score
        score = sum(analysis.values())
        if score >= 4:
            print("\n✅ Test PASSED - Phase 2 improvements validated")
            return 0
        else:
            print("\n⚠️  Test INCOMPLETE - Phase 2 improvements need review")
            return 1

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
