import discord
from discord.ext import commands
from discord import app_commands
from typing import Literal

class SettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="settings", description="Configure bot settings")
    async def configure_settings(self, interaction: discord.Interaction):
        prefs = await self.bot.db.get_user_preferences(str(interaction.user.id))

        if not prefs:
            prefs = {
                'enabled': True,
                'aggressiveness': 0.7,
                'min_confidence': 0.6,
                'suggestion_style': 'inline'
            }

        embed = discord.Embed(
            title="⚙️ Your Bot Settings",
            description="Current configuration:",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Suggestions Enabled",
            value="✅ Yes" if prefs.get('enabled', True) else "❌ No",
            inline=True
        )

        embed.add_field(
            name="Aggressiveness",
            value=f"{prefs.get('aggressiveness', 0.7):.1f}",
            inline=True
        )

        embed.add_field(
            name="Min Confidence",
            value=f"{prefs.get('min_confidence', 0.6):.1%}",
            inline=True
        )

        embed.add_field(
            name="Suggestion Style",
            value=prefs.get('suggestion_style', 'inline'),
            inline=True
        )

        embed.set_footer(text="Use the commands below to modify settings")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="toggle", description="Enable or disable suggestions")
    @app_commands.describe(enabled="Enable or disable command suggestions")
    async def toggle_suggestions(self, interaction: discord.Interaction, enabled: bool):
        await interaction.response.defer(ephemeral=True)

        prefs = await self.bot.db.get_user_preferences(str(interaction.user.id))

        if not prefs:
            prefs = {
                'enabled': True,
                'aggressiveness': 0.7,
                'min_confidence': 0.6,
                'suggestion_style': 'inline'
            }

        prefs['enabled'] = enabled

        await self.bot.db.update_user_preferences(str(interaction.user.id), prefs)
        await self.bot.db.register_user(str(interaction.user.id), str(interaction.user.name))

        status = "enabled" if enabled else "disabled"
        await interaction.followup.send(f"✅ Command suggestions have been {status}.", ephemeral=True)

    @app_commands.command(name="confidence", description="Set minimum confidence threshold for suggestions")
    @app_commands.describe(threshold="Confidence threshold between 0.0 and 1.0 (default: 0.6)")
    async def set_confidence(self, interaction: discord.Interaction, threshold: float):
        await interaction.response.defer(ephemeral=True)

        threshold = max(0.0, min(1.0, threshold))

        prefs = await self.bot.db.get_user_preferences(str(interaction.user.id))

        if not prefs:
            prefs = {
                'enabled': True,
                'aggressiveness': 0.7,
                'min_confidence': 0.6,
                'suggestion_style': 'inline'
            }

        prefs['min_confidence'] = threshold

        await self.bot.db.update_user_preferences(str(interaction.user.id), prefs)
        await self.bot.db.register_user(str(interaction.user.id), str(interaction.user.name))

        await interaction.followup.send(
            f"✅ Minimum confidence threshold set to {threshold:.0%}.",
            ephemeral=True
        )

    @app_commands.command(name="style", description="Set suggestion display style")
    @app_commands.describe(style="How suggestions should be displayed")
    async def set_style(
        self,
        interaction: discord.Interaction,
        style: Literal['inline', 'buttons', 'disabled']
    ):
        await interaction.response.defer(ephemeral=True)

        prefs = await self.bot.db.get_user_preferences(str(interaction.user.id))

        if not prefs:
            prefs = {
                'enabled': True,
                'aggressiveness': 0.7,
                'min_confidence': 0.6,
                'suggestion_style': 'inline'
            }

        prefs['suggestion_style'] = style

        if style == 'disabled':
            prefs['enabled'] = False

        await self.bot.db.update_user_preferences(str(interaction.user.id), prefs)
        await self.bot.db.register_user(str(interaction.user.id), str(interaction.user.name))

        await interaction.followup.send(
            f"✅ Suggestion style set to **{style}**.",
            ephemeral=True
        )

    @app_commands.command(name="reset", description="Reset all settings to defaults")
    async def reset_settings(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        default_prefs = {
            'enabled': True,
            'aggressiveness': 0.7,
            'min_confidence': 0.6,
            'suggestion_style': 'inline'
        }

        await self.bot.db.update_user_preferences(str(interaction.user.id), default_prefs)
        await self.bot.db.register_user(str(interaction.user.id), str(interaction.user.name))

        await interaction.followup.send(
            "✅ All settings have been reset to defaults.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(SettingsCog(bot))
