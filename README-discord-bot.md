# Claude Assistant Discord Bot

A Discord bot that provides intelligent command suggestions using ghost-text/tab-completion patterns inspired by Carapace. The bot learns from your command history and suggests what you might want to run next.

## Features

### 🤖 Smart Command Suggestions
- **Pattern Recognition**: Learns common command sequences from your history
- **Frequency Analysis**: Suggests frequently used commands based on context
- **Knowledge Base Integration**: Extracts commands from uploaded documentation
- **Workflow Completion**: Understands common development workflows (git, npm, etc.)

### 📊 Command Tracking
- Tracks all commands with context and metadata
- Analyzes command patterns and sequences
- Provides detailed usage statistics
- Learning system that improves over time

### 📚 Knowledge Base
- Upload Markdown, code files, and documentation
- Semantic search across your knowledge base
- Command extraction from code blocks
- Contextual suggestions based on KB content

### ⚙️ Customizable Settings
- Enable/disable suggestions per user
- Adjust confidence thresholds
- Choose suggestion display style (inline, buttons, disabled)
- Per-server configuration

## Installation

### Prerequisites
- Python 3.8+
- Discord Bot Token
- Supabase database (already configured)

### Setup Steps

1. **Install dependencies**:
   ```bash
   pip install -r requirements-discord.txt
   ```

2. **Configure environment variables**:
   Add your Discord bot token to `.env`:
   ```bash
   DISCORD_BOT_TOKEN=your_bot_token_here
   VITE_SUPABASE_URL=already_set
   VITE_SUPABASE_ANON_KEY=already_set
   ```

3. **Create Discord Application**:
   - Go to https://discord.com/developers/applications
   - Create a new application
   - Go to "Bot" section and create a bot
   - Copy the bot token
   - Enable "Message Content Intent" under Privileged Gateway Intents
   - Enable "Server Members Intent" under Privileged Gateway Intents

4. **Invite bot to your server**:
   - Go to OAuth2 > URL Generator
   - Select scopes: `bot`, `applications.commands`
   - Select bot permissions:
     - Read Messages/View Channels
     - Send Messages
     - Send Messages in Threads
     - Embed Links
     - Attach Files
     - Read Message History
     - Add Reactions
   - Copy the generated URL and open it in your browser

5. **Run the bot**:
   ```bash
   python discord_bot/main.py
   ```

## Usage

### Slash Commands

#### Suggestion Commands
- `/suggest` - Manually request command suggestions
- `/stats` - View your command usage statistics
- `/history [limit]` - View your recent command history
- `/clear-history` - Clear all your command history

#### Settings Commands
- `/settings` - View current settings
- `/toggle <enabled>` - Enable/disable suggestions
- `/confidence <threshold>` - Set minimum confidence (0.0-1.0)
- `/style <inline|buttons|disabled>` - Set suggestion display style
- `/reset` - Reset all settings to defaults

#### Knowledge Base Commands
- `/kb-upload <file>` - Upload a document to your KB
- `/kb-search <query>` - Search your knowledge base
- `/kb-list` - List all documents in your KB
- `/kb-delete <filename>` - Delete a document from your KB

### Automatic Suggestions

The bot automatically analyzes every message you send and provides suggestions when:
- High confidence suggestion is available (default: 60%)
- You have sufficient command history
- Suggestions are enabled in your settings

### Suggestion Sources

1. **Pattern-based**: Commands that typically follow your recent sequence
2. **Frequency-based**: Your most commonly used commands in similar contexts
3. **Knowledge Base**: Commands extracted from your uploaded documentation
4. **Workflow**: Common development workflow patterns (git, npm, python, etc.)

## Configuration

### User Preferences

Default settings:
```json
{
  "enabled": true,
  "aggressiveness": 0.7,
  "min_confidence": 0.6,
  "suggestion_style": "inline"
}
```

- **enabled**: Toggle suggestions on/off
- **aggressiveness**: How often to show suggestions (0.0-1.0)
- **min_confidence**: Minimum confidence threshold (0.0-1.0)
- **suggestion_style**: Display format (`inline`, `buttons`, `disabled`)

### Server Settings

Server administrators can configure:
- Enabled/disabled channels for bot activity
- Bot prefix (default: `!`)
- Feature toggles (suggestions, KB search, voice)

## Database Schema

The bot uses the following Supabase tables:
- `discord_users` - User profiles and preferences
- `discord_servers` - Server configurations
- `command_history` - Complete command tracking
- `command_patterns` - Learned command sequences
- `command_suggestions` - Suggestion history and feedback
- `kb_documents` - Knowledge base documents
- `kb_chunks` - Searchable document chunks

## Privacy & Data

- All data is stored per-user in Supabase
- Commands are only visible to the user who issued them
- Knowledge base is private to each user
- Use `/clear-history` to delete all your data

## Future Enhancements

### Voice Integration (Coming Soon)
- Deepgram speech-to-text integration
- Real-time voice command recognition
- Text-to-speech responses
- Multi-user voice channel support

### Advanced Features
- Command chaining suggestions
- Natural language to shell command translation
- Collaborative pattern sharing (opt-in)
- Integration with external APIs
- Custom command aliases
- Scheduled command suggestions

## Troubleshooting

### Bot not responding
- Check bot has necessary permissions in the server
- Verify bot token is correct in `.env`
- Check "Message Content Intent" is enabled

### Suggestions not appearing
- Ensure suggestions are enabled: `/toggle true`
- Check confidence threshold: `/confidence 0.5`
- Verify you have command history: `/history`

### Database connection errors
- Verify Supabase credentials in `.env`
- Check network connectivity
- Ensure RLS policies are configured correctly

## Architecture

```
discord_bot/
├── bot.py                  # Main bot class and message handler
├── database.py             # Supabase database operations
├── command_tracker.py      # Command history and pattern tracking
├── suggestion_engine.py    # Suggestion generation logic
├── main.py                 # Entry point
└── cogs/
    ├── suggestions.py      # Suggestion-related commands
    ├── settings.py         # User settings commands
    └── kb_management.py    # Knowledge base commands
```

## Contributing

Feel free to extend the bot with:
- Additional command classifiers
- New suggestion algorithms
- Integration with other services
- Voice capabilities with Deepgram/Pipecat

## License

See LICENSE file in the repository root.
