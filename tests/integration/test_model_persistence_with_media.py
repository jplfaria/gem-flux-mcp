"""
Integration tests for model persistence (save/load) with stored media files.

Tests that models can be:
1. Built and gapfilled
2. Saved to JSON
3. Loaded from JSON
4. Run FBA with stored media file (glucose_minimal_aerobic.json)
5. Produce identical growth rates
"""

import pytest
import json
import tempfile
from pathlib import Path

from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.tools.build_model import build_model
from gem_flux_mcp.tools.gapfill_model import gapfill_model
from gem_flux_mcp.tools.media_builder import build_media, BuildMediaRequest
from gem_flux_mcp.tools.run_fba import run_fba
from gem_flux_mcp.storage.models import clear_all_models, MODEL_STORAGE
from gem_flux_mcp.storage.media import clear_all_media
from gem_flux_mcp.templates.loader import load_templates


class TestModelPersistenceWithMedia:
    """Tests for model save/load with stored media files."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        # Clear storage
        clear_all_models()
        clear_all_media()

        # Setup paths
        self.project_root = Path(__file__).parent.parent.parent
        self.fasta_path = self.project_root / "specs-source" / "build_metabolic_model" / "GCF_000005845.2_ASM584v2_protein.faa"
        self.db_dir = self.project_root / "data" / "database"
        self.template_dir = self.project_root / "data" / "templates"
        self.media_file = self.project_root / "data" / "media" / "glucose_minimal_aerobic.json"

        # Load database
        compounds_df = load_compounds_database(self.db_dir / "compounds.tsv")
        reactions_df = load_reactions_database(self.db_dir / "reactions.tsv")
        self.db_index = DatabaseIndex(compounds_df, reactions_df)

        # Load templates
        load_templates(self.template_dir)

        yield

        # Cleanup
        clear_all_models()
        clear_all_media()

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_save_and_load_model_with_stored_media(self):
        """
        Test complete workflow: build → gapfill → save → load → FBA with stored media.

        Verifies that:
        1. Model can be built and gapfilled
        2. Model can be saved to JSON file
        3. Model can be loaded from JSON file
        4. FBA with stored glucose_minimal_aerobic.json produces expected growth rate
        5. Growth rate matches the expected 0.5544
        """
        # Step 1: Build model with ATP correction
        print("\n=== Step 1: Build Model ===")
        build_response = await build_model(
            fasta_file_path=str(self.fasta_path),
            template="GramNegative",
            model_name="ecoli_persistence_test",
            annotate_with_rast=True,
            apply_atp_correction=True
        )

        assert build_response["success"] is True
        model_id = build_response["model_id"]
        print(f"Model built: {model_id}")
        print(f"  Genes: {build_response['num_genes']}")
        print(f"  Reactions: {build_response['num_reactions']}")

        # Step 2: Load media from stored JSON file
        print("\n=== Step 2: Load Media from File ===")
        with open(self.media_file) as f:
            media_json = json.load(f)

        compounds = []
        custom_bounds = {}
        for cpd_id, cpd_data in media_json['compounds'].items():
            compounds.append(cpd_id)
            custom_bounds[cpd_id] = tuple(cpd_data['bounds'])

        media_request = BuildMediaRequest(
            compounds=compounds,
            default_uptake=100.0,
            custom_bounds=custom_bounds
        )

        media_response = build_media(media_request, self.db_index)
        media_id = media_response["media_id"]
        print(f"Media loaded: {media_id}")
        print(f"  Compounds: {len(media_response['compounds'])}")

        # Step 3: Gapfill model
        print("\n=== Step 3: Gapfill Model ===")
        gapfill_result = gapfill_model(
            model_id=model_id,
            media_id=media_id,
            db_index=self.db_index,
            target_growth_rate=0.01,
            gapfill_mode="full",
        )

        assert gapfill_result["success"] is True
        assert gapfill_result["gapfilling_successful"] is True
        gapfilled_model_id = gapfill_result["model_id"]
        print(f"Gapfilled model: {gapfilled_model_id}")
        print(f"  Growth rate after: {gapfill_result['growth_rate_after']:.6f}")
        print(f"  Reactions added: {gapfill_result.get('num_reactions_added', 0)}")

        # Step 4: Run FBA before saving (baseline)
        print("\n=== Step 4: Run FBA (Before Save) ===")
        fba_before = run_fba(
            model_id=gapfilled_model_id,
            media_id=media_id,
            db_index=self.db_index,
            objective="bio1",
            maximize=True,
            flux_threshold=0.001
        )

        assert fba_before["status"] == "optimal"
        growth_before = fba_before["objective_value"]
        print(f"Growth rate (before save): {growth_before:.6f}")

        # Verify growth rate is close to expected 0.5544
        expected_growth = 0.5544
        assert abs(growth_before - expected_growth) < 0.001, \
            f"Growth rate {growth_before:.6f} differs from expected {expected_growth:.6f}"

        # Step 5: Save model to JSON file
        print("\n=== Step 5: Save Model to JSON ===")
        model_file_path = tempfile.mktemp(suffix='.json')

        # Get model from storage
        model = MODEL_STORAGE[gapfilled_model_id]

        # Save using COBRApy's save_json_model
        from cobra.io import save_json_model
        save_json_model(model, model_file_path)
        print(f"Model saved to: {model_file_path}")

        # Step 6: Clear storage and load model from JSON
        print("\n=== Step 6: Load Model from JSON ===")
        clear_all_models()

        # Load model from JSON file using COBRApy's load_json_model
        from cobra.io import load_json_model
        loaded_model = load_json_model(model_file_path)

        # Store loaded model with new ID
        loaded_model_id = "ecoli_persistence_test.loaded"
        MODEL_STORAGE[loaded_model_id] = loaded_model
        print(f"Model loaded: {loaded_model_id}")
        print(f"  Reactions: {len(loaded_model.reactions)}")
        print(f"  Metabolites: {len(loaded_model.metabolites)}")
        print(f"  Genes: {len(loaded_model.genes)}")

        # Step 7: Re-create media (since storage was cleared)
        print("\n=== Step 7: Re-create Media ===")
        media_response2 = build_media(media_request, self.db_index)
        media_id2 = media_response2["media_id"]
        print(f"Media re-created: {media_id2}")

        # Step 8: Run FBA on loaded model
        print("\n=== Step 8: Run FBA (After Load) ===")
        fba_after = run_fba(
            model_id=loaded_model_id,
            media_id=media_id2,
            db_index=self.db_index,
            objective="bio1",
            maximize=True,
            flux_threshold=0.001
        )

        assert fba_after["status"] == "optimal"
        growth_after = fba_after["objective_value"]
        print(f"Growth rate (after load): {growth_after:.6f}")

        # Step 9: Verify growth rates match
        print("\n=== Step 9: Verify Results ===")
        print(f"Growth rate before save: {growth_before:.6f}")
        print(f"Growth rate after load:  {growth_after:.6f}")
        print(f"Expected growth rate:    {expected_growth:.6f}")
        print(f"Difference (before-after): {abs(growth_before - growth_after):.6f}")

        # Assert growth rates are identical (within numerical precision)
        assert abs(growth_before - growth_after) < 0.000001, \
            f"Growth rates differ: {growth_before:.6f} vs {growth_after:.6f}"

        # Assert both match expected growth rate
        assert abs(growth_after - expected_growth) < 0.001, \
            f"Loaded model growth rate {growth_after:.6f} differs from expected {expected_growth:.6f}"

        print("\n✓ Model persistence test PASSED!")
        print(f"✓ Saved and loaded model produces identical growth rate: {growth_after:.6f}")

        # Cleanup temp file
        Path(model_file_path).unlink()

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_multiple_save_load_cycles(self):
        """
        Test that model can survive multiple save/load cycles.

        Verifies that growth rate remains consistent across:
        1. Initial model
        2. First save/load cycle
        3. Second save/load cycle
        """
        # Build and gapfill model
        print("\n=== Build and Gapfill Model ===")
        build_response = await build_model(
            fasta_file_path=str(self.fasta_path),
            template="GramNegative",
            model_name="ecoli_multi_cycle",
            annotate_with_rast=True,
            apply_atp_correction=True
        )
        model_id = build_response["model_id"]

        # Load media
        with open(self.media_file) as f:
            media_json = json.load(f)

        compounds = []
        custom_bounds = {}
        for cpd_id, cpd_data in media_json['compounds'].items():
            compounds.append(cpd_id)
            custom_bounds[cpd_id] = tuple(cpd_data['bounds'])

        media_request = BuildMediaRequest(
            compounds=compounds,
            default_uptake=100.0,
            custom_bounds=custom_bounds
        )

        media_response = build_media(media_request, self.db_index)
        media_id = media_response["media_id"]

        # Gapfill
        gapfill_result = gapfill_model(
            model_id=model_id,
            media_id=media_id,
            db_index=self.db_index,
            target_growth_rate=0.01,
            gapfill_mode="full",
        )
        gapfilled_model_id = gapfill_result["model_id"]

        # Initial FBA
        fba_initial = run_fba(
            model_id=gapfilled_model_id,
            media_id=media_id,
            db_index=self.db_index,
            objective="bio1",
            maximize=True,
            flux_threshold=0.001
        )
        growth_initial = fba_initial["objective_value"]
        print(f"Initial growth rate: {growth_initial:.6f}")

        growth_rates = [growth_initial]

        # Perform 2 save/load cycles
        current_model_id = gapfilled_model_id

        for cycle in range(1, 3):
            print(f"\n=== Cycle {cycle}: Save and Load ===")

            # Save
            temp_file = tempfile.mktemp(suffix='.json')
            model = MODEL_STORAGE[current_model_id]
            from cobra.io import save_json_model
            save_json_model(model, temp_file)

            # Clear and load
            clear_all_models()

            from cobra.io import load_json_model
            loaded_model = load_json_model(temp_file)

            loaded_model_id = f"ecoli_multi_cycle.cycle{cycle}"
            MODEL_STORAGE[loaded_model_id] = loaded_model

            # Re-create media
            media_response = build_media(media_request, self.db_index)
            media_id = media_response["media_id"]

            # Run FBA
            fba_result = run_fba(
                model_id=loaded_model_id,
                media_id=media_id,
                db_index=self.db_index,
                objective="bio1",
                maximize=True,
                flux_threshold=0.001
            )

            growth = fba_result["objective_value"]
            growth_rates.append(growth)
            print(f"Cycle {cycle} growth rate: {growth:.6f}")

            current_model_id = loaded_model_id

            # Cleanup temp file
            Path(temp_file).unlink()

        # Verify all growth rates match
        print("\n=== Verify Consistency Across Cycles ===")
        for i, growth in enumerate(growth_rates):
            print(f"Cycle {i}: {growth:.6f}")

        # All growth rates should be identical
        for i in range(len(growth_rates) - 1):
            diff = abs(growth_rates[i] - growth_rates[i+1])
            assert diff < 0.000001, \
                f"Growth rate changed between cycles: {growth_rates[i]:.6f} vs {growth_rates[i+1]:.6f}"

        print(f"\n✓ Multiple save/load cycles test PASSED!")
        print(f"✓ Growth rate remained stable across {len(growth_rates)} measurements")
