"""Unit tests for build_model tool.

Tests the build_model MCP tool implementation according to specification
004-build-model-tool.md.

Test Coverage:
    - Valid model building from dict
    - Valid model building from FASTA file
    - Protein sequence validation (invalid amino acids)
    - Template validation
    - Mutually exclusive input validation
    - Model ID generation and storage
    - Model statistics collection
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from gem_flux_mcp.errors import ValidationError, LibraryError
from gem_flux_mcp.storage.models import (
    MODEL_STORAGE,
    clear_all_models,
    model_exists,
)
from gem_flux_mcp.tools.build_model import (
    validate_amino_acid_sequence,
    validate_protein_sequences,
    load_fasta_file,
    dict_to_fasta_file,
    collect_model_statistics,
    build_model,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def cleanup_model_storage():
    """Clear model storage before and after each test."""
    clear_all_models()
    yield
    clear_all_models()


@pytest.fixture
def valid_protein_sequences():
    """Valid protein sequences for testing."""
    return {
        "prot_001": "MKLVINLVGNSGLGKSTFTQRLIN",
        "prot_002": "MKQHKAMIVALERFRKEKRDAALL",
        "prot_003": "MSVALERYGIDEVASIGGLVEVNN",
    }


@pytest.fixture
def invalid_protein_sequences():
    """Invalid protein sequences for testing."""
    return {
        "prot_001": "MKLVINLXVGNS",  # Contains X
        "prot_002": "MKQHKAMI*ALL",  # Contains *
        "prot_003": "MSVALERYGIDE",  # Valid
    }


@pytest.fixture
def mock_template():
    """Mock ModelSEED template."""
    template = Mock()
    template.reactions = [Mock() for _ in range(100)]
    template.metabolites = [Mock() for _ in range(80)]
    template.compartments = ["c0", "e0"]
    return template


@pytest.fixture
def mock_genome():
    """Mock MSGenome."""
    genome = Mock()
    genome.id = "test_genome"
    genome.features = [Mock() for _ in range(3)]
    return genome


@pytest.fixture
def mock_builder():
    """Mock MSBuilder."""
    builder = Mock()

    # Mock model with reactions, metabolites, genes
    model = Mock()
    model.id = "test_model"

    # Create mock metabolites
    metabolites = [Mock(id=f"cpd_{i}_c0") for i in range(8)]
    model.metabolites = metabolites

    # Create mock reactions with proper metabolites attribute
    model.reactions = []
    for i in range(10):
        rxn = Mock(id=f"rxn_{i}_c0", lower_bound=-1000 if i % 2 == 0 else 0, upper_bound=1000)
        # Make metabolites iterable (dict of metabolite -> coefficient)
        rxn.metabolites = {metabolites[i % len(metabolites)]: -1}
        model.reactions.append(rxn)

    # Add some exchange reactions
    for i in range(2):
        ex_rxn = Mock(id=f"EX_cpd00{i}_e0", lower_bound=-10, upper_bound=100)
        ex_rxn.metabolites = {Mock(id=f"cpd00{i}_e0"): -1}
        model.reactions.append(ex_rxn)

    # Add biomass reaction
    bio_rxn = Mock(id="bio1", lower_bound=0, upper_bound=1000)
    bio_rxn.metabolites = {metabolites[0]: -1}
    model.reactions.append(bio_rxn)

    model.genes = [Mock(id=f"gene_{i}") for i in range(3)]

    builder.build_base_model.return_value = model
    builder.add_atpm.return_value = None

    return builder


@pytest.fixture
def temp_fasta_file(valid_protein_sequences):
    """Create temporary FASTA file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".faa", delete=False)

    for protein_id, sequence in valid_protein_sequences.items():
        temp_file.write(f">{protein_id} test protein\n")
        temp_file.write(f"{sequence}\n")

    temp_file.close()
    yield temp_file.name

    # Cleanup
    Path(temp_file.name).unlink(missing_ok=True)


# =============================================================================
# Test Amino Acid Validation
# =============================================================================


