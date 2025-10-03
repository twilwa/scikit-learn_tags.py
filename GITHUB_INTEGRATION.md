# GitHub Integration - Analyze Repos Without Logs

## Overview

You can now connect your GitHub account and analyze repositories directly - no Claude logs needed!

This enables:
- **Code exploration** - Browse and analyze any repo
- **Architecture review** - Understand project structure
- **Language analysis** - See language breakdown
- **File-by-file exploration** - Deep dive into specific files
- **Build detection** - Check if repo builds successfully
- **Gamification** - Earn points for repo analysis

## Setup

### 1. Create GitHub OAuth App

1. Go to https://github.com/settings/developers
2. Click "New OAuth App"
3. Fill in:
   - **Application name**: Claude Code Analyzer
   - **Homepage URL**: `http://localhost:8000` (or your domain)
   - **Authorization callback URL**: `http://localhost:8000/api/github/auth/callback`
4. Click "Register application"
5. Copy your **Client ID** and **Client Secret**

### 2. Configure Environment

Add to your `.env` file:

```bash
GITHUB_CLIENT_ID=your_client_id_here
GITHUB_CLIENT_SECRET=your_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:8000/api/github/auth/callback
```

For production, update the redirect URI to your domain.

### 3. Start the Server

```bash
uvicorn backend.main:app --reload
```

## Usage Flow

### Connect GitHub

1. Visit the homepage
2. Click "Connect GitHub"
3. Authorize the app on GitHub
4. You'll be redirected back with connection confirmed

### Browse Repositories

```bash
GET /api/github/repositories?user_profile_id=<your_id>&sync=true
```

Returns all your repos with metadata:
- Stars, forks, issues
- Primary language
- Last commit info
- Repository size

### Start Analysis

```bash
POST /api/github/analyze
{
  "user_profile_id": "uuid",
  "repo_full_name": "username/repo",
  "session_type": "exploration",
  "analysis_focus": ["architecture", "dependencies", "tests"]
}
```

Session types:
- `exploration` - General code browsing
- `full_analysis` - Complete repo analysis
- `code_review` - Focus on code quality
- `architecture` - Structure and patterns
- `security_audit` - Security issues
- `performance` - Performance bottlenecks

### View Analysis Results

```bash
GET /api/github/analysis/<session_url>
```

Returns:
- Repository structure
- Language breakdown
- File organization
- Key metrics
- Interesting patterns

### Explore Specific Files

```bash
POST /api/github/explore/<session_url>
{
  "file_path": "src/main.py",
  "user_profile_id": "uuid"
}
```

Fetches and analyzes the file:
- Full content
- Lines of code
- Language detection
- Complexity score
- Dependencies/imports/exports

## Frontend Integration

### Connect Button

```html
<button onclick="window.location.href='/api/github/auth/login'">
  Connect GitHub
</button>
```

### Check Connection Status

```javascript
const response = await fetch(`/api/github/connection?user_profile_id=${userId}`);
const data = await response.json();

if (data.connected) {
  console.log(`Connected as: ${data.github_username}`);
}
```

### List Repositories

```javascript
const response = await fetch(
  `/api/github/repositories?user_profile_id=${userId}&sync=true`
);
const repos = await response.json();

repos.forEach(repo => {
  console.log(`${repo.repo_full_name} - ${repo.stars} stars`);
});
```

### Start Analysis Session

```javascript
const response = await fetch('/api/github/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_profile_id: userId,
    repo_full_name: 'octocat/Hello-World',
    session_type: 'exploration'
  })
});

const { session_url } = await response.json();
window.location.href = `/analysis.html?github_session=${session_url}`;
```

## What Gets Analyzed

### Repository Structure

- **Directory layout** - src/, lib/, tests/, docs/
- **Configuration files** - package.json, requirements.txt, etc.
- **Build files** - Makefile, Dockerfile, CI configs
- **Documentation** - README, docs/, wikis

### Code Metrics

- **Total files** by type
- **Lines of code** per language
- **Language breakdown** with percentages
- **File size distribution**
- **Complexity estimates**

### Patterns Detected

- **Framework usage** - React, Django, Express, etc.
- **Testing setup** - Jest, pytest, Go test
- **Build tools** - Webpack, Vite, Cargo
- **Package managers** - npm, pip, cargo, go mod
- **Common architectures** - MVC, microservices, monorepo

## Gamification Integration

### Points Awarded

**Repository Connection**: 10 points
- First time connecting GitHub

**Repository Analysis**: 25 points per repo
- Each unique repo analyzed
- Quality multiplier based on complexity

**File Exploration**: 5 points per file
- Deep dive into specific files
- Bonus for complex files

**Build Success Detection**: 100 points
- Successfully analyzed buildable repos
- Major multiplier if build passes

**Architecture Discovery**: 50 points
- Identify architecture patterns
- Document findings

### Quests

**GitHub Explorer** (50 points)
1. Connect GitHub account
2. Analyze 5 repositories
3. Explore 20+ files
4. Complete full analysis session

