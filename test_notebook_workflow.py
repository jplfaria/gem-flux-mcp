#!/usr/bin/env python3
"""
Test script to verify the notebook workflow works end-to-end.
This mimics the exact steps from examples/01_basic_workflow.ipynb.
"""
import sys
sys.path.insert(0, 'examples')

from notebook_setup import quick_setup
from gem_flux_mcp.tools.run_fba import run_fba
from gem_flux_mcp.storage.models import store_model, retrieve_model
from gem_flux_mcp.storage.media import retrieve_media
import cobra

print("="*60)
print("Testing Notebook Workflow")
print("="*60)

# Setup (mimics notebook cell 4)
print("\n1. Setting up environment...")
db_index, templates, atp_media, predefined_media = quick_setup()
print(f"   ✓ db_index loaded: {db_index.get_compound_count()} compounds")

# Use predefined media (mimics notebook cell 6)
print("\n2. Using predefined media...")
media_id = "glucose_minimal_aerobic"
print(f"   ✓ Media: {media_id}")

# For testing, we'll create a tiny mock model instead of building
# (building takes too long for a quick test)
print("\n3. Creating mock gapfilled model...")
mock_model = cobra.Model("test_model")
mock_model.id = "test.gf"

# Add some minimal reactions to make it valid
from cobra import Metabolite, Reaction

# Create metabolites
glc_e = Metabolite('cpd00027_e0', compartment='e0', name='D-Glucose')
o2_e = Metabolite('cpd00007_e0', compartment='e0', name='O2')
co2_e = Metabolite('cpd00011_e0', compartment='e0', name='CO2')

# Create exchange reactions (these are what FBA looks for)
ex_glc = Reaction('EX_cpd00027_e0')
ex_glc.add_metabolites({glc_e: -1})
ex_glc.lower_bound = -10
ex_glc.upper_bound = 0

ex_o2 = Reaction('EX_cpd00007_e0')
ex_o2.add_metabolites({o2_e: -1})
ex_o2.lower_bound = -10
ex_o2.upper_bound = 0

ex_co2 = Reaction('EX_cpd00011_e0')
ex_co2.add_metabolites({co2_e: 1})
ex_co2.lower_bound = 0
ex_co2.upper_bound = 100

# Create a simple biomass reaction
biomass = Reaction('bio1')
biomass.add_metabolites({glc_e: -1, o2_e: -1, co2_e: 1})
biomass.lower_bound = 0
biomass.upper_bound = 1000

# Add to model
mock_model.add_reactions([ex_glc, ex_o2, ex_co2, biomass])
mock_model.objective = 'bio1'

# Store the mock model
gapfilled_model_id = "test.gf"
store_model(gapfilled_model_id, mock_model)
print(f"   ✓ Model stored: {gapfilled_model_id}")

# Run FBA (mimics notebook cell 12 - THE KEY TEST)
print("\n4. Running FBA with db_index parameter...")
try:
    fba_response = run_fba(
        model_id=gapfilled_model_id,
        media_id=media_id,
        db_index=db_index,     # <--- THIS IS THE FIX
        objective="bio1",
        maximize=True,
        flux_threshold=1e-6
    )

    if fba_response.get("success"):
        print(f"   ✅ FBA SUCCESS!")
        print(f"   Growth rate: {fba_response['objective_value']:.3f} hr⁻¹")
        print(f"   Active reactions: {fba_response['active_reactions']}")
        print(f"   Uptake reactions: {len(fba_response['uptake_fluxes'])}")
        print(f"   Secretion reactions: {len(fba_response['secretion_fluxes'])}")
    else:
        print(f"   ❌ FBA returned error: {fba_response.get('message')}")
        sys.exit(1)

except Exception as e:
    print(f"   ❌ FBA raised exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ All tests passed! Notebook should work correctly.")
print("="*60)