class TestAminoAcidValidation:
    """Test amino acid sequence validation."""

    def test_valid_sequence(self):
        """Test validation of valid amino acid sequence."""
        is_valid, invalid_chars = validate_amino_acid_sequence(
            "prot_001", "MKLVINLVGNSGLGKSTFTQRLIN"
        )

        assert is_valid is True
        assert len(invalid_chars) == 0

    def test_invalid_characters_x_and_asterisk(self):
        """Test detection of invalid characters X and *."""
        is_valid, invalid_chars = validate_amino_acid_sequence(
            "prot_001", "MKLVINLXVGNS*"
        )

        assert is_valid is False
        assert len(invalid_chars) == 2
        assert ("X", 7) in invalid_chars
        assert ("*", 12) in invalid_chars

    def test_case_insensitive(self):
        """Test case-insensitive validation."""
        is_valid, invalid_chars = validate_amino_acid_sequence(
            "prot_001", "mklvinlvgnsglgkstftqrlin"
        )

        assert is_valid is True
        assert len(invalid_chars) == 0

    def test_invalid_character_b(self):
        """Test detection of ambiguous amino acid B."""
        is_valid, invalid_chars = validate_amino_acid_sequence(
            "prot_001", "MKLBINLV"
        )

        assert is_valid is False
        assert ("B", 3) in invalid_chars


class TestProteinSequencesValidation:
    """Test protein sequences dictionary validation."""

    def test_valid_sequences(self, valid_protein_sequences):
        """Test validation of valid sequences dict."""
        result = validate_protein_sequences(valid_protein_sequences)

        assert result["valid"] is True
        assert result["num_sequences"] == 3

    def test_empty_dict_error(self):
        """Test error when protein sequences dict is empty."""
        with pytest.raises(ValidationError) as exc_info:
            validate_protein_sequences({})

        error = exc_info.value
        assert error.error_code == "EMPTY_PROTEIN_SEQUENCES"
        assert "cannot be empty" in error.message.lower()

    def test_invalid_amino_acids_error(self, invalid_protein_sequences):
        """Test error when sequences contain invalid amino acids."""
        with pytest.raises(ValidationError) as exc_info:
            validate_protein_sequences(invalid_protein_sequences)

        error = exc_info.value
        assert error.error_code == "INVALID_AMINO_ACIDS"
        assert "invalid amino acid" in error.message.lower()
        assert "prot_001" in error.details["invalid_sequences"]
        assert "prot_002" in error.details["invalid_sequences"]
        assert error.details["num_invalid"] == 2
        assert error.details["num_valid"] == 1

    def test_empty_sequence_error(self):
        """Test error when sequence is empty."""
        with pytest.raises(ValidationError) as exc_info:
            validate_protein_sequences({
                "prot_001": "",
                "prot_002": "MKLVINLV",
            })

        error = exc_info.value
        assert error.error_code == "INVALID_AMINO_ACIDS"
        assert "prot_001" in error.details.get("empty_sequences", [])


# =============================================================================
# Test FASTA File Loading
# =============================================================================


