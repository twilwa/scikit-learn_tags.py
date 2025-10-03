import discord
from discord.ext import commands
import os
from datetime import datetime
from typing import Optional, List, Dict
import asyncio

from discord_bot.database import DiscordDatabase
from discord_bot.suggestion_engine import SuggestionEngine
from discord_bot.command_tracker import CommandTracker

class ClaudeAssistantBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True

        super().__init__(
            command_prefix='!',
            intents=intents,
            description='Claude Code Assistant - Ghost-text command suggestions'
        )

        self.db = DiscordDatabase()
        self.suggestion_engine = SuggestionEngine(self.db)
        self.command_tracker = CommandTracker(self.db)

    async def setup_hook(self):
        await self.load_extension('discord_bot.cogs.suggestions')
        await self.load_extension('discord_bot.cogs.kb_management')
        await self.load_extension('discord_bot.cogs.settings')
        print(f'Loaded {len(self.extensions)} extensions')

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Connected to {len(self.guilds)} guilds')

        for guild in self.guilds:
            await self.db.register_server(str(guild.id), guild.name)

        await self.tree.sync()
        print('Command tree synced')

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        await self.process_commands(message)

        user_prefs = await self.db.get_user_preferences(str(message.author.id))

        if not user_prefs or not user_prefs.get('enabled', True):
            return

        server_settings = await self.db.get_server_settings(str(message.guild.id) if message.guild else None)

        if server_settings:
            enabled_channels = server_settings.get('settings', {}).get('enabled_channels', [])
            if enabled_channels and str(message.channel.id) not in enabled_channels:
                return

        await self.command_tracker.track_command(
            user_id=str(message.author.id),
            server_id=str(message.guild.id) if message.guild else None,
            channel_id=str(message.channel.id),
            command_text=message.content
        )

        context = await self.command_tracker.get_recent_context(
            user_id=str(message.author.id),
            limit=10
        )

        suggestions = await self.suggestion_engine.generate_suggestions(
            user_id=str(message.author.id),
            current_context=context,
            current_message=message.content,
            min_confidence=user_prefs.get('min_confidence', 0.6)
        )

        if suggestions:
            await self.send_suggestions(message, suggestions, user_prefs)

    async def send_suggestions(self, message: discord.Message, suggestions: List[Dict], user_prefs: Dict):
        style = user_prefs.get('suggestion_style', 'inline')

        if style == 'inline' and len(suggestions) > 0:
            top_suggestion = suggestions[0]

            if top_suggestion['confidence'] >= user_prefs.get('min_confidence', 0.6):
                embed = discord.Embed(
                    title="💡 Suggested Next Command",
                    description=f"```\n{top_suggestion['command']}\n```",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Confidence",
                    value=f"{top_suggestion['confidence']:.0%}",
                    inline=True
                )
                embed.add_field(
                    name="Source",
                    value=top_suggestion['source'],
                    inline=True
                )
                embed.set_footer(text="React with ✅ to use this command, or ignore to dismiss")

                suggestion_msg = await message.reply(embed=embed, mention_author=False)

                await suggestion_msg.add_reaction('✅')
                await suggestion_msg.add_reaction('❌')

                def check(reaction, user):
                    return user == message.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == suggestion_msg.id

                try:
                    reaction, user = await self.wait_for('reaction_add', timeout=60.0, check=check)

                    if str(reaction.emoji) == '✅':
                        await self.command_tracker.mark_suggestion_accepted(
                            user_id=str(message.author.id),
                            command_text=top_suggestion['command']
                        )
                        await message.channel.send(f"```\n{top_suggestion['command']}\n```")
                    else:
                        await suggestion_msg.delete()

                except asyncio.TimeoutError:
                    await suggestion_msg.delete()

        elif style == 'buttons' and len(suggestions) > 0:
            embed = discord.Embed(
                title="💡 Command Suggestions",
                description="Here are some commands you might want to run next:",
                color=discord.Color.blue()
            )

            for i, suggestion in enumerate(suggestions[:3], 1):
                embed.add_field(
                    name=f"{i}. {suggestion['source']} ({suggestion['confidence']:.0%})",
                    value=f"```\n{suggestion['command']}\n```",
                    inline=False
                )

            await message.reply(embed=embed, mention_author=False)

def run_bot():
    token = os.getenv('DISCORD_BOT_TOKEN')

    if not token:
        raise ValueError('DISCORD_BOT_TOKEN environment variable is not set')

    bot = ClaudeAssistantBot()
    bot.run(token)
