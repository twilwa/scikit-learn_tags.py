# Netlify Environment Variables Setup

## The Issue

Netlify Functions couldn't connect to Supabase because:
- Functions used `process.env.VITE_SUPABASE_URL`
- `VITE_` prefixed vars are for **build-time only** (Vite frontend)
- Netlify Functions run at **runtime** and need non-prefixed vars

## The Fix

All functions now check BOTH variable names:
```javascript
const supabaseUrl = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY;
```

This works for:
- ✅ Local dev (uses `VITE_` vars from `.env`)
- ✅ Netlify production (uses non-prefixed vars)

## Setting Up Netlify Environment Variables

### Step 1: Get Your Supabase Credentials

From your `.env` file, copy these values:
```
VITE_SUPABASE_URL=https://0ec90b57d6e95fcbda19832f.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Step 2: Add to Netlify Dashboard

1. Go to your Netlify site dashboard
2. Click: **Site configuration** → **Environment variables**
3. Click: **Add a variable** → **Add a single variable**

4. Add **TWO** variables:

**Variable 1:**
```
Key: SUPABASE_URL
Value: https://0ec90b57d6e95fcbda19832f.supabase.co
Scopes: ✅ Functions (REQUIRED), ✅ Builds, ✅ Post processing, ✅ Runtime
```

**Variable 2:**
```
Key: SUPABASE_ANON_KEY
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJib2x0IiwicmVmIjoiMGVjOTBiNTdkNmU5NWZjYmRhMTk4MzJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg4ODE1NzQsImV4cCI6MTc1ODg4MTU3NH0.9I8-U0x86Ak8t2DGaIk0HfvTSLsAyzdnz-Nw00mMkKw
Scopes: ✅ Functions (REQUIRED), ✅ Builds, ✅ Post processing, ✅ Runtime
```

**CRITICAL**: Make sure **"Functions"** scope is checked! Otherwise functions won't see them.

### Step 3: Optional - Keep VITE_ Versions Too

For consistency with local dev, you can ALSO add:
```
Key: VITE_SUPABASE_URL
Value: <same as above>
Scopes: ✅ Builds, ✅ Post processing
```

```
Key: VITE_SUPABASE_ANON_KEY
Value: <same as above>
Scopes: ✅ Builds, ✅ Post processing
```

But the functions will use the non-prefixed ones in production.

### Step 4: Trigger Redeploy

**IMPORTANT**: Environment variable changes require a new deploy!

1. Go to: **Deploys** tab
2. Click: **Trigger deploy** → **Deploy site**
3. Wait for deploy to finish (1-2 minutes)

## Verify It Worked

### Check Function Logs

1. After redeploying, try to upload a log
2. Go to: **Logs** tab in Netlify dashboard
3. Click on **Functions**
4. Look for `create-session` function logs

**Success looks like:**
```
Function execution complete
Duration: 500ms
Status: 200
```

**Failure looks like:**
```
Error: supabaseUrl is required
```

If you see the error, the env vars aren't set correctly.

### Test in Browser

1. Open your Netlify site
2. Press F12 (open console)
3. Click "Log Files" → Paste content → "analyze"
4. Check console:

**Success:**
```
[DEBUG] Posting to: /api/sessions
[DEBUG] Response status: 200
```

**Failure:**
```
[DEBUG] Response status: 500
[DEBUG] Error response: {"error":"supabaseUrl is required"}
```

## Common Issues

### Issue: "supabaseUrl is required"

**Cause**: Environment variables not set or not scoped to Functions

**Fix**:
1. Check Netlify dashboard → Environment variables
2. Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY` exist
3. Verify **"Functions"** scope is checked
4. Trigger redeploy

### Issue: Still not working after setting vars

**Cause**: Didn't redeploy after adding variables

**Fix**:
1. Deploys → Trigger deploy → Deploy site
2. Environment variables only apply to NEW deploys

### Issue: Variables showing in dashboard but functions can't see them

**Cause**: Wrong scope selected

**Fix**:
1. Edit each variable
2. Make sure **"Functions"** is checked
3. Save
4. Redeploy

### Issue: Local dev broken after changes

**Cause**: Code now checks `SUPABASE_URL` first, but `.env` has `VITE_SUPABASE_URL`

**Fix**: Either:

**Option A**: Add non-prefixed vars to `.env`:
```bash
# Add these to .env
SUPABASE_URL=https://0ec90b57d6e95fcbda19832f.supabase.co
SUPABASE_ANON_KEY=eyJhbG...

# Keep VITE_ ones too for frontend
VITE_SUPABASE_URL=https://0ec90b57d6e95fcbda19832f.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbG...
```

**Option B**: Nothing! Code falls back to `VITE_` vars if non-prefixed ones don't exist.

## Why Two Variable Names?

**For local dev (Netlify CLI)**:
- Reads from `.env` file
- Uses `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`
- These are injected: `◈ Injected .env file env var: VITE_SUPABASE_URL`

**For production (Netlify)**:
- Reads from dashboard Environment Variables
- Uses `SUPABASE_URL` and `SUPABASE_ANON_KEY`
- `VITE_` prefixed vars are for build-time (Vite bundler), not runtime (functions)

**The fallback handles both**:
```javascript
const supabaseUrl = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
//                  ↑ Production               ↑ Local dev
```

## Summary Checklist

✅ Get values from `.env` file
✅ Go to Netlify: Site configuration → Environment variables
✅ Add `SUPABASE_URL` with **Functions** scope
✅ Add `SUPABASE_ANON_KEY` with **Functions** scope
✅ Trigger redeploy
✅ Test log upload
✅ Check function logs if issues
✅ Verify in browser console (F12)

## Quick Reference

**Required Variables (Netlify Production)**:
```
SUPABASE_URL=https://0ec90b57d6e95fcbda19832f.supabase.co
SUPABASE_ANON_KEY=eyJhbG...
Scopes: Functions ✓
```

**Local Development (.env file)**:
```
VITE_SUPABASE_URL=https://0ec90b57d6e95fcbda19832f.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbG...
```

Code handles both automatically!

## Deploy Commands

```bash
# 1. Commit the function fixes
git add .
git commit -m "Fix env vars for Netlify Functions"
git push

# 2. Set env vars in Netlify dashboard (see above)

# 3. Trigger redeploy (in dashboard)

# 4. Test!
```

After this, log uploads should work on Netlify!
