# Upload Issues FIXED

## What Was Wrong

### Issue 1: File Type Validation
**Problem**: Drag-drop rejected `.jsonl` files
- Code only accepted: `.codex`, `.claude`, `.log`
- Your files were `.jsonl` → Rejected!

**Fix**: Added `.jsonl`, `.json`, `.txt` to accepted types

### Issue 2: "Method Not Allowed" (405)
**Problem**: Netlify function missing
- Frontend calls `/api/sessions/folder`
- No Netlify function existed at that path
- Got 405 error

**Fix**: Created `netlify/functions/create-session-folder.js`

### Issue 3: No Debug Info
**Problem**: Errors were vague ("failed to create session")
- Couldn't tell what was actually failing
- No console logging

**Fix**: Added detailed console.log statements

## What I Fixed

### Files Changed

**1. `netlify-frontend/js/tmux-app.js`**:
- ✅ Accept `.jsonl`, `.json`, `.txt` files (line 375)
- ✅ Added debug logging to `startAnalysis()` (shows URL, status, errors)
- ✅ Added debug logging to `analyzeFolder()` (shows files being uploaded)
- ✅ Better error messages with HTTP status codes

**2. `netlify-frontend/index.html`**:
- ✅ Updated text: "drag .jsonl/.json/.log files here..."

**3. `netlify/functions/create-session-folder.js`** (NEW):
- ✅ Handles multipart file uploads
- ✅ Parses .jsonl, .json, .log, .txt files
- ✅ Extracts config files (mcp.json, subagents.json, config.json)
- ✅ Inserts into Supabase sessions table
- ✅ Returns session_url + metadata

**4. `netlify.toml`**:
- ✅ Added redirect: `/api/sessions/folder` → function

**5. `package.json`**:
- ✅ Added `parse-multipart-data` dependency

## How To Test Now

### Step 1: Run Netlify Dev

```bash
npm run dev
```

Opens at: http://localhost:8888

### Step 2: Test Log Mode (Quick Analysis)

1. Click **"Log Files"** (blue button)
2. **Option A**: Paste your .jsonl content
3. **Option B**: Drag your .jsonl file into the textarea
4. Click **"analyze [enter]"**
5. Should see: "initializing..." → "connecting to backend..."
6. **Check browser console** (F12) for debug output

### Step 3: Test Folder Mode

1. Click **".codex Folder"** (orange button)
2. Click the file input or select multiple files
3. Click **"analyze folder [enter]"**
4. Should upload and process
5. **Check browser console** for debug output

### What You'll See In Console

**Success**:
```
[DEBUG] Posting to: http://localhost:8888/api/sessions
[DEBUG] Response status: 200
```

**OR for folder**:
```
[DEBUG] Posting folder to: http://localhost:8888/api/sessions/folder
[DEBUG] Files: ['session.jsonl', 'config.json']
[DEBUG] Response status: 200
```

**Failure** (shows exactly what's wrong):
```
[DEBUG] Posting to: http://localhost:8888/api/sessions
[DEBUG] Response status: 405
[DEBUG] Error response: Method not allowed
```

## Common Issues

### Still Getting 405?

**Check these**:

1. **Is Netlify Dev running?**
   ```bash
   npm run dev
   # Should see: Server now ready on http://localhost:8888
   ```

2. **Check the URL in console**
   - Should be: `http://localhost:8888/api/sessions/folder`
   - NOT: `http://localhost:8000/...` (that's Python backend)

3. **Try curl directly**:
   ```bash
   echo '{"type":"test"}' > /tmp/test.jsonl

   curl http://localhost:8888/api/sessions/folder \
     -F "files=@/tmp/test.jsonl" \
     -F "encryption_enabled=false" \
     -v
   ```

   Should return JSON with `session_url`

### "Failed to fetch"

**Causes**:
1. Netlify Dev not running
2. CORS issue (shouldn't happen - already configured)
3. Network error

**Check**: Browser console shows the actual fetch error

### Netlify Edge Functions Error

**You mentioned**: "netlify throwing an error when trying to configure the edge functions environment"

**Important**:
- We're using **Netlify Functions** (serverless, in `netlify/functions/`)
- NOT **Edge Functions** (Deno-based, different thing)
- You don't need to configure Edge Functions
- The `.env` file has everything needed

**If Netlify Dev won't start**:
```bash
# Check Netlify CLI version
npx netlify --version

# Should be 17.0.0 or higher
# If not:
npm install netlify-cli@latest

# Then:
npm run dev
```

### Database Still Empty?

**After successful upload**:
1. Go to Supabase Dashboard
2. Table Editor → sessions table
3. Should see new rows with:
   - `session_url`: "folder-123456..."
   - `status`: "analyzing"
   - `metadata`: JSON with file info

**If empty**: Upload failed (check console logs)

## Environment Variables

**Required** (already in `.env`):
```
VITE_SUPABASE_URL=https://0ec90b57d6e95fcbda19832f.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbG...
```

**NOT required**:
- No custom backend URL needed
- No Edge Functions config
- No additional secrets

Netlify Dev automatically loads `.env` file.

## Architecture Reminder

```
User uploads file
     ↓
Frontend (localhost:8888)
     ↓
Netlify Function (JavaScript)
     ↓
Supabase Database
     ↓
Results displayed in UI
```

**NOT using**:
- ❌ Python FastAPI backend (only for GitHub OAuth)
- ❌ Edge Functions
- ❌ External server

## Next Steps

1. **Test it**: `npm run dev` → Upload a file
2. **Check console**: Look for `[DEBUG]` lines
3. **If 405**: Paste the console output - shows exact URL and error
4. **If success**: Check Supabase dashboard for the session

## About GitHub Mode

**Separate issue** - requires:
1. Supabase GitHub provider configured with scopes: `user repo read:user`
2. Python backend running: `uvicorn backend.main:app --reload`

See `SUPABASE_GITHUB_CONFIG.md` for that setup.

## Summary

✅ File type validation fixed (.jsonl accepted)
✅ Folder upload endpoint created
✅ Debug logging added
✅ Better error messages
✅ Should work now!

**Try**: `npm run dev` → Upload .jsonl file → Check console

The console will tell you exactly what's happening!
