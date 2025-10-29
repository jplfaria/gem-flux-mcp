# GitHub Actions CI/CD Pipeline

This directory contains GitHub Actions workflows for the Gem-Flux MCP Server project.

## Workflows Overview

### 🔄 ci.yml - Continuous Integration
**Triggers**: Push to main/phase-1-implementation/develop, Pull Requests

**Jobs**:
- **Lint**: Code style checking with ruff
- **Type Check**: Static type analysis with mypy
- **Test**: Full test suite across Ubuntu, macOS, and Windows
- **Coverage**: Code coverage validation (≥80% requirement)
- **Build**: Package building and artifact upload
- **Integration Test Expectations**: Validates test expectations file

**Matrix Testing**:
- OS: Ubuntu, macOS, Windows
- Python: 3.11

**Artifacts**:
- Coverage reports (uploaded to Codecov)
- Built packages (dist/)

### 📦 release.yml - Release Management
**Triggers**: Git tags matching `v*.*.*` (e.g., v0.1.0)

**Jobs**:
- **Build and Release**: Create GitHub release with changelog
- **Publish to PyPI**: Publish package to PyPI (optional, currently commented out)

**Features**:
- Automatic changelog extraction
- Pre-release detection (alpha, beta, rc)
- GitHub release creation with artifacts
- PyPI publishing (ready to enable)

### 🔐 security-scan.yml - Security Scanning
**Triggers**: Push to main/develop, Pull Requests, Daily at 2 AM UTC

**Jobs**:
- **Security Scan**: pip-audit and safety checks for vulnerabilities
- **CodeQL Analysis**: GitHub's semantic code analysis

**Features**:
- Dependency vulnerability scanning
- Security and quality queries
- Automated security alerts

### 📚 docs.yml - Documentation Validation
**Triggers**: Push to main (docs/specs changes), Manual

**Jobs**:
- **Validate Docs**: Link checking and spec completeness
- **Check Spelling**: Spell checking in documentation

**Validation**:
- Broken link detection
- Critical spec existence verification
- Spelling checks

### 🔄 dependency-update.yml - Dependency Management
**Triggers**: Weekly (Monday 9 AM UTC), Manual

**Jobs**:
- **Check Updates**: Scan for outdated dependencies
- **Test Updates**: Validate updated dependencies
- **Create Issue**: Auto-create GitHub issue for updates

**Features**:
- Weekly dependency checks
- Automated testing with updates
- Issue creation for review

## Workflow Status Badges

Add these badges to your README.md:

```markdown
[![CI](https://github.com/yourorg/gem-flux-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/yourorg/gem-flux-mcp/actions/workflows/ci.yml)
[![Release](https://github.com/yourorg/gem-flux-mcp/actions/workflows/release.yml/badge.svg)](https://github.com/yourorg/gem-flux-mcp/actions/workflows/release.yml)
[![Security Scan](https://github.com/yourorg/gem-flux-mcp/actions/workflows/security-scan.yml/badge.svg)](https://github.com/yourorg/gem-flux-mcp/actions/workflows/security-scan.yml)
[![codecov](https://codecov.io/gh/yourorg/gem-flux-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/yourorg/gem-flux-mcp)
```

## Setup Requirements

### GitHub Secrets
For full functionality, configure these secrets in your repository settings:

- `CODECOV_TOKEN` (optional): Codecov upload token
- `PYPI_API_TOKEN` (optional): PyPI publishing token

### Branch Protection Rules
Recommended settings for `main` branch:

- ✅ Require pull request reviews (1 approver)
- ✅ Require status checks to pass before merging:
  - `Lint and Format Check`
  - `Test Suite`
  - `Coverage Check`
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging

### Codecov Integration
To enable coverage reporting:

1. Sign up at [codecov.io](https://codecov.io)
2. Connect your GitHub repository
3. Add `CODECOV_TOKEN` to GitHub secrets (optional for public repos)

## Local Testing of CI

### Run linting locally
```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

### Run type checking locally
```bash
uv run mypy src/
```

### Run tests locally
```bash
# Unit tests
uv run pytest tests/unit/ -v --cov=src

# Integration tests
uv run pytest tests/integration/ -v --cov=src --cov-append

# All tests with coverage
uv run pytest tests/ --cov=src --cov-fail-under=80
```

### Build package locally
```bash
uv build
```

### Security scan locally
```bash
uv pip install pip-audit safety
uv run pip-audit --desc
uv run safety check
```

## Workflow Triggers

### Manual Workflow Dispatch
All workflows can be triggered manually via GitHub UI:

1. Go to Actions tab
2. Select workflow
3. Click "Run workflow"
4. Choose branch

### Scheduled Workflows

- **dependency-update.yml**: Monday 9 AM UTC
- **security-scan.yml**: Daily 2 AM UTC

## Troubleshooting

### Test Failures
If tests fail in CI but pass locally:

1. Check Python version matches (3.11)
2. Verify UV lock file is committed
3. Check for platform-specific issues (Windows vs Linux)
4. Review test expectations file

### Coverage Failures
If coverage drops below 80%:

1. Run `uv run pytest tests/ --cov=src --cov-report=html`
2. Open `htmlcov/index.html` in browser
3. Identify uncovered lines
4. Add missing tests

### Build Failures
If package build fails:

1. Check `pyproject.toml` syntax
2. Verify all files are included
3. Test locally with `uv build`

### Security Scan Issues
If vulnerabilities are found:

1. Review the security report
2. Update dependencies: `uv lock --upgrade`
3. Test with updated dependencies
4. Create PR with updates

## Adding New Workflows

To add a new workflow:

1. Create `.github/workflows/your-workflow.yml`
2. Define triggers, jobs, and steps
3. Test locally if possible
4. Commit and push
5. Monitor first run in Actions tab

## Best Practices

### Workflow Design
- ✅ Use matrix strategy for multi-platform testing
- ✅ Fail fast for critical checks (lint, type-check)
- ✅ Continue on error for non-critical checks
- ✅ Upload artifacts for debugging
- ✅ Use workflow_dispatch for manual triggers

### Performance
- ✅ Cache dependencies when possible
- ✅ Run fast checks first (lint before tests)
- ✅ Parallelize independent jobs
- ✅ Use appropriate timeouts

### Security
- ✅ Pin action versions (@v4, not @latest)
- ✅ Use minimal permissions
- ✅ Never commit secrets
- ✅ Review third-party actions

## Maintenance

### Regular Tasks
- Review dependency update issues weekly
- Update action versions quarterly
- Monitor workflow run times
- Adjust concurrency limits if needed

### Workflow Updates
When updating workflows:

1. Test in a feature branch first
2. Review workflow runs before merging
3. Update this README if behavior changes
4. Notify team of significant changes

## Support

For issues with GitHub Actions:
- Check [GitHub Actions documentation](https://docs.github.com/en/actions)
- Review workflow logs in Actions tab
- Open issue with `ci/cd` label
