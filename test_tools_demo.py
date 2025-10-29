#!/usr/bin/env python3
"""
Test script to verify all tools work before creating demo notebooks.

This script exercises all the main tools to ensure they're functional
after the refactoring.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.tools.media_builder import build_media, BuildMediaRequest
from gem_flux_mcp.storage.media import store_media, retrieve_media, MEDIA_STORAGE
from gem_flux_mcp.storage.models import MODEL_STORAGE


def test_database_loading():
    """Test 1: Load ModelSEED database."""
    print("\n" + "="*80)
    print("TEST 1: Loading ModelSEED Database")
    print("="*80)

    try:
        # Load database files from data directory
        compounds_path = Path(__file__).parent / "data" / "database" / "compounds.tsv"
        reactions_path = Path(__file__).parent / "data" / "database" / "reactions.tsv"

        compounds_df = load_compounds_database(compounds_path)
        reactions_df = load_reactions_database(reactions_path)
        db_index = DatabaseIndex(compounds_df, reactions_df)

        print(f"✅ Loaded {len(compounds_df)} compounds")
        print(f"✅ Loaded {len(reactions_df)} reactions")
        print(f"✅ Database index created")

        return db_index
    except Exception as e:
        print(f"❌ Failed: {e}")
        raise


def test_build_media(db_index):
    """Test 2: Build glucose minimal media."""
    print("\n" + "="*80)
    print("TEST 2: Building Glucose Minimal Media")
    print("="*80)

    try:
        request = BuildMediaRequest(
            compounds=[
                "cpd00027",  # D-Glucose
                "cpd00007",  # O2
                "cpd00001",  # H2O
                "cpd00009",  # Phosphate
                "cpd00011",  # CO2
                "cpd00013",  # NH3
                "cpd00067",  # H+
            ],
            default_uptake=100.0,
            custom_bounds={
                "cpd00027": (-5.0, 100.0),  # Glucose limited
                "cpd00007": (-10.0, 100.0),  # Oxygen available
            }
        )

        response = build_media(request, db_index)

        print(f"✅ Media created: {response['media_id']}")
        print(f"✅ Contains {response['num_compounds']} compounds")
        print(f"✅ Media type: {response['media_type']}")

        # Verify MSMedia object stored
        media_obj = retrieve_media(response['media_id'])
        print(f"✅ MSMedia object stored: {type(media_obj).__name__}")
        print(f"✅ Has get_media_constraints: {hasattr(media_obj, 'get_media_constraints')}")

        return response['media_id']
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_compound_lookup(db_index):
    """Test 3: Look up compound information."""
    print("\n" + "="*80)
    print("TEST 3: Compound Lookup")
    print("="*80)

    try:
        # Test glucose lookup
        glucose = db_index.get_compound_by_id("cpd00027")
        print(f"✅ Found compound: {glucose['name']}")
        print(f"   ID: cpd00027")
        print(f"   Formula: {glucose['formula']}")
        print(f"   Charge: {glucose['charge']}")

        # Test search by name
        results = db_index.search_compounds_by_name("glucose")
        print(f"✅ Search 'glucose' found {len(results)} results")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_reaction_lookup(db_index):
    """Test 4: Look up reaction information."""
    print("\n" + "="*80)
    print("TEST 4: Reaction Lookup")
    print("="*80)

    try:
        # Test hexokinase lookup
        hex_rxn = db_index.get_reaction_by_id("rxn00148")
        print(f"✅ Found reaction: {hex_rxn['name']}")
        print(f"   ID: rxn00148")
        print(f"   Equation: {hex_rxn['equation']}")
        print(f"   EC: {hex_rxn['ec_numbers']}")

        # Test search by name
        results = db_index.search_reactions_by_name("hexokinase")
        print(f"✅ Search 'hexokinase' found {len(results)} results")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("GEM-FLUX MCP TOOLS VERIFICATION")
    print("Testing tools after Phase 1-5 refactoring")
    print("="*80)

    try:
        # Test 1: Database loading
        db_index = test_database_loading()

        # Test 2: Build media
        media_id = test_build_media(db_index)

        # Test 3: Compound lookup
        test_compound_lookup(db_index)

        # Test 4: Reaction lookup
        test_reaction_lookup(db_index)

        # Summary
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print(f"\nMedia in session: {len(MEDIA_STORAGE)} (should be 1)")
        print(f"Models in session: {len(MODEL_STORAGE)} (should be 0)")
        print("\n✅ Tools are ready for notebook creation!")

        return 0

    except Exception as e:
        print("\n" + "="*80)
        print("❌ TESTS FAILED")
        print("="*80)
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
