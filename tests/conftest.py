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
    genome.genes = []
    genome.name = "Test Genome"
    # Add method mocks
    genome.add_feature = Mock(return_value=True)
    genome.get_feature = Mock(return_value=None)
    return genome


@pytest.fixture
def mock_msgenome_from_dict():
    """Mock MSGenome.from_dict factory method."""
    genome = Mock()
    genome.id = "test_genome_from_dict"
    genome.features = [
        {"id": "gene1", "sequence": "MKLAVTCDEF"},
        {"id": "gene2", "sequence": "MSVALERYGIDEVASIGGLV"}
    ]
    return genome


@pytest.fixture
def mock_msgenome_from_fasta():
    """Mock MSGenome.from_fasta factory method."""
    genome = Mock()
    genome.id = "test_genome_from_fasta"
    genome.features = [
        {"id": "ecoli_hex", "sequence": "MKLVINLVGNSGLGKSTFTQRLIN"},
        {"id": "ecoli_pgk", "sequence": "MKQHKAMIVALERFRKEKRDAALL"}
    ]
    return genome


@pytest.fixture
def mock_msbuilder():
    """Mock MSBuilder class for model construction."""
    builder = Mock()
    model = Mock()
    model.id = "test_model.draft"  # Using .draft notation for new models
    model.reactions = []
    model.metabolites = []
    model.genes = []
    model.num_reactions = 856
    model.num_metabolites = 742
    # Add COBRApy-like methods
    model.add_reactions = Mock()
    model.remove_reactions = Mock()
    model.optimize = Mock()
    builder.build.return_value = model
    builder.build_base_model = Mock(return_value=model)
    return builder


@pytest.fixture
def mock_msbuilder_with_stats():
    """Mock MSBuilder with realistic model statistics."""
    builder = Mock()
    model = Mock()
    model.id = "test_model.draft"

    # Realistic statistics for E. coli-like model
    model.num_reactions = 856
    model.num_metabolites = 742
    model.num_genes = 150
    model.num_exchange_reactions = 95

    # Mock reaction/metabolite lists
    model.reactions = [Mock(id=f"rxn{i:05d}_c0") for i in range(1, 11)]
    model.metabolites = [Mock(id=f"cpd{i:05d}_c0") for i in range(1, 11)]
    model.genes = [Mock(id=f"gene{i}") for i in range(1, 6)]

    # Template info
    model.template_used = "GramNegative"
    model.compartments = ["c0", "e0", "p0"]

    builder.build.return_value = model
    builder.template = Mock(name="GramNegative")
    return builder


@pytest.fixture
def mock_msgapfill():
    """Mock MSGapfill class for gapfilling operations."""
    gapfiller = Mock()
    solution = Mock()
    solution.reactions_added = []
    solution.success = True
    solution.growth_rate = 0.874
    gapfiller.run_gapfilling.return_value = solution
    gapfiller.gapfill_count = 0
    return gapfiller


@pytest.fixture
def mock_msgapfill_with_reactions():
    """Mock MSGapfill with realistic gapfilling results."""
    gapfiller = Mock()
    solution = Mock()

    # Mock reactions that were added
    solution.reactions_added = [
        {"id": "rxn05459_c0", "name": "fumarate reductase"},
        {"id": "rxn05481_c0", "name": "malate dehydrogenase"},
        {"id": "rxn05482_c0", "name": "pyruvate formate lyase"},
    ]
    solution.num_reactions_added = 3
    solution.success = True
    solution.growth_rate_before = 0.0
    solution.growth_rate_after = 0.874

    gapfiller.run_gapfilling.return_value = solution
    gapfiller.model = Mock(id="test_model.draft")
    gapfiller.media = Mock(id="test_media")
    return gapfiller


@pytest.fixture
def mock_msatpcorrection():
    """Mock MSATPCorrection class for ATP gapfilling."""
    atp_corrector = Mock()

    # Mock ATP correction results
    atp_corrector.media_tested = 27
    atp_corrector.media_feasible = 27
    atp_corrector.reactions_added = []

    atp_corrector.run_atp_correction = Mock(return_value=True)
    return atp_corrector


