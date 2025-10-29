#!/usr/bin/env python3
"""Quick test to verify FBA objective_direction fix works."""

from examples.notebook_setup import quick_setup
from gem_flux_mcp.tools.run_fba import run_fba

print("="*60)
print("Testing FBA Fix")
print("="*60)

# Setup environment
print("\nLoading environment...")
db_index, templates, atp_media, predefined_media = quick_setup()

# Load the gapfilled model from JSON
print("\nLoading model from JSON...")
from cobra.io import load_json_model
from gem_flux_mcp.storage.models import store_model

model_path = "examples/output/E_coli_K12.draft.gf.json"
model = load_json_model(model_path)
store_model("E_coli_K12.draft.gf", model)
print(f"✓ Model loaded: {model.id} ({len(model.reactions)} reactions)")

# Check what media is in storage
print("\nChecking media in storage...")
from gem_flux_mcp.storage.media import retrieve_media
media_from_storage = retrieve_media("glucose_minimal_aerobic")
print(f"Media type: {type(media_from_storage)}")
if hasattr(media_from_storage, "get_media_constraints"):
    constraints = media_from_storage.get_media_constraints(cmp="e0")
    print(f"Media constraints (first 3): {list(constraints.items())[:3]}")

# Check model's exchange reactions before FBA
print("\nChecking model exchange reactions (first 5):")
for rxn in list(model.reactions)[:5]:
    if rxn.id.startswith("EX_"):
        print(f"  {rxn.id}: bounds=({rxn.lower_bound}, {rxn.upper_bound})")

# Run FBA on the model
print("\n" + "="*60)
print("Running FBA on E_coli_K12.draft.gf")
print("="*60)

try:
    result = run_fba(
        model_id="E_coli_K12.draft.gf",
        media_id="glucose_minimal_aerobic",
        db_index=db_index,
        objective="bio1",
        maximize=True
    )

    print(f"\nStatus: {result['status']}")
    print(f"Objective value: {result['objective_value']:.6f} hr⁻¹")
    print(f"Active reactions: {result['active_reactions']}")
    print(f"Total flux: {result['total_flux']:.2f} mmol/gDW/h")

    print("\n" + "="*60)
    if result['objective_value'] > 0.01:
        print("✅ SUCCESS! FBA shows POSITIVE growth!")
        print(f"   Growth rate: {result['objective_value']:.4f} hr⁻¹")
    elif abs(result['objective_value']) < 1e-10:
        print("❌ STILL BROKEN: Growth is -0.000 or ~0.000")
        print(f"   Actual value: {result['objective_value']}")
    else:
        print(f"⚠️  Unexpected value: {result['objective_value']}")
    print("="*60)

except Exception as e:
    print(f"\n❌ Error running FBA: {e}")
    import traceback
    traceback.print_exc()
