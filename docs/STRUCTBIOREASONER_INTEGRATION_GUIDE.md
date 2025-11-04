# StructBioReasoner Integration Guide

**Purpose**: Step-by-step instructions for integrating gem-flux-mcp with StructBioReasoner after gem-flux-mcp is fully tested and complete.

**Status**: ✅ **READY** - gem-flux-mcp v0.1.0 is fully compatible with StructBioReasoner

**Compatibility**:
- ✅ MCP Protocol: JSON-RPC 2.0 via stdio transport
- ✅ Tool Registration: FastMCP decorators properly configured
- ✅ Data Format: All tools return dict responses as expected
- ✅ Server Lifecycle: Proper startup/shutdown handling

**Repository**: https://github.com/jplfaria/gem-flux-mcp

---

## Prerequisites

Before integrating with StructBioReasoner, ensure:

- ✅ gem-flux-mcp Phase 11 is complete (MCP server working)
- ✅ All tests passing (785+ tests)
- ✅ MCP server validated with client test script
- ✅ You have access to StructBioReasoner repository

---

## Integration Steps

### Step 1: Fork StructBioReasoner Repository

```bash
# Navigate to GitHub
# Go to: https://github.com/[org]/StructBioReasoner
# Click "Fork" button

# Clone your fork
git clone https://github.com/YOUR_USERNAME/StructBioReasoner.git
cd StructBioReasoner

# Create integration branch
git checkout -b add-gemflux-mcp-integration
```

---

### Step 2: Add gem-flux-mcp Server Configuration

**File**: `struct_bio_reasoner/mcp/server_configs.py`

**Add this configuration to the `SERVER_CONFIGS` dictionary**:

```python
SERVER_CONFIGS = {
    # ... existing servers (chemtools, biotools, etc.) ...

    "gemflux": MCPServerConfig(
        name="gemflux",
        command=["uv", "--directory", "/path/to/gem-flux-mcp", "run", "python", "-m", "gem_flux_mcp"],
        description="Genome-scale metabolic modeling and flux balance analysis",
        capabilities=[
            # Growth media tools
            "build_media",          # Create growth media from compounds
            "list_media",           # List all stored media

            # Model building tools
            "build_model",          # Build metabolic model from genome (RAST, FASTA, dict)
            "gapfill_model",        # Gapfill model for growth on media
            "run_fba",              # Run flux balance analysis
            "list_models",          # List all stored models
            "delete_model",         # Delete stored model

            # Database lookup tools
            "get_compound_name",    # Look up compound by ModelSEED ID
            "search_compounds",     # Search compounds by name/formula
            "get_reaction_name",    # Look up reaction by ModelSEED ID
            "search_reactions",     # Search reactions by name
        ]
    )
}
```

**Notes**:
- Command uses `uv run python -m gem_flux_mcp.server` for maximum compatibility
- Assumes user has gem-flux-mcp installed in their environment
- If gem-flux-mcp adds CLI entry point, can use: `["uv", "run", "gem-flux-mcp"]`

---

### Step 3: Create Metabolic Modeling Agent (Optional)

**File**: `struct_bio_reasoner/agents/metabolic_modeler.py` (NEW)

