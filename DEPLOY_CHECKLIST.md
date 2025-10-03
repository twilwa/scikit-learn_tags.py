# Deployment Checklist - Final Setup

## Critical: Fix Environment Variables FIRST

Before deploying, you **MUST** add these environment variables in Netlify:

### Step 1: Add SUPABASE_URL

1. Go to Netlify Dashboard → Your Site
2. Click **Site configuration** → **Environment variables**
3. Click **Add a variable**
4. Enter:
   - **Key**: `SUPABASE_URL`
   - **Value**: (same value as your `VITE_SUPABASE_URL`)
   - **Scopes**: Check ✅ **Functions**
   - **Deploy contexts**: All
5. Click **Create variable**

### Step 2: Add SUPABASE_ANON_KEY

1. Click **Add a variable** again
2. Enter:
   - **Key**: `SUPABASE_ANON_KEY`
   - **Value**: (same value as your `VITE_SUPABASE_ANON_KEY`)
   - **Scopes**: Check ✅ **Functions**
   - **Deploy contexts**: All
3. Click **Create variable**

### Why This Matters

Without these, you'll get 500 errors on:
- `/api/sessions/{id}/insights`
- `/api/sessions/{id}/analysis`
- `/api/sessions/{id}`

The `VITE_` prefix only works during build. Functions need the non-VITE versions at runtime.

## Deploy Commands

```bash
# 1. Commit all changes
git add .
git commit -m "Add interactive command pane, detailed progress, and env var fixes"
git push

# 2. Netlify will auto-deploy (1-2 minutes)
#    Watch: Deploys tab in Netlify dashboard

# 3. After deploy, test immediately
```

## Testing After Deploy

### 1. Test Environment Variables

```bash
# Open browser console on your deployed site
# Paste logs and click analyze

# Check console for:
✅ [DEBUG] Posting to: /api/sessions
✅ [DEBUG] Response status: 200

# Should NOT see:
❌ GET /api/sessions/.../insights 500
```

If you see 500 errors:
- Check Netlify → Site configuration → Environment variables
- Verify both `SUPABASE_URL` and `SUPABASE_ANON_KEY` exist
- Verify **Functions** scope is checked
- Trigger a new deploy (env vars only apply to new deploys)

### 2. Test Progress Messages

1. Upload logs (paste or folder)
2. Should see:
   ```
   [info] analysis modules queued:
   [info]   • log parser - extracting structured data
   [info]   • pattern detector - identifying workflow patterns
   [info]   • insight engine - generating recommendations
   [info]   • tool analyzer - mapping tool usage
   [info] waiting for backend processor...
   ```
3. Every 20 seconds:
   ```
   [info] parsing log entries... (20s)
   [info] analyzing tool usage patterns... (40s)
   [info] detecting workflow sequences... (60s)
   ```
4. After 2 minutes:
   ```
   [warning] polling timeout - analysis may not be running
   [info] note: backend analysis service may not be deployed
   [info] session saved in database - check back later
   ```

### 3. Test Command Pane

1. Press **Ctrl+B** then **T**
2. Command pane should open
3. Type `help` and press **Enter**
4. Should see list of all 9 commands
5. Press **Tab** (with empty input)
6. Should see suggestions panel with all commands
7. Type `ana` and press **Tab**
8. Should see only commands starting with "ana"
9. Press **Tab** again
10. Should cycle through matches
11. Press **Enter**
12. Should execute command

### 4. Test Tab Completion

1. Open command pane (Ctrl+B T)
2. Press **Tab** with empty input
3. See all commands in popup
4. Type `a` and press **Tab**
5. Should complete to `analyze-patterns`
6. Press **Tab** again
7. Should change to `analyze-tools`
8. Continue pressing **Tab**
9. Should cycle through all `analyze-*` commands

### 5. Test Footer Shortcuts

1. Look at bottom of page
2. Should see:
   ```
   shortcuts: [ctrl+b t - command pane] [ctrl+b % - split pane]
              [ctrl+b " - split horizontal] [ctrl+enter - analyze]
   ```
3. Shortcuts should be:
   - Green "shortcuts:" label
   - Gray text with bracketed keys
   - Readable and not overlapping

### 6. Test Folder Upload (with limit)

1. Select folder with 60 files
2. Click "analyze folder"
3. Should process first 30 files
4. Should NOT timeout (10 seconds max)
5. Check Netlify function logs:
   ```
   [FOLDER UPLOAD] Files: 60, Encryption: false
   [FOLDER UPLOAD] Warning: 60 files uploaded, processing first 30
   ```

## What Should Work Now

### ✅ Working Features

1. **Log Paste Analysis**
   - Paste JSON logs
   - Session created in Supabase
   - Detailed progress messages
   - No 500 errors

2. **Folder Upload**
   - Upload up to 60 files
   - Processes first 30
   - No timeout errors
   - Session saved

3. **Progress Feedback**
   - Clear module list
   - Rotating analysis steps
   - Elapsed time shown
   - Helpful timeout message

4. **Command Pane**
   - Open with Ctrl+B T
   - Tab completion works
   - Help system functional
   - 9 commands available

5. **Visual UI**
   - Footer shortcuts visible
   - Command pane styled
   - Suggestions panel works
   - Matches tmux aesthetic

### ⏳ Not Yet Working

