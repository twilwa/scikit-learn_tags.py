# Supabase GitHub OAuth Configuration

## The Issue

Supabase GitHub provider gives us **user authentication**, but we also need **GitHub API access** to read repositories.

These are two separate OAuth flows that happen to use the same provider.

## Solution Overview

Configure Supabase to request **additional scopes** when users sign in, so we get a `provider_token` that works with GitHub API.

## Step-by-Step Configuration

### 1. Create GitHub OAuth App

1. Go to https://github.com/settings/developers
2. Click **"New OAuth App"**
3. Fill in:
   ```
   Application name: Claude Code Analyzer
   Homepage URL: https://your-domain.com
   Authorization callback URL: https://your-project-id.supabase.co/auth/v1/callback
   ```
4. Click **"Register application"**
5. Note your **Client ID**
6. Click **"Generate a new client secret"**
7. Copy the **Client Secret** (you'll only see it once!)

### 2. Configure Supabase GitHub Provider

1. Go to your Supabase Dashboard
2. Navigate to **Authentication** → **Providers**
3. Find **GitHub** in the list
4. Click to configure
5. Fill in:
   ```
   ✅ Enable GitHub provider

   Client ID: <paste from GitHub OAuth app>
   Client Secret: <paste from GitHub OAuth app>

   Additional Scopes: user repo read:user
   ```
6. **Important**: The "Additional Scopes" field is critical!
   - `user` - Basic user info
   - `repo` - Access to repositories
   - `read:user` - Read user profile
7. Save

### 3. Verify Configuration

After saving, check:
- ✅ GitHub provider is enabled
- ✅ Client ID matches your GitHub OAuth app
- ✅ Scopes include `repo`
- ✅ Callback URL in GitHub app matches Supabase

### 4. Test the Setup

1. **Sign Out**: If you're currently signed in, sign out completely
2. **Clear Session**: Clear browser cache/cookies for your domain
3. **Sign In**: Use the "Connect GitHub" button
4. **Check Permissions**: GitHub should ask for:
   - Read your email
   - **Access your repositories** ← This is key!
5. **Click Authorize**

### 5. Verify Provider Token

After signing in, run this in browser console:

```javascript
const { data: { session } } = await supabaseClient.auth.getSession()
console.log({
    hasSession: !!session,
    hasProviderToken: !!session?.provider_token,
    tokenLength: session?.provider_token?.length,
    userName: session?.user?.user_metadata?.user_name
})
```

Expected output:
```javascript
{
    hasSession: true,
    hasProviderToken: true,  // ← Must be true!
    tokenLength: 40,         // ← GitHub tokens are ~40 chars
    userName: "yourusername"
}
```

### 6. Test GitHub API Access

Click the **"debug"** button in the UI, or visit:
```
http://localhost:8000/api/github/auth/debug
```

Should return:
```json
{
    "user_id": "uuid",
    "email": "you@example.com",
    "provider": "github",
    "has_provider_token": true,
    "provider_token_length": 40
}
```

### 7. Test Repository Access

Click **"view repositories"** - it should:
1. Fetch your repos from GitHub API
2. Display them in the UI
3. Allow you to analyze any repo

## Troubleshooting

### "No GitHub API access" Warning

**Cause**: Signed in before configuring scopes

**Fix**:
1. Click "sign out"
2. Verify scopes in Supabase dashboard
3. Sign in again
4. GitHub will ask for repo access

### `provider_token` is `undefined`

**Possible causes**:

1. **Scopes not configured**
   - Go to Supabase → Authentication → Providers → GitHub
   - Add `user repo read:user` to Additional Scopes
   - Save

2. **Old session**
   - Sign out completely
   - Clear browser cookies
   - Sign in again

3. **Supabase doesn't support provider_token** (rare)
   - Check Supabase docs for your version
   - May need to implement GitHub App instead

### GitHub doesn't ask for repo permissions

**Fix**: Check your GitHub OAuth app settings:
1. Go to https://github.com/settings/developers
2. Find your OAuth app
3. Check the scopes it requests
4. Should include `repo`

If not, update scopes in Supabase and try again.

### "Failed to fetch repos: 401"

**Cause**: Token doesn't have correct permissions

**Fix**:
1. Go to https://github.com/settings/applications
2. Find your OAuth app in "Authorized OAuth Apps"
3. Click "Revoke"
4. Sign in again to grant fresh permissions

## Alternative: GitHub App (If Provider Token Doesn't Work)

If Supabase doesn't expose `provider_token` properly, implement GitHub App:

### Pros of GitHub App
- ✅ More granular permissions
- ✅ Works for organizations
- ✅ Better rate limits
- ✅ Installation-based, not user-based

### Cons of GitHub App
- ❌ More complex to set up
- ❌ Separate OAuth flow
- ❌ Need webhook endpoints
- ❌ More code to maintain

**Recommendation**: Try provider_token first. Only use GitHub App if provider_token doesn't work.

## What Our Code Expects

### Frontend
```javascript
const { data: { session } } = await supabaseClient.auth.getSession()
const githubToken = session.provider_token // ← We use this!
```

### Backend
```python
user_response = supabase.auth.get_user(auth_header)
provider_token = user_response.user.user_metadata.get('provider_token')
# Use provider_token for GitHub API calls
```

## Verification Checklist

Before asking for help, verify:

- [ ] GitHub OAuth app created
- [ ] Client ID and Secret in Supabase
- [ ] Scopes include `repo` in Supabase
- [ ] Signed out and signed in again after config
- [ ] GitHub asked for repo permissions during sign in
- [ ] `session.provider_token` exists in browser console
- [ ] Debug endpoint shows `has_provider_token: true`
- [ ] Can fetch repositories

If all checkmarks pass → Everything is working!

If any fail → That's where the issue is.

## Current Configuration

Check your current Supabase settings:

1. Dashboard → Authentication → Providers → GitHub
2. Look for:
   ```
   Additional Scopes: _______
   ```
3. Should see: `user repo read:user`
4. If empty or missing `repo` → Add it and save

## Debug Commands

**Check Supabase session**:
```javascript
supabaseClient.auth.getSession().then(({data}) => console.log(data))
```

**Test backend auth**:
```bash
# Get your access_token from browser console first
curl http://localhost:8000/api/github/auth/debug \
  -H "Authorization: Bearer <access_token>"
```

**Test GitHub API directly**:
```bash
# Use provider_token from session
curl https://api.github.com/user/repos \
  -H "Authorization: Bearer <provider_token>"
```

All three should work if configured correctly!

## Success Indicators

✅ **Sign in flow**:
- GitHub asks: "Allow access to your repositories?"
- You click "Authorize"
- Redirected back to app
- See: "✓ GitHub API access granted"

✅ **UI shows**:
- Green checkmark
- Your username
- "view repositories" button
- "debug" button

✅ **Debug output**:
- `has_provider_token: true`
- `provider_token_length: 40`

✅ **Repos load**:
- List of your repositories
- Correct language/stars/forks
- "analyze" button for each

## Next Steps After Configuration

1. ✅ Configure scopes in Supabase
2. ✅ Sign out and sign in again
3. ✅ Click "debug" to verify
4. ✅ Click "view repositories"
5. ✅ Click "analyze" on a repo
6. ✅ Explore files interactively

**No logs to upload - just connect and analyze!**
