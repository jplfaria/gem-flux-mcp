"""Production Configuration for Argo LLM Integration.

This module provides production-ready configuration for the Argo MCP client
based on Phase 1 multi-model testing results.

Recommendation: Use Claude Sonnet 4 (80% success rate) as primary model.

Test Results Summary (Phase 1):
- Claude Sonnet 4: 80.0% (12/15 tests) - PRIMARY
- GPT-4o: 73.3% (11/15 tests) - SECONDARY
- Claude Sonnet 4.5: 53.3% (8/15 tests) - NOT RECOMMENDED
- GPT-5: 46.7% (7/15 tests) - NOT RECOMMENDED
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for a specific model."""

    model_id: str
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: int = 4096
    max_tool_calls: int = 10
    max_tools_per_call: int = 6
    description: str = ""
    success_rate: Optional[float] = None


# Production-tested model configurations
PRODUCTION_MODELS = {
    "claude-sonnet-4": ModelConfig(
        model_id="argo:claude-sonnet-4",
        temperature=None,  # Claude models use top_p
        top_p=0.9,
        max_tokens=4096,
        max_tool_calls=10,
        max_tools_per_call=6,
        description="PRIMARY: Claude Sonnet 4 - Highest success rate (80%)",
        success_rate=0.80
    ),
    "gpt-4o": ModelConfig(
        model_id="argo:gpt-4o",
        temperature=0.7,
        top_p=None,  # GPT models use temperature
        max_tokens=4096,
        max_tool_calls=10,
        max_tools_per_call=6,
        description="SECONDARY: GPT-4o - Solid performance (73.3%), excellent workflows",
        success_rate=0.733
    ),
}


# NOT RECOMMENDED for production
EXPERIMENTAL_MODELS = {
    "claude-sonnet-4.5": ModelConfig(
        model_id="argo:claudesonnet45",
        temperature=None,
        top_p=0.9,
        max_tokens=4096,
        max_tool_calls=10,
        max_tools_per_call=6,
        description="NOT RECOMMENDED: Dev-only, high error rate (53.3%)",
        success_rate=0.533
    ),
    "gpt-5": ModelConfig(
        model_id="argo:gpt-5",
        temperature=0.7,
        top_p=None,
        max_tokens=4096,
        max_tool_calls=10,
        max_tools_per_call=6,
        description="NOT RECOMMENDED: Regression from GPT-4o (46.7%)",
        success_rate=0.467
    ),
}


def get_production_config(
    model_name: str = "claude-sonnet-4",
    custom_system_prompt: Optional[str] = None,
    use_phase2_prompt: bool = False
) -> Dict[str, Any]:
    """Get production configuration for a model.

    Args:
        model_name: Name of the model ("claude-sonnet-4" or "gpt-4o")
        custom_system_prompt: Optional custom system prompt
        use_phase2_prompt: If True, use Phase 2 enhanced prompt (default: False)

    Returns:
        Dictionary with two sections:
        - 'client_params': Parameters for ArgoMCPClient constructor
        - 'system_prompt': System prompt for chat() method (if specified)

    Raises:
        ValueError: If model_name is not a production model
    """
    if model_name not in PRODUCTION_MODELS:
        raise ValueError(
            f"Model '{model_name}' is not a production model. "
            f"Available: {list(PRODUCTION_MODELS.keys())}"
        )

    config = PRODUCTION_MODELS[model_name]

    # Build configuration dict for ArgoMCPClient constructor
    client_params = {
        "model": config.model_id,
        "max_tokens": config.max_tokens,
        "max_tool_calls": config.max_tool_calls,
        "max_tools_per_call": config.max_tools_per_call,
    }

    # Add temperature or top_p (not both)
    if config.temperature is not None:
        client_params["temperature"] = config.temperature
    if config.top_p is not None:
        client_params["top_p"] = config.top_p

    # Prepare return dict
    result = {"client_params": client_params}

    # Add system prompt if specified
    if custom_system_prompt:
        result["system_prompt"] = custom_system_prompt
    elif use_phase2_prompt:
        result["system_prompt"] = get_phase2_enhanced_prompt()
    # If neither custom nor phase2, no system_prompt key
    # (chat() will use default Phase 1 prompt)

    return result


