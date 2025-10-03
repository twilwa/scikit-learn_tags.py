# Claude Code Log Analyzer

hey. u stuck? lemme take a look.

A minimalist, terminal-style web application that analyzes Claude Code session logs to provide insights, visualizations, and next-step recommendations.

## Features

- Drag-and-drop log file upload (.codex, .claude, or .log files)
- Real-time analysis with WebSocket updates
- Automatic secret redaction for security
- Multiple parallel analysis pipelines:
  - AST analysis of referenced code files
  - Dependency graph generation
  - Tool usage patterns
  - Code complexity metrics
- AI-generated insights prioritized by signal strength
- Interactive 2D network visualizations
- Async commenting on insights
- Optional encrypted analysis in TEE

## Quick Start

### Prerequisites

- Python 3.8+
- Supabase account (database is pre-configured)
- Node.js (optional, for frontend development)

### Installation

1. Install backend dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-backend.txt
```

2. Environment setup:
The `.env` file should already have your Supabase credentials configured.

3. Run the server:
```bash
python -m backend.main
```

4. Open your browser to `http://localhost:8000`

## Usage

1. Drop your Claude Code log file (.codex or .claude) into the upload zone, or paste log content
2. Optionally enable encryption for sensitive sessions
3. Click "analyze →" to start
4. Watch real-time progress as analysis completes
5. Review insights and visualizations as they appear
6. Add comments to specific insights if desired

## Architecture

### Backend

- **FastAPI** web framework with WebSocket support
- **Supabase** for data persistence (sessions, analysis results, insights)
- **Analysis Service** runs parallel Python-based code analysis tasks
- **Insight Generator** creates prioritized recommendations from analysis
- **Secret Redaction** utility removes sensitive data before processing

### Frontend

- **HTMX** for reactive UI without heavy JavaScript
- **Terminal aesthetic** with dark theme and monospace fonts
- **Vis.js** for network graph visualizations
- **WebSocket** client for real-time updates

### Database Schema

- `sessions` - log upload sessions with status tracking
- `analysis_results` - output from parallel analysis tasks
- `insights` - AI-generated recommendations with signal scores
- `user_comments` - async feedback on insights

## Analysis Pipeline

1. **Log Parsing**: Extract tool calls, file operations, referenced files
2. **Secret Redaction**: Remove API keys, tokens, passwords
3. **Parallel Analysis**:
   - Tool call patterns
   - AST analysis of code structure
   - Dependency graph generation
   - Complexity scoring
4. **Insight Generation**: Create 2-3 sentence recommendations
5. **Signal Scoring**: Prioritize insights by relevance and confidence
6. **Real-time Streaming**: Push results as they complete

## Future Enhancements

- 3D interactive codebase graphs with Three.js
- Desktop application with continuous folder watching
- LLM-driven prompt optimization with DSPy
- Stripe integration for cost tracking
- GitHub issue integration
- SSH access to analysis containers
- Downloadable encrypted reports

## Cost Model

- First 10 users: free tier
- Usage tracking with $1 threshold before billing prompt
- Serverless execution cost + 20% margin
- Modal or E2B for isolated Python execution

## Development

Run in development mode:
```bash
uvicorn backend.main:app --reload --port 8000
```

## License

See LICENSE file for details.

---

btw, i can open these in a TEE if you want. all your secrets are redacted. we won't keep them either way.
