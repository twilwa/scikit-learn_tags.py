from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List
import json
from pydantic import BaseModel

from backend.database import get_supabase
from backend.models import SessionCreate, SessionResponse, SessionStatus, AnalysisType
from backend.utils.secret_redaction import redact_secrets
from backend.utils.log_parser import parse_log
from backend.services.analysis_service import AnalysisService
from backend.services.insight_service import InsightGenerator
from backend.routers import voice_router

app = FastAPI(title="Claude Code Log Analyzer")

app.include_router(voice_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

active_connections: Dict[str, WebSocket] = {}
analysis_service = AnalysisService()
insight_generator = InsightGenerator()

class CreateSessionRequest(BaseModel):
    log_content: str
    encryption_enabled: bool = False

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("frontend/index.html", "r") as f:
        return f.read()

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    try:
        supabase = get_supabase()

        redacted_log, found_secrets = redact_secrets(request.log_content)

        session_url = str(uuid.uuid4())

        result = supabase.table("sessions").insert({
            "session_url": session_url,
            "log_content": request.log_content,
            "redacted_log": redacted_log,
            "encryption_enabled": request.encryption_enabled,
            "status": SessionStatus.UPLOADING.value,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "metadata": {
                "secrets_found": len(found_secrets),
                "log_size": len(request.log_content)
            }
        }).execute()

        session_data = result.data[0]

        asyncio.create_task(process_log_analysis(session_data["id"], session_url, redacted_log))

        return SessionResponse(
            id=session_data["id"],
            session_url=session_url,
            status=SessionStatus.ANALYZING,
            created_at=session_data["created_at"],
            expires_at=session_data["expires_at"],
            cost_estimate=0.0
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_url}")
async def get_session(session_url: str):
    try:
        supabase = get_supabase()

        result = supabase.table("sessions").select("*").eq("session_url", session_url).maybeSingle().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Session not found")

        return result.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_url}/insights")
async def get_insights(session_url: str):
    try:
        supabase = get_supabase()

        session = supabase.table("sessions").select("id").eq("session_url", session_url).maybeSingle().execute()

        if not session.data:
            raise HTTPException(status_code=404, detail="Session not found")

        insights = supabase.table("insights").select("*").eq("session_id", session.data["id"]).order("signal_score", desc=True).execute()

        return insights.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_url}/analysis")
async def get_analysis(session_url: str):
    try:
        supabase = get_supabase()

        session = supabase.table("sessions").select("id").eq("session_url", session_url).maybeSingle().execute()

        if not session.data:
            raise HTTPException(status_code=404, detail="Session not found")

        analysis = supabase.table("analysis_results").select("*").eq("session_id", session.data["id"]).order("signal_score", desc=True).execute()

        return analysis.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{session_url}")
async def websocket_endpoint(websocket: WebSocket, session_url: str):
    await websocket.accept()
    active_connections[session_url] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "comment":
                await handle_comment(session_url, message.get("data", {}))

    except WebSocketDisconnect:
        del active_connections[session_url]

async def handle_comment(session_url: str, data: Dict):
    supabase = get_supabase()

    session = supabase.table("sessions").select("id").eq("session_url", session_url).maybeSingle().execute()

    if session.data:
        supabase.table("user_comments").insert({
            "session_id": session.data["id"],
            "insight_id": data.get("insight_id"),
            "comment_text": data.get("text", "")
        }).execute()

async def send_ws_message(session_url: str, message_type: str, data: Dict):
    if session_url in active_connections:
        try:
            await active_connections[session_url].send_json({
                "type": message_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception:
            pass

async def process_log_analysis(session_id: str, session_url: str, log_content: str):
    supabase = get_supabase()

    try:
        supabase.table("sessions").update({
            "status": SessionStatus.ANALYZING.value
        }).eq("id", session_id).execute()

        parsed_log = parse_log(log_content)

        await send_ws_message(session_url, "status", {"message": "Log parsed successfully", "progress": 20})

        analysis_tasks = [
            ("tool_calls", analysis_service.run_tool_call_analysis(parsed_log, session_id)),
            ("ast_analysis", analysis_service.run_ast_analysis(parsed_log, session_id)),
            ("dependency_graph", analysis_service.run_dependency_graph(parsed_log, session_id)),
            ("complexity", analysis_service.run_complexity_analysis(parsed_log, session_id))
        ]

        analysis_results = {}
        for i, (analysis_type, task) in enumerate(analysis_tasks):
            result = await task

            signal_score = analysis_service.calculate_signal_score(analysis_type, result, parsed_log)

            analysis_record = supabase.table("analysis_results").insert({
                "session_id": session_id,
                "analysis_type": analysis_type,
                "result_data": result,
                "status": "completed",
                "signal_score": signal_score,
                "completed_at": datetime.utcnow().isoformat()
            }).execute()

            analysis_results[analysis_type] = result

            progress = 20 + ((i + 1) / len(analysis_tasks)) * 60
            await send_ws_message(session_url, "analysis_complete", {
                "type": analysis_type,
                "data": result,
                "progress": progress
            })

        await send_ws_message(session_url, "status", {"message": "Generating insights", "progress": 85})

        insights = insight_generator.generate_insights(parsed_log, analysis_results)

        for insight_text, insight_type, signal_score, viz_data in insights:
            insight_record = supabase.table("insights").insert({
                "session_id": session_id,
                "insight_text": insight_text,
                "insight_type": insight_type.value,
                "signal_score": signal_score,
                "confidence": 0.8,
                "visualization_data": viz_data if viz_data else None,
                "shown": False
            }).execute()

            await send_ws_message(session_url, "insight", {
                "id": insight_record.data[0]["id"],
                "text": insight_text,
                "type": insight_type.value,
                "signal_score": signal_score,
                "visualization": viz_data
            })

        supabase.table("sessions").update({
            "status": SessionStatus.COMPLETED.value
        }).eq("id", session_id).execute()

        await send_ws_message(session_url, "complete", {"message": "Analysis complete", "progress": 100})

    except Exception as e:
        supabase.table("sessions").update({
            "status": SessionStatus.FAILED.value,
            "metadata": {"error": str(e)}
        }).eq("id", session_id).execute()

        await send_ws_message(session_url, "error", {"message": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