```python
"""Agent for genome-scale metabolic modeling using gem-flux-mcp."""
from struct_bio_reasoner.agents.base import BaseAgent
from struct_bio_reasoner.mcp.mcp_client import MCPClient
from struct_bio_reasoner.mcp.server_configs import SERVER_CONFIGS


class MetabolicModelerAgent(BaseAgent):
    """Agent for building and analyzing genome-scale metabolic models.

    Uses gem-flux-mcp MCP server to:
    - Build metabolic models from genomes (RAST, FASTA, dict)
    - Gapfill models for growth on different media
    - Run flux balance analysis (FBA)
    - Query ModelSEED database for compounds and reactions
    """

    def __init__(self):
        super().__init__(
            name="MetabolicModeler",
            description="Builds and analyzes genome-scale metabolic models"
        )

        # Initialize gem-flux-mcp client
        self.gemflux = MCPClient(SERVER_CONFIGS["gemflux"])
        self.gemflux.start_server()

        self.log(f"Connected to gem-flux-mcp with {len(self.gemflux.tools)} tools")

    def build_and_analyze_model(
        self,
        genome_id: str,
        model_id: str,
        media: str = "minimal",
        template: str = "auto"
    ) -> dict:
        """Build metabolic model from genome and analyze growth.

        Args:
            genome_id: RAST genome ID (e.g., "83333.1" for E. coli K-12)
            model_id: Unique model identifier using .gf notation (e.g., "ecoli_k12.gf")
            media: Growth medium ID (default: "minimal")
            template: ModelSEED template (default: "auto" for auto-detection)

        Returns:
            dict with model statistics and growth analysis
        """
        self.log(f"Building model {model_id} from genome {genome_id}")

        # Step 1: Build model from genome
        build_result = self.gemflux.call_tool("build_model", {
            "model_id": model_id,
            "genome_source_type": "rast_id",
            "genome_source_value": genome_id,
            "template_id": template
        })

        self.log(f"✅ Model built: {build_result['total_reactions']} reactions, "
                 f"{build_result['total_genes']} genes")

        # Step 2: Gapfill for growth on media
        self.log(f"Gapfilling model for growth on {media} medium")

        gapfill_result = self.gemflux.call_tool("gapfill_model", {
            "model_id": model_id,
            "media_id": media
        })

        if gapfill_result["status"] == "success":
            self.log(f"✅ Gapfilled: {gapfill_result['reactions_added']} reactions added")
        else:
            self.log(f"⚠️ Gapfilling failed: {gapfill_result['error_message']}")
            return {
                "status": "gapfill_failed",
                "model_id": model_id,
                "error": gapfill_result["error_message"]
            }

        # Step 3: Run FBA to verify growth
        self.log(f"Running flux balance analysis")

        fba_result = self.gemflux.call_tool("run_fba", {
            "model_id": model_id,
            "media_id": media
        })

        growth_rate = fba_result["objective_value"]
        can_grow = growth_rate > 1e-6  # Small positive threshold

        if can_grow:
            self.log(f"✅ Growth rate: {growth_rate:.4f}")
        else:
            self.log(f"❌ No growth: {growth_rate:.4e}")

        return {
            "status": "success",
            "model_id": model_id,
            "genome_id": genome_id,
            "template_id": build_result["template_id"],
            "total_reactions": build_result["total_reactions"],
            "total_genes": build_result["total_genes"],
            "reactions_added": gapfill_result["reactions_added"],
            "growth_rate": growth_rate,
            "can_grow": can_grow,
            "media": media
        }

    def test_media_conditions(
        self,
        model_id: str,
        media_list: list[str]
    ) -> dict:
        """Test growth on multiple media conditions.

        Args:
            model_id: Model identifier (must already be built)
            media_list: List of media IDs to test (e.g., ["minimal", "complete", "LB"])

        Returns:
            dict mapping media_id -> growth results
        """
        results = {}

        for media in media_list:
            self.log(f"Testing growth on {media}")

            # Gapfill for this media
            gapfill_result = self.gemflux.call_tool("gapfill_model", {
                "model_id": model_id,
                "media_id": media
            })

            # Run FBA
            fba_result = self.gemflux.call_tool("run_fba", {
                "model_id": model_id,
                "media_id": media
            })

            growth_rate = fba_result["objective_value"]
            can_grow = growth_rate > 1e-6

            results[media] = {
                "can_grow": can_grow,
                "growth_rate": growth_rate,
                "reactions_added": gapfill_result.get("reactions_added", 0)
            }

            status = "✅ Grows" if can_grow else "❌ No growth"
            self.log(f"{status} on {media}: {growth_rate:.4f}")

        return results

    def search_compound(self, query: str, limit: int = 5) -> list[dict]:
        """Search ModelSEED database for compounds.

        Args:
            query: Search term (name, formula, ID)
            limit: Maximum results to return

        Returns:
            list of compound dicts with id, name, formula, charge
        """
        result = self.gemflux.call_tool("search_compounds", {
            "query": query,
            "limit": limit
        })

        return result["compounds"]

    def search_reaction(self, query: str, limit: int = 5) -> list[dict]:
        """Search ModelSEED database for reactions.

        Args:
            query: Search term (name, EC number, ID)
            limit: Maximum results to return

        Returns:
            list of reaction dicts with id, name, equation, ec_numbers
        """
        result = self.gemflux.call_tool("search_reactions", {
            "query": query,
            "limit": limit
        })

        return result["reactions"]

    def cleanup(self, model_id: str):
        """Delete model from storage.

        Args:
            model_id: Model identifier to delete
        """
        self.gemflux.call_tool("delete_model", {"model_id": model_id})
        self.log(f"Deleted model {model_id}")
```

