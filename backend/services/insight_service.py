from typing import Dict, Any, List, Tuple
from backend.utils.log_parser import ParsedLog
from backend.models import InsightType
import random

class InsightGenerator:
    def __init__(self):
        self.templates = {
            InsightType.NEXT_STEP: [
                "Based on your recent file operations, consider refactoring {module} to improve maintainability.",
                "You've been working heavily in {area}. Next, focus on adding tests for the {component} module.",
                "The {file} has grown to {loc} lines. Consider breaking it into smaller, focused modules."
            ],
            InsightType.CODE_ISSUE: [
                "Detected high complexity ({score}) in {file}. This may indicate code that needs refactoring.",
                "Multiple file operations on {file} suggest potential merge conflicts or coordination issues.",
                "The {module} has {count} dependencies, which may create tight coupling."
            ],
            InsightType.ARCHITECTURE: [
                "Your codebase shows {pattern} pattern. Consider extracting shared logic into {suggestion}.",
                "The dependency graph indicates {observation}. This suggests a need for better module separation.",
                "Based on file structure, consider organizing code into feature-based modules instead of type-based."
            ],
            InsightType.OPTIMIZATION: [
                "Tool usage analysis shows {tool} was called {count} times. Consider batching operations.",
                "File {file} is frequently modified. Caching intermediate results could improve efficiency.",
                "The current workflow involves {count} separate operations. Consider creating a pipeline."
            ]
        }

    def generate_insights(
        self,
        parsed_log: ParsedLog,
        analysis_results: Dict[str, Dict[str, Any]]
    ) -> List[Tuple[str, InsightType, float, Dict[str, Any]]]:
        insights = []

        if 'tool_calls' in analysis_results:
            tool_insight = self._generate_tool_insight(analysis_results['tool_calls'], parsed_log)
            if tool_insight:
                insights.append(tool_insight)

        if 'ast_analysis' in analysis_results:
            ast_insight = self._generate_ast_insight(analysis_results['ast_analysis'], parsed_log)
            if ast_insight:
                insights.append(ast_insight)

        if 'dependency_graph' in analysis_results:
            dep_insight = self._generate_dependency_insight(analysis_results['dependency_graph'], parsed_log)
            if dep_insight:
                insights.append(dep_insight)

        if 'complexity' in analysis_results:
            complexity_insight = self._generate_complexity_insight(analysis_results['complexity'], parsed_log)
            if complexity_insight:
                insights.append(complexity_insight)

        insights.sort(key=lambda x: x[2], reverse=True)
        return insights[:5]

    def _generate_tool_insight(self, tool_data: Dict[str, Any], parsed_log: ParsedLog) -> Tuple[str, InsightType, float, Dict[str, Any]]:
        most_used = tool_data.get('most_used_tool')
        total_calls = tool_data.get('total_calls', 0)

        if most_used and total_calls > 5:
            insight_text = f"You've used {most_used} {tool_data['tool_usage'][most_used]} times. "
            if most_used in ['Read', 'Write', 'Edit']:
                insight_text += f"Consider reviewing your recent file changes in the {most_used.lower()} operations for consistency."
            else:
                insight_text += "This suggests an active exploration phase. Next, focus on consolidating your findings."

            viz_data = {
                'chart_type': 'bar',
                'data': tool_data['tool_usage']
            }

            signal_score = min(0.5 + (total_calls / 100), 0.9)

            return (insight_text, InsightType.OPTIMIZATION, signal_score, viz_data)

        return None

    def _generate_ast_insight(self, ast_data: Dict[str, Any], parsed_log: ParsedLog) -> Tuple[str, InsightType, float, Dict[str, Any]]:
        files = ast_data.get('files', [])
        if not files:
            return None

        high_complexity_files = [f for f in files if f.get('complexity', 0) > 15]

        if high_complexity_files:
            file = high_complexity_files[0]
            insight_text = f"The file {file['path'].split('/')[-1]} has complexity score of {file['complexity']}. "
            insight_text += "Consider refactoring complex functions or breaking down large classes to improve maintainability."

            viz_data = {
                'chart_type': 'heatmap',
                'data': [{'file': f['path'].split('/')[-1], 'complexity': f.get('complexity', 0)} for f in files[:10]]
            }

            signal_score = 0.8

            return (insight_text, InsightType.CODE_ISSUE, signal_score, viz_data)

        total_loc = ast_data.get('total_loc', 0)
        if total_loc > 500:
            insight_text = f"You're working with {total_loc} lines of code across {len(files)} files. "
            insight_text += "Focus next on adding comprehensive tests to ensure code quality as the codebase grows."

            return (insight_text, InsightType.NEXT_STEP, 0.7, {})

        return None

    def _generate_dependency_insight(self, dep_data: Dict[str, Any], parsed_log: ParsedLog) -> Tuple[str, InsightType, float, Dict[str, Any]]:
        nodes = dep_data.get('nodes', [])
        edges = dep_data.get('edges', [])

        if not nodes:
            return None

        insight_text = f"Your codebase has {len(nodes)} modules with {len(edges)} dependencies. "

        if len(edges) > len(nodes) * 1.5:
            insight_text += "The high dependency ratio suggests tightly coupled modules. Consider introducing interfaces or abstractions to reduce coupling."
            insight_type = InsightType.ARCHITECTURE
            signal_score = 0.85
        else:
            insight_text += "The dependency structure looks clean. Continue maintaining this modular approach as you add features."
            insight_type = InsightType.NEXT_STEP
            signal_score = 0.6

        viz_data = {
            'chart_type': 'network',
            'nodes': nodes[:20],
            'edges': edges[:30]
        }

        return (insight_text, insight_type, signal_score, viz_data)

    def _generate_complexity_insight(self, complexity_data: Dict[str, Any], parsed_log: ParsedLog) -> Tuple[str, InsightType, float, Dict[str, Any]]:
        avg_complexity = complexity_data.get('avg_complexity', 0)
        files_analyzed = complexity_data.get('files_analyzed', 0)

        if files_analyzed == 0:
            return None

        if avg_complexity > 20:
            insight_text = f"Average complexity across {files_analyzed} files is {avg_complexity:.1f}. "
            insight_text += "High complexity scores indicate code that may benefit from decomposition into smaller, focused functions."

            return (insight_text, InsightType.CODE_ISSUE, 0.75, {})
        else:
            insight_text = f"Code complexity looks manageable across {files_analyzed} files. "
            insight_text += "Maintain this quality by applying the single responsibility principle to new code."

            return (insight_text, InsightType.NEXT_STEP, 0.5, {})
