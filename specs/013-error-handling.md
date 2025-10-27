# Error Handling and Validation Specification - Gem-Flux MCP Server

**Type**: Cross-Cutting Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding system architecture)
- Read: 002-data-formats.md (for data structure details)
- Read: 003-build-media-tool.md through 012-complete-workflow.md (for tool-specific error conditions)

## Purpose

This specification defines error handling patterns, validation strategies, and error response formats for the Gem-Flux MCP Server. It ensures that all tools provide consistent, informative error messages that help LLMs and users understand failures and recover gracefully. The specification covers input validation, biological plausibility checks, library error handling, and helpful suggestions for error recovery.

## Error Response Format

### JSON-RPC Error Compatibility

The Gem-Flux MCP Server uses the Model Context Protocol (MCP), which is based on JSON-RPC 2.0. Error responses follow JSON-RPC conventions while adding domain-specific fields for metabolic modeling.

**JSON-RPC Error Codes** (Standard):
- `-32700`: Parse error (invalid JSON)
- `-32600`: Invalid request (malformed JSON-RPC)
- `-32601`: Method not found (tool doesn't exist)
- `-32602`: Invalid params (parameter validation failed)
- `-32603`: Internal error (server-side exception)
- `-32000 to -32099`: Server-defined errors (application-specific)

**Application Error Codes** (Custom):
- `-32000`: Validation error (input validation failed)
- `-32001`: Not found error (resource not found)
- `-32002`: Infeasibility error (model/gapfill infeasible)
- `-32003`: Library error (ModelSEEDpy/COBRApy exception)
- `-32004`: Database error (compound/reaction lookup failed)
- `-32005`: Timeout error (operation exceeded time limit)

### Standard Error Response Structure

All tools return errors in a consistent format that enables LLMs to understand and potentially recover from failures:

```json
{
  "success": false,
  "error_type": "validation_error",
  "jsonrpc_error_code": -32000,
  "error_code": "INVALID_COMPOUND_IDS",
  "jsonrpc_error_code": -32000,
  "message": "Invalid compound IDs provided",
  "details": {
    "invalid_ids": ["cpd99999", "cpd00ABC"],
    "valid_ids": ["cpd00027", "cpd00007"],
    "total_invalid": 2,
    "total_valid": 2
  },
  "suggestions": [
    "Verify compound IDs against ModelSEED database using search_compounds tool",
    "Check for typos in compound IDs",
    "Use get_compound_name to validate individual IDs"
  ],
  "tool_name": "build_media",
  "timestamp": "2025-10-27T14:32:15Z"
}
```

### Error Response Fields

**success** (required)
- Type: Boolean
- Value: Always `false` for error responses
- Purpose: Quick check for operation success

**error_type** (required)
- Type: String
- Purpose: High-level categorization of error
- Values:
  - `"validation_error"`: Input validation failed
  - `"not_found_error"`: Resource not found (model_id, media_id, etc.)
  - `"infeasibility_error"`: Model or gapfilling infeasible
  - `"library_error"`: ModelSEEDpy or COBRApy error
  - `"database_error"`: ModelSEED database lookup failed
  - `"server_error"`: Internal server error
  - `"timeout_error"`: Operation exceeded time limit

**error_code** (required)
- Type: String
- Format: UPPERCASE_SNAKE_CASE
- Purpose: Specific error identification for programmatic handling
- Examples: `"INVALID_COMPOUND_IDS"`, `"MODEL_NOT_FOUND"`, `"GAPFILL_INFEASIBLE"`

**jsonrpc_error_code** (required)
- Type: Integer
- Format: Negative integer in range -32768 to -32000
- Purpose: JSON-RPC 2.0 compatible error code for MCP protocol
- Mapping to error_type:
  - `validation_error` → `-32000`
  - `not_found_error` → `-32001`
  - `infeasibility_error` → `-32002`
  - `library_error` → `-32003`
  - `database_error` → `-32004`
  - `timeout_error` → `-32005`
- Standard JSON-RPC codes:
  - Parse/protocol errors: `-32700`, `-32600`, `-32601`, `-32602`, `-32603`

**message** (required)
- Type: String
- Purpose: Human-readable error summary
- Guidelines: Clear, concise, actionable
- Length: 1-2 sentences
- Example: "Gapfilling failed to find solution enabling growth in specified media"

**details** (optional)
- Type: Object
- Purpose: Structured error details for LLM interpretation
- Contents: Varies by error type
- Examples:
  - Invalid IDs list
  - Missing resources list
  - Solver status information
  - Constraint violations

**suggestions** (optional)
- Type: Array of strings
- Purpose: Actionable recovery steps for LLMs
- Guidelines: Specific tool calls or parameter changes
- Examples:
  - "Try gapfilling with higher complexity_threshold"
  - "Verify media contains carbon source using get_compound_name"
  - "Check if model has biomass reaction using export_model_json"

**tool_name** (required)
- Type: String
- Purpose: Identifies which tool produced the error
- Values: Tool name (e.g., "build_media", "run_fba")

**timestamp** (required)
- Type: String (ISO 8601 format)
- Purpose: Error occurrence time for debugging
- Format: "YYYY-MM-DDTHH:MM:SSZ"

## Validation Strategy

### Input Validation Hierarchy

All tools follow a three-stage validation approach:

**Stage 1: Type and Format Validation**
- Check parameter types (string, number, boolean, array, object)
- Validate format patterns (compound IDs, reaction IDs)
- Verify required parameters present
- Check numeric ranges (e.g., bounds, thresholds)
- Performed BEFORE any processing

**Stage 2: Reference Validation**
- Verify compound/reaction IDs exist in ModelSEED database
- Check model_id and media_id exist in session
- Validate protein sequence formats (amino acid alphabet)
- Confirm template names are valid
- Performed AFTER type validation, BEFORE library calls

**Stage 3: Biological Plausibility Validation** (optional, future)
- Check media contains carbon source
- Verify biomass reaction exists
- Validate flux magnitudes are reasonable
- Alert on unusual patterns (not errors)
- Performed AFTER operation completes

### Validation Timing

**Pre-validation** (before operation):
- All required parameters present
- All parameters correct type
- All IDs properly formatted
- All references exist

**Mid-validation** (during operation):
- Library calls succeed
- Intermediate results valid
- Resource constraints not exceeded

**Post-validation** (after operation):
- Results biologically plausible
- Output format correct
- Session state consistent

## Common Error Patterns

### 1. Invalid Compound IDs (build_media)

**Error Type**: `validation_error`
**Error Code**: `INVALID_COMPOUND_IDS`

**Trigger Conditions**:
- Compound ID doesn't match pattern `cpd\d{5}`
- Compound ID not found in ModelSEED database
- Empty compounds array

**Response Example**:
```json
{
  "success": false,
  "error_type": "validation_error",
  "jsonrpc_error_code": -32000,
  "error_code": "INVALID_COMPOUND_IDS",
  "jsonrpc_error_code": -32000,
  "message": "2 compound IDs not found in ModelSEED database",
  "details": {
    "invalid_ids": ["cpd99999", "cpd00ABC"],
    "valid_ids": ["cpd00027", "cpd00007", "cpd00001"],
    "total_provided": 5,
    "total_invalid": 2
  },
  "suggestions": [
    "Use search_compounds tool to find correct compound IDs",
    "Common compounds: cpd00027 (glucose), cpd00007 (O2), cpd00001 (H2O)",
    "Check for typos in compound IDs"
  ],
  "tool_name": "build_media",
  "timestamp": "2025-10-27T14:32:15Z"
}
```

### 2. Model Not Found (run_fba, gapfill_model)

**Error Type**: `not_found_error`
**Error Code**: `MODEL_NOT_FOUND`

**Trigger Conditions**:
- model_id doesn't exist in current session
- model_id is empty string
- Session has no models

**Response Example**:
```json
{
  "success": false,
  "error_type": "not_found_error",
  "error_code": "MODEL_NOT_FOUND",
  "jsonrpc_error_code": -32001,
  "message": "Model 'model_xyz' not found in current session",
  "details": {
    "requested_id": "model_xyz",
    "available_models": [
      "model_20251027_a1b2c3",
      "model_20251027_d4e5f6.gf"
    ],
    "num_available": 2
  },
  "suggestions": [
    "Use build_model tool to create a new model",
    "Check model_id spelling",
    "Available models listed in details.available_models"
  ],
  "tool_name": "run_fba",
  "timestamp": "2025-10-27T14:35:22Z"
}
```

### 3. Gapfilling Infeasible

**Error Type**: `infeasibility_error`
**Error Code**: `GAPFILL_INFEASIBLE`

**Trigger Conditions**:
- No combination of template reactions enables growth
- Target growth rate unachievable
- Media missing essential nutrients
- Model fundamentally incomplete

**Response Example**:
```json
{
  "success": false,
  "error_type": "infeasibility_error",
  "jsonrpc_error_code": -32002,
  "error_code": "GAPFILL_INFEASIBLE",
  "jsonrpc_error_code": -32002,
  "message": "Gapfilling could not find solution to enable growth in specified media",
  "details": {
    "model_id": "model_20251027_a1b2c3",
    "media_id": "media_20251027_x9y8z7",
    "target_growth": 0.01,
    "max_complexity": 10,
    "media_compounds": 15,
    "template_reactions_available": 4523
  },
  "suggestions": [
    "Verify media contains carbon source (glucose, acetate, etc.)",
    "Try increasing max_complexity parameter",
    "Check media with get_compound_name for each compound",
    "Try complete media (LB, M9+aa) instead of minimal media",
    "Verify model has biomass reaction using export_model_json"
  ],
  "tool_name": "gapfill_model",
  "timestamp": "2025-10-27T14:40:11Z"
}
```

### 4. FBA Infeasible

**Error Type**: `infeasibility_error`
**Error Code**: `FBA_INFEASIBLE`

**Trigger Conditions**:
- Linear programming problem has no solution
- Media too restrictive
- Model constraints contradictory
- Objective reaction cannot carry flux

**Response Example**:
```json
{
  "success": false,
  "error_type": "infeasibility_error",
  "jsonrpc_error_code": -32002,
  "error_code": "FBA_INFEASIBLE",
  "message": "FBA optimization failed - model infeasible in specified media",
  "details": {
    "model_id": "model_20251027_a1b2c3.gf",
    "media_id": "media_20251027_x9y8z7",
    "objective": "bio1",
    "solver_status": "infeasible",
    "num_reactions": 860,
    "num_metabolites": 781,
    "num_exchange_reactions": 123
  },
  "suggestions": [
    "Verify media contains essential nutrients (C, N, P, S sources)",
    "Check exchange reaction bounds are not too restrictive",
    "Try gapfilling model first if not already gapfilled",
    "Use get_compound_name to verify media composition",
    "Export model and check biomass reaction composition"
  ],
  "tool_name": "run_fba",
  "timestamp": "2025-10-27T14:45:33Z"
}
```

### 5. Invalid Protein Sequences

**Error Type**: `validation_error`
**Error Code**: `INVALID_PROTEIN_SEQUENCES`

**Trigger Conditions**:
- Sequence contains non-amino acid characters
- Empty sequence
- Empty protein_sequences dictionary
- Sequence IDs invalid format

**Response Example**:
```json
{
  "success": false,
  "error_type": "validation_error",
  "jsonrpc_error_code": -32000,
  "error_code": "INVALID_PROTEIN_SEQUENCES",
  "message": "2 protein sequences contain invalid characters",
  "details": {
    "invalid_sequences": {
      "prot_001": "Contains invalid character 'X' at position 45",
      "prot_003": "Empty sequence"
    },
    "valid_sequences": ["prot_002", "prot_004", "prot_005"],
    "total_sequences": 5,
    "total_invalid": 2,
    "allowed_characters": "ACDEFGHIKLMNPQRSTVWY"
  },
  "suggestions": [
    "Use standard amino acid alphabet: ACDEFGHIKLMNPQRSTVWY",
    "Remove sequences with ambiguous residues (X, B, Z)",
    "Verify sequences are protein (not DNA/RNA)",
    "Check for empty sequences"
  ],
  "tool_name": "build_model",
  "timestamp": "2025-10-27T14:50:44Z"
}
```

### 6. ModelSEEDpy Library Error

**Error Type**: `library_error`
**Error Code**: `MODELSEEDPY_ERROR`

**Trigger Conditions**:
- MSBuilder initialization fails
- MSGapfill raises exception
- MSMedia creation fails
- Template loading error

**Response Example**:
```json
{
  "success": false,
  "error_type": "library_error",
  "jsonrpc_error_code": -32003,
  "error_code": "MODELSEEDPY_ERROR",
  "message": "ModelSEEDpy library error during model building",
  "details": {
    "library": "ModelSEEDpy",
    "operation": "MSBuilder.build_base_model",
    "exception_type": "ValueError",
    "exception_message": "Template GramNegative not found",
    "template_requested": "GramNegative"
  },
  "suggestions": [
    "Verify template name is valid: GramNegative, GramPositive, Core",
    "Check ModelSEEDpy templates loaded correctly at server startup",
    "Restart server if templates failed to load",
    "Check server logs for template loading errors"
  ],
  "tool_name": "build_model",
  "timestamp": "2025-10-27T14:55:12Z"
}
```

### 7. COBRApy Solver Error

**Error Type**: `library_error`
**Error Code**: `COBRAPY_SOLVER_ERROR`

**Trigger Conditions**:
- Linear programming solver failure
- Solver not installed
- Numerical instability
- Solver timeout

**Response Example**:
```json
{
  "success": false,
  "error_type": "library_error",
  "jsonrpc_error_code": -32003,
  "error_code": "COBRAPY_SOLVER_ERROR",
  "message": "COBRApy solver failed during optimization",
  "details": {
    "library": "COBRApy",
    "operation": "model.optimize",
    "solver": "glpk",
    "exception_type": "OptimizationError",
    "exception_message": "Solver status: numerical_error"
  },
  "suggestions": [
    "Try different solver if available (CPLEX, Gurobi, GLPK)",
    "Check model for numerical instability (very large/small coefficients)",
    "Verify model is well-formed using export_model_json",
    "Contact support if error persists"
  ],
  "tool_name": "run_fba",
  "timestamp": "2025-10-27T15:00:28Z"
}
```

### 8. Database Lookup Error

**Error Type**: `database_error`
**Error Code**: `COMPOUND_NOT_FOUND`

**Trigger Conditions**:
- Compound ID not in compounds.tsv
- Database not loaded
- Database file corrupted

**Response Example**:
```json
{
  "success": false,
  "error_type": "database_error",
  "jsonrpc_error_code": -32004,
  "error_code": "COMPOUND_NOT_FOUND",
  "message": "Compound 'cpd99999' not found in ModelSEED database",
  "details": {
    "requested_id": "cpd99999",
    "database": "compounds.tsv",
    "total_compounds": 33993,
    "similar_ids": ["cpd00999", "cpd09999"]
  },
  "suggestions": [
    "Use search_compounds to find correct ID",
    "Check for typos in compound ID",
    "Verify compound exists in ModelSEED database",
    "Similar IDs listed in details.similar_ids"
  ],
  "tool_name": "get_compound_name",
  "timestamp": "2025-10-27T15:05:41Z"
}
```

## Tool-Specific Error Handling

### build_media Tool Errors

**Error Codes**:
- `INVALID_COMPOUND_IDS`: One or more compound IDs invalid
- `EMPTY_COMPOUNDS_LIST`: No compounds provided
- `INVALID_BOUNDS_FORMAT`: custom_bounds has invalid format
- `BOUNDS_OUT_OF_ORDER`: lower_bound >= upper_bound
- `NEGATIVE_UPTAKE`: default_uptake is negative
- `COMPOUND_NOT_IN_LIST`: custom_bounds key not in compounds list

**Validation Order**:
1. Check compounds array not empty
2. Validate all compound ID formats
3. Check all compound IDs exist in database
4. Validate default_uptake > 0
5. Validate custom_bounds format
6. Check all custom_bounds keys in compounds list
7. Verify all bounds: lower < upper

### build_model Tool Errors

**Error Codes**:
- `INVALID_PROTEIN_SEQUENCES`: Sequences contain non-amino acids
- `EMPTY_PROTEIN_SEQUENCES`: No sequences provided
- `INVALID_TEMPLATE_NAME`: Template not found
- `MODELSEEDPY_ERROR`: MSBuilder or MSGenome error
- `RAST_UNAVAILABLE`: RAST annotation requested but unavailable (offline mode)

**Validation Order**:
1. Check protein_sequences not empty
2. Validate all sequence IDs
3. Check all sequences contain only valid amino acids
4. Validate template name
5. Verify template loaded
6. Check RAST availability if requested

### gapfill_model Tool Errors

**Error Codes**:
- `MODEL_NOT_FOUND`: model_id not in session
- `MEDIA_NOT_FOUND`: media_id not in session
- `GAPFILL_INFEASIBLE`: No gapfilling solution found
- `INVALID_TARGET_GROWTH`: target_growth negative or too high
- `TEMPLATE_NOT_LOADED`: Gapfill template not available
- `MAX_COMPLEXITY_EXCEEDED`: Solution requires too many reactions

**Validation Order**:
1. Check model_id exists
2. Check media_id exists
3. Validate target_growth > 0
4. Check max_complexity reasonable
5. Verify template loaded
6. Attempt gapfilling
7. Check solution feasibility

### run_fba Tool Errors

**Error Codes**:
- `MODEL_NOT_FOUND`: model_id not in session
- `MEDIA_NOT_FOUND`: media_id not in session
- `OBJECTIVE_NOT_FOUND`: Objective reaction not in model
- `FBA_INFEASIBLE`: No feasible solution
- `FBA_UNBOUNDED`: Objective unbounded
- `COBRAPY_SOLVER_ERROR`: Solver failure
- `INVALID_FLUX_THRESHOLD`: threshold negative

**Validation Order**:
1. Check model_id exists
2. Check media_id exists
3. Validate objective reaction exists
4. Check flux_threshold >= 0
5. Apply media constraints
6. Run optimization
7. Check solution status
8. Validate solution quality

### Database Lookup Tool Errors

**Error Codes (get_compound_name, get_reaction_name)**:
- `COMPOUND_NOT_FOUND`: Compound ID not in database
- `REACTION_NOT_FOUND`: Reaction ID not in database
- `INVALID_ID_FORMAT`: ID doesn't match expected pattern
- `DATABASE_NOT_LOADED`: Database files not loaded

**Error Codes (search_compounds, search_reactions)**:
- `EMPTY_QUERY`: Search query is empty
- `INVALID_LIMIT`: Limit not positive integer
- `DATABASE_NOT_LOADED`: Database files not loaded

**Validation Order**:
1. Check database loaded
2. Validate ID format
3. Check ID exists in database
4. Return data or error

## Error Recovery Patterns

### LLM Error Recovery Guidelines

When an error occurs, LLMs should:

**Step 1: Understand the Error**
- Read error_type and error_code
- Examine error message
- Review details for specifics

**Step 2: Check Suggestions**
- Follow suggestions in order
- Use suggested tool calls
- Modify parameters as recommended

**Step 3: Retry with Corrections**
- Apply fixes from suggestions
- Re-run with corrected parameters
- Monitor for different errors

**Step 4: Escalate if Unrecoverable**
- Report to user if suggestions don't work
- Provide error details for debugging
- Suggest manual intervention

### Example Recovery Scenarios

**Scenario 1: Invalid Compound ID**
1. Error: `INVALID_COMPOUND_IDS` with cpd99999
2. Suggestion: "Use search_compounds tool"
3. LLM calls: `search_compounds(query="glucose")`
4. Find correct ID: cpd00027
5. Retry: `build_media` with cpd00027
6. Success

**Scenario 2: Gapfilling Infeasible**
1. Error: `GAPFILL_INFEASIBLE` on minimal media
2. Suggestion: "Verify media contains carbon source"
3. LLM calls: `get_compound_name` for each media compound
4. Find missing nitrogen source
5. Retry: `build_media` with complete nutrients
6. Retry: `gapfill_model` with new media
7. Success

**Scenario 3: FBA Infeasible on Gapfilled Model**
1. Error: `FBA_INFEASIBLE` after gapfilling
2. Unexpected (gapfilled models should grow)
3. LLM calls: `export_model_json` to inspect model
4. Check exchange reactions and biomass
5. Report to user: "Unexpected FBA failure after successful gapfill"
6. Suggest: Re-run gapfilling or check media

## Validation Helpers

### Input Validation Patterns

**Compound ID Validation**:
- Pattern: `cpd\d{5}`
- Example valid: "cpd00027", "cpd00001"
- Example invalid: "cpd27", "CPD00027", "compound_027"

**Reaction ID Validation**:
- Pattern: `rxn\d{5}`
- Example valid: "rxn00148", "rxn05459"
- Example invalid: "rxn148", "RXN00148", "reaction_148"

**Exchange Reaction Pattern**:
- Format: `EX_{compound_id}_{compartment}`
- Example: "EX_cpd00027_e0", "EX_cpd00007_e0"

**Protein Sequence Validation**:
- Allowed characters: ACDEFGHIKLMNPQRSTVWY
- Minimum length: 10 amino acids (typical)
- Maximum length: 10,000 amino acids (practical limit)

**Bounds Validation**:
- Format: [lower, upper] where lower < upper
- Uptake: negative lower bound (e.g., -10)
- Secretion: positive upper bound (e.g., 100)
- Blocked: [0, 0]

### Biological Plausibility Checks (Future)

These are warnings, not errors:

**Media Plausibility**:
- Contains at least one carbon source
- Contains nitrogen source
- Contains essential elements (P, S)
- Has electron acceptor (O2, NO3, SO4)

**Model Plausibility**:
- Has biomass reaction
- Has exchange reactions
- Has at least 100 reactions (typical)
- Growth rate 0.1-2.0 hr^-1 (typical range)

**Flux Plausibility**:
- No single flux > 1000 mmol/gDW/h
- Uptake fluxes negative
- Secretion fluxes positive
- Biomass flux reasonable (< 5 hr^-1)

## Error Logging

### Server-Side Logging

All errors should be logged with:

**Error Log Entry**:
```json
{
  "timestamp": "2025-10-27T15:15:22Z",
  "level": "ERROR",
  "tool_name": "gapfill_model",
  "error_type": "infeasibility_error",
  "jsonrpc_error_code": -32002,
  "error_code": "GAPFILL_INFEASIBLE",
  "message": "Gapfilling failed for model_xyz in media_abc",
  "details": {
    "model_id": "model_xyz",
    "media_id": "media_abc",
    "target_growth": 0.01
  },
  "stack_trace": "...",
  "session_id": "session_123"
}
```

**Log Levels**:
- `ERROR`: Operation failed
- `WARNING`: Operation succeeded but with concerns
- `INFO`: Normal operation
- `DEBUG`: Detailed debugging information

**What to Log**:
- All validation errors
- All library errors
- All infeasibility errors
- Recovery attempts
- Performance issues (slow operations)

**What NOT to Log**:
- User credentials (future: when auth added)
- Full model data (too large)
- Sensitive biological sequences (if applicable)

## Error Message Guidelines

### Writing Good Error Messages

**DO**:
- Be specific about what went wrong
- Explain why it went wrong if known
- Suggest specific recovery actions
- Include relevant details
- Use clear, simple language
- Reference tools that can help

**DON'T**:
- Use technical jargon without explanation
- Blame the user
- Be vague ("Something went wrong")
- Hide error details
- Suggest impossible solutions
- Omit context

### Example Good vs Bad Messages

**Bad**: "Error occurred"
**Good**: "Gapfilling failed to find solution enabling growth in specified media. Try increasing max_complexity or adding more nutrients to media."

**Bad**: "Invalid input"
**Good**: "2 compound IDs not found in ModelSEED database: cpd99999, cpd00ABC. Use search_compounds tool to find correct IDs."

**Bad**: "Model error"
**Good**: "Model 'model_xyz' not found in current session. Available models: model_abc, model_def. Use build_model to create a new model."

**Bad**: "FBA failed"
**Good**: "FBA optimization failed - model infeasible in specified media. Verify media contains essential nutrients (C, N, P, S sources) using get_compound_name."

## Testing Error Handling

### Error Handling Test Cases

Each tool must have tests for:

**Validation Errors**:
- Empty required parameters
- Invalid parameter types
- Invalid ID formats
- Out-of-range values
- Missing references

**Infeasibility Errors**:
- Gapfilling on impossible media
- FBA on infeasible model
- Contradictory constraints

**Library Errors**:
- ModelSEEDpy exceptions
- COBRApy exceptions
- Template loading failures
- Solver failures

**Database Errors**:
- Invalid compound IDs
- Invalid reaction IDs
- Database not loaded

**Recovery Tests**:
- LLM can understand error
- LLM can follow suggestions
- Retry succeeds after correction

### Test Coverage Requirements

- All error codes must have test cases
- All suggestions must be testable
- All recovery patterns must be validated
- Error messages must be clear to humans and LLMs

## Summary

### Key Principles

1. **Consistency**: All tools use same error format
2. **Clarity**: Error messages are clear and actionable
3. **Recovery**: Suggestions enable LLM error recovery
4. **Detail**: Enough information to understand and fix
5. **Validation**: Catch errors early with thorough validation
6. **Logging**: All errors logged for debugging

### Error Handling Checklist

For each tool implementation:
- [ ] Define all possible error codes
- [ ] Implement validation in correct order
- [ ] Return errors in standard format
- [ ] Provide actionable suggestions
- [ ] Include relevant details
- [ ] Log errors appropriately
- [ ] Test all error paths
- [ ] Verify LLMs can recover

### Integration with Other Specifications

This specification works with:
- **Tool specifications**: Defines errors for each tool
- **Data formats**: Specifies error response format
- **Complete workflow**: Shows error recovery in context
- **Installation**: Covers server startup errors
- **MCP server setup**: Defines server-level errors

---

**Document Status**: Complete
**Last Updated**: 2025-10-27
**Next Review**: After implementation testing
