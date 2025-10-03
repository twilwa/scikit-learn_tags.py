# UI Changes - Three Mode Selection

## What Changed

The frontend now clearly shows **three distinct analysis modes** at startup.

## Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE LOG ANALYZER                  │
│                                                               │
│                  > select analysis mode:                      │
│                                                               │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│   │      🐙      │  │      📁      │  │      📊      │     │
│   │  GitHub Only │  │ .codex Folder│  │  Log Files   │     │
│   │ NO LOGS NEEDED│ │ with configs │  │quick analysis│     │
│   └──────────────┘  └──────────────┘  └──────────────┘     │
│        ▲                                                      │
│        │                                                      │
│    Selected (green border)                                   │
│                                                               │
│   [GitHub connection UI shown here]                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Mode Buttons

### GitHub Only (Default, Green Highlight)
```
┌──────────────────────┐
│         🐙           │
│    GitHub Only       │
│  NO LOGS NEEDED ✓    │  ← Green text
└──────────────────────┘
   Green border (rgba(76, 175, 80, 0.2))
```

### .codex Folder (Orange when selected)
```
┌──────────────────────┐
│         📁           │
│   .codex Folder      │
│   with configs       │
└──────────────────────┘
   Orange border when active
```

### Log Files (Blue when selected)
```
┌──────────────────────┐
│         📊           │
│     Log Files        │
│   quick analysis     │
└──────────────────────┘
   Blue border when active
```

## Mode-Specific Content

### GitHub Mode (Shows on select)
```
> connecting to github...

[connect github [enter]]

Status updates appear here after connection
```

### Folder Mode (Shows on select)
```
> drop entire .codex or .claude folder (multiple files)

[Choose Files] (supports directory upload)

includes: logs + config.json + mcp.json + subagents.json

[analyze folder [enter]]
```

### Log Mode (Shows on select)
```
> drop .jsonl/.json/.log files or paste content below

┌─────────────────────────────────┐
│ paste log content...            │
│                                 │
│                                 │
└─────────────────────────────────┘

☐ run in TEE?

[analyze [enter]]
```

## Keyboard Shortcuts (Updated)

```
keyboard shortcuts:
  ctrl+b 1  - github mode
  ctrl+b 2  - folder mode
  ctrl+b 3  - log mode
  enter     - start analysis
```

## Color Scheme

**GitHub Mode (Highlighted)**:
- Background: `rgba(76, 175, 80, 0.2)` (light green)
- Border: `#4CAF50` (green)
- Text: `#4CAF50` (green) for "NO LOGS NEEDED"

**Folder Mode (When selected)**:
- Background: `rgba(255, 152, 0, 0.2)` (light orange)
- Border: `#FF9800` (orange)

**Log Mode (When selected)**:
- Background: `rgba(33, 150, 243, 0.2)` (light blue)
- Border: `#2196F3` (blue)

**Inactive Buttons**:
- Background: `rgba(255, 255, 255, 0.05)` (dark gray)
- Border: `#666` (gray)

## Interaction Flow

1. **Page loads** → GitHub mode selected by default (green)
2. **Click folder button** → Folder mode activates (orange)
3. **Click log button** → Log mode activates (blue)
4. **Only one mode visible at a time** → Clear user intent

## Benefits

### Before (Issues)
- ❌ Only saw one upload field
- ❌ Not clear GitHub mode existed
- ❌ Confusing to switch between modes
- ❌ Users had to read docs to know options

### After (Solutions)
- ✅ Three modes visible immediately
- ✅ GitHub mode highlighted as "NO LOGS NEEDED"
- ✅ Click to switch modes
- ✅ Self-explanatory interface

## File Upload Details

### Folder Mode
```html
<input type="file"
       multiple
       webkitdirectory
       directory>
```
Allows users to:
- Select entire .codex folder
- All files uploaded at once
- Maintains structure

### Results Display
```
> folder structure detected: 12 logs, 1547 entries
> configs found: config.json, mcp.json, subagents.json
> mcp: 5 servers configured
> subagents: 3 configured
```

## Mobile Responsive

Buttons stack vertically on small screens:
```
┌──────────┐
│    🐙    │
│  GitHub  │
└──────────┘

┌──────────┐
│    📁    │
│  Folder  │
└──────────┘

┌──────────┐
│    📊    │
│   Logs   │
└──────────┘
```

## Status Line Updates

Bottom status bar shows:
```
┌──────────────────────────────────────────────────┐
│ ● github mode active    │    api: integrated     │
└──────────────────────────────────────────────────┘
```

Changes based on selected mode.

## Error Handling

### GitHub Mode
- Not configured → "Set GITHUB_CLIENT_ID in .env"
- Not connected → "Click to connect GitHub"
- Connected → Shows username and repos

### Folder Mode
- No files selected → Alert: "please select a folder"
- Upload fails → Shows error in analysis pane
- Success → Shows config insights immediately

### Log Mode
- Empty content → Alert: "please paste log content"
- Invalid format → Parses what it can, shows warnings
- Success → Standard analysis flow

## Implementation Details

**JavaScript Changes**:
- Added `setMode(mode)` function
- Three button event listeners
- Mode-specific section visibility
- Color highlighting on selection
- Default to GitHub mode on load

**HTML Changes**:
- Mode selector grid (3 columns)
- Three hidden sections (shown based on mode)
- Updated help text with keyboard shortcuts
- Styled buttons with inline CSS

**CSS Compatibility**:
- Works with existing tmux.css
- Inline styles for mode-specific colors
- Maintains terminal aesthetic
- Responsive grid layout

## Testing Checklist

- [x] Three buttons visible on load
- [x] GitHub mode selected by default (green)
- [x] Click folder button → orange highlight
- [x] Click log button → blue highlight
- [x] Only one mode content visible at a time
- [x] Folder upload accepts multiple files
- [x] GitHub button redirects to OAuth
- [x] Log textarea works as before
- [x] Keyboard shortcuts functional

## User Feedback

**Expected reactions**:
- "Oh, I don't need to upload anything for GitHub!"
- "I can upload my whole .codex folder with configs"
- "Three clear options, easy to understand"

---

**The frontend now makes it crystal clear there are three ways to use the platform, with GitHub mode prominently featured as requiring no uploads.**
