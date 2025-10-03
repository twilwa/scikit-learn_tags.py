# Claude Log Analyzer - Static Frontend

tmux-style static frontend deployable to Netlify.

## Deploy to Netlify

1. Push this repo to GitHub
2. Connect to Netlify
3. Set build directory to `netlify-frontend`
4. Deploy

Or use Netlify CLI:
```bash
cd netlify-frontend
netlify deploy --prod
```

## Configuration

On first visit, you'll be prompted to enter your backend API URL.

The backend should be running separately (e.g., on Railway, Fly.io, or your own server).

## Local Development

Just open `index.html` in a browser or use:
```bash
python3 -m http.server 8080
```

## Features

- tmux-style pane splitting
- Real-time WebSocket updates
- Terminal aesthetic
- Keyboard shortcuts
- No build step required
- Pure HTML/CSS/JS

## Keyboard Shortcuts

- `Enter` - start analysis
- `Ctrl+Enter` - submit from textarea
