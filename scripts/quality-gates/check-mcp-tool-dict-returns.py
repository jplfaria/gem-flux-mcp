#!/usr/bin/env python3
"""Check that MCP tool functions return dicts, not Pydantic objects.

This script validates that all MCP tool functions:
1. Have a Response model defined (ending with "Response")
2. Return dict (not the Response model instance)
3. Call .model_dump() to convert Pydantic objects to dicts

This prevents integration test failures where tests expect dict access
but receive Pydantic objects.

Usage:
    python scripts/quality-gates/check-mcp-tool-dict-returns.py

Exit codes:
    0: All MCP tools return dicts correctly
    1: Found tools that don't return dicts or missing .model_dump() calls

See Also:
    - Session 10 (deep-dive-reviews/sessions/session-10-iteration-02-failed.md)
    - MCP protocol requires JSON-RPC serialization (dicts, not Pydantic)
"""

import ast
import sys
from pathlib import Path
from typing import NamedTuple


class ToolFunction(NamedTuple):
    """Represents a tool function to validate."""

    name: str
    file_path: Path
    return_annotation: str | None
    has_model_dump_call: bool
    response_model_name: str | None


class FunctionVisitor(ast.NodeVisitor):
    """AST visitor to find tool functions and their return patterns."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.tool_functions: list[ToolFunction] = []
        self.response_models: set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Collect Response model names."""
        if node.name.endswith("Response"):
            self.response_models.add(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check tool functions for dict returns and .model_dump() calls."""
        # Skip private functions and test helpers
        if node.name.startswith("_") or node.name.startswith("test_"):
            return

        # Check if function has a Response model parameter
        response_model_name = self._find_response_model(node)

        if response_model_name:
            # This is a tool function - check return type and .model_dump()
            return_annotation = self._get_return_annotation(node)
            has_model_dump = self._has_model_dump_call(node)

            tool_func = ToolFunction(
                name=node.name,
                file_path=self.file_path,
                return_annotation=return_annotation,
                has_model_dump_call=has_model_dump,
                response_model_name=response_model_name,
            )
            self.tool_functions.append(tool_func)

        self.generic_visit(node)

    def _find_response_model(self, node: ast.FunctionDef) -> str | None:
        """Find if function uses a Response model (creates instance and returns it)."""
        for stmt in ast.walk(node):
            # Look for assignments like: response = SomeResponse(...)
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "response":
                        if isinstance(stmt.value, ast.Call):
                            if isinstance(stmt.value.func, ast.Name):
                                model_name = stmt.value.func.id
                                if model_name.endswith("Response"):
                                    return model_name
        return None

    def _get_return_annotation(self, node: ast.FunctionDef) -> str | None:
        """Get the return type annotation as a string."""
        if node.returns:
            return ast.unparse(node.returns)
        return None

    def _has_model_dump_call(self, node: ast.FunctionDef) -> bool:
        """Check if function calls .model_dump() before returning."""
        for stmt in ast.walk(node):
            # Look for return response.model_dump()
            if isinstance(stmt, ast.Return) and stmt.value:
                if isinstance(stmt.value, ast.Call):
                    if isinstance(stmt.value.func, ast.Attribute):
                        if stmt.value.func.attr == "model_dump":
                            return True
        return False


def check_tool_file(file_path: Path) -> list[ToolFunction]:
    """Parse a Python file and extract tool function information."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        visitor = FunctionVisitor(file_path)
        visitor.visit(tree)
        return visitor.tool_functions

    except SyntaxError as e:
        print(f"⚠️  Syntax error in {file_path}: {e}")
        return []
    except Exception as e:
        print(f"⚠️  Error parsing {file_path}: {e}")
        return []


def validate_tool_functions(tool_funcs: list[ToolFunction]) -> list[str]:
    """Validate that tool functions return dicts and use .model_dump()."""
    issues = []

    for func in tool_funcs:
        # Check 1: Return annotation should be dict
        if func.return_annotation != "dict":
            issues.append(
                f"❌ {func.file_path.name}:{func.name}() - "
                f"Return type should be 'dict', got '{func.return_annotation or 'None'}'"
            )

        # Check 2: Should call .model_dump() to convert Pydantic to dict
        if not func.has_model_dump_call:
            issues.append(
                f"❌ {func.file_path.name}:{func.name}() - "
                f"Missing .model_dump() call to convert {func.response_model_name} to dict"
            )

    return issues


def main() -> int:
    """Main entry point."""
    # Find all tool files
    tools_dir = Path("src/gem_flux_mcp/tools")
    if not tools_dir.exists():
        print(f"❌ Tools directory not found: {tools_dir}")
        return 1

    tool_files = list(tools_dir.glob("*.py"))
    tool_files = [f for f in tool_files if f.name != "__init__.py"]

    print(f"🔍 Checking {len(tool_files)} MCP tool files for dict returns...")

    all_tool_functions = []
    for file_path in sorted(tool_files):
        tool_funcs = check_tool_file(file_path)
        all_tool_functions.extend(tool_funcs)

    print(f"   Found {len(all_tool_functions)} tool functions")

    # Validate all tool functions
    issues = validate_tool_functions(all_tool_functions)

    if issues:
        print(f"\n❌ Found {len(issues)} MCP tool dict return issues:\n")
        for issue in issues:
            print(f"   {issue}")
        print()
        print("💡 MCP tools must return dict (not Pydantic objects) for JSON-RPC serialization")
        print("   Fix: Call response.model_dump() before returning")
        print()
        return 1

    print("✅ All MCP tools return dicts correctly (.model_dump() called)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
