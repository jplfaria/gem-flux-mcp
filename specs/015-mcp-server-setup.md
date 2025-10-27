# MCP Server Setup - Gem-Flux MCP Server

**Type**: Server Configuration Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: **001-system-overview.md** (for understanding overall architecture)
- Read: **014-installation.md** (for understanding installation procedures)
- Read: **007-database-integration.md** (for understanding database loading requirements)
- Understand: FastMCP framework patterns
- Understand: Model Context Protocol (MCP) specification

## Purpose

This specification defines how the Gem-Flux MCP server initializes, registers tools, loads resources, handles lifecycle events, and manages errors. It describes the server's behavior from startup to shutdown, focusing on configuration, resource loading, and error handling patterns.

## Server Initialization

### Startup Sequence

The MCP server follows this initialization sequence:

**Phase 1: Server Creation**
1. Import FastMCP framework
2. Create MCP server instance with metadata
3. Set server name, version, and description

**Phase 2: Resource Loading**
1. Load ModelSEED database files (compounds.tsv, reactions.tsv)
2. Load ModelSEED templates (GramNegative, GramPositive, Core, etc.)
3. Index database files for O(1) lookup
4. Validate resource integrity

**Phase 3: Tool Registration**
1. Register 4 core modeling tools (build_media, build_model, gapfill_model, run_fba)
2. Register 4 database lookup tools (get_compound_name, get_reaction_name, search_compounds, search_reactions)
3. Register model I/O tools (future: import_model_json, export_model_json)
4. Configure tool metadata and input schemas

**Phase 4: Session Storage Initialization**
1. Initialize in-memory model storage (session-based for MVP)
2. Initialize in-memory media storage
3. Set up ID generation for models and media

**Phase 5: Server Ready**
1. Bind to network interface (if remote server)
2. Log server ready message
3. Begin accepting MCP requests

### Server Metadata

**Required Metadata**:
```python
{
    "name": "gem-flux-mcp",
    "version": "0.1.0",
    "description": "MCP server for metabolic modeling with ModelSEEDpy and COBRApy",
    "protocol_version": "2025-06-18",  # MCP protocol version (latest stable)
    "capabilities": {
        "tools": True,
        "resources": False,  # Not in MVP
        "prompts": False,    # Not in MVP
        "logging": True
    }
}
```

**Protocol Version History**:
- `2025-06-18`: Latest stable MCP protocol (current)
- `2024-11-05`: Previous MCP protocol version
- Using latest protocol ensures compatibility with modern MCP clients

**Behavior**:
- Server metadata is returned in response to MCP `initialize` request
- Protocol version indicates MCP specification compatibility
- Capabilities advertise which MCP features are supported
- Clients use protocol_version to negotiate compatible feature set

### Configuration Options

**Environment Variables** (optional):
```bash
# Server configuration
GEM_FLUX_HOST="localhost"            # Host to bind (default: localhost)
GEM_FLUX_PORT="8080"                 # Port to listen (default: 8080)

# Resource paths
GEM_FLUX_DATABASE_DIR="./database"   # ModelSEED database location
GEM_FLUX_TEMPLATE_DIR="./templates" # ModelSEED template location

# Performance tuning
GEM_FLUX_MAX_MODELS="100"           # Max models in session storage
GEM_FLUX_SOLVER_TIMEOUT="300"       # FBA solver timeout (seconds)

# Logging
GEM_FLUX_LOG_LEVEL="INFO"           # DEBUG, INFO, WARNING, ERROR
GEM_FLUX_LOG_FILE="./gem-flux.log"  # Log file path
```

**Configuration File** (future):
```yaml
# config.yaml
server:
  host: localhost
  port: 8080

resources:
  database_dir: ./database
  template_dir: ./templates

limits:
  max_models: 100
  solver_timeout: 300

logging:
  level: INFO
  file: ./gem-flux.log
```

**Behavior**:
- Environment variables take precedence over configuration file
- Defaults are used if neither environment variable nor config file specified
- Invalid configuration values log warning and use defaults
- Server fails to start if critical resources (database, templates) cannot be loaded

## Resource Loading

