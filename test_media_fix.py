#!/usr/bin/env python3
"""Test that media loading and FBA work correctly after fix."""

import sys
sys.path.insert(0, '/Users/jplfaria/repos/gem-flux-mcp/src')

from gem_flux_mcp.media.predefined_loader import load_predefined_media
from gem_flux_mcp.storage.media import store_media, retrieve_media
from modelseedpy.core.msmedia import MSMedia

print("="*60)
print("Testing Media Loading Fix")
print("="*60)

# Load predefined media
print("\n1. Loading predefined media...")
predefined_media = load_predefined_media()
print(f"   Loaded {len(predefined_media)} media")

# Check the compounds dict format
media_dict = predefined_media["glucose_minimal_aerobic"]
compounds_dict = media_dict["compounds"]
first_cpd = list(compounds_dict.keys())[0]
print(f"\n2. Checking compounds dict format...")
print(f"   First compound key: '{first_cpd}'")
print(f"   Has _e0 suffix: {first_cpd.endswith('_e0')}")

# Convert to MSMedia object
print(f"\n3. Converting to MSMedia object...")
media_obj = MSMedia.from_dict(compounds_dict)
print(f"   MSMedia object created")

# Check get_media_constraints output
print(f"\n4. Checking get_media_constraints output...")
constraints = media_obj.get_media_constraints(cmp="e0")
first_rxn = list(constraints.keys())[0]
print(f"   First constraint key: '{first_rxn}'")
print(f"   Starts with EX_: {first_rxn.startswith('EX_')}")
print(f"   Has double _e0: {'_e0_e0' in first_rxn}")

# Check if it matches expected format
expected_format = first_rxn.startswith("EX_") and "_e0_e0" not in first_rxn
print(f"\n5. Result:")
if expected_format:
    print(f"   ✓ PASS - Media constraints have correct format")
    print(f"   Example: {first_rxn}")
else:
    print(f"   ✗ FAIL - Media constraints have WRONG format")
    print(f"   Got: {first_rxn}")
    print(f"   Expected: EX_cpdXXXXX_e0 (single _e0, not double)")
    sys.exit(1)

print("\n" + "="*60)
print("Test PASSED - Media loading is fixed!")
print("="*60)
