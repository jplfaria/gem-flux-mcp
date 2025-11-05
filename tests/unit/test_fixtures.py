"""Tests to validate all comprehensive test fixtures work correctly.

This test file ensures all fixtures defined in conftest.py are properly
configured and return expected data structures.
"""

from pathlib import Path


class TestProteinSequenceFixtures:
    """Test protein sequence fixtures."""

    def test_comprehensive_protein_sequences_dict(self, comprehensive_protein_sequences_dict):
        """Test comprehensive protein sequence dictionary fixture."""
        assert isinstance(comprehensive_protein_sequences_dict, dict)
        assert len(comprehensive_protein_sequences_dict) > 0

        # Verify key sequences present
        assert "ecoli_hex" in comprehensive_protein_sequences_dict
        assert "ecoli_pgk" in comprehensive_protein_sequences_dict
        assert "short_protein" in comprehensive_protein_sequences_dict
        assert "long_protein" in comprehensive_protein_sequences_dict

        # Verify sequences are valid strings
        for seq_id, sequence in comprehensive_protein_sequences_dict.items():
            assert isinstance(sequence, str)
            assert len(sequence) > 0

    def test_comprehensive_protein_sequences_fasta(self, comprehensive_protein_sequences_fasta):
        """Test comprehensive protein sequence FASTA fixture."""
        assert isinstance(comprehensive_protein_sequences_fasta, str)

        # Verify file exists
        fasta_path = Path(comprehensive_protein_sequences_fasta)
        assert fasta_path.exists()
        assert fasta_path.suffix == ".faa"

        # Verify file content
        content = fasta_path.read_text()
        assert content.startswith(">")
        assert "ecoli_hex" in content
        assert "MKLVINLVGNSGLGK" in content

    def test_invalid_protein_sequences(self, invalid_protein_sequences):
        """Test invalid protein sequence fixture."""
        assert isinstance(invalid_protein_sequences, dict)
        assert len(invalid_protein_sequences) > 0

        # Verify invalid sequences present
        assert "has_stop" in invalid_protein_sequences
        assert "has_unknown" in invalid_protein_sequences
        assert "*" in invalid_protein_sequences["has_stop"]
        assert "X" in invalid_protein_sequences["has_unknown"]

    def test_edge_case_protein_sequences(self, edge_case_protein_sequences):
        """Test edge case protein sequence fixture."""
        assert isinstance(edge_case_protein_sequences, dict)

        # Verify edge cases
        assert "very_long" in edge_case_protein_sequences
        assert "just_methionine" in edge_case_protein_sequences
        assert len(edge_case_protein_sequences["very_long"]) > 10000
        assert all(aa == "M" for aa in edge_case_protein_sequences["just_methionine"])


class TestCompoundIDFixtures:
    """Test ModelSEED compound ID fixtures."""

    def test_comprehensive_compound_ids(self, comprehensive_compound_ids):
        """Test comprehensive compound IDs fixture."""
        assert isinstance(comprehensive_compound_ids, dict)
        assert len(comprehensive_compound_ids) > 40  # At least 40 compounds

        # Verify core metabolites
        assert "water" in comprehensive_compound_ids
        assert "glucose" in comprehensive_compound_ids
        assert "oxygen" in comprehensive_compound_ids

        # Verify ID format
        assert comprehensive_compound_ids["water"] == "cpd00001"
        assert comprehensive_compound_ids["glucose"] == "cpd00027"

        # Verify all IDs match pattern cpd#####
        for compound_id in comprehensive_compound_ids.values():
            assert compound_id.startswith("cpd")
            assert len(compound_id) == 8

    def test_comprehensive_compound_metadata(self, comprehensive_compound_metadata):
        """Test comprehensive compound metadata fixture."""
        assert isinstance(comprehensive_compound_metadata, dict)

        # Verify glucose metadata
        glucose = comprehensive_compound_metadata["cpd00027"]
        assert glucose["name"] == "D-Glucose"
        assert glucose["formula"] == "C6H12O6"
        assert glucose["mass"] == 180.156
        assert glucose["charge"] == 0

    def test_invalid_compound_ids(self, invalid_compound_ids):
        """Test invalid compound IDs fixture."""
        assert isinstance(invalid_compound_ids, list)
        assert len(invalid_compound_ids) > 0

        # Verify various invalid patterns
        assert "cpd99999" in invalid_compound_ids
        assert "" in invalid_compound_ids