### ModelSEED Database Loading

**What is Loaded**:
1. **compounds.tsv** - 33,993 compounds with IDs, names, formulas, aliases
2. **reactions.tsv** - 43,775 reactions with IDs, names, equations, EC numbers

**Loading Behavior**:
1. Read TSV files using pandas `read_csv()` with tab delimiter
2. Index by ID column for O(1) lookup
3. Parse aliases column (pipe-delimited) into lists
4. Store in memory for fast access during server lifetime
5. Log loading statistics (number of compounds/reactions loaded)

**Error Handling**:
- Database files not found → Log error, exit server startup
- Invalid TSV format → Log error with line number, exit startup
- Missing required columns → Log error listing missing columns, exit startup
- Partial data corruption → Log warning, continue with valid rows

**Example Loading**:
```
[INFO] Loading ModelSEED database from ./database
[INFO] Loaded 33,993 compounds from compounds.tsv
[INFO] Loaded 43,775 reactions from reactions.tsv
[INFO] Database indexing complete (0.45s)
```

### ModelSEED Template Loading

**Templates to Load**:
1. **GramNegative** - Gram-negative bacteria (default)
2. **GramPositive** - Gram-positive bacteria
3. **Core** - Core metabolic template for gapfilling
4. **Archaea** - Archaeal template (optional)
5. **Eukaryote** - Eukaryotic template (optional)

**Loading Behavior**:
1. Read template JSON files from template directory
2. Parse using `MSTemplateBuilder.from_dict()`
3. Call `.build()` to create `MSTemplate` object
4. Store in dictionary keyed by template name
5. Validate template integrity (reactions, metabolites, compartments)
6. Log template statistics (number of reactions)

**Error Handling**:
- Template file not found → Log warning, continue without template
- Invalid JSON format → Log warning, skip template
- Template build failure → Log warning with details, skip template
- At least one template required → If zero templates loaded, exit startup

**Example Loading**:
```
[INFO] Loading ModelSEED templates from ./templates
[INFO] Loaded template 'GramNegative' (2,138 reactions)
[INFO] Loaded template 'GramPositive' (1,986 reactions)
[INFO] Loaded template 'Core' (452 reactions)
[WARNING] Template 'Archaea' not found, skipping
[INFO] Template loading complete (3 templates loaded)
```

### ATP Gapfilling Media Loading

**What is Loaded**:
- Default ATP gapfilling media (54 media compositions)
- Used by MSATPCorrection for ATP metabolism validation

**Loading Behavior**:
1. Call `load_default_medias()` from ModelSEEDpy
2. Returns list of tuples: `[(media, min_objective), ...]`
3. Store in memory for gapfilling operations
4. Log number of media loaded

**Error Handling**:
- Loading fails → Log warning, continue without ATP correction media
- ATP correction will be skipped if media unavailable

**Example Loading**:
```
[INFO] Loading default ATP gapfilling media
[INFO] Loaded 54 ATP test media conditions
```

## Tool Registration

### Tool Registration Pattern

Each MCP tool is registered with:
1. **Tool name** - Unique identifier (e.g., "build_media")
2. **Tool description** - Human-readable explanation for AI assistants
3. **Input schema** - JSON Schema defining parameters
4. **Handler function** - Async function implementing tool behavior

**Registration Behavior**:
```python
@mcp.tool()
async def build_media(
    compounds: list[str],
    default_uptake: float = 100.0,
    custom_bounds: dict[str, tuple[float, float]] | None = None
) -> dict:
    """Create a growth medium from ModelSEED compound IDs.

    This tool creates an MSMedia object that can be used with
    gapfill_model and run_fba. Compounds are specified using
    ModelSEED IDs (e.g., 'cpd00027' for D-Glucose).

    Args:
        compounds: List of ModelSEED compound IDs to include in media
        default_uptake: Default uptake bound in mmol/gDW/h (default: 100.0)
        custom_bounds: Optional dict mapping compound IDs to (lower, upper) bounds

    Returns:
        dict: Media metadata including media_id, compound list, and validation
    """
```

