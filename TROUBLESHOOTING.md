# Troubleshooting Guide

## Understanding The Architecture

This project has **TWO separate backends**:

### 1. Netlify Functions (JavaScript) - For Log Uploads
- ✅ **Located**: `netlify/functions/*.js`
- ✅ **What**: Handles file uploads, log paste, sessions
- ✅ **How to run**: `npm run dev`
- ✅ **URL**: http://localhost:8888
- ✅ **Endpoints**:
  - `POST /api/sessions` - Log paste/upload
  - `POST /api/sessions/folder` - Folder upload
  - `GET /api/sessions/:url` - Get session
  - `GET /api/sessions/:url/analysis` - Get analysis
  - `GET /api/sessions/:url/insights` - Get insights

### 2. Python FastAPI - For GitHub OAuth ONLY
- ⚠️ **Located**: `backend/*.py`
- ⚠️ **What**: GitHub OAuth, repo analysis
- ⚠️ **How to run**: `uvicorn backend.main:app --reload`
- ⚠️ **URL**: http://localhost:8000
- ⚠️ **Endpoints**:
  - `GET /api/github/auth/debug` - Debug auth status
  - `GET /api/github/repositories` - List repos
  - `POST /api/github/analyze` - Analyze repo

**Key Point**: Log uploads work WITHOUT the Python backend!

## The Edge Functions Error - IGNORE IT!

```
✖ Setting up the Edge Functions environment
Error: There was a problem setting up the Edge Functions environment
```

**This is NOT the problem!**

- Edge Functions are a different Netlify feature (Deno-based)
- We're using **Netlify Functions** (Node.js-based)
- Notice the output says:
  ```
  ◈ Loaded function create-session
  ◈ Loaded function create-session-folder   ← These ARE loaded!
  ◈ Server now ready on http://localhost:8888
  ```

The functions ARE working despite that error!

## Testing The Setup

### Quick Test

```bash
# Start Netlify Dev
npm run dev

# In another terminal, run test script
./test-functions.sh
```

This tests:
1. Log paste upload
2. Folder upload
3. GitHub endpoint (optional)

### Manual Tests

**Test 1: Log paste** (should work immediately)
```bash
curl http://localhost:8888/api/sessions \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"log_content":"test","encryption_enabled":false}'
```

Expected: `{"session_url":"...", "status":"analyzing"}`

**Test 2: Folder upload** (should work immediately)
```bash
echo '{"type":"test"}' > /tmp/test.jsonl

curl http://localhost:8888/api/sessions/folder \
  -X POST \
  -F "files=@/tmp/test.jsonl" \
  -F "encryption_enabled=false"
```

Expected: `{"session_url":"folder-...", "status":"analyzing", ...}`

**Test 3: GitHub** (requires Python backend)
```bash
# Start Python backend first
uvicorn backend.main:app --reload --port 8000

# Then test
curl http://localhost:8000/api/github/auth/debug \
  -H "Authorization: Bearer test"
```

## Common Issues

### Issue: "404 Not Found" on log paste

**Symptoms**:
- Click "Log Files" mode
- Paste content
- Click "analyze"
- Get 404 error

**Causes**:
1. Netlify Dev not running
2. Function didn't load
3. Wrong URL

**Fix**:
```bash
# Stop Netlify Dev (Ctrl+C)
# Restart it
npm run dev

# Look for this in output:
# ◈ Loaded function create-session
# ◈ Loaded function create-session-folder
# ◈ Server now ready on http://localhost:8888

# Test directly
curl http://localhost:8888/.netlify/functions/create-session \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"log_content":"test","encryption_enabled":false}'
```

If still 404:
- Check `netlify.toml` has redirects
- Check function file exists: `netlify/functions/create-session.js`

### Issue: "Failed to fetch" on folder upload

**Symptoms**:
- Click ".codex Folder" mode
- Select files
- Click "analyze folder"
- Get "failed to fetch"

**Causes**:
1. CORS issue
2. Netlify Dev not running
3. Network error

**Fix**:
```bash
# Check function is loaded
npm run dev
# Should see: ◈ Loaded function create-session-folder

# Test with curl
echo '{"test":"data"}' > /tmp/test.jsonl
curl http://localhost:8888/api/sessions/folder \
  -F "files=@/tmp/test.jsonl" \
  -F "encryption_enabled=false"
```

**Check browser console** (F12) - shows actual error:
```
[DEBUG] Posting folder to: http://localhost:8888/api/sessions/folder
[DEBUG] Files: ['test.jsonl']
[DEBUG] Response status: 500
[DEBUG] Error response: ...
```

### Issue: GitHub connection fails

**Symptoms**:
- Click "GitHub Only"
- Click "connect github"
- OAuth succeeds but can't fetch repos
- Gets 404 or timeout

**Cause**: Python backend NOT running

**Fix**:
```bash
# Terminal 1: Netlify Dev (keep running)
npm run dev

# Terminal 2: Python backend
cd /tmp/cc-agent/57953517/project
uvicorn backend.main:app --reload --port 8000

# Now try GitHub mode
```

**Note**: You need pip/uvicorn installed. If not:
```bash
# Install Python dependencies
pip install fastapi uvicorn supabase python-dotenv
```

### Issue: "Method Not Allowed" (405)

**Symptoms**:
- Any upload gets 405 error

