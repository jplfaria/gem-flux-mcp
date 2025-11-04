#!/usr/bin/env python3
"""Check that all imports in test files are actually available.

This script validates that imports in test files like:
    from gem_flux_mcp.tools import GetCompoundNameRequest
are actually exported by the module (__all__ list).

This prevents import errors that only appear during test collection.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple, Set


def extract_imports(test_file: Path) -> List[Tuple[str, List[str]]]:
    """Extract all 'from X import Y' statements from a test file.

    Returns:
        List of (module, [imported_names]) tuples
    """
    try:
        with open(test_file, 'r') as f:
            content = f.read()
            tree = ast.parse(content, filename=str(test_file))
    except SyntaxError:
        # Skip files with syntax errors (might be incomplete)
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith('gem_flux_mcp'):
                imported_names = []
                for alias in node.names:
                    if alias.name == '*':
                        continue
                    # Skip imports that look like submodules (lowercase)
                    # e.g., "from gem_flux_mcp.storage import initialization"
                    # This is a module import, not a function/class import
                    if not alias.name.islower() or alias.name.startswith('_'):
                        # Likely a class or function (CamelCase or _private)
                        imported_names.append(alias.name)
                    else:
                        # Check if it's actually a function/class by looking at usage
                        # For now, assume lowercase = module, CamelCase/snake_case with _ = function
                        # This heuristic: if it has underscore OR starts uppercase, it's a symbol
                        if '_' in alias.name or alias.name[0].isupper():
                            imported_names.append(alias.name)
                        # else: skip, likely a module import

                if imported_names:
                    imports.append((node.module, imported_names))

    return imports


def get_module_exports(module_path: str) -> Set[str]:
    """Get the __all__ list from a module's __init__.py.

    Returns:
        Set of exported names, or None if __all__ not found
    """
    # Convert module path to file path
    # gem_flux_mcp.tools -> src/gem_flux_mcp/tools/__init__.py
    parts = module_path.split('.')
    init_file = Path('src') / Path(*parts) / '__init__.py'

    if not init_file.exists():
        return None

    try:
        with open(init_file, 'r') as f:
            tree = ast.parse(f.read(), filename=str(init_file))
    except SyntaxError:
        return None

    # Find __all__ assignment
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '__all__':
                    # Extract list elements
                    if isinstance(node.value, ast.List):
                        exports = set()
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant):
                                exports.add(elt.value)
                        return exports

    return None


def check_test_imports(test_dir: Path) -> Tuple[bool, List[str]]:
    """Check all test files for import issues.

    Returns:
        (success, error_messages)
    """
    errors = []

    # Find all test files
    test_files = list(test_dir.rglob('test_*.py'))

    for test_file in test_files:
        imports = extract_imports(test_file)

        for module, imported_names in imports:
            exports = get_module_exports(module)

            if exports is None:
                # Module doesn't have __all__, skip (might be fine)
                continue

            # Check if all imported names are in exports
            missing = [name for name in imported_names if name not in exports]

            if missing:
                try:
                    rel_path = test_file.relative_to(Path.cwd())
                except ValueError:
                    rel_path = test_file
                errors.append(
                    f"{rel_path}: imports {missing} from {module} "
                    f"but they're not in __all__"
                )

    return len(errors) == 0, errors


def main():
    """Main entry point."""
    test_dir = Path('tests')

    if not test_dir.exists():
        print("No tests directory found - skipping import check")
        return 0

    success, errors = check_test_imports(test_dir)

    if success:
        print("✅ All test imports are properly exported")
        return 0
    else:
        print("❌ Test import issues found:\n")
        for error in errors:
            print(f"  • {error}")
        print("\n💡 Fix: Export missing names in module's __all__ list")
        return 1


if __name__ == '__main__':
    sys.exit(main())
