"""Shared test configuration and fixtures."""

import sys
import pytest
from unittest.mock import MagicMock, AsyncMock

# Mock BAML client to avoid import errors during testing
def pytest_configure(config):
    """Configure pytest - runs before tests."""
    # Check if we're running real LLM tests
    if config.getoption("--real-llm"):
        # Skip BAML mocking for real LLM tests
        return
    
    # Create mock for baml_client
    mock_baml_client = MagicMock()
    
    # Create a mock b with async methods
    mock_b = MagicMock()
    
    # Mock the specific async methods with default return values
    # Create a mock hypothesis return value
    mock_hypothesis = MagicMock()
    mock_hypothesis.id = "test-hypothesis-123"
    mock_hypothesis.summary = "Test hypothesis for KIRA6 inhibition of IRE1α in AML treatment"
    mock_hypothesis.category = "therapeutic"
    mock_hypothesis.full_description = "KIRA6 selectively inhibits IRE1α kinase activity to reduce ER stress in AML cells"
    mock_hypothesis.novelty_claim = "Novel use of KIRA6 as repurposed drug for AML"
    mock_hypothesis.assumptions = ["IRE1α is overactive in AML cells", "KIRA6 can penetrate cell membranes"]
    mock_hypothesis.reasoning = "Based on literature showing increased ER stress in AML"
    mock_hypothesis.confidence_score = 0.85
    mock_hypothesis.generation_method = "literature_based"
    mock_hypothesis.created_at = "2024-01-01T00:00:00Z"
    
    # Create mock experimental protocol
    mock_protocol = MagicMock()
    mock_protocol.objective = "Test KIRA6 efficacy in AML cell lines"
    mock_protocol.methodology = "In vitro testing with AML cell lines"
    mock_protocol.required_resources = ["KIRA6 compound", "AML cell lines", "Cell culture facilities"]
    mock_protocol.timeline = "6 months"
    mock_protocol.success_metrics = ["Cell viability reduction", "IRE1α activity measurement", "Effectiveness metrics"]
    mock_protocol.expected_outcomes = ["Cell viability reduction", "IRE1α activity measurement"]
    mock_protocol.potential_challenges = ["Drug solubility", "Cell line variability"]
    mock_protocol.safety_considerations = ["BSL-2 safety protocols", "Chemical handling procedures"]
    
    mock_hypothesis.experimental_protocol = mock_protocol
    mock_hypothesis.supporting_evidence = []
    
    # Set up the mock to return different hypotheses based on input
    def generate_hypothesis_side_effect(*args, **kwargs):
        # Check generation method in kwargs
        generation_method = kwargs.get('generation_method', '')
        goal = kwargs.get('goal', '')
        constraints = kwargs.get('constraints', [])
        
        # Check generation method first (highest priority)
        if generation_method == 'debate':
            debate_hypothesis = MagicMock()
            debate_hypothesis.id = "debate-hypothesis-123"
            debate_hypothesis.summary = "Hypothesis about whale communication synthesized from 3 debate perspectives"
            debate_hypothesis.category = "theoretical"
            debate_hypothesis.full_description = "Novel theory on whale communication patterns"
            debate_hypothesis.novelty_claim = "Whales use communication for complex social structures"
            debate_hypothesis.assumptions = ["Whales have complex social needs", "Communication patterns are learnable", "Multi-perspective analysis improves understanding"]
            debate_hypothesis.reasoning = "Synthesized from debate perspectives"
            debate_hypothesis.confidence_score = 0.75
            debate_hypothesis.generation_method = "debate"
            debate_hypothesis.created_at = "2024-01-01T00:00:00Z"
            debate_hypothesis.experimental_protocol = mock_protocol
            debate_hypothesis.supporting_evidence = []
            return debate_hypothesis

        elif generation_method == 'assumptions':
            # Check if this has natural/plant constraints and adjust response accordingly
            if any('natural' in str(c).lower() or 'plant' in str(c).lower() for c in constraints):
                assumptions_hypothesis = MagicMock()
                assumptions_hypothesis.id = "natural-assumptions-hypothesis-123"
                assumptions_hypothesis.summary = "Hypothesis addressing: Find treatments using only natural compounds"
                assumptions_hypothesis.category = "therapeutic"
                assumptions_hypothesis.full_description = "Using natural plant compounds based on testable assumptions"
                assumptions_hypothesis.novelty_claim = "Novel use of natural compounds with assumption-based approach"
                assumptions_hypothesis.assumptions = ["Natural compounds are safer", "Plant-based treatments are effective", "Assumption-based approach is valid"]
                assumptions_hypothesis.reasoning = "Based on natural compound assumptions"
                assumptions_hypothesis.confidence_score = 0.80
                assumptions_hypothesis.generation_method = "assumptions"
                assumptions_hypothesis.created_at = "2024-01-01T00:00:00Z"
                assumptions_hypothesis.experimental_protocol = mock_protocol
                assumptions_hypothesis.supporting_evidence = []
                return assumptions_hypothesis
            else:
                assumptions_hypothesis = MagicMock()
                assumptions_hypothesis.id = "assumptions-hypothesis-123"
                assumptions_hypothesis.summary = "Hypothesis based on key testable assumptions"
                assumptions_hypothesis.category = "mechanistic"
                # Make description research-specific based on goal
                if 'ice' in goal.lower() and 'float' in goal.lower():
                    assumptions_hypothesis.full_description = "Hypothesis about ice density and buoyancy mechanisms"
                elif 'unit testing' in goal.lower():
                    assumptions_hypothesis.full_description = "Hypothesis about density mechanisms in test scenarios"
                else:
                    assumptions_hypothesis.full_description = "Hypothesis built from systematic analysis of testable assumptions"
                assumptions_hypothesis.novelty_claim = "Novel approach based on testable assumptions"
                assumptions_hypothesis.assumptions = ["Test assumption 1", "Test assumption 2", "Test assumption 3"]
                assumptions_hypothesis.reasoning = "Based on systematic assumption analysis"
                assumptions_hypothesis.confidence_score = 0.80
                assumptions_hypothesis.generation_method = "assumptions"
                assumptions_hypothesis.created_at = "2024-01-01T00:00:00Z"
                assumptions_hypothesis.experimental_protocol = mock_protocol
                assumptions_hypothesis.supporting_evidence = []
                return assumptions_hypothesis

        # Check if this is for natural/plant constraints (but also respect generation method)
        elif any('natural' in str(c).lower() or 'plant' in str(c).lower() for c in constraints):
            natural_hypothesis = MagicMock()
            natural_hypothesis.id = "natural-hypothesis-123"
            natural_hypothesis.summary = "Hypothesis addressing: Find treatments using only natural compounds"
            natural_hypothesis.category = "therapeutic"
            natural_hypothesis.full_description = "Using natural plant compounds to treat disease"
            natural_hypothesis.novelty_claim = "Novel use of natural compounds"
            natural_hypothesis.assumptions = ["Natural compounds are safer", "Plant-based treatments are effective"]
            natural_hypothesis.reasoning = "Based on traditional medicine"
            natural_hypothesis.confidence_score = 0.80
            natural_hypothesis.generation_method = generation_method or "assumptions"  # Use provided method or default
            natural_hypothesis.created_at = "2024-01-01T00:00:00Z"
            natural_hypothesis.experimental_protocol = mock_protocol
            natural_hypothesis.supporting_evidence = []
            return natural_hypothesis
        
        # Check if this is for expansion method
        elif generation_method == 'expansion':
            expansion_hypothesis = MagicMock()
            expansion_hypothesis.id = "expansion-hypothesis-123"
            expansion_hypothesis.summary = "Expanded hypothesis building on existing research networks"
            expansion_hypothesis.category = "mechanistic"
            expansion_hypothesis.full_description = "Extended hypothesis that builds on network system understanding"
            expansion_hypothesis.novelty_claim = "Novel extension that builds upon existing framework"
            expansion_hypothesis.assumptions = ["Network effects are measurable", "System expansion is possible"]
            expansion_hypothesis.reasoning = "Expansion of previous research"
            expansion_hypothesis.confidence_score = 0.85
            expansion_hypothesis.generation_method = "expansion"
            expansion_hypothesis.created_at = "2024-01-01T00:00:00Z"
            expansion_hypothesis.experimental_protocol = mock_protocol
            expansion_hypothesis.supporting_evidence = []
            return expansion_hypothesis

        # Check if this is for literature-based with citations
        elif generation_method == 'literature_based':
            lit_hypothesis = MagicMock()
            lit_hypothesis.id = "lit-hypothesis-123"
            lit_hypothesis.summary = "Test hypothesis for KIRA6 inhibition of IRE1α in AML treatment"
            lit_hypothesis.category = "therapeutic"
            lit_hypothesis.full_description = "KIRA6 selectively inhibits IRE1α kinase activity"
            lit_hypothesis.novelty_claim = "Novel use of KIRA6 for AML"
            lit_hypothesis.assumptions = ["IRE1α is overactive in AML"]
            lit_hypothesis.reasoning = "Based on literature"
            lit_hypothesis.confidence_score = 0.85
            lit_hypothesis.generation_method = "literature_based"
            lit_hypothesis.created_at = "2024-01-01T00:00:00Z"
            lit_hypothesis.experimental_protocol = mock_protocol
            lit_hypothesis.supporting_evidence = [{"doi": "10.1234/test", "citation": "Test et al., 2024"}]
            return lit_hypothesis
        
        # Default hypothesis
        return mock_hypothesis
    
    mock_b.GenerateHypothesis = AsyncMock(side_effect=generate_hypothesis_side_effect)
    mock_b.EvaluateHypothesis = AsyncMock()
    mock_b.PerformSafetyCheck = AsyncMock()
    mock_b.CompareHypotheses = AsyncMock()
    mock_b.EnhanceHypothesis = AsyncMock()
    mock_b.CalculateSimilarity = AsyncMock()
    mock_b.ExtractResearchPatterns = AsyncMock()
    mock_b.ParseResearchGoal = AsyncMock()

    # Add future BAML functions that will be needed in upcoming phases
    # Phase 9-10: Supervisor and Generation
    mock_b.PlanResearchStrategy = AsyncMock()
    mock_b.DetermineTaskPriority = AsyncMock()
    mock_b.ConductScientificDebate = AsyncMock()
    mock_b.AnalyzeLiteratureForHypothesis = AsyncMock()

    # Phase 11: Reflection
    # GenerateReview mock with proper Review structure
    def generate_review_side_effect(*args, **kwargs):
        review_type = kwargs.get('review_type', 'initial')
        hypothesis = kwargs.get('hypothesis')

        mock_review = MagicMock()
        mock_review.id = f"review-{hypothesis.id if hypothesis else 'test'}"
        mock_review.hypothesis_id = hypothesis.id if hypothesis else "test-hypothesis-123"
        mock_review.reviewer_agent_id = "reflection-agent"
        mock_review.review_type = review_type
        mock_review.decision = "accept"

        # Mock ReviewScores
        mock_scores = MagicMock()
        mock_scores.correctness = 0.85
        mock_scores.quality = 0.80
        mock_scores.novelty = 0.75
        mock_scores.safety = 0.90
        mock_scores.feasibility = 0.70
        mock_review.scores = mock_scores

        mock_review.narrative_feedback = f"This is a {review_type} review providing comprehensive feedback"
        mock_review.key_strengths = ["Strong scientific basis", "Novel approach"]
        mock_review.key_weaknesses = ["Needs more evidence", "Resource intensive"]
        mock_review.improvement_suggestions = ["Add more citations", "Simplify protocol"]
        mock_review.confidence_level = "high"
        mock_review.assumption_decomposition = None
        mock_review.simulation_results = None
        mock_review.literature_citations = []
        mock_review.created_at = "2024-01-01T00:00:00Z"
        mock_review.time_spent_seconds = 5.0

        return mock_review

    mock_b.GenerateReview = AsyncMock(side_effect=generate_review_side_effect)

    # GenerateCritique mock with proper Review structure including special fields
    def generate_critique_side_effect(*args, **kwargs):
        critique_type = kwargs.get('critique_type', 'deep_verification')
        hypothesis = kwargs.get('hypothesis')

        mock_review = MagicMock()
        mock_review.id = f"critique-{hypothesis.id if hypothesis else 'test'}"
        mock_review.hypothesis_id = hypothesis.id if hypothesis else "test-hypothesis-123"
        mock_review.reviewer_agent_id = "reflection-agent"
        mock_review.review_type = critique_type
        mock_review.decision = "revise"

        # Mock ReviewScores
        mock_scores = MagicMock()
        mock_scores.correctness = 0.75
        mock_scores.quality = 0.70
        mock_scores.novelty = 0.80
        mock_scores.safety = 0.90
        mock_scores.feasibility = 0.65
        mock_review.scores = mock_scores

        mock_review.narrative_feedback = f"This is a {critique_type} critique with deep analysis"
        mock_review.key_strengths = ["Interesting approach", "Novel perspective"]
        mock_review.key_weaknesses = ["Some assumptions need validation", "Experimental challenges"]
        mock_review.improvement_suggestions = ["Validate key assumptions", "Simplify experimental design"]
        mock_review.confidence_level = "medium"
        mock_review.literature_citations = []
        mock_review.created_at = "2024-01-01T00:00:00Z"
        mock_review.time_spent_seconds = 15.0

        # Add critique-specific fields based on type
        if critique_type == "deep_verification":
            # Mock assumption decomposition
            mock_decomposition = []
            if hypothesis and hasattr(hypothesis, 'assumptions'):
                for assumption in hypothesis.assumptions[:3]:  # Limit to first 3
                    mock_assumption = MagicMock()
                    mock_assumption.assumption = assumption
                    mock_assumption.validity = "questionable"
                    mock_assumption.evidence = f"Needs more evidence for: {assumption}"
                    mock_assumption.criticality = "fundamental"
                    mock_decomposition.append(mock_assumption)
            mock_review.assumption_decomposition = mock_decomposition
            mock_review.simulation_results = None
        elif critique_type == "simulation":
            # Mock simulation results
            mock_simulation = MagicMock()
            mock_simulation.mechanism_steps = [
                "Step 1: Initial compound binding",
                "Step 2: Conformational change",
                "Step 3: Signal cascade activation",
                "Step 4: Downstream effects"
            ]

            # Mock failure points
            mock_failure_points = []
            mock_failure1 = MagicMock()
            mock_failure1.step = "Step 2: Conformational change"
            mock_failure1.probability = 0.3
            mock_failure1.impact = "Would prevent downstream signaling"
            mock_failure_points.append(mock_failure1)

            mock_failure2 = MagicMock()
            mock_failure2.step = "Step 3: Signal cascade activation"
            mock_failure2.probability = 0.2
            mock_failure2.impact = "Reduced efficacy but not complete failure"
            mock_failure_points.append(mock_failure2)

            mock_simulation.failure_points = mock_failure_points
            mock_simulation.predicted_outcomes = [
                "Expected reduction in target activity",
                "Possible off-target effects",
                "Time-dependent response"
            ]

            mock_review.simulation_results = mock_simulation
            mock_review.assumption_decomposition = None
        else:
            mock_review.assumption_decomposition = None
            mock_review.simulation_results = None

        return mock_review

    mock_b.GenerateCritique = AsyncMock(side_effect=generate_critique_side_effect)
    mock_b.PerformQuickReview = AsyncMock()
    mock_b.SimulateExperimentalMechanism = AsyncMock()

    # Phase 12: Ranking - Multi-turn debate comparison
    def generate_comparison_reasoning_side_effect(*args, **kwargs):
        """Mock for multi-turn debate comparison."""
        hypothesis1 = kwargs.get('hypothesis1')
        hypothesis2 = kwargs.get('hypothesis2')
        debate_round = kwargs.get('debate_round', 1)

        mock_result = MagicMock()
        # Winner alternates or based on some logic
        mock_result.winner_id = hypothesis1.id if debate_round % 2 == 0 else hypothesis2.id
        mock_result.confidence = 0.6 if debate_round < 4 else 0.85
        mock_result.reasoning = f"Round {debate_round} debate reasoning comparing the hypotheses"
        mock_result.strengths_h1 = ["Strong experimental design", "Novel mechanism"]
        mock_result.strengths_h2 = ["Better safety profile", "More feasible timeline"]
        mock_result.decisive_factors = [
            "Experimental feasibility",
            "Safety considerations",
            "Scientific impact"
        ]
        return mock_result

    mock_b.GenerateComparisonReasoning = AsyncMock(side_effect=generate_comparison_reasoning_side_effect)

    # Phase 13: Evolution - Hypothesis Evolution Functions
    def evolve_hypothesis_side_effect(*args, **kwargs):
        """Mock for EvolveHypothesis BAML function."""
        original_hypothesis = kwargs.get('original_hypothesis')
        evolution_strategy = kwargs.get('evolution_strategy', 'refine')
        feedback = kwargs.get('feedback', [])

        # Create evolved hypothesis
        evolved_hypothesis = MagicMock()
        evolved_hypothesis.id = f"evolved-{original_hypothesis.id if original_hypothesis else 'test'}"
        evolved_hypothesis.summary = f"Evolved: {original_hypothesis.summary if original_hypothesis else 'test hypothesis'}"
        evolved_hypothesis.category = original_hypothesis.category if original_hypothesis else "therapeutic"

        if evolution_strategy == "refine":
            evolved_hypothesis.full_description = f"Refined version with stronger evidence: {original_hypothesis.full_description if original_hypothesis else 'test'}"
            evolved_hypothesis.novelty_claim = "Enhanced novelty with additional evidence"
            evolved_hypothesis.confidence_score = 0.90
        elif evolution_strategy == "simplify":
            evolved_hypothesis.full_description = "Simplified version focusing on core mechanism"
            evolved_hypothesis.novelty_claim = "Streamlined approach for easier testing"
            evolved_hypothesis.confidence_score = 0.85
        else:
            evolved_hypothesis.full_description = f"Evolved: {original_hypothesis.full_description if original_hypothesis else 'test'}"
            evolved_hypothesis.novelty_claim = "Evolved novelty claim"
            evolved_hypothesis.confidence_score = 0.88

        evolved_hypothesis.assumptions = ["Evolved assumption 1", "Evolved assumption 2", "Evolved assumption 3"]
        evolved_hypothesis.reasoning = f"Evolution strategy '{evolution_strategy}' applied with feedback"
        evolved_hypothesis.generation_method = f"evolution_{evolution_strategy}"
        evolved_hypothesis.created_at = "2024-01-01T00:00:00Z"
        evolved_hypothesis.experimental_protocol = mock_protocol
        evolved_hypothesis.supporting_evidence = []

        return evolved_hypothesis

    def crossover_hypotheses_side_effect(*args, **kwargs):
        """Mock for CrossoverHypotheses BAML function."""
        hypothesis1 = kwargs.get('hypothesis1')
        hypothesis2 = kwargs.get('hypothesis2')

        # Create combined hypothesis
        combined_hypothesis = MagicMock()
        combined_hypothesis.id = "crossover-combined-123"
        combined_hypothesis.summary = f"Combined: {hypothesis1.summary if hypothesis1 else 'H1'} + {hypothesis2.summary if hypothesis2 else 'H2'}"
        combined_hypothesis.category = hypothesis1.category if hypothesis1 else "therapeutic"
        combined_hypothesis.full_description = "Unified hypothesis integrating mechanisms from both parent hypotheses"
        combined_hypothesis.novelty_claim = "Synergistic combination of complementary approaches"
        combined_hypothesis.assumptions = ["Combined assumption 1", "Combined assumption 2", "Combined assumption 3"]
        combined_hypothesis.reasoning = "Synthesis of complementary mechanisms and approaches"
        combined_hypothesis.confidence_score = 0.88
        combined_hypothesis.generation_method = "evolution_crossover"
        combined_hypothesis.created_at = "2024-01-01T00:00:00Z"
        combined_hypothesis.experimental_protocol = mock_protocol
        combined_hypothesis.supporting_evidence = []

        return combined_hypothesis

    def mutate_hypothesis_side_effect(*args, **kwargs):
        """Mock for MutateHypothesis BAML function."""
        original_hypothesis = kwargs.get('original_hypothesis')
        mutation_guidance = kwargs.get('mutation_guidance')

        # Create mutated hypothesis with paradigm shift
        mutated_hypothesis = MagicMock()
        mutated_hypothesis.id = f"mutated-{original_hypothesis.id if original_hypothesis else 'test'}"
        mutated_hypothesis.summary = f"Paradigm shift: {original_hypothesis.summary if original_hypothesis else 'test hypothesis'}"
        mutated_hypothesis.category = "methodology"  # Often changes category
        mutated_hypothesis.full_description = "Radically transformed hypothesis using unconventional approach from different domain"
        mutated_hypothesis.novelty_claim = "Paradigm-shifting approach challenging fundamental assumptions"
        mutated_hypothesis.assumptions = ["Radical assumption 1", "Unconventional assumption 2", "Cross-domain insight"]
        mutated_hypothesis.reasoning = "Applied cross-domain analogy and challenged core assumptions"
        mutated_hypothesis.confidence_score = 0.75  # Lower due to novelty
        mutated_hypothesis.generation_method = "evolution_mutation"
        mutated_hypothesis.created_at = "2024-01-01T00:00:00Z"
        mutated_hypothesis.experimental_protocol = mock_protocol
        mutated_hypothesis.supporting_evidence = []

        return mutated_hypothesis

    mock_b.EvolveHypothesis = AsyncMock(side_effect=evolve_hypothesis_side_effect)
    mock_b.CrossoverHypotheses = AsyncMock(side_effect=crossover_hypotheses_side_effect)
    mock_b.MutateHypothesis = AsyncMock(side_effect=mutate_hypothesis_side_effect)

    # Phase 15: Meta-Review - New BAML functions
    def synthesize_findings_side_effect(*args, **kwargs):
        """Mock for SynthesizeFindings BAML function."""
        top_hypotheses = kwargs.get('top_hypotheses', [])
        research_goal = kwargs.get('research_goal', '')
        iteration_number = kwargs.get('iteration_number', 1)

        # Create mock research overview
        mock_overview = MagicMock()
        mock_overview.executive_summary = f"Research overview for {len(top_hypotheses)} hypotheses at iteration {iteration_number}"

        # Mock research areas
        mock_area = MagicMock()
        mock_area.area_title = "Epigenetic Modulation for Disease Treatment"
        mock_area.importance_justification = "Epigenetic changes are reversible and offer non-invasive intervention potential"
        mock_area.key_hypotheses = [h.id for h in top_hypotheses[:3]] if top_hypotheses else ["hyp_001", "hyp_002"]

        # Mock proposed experiments
        mock_experiment = MagicMock()
        mock_experiment.experiment_description = "Screen HDAC6-specific inhibitors in target cells"
        mock_experiment.expected_outcomes = "30-50% reduction in disease markers"
        mock_experiment.resource_requirements = "Primary cells, inhibitor library, 6 months timeline"
        mock_area.proposed_experiments = [mock_experiment]

        # Mock citations
        mock_citation = MagicMock()
        mock_citation.authors = ["Smith, J", "Jones, A"]
        mock_citation.title = "HDAC inhibitors in disease"
        mock_citation.journal = "Nature Medicine"
        mock_citation.year = 2023
        mock_citation.doi = "10.1038/test"
        mock_citation.url = "https://test.com"
        mock_area.related_literature = [mock_citation]

        mock_overview.research_areas = [mock_area]
        mock_overview.cross_cutting_themes = [
            "Targeting cellular plasticity",
            "Reversibility over prevention",
            "Combining multiple approaches"
        ]
        mock_overview.innovation_highlights = [
            "Novel KDM4A targeting approach",
            "HDAC-BET inhibitor combination",
            "CRISPR-based screening methodology"
        ]
        mock_overview.risk_assessment = "Primary risks include off-target effects and translation challenges. Mitigation: early toxicity screening."
        mock_overview.recommended_next_steps = [
            "Validate top candidates experimentally",
            "Establish patient-derived models",
            "Initiate medicinal chemistry optimization"
        ]

        return mock_overview

    def extract_patterns_side_effect(*args, **kwargs):
        """Mock for ExtractPatterns BAML function."""
        hypotheses = kwargs.get('hypotheses', [])
        reviews = kwargs.get('reviews', [])
        focus_areas = kwargs.get('focus_areas', [])

        # Create mock meta-review critique
        mock_critique = MagicMock()
        mock_critique.synthesis_summary = f"Analysis of {len(hypotheses)} hypotheses and {len(reviews)} reviews reveals strong mechanistic reasoning"

        # Mock common patterns
        mock_pattern = MagicMock()
        mock_pattern.pattern_type = "missing_safety_protocols"
        mock_pattern.frequency = 15
        mock_pattern.description = "Hypotheses lack specific safety protocols for human studies"
        mock_pattern.impact_on_quality = "high"
        mock_pattern.examples = [hypotheses[i].id for i in range(min(3, len(hypotheses)))] if hypotheses else ["hyp_001", "hyp_002"]
        mock_critique.common_patterns = [mock_pattern]

        # Mock agent-specific feedback
        mock_agent_feedback = MagicMock()

        # Generation agent feedback
        mock_gen_feedback = MagicMock()
        mock_gen_feedback.strengths = [
            "Excellent literature grounding",
            "Creative mechanism combinations"
        ]
        mock_gen_feedback.improvement_areas = [
            "Resource estimates need detail",
            "Success metrics too vague"
        ]
        mock_gen_feedback.specific_recommendations = [
            "Add quantitative metrics template",
            "Include resource estimation tool"
        ]
        mock_agent_feedback.generation_agent = mock_gen_feedback

        # Reflection agent feedback
        mock_ref_feedback = MagicMock()
        mock_ref_feedback.strengths = ["Consistent scoring", "Good assumption analysis"]
        mock_ref_feedback.improvement_areas = ["Missed safety issues", "Inconsistent novelty assessment"]
        mock_ref_feedback.specific_recommendations = ["Add safety checklist", "Standardize novelty criteria"]
        mock_agent_feedback.reflection_agent = mock_ref_feedback

        # Ranking agent feedback
        mock_rank_feedback = MagicMock()
        mock_rank_feedback.strengths = ["Fair tournament pairing", "Meaningful Elo progression"]
        mock_rank_feedback.improvement_areas = ["Debate quality varies", "Generic decisive factors"]
        mock_rank_feedback.specific_recommendations = ["Structure debate prompts", "Require evidence-based factors"]
        mock_agent_feedback.ranking_agent = mock_rank_feedback

        # Evolution agent feedback
        mock_evo_feedback = MagicMock()
        mock_evo_feedback.strengths = ["Effective refinement", "Good mutation diversity"]
        mock_evo_feedback.improvement_areas = ["Verbose combinations", "Simplification loses details"]
        mock_evo_feedback.specific_recommendations = ["Add length constraints", "Preserve core assumptions"]
        mock_agent_feedback.evolution_agent = mock_evo_feedback

        mock_critique.agent_specific_feedback = mock_agent_feedback

        # Mock iteration improvements
        mock_improvements = MagicMock()
        mock_metrics_comparison = MagicMock()
        mock_metrics_comparison.previous_iteration_metrics = {"avg_correctness": 0.78, "avg_novelty": 0.72}
        mock_metrics_comparison.current_iteration_metrics = {"avg_correctness": 0.82, "avg_novelty": 0.76}
        mock_metrics_comparison.improvements = ["Correctness improved 5%", "Novelty improved 6%"]
        mock_metrics_comparison.regressions = ["Feasibility declined 2%"]
        mock_improvements.metrics_comparison = mock_metrics_comparison
        mock_improvements.progress_indicators = [
            "Faster Elo convergence",
            "Fewer rejections"
        ]
        mock_improvements.next_iteration_priorities = [
            "Improve feasibility assessment",
            "Address safety gaps"
        ]
        mock_critique.iteration_improvements = mock_improvements

        return mock_critique

    def generate_insights_side_effect(*args, **kwargs):
        """Mock for GenerateInsights BAML function."""
        patterns = kwargs.get('patterns', [])
        synthesis_summary = kwargs.get('synthesis_summary', '')

        # Create mock research patterns
        mock_insights = MagicMock()
        mock_insights.identified_patterns = [
            "Strong mechanistic hypothesis generation",
            "Experimental protocols lack quantitative metrics",
            "Safety considerations under-specified"
        ]
        mock_insights.common_strengths = [
            "Excellent scientific rigor",
            "Creative combinations",
            "Strong literature grounding"
        ]
        mock_insights.common_weaknesses = [
            "Resource specificity lacking",
            "Success metrics too qualitative",
            "Safety details missing"
        ]
        mock_insights.emerging_themes = [
            "Shift toward epigenetic approaches",
            "Focus on reversibility",
            "Integration of AI methods"
        ]
        mock_insights.recommendations = [
            "Add quantitative metrics requirements",
            "Create safety checklist",
            "Implement resource estimation tool",
            "Standardize novelty assessment"
        ]
        mock_insights.synthesis_summary = "Strong scientific foundations with systematic gaps in feasibility assessment and safety protocols"

        return mock_insights

    mock_b.SynthesizeFindings = AsyncMock(side_effect=synthesize_findings_side_effect)
    mock_b.ExtractPatterns = AsyncMock(side_effect=extract_patterns_side_effect)
    mock_b.GenerateInsights = AsyncMock(side_effect=generate_insights_side_effect)

    # Legacy Phase 15 mocks (kept for backward compatibility)
    mock_b.GenerateAgentFeedback = AsyncMock()
    mock_b.FormatResearchOverview = AsyncMock()
    
    # Phase 16: Natural Language Interface
    mock_b.InterpretUserFeedback = AsyncMock()
    mock_b.SummarizeResearchProgress = AsyncMock()
    
    # Create nested baml_client module for the actual import path
    mock_baml_client.baml_client = MagicMock()
    mock_baml_client.baml_client.b = mock_b
    
    # Mock type definitions with proper class structure
    mock_types = MagicMock()
    
    # Create mock classes for BAML types that accept arguments
    class MockBAMLType:
        def __init__(self, **kwargs):
            # Store all kwargs as attributes
            self._data = kwargs
            for k, v in kwargs.items():
                setattr(self, k, v)
        
        def __getattr__(self, name):
            # If attribute exists in _data, return it
            if hasattr(self, '_data') and name in self._data:
                return self._data[name]
            # Otherwise return a mock
            mock = MagicMock()
            # Store it so subsequent accesses return the same mock
            setattr(self, name, mock)
            return mock
    
    mock_types.Hypothesis = MockBAMLType
    mock_types.SafetyCheck = MockBAMLType
    mock_types.ParsedResearchGoal = MockBAMLType
    mock_types.AgentRequest = MockBAMLType
    mock_types.AgentResponse = MockBAMLType
    
    # Create enum-like objects for AgentType
    class MockEnumValue:
        def __init__(self, value):
            self.value = value
    
    mock_types.AgentType = MagicMock()
    mock_types.AgentType.Generation = MockEnumValue("Generation")
    mock_types.AgentType.Reflection = MockEnumValue("Reflection")
    mock_types.AgentType.Ranking = MockEnumValue("Ranking")
    mock_types.AgentType.Evolution = MockEnumValue("Evolution")
    mock_types.AgentType.Proximity = MockEnumValue("Proximity")
    mock_types.AgentType.MetaReview = MockEnumValue("MetaReview")
    mock_types.ComparisonResult = MockBAMLType
    mock_types.Pattern = MockBAMLType
    mock_types.ResearchTopic = MockBAMLType
    mock_types.SimilarityResult = MockBAMLType
    mock_types.Review = MockBAMLType
    
    # Create enum-like objects for ReviewType
    mock_types.ReviewType = MagicMock()
    mock_types.ReviewType.Initial = MockEnumValue("Initial")
    mock_types.ReviewType.Deep = MockEnumValue("Deep")
    mock_types.ReviewType.Observation = MockEnumValue("Observation")
    mock_types.ReviewType.Simulation = MockEnumValue("Simulation")
    mock_types.ReviewType.Tournament = MockEnumValue("Tournament")
    
    mock_types.ExperimentalProtocol = MockBAMLType
    
    # Add missing types that tests are trying to use with spec
    mock_types.SimilarityScore = MockBAMLType
    mock_types.ResearchPatterns = MockBAMLType
    mock_types.Task = MockBAMLType
    mock_types.Citation = MockBAMLType
    mock_types.ReviewScores = MockBAMLType
    mock_types.AssumptionDecomposition = MockBAMLType
    mock_types.FailurePoint = MockBAMLType
    mock_types.SimulationResults = MockBAMLType
    mock_types.RequestContent = MockBAMLType
    mock_types.RequestType = MagicMock()
    mock_types.RequestType.Generate = MockEnumValue("Generate")

    # Phase 15 Meta-Review types
    mock_types.MetaReviewCritique = MockBAMLType
    mock_types.ResearchOverview = MockBAMLType
    mock_types.CommonPattern = MockBAMLType
    mock_types.AgentFeedback = MockBAMLType
    mock_types.AgentSpecificFeedback = MockBAMLType
    mock_types.IterationImprovements = MockBAMLType
    mock_types.MetricsComparison = MockBAMLType
    mock_types.ResearchArea = MockBAMLType
    mock_types.ProposedExperiment = MockBAMLType
    mock_types.ResearchContact = MockBAMLType
    
    # Add missing enums
    mock_types.SafetyLevel = MagicMock()
    mock_types.SafetyLevel.Safe = MockEnumValue("Safe")
    mock_types.SafetyLevel.Concerning = MockEnumValue("Concerning")
    mock_types.SafetyLevel.Dangerous = MockEnumValue("Dangerous")
    
    mock_types.HypothesisCategory = MagicMock()
    mock_types.HypothesisCategory.Therapeutic = MockEnumValue("Therapeutic")
    mock_types.HypothesisCategory.Observational = MockEnumValue("Observational")
    mock_types.HypothesisCategory.Theoretical = MockEnumValue("Theoretical")
    
    mock_types.ReviewDecision = MagicMock()
    mock_types.ReviewDecision.Accept = MockEnumValue("Accept")
    mock_types.ReviewDecision.Reject = MockEnumValue("Reject")
    mock_types.ReviewDecision.Revise = MockEnumValue("Revise")
    
    mock_baml_client.baml_client.types = mock_types
    
    # Register all the mock modules
    sys.modules['baml_client'] = mock_baml_client
    sys.modules['baml_client.baml_client'] = mock_baml_client.baml_client
    sys.modules['baml_client.baml_client.types'] = mock_types
    sys.modules['baml_client.types'] = mock_types


# Test fixtures
@pytest.fixture
def mock_baml_wrapper():
    """Create mock BAML wrapper for testing agents."""
    from unittest.mock import MagicMock, AsyncMock

    wrapper = MagicMock()

    # Evolution methods
    wrapper.evolve_hypothesis = AsyncMock()
    wrapper.crossover_hypotheses = AsyncMock()
    wrapper.mutate_hypothesis = AsyncMock()

    # Comparison methods
    wrapper.compare_hypotheses = AsyncMock()
    wrapper.generate_comparison_reasoning = AsyncMock()

    # Generation methods
    wrapper.generate_hypothesis = AsyncMock()

    # Review methods
    wrapper.generate_review = AsyncMock()
    wrapper.generate_critique = AsyncMock()

    return wrapper