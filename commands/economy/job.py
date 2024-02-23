import discord
from discord.ext import commands
from discord import app_commands
from helpers.config import *
import json
import requests

class Job(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot   = bot
        self.blue  = Colors.maincolor
        self.error = Colors.error

    @app_commands.command(name="job", description="See information regarding your current job and the next job.")
    async def job(self, i:discord.Interaction, name:str):
        pass

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Job(bot))