**What Gets Registered**:
- Function name becomes tool name
- Docstring becomes tool description (shown to AI assistants)
- Type hints define input/output schemas
- FastMCP auto-generates JSON Schema from type hints

**Error During Registration**:
- Invalid tool definition → Log error, skip tool registration
- Duplicate tool name → Log error, exit startup (names must be unique)
- Invalid type hints → Log error, skip tool

### Tool List

**MVP Tools Registered**:
1. `build_media` - Create growth medium
2. `build_model` - Build metabolic model from proteins
3. `gapfill_model` - Gapfill model for growth
4. `run_fba` - Execute flux balance analysis
5. `get_compound_name` - Lookup compound name by ID
6. `get_reaction_name` - Lookup reaction name by ID
7. `search_compounds` - Search compounds by query
8. `search_reactions` - Search reactions by query

**Registration Logging**:
```
[INFO] Registering MCP tools
[INFO] Registered tool: build_media
[INFO] Registered tool: build_model
[INFO] Registered tool: gapfill_model
[INFO] Registered tool: run_fba
[INFO] Registered tool: get_compound_name
[INFO] Registered tool: get_reaction_name
[INFO] Registered tool: search_compounds
[INFO] Registered tool: search_reactions
[INFO] Tool registration complete (8 tools)
```

## Session Storage

### Model Storage Initialization

**Storage Type**: In-memory dictionary (session-based, MVP)

**Behavior**:
1. Create empty dictionary to store models: `models: dict[str, cobra.Model] = {}`
2. Create model ID counter for unique IDs: `model_counter: int = 0`
3. No persistence - models lost on server restart
4. Models accessible only within same MCP session

**Model ID Generation**:
- Pattern: `model_{timestamp}_{counter}`
- Example: `model_20251027_001`
- Ensures uniqueness across session
- Human-readable for debugging

**Limits**:
- Maximum models in memory: 100 (configurable via `GEM_FLUX_MAX_MODELS`)
- Oldest models evicted when limit reached (FIFO)
- Log warning when approaching limit (80% capacity)

### Media Storage Initialization

**Storage Type**: In-memory dictionary (session-based, MVP)

**Behavior**:
1. Create empty dictionary: `media: dict[str, MSMedia] = {}`
2. Create media ID counter: `media_counter: int = 0`
3. Media lost on server restart
4. Media accessible only within same session

**Media ID Generation**:
- Pattern: `media_{timestamp}_{counter}`
- Example: `media_20251027_001`

**Limits**:
- Maximum media in memory: 50 (configurable)
- Oldest media evicted when limit reached

### Storage Cleanup

**Behavior**:
- No automatic cleanup during server runtime (MVP)
- All storage cleared on server shutdown
- Future: TTL-based cleanup, LRU eviction

## Server Lifecycle

### Startup Lifecycle

**Sequence**:
1. Parse command-line arguments / environment variables
2. Load configuration file (if present)
3. Initialize logging
4. Load ModelSEED database
5. Load ModelSEED templates
6. Load ATP gapfilling media
7. Initialize session storage
8. Register MCP tools
9. Start MCP server (bind to host:port)
10. Log "Server ready" message

**Example Startup Logs**:
```
[INFO] Gem-Flux MCP Server v0.1.0 starting...
[INFO] Configuration loaded from environment variables
[INFO] Loading ModelSEED database from ./database
[INFO] Loaded 33,993 compounds, 43,775 reactions
[INFO] Loading ModelSEED templates from ./templates
[INFO] Loaded 3 templates (GramNegative, GramPositive, Core)
[INFO] Loading ATP gapfilling media
[INFO] Loaded 54 ATP test media conditions
[INFO] Initializing session storage
[INFO] Registering MCP tools
[INFO] Registered 8 tools
[INFO] Starting MCP server on localhost:8080
[INFO] Server ready - accepting MCP requests
```

### Shutdown Lifecycle

**Graceful Shutdown Behavior**:
1. Receive shutdown signal (SIGINT, SIGTERM)
2. Stop accepting new MCP requests
3. Wait for active requests to complete (timeout: 30s)
4. Clear session storage (models, media)
5. Close database connections (if applicable)
6. Log shutdown complete message
7. Exit with code 0

