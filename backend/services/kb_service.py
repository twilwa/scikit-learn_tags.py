from typing import List, Dict, Optional
from datetime import datetime
from backend.database import get_supabase


class KBService:
    def __init__(self):
        self.supabase = get_supabase()

    async def set_document_visibility(
        self,
        document_id: str,
        visibility: str,
        user_id: str
    ) -> Dict:
        doc = self.supabase.table('kb_documents').select('user_id').eq('id', document_id).maybeSingle().execute()

        if not doc.data or doc.data['user_id'] != user_id:
            raise ValueError("Document not found or not owned by user")

        update_data = {
            'visibility': visibility
        }

        if visibility == 'shared':
            update_data['contributed_at'] = datetime.utcnow().isoformat()

        result = self.supabase.table('kb_documents').update(update_data).eq('id', document_id).execute()

        if visibility == 'shared' and doc.data:
            await self._promote_to_shared_pool(document_id)

        return result.data[0]

    async def _promote_to_shared_pool(self, document_id: str):
        doc = self.supabase.table('kb_documents').select('*').eq('id', document_id).maybeSingle().execute()

        if not doc.data:
            return

        chunks = self.supabase.table('kb_chunks').select('*').eq('document_id', document_id).execute()

        for chunk in chunks.data:
            existing = self.supabase.table('shared_kb_pool').select('id').eq('source_document_id', document_id).maybeSingle().execute()

            if not existing.data:
                metadata = doc.data.get('metadata', {})
                category = self._infer_category(doc.data['file_name'], chunk['content'])

                self.supabase.table('shared_kb_pool').insert({
                    'source_document_id': document_id,
                    'title': doc.data['file_name'],
                    'category': category,
                    'content': chunk['content'],
                    'embedding': chunk['embedding'],
                    'metadata': metadata,
                    'quality_score': 0.5,
                    'usage_count': 0,
                    'contributor_count': 1
                }).execute()

    def _infer_category(self, filename: str, content: str) -> str:
        filename_lower = filename.lower()
        content_lower = content.lower()

        categories = {
            'deployment': ['deploy', 'production', 'kubernetes', 'docker', 'aws', 'gcp'],
            'git': ['git', 'github', 'commit', 'branch', 'merge', 'pull request'],
            'debugging': ['debug', 'error', 'bug', 'troubleshoot', 'fix'],
            'testing': ['test', 'pytest', 'jest', 'unittest', 'coverage'],
            'development': ['code', 'function', 'class', 'api', 'endpoint'],
            'documentation': ['readme', 'docs', 'guide', 'tutorial', 'how to']
        }

        for category, keywords in categories.items():
            if any(kw in filename_lower or kw in content_lower for kw in keywords):
                return category

        return 'general'

    async def search_shared_kb(
        self,
        query_embedding: List[float],
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        results = self.supabase.rpc(
            'match_shared_kb',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.6,
                'match_count': limit,
                'category_filter': category
            }
        ).execute()

        if results.data:
            for result in results.data:
                self.supabase.table('shared_kb_pool').update({
                    'usage_count': result['usage_count'] + 1
                }).eq('id', result['id']).execute()

            return results.data
        else:
            query = self.supabase.table('shared_kb_pool').select('*')

            if category:
                query = query.eq('category', category)

            results = query.order('quality_score', desc=True).limit(limit).execute()
            return results.data

    async def submit_feedback(
        self,
        user_id: str,
        document_id: Optional[str] = None,
        chunk_id: Optional[str] = None,
        feedback_type: str = 'helpful',
        rating: Optional[int] = None,
        correction_text: Optional[str] = None,
        is_helpful: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> Dict:
        result = self.supabase.table('kb_feedback').insert({
            'document_id': document_id,
            'chunk_id': chunk_id,
            'user_id': user_id,
            'feedback_type': feedback_type,
            'rating': rating,
            'correction_text': correction_text,
            'is_helpful': is_helpful,
            'tags': tags
        }).execute()

        if is_helpful is not None and chunk_id:
            await self._update_quality_score(chunk_id, is_helpful)

        return result.data[0]

    async def _update_quality_score(self, chunk_id: str, is_helpful: bool):
        chunk = self.supabase.table('kb_chunks').select('document_id').eq('id', chunk_id).maybeSingle().execute()

        if not chunk.data:
            return

        shared_entries = self.supabase.table('shared_kb_pool').select('*').eq('source_document_id', chunk.data['document_id']).execute()

        for entry in shared_entries.data:
            feedback_count = self.supabase.table('kb_feedback').select('*', count='exact').eq('chunk_id', chunk_id).execute()

            if feedback_count.count > 0:
                helpful_count = self.supabase.table('kb_feedback').select('*', count='exact').eq('chunk_id', chunk_id).eq('is_helpful', True).execute()

                quality_score = helpful_count.count / feedback_count.count

                self.supabase.table('shared_kb_pool').update({
                    'quality_score': quality_score,
                    'last_updated': datetime.utcnow().isoformat()
                }).eq('id', entry['id']).execute()

    async def get_user_contributions(self, user_id: str) -> List[Dict]:
        docs = self.supabase.table('kb_documents').select('*').eq('user_id', user_id).eq('visibility', 'shared').order('contributed_at', desc=True).execute()

        contributions = []
        for doc in docs.data:
            feedback = self.supabase.table('kb_feedback').select('*', count='exact').eq('document_id', doc['id']).execute()

            helpful = self.supabase.table('kb_feedback').select('*', count='exact').eq('document_id', doc['id']).eq('is_helpful', True).execute()

            contributions.append({
                'document': doc,
                'total_feedback': feedback.count,
                'helpful_feedback': helpful.count,
                'helpfulness_rate': helpful.count / feedback.count if feedback.count > 0 else 0
            })

        return contributions

    async def get_shared_kb_stats(self) -> Dict:
        docs = self.supabase.table('shared_kb_pool').select('*', count='exact').execute()

        categories = self.supabase.table('shared_kb_pool').select('category').execute()
        category_counts = {}
        for item in categories.data:
            cat = item['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            'total_entries': docs.count,
            'categories': category_counts,
            'total_usage': sum(d['usage_count'] for d in docs.data),
            'avg_quality_score': sum(d['quality_score'] for d in docs.data) / docs.count if docs.count > 0 else 0
        }
