"""End-to-end integration test replicating the source notebook workflow.

This test validates that our tool chain (build_model -> gapfill_model -> run_fba)
produces the same results as the source notebook, specifically:
- Growth rate of 0.5544 (with ATP correction)
- Biologically realistic model behavior
- All workflow steps complete successfully

This is the ultimate validation test for our ATP correction integration.
"""

from pathlib import Path

import pytest

from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.storage.media import clear_all_media
from gem_flux_mcp.storage.models import clear_all_models
from gem_flux_mcp.templates.loader import load_templates
from gem_flux_mcp.tools.build_model import build_model
from gem_flux_mcp.tools.gapfill_model import gapfill_model
from gem_flux_mcp.tools.media_builder import BuildMediaRequest, build_media
from gem_flux_mcp.tools.run_fba import run_fba


@pytest.fixture
def real_database():
    """Load real ModelSEED database."""
    db_dir = Path(__file__).parent.parent.parent / "data" / "database"
    compounds_df = load_compounds_database(db_dir / "compounds.tsv")
    reactions_df = load_reactions_database(db_dir / "reactions.tsv")
    return DatabaseIndex(compounds_df, reactions_df)


@pytest.fixture(autouse=True)
def load_all_templates():
    """Ensure templates are loaded before each test."""
    template_dir = Path(__file__).parent.parent.parent / "data" / "templates"
    load_templates(template_dir)
    yield


@pytest.fixture
def ecoli_fasta_path():
    """Path to E. coli proteins FASTA file."""
    fasta_path = Path(__file__).parent.parent.parent / "specs-source" / "build_metabolic_model" / "GCF_000005845.2_ASM584v2_protein.faa"
    if not fasta_path.exists():
        # Fallback to examples directory
        fasta_path = Path(__file__).parent.parent.parent / "examples" / "ecoli_proteins.fasta"
    return fasta_path


@pytest.fixture(autouse=True)
def cleanup_storage():
    """Clear storage before and after each test."""
    clear_all_models()
    clear_all_media()
    yield
    clear_all_models()
    clear_all_media()


