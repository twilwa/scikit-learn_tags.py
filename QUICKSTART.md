# Quick Start Guide

## Three Ways to Use the Platform

### 1. GitHub Only (No Logs Needed!)

**Perfect for**: Quick code exploration, repo analysis, learning new codebases

**Setup**:
```bash
# Set in .env
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

**Usage**:
1. Click "GitHub Only" on homepage
2. Connect your GitHub account
3. Select a repository
4. Get instant analysis
5. Explore files interactively

**What You Get**:
- Repository structure
- Language breakdown
- File organization
- Build detection
- No need to upload anything!

---

### 2. .codex / .claude Folder Upload

**Perfect for**: Deep analysis with configuration context, understanding your setup

**What to Upload**:
```
.codex/
├── sessions/
│   ├── session1.jsonl
│   ├── session2.jsonl
│   └── session3.jsonl
├── config.json        # Your interaction settings
├── mcp.json           # MCP server configuration
└── subagents.json     # Subagent setup
```

**Usage**:
1. Click ".codex / .claude Folder"
2. Drag and drop your entire folder
3. Or select multiple files
4. Get comprehensive analysis

**What You Get**:
- All session logs analyzed
- Configuration insights (MCP, subagents, interaction styles)
- Folder structure visualization
- Config recommendations
- Pattern detection across sessions

**Example Analysis**:
```json
{
  "folder_structure": {
    "name": ".codex",
    "children": [
      {"name": "sessions", "type": "directory"},
      {"name": "config.json", "type": "file"},
      {"name": "mcp.json", "type": "file"}
    ]
  },
  "config_insights": {
    "mcp": {
      "total_servers": 5,
      "servers": ["filesystem", "github", "brave-search", ...],
      "recommendations": ["..."]
    },
    "interaction_style": {
      "verbosity": "concise",
      "code_format": "markdown"
    }
  }
}
```

---

### 3. Log Files Only

**Perfect for**: Quick analysis without configuration, single session review

**What to Upload**:
- `.jsonl` files (JSONL format logs)
- `.json` files (JSON logs)
- `.txt` or `.log` files (plain text)

**Usage**:
1. Click "Log Files Only"
2. Paste content or upload file
3. Get analysis

**What You Get**:
- Session analysis
- Pattern detection
- Insights and recommendations
- No config context

---

## Feature Comparison

| Feature | GitHub Only | Folder Upload | Log Files Only |
|---------|-------------|---------------|----------------|
| **Setup Required** | GitHub OAuth | None | None |
| **Upload Needed** | ❌ No | ✅ Folder | ✅ Files |
| **Config Analysis** | ❌ | ✅ Yes | ❌ |
| **Repo Structure** | ✅ Yes | ❌ | ❌ |
| **Session Logs** | ❌ | ✅ Yes | ✅ Yes |
| **MCP Insights** | ❌ | ✅ Yes | ❌ |
| **Subagent Analysis** | ❌ | ✅ Yes | ❌ |
| **File Exploration** | ✅ Interactive | 📊 Static | ❌ |
| **Build Detection** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Speed** | ⚡ Instant | 🔄 Upload | 🔄 Upload |

---

## Recommended Workflow

### For Understanding New Repos
→ Use **GitHub Only**

### For Debugging Your Setup
→ Use **Folder Upload** (.codex with configs)

### For Quick Session Review
→ Use **Log Files Only**

### For Collaborative Work
→ Start any mode, then switch to **Voice Session**

---

## API Endpoints

### GitHub Mode
```bash
# Connect
GET /api/github/auth/login

# List repos
GET /api/github/repositories?user_profile_id=<id>&sync=true

# Analyze
POST /api/github/analyze
{
  "user_profile_id": "uuid",
  "repo_full_name": "owner/repo",
  "session_type": "exploration"
}
```

### Folder Upload Mode
```bash
POST /api/sessions/folder
Content-Type: multipart/form-data

files: [file1, file2, file3, ...]
encryption_enabled: false
```

### Log Files Mode
```bash
POST /api/sessions
Content-Type: application/json

{
  "log_content": "...",
  "encryption_enabled": false
}
```

---

## Configuration File Formats

### config.json
```json
{
  "interaction_style": {
    "verbosity": "concise",
    "code_format": "markdown",
    "explanation_level": "detailed"
  },
  "model": "claude-3-5-sonnet-20241022",
  "temperature": 0.7
}
```

### mcp.json
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
      "env": {}
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "..."
      }
    }
  }
}
```

