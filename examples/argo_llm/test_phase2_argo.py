#!/usr/bin/env python3
"""Test Phase 2 improvements via Argo client.

Tests both Claude Sonnet 4 and Claude Sonnet 4.5 with the E. coli workflow
to see if Phase 2 improvements (next_steps, interpretation, real pathways)
make a difference when using Argo instead of Claude Code directly.
"""

import asyncio
import sys
from pathlib import Path
from gem_flux_mcp.server import initialize_server, create_server
from gem_flux_mcp.argo.client import ArgoMCPClient


ECOLI_WORKFLOW = """I want to build a genome-scale metabolic model for E. coli and analyze its growth on glucose.

The protein sequences are in: examples/ecoli_proteins.fasta

Please:
1. Build a draft model using the GramNegative template with RAST annotation
2. Gapfill it for growth on glucose minimal aerobic media
3. Run FBA to predict the growth rate
4. Explain what you learned about the model's metabolism

Important: Pay attention to the tool outputs - they include guidance on next steps and biological interpretation. Use this information to guide your workflow."""


async def test_model(model_name: str, model_id: str):
    """Test a specific model with the E. coli workflow."""

    print("\n" + "=" * 80)
    print(f"Testing: {model_name}")
    print(f"Model ID: {model_id}")
    print("=" * 80)

    # Initialize MCP server
    print("\nInitializing MCP server...")
    initialize_server()
    mcp_server = create_server()
    print("✓ MCP server initialized")

    # Create Argo client
    print(f"\nCreating Argo client for {model_name}...")
    client = ArgoMCPClient(
        mcp_server=mcp_server,
        argo_base_url="http://localhost:8000/v1",
        argo_api_key="not-needed",
        model=model_id,
        temperature=0.0,
        max_tokens=4096,
        max_tool_calls=20,
        max_tools_per_call=6,
    )
    print("✓ Client created")

    # Initialize
    print("\nInitializing (loading tools)...")
    await client.initialize()
    print(f"✓ Loaded {len(client.get_available_tools())} tools")

    # Run workflow
    print("\n" + "-" * 80)
    print("Running E. coli workflow...")
    print("-" * 80)
    print("\nThis will take 5-7 minutes (RAST annotation + gapfilling)...")
    print()

    try:
        response = await client.chat(
            ECOLI_WORKFLOW,
            reset_history=True
        )

        print("\n" + "=" * 80)
        print(f"{model_name} RESPONSE:")
        print("=" * 80)
        print(response)
        print("=" * 80)

        # Analyze for Phase 2 features
        response_lower = response.lower()

        analysis = {
            "asked_what_next": any(phrase in response_lower for phrase in [
                "what should i do next", "what next", "should i proceed"
            ]),
            "mentioned_pathways": "pathway" in response_lower,
            "real_pathway_names": any(name in response for name in [
                "Glycolysis / Gluconeogenesis", "Pentose Phosphate Pathway", "-PWY"
            ]),
            "biological_context": any(term in response_lower for term in [
                "aerobic", "fast growth", "moderate growth", "carbon source"
            ]),
            "growth_improvement": "0.0" in response or "growth improved" in response_lower,
            "model_quality": any(term in response_lower for term in [
                "high-quality", "extensive reaction coverage", "minimal gapfilling"
            ]),
        }

        print("\n" + "=" * 80)
        print("PHASE 2 FEATURE ANALYSIS")
        print("=" * 80)

        print(f"\n✓ Workflow autonomous: {not analysis['asked_what_next']}")
        print(f"✓ Mentioned pathways: {analysis['mentioned_pathways']}")
        print(f"✓ Used real pathway names: {analysis['real_pathway_names']}")
        print(f"✓ Provided biological context: {analysis['biological_context']}")
        print(f"✓ Mentioned growth improvement: {analysis['growth_improvement']}")
        print(f"✓ Explained model quality: {analysis['model_quality']}")

        score = sum([
            not analysis['asked_what_next'],
            analysis['mentioned_pathways'],
            analysis['real_pathway_names'],
            analysis['biological_context'],
            analysis['growth_improvement'],
            analysis['model_quality'],
        ])

        print(f"\nPhase 2 Feature Score: {score}/6 ({score/6*100:.0f}%)")

        return score, analysis, response

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 0, None, None


async def main():
    """Run tests for both models."""

    print("=" * 80)
    print("ARGO PHASE 2 VALIDATION TEST")
    print("=" * 80)
    print("\nTesting if Phase 2 improvements help when using Argo client")
    print("(instead of Claude Code directly)")
    print("\nModels to test:")
    print("1. Claude Sonnet 4 (80% success rate in production)")
    print("2. Claude Sonnet 4.5 (53.3% success rate, same as Claude Code)")

    results = {}

    # Test Claude Sonnet 4
    print("\n" + "=" * 80)
    print("TEST 1: CLAUDE SONNET 4")
    print("=" * 80)

    score_4, analysis_4, response_4 = await test_model(
        "Claude Sonnet 4",
        "argo:claude-sonnet-4"
    )
    results["Claude Sonnet 4"] = {"score": score_4, "analysis": analysis_4}

    # Test Claude Sonnet 4.5
    print("\n" + "=" * 80)
    print("TEST 2: CLAUDE SONNET 4.5")
    print("=" * 80)

    score_45, analysis_45, response_45 = await test_model(
        "Claude Sonnet 4.5",
        "argo:claudesonnet45"
    )
    results["Claude Sonnet 4.5"] = {"score": score_45, "analysis": analysis_45}

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"\nClaude Sonnet 4 Phase 2 Score: {score_4}/6 ({score_4/6*100:.0f}%)")
    print(f"Claude Sonnet 4.5 Phase 2 Score: {score_45}/6 ({score_45/6*100:.0f}%)")

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)

    if score_4 >= 4 or score_45 >= 4:
        print("\n✅ Phase 2 improvements are helping! LLM is using:")
        print("   - Workflow guidance (next_steps)")
        print("   - Biological interpretation")
        print("   - Real pathway data")
    else:
        print("\n⚠️  Phase 2 improvements need more work")

    return 0 if (score_4 >= 4 or score_45 >= 4) else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