class TestReactionIDFixtures:
    """Test ModelSEED reaction ID fixtures."""

    def test_comprehensive_reaction_ids(self, comprehensive_reaction_ids):
        """Test comprehensive reaction IDs fixture."""
        assert isinstance(comprehensive_reaction_ids, dict)
        assert len(comprehensive_reaction_ids) > 20

        # Verify glycolysis reactions
        assert "hexokinase" in comprehensive_reaction_ids
        assert comprehensive_reaction_ids["hexokinase"] == "rxn00148"

        # Verify TCA cycle reactions
        assert "citrate_synthase" in comprehensive_reaction_ids
        assert "malate_dehydrogenase" in comprehensive_reaction_ids

        # Verify all IDs match pattern rxn#####
        for reaction_id in comprehensive_reaction_ids.values():
            assert reaction_id.startswith("rxn")
            assert len(reaction_id) == 8

    def test_comprehensive_reaction_metadata(self, comprehensive_reaction_metadata):
        """Test comprehensive reaction metadata fixture."""
        assert isinstance(comprehensive_reaction_metadata, dict)

        # Verify hexokinase metadata
        hex_rxn = comprehensive_reaction_metadata["rxn00148"]
        assert hex_rxn["name"] == "hexokinase"
        assert hex_rxn["ec_numbers"] == "2.7.1.1"
        assert hex_rxn["direction_symbol"] == ">"
        assert hex_rxn["is_transport"] is False

    def test_invalid_reaction_ids(self, invalid_reaction_ids):
        """Test invalid reaction IDs fixture."""
        assert isinstance(invalid_reaction_ids, list)
        assert len(invalid_reaction_ids) > 0

        assert "rxn99999" in invalid_reaction_ids
        assert "" in invalid_reaction_ids


class TestMediaCompositionFixtures:
    """Test media composition fixtures."""

    def test_comprehensive_media_compositions(self, comprehensive_media_compositions):
        """Test comprehensive media compositions fixture."""
        assert isinstance(comprehensive_media_compositions, dict)
        assert len(comprehensive_media_compositions) >= 4

        # Verify glucose minimal aerobic
        glucose_aerobic = comprehensive_media_compositions["glucose_minimal_aerobic"]
        assert "cpd00027" in glucose_aerobic["compounds"]  # Glucose
        assert "cpd00007" in glucose_aerobic["compounds"]  # O2
        assert glucose_aerobic["default_uptake"] == 100.0
        assert "cpd00027" in glucose_aerobic["custom_bounds"]

        # Verify glucose minimal anaerobic
        glucose_anaerobic = comprehensive_media_compositions["glucose_minimal_anaerobic"]
        assert "cpd00027" in glucose_anaerobic["compounds"]  # Glucose
        # Oxygen should be blocked
        assert glucose_anaerobic["custom_bounds"]["cpd00007"] == (0.0, 0.0)

        # Verify rich media
        rich = comprehensive_media_compositions["rich_media"]
        assert len(rich["compounds"]) > 40  # Many compounds

    def test_media_with_custom_bounds(self, media_with_custom_bounds):
        """Test media with custom bounds fixture."""
        assert isinstance(media_with_custom_bounds, dict)

        # Verify uptake only
        uptake_only = media_with_custom_bounds["uptake_only"]
        for bound in uptake_only["custom_bounds"].values():
            assert bound[1] == 0.0  # Upper bound = 0 (no secretion)

        # Verify secretion only
        secretion_only = media_with_custom_bounds["secretion_only"]
        for bound in secretion_only["custom_bounds"].values():
            assert bound[0] == 0.0  # Lower bound = 0 (no uptake)

        # Verify blocked
        blocked = media_with_custom_bounds["blocked"]
        assert blocked["custom_bounds"]["cpd00027"] == (0.0, 0.0)

    def test_invalid_media_compositions(self, invalid_media_compositions):
        """Test invalid media compositions fixture."""
        assert isinstance(invalid_media_compositions, dict)

        # Verify empty compounds
        assert invalid_media_compositions["empty_compounds"]["compounds"] == []

        # Verify invalid bounds format
        invalid_bounds = invalid_media_compositions["invalid_bounds_format"]
        bounds = invalid_bounds["custom_bounds"]["cpd00027"]
        assert bounds[0] > bounds[1]  # Invalid: lower > upper