@pytest.fixture
def mock_msmedia():
    """Mock MSMedia class for growth media."""
    media = Mock()
    media.id = "test_media"
    media.compounds = []
    media.mediacompounds = {}
    media.get_media_constraints = Mock(return_value={})
    return media


@pytest.fixture
def mock_msmedia_from_dict():
    """Mock MSMedia.from_dict factory method with realistic data."""
    media = Mock()
    media.id = "glucose_minimal"
    media.name = "Glucose Minimal Media"

    # Mock compound list
    media.compounds = [
        "cpd00027_e0",  # Glucose
        "cpd00007_e0",  # O2
        "cpd00001_e0",  # H2O
        "cpd00009_e0",  # Phosphate
    ]

    # Mock media constraints
    media.mediacompounds = {
        "cpd00027_e0": (-5.0, 100.0),
        "cpd00007_e0": (-10.0, 100.0),
        "cpd00001_e0": (-100.0, 100.0),
        "cpd00009_e0": (-100.0, 100.0),
    }

    media.get_media_constraints = Mock(return_value=media.mediacompounds)
    return media


@pytest.fixture
def mock_mstemplate():
    """Mock MSTemplate for template-based model building."""
    template = Mock()
    template.id = "GramNegative"
    template.name = "Gram-Negative Bacteria Template"
    template.version = "6.0"

    # Mock template statistics
    template.num_reactions = 2035
    template.num_compounds = 1542  # Templates use .compounds, not .metabolites
    template.compartments = ["c0", "e0", "p0"]

    # Mock reaction and compound lists
    template.reactions = [Mock(id=f"rxn{i:05d}") for i in range(1, 21)]
    template.compounds = [Mock(id=f"cpd{i:05d}") for i in range(1, 21)]  # Templates use .compounds

    return template


@pytest.fixture
def mock_mstemplate_core():
    """Mock MSTemplate for Core template."""
    template = Mock()
    template.id = "Core"
    template.name = "Core Metabolic Template"
    template.version = "5.2"

    # Mock template statistics
    template.num_reactions = 452
    template.num_compounds = 325  # Templates use .compounds, not .metabolites
    template.compartments = ["c0", "e0"]

    # Mock reaction and compound lists (smaller than GramNegative)
    template.reactions = [Mock(id=f"rxn{i:05d}") for i in range(1, 11)]
    template.compounds = [Mock(id=f"cpd{i:05d}") for i in range(1, 11)]  # Templates use .compounds

    return template


# ============================================================================
# COBRApy Mocks
# ============================================================================

@pytest.fixture
def mock_cobra_model():
    """Mock COBRApy Model for FBA operations."""
    model = Mock()
    model.id = "test_model.draft.gf"
    model.reactions = []
    model.metabolites = []
    model.genes = []

    # Mock optimization
    solution = Mock()
    solution.objective_value = 0.85
    solution.status = "optimal"
    solution.fluxes = {}
    model.optimize.return_value = solution

    return model


@pytest.fixture
def mock_cobra_model_with_fluxes():
    """Mock COBRApy Model with realistic flux distribution."""
    model = Mock()
    model.id = "test_model.draft.gf"

    # Mock reaction/metabolite lists
    model.reactions = [Mock(id=f"rxn{i:05d}_c0") for i in range(1, 21)]
    model.metabolites = [Mock(id=f"cpd{i:05d}_c0") for i in range(1, 21)]
    model.genes = [Mock(id=f"gene{i}") for i in range(1, 11)]

    # Mock optimization solution
    solution = Mock()
    solution.objective_value = 0.874
    solution.status = "optimal"
    solution.fluxes = {
        "bio1": 0.874,                  # Biomass
        "EX_cpd00027_e0": -5.0,        # Glucose uptake
        "EX_cpd00007_e0": -10.234,     # O2 uptake
        "EX_cpd00011_e0": 8.456,       # CO2 secretion
        "rxn00148_c0": 5.0,            # Hexokinase
        "rxn00342_c0": 4.5,            # Glycolysis
        "rxn00352_c0": 3.2,            # TCA cycle
    }

    # Mock active/total reactions
    solution.active_reactions = 423
    solution.total_reactions = 856

    model.optimize.return_value = solution

    # Mock medium property
    model.medium = {
        "EX_cpd00027_e0": 5.0,
        "EX_cpd00007_e0": 10.0,
    }

    return model


