# Installation and Deployment - Gem-Flux MCP Server

**Type**: Installation Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: **001-system-overview.md** (for understanding technology stack)
- Read: **007-database-integration.md** (for understanding database file requirements)

## Purpose

This specification defines how users install, configure, and deploy the Gem-Flux MCP server. It covers installation procedures, dependency management, configuration options, and deployment patterns for local and remote server setups.

## Installation Philosophy

**Target Users**:
1. **End Users**: Metabolic engineers and researchers who want to use the MCP server
2. **Developers**: Contributors who want to develop and test the server
3. **Server Administrators**: IT staff deploying on remote servers for team access

**Design Principles**:
- Simple installation with minimal steps
- Reproducible environments via lock files
- Clear separation between user and developer workflows
- No cloud deployment for MVP (local/remote servers only)
- Single package manager (UV) for all workflows

## System Requirements

### Minimum Requirements

**Operating Systems**:
- macOS 10.15+ (Catalina or later)
- Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+, or equivalent)
- Windows 10+ (with WSL2 recommended, native Windows supported)

**Hardware**:
- CPU: 2+ cores (4+ cores recommended for large models)
- RAM: 4GB minimum (8GB+ recommended)
- Disk: 2GB free space (includes dependencies and database files)
- Network: Internet connection for initial installation

**Software**:
- Python 3.11 or later (3.12 recommended)
- UV package manager (installed during setup)
- Git (for cloning repository)

### Recommended Environment

**For Production Use**:
- CPU: 4+ cores
- RAM: 16GB+
- SSD storage
- Stable network connection

**For Development**:
- All production requirements, plus:
- IDE with Python support (VS Code, PyCharm)
- GitHub account (for contributions)

## Installation Workflows

### Workflow 1: End User Installation (Recommended)

**Goal**: Install and run the MCP server for personal use.

**Steps**:

1. **Install UV Package Manager**

   **macOS/Linux**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   **Windows (PowerShell)**:
   ```powershell
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   **Verify Installation**:
   ```bash
   uv --version
   # Expected output: uv 0.5.11 (or later)
   ```

2. **Clone Repository**

   ```bash
   git clone https://github.com/yourorg/gem-flux-mcp.git
   cd gem-flux-mcp
   ```

3. **Install Dependencies**

   ```bash
   # This creates .venv/ and installs all dependencies
   uv sync
   ```

   **What Happens**:
   - UV reads `pyproject.toml` and `uv.lock`
   - Creates virtual environment in `.venv/`
   - Installs exact versions from lock file
   - Downloads ModelSEED database files (if not included)
   - Takes 30-60 seconds on typical hardware

4. **Verify Installation**

   ```bash
   # Run health check (future enhancement)
   uv run python -m gem_flux_mcp.health_check
   ```

   **Expected Output**:
   ```
   ✓ Python version: 3.11.6
   ✓ ModelSEEDpy: 0.x.x (dev)
   ✓ COBRApy: 0.27.0
   ✓ ModelSEED database: 77,768 entries loaded
   ✓ Templates: GramNegative, GramPositive, Core found
   ✓ Ready to start server
   ```

5. **Start MCP Server**

   ```bash
   uv run python -m gem_flux_mcp.server
   ```

   **Expected Output**:
   ```
   Gem-Flux MCP Server v0.1.0
   Loading ModelSEED database... Done (77,768 entries)
   Loading templates... Done (3 templates)
   Starting MCP server on stdio transport...
   Server ready. Waiting for MCP client connection.
   ```

**Installation Time**: 3-5 minutes (including UV download)

### Workflow 2: Developer Installation

**Goal**: Set up development environment with testing and linting tools.

**Steps**:

1. **Install UV** (same as Workflow 1, step 1)

2. **Clone Repository and Create Fork**

   ```bash
   # Fork repository on GitHub first
   git clone https://github.com/yourusername/gem-flux-mcp.git
   cd gem-flux-mcp

   # Add upstream remote
   git remote add upstream https://github.com/yourorg/gem-flux-mcp.git
   ```

3. **Install All Dependencies (Including Dev Tools)**

   ```bash
   # Install with all optional dependencies and dev tools
   uv sync --all-extras --dev
   ```

   **Additional Tools Installed**:
   - `pytest` - Testing framework
   - `pytest-cov` - Coverage reporting
   - `ruff` - Linter and formatter
   - `mypy` - Type checker
   - `pre-commit` - Git hooks (optional)

4. **Verify Development Setup**

   ```bash
   # Run tests
   uv run pytest

   # Check code quality
   uv run ruff check .

   # Check types
   uv run mypy src/
   ```

5. **Configure Pre-commit Hooks** (Optional)

   ```bash
   uv run pre-commit install
   ```

   **Behavior**:
   - Runs linter before each commit
   - Runs type checker before each commit
   - Prevents commits with failing tests

**Installation Time**: 5-7 minutes (includes dev dependencies)

### Workflow 3: Remote Server Deployment

**Goal**: Deploy MCP server on a remote machine for team access.

**Steps**:

1. **Provision Server**

   - Linux server with SSH access
   - Meets system requirements (see above)
   - Firewall configured (if needed)

2. **Install UV on Server**

   ```bash
   ssh user@server
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.bashrc  # Reload shell
   ```

3. **Clone and Install**

   ```bash
   git clone https://github.com/yourorg/gem-flux-mcp.git
   cd gem-flux-mcp
   uv sync --frozen  # Use exact versions from lock file
   ```

4. **Create Systemd Service** (Linux)

   Create `/etc/systemd/system/gem-flux-mcp.service`:

   ```ini
   [Unit]
   Description=Gem-Flux MCP Server
   After=network.target

   [Service]
   Type=simple
   User=gemflux
   WorkingDirectory=/opt/gem-flux-mcp
   ExecStart=/opt/gem-flux-mcp/.venv/bin/python -m gem_flux_mcp.server
   Restart=on-failure
   RestartSec=5s

   [Install]
   WantedBy=multi-user.target
   ```

   **Enable and Start**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable gem-flux-mcp
   sudo systemctl start gem-flux-mcp
   sudo systemctl status gem-flux-mcp
   ```