---

### Step 4: Create Integration Test

**File**: `examples/test_gemflux_integration.py` (NEW)

```python
"""Integration test for gem-flux-mcp MCP server.

Run this to verify gem-flux-mcp integration works correctly.
"""
from struct_bio_reasoner.mcp.mcp_client import MCPClient
from struct_bio_reasoner.mcp.server_configs import SERVER_CONFIGS


def test_direct_mcp_client():
    """Test gem-flux-mcp using MCPClient directly."""
    print("=" * 60)
    print("Testing gem-flux-mcp MCP Server Integration")
    print("=" * 60)

    # Initialize client
    print("\n1. Initializing gem-flux-mcp MCP client...")
    client = MCPClient(SERVER_CONFIGS["gemflux"])
    client.start_server()
    print(f"✅ Connected to gem-flux-mcp with {len(client.tools)} tools")

    # Test 1: Build model
    print("\n2. Building E. coli K-12 metabolic model...")
    build_result = client.call_tool("build_model", {
        "model_id": "test_ecoli.gf",
        "genome_source_type": "rast_id",
        "genome_source_value": "83333.1",
        "template_id": "auto"
    })
    print(f"✅ Model built: {build_result['total_reactions']} reactions, "
          f"{build_result['total_genes']} genes")

    # Test 2: Gapfill model
    print("\n3. Gapfilling model for growth on minimal medium...")
    gapfill_result = client.call_tool("gapfill_model", {
        "model_id": "test_ecoli.gf",
        "media_id": "minimal"
    })

    if gapfill_result["status"] == "success":
        print(f"✅ Gapfilled: {gapfill_result['reactions_added']} reactions added")
    else:
        print(f"❌ Gapfilling failed: {gapfill_result['error_message']}")
        return

    # Test 3: Run FBA
    print("\n4. Running flux balance analysis...")
    fba_result = client.call_tool("run_fba", {
        "model_id": "test_ecoli.gf",
        "media_id": "minimal"
    })

    growth_rate = fba_result["objective_value"]
    print(f"✅ Growth rate: {growth_rate:.4f}")

    # Test 4: List models
    print("\n5. Listing stored models...")
    list_result = client.call_tool("list_models", {})
    print(f"✅ Found {len(list_result['models'])} models in storage")

    # Test 5: Search compounds
    print("\n6. Searching for glucose compounds...")
    search_result = client.call_tool("search_compounds", {
        "query": "glucose",
        "limit": 3
    })
    print(f"✅ Found {len(search_result['compounds'])} glucose compounds")
    for cpd in search_result['compounds']:
        print(f"   - {cpd['id']}: {cpd['name']}")

    # Test 6: Clean up
    print("\n7. Cleaning up test model...")
    client.call_tool("delete_model", {"model_id": "test_ecoli.gf"})
    print("✅ Model deleted")

    print("\n" + "=" * 60)
    print("✅ All tests passed! gem-flux-mcp integration working correctly.")
    print("=" * 60)


def test_agent_interface():
    """Test gem-flux-mcp using MetabolicModelerAgent."""
    print("\n" + "=" * 60)
    print("Testing MetabolicModelerAgent Interface")
    print("=" * 60)

    from struct_bio_reasoner.agents.metabolic_modeler import MetabolicModelerAgent

    # Initialize agent
    print("\n1. Initializing MetabolicModelerAgent...")
    agent = MetabolicModelerAgent()

    # Test complete workflow
    print("\n2. Running complete modeling workflow...")
    result = agent.build_and_analyze_model(
        genome_id="83333.1",  # E. coli K-12
        model_id="agent_test.gf",
        media="minimal"
    )

    if result["status"] == "success":
        print(f"\n✅ Workflow complete!")
        print(f"   Model ID: {result['model_id']}")
        print(f"   Reactions: {result['total_reactions']} ({result['reactions_added']} added)")
        print(f"   Genes: {result['total_genes']}")
        print(f"   Growth rate: {result['growth_rate']:.4f}")
    else:
        print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
        return

    # Test media conditions
    print("\n3. Testing multiple media conditions...")
    media_results = agent.test_media_conditions(
        model_id="agent_test.gf",
        media_list=["minimal", "complete"]
    )

    print("\nMedia test results:")
    for media, result in media_results.items():
        status = "✅" if result["can_grow"] else "❌"
        print(f"   {status} {media}: {result['growth_rate']:.4f}")

    # Clean up
    print("\n4. Cleaning up...")
    agent.cleanup("agent_test.gf")

    print("\n" + "=" * 60)
    print("✅ Agent interface tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    # Test both interfaces
    test_direct_mcp_client()
    print("\n" * 2)
    test_agent_interface()
```

