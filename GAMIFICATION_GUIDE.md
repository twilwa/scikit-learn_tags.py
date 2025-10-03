# Gamification System - Level Up Your Debugging

## Overview

The platform now includes a full RPG-style progression system with mysterious scoring, achievements, quests, and a Top 10 leaderboard.

## The Mysterious Score

Your score is calculated using a secret algorithm that considers:

- **Session completions** - Finish what you start
- **KB contributions** - Share knowledge with the community
- **Insights discovered** - High-signal analysis
- **Successful builds** - Make repos actually work
- **Voice session hours** - Deep collaborative work
- **REPL executions** - Hands-on debugging
- **??? bonus multipliers** - The path reveals itself

The exact formula is intentionally mysterious. Experiment and discover what works!

## Leaderboard

### Top 10

Only the best make it to the eternal leaderboard. Rankings update in real-time based on:

1. Base score from activities
2. Quality multipliers (successful builds, helpful KB votes)
3. Engagement multipliers (voice sessions, deep analysis)
4. Mysterious bonus (unlocked through discovery)

### Viewing the Leaderboard

Visit the homepage to see current rankings:
- Rank (1-10)
- Username
- Title (earned through progression)
- Mysterious Score (the only number that matters)

Top 3 get special badges:
- 🥇 Gold
- 🥈 Silver
- 🥉 Bronze

## Achievements

### Tiers

**Bronze** - Starter achievements (10-50 points)
- First Contact - Complete your first session
- Night Owl - Work late night sessions

**Silver** - Intermediate achievements (50-100 points)
- Log Whisperer - Analyze 10 logs
- Knowledge Keeper - Contribute 5 KB docs

**Gold** - Advanced achievements (150-250 points)
- Community Guide - Get 50 helpful votes
- Voice Commander - Complete 10 voice sessions
- Speed Demon - Debug in under 10 minutes

**Platinum** - Expert achievements (500-750 points)
- Build Wizard - Successfully build 25 repos
- Artifact Collector - Generate 100 high-signal insights

**Mysterious** - Hidden achievements (1000+ points)
- ??? - The path reveals itself to those who seek

### Unlocking Achievements

Achievements unlock automatically when you meet the criteria. Some are hidden and must be discovered through experimentation.

Check your profile to see:
- Unlocked achievements
- Progress toward locked achievements
- Total achievement points
- Rarity tier distribution

## Quests

### Module System

Complete full workflows to earn bonus points:

**First Log** (10 points)
1. Upload a Claude Code log
2. Review analysis results
3. Export insights

**Voice Session Master** (50 points)
1. Start a voice session
2. Execute 10+ REPL commands
3. Generate visualizations
4. Successfully debug an issue

**Knowledge Contributor** (25 points)
1. Upload Obsidian document
2. Set visibility to "shared"
3. Receive 5+ helpful votes
4. Update based on feedback

**Build Master** (100 points)
1. Upload repo
2. Analyze build failures
3. Apply suggested fixes
4. Achieve successful build

**Speed Run** (150 points)
1. Complete full debugging session
2. Finish in under 10 minutes
3. Achieve successful build
4. Generate exportable insights

### Quest Tracking

View quest progress in your profile:
- Active quests
- Completion percentage
- Recent completions
- Total quest score

## Level Progression

### Experience Points (XP)

Earn XP from:
- Completing sessions (+10 XP)
- Contributing to KB (+25 XP)
- Successful builds (+50 XP)
- Unlocking achievements (varies)
- Completing quests (varies)

### Level Thresholds

- **Level 1-10**: 100 XP per level (Novice)
- **Level 11-25**: 250 XP per level (Intermediate)
- **Level 26-50**: 500 XP per level (Advanced)
- **Level 51-100**: 1000 XP per level (Expert)
- **Level 100+**: 2000 XP per level (Master)

### Titles

Earned automatically as you level up:

- Level 1-10: Novice Debugger
- Level 11-25: Code Investigator
- Level 26-50: System Analyst
- Level 51-75: Architecture Wizard
- Level 76-100: Debug Master
- Level 100+: Mysterious One

## Stats Tracking

Your profile tracks comprehensive stats:

