import time
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp


class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Show gateway and network latency")
    async def ping(self, interaction: discord.Interaction):
        gateway_ms = round(self.bot.latency * 1000)

        start = time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://discord.com"):
                pass
        network_ms = round((time.perf_counter() - start) * 1000)

        await interaction.response.send_message(
            f"Gateway: `{gateway_ms}ms`\nNetwork: `{network_ms}ms`",
            ephemeral=True
        )

    @app_commands.command(name="shard", description="Show shard information")
    async def shard(self, interaction: discord.Interaction):
        shard_id = interaction.guild.shard_id if interaction.guild else 0
        shard_count = self.bot.shard_count or 1

        await interaction.response.send_message(
            f"Shard ID: `{shard_id}`\nTotal Shards: `{shard_count}`",
            ephemeral=True
        )

    @app_commands.command(name="support", description="Get the support server link")
    async def support(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "You can join our support server [here](<https://discord.gg/https://discord.gg/rzEfDvDNdJ>)!", # <link> stops embeding
            ephemeral=True
        )

    @app_commands.command(name="invite", description="Get the bot invite link")
    async def invite(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "[Tap here to invite the bot now!](https://discord.com/oauth2/authorize?client_id=1455721172271501363)",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Utils(bot))
