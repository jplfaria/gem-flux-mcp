#!/usr/bin/env python3
"""
Run database lookup notebook cells programmatically to verify they work.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex

def main():
    print("="*80)
    print("TESTING DATABASE_LOOKUP_DEMO NOTEBOOK")
    print("="*80)

    # Setup: Load database
    print("\n[Setup] Loading ModelSEED database...")
    db_dir = Path(__file__).parent / "data" / "database"
    compounds_df = load_compounds_database(db_dir / "compounds.tsv")
    reactions_df = load_reactions_database(db_dir / "reactions.tsv")
    db_index = DatabaseIndex(compounds_df, reactions_df)
    print(f"✅ Loaded {len(compounds_df)} compounds")
    print(f"✅ Loaded {len(reactions_df)} reactions")

    # Example 1: Get Compound by ID
    print("\n" + "="*80)
    print("[Example 1] Get Compound by ID")
    print("="*80)
    glucose = db_index.get_compound_by_id("cpd00027")
    if glucose is not None:
        print(f"Compound ID: cpd00027")
        print(f"Name: {glucose['name']}")
        print(f"Formula: {glucose['formula']}")
        print(f"Mass: {glucose['mass']:.2f} Da")
        print(f"Charge: {glucose['charge']}")
        print(f"SMILES: {glucose['smiles']}")
    else:
        print("❌ Compound not found")
        return 1

    # Example 2: Search Compounds by Name
    print("\n" + "="*80)
    print("[Example 2] Search Compounds by Name")
    print("="*80)
    glucose_compounds = db_index.search_compounds_by_name("glucose")
    print(f"Found {len(glucose_compounds)} compounds matching 'glucose':\n")
    for compound in glucose_compounds:
        print(f"  {compound.name}: {compound['name']} ({compound['formula']})")

    # Example 3: Search Compounds by Abbreviation
    print("\n" + "="*80)
    print("[Example 3] Search Compounds by Abbreviation")
    print("="*80)
    atp_compounds = db_index.search_compounds_by_abbreviation("atp")
    print(f"Found {len(atp_compounds)} compounds with 'ATP' in abbreviation:\n")
    for compound in atp_compounds[:5]:
        print(f"  {compound.name}: {compound['name']}")
        print(f"    Abbreviation: {compound['abbreviation']}")
        print(f"    Formula: {compound['formula']}")
        print()

    # Example 4: Get Reaction by ID
    print("\n" + "="*80)
    print("[Example 4] Get Reaction by ID")
    print("="*80)
    hexokinase = db_index.get_reaction_by_id("rxn00148")
    if hexokinase is not None:
        print(f"Reaction ID: rxn00148")
        print(f"Name: {hexokinase['name']}")
        print(f"Equation: {hexokinase['equation']}")
        print(f"EC Numbers: {hexokinase['ec_numbers']}")
        print(f"Reversibility: {hexokinase['reversibility']}")
        print(f"Is Transport: {hexokinase['is_transport']}")
    else:
        print("❌ Reaction not found")
        return 1

    # Example 5: Search Reactions by Name
    print("\n" + "="*80)
    print("[Example 5] Search Reactions by Name")
    print("="*80)
    kinase_reactions = db_index.search_reactions_by_name("kinase")
    print(f"Found {len(kinase_reactions)} reactions with 'kinase' in name:\n")
    for reaction in kinase_reactions:
        print(f"  {reaction.name}: {reaction['name']}")

    # Example 6: Search Reactions by EC Number
    print("\n" + "="*80)
    print("[Example 6] Search Reactions by EC Number")
    print("="*80)
    transferase_reactions = db_index.search_reactions_by_ec_number("2.7.1")
    print(f"Found {len(transferase_reactions)} reactions with EC 2.7.1.x:\n")
    for reaction in transferase_reactions:
        print(f"  {reaction.name}: {reaction['name']}")
        print(f"    EC: {reaction['ec_numbers']}")
        print()

    # Example 7: Explore Metabolic Pathways
    print("\n" + "="*80)
    print("[Example 7] Explore Metabolic Pathways")
    print("="*80)
    glycolysis_reactions = db_index.search_reactions_by_name("glycolysis")
    print(f"Found {len(glycolysis_reactions)} reactions related to glycolysis:\n")
    for reaction in glycolysis_reactions:
        print(f"  {reaction.name}: {reaction['name']}")
        equation_preview = reaction['equation'][:80] + "..." if len(reaction['equation']) > 80 else reaction['equation']
        print(f"    Equation: {equation_preview}")
        print()

    # Example 8: Cross-Reference Compounds and Reactions
    print("\n" + "="*80)
    print("[Example 8] Cross-Reference Compounds and Reactions")
    print("="*80)
    atp_reactions = db_index.search_reactions_by_name("atp")
    print(f"Found {len(atp_reactions)} reactions involving ATP\n")
    print("Sample reactions:")
    for reaction in atp_reactions[:5]:
        print(f"  {reaction.name}: {reaction['name']}")

    print("\n" + "="*80)
    print("✅ ALL NOTEBOOK CELLS EXECUTED SUCCESSFULLY")
    print("="*80)
    print("\n✅ database_lookup_demo.ipynb is verified and ready!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