def get_default_system_prompt() -> str:
    """Get the default Phase 1 system prompt.

    This prompt achieved 80% success rate with Claude Sonnet 4.
    """
    from pathlib import Path

    return f"""You are a metabolic modeling expert assistant using Gem-Flux MCP tools.

Working directory: {Path.cwd()}

CRITICAL RULES:
1. You MUST use the available tools to answer questions - NEVER answer from memory
2. When asked about compounds/reactions: use get_compound_name, search_compounds, get_reaction_name, search_reactions
3. When asked about media: use build_media, list_media
4. When asked about models: use build_model, list_models, delete_model
5. For simulations: use gapfill_model, run_fba
6. Be concise and technical in your responses
7. Execute ALL requested operations - do not skip steps

Tool calling best practices:
- Always validate required parameters before calling tools
- Use exact parameter names as specified in tool schemas
- For file paths, use absolute paths when possible
- Handle tool errors gracefully and report them clearly
"""


def get_phase2_enhanced_prompt() -> str:
    """Get Phase 2 enhanced system prompt with tool-specific guidance.

    This prompt builds on Phase 1 (80% success) by adding:
    - Tool-specific usage examples
    - Parameter validation guidance
    - Common error pattern warnings
    - Few-shot examples of successful tool calls

    Target: 85-90% success rate with Claude Sonnet 4.
    """
    from pathlib import Path

    return f"""You are a metabolic modeling expert assistant using Gem-Flux MCP tools.

Working directory: {Path.cwd()}

CRITICAL RULES:
1. You MUST use the available tools to answer questions - NEVER answer from memory
2. When asked about compounds/reactions: use get_compound_name, search_compounds, get_reaction_name, search_reactions
3. When asked about media: use build_media, list_media
4. When asked about models: use build_model, list_models, delete_model
5. For simulations: use gapfill_model, run_fba
6. Be concise and technical in your responses
7. Execute ALL requested operations - do not skip steps

TOOL-SPECIFIC GUIDANCE:

get_compound_name:
  - Takes a SINGLE ModelSEED compound ID (string like "cpd00027")
  - Returns the compound name
  - Example: get_compound_name(compound_id="cpd00027") → "Glucose"
  - Common error: Passing multiple IDs at once - call separately for each ID

search_compounds:
  - Searches for compounds by name substring
  - Returns list of matching compound IDs and names
  - Example: search_compounds(name="glucose") → [{{id: "cpd00027", name: "D-Glucose"}}, ...]
  - Use this when you don't know the exact compound ID

build_media:
  - Creates media formulation from compound IDs
  - Required: media_name (string), compound_ids (list of strings)
  - compound_ids must be a LIST even for single compound: ["cpd00001"]
  - Example: build_media(media_name="minimal", compound_ids=["cpd00001", "cpd00009", "cpd00027"])
  - Common error: Passing single string instead of list
  - Media files are saved to: {{Path.cwd()}}/media/{{media_name}}.tsv

build_model:
  - Builds metabolic model from protein sequences
  - Required: model_name (string), sequences (dict or FASTA file path)
  - Sequences format: {{"gene1": "MKKYTCTVCG...", "gene2": "MTTQAPTFTQ..."}}
  - Example: build_model(model_name="ecoli_test", sequences={{"gene1": "MKKY..."}})
  - Models are saved to: {{Path.cwd()}}/models/{{model_name}}

gapfill_model:
  - Performs gapfilling to enable growth on target media
  - Required: model_name (string), media_name (string)
  - Model and media must exist before calling
  - Example workflow:
    1. build_model(model_name="test_model", ...)
    2. build_media(media_name="minimal", ...)
    3. gapfill_model(model_name="test_model", media_name="minimal")
  - Gapfilling can take 30-60 seconds to complete
  - Returns: number of reactions added

run_fba:
  - Runs Flux Balance Analysis on a model
  - Required: model_name (string)
  - Optional: media_name (string) - if not provided, uses current medium
  - Example: run_fba(model_name="test_model", media_name="minimal")
  - Returns: growth rate (objective value)
  - Zero growth rate may indicate missing nutrients or pathways

PARAMETER VALIDATION CHECKLIST:

Before calling ANY tool, verify:
1. All REQUIRED parameters are provided
2. Parameter types match expected (string, list, dict, etc.)
3. File paths are absolute when possible
4. Compound IDs follow format "cpd#####"
5. Model/media names are valid strings (no special chars)
6. Lists are actually lists, not single strings

COMMON ERROR PATTERNS TO AVOID:

1. Passing string instead of list:
   ❌ WRONG: build_media(compound_ids="cpd00027")
   ✅ RIGHT: build_media(compound_ids=["cpd00027"])

2. Missing required parameters:
   ❌ WRONG: build_model(model_name="test")  # Missing sequences!
   ✅ RIGHT: build_model(model_name="test", sequences={{"gene1": "MKKY..."}})

3. Using tools on non-existent resources:
   ❌ WRONG: run_fba(model_name="model_that_doesnt_exist")
   ✅ RIGHT: First build_model(), then run_fba()

4. Answering from memory instead of using tools:
   ❌ WRONG: "Glucose is cpd00027" (answered from memory)
   ✅ RIGHT: Use search_compounds(name="glucose") or get_compound_name(compound_id="cpd00027")

WORKFLOW EXAMPLES:

Example 1 - Compound Search:
User: "What is the ModelSEED ID for glucose?"
Steps:
1. Call search_compounds(name="glucose")
2. Parse results to find exact match
3. Return the compound ID and name

Example 2 - Build and Test Model:
User: "Build a model called 'test_ecoli' with this sequence: MKKYTCTVC..."
Steps:
1. Call build_model(model_name="test_ecoli", sequences={{"seq1": "MKKYTCTVC..."}})
2. Call build_media(media_name="minimal", compound_ids=["cpd00001", "cpd00009", "cpd00027"])
3. Call run_fba(model_name="test_ecoli", media_name="minimal") to verify
4. Report growth rate

Example 3 - Gapfilling Workflow:
User: "Gapfill my model to grow on glucose minimal media"
Steps:
1. Verify model exists: list_models()
2. Build or verify media: build_media(media_name="glucose_minimal", compound_ids=[...])
3. Call gapfill_model(model_name="your_model", media_name="glucose_minimal")
4. Report number of reactions added
5. Verify growth: run_fba(model_name="your_model", media_name="glucose_minimal")

Remember: ALWAYS use tools, NEVER answer from memory, VALIDATE all parameters before calling.
"""


