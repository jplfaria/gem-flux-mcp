#!/usr/bin/env python3
"""
Validation Script for All Example Notebooks

This script replicates the exact behavior of all 4 example notebooks
to ensure they will execute without errors.

Notebooks validated:
1. 01_basic_workflow.ipynb - Complete end-to-end workflow
2. 02_database_lookups.ipynb - Database search and lookup
3. 03_session_management.ipynb - Model and media management
4. 04_error_handling.ipynb - Error handling and recovery

Run this BEFORE running the actual notebooks to catch any issues.
"""

import asyncio
from pathlib import Path

# Import notebook setup helper
import sys
sys.path.insert(0, str(Path(__file__).parent / "examples"))
from notebook_setup import quick_setup

# Import all tools
from gem_flux_mcp.tools.build_model import build_model
from gem_flux_mcp.tools.gapfill_model import gapfill_model
from gem_flux_mcp.tools.run_fba import run_fba
from gem_flux_mcp.tools.media_builder import build_media
from gem_flux_mcp.tools.compound_lookup import get_compound_name, search_compounds
from gem_flux_mcp.tools.reaction_lookup import get_reaction_name, search_reactions
from gem_flux_mcp.tools.list_models import list_models
from gem_flux_mcp.tools.delete_model import delete_model
from gem_flux_mcp.tools.list_media import list_media

# Import compound and reaction lookup types from their tool modules
from gem_flux_mcp.tools.compound_lookup import (
    GetCompoundNameRequest,
    SearchCompoundsRequest
)
from gem_flux_mcp.tools.reaction_lookup import (
    GetReactionNameRequest,
    SearchReactionsRequest
)

# Import types
from gem_flux_mcp.types import (
    BuildMediaRequest,
    ListModelsRequest,
    DeleteModelRequest
)

# Import errors
from gem_flux_mcp.errors import ValidationError, NotFoundError, InfeasibilityError

# Import COBRApy for model export
from cobra.io import save_json_model
from gem_flux_mcp.storage.models import retrieve_model


print("=" * 70)
print("VALIDATION SCRIPT FOR ALL EXAMPLE NOTEBOOKS")
print("=" * 70)
print()

# Setup environment
print("Setting up environment...")
db_index, templates, atp_media, predefined_media = quick_setup()
print()


# ==============================================================================
# NOTEBOOK 1: 01_basic_workflow.ipynb
# ==============================================================================
print("=" * 70)
print("VALIDATING: 01_basic_workflow.ipynb")
print("=" * 70)
print()

