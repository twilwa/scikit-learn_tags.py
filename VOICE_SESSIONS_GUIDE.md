## Voice Sessions - Collaborative AI Debugging

Real-time collaborative sessions where you and an AI assistant work together to analyze logs, review code, and debug repositories.

## Overview

Voice Sessions transform log analysis from a passive review into an active, collaborative debugging experience. Think of it as pair programming with an AI that can:

- Analyze your Claude Code logs in real-time
- Review repository structure and suggest improvements
- Execute Python code collaboratively
- Generate visualizations on the fly
- Learn from your Obsidian knowledge base
- Provide context-aware suggestions

## Session Modes

### 1. Text-Only Mode (Free)
- Web-based chat interface
- Python REPL access
- 2-hour session limit
- Great for async log review

### 2. Voice Browser Mode ($5/hour)
- Browser microphone input
- Real-time transcription
- Voice responses
- 1-hour session limit
- WebSocket streaming

### 3. Voice Discord Mode ($10/month)
- Discord voice channel integration
- Multi-user sessions
- Persistent history
- Unlimited sessions
- Bot joins your VC

## Session Types

### Log Analysis Session
**Purpose**: Deep dive into Claude Code session logs

Flow:
1. Upload your log file
2. AI automatically identifies patterns, errors, and inefficiencies
3. Collaborative discussion about what went wrong
4. AI suggests fixes and improvements
5. Test fixes in Python REPL
6. Generate visualizations of patterns

**Use cases**:
- Claude isn't doing what you want
- Session went off the rails
- Need to understand token usage
- Want to improve prompt effectiveness

### Repo Review Session
**Purpose**: Comprehensive repository analysis

Flow:
1. Connect your repository
2. AI analyzes structure, dependencies, and patterns
3. Discuss architecture decisions together
4. Identify technical debt
5. Plan refactoring strategies
6. Execute analysis scripts in REPL

**Use cases**:
- New codebase orientation
- Pre-deployment review
- Refactoring planning
- Performance optimization

### Collaborative Coding Session
**Purpose**: Build and debug together in real-time

Flow:
1. Share code context
2. Discuss implementation approaches
3. Write code in Python REPL
4. Generate graphs and visualizations
5. Test different algorithms
6. Iterate until solution works

**Use cases**:
- Debugging complex issues
- Algorithm development
- Data analysis
- ML model experimentation

### Debugging Session
**Purpose**: Targeted problem-solving

Flow:
1. Describe the bug
2. AI reviews relevant code
3. Collaborative hypothesis testing
4. Execute debug scripts
5. Verify fixes
6. Document solution

**Use cases**:
- Production incidents
- Intermittent bugs
- Performance issues
- Integration problems

## How to Start a Session

### Web Interface

1. **Upload your log or connect repo**:
```
POST /api/sessions
{
  "log_content": "...",
  "encryption_enabled": false
}
```

2. **Create voice session**:
```
POST /api/voice-sessions
{
  "session_type": "log_analysis",
  "mode": "voice_browser",
  "log_session_id": "uuid-of-log-session"
}
```

3. **Join session**:
Navigate to: `/voice-session.html?session=<session_url>`

4. **Click mic to talk** or type in chat

### Discord Bot

```
/start-session type:log_analysis mode:voice
```

Bot will:
1. Create a voice channel
2. Join the channel
3. Start listening
4. Respond in real-time

## During the Session

### Voice Controls
- **Push-to-talk**: Click and hold mic button
- **Always-on**: Toggle mic button to stay recording
- **Mute**: Stop recording to prevent audio processing

### Python REPL
Execute any Python code:
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load log data
df = pd.read_json(session_data['log_content'])

# Analyze patterns
df.groupby('tool_name').size().plot(kind='bar')
plt.show()
```

Results appear instantly with visualizations.

### Commands
- `!analyze` - Run full log analysis
- `!visualize <metric>` - Create visualization
- `!history` - Show REPL history
- `!export` - Export session transcript
- `!share` - Make session public
- `!end` - End session early

## Pricing & Limits

### Free Tier
- Text-only mode
- 2-hour sessions
- 5 sessions per day
- Basic Python REPL
- Public shared KB access

### Voice Browser ($5/session)
- 1-hour session
- Browser microphone
- Real-time transcription
- Full Python REPL
- Visualization support
- Private KB access

### Discord Bot ($10/month)
- Unlimited sessions
- Discord voice channel
- Multi-user support
- Persistent history
- Priority support
- Advanced visualizations

## Knowledge Base Integration

### Personal KB (Private)
Upload your Obsidian notes:
1. `/kb_upload` - Upload markdown files
2. Visibility: `private` (default)
3. AI searches your KB for context
4. Improves suggestions quality

### Shared KB (Opt-in)
Contribute to community knowledge:
1. Upload document
2. Set visibility: `shared`
3. Others can search (anonymously)
4. You get credit for helpfulness
5. Improves everyone's experience

### How Sharing Works
- Your identity is not exposed
- Content is searchable by all
- Quality scored by helpfulness votes
- High-quality content ranked higher
- You can remove anytime

### Feedback System
Rate shared KB content:
- 👍 Helpful - Improves quality score
- 👎 Not helpful - Lowers quality score
- ✏️ Suggest correction - Improves content
- 🏷️ Add tags - Better categorization

## Session Flow Example

**Scenario**: Claude kept adding unnecessary dependencies

1. **Upload log**:
```bash
curl -X POST /api/sessions \
  -H "Content-Type: application/json" \
  -d '{"log_content": "..."}'
