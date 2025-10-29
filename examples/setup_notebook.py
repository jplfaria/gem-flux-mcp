"""
Setup script for Jupyter notebooks.

Run this in the first cell of each notebook to configure the Python path.
"""
import sys
from pathlib import Path

# Add parent directory to Python path
repo_root = Path.cwd().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(f"✓ Added {repo_root} to Python path")
print(f"✓ Ready to import gem_flux_mcp modules")
