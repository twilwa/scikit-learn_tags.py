from typing import Optional, Dict, List
from datetime import datetime
import os
from supabase import create_client, Client
import hashlib

class DiscordDatabase:
    def __init__(self):
        url = os.getenv('VITE_SUPABASE_URL')
        key = os.getenv('VITE_SUPABASE_ANON_KEY')

        if not url or not key:
            raise ValueError('Supabase credentials not found in environment')

        self.client: Client = create_client(url, key)

    async def register_user(self, discord_id: str, username: str) -> Dict:
        result = self.client.table('discord_users').select('*').eq('discord_id', discord_id).maybeSingle().execute()

        if result.data:
            self.client.table('discord_users').update({
                'discord_username': username,
                'last_active': datetime.utcnow().isoformat()
            }).eq('discord_id', discord_id).execute()
            return result.data

        result = self.client.table('discord_users').insert({
            'discord_id': discord_id,
            'discord_username': username
        }).execute()

        return result.data[0] if result.data else None

    async def register_server(self, guild_id: str, guild_name: str) -> Dict:
        result = self.client.table('discord_servers').select('*').eq('discord_guild_id', guild_id).maybeSingle().execute()

        if result.data:
            self.client.table('discord_servers').update({
                'guild_name': guild_name
            }).eq('discord_guild_id', guild_id).execute()
            return result.data

        result = self.client.table('discord_servers').insert({
            'discord_guild_id': guild_id,
            'guild_name': guild_name
        }).execute()

        return result.data[0] if result.data else None

    async def get_user_preferences(self, discord_id: str) -> Optional[Dict]:
        result = self.client.table('discord_users').select('preferences').eq('discord_id', discord_id).maybeSingle().execute()
        return result.data['preferences'] if result.data else None

    async def update_user_preferences(self, discord_id: str, preferences: Dict) -> bool:
        user = await self.register_user(discord_id, 'unknown')
        if not user:
            return False

        self.client.table('discord_users').update({
            'preferences': preferences
        }).eq('discord_id', discord_id).execute()
        return True

    async def get_server_settings(self, guild_id: Optional[str]) -> Optional[Dict]:
        if not guild_id:
            return None

        result = self.client.table('discord_servers').select('*').eq('discord_guild_id', guild_id).maybeSingle().execute()
        return result.data if result.data else None

    async def store_command(self, user_id: str, server_id: Optional[str], channel_id: str,
                           command_text: str, context_before: Optional[str] = None,
                           command_type: str = 'unknown', was_suggested: bool = False) -> Dict:

        user_result = self.client.table('discord_users').select('id').eq('discord_id', user_id).maybeSingle().execute()

        if not user_result.data:
            await self.register_user(user_id, 'unknown')
            user_result = self.client.table('discord_users').select('id').eq('discord_id', user_id).maybeSingle().execute()

        user_uuid = user_result.data['id']
        server_uuid = None

        if server_id:
            server_result = self.client.table('discord_servers').select('id').eq('discord_guild_id', server_id).maybeSingle().execute()
            if server_result.data:
                server_uuid = server_result.data['id']

        result = self.client.table('command_history').insert({
            'user_id': user_uuid,
            'server_id': server_uuid,
            'channel_id': channel_id,
            'command_text': command_text,
            'context_before': context_before,
            'command_type': command_type,
            'was_suggested': was_suggested
        }).execute()

        return result.data[0] if result.data else None

    async def get_command_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        user_result = self.client.table('discord_users').select('id').eq('discord_id', user_id).maybeSingle().execute()

        if not user_result.data:
            return []

        user_uuid = user_result.data['id']

        result = self.client.table('command_history').select('*').eq('user_id', user_uuid).order('created_at', desc=True).limit(limit).execute()

        return result.data if result.data else []

    async def get_command_patterns(self, user_id: str) -> List[Dict]:
        user_result = self.client.table('discord_users').select('id').eq('discord_id', user_id).maybeSingle().execute()

        if not user_result.data:
            return []

        user_uuid = user_result.data['id']

        result = self.client.table('command_patterns').select('*').eq('user_id', user_uuid).order('frequency', desc=True).execute()

        return result.data if result.data else []

    async def update_command_pattern(self, user_id: str, pattern_name: str,
                                    command_sequence: List[str], trigger_context: List[str]) -> bool:
        user_result = self.client.table('discord_users').select('id').eq('discord_id', user_id).maybeSingle().execute()

        if not user_result.data:
            return False

        user_uuid = user_result.data['id']

        existing = self.client.table('command_patterns').select('*').eq('user_id', user_uuid).eq('pattern_name', pattern_name).maybeSingle().execute()

        if existing.data:
            self.client.table('command_patterns').update({
                'frequency': existing.data['frequency'] + 1,
                'last_used': datetime.utcnow().isoformat()
            }).eq('id', existing.data['id']).execute()
        else:
            self.client.table('command_patterns').insert({
                'user_id': user_uuid,
                'pattern_name': pattern_name,
                'trigger_context': trigger_context,
                'command_sequence': command_sequence
            }).execute()

        return True

    async def store_suggestion(self, user_id: str, context_hash: str, suggested_command: str,
                              source: str, confidence: float) -> Dict:
        user_result = self.client.table('discord_users').select('id').eq('discord_id', user_id).maybeSingle().execute()

        if not user_result.data:
            return None

        user_uuid = user_result.data['id']

        result = self.client.table('command_suggestions').insert({
            'user_id': user_uuid,
            'context_hash': context_hash,
            'suggested_command': suggested_command,
            'suggestion_source': source,
            'confidence_score': confidence,
            'was_shown': True
        }).execute()

        return result.data[0] if result.data else None

    async def mark_suggestion_accepted(self, user_id: str, context_hash: str):
        user_result = self.client.table('discord_users').select('id').eq('discord_id', user_id).maybeSingle().execute()

        if not user_result.data:
            return

        user_uuid = user_result.data['id']

        self.client.table('command_suggestions').update({
            'was_accepted': True
        }).eq('user_id', user_uuid).eq('context_hash', context_hash).execute()

    async def store_kb_document(self, user_id: str, file_name: str, file_path: str, content: str) -> Dict:
        user_result = self.client.table('discord_users').select('id').eq('discord_id', user_id).maybeSingle().execute()

        if not user_result.data:
            return None

        user_uuid = user_result.data['id']

        content_hash = hashlib.sha256(content.encode()).hexdigest()

        existing = self.client.table('kb_documents').select('id').eq('user_id', user_uuid).eq('file_path', file_path).maybeSingle().execute()

        if existing.data:
            result = self.client.table('kb_documents').update({
                'content': content,
                'content_hash': content_hash,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', existing.data['id']).execute()
            return result.data[0] if result.data else None
        else:
            result = self.client.table('kb_documents').insert({
                'user_id': user_uuid,
                'file_name': file_name,
                'file_path': file_path,
                'content': content,
                'content_hash': content_hash
            }).execute()
            return result.data[0] if result.data else None

    async def store_kb_chunk(self, document_id: str, chunk_index: int, content: str,
                            embedding: Optional[List[float]] = None, metadata: Dict = None) -> Dict:
        result = self.client.table('kb_chunks').insert({
            'document_id': document_id,
            'chunk_index': chunk_index,
            'content': content,
            'embedding': embedding,
            'metadata': metadata or {}
        }).execute()

        return result.data[0] if result.data else None

    async def search_kb_chunks(self, user_id: str, query: str, limit: int = 5) -> List[Dict]:
        user_result = self.client.table('discord_users').select('id').eq('discord_id', user_id).maybeSingle().execute()

        if not user_result.data:
            return []

        user_uuid = user_result.data['id']

        docs = self.client.table('kb_documents').select('id').eq('user_id', user_uuid).execute()

        if not docs.data:
            return []

        doc_ids = [doc['id'] for doc in docs.data]

        results = []
        for doc_id in doc_ids:
            chunks = self.client.table('kb_chunks').select('*').eq('document_id', doc_id).ilike('content', f'%{query}%').limit(limit).execute()

            if chunks.data:
                results.extend(chunks.data)

        return results[:limit]
