#!/usr/bin/env python3
"""
Run notebook cells programmatically to verify they work.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.tools.media_builder import build_media, BuildMediaRequest
from gem_flux_mcp.storage.media import retrieve_media

def main():
    print("="*80)
    print("TESTING BUILD_MEDIA_DEMO NOTEBOOK")
    print("="*80)

    # Setup: Load database
    print("\n[Setup] Loading ModelSEED database...")
    db_dir = Path(__file__).parent / "data" / "database"
    compounds_df = load_compounds_database(db_dir / "compounds.tsv")
    reactions_df = load_reactions_database(db_dir / "reactions.tsv")
    db_index = DatabaseIndex(compounds_df, reactions_df)
    print(f"✅ Loaded {len(compounds_df)} compounds")
    print(f"✅ Loaded {len(reactions_df)} reactions")

    # Example 1: Glucose Minimal Media
    print("\n" + "="*80)
    print("[Example 1] Glucose Minimal Media")
    print("="*80)
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
            "cpd00027": (-5.0, 100.0),
            "cpd00007": (-10.0, 100.0),
        }
    )

    response = build_media(request, db_index)

    print(f"Media ID: {response['media_id']}")
    print(f"Media type: {response['media_type']}")
    print(f"Number of compounds: {response['num_compounds']}")
    print(f"\nCompounds:")
    for cpd in response['compounds']:
        lower, upper = cpd['bounds']
        print(f"  - {cpd['id']}: {cpd['name']} ({lower:.1f}, {upper:.1f})")

    # Example 2: Retrieve Media Object
    print("\n" + "="*80)
    print("[Example 2] Retrieve Media Object")
    print("="*80)
    media_obj = retrieve_media(response['media_id'])

    print(f"Type: {type(media_obj).__name__}")
    print(f"Media ID: {media_obj.id}")
    print(f"Has get_media_constraints: {hasattr(media_obj, 'get_media_constraints')}")

    constraints = media_obj.get_media_constraints()
    print(f"\nMedia constraints (first 5):")
    for cpd_id, bounds in list(constraints.items())[:5]:
        print(f"  {cpd_id}: {bounds}")

    # Example 3: Complex Media
    print("\n" + "="*80)
    print("[Example 3] Complex Media")
    print("="*80)
    request = BuildMediaRequest(
        compounds=[
            "cpd00027",  # D-Glucose
            "cpd00007",  # O2
            "cpd00001",  # H2O
            "cpd00009",  # Phosphate
            "cpd00011",  # CO2
            "cpd00013",  # NH3
            "cpd00067",  # H+
            "cpd00023",  # L-Glutamate
            "cpd00033",  # Glycine
            "cpd00035",  # L-Alanine
            "cpd00039",  # L-Lysine
            "cpd00041",  # L-Aspartate
            "cpd00051",  # L-Arginine
            "cpd00054",  # L-Serine
            "cpd00060",  # L-Methionine
            "cpd00066",  # L-Phenylalanine
            "cpd00069",  # L-Tyrosine
        ],
        default_uptake=100.0,
        custom_bounds={
            "cpd00027": (-10.0, 100.0),
            "cpd00007": (-20.0, 100.0),
        }
    )

    response = build_media(request, db_index)

    print(f"Media ID: {response['media_id']}")
    print(f"Media type: {response['media_type']}")
    print(f"Number of compounds: {response['num_compounds']}")
    print(f"\nFirst 10 compounds:")
    for cpd in response['compounds'][:10]:
        print(f"  - {cpd['id']}: {cpd['name']}")

    # Example 4: M9-like Minimal Media
    print("\n" + "="*80)
    print("[Example 4] M9-like Minimal Media")
    print("="*80)
    request = BuildMediaRequest(
        compounds=[
            "cpd00027",  # D-Glucose
            "cpd00007",  # O2
            "cpd00001",  # H2O
            "cpd00009",  # Phosphate
            "cpd00011",  # CO2
            "cpd00013",  # NH3
            "cpd00067",  # H+
            "cpd00099",  # Cl-
            "cpd00058",  # Cu2+
            "cpd00034",  # Zn2+
            "cpd00149",  # Co2+
            "cpd00030",  # Mn2+
            "cpd00048",  # Sulfate
            "cpd00063",  # Ca2+
            "cpd00205",  # K+
            "cpd00971",  # Na+
            "cpd00254",  # Mg2+
            "cpd10515",  # Fe2+
            "cpd00244",  # Ni2+
            "cpd00263",  # Cations
        ],
        default_uptake=100.0,
        custom_bounds={
            "cpd00027": (-10.0, 100.0),
            "cpd00007": (-20.0, 100.0),
        }
    )

    response = build_media(request, db_index)

    print(f"Media ID: {response['media_id']}")
    print(f"Media type: {response['media_type']}")
    print(f"Number of compounds: {response['num_compounds']}")

    print("\n" + "="*80)
    print("✅ ALL NOTEBOOK CELLS EXECUTED SUCCESSFULLY")
    print("="*80)
    print("\n✅ build_media_demo.ipynb is verified and ready!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
