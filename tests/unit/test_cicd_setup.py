"""Unit tests for CI/CD setup validation.

Tests verify that all GitHub Actions workflows are properly configured
and that the CI/CD infrastructure is complete.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml


class TestCICDSetup:
    """Test suite for CI/CD pipeline setup."""

    @pytest.fixture
    def workflows_dir(self) -> Path:
        """Return path to workflows directory."""
        return Path(".github/workflows")

    @pytest.fixture
    def workflow_files(self, workflows_dir: Path) -> list[Path]:
        """Return list of all workflow YAML files."""
        return list(workflows_dir.glob("*.yml"))

    def test_workflows_directory_exists(self, workflows_dir: Path):
        """Test that .github/workflows directory exists."""
        assert workflows_dir.exists()
        assert workflows_dir.is_dir()

    def test_workflow_files_exist(self, workflow_files: list[Path]):
        """Test that workflow files exist."""
        assert len(workflow_files) >= 5, "Expected at least 5 workflow files"

        expected_workflows = [
            "ci.yml",
            "release.yml",
            "security-scan.yml",
            "dependency-update.yml",
            "docs.yml",
        ]

        actual_names = [f.name for f in workflow_files]
        for expected in expected_workflows:
            assert expected in actual_names, f"Missing workflow: {expected}"

    def test_workflow_yaml_valid(self, workflow_files: list[Path]):
        """Test that all workflow files are valid YAML."""
        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                try:
                    data = yaml.safe_load(f)
                    assert data is not None
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {workflow_file.name}: {e}")

    def test_workflow_has_required_fields(self, workflow_files: list[Path]):
        """Test that workflows have required fields."""
        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                data = yaml.safe_load(f)

            # Check required top-level fields
            assert "name" in data, f"{workflow_file.name} missing 'name' field"
            # YAML parses "on" as True (boolean), so check for either
            assert "on" in data or True in data, f"{workflow_file.name} missing 'on' field"
            assert "jobs" in data, f"{workflow_file.name} missing 'jobs' field"

            # Check that jobs is not empty
            assert len(data["jobs"]) > 0, f"{workflow_file.name} has no jobs"

    def test_ci_workflow_structure(self, workflows_dir: Path):
        """Test CI workflow has expected structure."""
        ci_file = workflows_dir / "ci.yml"
        with open(ci_file) as f:
            ci_data = yaml.safe_load(f)

        # Check expected jobs exist
        expected_jobs = [
            "lint",
            "type-check",
            "test",
            "coverage",
            "build",
            "integration-test-expectations",
        ]

        for job in expected_jobs:
            assert job in ci_data["jobs"], f"CI workflow missing job: {job}"

        # Check test job has matrix
        assert "matrix" in ci_data["jobs"]["test"]["strategy"]
        assert "os" in ci_data["jobs"]["test"]["strategy"]["matrix"]
        assert "python-version" in ci_data["jobs"]["test"]["strategy"]["matrix"]

        # Verify matrix includes required platforms
        os_list = ci_data["jobs"]["test"]["strategy"]["matrix"]["os"]
        assert "ubuntu-latest" in os_list
        assert "macos-latest" in os_list
        assert "windows-latest" in os_list

        # Verify Python 3.11
        python_versions = ci_data["jobs"]["test"]["strategy"]["matrix"]["python-version"]
        assert "3.11" in python_versions

    def test_release_workflow_structure(self, workflows_dir: Path):
        """Test release workflow has expected structure."""
        release_file = workflows_dir / "release.yml"
        with open(release_file) as f:
            release_data = yaml.safe_load(f)

        # Get trigger data (YAML parses "on" as True)
        trigger_data = release_data.get("on") or release_data.get(True)
        assert trigger_data is not None, "No trigger definition found"

        # Check triggered by tags
        assert "push" in trigger_data
        assert "tags" in trigger_data["push"]

        # Check jobs exist
        assert "build-and-release" in release_data["jobs"]
        assert "publish-pypi" in release_data["jobs"]

    def test_security_scan_workflow_structure(self, workflows_dir: Path):
        """Test security scan workflow has expected structure."""
        security_file = workflows_dir / "security-scan.yml"
        with open(security_file) as f:
            security_data = yaml.safe_load(f)

        # Check jobs exist
        assert "security-scan" in security_data["jobs"]
        assert "codeql-analysis" in security_data["jobs"]

        # Check scheduled trigger (YAML parses "on" as True)
        trigger_data = security_data.get("on") or security_data.get(True)
        assert trigger_data is not None, "No trigger definition found"
        assert "schedule" in trigger_data

    def test_dependency_update_workflow_structure(self, workflows_dir: Path):
        """Test dependency update workflow has expected structure."""
        dep_file = workflows_dir / "dependency-update.yml"
        with open(dep_file) as f:
            dep_data = yaml.safe_load(f)

        # Check scheduled trigger (YAML parses "on" as True)
        trigger_data = dep_data.get("on") or dep_data.get(True)
        assert trigger_data is not None, "No trigger definition found"
        assert "schedule" in trigger_data
        assert "workflow_dispatch" in trigger_data

        # Check job exists
        assert "check-updates" in dep_data["jobs"]

    def test_docs_workflow_structure(self, workflows_dir: Path):
        """Test docs workflow has expected structure."""
        docs_file = workflows_dir / "docs.yml"
        with open(docs_file) as f:
            docs_data = yaml.safe_load(f)

        # Check jobs exist
        assert "validate-docs" in docs_data["jobs"]
        assert "check-spelling" in docs_data["jobs"]

    def test_config_files_exist(self):
        """Test that workflow config files exist."""
        config_files = [
            ".github/markdown-link-check-config.json",
            ".github/spellcheck-config.yml",
        ]

        for config_file in config_files:
            assert Path(config_file).exists(), f"Missing config file: {config_file}"

    def test_markdown_link_check_config_valid(self):
        """Test that markdown link check config is valid JSON."""
        config_file = Path(".github/markdown-link-check-config.json")
        with open(config_file) as f:
            try:
                data = json.load(f)
                assert data is not None
                assert "ignorePatterns" in data
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {config_file}: {e}")

    def test_workflows_use_uv(self, workflow_files: list[Path]):
        """Test that workflows use UV package manager."""
        # Workflows that should use UV
        uv_workflows = ["ci.yml", "release.yml", "security-scan.yml", "dependency-update.yml"]

        for workflow_file in workflow_files:
            if workflow_file.name not in uv_workflows:
                continue

            with open(workflow_file) as f:
                content = f.read()

            # Check for UV setup action
            assert "astral-sh/setup-uv@v3" in content, (
                f"{workflow_file.name} doesn't use UV setup action"
            )

            # Check for UV commands
            assert "uv sync" in content or "uv run" in content or "uv build" in content, (
                f"{workflow_file.name} doesn't use UV commands"
            )

    def test_workflows_specify_python_311(self, workflow_files: list[Path]):
        """Test that workflows specify Python 3.11."""
        # Workflows that should specify Python version
        python_workflows = ["ci.yml", "release.yml", "security-scan.yml", "dependency-update.yml"]

        for workflow_file in workflow_files:
            if workflow_file.name not in python_workflows:
                continue

            with open(workflow_file) as f:
                content = f.read()

            # Check for Python 3.11 reference
            assert "3.11" in content, f"{workflow_file.name} doesn't specify Python 3.11"

    def test_ci_workflow_runs_tests(self, workflows_dir: Path):
        """Test that CI workflow runs pytest."""
        ci_file = workflows_dir / "ci.yml"
        with open(ci_file) as f:
            content = f.read()

        assert "pytest" in content, "CI workflow doesn't run pytest"
        assert "tests/unit/" in content, "CI workflow doesn't run unit tests"
        assert "tests/integration/" in content, "CI workflow doesn't run integration tests"

    def test_ci_workflow_checks_coverage(self, workflows_dir: Path):
        """Test that CI workflow checks coverage."""
        ci_file = workflows_dir / "ci.yml"
        with open(ci_file) as f:
            content = f.read()

        assert "--cov" in content, "CI workflow doesn't check coverage"
        assert "--cov-fail-under=80" in content, "CI workflow doesn't enforce 80% coverage"

    def test_ci_workflow_runs_linting(self, workflows_dir: Path):
        """Test that CI workflow runs linting."""
        ci_file = workflows_dir / "ci.yml"
        with open(ci_file) as f:
            content = f.read()

        assert "ruff check" in content, "CI workflow doesn't run ruff check"
        assert "ruff format" in content, "CI workflow doesn't check formatting"

    def test_ci_workflow_runs_type_checking(self, workflows_dir: Path):
        """Test that CI workflow runs type checking."""
        ci_file = workflows_dir / "ci.yml"
        with open(ci_file) as f:
            content = f.read()

        assert "mypy" in content, "CI workflow doesn't run mypy"

    def test_validation_script_exists(self):
        """Test that workflow validation script exists."""
        script = Path("scripts/validate_workflows.sh")
        assert script.exists(), "Workflow validation script not found"
        assert os.access(script, os.X_OK), "Workflow validation script not executable"

    def test_validation_script_runs(self):
        """Test that validation script can be executed."""
        script = Path("scripts/validate_workflows.sh")
        result = subprocess.run([str(script)], capture_output=True, text=True)

        assert result.returncode == 0, f"Validation script failed: {result.stderr}"
        assert "All workflows validated successfully" in result.stdout

    def test_cicd_documentation_exists(self):
        """Test that CI/CD documentation exists."""
        docs = [
            ".github/workflows/README.md",
            "docs/CI_CD_SETUP.md",
        ]

        for doc in docs:
            path = Path(doc)
            assert path.exists(), f"Missing CI/CD documentation: {doc}"
            assert path.stat().st_size > 0, f"CI/CD documentation is empty: {doc}"

    def test_implementation_plan_updated(self):
        """Test that implementation plan marks Task 87 as complete."""
        plan_file = Path("IMPLEMENTATION_PLAN.md")
        assert plan_file.exists()

        with open(plan_file) as f:
            content = f.read()

        # Check Task 87 is marked complete
        assert "[x] **Task 87**: Set up CI/CD pipeline" in content or (
            "[x] **Task 87**" in content and "CI/CD" in content
        ), "Task 87 not marked as complete in IMPLEMENTATION_PLAN.md"


class TestWorkflowQuality:
    """Test workflow quality and best practices."""

    @pytest.fixture
    def workflows_dir(self) -> Path:
        """Return path to workflows directory."""
        return Path(".github/workflows")

    def test_workflows_have_descriptions(self, workflows_dir: Path):
        """Test that workflows have descriptive names."""
        for workflow_file in workflows_dir.glob("*.yml"):
            with open(workflow_file) as f:
                data = yaml.safe_load(f)

            name = data.get("name", "")
            assert len(name) > 0, f"{workflow_file.name} has no name"
            # Allow short names like "CI" - descriptive enough
            assert len(name) >= 2, f"{workflow_file.name} name too short"

    def test_workflows_use_pinned_actions(self, workflows_dir: Path):
        """Test that workflows use pinned action versions."""
        for workflow_file in workflows_dir.glob("*.yml"):
            with open(workflow_file) as f:
                content = f.read()

            # Check for common actions
            if "actions/checkout" in content:
                assert "actions/checkout@v4" in content, (
                    f"{workflow_file.name} doesn't pin checkout action version"
                )

            if "astral-sh/setup-uv" in content:
                assert "astral-sh/setup-uv@v3" in content, (
                    f"{workflow_file.name} doesn't pin UV setup action version"
                )

    def test_workflows_have_job_names(self, workflows_dir: Path):
        """Test that all jobs have descriptive names."""
        for workflow_file in workflows_dir.glob("*.yml"):
            with open(workflow_file) as f:
                data = yaml.safe_load(f)

            for job_id, job_data in data["jobs"].items():
                assert "name" in job_data, f"Job '{job_id}' in {workflow_file.name} has no name"
                name = job_data["name"]
                assert len(name) > 0, f"Job '{job_id}' in {workflow_file.name} has empty name"
