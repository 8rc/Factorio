import discord
from discord.ext import commands
from discord import app_commands
from helpers.config import *
import json
import requests
import random

class Work(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot   = bot
        self.blue  = Colors.maincolor
        self.error = Colors.error
        
        self.actions = {
            0: [
                'just stole a wallet and found <money> in it!',
                'just scraped the ground for change and found <money>!',
                'just sold illegal stuff animals for <money> on the hackerweb!',
                "just cleaned their moms house for millions (actually was <money>)!",
                "just started a fansly and sold toe pics for <money>!",
                "just got paid <money> from their Rent-A-Friend service!",
                "just started a ponzi scheme and pulled out <money>!",
                "just made <money> by selling fake coupon codes!",
                "just made <money> from their illegal robux gambling site!",
                "just catfished my dad and made him send <money>!",
                "just blackmailed adin ross into giving him <money>!",
                "just rug pulled 10293 Ethereum adding up to <money>!",
                "just sold their pandabuy shoes and earned <money> profit!",
                "just staged a series of elbaorate insurance scams and earned <money>!",
                "just made <money> from offering fake diplomas and certificates online!",
                "just sold 'miracle' weight loss pills and made <money>!",
                "just posed as a stranded travelor and solicited <money> from sympathetic strangers with fake sob stories!",
                "just got caught making fake charities but made a total of <money>!",
                "just made <money> from running a 'physic' hotline charging exorbitant fees for vague predictions, exploiting their vulnerabilities!",
                "just setup a lemonade stand but diluted the lemonade to save money on ingredients and made <money>!",
                "just earned <money> from doing chores for their neighbors but intentionally did a bad job so they get paid to go away!",]
        }

        self.job_functions = {
            0: self.job
        }

        self.job_salary = {
            0: [5, 10],
            1: [11, 25],
            2: [26, 50],
        }
        self.xp = {
            0: [1, 2],
            1: [3, 5],
            2: [6, 10],
            3: [11, 16],
            4: [17, 25],
            5: [26, 40],
            6: [41, 60],
            7: [61, 90],
            8: [91, 125],
            9: [126, 175],
            10: [176, 250]
        }

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
        result = await self.bot.db.fetch("SELECT user_id FROM profile WHERE user_id = $1", uid)
        
        if result == []:
            result = None
        return result
    
    async def get_job(self, uid):
        result = await self.bot.db.fetch("SELECT job FROM profile WHERE user_id = $1", uid)

        return int(result[0]['job'])
    
    async def add_money(self, uid, amount):
        old_bal = await self.bot.db.fetch("SELECT wallet FROM profile WHERE user_id = $1", uid)
        level = await self.bot.db.fetch("SELECT level FROM profile WHERE user_id = $1", uid)
        bal = int(amount) + int(old_bal[0]['wallet'])

        multi = (level[0]['level'] * .25) + 1

        print()

        amount = multi * bal

        print(f"Default: {bal} | Multi: {multi}")


        try:
            result = await self.bot.db.execute("UPDATE profile SET wallet = $1 WHERE user_id = $2", round(amount), uid)
            return True
        except:
            return None

    async def add_xp(self, uid, job_id):
        _min, _max = self.xp[job_id][0], self.xp[job_id][1]
        amount = random.randint(_min, _max)
        old_xp = await self.bot.db.fetch("SELECT xp FROM profile WHERE user_id = $1", uid)
        old_xp = old_xp[0]['xp']
        level  = await self.bot.db.fetch("SELECT level FROM profile WHERE user_id = $1", uid)
        level = level[0]['level']
        xp = amount + old_xp
        next_level_xp = self.required_xp[level + 1]


        if xp >= next_level_xp:
            xp = xp - self.required_xp[int(level) + 1]
            new_level = level + 1
        else:
            new_level = level

        try:
            await self.bot.db.execute("UPDATE profile SET xp = $1 WHERE user_id = $2", xp, uid)
            if new_level != level:
                await self.bot.db.execute("UPDATE profile SET level = $1 WHERE user_id = $2", new_level, uid)
                
            return xp, level, new_level, amount
        except Exception as error:
            return error

    async def job(self, uid, i, job_id:int):
        _min, _max = self.job_salary[job_id][0], self.job_salary[job_id][1]
        pay = random.randint(_min, _max)

        add_pay = await self.add_money(uid, pay)

        if add_pay is False:
            return # Return error
        
        data = await self.add_xp(uid, job_id)

        #print(f"Data: {data}\n Level: {data[0]}")
        if data is None:
            return await i.response.send_message("Error")
        
        #print(f"data: {data[0]}")

        level = data[1]
        new_level = data[2]
        amount = data[3]

        multi = (level * .25) + 1

        sentence = random.choice(self.actions[job_id])
        sentence = sentence.replace("<money>", f"**${str(round(pay * multi))}**")
        
        embed = discord.Embed(description=f"{i.user.mention} {sentence}", color=self.blue)
        embed.set_footer(text=f"+{data[3]} XP")
        await i.response.send_message(embed=embed)

        if int(new_level) != level:
            embed = discord.Embed(title="Congrats!", description=f"{i.user.mention} has leveled up! User is now level {new_level}. Run /level to see your level benefits.")
            await i.channel.send(embed=embed)
        

    @app_commands.command(name="work", description="Work duh")
    async def work(self, i:discord.Interaction):
        profile = await self.check_profile(i.user.id)

        if profile is None:
            e = discord.Embed(color=self.error, description=f"You need to make an account to use this command! Use **/start**")
            return await i.response.send_message(embed=e, ephemeral=True)

        job = await self.get_job(i.user.id)
        await self.job_functions[job](i.user.id, i, job)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Work(bot))