@pytest.fixture
def mock_cobra_model_infeasible():
    """Mock COBRApy Model that returns infeasible solution."""
    model = Mock()
    model.id = "test_model.draft"

    # Mock infeasible optimization
    solution = Mock()
    solution.objective_value = None
    solution.status = "infeasible"
    solution.fluxes = {}
    model.optimize.return_value = solution

    return model


@pytest.fixture
def mock_cobra_solution_optimal():
    """Mock optimal FBA solution."""
    solution = Mock()
    solution.objective_value = 0.874
    solution.status = "optimal"
    solution.fluxes = {
        "bio1": 0.874,
        "EX_cpd00027_e0": -5.0,
        "EX_cpd00007_e0": -10.0,
        "rxn00148_c0": 5.0,
    }
    solution.shadow_prices = {}
    solution.reduced_costs = {}
    return solution


@pytest.fixture
def mock_cobra_solution_infeasible():
    """Mock infeasible FBA solution."""
    solution = Mock()
    solution.objective_value = None
    solution.status = "infeasible"
    solution.fluxes = {}
    return solution


@pytest.fixture
def mock_cobra_solution_unbounded():
    """Mock unbounded FBA solution."""
    solution = Mock()
    solution.objective_value = float('inf')
    solution.status = "unbounded"
    solution.fluxes = {}
    return solution


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


# ============================================================================
# Comprehensive Protein Sequence Fixtures
# ============================================================================

@pytest.fixture
def comprehensive_protein_sequences_dict():
    """Comprehensive protein sequences dictionary covering various scenarios."""
    return {
        # Real E. coli proteins (truncated for testing)
        "ecoli_hex": "MKLVINLVGNSGLGKSTFTQRLINSLQIDEDVRKQLAELSALQRGVKVVLTGSKGVTTS" \
                     "HIAPERDVDLLAKLGVEVTTSGKMTSFVSRAKEKYNEKASQIAKELFPQYLGGVKD",
        "ecoli_pgk": "MKQHKAMIVALERFRKEKRDAALLNLVRNPVADAGVIHYVDAKK",

        # Different length proteins
        "short_protein": "MKLAVTCDEF",  # 10 aa
        "medium_protein": "MKLAVTCDEFGHIKLMNPQRSTVWYAACDEFGHIKLMNPQRSTVWY",  # 46 aa
        "long_protein": "M" + "ACDEFGHIKLMNPQRSTVWY" * 20,  # 401 aa

        # Edge cases
        "single_aa": "M",
        "all_amino_acids": "ACDEFGHIKLMNPQRSTVWY",
        "repeated_motif": "MKLAVT" * 10,

        # Realistic protein sequences
        "glycolysis_enzyme": "MKLVINLVGNSGLGKSTFTQRLINSLQIDEDVRKQLAELS",
        "tca_enzyme": "MSVALERYGIDEVASIGGLVEVNNQYLNSSNGIIKQLLKKL",
        "biosynthesis_enzyme": "MTIKVGINGFGRIGRLVLRAALFGKDKEVDVVAVNDPFI"
    }


@pytest.fixture
def comprehensive_protein_sequences_fasta(tmp_path):
    """Comprehensive protein sequences in FASTA format."""
    fasta_content = """>ecoli_hex hexokinase from E. coli
MKLVINLVGNSGLGKSTFTQRLINSLQIDEDVRKQLAELSALQRGVKVVLTGSKGVTTS
HIAPERDVDLLAKLGVEVTTSGKMTSFVSRAKEKYNEKASQIAKELFPQYLGGVKD
>ecoli_pgk phosphoglycerate kinase
MKQHKAMIVALERFRKEKRDAALLNLVRNPVADAGVIHYVDAKK
>short_protein minimal test protein
MKLAVTCDEF
>glycolysis_enzyme glycolysis pathway enzyme
MKLVINLVGNSGLGKSTFTQRLINSLQIDEDVRKQLAELS
>tca_enzyme TCA cycle enzyme
MSVALERYGIDEVASIGGLVEVNNQYLNSSNGIIKQLLKKL
"""
    fasta_file = tmp_path / "test_proteins.faa"
    fasta_file.write_text(fasta_content)
    return str(fasta_file)