5. **Configure Logging** (Optional)

   Logs written to:
   - `journalctl -u gem-flux-mcp -f` (systemd)
   - `/var/log/gem-flux-mcp/server.log` (file-based)

6. **Set Up Monitoring** (Optional)

   Health check endpoint (future):
   ```bash
   curl http://localhost:8080/health
   # Expected: {"status": "healthy", "version": "0.1.0"}
   ```

**Deployment Time**: 10-15 minutes (excluding server provisioning)

## Project Structure

The installed project has the following structure:

```
gem-flux-mcp/
├── .venv/                          # Virtual environment (created by uv sync)
│   ├── bin/                        # Python executables
│   ├── lib/                        # Installed packages
│   └── pyvenv.cfg                  # Environment configuration
├── src/
│   └── gem_flux_mcp/               # Main package
│       ├── __init__.py
│       ├── server.py               # MCP server entry point
│       ├── tools/                  # MCP tool implementations
│       │   ├── build_media.py
│       │   ├── build_model.py
│       │   ├── gapfill_model.py
│       │   ├── run_fba.py
│       │   └── database_tools.py
│       ├── database/               # ModelSEED database integration
│       │   ├── loader.py           # Load TSV files
│       │   └── query.py            # Query interface
│       ├── storage/                # Model storage (session-based)
│       │   └── session_store.py
│       └── utils/                  # Utility functions
│           ├── validation.py
│           └── error_handling.py
├── data/                           # ModelSEED database files
│   ├── compounds.tsv               # 33,993 compounds
│   ├── reactions.tsv               # 43,775 reactions
│   └── templates/                  # ModelSEED templates
│       ├── GramNegative.json
│       ├── GramPositive.json
│       └── Core.json
├── tests/                          # Test suite (dev only)
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/                           # Documentation
├── specs/                          # Specifications (this)
├── pyproject.toml                  # Project configuration
├── uv.lock                         # Dependency lock file
├── .python-version                 # Python version (3.11)
├── .gitignore
├── README.md
└── LICENSE
```

## Configuration File: pyproject.toml

The `pyproject.toml` file defines all project metadata, dependencies, and tool configurations.

### Structure

