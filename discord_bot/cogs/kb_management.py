import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import re

class KnowledgeBaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kb-upload", description="Upload a document to your knowledge base")
    async def upload_document(self, interaction: discord.Interaction, attachment: discord.Attachment):
        await interaction.response.defer(ephemeral=True)

        if not attachment.filename.endswith(('.md', '.txt', '.py', '.js', '.ts', '.json', '.yaml', '.yml')):
            await interaction.followup.send(
                "❌ Only text-based files are supported (.md, .txt, .py, .js, .ts, .json, .yaml, .yml)",
                ephemeral=True
            )
            return

        if attachment.size > 1024 * 1024:
            await interaction.followup.send(
                "❌ File size must be under 1MB.",
                ephemeral=True
            )
            return

        try:
            content = await attachment.read()
            content_text = content.decode('utf-8')

            doc = await self.bot.db.store_kb_document(
                user_id=str(interaction.user.id),
                file_name=attachment.filename,
                file_path=f"discord/{attachment.filename}",
                content=content_text
            )

            if not doc:
                await interaction.followup.send("❌ Failed to store document.", ephemeral=True)
                return

            chunks = self._chunk_document(content_text)

            for i, chunk in enumerate(chunks):
                await self.bot.db.store_kb_chunk(
                    document_id=doc['id'],
                    chunk_index=i,
                    content=chunk,
                    metadata={'file_name': attachment.filename}
                )

            await interaction.followup.send(
                f"✅ Successfully uploaded **{attachment.filename}** to your knowledge base!\n"
                f"Created {len(chunks)} searchable chunks.",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error processing file: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="kb-search", description="Search your knowledge base")
    @app_commands.describe(query="Search query")
    async def search_kb(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(ephemeral=True)

        results = await self.bot.db.search_kb_chunks(str(interaction.user.id), query, limit=5)

        if not results:
            await interaction.followup.send(
                f"No results found for: **{query}**",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"🔍 Knowledge Base Search Results",
            description=f"Query: **{query}**",
            color=discord.Color.blue()
        )

        for i, result in enumerate(results[:5], 1):
            content = result['content'][:200]
            if len(result['content']) > 200:
                content += "..."

            file_name = result.get('metadata', {}).get('file_name', 'unknown')

            embed.add_field(
                name=f"{i}. {file_name}",
                value=f"```\n{content}\n```",
                inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="kb-list", description="List all documents in your knowledge base")
    async def list_documents(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_result = self.bot.db.client.table('discord_users').select('id').eq('discord_id', str(interaction.user.id)).maybeSingle().execute()

        if not user_result.data:
            await interaction.followup.send("You don't have any documents yet.", ephemeral=True)
            return

        user_uuid = user_result.data['id']

        docs = self.bot.db.client.table('kb_documents').select('*').eq('user_id', user_uuid).execute()

        if not docs.data:
            await interaction.followup.send("You don't have any documents yet.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📚 Your Knowledge Base",
            description=f"Total documents: {len(docs.data)}",
            color=discord.Color.green()
        )

        for doc in docs.data[:10]:
            size_kb = len(doc['content']) / 1024

            embed.add_field(
                name=doc['file_name'],
                value=f"Path: `{doc['file_path']}`\nSize: {size_kb:.1f} KB\nAdded: {doc['created_at'][:10]}",
                inline=False
            )

        if len(docs.data) > 10:
            embed.set_footer(text=f"Showing 10 of {len(docs.data)} documents")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="kb-delete", description="Delete a document from your knowledge base")
    @app_commands.describe(filename="Name of the file to delete")
    async def delete_document(self, interaction: discord.Interaction, filename: str):
        await interaction.response.defer(ephemeral=True)

        user_result = self.bot.db.client.table('discord_users').select('id').eq('discord_id', str(interaction.user.id)).maybeSingle().execute()

        if not user_result.data:
            await interaction.followup.send("Document not found.", ephemeral=True)
            return

        user_uuid = user_result.data['id']

        doc = self.bot.db.client.table('kb_documents').select('id').eq('user_id', user_uuid).eq('file_name', filename).maybeSingle().execute()

        if not doc.data:
            await interaction.followup.send(f"Document **{filename}** not found.", ephemeral=True)
            return

        self.bot.db.client.table('kb_chunks').delete().eq('document_id', doc.data['id']).execute()
        self.bot.db.client.table('kb_documents').delete().eq('id', doc.data['id']).execute()

        await interaction.followup.send(
            f"✅ Successfully deleted **{filename}** from your knowledge base.",
            ephemeral=True
        )

    def _chunk_document(self, content: str, chunk_size: int = 500) -> list:
        paragraphs = re.split(r'\n\s*\n', content)

        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            if current_size + para_size > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

async def setup(bot):
    await bot.add_cog(KnowledgeBaseCog(bot))
