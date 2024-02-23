import discord
from discord.ext import commands
from discord import app_commands
from helpers.config import *
import json
import requests

class Profile(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot   = bot
        self.blue  = Colors.maincolor
        self.error = Colors.error

    async def check_profile(self, uid):
        result = await self.bot.db.fetch("SELECT * FROM profile WHERE user_id = $1", uid)
        print(result)
        return result[0] if result else None

    @app_commands.command(name="profile", description="See a user's stat.")
    async def profile(self, i: discord.Interaction, user: discord.Member = None):
        target_user_id = user.id if user else i.user.id
        profile = await self.check_profile(target_user_id)

        if profile is None:
            e = discord.Embed(color=self.error, description=f"You need to make an account to use this command! Use **/start**")
            return await i.response.send_message(embed=e, ephemeral=True)

        if user is None:
            author = i.user
        else:
            author = user

        embed = discord.Embed(title=f"{author.name}'s Profile", description=f"PROFILE NAME - **{profile['name']}** ({author.mention})", color=self.blue)
        embed.add_field(name="Level", value=profile['level'], inline=True)
        embed.add_field(name="XP", value=profile['xp'])
        embed.add_field(name=" ", value=" ", inline=False)
        embed.add_field(name="Wallet", value=profile['wallet'])
        embed.add_field(name="Bank", value=profile['bank'], inline=True)
        
        await i.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Profile(bot))