**Force Shutdown Behavior**:
1. Receive force signal (SIGKILL, double Ctrl+C)
2. Immediately terminate server
3. No cleanup performed
4. Exit with code 1

**Example Shutdown Logs**:
```
[INFO] Shutdown signal received (SIGINT)
[INFO] Stopping MCP server (waiting for active requests)
[INFO] 2 active requests remaining...
[INFO] All requests completed
[INFO] Clearing session storage (47 models, 12 media)
[INFO] Shutdown complete
```

### Health Checks

**Health Check Behavior** (future):
- Endpoint: `/health` (HTTP GET)
- Returns: `{"status": "healthy", "version": "0.1.0", "uptime": 3600}`
- Checks:
  - Server is running
  - Database loaded successfully
  - At least one template available
  - Session storage within limits
- Used by monitoring systems, load balancers

**Status Values**:
- `healthy` - All systems operational
- `degraded` - Some non-critical issues (warnings in logs)
- `unhealthy` - Critical issues (cannot serve requests)

## Error Handling at Server Level

### Server-Level Error Categories

**Startup Errors** (fatal, exit server):
1. Database files not found or corrupted
2. No templates loaded successfully
3. Port already in use
4. Invalid configuration

**Runtime Errors** (non-fatal, log and continue):
1. Tool execution failures (handled by tool, see spec 013)
2. Invalid MCP requests (return error response)
3. Session storage limits exceeded (evict oldest)

**Shutdown Errors**:
1. Requests timeout during shutdown (force terminate after 30s)

### Error Response Format

**MCP Error Response**:
```json
{
  "jsonrpc": "2.0",
  "id": "request_id",
  "error": {
    "code": -32000,
    "message": "Server error message",
    "data": {
      "error_type": "ResourceLoadError",
      "details": "Additional error context"
    }
  }
}
```

**Error Codes**:
- `-32700` - Parse error (invalid JSON)
- `-32600` - Invalid request (malformed MCP request)
- `-32601` - Method not found (unknown tool)
- `-32602` - Invalid params (tool parameter validation failed)
- `-32603` - Internal error (unexpected server error)
- `-32000` - Server error (domain-specific errors)

### Logging Behavior

**Log Levels**:
- **DEBUG**: Detailed diagnostic information (tool parameters, intermediate results)
- **INFO**: General server events (startup, tool calls, shutdown)
- **WARNING**: Recoverable issues (template loading failures, storage limits)
- **ERROR**: Errors requiring attention (tool failures, invalid requests)

**Log Format**:
```
[TIMESTAMP] [LEVEL] [MODULE] MESSAGE
[2025-10-27 10:15:23] [INFO] [mcp_server] Server ready - accepting MCP requests
[2025-10-27 10:15:45] [WARNING] [session_storage] Model storage at 85% capacity (85/100)
[2025-10-27 10:16:02] [ERROR] [build_model] Failed to load template: GramNegative
```

**Log Destinations**:
- **Console**: All levels ≥ INFO (default)
- **File**: All levels ≥ DEBUG (if `GEM_FLUX_LOG_FILE` set)
- **Rotating**: Log rotation at 10MB, keep 5 files (future)

## Server Communication Patterns

### MCP Protocol Flow

**Request-Response Pattern**:
1. Client sends JSON-RPC request with tool name and parameters
2. Server validates request format
3. Server looks up tool handler
4. Server validates tool parameters against schema
5. Server executes tool handler (async)
6. Server returns JSON-RPC response with result or error

**Example Request**:
```json
{
  "jsonrpc": "2.0",
  "id": "call_123",
  "method": "tools/call",
  "params": {
    "name": "build_media",
    "arguments": {
      "compounds": ["cpd00027", "cpd00007", "cpd00001"],
      "default_uptake": 100.0
    }
  }
}
```

**Example Response**:
```json
{
  "jsonrpc": "2.0",
  "id": "call_123",
  "result": {
    "success": true,
    "media_id": "media_20251027_001",
    "compounds": [
      {"id": "cpd00027", "name": "D-Glucose", "bounds": [-100, 100]},
      {"id": "cpd00007", "name": "O2", "bounds": [-100, 100]},
      {"id": "cpd00001", "name": "H2O", "bounds": [-100, 100]}
    ],
    "num_compounds": 3
  }
}
```

