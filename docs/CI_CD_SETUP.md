# CI/CD Pipeline Setup for Gem-Flux MCP Server

**Date**: October 28, 2025
**Task**: Task 87 - Set up CI/CD pipeline (GitHub Actions)
**Status**: ✅ Complete

## Overview

This document describes the comprehensive CI/CD pipeline implemented for the Gem-Flux MCP Server using GitHub Actions. The pipeline ensures code quality, security, and reliability through automated testing, security scanning, and release management.

## Workflows Implemented

### 1. Main CI Pipeline (ci.yml)

**Purpose**: Continuous integration for all code changes

**Triggers**:
- Push to `main`, `phase-1-implementation`, `develop` branches
- Pull requests to `main`, `develop` branches

**Jobs**:

1. **Lint and Format Check**
   - Runs `ruff check` on source and test code
   - Runs `ruff format --check` to verify formatting
   - Fast failure for style violations

2. **Type Checking**
   - Runs `mypy` on source code
   - Currently non-blocking (continue-on-error)
   - Will be enforced in future versions

3. **Test Suite**
   - Matrix testing across:
     - OS: Ubuntu, macOS, Windows
     - Python: 3.11
   - Separate unit and integration test runs
   - Code coverage collection

4. **Coverage Check**
   - Validates ≥80% code coverage requirement
   - Generates HTML coverage report
   - Uploads to Codecov (if configured)

5. **Build Package**
   - Builds distribution packages
   - Uploads artifacts for 7 days
   - Verifies package creation succeeds

6. **Integration Test Expectations**
   - Validates `test_expectations.json` exists
   - Verifies integration test structure
   - Records test results

**Why Multi-OS Testing?**
- Ensures platform compatibility
- Catches OS-specific issues (path handling, line endings)
- Important for UV virtual environment behavior

### 2. Release Pipeline (release.yml)

**Purpose**: Automated releases for version tags

**Triggers**:
- Git tags matching `v*.*.*` (e.g., `v0.1.0`, `v1.2.3`)

**Jobs**:

1. **Build and Release**
   - Runs full test suite
   - Builds distribution packages
   - Extracts version from tag
   - Generates changelog from CHANGELOG.md
   - Creates GitHub release with artifacts
   - Marks pre-releases (alpha, beta, rc) appropriately

2. **Publish to PyPI** (optional)
   - Only runs for stable releases (not pre-releases)
   - Uses PyPI trusted publisher (no API token needed)
   - Currently commented out (enable when ready)

**Release Process**:
```bash
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md
# 3. Commit changes
git commit -m "chore: release v0.1.0"

# 4. Create and push tag
git tag v0.1.0
git push origin v0.1.0

# 5. GitHub Actions automatically creates release
```

### 3. Security Scanning Pipeline (security-scan.yml)

**Purpose**: Continuous security monitoring

**Triggers**:
- Push to `main`, `develop` branches
- Pull requests to `main`, `develop` branches
- Daily at 2:00 AM UTC

**Jobs**:

1. **Security Vulnerability Scan**
   - Runs `pip-audit` for dependency vulnerabilities
   - Runs `safety check` for known security issues
   - Non-blocking (continue-on-error)
   - Creates issues for critical vulnerabilities

2. **CodeQL Security Analysis**
   - GitHub's semantic code analysis
   - Detects security vulnerabilities
   - Analyzes data flow and control flow
   - Checks against CWE database
   - Reports findings to Security tab

**Why Daily Scans?**
- New vulnerabilities discovered daily
- Early detection enables quick patching
- Maintains security posture

### 4. Dependency Update Pipeline (dependency-update.yml)

**Purpose**: Automated dependency management

**Triggers**:
- Weekly on Monday at 9:00 AM UTC
- Manual trigger via workflow_dispatch

**Jobs**:

1. **Check for Updates**
   - Lists outdated dependencies with `uv pip list --outdated`
   - Creates backup of current lock file
   - Generates updated lock file with `uv lock --upgrade`

