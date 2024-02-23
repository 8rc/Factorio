import discord
from discord.ext import commands
from discord import app_commands
from helpers.config import *
import json
import requests

class Level(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot   = bot
        self.blue  = Colors.maincolor
        self.error = Colors.error

        self.required_xp = {
            1: 5,
            2: 10,
            3: 20,
            4: 30,
            5: 40,
            6: 50,
            7: 60
        }

    async def check_profile(self, uid):
        result = await self.bot.db.fetch("SELECT * FROM profile WHERE user_id = $1", uid)
        print(result)
        return result[0] if result else None

    async def progress_bar(self, uid):
        xp = await self.bot.db.fetch("SELECT xp FROM profile WHERE user_id = $1", uid)
        level  = await self.bot.db.fetch("SELECT level FROM profile WHERE user_id = $1", uid)

        next_level = level[0]['level'] + 1
        next_level_xp = self.required_xp[next_level]

        progress = xp[0]['xp'] / next_level_xp

        bar_progress = int(20 * progress)
        bar = '█' * bar_progress + '-' * (20 - bar_progress) + f" **{progress:.2%}**"

        xp_progression = f"{xp[0]['xp']}/{next_level_xp}"

        return bar, next_level, xp_progression

    @app_commands.command(name="level", description="See your current level and information regarding it.")
    async def level(self, i:discord.Interaction):
        profile = await self.check_profile(i.user.id)

        if profile is None:
            e = discord.Embed(color=self.error, description=f"You need to make an account to use this command! Use **/start**")
            return await i.response.send_message(embed=e, ephemeral=True)
        
        data = await self.progress_bar(i.user.id)

        bar = data[0]
        level = data[1]
        xp_needed = data[2]

        print(f"Level: {level} - hi: {level-1}")

        multi = .25 * (level-1) + 1

        embed = discord.Embed(title=f"{i.user.name}'s Level Information", description=f"{bar} to level **{level}**", color=self.blue)
        embed.add_field(name="XP", value=f"{xp_needed}", inline=True)
        embed.add_field(name="Level Bonus", value=f"X{multi}")

        await i.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Level(bot))