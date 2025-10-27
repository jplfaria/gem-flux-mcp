# Modern CLI Implementation Examples

**Purpose**: Reference implementations for AI Co-Scientist CLI design
**Date**: October 15, 2025

## Example 1: Typer-Based CLI Structure

### Complete Example

```python
"""AI Co-Scientist Command-Line Interface.

Provides expert developers with direct access to research capabilities.
"""
import typer
import json
import sys
from typing import Optional
from pathlib import Path
from enum import Enum

app = typer.Typer(
    name="co-scientist",
    help="AI-powered scientific research assistant",
    add_completion=True,
)

# Create subcommands for organization
research_app = typer.Typer(help="Manage research projects")
hypotheses_app = typer.Typer(help="Manage hypotheses")
results_app = typer.Typer(help="View and export results")

app.add_typer(research_app, name="research")
app.add_typer(hypotheses_app, name="hypotheses")
app.add_typer(results_app, name="results")


class OutputFormat(str, Enum):
    """Supported output formats."""
    text = "text"
    json = "json"
    yaml = "yaml"


def is_interactive() -> bool:
    """Check if running in interactive mode (TTY)."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def output_result(data: dict, format: OutputFormat, template: Optional[str] = None):
    """Output data in requested format.

    Args:
        data: Data to output
        format: Output format (text, json, yaml)
        template: Optional Go-style template string
    """
    if format == OutputFormat.json:
        typer.echo(json.dumps(data, indent=2))
    elif format == OutputFormat.yaml:
        import yaml
        typer.echo(yaml.dump(data, default_flow_style=False))
    elif template:
        # Go-style template (like GitHub CLI)
        from string import Template
        typer.echo(Template(template).safe_substitute(data))
    else:
        # Human-readable text output
        format_text_output(data)


def format_text_output(data: dict):
    """Format data as human-readable text."""
    if "research_id" in data:
        typer.echo(f"Research ID: {data['research_id']}")
        typer.echo(f"Status: {data.get('status', 'unknown')}")
        if "hypotheses_count" in data:
            typer.echo(f"Hypotheses: {data['hypotheses_count']}")


# ============================================================================
# Research Commands
# ============================================================================

@research_app.command("start")
def research_start(
    goal: str = typer.Argument(..., help="Research goal in natural language"),
    domain: Optional[str] = typer.Option(None, help="Scientific domain"),
    constraints: Optional[list[str]] = typer.Option(
        None,
        "--constraint", "-c",
        help="Research constraints (can be specified multiple times)"
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.text,
        "--format", "-f",
        help="Output format"
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to configuration file (YAML/JSON)"
    ),
):
    """Start a new research project.

    Examples:
        co-scientist research start "Find treatments for liver fibrosis"

        co-scientist research start "Why does ice float?" \\
            --domain physics --format json

        co-scientist research start "Novel antibiotics" \\
            --constraint "No animal testing" \\
            --constraint "Budget under $1M"
    """
    from co_scientist.core import ResearchEngine

    # Load config if provided
    research_config = {}
    if config and config.exists():
        research_config = load_config(config)

    # Build research parameters
    params = {
        "goal": goal,
        "domain": domain,
        "constraints": constraints or [],
        **research_config
    }

    # Interactive confirmation if TTY
    if is_interactive() and not typer.confirm(
        f"Start research on: {goal}?",
        default=True
    ):
        raise typer.Abort()

    # Execute research
    engine = ResearchEngine()
    result = engine.start_research(**params)

    # Output result
    output_result(result.dict(), format)


@research_app.command("status")
def research_status(
    research_id: str = typer.Argument(..., help="Research ID"),
    format: OutputFormat = typer.Option(OutputFormat.text, "--format", "-f"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch for updates"),
):
    """Check status of a research project.

    Examples:
        co-scientist research status res_abc123

        co-scientist research status res_abc123 --format json

        co-scientist research status res_abc123 --watch
    """
    from co_scientist.core import ResearchEngine
    import time

    engine = ResearchEngine()

    if watch:
        # Watch mode - update every 2 seconds
        try:
            while True:
                status = engine.get_research_status(research_id)
                output_result(status.dict(), format)

                if status.is_complete:
                    break

                time.sleep(2)
                if is_interactive():
                    typer.echo("\033[2J\033[H")  # Clear screen
        except KeyboardInterrupt:
            typer.echo("\nStopped watching.")
    else:
        # Single status check
        status = engine.get_research_status(research_id)
        output_result(status.dict(), format)


@research_app.command("list")
def research_list(
    format: OutputFormat = typer.Option(OutputFormat.text, "--format", "-f"),
    status: Optional[str] = typer.Option(None, help="Filter by status"),
    limit: int = typer.Option(10, help="Maximum results to return"),
):
    """List all research projects.

    Examples:
        co-scientist research list

        co-scientist research list --status active --format json

        co-scientist research list --limit 50
    """
    from co_scientist.core import ResearchEngine

    engine = ResearchEngine()
    projects = engine.list_research_projects(status=status, limit=limit)

    if format == OutputFormat.json:
        typer.echo(json.dumps([p.dict() for p in projects], indent=2))
    else:
        # Table output
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Research Projects")

        table.add_column("ID", style="cyan")
        table.add_column("Goal", style="green")
        table.add_column("Status")
        table.add_column("Hypotheses", justify="right")

        for project in projects:
            table.add_row(
                project.id,
                project.goal[:50] + "..." if len(project.goal) > 50 else project.goal,
                project.status,
                str(project.hypotheses_count)
            )

        console.print(table)


# ============================================================================
# Hypothesis Commands
# ============================================================================

@hypotheses_app.command("list")
def hypotheses_list(
    research_id: str = typer.Argument(..., help="Research ID"),
    format: OutputFormat = typer.Option(OutputFormat.text, "--format", "-f"),
    sort_by: str = typer.Option("elo", help="Sort field (elo, created, novelty)"),
    min_elo: Optional[float] = typer.Option(None, help="Minimum Elo rating"),
):
    """List hypotheses for a research project.

    Examples:
        co-scientist hypotheses list res_abc123

        co-scientist hypotheses list res_abc123 --format json

        co-scientist hypotheses list res_abc123 --min-elo 1400
    """
    from co_scientist.core import ResearchEngine

    engine = ResearchEngine()
    hypotheses = engine.list_hypotheses(
        research_id=research_id,
        sort_by=sort_by,
        min_elo=min_elo
    )

    if format == OutputFormat.json:
        typer.echo(json.dumps([h.dict() for h in hypotheses], indent=2))
    else:
        # Table output
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title=f"Hypotheses for {research_id}")

        table.add_column("ID", style="cyan")
        table.add_column("Summary", style="green")
        table.add_column("Elo", justify="right")
        table.add_column("Category")

        for hyp in hypotheses:
            table.add_row(
                hyp.id,
                hyp.summary[:60] + "..." if len(hyp.summary) > 60 else hyp.summary,
                f"{hyp.elo_rating:.0f}",
                hyp.category
            )

        console.print(table)


@hypotheses_app.command("show")
def hypotheses_show(
    hypothesis_id: str = typer.Argument(..., help="Hypothesis ID"),
    format: OutputFormat = typer.Option(OutputFormat.text, "--format", "-f"),
    include_reviews: bool = typer.Option(False, "--reviews", help="Include reviews"),
):
    """Show detailed information about a hypothesis.

    Examples:
        co-scientist hypotheses show hyp_123

        co-scientist hypotheses show hyp_123 --format json

        co-scientist hypotheses show hyp_123 --reviews
    """
    from co_scientist.core import ResearchEngine

    engine = ResearchEngine()
    hypothesis = engine.get_hypothesis(hypothesis_id, include_reviews=include_reviews)

    if format == OutputFormat.json:
        typer.echo(json.dumps(hypothesis.dict(), indent=2))
    else:
        # Rich formatted output
        from rich.console import Console
        from rich.panel import Panel
        from rich.markdown import Markdown

        console = Console()

        console.print(f"\n[bold cyan]Hypothesis {hypothesis.id}[/bold cyan]")
        console.print(f"[green]{hypothesis.summary}[/green]\n")

        console.print(Panel(hypothesis.full_description, title="Description"))
        console.print(f"\n[yellow]Elo Rating:[/yellow] {hypothesis.elo_rating:.0f}")
        console.print(f"[yellow]Category:[/yellow] {hypothesis.category}")
        console.print(f"[yellow]Confidence:[/yellow] {hypothesis.confidence_score:.2f}")

        if include_reviews and hypothesis.reviews:
            console.print(f"\n[bold]Reviews ({len(hypothesis.reviews)}):[/bold]")
            for review in hypothesis.reviews:
                console.print(f"  - {review.decision}: {review.narrative_feedback[:100]}...")


@hypotheses_app.command("evolve")
def hypotheses_evolve(
    hypothesis_id: str = typer.Argument(..., help="Hypothesis ID to evolve"),
    strategy: str = typer.Option(
        "refine",
        help="Evolution strategy (refine, combine, simplify, mutation)"
    ),
    format: OutputFormat = typer.Option(OutputFormat.text, "--format", "-f"),
):
    """Evolve a hypothesis using specified strategy.

    Examples:
        co-scientist hypotheses evolve hyp_123

        co-scientist hypotheses evolve hyp_123 --strategy combine

        co-scientist hypotheses evolve hyp_123 --format json
    """
    from co_scientist.core import ResearchEngine

    engine = ResearchEngine()

    # Interactive confirmation
    if is_interactive():
        typer.echo(f"Evolving hypothesis {hypothesis_id} using '{strategy}' strategy...")

    result = engine.evolve_hypothesis(hypothesis_id, strategy=strategy)

    output_result(result.dict(), format)

    if is_interactive() and format == OutputFormat.text:
        typer.echo(f"\n[green]✓[/green] Created evolved hypothesis: {result.id}")


# ============================================================================
# Results Commands
# ============================================================================

@results_app.command("overview")
def results_overview(
    research_id: str = typer.Argument(..., help="Research ID"),
    format: OutputFormat = typer.Option(OutputFormat.text, "--format", "-f"),
):
    """Get research overview and meta-analysis.

    Examples:
        co-scientist results overview res_abc123

        co-scientist results overview res_abc123 --format json
    """
    from co_scientist.core import ResearchEngine

    engine = ResearchEngine()
    overview = engine.get_research_overview(research_id)

    if format == OutputFormat.json:
        typer.echo(json.dumps(overview.dict(), indent=2))
    else:
        # Rich formatted output
        from rich.console import Console
        from rich.panel import Panel

        console = Console()

        console.print(f"\n[bold cyan]Research Overview: {research_id}[/bold cyan]\n")
        console.print(Panel(overview.executive_summary, title="Executive Summary"))

        console.print(f"\n[bold]Research Areas ({len(overview.research_areas)}):[/bold]")
        for area in overview.research_areas:
            console.print(f"\n[yellow]{area.area_title}[/yellow]")
            console.print(f"  {area.importance_justification}")
            console.print(f"  Key hypotheses: {', '.join(area.key_hypotheses[:3])}")


@results_app.command("export")
def results_export(
    research_id: str = typer.Argument(..., help="Research ID"),
    output_file: Path = typer.Option(..., "--output", "-o", help="Output file path"),
    format_type: str = typer.Option("json", help="Export format (json, yaml, pdf, markdown)"),
    include_reviews: bool = typer.Option(False, "--include-reviews", help="Include all reviews"),
):
    """Export research results to file.

    Examples:
        co-scientist results export res_abc123 -o results.json

        co-scientist results export res_abc123 -o report.pdf --format pdf

        co-scientist results export res_abc123 -o full.json --include-reviews
    """
    from co_scientist.core import ResearchEngine

    engine = ResearchEngine()

    with typer.progressbar(length=100, label="Exporting") as progress:
        result = engine.export_results(
            research_id=research_id,
            include_reviews=include_reviews,
            format=format_type,
            output_path=output_file,
            progress_callback=progress.update
        )

    typer.echo(f"[green]✓[/green] Exported to: {output_file}")


# ============================================================================
# Helper Functions
# ============================================================================

def load_config(config_path: Path) -> dict:
    """Load configuration from YAML or JSON file."""
    import yaml

    with open(config_path) as f:
        if config_path.suffix == ".json":
            return json.load(f)
        else:
            return yaml.safe_load(f)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    app()
```

