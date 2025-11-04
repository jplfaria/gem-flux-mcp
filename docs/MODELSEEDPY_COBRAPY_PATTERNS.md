# ModelSEEDpy/COBRApy Integration Patterns

**Status**: Implementation Reference
**Last Updated**: 2025-10-27
**Source**: specs-source/references/MODELSEEDPY_COBRAPY_COMPATIBILITY_GUIDE.md

## Purpose

This document summarizes the critical patterns needed when implementing MCP tools that integrate ModelSEEDpy gapfilling with COBRApy models. These patterns prevent common bugs that cause runtime failures.

---

## Pattern 1: Compartment Suffix Conversion

### The Problem

- **Gapfill solutions** use indexed compartments: `rxn05481_c0`, `rxn00062_e0`
- **Templates** use non-indexed compartments: `rxn05481_c`, `rxn00062_e`
- Direct lookup fails: `template.reactions.get_by_id('rxn05481_c0')` → `KeyError`

### The Solution

```python
def get_template_reaction_id(model_rxn_id: str) -> str:
    """Convert model reaction ID to template reaction ID.

    Args:
        model_rxn_id: Reaction ID from model/gapfill (indexed compartment)

    Returns:
        Reaction ID for template lookup (non-indexed compartment)

    Examples:
        rxn05481_c0 → rxn05481_c
        rxn00062_e0 → rxn00062_e
        rxn05481_c → rxn05481_c (already template format)
    """
    if model_rxn_id.endswith('0'):
        return model_rxn_id[:-1]  # Strip trailing '0' only
    return model_rxn_id
```

### When to Use

- **Gapfill model tool** (spec 005): When integrating gapfill solutions into models
- **Any code** that looks up reactions in templates using IDs from models

### Common Mistakes to Avoid

```python
# ❌ WRONG - removes entire compartment
template_rxn_id = rxn_id[:-3]  # 'rxn05481_c0' → 'rxn05481'

# ❌ WRONG - hardcodes compartment type
template_rxn_id = rxn_id.replace('_c0', '_c')  # fails for _e0, _p0

# ❌ WRONG - splits on underscore
template_rxn_id = rxn_id.split('_')[0]  # loses compartment

# ✅ CORRECT - generic, handles all types
template_rxn_id = rxn_id[:-1] if rxn_id.endswith('0') else rxn_id
```

---

## Pattern 2: Media Format Conversion

### The Problem

- **MCP tools** accept compound IDs: `["cpd00027", "cpd00007"]`
- **ModelSEED media** uses negative uptake: `{"cpd00027": [-10, 100]}`
- **COBRApy** needs exchange IDs with positive uptake: `{"EX_cpd00027_e0": 10}`

### The Solution

```python
def convert_media_to_cobra_format(
    compounds: List[str],
    default_uptake: float,
    custom_bounds: Optional[Dict[str, List[float]]],
    model: cobra.Model
) -> Tuple[Dict[str, float], List[str]]:
    """Convert MCP media format to COBRApy medium format.

    Args:
        compounds: List of compound IDs (e.g., ["cpd00027", "cpd00007"])
        default_uptake: Default max uptake rate (positive)
        custom_bounds: Optional {cpd_id: [lower, upper]} bounds
        model: COBRApy model to check for exchange reactions

    Returns:
        cobra_medium: {"EX_cpd00027_e0": 10, ...} for model.medium
        missing: List of compound IDs without exchange reactions

    Example:
        compounds = ["cpd00027", "cpd00007"]
        custom_bounds = {"cpd00027": [-5, 100]}

        Result: ({"EX_cpd00027_e0": 5, "EX_cpd00007_e0": 10}, [])
    """
    cobra_medium = {}
    missing = []

    for cpd_id in compounds:
        # Get uptake rate from custom bounds or use default
        if custom_bounds and cpd_id in custom_bounds:
            lower, upper = custom_bounds[cpd_id]
            uptake_rate = abs(lower)  # Negative → positive
        else:
            uptake_rate = default_uptake

        # Cap unlimited uptake
        if uptake_rate >= 100:
            uptake_rate = default_uptake

        # Try multiple exchange reaction formats
        possible_exchange_ids = [
            f"EX_{cpd_id}_e0",    # Most common: EX_cpd00027_e0
            f"EX_{cpd_id}_e",     # Alternative: EX_cpd00027_e
            f"{cpd_id}_e0",       # Minimal: cpd00027_e0
        ]

        found = False
        for ex_id in possible_exchange_ids:
            if ex_id in model.reactions:
                cobra_medium[ex_id] = uptake_rate
                found = True
                break

        if not found:
            missing.append(cpd_id)

    return cobra_medium, missing
```

### When to Use

- **Build media tool** (spec 003): Converting `BuildMediaRequest` to COBRApy medium
- **Run FBA tool** (spec 006): Applying media before optimization
- **Predefined media** (spec 019): Loading ModelSEED JSON media files

### Key Conversions

```python
# 1. Compound ID → Exchange Reaction ID
"cpd00027" → "EX_cpd00027_e0"

# 2. Negative flux → Positive uptake
[-10, 100] → 10  # abs(lower_bound)

# 3. Unlimited uptake → Default cap
[-100, 100] → 10  # Use default_uptake instead

# 4. Single value format
-10 → 10  # abs(value)
```

