#!/usr/bin/env python3
"""Debug media application to understand the exchange reaction mismatch."""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.tools.gapfill_model import gapfill_model
from gem_flux_mcp.tools.build_model import build_model
from gem_flux_mcp.storage.models import clear_all_models, retrieve_model
from gem_flux_mcp.storage.media import clear_all_media, store_media, retrieve_media, generate_media_id
from gem_flux_mcp.templates import load_templates
from modelseedpy.core.msmedia import MSMedia
import asyncio
import json
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')


async def main():
    clear_all_media()
    clear_all_models()

    print("=" * 70)
    print("Debug: Media Application Investigation")
    print("=" * 70)

    # Load templates
    print("\n1. Loading templates...")
    template_dir = Path(__file__).parent / "data" / "templates"
    load_templates(template_dir)

    # Load database
    print("\n2. Loading database...")
    db_dir = Path(__file__).parent / "data" / "database"
    compounds_df = load_compounds_database(db_dir / "compounds.tsv")
    reactions_df = load_reactions_database(db_dir / "reactions.tsv")
    db_index = DatabaseIndex(compounds_df, reactions_df)

    # Load media
    print("\n3. Loading media...")
    media_file = Path(__file__).parent / "data" / "media" / "glucose_minimal_aerobic.json"

    with open(media_file) as f:
        media_data = json.load(f)

    media_dict = {}
    for cpd_id, cpd_info in media_data["compounds"].items():
        bounds = cpd_info["bounds"]
        media_dict[cpd_id] = (bounds[0], bounds[1])

    media = MSMedia.from_dict(media_dict)
    media_id = generate_media_id()
    store_media(media_id, media)
    print(f"   ✓ Media stored: {media_id}")

    # Build model
    print("\n4. Building model...")
    fasta_path = Path(__file__).parent / "examples" / "GCF_000005845.2_ASM584v2_protein.faa"

    result = await build_model(
        fasta_file_path=str(fasta_path),
        template="GramNegative",
        model_name="debug_media",
        annotate_with_rast=True
    )

    model_id = result['model_id']
    print(f"   ✓ Model: {model_id}")

    # Gapfill
    print("\n5. Running gapfilling...")
    gapfill_result = gapfill_model(
        model_id=model_id,
        media_id=media_id,
        db_index=db_index,
        target_growth_rate=0.01,
        gapfill_mode="full",
    )
    print(f"   ✓ Growth after gapfilling: {gapfill_result['growth_rate_after']:.6f}")

    # Now debug the media application
    print("\n6. Debugging media application...")

    # Get the model and media
    model = retrieve_model(model_id)
    media_obj = retrieve_media(media_id)

    # Get media constraints
    print("\n   Media constraints from get_media_constraints(cmp='e0'):")
    media_constraints = media_obj.get_media_constraints(cmp="e0")
    for cpd_id, (lb, ub) in list(media_constraints.items())[:5]:
        print(f"      {cpd_id}: ({lb}, {ub})")
    print(f"   ... {len(media_constraints)} total compounds")

    # Check exchange reactions in model
    print("\n   Exchange reactions in model:")
    exchange_rxns = [r.id for r in model.reactions if r.id.startswith("EX_")]
    for rxn_id in exchange_rxns[:10]:
        print(f"      {rxn_id}")
    print(f"   ... {len(exchange_rxns)} total exchange reactions")

    # Check for matches
    print("\n   Checking for matches:")
    matches = []
    mismatches = []

    for cpd_id in media_constraints.keys():
        expected_rxn_id = f"EX_{cpd_id}"
        if expected_rxn_id in [r.id for r in model.reactions]:
            matches.append((cpd_id, expected_rxn_id))
        else:
            mismatches.append((cpd_id, expected_rxn_id))

    print(f"\n   ✓ Matches found: {len(matches)}")
    if matches:
        for cpd_id, rxn_id in matches[:5]:
            print(f"      {cpd_id} → {rxn_id} ✓")

    print(f"\n   ✗ Mismatches found: {len(mismatches)}")
    if mismatches:
        for cpd_id, rxn_id in mismatches[:5]:
            print(f"      {cpd_id} → {rxn_id} NOT FOUND")
            # Try to find similar reactions
            similar = [r.id for r in model.reactions if cpd_id.split("_")[0] in r.id]
            if similar:
                print(f"         Similar: {similar[:3]}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
