#!/bin/bash
# Start Gem-Flux MCP Server
#
# This script starts the Gem-Flux MCP server with configuration
# from environment variables.

set -e  # Exit on error

echo "Starting Gem-Flux MCP Server..."
echo "================================"

# Set default configuration (can be overridden via environment)
export GEM_FLUX_HOST="${GEM_FLUX_HOST:-localhost}"
export GEM_FLUX_PORT="${GEM_FLUX_PORT:-8080}"
export GEM_FLUX_DATABASE_DIR="${GEM_FLUX_DATABASE_DIR:-./data/database}"
export GEM_FLUX_TEMPLATE_DIR="${GEM_FLUX_TEMPLATE_DIR:-./data/templates}"
export GEM_FLUX_LOG_LEVEL="${GEM_FLUX_LOG_LEVEL:-INFO}"
export GEM_FLUX_MAX_MODELS="${GEM_FLUX_MAX_MODELS:-100}"

echo "Configuration:"
echo "  Host: $GEM_FLUX_HOST"
echo "  Port: $GEM_FLUX_PORT"
echo "  Database Dir: $GEM_FLUX_DATABASE_DIR"
echo "  Template Dir: $GEM_FLUX_TEMPLATE_DIR"
echo "  Log Level: $GEM_FLUX_LOG_LEVEL"
echo "  Max Models: $GEM_FLUX_MAX_MODELS"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found (.venv)"
    echo "Please run: uv sync"
    exit 1
fi

# Check if database files exist
if [ ! -f "$GEM_FLUX_DATABASE_DIR/compounds.tsv" ]; then
    echo "Error: Database file not found: $GEM_FLUX_DATABASE_DIR/compounds.tsv"
    echo "Please download ModelSEED database files"
    exit 1
fi

if [ ! -f "$GEM_FLUX_DATABASE_DIR/reactions.tsv" ]; then
    echo "Error: Database file not found: $GEM_FLUX_DATABASE_DIR/reactions.tsv"
    echo "Please download ModelSEED database files"
    exit 1
fi

# Start server using uv run
echo "Starting server..."
uv run python -m gem_flux_mcp
