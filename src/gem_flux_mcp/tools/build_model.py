"""
build_model tool for constructing draft genome-scale metabolic models.

This module implements the build_model MCP tool according to specification
004-build-model-tool.md. It creates draft models from protein sequences using
template-based reconstruction with ModelSEEDpy.

Tool Capabilities:
    - Build models from protein sequences (dict or FASTA file)
    - Template-based reconstruction (GramNegative, GramPositive, Core)
    - Optional RAST annotation for improved reaction mapping
    - ATP maintenance (ATPM) reaction addition
    - Session-based model storage with .draft suffix

What this tool does NOT do (MVP):
    - Does not gapfill models (use gapfill_model)
    - Does not validate if model can grow
    - Does not optimize or refine models
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Optional

from modelseedpy import MSGenome, MSBuilder
from modelseedpy.core.rast_client import RastClient

from gem_flux_mcp.logging import get_logger
from gem_flux_mcp.errors import ValidationError, LibraryError
from gem_flux_mcp.storage.models import (
    generate_model_id,
    generate_model_id_from_name,
    store_model,
)
from gem_flux_mcp.templates.loader import get_template, validate_template_name
from gem_flux_mcp.utils.atp_correction import (
    apply_atp_correction as do_atp_correction,
    get_atp_correction_statistics,
)

logger = get_logger(__name__)

# Valid amino acid alphabet (standard 20 amino acids + U for selenocysteine)
# U (selenocysteine) and O (pyrrolysine) are rare but valid in some proteins
VALID_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWYU")


def validate_amino_acid_sequence(protein_id: str, sequence: str) -> tuple[bool, list[tuple[str, int]]]:
    """Validate amino acid sequence contains only valid characters.

    Args:
        protein_id: Protein identifier for error reporting
        sequence: Amino acid sequence to validate

    Returns:
        Tuple of (is_valid, list of (invalid_char, position) tuples)
    """
    sequence_upper = sequence.upper()
    invalid_chars = []

    for i, char in enumerate(sequence_upper):
        if char not in VALID_AMINO_ACIDS:
            invalid_chars.append((char, i))

    return len(invalid_chars) == 0, invalid_chars


def validate_protein_sequences(protein_sequences: dict[str, str]) -> dict[str, Any]:
    """Validate protein sequences dictionary.

    Args:
        protein_sequences: Dict mapping protein IDs to sequences

    Returns:
        Dict with validation results

    Raises:
        ValidationError: If validation fails
    """
    # Check non-empty
    if not protein_sequences:
        raise ValidationError(
            message="Protein sequences dictionary cannot be empty",
            error_code="EMPTY_PROTEIN_SEQUENCES",
            details={
                "num_sequences_provided": 0,
                "minimum_required": 1,
            },
            suggestions=["Provide at least one protein sequence in the protein_sequences dictionary."],
        )

    # Validate each sequence
    invalid_sequences = {}
    empty_sequences = []

    for protein_id, sequence in protein_sequences.items():
        # Check for empty sequence
        if not sequence or not sequence.strip():
            empty_sequences.append(protein_id)
            continue

        # Validate amino acids
        is_valid, invalid_chars = validate_amino_acid_sequence(protein_id, sequence)
        if not is_valid:
            invalid_sequences[protein_id] = {
                "invalid_chars": [char for char, _ in invalid_chars],
                "positions": [pos for _, pos in invalid_chars],
            }

    # Raise error if any validation issues
    if empty_sequences or invalid_sequences:
        error_details: dict[str, Any] = {
            "num_invalid": len(invalid_sequences),
            "num_valid": len(protein_sequences) - len(invalid_sequences) - len(empty_sequences),
            "valid_alphabet": "ACDEFGHIKLMNPQRSTVWY",
        }

        if empty_sequences:
            error_details["empty_sequences"] = empty_sequences

        if invalid_sequences:
            error_details["invalid_sequences"] = invalid_sequences

        raise ValidationError(
            message="Invalid amino acid characters found in protein sequences",
            error_code="INVALID_AMINO_ACIDS",
            details=error_details,
            suggestions=[
                "Remove invalid characters or ambiguous amino acid codes.",
                "Use standard 20 amino acids only: ACDEFGHIKLMNPQRSTVWY",
                "Stop codons (*) and unknown residues (X, B, Z) are not supported.",
            ],
        )

    return {"valid": True, "num_sequences": len(protein_sequences)}


def load_fasta_file(fasta_file_path: str) -> dict[str, str]:
    """Load protein sequences from FASTA file.

    Args:
        fasta_file_path: Path to FASTA file (.faa)

    Returns:
        Dict mapping protein IDs to sequences

    Raises:
        ValidationError: If file not found, invalid format, or validation fails
    """
    filepath = Path(fasta_file_path)

    # Check file exists
    if not filepath.exists():
        raise ValidationError(
            message="FASTA file not found or invalid format",
            error_code="FASTA_FILE_NOT_FOUND",
            details={
                "fasta_file_path": fasta_file_path,
                "error": "File does not exist",
            },
            suggestions=[
                "Verify file path is correct and file exists.",
                "FASTA files should have .faa extension.",
            ],
        )

    # Check file is readable
    if not filepath.is_file():
        raise ValidationError(
            message="FASTA file path is not a file",
            error_code="FASTA_PATH_NOT_FILE",
            details={
                "fasta_file_path": fasta_file_path,
            },
            suggestions=["Provide path to a FASTA file, not a directory."],
        )

    # Parse FASTA file
    protein_sequences = {}
    current_id = None
    current_seq = []

    try:
        with open(filepath, "r") as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Header line
                if line.startswith(">"):
                    # Save previous sequence
                    if current_id is not None:
                        protein_sequences[current_id] = "".join(current_seq)
                        current_seq = []

                    # Extract protein ID (first word after >)
                    header = line[1:].strip()
                    current_id = header.split()[0] if header else f"protein_{line_num}"

                # Sequence line
                else:
                    if current_id is None:
                        raise ValidationError(
                            message="FASTA file invalid: sequence before header",
                            error_code="FASTA_INVALID_FORMAT",
                            details={
                                "line_number": line_num,
                                "error": "Sequence line found before first header (>)",
                            },
                            suggestions=["FASTA files must start with header line (>protein_id)."],
                        )
                    current_seq.append(line)

            # Save last sequence
            if current_id is not None:
                protein_sequences[current_id] = "".join(current_seq)

    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(
            message=f"Failed to read FASTA file: {e}",
            error_code="FASTA_READ_ERROR",
            details={
                "fasta_file_path": fasta_file_path,
                "error": str(e),
            },
            suggestions=["Check file permissions and format."],
        )

    # Validate sequences loaded
    if not protein_sequences:
        raise ValidationError(
            message="FASTA file contains no sequences",
            error_code="FASTA_NO_SEQUENCES",
            details={
                "fasta_file_path": fasta_file_path,
            },
            suggestions=["FASTA file must contain at least one sequence."],
        )

    # Validate amino acid sequences
    validate_protein_sequences(protein_sequences)

    logger.info(f"Loaded {len(protein_sequences)} sequences from FASTA: {fasta_file_path}")
    return protein_sequences


def dict_to_fasta_file(protein_sequences: dict[str, str]) -> str:
    """Convert protein sequences dict to temporary FASTA file.

    Args:
        protein_sequences: Dict mapping protein IDs to sequences

    Returns:
        Path to temporary .faa file

    Raises:
        LibraryError: If file creation fails
    """
    try:
        temp_faa = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".faa",
            delete=False,
            prefix="gem_flux_proteins_",
        )

        for protein_id, sequence in protein_sequences.items():
            # Write FASTA header
            temp_faa.write(f">{protein_id}\n")

            # Write sequence (wrap at 80 characters for readability)
            for i in range(0, len(sequence), 80):
                temp_faa.write(f"{sequence[i:i+80]}\n")

        temp_faa.close()
        logger.debug(f"Created temporary FASTA file: {temp_faa.name}")
        return temp_faa.name

    except Exception as e:
        raise LibraryError(
            message=f"Failed to create temporary FASTA file: {e}",
            error_code="FASTA_CREATE_ERROR",
            details={"error": str(e)},
            suggestions=["Check system temporary directory permissions."],
        )


def create_genome_from_dict(
    protein_sequences: dict[str, str],
    annotate_with_rast: bool = False,
) -> MSGenome:
    """Create MSGenome from protein sequences dict.

    Args:
        protein_sequences: Dict mapping protein IDs to sequences
        annotate_with_rast: Whether to use RAST annotation (default: False for MVP)

    Returns:
        MSGenome object

    Raises:
        LibraryError: If genome creation fails
        ValidationError: If RAST annotation fails (when enabled)
    """
    if annotate_with_rast:
        # Convert dict to FASTA file for RAST
        fasta_path = dict_to_fasta_file(protein_sequences)

        try:
            # Create genome from FASTA, then annotate with RAST
            genome = MSGenome.from_fasta(fasta_path)
            rast_client = RastClient()
            rast_client.annotate_genome(genome)  # Annotates in-place
            logger.info(f"Created genome from RAST annotation ({len(protein_sequences)} sequences)")

        except Exception as e:
            raise ValidationError(
                message="RAST annotation request failed",
                error_code="RAST_ANNOTATION_ERROR",
                details={
                    "rast_status": "connection_error",
                    "error": str(e),
                },
                suggestions=[
                    "Check internet connection.",
                    "Retry with 'annotate_with_rast': false for offline mode.",
                ],
            )

        finally:
            # Clean up temporary file
            import os
            try:
                os.unlink(fasta_path)
                logger.debug(f"Cleaned up temporary FASTA file: {fasta_path}")
            except FileNotFoundError:
                pass  # Already deleted, that's fine
            except Exception as e:
                # Log but don't raise - cleanup failure shouldn't break the tool
                logger.warning(f"Failed to clean up temporary file {fasta_path}: {e}")

    else:
        # Offline mode: create genome directly from dict
        try:
            genome = MSGenome.from_protein_sequences_hash(protein_sequences)
            logger.info(f"Created genome from dict (offline mode, {len(protein_sequences)} sequences)")

        except Exception as e:
            raise LibraryError(
                message=f"Failed to create genome from protein sequences: {e}",
                error_code="GENOME_CREATE_ERROR",
                details={"error": str(e)},
                suggestions=["Check protein sequences format and ModelSEEDpy installation."],
            )

    return genome


def create_genome_from_fasta(
    fasta_file_path: str,
    annotate_with_rast: bool = False,
) -> MSGenome:
    """Create MSGenome from FASTA file.

    Args:
        fasta_file_path: Path to FASTA file
        annotate_with_rast: Whether to use RAST annotation (default: False for MVP)

    Returns:
        MSGenome object

    Raises:
        LibraryError: If genome creation fails
        ValidationError: If RAST annotation fails (when enabled)
    """
    if annotate_with_rast:
        try:
            # First create genome from FASTA
            genome = MSGenome.from_fasta(fasta_file_path)
            logger.info(f"Created genome from FASTA: {fasta_file_path}")

            # Then annotate with RAST
            rast_client = RastClient()
            rast_client.annotate_genome(genome)
            logger.info(f"Annotated genome with RAST")

        except Exception as e:
            raise ValidationError(
                message="RAST annotation request failed",
                error_code="RAST_ANNOTATION_ERROR",
                details={
                    "rast_status": "connection_error",
                    "attempted_file": fasta_file_path,
                    "error": str(e),
                },
                suggestions=[
                    "Check internet connection.",
                    "Retry with 'annotate_with_rast': false for offline mode.",
                ],
            )

    else:
        # Offline mode: create genome directly from FASTA
        try:
            genome = MSGenome.from_fasta(fasta_file_path)
            logger.info(f"Created genome from FASTA (offline mode): {fasta_file_path}")

        except Exception as e:
            raise LibraryError(
                message=f"Failed to create genome from FASTA file: {e}",
                error_code="GENOME_FROM_FASTA_ERROR",
                details={
                    "fasta_file_path": fasta_file_path,
                    "error": str(e),
                },
                suggestions=["Check FASTA file format and ModelSEEDpy installation."],
            )

    return genome


def collect_model_statistics(model: Any, template_name: str) -> dict[str, Any]:
    """Collect statistics about the built model.

    Args:
        model: COBRApy Model object
        template_name: Template used for building

    Returns:
        Dict with model statistics
    """
    # Count reactions by compartment
    reactions_by_compartment: dict[str, int] = {}
    metabolites_by_compartment: dict[str, int] = {}

    for reaction in model.reactions:
        # Extract compartment from reaction ID
        if "_" in reaction.id:
            compartment = reaction.id.split("_")[-1]
            reactions_by_compartment[compartment] = reactions_by_compartment.get(compartment, 0) + 1

    for metabolite in model.metabolites:
        # Extract compartment from metabolite ID
        if "_" in metabolite.id:
            compartment = metabolite.id.split("_")[-1]
            metabolites_by_compartment[compartment] = metabolites_by_compartment.get(compartment, 0) + 1

    # Count exchange reactions
    num_exchange = sum(1 for r in model.reactions if r.id.startswith("EX_"))

    # Count reversible vs irreversible
    num_reversible = sum(1 for r in model.reactions if r.lower_bound < 0 and r.upper_bound > 0)
    num_irreversible = len(model.reactions) - num_reversible

    # Count transport reactions (reactions with metabolites in multiple compartments)
    num_transport = 0
    for reaction in model.reactions:
        compartments = set()
        for metabolite in reaction.metabolites:
            if "_" in metabolite.id:
                compartments.add(metabolite.id.split("_")[-1])
        if len(compartments) > 1:
            num_transport += 1

    # Get compartments
    compartments = list(reactions_by_compartment.keys())

    # Check for biomass reaction
    has_biomass = any(r.id.startswith("bio") for r in model.reactions)
    biomass_reaction_id = next((r.id for r in model.reactions if r.id.startswith("bio")), "bio1")

    # Check for ATPM
    has_atpm = any("ATPM" in r.id for r in model.reactions)
    atpm_reaction_id = next((r.id for r in model.reactions if "ATPM" in r.id), "ATPM_c0")

    return {
        "num_reactions": len(model.reactions),
        "num_metabolites": len(model.metabolites),
        "num_genes": len(model.genes),
        "num_exchange_reactions": num_exchange,
        "template_used": template_name,
        "has_biomass_reaction": has_biomass,
        "biomass_reaction_id": biomass_reaction_id,
        "compartments": compartments,
        "has_atpm": has_atpm,
        "atpm_reaction_id": atpm_reaction_id,
        "statistics": {
            "reactions_by_compartment": reactions_by_compartment,
            "metabolites_by_compartment": metabolites_by_compartment,
            "reversible_reactions": num_reversible,
            "irreversible_reactions": num_irreversible,
            "transport_reactions": num_transport,
        },
        "model_properties": {
            "is_draft": True,
            "requires_gapfilling": True,
            "estimated_growth_without_gapfilling": 0.0,
        },
    }


async def build_model(
    protein_sequences: Optional[dict[str, str]] = None,
    fasta_file_path: Optional[str] = None,
    template: str = "GramNegative",
    model_name: Optional[str] = None,
    annotate_with_rast: bool = False,  # Default False for MVP (RAST not yet implemented)
    apply_atp_correction: bool = True,  # Default True - ON by default for biologically realistic models
) -> dict[str, Any]:
    """Build a draft genome-scale metabolic model from protein sequences.

    This tool creates a draft metabolic model using template-based reconstruction.
    The resulting model typically requires gapfilling to enable growth.

    ATP Correction (ON by default):
    By default, this tool applies ATP correction to produce biologically realistic models
    that match the published ModelSEED workflow. ATP correction:
    - Tests ATP production across multiple media conditions
    - Expands models to genome scale with additional reactions
    - Creates test conditions for multi-media validation during gapfilling
    - Results in more constrained, biologically realistic growth predictions

    ATP correction takes longer (~3-5 minutes vs ~30 seconds) but produces scientifically
    accurate models. You can disable it with apply_atp_correction=False for faster builds
    during development or testing.

    Args:
        protein_sequences: Dict mapping protein IDs to sequences (mutually exclusive with fasta_file_path)
        fasta_file_path: Path to FASTA file with protein sequences (mutually exclusive with protein_sequences)
        template: Template name ("GramNegative", "GramPositive", "Core")
        model_name: Optional custom model name
        annotate_with_rast: Use RAST annotation for improved mapping (default: False)
        apply_atp_correction: Apply ATP correction for biologically realistic models (default: True)

    Returns:
        Dict with success status, model_id, and model statistics

    Raises:
        ValidationError: If inputs invalid
        LibraryError: If model building fails
    """
    logger.info(f"build_model called: template={template}, annotate_with_rast={annotate_with_rast}, apply_atp_correction={apply_atp_correction}")

    # Step 1: Validate mutually exclusive inputs
    if protein_sequences is not None and fasta_file_path is not None:
        raise ValidationError(
            message="Cannot provide both protein_sequences and fasta_file_path",
            error_code="BOTH_INPUTS_PROVIDED",
            details={
                "provided_inputs": ["protein_sequences", "fasta_file_path"],
            },
            suggestions=["Choose ONE input method: either 'protein_sequences' (dict) OR 'fasta_file_path' (string path)."],
        )

    if protein_sequences is None and fasta_file_path is None:
        raise ValidationError(
            message="Must provide either protein_sequences or fasta_file_path",
            error_code="NO_INPUT_PROVIDED",
            details={
                "provided_inputs": [],
            },
            suggestions=["Provide protein sequences via 'protein_sequences' dict OR 'fasta_file_path' string."],
        )

    # Step 2: Validate template name
    if not validate_template_name(template):
        available_templates = ["GramNegative", "GramPositive", "Core"]
        raise ValidationError(
            message="Invalid template name specified",
            error_code="INVALID_TEMPLATE",
            details={
                "provided_template": template,
                "valid_templates": available_templates,
            },
            suggestions=[
                "Choose from valid templates: 'GramNegative' for E. coli-like organisms, "
                "'GramPositive' for Bacillus-like organisms, or 'Core' for central metabolism only."
            ],
        )

    # Step 3: Load protein sequences
    if protein_sequences is not None:
        # Validate dict input
        validate_protein_sequences(protein_sequences)
        sequences = protein_sequences
    else:
        # Load and validate FASTA file
        sequences = load_fasta_file(fasta_file_path)  # type: ignore

    # Step 4: Load template
    try:
        template_obj = get_template(template)
        logger.info(f"Loaded template: {template}")
    except Exception as e:
        raise LibraryError(
            message=f"Failed to load ModelSEED template: {e}",
            error_code="TEMPLATE_LOAD_ERROR",
            details={
                "template": template,
                "error": str(e),
            },
            suggestions=["Ensure ModelSEEDpy is correctly installed. Try reinstalling with 'uv sync'."],
        )

    # Step 5: Create genome
    try:
        if protein_sequences is not None:
            genome = create_genome_from_dict(sequences, annotate_with_rast)
        else:
            genome = create_genome_from_fasta(fasta_file_path, annotate_with_rast)  # type: ignore
    except (ValidationError, LibraryError):
        raise
    except Exception as e:
        raise LibraryError(
            message=f"Failed to create genome: {e}",
            error_code="GENOME_CREATE_ERROR",
            details={"error": str(e)},
            suggestions=["Check protein sequences and ModelSEEDpy installation."],
        )

    # Step 6: Initialize MSBuilder and build base model
    try:
        # Generate base model ID for builder
        if model_name:
            base_model_id = model_name
        else:
            base_model_id = "temp_model"

        builder = MSBuilder(genome, template_obj, base_model_id)
        logger.info(f"Initialized MSBuilder with {len(sequences)} sequences")

        # Build base model
        model = builder.build_base_model(base_model_id, annotate_with_rast=annotate_with_rast)
        logger.info(f"Built base model: {len(model.reactions)} reactions")

    except Exception as e:
        raise LibraryError(
            message=f"Model building process failed: {e}",
            error_code="MODEL_BUILD_ERROR",
            details={
                "stage": "base_model_construction",
                "error": str(e),
            },
            suggestions=["Check protein sequences for validity. If problem persists, this may be a ModelSEEDpy library issue."],
        )

    # Step 7: Add ATPM reaction
    try:
        builder.add_atpm(model)
        logger.info("Added ATPM reaction")
    except Exception as e:
        logger.warning(f"Failed to add ATPM reaction: {e}")
        # Continue anyway - ATPM is optional

    # Step 7.5: Apply ATP correction (if enabled)
    test_conditions = None
    atp_stats = None
    if apply_atp_correction:
        try:
            logger.info("ATP correction enabled - applying workflow (this may take 3-5 minutes)...")
            original_num_reactions = len(model.reactions)

            # Load Core template for ATP correction
            core_template = get_template("Core")

            # Apply ATP correction workflow
            model, test_conditions = do_atp_correction(model, core_template)

            # Collect statistics
            atp_stats = get_atp_correction_statistics(
                original_num_reactions,
                len(model.reactions),
                test_conditions
            )
            logger.info(f"ATP correction completed: {atp_stats['reactions_added_by_correction']} reactions added")

        except Exception as e:
            logger.warning(f"ATP correction failed: {e}")
            logger.warning("Continuing without ATP correction - model may have unrealistic growth rates")
            test_conditions = None
            atp_stats = None
            # Continue anyway - ATP correction failure shouldn't break the tool
    else:
        logger.info("ATP correction disabled - model may have unrealistic growth rates")

    # Step 8: Generate model ID with .draft suffix
    if model_name:
        model_id = generate_model_id_from_name(model_name, state="draft")
    else:
        model_id = generate_model_id(state="draft")

    # Step 9: Store model in session
    try:
        store_model(model_id, model)
        logger.info(f"Stored model in session: {model_id}")

        # Store test_conditions alongside model if ATP correction was applied
        if test_conditions is not None:
            test_conditions_id = f"{model_id}.test_conditions"
            store_model(test_conditions_id, test_conditions)
            logger.info(f"Stored ATP correction test_conditions: {test_conditions_id}")

    except Exception as e:
        raise LibraryError(
            message=f"Failed to store model in session: {e}",
            error_code="MODEL_STORAGE_ERROR",
            details={"model_id": model_id, "error": str(e)},
            suggestions=["This is an internal error. Please report if it persists."],
        )

    # Step 10: Collect statistics
    stats = collect_model_statistics(model, template)

    # Step 11: Build response
    response = {
        "success": True,
        "model_id": model_id,
        "model_name": model_name,
        "annotated_with_rast": annotate_with_rast,
        **stats,
    }

    # Include ATP correction statistics if available
    if atp_stats is not None:
        response["atp_correction"] = atp_stats
    else:
        response["atp_correction"] = {
            "atp_correction_applied": False,
            "warning": "ATP correction disabled or failed - model may have unrealistic growth rates",
        }

    logger.info(f"build_model completed successfully: {model_id}")
    return response