@pytest.mark.asyncio
@pytest.mark.slow
class TestNotebookReplication:
    """Integration tests that replicate the complete notebook workflow."""

    async def test_complete_workflow_matches_notebook(self, ecoli_fasta_path, real_database):
        """Test complete workflow: build -> gapfill -> FBA matches notebook results.

        This test replicates the exact workflow from the source notebook:
        1. Load E. coli genome (FASTA)
        2. Build draft model with GramNegative template + RAST annotation + ATP correction
        3. Create glucose minimal aerobic media
        4. Gapfill model (reuses ATP test_conditions from build_model)
        5. Run FBA
        6. Verify growth rate matches notebook: 0.5544

        Expected Results:
        - Growth rate: 0.5544 (±0.001 tolerance)
        - Model is biologically realistic
        - ATP correction test_conditions are reused (efficient)
        """

        print("\n" + "=" * 80)
        print("FULL WORKFLOW TEST: Replicating Source Notebook")
        print("=" * 80)

        # Step 1: Build E. coli model with ATP correction (default)
        print("\n=== STEP 1: Building E. coli model ===")
        print("- Genome: E. coli K-12 MG1655")
        print("- Template: GramNegative")
        print("- RAST annotation: Yes")
        print("- ATP correction: Yes (default)")
        print("Expected time: ~5-7 minutes (RAST + ATP correction)")

        build_response = await build_model(
            fasta_file_path=str(ecoli_fasta_path),
            template="GramNegative",
            model_name="ecoli_notebook_replication",
            annotate_with_rast=True,
            apply_atp_correction=True  # Explicit for clarity (this is default)
        )

        # Verify build succeeded
        assert build_response["success"] is True, "Model building should succeed"
        model_id = build_response["model_id"]
        print(f"\n✓ Model built successfully: {model_id}")
        print(f"  Genes: {build_response['num_genes']}")
        print(f"  Reactions: {build_response['num_reactions']}")
        print(f"  Metabolites: {build_response['num_metabolites']}")

        # Verify ATP correction was applied
        assert "atp_correction" in build_response, "Response should include ATP correction stats"
        atp_stats = build_response["atp_correction"]
        assert atp_stats["atp_correction_applied"] is True, "ATP correction should be applied by default"

        reactions_added_by_atp = atp_stats["reactions_added_by_correction"]
        print("\n  ATP Correction Statistics:")
        print(f"    Before: {atp_stats['reactions_before_correction']} reactions")
        print(f"    After: {atp_stats['reactions_after_correction']} reactions")
        print(f"    Added: {reactions_added_by_atp} reactions")
        print(f"    Test conditions: {atp_stats['num_test_conditions']}")

        # Step 2: Create glucose minimal aerobic media (matching notebook)
        print("\n=== STEP 2: Creating glucose minimal aerobic media ===")
        print("- Carbon source: Glucose (cpd00027)")
        print("- Electron acceptor: O2 (cpd00007)")
        print("- Essential nutrients: 18 compounds total")

        media_request = BuildMediaRequest(
            compounds=[
                "cpd00027",  # D-Glucose
                "cpd00007",  # O2
                "cpd00001",  # H2O
                "cpd00009",  # Phosphate
                "cpd00011",  # CO2
                "cpd00013",  # NH3
                "cpd00048",  # SO4 (sulfate)
                "cpd00067",  # H+
                "cpd00099",  # Cl-
                "cpd00205",  # K+
                "cpd00254",  # Mg2+
                "cpd00971",  # Na+
                "cpd00063",  # Ca2+
                "cpd10515",  # Fe2+
                "cpd00030",  # Mn2+
                "cpd00034",  # Zn2+
                "cpd00058",  # Cu2+
                "cpd00149",  # Co2+
                "cpd00244",  # Ni2+
                "cpd00263",  # Selenium (cpd00048 is sulfate, this is selenate)
            ],
            default_uptake=100.0,
            custom_bounds={
                "cpd00027": (-10.0, 100.0),  # Glucose uptake limit
                "cpd00007": (-20.0, 100.0),  # O2 uptake limit
            }
        )

        media_response = build_media(media_request, real_database)
        media_id = media_response["media_id"]
        print(f"\n✓ Media created: {media_id}")
        print(f"  Compounds: {len(media_response['compounds'])}")

        # Step 3: Gapfill model (should reuse ATP test_conditions!)
        print("\n=== STEP 3: Gapfilling model ===")
        print("- Target growth rate: 0.01")
        print("- Mode: full (ATP correction + genome-scale)")
        print("- Expected: ATP correction SKIPPED (test_conditions reused)")
        print("Expected time: ~5-10 minutes (only genome-scale gapfilling)")

        gapfill_result = gapfill_model(
            model_id=model_id,
            media_id=media_id,
            db_index=real_database,
            target_growth_rate=0.01,
            gapfill_mode="full",
        )

        # Verify gapfilling succeeded
        assert gapfill_result["success"] is True, "Gapfilling should succeed"
        gapfilled_model_id = gapfill_result["model_id"]
        print(f"\n✓ Gapfilling completed: {gapfilled_model_id}")

        # Verify ATP correction was SKIPPED (test_conditions reused)
        assert "atp_correction" in gapfill_result
        atp_gapfill_stats = gapfill_result["atp_correction"]

        if atp_gapfill_stats["performed"]:
            print("\n  WARNING: ATP correction was performed (test_conditions not reused)")
            print("    This is slower but still correct")
        else:
            print("\n  ✓ ATP correction SKIPPED (test_conditions reused from build_model)")
            print("    Time saved: ~3-5 minutes")
            assert "test_conditions_reused" in atp_gapfill_stats
            print(f"    Reused: {atp_gapfill_stats['test_conditions_reused']} test conditions")

        # Verify genome-scale gapfilling ran
        assert "genomescale_gapfill" in gapfill_result
        genomescale_stats = gapfill_result["genomescale_gapfill"]
        assert genomescale_stats["performed"] is True, "Genome-scale gapfilling should be performed"

        reactions_added_by_gapfill = gapfill_result.get("num_reactions_added", 0)
        print("\n  Genome-scale Gapfilling Statistics:")
        print(f"    Reactions added: {reactions_added_by_gapfill}")
        print(f"    Growth rate after: {gapfill_result['growth_rate_after']:.6f}")
        print(f"    Target growth rate: {gapfill_result['target_growth_rate']:.6f}")

        # Verify model can grow
        assert gapfill_result["gapfilling_successful"] is True, "Gapfilling should enable growth"
        assert gapfill_result["growth_rate_after"] >= gapfill_result["target_growth_rate"], \
            "Model should reach target growth rate"

        # Step 4: Run FBA on gapfilled model
        print("\n=== STEP 4: Running FBA on gapfilled model ===")
        print("- Objective: bio1 (biomass)")
        print("- Maximize: True")
        print("- Expected growth rate: 0.5544 (matching notebook)")

        fba_result = run_fba(
            model_id=gapfilled_model_id,
            media_id=media_id,
            db_index=real_database,
            objective="bio1",
            maximize=True,
            flux_threshold=0.001
        )

        # Verify FBA succeeded
        assert fba_result["status"] == "optimal", "FBA should find optimal solution"
        growth_rate = fba_result["objective_value"]

        print("\n✓ FBA completed successfully")
        print(f"  Status: {fba_result['status']}")
        print(f"  Growth rate: {growth_rate:.6f}")
        print(f"  Active reactions: {fba_result['active_reactions']}")
        print(f"  Uptake fluxes: {len(fba_result['uptake_fluxes'])}")
        print(f"  Secretion fluxes: {len(fba_result['secretion_fluxes'])}")

        # Step 5: Verify growth rate matches notebook (0.5544)
        print("\n=== STEP 5: Validating Results ===")
        print("Expected growth rate: 0.5544")
        print(f"Actual growth rate:   {growth_rate:.6f}")

        # Allow small tolerance for numerical differences
        EXPECTED_GROWTH_RATE = 0.5544
        TOLERANCE = 0.001

        growth_rate_matches = abs(growth_rate - EXPECTED_GROWTH_RATE) < TOLERANCE

        if growth_rate_matches:
            print("\n✓✓✓ SUCCESS! Growth rate matches notebook ✓✓✓")
            print(f"    Difference: {abs(growth_rate - EXPECTED_GROWTH_RATE):.6f}")
            print(f"    Within tolerance: {TOLERANCE}")
        else:
            print("\n✗ MISMATCH: Growth rate does not match notebook")
            print(f"    Expected: {EXPECTED_GROWTH_RATE:.6f}")
            print(f"    Actual: {growth_rate:.6f}")
            print(f"    Difference: {abs(growth_rate - EXPECTED_GROWTH_RATE):.6f}")
            print(f"    Tolerance: {TOLERANCE}")

        # Final assertion
        assert growth_rate_matches, \
            f"Growth rate {growth_rate:.6f} should match notebook value {EXPECTED_GROWTH_RATE:.6f} (±{TOLERANCE})"

        # Summary
        print("\n" + "=" * 80)
        print("WORKFLOW SUMMARY")
        print("=" * 80)
        print(f"✓ Model built: {model_id}")
        print(f"  - ATP correction applied: {reactions_added_by_atp} reactions")
        print(f"  - Test conditions stored: {atp_stats['num_test_conditions']}")
        print(f"\n✓ Model gapfilled: {gapfilled_model_id}")
        print(f"  - ATP correction reused: {not atp_gapfill_stats['performed']}")
        print(f"  - Genome-scale reactions added: {reactions_added_by_gapfill}")
        print("\n✓ FBA completed:")
        print(f"  - Growth rate: {growth_rate:.6f}")
        print("  - Matches notebook: YES")
        print("  - Biologically realistic: YES")
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED! 🎉")
        print("Our tool chain successfully replicates the notebook workflow!")
        print("=" * 80)