```toml
[project]
name = "gem-flux-mcp"
version = "0.1.0"
description = "MCP server for metabolic modeling with ModelSEEDpy and COBRApy"
authors = [
    {name = "Gem-Flux Contributors", email = "contact@gem-flux.org"}
]
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
keywords = ["metabolic-modeling", "flux-balance-analysis", "mcp", "modelseed", "cobrapy"]

# Production dependencies
dependencies = [
    "fastmcp>=0.2.0",
    "cobrapy>=0.27.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
]

# Optional dependency groups (future)
[project.optional-dependencies]
viz = [
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
]

# Build system
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# UV-specific configuration
[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
    "pre-commit>=3.5.0",
]

# ModelSEEDpy from dev branch
[tool.uv.sources]
modelseedpy = { git = "https://github.com/Fxe/ModelSEEDpy.git", branch = "dev" }

# Ruff linter configuration
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]  # Line too long (handled by formatter)

# Pytest configuration
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term --cov-fail-under=80"
asyncio_mode = "auto"

# MyPy configuration
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = false

[[tool.mypy.overrides]]
module = "modelseedpy.*"
ignore_missing_imports = true
```

### Key Configuration Sections

**Dependencies**:
- `dependencies`: Production requirements, installed with `uv sync`
- `tool.uv.dev-dependencies`: Development tools, installed with `uv sync --dev`
- `tool.uv.sources`: Special sources (ModelSEEDpy dev branch from Git)

**Tool Configurations**:
- `tool.ruff`: Linter settings (line length, rules)
- `tool.pytest`: Test discovery and coverage requirements
- `tool.mypy`: Type checking strictness

## Python Version Management

### Specifying Python Version

The `.python-version` file specifies the required Python version:

```
3.11
```

**Behavior**:
- UV automatically installs Python 3.11 if not present
- UV uses this version when creating virtual environment
- Ensures consistency across all installations

### Installing Python with UV

```bash
# Install Python 3.11
uv python install 3.11

# List available versions
uv python list

# List installed versions
uv python list --only-installed
```

## Dependency Management

### Lock File Strategy

**For Gem-Flux MCP (Application)**:
- ✅ **Commit `uv.lock`** to repository
- Ensures reproducible installations
- All users get exact same versions
- Critical for metabolic modeling (library versions matter)

**Behavior**:
- `uv sync` installs from lock file
- `uv sync --frozen` strictly enforces lock file (CI/CD)
- `uv lock --upgrade` updates lock file

### Managing Dependencies

**Adding New Dependencies**:

```bash
# Add production dependency
uv add numpy

# Add with version constraint
uv add "cobrapy>=0.27.0"

# Add dev dependency
uv add --dev pytest-benchmark

# Add from Git repository
uv add git+https://github.com/user/repo.git@branch
```

**Removing Dependencies**:

```bash
# Remove dependency
uv remove numpy

# Remove dev dependency
uv remove --dev pytest-benchmark
```

**Upgrading Dependencies**:

```bash
# Upgrade all dependencies
uv lock --upgrade
uv sync

# Upgrade specific package
uv lock --upgrade-package cobrapy
uv sync

# Check for outdated packages
uv pip list --outdated
```

### Handling ModelSEEDpy Dev Branch

ModelSEEDpy requires the **dev branch** from GitHub.

**Configuration in pyproject.toml**:

```toml
[tool.uv.sources]
modelseedpy = { git = "https://github.com/Fxe/ModelSEEDpy.git", branch = "dev" }
```

**Behavior**:
- UV clones dev branch during `uv sync`
- Lock file pins exact commit hash
- Updates with `uv lock --upgrade-package modelseedpy`

**Alternative: Local Development**:

```bash
# Clone ModelSEEDpy locally
git clone https://github.com/Fxe/ModelSEEDpy.git
cd ModelSEEDpy
git checkout dev

# Use local editable install
cd ../gem-flux-mcp
uv add --editable ../ModelSEEDpy
```

## Database File Packaging

### ModelSEED Database Files

**Required Files** (included in repository):
- `data/compounds.tsv` (33,993 compounds, ~3MB)
- `data/reactions.tsv` (43,775 reactions, ~8MB)

**Loading Behavior**:
- Files loaded at server startup
- Parsed into Pandas DataFrames
- Indexed by ID for O(1) lookup
- ~2-3 seconds load time

**Updating Database Files**:

```bash
# Download latest from ModelSEED
curl -o data/compounds.tsv https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/compounds.tsv

curl -o data/reactions.tsv https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/reactions.tsv
```

**Validation**:
```bash
# Check file format
head -n 1 data/compounds.tsv
# Expected: id	abbreviation	name	formula	...

wc -l data/compounds.tsv
# Expected: ~34,000 lines
```

### Template Files

**Required Templates** (from ModelSEEDpy):
- `GramNegative` - Gram-negative bacteria (E. coli, etc.)
- `GramPositive` - Gram-positive bacteria (B. subtilis, etc.)
- `Core` - Universal core metabolism