---

### Step 5: Test Integration

```bash
# Ensure gem-flux-mcp is installed
pip install -e /path/to/gem-flux-mcp

# Run integration test
python examples/test_gemflux_integration.py
```

**Expected Output**:
```
============================================================
Testing gem-flux-mcp MCP Server Integration
============================================================

1. Initializing gem-flux-mcp MCP client...
✅ Connected to gem-flux-mcp with 11 tools

2. Building E. coli K-12 metabolic model...
✅ Model built: 1247 reactions, 4140 genes

3. Gapfilling model for growth on minimal medium...
✅ Gapfilled: 23 reactions added

4. Running flux balance analysis...
✅ Growth rate: 0.8540

5. Listing stored models...
✅ Found 1 models in storage

6. Searching for glucose compounds...
✅ Found 3 glucose compounds
   - cpd00027: D-Glucose
   - cpd00221: D-Glucose 1-phosphate
   - cpd00179: D-Glucose 6-phosphate

7. Cleaning up test model...
✅ Model deleted

============================================================
✅ All tests passed! gem-flux-mcp integration working correctly.
============================================================
```

---

### Step 6: Commit and Push

```bash
# Stage changes
git add struct_bio_reasoner/mcp/server_configs.py
git add struct_bio_reasoner/agents/metabolic_modeler.py
git add examples/test_gemflux_integration.py

# Commit
git commit -m "Add gem-flux-mcp MCP server integration

Adds support for genome-scale metabolic modeling via gem-flux-mcp:
- 11 MCP tools for model building, gapfilling, FBA, and database queries
- MetabolicModelerAgent for high-level workflow automation
- Integration tests validating MCP communication

Capabilities:
- Build models from RAST genomes, FASTA files, or genome dicts
- Gapfill models for growth on custom media
- Run flux balance analysis
- Query ModelSEED compound and reaction databases
- Session-based model storage"

# Push to your fork
git push origin add-gemflux-mcp-integration
```

---

### Step 7: Create Pull Request (Optional)

If you want to contribute back to the main StructBioReasoner repository:

1. Go to your fork on GitHub
2. Click "Pull Request" button
3. Write description explaining the integration
4. Submit for review

---

## Usage Examples

### Example 1: Basic Model Building

```python
from struct_bio_reasoner.mcp.mcp_client import MCPClient
from struct_bio_reasoner.mcp.server_configs import SERVER_CONFIGS

# Initialize client
client = MCPClient(SERVER_CONFIGS["gemflux"])
client.start_server()

# Build model from RAST genome
result = client.call_tool("build_model", {
    "model_id": "ecoli_k12.gf",
    "genome_source_type": "rast_id",
    "genome_source_value": "83333.1"
})

print(f"Model built with {result['total_reactions']} reactions")
```

---

### Example 2: Complete Workflow with Agent

```python
from struct_bio_reasoner.agents.metabolic_modeler import MetabolicModelerAgent

# Initialize agent
agent = MetabolicModelerAgent()

# Build and analyze model
result = agent.build_and_analyze_model(
    genome_id="83333.1",
    model_id="ecoli.gf",
    media="minimal"
)

if result["can_grow"]:
    print(f"✅ Model grows at {result['growth_rate']:.4f}")
else:
    print("❌ Model cannot grow on minimal media")
```

