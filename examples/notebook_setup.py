"""
Notebook Setup Helper for Gem-Flux MCP Examples

This module provides a convenient setup function for Jupyter notebooks that:
1. Changes working directory to repository root
2. Loads all necessary components (database, templates, media)
3. Returns initialized objects ready for use

Usage in notebooks:
    from notebook_setup import setup_environment

    db_index, templates, atp_media, predefined_media = setup_environment()
"""

import os
import sys
from pathlib import Path
from typing import Tuple, Dict, Any


def setup_environment(verbose: bool = True) -> Tuple[Any, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Set up the notebook environment with all required components.

    This function:
    1. Changes working directory to repository root (if in examples/)
    2. Ensures gem_flux_mcp is importable
    3. Loads database index
    4. Loads ModelSEED templates
    5. Loads ATP gapfilling media
    6. Loads predefined media library

    Args:
        verbose: Print status messages during setup (default: True)

    Returns:
        Tuple of (db_index, templates, atp_media, predefined_media)
        - db_index: DatabaseIndex object
        - templates: Dict of loaded MSTemplate objects
        - atp_media: Dict of ATP test media
        - predefined_media: Dict of predefined media

    Example:
        >>> from notebook_setup import setup_environment
        >>> db_index, templates, atp_media, predefined_media = setup_environment()
        ✓ Changed to repository root: /Users/user/repos/gem-flux-mcp
        ✓ Loaded 33992 compounds and 43774 reactions
        ✓ Loaded 2 templates: ['GramNegative', 'Core']
        ✓ Loaded 54 ATP test media
        ✓ Loaded 4 predefined media: ['glucose_minimal_aerobic', ...]
    """
    # Step 1: Change to repository root if we're in examples/
    current_dir = Path.cwd()

    if current_dir.name == "examples":
        repo_root = current_dir.parent
        os.chdir(repo_root)
        if verbose:
            print(f"✓ Changed to repository root: {repo_root}")
    elif (current_dir / "examples").exists() and (current_dir / "src").exists():
        # Already in repo root
        if verbose:
            print(f"✓ Already in repository root: {current_dir}")
    else:
        # Try to find repo root by looking for src/gem_flux_mcp
        repo_root = current_dir
        while repo_root != repo_root.parent:
            if (repo_root / "src" / "gem_flux_mcp").exists():
                os.chdir(repo_root)
                if verbose:
                    print(f"✓ Changed to repository root: {repo_root}")
                break
            repo_root = repo_root.parent
        else:
            print(f"⚠ Warning: Could not find repository root. Current directory: {current_dir}")

    # Step 2: Ensure gem_flux_mcp is importable
    repo_root = Path.cwd()
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Step 3: Import required modules
    try:
        from gem_flux_mcp.database.loader import load_compounds_database, load_reactions_database
        from gem_flux_mcp.database.index import DatabaseIndex
        from gem_flux_mcp.templates.loader import load_templates
        from gem_flux_mcp.media.atp_loader import load_atp_media
        from gem_flux_mcp.media.predefined_loader import load_predefined_media
    except ImportError as e:
        print(f"✗ Error importing gem_flux_mcp modules: {e}")
        print(f"  Current directory: {Path.cwd()}")
        print(f"  sys.path includes: {src_path}")
        raise

    # Step 4: Load database
    if verbose:
        print("\nLoading database from data/database...")

    compounds_df = load_compounds_database("data/database/compounds.tsv")
    reactions_df = load_reactions_database("data/database/reactions.tsv")
    db_index = DatabaseIndex(compounds_df, reactions_df)

    if verbose:
        print(f"✓ Loaded {db_index.get_compound_count()} compounds and {db_index.get_reaction_count()} reactions")

    # Step 5: Load templates
    if verbose:
        print("\nLoading templates from data/templates...")

    templates = load_templates()

    if verbose:
        print(f"✓ Loaded {len(templates)} templates: {list(templates.keys())}")

    # Step 6: Load ATP media
    if verbose:
        print("\nLoading ATP gapfilling media...")

    atp_media = load_atp_media()

    if verbose:
        print(f"✓ Loaded {len(atp_media)} ATP test media")

    # Step 7: Load predefined media
    if verbose:
        print("\nLoading predefined media library...")

    predefined_media = load_predefined_media()

    if verbose:
        media_names = list(predefined_media.keys())
        print(f"✓ Loaded {len(predefined_media)} predefined media: {media_names}")

    # Step 8: Store predefined media in session for immediate use
    from gem_flux_mcp.storage.media import store_media
    from modelseedpy.core.msmedia import MSMedia

    for media_id, media_dict in predefined_media.items():
        try:
            # Convert dict to MSMedia object before storing
            # MSMedia.from_dict expects just the compounds dict with bounds
            compounds_dict = media_dict["compounds"]
            media_obj = MSMedia.from_dict(compounds_dict)
            media_obj.id = media_id  # Set the media ID
            store_media(media_id, media_obj)
        except RuntimeError:
            # Already exists, that's fine
            pass

    if verbose:
        print(f"✓ Stored {len(predefined_media)} predefined media in session")

    if verbose:
        print("\n" + "="*60)
        print("Environment setup complete! Ready to use.")
        print("="*60)

    return db_index, templates, atp_media, predefined_media


def clear_session_storage(verbose: bool = True):
    """
    Clear the in-memory session storage.

    This is useful when restarting a notebook or clearing all models/media
    from the current session.

    Args:
        verbose: Print status message (default: True)
    """
    from gem_flux_mcp.storage.models import MODEL_STORAGE
    from gem_flux_mcp.storage.media import MEDIA_STORAGE

    MODEL_STORAGE.clear()
    MEDIA_STORAGE.clear()

    if verbose:
        print("✓ Session storage cleared")


# Convenience function for quick setup
def quick_setup() -> Tuple[Any, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Quick setup with storage clearing.

    Combines clear_session_storage() and setup_environment() for convenience.

    Returns:
        Tuple of (db_index, templates, atp_media, predefined_media)
    """
    clear_session_storage()
    return setup_environment()