@pytest.fixture
def invalid_protein_sequences():
    """Invalid protein sequences for error testing."""
    return {
        "has_stop": "MKLAV*TCDEF",  # Contains stop codon
        "has_unknown": "MKLAVXTCDEF",  # Contains unknown amino acid X
        "has_ambiguous_b": "MKLAVBTCDEF",  # Contains ambiguous B
        "has_ambiguous_z": "MKLAVZTCDEF",  # Contains ambiguous Z
        "has_number": "MKLAV5TCDEF",  # Contains number
        "has_lowercase": "mklavtcdef",  # Lowercase (should be handled, but testing)
    }


@pytest.fixture
def edge_case_protein_sequences():
    """Edge case protein sequences for boundary testing."""
    return {
        "very_long": "M" + "ACDEFGHIKLMNPQRSTVWY" * 500,  # 10,001 aa
        "just_methionine": "M" * 100,  # Homopolymer
        "alternating": "MK" * 50,  # Alternating pattern
        "no_start_codon": "ACDEFGHIKLMNPQRSTVWY",  # No methionine start
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
# Comprehensive Media Composition Fixtures
# ============================================================================

@pytest.fixture
def comprehensive_media_compositions():
    """Comprehensive media compositions for different growth conditions."""
    return {
        "glucose_minimal_aerobic": {
            "id": "glucose_minimal_aerobic",
            "name": "Glucose Minimal Media (Aerobic)",
            "compounds": [
                "cpd00027",  # D-Glucose
                "cpd00007",  # O2
                "cpd00001",  # H2O
                "cpd00009",  # Phosphate
                "cpd00011",  # CO2
                "cpd00013",  # NH3
                "cpd00067",  # H+
                "cpd00099",  # Cl-
                "cpd00205",  # K+
                "cpd00254",  # Mg2+
                "cpd00971",  # Na+
                "cpd10515",  # Fe2+
                "cpd00048",  # Sulfate
            ],
            "default_uptake": 100.0,
            "custom_bounds": {
                "cpd00027": (-5.0, 100.0),   # Glucose limited
                "cpd00007": (-10.0, 100.0),  # Oxygen available
            }
        },
        "glucose_minimal_anaerobic": {
            "id": "glucose_minimal_anaerobic",
            "name": "Glucose Minimal Media (Anaerobic)",
            "compounds": [
                "cpd00027",  # D-Glucose
                "cpd00001",  # H2O
                "cpd00009",  # Phosphate
                "cpd00011",  # CO2
                "cpd00013",  # NH3
                "cpd00067",  # H+
                "cpd00099",  # Cl-
                "cpd00205",  # K+
                "cpd00254",  # Mg2+
                "cpd00971",  # Na+
                "cpd10515",  # Fe2+
                "cpd00048",  # Sulfate
            ],
            "default_uptake": 100.0,
            "custom_bounds": {
                "cpd00027": (-10.0, 100.0),  # Higher glucose for anaerobic
                "cpd00007": (0.0, 0.0),      # No oxygen
            }
        },
        "pyruvate_minimal": {
            "id": "pyruvate_minimal",
            "name": "Pyruvate Minimal Media",
            "compounds": [
                "cpd00020",  # Pyruvate
                "cpd00007",  # O2
                "cpd00001",  # H2O
                "cpd00009",  # Phosphate
                "cpd00011",  # CO2
                "cpd00013",  # NH3
                "cpd00067",  # H+
                "cpd00099",  # Cl-
                "cpd00205",  # K+
                "cpd00254",  # Mg2+
                "cpd00971",  # Na+
                "cpd10515",  # Fe2+
                "cpd00048",  # Sulfate
            ],
            "default_uptake": 100.0,
            "custom_bounds": {
                "cpd00020": (-10.0, 100.0),  # Pyruvate
                "cpd00007": (-10.0, 100.0),  # Oxygen
            }
        },
        "rich_media": {
            "id": "rich_media",
            "name": "Rich Media (LB-like)",
            "compounds": [
                # Carbon sources
                "cpd00027", "cpd00020", "cpd00029", "cpd00100",
                # Amino acids (all 20)
                "cpd00035", "cpd00051", "cpd00132", "cpd00041", "cpd00084",
                "cpd00023", "cpd00053", "cpd00033", "cpd00119", "cpd00322",
                "cpd00107", "cpd00039", "cpd00060", "cpd00066", "cpd00129",
                "cpd00054", "cpd00161", "cpd00065", "cpd00069", "cpd00156",
                # Vitamins and cofactors
                "cpd00010", "cpd00982", "cpd00975",
                # Core metabolites
                "cpd00001", "cpd00007", "cpd00009", "cpd00011", "cpd00013", "cpd00067",
                # Ions
                "cpd00099", "cpd00205", "cpd00254", "cpd00971", "cpd10515",
                "cpd00048", "cpd00063", "cpd00030", "cpd00034", "cpd00058",
            ],
            "default_uptake": 100.0,
            "custom_bounds": {
                "cpd00007": (-20.0, 100.0),  # High oxygen for rich media
            }
        },
        "minimal_no_carbon": {
            "id": "minimal_no_carbon",
            "name": "Minimal Media Without Carbon Source",
            "compounds": [
                "cpd00001",  # H2O
                "cpd00007",  # O2
                "cpd00009",  # Phosphate
                "cpd00013",  # NH3
                "cpd00067",  # H+
                "cpd00099",  # Cl-
                "cpd00205",  # K+
                "cpd00254",  # Mg2+
                "cpd00048",  # Sulfate
            ],
            "default_uptake": 100.0,
            "custom_bounds": {}
        }
    }


@pytest.fixture
def media_with_custom_bounds():
    """Media compositions with various custom bound configurations."""
    return {
        "uptake_only": {
            "compounds": ["cpd00027", "cpd00007"],
            "default_uptake": 100.0,
            "custom_bounds": {
                "cpd00027": (-5.0, 0.0),   # Uptake only, no secretion
                "cpd00007": (-10.0, 0.0),  # Uptake only
            }
        },
        "secretion_only": {
            "compounds": ["cpd00011", "cpd00067"],  # CO2, H+
            "default_uptake": 0.0,
            "custom_bounds": {
                "cpd00011": (0.0, 100.0),  # Secretion only
                "cpd00067": (0.0, 100.0),  # Secretion only
            }
        },
        "bidirectional": {
            "compounds": ["cpd00027", "cpd00001"],
            "default_uptake": 100.0,
            "custom_bounds": {
                "cpd00027": (-5.0, 5.0),   # Both uptake and secretion
                "cpd00001": (-100.0, 100.0),  # Fully bidirectional
            }
        },
        "blocked": {
            "compounds": ["cpd00027"],
            "default_uptake": 100.0,
            "custom_bounds": {
                "cpd00027": (0.0, 0.0),  # Completely blocked
            }
        }
    }


@pytest.fixture
def invalid_media_compositions():
    """Invalid media compositions for error testing."""
    return {
        "empty_compounds": {
            "compounds": [],  # No compounds
            "default_uptake": 100.0,
        },
        "invalid_compound_ids": {
            "compounds": ["cpd99999", "cpd00000"],  # Non-existent
            "default_uptake": 100.0,
        },
        "negative_default_uptake": {
            "compounds": ["cpd00027"],
            "default_uptake": -100.0,  # Invalid negative
        },
        "invalid_bounds_format": {
            "compounds": ["cpd00027"],
            "default_uptake": 100.0,
            "custom_bounds": {
                "cpd00027": (5.0, -5.0),  # Lower > Upper (invalid)
            }
        }
    }


# ============================================================================
# Comprehensive ModelSEED Compound ID Fixtures
# ============================================================================

@pytest.fixture
def comprehensive_compound_ids():
    """Comprehensive set of ModelSEED compound IDs for testing."""
    return {
        # Core metabolites
        "water": "cpd00001",
        "oxygen": "cpd00007",
        "phosphate": "cpd00009",
        "co2": "cpd00011",
        "ammonia": "cpd00013",
        "proton": "cpd00067",

        # Carbon sources
        "glucose": "cpd00027",
        "pyruvate": "cpd00020",
        "acetate": "cpd00029",
        "lactose": "cpd00108",
        "glycerol": "cpd00100",
        "succinate": "cpd00036",

        # Amino acids (essential set)
        "L-alanine": "cpd00035",
        "L-arginine": "cpd00051",
        "L-asparagine": "cpd00132",
        "L-aspartate": "cpd00041",
        "L-cysteine": "cpd00084",
        "L-glutamate": "cpd00023",
        "L-glutamine": "cpd00053",
        "glycine": "cpd00033",
        "L-histidine": "cpd00119",
        "L-isoleucine": "cpd00322",
        "L-leucine": "cpd00107",
        "L-lysine": "cpd00039",
        "L-methionine": "cpd00060",
        "L-phenylalanine": "cpd00066",
        "L-proline": "cpd00129",
        "L-serine": "cpd00054",
        "L-threonine": "cpd00161",
        "L-tryptophan": "cpd00065",
        "L-tyrosine": "cpd00069",
        "L-valine": "cpd00156",

        # Energy metabolites
        "ATP": "cpd00002",
        "ADP": "cpd00008",
        "AMP": "cpd00018",
        "NAD": "cpd00003",
        "NADH": "cpd00004",
        "NADP": "cpd00006",
        "NADPH": "cpd00005",

        # Cofactors
        "CoA": "cpd00010",
        "FAD": "cpd00982",
        "FMN": "cpd00975",

        # Ions
        "chloride": "cpd00099",
        "potassium": "cpd00205",
        "magnesium": "cpd00254",
        "sodium": "cpd00971",
        "iron2": "cpd10515",
        "iron3": "cpd10516",
        "calcium": "cpd00063",
        "manganese": "cpd00030",
        "zinc": "cpd00034",
        "sulfate": "cpd00048",
        "copper": "cpd00058",
        "cobalt": "cpd00149",
        "nickel": "cpd00244",
    }


@pytest.fixture
def comprehensive_compound_metadata():
    """Comprehensive compound metadata for enriched testing."""
    return {
        "cpd00027": {
            "id": "cpd00027",
            "name": "D-Glucose",
            "abbreviation": "glc__D",
            "formula": "C6H12O6",
            "mass": 180.156,
            "charge": 0,
            "inchikey": "WQZGKKKJIJFFOK-GASJEMHNSA-N",
            "smiles": "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O",
            "aliases": "KEGG: C00031|BiGG: glc__D|MetaCyc: GLC"
        },
        "cpd00020": {
            "id": "cpd00020",
            "name": "Pyruvate",
            "abbreviation": "pyr",
            "formula": "C3H3O3",
            "mass": 87.055,
            "charge": -1,
            "inchikey": "LCTONWCANYUPML-UHFFFAOYSA-M",
            "smiles": "[O-]C(=O)C(=O)C",
            "aliases": "KEGG: C00022|BiGG: pyr|MetaCyc: PYRUVATE"
        },
        "cpd00007": {
            "id": "cpd00007",
            "name": "O2",
            "abbreviation": "o2",
            "formula": "O2",
            "mass": 31.999,
            "charge": 0,
            "inchikey": "MYMOFIZGZYHOMD-UHFFFAOYSA-N",
            "smiles": "O=O",
            "aliases": "KEGG: C00007|BiGG: o2|MetaCyc: OXYGEN-MOLECULE"
        }
    }


@pytest.fixture
def invalid_compound_ids():
    """Invalid compound IDs for error testing."""
    return [
        "cpd99999",  # Non-existent
        "cpd00000",  # Edge case ID
        "rxn00001",  # Reaction ID instead of compound
        "cpd001",    # Wrong format (too short)
        "cpd0000001", # Wrong format (too long)
        "CPD00027",  # Wrong case
        "compound_00027",  # Wrong prefix
        "",          # Empty string
        "cpd00abc",  # Non-numeric
    ]


# ============================================================================
# Comprehensive ModelSEED Reaction ID Fixtures
# ============================================================================

@pytest.fixture
def comprehensive_reaction_ids():
    """Comprehensive set of ModelSEED reaction IDs for testing."""
    return {
        # Glycolysis reactions
        "hexokinase": "rxn00148",
        "phosphoglucose_isomerase": "rxn01100",
        "phosphofructokinase": "rxn00345",
        "aldolase": "rxn00341",
        "triose_phosphate_isomerase": "rxn00344",
        "glyceraldehyde_3p_dehydrogenase": "rxn00342",
        "phosphoglycerate_kinase": "rxn00343",
        "phosphoglycerate_mutase": "rxn00346",
        "enolase": "rxn00347",
        "pyruvate_kinase": "rxn00348",

        # TCA cycle reactions
        "citrate_synthase": "rxn00352",
        "aconitase": "rxn00353",
        "isocitrate_dehydrogenase": "rxn00354",
        "alpha_ketoglutarate_dehydrogenase": "rxn00355",
        "succinyl_coa_synthetase": "rxn00356",
        "succinate_dehydrogenase": "rxn00357",
        "fumarase": "rxn00358",
        "malate_dehydrogenase": "rxn00359",

        # Pentose phosphate pathway
        "glucose_6p_dehydrogenase": "rxn00371",
        "6_phosphogluconate_dehydrogenase": "rxn00372",

        # Transport reactions
        "glucose_transport": "rxn05478",
        "oxygen_transport": "rxn08518",

        # Biomass
        "biomass_reaction": "rxn00001",

        # ATP synthesis
        "atp_synthase": "rxn00062",
    }


@pytest.fixture
def comprehensive_reaction_metadata():
    """Comprehensive reaction metadata for enriched testing."""
    return {
        "rxn00148": {
            "id": "rxn00148",
            "name": "hexokinase",
            "abbreviation": "HEX1",
            "equation": "D-Glucose + ATP => ADP + H+ + D-Glucose 6-phosphate",
            "equation_with_ids": "(1) cpd00027[c0] + (1) cpd00002[c0] => (1) cpd00008[c0] + (1) cpd00067[c0] + (1) cpd00079[c0]",
            "reversibility": "irreversible_forward",
            "direction_symbol": ">",
            "ec_numbers": "2.7.1.1",
            "pathways": "Glycolysis|Central Metabolism",
            "is_transport": False,
            "aliases": "KEGG: R00200|BiGG: HEX1|MetaCyc: GLUCOKIN-RXN"
        },
        "rxn00359": {
            "id": "rxn00359",
            "name": "malate dehydrogenase",
            "abbreviation": "MDH",
            "equation": "Malate + NAD <=> Oxaloacetate + NADH + H+",
            "equation_with_ids": "(1) cpd00130[c0] + (1) cpd00003[c0] <=> (1) cpd00036[c0] + (1) cpd00004[c0] + (1) cpd00067[c0]",
            "reversibility": "reversible",
            "direction_symbol": "=",
            "ec_numbers": "1.1.1.37",
            "pathways": "TCA Cycle|Central Metabolism",
            "is_transport": False,
            "aliases": "KEGG: R00342|BiGG: MDH|MetaCyc: MALATE-DEH-RXN"
        }
    }


@pytest.fixture
def invalid_reaction_ids():
    """Invalid reaction IDs for error testing."""
    return [
        "rxn99999",  # Non-existent
        "rxn00000",  # Edge case ID
        "cpd00027",  # Compound ID instead of reaction
        "rxn001",    # Wrong format (too short)
        "rxn0000001", # Wrong format (too long)
        "RXN00148",  # Wrong case
        "reaction_00148",  # Wrong prefix
        "",          # Empty string
        "rxn00abc",  # Non-numeric
    ]


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
    config.addinivalue_line(
        "markers", "real_llm: mark test as requiring real LLM API calls (expensive, slow, requires argo-proxy)"
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


# ============================================================================
# Argo LLM Integration Fixtures (Phase 11.5)
# ============================================================================

@pytest.fixture
def argo_available():
    """Check if argo-proxy is available on localhost:8000.

    Skips test if argo-proxy is not running.
    Used for real LLM integration tests.
    """
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()

    if result != 0:
        pytest.skip("argo-proxy not running on localhost:8000")
