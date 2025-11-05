#!/usr/bin/env python3
"""Quick test script to verify Phase 2 improvements work correctly."""

import json
from pathlib import Path
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.database.loader import load_compounds_database, load_reactions_database
from gem_flux_mcp.tools.gapfill_model import categorize_reactions_by_pathway

print("=" * 80)
print("PHASE 2 IMPROVEMENTS TEST")
print("=" * 80)

# Load database
print("\n1. Loading ModelSEED database...")
compounds_df = load_compounds_database(Path("data/database/compounds.tsv"))
reactions_df = load_reactions_database(Path("data/database/reactions.tsv"))
db_index = DatabaseIndex(compounds_df, reactions_df)
print(f"   ✓ Loaded {db_index.get_reaction_count()} reactions")

# Test 1: Verify pathway categorization uses real database data
print("\n2. Testing pathway categorization (CRITICAL IMPROVEMENT)...")
print("   This should use REAL ModelSEED pathway data, not keyword matching")

# Create sample enriched reactions
sample_reactions = [
    {"id": "rxn00148_c0", "name": "hexokinase"},  # Should have real pathway from DB
    {"id": "rxn00200_c0", "name": "phosphoglucose isomerase"},
]

# Call the improved function
pathway_summary = categorize_reactions_by_pathway(sample_reactions, db_index)

print(f"\n   Results:")
print(f"   - Total reactions: {pathway_summary['total_reactions']}")
print(f"   - Pathways affected: {pathway_summary['num_pathways_affected']}")
print(f"   - Reactions without pathways: {pathway_summary['reactions_without_pathways']}")
print(f"   - Percentage without pathways: {pathway_summary['reactions_without_pathways_percentage']}%")
print(f"\n   Pathways detected:")
for pathway_info in pathway_summary['pathways']:
    print(f"     • {pathway_info['pathway']}: {pathway_info['reactions_added']} reactions")

# Test 2: Check if we get real pathway names (not generic categories)
print("\n3. Verifying pathway names are from ModelSEED database...")
pathway_names = [p['pathway'] for p in pathway_summary['pathways']]
# Old keyword matching would give names like "Glycolysis/Gluconeogenesis"
# New database should give exact ModelSEED pathway names
if any('/' in name or 'metabolism' in name.lower() for name in pathway_names if name not in ['Unknown', 'Unannotated']):
    print("   ⚠️  WARNING: Found generic pathway categories (might still be using keywords)")
else:
    print("   ✓ Pathway names look like database pathways!")

print("\n" + "=" * 80)
print("KEY VERIFICATION POINTS:")
print("=" * 80)
print("\n✓ Check 1: Does categorize_reactions_by_pathway accept db_index parameter?")
print("  Result: YES (function signature updated)")

print("\n✓ Check 2: Does pathway_summary include new fields?")
print(f"  - reactions_without_pathways: {'YES' if 'reactions_without_pathways' in pathway_summary else 'NO'}")
print(f"  - reactions_without_pathways_percentage: {'YES' if 'reactions_without_pathways_percentage' in pathway_summary else 'NO'}")

print("\n✓ Check 3: Are pathway names from database (not keyword categories)?")
print(f"  Pathway names: {pathway_names}")
print(f"  Analysis: If you see exact ModelSEED pathway names → SUCCESS")
print(f"           If you see 'Pentose phosphate', 'TCA cycle' → FAILURE (still using keywords)")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\nNext: Run this via MCP with Argo to see if improvements help LLM usage")
