# Fix Netlify Environment Variables for Functions

## Problem

You have:
- ✅ `VITE_SUPABASE_URL`
- ✅ `VITE_SUPABASE_ANON_KEY`

But Netlify Functions need the **non-VITE** versions:
- ❌ `SUPABASE_URL` (missing)
- ❌ `SUPABASE_ANON_KEY` (missing)

## Why Both?

### VITE_ Prefix = Frontend Only
- `VITE_SUPABASE_URL` - Used by Vite frontend build
- `VITE_SUPABASE_ANON_KEY` - Used by Vite frontend build
- **NOT available** to Netlify Functions

### No Prefix = Functions
- `SUPABASE_URL` - Used by Netlify serverless functions
- `SUPABASE_ANON_KEY` - Used by Netlify serverless functions
- Available at runtime in Node.js environment

## Fix Instructions

### Step 1: Add Missing Variables

In Netlify Dashboard:
1. Go to: **Site configuration** → **Environment variables**
2. Click **Add a variable**
3. Add `SUPABASE_URL`:
   - Key: `SUPABASE_URL`
   - Value: (same value as `VITE_SUPABASE_URL`)
   - Scopes: Check **Functions** ✅
   - Deploy contexts: All
4. Click **Add a variable** again
5. Add `SUPABASE_ANON_KEY`:
   - Key: `SUPABASE_ANON_KEY`
   - Value: (same value as `VITE_SUPABASE_ANON_KEY`)
   - Scopes: Check **Functions** ✅
   - Deploy contexts: All

### Step 2: Verify Scopes

Make sure you have all 4 variables with correct scopes:

| Variable | Scopes | Deploy Contexts |
|----------|--------|-----------------|
| `VITE_SUPABASE_URL` | Builds, Functions | All |
| `VITE_SUPABASE_ANON_KEY` | Builds, Functions | All |
| `SUPABASE_URL` | **Functions** ✅ | All |
| `SUPABASE_ANON_KEY` | **Functions** ✅ | All |

### Step 3: Redeploy

Environment variables only apply to **new deploys**:

1. Go to: **Deploys**
2. Click: **Trigger deploy** → **Deploy site**
3. Wait 1-2 minutes for build
4. Test functions

## How to Find Your Values

If you don't remember your Supabase URL/key:

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to: **Settings** → **API**
4. Copy:
   - **Project URL** → use for both `*_SUPABASE_URL` vars
   - **anon public** key → use for both `*_ANON_KEY` vars

## Why It Matters

### Before Fix:
```javascript
// In Netlify Function:
const supabaseUrl = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
//                   ❌ undefined              ❌ undefined (VITE_ not available)

const supabase = createClient(undefined, undefined);
// 💥 500 error: Cannot read properties of undefined
```

### After Fix:
```javascript
// In Netlify Function:
const supabaseUrl = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
//                   ✅ "https://abc.supabase.co"

const supabase = createClient(supabaseUrl, supabaseKey);
// ✅ Works! Functions can query database
```

## Testing

After adding variables and redeploying:

1. **Open browser console** on your site
2. **Paste log content** and click analyze
3. **Check console** - should see:
   ```
   [DEBUG] Posting to: /api/sessions
   [DEBUG] Response status: 200
   ```
   (NO 500 errors on insights/analysis endpoints)

4. **Check Netlify function logs**:
   - Go to: Deploys → Select latest → Functions
   - Should **NOT** see: "Missing Supabase credentials"
   - Should see: Successful database queries

## Common Mistakes

### ❌ Wrong Scope
If you only check "Builds" scope:
- Frontend can use it (via Vite)
- Functions **cannot** use it (not in runtime environment)

### ❌ Didn't Redeploy
Old deploys don't get new environment variables.
Must trigger a new deploy after adding vars.

### ❌ Typo in Variable Name
Must be exact:
- ✅ `SUPABASE_URL`
- ❌ `SUPABASE-URL` (dash instead of underscore)
- ❌ `supabase_url` (lowercase)

## Quick Copy-Paste

For your convenience, here's what you need:

```bash
# Add these in Netlify UI:

SUPABASE_URL=<same as VITE_SUPABASE_URL>
SUPABASE_ANON_KEY=<same as VITE_SUPABASE_ANON_KEY>

# Both with Functions scope checked ✅
```

## Summary

1. Add `SUPABASE_URL` with Functions scope
2. Add `SUPABASE_ANON_KEY` with Functions scope
3. Trigger new deploy
4. Test - no more 500 errors!

The `VITE_` prefix is a Vite convention that only works during build time, not at runtime in serverless functions.
