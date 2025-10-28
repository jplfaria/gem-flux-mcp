"""Pytest configuration and fixtures for Gem-Flux MCP Server tests."""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
import pandas as pd


# ============================================================================
# Test Database Mocks
# ============================================================================

@pytest.fixture
def mock_compounds_df():
    """Mock compounds DataFrame for testing."""
    data = {
        "id": ["cpd00001", "cpd00007", "cpd00009", "cpd00011", "cpd00027"],
        "name": ["H2O", "O2", "Phosphate", "CO2", "D-Glucose"],
        "abbreviation": ["h2o", "o2", "pi", "co2", "glc__D"],
        "formula": ["H2O", "O2", "HO4P", "CO2", "C6H12O6"],
        "mass": [18.0, 32.0, 95.0, 44.0, 180.0],
        "charge": [0, 0, -2, 0, 0],
        "inchikey": ["", "", "", "", "WQZGKKKJIJFFOK-GASJEMHNSA-N"],
        "smiles": ["", "", "", "", "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O"],
        "aliases": ["", "", "", "", "KEGG: C00031|BiGG: glc__D"],
    }
    df = pd.DataFrame(data)
    df = df.set_index("id")
    return df


@pytest.fixture
def mock_reactions_df():
    """Mock reactions DataFrame for testing."""
    data = {
        "id": ["rxn00001", "rxn00148"],
        "name": ["Test Reaction", "hexokinase"],
        "abbreviation": ["TEST", "HEX1"],
        "equation": ["A <=> B", "D-Glucose + ATP => ADP + H+ + D-Glucose-6-phosphate"],
        "definition": ["", ""],
        "stoichiometry": ["", ""],
        "reversibility": ["=", ">"],
        "is_transport": [0, 0],
        "ec_numbers": ["", "2.7.1.1"],
        "pathways": ["", "Glycolysis"],
        "aliases": ["", "KEGG: R00200|BiGG: HEX1"],
    }
    df = pd.DataFrame(data)
    df = df.set_index("id")
    return df


@pytest.fixture
def mock_modelseed_database():
    """Mock ModelSEED database for testing without loading 49MB of files."""
    db = Mock()
    db.compounds = {
        "cpd00001": {"id": "cpd00001", "name": "H2O", "formula": "H2O"},
        "cpd00007": {"id": "cpd00007", "name": "O2", "formula": "O2"},
        "cpd00009": {"id": "cpd00009", "name": "Phosphate", "formula": "PO4"},
    }
    db.reactions = {
        "rxn00001": {"id": "rxn00001", "name": "Test Reaction", "equation": "A <=> B"},
    }
    db.get_compound = lambda cpd_id: db.compounds.get(cpd_id)
    db.get_reaction = lambda rxn_id: db.reactions.get(rxn_id)
    return db


@pytest.fixture
def mock_template():
    """Mock ModelSEED template for testing."""
    template = Mock()
    template.reactions = []
    template.name = "GramNegative"
    return template


# ============================================================================
# ModelSEEDpy Class Mocks
# ============================================================================

@pytest.fixture
def mock_msgenome():
    """Mock MSGenome class for genome data handling."""
    genome = Mock()
    genome.id = "test_genome"
    genome.features = []
    return genome


@pytest.fixture
def mock_msbuilder():
    """Mock MSBuilder class for model construction."""
    builder = Mock()
    model = Mock()
    model.id = "test_model.gf"  # Using .gf notation
    model.reactions = []
    model.metabolites = []
    builder.build.return_value = model
    return builder


@pytest.fixture
def mock_msgapfill():
    """Mock MSGapfill class for gapfilling operations."""
    gapfiller = Mock()
    solution = Mock()
    solution.reactions_added = []
    solution.success = True
    gapfiller.run_gapfilling.return_value = solution
    return gapfiller


@pytest.fixture
def mock_msmedia():
    """Mock MSMedia class for growth media."""
    media = Mock()
    media.id = "test_media"
    media.compounds = []
    return media


# ============================================================================
# COBRApy Mocks
# ============================================================================

@pytest.fixture
def mock_cobra_model():
    """Mock COBRApy Model for FBA operations."""
    model = Mock()
    model.id = "test_model.gf"
    model.reactions = []
    model.metabolites = []

    # Mock optimization
    solution = Mock()
    solution.objective_value = 0.85
    solution.status = "optimal"
    solution.fluxes = {}
    model.optimize.return_value = solution

    return model


# ============================================================================
# Session Storage Mocks
# ============================================================================

@pytest.fixture
def mock_model_storage():
    """Mock in-memory model storage session."""
    storage = {}

    def store_model(model_id, model):
        storage[model_id] = model

    def get_model(model_id):
        return storage.get(model_id)

    def list_models():
        return list(storage.keys())

    def delete_model(model_id):
        if model_id in storage:
            del storage[model_id]
            return True
        return False

    return {
        "store": store_model,
        "get": get_model,
        "list": list_models,
        "delete": delete_model,
        "storage": storage
    }


@pytest.fixture
def mock_media_storage():
    """Mock in-memory media storage session."""
    storage = {}

    def store_media(media_id, media):
        storage[media_id] = media

    def get_media(media_id):
        return storage.get(media_id)

    def list_media():
        return list(storage.keys())

    return {
        "store": store_media,
        "get": get_media,
        "list": list_media,
        "storage": storage
    }


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_genome_fasta():
    """Sample FASTA genome data for testing."""
    return ">gene1\nATGCGATCGATCGATC\n>gene2\nCGATCGATCGATCGAT\n"


@pytest.fixture
def sample_genome_dict():
    """Sample genome dictionary for testing."""
    return {
        "id": "test_genome",
        "features": [
            {"id": "gene1", "sequence": "ATGCGATCGATCGATC"},
            {"id": "gene2", "sequence": "CGATCGATCGATCGAT"},
        ]
    }


@pytest.fixture
def sample_media_compounds():
    """Sample compound list for media creation."""
    return ["cpd00001", "cpd00007", "cpd00009"]  # H2O, O2, Phosphate


@pytest.fixture
def predefined_media_minimal():
    """Predefined minimal media composition."""
    return {
        "id": "minimal",
        "name": "Minimal Media",
        "compounds": ["cpd00001", "cpd00007", "cpd00009", "cpd00011"]
    }


# ============================================================================
# Integration Test Helpers
# ============================================================================

@pytest.fixture
def temp_test_dir(tmp_path):
    """Temporary directory for test file operations."""
    test_dir = tmp_path / "gem_flux_test"
    test_dir.mkdir()
    return test_dir


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on location."""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark slow tests (those involving actual ModelSEEDpy operations)
        if any(keyword in item.nodeid for keyword in ["workflow", "end_to_end", "gapfill"]):
            item.add_marker(pytest.mark.slow)
