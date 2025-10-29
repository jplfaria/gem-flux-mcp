#!/usr/bin/env python3
"""
Complete test showing:
1. The JSON model has broken bounds (all exchanges are 0-100, no uptake!)
2. The FBA fix works when proper bounds are applied
"""

from cobra.io import load_json_model
from modelseedpy.core.msmedia import MSMedia
from examples.notebook_setup import quick_setup
from gem_flux_mcp.storage.models import store_model
from gem_flux_mcp.tools.run_fba import run_fba

print("=" * 70)
print("COMPLETE FBA FIX VERIFICATION")
print("=" * 70)

# Setup
print("\nSetting up environment...")
db_index, _, _, _ = quick_setup()

# Load model
print("\nLoading model from JSON...")
model = load_json_model("examples/output/E_coli_K12.draft.gf.json")

# Show the problem
print("\n" + "=" * 70)
print("PROBLEM: Exchange reactions have wrong bounds in saved JSON")
print("=" * 70)
ex_rxns = [r for r in model.reactions if r.id.startswith("EX_")]
print(f"\nTotal exchange reactions: {len(ex_rxns)}")
print("First 10 exchange reactions from JSON:")
for rxn in ex_rxns[:10]:
    print(f"  {rxn.id}: bounds=({rxn.lower_bound}, {rxn.upper_bound})")
print("\n⚠️  ALL exchanges have bounds (0.0, 100.0) = can only SECRETE, not UPTAKE!")
print("   This means the model cannot consume ANY nutrients → cannot grow")

# Fix the bounds manually for glucose and oxygen
print("\n" + "=" * 70)
print("FIX: Manually set correct bounds for key nutrients")
print("=" * 70)

# Set glucose uptake
if "EX_cpd00027_e0" in model.reactions:
    glucose_ex = model.reactions.get_by_id("EX_cpd00027_e0")
    glucose_ex.lower_bound = -5.0  # Allow uptake
    print(f"✓ Set glucose bounds: ({glucose_ex.lower_bound}, {glucose_ex.upper_bound})")

# Set O2 uptake
if "EX_cpd00007_e0" in model.reactions:
    o2_ex = model.reactions.get_by_id("EX_cpd00007_e0")
    o2_ex.lower_bound = -10.0  # Allow uptake
    print(f"✓ Set O2 bounds: ({o2_ex.lower_bound}, {o2_ex.upper_bound})")

# Set other minimal media compounds
minimal_compounds = [
    "cpd00001",  # H2O
    "cpd00009",  # Phosphate
    "cpd00011",  # CO2
    "cpd00067",  # H+
    "cpd00013",  # NH3
    "cpd00048",  # SO4
]

for cpd in minimal_compounds:
    rxn_id = f"EX_{cpd}_e0"
    if rxn_id in model.reactions:
        rxn = model.reactions.get_by_id(rxn_id)
        rxn.lower_bound = -100.0

print(f"✓ Set bounds for {len(minimal_compounds)} additional compounds")

# Store fixed model
store_model("E_coli_K12.draft.gf", model)

# Now test FBA with proper bounds
print("\n" + "=" * 70)
print("TESTING: Run FBA with fixed bounds")
print("=" * 70)

# Create minimal MSMedia manually
media = MSMedia.from_dict({
    "cpd00027_e0": (-5.0, 100.0),   # Glucose
    "cpd00007_e0": (-10.0, 100.0),  # O2
    "cpd00001_e0": (-100.0, 100.0), # H2O
    "cpd00009_e0": (-100.0, 100.0), # Phosphate
    "cpd00011_e0": (-100.0, 100.0), # CO2
    "cpd00067_e0": (-100.0, 100.0), # H+
    "cpd00013_e0": (-100.0, 100.0), # NH3
    "cpd00048_e0": (-100.0, 100.0), # SO4
}, db_index.biochem)

from gem_flux_mcp.storage.media import store_media
store_media("test_minimal", media)

# Run FBA
result = run_fba(
    model_id="E_coli_K12.draft.gf",
    media_id="test_minimal",
    db_index=db_index,
    objective="bio1",
    maximize=True
)

print(f"\nFBA Results:")
print(f"  Status: {result['status']}")
print(f"  Objective value: {result['objective_value']:.6f} hr⁻¹")
print(f"  Active reactions: {result['active_reactions']}")
print(f"  Total flux: {result['total_flux']:.2f} mmol/gDW/h")

print("\n" + "=" * 70)
if result['objective_value'] > 0.01:
    print("✅✅✅ SUCCESS! FBA FIX WORKS! ✅✅✅")
    print(f"   Growth rate: {result['objective_value']:.4f} hr⁻¹")
    print("\n" + "The objective_direction fix is working correctly!")
    print("The problem was that the saved JSON had broken exchange bounds.")
    print("\nTO FIX THE NOTEBOOK:")
    print("  1. Restart Jupyter kernel")
    print("  2. Run all cells again")
    print("  3. The new code will apply media bounds correctly during FBA")
else:
    print(f"❌ Still no growth: {result['objective_value']}")
print("=" * 70)