class TestModelSEEDpyMocks:
    """Test ModelSEEDpy class mocks."""

    def test_mock_msgenome(self, mock_msgenome):
        """Test MSGenome mock."""
        assert mock_msgenome.id == "test_genome"
        assert isinstance(mock_msgenome.features, list)
        assert hasattr(mock_msgenome, "add_feature")

    def test_mock_msgenome_from_dict(self, mock_msgenome_from_dict):
        """Test MSGenome.from_dict mock."""
        assert mock_msgenome_from_dict.id == "test_genome_from_dict"
        assert len(mock_msgenome_from_dict.features) == 2

    def test_mock_msbuilder(self, mock_msbuilder):
        """Test MSBuilder mock."""
        model = mock_msbuilder.build()
        assert model.id.endswith(".draft")
        assert model.num_reactions == 856
        assert hasattr(model, "optimize")

    def test_mock_msbuilder_with_stats(self, mock_msbuilder_with_stats):
        """Test MSBuilder with stats mock."""
        model = mock_msbuilder_with_stats.build()
        assert model.num_reactions == 856
        assert model.num_metabolites == 742
        assert model.num_genes == 150
        assert model.template_used == "GramNegative"
        assert len(model.compartments) == 3

    def test_mock_msgapfill(self, mock_msgapfill):
        """Test MSGapfill mock."""
        solution = mock_msgapfill.run_gapfilling()
        assert solution.success is True
        assert solution.growth_rate == 0.874

    def test_mock_msgapfill_with_reactions(self, mock_msgapfill_with_reactions):
        """Test MSGapfill with reactions mock."""
        solution = mock_msgapfill_with_reactions.run_gapfilling()
        assert solution.num_reactions_added == 3
        assert len(solution.reactions_added) == 3
        assert solution.growth_rate_before == 0.0
        assert solution.growth_rate_after == 0.874

    def test_mock_msatpcorrection(self, mock_msatpcorrection):
        """Test MSATPCorrection mock."""
        assert mock_msatpcorrection.media_tested == 27
        assert mock_msatpcorrection.media_feasible == 27
        result = mock_msatpcorrection.run_atp_correction()
        assert result is True

    def test_mock_msmedia(self, mock_msmedia):
        """Test MSMedia mock."""
        assert mock_msmedia.id == "test_media"
        assert isinstance(mock_msmedia.compounds, list)
        assert hasattr(mock_msmedia, "get_media_constraints")

    def test_mock_msmedia_from_dict(self, mock_msmedia_from_dict):
        """Test MSMedia.from_dict mock."""
        assert mock_msmedia_from_dict.id == "glucose_minimal"
        assert len(mock_msmedia_from_dict.compounds) == 4
        constraints = mock_msmedia_from_dict.get_media_constraints()
        assert "cpd00027_e0" in constraints

    def test_mock_mstemplate(self, mock_mstemplate):
        """Test MSTemplate mock."""
        assert mock_mstemplate.id == "GramNegative"
        assert mock_mstemplate.num_reactions == 2035
        assert mock_mstemplate.num_compounds == 1542  # Templates use .compounds, not .metabolites
        assert len(mock_mstemplate.compartments) == 3
        assert len(mock_mstemplate.reactions) == 20

    def test_mock_mstemplate_core(self, mock_mstemplate_core):
        """Test Core MSTemplate mock."""
        assert mock_mstemplate_core.id == "Core"
        assert mock_mstemplate_core.num_reactions == 452
        assert (
            mock_mstemplate_core.num_compounds == 325
        )  # Templates use .compounds, not .metabolites
        assert len(mock_mstemplate_core.compartments) == 2