class TestFastaFileLoading:
    """Test FASTA file loading and validation."""

    def test_load_valid_fasta(self, temp_fasta_file):
        """Test loading valid FASTA file."""
        sequences = load_fasta_file(temp_fasta_file)

        assert len(sequences) == 3
        assert "prot_001" in sequences
        assert "prot_002" in sequences
        assert "prot_003" in sequences

    def test_fasta_file_not_found_error(self):
        """Test error when FASTA file not found."""
        with pytest.raises(ValidationError) as exc_info:
            load_fasta_file("/nonexistent/path/file.faa")

        error = exc_info.value
        assert error.error_code == "FASTA_FILE_NOT_FOUND"
        assert "not found" in error.message.lower()

    def test_invalid_fasta_format_error(self):
        """Test error when FASTA format is invalid."""
        # Create temp file with sequence before header
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".faa", delete=False)
        temp_file.write("MKLVINLV\n")  # Sequence before header
        temp_file.write(">prot_001\n")
        temp_file.close()

        try:
            with pytest.raises(ValidationError) as exc_info:
                load_fasta_file(temp_file.name)

            error = exc_info.value
            assert error.error_code == "FASTA_INVALID_FORMAT"
        finally:
            Path(temp_file.name).unlink(missing_ok=True)

    def test_empty_fasta_file_error(self):
        """Test error when FASTA file is empty."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".faa", delete=False)
        temp_file.close()

        try:
            with pytest.raises(ValidationError) as exc_info:
                load_fasta_file(temp_file.name)

            error = exc_info.value
            assert error.error_code == "FASTA_NO_SEQUENCES"
        finally:
            Path(temp_file.name).unlink(missing_ok=True)


# =============================================================================
# Test Dict to FASTA Conversion
# =============================================================================


class TestDictToFasta:
    """Test conversion of dict to FASTA file."""

    def test_dict_to_fasta_conversion(self, valid_protein_sequences):
        """Test converting dict to FASTA file."""
        fasta_path = dict_to_fasta_file(valid_protein_sequences)

        try:
            assert Path(fasta_path).exists()

            # Verify content
            with open(fasta_path, "r") as fh:
                content = fh.read()
                assert ">prot_001" in content
                assert "MKLVINLVGNSGLGKSTFTQRLIN" in content
        finally:
            Path(fasta_path).unlink(missing_ok=True)


# =============================================================================
# Test Model Statistics Collection
# =============================================================================


class TestModelStatistics:
    """Test model statistics collection."""

    def test_collect_statistics(self):
        """Test collecting model statistics."""
        # Create mock model
        model = Mock()
        model.reactions = [
            Mock(id="rxn_001_c0", lower_bound=-1000, upper_bound=1000),
            Mock(id="rxn_002_c0", lower_bound=0, upper_bound=1000),
            Mock(id="EX_cpd00027_e0", lower_bound=-10, upper_bound=100),
            Mock(id="bio1", lower_bound=0, upper_bound=1000),
            Mock(id="ATPM_c0", lower_bound=8.39, upper_bound=1000),
        ]

        # Add metabolites with compartments
        model.reactions[0].metabolites = {
            Mock(id="cpd00001_c0"): -1,
            Mock(id="cpd00002_c0"): 1,
        }
        model.reactions[1].metabolites = {
            Mock(id="cpd00003_c0"): -1,
        }
        model.reactions[2].metabolites = {
            Mock(id="cpd00027_e0"): -1,
        }
        model.reactions[3].metabolites = {
            Mock(id="cpd00010_c0"): -1,
        }
        model.reactions[4].metabolites = {
            Mock(id="cpd00002_c0"): -1,
            Mock(id="cpd00008_c0"): 1,
        }

        model.metabolites = [
            Mock(id="cpd00001_c0"),
            Mock(id="cpd00002_c0"),
            Mock(id="cpd00003_c0"),
            Mock(id="cpd00027_e0"),
        ]

        model.genes = [Mock(id="gene_001"), Mock(id="gene_002")]

        stats = collect_model_statistics(model, "GramNegative")

        assert stats["num_reactions"] == 5
        assert stats["num_metabolites"] == 4
        assert stats["num_genes"] == 2
        assert stats["num_exchange_reactions"] == 1
        assert stats["template_used"] == "GramNegative"
        assert stats["has_biomass_reaction"] is True
        assert stats["has_atpm"] is True
        assert stats["model_properties"]["is_draft"] is True
        assert stats["model_properties"]["requires_gapfilling"] is True


# =============================================================================
# Test build_model Tool
# =============================================================================


class TestBuildModel:
    """Test build_model tool main function."""

    @pytest.mark.asyncio
    @patch("gem_flux_mcp.tools.build_model.validate_template_name")
    @patch("gem_flux_mcp.tools.build_model.get_template")
    @patch("gem_flux_mcp.tools.build_model.MSGenome")
    @patch("gem_flux_mcp.tools.build_model.MSBuilder")
    async def test_build_model_from_dict(
        self,
        mock_msbuilder_class,
        mock_msgenome_class,
        mock_get_template,
        mock_validate_template,
        valid_protein_sequences,
        mock_template,
        mock_genome,
        mock_builder,
    ):
        """Test successful model building from protein sequences dict."""
        # Setup mocks
        mock_validate_template.return_value = True
        mock_get_template.return_value = mock_template
        mock_msgenome_class.from_dict.return_value = mock_genome
        mock_msbuilder_class.return_value = mock_builder

        # Call build_model
        result = await build_model(
            protein_sequences=valid_protein_sequences,
            template="GramNegative",
            model_name="test_model",
        )

        # Verify result
        assert result["success"] is True
        assert result["model_id"].endswith(".draft")
        assert "test_model" in result["model_id"]
        assert result["model_name"] == "test_model"
        assert result["template_used"] == "GramNegative"
        assert result["num_reactions"] > 0

        # Verify model stored
        assert model_exists(result["model_id"])

    @pytest.mark.asyncio
    @patch("gem_flux_mcp.tools.build_model.validate_template_name")
    @patch("gem_flux_mcp.tools.build_model.get_template")
    @patch("gem_flux_mcp.tools.build_model.MSGenome")
    @patch("gem_flux_mcp.tools.build_model.MSBuilder")
    async def test_build_model_from_fasta(
        self,
        mock_msbuilder_class,
        mock_msgenome_class,
        mock_get_template,
        mock_validate_template,
        temp_fasta_file,
        mock_template,
        mock_genome,
        mock_builder,
    ):
        """Test successful model building from FASTA file."""
        # Setup mocks
        mock_validate_template.return_value = True
        mock_get_template.return_value = mock_template
        mock_msgenome_class.from_fasta.return_value = mock_genome
        mock_msbuilder_class.return_value = mock_builder

        # Call build_model
        result = await build_model(
            fasta_file_path=temp_fasta_file,
            template="GramNegative",
        )

        # Verify result
        assert result["success"] is True
        assert result["model_id"].endswith(".draft")
        assert result["template_used"] == "GramNegative"

        # Verify model stored
        assert model_exists(result["model_id"])

    @pytest.mark.asyncio
    async def test_both_inputs_provided_error(self, valid_protein_sequences):
        """Test error when both protein_sequences and fasta_file_path provided."""
        with pytest.raises(ValidationError) as exc_info:
            await build_model(
                protein_sequences=valid_protein_sequences,
                fasta_file_path="/path/to/file.faa",
                template="GramNegative",
            )

        error = exc_info.value
        assert error.error_code == "BOTH_INPUTS_PROVIDED"
        assert "cannot provide both" in error.message.lower()

    @pytest.mark.asyncio
    async def test_no_input_provided_error(self):
        """Test error when neither input provided."""
        with pytest.raises(ValidationError) as exc_info:
            await build_model(template="GramNegative")

        error = exc_info.value
        assert error.error_code == "NO_INPUT_PROVIDED"
        assert "must provide either" in error.message.lower()

    @pytest.mark.asyncio
    @patch("gem_flux_mcp.tools.build_model.validate_template_name")
    async def test_invalid_template_error(self, mock_validate, valid_protein_sequences):
        """Test error when template name is invalid."""
        mock_validate.return_value = False

        with pytest.raises(ValidationError) as exc_info:
            await build_model(
                protein_sequences=valid_protein_sequences,
                template="InvalidTemplate",
            )

        error = exc_info.value
        assert error.error_code == "INVALID_TEMPLATE"
        assert "invalid template" in error.message.lower()

    @pytest.mark.asyncio
    @patch("gem_flux_mcp.tools.build_model.validate_template_name")
    async def test_invalid_amino_acids_error(self, mock_validate, invalid_protein_sequences):
        """Test error when protein sequences contain invalid amino acids."""
        mock_validate.return_value = True

        with pytest.raises(ValidationError) as exc_info:
            await build_model(
                protein_sequences=invalid_protein_sequences,
                template="GramNegative",
            )

        error = exc_info.value
        assert error.error_code == "INVALID_AMINO_ACIDS"
        assert "invalid amino acid" in error.message.lower()
