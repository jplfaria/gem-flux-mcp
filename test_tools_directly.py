#!/usr/bin/env python3
"""
Direct test of gapfill_model and run_fba tools.
Tests the actual tool functions, not notebook code.
"""

from examples.notebook_setup import quick_setup
from gem_flux_mcp.tools.build_model import build_model
from gem_flux_mcp.tools.gapfill_model import gapfill_model
from gem_flux_mcp.tools.run_fba import run_fba
import asyncio

print("=" * 70)
print("DIRECT TOOL TEST: Build → Gapfill → FBA")
print("=" * 70)

async def test_tools():
    # Setup
    print("\n1. Setup environment...")
    db_index, templates, atp_media, predefined_media = quick_setup()
    print("✓ Environment ready")

    # Build model
    print("\n2. Build model...")
    build_result = await build_model(
        fasta_file_path="examples/ecoli_proteins.fasta",
        template="GramNegative",
        model_name="test_ecoli",
        annotate_with_rast=True
    )
    model_id = build_result["model_id"]
    print(f"✓ Built model: {model_id}")
    print(f"  Reactions: {build_result['num_reactions']}")
    print(f"  Has biomass: {build_result['has_biomass_reaction']}")

    # Gapfill model
    print("\n3. Gapfill model...")
    gf_result = gapfill_model(
        model_id=model_id,
        media_id="glucose_minimal_aerobic",
        db_index=db_index,
        target_growth_rate=0.01,
        gapfill_mode="full"
    )
    gf_model_id = gf_result["model_id"]
    print(f"✓ Gapfilled model: {gf_model_id}")
    print(f"  Reactions added: {gf_result['num_reactions_added']}")
    print(f"  Growth before: {gf_result['growth_rate_before']:.3f} hr⁻¹")
    print(f"  Growth after: {gf_result['growth_rate_after']:.3f} hr⁻¹")

    # Run FBA with ATPM_c0
    print("\n4. Run FBA with ATPM_c0 objective...")
    fba_atpm = run_fba(
        model_id=gf_model_id,
        media_id="glucose_minimal_aerobic",
        db_index=db_index,
        objective="ATPM_c0",
        maximize=True
    )
    print(f"✓ FBA with ATPM_c0:")
    print(f"  Status: {fba_atpm['status']}")
    print(f"  Objective: {fba_atpm['objective_value']:.3f}")

    # Run FBA with bio1
    print("\n5. Run FBA with bio1 objective...")
    fba_bio1 = run_fba(
        model_id=gf_model_id,
        media_id="glucose_minimal_aerobic",
        db_index=db_index,
        objective="bio1",
        maximize=True
    )
    print(f"✓ FBA with bio1:")
    print(f"  Status: {fba_bio1['status']}")
    print(f"  Objective: {fba_bio1['objective_value']:.3f}")

    # Summary
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)

    if gf_result['growth_rate_after'] > 0.01:
        print("✅ Gapfilling: SUCCESS")
        print(f"   Growth after gapfilling: {gf_result['growth_rate_after']:.3f} hr⁻¹")
    else:
        print("❌ Gapfilling: FAILED")

    if fba_atpm['objective_value'] > 0.01:
        print("✅ FBA with ATPM_c0: SUCCESS")
        print(f"   ATP production rate: {fba_atpm['objective_value']:.3f}")
    else:
        print("❌ FBA with ATPM_c0: FAILED")

    if fba_bio1['objective_value'] > 0.01:
        print("✅ FBA with bio1: SUCCESS")
        print(f"   Growth rate: {fba_bio1['objective_value']:.3f} hr⁻¹")
    else:
        print("⚠️  FBA with bio1: NO GROWTH")
        print(f"   Growth rate: {fba_bio1['objective_value']:.3f} hr⁻¹")
        print("\n   This suggests gapfilling optimized for ATPM_c0, not bio1")
        print("   Media application is working (ATPM_c0 succeeded)")
        print("   But biomass production pathways may need additional gapfilling")

    print("=" * 70)

# Run the test
asyncio.run(test_tools())
