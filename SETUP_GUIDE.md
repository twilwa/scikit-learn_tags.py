# Complete Setup Guide

## Quick Start (5 Minutes)

### 1. Enable GitHub OAuth in Supabase

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Navigate to **Authentication** → **Providers**
4. Find **GitHub** and click to configure
5. Enable the provider
6. Enter your GitHub OAuth credentials (see below)
7. Set redirect URL: `https://your-project.supabase.co/auth/v1/callback`
8. Save

### 2. Create GitHub OAuth App

1. Go to https://github.com/settings/developers
2. Click **"New OAuth App"**
3. Fill in:
   - **Application name**: Claude Code Analyzer
   - **Homepage URL**: `https://your-domain.com` (or `http://localhost:8000` for local)
   - **Authorization callback URL**: `https://your-project.supabase.co/auth/v1/callback`
4. Click **"Register application"**
5. Copy your **Client ID**
6. Generate a **Client Secret** and copy it
7. Paste both into Supabase GitHub provider settings

### 3. Run the Application

```bash
# No additional env variables needed!
# Supabase handles everything

uvicorn backend.main:app --reload
```

Visit: `http://localhost:8000/netlify-frontend/`

## Three Analysis Modes

### Mode 1: GitHub Only (No Uploads!)

**What you get**:
- ✅ No log files needed
- ✅ Direct repo analysis
- ✅ File-by-file exploration
- ✅ Language breakdown
- ✅ Structure analysis

**Setup**: Just enable GitHub provider in Supabase (above)

**Usage**:
1. Click "GitHub Only" mode (green button)
2. Click "connect github"
3. Authorize on GitHub
4. View your repositories
5. Click "analyze" on any repo
6. Explore files interactively

**How it works**:
- Supabase handles OAuth
- GitHub token stored securely by Supabase
- Automatic token refresh
- Access via `session.provider_token`

---

### Mode 2: .codex/.claude Folder Upload

**What you get**:
- ✅ All session logs analyzed
- ✅ Config insights (MCP, subagents, interaction styles)
- ✅ Folder structure visualization
- ✅ Configuration recommendations
- ✅ Pattern detection

**Setup**: None needed, works immediately

**Usage**:
1. Click ".codex Folder" mode (orange button)
2. Click file input to select folder
3. Or drag folder onto input
4. Click "analyze folder"
5. View config insights + log analysis

**Supported files**:
- `.jsonl` - JSONL log format (line-by-line JSON)
- `.json` - JSON logs
- `.txt`, `.log` - Plain text logs
- `config.json` - Interaction settings
- `mcp.json` - MCP server configuration
- `subagents.json` - Subagent definitions

**Example folder structure**:
```
.codex/
├── sessions/
│   ├── session1.jsonl
│   ├── session2.jsonl
│   └── session3.jsonl
├── config.json
├── mcp.json
└── subagents.json
```

**What gets analyzed**:
- Total logs and entries
- Config files found
- MCP servers configured
- Subagents defined
- Interaction style settings
- Plus all normal log analysis

---

### Mode 3: Log Files Only

**What you get**:
- ✅ Quick paste/upload
- ✅ Pattern detection
- ✅ Session analysis
- ✅ Build detection

**Setup**: None needed

**Usage**:
1. Click "Log Files" mode (blue button)
2. Paste log content in textarea
3. Or drag .jsonl/.json/.log files
4. Optional: Enable TEE encryption
5. Click "analyze"

**Best for**:
- Single session review
- Quick analysis
- No config context needed

---

## Troubleshooting

### "405 Method Not Allowed" for Folder Upload

**Fix**: Ensure you're using POST, not GET. The endpoint is:
```
POST /api/sessions/folder
Content-Type: multipart/form-data
```

Frontend handles this automatically.

### "GitHub provider not enabled"

**Fix**:
1. Supabase dashboard → Authentication → Providers
2. Enable GitHub
3. Add Client ID and Secret
4. Save

### "No GitHub token found"

**Cause**: User signed in without GitHub provider

**Fix**: Sign out and use "Connect GitHub" button specifically

### "Repository not found. Sync repos first."

**Fix**: Click "view repositories" to sync first, then analyze

### Can't select folder in browser

**Solution**: The folder input uses `webkitdirectory` attribute.
- Supported: Chrome, Edge, Safari
- Not supported: Some older browsers
- Alternative: Zip folder and upload (coming soon)

---

## Architecture Overview

### GitHub Mode Flow

```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Click "Connect GitHub"
     ▼
┌──────────────────┐
│ Supabase Auth    │ → OAuth with GitHub
└────┬─────────────┘
     │ 2. Get provider_token
     ▼
┌──────────────────┐
│ Backend API      │ → Fetch repos via GitHub API
└────┬─────────────┘
     │ 3. Cache in github_repositories
     ▼
┌──────────────────┐
│ Database         │ → Store repo metadata
└────┬─────────────┘
     │ 4. User selects repo
     ▼
┌──────────────────┐
│ Analyze Repo     │ → Fetch tree, analyze structure
└────┬─────────────┘
     │ 5. Create session
     ▼
┌──────────────────┐
│ Display Results  │ → Show findings
└──────────────────┘
```