### subagents.json
```json
{
  "subagents": [
    {
      "name": "code-reviewer",
      "model": "claude-3-5-sonnet",
      "role": "review",
      "capabilities": ["code_quality", "best_practices"]
    },
    {
      "name": "debugger",
      "model": "claude-3-opus",
      "role": "debug",
      "capabilities": ["error_analysis", "root_cause"]
    }
  ]
}
```

---

## JSONL Log Format

Each line is a JSON object:

```jsonl
{"timestamp": "2025-10-03T10:00:00Z", "event": "tool_call", "tool": "write_file", "args": {...}}
{"timestamp": "2025-10-03T10:00:01Z", "event": "tool_result", "result": "success"}
{"timestamp": "2025-10-03T10:00:02Z", "event": "message", "content": "File written successfully"}
```

Parser handles:
- Multi-line entries
- Nested JSON
- Mixed formats
- Large files (streaming)

---

## Folder Structure Detection

Automatically detects:

**.codex folders**:
```
.codex/
├── sessions/        # Session logs
├── config.json      # User config
├── mcp.json         # MCP servers
└── subagents.json   # Subagents
```

**.claude folders**:
```
.claude/
├── logs/            # Log files
├── settings.json    # Settings
└── plugins/         # Plugin configs
```

**Generic folders**:
- Any structure
- Finds logs by extension
- Finds configs by name

---

## Common Use Cases

### 1. "Claude keeps doing X wrong"

**Use**: Folder Upload
- Upload your .codex folder
- Check config insights
- See if MCP/subagents misconfigured
- Review interaction style settings

### 2. "Need to understand this codebase fast"

**Use**: GitHub Only
- Connect GitHub
- Analyze repo structure
- Explore key files
- No downloads needed

### 3. "Session went off the rails"

**Use**: Log Files Only
- Upload the session .jsonl
- Get analysis
- See where it diverged
- Get recommendations

### 4. "Want to improve my setup"

**Use**: Folder Upload
- Upload full .codex with configs
- Get config analysis
- See MCP server recommendations
- Optimize interaction style

---

## Troubleshooting

### "Method Not Allowed"

**Cause**: Using GET instead of POST for uploads

**Fix**: Use correct endpoints:
- Logs: `POST /api/sessions`
- Folder: `POST /api/sessions/folder`
- GitHub: `POST /api/github/analyze`

### "Failed to parse folder"

**Cause**: Missing log files or wrong structure

**Fix**: Ensure folder contains:
- At least one .jsonl, .json, .txt, or .log file
- OR config files (config.json, mcp.json, etc.)

### "Config not detected"

**Cause**: Config files not at root level

**Fix**: Place config files at folder root:
```
.codex/
├── config.json      ← Here
├── mcp.json         ← Here
└── sessions/
    └── logs...
```

---

## Best Practices

### For GitHub Mode
1. Sync repos first with `?sync=true`
2. Start with "exploration" session type
3. Explore interesting files interactively
4. Export insights for later

### For Folder Mode
1. Upload complete .codex/.claude folder
2. Include all config files
3. Review config insights first
4. Then analyze session logs

### For Log Files Mode
1. Use for quick single-session review
2. Combine multiple sessions manually if needed
3. Add encryption for sensitive logs
4. Export analysis for documentation

---

## What Gets Analyzed

### From Logs
- Tool calls and results
- Error patterns
- Token usage
- Session flow
- Build success/failure
- Code changes

### From Configs
- MCP server setup
- Subagent configuration
- Interaction styles
- Model settings
- Custom commands

### From GitHub
- Repository structure
- Language breakdown
- File organization
- Dependencies
- Build configs

---

## Privacy & Security

### Folder Upload
- Files processed in memory
- Deleted after analysis
- Configs stored encrypted
- Secrets auto-redacted

### GitHub Mode
- OAuth tokens encrypted
- Only fetches public repos (unless granted)
- Can disconnect anytime
- No code stored permanently

### Log Files
- Secrets auto-redacted
- Optional TEE encryption
- 24-hour expiration
- Export for local storage

---

## Getting Started (30 seconds)

**Quickest**: GitHub Only
1. Visit homepage
2. Click "GitHub Only"
3. Authorize
4. Done!

**Most Powerful**: Folder Upload
1. Locate your .codex folder
2. Drag to upload area
3. Wait for analysis
4. Review insights

**Simplest**: Log Files
1. Paste log content
2. Click analyze
3. Done!

---

**Choose your path and start analyzing!**
