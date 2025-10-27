# UV Package Manager Guide for Gem-Flux MCP Server

**Purpose**: Guide for using UV as the Python package manager for the Gem-Flux MCP server project.

**Official Documentation**: https://docs.astral.sh/uv/

## Overview

UV is an extremely fast Python package and project manager written in Rust. It replaces multiple tools:
- **pip** - Package installation
- **pip-tools** - Dependency resolution
- **virtualenv** - Virtual environment creation
- **pyenv** - Python version management
- **pipx** - Tool installation

**Key Benefits**:
- **10-100x faster** than pip for package installation
- **Unified tool** - One command for all Python project needs
- **Built-in Python management** - No need for pyenv
- **Lock files** - Reproducible environments
- **GitHub Actions integration** - First-class CI/CD support

---

## Installation

### macOS/Linux (Recommended)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### macOS (Homebrew)

```bash
brew install uv
```

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Verify Installation

```bash
uv --version
# Output: uv 0.5.11 (or later)
```

### Shell Completion (Optional)

```bash
# Bash
echo 'eval "$(uv generate-shell-completion bash)"' >> ~/.bashrc

# Zsh
echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc

# Fish
uv generate-shell-completion fish > ~/.config/fish/completions/uv.fish
```

---

## Quick Start for Gem-Flux MCP

### For Users Installing Gem-Flux

```bash
# Clone repository
git clone https://github.com/yourorg/gem-flux-mcp.git
cd gem-flux-mcp

# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Run the MCP server
uv run python -m fastmcp run src/mcp_server.py
```

### For Developers Working on Gem-Flux

```bash
# Clone and enter directory
git clone https://github.com/yourorg/gem-flux-mcp.git
cd gem-flux-mcp

# Sync dev dependencies
uv sync --all-extras --dev

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Run the server in dev mode
uv run python -m fastmcp run src/mcp_server.py --dev
```

---

## Creating and Managing Virtual Environments

### Modern Approach (Recommended)

UV automatically manages virtual environments when you use `uv sync` or `uv run`:

```bash
# Initialize new project
mkdir my-project && cd my-project
uv init

# This creates:
# - pyproject.toml (project configuration)
# - .python-version (Python version spec)
# - .venv/ (virtual environment, created on first sync)
```

### Python Version Management

```bash
# Install a specific Python version
uv python install 3.11

# List available Python versions
uv python list

# List installed Python versions
uv python list --only-installed

# Set project Python version
echo "3.11" > .python-version

# UV will automatically use this version
uv sync
```

### Running Commands in Virtual Environment

```bash
# UV automatically activates the venv
uv run python script.py
uv run pytest
uv run python -m fastmcp run src/mcp_server.py

# No need for "source .venv/bin/activate"!
```

### Manual Activation (if needed)

```bash
# If you need to activate manually
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

---

## Managing Dependencies

### Adding Dependencies

```bash
# Add production dependency
uv add cobrapy

# Add with version constraint
uv add "cobrapy>=0.27.0"

# Add dev dependency
uv add --dev pytest

# Add optional dependency group
uv add --optional viz matplotlib seaborn

# Add from Git repository
uv add git+https://github.com/Fxe/ModelSEEDpy.git@dev
```

### Removing Dependencies

```bash
# Remove dependency
uv remove numpy

# Remove dev dependency
uv remove --dev pytest
```

### Upgrading Dependencies

```bash
# Upgrade all dependencies
uv lock --upgrade

# Upgrade specific package
uv lock --upgrade-package cobrapy

# Sync after upgrade
uv sync
```

### Installing from Lock File

```bash
# Install exact versions from uv.lock
uv sync --frozen

# Install with optional dependencies
uv sync --all-extras

# Install dev dependencies
uv sync --dev

# Install everything
uv sync --all-extras --dev
```

---

## Project Configuration: pyproject.toml

### Complete Example for Gem-Flux MCP

```toml
[project]
name = "gem-flux-mcp"
version = "0.1.0"
description = "MCP server for metabolic modeling with ModelSEEDpy and COBRApy"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
keywords = ["metabolic-modeling", "flux-balance-analysis", "mcp", "modelseed"]

