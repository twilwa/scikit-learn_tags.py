# Deployment Instructions

## Quick Deploy

1. Push this repo to GitHub

2. Go to [Netlify](https://netlify.com) and click "Add new site" → "Import an existing project"

3. Connect your GitHub repo

4. Configure build settings:
   - Build command: `echo "No build needed"`
   - Publish directory: `netlify-frontend`
   - Functions directory: `netlify/functions`

5. Add environment variables in Netlify dashboard:
   - `VITE_SUPABASE_URL` - your Supabase project URL
   - `VITE_SUPABASE_ANON_KEY` - your Supabase anon key

6. Deploy!

## What You Get

- Static frontend with tmux aesthetic
- Serverless functions for backend API
- No WebSocket needed (polling mode)
- Fully integrated - no config needed on frontend

The frontend will automatically use the same domain for API calls.

## Local Development

```bash
npm install
netlify dev
```

This runs both the static site and serverless functions locally.

## Backend API Routes

All routes are serverless functions:
- `POST /api/sessions` - create session
- `GET /api/sessions/:id` - get session status
- `GET /api/sessions/:id/insights` - get insights
- `GET /api/sessions/:id/analysis` - get analysis results

No WebSocket support in serverless mode, but frontend uses polling (2s interval).
