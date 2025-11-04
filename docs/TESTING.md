# Testing Guide

This document describes the testing strategy and test suite for gem-flux-mcp.

## Overview

gem-flux-mcp uses a comprehensive test suite covering:
- **Unit tests**: Individual function and component testing
- **Integration tests**: End-to-end workflow validation
- **Test coverage**: 150+ tests across 14 modules

## Test Organization

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_compound_lookup.py
│   ├── test_reaction_lookup.py
│   ├── test_media_builder.py
│   └── ...
├── integration/             # Integration tests for workflows
│   ├── test_build_model_integration.py        # 13 tests
│   ├── test_full_workflow_notebook_replication.py
│   ├── test_model_persistence_with_media.py
│   └── ...
└── conftest.py             # Shared fixtures
```

## Running Tests

### Run All Tests

```bash
uv run pytest
```

### Run Specific Test Module

```bash
uv run pytest tests/integration/test_build_model_integration.py
```

### Run Tests by Pattern

```bash
# Run all ATP correction tests
uv run pytest -k "atp"

# Run all build_model tests
uv run pytest -k "build_model"
```

### Run Tests with Verbose Output

```bash
uv run pytest -v
```

### Run Tests with Coverage

```bash
uv run pytest --cov=src/gem_flux_mcp --cov-report=html
```

### Skip Slow Tests

```bash
uv run pytest -m "not slow"
```

## Test Modules

### Core Workflow Tests

#### `test_build_model_integration.py` (13 tests)

Tests for model building with different configurations:

**Class: TestBuildModelIntegration**
- Basic model building (FASTA, protein dict)
- Template variations (GramNegative, GramPositive, Core)
- RAST annotation integration
- Input validation

**Class: TestATPCorrectionIntegration**
- ATP correction application
- Test conditions creation
- Multi-media validation
- Genome-scale gapfilling

```bash
# Run all build_model tests
uv run pytest tests/integration/test_build_model_integration.py -v

# Run ATP correction tests only
uv run pytest tests/integration/test_build_model_integration.py::TestATPCorrectionIntegration -v
```

#### `test_full_workflow_notebook_replication.py`

End-to-end workflow tests replicating notebook behavior:
- Complete build → gapfill → FBA workflow
- Growth rate validation (~0.5544 expected)
- Media application correctness
- Model persistence

```bash
uv run pytest tests/integration/test_full_workflow_notebook_replication.py -v
```

#### `test_model_persistence_with_media.py`

Model save/load and media handling tests:
- Model save to JSON
- Model load from JSON
- Media persistence across sessions
- Growth rate preservation after load

```bash
uv run pytest tests/integration/test_model_persistence_with_media.py -v
```

### Unit Tests

#### `test_compound_lookup.py` (15 tests)

Tests for compound database queries:
- `get_compound_name`: ID lookups
- `search_compounds`: Text search (name, formula, aliases)
- Input validation
- Error handling

```bash
uv run pytest tests/unit/test_compound_lookup.py -v
```

#### `test_reaction_lookup.py` (15 tests)

Tests for reaction database queries:
- `get_reaction_name`: ID lookups
- `search_reactions`: Text search (name, EC, pathway)
- Equation formatting
- Metadata parsing

```bash
uv run pytest tests/unit/test_reaction_lookup.py -v
```

#### `test_media_builder.py` (11 tests)

Tests for media construction:
- Compound validation
- Bounds application
- Custom bounds override
- Error handling

```bash
uv run pytest tests/unit/test_media_builder.py -v
```

## Key Test Scenarios

### Building Models

```python
# Test: Build model with ATP correction
@pytest.mark.asyncio
async def test_build_with_atp_correction():
    result = await build_model(
        fasta_file_path=fasta_path,
        template="GramNegative",
        model_name="test_model",
        apply_atp_correction=True
    )
    assert result['atp_correction']['atp_correction_applied'] == True
```

### Gapfilling Models

```python
# Test: Gapfilling enables growth
def test_gapfilling_enables_growth():
    # Build draft model
    build_result = await build_model(...)

    # Gapfill
    gapfill_result = gapfill_model(
        model_id=build_result["model_id"],
        media_id="glucose_minimal",
        db_index=db_index
    )

    # Verify growth increased
    assert gapfill_result['growth_rate_after'] > 0.01
```

### Running FBA

```python
# Test: FBA produces expected growth rate
def test_fba_growth_rate():
    fba_result = run_fba(
        model_id="ecoli.draft.gf",
        media_id="glucose_minimal",
        db_index=db_index
    )

    # E. coli on glucose minimal should be ~0.5544
    assert abs(fba_result['objective_value'] - 0.5544) < 0.01
```

## Test Fixtures

### Shared Fixtures (`conftest.py`)

```python
@pytest.fixture
def db_index():
    """DatabaseIndex with loaded compounds and reactions"""
    compounds_df = load_compounds_database("data/database/compounds.tsv")
    reactions_df = load_reactions_database("data/database/reactions.tsv")
    return DatabaseIndex(compounds_df, reactions_df)

