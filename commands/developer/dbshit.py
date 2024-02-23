import discord
from discord.ext import commands
import asyncpg
import prettytable
from helpers.factorio import factorio
from helpers.config import *
from helpers.paginator import Paginator
from helpers.context import *
from typing import Literal, Optional


class db(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(help="N/A", usage="db", hidden=True, invoke_without_command=True)
    @commands.is_owner()
    async def db(self, ctx):
        # display all subcommands in tbale prettytable
        table = prettytable.PrettyTable()
        table.field_names = ["Subcommand", "Description", "Usage"]
        # automaticcly find all subcommands
        for command in self.walk_commands():
            table.add_row([command.name, command.help, command.usage])
        await ctx.reply(f"```bf\n{table}```")

    @db.command(help="N/A", usage="db tables", hidden=True)
    @commands.is_owner()
    async def tables(self, ctx):
        table = prettytable.PrettyTable()
        table.field_names = ["Table Name", 'Size', 'Rows']
        async with self.bot.db.acquire() as connection:
            # display all tables using simple method
            tables = await connection.fetch("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';")
            
            # get tables sizes and rows
            for table_name in tables:
                size = await connection.fetchval(f"SELECT pg_size_pretty(pg_total_relation_size('{table_name[0]}'));")
                rows = await connection.fetchval(f"SELECT COUNT(*) FROM {table_name[0]};")
                # display columns names
                columns = await connection.fetchval(f"SELECT array_to_string(ARRAY(SELECT column_name::text FROM information_schema.columns WHERE table_name = '{table_name[0]}'), ', ');")
                table.add_row([table_name[0], size, rows])
        await ctx.reply(f"```bf\n{table}```")

    # display table
    @db.command(help="N/A", usage="db display <table name>", hidden=True, aliases=["show"])
    @commands.is_owner()
    async def display(self, ctx, table_name: str):
        # display table in prettytable
        table = prettytable.PrettyTable()
    
        async with self.bot.db.acquire() as connection:
            # get columns names
            columns = await connection.fetchval(f"SELECT array_to_string(ARRAY(SELECT column_name::text FROM information_schema.columns WHERE table_name = '{table_name}'), ', ');")
            table.field_names = columns.split(", ")
    
            # get all rows
            rows = await connection.fetch(f"SELECT * FROM {table_name};")
            for row in rows:
                table.add_row(list(row))  # Convert the row tuple to a list before adding
    
        await ctx.reply(f"```bf\n{table}```")

async def setup(bot):
    await bot.add_cog(db(bot))