1. **Actual Analysis**
   - Backend not deployed
   - No results returned
   - Polling times out
   - Commands show "backend not deployed" message

2. **Insights Generation**
   - No AI insights yet
   - Requires backend service

3. **Visualizations**
   - No graphs shown
   - Requires analysis results

4. **Command Execution**
   - Commands recognized
   - But show "not deployed" message
   - Will work when backend added

## Troubleshooting

### 500 Error on Insights Endpoint

**Problem**: Console shows:
```
GET /api/sessions/.../insights 500
```

**Solution**:
1. Go to Netlify → Environment variables
2. Verify these exist with Functions scope:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
3. If missing, add them (see top of this doc)
4. Trigger new deploy
5. Wait 1-2 minutes
6. Test again

### Command Pane Won't Open

**Problem**: Pressing Ctrl+B T does nothing.

**Solution**:
1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R)
3. Check browser console for JS errors
4. Verify `pane-command` element exists in HTML

### Tab Completion Not Working

**Problem**: Pressing Tab does nothing.

**Solution**:
1. Make sure command input is focused
2. Check if suggestions panel is hidden (CSS issue)
3. Open browser console, check for errors
4. Verify `ANALYSIS_COMMANDS` object exists

### Progress Messages Not Showing

**Problem**: Only see "initializing..." and nothing else.

**Solution**:
1. Check that session was created (status 200)
2. Verify polling started (check console)
3. Look for JS errors in console
4. Hard refresh page

### LocalStorage Quota Error

**Problem**: Console shows:
```
Error: Resource::kQuotaBytesPerItem quota exceeded
```

**Solution**:
This is harmless. Clear it:
```javascript
localStorage.clear()
```
Then refresh page.

## Next Steps

### When Backend Is Ready

1. **Update Command Execution**:
   ```javascript
   // In tmux-app.js, update executeCommand()
   const response = await fetch(`/api/analysis/${cmd}/${sessionId}`);
   const result = await response.json();
   addCommandOutput(JSON.stringify(result, null, 2));
   ```

2. **Connect Polling to Real Analysis**:
   - Backend updates session status
   - Frontend polls and gets real results
   - Visualizations auto-populate

3. **Add More Commands**:
   - `export-json`
   - `export-pdf`
   - `view-session`
   - `delete-session`

### Immediate Improvements

Even without backend:

1. **Add Command History**:
   - Store last 50 commands
   - Navigate with ↑/↓ arrows

2. **Add Session List View**:
   - Show all sessions from Supabase
   - Click to view details

3. **Add Settings Panel**:
   - Configure polling interval
   - Toggle progress messages
   - Set default mode

## Current File Structure

```
netlify-frontend/
├── index.html                 # Main HTML with command pane
├── css/
│   └── tmux.css              # Styles including command pane
└── js/
    └── tmux-app.js           # JS including tab completion

netlify/functions/
├── create-session.js         # Creates session (fixed crypto import)
├── create-session-folder.js  # Folder upload (30 file limit)
├── get-insights.js           # Gets insights (env var validation)
├── get-analysis.js           # Gets analysis (env var validation)
└── get-session.js            # Gets session (env var validation)

docs/
├── NETLIFY_ENV_FIX.md        # Detailed env var instructions
├── FEEDBACK_IMPROVEMENTS.md  # Progress messages explanation
├── INTERACTIVE_FEATURES.md   # Command pane documentation
└── DEPLOY_CHECKLIST.md       # This file
```

## Summary

**Before Deploy**:
1. ✅ Add `SUPABASE_URL` env var with Functions scope
2. ✅ Add `SUPABASE_ANON_KEY` env var with Functions scope
3. ✅ Commit and push code

**After Deploy**:
1. ✅ Test log paste (check for 500 errors)
2. ✅ Test progress messages (detailed steps)
3. ✅ Test command pane (Ctrl+B T)
4. ✅ Test tab completion (press Tab)
5. ✅ Test folder upload (<30 files)

**Expected Results**:
- No 500 errors
- Detailed progress messages
- Working command pane
- Tab completion cycles through commands
- Timeout message explains backend needed

**Next Step**:
Deploy Python backend or implement Edge Functions for actual analysis functionality!

## Quick Reference

### Environment Variables Needed

| Variable | Scope | Where Used |
|----------|-------|------------|
| `VITE_SUPABASE_URL` | Builds | Frontend (Vite) |
| `VITE_SUPABASE_ANON_KEY` | Builds | Frontend (Vite) |
| `SUPABASE_URL` | **Functions** ✅ | Netlify Functions |
| `SUPABASE_ANON_KEY` | **Functions** ✅ | Netlify Functions |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+B T** | Open command pane |
| **Ctrl+Enter** | Analyze (in textarea) |
| **Tab** | Show/cycle completions |
| **Enter** | Execute command |
| **Escape** | Hide suggestions |

### Available Commands

1. `analyze-patterns` - Detect workflow patterns
2. `analyze-tools` - Analyze tool usage
3. `generate-insights` - Generate AI insights
4. `build-graph` - Build dependency graphs
5. `extract-features` - Extract features
6. `detect-errors` - Identify errors
7. `list-sessions` - List all sessions
8. `help` - Show help
9. `clear` - Clear output

Type `help [command]` for details on any command.

---

**Ready to deploy!** Follow the steps above and your interactive log analyzer will be live! 🚀