class TestCOBRApyMocks:
    """Test COBRApy mocks."""

    def test_mock_cobra_model(self, mock_cobra_model):
        """Test basic COBRApy model mock."""
        assert mock_cobra_model.id.endswith(".gf")
        solution = mock_cobra_model.optimize()
        assert solution.objective_value == 0.85
        assert solution.status == "optimal"

    def test_mock_cobra_model_with_fluxes(self, mock_cobra_model_with_fluxes):
        """Test COBRApy model with fluxes mock."""
        solution = mock_cobra_model_with_fluxes.optimize()
        assert solution.objective_value == 0.874
        assert solution.status == "optimal"
        assert "bio1" in solution.fluxes
        assert solution.fluxes["bio1"] == 0.874
        assert solution.active_reactions == 423

    def test_mock_cobra_model_infeasible(self, mock_cobra_model_infeasible):
        """Test infeasible COBRApy model mock."""
        solution = mock_cobra_model_infeasible.optimize()
        assert solution.status == "infeasible"
        assert solution.objective_value is None

    def test_mock_cobra_solution_optimal(self, mock_cobra_solution_optimal):
        """Test optimal solution mock."""
        assert mock_cobra_solution_optimal.status == "optimal"
        assert mock_cobra_solution_optimal.objective_value == 0.874
        assert len(mock_cobra_solution_optimal.fluxes) > 0

    def test_mock_cobra_solution_infeasible(self, mock_cobra_solution_infeasible):
        """Test infeasible solution mock."""
        assert mock_cobra_solution_infeasible.status == "infeasible"
        assert mock_cobra_solution_infeasible.objective_value is None

    def test_mock_cobra_solution_unbounded(self, mock_cobra_solution_unbounded):
        """Test unbounded solution mock."""
        assert mock_cobra_solution_unbounded.status == "unbounded"
        assert mock_cobra_solution_unbounded.objective_value == float("inf")


class TestSessionStorageMocks:
    """Test session storage mocks."""

    def test_mock_model_storage(self, mock_model_storage, mock_cobra_model):
        """Test model storage mock."""
        # Store a model
        mock_model_storage["store"]("model_001", mock_cobra_model)

        # Retrieve model
        retrieved = mock_model_storage["get"]("model_001")
        assert retrieved is mock_cobra_model

        # List models
        models = mock_model_storage["list"]()
        assert "model_001" in models

        # Delete model
        result = mock_model_storage["delete"]("model_001")
        assert result is True

        # Verify deleted
        assert "model_001" not in mock_model_storage["list"]()

    def test_mock_media_storage(self, mock_media_storage, mock_msmedia):
        """Test media storage mock."""
        # Store media
        mock_media_storage["store"]("media_001", mock_msmedia)

        # Retrieve media
        retrieved = mock_media_storage["get"]("media_001")
        assert retrieved is mock_msmedia

        # List media
        media = mock_media_storage["list"]()
        assert "media_001" in media


class TestIntegrationHelpers:
    """Test integration test helper fixtures."""

    def test_temp_test_dir(self, temp_test_dir):
        """Test temporary test directory fixture."""
        assert temp_test_dir.exists()
        assert temp_test_dir.is_dir()

        # Create a test file
        test_file = temp_test_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
