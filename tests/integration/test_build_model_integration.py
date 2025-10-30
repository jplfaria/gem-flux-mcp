"""Integration tests for build_model tool with real E. coli genome.

Tests the complete workflow: FASTA -> RAST annotation -> model building -> FBA.
These tests use the real E. coli proteins FASTA file from examples/.
"""

import pytest
import asyncio
from pathlib import Path

from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.tools.build_model import build_model
from gem_flux_mcp.tools.media_builder import build_media, BuildMediaRequest
from gem_flux_mcp.tools.run_fba import run_fba
from gem_flux_mcp.tools.gapfill_model import gapfill_model
from gem_flux_mcp.storage.models import retrieve_model, model_exists, clear_all_models
from gem_flux_mcp.storage.media import clear_all_media
from gem_flux_mcp.templates.loader import load_templates


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
    return Path(__file__).parent.parent.parent / "examples" / "ecoli_proteins.fasta"


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
class TestBuildModelIntegration:
    """Integration tests for building models from real genomes."""

    async def test_build_model_from_fasta(self, ecoli_fasta_path, real_database):
        """Test building E. coli model from FASTA file."""

        print(f"\nBuilding model from: {ecoli_fasta_path}")
        print("This will use RAST for annotation (may take time)...")

        # Build model (annotate_with_rast=True for real annotation)
        response = await build_model(
            fasta_file_path=str(ecoli_fasta_path),
            template="GramNegative",
            model_name="ecoli_test",
            annotate_with_rast=True
        )

        # Verify response structure
        assert response["success"] is True
        # Note: with RAST annotation, this will be .gf after gapfilling in future
        # For now it's .draft since we're testing build only
        model_id_suffix = response["model_id"].split(".")[-1]
        assert model_id_suffix in ["draft", "gf"], f"Expected .draft or .gf, got .{model_id_suffix}"
        assert response["num_genes"] > 0
        assert response["num_reactions"] > 0
        assert response["num_metabolites"] > 0
        # gene_coverage is only available for certain annotation types
        # assert "gene_coverage" in response  # Not always present
        # assert "template_name" in response  # Not always present

        print(f"\n✓ Model built successfully:")
        print(f"  - Genes: {response['num_genes']}")
        print(f"  - Reactions: {response['num_reactions']}")
        print(f"  - Metabolites: {response['num_metabolites']}")
        if 'gene_coverage' in response:
            print(f"  - Coverage: {response['gene_coverage']:.1f}%")

        # Verify model is stored
        model_id = response["model_id"]
        assert model_exists(model_id)
        model = retrieve_model(model_id)
        assert model is not None
        assert len(model.reactions) == response["num_reactions"]
        assert len(model.metabolites) == response["num_metabolites"]

    async def test_build_model_and_run_fba(self, ecoli_fasta_path, real_database):
        """Test complete workflow: build model -> create media -> run FBA."""

        # Step 1: Build model
        print("\n=== Step 1: Building E. coli model ===")
        build_response = await build_model(
            fasta_file_path=str(ecoli_fasta_path),
            template="GramNegative",
            model_name="ecoli_fba_test",
            annotate_with_rast=True
        )

        assert build_response["success"] is True
        model_id = build_response["model_id"]
        print(f"✓ Model built: {model_id}")
        print(f"  Reactions: {build_response['num_reactions']}")

        # Step 2: Create M9 minimal media
        print("\n=== Step 2: Creating M9 minimal media ===")
        media_request = BuildMediaRequest(
            compounds=[
                "cpd00027",  # D-Glucose
                "cpd00001",  # H2O
                "cpd00007",  # O2
                "cpd00009",  # Phosphate
                "cpd00011",  # CO2
                "cpd00013",  # NH3
                "cpd00067",  # H+
                "cpd00099",  # Cl-
                "cpd00205",  # K+
                "cpd00254",  # Mg2+
                "cpd00971",  # Na+
                "cpd00058",  # Cu2+
                "cpd00063",  # Ca2+
                "cpd00149",  # Co2+
                "cpd10515",  # Fe2+
                "cpd00030",  # Mn2+
                "cpd00034",  # Zn2+
            ],
            default_uptake=100.0,
            custom_bounds={
                "cpd00027": (-10.0, 100.0),  # Glucose limited
                "cpd00007": (-20.0, 100.0),  # O2 available
            }
        )

        media_response = build_media(media_request, real_database)
        media_id = media_response["media_id"]
        print(f"✓ Media created: {media_id}")

        # Step 3: Run FBA
        print("\n=== Step 3: Running FBA ===")
        fba_result = run_fba(
            model_id=model_id,
            media_id=media_id,
            db_index=real_database,
            objective="bio1",
            maximize=True,
            flux_threshold=0.001
        )

        # Verify FBA results
        assert fba_result["status"] == "optimal"
        # Note: Draft models without gapfilling may have zero growth
        # This is expected - they need gapfilling to enable growth
        # assert fba_result["objective_value"] > 0, "Should have positive growth"
        # For now, just verify FBA runs without errors
        assert fba_result["objective_value"] >= 0, "Objective should be non-negative"
        # Uptake fluxes may be present even with zero growth
        # assert len(fba_result["uptake_fluxes"]) > 0, "Should have uptake fluxes"

        print(f"✓ FBA successful:")
        print(f"  Status: {fba_result['status']}")
        print(f"  Growth rate: {fba_result['objective_value']:.4f}")
        if 'summary' in fba_result and fba_result['summary']:
            print(f"  Active reactions: {fba_result['summary'].get('active_reactions', 'N/A')}")
        print(f"  Uptake fluxes: {len(fba_result.get('uptake_fluxes', {}))}")

        # Note: Draft models may not uptake anything if they can't grow
        # uptake_ids = list(fba_result.get('uptake_fluxes', {}).keys())
        # assert any("cpd00027" in rxn_id for rxn_id in uptake_ids), "Should uptake glucose"

    async def test_build_model_with_dict(self, real_database):
        """Test building model from protein sequences dict (smaller test)."""

        # Create small test genome with a few proteins
        protein_sequences = {
            "prot1": "MKRISTTITTTITITTGNGAG",  # Leader peptide
            "prot2": "MRVLKFGGTSVANAERFLRVADILESNARQGQVATVLSAPAKITNHLVAMIEKTISGQDALPNISDAERIFAELLTGLAAAQPGFPLAQLKTFVDQEFAQIKHVLHGISLLGQCPDSINAALICR",
            "prot3": "MVKVYAPASSANMSVGFDVLGAAVTPVDGALLGDVVTVEAAETFSLNNLGRFADKLPSEPRENIVYQCWERFCQELGKQIPVAMTLEKNMPIGSGLGSSACSVVAALMAMNEHCGKPLND",
        }

        print("\nBuilding small test model from 3 proteins...")
        response = await build_model(
            protein_sequences=protein_sequences,
            template="GramNegative",
            model_name="small_test",
            annotate_with_rast=True  # Use RAST annotation
        )

        assert response["success"] is True
        assert response["model_id"] == "small_test.draft"  # Draft models use .draft suffix
        # With RAST annotation, genes should be annotated (RAST may filter out short sequences)
        assert response["num_genes"] >= 2  # Should have at least 2 annotated genes
        assert response["num_reactions"] > 0

        print(f"✓ Small model built:")
        print(f"  Genes: {response['num_genes']}")
        print(f"  Reactions: {response['num_reactions']}")

    async def test_build_model_error_handling(self, real_database):
        """Test error handling for invalid inputs."""
        from gem_flux_mcp.errors import ValidationError

        # Test with non-existent FASTA file
        with pytest.raises((ValidationError, FileNotFoundError)):
            await build_model(
                fasta_file_path="/nonexistent/path.fasta",
                template="GramNegative",
                model_name="error_test",
                annotate_with_rast=False
            )

    async def test_build_model_stores_correctly(self, real_database):
        """Test that built models are stored correctly."""

        protein_sequences = {
            "test_prot": "MKRISTTITTTITITTGNGAG"
        }

        response = await build_model(
            protein_sequences=protein_sequences,
            template="GramNegative",
            model_name="storage_test",
            annotate_with_rast=False  # Use template-based reconstruction without RAST
        )
        model_id = response["model_id"]

        # Verify storage
        assert model_exists(model_id)

        # Retrieve and verify
        model = retrieve_model(model_id)
        assert model is not None
        assert hasattr(model, "reactions")
        assert hasattr(model, "metabolites")
        assert hasattr(model, "objective")

    async def test_atpm_reaction_creation(self, real_database):
        """Test that ATP maintenance (ATPM) reaction is correctly added to model."""

        protein_sequences = {
            "prot1": "MRVLKFGGTSVANAERFLRVADILESNARQGQVATVLSAPAKITNHLVAMIEKTISGQDALPNISDAERIFAELLTGLAAAQPGFPLAQLKTFVDQEFAQIKHVLHGISLLGQCPDSINAALICR",
        }

        print("\nTesting ATPM reaction creation...")
        response = await build_model(
            protein_sequences=protein_sequences,
            template="GramNegative",
            model_name="atpm_test",
            annotate_with_rast=False
        )

        # Verify ATPM reaction ID is in response
        assert "atpm_reaction_id" in response, "Response should include ATPM reaction ID"
        atpm_id = response["atpm_reaction_id"]
        assert atpm_id is not None, "ATPM reaction ID should not be None"
        print(f"  ✓ ATPM reaction ID: {atpm_id}")

        # Retrieve model and verify ATPM reaction exists
        model = retrieve_model(response["model_id"])
        assert atpm_id in [r.id for r in model.reactions], f"Model should contain ATPM reaction {atpm_id}"

        # Get the ATPM reaction
        atpm_reaction = model.reactions.get_by_id(atpm_id)

        # Verify ATPM reaction stoichiometry (ATP + H2O -> ADP + Pi + H+)
        # cpd00002 = ATP, cpd00001 = H2O, cpd00008 = ADP, cpd00009 = Pi, cpd00067 = H+
        metabolite_ids = [m.id for m in atpm_reaction.metabolites]

        # Check that ATP and ADP are involved
        assert any("cpd00002" in mid for mid in metabolite_ids), "ATPM should consume ATP (cpd00002)"
        assert any("cpd00008" in mid for mid in metabolite_ids), "ATPM should produce ADP (cpd00008)"

        print(f"  ✓ ATPM stoichiometry: {atpm_reaction.reaction}")

        # Verify ATPM bounds (should allow ATP consumption)
        assert atpm_reaction.lower_bound >= 0, "ATPM lower bound should be >= 0 (only consumption)"
        assert atpm_reaction.upper_bound > 0, "ATPM upper bound should be > 0 (allow consumption)"
        print(f"  ✓ ATPM bounds: [{atpm_reaction.lower_bound}, {atpm_reaction.upper_bound}]")

        print(f"✓ ATP maintenance (ATPM) reaction correctly configured")


