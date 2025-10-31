#!/usr/bin/env python3
"""
Test full workflow using stored glucose_minimal_aerobic.json media file.
This should produce identical results to using the inline media dict.

Expected Result: Growth rate of 0.5544 (same as before)
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

import asyncio
import json
from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.tools.build_model import build_model
from gem_flux_mcp.tools.gapfill_model import gapfill_model
from gem_flux_mcp.tools.media_builder import build_media, BuildMediaRequest
from gem_flux_mcp.tools.run_fba import run_fba
from gem_flux_mcp.storage.models import clear_all_models, MODEL_STORAGE
from gem_flux_mcp.storage.media import clear_all_media
from gem_flux_mcp.templates.loader import load_templates

print("=" * 80)
print("WORKFLOW TEST: Using stored glucose_minimal_aerobic.json")
print("=" * 80)

# Setup paths
fasta_path = Path(__file__).parent / "specs-source" / "build_metabolic_model" / "GCF_000005845.2_ASM584v2_protein.faa"
db_dir = Path(__file__).parent / "data" / "database"
template_dir = Path(__file__).parent / "data" / "templates"
media_file = Path(__file__).parent / "data" / "media" / "glucose_minimal_aerobic.json"

print(f"\nPaths:")
print(f"  FASTA: {fasta_path.exists()}")
print(f"  Database dir: {db_dir.exists()}")
print(f"  Templates dir: {template_dir.exists()}")
print(f"  Media file: {media_file.exists()}")

# Load media file to inspect
with open(media_file) as f:
    media_json = json.load(f)

print(f"\nMedia file contents:")
print(f"  Name: {media_json['name']}")
print(f"  Description: {media_json['description']}")
print(f"  Number of compounds: {len(media_json['compounds'])}")

# Clear storage
print("\nClearing storage...")
clear_all_models()
clear_all_media()
print("✓ Storage cleared")

# Load database
print("\n" + "=" * 80)
print("STEP 1: Load Database")
print("=" * 80)
compounds_df = load_compounds_database(db_dir / "compounds.tsv")
reactions_df = load_reactions_database(db_dir / "reactions.tsv")
db_index = DatabaseIndex(compounds_df, reactions_df)
print(f"✓ Database loaded")
print(f"  Compounds: {len(compounds_df)}")
print(f"  Reactions: {len(reactions_df)}")

# Load templates
print("\n" + "=" * 80)
print("STEP 2: Load Templates")
print("=" * 80)
load_templates(template_dir)
print(f"✓ Templates loaded from {template_dir}")

async def run_workflow():
    # Build model with ATP correction
    print("\n" + "=" * 80)
    print("STEP 3: Build Model with ATP Correction")
    print("=" * 80)
    print("Parameters:")
    print(f"  FASTA: {fasta_path}")
    print(f"  Template: GramNegative")
    print(f"  Model name: ecoli_stored_media")
    print(f"  RAST annotation: True")
    print(f"  ATP correction: True (default)")
    print("\nExpected time: ~5-7 minutes (RAST + ATP correction)")

    build_response = await build_model(
        fasta_file_path=str(fasta_path),
        template="GramNegative",
        model_name="ecoli_stored_media",
        annotate_with_rast=True,
        apply_atp_correction=True
    )

    print(f"\n✓ Model built successfully")
    print(f"  Model ID: {build_response['model_id']}")
    print(f"  Success: {build_response['success']}")
    print(f"  Genes: {build_response['num_genes']}")
    print(f"  Reactions: {build_response['num_reactions']}")
    print(f"  Metabolites: {build_response['num_metabolites']}")

    # ATP correction statistics
    if "atp_correction" in build_response:
        atp_stats = build_response["atp_correction"]
        print(f"\n  ATP Correction Statistics:")
        print(f"    Applied: {atp_stats['atp_correction_applied']}")
        print(f"    Reactions before: {atp_stats['reactions_before_correction']}")
        print(f"    Reactions after: {atp_stats['reactions_after_correction']}")
        print(f"    Reactions added: {atp_stats['reactions_added_by_correction']}")
        print(f"    Test conditions: {atp_stats['num_test_conditions']}")

    model_id = build_response["model_id"]

    # Build media from stored JSON file
    print("\n" + "=" * 80)
    print("STEP 4: Build Media from glucose_minimal_aerobic.json")
    print("=" * 80)

    # Extract compounds and bounds from JSON file
    compounds = []
    custom_bounds = {}

    for cpd_id, cpd_data in media_json['compounds'].items():
        compounds.append(cpd_id)
        custom_bounds[cpd_id] = tuple(cpd_data['bounds'])

    print(f"Loaded from file:")
    print(f"  Compounds: {len(compounds)}")
    print(f"  All compound IDs: {sorted(compounds)}")

    media_request = BuildMediaRequest(
        compounds=compounds,
        default_uptake=100.0,  # Won't be used since we provide custom_bounds for all
        custom_bounds=custom_bounds
    )

    media_response = build_media(media_request, db_index)
    media_id = media_response["media_id"]
    print(f"\n✓ Media created from stored file")
    print(f"  Media ID: {media_id}")
    print(f"  Compounds: {len(media_response['compounds'])}")

    # Print media composition for verification
    print("\nMedia composition from file:")
    for cpd_info in sorted(media_response['compounds'], key=lambda x: x['id']):
        bounds = cpd_info['bounds']
        print(f"  {cpd_info['id']}: {bounds}")

    # Gapfill model
    print("\n" + "=" * 80)
    print("STEP 5: Gapfill Model")
    print("=" * 80)
    print("Parameters:")
    print(f"  Model ID: {model_id}")
    print(f"  Media ID: {media_id}")
    print(f"  Target growth rate: 0.01")
    print(f"  Gapfill mode: full (ATP + genome-scale)")
    print("\nExpected: ATP correction SKIPPED (test_conditions reused)")
    print("Expected time: ~5-10 minutes (only genome-scale gapfilling)")

    gapfill_result = gapfill_model(
        model_id=model_id,
        media_id=media_id,
        db_index=db_index,
        target_growth_rate=0.01,
        gapfill_mode="full",
    )

    print(f"\n✓ Gapfilling completed")
    print(f"  Gapfilled model ID: {gapfill_result['model_id']}")
    print(f"  Success: {gapfill_result['success']}")
    print(f"  Gapfilling successful: {gapfill_result['gapfilling_successful']}")
    print(f"  Growth rate before: {gapfill_result['growth_rate_before']:.6f}")
    print(f"  Growth rate after: {gapfill_result['growth_rate_after']:.6f}")
    print(f"  Target growth rate: {gapfill_result['target_growth_rate']:.6f}")
    print(f"  Reactions added: {gapfill_result.get('num_reactions_added', 0)}")

    # ATP correction statistics
    if "atp_correction" in gapfill_result:
        atp_gapfill_stats = gapfill_result["atp_correction"]
        print(f"\n  ATP Correction (in gapfilling):")
        print(f"    Performed: {atp_gapfill_stats['performed']}")
        if not atp_gapfill_stats['performed']:
            print(f"    Test conditions reused: {atp_gapfill_stats.get('test_conditions_reused', 'N/A')}")
        else:
            print(f"    Media tested: {atp_gapfill_stats.get('media_tested', 0)}")
            print(f"    Reactions added: {atp_gapfill_stats.get('reactions_added', 0)}")

    # Genome-scale gapfilling statistics
    if "genomescale_gapfill" in gapfill_result:
        genomescale_stats = gapfill_result["genomescale_gapfill"]
        print(f"\n  Genome-scale Gapfilling:")
        print(f"    Performed: {genomescale_stats['performed']}")
        print(f"    Reactions added: {genomescale_stats.get('reactions_added', 0)}")

    gapfilled_model_id = gapfill_result["model_id"]

    # Run FBA
    print("\n" + "=" * 80)
    print("STEP 6: Run FBA")
    print("=" * 80)
    print("Parameters:")
    print(f"  Model ID: {gapfilled_model_id}")
    print(f"  Media ID: {media_id}")
    print(f"  Objective: bio1")
    print(f"  Maximize: True")
    print(f"  Flux threshold: 0.001")

    fba_result = run_fba(
        model_id=gapfilled_model_id,
        media_id=media_id,
        db_index=db_index,
        objective="bio1",
        maximize=True,
        flux_threshold=0.001
    )

    print(f"\n✓ FBA completed")
    print(f"  Status: {fba_result['status']}")
    print(f"  Objective value: {fba_result['objective_value']:.6f}")
    print(f"  Active reactions: {fba_result['active_reactions']}")
    print(f"  Uptake fluxes: {len(fba_result['uptake_fluxes'])}")
    print(f"  Secretion fluxes: {len(fba_result['secretion_fluxes'])}")

    # Final results
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Status: {fba_result['status']}")
    print(f"Growth Rate: {fba_result['objective_value']:.6f}")
    print(f"Objective: bio1")
    print(f"\nExpected: 0.5544")
    print(f"Actual: {fba_result['objective_value']:.6f}")
    print(f"Difference: {abs(fba_result['objective_value'] - 0.5544):.6f}")

    if abs(fba_result['objective_value'] - 0.5544) < 0.001:
        print(f"\n✓✓✓ SUCCESS! Matches expected growth rate ✓✓✓")
    else:
        print(f"\n✗ MISMATCH! Does not match expected growth rate")

    # Summary
    print("\n" + "=" * 80)
    print("WORKFLOW SUMMARY")
    print("=" * 80)
    print(f"1. Model built: {model_id}")
    print(f"   - Genes: {build_response['num_genes']}")
    print(f"   - Reactions: {build_response['num_reactions']}")
    print(f"   - ATP correction reactions added: {build_response['atp_correction']['reactions_added_by_correction']}")
    print(f"2. Media built from: glucose_minimal_aerobic.json")
    print(f"   - Compounds: {len(media_response['compounds'])}")
    print(f"3. Model gapfilled: {gapfilled_model_id}")
    print(f"   - ATP correction reused: {not gapfill_result['atp_correction']['performed']}")
    print(f"   - Reactions added: {gapfill_result.get('num_reactions_added', 0)}")
    print(f"   - Growth rate after: {gapfill_result['growth_rate_after']:.6f}")
    print(f"4. FBA completed:")
    print(f"   - Growth rate: {fba_result['objective_value']:.6f}")
    print(f"   - Active reactions: {fba_result['active_reactions']}")
    print("=" * 80)

    return build_response, media_response, gapfill_result, fba_result

# Run workflow
build_resp, media_resp, gapfill_resp, fba_resp = asyncio.run(run_workflow())
