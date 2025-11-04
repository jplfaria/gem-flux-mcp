# Import notebook setup helper
from notebook_setup import quick_setup

# Import Gem-Flux MCP tools
from gem_flux_mcp.tools.media_builder import build_media
from gem_flux_mcp.tools.run_fba import run_fba
from gem_flux_mcp.tools.compound_lookup import search_compounds, SearchCompoundsRequest
from gem_flux_mcp.types import (
    BuildMediaRequest,
    RunFBARequest,
)

print("✓ Imports successful")


# Setup environment
db_index, templates, atp_media, predefined_media = quick_setup()

print("\n✓ Environment ready!")


# Try to build media with invalid compound ID
try:
    invalid_request = BuildMediaRequest(
        compounds=["invalid_compound_id"],
        default_uptake=100.0,
        custom_bounds={}
    )
    response = build_media(invalid_request, db_index)
    
    if not response.get('success', True):
        print(f"❌ Error: {response['error_type']}")
        print(f"   Message: {response['message']}")
except Exception as e:
    print(f"Exception: {e}")


# Try to run FBA on non-existent model
try:
    fba_request = RunFBARequest(
        model_id="nonexistent_model.draft",
        media_id="glucose_minimal_aerobic",
        objective="bio1",
        maximize=True
    )
    response = run_fba(fba_request, db_index)
    
    if not response.get('success', True):
        print(f"❌ Error: {response['error_type']}")
        print(f"   Message: {response['message']}")
except Exception as e:
    print(f"Exception: {e}")


# Valid compound search
search_request = SearchCompoundsRequest(
    query="glucose",
    search_fields=["name"],
    limit=5
)

search_response = search_compounds(search_request, db_index)

print(f"Found {search_response['num_results']} results")
for result in search_response['results']:
    print(f"  {result['name']} ({result['id']})")