## Example 2: Configuration File Support

### YAML Configuration

```yaml
# ~/.co-scientist/config.yaml

# Default research parameters
defaults:
  domain: biology
  max_hypotheses: 50
  tournament_rounds: 100

# LLM provider settings
llm:
  provider: argo
  model: o3
  api_key_env: ARGO_API_KEY
  timeout: 30

# Output preferences
output:
  default_format: text
  color: true
  pager: auto

# Safety settings
safety:
  require_confirmation: true
  blocked_methods:
    - animal_testing
    - human_subjects

# Resource limits
resources:
  max_compute: 1000.0
  max_time_hours: 24
  max_cost_usd: 100.0
```

### JSON Configuration

```json
{
  "defaults": {
    "domain": "biology",
    "max_hypotheses": 50
  },
  "llm": {
    "provider": "argo",
    "model": "o3"
  },
  "output": {
    "default_format": "json",
    "indent": 2
  }
}
```

## Example 3: Shell Completion

### Bash Completion

```bash
# Generate completion script
co-scientist --install-completion bash

# Add to ~/.bashrc
eval "$(_CO_SCIENTIST_COMPLETE=bash_source co-scientist)"
```

### Zsh Completion

```zsh
# Generate completion script
co-scientist --install-completion zsh

# Add to ~/.zshrc
eval "$(_CO_SCIENTIST_COMPLETE=zsh_source co-scientist)"
```