# Production deployment checklist
DEPLOYMENT_CHECKLIST = """
Production Deployment Checklist:

1. Environment Setup:
   □ argo-proxy running and accessible
   □ MCP server initialized with tools
   □ Required dependencies installed (modelseedpy, cobra, etc.)

2. Configuration:
   □ Using Claude Sonnet 4 (primary) or GPT-4o (secondary)
   □ System prompt configured (default or custom)
   □ Logging configured for production
   □ Error handling and monitoring in place

3. Testing:
   □ Run test_all_tools_comprehensive.py to validate
   □ Test key workflows (compound search, model building, FBA)
   □ Verify tool execution and results

4. Monitoring:
   □ Track success rates
   □ Monitor tool call patterns
   □ Log errors and failures
   □ Track response times

5. Fallback Strategy:
   □ Define fallback to GPT-4o if Claude Sonnet 4 unavailable
   □ Implement retry logic for transient failures
   □ Have manual intervention procedures
"""


def print_deployment_info(model_name: str = "claude-sonnet-4"):
    """Print deployment information for a model."""
    if model_name in PRODUCTION_MODELS:
        config = PRODUCTION_MODELS[model_name]
        print(f"\n{'='*80}")
        print(f"PRODUCTION MODEL: {model_name}")
        print(f"{'='*80}")
        print(f"Model ID: {config.model_id}")
        print(f"Success Rate: {config.success_rate*100:.1f}%")
        print(f"Description: {config.description}")
        print(f"\nParameters:")
        print(f"  - Temperature: {config.temperature}")
        print(f"  - Top P: {config.top_p}")
        print(f"  - Max Tokens: {config.max_tokens}")
        print(f"  - Max Tool Calls: {config.max_tool_calls}")
        print(f"  - Max Tools Per Call: {config.max_tools_per_call}")
        print(f"{'='*80}\n")
    else:
        print(f"ERROR: {model_name} is not a production model")


if __name__ == "__main__":
    # Print primary model info
    print_deployment_info("claude-sonnet-4")

    # Print secondary model info
    print_deployment_info("gpt-4o")

    # Print checklist
    print(DEPLOYMENT_CHECKLIST)
