import discord
from discord.ext import commands
from discord import app_commands
from helpers.config import *
import json
import requests

class Start(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot   = bot
        self.blue  = Colors.maincolor
        self.error = Colors.error

    async def check_name(self, name):
        result = await self.bot.db.fetchval("SELECT name FROM profile WHERE name = $1", name)

        if result == []:
            result = None
        return 
    
    async def check_profile(self, uid):
        result = await self.bot.db.fetch("SELECT user_id FROM profile WHERE user_id = $1", uid)
        
        if result == []:
            result = None
        return result

    @app_commands.command(name="start", description="Start a Profile!")
    async def start(self, i: discord.Interaction, name: str):
        member = i.user
    
        check_profile = await self.check_profile(member.id)
        if check_profile is not None:
            e = discord.Embed(color=self.error, description="You already have an account!")
            return await i.response.send_message(embed=e, ephemeral=True)
    
        if len(name) < 4:
            e = discord.Embed(color=self.error, description="Name must be at least 4 characters long!")
            return await i.response.send_message(embed=e, ephemeral=True)
    
        if len(name) > 12:
            e = discord.Embed(color=self.error, description="Name can't be longer than 12 characters!")
            return await i.response.send_message(embed=e, ephemeral=True)
    
        name_exists = await self.check_name(name)
        if name_exists:
            e = discord.Embed(color=self.error, description="Sorry, that name is already taken!")
            return await i.response.send_message(embed=e, ephemeral=True)
    
        await self.bot.db.execute("INSERT INTO profile (user_id, name) VALUES ($1, $2)", member.id, name)
    
        # Welcoming message in the Profile Created embed
        embed = discord.Embed(color=self.blue, title="Profile Created!")
        embed.add_field(name="Welcome to Factorio Mafia World! 🏭🕴️🔫", value=(
            f"Congratulations, {member.mention}! You are now a part of the Factorio Mafia.\n"
            f"As a mafia boss in the world of factories, you'll manage your empire, build powerful factories, and dominate the market.\n\n"
            f"🌟 Level: 1\n"
            f"💰 Wallet: 0\n"
            f"🏦 Bank: 0\n\n"
            f"**Clans and Fights**: Stay tuned for future updates! Weekly updates will bring new features, including the ability to form clans and engage in epic mafia battles. Exciting times await you!\n\n"
            f"**Factories**: Embrace the power of automation! Build, expand, and optimize your factories to become the ultimate industrial tycoon. Keep an eye out for resources, research new technologies, and conquer the world of Factorio!"
        ))
        await i.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Start(bot))