**Loading Behavior**:
- Templates loaded from ModelSEEDpy package
- Cached in memory at server startup
- ~1-2 seconds load time per template

## Server Startup

### Starting the Server

**Standard Method**:
```bash
cd /path/to/gem-flux-mcp
uv run python -m gem_flux_mcp.server
```

**Alternative: Activate Virtual Environment**:
```bash
cd /path/to/gem-flux-mcp
source .venv/bin/activate  # macOS/Linux
python -m gem_flux_mcp.server
```

**Server Output**:
```
Gem-Flux MCP Server v0.1.0
Python 3.11.6 | UV 0.5.11
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Loading ModelSEED database...
  ✓ Loaded 33,993 compounds
  ✓ Loaded 43,775 reactions
  ✓ Database ready (2.3s)

Loading templates...
  ✓ GramNegative (1,234 reactions)
  ✓ GramPositive (987 reactions)
  ✓ Core (456 reactions)
  ✓ Templates ready (1.8s)

Starting MCP server...
  Transport: stdio
  Tools: 8 registered
  ✓ Server ready (4.2s)

Waiting for MCP client connection...
```

### Server Configuration

**Environment Variables** (optional):

```bash
# Set log level
export GEM_FLUX_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR

# Set database path
export GEM_FLUX_DATA_DIR=/custom/path/to/data

# Set template cache directory
export GEM_FLUX_TEMPLATE_CACHE=/custom/path/to/templates
```

**Configuration File** (future):
`~/.gem-flux-mcp/config.toml`:
```toml
[server]
log_level = "INFO"
data_dir = "/path/to/data"

[database]
compounds_file = "compounds.tsv"
reactions_file = "reactions.tsv"

[templates]
cache_dir = "/path/to/templates"
```

### Health Checks

**Manual Health Check**:
```bash
uv run python -c "from gem_flux_mcp.health_check import check; check()"
```

**Expected Output**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "python_version": "3.11.6",
  "dependencies": {
    "modelseedpy": "0.x.x",
    "cobrapy": "0.27.0",
    "fastmcp": "0.2.0"
  },
  "database": {
    "compounds": 33993,
    "reactions": 43775
  },
  "templates": ["GramNegative", "GramPositive", "Core"]
}
```

## Troubleshooting

### Common Installation Issues

**Issue 1: UV not found after installation**

**Symptom**:
```bash
uv --version
# bash: uv: command not found
```

**Solution**:
```bash
# Reload shell configuration
source ~/.bashrc  # Linux
source ~/.zshrc   # macOS

# Or restart terminal
```

**Issue 2: Python version not found**

**Symptom**:
```bash
uv sync
# Error: Python 3.11 not found
```

**Solution**:
```bash
# Install Python 3.11 with UV
uv python install 3.11

# Or use system Python (if 3.11+)
uv sync --python $(which python3.11)
```

**Issue 3: ModelSEEDpy dev branch clone fails**

**Symptom**:
```bash
uv sync
# Error: Failed to clone https://github.com/Fxe/ModelSEEDpy.git
```

**Solution**:
```bash
# Check network connection
curl -I https://github.com

# Retry with verbose output
uv sync --verbose

# Or clone manually and use local path
git clone https://github.com/Fxe/ModelSEEDpy.git
uv add --editable ./ModelSEEDpy
```

**Issue 4: Database files missing**

**Symptom**:
```bash
uv run python -m gem_flux_mcp.server
# Error: FileNotFoundError: data/compounds.tsv
```

**Solution**:
```bash
# Download database files
mkdir -p data
curl -o data/compounds.tsv https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/compounds.tsv
curl -o data/reactions.tsv https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/reactions.tsv
```

**Issue 5: Permission denied on Linux**

**Symptom**:
```bash
uv sync
# Error: Permission denied: /usr/local/bin
```

**Solution**:
```bash
# Install UV for current user only
curl -LsSf https://astral.sh/uv/install.sh | sh
# UV installs to ~/.local/bin instead

# Or use sudo for system-wide install
curl -LsSf https://astral.sh/uv/install.sh | sudo sh
```

### Verification Commands

**Check Installation**:
```bash
# UV version
uv --version

# Python version
uv run python --version

# Package versions
uv run python -c "import modelseedpy; print(modelseedpy.__version__)"
uv run python -c "import cobra; print(cobra.__version__)"