## Example 4: Streaming Output

```python
@research_app.command("start")
def research_start(
    goal: str,
    stream: bool = typer.Option(False, "--stream", help="Stream progress updates"),
):
    """Start research with optional streaming updates."""
    from co_scientist.core import ResearchEngine

    engine = ResearchEngine()

    if stream:
        # Stream progress as JSONL (one JSON object per line)
        for event in engine.start_research_stream(goal):
            typer.echo(json.dumps(event.dict()))
    else:
        # Batch mode - return final result
        result = engine.start_research(goal)
        typer.echo(json.dumps(result.dict()))
```

**Usage**:
```bash
# Stream mode
co-scientist research start "goal" --stream
{"type": "started", "research_id": "res_123"}
{"type": "hypothesis_generated", "id": "hyp_1"}
{"type": "hypothesis_generated", "id": "hyp_2"}
{"type": "completed", "total": 47}

# Batch mode
co-scientist research start "goal"
{"research_id": "res_123", "status": "completed", "hypotheses": 47}
```

## Example 5: Piping and jq Integration

```bash
# Get all hypothesis IDs with Elo > 1400
co-scientist hypotheses list res_123 --format json | \\
  jq -r '.[] | select(.elo_rating > 1400) | .id'

# Export top hypotheses to CSV
co-scientist hypotheses list res_123 --format json | \\
  jq -r '["id","summary","elo"], (.[] | [.id, .summary, .elo_rating]) | @csv' > top.csv

# Count hypotheses by category
co-scientist hypotheses list res_123 --format json | \\
  jq 'group_by(.category) | map({category: .[0].category, count: length})'
```