---

## Pattern 3: Reaction Direction Symbols

### The Problem

- **ModelSEEDpy gapfill** returns direction symbols: `'>'`, `'<'`, `'='`
- **COBRApy** needs numeric bounds: `(lower_bound, upper_bound)`

### The Solution

```python
def get_reaction_bounds_from_direction(direction: str) -> Tuple[float, float]:
    """Convert ModelSEEDpy direction symbol to COBRApy bounds.

    Args:
        direction: Direction symbol from gapfill solution
            '>' = Forward only (A → B)
            '<' = Reverse only (A ← B)
            '=' = Reversible (A ⇌ B)

    Returns:
        (lower_bound, upper_bound) for COBRApy reaction

    Examples:
        '>' → (0, 1000)      # Forward only
        '<' → (-1000, 0)     # Reverse only
        '=' → (-1000, 1000)  # Reversible
    """
    if direction == '>':
        return (0, 1000)      # Forward only
    elif direction == '<':
        return (-1000, 0)     # Reverse only
    elif direction == '=':
        return (-1000, 1000)  # Reversible
    else:
        raise ValueError(f"Unknown direction symbol: {direction}")
```

### When to Use

- **Gapfill model tool** (spec 005): Setting bounds on added reactions
- **Any code** that processes `GapfillModelResponse.reactions_added`

---

## Implementation Status

### ✅ Already Fixed
- [x] Spec 005 line 1194: Corrected compartment suffix stripping pattern

### ⏳ To Implement (Future Tasks)

**Task 33: Compartment Utilities**
- Location: `src/gem_flux_mcp/utils/compartments.py`
- Functions: `get_template_reaction_id()`, `is_indexed_compartment()`
- Tests: `tests/unit/test_compartments.py`

**Task 34: Media Conversion Utilities**
- Location: `src/gem_flux_mcp/media/converter.py`
- Functions: `convert_media_to_cobra_format()`, `build_exchange_reaction_id()`
- Tests: `tests/unit/test_media_converter.py`

**Task 40: Build Media Tool**
- Uses: Media conversion utilities
- Implements: Pattern 2 (media format conversion)

**Task 54: Gapfill Model Tool**
- Uses: Compartment utilities, reaction direction conversion
- Implements: Pattern 1 (compartment suffix), Pattern 3 (direction symbols)

---

## Testing Requirements

### Unit Tests Needed

**Compartment Conversion**:
```python
def test_compartment_suffix_conversion():
    assert get_template_reaction_id('rxn05481_c0') == 'rxn05481_c'
    assert get_template_reaction_id('rxn00062_e0') == 'rxn00062_e'
    assert get_template_reaction_id('rxn09876_p0') == 'rxn09876_p'
    assert get_template_reaction_id('rxn05481_c') == 'rxn05481_c'
```

**Media Conversion**:
```python
def test_media_format_conversion(model):
    compounds = ["cpd00027", "cpd00007"]
    custom_bounds = {"cpd00027": [-5, 100]}

    medium, missing = convert_media_to_cobra_format(
        compounds, default_uptake=10, custom_bounds=custom_bounds, model=model
    )

    assert medium["EX_cpd00027_e0"] == 5  # From custom bounds
    assert medium["EX_cpd00007_e0"] == 10  # From default
    assert len(missing) == 0
```

**Direction Conversion**:
```python
def test_direction_to_bounds():
    assert get_reaction_bounds_from_direction('>') == (0, 1000)
    assert get_reaction_bounds_from_direction('<') == (-1000, 0)
    assert get_reaction_bounds_from_direction('=') == (-1000, 1000)
```

### Integration Tests Needed

**End-to-End Gapfill**:
```python
def test_gapfill_integration_workflow():
    # Build model
    model = build_model(...)

    # Gapfill
    result = gapfill_model(model_id, media_id)

    # Verify reactions added (uses Pattern 1)
    assert len(result.reactions_added) > 0
    for rxn in result.reactions_added:
        # Reaction IDs should be in model format (indexed)
        assert rxn.id.endswith('0') or rxn.id.startswith('EX_')
        # Compartment should be single letter
        assert rxn.compartment in ['c', 'e', 'p']
```

**End-to-End Media Application**:
```python
def test_media_application_workflow():
    # Build media
    media_result = build_media(compounds=["cpd00027", "cpd00007"])

    # Apply to model for FBA (uses Pattern 2)
    fba_result = run_fba(model_id, media_id)

    # Verify FBA ran with correct medium
    assert fba_result.objective_value > 0
    assert len(fba_result.uptake_fluxes) > 0
```

---

## References

- **Full Compatibility Guide**: `specs-source/references/MODELSEEDPY_COBRAPY_COMPATIBILITY_GUIDE.md`
- **Spec 002**: Data formats and compartment notation
- **Spec 003**: Build media tool specification
- **Spec 005**: Gapfill model tool specification (FIXED)
- **Spec 006**: Run FBA tool specification

---

## Changelog

### 2025-10-27
- Initial document created
- Fixed spec 005 line 1194 compartment suffix pattern
- Documented three critical integration patterns
- Added implementation status tracking
