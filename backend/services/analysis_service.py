import sys
import os
from pathlib import Path
from typing import Dict, Any, List
import tempfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from repo_synthesis.analyzer import CodeAnalyzer, RepositoryStructure
from repo_synthesis.graph import DependencyGraph
from feature_extraction.extractors import CodeFeatureExtractor
from backend.utils.log_parser import ParsedLog
from backend.models import AnalysisType

class AnalysisService:
    def __init__(self):
        self.code_analyzer = CodeAnalyzer()
        self.feature_extractor = CodeFeatureExtractor()

    async def run_ast_analysis(self, parsed_log: ParsedLog, session_id: str) -> Dict[str, Any]:
        referenced_files = parsed_log.referenced_files[:10]
        file_analyses = []

        for file_path in referenced_files:
            if os.path.exists(file_path):
                try:
                    file_info = self.code_analyzer.analyze_file(file_path)
                    file_analyses.append({
                        'path': file_path,
                        'loc': file_info.lines_of_code,
                        'functions': len(file_info.functions),
                        'classes': len(file_info.classes),
                        'complexity': file_info.complexity_score,
                        'imports': list(file_info.imports)[:20]
                    })
                except Exception as e:
                    file_analyses.append({
                        'path': file_path,
                        'error': str(e)
                    })

        return {
            'type': 'ast_analysis',
            'files_analyzed': len(file_analyses),
            'files': file_analyses,
            'total_loc': sum(f.get('loc', 0) for f in file_analyses),
            'total_complexity': sum(f.get('complexity', 0) for f in file_analyses)
        }

    async def run_dependency_graph(self, parsed_log: ParsedLog, session_id: str) -> Dict[str, Any]:
        working_dir = parsed_log.active_directory
        if not working_dir or not os.path.exists(working_dir):
            return {
                'type': 'dependency_graph',
                'nodes': [],
                'edges': [],
                'error': 'Working directory not found'
            }

        try:
            repo_structure = self.code_analyzer.analyze_repository(working_dir)

            nodes = []
            edges = []

            for file_path in list(repo_structure.files.keys())[:30]:
                nodes.append({
                    'id': file_path,
                    'label': file_path.split('/')[-1],
                    'type': 'file',
                    'loc': repo_structure.files[file_path].lines_of_code
                })

            for file_path, deps in list(repo_structure.dependencies.items())[:30]:
                for dep in deps:
                    edges.append({
                        'from': file_path,
                        'to': dep,
                        'type': 'imports'
                    })

            return {
                'type': 'dependency_graph',
                'nodes': nodes,
                'edges': edges,
                'total_files': len(repo_structure.files),
                'total_dependencies': sum(len(deps) for deps in repo_structure.dependencies.values())
            }
        except Exception as e:
            return {
                'type': 'dependency_graph',
                'nodes': [],
                'edges': [],
                'error': str(e)
            }

    async def run_tool_call_analysis(self, parsed_log: ParsedLog, session_id: str) -> Dict[str, Any]:
        tool_usage = {}
        for tool_call in parsed_log.tool_calls:
            if tool_call.tool_name not in tool_usage:
                tool_usage[tool_call.tool_name] = 0
            tool_usage[tool_call.tool_name] += 1

        recent_tools = [t.tool_name for t in parsed_log.tool_calls[-20:]]

        return {
            'type': 'tool_calls',
            'total_calls': len(parsed_log.tool_calls),
            'tool_usage': tool_usage,
            'recent_tools': recent_tools,
            'file_operations': len(parsed_log.file_operations),
            'most_used_tool': max(tool_usage.items(), key=lambda x: x[1])[0] if tool_usage else None
        }

    async def run_complexity_analysis(self, parsed_log: ParsedLog, session_id: str) -> Dict[str, Any]:
        complexity_scores = []

        for file_path in parsed_log.referenced_files[:15]:
            if os.path.exists(file_path) and file_path.endswith('.py'):
                try:
                    with open(file_path, 'r') as f:
                        code = f.read()
                    features = self.feature_extractor.extract(code)

                    complexity_scores.append({
                        'file': file_path,
                        'features': len(features.features),
                        'score': sum(f.value for f in features.features if isinstance(f.value, (int, float)))
                    })
                except Exception:
                    pass

        return {
            'type': 'complexity',
            'files_analyzed': len(complexity_scores),
            'complexity_scores': complexity_scores,
            'avg_complexity': sum(s['score'] for s in complexity_scores) / len(complexity_scores) if complexity_scores else 0
        }

    def calculate_signal_score(self, analysis_type: str, result_data: Dict[str, Any], parsed_log: ParsedLog) -> float:
        base_score = 0.5

        if analysis_type == 'tool_calls':
            if result_data.get('total_calls', 0) > 10:
                base_score += 0.3
            if result_data.get('file_operations', 0) > 5:
                base_score += 0.2

        elif analysis_type == 'ast_analysis':
            if result_data.get('files_analyzed', 0) > 0:
                base_score += 0.4
            if result_data.get('total_complexity', 0) > 20:
                base_score += 0.1

        elif analysis_type == 'dependency_graph':
            if len(result_data.get('nodes', [])) > 10:
                base_score += 0.3
            if len(result_data.get('edges', [])) > 15:
                base_score += 0.2

        return min(base_score, 1.0)