**Causes**:
1. Wrong HTTP method (GET instead of POST)
2. OPTIONS request not handled
3. Function not loaded

**Fix**:

Check browser console:
```javascript
// Should see these headers in Network tab
Request Method: POST
Content-Type: application/json  (or multipart/form-data for folder)
```

Test curl:
```bash
# Should return 405 if using GET
curl http://localhost:8888/api/sessions

# Should return 200 with POST
curl http://localhost:8888/api/sessions \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"log_content":"test","encryption_enabled":false}'
```

### Issue: Database errors

**Symptoms**:
- Upload succeeds but shows error
- Console shows: "table 'sessions' does not exist"

**Cause**: Supabase tables not created

**Fix**:
1. Go to Supabase dashboard
2. SQL Editor → New query
3. Run migrations from `supabase/migrations/*.sql`

Or use Supabase CLI:
```bash
# If you have Supabase CLI installed
supabase db push
```

**Check tables exist**:
- Supabase dashboard → Table Editor
- Should see: sessions, analysis_results, insights, etc.

### Issue: File type rejected

**Symptoms**:
- Drag file into log mode
- Shows: "invalid file type"

**Cause**: File extension not recognized

**Fix**: Already fixed to accept:
- `.jsonl`
- `.json`
- `.log`
- `.txt`
- `.codex`
- `.claude`

If still rejected, check filename has correct extension.

## Environment Variables

**Required** (in `.env`):
```
VITE_SUPABASE_URL=https://0ec90b57d6e95fcbda19832f.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbG...
```

**Loaded by**: Netlify Dev automatically

**Check they're loaded**:
```bash
npm run dev

# Should see in output:
# ◈ Injected .env file env var: VITE_SUPABASE_URL
# ◈ Injected .env file env var: VITE_SUPABASE_ANON_KEY
```

**NOT required**:
- No GitHub tokens (handled by OAuth)
- No service role keys (using anon key)
- No custom API URLs

## Debugging Steps

### Step 1: Verify Netlify Dev is running

```bash
npm run dev

# Should see:
# ◈ Loaded function create-session
# ◈ Loaded function create-session-folder
# ◈ Server now ready on http://localhost:8888
```

**Ignore**: Edge Functions error - doesn't affect us

### Step 2: Test functions directly

```bash
# Run test script
./test-functions.sh

# Or test manually
curl http://localhost:8888/api/sessions \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"log_content":"test","encryption_enabled":false}'
```

### Step 3: Check browser console

Open http://localhost:8888, press F12, try to upload, check for:
```
[DEBUG] Posting to: http://localhost:8888/api/sessions
[DEBUG] Response status: 200
```

### Step 4: Check Supabase

- Dashboard → Table Editor → sessions
- After successful upload, should see new row

### Step 5: Check Network tab

- F12 → Network
- Try upload
- Click the request
- Check:
  - Request URL (should be localhost:8888)
  - Request Method (should be POST)
  - Status Code (200 = success, 404 = not found, 405 = wrong method)
  - Response body (shows error message if failed)

## The Three Modes

### Mode 1: Log Files (Blue)
- ✅ Uses: Netlify Functions
- ✅ Works: Immediately with `npm run dev`
- ✅ For: Quick log analysis
- ✅ Accepts: Paste or drag .jsonl/.json/.log files

### Mode 2: .codex Folder (Orange)
- ✅ Uses: Netlify Functions
- ✅ Works: Immediately with `npm run dev`
- ✅ For: Full folder with configs
- ✅ Accepts: Multiple files, extracts configs

### Mode 3: GitHub Only (Green)
- ⚠️ Uses: Python FastAPI backend
- ⚠️ Requires: `uvicorn backend.main:app --reload`
- ⚠️ Requires: GitHub OAuth configured in Supabase
- ✅ For: Analyzing GitHub repos directly
- ❌ Won't work: Without Python backend running

## Quick Fixes

**Problem**: Nothing works
**Solution**: Restart Netlify Dev
```bash
# Ctrl+C to stop
npm run dev
```

**Problem**: Functions loaded but 404
**Solution**: Check redirects in netlify.toml

**Problem**: GitHub mode fails
**Solution**: Start Python backend
```bash
uvicorn backend.main:app --reload --port 8000
```

**Problem**: Database errors
**Solution**: Check Supabase tables exist

**Problem**: CORS errors
**Solution**: Already fixed - restart Netlify Dev

**Problem**: Can't install Python backend
**Solution**: Use log upload modes only (don't need GitHub)

## Success Checklist

✅ Run `npm run dev`
✅ See "Loaded function create-session"
✅ See "Loaded function create-session-folder"
✅ See "Server now ready on http://localhost:8888"
✅ Open http://localhost:8888 in browser
✅ Click "Log Files" → Paste test content → Click "analyze"
✅ Should see "initializing..." → "connecting to backend..."
✅ Check browser console (F12) for `[DEBUG]` logs
✅ Should see HTTP 200 status

**Ignore**: Edge Functions error - doesn't matter!

## Still Stuck?

Run the test script and share output:
```bash
./test-functions.sh
```

This shows exactly what's working and what isn't.

Also check:
1. Browser console (F12) - shows frontend errors
2. Terminal running `npm run dev` - shows backend logs
3. Supabase dashboard - shows if data is being stored

The `[DEBUG]` logs will tell you exactly what URL is being called and what response you're getting!
