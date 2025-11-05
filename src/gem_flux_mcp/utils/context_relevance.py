import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

@dataclass
class ContextRecommendation:
    specs: List[str]
    confidence_score: float
    reasoning: str
    fallback_needed: bool = False

class SpecificationRelevanceScorer:
    def __init__(self, specs_directory: str = "specs/"):
        self.specs_dir = specs_directory
        self.cache = {}
        # Always include foundational specs
        self.critical_specs = ["001-system-overview.md", "002-data-formats.md"]

        # Domain keyword mappings for relevance scoring
        self.domain_keywords = {
            'tools': ['build_media', 'build_model', 'gapfill_model', 'run_fba', 'tool', 'mcp'],
            'database': ['database', 'compound', 'reaction', 'modelseed', 'lookup', 'search'],
            'testing': ['test', 'mock', 'pytest', 'integration', 'unit', 'coverage'],
            'modeling': ['model', 'genome', 'metabolic', 'template', 'fba', 'gapfill'],
            'session': ['session', 'storage', 'list_models', 'list_media', 'delete'],
            'media': ['media', 'growth', 'minimal', 'complete', 'cpd']
        }

        # Component name to spec file mapping
        # This ensures critical component specs are always included
        self.component_spec_map = {
            'build_media': '003-build-media-tool.md',
            'buildmedia': '003-build-media-tool.md',
            'build_model': '004-build-model-tool.md',
            'buildmodel': '004-build-model-tool.md',
            'gapfill_model': '005-gapfill-model-tool.md',
            'gapfillmodel': '005-gapfill-model-tool.md',
            'gapfill': '005-gapfill-model-tool.md',
            'run_fba': '006-run-fba-tool.md',
            'runfba': '006-run-fba-tool.md',
            'fba': '006-run-fba-tool.md',
            'database': '007-database-integration.md',
            'compound': '008-compound-lookup-tools.md',
            'compoundlookup': '008-compound-lookup-tools.md',
            'reaction': '009-reaction-lookup-tools.md',
            'reactionlookup': '009-reaction-lookup-tools.md',
            'storage': '010-model-storage.md',
            'modelstorage': '010-model-storage.md',
            'import': '011-model-import-export.md',
            'export': '011-model-import-export.md',
            'template': '017-template-management.md',
            'templatemanagement': '017-template-management.md',
            'session': '018-session-management-tools.md',
            'sessionmanagement': '018-session-management-tools.md',
            'list_models': '018-session-management-tools.md',
            'list_media': '018-session-management-tools.md',
            'delete_model': '018-session-management-tools.md',
            'media': '019-predefined-media-library.md',
            'predefinedmedia': '019-predefined-media-library.md',
        }

    def extract_task_keywords(self, task_description: str) -> Set[str]:
        """Extract domain-relevant keywords from task description."""
        words = set(re.findall(r'\b\w+\b', task_description.lower()))

        # Handle CamelCase by splitting it
        for word in list(words):
            # Split CamelCase words like "ReflectionAgent" -> ["reflection", "agent"]
            if len(word) > 5:  # Only split longer words
                # Insert spaces before capital letters and split
                camel_split = re.sub(r'([a-z])([A-Z])', r'\1 \2', task_description)
                extra_words = set(re.findall(r'\b\w+\b', camel_split.lower()))
                words.update(extra_words)

        # Add compound concepts
        if 'reflection' in words and 'agent' in words:
            words.add('reflection-agent')
            words.add('reflection')  # Ensure individual words are there too
            words.add('agent')
        if 'baml' in words and any(w in words for w in ['function', 'integration']):
            words.add('baml-integration')

        return words

    def _detect_component_spec(self, task_description: str, task_analysis: Dict[str, any] = None) -> str | None:
        """Detect and return the primary component specification file.

        This ensures that the spec defining the main component being worked on
        is always included, regardless of scoring.

        Args:
            task_description: The task description string
            task_analysis: Optional analysis dict with component info

        Returns:
            Spec filename if a primary component is detected, None otherwise
        """
        task_lower = task_description.lower()

        # Priority 0: For agent implementation phases (8-15), guarantee phase-specific agent spec
        # This ensures agent specs are always included even for infrastructure tasks like BAML
        if task_analysis and 'phase' in task_analysis:
            phase = task_analysis['phase']
            # Agent implementation phases
            if phase in [8, 9, 10, 11, 12, 13, 14, 15]:
                phase_specs = self.get_phase_specific_specs(phase)
                if phase_specs and phase_specs[0].endswith('-agent.md'):
                    # This is an agent spec - guarantee it for agent phases
                    logger.info(f"✓ Component spec detected via phase: {phase_specs[0]} (Phase {phase} agent implementation)")
                    return phase_specs[0]

        # Priority 1: Check task analysis for explicit components
        if task_analysis and 'components' in task_analysis:
            components = task_analysis['components']
            if components:
                # Take the first component as primary
                primary_component = components[0].lower().replace('_', '').replace('-', '')
                if primary_component in self.component_spec_map:
                    detected_spec = self.component_spec_map[primary_component]
                    logger.info(f"✓ Component spec detected via analysis: {detected_spec} (from component: {components[0]})")
                    return detected_spec

        # Priority 2: Direct pattern matching in task description
        # Look for component names (case-insensitive, handle variations)
        for component_key, spec_file in self.component_spec_map.items():
            # Match whole word or as part of compound (e.g., "EvolutionAgent")
            pattern = r'\b' + re.escape(component_key) + r'\b'
            if re.search(pattern, task_lower):
                logger.info(f"✓ Component spec detected via pattern matching: {spec_file} (keyword: {component_key})")
                return spec_file

        # Priority 3: Check for agent-related tasks with specific agent type
        agent_match = re.search(r'(\w+)agent', task_lower)
        if agent_match:
            agent_type = agent_match.group(1)
            if agent_type in self.component_spec_map:
                detected_spec = self.component_spec_map[agent_type]
                logger.info(f"✓ Component spec detected via agent pattern: {detected_spec} (agent: {agent_type})")
                return detected_spec

        logger.debug("No primary component spec detected for this task")
        return None

    def score_specification(self, task_keywords: Set[str], spec_path: str) -> float:
        """Score a single specification for relevance to task."""
        if spec_path in self.cache:
            spec_content = self.cache[spec_path]
        else:
            try:
                with open(os.path.join(self.specs_dir, spec_path), 'r') as f:
                    spec_content = f.read().lower()
                self.cache[spec_path] = spec_content
            except FileNotFoundError:
                return 0.0

        # Check spec filename for keywords
        filename_score = 0.0
        spec_name_lower = spec_path.lower()
        for keyword in task_keywords:
            if keyword in spec_name_lower:
                filename_score += 0.3

        spec_words = set(re.findall(r'\b\w+\b', spec_content))

        # Calculate keyword coverage (what % of task keywords appear in spec)
        # This is better than Jaccard for large documents
        intersection = task_keywords.intersection(spec_words)
        if len(task_keywords) > 0:
            base_score = len(intersection) / len(task_keywords)
        else:
            base_score = 0.0

        # Combine filename and content scores
        combined_score = min(1.0, base_score + filename_score)

        # Apply domain weighting
        weighted_score = self.apply_domain_weighting(combined_score, task_keywords, spec_path)

        return min(1.0, weighted_score)

    def apply_domain_weighting(self, base_score: float, task_keywords: Set[str], spec_path: str) -> float:
        """Apply domain-specific weighting to relevance scores."""
        weight_multiplier = 1.0

        # Boost tool specs for tool-related tasks
        if any(kw in task_keywords for kw in self.domain_keywords['tools']):
            if any(tool in spec_path for tool in [
                'build-media', 'build-model', 'gapfill', 'run-fba'
            ]):
                weight_multiplier += 0.3

        # Boost database specs for database/lookup tasks
        if any(kw in task_keywords for kw in self.domain_keywords['database']):
            if any(db in spec_path for db in ['database', 'compound', 'reaction']):
                weight_multiplier += 0.3

        # Boost modeling specs for metabolic modeling tasks
        if any(kw in task_keywords for kw in self.domain_keywords['modeling']):
            if any(model in spec_path for model in ['model', 'template', 'genome']):
                weight_multiplier += 0.2

        # Boost testing specs for test implementation
        if any(kw in task_keywords for kw in self.domain_keywords['testing']):
            if 'test' in spec_path:
                weight_multiplier += 0.2

        return base_score * weight_multiplier

    def select_optimal_specs(self, task_description: str, max_specs: int = 5) -> ContextRecommendation:
        """Select optimal specifications for current task."""
        task_keywords = self.extract_task_keywords(task_description)

        # Always include critical specs
        selected_specs = list(self.critical_specs)

        # Score all available specs
        spec_scores = []
        for spec_file in os.listdir(self.specs_dir):
            if spec_file.endswith('.md') and spec_file not in self.critical_specs:
                score = self.score_specification(task_keywords, spec_file)
                spec_scores.append((spec_file, score))

        # Sort by relevance and select top specs
        spec_scores.sort(key=lambda x: x[1], reverse=True)

        remaining_slots = max_specs - len(selected_specs)
        relevance_threshold = 0.15  # Lowered from 0.3

        for spec_file, score in spec_scores:
            if remaining_slots <= 0:
                break
            if score >= relevance_threshold:
                selected_specs.append(spec_file)
                remaining_slots -= 1

        # Calculate confidence based on whether we found relevant specs
        if len(spec_scores) > 0:
            top_scores = [score for _, score in spec_scores[:3]]
            avg_top_score = sum(top_scores) / len(top_scores) if top_scores else 0
            confidence = min(1.0, avg_top_score * 2)  # Scale up the confidence
        else:
            confidence = 0.0

        # Generate reasoning
        reasoning = f"Selected {len(selected_specs)} specs based on task keywords: {', '.join(list(task_keywords)[:5])}"

        return ContextRecommendation(
            specs=selected_specs,
            confidence_score=confidence,
            reasoning=reasoning,
            fallback_needed=confidence < 0.4  # Lowered from 0.6
        )

    def analyze_task_context(self, task_description: str, current_phase: int) -> Dict[str, any]:
        """Analyze task for enhanced context understanding."""

        analysis = {
            'phase': current_phase,
            'task_type': self.detect_task_type(task_description),
            'components': self.extract_components(task_description),
            'domain': self.identify_domain(task_description),
            'complexity': self.assess_complexity(task_description)
        }

        return analysis

    def detect_task_type(self, task_description: str) -> str:
        """Detect the type of implementation task."""
        task_lower = task_description.lower()

        if any(keyword in task_lower for keyword in ['test', 'testing', 'unit test', 'integration test']):
            return 'testing'
        elif any(keyword in task_lower for keyword in ['build_media', 'build_model', 'gapfill', 'run_fba', 'tool']):
            return 'tool_implementation'
        elif any(keyword in task_lower for keyword in ['database', 'compound', 'reaction', 'lookup']):
            return 'database_integration'
        elif any(keyword in task_lower for keyword in ['session', 'storage', 'list', 'delete']):
            return 'session_management'
        elif any(keyword in task_lower for keyword in ['template', 'media', 'predefined']):
            return 'infrastructure'
        else:
            return 'general'

    def extract_components(self, task_description: str) -> List[str]:
        """Extract system components mentioned in task."""
        components = []
        component_patterns = {
            'build_media': ['build_media', 'media creation', 'growth media'],
            'build_model': ['build_model', 'model building', 'genome', 'rast', 'fasta'],
            'gapfill_model': ['gapfill', 'gap fill', 'gapfilling'],
            'run_fba': ['fba', 'flux balance', 'optimize', 'simulation'],
            'database': ['database', 'modelseed', 'compounds.tsv', 'reactions.tsv'],
            'compound_lookup': ['compound', 'cpd', 'lookup compound'],
            'reaction_lookup': ['reaction', 'rxn', 'lookup reaction'],
            'model_storage': ['storage', 'session', 'store model'],
            'template_management': ['template', 'gramnegative', 'core'],
            'session_tools': ['list_models', 'list_media', 'delete_model'],
            'predefined_media': ['minimal', 'complete', 'rich', 'predefined']
        }

        task_lower = task_description.lower()
        for component, keywords in component_patterns.items():
            if any(keyword in task_lower for keyword in keywords):
                components.append(component)

        return components

    def identify_domain(self, task_description: str) -> str:
        """Identify the primary domain of the task."""
        task_lower = task_description.lower()

        # Count matches for each domain
        domain_scores = {}
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in task_lower)
            if score > 0:
                domain_scores[domain] = score

        if not domain_scores:
            return 'general'

        # Return domain with highest score
        return max(domain_scores, key=domain_scores.get)

    def assess_complexity(self, task_description: str) -> str:
        """Assess the complexity level of the task."""
        task_lower = task_description.lower()

        # High complexity indicators
        high_indicators = ['integration', 'coordination', 'multiple', 'complex', 'comprehensive']
        # Medium complexity indicators
        medium_indicators = ['implement', 'create', 'add', 'enhance', 'update']
        # Low complexity indicators
        low_indicators = ['test', 'fix', 'update', 'simple', 'basic']

        high_count = sum(1 for indicator in high_indicators if indicator in task_lower)
        medium_count = sum(1 for indicator in medium_indicators if indicator in task_lower)
        low_count = sum(1 for indicator in low_indicators if indicator in task_lower)

        if high_count >= 2 or 'integration' in task_lower:
            return 'high'
        elif medium_count > low_count:
            return 'medium'
        else:
            return 'low'

    def select_optimal_specs_with_analysis(self, task_description: str, task_analysis: Dict[str, any], max_specs: int = 6) -> ContextRecommendation:
        """Select optimal specifications using enhanced task analysis.

        Selection Strategy (Option B - Structural Fix):
        1. Always include 3 critical specs (system overview, principles, workflow)
        2. Detect and GUARANTEE inclusion of primary component spec (if found)
        3. Fill remaining slots with highest-scored specs

        This ensures the spec defining the main component being worked on
        is NEVER missed, even if infrastructure specs score higher.
        """
        task_keywords = self.extract_task_keywords(task_description)

        # Step 1: Always include critical specs (3 slots)
        selected_specs = list(self.critical_specs)

        # Step 2: Detect and guarantee primary component spec (1 slot if found)
        component_spec = self._detect_component_spec(task_description, task_analysis)
        component_guaranteed = False

        if component_spec:
            if component_spec in selected_specs:
                logger.info(f"✓ Component spec {component_spec} already in critical specs")
                remaining_slots = max_specs - 3
            else:
                selected_specs.append(component_spec)
                component_guaranteed = True
                logger.info(f"✓ GUARANTEED component spec inclusion: {component_spec}")
                # Remaining slots = max_specs - 3 critical - 1 component
                remaining_slots = max_specs - 4
        else:
            # No component spec detected
            logger.debug("No component spec detected - using score-based selection only")
            # Remaining slots = max_specs - 3 critical
            remaining_slots = max_specs - 3

        # Step 3: Score all available specs with enhanced analysis
        spec_scores = []
        for spec_file in os.listdir(self.specs_dir):
            # Skip specs already selected (critical or component)
            if spec_file.endswith('.md') and spec_file not in selected_specs:
                base_score = self.score_specification(task_keywords, spec_file)

                # Apply enhanced scoring based on analysis
                enhanced_score = self.enhance_score_with_analysis(base_score, spec_file, task_analysis)
                spec_scores.append((spec_file, enhanced_score))

        # Sort by relevance and fill remaining slots
        spec_scores.sort(key=lambda x: x[1], reverse=True)

        relevance_threshold = 0.15

        for spec_file, score in spec_scores:
            if remaining_slots <= 0:
                break
            if score >= relevance_threshold:
                selected_specs.append(spec_file)
                remaining_slots -= 1

        # Calculate enhanced confidence
        if len(spec_scores) > 0:
            top_scores = [score for _, score in spec_scores[:3]]
            avg_top_score = sum(top_scores) / len(top_scores) if top_scores else 0

            # Boost confidence for phase-appropriate selections
            phase_boost = self.get_phase_confidence_boost(task_analysis['phase'], selected_specs)
            confidence = min(1.0, (avg_top_score * 2) + phase_boost)
        else:
            confidence = 0.0

        # Boost confidence if we successfully detected and included component spec
        if component_guaranteed:
            confidence = min(1.0, confidence + 0.1)

        # Generate enhanced reasoning
        components_str = ', '.join(task_analysis['components'][:3]) if task_analysis['components'] else 'general'
        reasoning = f"Selected {len(selected_specs)} specs for {task_analysis['task_type']} task (Phase {task_analysis['phase']}) involving {components_str}"
        if component_guaranteed:
            reasoning += f" [component spec guaranteed: {component_spec}]"

        # Log final selection for debugging
        logger.info(f"📋 Final spec selection: {' '.join(selected_specs)}")
        logger.info(f"🎯 Confidence: {confidence:.2f} | Reasoning: {reasoning}")

        return ContextRecommendation(
            specs=selected_specs,
            confidence_score=confidence,
            reasoning=reasoning,
            fallback_needed=confidence < 0.4
        )

    def enhance_score_with_analysis(self, base_score: float, spec_file: str, task_analysis: Dict[str, any]) -> float:
        """Enhance spec score based on task analysis."""
        enhanced_score = base_score

        # Component-based enhancement
        for component in task_analysis['components']:
            if component.lower() in spec_file.lower():
                enhanced_score += 0.4

        # Phase-specific enhancement
        phase_specs = self.get_phase_specific_specs(task_analysis['phase'])
        if spec_file in phase_specs:
            enhanced_score += 0.3

        # Domain-specific enhancement
        domain = task_analysis['domain']
        if domain == 'tools' and 'tool' in spec_file:
            enhanced_score += 0.2
        elif domain == 'database' and ('database' in spec_file or 'lookup' in spec_file):
            enhanced_score += 0.2
        elif domain == 'modeling' and any(model in spec_file for model in ['model', 'template', 'media']):
            enhanced_score += 0.2

        # For tool phases, boost related tool specs (tools that the primary tool depends on)
        phase = task_analysis['phase']
        if phase in [4, 5, 6, 7, 8, 9, 10, 11, 12]:
            # Boost workflow spec for understanding end-to-end integration
            if spec_file == '012-complete-workflow.md':
                enhanced_score += 0.25

            # Boost error handling for understanding failure cases
            if spec_file == '013-error-handling.md':
                enhanced_score += 0.2

            # Phase-specific related tools that should be included
            related_tools = self.get_related_tool_specs(phase)
            if spec_file in related_tools:
                enhanced_score += 0.35  # Strong boost for related tools

        return min(1.0, enhanced_score)

    def get_phase_specific_specs(self, phase: int) -> List[str]:
        """Get specifications most relevant to specific phases.

        Note: Actual phases will be determined by AI during implementation planning.
        This is a placeholder mapping for common patterns.
        """
        phase_spec_map = {
            # Infrastructure phases (likely 1-3)
            1: ['014-installation.md', '015-mcp-server-setup.md'],
            2: ['007-database-integration.md', '017-template-management.md'],
            3: ['010-model-storage.md', '018-session-management-tools.md'],

            # Core tool phases (likely 4-7)
            4: ['003-build-media-tool.md', '019-predefined-media-library.md'],
            5: ['004-build-model-tool.md'],
            6: ['005-gapfill-model-tool.md'],
            7: ['006-run-fba-tool.md'],

            # Database tool phases (likely 8-9)
            8: ['008-compound-lookup-tools.md'],
            9: ['009-reaction-lookup-tools.md'],

            # Integration phases (likely 10+)
            10: ['011-model-import-export.md'],
            11: ['012-complete-workflow.md'],
            12: ['013-error-handling.md'],
        }

        return phase_spec_map.get(phase, [])

    def get_related_tool_specs(self, phase: int) -> List[str]:
        """Get tool specs that are related/interact with the phase's primary tool.

        This helps include specs for tools that the current phase's tool depends on.
        """
        related_tools_map = {
            # build_model depends on template and database
            5: ['007-database-integration.md', '017-template-management.md'],
            # gapfill depends on build_model and build_media
            6: ['004-build-model-tool.md', '003-build-media-tool.md'],
            # run_fba depends on build_model (and potentially gapfill)
            7: ['004-build-model-tool.md', '005-gapfill-model-tool.md'],
            # workflow depends on all core tools
            11: ['003-build-media-tool.md', '004-build-model-tool.md', '005-gapfill-model-tool.md', '006-run-fba-tool.md'],
        }

        return related_tools_map.get(phase, [])

    def get_phase_confidence_boost(self, phase: int, selected_specs: List[str]) -> float:
        """Calculate confidence boost based on phase-appropriate spec inclusion."""
        phase_specs = self.get_phase_specific_specs(phase)
        if not phase_specs:
            return 0.0

        # Boost if we included phase-specific specs
        included_phase_specs = [spec for spec in selected_specs if spec in phase_specs]
        if included_phase_specs:
            return 0.1 * len(included_phase_specs)
        else:
            return 0.0

    def validate_context_selection(self, task: str, selected_specs: List[str],
                                 current_phase: int) -> Dict[str, any]:
        """Validate that context selection meets quality requirements."""

        validation_result = {
            'is_valid': True,
            'warnings': [],
            'critical_issues': [],
            'confidence_adjustment': 0.0
        }

        # Check critical spec inclusion
        missing_critical = set(self.critical_specs) - set(selected_specs)
        if missing_critical:
            validation_result['critical_issues'].append(
                f"Missing critical specs: {missing_critical}"
            )
            validation_result['is_valid'] = False

        # Check phase-appropriate specs
        phase_requirements = self.get_phase_requirements(current_phase)
        for requirement in phase_requirements:
            if not any(req in spec for spec in selected_specs for req in requirement['keywords']):
                validation_result['warnings'].append(
                    f"Phase {current_phase} may need {requirement['spec_type']} specification"
                )
                validation_result['confidence_adjustment'] -= 0.1

        # Check minimum specs threshold
        if len(selected_specs) < 3:
            validation_result['warnings'].append(
                "Very few specifications selected - may lack context"
            )
            validation_result['confidence_adjustment'] -= 0.2

        # Check maximum specs threshold
        if len(selected_specs) > 10:
            validation_result['warnings'].append(
                f"Too many specifications selected ({len(selected_specs)}) - may reduce optimization benefit"
            )
            validation_result['confidence_adjustment'] -= 0.1

        return validation_result

    def get_phase_requirements(self, phase: int) -> List[Dict[str, any]]:
        """Get specification requirements for specific phases."""

        phase_map = {
            1: [{'spec_type': 'installation', 'keywords': ['installation', 'setup', 'dependencies', 'uv']}],
            2: [{'spec_type': 'database', 'keywords': ['database', 'compounds', 'reactions', 'modelseed']}],
            3: [{'spec_type': 'storage', 'keywords': ['storage', 'session', 'model']}],
            4: [{'spec_type': 'build-media', 'keywords': ['media', 'compounds', 'growth']}],
            5: [{'spec_type': 'build-model', 'keywords': ['model', 'genome', 'template', 'rast', 'fasta']}],
            6: [{'spec_type': 'gapfill', 'keywords': ['gapfill', 'media', 'reactions']}],
            7: [{'spec_type': 'fba', 'keywords': ['fba', 'optimize', 'flux', 'simulation']}],
            8: [{'spec_type': 'compound-lookup', 'keywords': ['compound', 'search', 'lookup']}],
            9: [{'spec_type': 'reaction-lookup', 'keywords': ['reaction', 'search', 'lookup']}],
            10: [{'spec_type': 'import-export', 'keywords': ['import', 'export', 'json', 'sbml']}],
            11: [{'spec_type': 'workflow', 'keywords': ['workflow', 'integration', 'end-to-end']}],
            12: [{'spec_type': 'error-handling', 'keywords': ['error', 'jsonrpc', 'failure']}]
        }

        return phase_map.get(phase, [])
