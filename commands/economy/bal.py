import discord
from discord.ext import commands
from discord import app_commands
from helpers.config import *
import json
import requests

class Balance(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot   = bot
        self.blue  = Colors.maincolor
        self.error = Colors.error

    async def get_balance(self, uid):
        data = await self.bot.db.fetch("SELECT * FROM profile WHERE user_id = $1", uid)
        return data[0]['wallet'], data[0]['bank']

    async def check_profile(self, uid):
        result = await self.bot.db.fetch("SELECT * FROM profile WHERE user_id = $1", uid)
        return result[0] if result else None

    @app_commands.command(name="balance", description="See a user's balance")
    async def balance(self, i: discord.Interaction, user: discord.User = None):
        target_user = user or i.user  # If user parameter is not provided, default to the command user

        profile = await self.check_profile(target_user.id)
        if profile is None:
            e = discord.Embed(color=self.error, description=f"{target_user.name} needs to make an account to use this command! Use **/start**")
            return await i.response.send_message(embed=e, ephemeral=True)

        wallet, bank = await self.get_balance(target_user.id)

        embed = discord.Embed(title=f"{target_user.name}'s Balance")
        embed.add_field(name="Wallet", value=int(wallet), inline=True)
        embed.add_field(name="Bank", value=int(bank))

        await i.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Balance(bot))