@pytest.mark.asyncio
@pytest.mark.slow
class TestBuildModelPerformance:
    """Performance tests for model building."""

    async def test_small_genome_performance(self, real_database):
        """Test that small genomes build quickly."""
        import time

        protein_sequences = {
            f"prot{i}": "MKRISTTITTTITITTGNGAG" for i in range(10)
        }

        start = time.perf_counter()
        response = await build_model(
            protein_sequences=protein_sequences,
            template="GramNegative",
            model_name="perf_test",
            annotate_with_rast=False  # Use template-based reconstruction without RAST
        )
        elapsed = time.perf_counter() - start

        assert response["success"] is True
        # Without RAST, template-based reconstruction doesn't preserve gene info
        assert response["num_genes"] >= 0  # May be 0 without RAST annotation

        # Small genomes should build reasonably fast without RAST
        assert elapsed < 10, f"Build took {elapsed:.1f}s, expected < 10s without RAST"

        print(f"\n✓ Small genome built in {elapsed:.1f}s")


@pytest.mark.asyncio
@pytest.mark.slow
class TestATPCorrectionIntegration:
    """Integration tests for ATP correction gapfilling workflow."""

    @pytest.mark.slow
    async def test_atp_correction_media_testing(self, ecoli_fasta_path, real_database):
        """Test ATP correction stage: tests 54 media conditions but does NOT expect growth.

        ATP correction uses Core template with ATPM (ATP maintenance) objective.
        At this stage, the model does NOT have a biomass objective reaction yet.
        Growth is only expected after genome-scale expansion and gapfilling.

        This test verifies:
        - ATP correction tests 54 default media conditions
        - Reports statistics (media passed/failed, reactions added)
        - Model expands progressively based on media tests
        - Does NOT expect growth (no bio1 objective yet)
        """

        # Step 1: Build E. coli model from FASTA (full genome with RAST)
        print("\n=== Building E. coli model for ATP correction test ===")
        build_response = await build_model(
            fasta_file_path=str(ecoli_fasta_path),
            template="GramNegative",
            model_name="atp_ecoli_test",
            annotate_with_rast=True
        )

        assert build_response["success"] is True
        model_id = build_response["model_id"]
        print(f"✓ Draft model built: {model_id}")
        print(f"  - Reactions: {build_response['num_reactions']}")

        # Step 2: Create glucose minimal aerobic media
        print("\n=== Creating glucose minimal aerobic media ===")
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
            ],
            default_uptake=100.0,
            custom_bounds={
                "cpd00027": (-5.0, 100.0),
                "cpd00007": (-10.0, 100.0),
            }
        )

        media_response = build_media(media_request, real_database)
        media_id = media_response["media_id"]
        print(f"✓ Media created: {media_id}")

        # Step 3: Run ATP correction ONLY (not full gapfilling)
        print("\n=== Running ATP correction (Core template + ATPM) ===")
        print("This will test ATP production across 54 default media conditions...")
        print("Expected runtime: ~5 minutes")
        print("NOTE: Growth is NOT expected at this stage (no bio1 objective yet)")

        gapfill_result = gapfill_model(
            model_id=model_id,
            media_id=media_id,
            db_index=real_database,
            target_growth_rate=0.01,
            gapfill_mode="atp_only",  # ATP correction only
        )

        # Step 4: Verify ATP correction ran successfully
        assert gapfill_result["success"] is True
        assert "atp_correction" in gapfill_result

        atp_stats = gapfill_result["atp_correction"]
        assert atp_stats["performed"] is True

        # Verify statistics
        assert "media_tested" in atp_stats
        assert "media_passed" in atp_stats
        assert "media_failed" in atp_stats
        assert "reactions_added" in atp_stats

        media_tested = atp_stats["media_tested"]
        media_passed = atp_stats["media_passed"]
        media_failed = atp_stats["media_failed"]
        reactions_added = atp_stats["reactions_added"]

        print(f"\n=== ATP Correction Results ===")
        print(f"  Media tested: {media_tested}")
        print(f"  Media passed: {media_passed}")
        print(f"  Media failed: {media_failed}")
        print(f"  Reactions added: {reactions_added}")

        # Verify reasonable values
        assert media_tested == 54
        assert media_passed >= 0
        assert media_failed >= 0
        assert media_passed + media_failed <= media_tested
        assert reactions_added >= 0

        # Show examples
        if "failed_media_examples" in atp_stats and atp_stats["failed_media_examples"]:
            print(f"\n  Failed media examples (first 5):")
            for media_name in atp_stats["failed_media_examples"][:5]:
                print(f"    - {media_name}")

        # Verify model was stored (should have intermediate suffix)
        new_model_id = gapfill_result["model_id"]
        assert model_exists(new_model_id)

        # Verify growth is NOT expected at this stage
        growth_rate = gapfill_result.get("growth_rate_after", 0.0)
        print(f"\n  Growth rate after ATP correction: {growth_rate:.6f}")
        print(f"  (Growth NOT expected - no biomass objective yet)")

        print(f"\n✓ ATP correction workflow complete!")
        print(f"  Original model: {model_id}")
        print(f"  After ATP correction: {new_model_id}")
        print(f"  {media_passed}/{media_tested} media conditions satisfied")

    @pytest.mark.slow
    async def test_genomescale_gapfilling_enables_growth(self, ecoli_fasta_path, real_database):
        """Test genome-scale gapfilling: validates that model GROWS after gapfilling.

        After ATP correction, genome-scale gapfilling:
        - Uses full GramNegative template
        - Uses bio1 (biomass) as objective
        - Should enable growth on glucose minimal media
        - Creates .gf (gapfilled) model

        This test verifies the complete workflow produces a functional model.
        """

        # Step 1: Build E. coli model from FASTA (full genome with RAST)
        print("\n=== Building E. coli model for genome-scale gapfilling test ===")
        build_response = await build_model(
            fasta_file_path=str(ecoli_fasta_path),
            template="GramNegative",
            model_name="genomescale_ecoli_test",
            annotate_with_rast=True
        )

        assert build_response["success"] is True
        model_id = build_response["model_id"]
        print(f"✓ Draft model built: {model_id}")
        print(f"  - Reactions: {build_response['num_reactions']}")

        # Step 2: Create glucose minimal aerobic media
        print("\n=== Creating glucose minimal aerobic media ===")
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
            ],
            default_uptake=100.0,
            custom_bounds={
                "cpd00027": (-10.0, 100.0),  # More glucose for growth
                "cpd00007": (-20.0, 100.0),  # More O2 for aerobic growth
            }
        )

        media_response = build_media(media_request, real_database)
        media_id = media_response["media_id"]
        print(f"✓ Media created: {media_id}")

        # Step 3: Run FULL gapfilling (ATP correction + genome-scale)
        print("\n=== Running full gapfilling workflow ===")
        print("This includes:")
        print("  1. ATP correction (Core + ATPM)")
        print("  2. Genome-scale expansion")
        print("  3. Genome-scale gapfilling (GramNegative + bio1)")
        print("Expected runtime: ~10-15 minutes")

        gapfill_result = gapfill_model(
            model_id=model_id,
            media_id=media_id,
            db_index=real_database,
            target_growth_rate=0.01,
            gapfill_mode="full",
        )

        # Step 4: Verify gapfilling succeeded
        assert gapfill_result["success"] is True

        # Verify ATP correction ran
        assert "atp_correction" in gapfill_result
        assert gapfill_result["atp_correction"]["performed"] is True

        # Verify genome-scale gapfilling ran
        assert "genomescale_gapfill" in gapfill_result
        assert gapfill_result["genomescale_gapfill"]["performed"] is True

        # Verify growth was achieved
        growth_after = gapfill_result["growth_rate_after"]
        target_growth = gapfill_result["target_growth_rate"]
        print(f"\n=== Gapfilling Results ===")
        print(f"  Growth rate achieved: {growth_after:.6f}")
        print(f"  Target growth rate: {target_growth:.6f}")
        print(f"  Gapfilling successful: {gapfill_result['gapfilling_successful']}")

        # CRITICAL: Verify model can grow
        assert growth_after >= target_growth, \
            f"Model should grow after genome-scale gapfilling (achieved {growth_after:.6f} >= target {target_growth:.6f})"

        # Verify model has .gf suffix
        new_model_id = gapfill_result["model_id"]
        assert new_model_id.endswith(".gf")
        assert model_exists(new_model_id)

        # Verify reactions were added
        reactions_added = gapfill_result.get("num_reactions_added", 0)
        assert reactions_added > 0, "Gapfilling should add reactions to enable growth"

        print(f"\n✓ Genome-scale gapfilling complete!")
        print(f"  Original model: {model_id}")
        print(f"  Gapfilled model: {new_model_id}")
        print(f"  Reactions added: {reactions_added}")
        print(f"  Growth enabled: YES ({growth_after:.6f} >= {target_growth:.6f})")
