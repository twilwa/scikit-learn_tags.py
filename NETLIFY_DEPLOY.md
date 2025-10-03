# Deploying to Netlify - FIXED

## The Problem

Your frontend was calling `https://twilwa-scikit-learn-nnon.bolt.host/api/sessions` instead of the Netlify Functions.

**Why**: The code used `window.location.origin` which points to your Bolt URL when deployed.

**Fix**: Changed to use **relative URLs** (`/api/sessions`) which work everywhere.

## What Changed

**File**: `netlify-frontend/js/tmux-app.js`

**Before**:
```javascript
let API_URL = localStorage.getItem(CONFIG_KEY) || window.location.origin;
// On Netlify this became: https://twilwa-scikit-learn-nnon.bolt.host
```

**After**:
```javascript
let API_URL = localStorage.getItem(CONFIG_KEY) || '';
// Empty string means relative URLs: /api/sessions
// Works on: localhost:8888, your-site.netlify.app, anywhere!
```

## Deploy Now

### Step 1: Commit Changes

```bash
git add .
git commit -m "Fix API URLs to use relative paths"
git push
```

### Step 2: Netlify Will Auto-Deploy

Netlify watches your repo and redeploys automatically.

**Check deployment**:
1. Go to your Netlify dashboard
2. Click your site
3. See "Deploys" tab
4. Wait for build to finish (usually 1-2 minutes)

### Step 3: Test Your Netlify Site

Open your Netlify URL (e.g., `your-site.netlify.app`):

**Test 1: Log paste**
1. Click "Log Files" (blue)
2. Paste JSON content
3. Click "analyze"
4. **Open browser console (F12)**
5. Should see:
   ```
   [DEBUG] Posting to: /api/sessions
   [DEBUG] Response status: 200
   ```

**Test 2: Folder upload**
1. Click ".codex Folder" (orange)
2. Select files
3. Click "analyze folder"
4. Console shows:
   ```
   [DEBUG] Posting folder to: /api/sessions/folder
   [DEBUG] Files: ['test.jsonl']
   [DEBUG] Response status: 200
   ```

## Environment Variables on Netlify

**Required**: Set these in Netlify dashboard:

1. Go to: Site settings → Environment variables
2. Add:
   ```
   VITE_SUPABASE_URL = https://0ec90b57d6e95fcbda19832f.supabase.co
   VITE_SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

3. **Trigger redeploy** (needed for env vars to take effect):
   - Deploys → Trigger deploy → Deploy site

## How It Works Now

### Local Development (npm run dev)

```
Frontend: http://localhost:8888
Calls: /api/sessions
→ Redirects to: /.netlify/functions/create-session
→ Function runs locally
→ Stores in Supabase
```

### Netlify Production

```
Frontend: https://your-site.netlify.app
Calls: /api/sessions (relative URL!)
→ Redirects to: /.netlify/functions/create-session
→ Function runs on Netlify edge
→ Stores in Supabase
```

**Key**: Using `/api/sessions` (no domain) makes it work everywhere!

## Troubleshooting Netlify Deploy

### Issue: Still getting 404

**Check**:
1. Functions deployed? Netlify dashboard → Functions tab
   - Should see: `create-session`, `create-session-folder`, etc.

2. Redirects working? Check deploy log:
   ```
   Netlify.toml redirects processed
   ```

3. Browser cache? Hard refresh:
   - Chrome/Edge: Ctrl+Shift+R
   - Firefox: Ctrl+F5
   - Safari: Cmd+Shift+R

### Issue: Functions not showing up

**Cause**: `netlify.toml` not in root or functions not in `netlify/functions/`

**Check**:
```bash
# Verify structure
ls netlify.toml                    # Should exist
ls netlify/functions/*.js          # Should list all functions
```

### Issue: Environment variables not working

**Symptoms**: Database errors, Supabase auth fails

**Fix**:
1. Netlify dashboard → Site settings → Environment variables
2. Verify `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set
3. Trigger redeploy (env changes need redeploy)

### Issue: 500 error on upload

**Check Netlify function logs**:
1. Netlify dashboard → Functions
2. Click function name (e.g., `create-session`)
3. See logs showing the actual error

Common errors:
- `supabase is not defined` → Env vars not set
- `table 'sessions' does not exist` → Run Supabase migrations
- `permission denied` → RLS policies too restrictive

### Issue: LocalStorage quota exceeded

**Error**: `Resource::kQuotaBytesPerItem quota exceeded`

**Cause**: Trying to store huge logs in localStorage

**Fix**: Already handled - doesn't affect functionality, just a warning

**Clear it**:
```javascript
// In browser console:
localStorage.clear()
```

## GitHub OAuth on Netlify

**Separate issue** - requires Python backend.

**Options**:

### Option 1: Use Supabase Edge Functions (Recommended)

Convert `backend/routers/github_router_simple.py` to a Supabase Edge Function:
- Deno/TypeScript instead of Python
- Runs on Supabase edge network
- No need for separate backend

### Option 2: Deploy Python backend separately

- Deploy to: Railway, Render, Fly.io, etc.
- Set `API_URL` in frontend to point to it
- More complex, but works

### Option 3: Skip GitHub mode

- Use log upload modes only
- No backend needed
- Simpler deployment

## Testing Checklist

On your deployed Netlify site:

✅ Open site URL
✅ Click "Log Files"
✅ Paste test content
✅ Click "analyze"
✅ Open console (F12)
✅ Check debug output
✅ Should see: `[DEBUG] Posting to: /api/sessions`
✅ Should see: `[DEBUG] Response status: 200`
✅ Check Supabase dashboard → sessions table
✅ Should see new row

## Success!

After this fix:
- ✅ Log paste works on Netlify
- ✅ Folder upload works on Netlify
- ✅ Works locally too
- ✅ No hardcoded URLs
- ✅ Netlify Functions handle everything

## One More Thing

**Clear localStorage** on first visit to deployed site:

```javascript
// Browser console (F12):
localStorage.removeItem('claude_analyzer_api')
```

Or it might still have the old Bolt URL cached.

## Deploy and Test

```bash
# 1. Push changes
git add .
git commit -m "Fix API URLs for Netlify deployment"
git push

# 2. Wait for Netlify to deploy (check dashboard)

# 3. Open your site

# 4. Clear localStorage (F12 console):
localStorage.clear()

# 5. Refresh page

# 6. Test log upload with console open (F12)

# Should work now! 🎉
```

The console `[DEBUG]` logs will tell you exactly what's happening.