### Session Stats
- Total sessions completed
- Average session duration
- Success rate
- Fastest completion time

### Contribution Stats
- KB documents shared
- Total helpful votes received
- Average quality score
- Community impact score

### Technical Stats
- Successful builds
- Insights discovered
- Artifacts generated
- Lines of code analyzed

### Engagement Stats
- Voice session hours
- REPL executions
- Visualizations created
- Days active

## Scoring Multipliers

### Quality Multipliers

**High Success Rate** (×1.5)
- 80%+ of your builds succeed
- Consistent high-quality contributions

**Community Champion** (×1.3)
- 20+ shared KB documents
- High helpfulness rating

**Build Expert** (×2.0)
- 10+ successful builds
- Complex repositories

### Engagement Multipliers

**Voice Power User** (×1.2)
- 10+ hours of voice sessions
- Deep collaborative work

**Consistency Bonus** (×1.1)
- Active 5+ days this week
- Regular contributions

### Mysterious Bonuses

Unlock hidden multipliers by:
- Discovering patterns others miss
- Contributing unique insights
- Helping community members
- Finding edge cases
- Building the impossible

The exact triggers are intentionally hidden. Experiment!

## Competitive Features

### Seasons

Leaderboards reset seasonally:
- **Eternal** - All-time rankings
- **Monthly** - Reset each month
- **Weekly** - Reset each week
- **Daily** - 24-hour competition

Compete in multiple seasons simultaneously.

### Challenges

Special limited-time events:
- Speed debugging competitions
- Quality contribution contests
- Community collaboration challenges
- Mystery hunts

Check the homepage for active challenges.

## API Integration

### Update Stats

```bash
POST /api/users/{user_id}/stats
{
  "stat_updates": {
    "sessions_completed": 1,
    "builds_successful": 1,
    "insights_discovered": 5
  }
}
```

### View Profile

```bash
GET /api/users/{user_id}/profile
```

Returns:
- Profile data
- Unlocked achievements
- Recent quest completions
- Current rank

### Complete Quest

```bash
POST /api/quests/{quest_key}/complete
```

### View Leaderboard

```bash
GET /api/leaderboard?season=eternal&limit=10
```

## Tips for Ranking Up

### Fast XP
1. Complete voice sessions (50 XP + multipliers)
2. Successful builds (100 XP + quality bonus)
3. Contribute high-quality KB docs (25 XP + votes)

### Quality Over Quantity
- One successful build > 10 failed attempts
- One well-documented KB entry > 5 low-quality
- Deep voice session > quick text session

### Community Engagement
- Help others by sharing knowledge
- Vote helpfully on KB contributions
- Provide constructive feedback
- Collaborate in voice sessions

### Discover Secrets
- Try unusual combinations
- Explore all features
- Look for patterns
- Think creatively

### Consistency Wins
- Log in daily for streak bonuses
- Complete at least one session daily
- Maintain high success rate
- Stay active in community

## Hidden Features

There are easter eggs and hidden features throughout:
- Secret achievement triggers
- Bonus score multipliers
- Mysterious quest chains
- Leaderboard shortcuts

Find them all to unlock the "Mysterious One" achievement.

## Privacy

### What's Public
- Username
- Title
- Mysterious score
- Achievement count (not details)
- Leaderboard rank

### What's Private
- Specific sessions
- KB content details
- Exact stat breakdowns
- Error logs
- Personal information

You control visibility in your profile settings.

## Fair Play

### Allowed
- Multiple sessions per day
- Sharing knowledge freely
- Collaborating with others
- Experimenting with features

### Not Allowed
- Fake sessions
- Automated stat farming
- Multiple accounts
- Manipulating votes

Violations result in score reset and potential ban.

## Future Features

Coming soon:
- [ ] Team competitions
- [ ] Guild system
- [ ] Custom challenges
- [ ] Betting on rankings
- [ ] Achievement trading
- [ ] Seasonal rewards
- [ ] Hall of fame

---

**Current Leader**: Check the leaderboard!

**Your Rank**: Complete your first session to appear

**Next Level**: Start earning XP now

The top spot is waiting. Will you take it?
