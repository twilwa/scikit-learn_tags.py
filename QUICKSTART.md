# Quick Start Guide

## ⚠️ Important: This is a Netlify Project

This project uses **Netlify Functions** (JavaScript/Node.js), NOT Python FastAPI backend.

## Setup (1 Minute)

### 1. Install Dependencies

```bash
npm install
```

### 2. Run Locally

```bash
npm run dev
```

Opens at: **http://localhost:8888**

## What Was Wrong

**The Issue**: "405 Method Not Allowed" on folder upload

**Root Cause**: The folder upload endpoint didn't exist!
- Project uses Netlify Functions (JavaScript)
- You were getting 405 because `/api/sessions/folder` wasn't implemented
- Python backend exists but is only for GitHub OAuth
- Database is fine (just empty until you upload)

**The Fix**:
1. ✅ Created `netlify/functions/create-session-folder.js`
2. ✅ Added redirect in `netlify.toml`
3. ✅ Installed `parse-multipart-data` for file parsing
4. ✅ Function handles multipart uploads, parses configs, stores in DB

## Test It Now

### Option 1: Via UI

```bash
npm run dev
# Opens http://localhost:8888
```

1. Click orange ".codex Folder" button
2. Select any `.jsonl`, `.json`, or `.log` files
3. Click "analyze folder"
4. Should work now!

### Option 2: Via curl

```bash
# Create test file
echo '{"type":"test","timestamp":"2025-01-01"}' > /tmp/test.jsonl

# Upload it
curl http://localhost:8888/api/sessions/folder \
  -F "files=@/tmp/test.jsonl" \
  -F "encryption_enabled=false"

# Should return JSON with session_url
```

### Option 3: Via browser console

```javascript
const formData = new FormData();
const blob = new Blob([JSON.stringify({type: "test"})], {type: 'application/json'});
const file = new File([blob], "test.jsonl");
formData.append('files', file);
formData.append('encryption_enabled', 'false');

fetch('http://localhost:8888/api/sessions/folder', {
    method: 'POST',
    body: formData
}).then(r => r.json()).then(console.log);
```

## How The Project Works

### Architecture

**Frontend** (`netlify-frontend/`):
- Pure HTML/JS/CSS
- Terminal-style UI
- Three mode buttons

**Backend** (TWO parts!):

1. **Netlify Functions** (`netlify/functions/*.js`):
   - `create-session.js` - Log paste/upload
   - `create-session-folder.js` - Folder upload ← NEW!
   - `get-session.js`, `get-analysis.js`, `get-insights.js`
   - Run via Netlify Dev

2. **Python FastAPI** (`backend/*.py`):
   - ONLY for GitHub OAuth
   - Handles repo analysis
   - Run separately: `uvicorn backend.main:app`

**Database**:
- Supabase (already connected via Bolt)
- Tables: sessions, analysis_results, insights, etc.
- Env vars in `.env`

### The Three Modes

**1. GitHub Only** (green):
- Uses Python backend
- Requires: GitHub OAuth setup in Supabase
- No logs needed!

**2. Folder Upload** (orange):
- Uses Netlify Function ← YOU ARE HERE
- Works now!
- Parses .codex folders with configs

**3. Log Files** (blue):
- Uses Netlify Function
- Already working
- Quick paste/upload

## Folder Upload Details

**What it accepts**:
- `.jsonl` - JSONL logs (line-delimited JSON)
- `.json` - JSON logs or config files
- `.log`, `.txt` - Plain text logs

**Special files**:
- `config.json` - Interaction style settings
- `mcp.json` - MCP server configuration
- `subagents.json` - Subagent definitions

**What it returns**:
```json
{
  "session_url": "folder-1234567890-abc123",
  "status": "analyzing",
  "total_logs": 3,
  "total_entries": 150,
  "configs_found": ["config.json", "mcp.json"],
  "config_insights": {
    "mcp": {
      "servers_configured": 2,
      "servers": ["filesystem", "postgres"]
    }
  }
}
```

## Troubleshooting

### Still getting 405?

**Check**:
```bash
# Is Netlify Dev running?
npm run dev

# Can you see the function?
curl http://localhost:8888/.netlify/functions/create-session-folder

# Should return 405 (need POST) but not 404
```

### "Failed to fetch"

**Check browser console** for actual error:
- CORS? (Should be configured)
- Wrong URL? (Should be `/api/sessions/folder`)
- Netlify Dev running?

### Function logs not showing?

Netlify Dev shows logs in terminal where you ran `npm run dev`

Look for:
```
[FOLDER UPLOAD] Processing request
[FOLDER UPLOAD] Received N parts
[FOLDER UPLOAD] Files: N, Encryption: false
```

### Database empty after upload?

**Check**:
1. Did upload succeed? (Check terminal logs)
2. Supabase dashboard → Table Editor → sessions
3. Look for rows with `folder_type: ".codex"` or `"logs"`

## GitHub Mode Setup

If you want to use GitHub mode:

1. **Configure Supabase**:
   - Dashboard → Authentication → Providers → GitHub
   - Add scopes: `user repo read:user`
   - Save

2. **Run Python backend** (separate terminal):
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

3. **Use it**:
   - Click "GitHub Only"
   - "connect github"
   - Authorize
   - View repos

See `SUPABASE_GITHUB_CONFIG.md` for details.

## Files Changed

**New**:
- `netlify/functions/create-session-folder.js` - Folder upload handler

**Modified**:
- `netlify.toml` - Added redirect for `/api/sessions/folder`
- `package.json` - Added `parse-multipart-data` dependency

**Already Working**:
- Frontend UI
- Database tables
- Other Netlify functions
- GitHub OAuth backend

## Next Steps

1. `npm run dev`
2. Test folder upload via UI
3. Check it inserts into database
4. Optionally: Set up GitHub OAuth

The folder upload **should work now** - try it!