2. **Test with Updates**
   - Syncs with updated dependencies
   - Runs full test suite
   - Reports success/failure

3. **Create Issue**
   - Automatically creates GitHub issue if updates available
   - Includes update instructions
   - Labels with `dependencies` and `maintenance`
   - Avoids duplicate issues

**Why Weekly?**
- Balances freshness with stability
- Manageable review cadence
- Prevents large update backlogs

### 5. Documentation Pipeline (docs.yml)

**Purpose**: Documentation quality assurance

**Triggers**:
- Push to `main` affecting docs/, specs/, or .md files
- Manual trigger

**Jobs**:

1. **Validate Documentation**
   - Checks for broken links
   - Validates critical spec files exist
   - Verifies README.md present

2. **Check Spelling**
   - Runs spell checker on markdown files
   - Uses custom dictionary
   - Non-blocking (continue-on-error)

**Critical Specs Verified**:
- 001-system-overview.md
- 002-data-formats.md
- 003-build-media-tool.md
- 004-build-model-tool.md
- 005-gapfill-model-tool.md
- 006-run-fba-tool.md

## Configuration Files

### .github/markdown-link-check-config.json
Configures link checking behavior:
- Ignores localhost URLs
- Handles redirects
- Sets timeouts and retries
- GitHub-specific headers

### .github/spellcheck-config.yml
Configures spell checking:
- English dictionary
- Markdown and HTML filtering
- Ignores code blocks

## Workflow Status Badges

Add these badges to README.md:

```markdown
[![CI](https://github.com/yourorg/gem-flux-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/yourorg/gem-flux-mcp/actions/workflows/ci.yml)
[![Release](https://github.com/yourorg/gem-flux-mcp/actions/workflows/release.yml/badge.svg)](https://github.com/yourorg/gem-flux-mcp/actions/workflows/release.yml)
[![Security Scan](https://github.com/yourorg/gem-flux-mcp/actions/workflows/security-scan.yml/badge.svg)](https://github.com/yourorg/gem-flux-mcp/actions/workflows/security-scan.yml)
[![codecov](https://codecov.io/gh/yourorg/gem-flux-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/yourorg/gem-flux-mcp)
```

Replace `yourorg` with actual organization/user name.

## Setup Instructions

### 1. Enable GitHub Actions
GitHub Actions are enabled by default for most repositories. Verify in repository Settings > Actions.

### 2. Configure Secrets (Optional)

