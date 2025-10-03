# GitHub OAuth: Two Flows Explained

## The Problem

You need **TWO separate things**:

1. **User signs in** → Prove they are who they say they are
2. **Access GitHub API** → Read their repos, files, etc.

Supabase GitHub Auth only does #1. We need to set up #2.

## Solution: Enable Provider Token

Supabase **can** give us both! We just need to configure it correctly.

### How It Works

When a user signs in with GitHub via Supabase:
- Supabase gets a `provider_token` from GitHub
- This token has GitHub API scopes we request
- We can use it to call GitHub API
- Supabase stores it securely
- Automatic refresh handled by Supabase

### What You Need To Do

#### 1. Configure GitHub OAuth App with Correct Scopes

In your Supabase Dashboard:

1. Go to **Authentication** → **Providers** → **GitHub**
2. Look for **"Scopes"** field
3. Add these scopes:
   ```
   user repo read:user
   ```
4. Save

This tells Supabase: "When users sign in with GitHub, also request permission to access their repos"

#### 2. Enable Provider Token Storage

In Supabase Dashboard:

1. **Authentication** → **Providers** → **GitHub**
2. Look for option: **"Enable Provider Refresh Token"** or similar
3. Enable it
4. This ensures Supabase stores the `provider_token` we need

**Important**: The token is stored in `auth.users` metadata and accessible via:
```javascript
const { data: { user } } = await supabase.auth.getUser()
const githubToken = user.user_metadata.provider_token
```

### Alternative: GitHub App (More Complex)

If Supabase doesn't expose provider_token well, we can use a **GitHub App**:

**Pros**:
- More granular permissions
- Works for organizations
- Better rate limits
- Installation-based auth

**Cons**:
- More complex setup
- Need separate OAuth flow
- More code to maintain

**For now, let's use Supabase's provider_token** - it's simpler and sufficient for most use cases.

## Current Implementation

Our code already tries to use `provider_token`:

```javascript
// Frontend (netlify-frontend/js/tmux-app.js)
const { data: { session } } = await supabaseClient.auth.getSession();
const githubToken = session.provider_token; // ← We get this!
```

```python
# Backend (backend/routers/github_router_simple.py)
user_metadata = user_response.user.user_metadata or {}
provider_token = user_metadata.get('provider_token')  # ← We use this!
```

## Testing

After configuring scopes in Supabase:

1. Sign out completely
2. Sign in again with GitHub
3. During OAuth, GitHub will ask for **repo permissions**
4. Accept
5. Now `provider_token` will have API access

## Verification

Check if provider_token has correct scopes:

```javascript
// In browser console after signing in
const { data: { session } } = await supabaseClient.auth.getSession()
console.log(session.provider_token) // Should be a GitHub token
```

Test the token:
```bash
curl -H "Authorization: Bearer <provider_token>" \
  https://api.github.com/user/repos
```

Should return your repositories!

## What If Provider Token Doesn't Work?

Then we implement **GitHub App** flow:

### GitHub App Setup

1. Create GitHub App at: https://github.com/settings/apps/new
2. Set permissions:
   - Repository permissions:
     - Contents: Read
     - Metadata: Read
3. Copy App ID, Client ID, Client Secret
4. Generate Private Key
5. Store in `.env`:
   ```
   GITHUB_APP_ID=123456
   GITHUB_APP_CLIENT_ID=Iv1.abc123
   GITHUB_APP_CLIENT_SECRET=secret
   GITHUB_APP_PRIVATE_KEY_PATH=./github-app-key.pem
   ```

### GitHub App Flow

```
User clicks "Connect GitHub"
  ↓
Redirect to GitHub App installation
  ↓
User installs app for repos
  ↓
GitHub redirects back with installation_id
  ↓
We exchange for installation_access_token
  ↓
Use token for GitHub API calls
```

But **let's try provider_token first** - it's much simpler!

## Current Status

✅ Frontend requests provider_token
✅ Backend expects provider_token
❌ Need to configure scopes in Supabase
❌ Need to test with fresh login

## Next Steps

1. **You**: Add `user repo read:user` scopes in Supabase GitHub settings
2. **You**: Sign out and sign in again
3. **Test**: Check if `session.provider_token` exists
4. **Test**: Try calling `/api/github/repositories?sync=true`
5. If it works → Done!
6. If not → Implement GitHub App flow

## Quick Check

Run this in browser console after signing in:

```javascript
const { data: { session } } = await supabaseClient.auth.getSession()
console.log({
  hasSession: !!session,
  hasProviderToken: !!session?.provider_token,
  tokenLength: session?.provider_token?.length,
  userMetadata: session?.user?.user_metadata
})
```

Expected output:
```javascript
{
  hasSession: true,
  hasProviderToken: true,
  tokenLength: 40,  // GitHub tokens are ~40 chars
  userMetadata: {
    provider_token: "gho_xxxxxxxxxxxxx",
    user_name: "yourusername",
    ...
  }
}
```

If `hasProviderToken: false` → Need to configure scopes in Supabase!
