from typing import Optional, Dict, List
from datetime import datetime, timedelta
import uuid
from backend.database import get_supabase


class VoiceSessionService:
    def __init__(self):
        self.supabase = get_supabase()

        self.pricing = {
            'voice_browser': 500,
            'voice_discord': 1000,
            'text_only': 0
        }

        self.duration_limits = {
            'voice_browser': 60,
            'voice_discord': 60,
            'text_only': 120
        }

    async def create_session(
        self,
        host_user_id: str,
        session_type: str,
        mode: str,
        repo_url: Optional[str] = None,
        log_session_id: Optional[str] = None
    ) -> Dict:
        session_url = str(uuid.uuid4())
        price_cents = self.pricing.get(mode, 0)
        duration_minutes = self.duration_limits.get(mode, 60)

        expires_at = datetime.utcnow() + timedelta(hours=24)

        result = self.supabase.table('voice_sessions').insert({
            'session_url': session_url,
            'host_user_id': host_user_id,
            'session_type': session_type,
            'mode': mode,
            'status': 'waiting',
            'price_cents': price_cents,
            'duration_minutes': duration_minutes,
            'repo_url': repo_url,
            'log_session_id': log_session_id,
            'expires_at': expires_at.isoformat(),
            'metadata': {
                'features': {
                    'voice': mode != 'text_only',
                    'repl': True,
                    'visualization': True,
                    'collaborative': True
                }
            }
        }).execute()

        session = result.data[0]

        await self._add_participant(session['id'], host_user_id, 'host')

        return session

    async def start_session(self, session_id: str) -> Dict:
        now = datetime.utcnow()

        result = self.supabase.table('voice_sessions').update({
            'status': 'active',
            'started_at': now.isoformat()
        }).eq('id', session_id).execute()

        return result.data[0]

    async def _add_participant(
        self,
        session_id: str,
        user_id: str,
        role: str
    ):
        self.supabase.table('session_participants').insert({
            'session_id': session_id,
            'user_id': user_id,
            'role': role
        }).execute()

    async def join_session(
        self,
        session_id: str,
        user_id: str,
        role: str = 'guest'
    ) -> Dict:
        await self._add_participant(session_id, user_id, role)

        session = self.supabase.table('voice_sessions').select('*').eq('id', session_id).maybeSingle().execute()

        return session.data

    async def execute_code(
        self,
        session_id: str,
        user_id: str,
        code: str
    ) -> Dict:
        import time
        import sys
        from io import StringIO

        start_time = time.time()

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        output_type = 'text'
        output = None
        error_message = None
        visualization_data = None

        try:
            exec_globals = {
                '__builtins__': __builtins__,
                'numpy': __import__('numpy'),
                'pandas': __import__('pandas'),
                'matplotlib': __import__('matplotlib.pyplot'),
                'json': __import__('json')
            }

            exec(code, exec_globals)

            output = sys.stdout.getvalue()

            if not output:
                last_expr = code.strip().split('\n')[-1]
                if '=' not in last_expr and not last_expr.startswith(('import', 'def', 'class', 'if', 'for', 'while')):
                    try:
                        result = eval(last_expr, exec_globals)
                        output = str(result)
                    except:
                        pass

        except Exception as e:
            error_message = str(e)
            output_type = 'error'
        finally:
            sys.stdout = old_stdout

        execution_time_ms = int((time.time() - start_time) * 1000)

        result = self.supabase.table('repl_executions').insert({
            'session_id': session_id,
            'user_id': user_id,
            'code': code,
            'output': output,
            'output_type': output_type,
            'visualization_data': visualization_data,
            'execution_time_ms': execution_time_ms,
            'error_message': error_message
        }).execute()

        return result.data[0]

    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict]:
        result = self.supabase.table('repl_executions').select('*').eq('session_id', session_id).order('created_at', desc=True).limit(limit).execute()

        return result.data

    async def update_session_time(
        self,
        session_id: str,
        minutes_used: int
    ):
        session = self.supabase.table('voice_sessions').select('duration_minutes').eq('id', session_id).maybeSingle().execute()

        if session.data and minutes_used >= session.data['duration_minutes']:
            self.supabase.table('voice_sessions').update({
                'status': 'expired',
                'minutes_used': minutes_used,
                'ended_at': datetime.utcnow().isoformat()
            }).eq('id', session_id).execute()
        else:
            self.supabase.table('voice_sessions').update({
                'minutes_used': minutes_used
            }).eq('id', session_id).execute()

    async def end_session(self, session_id: str):
        self.supabase.table('voice_sessions').update({
            'status': 'completed',
            'ended_at': datetime.utcnow().isoformat()
        }).eq('id', session_id).execute()

        self.supabase.table('session_participants').update({
            'is_active': False,
            'left_at': datetime.utcnow().isoformat()
        }).eq('session_id', session_id).execute()
