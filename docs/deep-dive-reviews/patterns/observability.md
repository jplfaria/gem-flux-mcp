# Pattern: Observability and Error Classification

**Discovered**: Session 2 (Iteration 8)
**Frequency**: Common in cleanup/resource management code
**Status**: ⚠️ Template established, apply to file operations

## Problem

Bare `except` blocks silently swallow ALL exceptions, making debugging impossible:

```python
try:
    os.unlink(fasta_path)
except Exception:
    pass  # ❌ What happened? Why did it fail?
```

**Issues**:
- No visibility into success vs failure
- Can't distinguish expected errors (file already deleted) from unexpected errors (permission issues, disk full)
- Debugging file system issues is impossible
- Silent failures hide real problems

## Solution: Three-Tier Error Handling

Classify exceptions and log appropriately:

```python
try:
    os.unlink(fasta_path)
    logger.debug(f"Cleaned up temporary FASTA file: {fasta_path}")
except FileNotFoundError:
    pass  # Already deleted, that's fine
except Exception as e:
    # Log but don't raise - cleanup failure shouldn't break the tool
    logger.warning(f"Failed to clean up temporary file {fasta_path}: {e}")
```

## Three Tiers

### Tier 1: Success (Debug Level)
```python
logger.debug("Operation succeeded")
```

**When to use**:
- Normal operation completed successfully
- Not important for production logs
- Useful for development/troubleshooting

### Tier 2: Expected Failure (Pass Silently)
```python
except FileNotFoundError:
    pass  # Expected - file already deleted
```

**When to use**:
- Error is expected and harmless
- System is designed to handle this gracefully
- No action needed from user/developer

### Tier 3: Unexpected Failure (Warning/Error)
```python
except Exception as e:
    logger.warning(f"Unexpected error: {e}")
```

**When to use**:
- Error is unexpected but non-fatal
- System can continue but user should know
- Helps diagnose issues in production

## Common Scenarios

### File Cleanup
```python
finally:
    try:
        os.unlink(temp_file)
        logger.debug(f"Cleaned up temporary file: {temp_file}")
    except FileNotFoundError:
        pass  # Already deleted
    except Exception as e:
        logger.warning(f"Failed to clean up {temp_file}: {e}")
```

### Resource Initialization
```python
try:
    resource = initialize_resource()
    logger.info(f"Initialized {resource.name}")
except ResourceNotAvailableError:
    logger.warning("Resource unavailable, using fallback")
    resource = fallback_resource()
except Exception as e:
    logger.error(f"Failed to initialize resource: {e}")
    raise
```

### Optional Features
```python
try:
    enable_optional_feature()
    logger.debug("Optional feature enabled")
except FeatureNotSupportedError:
    logger.info("Optional feature not available, continuing without it")
except Exception as e:
    logger.warning(f"Error enabling optional feature: {e}")
    # Continue without feature
```

## Logging Level Guidelines

| Level | When to Use | Example |
|-------|-------------|---------|
| `DEBUG` | Success, detailed operations | "Cleaned up temp file" |
| `INFO` | Important milestones | "Database loaded with 5000 compounds" |
| `WARNING` | Unexpected but non-fatal | "Failed to clean up temp file" |
| `ERROR` | Fatal errors | "Database not found, cannot continue" |

## Benefits

1. **Visibility**: Know what succeeded and what failed
2. **Classification**: Distinguish expected from unexpected errors
3. **Debugging**: Can diagnose production issues from logs
4. **Graceful Degradation**: System continues but user is informed

## Anti-Patterns to Avoid

### ❌ Bare Pass
```python
except Exception:
    pass  # Silent failure
```

### ❌ Logging Without Classification
```python
except Exception as e:
    logger.error(f"Error: {e}")  # Is this fatal? Expected?
```

### ❌ Wrong Log Level
```python
except FileNotFoundError:
    logger.error("File not found")  # This is expected!
```

## Loop Improvement Opportunity

The implementation loop could:
1. Detect bare `except` blocks
2. Template file cleanup operations with three-tier handling
3. Suggest appropriate log levels based on context

## Related Files

- Example: `src/gem_flux_mcp/tools/build_model.py:333-343`
- Session: [Session 2](../sessions/session-02-iteration-08.md)

## Impact

**Session 2 Impact**:
- Improved debugging capability
- Classified exceptions appropriately
- Established logging pattern for resource management
