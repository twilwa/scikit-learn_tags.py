from typing import List, Dict, Optional
from collections import Counter
import re
import hashlib

from discord_bot.database import DiscordDatabase

class SuggestionEngine:
    def __init__(self, db: DiscordDatabase):
        self.db = db

    async def generate_suggestions(self, user_id: str, current_context: List[Dict],
                                   current_message: str, min_confidence: float = 0.6) -> List[Dict]:
        suggestions = []

        pattern_suggestions = await self._get_pattern_based_suggestions(user_id, current_context)
        suggestions.extend(pattern_suggestions)

        frequency_suggestions = await self._get_frequency_based_suggestions(user_id, current_context)
        suggestions.extend(frequency_suggestions)

        kb_suggestions = await self._get_kb_based_suggestions(user_id, current_message)
        suggestions.extend(kb_suggestions)

        workflow_suggestions = self._get_workflow_suggestions(current_context, current_message)
        suggestions.extend(workflow_suggestions)

        suggestions = self._deduplicate_suggestions(suggestions)

        suggestions = [s for s in suggestions if s['confidence'] >= min_confidence]

        suggestions.sort(key=lambda x: x['confidence'], reverse=True)

        context_hash = self._generate_context_hash(current_context)
        for suggestion in suggestions[:5]:
            await self.db.store_suggestion(
                user_id=user_id,
                context_hash=context_hash,
                suggested_command=suggestion['command'],
                source=suggestion['source'],
                confidence=suggestion['confidence']
            )

        return suggestions[:5]

    async def _get_pattern_based_suggestions(self, user_id: str, context: List[Dict]) -> List[Dict]:
        patterns = await self.db.get_command_patterns(user_id)

        if not patterns or len(context) < 2:
            return []

        recent_commands = [cmd['command_text'] for cmd in context[-3:]]

        suggestions = []

        for pattern in patterns:
            trigger = pattern.get('trigger_context', [])
            sequence = pattern.get('command_sequence', [])

            if not trigger or not sequence:
                continue

            match_score = self._calculate_pattern_match(recent_commands, trigger)

            if match_score > 0.5:
                next_command = sequence[-1] if sequence else None

                if next_command and next_command not in recent_commands:
                    confidence = (match_score * 0.7 +
                                pattern.get('success_rate', 0.5) * 0.3)

                    suggestions.append({
                        'command': next_command,
                        'source': 'pattern',
                        'confidence': confidence,
                        'pattern_name': pattern.get('pattern_name', 'unknown')
                    })

        return suggestions

    async def _get_frequency_based_suggestions(self, user_id: str, context: List[Dict]) -> List[Dict]:
        history = await self.db.get_command_history(user_id, limit=200)

        if not history:
            return []

        command_counts = Counter([cmd['command_text'] for cmd in history])

        total_commands = len(history)

        suggestions = []

        for command, count in command_counts.most_common(10):
            if count < 3:
                continue

            if any(cmd['command_text'] == command for cmd in context[-3:]):
                continue

            frequency_score = min(count / total_commands * 10, 1.0)

            context_relevance = self._calculate_context_relevance(command, context)

            confidence = frequency_score * 0.4 + context_relevance * 0.6

            if confidence >= 0.5:
                suggestions.append({
                    'command': command,
                    'source': 'frequency',
                    'confidence': confidence,
                    'usage_count': count
                })

        return suggestions

    async def _get_kb_based_suggestions(self, user_id: str, current_message: str) -> List[Dict]:
        if len(current_message.split()) < 3:
            return []

        kb_results = await self.db.search_kb_chunks(user_id, current_message, limit=3)

        if not kb_results:
            return []

        suggestions = []

        for result in kb_results:
            content = result.get('content', '')

            commands = self._extract_commands_from_text(content)

            for command in commands[:2]:
                suggestions.append({
                    'command': command,
                    'source': 'knowledge_base',
                    'confidence': 0.65,
                    'kb_source': result.get('metadata', {}).get('file_name', 'unknown')
                })

        return suggestions

    def _get_workflow_suggestions(self, context: List[Dict], current_message: str) -> List[Dict]:
        if not context:
            return []

        last_command = context[-1]['command_text'].lower().strip() if context else ''

        common_workflows = {
            'git add': ['git commit -m "Update"', 'git status'],
            'git commit': ['git push', 'git push origin main'],
            'npm install': ['npm run dev', 'npm run build', 'npm test'],
            'npm run build': ['npm test', 'npm start'],
            'git pull': ['npm install', 'git status'],
            'git clone': ['cd', 'npm install'],
            'mkdir': ['cd', 'git init'],
            'touch': ['code .', 'vim'],
            'python': ['pytest', 'pip install'],
            'pip install': ['python', 'pytest'],
        }

        suggestions = []

        for trigger, next_commands in common_workflows.items():
            if trigger in last_command:
                for next_cmd in next_commands:
                    suggestions.append({
                        'command': next_cmd,
                        'source': 'workflow',
                        'confidence': 0.7
                    })

        return suggestions

    def _calculate_pattern_match(self, recent: List[str], trigger: List[str]) -> float:
        if not recent or not trigger:
            return 0.0

        matches = 0
        for i, trigger_cmd in enumerate(trigger):
            if i < len(recent) and recent[-(len(trigger)-i)] == trigger_cmd:
                matches += 1

        return matches / len(trigger) if trigger else 0.0

    def _calculate_context_relevance(self, command: str, context: List[Dict]) -> float:
        if not context:
            return 0.5

        command_tokens = set(command.lower().split())

        context_text = ' '.join([cmd['command_text'] for cmd in context[-5:]])
        context_tokens = set(context_text.lower().split())

        overlap = len(command_tokens & context_tokens)
        total = len(command_tokens | context_tokens)

        return overlap / total if total > 0 else 0.3

    def _extract_commands_from_text(self, text: str) -> List[str]:
        code_block_pattern = r'```(?:\w+)?\n(.*?)```'
        code_blocks = re.findall(code_block_pattern, text, re.DOTALL)

        commands = []

        for block in code_blocks:
            lines = block.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('//'):
                    commands.append(line)

        inline_code_pattern = r'`([^`]+)`'
        inline_commands = re.findall(inline_code_pattern, text)

        for cmd in inline_commands:
            if cmd and not cmd.startswith('#'):
                commands.append(cmd)

        return commands[:10]

    def _deduplicate_suggestions(self, suggestions: List[Dict]) -> List[Dict]:
        seen = {}

        for suggestion in suggestions:
            command = suggestion['command']

            if command not in seen or suggestion['confidence'] > seen[command]['confidence']:
                seen[command] = suggestion

        return list(seen.values())

    def _generate_context_hash(self, context: List[Dict]) -> str:
        context_string = '|'.join([cmd['command_text'] for cmd in context[-5:]])
        return hashlib.md5(context_string.encode()).hexdigest()