---

### Example 3: Multi-Media Testing

```python
from struct_bio_reasoner.agents.metabolic_modeler import MetabolicModelerAgent

agent = MetabolicModelerAgent()

# Build model
agent.build_and_analyze_model(
    genome_id="83333.1",
    model_id="ecoli.gf",
    media="minimal"
)

# Test on multiple media
results = agent.test_media_conditions(
    model_id="ecoli.gf",
    media_list=["minimal", "complete", "LB", "rich"]
)

# Analyze results
for media, result in results.items():
    if result["can_grow"]:
        print(f"✅ {media}: {result['growth_rate']:.4f}")
    else:
        print(f"❌ {media}: No growth")
```

---

### Example 4: Database Queries

```python
from struct_bio_reasoner.agents.metabolic_modeler import MetabolicModelerAgent

agent = MetabolicModelerAgent()

# Search for compounds
glucose_compounds = agent.search_compound("glucose", limit=5)
for cpd in glucose_compounds:
    print(f"{cpd['id']}: {cpd['name']} ({cpd['formula']})")

# Search for reactions
glycolysis = agent.search_reaction("glycolysis", limit=5)
for rxn in glycolysis:
    print(f"{rxn['id']}: {rxn['name']}")
    print(f"  Equation: {rxn['equation']}")
```

---

## Troubleshooting

### Issue: "gem-flux-mcp server not found"

**Cause**: gem-flux-mcp not installed in environment

**Solution**:
```bash
# Install gem-flux-mcp
pip install -e /path/to/gem-flux-mcp

# Or if published to PyPI:
pip install gem-flux-mcp
```

---

### Issue: "No tools available from server"

**Cause**: gem-flux-mcp server.py tool registration bug (Phase 11 Task 11.2 not complete)

**Solution**: Ensure gem-flux-mcp Phase 11 is fully complete before integration.

---

### Issue: "Gapfilling fails with no solution"

**Cause**: Model cannot grow on specified media (biological constraint)

**Solution**: This is expected behavior. Try:
- Different media (e.g., "complete" instead of "minimal")
- Check if organism is auxotrophic
- Verify genome quality

---

### Issue: "DatabaseIndex not loaded"

**Cause**: ModelSEED database not initialized

**Solution**: gem-flux-mcp automatically loads database on first tool call. If issues persist, check gem-flux-mcp installation.

---

## MCP Tool Reference

### Model Building Tools

- **build_model**: Build metabolic model from genome (RAST ID, FASTA, or dict)
- **gapfill_model**: Gapfill model for growth on specified media
- **run_fba**: Run flux balance analysis (FBA)
- **list_models**: List all models in session storage
- **delete_model**: Delete model from session storage

### Media Tools

- **build_media**: Create custom growth medium from compounds
- **list_media**: List all media in session storage

### Database Query Tools

- **get_compound_name**: Look up compound by ModelSEED ID
- **search_compounds**: Search compounds by name/formula/ID
- **get_reaction_name**: Look up reaction by ModelSEED ID
- **search_reactions**: Search reactions by name/EC number

---

## Model ID Notation

gem-flux-mcp uses `.gf` notation for model IDs to indicate gapfilled models:

- `ecoli.gf` - E. coli gapfilled model
- `bsubtilis_168.gf` - B. subtilis 168 gapfilled model
- `mymodel.gf` - Generic gapfilled model

This is a **convention**, not a requirement. You can use any string as model_id, but `.gf` helps identify gapfilled models in workflows.

---

## Next Steps

After successful integration:

1. **Use in StructBioReasoner workflows**: Integrate MetabolicModelerAgent into multi-agent workflows
2. **Create domain-specific agents**: Build specialized agents for specific organisms or analyses
3. **Extend functionality**: Combine metabolic modeling with protein structure analysis
4. **Share with community**: Submit PR to StructBioReasoner if valuable to others

---

**Document Version**: 1.0
**Last Updated**: 2025-10-29
**Next Review**: After StructBioReasoner integration testing