**For Codecov Integration**:
1. Sign up at [codecov.io](https://codecov.io)
2. Connect repository
3. Add `CODECOV_TOKEN` to repository secrets (Settings > Secrets > Actions)

**For PyPI Publishing**:
1. Generate PyPI API token at [pypi.org](https://pypi.org)
2. Add `PYPI_API_TOKEN` to repository secrets
3. Uncomment publishing step in release.yml

### 3. Configure Branch Protection

Recommended settings for `main` branch (Settings > Branches > Branch protection rules):

- ✅ Require pull request reviews before merging (1 approver)
- ✅ Require status checks to pass before merging:
  - `Lint and Format Check`
  - `Test Suite (ubuntu-latest, 3.11)`
  - `Coverage Check`
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging
- ✅ Require linear history (optional)

### 4. Enable Security Features

Enable in Settings > Security:
- ✅ Dependency graph
- ✅ Dependabot alerts
- ✅ Dependabot security updates
- ✅ Code scanning (CodeQL)

## Local Testing

Before pushing, run these commands locally:

```bash
# Lint and format check
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Type checking
uv run mypy src/

# Unit tests
uv run pytest tests/unit/ -v --cov=src

# Integration tests
uv run pytest tests/integration/ -v --cov=src --cov-append

# All tests with coverage
uv run pytest tests/ --cov=src --cov-fail-under=80

# Build package
uv build

# Security scan
uv pip install pip-audit safety
uv run pip-audit --desc
uv run safety check
```

## Workflow Maintenance

### Weekly Tasks
- Review dependency update issues
- Check security scan results
- Monitor workflow run times

### Monthly Tasks
- Review CodeQL findings
- Update action versions if needed
- Audit test coverage trends

### Quarterly Tasks
- Review and update branch protection rules
- Audit secret rotation needs
- Update workflow documentation

## Troubleshooting

### Tests Pass Locally but Fail in CI

**Possible Causes**:
1. Python version mismatch (ensure 3.11)
2. Lock file not committed (`uv.lock`)
3. Platform-specific test issues
4. Missing test dependencies

**Solution**:
```bash
# Verify Python version
python --version  # Should be 3.11.x

# Update lock file
uv lock
git add uv.lock
git commit -m "chore: update lock file"
```

### Coverage Drops Below 80%

**Solution**:
```bash
# Generate HTML coverage report
uv run pytest tests/ --cov=src --cov-report=html

# Open report
open htmlcov/index.html

# Identify uncovered lines and add tests
```

### Security Vulnerabilities Found

**Solution**:
```bash
# Update dependencies
uv lock --upgrade

# Test with updates
uv sync
uv run pytest tests/

# If tests pass, commit updates
git add uv.lock
git commit -m "chore: update dependencies to fix vulnerabilities"
```

### Release Creation Fails

**Possible Causes**:
1. CHANGELOG.md missing version section
2. Tests failing at release time
3. Build errors

**Solution**:
1. Ensure CHANGELOG.md has section for version
2. Run full test suite before tagging
3. Test build locally with `uv build`

## Best Practices

### Commit Messages
Use conventional commits for automated changelog generation:
- `feat:` - New features
- `fix:` - Bug fixes
- `chore:` - Maintenance tasks
- `docs:` - Documentation changes
- `test:` - Test additions/changes

### Pull Request Workflow
1. Create feature branch from `develop`
2. Make changes and commit
3. Push to GitHub
4. Create pull request to `develop`
5. Wait for CI checks to pass
6. Request review
7. Merge after approval

### Release Workflow
1. Merge `develop` into `main`
2. Update version in `pyproject.toml`
3. Update `CHANGELOG.md`
4. Commit: `chore: release v0.1.0`
5. Tag: `git tag v0.1.0`
6. Push: `git push origin main --tags`
7. Monitor release workflow

## Metrics and Monitoring

### Key Metrics to Track
- Test pass rate
- Code coverage percentage
- Workflow run time
- Security vulnerability count
- Dependency update frequency

### Monitoring Tools
- GitHub Actions dashboard (Actions tab)
- Codecov dashboard (if configured)
- GitHub Security tab (Dependabot, CodeQL)
- GitHub Insights (pull request metrics)

## Future Enhancements

### Planned Improvements
1. **Performance Benchmarking**: Add workflow to track performance over time
2. **Docker Image Building**: Automate container image creation
3. **Documentation Building**: Auto-deploy documentation to GitHub Pages
4. **Release Notes Generation**: Automated changelog from commits
5. **Deployment Automation**: Auto-deploy to staging environment

### Advanced Features
- Canary deployments
- Blue-green deployments
- Automated rollback on failure
- Integration with external monitoring
- Slack/Discord notifications

## Resources

### Documentation
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [UV Documentation](https://docs.astral.sh/uv/)
- [Codecov Documentation](https://docs.codecov.io/)
- [CodeQL Documentation](https://codeql.github.com/docs/)

### Action Marketplaces
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [Awesome Actions](https://github.com/sdras/awesome-actions)

## Summary

The CI/CD pipeline provides:

✅ **Automated Testing**: Multi-platform test execution
✅ **Code Quality**: Linting, formatting, type checking
✅ **Security**: Vulnerability scanning, CodeQL analysis
✅ **Release Management**: Automated GitHub releases
✅ **Dependency Management**: Weekly update checks
✅ **Documentation Validation**: Link checking, spell checking

This comprehensive pipeline ensures code quality, security, and reliability while minimizing manual work.

---

**Completion Status**: Task 87 Complete ✅
**Date**: October 28, 2025
**Implementation**: 5 workflows, 3 config files, comprehensive documentation