## Example 6: Error Handling

```python
from typer import Exit

class ResearchError(Exception):
    """Base exception for research errors."""
    exit_code = 1


class ConnectionError(ResearchError):
    """LLM connection failed."""
    exit_code = 70  # Internal error


class ValidationError(ResearchError):
    """Input validation failed."""
    exit_code = 64  # Input data error


def handle_error(error: Exception):
    """Handle errors with proper exit codes and messages."""
    from rich.console import Console
    console = Console(stderr=True)

    if isinstance(error, ResearchError):
        console.print(f"[red]Error:[/red] {error}")
        console.print(f"[dim]Exit code: {error.exit_code}[/dim]")
        raise Exit(error.exit_code)
    else:
        console.print(f"[red]Unexpected error:[/red] {error}")
        raise Exit(1)


# Wrap main commands
@research_app.command("start")
def research_start(goal: str):
    try:
        engine = ResearchEngine()
        result = engine.start_research(goal)
        typer.echo(json.dumps(result.dict()))
    except Exception as e:
        handle_error(e)
```

## Example 7: Testing

```python
# tests/test_cli.py
from typer.testing import CliRunner
from co_scientist.cli import app

runner = CliRunner()


def test_research_start_json_output():
    """Test research start with JSON output."""
    result = runner.invoke(app, [
        "research", "start",
        "Why does ice float?",
        "--format", "json"
    ])

    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert "research_id" in data
    assert data["status"] == "started"


def test_research_start_interactive_abort():
    """Test aborting interactive research start."""
    result = runner.invoke(app, [
        "research", "start",
        "Test goal"
    ], input="n\n")  # Say "no" to confirmation

    assert result.exit_code == 1  # Aborted


def test_hypotheses_list_formatting():
    """Test hypothesis list output formats."""
    # JSON format
    result = runner.invoke(app, [
        "hypotheses", "list", "res_123",
        "--format", "json"
    ])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)

    # Text format (check for table)
    result = runner.invoke(app, [
        "hypotheses", "list", "res_123"
    ])

    assert result.exit_code == 0
    assert "Hypotheses for res_123" in result.stdout
```

## Best Practices Demonstrated

1. **Type Hints**: Full typing for autocomplete and validation
2. **Subcommands**: Organized command structure (research, hypotheses, results)
3. **Output Formats**: JSON, YAML, text, templates
4. **Interactive Detection**: Different behavior for TTY vs scripts
5. **Error Handling**: Proper exit codes and error messages
6. **Configuration**: YAML/JSON config file support
7. **Shell Completion**: Bash/Zsh completion scripts
8. **Streaming**: JSONL streaming for long operations
9. **Piping**: jq-friendly JSON output
10. **Testing**: Comprehensive CLI tests with CliRunner

These patterns ensure the CLI is both human-friendly and automation-ready.
