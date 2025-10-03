import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class SuggestionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="suggest", description="Manually request command suggestions")
    async def suggest_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        context = await self.bot.command_tracker.get_recent_context(
            user_id=str(interaction.user.id),
            limit=10
        )

        user_prefs = await self.bot.db.get_user_preferences(str(interaction.user.id))

        suggestions = await self.bot.suggestion_engine.generate_suggestions(
            user_id=str(interaction.user.id),
            current_context=context,
            current_message="",
            min_confidence=user_prefs.get('min_confidence', 0.5) if user_prefs else 0.5
        )

        if not suggestions:
            await interaction.followup.send("No suggestions available based on your command history.", ephemeral=True)
            return

        embed = discord.Embed(
            title="💡 Command Suggestions",
            description="Based on your recent command history:",
            color=discord.Color.blue()
        )

        for i, suggestion in enumerate(suggestions[:5], 1):
            embed.add_field(
                name=f"{i}. {suggestion['source']} ({suggestion['confidence']:.0%})",
                value=f"```\n{suggestion['command']}\n```",
                inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="stats", description="View your command usage statistics")
    async def view_stats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        stats = await self.bot.command_tracker.get_command_statistics(str(interaction.user.id))

        embed = discord.Embed(
            title="📊 Your Command Statistics",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Total Commands",
            value=str(stats['total_commands']),
            inline=True
        )

        embed.add_field(
            name="Suggestions Shown",
            value=str(stats['suggestions_shown']),
            inline=True
        )

        embed.add_field(
            name="Acceptance Rate",
            value=f"{stats['acceptance_rate']:.1%}",
            inline=True
        )

        if stats['command_types']:
            top_types = sorted(stats['command_types'].items(), key=lambda x: x[1], reverse=True)[:5]
            type_text = '\n'.join([f"• {cmd_type}: {count}" for cmd_type, count in top_types])
            embed.add_field(
                name="Most Used Command Types",
                value=type_text,
                inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="history", description="View your recent command history")
    @app_commands.describe(limit="Number of commands to show (default: 10, max: 25)")
    async def view_history(self, interaction: discord.Interaction, limit: Optional[int] = 10):
        await interaction.response.defer(ephemeral=True)

        limit = min(max(1, limit), 25)

        history = await self.bot.db.get_command_history(str(interaction.user.id), limit=limit)

        if not history:
            await interaction.followup.send("No command history found.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📜 Recent Command History (Last {len(history)})",
            color=discord.Color.blue()
        )

        for i, cmd in enumerate(reversed(history[:limit]), 1):
            cmd_text = cmd['command_text'][:100]
            cmd_type = cmd.get('command_type', 'unknown')
            timestamp = cmd.get('created_at', '')

            suggested_badge = "✅" if cmd.get('was_suggested') else ""

            embed.add_field(
                name=f"{i}. {cmd_type} {suggested_badge}",
                value=f"```\n{cmd_text}\n```",
                inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="clear-history", description="Clear your command history")
    async def clear_history(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "⚠️ This will permanently delete all your command history. Are you sure?",
            ephemeral=True,
            view=ConfirmClearView(self.bot, interaction.user.id)
        )

class ConfirmClearView(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=60)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="Yes, clear my history", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_result = self.bot.db.client.table('discord_users').select('id').eq('discord_id', str(self.user_id)).maybeSingle().execute()

        if user_result.data:
            user_uuid = user_result.data['id']

            self.bot.db.client.table('command_history').delete().eq('user_id', user_uuid).execute()
            self.bot.db.client.table('command_patterns').delete().eq('user_id', user_uuid).execute()
            self.bot.db.client.table('command_suggestions').delete().eq('user_id', user_uuid).execute()

            await interaction.response.edit_message(
                content="✅ Your command history has been cleared.",
                view=None
            )
        else:
            await interaction.response.edit_message(
                content="❌ Unable to find your user record.",
                view=None
            )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="Command history clearing cancelled.",
            view=None
        )

async def setup(bot):
    await bot.add_cog(SuggestionsCog(bot))