### Async Execution

**Behavior**:
- All tool handlers are async functions
- Long-running operations (gapfilling, FBA) run asynchronously
- Server can handle multiple concurrent requests
- No blocking of server event loop

**Concurrency Limits** (future):
- Maximum concurrent gapfilling operations: 5
- Maximum concurrent FBA operations: 10
- Requests queued if limits exceeded

## Integration with System Components

### ModelSEEDpy Integration

**When Integrated**:
- Startup: Load templates, ATP media
- Runtime: Call MSBuilder, MSGapfill, MSMedia APIs

**Integration Points**:
- `MSGenome.from_dict()` - Create genome from protein sequences
- `MSBuilder.build_base_model()` - Build draft model
- `MSATPCorrection` - ATP gapfilling
- `MSGapfill.run_gapfilling()` - Genome-scale gapfilling
- `MSMedia.from_dict()` - Create media from compound bounds

### COBRApy Integration

**When Integrated**:
- Runtime: FBA execution, model I/O (future)

**Integration Points**:
- `model.optimize()` - Execute FBA
- `model.medium` - Set media constraints
- `cobra.io.load_json_model()` - Import models (future)
- `cobra.io.save_json_model()` - Export models (future)

### Database Integration

**When Integrated**:
- Startup: Load compounds.tsv, reactions.tsv
- Runtime: Lookup queries for compound/reaction names

**Integration Points**:
- Pandas DataFrame queries for ID lookups
- String matching for search operations

## Testing Server Setup

### Unit Tests

**What to Test**:
1. Server initialization completes successfully
2. Database loading handles missing files
3. Template loading handles invalid JSON
4. Tool registration creates 8 tools
5. Session storage respects limits
6. Graceful shutdown clears storage

**Test Examples**:
```python
@pytest.mark.asyncio
async def test_server_initialization():
    """Test server starts successfully with valid config."""
    server = await create_server(config_path="./test_config.yaml")
    assert server.is_ready
    assert len(server.tools) == 8
    await server.shutdown()

@pytest.mark.asyncio
async def test_database_loading_failure():
    """Test server fails gracefully when database missing."""
    with pytest.raises(DatabaseLoadError):
        await create_server(database_dir="./nonexistent")

@pytest.mark.asyncio
async def test_session_storage_limits():
    """Test session storage evicts oldest when limit reached."""
    server = await create_server(max_models=10)
    # Create 15 models
    for i in range(15):
        await server.call_tool("build_model", {...})
    # Verify only 10 models stored (oldest 5 evicted)
    assert len(server.session_storage.models) == 10
```

### Integration Tests

**What to Test**:
1. Complete startup → tool call → shutdown cycle
2. Multiple concurrent tool calls
3. Error recovery during tool execution

## Performance Characteristics

### Startup Time

**Expected Startup Times**:
- Database loading: 0.5 - 1.0 seconds
- Template loading: 2.0 - 4.0 seconds
- Total startup: 3.0 - 5.0 seconds

**Optimization**:
- Lazy loading of templates (future): Load templates on first use
- Parallel loading (future): Load database and templates concurrently

### Runtime Performance

**Session Storage**:
- Model lookup: O(1) (dictionary)
- Media lookup: O(1) (dictionary)
- Storage limit check: O(1)

**Database Queries**:
- Compound/reaction lookup by ID: O(1) (indexed)
- Search queries: O(n) where n = database size (future: add indexing)

## Deployment Patterns

### Local Development Server

**Purpose**: Developer testing and debugging

**Startup**:
```bash
# From project root
uv run python -m gem_flux_mcp.server

# Expected output:
[INFO] Gem-Flux MCP Server v0.1.0 starting...
[INFO] Server ready on localhost:8080
```

**Behavior**:
- Binds to localhost only (not accessible remotely)
- Verbose logging to console
- Auto-reload on code changes (future)

### Remote Server Deployment

