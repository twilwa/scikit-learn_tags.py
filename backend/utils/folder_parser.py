import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import tempfile
import zipfile


class FolderParser:
    """Parse .codex or .claude folders with logs and configs"""

    def __init__(self):
        self.supported_formats = ['.jsonl', '.json', '.txt', '.log']
        self.config_files = ['config.json', 'settings.json', 'mcp.json', 'subagents.json']

    def parse_folder(self, folder_path: str) -> Dict:
        """Parse a .codex or .claude folder"""
        result = {
            'folder_type': self._detect_folder_type(folder_path),
            'structure': self._build_structure(folder_path),
            'logs': [],
            'configs': {},
            'metadata': {}
        }

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder_path)

                if self._is_log_file(file):
                    log_data = self._parse_log_file(file_path)
                    if log_data:
                        log_data['path'] = relative_path
                        result['logs'].append(log_data)

                elif self._is_config_file(file):
                    config_data = self._parse_config_file(file_path)
                    if config_data:
                        result['configs'][file] = config_data

        result['metadata'] = self._extract_metadata(result)
        return result

    def parse_zip(self, zip_path: str) -> Dict:
        """Parse a zipped .codex or .claude folder"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            extracted_folders = os.listdir(temp_dir)
            if len(extracted_folders) == 1:
                folder_path = os.path.join(temp_dir, extracted_folders[0])
            else:
                folder_path = temp_dir

            return self.parse_folder(folder_path)

    def parse_jsonl_logs(self, file_path: str) -> List[Dict]:
        """Parse JSONL log format"""
        logs = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            log_entry = json.loads(line)
                            logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error parsing JSONL: {e}")

        return logs

    def _detect_folder_type(self, folder_path: str) -> str:
        """Detect if folder is .codex, .claude, or generic"""
        folder_name = os.path.basename(folder_path)

        if folder_name.startswith('.codex'):
            return 'codex'
        elif folder_name.startswith('.claude'):
            return 'claude'
        else:
            return 'generic'

    def _build_structure(self, folder_path: str) -> Dict:
        """Build tree structure of folder"""
        structure = {
            'name': os.path.basename(folder_path),
            'type': 'directory',
            'children': []
        }

        try:
            items = sorted(os.listdir(folder_path))
            for item in items:
                item_path = os.path.join(folder_path, item)

                if os.path.isdir(item_path):
                    structure['children'].append({
                        'name': item,
                        'type': 'directory',
                        'children': []
                    })
                else:
                    file_size = os.path.getsize(item_path)
                    structure['children'].append({
                        'name': item,
                        'type': 'file',
                        'size': file_size,
                        'extension': os.path.splitext(item)[1]
                    })
        except Exception as e:
            print(f"Error building structure: {e}")

        return structure

    def _is_log_file(self, filename: str) -> bool:
        """Check if file is a log file"""
        return any(filename.endswith(ext) for ext in self.supported_formats)

    def _is_config_file(self, filename: str) -> bool:
        """Check if file is a config file"""
        return filename in self.config_files or 'config' in filename.lower()

    def _parse_log_file(self, file_path: str) -> Optional[Dict]:
        """Parse individual log file"""
        try:
            ext = os.path.splitext(file_path)[1]

            if ext == '.jsonl':
                logs = self.parse_jsonl_logs(file_path)
                return {
                    'format': 'jsonl',
                    'entries': logs,
                    'entry_count': len(logs),
                    'size': os.path.getsize(file_path)
                }

            elif ext == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return {
                    'format': 'json',
                    'data': data,
                    'size': os.path.getsize(file_path)
                }

            else:
                with open(file_path, 'r') as f:
                    content = f.read()
                return {
                    'format': 'text',
                    'content': content,
                    'size': len(content)
                }

        except Exception as e:
            print(f"Error parsing log file {file_path}: {e}")
            return None

    def _parse_config_file(self, file_path: str) -> Optional[Dict]:
        """Parse configuration file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error parsing config file {file_path}: {e}")
            return None

    def _extract_metadata(self, parsed_data: Dict) -> Dict:
        """Extract metadata from parsed folder"""
        metadata = {
            'total_logs': len(parsed_data['logs']),
            'total_entries': sum(
                log.get('entry_count', 0) if log.get('format') == 'jsonl' else 1
                for log in parsed_data['logs']
            ),
            'config_files': list(parsed_data['configs'].keys()),
            'has_mcp_config': 'mcp.json' in parsed_data['configs'],
            'has_subagents': 'subagents.json' in parsed_data['configs']
        }

        if parsed_data['configs']:
            metadata['config_summary'] = self._summarize_configs(parsed_data['configs'])

        return metadata

    def _summarize_configs(self, configs: Dict) -> Dict:
        """Summarize configuration settings"""
        summary = {}

        if 'config.json' in configs:
            config = configs['config.json']
            summary['interaction_style'] = config.get('interaction_style')
            summary['model'] = config.get('model')
            summary['temperature'] = config.get('temperature')

        if 'mcp.json' in configs:
            mcp = configs['mcp.json']
            summary['mcp_servers'] = list(mcp.get('mcpServers', {}).keys())
            summary['mcp_count'] = len(mcp.get('mcpServers', {}))

        if 'subagents.json' in configs:
            subagents = configs['subagents.json']
            summary['subagent_count'] = len(subagents.get('subagents', []))
            summary['subagent_names'] = [
                s.get('name') for s in subagents.get('subagents', [])
            ]

        return summary


