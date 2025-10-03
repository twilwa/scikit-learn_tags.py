from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class SessionStatus(str, Enum):
    UPLOADING = "uploading"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisType(str, Enum):
    AST = "ast"
    DEPENDENCY_GRAPH = "dependency_graph"
    TOOL_CALLS = "tool_calls"
    COMPLEXITY = "complexity"
    FILE_STRUCTURE = "file_structure"

class InsightType(str, Enum):
    NEXT_STEP = "next_step"
    CODE_ISSUE = "code_issue"
    ARCHITECTURE = "architecture"
    OPTIMIZATION = "optimization"

class SessionCreate(BaseModel):
    log_content: str
    encryption_enabled: bool = False
    user_id: Optional[str] = None

class SessionResponse(BaseModel):
    id: str
    session_url: str
    status: SessionStatus
    created_at: datetime
    expires_at: datetime
    cost_estimate: float = 0.0

class AnalysisResultCreate(BaseModel):
    session_id: str
    analysis_type: AnalysisType
    result_data: Dict[str, Any]
    signal_score: float = 0.0

class AnalysisResultResponse(BaseModel):
    id: str
    session_id: str
    analysis_type: AnalysisType
    result_data: Dict[str, Any]
    status: AnalysisStatus
    signal_score: float
    completed_at: Optional[datetime] = None
    created_at: datetime

class InsightCreate(BaseModel):
    session_id: str
    analysis_id: Optional[str] = None
    insight_text: str
    insight_type: InsightType
    signal_score: float = 0.0
    confidence: float = 0.5
    visualization_data: Optional[Dict[str, Any]] = None

class InsightResponse(BaseModel):
    id: str
    session_id: str
    insight_text: str
    insight_type: InsightType
    signal_score: float
    confidence: float
    visualization_data: Optional[Dict[str, Any]]
    shown: bool
    created_at: datetime

class CommentCreate(BaseModel):
    session_id: str
    insight_id: Optional[str] = None
    comment_text: str

class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