**Code Archaeologist** (100 points)
1. Analyze repos with 1000+ stars
2. Explore legacy code (5+ years old)
3. Document architecture patterns
4. Suggest refactoring

**Build Master** (150 points)
1. Analyze 10 repositories
2. Detect build configurations
3. Identify build issues
4. Achieve 5 successful builds

## Privacy & Security

### What's Stored

- GitHub username and user ID
- Repository metadata (public info)
- Access tokens (encrypted)
- Analysis results
- File exploration history

### What's NOT Stored

- Your GitHub password
- Private repo code (unless you analyze it)
- OAuth client secret
- Other users' data

### Token Security

- Tokens stored encrypted in database
- RLS policies prevent access by others
- Tokens used only for API calls
- Can disconnect anytime

### Scopes Requested

- `repo` - Access public and private repos
- `read:user` - Read user profile info

You can revoke access anytime at: https://github.com/settings/applications

## Disconnect

Remove GitHub connection:

```bash
DELETE /api/github/connection?user_profile_id=<your_id>
```

This:
- Deletes your OAuth tokens
- Removes cached repository data
- Preserves analysis history (anonymized)
- Doesn't affect GitHub (revoke separately)

## Use Cases

### 1. Quick Repo Overview

**Scenario**: Need to understand a new codebase fast

**Flow**:
1. Connect GitHub
2. Select the repo
3. Start "exploration" session
4. Review structure analysis
5. Explore key files
6. Get architecture summary

**Time**: 5-10 minutes

### 2. Pre-Interview Prep

**Scenario**: Interview requires understanding company's tech stack

**Flow**:
1. Find company's GitHub org
2. Analyze their public repos
3. Identify patterns and tools
4. Explore interesting files
5. Export insights for notes

**Time**: 30 minutes

### 3. Open Source Contributing

**Scenario**: Want to contribute but codebase is huge

**Flow**:
1. Analyze the repo structure
2. Find test files
3. Explore contribution guide
4. Identify good first issues
5. Understand architecture

**Time**: 15-20 minutes

### 4. Debugging Production Issues

**Scenario**: Need to understand legacy code causing bugs

**Flow**:
1. Analyze problematic repo
2. Explore files mentioned in errors
3. Trace dependency graphs
4. Find similar patterns
5. Suggest fixes

**Time**: 20-30 minutes

### 5. Architecture Review

**Scenario**: Reviewing architecture for new project

**Flow**:
1. Analyze similar successful projects
2. Compare structures
3. Identify best practices
4. Document patterns
5. Generate recommendations

**Time**: 1 hour

## Advanced Features

### Automatic Language Detection

Supports 20+ languages:
- JavaScript, TypeScript, Python, Go, Rust
- Java, C, C++, C#, Swift, Kotlin
- Ruby, PHP, Scala, Elixir, Haskell
- And more...

### Complexity Scoring

Files scored on:
- Lines of code
- Nesting depth
- Cyclomatic complexity
- Dependencies

### Pattern Recognition

Detects:
- MVC architecture
- Microservices
- Monorepos
- Design patterns
- Testing strategies
- CI/CD setup

### Build Detection

Identifies:
- npm/yarn/pnpm
- pip/poetry
- cargo
- go mod
- maven/gradle

Then checks if build would succeed.

## API Reference

### Auth Endpoints

```
GET  /api/github/auth/login
     → Redirects to GitHub OAuth

GET  /api/github/auth/callback?code=<code>
     → Handles OAuth callback
```

### Connection Management

```
GET    /api/github/connection?user_profile_id=<id>
       → Check connection status

DELETE /api/github/connection?user_profile_id=<id>
       → Disconnect GitHub
```

### Repository Operations

```
GET  /api/github/repositories?user_profile_id=<id>&sync=<bool>
     → List user's repos

POST /api/github/analyze
     → Start analysis session

GET  /api/github/analysis/<session_url>
     → Get analysis results

POST /api/github/explore/<session_url>
     → Explore specific file
```

## Troubleshooting

### "GitHub OAuth not configured"

**Fix**: Set `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in `.env`

### "Repository not found"

**Fix**: Sync repositories first with `?sync=true` parameter

### "Failed to fetch file content"

**Fix**:
- Check file path is correct
- Ensure file is text (not binary)
- Verify repo access permissions

### "Token expired"

**Fix**: Reconnect your GitHub account (tokens refresh automatically)

## Limitations

- **File size**: Max 1MB per file
- **Repo size**: Works best with < 1000 files
- **API rate limits**: 5000 requests/hour (GitHub)
- **Private repos**: Requires repo scope

For large repos, analysis may take longer.

## Future Enhancements

Coming soon:
- [ ] Commit history analysis
- [ ] PR review suggestions
- [ ] Issue detection
- [ ] Code smell identification
- [ ] Automated refactoring suggestions
- [ ] Team collaboration features
- [ ] Multi-repo analysis
- [ ] Dependency security scanning

---

**No logs needed!** Just connect GitHub and start exploring.