# Production dependencies
dependencies = [
    "fastmcp>=0.2.0",
    "cobrapy>=0.27.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
]

# Optional dependency groups
[project.optional-dependencies]
viz = [
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
]

# CLI entry points (if needed)
[project.scripts]
gem-flux = "gem_flux_mcp.cli:main"

# Build system
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# UV-specific configuration
[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

# ModelSEEDpy from dev branch
[tool.uv.sources]
modelseedpy = { git = "https://github.com/Fxe/ModelSEEDpy.git", branch = "dev" }

# Package indexes (if using private packages)
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
explicit = true

# Workspace configuration (for monorepos)
[tool.uv.workspace]
members = ["packages/*"]

# Ruff linter configuration
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = ["E501"]

# Pytest configuration
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term"

# MyPy configuration
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Dependency Sources

UV supports multiple dependency sources:

```toml
[tool.uv.sources]
# Git repository (specific branch)
modelseedpy = { git = "https://github.com/Fxe/ModelSEEDpy.git", branch = "dev" }

# Git repository (specific tag)
some-package = { git = "https://github.com/user/repo.git", tag = "v1.0.0" }

# Git repository (specific commit)
another-package = { git = "https://github.com/user/repo.git", rev = "abc123" }

# Local path (for development)
local-package = { path = "../local-package", editable = true }

# Direct URL
direct-package = { url = "https://example.com/package.tar.gz" }
```

---

## Using UV in GitHub Workflows

### Complete CI/CD Workflow

```yaml
name: CI/CD

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up UV
        uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --all-extras --dev

      - name: Run linter
        run: uv run ruff check .

      - name: Run type checker
        run: uv run mypy src/

      - name: Run tests
        run: uv run pytest

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Set up UV
        uses: astral-sh/setup-uv@v6

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        if: startsWith(github.ref, 'refs/tags/')
        run: uv publish
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
```

### Caching Strategies

```yaml
# Option 1: Built-in caching (recommended)
- uses: astral-sh/setup-uv@v6
  with:
    enable-cache: true
    cache-dependency-glob: "uv.lock"

# Option 2: Manual caching (for more control)
- uses: actions/cache@v3
  with:
    path: |
      ~/.cache/uv
      .venv
    key: ${{ runner.os }}-uv-${{ hashFiles('uv.lock') }}
    restore-keys: |
      ${{ runner.os }}-uv-
```

---

## Best Practices for Distributable Projects

### 1. Project Structure

```
gem-flux-mcp/
├── src/
│   └── gem_flux_mcp/
│       ├── __init__.py
│       ├── mcp_server.py
│       └── tools/
├── tests/
│   ├── __init__.py
│   ├── test_tools.py
│   └── test_integration.py
├── specs-source/          # Source materials
├── specs/                 # Generated specs
├── docs/
├── pyproject.toml         # Project config
├── uv.lock                # Lock file (COMMIT THIS)
├── .python-version        # Python version (3.11)
├── .gitignore
├── README.md
├── LICENSE
└── .github/
    └── workflows/
        └── ci.yml
```

### 2. Version Control

**Commit these files**:
```gitignore
# Essential files
pyproject.toml
uv.lock              # IMPORTANT: Commit for applications
.python-version
README.md
LICENSE

# Source code
src/
tests/
```

**Don't commit these** (add to `.gitignore`):
```gitignore
# Virtual environment
.venv/
venv/

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so

# UV cache
.uv_cache/

# Testing
.coverage
htmlcov/
.pytest_cache/

# IDEs
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

### 3. README Installation Instructions

```markdown
## Installation

### Prerequisites
- Python 3.11 or later
- [UV package manager](https://docs.astral.sh/uv/)

### Install UV

**macOS/Linux**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows**:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install Gem-Flux MCP

```bash
# Clone repository
git clone https://github.com/yourorg/gem-flux-mcp.git
cd gem-flux-mcp

# Install dependencies
uv sync

# Run the server
uv run python -m fastmcp run src/mcp_server.py
```

### Development Setup

```bash
# Install with dev dependencies
uv sync --all-extras --dev

# Run tests
uv run pytest

# Run linter
uv run ruff check .
```
```

### 4. MCP Server Deployment

For MCP servers, use absolute paths or `--directory` flag:

```bash
# Option 1: Change to directory first
cd /path/to/gem-flux-mcp
uv run python -m fastmcp run src/mcp_server.py

# Option 2: Use --directory flag (if supported)
uv run --directory /path/to/gem-flux-mcp python -m fastmcp run src/mcp_server.py

# Option 3: Activate environment manually
source /path/to/gem-flux-mcp/.venv/bin/activate
python -m fastmcp run src/mcp_server.py
```

### 5. Lock File Strategy

**For applications** (like Gem-Flux MCP):
- ✅ **Commit `uv.lock`** to ensure reproducible deployments
- Use `uv sync --frozen` in production for exact versions
- Update lock file periodically: `uv lock --upgrade`

**For libraries** (if publishing to PyPI):
- ❌ **Don't commit `uv.lock`** (add to `.gitignore`)
- Use broad version constraints in `dependencies`
- Let users' lock files resolve actual versions

### 6. Version Management

Use semantic versioning in `pyproject.toml`:

```toml
[project]
version = "0.1.0"  # Start here for MVP
# 0.1.0 → 0.2.0 (minor features)
# 0.2.0 → 1.0.0 (stable release)
# 1.0.0 → 1.0.1 (bug fixes)
# 1.0.0 → 1.1.0 (new features, backwards compatible)
# 1.0.0 → 2.0.0 (breaking changes)
```

---

## Quick Command Reference

### Installation & Setup

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh    # Install UV
uv self update                                      # Update UV
uv init                                            # Initialize new project
uv python install 3.11                             # Install Python version
```

### Dependency Management

```bash
uv add package                                      # Add dependency
uv add --dev pytest                                 # Add dev dependency
uv add --optional viz matplotlib                    # Add optional dependency
uv add "package>=1.0.0"                             # Add with version
uv remove package                                   # Remove dependency
uv lock --upgrade                                   # Upgrade all dependencies
uv lock --upgrade-package cobrapy                   # Upgrade specific package
```

### Environment Sync

```bash
uv sync                                             # Install dependencies
uv sync --frozen                                    # Use exact lock file versions
uv sync --all-extras                                # Install optional dependencies
uv sync --dev                                       # Install dev dependencies
uv sync --all-extras --dev                          # Install everything
```

### Running Commands

```bash
uv run python script.py                             # Run Python script
uv run pytest                                       # Run tests
uv run python -m module                             # Run module
```

### Building & Publishing

```bash
uv build                                            # Build package
uv publish                                          # Publish to PyPI
uv publish --token $PYPI_TOKEN                      # Publish with token
```

---

## Common Workflows

### Starting a New Project

```bash
mkdir my-project && cd my-project
uv init
uv add cobrapy pandas
uv add --dev pytest ruff
echo "3.11" > .python-version
uv sync
```

### Cloning an Existing Project

```bash
git clone https://github.com/user/project.git
cd project
uv sync --frozen  # Use exact versions from lock file
uv run pytest     # Run tests
```

### Updating Dependencies

```bash
# Update all dependencies
uv lock --upgrade
uv sync

# Update specific package
uv lock --upgrade-package cobrapy
uv sync

# Check for outdated packages
uv pip list --outdated
```

### Running Tests in CI

```bash
uv sync --frozen --all-extras --dev
uv run pytest --cov=src --cov-report=xml
```

---

## Summary

UV provides a modern, fast, and unified Python development experience for Gem-Flux MCP:

✅ **Fast**: 10-100x faster than pip
✅ **Unified**: Replaces pip, virtualenv, pyenv, pipx
✅ **Reproducible**: Lock files ensure consistent environments
✅ **GitHub-friendly**: First-class Actions support
✅ **Simple**: One tool for all Python needs

**Key Commands for Gem-Flux**:
- `uv sync` - Install dependencies
- `uv run` - Run commands in environment
- `uv add` - Add dependencies
- `uv lock --upgrade` - Update dependencies

**For Users**: Just run `uv sync` after cloning
**For Developers**: Run `uv sync --all-extras --dev`
**For CI/CD**: Use `astral-sh/setup-uv@v6` action

This guide covers everything needed to use UV effectively for the Gem-Flux MCP server project.
