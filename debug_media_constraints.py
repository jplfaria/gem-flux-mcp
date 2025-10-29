#!/usr/bin/env python3
"""Debug script to understand media constraints format issue."""

import sys
sys.path.insert(0, '/Users/jplfaria/repos/gem-flux-mcp/src')

from gem_flux_mcp.storage.media import MEDIA_STORAGE, load_predefined_media
from gem_flux_mcp.storage.models import MODEL_STORAGE
from gem_flux_mcp.database.index import DatabaseIndex

# Load database
print("Loading database...")
db_index = DatabaseIndex()
db_index.load()

# Load predefined media
print("\nLoading predefined media...")
load_predefined_media(db_index)

# Get complete media
print("\n=== COMPLETE MEDIA ===")
media = MEDIA_STORAGE.get("complete")
print(f"Media type: {type(media)}")
print(f"Has get_media_constraints: {hasattr(media, 'get_media_constraints')}")

if hasattr(media, "get_media_constraints"):
    constraints = media.get_media_constraints(cmp="e0")
    print(f"\nget_media_constraints returned {len(constraints)} items")
    print("First 5 constraint keys:")
    for rxn_id in list(constraints.keys())[:5]:
        print(f"  '{rxn_id}'")

    # Check if it's returning EX_ format or compound format
    first_key = list(constraints.keys())[0]
    print(f"\nFirst key: '{first_key}'")
    print(f"Starts with 'EX_': {first_key.startswith('EX_')}")
    print(f"Contains '_e0': {'_e0' in first_key}")

# Now check what exchange reactions are actually in a model
print("\n=== MODEL EXCHANGE REACTIONS ===")
if MODEL_STORAGE:
    model_id = list(MODEL_STORAGE.keys())[0]
    model = MODEL_STORAGE[model_id]
    exchange_rxns = [r.id for r in model.reactions if r.id.startswith("EX_")]
    print(f"Model has {len(exchange_rxns)} exchange reactions")
    print("First 5 exchange reaction IDs:")
    for rxn_id in exchange_rxns[:5]:
        print(f"  '{rxn_id}'")
else:
    print("No models in storage - need to build one first")