```

2. **Start voice session**:
```javascript
const response = await fetch('/api/voice-sessions', {
  method: 'POST',
  body: JSON.stringify({
    session_type: 'log_analysis',
    mode: 'voice_browser',
    log_session_id: 'log-uuid'
  })
});
const { session_url } = await response.json();
```

3. **Join and discuss**:
```
You: "Claude kept adding React even though I said vanilla JS"
AI: "I can see that. Let me analyze the tool calls...
     Ah, it added React 3 times despite your instruction.
     This happened because [analysis]...
     Want to see the exact tokens where this occurred?"
```

4. **Analyze in REPL**:
```python
# AI executes:
tool_calls = parse_tool_calls(log_content)
react_adds = [t for t in tool_calls if 'react' in t['args']]
visualize_timeline(react_adds)
```

5. **Get recommendations**:
```
AI: "Based on this analysis, here's how to prevent this:
     1. Be more explicit in your instructions
     2. Use these specific phrases: [list]
     3. Add this to your .cursorrules file
     Would you like me to generate the config?"
```

6. **Export and share**:
```
You: "!export"
AI: "Session exported. Want to contribute this pattern
     to shared KB? It could help others with the same issue."
```

## Privacy & Security

### What's Stored
- Session transcripts (encrypted)
- REPL execution history
- Log analysis results
- Visualization data
- Time spent in session

### What's NOT Stored
- Raw audio files
- Payment information (handled by Stripe)
- Personal identifiers in shared KB
- API keys or secrets (auto-redacted)

### Data Retention
- Active sessions: Real-time only
- Session history: 30 days
- Shared KB contributions: Permanent (until removed)
- Payment records: Per Stripe policy

### Opt-Out
- Delete session: `/api/voice-sessions/{id}` DELETE
- Remove KB contribution: `/api/kb/documents/{id}` DELETE
- Export data: `/api/user/export` GET
- Delete account: `/api/user/delete` DELETE

## Technical Details

### WebSocket Protocol

**Client → Server**:
```json
{
  "type": "audio_chunk",
  "data": "<base64_audio>"
}
```

**Server → Client**:
```json
{
  "type": "transcription",
  "data": {
    "text": "What you said",
    "confidence": 0.95,
    "timestamp": "2025-10-03T10:00:00Z"
  }
}
```

### Python REPL Environment

Available packages:
- numpy, pandas - Data analysis
- matplotlib, seaborn - Visualization
- scikit-learn - ML basics
- requests - HTTP requests
- beautifulsoup4 - HTML parsing
- Custom session_utils - Session-specific helpers

Restrictions:
- No file system writes (except /tmp)
- No network calls to private IPs
- 10-second execution timeout
- 500MB memory limit

### Voice Processing Pipeline

1. Browser captures audio (WebRTC)
2. Compressed to 16kHz mono
3. Streamed via WebSocket
4. Deepgram transcription (if enabled)
5. Text processed by Claude
6. Response synthesized (if voice mode)
7. Streamed back to client

## Best Practices

### Getting the Most Value

1. **Prepare beforehand**:
   - Have logs ready
   - Know what questions to ask
   - Upload relevant KB docs

2. **Use voice efficiently**:
   - Speak clearly and concisely
   - Use push-to-talk to avoid noise
   - Pause between thoughts

3. **Leverage REPL**:
   - Test hypotheses immediately
   - Generate visualizations
   - Explore data interactively

4. **Take notes**:
   - Export session transcript
   - Save REPL outputs
   - Document solutions

5. **Contribute back**:
   - Share useful patterns
   - Rate KB content
   - Suggest improvements

### Common Pitfalls

❌ **Don't**:
- Run sessions without clear goal
- Forget to export results
- Share sensitive information
- Let sessions run idle (wasting time)

✅ **Do**:
- Set specific objectives
- Take breaks for long sessions
- Use private KB for secrets
- End sessions when done

## Troubleshooting

### Microphone not working
1. Check browser permissions
2. Try different browser (Chrome works best)
3. Test microphone in system settings
4. Refresh page and try again

### Session disconnected
1. Check internet connection
2. Rejoin with same session URL
3. History is preserved
4. Resume where you left off

### REPL execution failed
1. Check Python syntax
2. Verify package availability
3. Review error message
4. Ask AI for help debugging

### Poor transcription quality
1. Reduce background noise
2. Speak slower and clearer
3. Use push-to-talk mode
4. Check microphone quality

## API Reference

### Create Session
```
POST /api/voice-sessions
Body: {
  "session_type": "log_analysis" | "repo_review" | "collaborative_coding" | "debugging",
  "mode": "text_only" | "voice_browser" | "voice_discord",
  "repo_url": "https://github.com/...",  // optional
  "log_session_id": "uuid"  // optional
}
Response: {
  "session_url": "uuid",
  "mode": "voice_browser",
  "duration_minutes": 60,
  "price_cents": 500,
  "status": "waiting"
}
```

### Execute Code
```
POST /api/voice-sessions/{session_url}/execute
Body: { "code": "print('hello')" }
Response: {
  "output": "hello",
  "output_type": "text",
  "execution_time_ms": 12,
  "error_message": null
}
```

### Get History
```
GET /api/voice-sessions/{session_url}/history
Response: [
  {
    "code": "print('hello')",
    "output": "hello",
    "created_at": "2025-10-03T10:00:00Z"
  }
]
```

## Future Features

Coming soon:
- [ ] Screen sharing for code review
- [ ] Multi-user collaborative sessions
- [ ] Integration with GitHub Actions
- [ ] LLM model selection (Claude, GPT-4, etc.)
- [ ] Custom voice training
- [ ] Whiteboard for architecture diagrams
- [ ] Recording and playback
- [ ] Session templates

---

**Ready to start?** Create your first session:
```bash
curl -X POST https://your-app.com/api/voice-sessions \
  -H "Content-Type: application/json" \
  -d '{"session_type":"log_analysis","mode":"text_only"}'
```