class ConfigAnalyzer:
    """Analyze configuration files and provide insights"""

    def analyze_mcp_config(self, mcp_config: Dict) -> Dict:
        """Analyze MCP server configuration"""
        servers = mcp_config.get('mcpServers', {})

        analysis = {
            'total_servers': len(servers),
            'servers': [],
            'recommendations': []
        }

        for server_name, server_config in servers.items():
            server_info = {
                'name': server_name,
                'command': server_config.get('command'),
                'args': server_config.get('args', []),
                'env': list(server_config.get('env', {}).keys())
            }
            analysis['servers'].append(server_info)

        if analysis['total_servers'] == 0:
            analysis['recommendations'].append('No MCP servers configured')
        elif analysis['total_servers'] > 10:
            analysis['recommendations'].append('Large number of MCP servers may impact performance')

        return analysis

    def analyze_subagents(self, subagents_config: Dict) -> Dict:
        """Analyze subagent configuration"""
        subagents = subagents_config.get('subagents', [])

        analysis = {
            'total_subagents': len(subagents),
            'subagents': [],
            'capabilities': set()
        }

        for subagent in subagents:
            agent_info = {
                'name': subagent.get('name'),
                'model': subagent.get('model'),
                'role': subagent.get('role'),
                'capabilities': subagent.get('capabilities', [])
            }
            analysis['subagents'].append(agent_info)

            for cap in agent_info['capabilities']:
                analysis['capabilities'].add(cap)

        analysis['capabilities'] = list(analysis['capabilities'])
        return analysis

    def analyze_interaction_style(self, config: Dict) -> Dict:
        """Analyze interaction style settings"""
        style = config.get('interaction_style', {})

        return {
            'verbosity': style.get('verbosity', 'normal'),
            'code_format': style.get('code_format', 'markdown'),
            'explanation_level': style.get('explanation_level', 'detailed'),
            'suggestions': self._suggest_style_improvements(style)
        }

    def _suggest_style_improvements(self, style: Dict) -> List[str]:
        """Suggest improvements to interaction style"""
        suggestions = []

        verbosity = style.get('verbosity', 'normal')
        if verbosity == 'verbose':
            suggestions.append('Consider "concise" mode for faster responses')

        if not style.get('code_format'):
            suggestions.append('Set code_format preference for consistent output')

        return suggestions
