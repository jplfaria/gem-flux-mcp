# Claude Code Guidelines for Gem-Flux MCP

## Notebook Guidelines

When working with Jupyter notebooks in this project:

- **ALWAYS create notebooks in one-shot mode with all cells at once**
  - Never add cells iteratively or one-by-one (they end up in random order)
  - Create the ENTIRE notebook structure at once

- **NEVER add cells iteratively**
  - Iterative cell addition leads to cell ordering issues
  - All cells must be defined in their correct order from the start

- **Make all visualizations "aesthetically pleasing"**
  - Use proper formatting, labels, and styling
  - Ensure plots and outputs are clear and professional

- **Use jupyter nbconvert for conversions**
  - Convert notebooks to Python for testing: `jupyter nbconvert --to script notebook.ipynb`
  - Clean up image data: `sed -i '' '/data:image\//d' notebook.py`
  - Always test converted Python versions to ensure notebook code is correct

## Testing Philosophy

- **Use real-world data in examples and notebooks**
  - Prefer actual genome files over mock sequences
  - Use real compound IDs from the database
  - Test with realistic use cases that users will encounter

- **Test both input methods when applicable**
  - For model building: test both FASTA file path and dictionary of functions
  - Ensure all tool input variations are covered in examples