### Folder Upload Flow

```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Select folder
     ▼
┌──────────────────┐
│ Browser          │ → Collect all files
└────┬─────────────┘
     │ 2. Upload via FormData
     ▼
┌──────────────────┐
│ Backend API      │ → Save to temp directory
└────┬─────────────┘
     │ 3. Parse folder
     ▼
┌──────────────────┐
│ Folder Parser    │ → Extract logs + configs
└────┬─────────────┘
     │ 4. Analyze configs
     ▼
┌──────────────────┐
│ Config Analyzer  │ → MCP, subagents, styles
└────┬─────────────┘
     │ 5. Combine logs
     ▼
┌──────────────────┐
│ Standard Analysis│ → Pattern detection
└────┬─────────────┘
     │ 6. Return insights
     ▼
┌──────────────────┐
│ Display Results  │ → Folder structure + insights
└──────────────────┘
```

---

## Database Schema

### Key Tables

**github_repositories**:
- `auth_user_id` - References auth.users(id)
- `repo_full_name` - "owner/repo"
- `repo_url` - GitHub URL
- `primary_language` - Main language
- `stars`, `forks`, `open_issues` - Metrics

**repo_analysis_sessions**:
- `auth_user_id` - References auth.users(id)
- `github_repository_id` - References github_repositories(id)
- `session_url` - Unique session ID
- `session_type` - exploration, full_analysis, etc.
- `findings` - JSONB analysis results

**user_profiles**:
- `auth_user_id` - Links to Supabase auth.users
- `username` - Display name
- `level`, `xp`, `points` - Gamification

---

## API Endpoints

### GitHub Mode

```bash
# List repositories (auto-syncs from GitHub)
GET /api/github/repositories?sync=true
Authorization: Bearer <supabase_access_token>

# Create analysis session
POST /api/github/analyze
Authorization: Bearer <supabase_access_token>
{
  "repo_full_name": "owner/repo",
  "session_type": "exploration"
}

# Get analysis results
GET /api/github/analysis/<session_url>
Authorization: Bearer <supabase_access_token>

# Explore specific file
POST /api/github/explore/<session_url>?file_path=src/main.py
Authorization: Bearer <supabase_access_token>
```

### Folder Mode

```bash
# Upload folder
POST /api/sessions/folder
Content-Type: multipart/form-data

files: [file1, file2, file3, ...]
encryption_enabled: false

# Returns:
{
  "session_url": "uuid",
  "folder_structure": {...},
  "configs_found": ["config.json", "mcp.json"],
  "config_insights": {...}
}
```

### Log Mode

```bash
# Upload logs
POST /api/sessions
{
  "log_content": "...",
  "encryption_enabled": false
}
```

---

## Security

### GitHub OAuth
- Tokens managed by Supabase Auth
- Never stored in frontend
- Automatic token refresh
- Can revoke anytime at github.com/settings/applications

### Folder Uploads
- Processed in temp directory
- Deleted after analysis
- Secrets auto-redacted
- Optional TEE encryption

### API Authentication
- All GitHub endpoints require auth
- Bearer token in Authorization header
- RLS policies enforce user isolation
- No cross-user data access

---

## Development

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Run backend
uvicorn backend.main:app --reload --port 8000

# Frontend is served at:
http://localhost:8000/netlify-frontend/
```

### Environment Variables

**Not needed for GitHub** - Supabase handles everything!

Only set if using custom backend:
```bash
VITE_SUPABASE_URL=your_url
VITE_SUPABASE_ANON_KEY=your_key
```

### Testing

```bash
# Test folder upload
curl -X POST http://localhost:8000/api/sessions/folder \
  -F "files=@.codex/config.json" \
  -F "files=@.codex/sessions/log1.jsonl" \
  -F "encryption_enabled=false"

# Test GitHub (requires auth token)
curl http://localhost:8000/api/github/repositories?sync=true \
  -H "Authorization: Bearer <your_supabase_token>"
```

---

## Next Steps

1. ✅ Enable GitHub provider in Supabase
2. ✅ Create GitHub OAuth app
3. ✅ Run the application
4. ✅ Test all three modes
5. ✅ Explore your repositories!

**No logs needed for GitHub mode - just connect and analyze!**

---

## Support

**Issues?**
- Check Supabase logs
- Verify GitHub provider enabled
- Ensure OAuth callback URL correct
- Test with folder mode first (no auth needed)

**Need help?**
- Read QUICKSTART.md for usage examples
- Check GITHUB_INTEGRATION.md for details
- Review UI_CHANGES.md for frontend info