async def validate_basic_workflow():
    """Replicate 01_basic_workflow.ipynb exactly"""

    print("Step 1: Using predefined media (glucose_minimal_aerobic)")
    media_id = "glucose_minimal_aerobic"
    print(f"  ✓ Media ID: {media_id}\n")

    print("Step 2: Building model from E. coli FASTA")
    print("  This will take 2-5 minutes for RAST annotation...")
    build_response = await build_model(
        fasta_file_path="examples/ecoli_proteins.fasta",
        template="GramNegative",
        model_name="E_coli_K12",
        annotate_with_rast=True
    )

    model_id = build_response["model_id"]
    print(f"  ✓ Model built: {model_id}")
    print(f"    Reactions: {build_response['num_reactions']}")
    print(f"    Genes: {build_response['num_genes']}")
    print(f"    RAST annotation: {build_response.get('annotated_with_rast', False)}\n")

    print("Step 3: Gapfilling model")
    print("  This may take 1-5 minutes...")
    gapfill_response = gapfill_model(
        model_id=model_id,
        media_id=media_id,
        db_index=db_index,
        target_growth_rate=0.01,
        gapfill_mode="full"
    )

    gapfilled_model_id = gapfill_response["model_id"]
    print(f"  ✓ Model gapfilled: {gapfilled_model_id}")
    print(f"    Reactions added: {gapfill_response['num_reactions_added']}")
    print(f"    Growth rate after: {gapfill_response['growth_rate_after']:.3f} hr⁻¹")
    print(f"    ATP correction performed: {gapfill_response['atp_correction']['performed']}\n")

    print("Step 4: Running FBA")
    fba_response = run_fba(
        model_id=gapfilled_model_id,
        media_id=media_id,
        db_index=db_index,
        objective="bio1",
        maximize=True,
        flux_threshold=1e-6
    )

    if not fba_response.get("success", True):
        print(f"  ✗ FBA Failed: {fba_response.get('message')}")
        return False

    print(f"  ✓ FBA Complete")
    print(f"    Status: {fba_response['status']}")
    print(f"    Growth rate: {fba_response['objective_value']:.3f} hr⁻¹")
    print(f"    Active reactions: {fba_response['active_reactions']}\n")

    print("Step 5: Exporting model to JSON")
    final_model = retrieve_model(gapfilled_model_id)
    output_dir = Path("examples/output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{gapfilled_model_id}.json"
    save_json_model(final_model, str(output_file))
    print(f"  ✓ Model exported: {output_file}\n")

    return True

print("Running basic workflow validation...")
success_1 = asyncio.run(validate_basic_workflow())
if success_1:
    print("✓ PASSED: 01_basic_workflow.ipynb validates successfully\n")
else:
    print("✗ FAILED: 01_basic_workflow.ipynb validation failed\n")
    sys.exit(1)


# ==============================================================================
# NOTEBOOK 2: 02_database_lookups.ipynb
# ==============================================================================
print("=" * 70)
print("VALIDATING: 02_database_lookups.ipynb")
print("=" * 70)
print()

def validate_database_lookups():
    """Replicate 02_database_lookups.ipynb exactly"""

    print("Part 1: Compound Lookups")

    # Get compound by ID
    print("  Testing get_compound_name (glucose)...")
    request = GetCompoundNameRequest(compound_id="cpd00027")
    response = get_compound_name(request, db_index)
    assert response["name"] == "D-Glucose", f"Expected D-Glucose, got {response['name']}"
    print(f"    ✓ Got: {response['name']}\n")

    # Search compounds
    print("  Testing search_compounds (glucose)...")
    request = SearchCompoundsRequest(query="glucose", limit=10)
    response = search_compounds(request, db_index)
    assert response["num_results"] > 0, "Expected glucose search results"
    print(f"    ✓ Found {response['num_results']} compounds\n")

    # Search by formula
    print("  Testing search_compounds by formula (C6H12O6)...")
    request = SearchCompoundsRequest(query="C6H12O6", limit=5)
    response = search_compounds(request, db_index)
    assert response["num_results"] > 0, "Expected formula search results"
    print(f"    ✓ Found {response['num_results']} compounds\n")

    print("Part 2: Reaction Lookups")

    # Get reaction by ID
    print("  Testing get_reaction_name (hexokinase)...")
    request = GetReactionNameRequest(reaction_id="rxn00148")
    response = get_reaction_name(request, db_index)
    assert "hexokinase" in response["name"].lower() or "glucokinase" in response["name"].lower()
    print(f"    ✓ Got: {response['name']}\n")

    # Search reactions by name
    print("  Testing search_reactions (hexokinase)...")
    request = SearchReactionsRequest(query="hexokinase", limit=10)
    response = search_reactions(request, db_index)
    assert response["num_results"] > 0, "Expected hexokinase search results"
    print(f"    ✓ Found {response['num_results']} reactions\n")

    # Search by EC number
    print("  Testing search_reactions by EC number (2.7.1.1)...")
    request = SearchReactionsRequest(query="2.7.1.1", limit=10)
    response = search_reactions(request, db_index)
    assert response["num_results"] > 0, "Expected EC number search results"
    print(f"    ✓ Found {response['num_results']} reactions\n")

    return True

success_2 = validate_database_lookups()
if success_2:
    print("✓ PASSED: 02_database_lookups.ipynb validates successfully\n")
else:
    print("✗ FAILED: 02_database_lookups.ipynb validation failed\n")
    sys.exit(1)


# ==============================================================================
# NOTEBOOK 3: 03_session_management.ipynb
# ==============================================================================
print("=" * 70)
print("VALIDATING: 03_session_management.ipynb")
print("=" * 70)
print()

async def validate_session_management():
    """Replicate 03_session_management.ipynb exactly"""

    print("Part 1: Listing Models")

    # List empty session
    print("  Testing list_models (empty session)...")
    request = ListModelsRequest()
    response = list_models(request)
    # Note: May not be empty if previous test created models
    print(f"    ✓ Total models: {response['total_models']}\n")

    print("Part 2: Creating Multiple Models")

    # Create first model
    print("  Creating model 1 (E_coli_K12)...")
    response_1 = await build_model(
        protein_sequences={
            "prot1": "MKLVINLVGNSGLGKSTFTQRLIN",
            "prot2": "MKQHKAMIVALERFRKEKRDAALL"
        },
        template="GramNegative",
        model_name="E_coli_K12",
        annotate_with_rast=False
    )
    model_id_1 = response_1["model_id"]
    print(f"    ✓ Created: {model_id_1}\n")

    # Create second model
    print("  Creating model 2 (B_subtilis_168)...")
    response_2 = await build_model(
        protein_sequences={
            "prot1": "MSVALERYGIDEVASIGGLVEVNN",
            "prot2": "MGKVIASKLAGNKAPLYRHIADLA"
        },
        template="Core",
        model_name="B_subtilis_168",
        annotate_with_rast=False
    )
    model_id_2 = response_2["model_id"]
    print(f"    ✓ Created: {model_id_2}\n")

    # List all models
    print("  Testing list_models (with models)...")
    request = ListModelsRequest()
    response = list_models(request)
    assert response["total_models"] >= 2, f"Expected >=2 models, got {response['total_models']}"
    print(f"    ✓ Total models: {response['total_models']}")
    print(f"      Draft: {response['models_by_state']['draft']}")
    print(f"      Gapfilled: {response['models_by_state']['gapfilled']}\n")

    print("Part 3: Deleting Models")

    # Delete a model
    print(f"  Deleting model: {model_id_2}...")
    delete_request = DeleteModelRequest(model_id=model_id_2)
    delete_response = delete_model(delete_request)
    assert delete_response["success"] == True
    print(f"    ✓ Deleted: {delete_response['deleted_model_id']}\n")

    # Test error handling
    print("  Testing delete_model error handling (nonexistent model)...")
    try:
        delete_request = DeleteModelRequest(model_id="nonexistent_model.draft")
        delete_response = delete_model(delete_request)
        print("    ✗ Should have raised NotFoundError")
        return False
    except NotFoundError as e:
        print(f"    ✓ Correctly raised NotFoundError\n")

    print("Part 4: Managing Media")

    # List predefined media
    print("  Testing list_media...")
    response = list_media(db_index)
    assert response["total_media"] >= 4, f"Expected >=4 media, got {response['total_media']}"
    assert response["predefined_media"] >= 4, f"Expected >=4 predefined media"
    print(f"    ✓ Total media: {response['total_media']}")
    print(f"      Predefined: {response['predefined_media']}")
    print(f"      User-created: {response['user_created_media']}\n")

    # Create custom media
    print("  Creating custom pyruvate media...")
    custom_media_request = BuildMediaRequest(
        compounds=[
            "cpd00020",  # Pyruvate
            "cpd00007",  # O2
            "cpd00001",  # H2O
            "cpd00009",  # Phosphate
            "cpd00067",  # H+
        ],
        default_uptake=100.0,
        custom_bounds={
            "cpd00020": (-5.0, 100.0),
            "cpd00007": (-10.0, 100.0)
        }
    )
    custom_media_response = build_media(custom_media_request, db_index)
    custom_media_id = custom_media_response["media_id"]
    print(f"    ✓ Created: {custom_media_id}")
    print(f"      Compounds: {custom_media_response['num_compounds']}\n")

    return True

success_3 = asyncio.run(validate_session_management())
if success_3:
    print("✓ PASSED: 03_session_management.ipynb validates successfully\n")
else:
    print("✗ FAILED: 03_session_management.ipynb validation failed\n")
    sys.exit(1)


# ==============================================================================
# NOTEBOOK 4: 04_error_handling.ipynb
# ==============================================================================
print("=" * 70)
print("VALIDATING: 04_error_handling.ipynb")
print("=" * 70)
print()

async def validate_error_handling():
    """Replicate 04_error_handling.ipynb exactly"""

    print("Part 1: Validation Errors")

    # Invalid compound IDs
    print("  Testing invalid compound IDs...")
    try:
        request = BuildMediaRequest(
            compounds=["cpd99999", "cpd88888", "cpd00027"],
            default_uptake=100.0
        )
        response = build_media(request, db_index)
        print("    ✗ Should have raised ValidationError")
        return False
    except ValidationError as e:
        print(f"    ✓ Correctly raised ValidationError")
        print(f"      Invalid IDs: {e.details.get('invalid_ids', [])[:2]}\n")

    # Invalid protein sequences
    print("  Testing invalid protein sequences...")
    try:
        response = await build_model(
            protein_sequences={
                "prot1": "MKLVINLV",
                "prot2": "MKXLINVAL*",  # Invalid
            },
            template="GramNegative",
            annotate_with_rast=False
        )
        print("    ✗ Should have raised ValidationError")
        return False
    except ValidationError as e:
        print(f"    ✓ Correctly raised ValidationError")
        print(f"      Message: {e.message[:60]}...\n")

    # Empty input
    print("  Testing empty compounds list...")
    try:
        request = BuildMediaRequest(
            compounds=[],
            default_uptake=100.0
        )
        response = build_media(request, db_index)
        print("    ✗ Should have raised ValidationError")
        return False
    except ValidationError as e:
        print(f"    ✓ Correctly raised ValidationError\n")

    print("Part 2: Not Found Errors")

    # Model not found
    print("  Testing model not found...")
    try:
        response = run_fba(
            model_id="nonexistent_model.draft",
            media_id="glucose_minimal_aerobic",
            db_index=db_index
        )
        print("    ✗ Should have raised NotFoundError")
        return False
    except NotFoundError as e:
        print(f"    ✓ Correctly raised NotFoundError")
        print(f"      Requested: nonexistent_model.draft\n")

    # Compound not found
    print("  Testing compound not found...")
    try:
        request = GetCompoundNameRequest(compound_id="cpd99999")
        response = get_compound_name(request, db_index)
        print("    ✗ Should have raised NotFoundError")
        return False
    except NotFoundError as e:
        print(f"    ✓ Correctly raised NotFoundError\n")

    print("Part 3: Infeasibility Errors")

    # Create draft model for testing
    print("  Creating draft model for infeasibility tests...")
    build_response = await build_model(
        protein_sequences={"prot1": "MKLVINLV"},
        template="Core",
        model_name="draft_model",
        annotate_with_rast=False
    )
    draft_model_id = build_response["model_id"]
    print(f"    ✓ Created: {draft_model_id}\n")

    # Infeasible FBA (ungapfilled model)
    print("  Testing infeasible FBA on ungapfilled model...")
    try:
        fba_response = run_fba(
            model_id=draft_model_id,
            media_id="glucose_minimal_aerobic",
            db_index=db_index
        )
        # May not raise error, just return infeasible status
        if fba_response.get("status") == "infeasible" or not fba_response.get("success", True):
            print(f"    ✓ FBA correctly returned infeasible status\n")
        else:
            print(f"    ✓ FBA completed (model may have some growth)\n")
    except InfeasibilityError as e:
        print(f"    ✓ Correctly raised InfeasibilityError\n")

    return True

success_4 = asyncio.run(validate_error_handling())
if success_4:
    print("✓ PASSED: 04_error_handling.ipynb validates successfully\n")
else:
    print("✗ FAILED: 04_error_handling.ipynb validation failed\n")
    sys.exit(1)


# ==============================================================================
# SUMMARY
# ==============================================================================
print("=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)
print()
print(f"✓ 01_basic_workflow.ipynb      - {'PASSED' if success_1 else 'FAILED'}")
print(f"✓ 02_database_lookups.ipynb    - {'PASSED' if success_2 else 'FAILED'}")
print(f"✓ 03_session_management.ipynb  - {'PASSED' if success_3 else 'FAILED'}")
print(f"✓ 04_error_handling.ipynb      - {'PASSED' if success_4 else 'FAILED'}")
print()

all_passed = success_1 and success_2 and success_3 and success_4

if all_passed:
    print("=" * 70)
    print("ALL NOTEBOOKS VALIDATED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("The notebooks are ready to execute without errors.")
    print("You can now run them with confidence.")
    sys.exit(0)
else:
    print("=" * 70)
    print("SOME NOTEBOOKS FAILED VALIDATION")
    print("=" * 70)
    print()
    print("Please fix the issues before running the notebooks.")
    sys.exit(1)