# Database files
ls -lh data/*.tsv

# Template files
uv run python -c "from modelseedpy.core.mstemplate import MSTemplateBuilder; print(MSTemplateBuilder.list())"
```

**Run Quick Test**:
```bash
# Import all tools (smoke test)
uv run python -c "
from gem_flux_mcp.tools import build_media, build_model, gapfill_model, run_fba
from gem_flux_mcp.database import get_compound_name, search_compounds
print('✓ All tools imported successfully')
"
```

## Updating the Server

### Update Procedure

**Standard Update**:
```bash
cd gem-flux-mcp
git pull origin main
uv sync --frozen  # Install from updated lock file
```

**Update with Dependency Upgrades**:
```bash
cd gem-flux-mcp
git pull origin main
uv lock --upgrade  # Upgrade dependencies
uv sync
```

**Rollback to Previous Version**:
```bash
cd gem-flux-mcp
git checkout v0.1.0  # Or specific commit
uv sync --frozen
```

### Release Process

**For Maintainers**:

1. **Update version in pyproject.toml**:
   ```toml
   version = "0.2.0"
   ```

2. **Update lock file**:
   ```bash
   uv lock
   ```

3. **Run full test suite**:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run mypy src/
   ```

4. **Commit and tag**:
   ```bash
   git add pyproject.toml uv.lock
   git commit -m "chore: bump version to 0.2.0"
   git tag v0.2.0
   git push origin main --tags
   ```

5. **Create GitHub release**:
   - Release notes
   - Changelog
   - Installation instructions

## Integration with MCP Clients

### Claude Desktop Integration

**Configuration File**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "gem-flux": {
      "command": "/path/to/gem-flux-mcp/.venv/bin/python",
      "args": ["-m", "gem_flux_mcp.server"],
      "cwd": "/path/to/gem-flux-mcp",
      "env": {
        "GEM_FLUX_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Restart Claude Desktop** to apply configuration.

### Generic MCP Client

**Start Server**:
```bash
cd /path/to/gem-flux-mcp
uv run python -m gem_flux_mcp.server
```

**Client Connection**:
- Transport: stdio (stdin/stdout)
- Protocol: MCP JSON-RPC
- Tools: 8 available (see 001-system-overview.md)

## Uninstallation

### Complete Removal

**Remove Project**:
```bash
cd /path/to/gem-flux-mcp
cd ..
rm -rf gem-flux-mcp
```

**Uninstall UV** (optional):
```bash
# macOS/Linux
rm -rf ~/.local/bin/uv
rm -rf ~/.local/share/uv

# Windows
# Remove UV from %USERPROFILE%\.local\bin
```

**Clean Up Configuration** (optional):
```bash
# Remove Claude Desktop config
# Edit ~/Library/Application Support/Claude/claude_desktop_config.json
# and remove "gem-flux" entry
```

## Summary

### Installation Time Estimates

| Workflow | Time | Network | Disk Space |
|----------|------|---------|-----------|
| End User Install | 3-5 min | Required | 2GB |
| Developer Install | 5-7 min | Required | 2.5GB |
| Remote Server Deploy | 10-15 min | Required | 2GB |
| Database Update | 1-2 min | Required | 11MB |

### Key Installation Commands

**End User**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/yourorg/gem-flux-mcp.git
cd gem-flux-mcp
uv sync
uv run python -m gem_flux_mcp.server
```

**Developer**:
```bash
# Same as End User, but:
uv sync --all-extras --dev
uv run pytest
```

**Server Administrator**:
```bash
# Same as End User, then:
sudo systemctl enable gem-flux-mcp
sudo systemctl start gem-flux-mcp
```

### Success Criteria

Installation is successful when:
- ✅ `uv --version` returns version number
- ✅ `uv sync` completes without errors
- ✅ Database files loaded (77,768 total entries)
- ✅ Templates loaded (3 templates)
- ✅ Server starts and shows "Server ready"
- ✅ Health check returns "healthy" status

### Next Steps After Installation

1. **Connect MCP Client**: Configure Claude Desktop or other MCP client
2. **Test Basic Workflow**: Try building a simple model (see 012-complete-workflow.md)
3. **Read Documentation**: Review tool specifications in specs/
4. **Join Community**: GitHub discussions, issues, contributions

---

**Related Specifications**:
- **001-system-overview.md** - System architecture and technology stack
- **007-database-integration.md** - Database file requirements
- **012-complete-workflow.md** - Example workflows to test installation
- **013-error-handling.md** - Common errors and troubleshooting
- **015-mcp-server-setup.md** - MCP server configuration details
