#!/usr/bin/env python3
"""Debug script to verify media application works correctly."""

from cobra.io import load_json_model
from modelseedpy.core.msmedia import MSMedia
from examples.notebook_setup import quick_setup
from gem_flux_mcp.storage.models import store_model
from gem_flux_mcp.storage.media import store_media
import math

print("=" * 70)
print("DEBUG: Media Application Test")
print("=" * 70)

# Setup
print("\nSetting up environment...")
db_index, _, _, predefined_media = quick_setup()

# Load model
print("\nLoading model from JSON...")
model = load_json_model("examples/output/E_coli_K12.draft.gf.json")
print(f"✓ Model loaded: {model.id} ({len(model.reactions)} reactions)")

# Get media from storage (MSMedia object)
print("\nGetting glucose minimal aerobic media from storage...")
from gem_flux_mcp.storage.media import retrieve_media
media = retrieve_media("glucose_minimal_aerobic")
print(f"✓ Media type: {type(media)}")

# Get constraints
print("\nGetting media constraints...")
media_constraints = media.get_media_constraints(cmp="e0")
print(f"✓ Got {len(media_constraints)} constraints")
print(f"First 5 constraints:")
for cpd_id, (lb, ub) in list(media_constraints.items())[:5]:
    print(f"  {cpd_id}: ({lb}, {ub})")

# Build medium dict
print("\nBuilding medium dict...")
medium = {}
for compound_id, (lower_bound, upper_bound) in media_constraints.items():
    exchange_rxn_id = f"EX_{compound_id}"
    if exchange_rxn_id in model.reactions:
        medium[exchange_rxn_id] = math.fabs(lower_bound)
    else:
        print(f"  ⚠️  {exchange_rxn_id} not in model")

print(f"✓ Built medium dict with {len(medium)} exchanges")
print(f"First 5 entries:")
for rxn_id, rate in list(medium.items())[:5]:
    print(f"  {rxn_id}: {rate}")

# Check exchange reactions BEFORE applying medium
print("\n" + "=" * 70)
print("BEFORE: Exchange reaction bounds")
print("=" * 70)
ex_rxns = [r for r in model.reactions if r.id.startswith("EX_")]
print(f"Total exchange reactions: {len(ex_rxns)}")
print("First 10 exchange reactions:")
for rxn in ex_rxns[:10]:
    print(f"  {rxn.id}: bounds=({rxn.lower_bound}, {rxn.upper_bound})")

# Apply medium
print("\n" + "=" * 70)
print("APPLYING MEDIUM")
print("=" * 70)
model.medium = medium
print(f"✓ Applied medium with {len(medium)} exchanges")

# Check exchange reactions AFTER applying medium
print("\n" + "=" * 70)
print("AFTER: Exchange reaction bounds")
print("=" * 70)
print("First 10 exchange reactions:")
for rxn in ex_rxns[:10]:
    print(f"  {rxn.id}: bounds=({rxn.lower_bound}, {rxn.upper_bound})")

# Check specific key reactions
print("\n" + "=" * 70)
print("KEY NUTRIENTS")
print("=" * 70)
key_rxns = ["EX_cpd00027_e0", "EX_cpd00007_e0", "EX_cpd00001_e0"]
for rxn_id in key_rxns:
    if rxn_id in model.reactions:
        rxn = model.reactions.get_by_id(rxn_id)
        print(f"{rxn_id}: bounds=({rxn.lower_bound}, {rxn.upper_bound})")
    else:
        print(f"{rxn_id}: NOT IN MODEL")

# Check objective
print("\n" + "=" * 70)
print("OBJECTIVE")
print("=" * 70)
print(f"Objective: {model.objective}")
print(f"Objective direction: {model.objective_direction}")

# Run FBA
print("\n" + "=" * 70)
print("RUNNING FBA")
print("=" * 70)
solution = model.optimize()
print(f"Status: {solution.status}")
print(f"Objective value: {solution.objective_value:.6f}")

if solution.objective_value > 0.01:
    print("\n✅ SUCCESS! Model shows positive growth!")
else:
    print("\n❌ FAILED: Model still shows 0.0 growth")
    print("\nInvestigating why...")

    # Check if biomass reaction exists
    print("\nLooking for biomass reaction...")
    bio_rxns = [r for r in model.reactions if 'bio' in r.id.lower()]
    print(f"Found {len(bio_rxns)} bio reactions:")
    for rxn in bio_rxns[:5]:
        print(f"  {rxn.id}: bounds=({rxn.lower_bound}, {rxn.upper_bound})")

    # Check model.objective expression
    print(f"\nObjective expression: {model.objective.expression}")
    print(f"Objective variables: {list(model.objective.variables)}")
