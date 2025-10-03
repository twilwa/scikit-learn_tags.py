from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import json

from backend.services.voice_session_service import VoiceSessionService
from backend.services.voice_streaming_service import VoiceStreamingService
from backend.services.kb_service import KBService

router = APIRouter(prefix="/api", tags=["voice"])

voice_service = VoiceSessionService()
streaming_service = VoiceStreamingService()
kb_service = KBService()


class CreateVoiceSessionRequest(BaseModel):
    session_type: str
    mode: str = 'text_only'
    repo_url: Optional[str] = None
    log_session_id: Optional[str] = None


class ExecuteCodeRequest(BaseModel):
    code: str


class SetVisibilityRequest(BaseModel):
    visibility: str


class SubmitFeedbackRequest(BaseModel):
    chunk_id: Optional[str] = None
    document_id: Optional[str] = None
    is_helpful: Optional[bool] = None
    rating: Optional[int] = None
    correction_text: Optional[str] = None
    feedback_type: str = 'helpful'


@router.post("/voice-sessions")
async def create_voice_session(request: CreateVoiceSessionRequest):
    try:
        session = await voice_service.create_session(
            host_user_id="anonymous",
            session_type=request.session_type,
            mode=request.mode,
            repo_url=request.repo_url,
            log_session_id=request.log_session_id
        )

        return {
            'session_url': session['session_url'],
            'mode': session['mode'],
            'duration_minutes': session['duration_minutes'],
            'price_cents': session['price_cents'],
            'status': session['status']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice-sessions/{session_url}")
async def get_voice_session(session_url: str):
    try:
        from backend.database import get_supabase
        supabase = get_supabase()

        result = supabase.table('voice_sessions').select('*').eq('session_url', session_url).maybeSingle().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Session not found")

        return result.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-sessions/{session_url}/start")
async def start_voice_session(session_url: str):
    try:
        from backend.database import get_supabase
        supabase = get_supabase()

        session = supabase.table('voice_sessions').select('id').eq('session_url', session_url).maybeSingle().execute()

        if not session.data:
            raise HTTPException(status_code=404, detail="Session not found")

        updated = await voice_service.start_session(session.data['id'])

        return updated

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-sessions/{session_url}/execute")
async def execute_code(session_url: str, request: ExecuteCodeRequest):
    try:
        from backend.database import get_supabase
        supabase = get_supabase()

        session = supabase.table('voice_sessions').select('id').eq('session_url', session_url).maybeSingle().execute()

        if not session.data:
            raise HTTPException(status_code=404, detail="Session not found")

        result = await voice_service.execute_code(
            session_id=session.data['id'],
            user_id="anonymous",
            code=request.code
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice-sessions/{session_url}/history")
async def get_session_history(session_url: str):
    try:
        from backend.database import get_supabase
        supabase = get_supabase()

        session = supabase.table('voice_sessions').select('id').eq('session_url', session_url).maybeSingle().execute()

        if not session.data:
            raise HTTPException(status_code=404, detail="Session not found")

        history = await voice_service.get_session_history(session.data['id'])

        return history

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/voice/{session_url}")
async def voice_websocket(websocket: WebSocket, session_url: str):
    await websocket.accept()

    try:
        from backend.database import get_supabase
        supabase = get_supabase()

        session = supabase.table('voice_sessions').select('*').eq('session_url', session_url).maybeSingle().execute()

        if not session.data:
            await websocket.close(code=1008)
            return

        stream_id = await streaming_service.start_voice_stream(
            session_id=session.data['id'],
            websocket=websocket,
            mode=session.data['mode']
        )

        while True:
            data = await websocket.receive()

            if 'bytes' in data:
                transcription = await streaming_service.handle_audio_chunk(
                    stream_id=stream_id,
                    audio_data=data['bytes']
                )

                if transcription:
                    await streaming_service.send_to_stream(
                        stream_id=stream_id,
                        message_type='transcription',
                        data={'text': transcription}
                    )

            elif 'text' in data:
                message = json.loads(data['text'])

                if message.get('type') == 'ping':
                    await websocket.send_json({'type': 'pong'})

    except WebSocketDisconnect:
        await streaming_service.stop_voice_stream(stream_id)


@router.post("/kb/upload")
async def upload_kb_document(
    file: UploadFile = File(...),
    visibility: str = 'private'
):
    try:
        content = await file.read()
        content_text = content.decode('utf-8')

        from backend.database import get_supabase
        supabase = get_supabase()

        import hashlib
        content_hash = hashlib.sha256(content_text.encode()).hexdigest()

        result = supabase.table('kb_documents').insert({
            'user_id': 'anonymous',
            'file_name': file.filename,
            'file_path': file.filename,
            'content': content_text,
            'content_hash': content_hash,
            'visibility': visibility,
            'metadata': {}
        }).execute()

        return {
            'document_id': result.data[0]['id'],
            'filename': file.filename,
            'visibility': visibility
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/kb/documents/{document_id}/visibility")
async def set_document_visibility(document_id: str, request: SetVisibilityRequest):
    try:
        result = await kb_service.set_document_visibility(
            document_id=document_id,
            visibility=request.visibility,
            user_id="anonymous"
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/shared/search")
async def search_shared_kb(query: str, category: Optional[str] = None):
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = model.encode(query).tolist()

        results = await kb_service.search_shared_kb(
            query_embedding=query_embedding,
            category=category,
            limit=10
        )

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kb/feedback")
async def submit_kb_feedback(request: SubmitFeedbackRequest):
    try:
        result = await kb_service.submit_feedback(
            user_id="anonymous",
            document_id=request.document_id,
            chunk_id=request.chunk_id,
            feedback_type=request.feedback_type,
            rating=request.rating,
            correction_text=request.correction_text,
            is_helpful=request.is_helpful
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/my-contributions")
async def get_my_contributions():
    try:
        contributions = await kb_service.get_user_contributions(user_id="anonymous")
        return contributions

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/shared/stats")
async def get_shared_kb_stats():
    try:
        stats = await kb_service.get_shared_kb_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