@pytest.fixture
def fasta_path():
    """Path to E. coli test FASTA file"""
    return "specs-source/build_metabolic_model/GCF_000005845.2_ASM584v2_protein.faa"

@pytest.fixture
def glucose_minimal_media(db_index):
    """Glucose minimal aerobic media"""
    # Load from stored file
    media_file = "data/media/glucose_minimal_aerobic.json"
    with open(media_file) as f:
        media_json = json.load(f)

    # Build media
    compounds = list(media_json['compounds'].keys())
    custom_bounds = {k: tuple(v['bounds']) for k, v in media_json['compounds'].items()}

    request = BuildMediaRequest(
        compounds=compounds,
        default_uptake=100.0,
        custom_bounds=custom_bounds
    )
    return build_media(request, db_index)
```

## Test Coverage

### Coverage by Module

| Module | Tests | Coverage |
|--------|-------|----------|
| build_model | 13 | Comprehensive |
| gapfill_model | Workflow tests | Good |
| run_fba | Workflow tests | Good |
| compound_lookup | 15 | Comprehensive |
| reaction_lookup | 15 | Comprehensive |
| media_builder | 11 | Comprehensive |
| list_models | Basic | Good |
| list_media | Basic | Good |
| delete_model | Basic | Good |

### Running Coverage Report

```bash
# Generate HTML coverage report
uv run pytest --cov=src/gem_flux_mcp --cov-report=html

# Open report
open htmlcov/index.html
```

## Expected Test Results

### E. coli Model on Glucose Minimal

After complete workflow (build → gapfill → FBA):

```python
{
    "objective_value": 0.5544,  # Growth rate (± 0.01)
    "active_reactions": ~800,   # Of ~2000 total
    "uptake_fluxes": [
        {"compound_id": "cpd00027", "flux": -10.0},  # Glucose
        {"compound_id": "cpd00007", "flux": -21.8},  # O2
        # ... more uptake
    ],
    "secretion_fluxes": [
        {"compound_id": "cpd00011", "flux": 22.8},   # CO2
        # ... more secretion
    ]
}
```

## Testing Best Practices

### 1. Clean State Between Tests

```python
@pytest.fixture(autouse=True)
def clean_storage():
    """Clear model/media storage before each test"""
    from gem_flux_mcp.storage.models import clear_all_models
    from gem_flux_mcp.storage.media import clear_all_media

    clear_all_models()
    clear_all_media()
    yield
```

### 2. Use Descriptive Test Names

```python
# Good
def test_build_model_with_atp_correction_creates_test_conditions():
    ...

# Bad
def test_build():
    ...
```

### 3. Test Both Success and Failure Cases

```python
def test_compound_lookup_valid_id():
    result = get_compound_name(
        GetCompoundNameRequest(compound_id="cpd00027"),
        db_index
    )
    assert result['name'] == 'D-Glucose'

def test_compound_lookup_invalid_id():
    with pytest.raises(NotFoundError):
        get_compound_name(
            GetCompoundNameRequest(compound_id="cpd99999"),
            db_index
        )
```

### 4. Validate Key Properties

```python
def test_gapfilled_model_properties():
    result = gapfill_model(...)

    # Verify model ID transformation
    assert result['model_id'].endswith('.gf')

    # Verify growth improvement
    assert result['growth_rate_after'] > result['growth_rate_before']

    # Verify reactions added
    assert result['num_reactions_added'] > 0
```

## Debugging Failed Tests

### View Full Test Output

```bash
uv run pytest -v -s  # -s shows print statements
```

### Run Single Test with Debug Output

```bash
uv run pytest tests/integration/test_build_model_integration.py::TestBuildModelIntegration::test_build_model_basic -v -s
```

### Use Pytest Debugger

```python
def test_something():
    result = some_function()
    import pdb; pdb.set_trace()  # Breakpoint
    assert result == expected
```

## Continuous Integration

### GitHub Actions

Tests are automatically run on:
- Push to main branch
- Pull requests
- Manual workflow trigger

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install uv
          uv run pytest --cov
```

## Performance Testing

### Timing Tests

```python
import time

def test_build_model_performance():
    start = time.time()
    result = await build_model(...)
    duration = time.time() - start

    # Should complete in <5 minutes
    assert duration < 300
```

### Memory Testing

```python
import tracemalloc

def test_memory_usage():
    tracemalloc.start()
    result = run_fba(...)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Peak usage should be <2GB
    assert peak < 2 * 1024**3
```

## See Also

- [ATP Correction](ATP_CORRECTION.md) - ATP correction feature details
- [Tool Documentation](tools/README.md) - Tool usage examples
- Integration test examples in `tests/integration/`
- Unit test examples in `tests/unit/`
