# Import notebook setup helper
from notebook_setup import quick_setup

# Import Gem-Flux MCP tools
from gem_flux_mcp.tools.build_model import build_model
from gem_flux_mcp.tools.list_models import list_models
from gem_flux_mcp.tools.list_media import list_media
from gem_flux_mcp.tools.delete_model import delete_model
from gem_flux_mcp.tools.delete_media import delete_media
from gem_flux_mcp.tools.media_builder import build_media
from gem_flux_mcp.types import (
    ListModelsRequest,
    DeleteModelRequest,
    DeleteMediaRequest,
    BuildMediaRequest,
)

print("✓ Imports successful")


# Setup environment
db_index, templates, atp_media, predefined_media = quick_setup()

print("\n✓ Environment ready!")
print(f"  Database: {db_index.get_compound_count()} compounds")
print(f"  Templates: {list(templates.keys())}")
print(f"  Predefined media: {list(predefined_media.keys())}")


# List all models (should be empty initially)
request = ListModelsRequest()
response = list_models(request)

print(f"Total models: {response['total_models']}")
print(f"By state: {response['models_by_state']}")

if response['models']:
    for model in response['models']:
        print(f"\n{model['model_id']}:")
        print(f"  State: {model['state']}")
        print(f"  Reactions: {model['num_reactions']}")
else:
    print("\nNo models in session yet.")


# Build E. coli model from FASTA file
print("Building E. coli model from genome...\n")

build_response_1 = await build_model(
    fasta_file_path="examples/ecoli_proteins.fasta",
    template="GramNegative",
    model_name="E_coli_test",
    annotate_with_rast=True
)

print(f"✓ Model built: {build_response_1['model_id']}")
print(f"  Reactions: {build_response_1['num_reactions']}")
print(f"  Genes: {build_response_1['num_genes']}")


# Build B. subtilis model from dictionary of protein sequences
# This demonstrates building from protein_sequences dict instead of FASTA file
print("Parsing B. subtilis FASTA to create dictionary of protein sequences...\n")

# Parse FASTA file to extract protein ID → amino acid sequence mapping
protein_sequences = {}
current_id = None
current_seq = []

with open("examples/B_subtilies_proteins.faa", "r") as f:
    for line in f:
        line = line.strip()
        if line.startswith(">"):
            # Save previous sequence if exists
            if current_id is not None:
                protein_sequences[current_id] = "".join(current_seq)
            # Start new sequence
            # Header line: >NP_387882.1 chromosomal replication...
            parts = line[1:].split(" ", 1)  # Remove '>' and split on first space
            current_id = parts[0]
            current_seq = []
        else:
            # Sequence line
            current_seq.append(line)

    # Save last sequence
    if current_id is not None:
        protein_sequences[current_id] = "".join(current_seq)

print(f"Parsed {len(protein_sequences)} protein sequences from FASTA")
# Show example with sequence preview
example_id, example_seq = list(protein_sequences.items())[0]
print(f"Example: {example_id}: {example_seq[:50]}... (length: {len(example_seq)} aa)")

# Build model from dictionary
print("\nBuilding B. subtilis model from dictionary of protein sequences...")
print("This will take 2-5 minutes for RAST annotation and model construction.\n")

build_response_2 = await build_model(
    protein_sequences=protein_sequences,
    template="GramPositive",  # B. subtilis is Gram-positive
    model_name="B_subtilis_168",
    annotate_with_rast=True
)

print(f"✓ Model built: {build_response_2['model_id']}")
print(f"  Reactions: {build_response_2['num_reactions']}")
print(f"  Genes: {build_response_2['num_genes']}")


# List all models
request = ListModelsRequest()
response = list_models(request)

print(f"Total models: {response['total_models']}")
print(f"By state: {response['models_by_state']}")

print("\nModels in session:")
for model in response['models']:
    print(f"\n{model['model_id']}:")
    print(f"  State: {model['state']}")
    print(f"  Reactions: {model['num_reactions']}")
    print(f"  Metabolites: {model['num_metabolites']}")
    print(f"  Genes: {model['num_genes']}")
    print(f"  Template: {model['template_used']}")


# List media - note: list_media() takes NO arguments
media_response = list_media()

print(f"Total media: {media_response['total_media']}")
print(f"Predefined: {media_response['predefined_media']}")
print(f"User-created: {media_response['user_created_media']}")

print("\nAvailable media:")
for media in media_response['media']:
    print(f"  {media['media_id']} ({media['media_type']})")


# Create a custom minimal media
custom_media_request = BuildMediaRequest(
    compounds=[
        "cpd00027",  # D-Glucose
        "cpd00007",  # O2
        "cpd00001",  # H2O
        "cpd00009",  # Phosphate
        "cpd00013",  # NH3
        "cpd00048",  # SO4
        "cpd00205",  # K+
        "cpd00254",  # Mg
    ],
    default_uptake=100.0,
    custom_bounds={}
)

custom_media_response = build_media(custom_media_request, db_index)

print(f"✓ Created custom media: {custom_media_response['media_id']}")
print(f"  Compounds: {custom_media_response['num_compounds']}")
print(f"  Type: {custom_media_response['media_type']}")


# List media again
media_response = list_media()

print(f"Total media: {media_response['total_media']}")
print(f"Predefined: {media_response['predefined_media']}")
print(f"User-created: {media_response['user_created_media']}")

print("\nUser-created media:")
for media in media_response['media']:
    if media['media_type'] == 'custom':
        print(f"  {media['media_id']}")


# Delete the second model
delete_request = DeleteModelRequest(
    model_id=build_response_2['model_id']
)

delete_response = delete_model(delete_request)

print(f"✓ Deleted: {delete_response['deleted_model_id']}")
print(f"  Success: {delete_response['success']}")


# List models after deletion
request = ListModelsRequest()
response = list_models(request)

print(f"Total models after deletion: {response['total_models']}")

print("\nRemaining models:")
for model in response['models']:
    print(f"  {model['model_id']}")


# Delete the custom media
delete_media_request = DeleteMediaRequest(
    media_id=custom_media_response['media_id']
)

delete_media_response = delete_media(delete_media_request)

print(f"✓ Deleted media: {delete_media_response['deleted_media_id']}")
print(f"  Success: {delete_media_response['success']}")


# List media after deletion
media_response = list_media()

print(f"Total media: {media_response['total_media']}")
print(f"User-created: {media_response['user_created_media']}")
print("\nShould only have predefined media remaining.")

