from typing import List, Dict, Optional
from datetime import datetime
import hashlib

from discord_bot.database import DiscordDatabase

class CommandTracker:
    def __init__(self, db: DiscordDatabase):
        self.db = db

    async def track_command(self, user_id: str, server_id: Optional[str], channel_id: str,
                           command_text: str, was_suggested: bool = False) -> Dict:
        context = await self.get_recent_context(user_id, limit=5)

        context_text = ' '.join([cmd['command_text'] for cmd in context]) if context else ''

        command_type = self._classify_command(command_text)

        result = await self.db.store_command(
            user_id=user_id,
            server_id=server_id,
            channel_id=channel_id,
            command_text=command_text,
            context_before=context_text,
            command_type=command_type,
            was_suggested=was_suggested
        )

        await self._update_patterns(user_id, command_text, context)

        return result

    async def get_recent_context(self, user_id: str, limit: int = 10) -> List[Dict]:
        history = await self.db.get_command_history(user_id, limit=limit)
        return list(reversed(history))

    async def mark_suggestion_accepted(self, user_id: str, command_text: str):
        context = await self.get_recent_context(user_id, limit=5)
        context_hash = self._generate_context_hash(context)

        await self.db.mark_suggestion_accepted(user_id, context_hash)

        await self.track_command(
            user_id=user_id,
            server_id=None,
            channel_id='dm',
            command_text=command_text,
            was_suggested=True
        )

    def _classify_command(self, command_text: str) -> str:
        command_lower = command_text.lower().strip()

        if command_lower.startswith(('git ', 'gh ')):
            return 'git'
        elif command_lower.startswith(('npm ', 'yarn ', 'pnpm ', 'npx ')):
            return 'package_manager'
        elif command_lower.startswith(('cd ', 'ls ', 'mkdir ', 'rm ', 'mv ', 'cp ')):
            return 'filesystem'
        elif command_lower.startswith(('python ', 'pip ', 'pytest ')):
            return 'python'
        elif command_lower.startswith(('node ', 'deno ')):
            return 'javascript'
        elif command_lower.startswith(('docker ', 'kubectl ')):
            return 'containers'
        elif command_lower.startswith('!'):
            return 'bot_command'
        else:
            return 'unknown'

    async def _update_patterns(self, user_id: str, command_text: str, context: List[Dict]):
        if len(context) < 2:
            return

        recent_commands = [cmd['command_text'] for cmd in context[-3:]]
        recent_commands.append(command_text)

        command_types = [self._classify_command(cmd) for cmd in recent_commands]

        pattern_signature = '->'.join(command_types)

        trigger_context = [cmd['command_text'] for cmd in context[-2:]]

        await self.db.update_command_pattern(
            user_id=user_id,
            pattern_name=pattern_signature,
            command_sequence=recent_commands,
            trigger_context=trigger_context
        )

    def _generate_context_hash(self, context: List[Dict]) -> str:
        context_string = '|'.join([cmd['command_text'] for cmd in context])
        return hashlib.md5(context_string.encode()).hexdigest()

    async def get_command_statistics(self, user_id: str) -> Dict:
        history = await self.db.get_command_history(user_id, limit=1000)

        total_commands = len(history)
        command_types = {}
        suggested_count = 0
        accepted_count = 0

        for cmd in history:
            cmd_type = cmd.get('command_type', 'unknown')
            command_types[cmd_type] = command_types.get(cmd_type, 0) + 1

            if cmd.get('was_suggested'):
                suggested_count += 1

            if cmd.get('accepted_suggestion'):
                accepted_count += 1

        return {
            'total_commands': total_commands,
            'command_types': command_types,
            'suggestions_shown': suggested_count,
            'suggestions_accepted': accepted_count,
            'acceptance_rate': accepted_count / suggested_count if suggested_count > 0 else 0
        }