**Purpose**: Team access to shared server

**Startup** (systemd service example):
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

[Install]
WantedBy=multi-user.target
```

**Behavior**:
- Binds to network interface (configurable)
- Logs to file with rotation
- Automatic restart on failure
- Process monitoring via systemd

### Docker Container (Future)

**Purpose**: Containerized deployment

**Dockerfile Pattern**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 8080
CMD ["uv", "run", "python", "-m", "gem_flux_mcp.server"]
```

**Behavior**:
- Self-contained environment
- Reproducible deployment
- Easy scaling with orchestration (Kubernetes, Docker Swarm)

## Security Considerations (Future)

**Not Included in MVP**:
- Authentication and authorization (deferred to v0.2.0)
- Rate limiting (deferred to v0.2.0)
- Input sanitization (basic validation only in MVP)
- TLS/SSL encryption (local deployment only in MVP)

**Future Security Features**:
- OAuth 2.1 with PKCE for authentication
- Scope-based permissions per tool
- Rate limiting per client
- Comprehensive input validation
- Audit logging for security events

## Alignment with Other Specifications

**Dependencies**:
- **001-system-overview.md**: Defines overall architecture and technology stack
- **007-database-integration.md**: Specifies database loading requirements
- **014-installation.md**: Defines installation procedures that precede server setup

**Provides Foundation For**:
- **003-006**: Core tool specifications (tools must be registered during setup)
- **008-009**: Database lookup tools (require database loaded at startup)
- **013-error-handling.md**: Server-level error handling patterns

## Success Criteria

**Server Setup is Successful When**:
1. Server starts without errors in under 5 seconds
2. All 8 MVP tools registered successfully
3. Database loaded with 33,993+ compounds and 43,775+ reactions
4. At least 1 template loaded (GramNegative minimum)
5. Session storage initialized
6. Server accepts and processes MCP requests
7. Graceful shutdown clears all resources

**Server Setup Fails When**:
1. Database files not found or corrupted
2. Zero templates loaded successfully
3. Port binding fails (already in use)
4. Tool registration fails for any MVP tool

## Future Enhancements

**Post-MVP Improvements** (v0.2.0+):
1. Configuration file support (YAML/TOML)
2. Hot reload of templates without server restart
3. Persistent storage backend (file-based, database)
4. Authentication and authorization
5. Rate limiting and quota management
6. Health check endpoints
7. Metrics and monitoring (Prometheus, StatsD)
8. Distributed deployment (multiple server instances)
9. Template auto-download from ModelSEED repository
10. Database update mechanism (pull latest from GitHub)

## Example Server Startup Script

**Complete Startup Example**:
```bash
#!/bin/bash
# start-server.sh

# Set configuration via environment variables
export GEM_FLUX_HOST="0.0.0.0"
export GEM_FLUX_PORT="8080"
export GEM_FLUX_DATABASE_DIR="./database"
export GEM_FLUX_TEMPLATE_DIR="./templates"
export GEM_FLUX_LOG_LEVEL="INFO"
export GEM_FLUX_LOG_FILE="./gem-flux.log"

# Start server
echo "Starting Gem-Flux MCP Server..."
uv run python -m gem_flux_mcp.server

# Server output:
# [INFO] Gem-Flux MCP Server v0.1.0 starting...
# [INFO] Configuration loaded from environment variables
# [INFO] Loading ModelSEED database from ./database
# [INFO] Loaded 33,993 compounds, 43,775 reactions
# [INFO] Loading ModelSEED templates from ./templates
# [INFO] Loaded 3 templates (GramNegative, GramPositive, Core)
# [INFO] Loading ATP gapfilling media
# [INFO] Loaded 54 ATP test media conditions
# [INFO] Initializing session storage
# [INFO] Registering MCP tools
# [INFO] Registered 8 tools
# [INFO] Starting MCP server on 0.0.0.0:8080
# [INFO] Server ready - accepting MCP requests
```

---

**This specification describes the MCP server setup behavior, resource loading, lifecycle management, and error handling patterns. It provides the foundation for implementing the Gem-Flux MCP server initialization and configuration system.**
