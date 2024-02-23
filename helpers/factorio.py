import discord
from discord.ext import commands
from discord.ext.commands import core
from discord.utils import utcnow
from helpers.config import *
from helpers.context import Context
from helpers import regex
import asyncpg
from pathlib import Path
import time
import os, datetime, aiohttp, aiosqlite, humanize, time
from datetime import *
from discord.gateway import DiscordWebSocket
from datetime import datetime
from loguru import logger
from sys import stdout
from logging import getLogger, CRITICAL
import sys
from multiprocessing import Process
import asyncio
import contextlib
from discord import app_commands
from typing import Optional, List

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"
os.environ["JISHAKU_RETAIN"] = "True"

for log in ["discord", "discord.client", "discord.gateway"]:
    getLogger(log).setLevel(CRITICAL)

class MentionableTree(app_commands.CommandTree):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application_commands: dict[Optional[int], List[app_commands.AppCommand]] = {}

    async def sync(self, *, guild: Optional[discord.abc.Snowflake] = None):
        ret = await super().sync(guild=guild)
        self.application_commands[guild.id if guild else None] = ret
        return ret

    async def fetch_commands(self, *, guild: Optional[discord.abc.Snowflake] = None):
        ret = await super().fetch_commands(guild=guild)
        self.application_commands[guild.id if guild else None] = ret
        return ret

    async def find_mention_for(
        self,
        command: app_commands.Command,
        *,
        guild: Optional[discord.abc.Snowflake] = None,
    ) -> Optional[str]:
        try:
            found_commands = self.application_commands[guild.id if guild else None]
        except KeyError:
            found_commands = await self.fetch_commands(guild=guild)

        root_parent = command.root_parent or command
        command_id_found = discord.utils.get(found_commands, name=root_parent.name)
        if command_id_found:
            return f"</{command.qualified_name}:{command_id_found.id}>"
        return None

class factorio(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            intents=discord.Intents.all(),
            command_prefix=Auth.prefix,
            case_insensitive=True,
            activity=discord.Activity(type=discord.ActivityType.custom, name='🤓', state='🤓'),
            help_command=None,
            owner_ids=Auth.owners,
            tree_cls=MentionableTree,
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                users=True,
                roles=False,
                replied_user=False,
            ),
        )
        self.logger = logger
        self.logger.remove()
        self.logger.add(stdout, colorize=True, format=Auth.logger)

    def __repr__(self):
        pid = os.getpid()
        active_tasks = len(asyncio.all_tasks())
        unchunked_guilds = len([guild for guild in self.guilds if not guild.chunked])
        return f"<saint PID={pid} tasks={active_tasks} unchunked={unchunked_guilds}>"

    async def setup_hook(self):
        self.pool         = await asyncpg.create_pool(user='postgres', password='001278870', database='factorio', host='localhost')
        self.db           = self.pool
        await self.load_extension("jishaku")
        self.session: ClientSession = self.http._HTTPClient__session
        with open("schema.sql") as file:
            await self.db.execute(file.read())

    async def get_context(self, message: discord.Message, *, cls=None):
        return await super().get_context(message, cls=cls or Context)

    async def on_ready(self):
        self.logger.info("factorio starting...")
        #for file in Path("commands").glob("**/*.py"):
        #    *tree, _ = file.parts
        #    module = ".".join(tree)
        #    await self.load_extension(f"{module}.{file.stem}")
        #    cog_name = next(
        #        name
        #        for name, cog in self.cogs.items()
        #        if cog.__module__ == f"{module}.{file.stem}"
        #    )
        #    self.logger.success(f"Loaded {cog_name}")\

        blacklisted = ['test']

        for category in os.listdir("commands"):
            if category not in blacklisted:
                for com in os.listdir(f"commands/{category}"):
                    if com.endswith(".py"):
                        await self.load_extension(f"commands.{category}.{com[:-3]}")

                        print(f"LOADED  >  {category}.{com}")

        #synced = await self.tree.sync()
       # print(f"Synced: {len(synced)}")
    
        self.logger.success(f"Logged in as {self.user} ({self.user.id})")
        pid = os.getpid()
        active_tasks = len(asyncio.all_tasks())
        unchunked_guilds = len([guild for guild in self.guilds if not guild.chunked])
        self.logger.success(
            f"<saint PID={pid} tasks={active_tasks} unchunked={unchunked_guilds}>"
        )

    async def on_guild_join(self, guild: discord.Guild):
        if not guild.chunked:
            await guild.chunk(cache=True)
        self.logger.info(
            f"Joined guild {guild} ({guild.id}) owned by {guild.owner.global_name} ({guild.owner.id})"
        )

    async def on_guild_remove(self, guild: discord.Guild):
        self.logger.info(f"Left guild {guild} ({guild.id})")

    async def before_invoke(self, ctx, message):
        await self.hierarchy_check(ctx)

    @property
    def members(self):
        return list(self.get_all_members())

    @property
    def channels(self):
        return list(self.get_all_channels())

    @property
    def text_channels(self):
        return list(
            filter(
                lambda channel: isinstance(channel, discord.TextChannel),
                self.get_all_channels(),
            )
        )

    @property
    def voice_channels(self):
        return list(
            filter(
                lambda channel: isinstance(channel, discord.VoiceChannel),
                self.get_all_channels(),
            )
        )

    async def on_command(self, ctx: Context):
        self.logger.info(
            f"{ctx.author} ({ctx.author.id}): {ctx.command.qualified_name} in {ctx.guild} ({ctx.guild.id}) #{ctx.channel} ({ctx.channel.id})"
        )

    async def on_message_edit(self, before, after):
        await self.process_commands(after)
        if before.content == after.content:
            return

    def get_command(self, command: str, module: str = None):
        if command := super().get_command(command):
            if not command.cog_name:
                return command
            if command.cog_name.lower() in ("jishaku", "developer") or command.hidden:
                return None
            if module and command.cog_name.lower() != module.lower():
                return None
            return command

        return None

    def walk_commands(self):
        for command in super().walk_commands():
            if command.cog_name in ("jishaku", "developer") or command.hidden:
                continue
            yield command

    @staticmethod
    async def command_cooldown(ctx: commands.Context):
        if ctx.author.id == ctx.guild.owner_id:
            return True

        blocked = ctx.bot.buckets["guild_commands"]["blocked"]
        if not ctx.bot.get_guild(ctx.guild.id) or ctx.guild.id in blocked:
            return False

        bucket = ctx.bot.buckets["guild_commands"]["cooldown"].get_bucket(ctx.message)
        if retry_after := bucket.update_rate_limit():
            blocked.add(ctx.guild.id)
            lock = ctx.bot.buckets["guild_commands"]["lock"]
            async with lock:
                ego = ctx.bot.get_user(1032330167856668792)
                await ego.send(
                    f"santa is being flooded in {ctx.guild} (`{ctx.guild.id}`) owned by {ctx.guild.owner} (`{ctx.guild.owner_id}`)"
                )
                return False

        return True

    async def on_message(self, message: discord.Message):
        if not self.is_ready() or not message.guild or message.author.bot:
            return

        if message.content == f"<@{self.user.id}>":
            with contextlib.suppress(discord.HTTPException):
                #prefix = await self.get_prefix(message, mention=False)
                await message.reply(f"my prefix is `$`")

        ctx = await self.get_context(message)

        if not ctx.command:
            return
        await self.process_commands(message)

    async def on_error(self, event: str, *args, **kwargs):
        if event.startswith("on_command"):
            return

        error = sys.exc_info()
        if len(args) != 0 and isinstance(args[0], Context):
            ctx = args[0]
            if "Payload Too Large" in str(error[1]):
                return await ctx.warn("The **video** is too large to be sent")

        if event == "on_member_remove" and "top_role" in str(error[1]):  # wock kicked
            return

        self.logger.info(f"{event}: ({error[0].__name__}): {error[1]} | {args}")
        self.logger.exception(error)

    async def get_context(self, message: discord.Message, *, cls=None):
        return await super().get_context(message, cls=cls or Context)

    async def before_invoke(self, ctx):
        await self.hierarchy_check(ctx)

    async def on_command_error(self, ctx, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            invoked_command = ctx.message.content.split()[0]
            await ctx.warn(f"`{invoked_command}` isn't a **command**")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send_help()
        elif isinstance(error, commands.MissingPermissions):
            await ctx.warn(
                f"You're **missing** the `{', '.join(error.missing_permissions)}` permission"
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.warn(
                f"I'm **missing** the `{', '.join(error.missing_permissions)}` permission"
            )
        elif isinstance(error, commands.GuildNotFound):
            await ctx.warn(f"I wasn't able to find that **guild**")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.warn(f"I wasn't able to find that **channel**")
        elif isinstance(error, commands.RoleNotFound):
            await ctx.warn("I wasn't able to find that **role**")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.warn("I wasn't able to find that **member**")
        elif isinstance(error, commands.UserNotFound):
            await ctx.warn("I wasn't able to find that **user**")
        elif isinstance(error, commands.EmojiNotFound):
            await ctx.warn("I wasn't able to find that **emoji**")
        elif isinstance(error, commands.BadUnionArgument):
            parameter = error.param.name
            converters = list()
            for converter in error.converters:
                if name := getattr(converter, "__name__", None):
                    if name == "Literal":
                        converters.extend(
                            [f"`{literal}`" for literal in converter.__args__]
                        )
                    else:
                        converters.append(f"`{name}`")
            if len(converters) > 2:
                fmt = "{}, or {}".format(", ".join(converters[:-1]), converters[-1])
            else:
                fmt = " or ".join(converters)
            await ctx.warn(f"Couldn't convert **{parameter}** into {fmt}")
        elif isinstance(error, commands.BadLiteralArgument):
            parameter = error.param.name
            literals = [f"`{literal}`" for literal in error.literals]
            if len(literals) > 2:
                fmt = "{}, or {}".format(", ".join(literals[:-1]), literals[-1])
            else:
                fmt = " or ".join(literals)
            await ctx.warn(f"Parameter **{parameter}** must be {fmt}")
        elif isinstance(error, commands.BadArgument):
            await ctx.warn(f"{ctx.author.mention}: {error}")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.warn(
                f"This command is on cooldown for **{error.retry_after:.2f}** seconds"
            )
        elif isinstance(error, commands.CommandError):
            await ctx.warn(f"{error}")
        else:
            await ctx.warn("An unknown error occurred. Please try again later")

    async def hierarchy_check(
        self, ctx: Context, user: discord.Member, author: bool = False
    ):
        if isinstance(user, discord.User):
            return True
        elif ctx.guild.me.top_role <= user.top_role:
            raise commands.CommandError(
                f"I'm unable to **{ctx.command.qualified_name}** {user.mention}"
            )
        elif ctx.author.id == user.id and not author:
            raise commands.CommandError(
                f"You're unable to **{ctx.command.qualified_name}** yourself"
            )
        elif ctx.author.id == user.id and author:
            return True
        elif ctx.author.id == ctx.guild.owner_id:
            return True
        elif user.id == ctx.guild.owner_id:
            raise commands.CommandError(
                f"You're unable to **{ctx.command.qualified_name}** the **server owner**"
            )
        elif ctx.author.top_role.is_default():
            raise commands.CommandError(
                f"You're unable to **{ctx.command.qualified_name}** {user.mention} because your **highest role** is {ctx.guild.default_role.mention}"
            )
        elif ctx.author.top_role == user.top_role:
            raise commands.CommandError(
                f"You're unable to **{ctx.command.qualified_name}** {user.mention} because they have the **same role** as you"
            )
        elif ctx.author.top_role < user.top_role:
            raise commands.CommandError(
                f"You're unable to **{ctx.command.qualified_name}** {user.mention} because they have a **higher role** than you"
            )
        else:
            return True


class MemberStrict(commands.MemberConverter):
    async def convert(self, ctx: Context, argument: str):
        member = None
        argument = str(argument)
        if match := regex.DISCORD_ID.match(argument):
            member = ctx.guild.get_member(int(match.group(1)))
        elif match := regex.DISCORD_USER_MENTION.match(argument):
            member = ctx.guild.get_member(int(match.group(1)))

        if not member:
            raise commands.MemberNotFound(argument)
        return member


class Member(commands.MemberConverter):
    async def convert(self, ctx: Context, argument: str):
        member = None
        argument = str(argument)
        if match := regex.DISCORD_ID.match(argument):
            member = ctx.guild.get_member(int(match.group(1)))
        elif match := regex.DISCORD_USER_MENTION.match(argument):
            member = ctx.guild.get_member(int(match.group(1)))
        else:
            member = (
                discord.utils.find(
                    lambda m: m.name.lower() == argument.lower(),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: argument.lower() in m.name.lower(),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.name.lower().startswith(argument.lower()),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.display_name.lower() == argument.lower(),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: argument.lower() in m.display_name.lower(),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.display_name.lower().startswith(argument.lower()),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: str(m).lower() == argument.lower(),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: argument.lower() in str(m).lower(),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: str(m).lower().startswith(argument.lower()),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.name.lower() == argument.lower(),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: argument.lower() in m.name.lower(),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.name.lower().startswith(argument.lower()),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.display_name.lower() == argument.lower(),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: argument.lower() in m.display_name.lower(),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.display_name.lower().startswith(argument.lower()),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: str(m).lower() == argument.lower(),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: argument.lower() in str(m).lower(),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: str(m).lower().startswith(argument.lower()),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
            )
        if not member:
            raise commands.MemberNotFound(argument)
        return member


class MemberStrict(commands.MemberConverter):
    async def convert(self, ctx: Context, argument: str):
        member = None
        argument = str(argument)
        if match := regex.DISCORD_ID.match(argument):
            member = ctx.guild.get_member(int(match.group(1)))
        elif match := regex.DISCORD_USER_MENTION.match(argument):
            member = ctx.guild.get_member(int(match.group(1)))

        if not member:
            raise commands.MemberNotFound(argument)
        return member


class Member(commands.MemberConverter):
    async def convert(self, ctx: Context, argument: str):
        member = None
        argument = str(argument)
        if match := regex.DISCORD_ID.match(argument):
            member = ctx.guild.get_member(int(match.group(1)))
        elif match := regex.DISCORD_USER_MENTION.match(argument):
            member = ctx.guild.get_member(int(match.group(1)))
        else:
            member = (
                discord.utils.find(
                    lambda m: m.name.lower() == argument.lower(),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: argument.lower() in m.name.lower(),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.name.lower().startswith(argument.lower()),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.display_name.lower() == argument.lower(),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: argument.lower() in m.display_name.lower(),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.display_name.lower().startswith(argument.lower()),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: str(m).lower() == argument.lower(),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: argument.lower() in str(m).lower(),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: str(m).lower().startswith(argument.lower()),
                    sorted(
                        ctx.channel.members,
                        key=lambda m: int(
                            m.discriminator
                            if not isinstance(m, discord.ThreadMember)
                            else 0
                        ),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.name.lower() == argument.lower(),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: argument.lower() in m.name.lower(),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.name.lower().startswith(argument.lower()),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.display_name.lower() == argument.lower(),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: argument.lower() in m.display_name.lower(),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: m.display_name.lower().startswith(argument.lower()),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: str(m).lower() == argument.lower(),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: argument.lower() in str(m).lower(),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
                or discord.utils.find(
                    lambda m: str(m).lower().startswith(argument.lower()),
                    sorted(
                        ctx.guild.members,
                        key=lambda m: int(m.discriminator),
                        reverse=False,
                    ),
                )
            )
        if not member:
            raise commands.MemberNotFound(argument)
        return member


class User(commands.UserConverter):
    async def convert(self, ctx: Context, argument: str):
        user = None
        argument = str(argument)
        if match := regex.DISCORD_ID.match(argument):
            user = ctx.bot.get_user(int(match.group(1)))
            if not user:
                user = await ctx.bot.fetch_user(int(match.group(1)))
        elif match := regex.DISCORD_USER_MENTION.match(argument):
            user = ctx.bot.get_user(int(match.group(1)))
            if not user:
                user = await ctx.bot.fetch_user(int(match.group(1)))
        else:
            user = (
                discord.utils.find(
                    lambda u: u.name.lower() == argument.lower(), ctx.bot.users
                )
                or discord.utils.find(
                    lambda u: argument.lower() in u.name.lower(), ctx.bot.users
                )
                or discord.utils.find(
                    lambda u: u.name.lower().startswith(argument.lower()),
                    ctx.bot.users,
                )
                or discord.utils.find(
                    lambda u: str(u).lower() == argument.lower(), ctx.bot.users
                )
                or discord.utils.find(
                    lambda u: argument.lower() in str(u).lower(), ctx.bot.users
                )
                or discord.utils.find(
                    lambda u: str(u).lower().startswith(argument.lower()),
                    ctx.bot.users,
                )
            )
        if not user:
            raise commands.UserNotFound(argument)
        return user


class Role(commands.RoleConverter):
    async def convert(self, ctx: Context, argument: str):
        role = None
        argument = str(argument)
        if match := regex.DISCORD_ID.match(argument):
            role = ctx.guild.get_role(int(match.group(1)))
        elif match := regex.DISCORD_ROLE_MENTION.match(argument):
            role = ctx.guild.get_role(int(match.group(1)))
        else:
            role = (
                discord.utils.find(
                    lambda r: r.name.lower() == argument.lower(), ctx.guild.roles
                )
                or discord.utils.find(
                    lambda r: argument.lower() in r.name.lower(), ctx.guild.roles
                )
                or discord.utils.find(
                    lambda r: r.name.lower().startswith(argument.lower()),
                    ctx.guild.roles,
                )
            )
        if not role or role.is_default():
            raise commands.RoleNotFound(argument)
        return role

    async def manageable(self, ctx: Context, role: discord.Role, booster: bool = False):
        if role.managed and not booster:
            raise commands.CommandError(f"You're unable to manage {role.mention}")
        elif not role.is_assignable() and not booster:
            raise commands.CommandError(f"I'm unable to manage {role.mention}")
        elif role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner.id:
            raise commands.CommandError(f"You're unable to manage {role.mention}")

        return True

    async def dangerous(self, ctx: Context, role: discord.Role, _: str = "manage"):
        if (
            permissions := list(
                filter(
                    lambda permission: getattr(role.permissions, permission),
                    DANGEROUS_PERMISSIONS,
                )
            )
        ) and not ctx.author.id == ctx.guild.owner_id:
            raise commands.CommandError(
                f"You're unable to {_} {role.mention} because it has the `{permissions[0]}` permission"
            )

        return False


class Roles(commands.RoleConverter):
    async def convert(self, ctx: Context, argument: str):
        roles = []
        argument = str(argument)
        for role in argument.split(","):
            try:
                role = await Role().convert(ctx, role.strip())
                if role not in roles:
                    roles.append(role)
            except commands.RoleNotFound:
                continue

        if not roles:
            raise commands.RoleNotFound(argument)
        return roles

    async def manageable(
        self, ctx: Context, roles: list[discord.Role], booster: bool = False
    ):
        for role in roles:
            await Role().manageable(ctx, role, booster)

        return True

    async def dangerous(
        self, ctx: Context, roles: list[discord.Role], _: str = "manage"
    ):
        for role in roles:
            await Role().dangerous(ctx, role, _)

        return False


DANGEROUS_PERMISSIONS = [
    "administrator",
    "kick_members",
    "ban_members",
    "manage_guild",
    "manage_roles",
    "manage_channels",
    "manage_emojis",
    "manage_webhooks",
    "manage_nicknames",
    "mention_everyone",
]


class Time:
    def __init__(self, seconds: int):
        self.seconds: int = seconds
        self.minutes: int = (self.seconds % 3600) // 60
        self.hours: int = (self.seconds % 86400) // 3600
        self.days: int = self.seconds // 86400
        self.weeks: int = self.days // 7
        self.delta: timedelta = timedelta(seconds=self.seconds)

    def __str__(self):
        return humanize.naturaldelta(self.delta)


class TimeConverter(commands.Converter):
    def _convert(self, argument: str):
        argument = str(argument)
        units = dict(
            s=1,
            m=60,
            h=3600,
            d=86400,
            w=604800,
        )
        if matches := regex.TIME.findall(argument):
            seconds = 0
            for time, unit in matches:
                try:
                    seconds += units[unit] * int(time)
                except KeyError:
                    raise commands.CommandError(f"Invalid time unit `{unit}`")

            return seconds

    async def convert(self, ctx: Context, argument: str):
        if seconds := self._convert(argument):
            return Time(seconds)
        else:
            raise commands.CommandError("Please **specify** a valid time - `1h 30m`")


class Location(commands.Converter):
    async def convert(self, ctx: Context, argument: str):
        argument = str(argument)
        async with ctx.typing():
            response = await ctx.bot.session.get(
                "https://api.weatherapi.com/v1/timezone.json",
                params=dict(key=Auth.weather, q=argument),
            )

            if response.status == 200:
                data = await response.json()
                return data.get("location")
            else:
                raise commands.CommandError(f"Location **{argument}** not found")


class State(commands.Converter):
    async def convert(self, ctx: Context, argument: str):
        argument = str(argument)
        if argument.lower() in ("on", "yes", "true", "enable"):
            return True
        elif argument.lower() in ("off", "no", "none", "null", "false", "disable"):
            return False
        else:
            raise commands.CommandError(
                "Please **specify** a valid state - `on` or `off`"
            )


class Emoji:
    def __init__(self, name: str, url: str, **kwargs):
        self.name: str = name
        self.url: str = url
        self.id: int = int(kwargs.get("id", 0))
        self.animated: bool = kwargs.get("animated", False)

    async def read(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                return await response.read()

    def __str__(self):
        if self.id:
            return f"<{'a' if self.animated else ''}:{self.name}:{self.id}>"
        else:
            return self.name

    def __repr__(self):
        return f"<helpers.yeehaw.Emoji name={self.name!r} url={self.url!r}>"


class EmojiFinder(commands.Converter):
    async def convert(self, ctx: Context, argument: str):
        argument = str(argument)
        if match := regex.DISCORD_EMOJI.match(argument):
            return Emoji(
                match.group("name"),
                "https://cdn.discordapp.com/emojis/"
                + match.group("id")
                + (".gif" if match.group("animated") else ".png"),
                id=int(match.group("id")),
                animated=bool(match.group("animated")),
            )
        else:
            characters = list()
            for character in argument:
                characters.append(str(hex(ord(character)))[2:])
            if len(characters) == 2:
                if "fe0f" in characters:
                    characters.remove("fe0f")
            if "20e3" in characters:
                characters.remove("20e3")

            hexcode = "-".join(characters)
            url = "https://cdn.notsobot.com/twemoji/512x512/" + hexcode + ".png"
            response = await ctx.bot.session.get(url)
            if response.status == 200:
                return Emoji(argument, url)

        raise commands.EmojiNotFound(argument)


class StickerFinder(commands.Converter):
    async def convert(self, ctx: Context, argument: str):
        argument = str(argument)
        try:
            message = await commands.MessageConverter().convert(ctx, argument)
        except commands.MessageNotFound:
            pass
        else:
            if message.stickers:
                sticker = await message.stickers[0].fetch()
                if isinstance(sticker, discord.StandardSticker):
                    raise commands.CommandError("Sticker **must** be a nitro sticker")
                return sticker
            else:
                raise commands.CommandError(
                    f"[**Message**]({message.jump_url}) doesn't contain a sticker"
                )

        sticker = discord.utils.get(ctx.guild.stickers, name=argument)
        if not sticker:
            raise commands.CommandError("That **sticker** doesn't exist in this server")
        return sticker

    async def search(ctx: Context):
        if ctx.message.stickers:
            sticker = await ctx.message.stickers[0].fetch()
        elif ctx.replied_message:
            if ctx.replied_message.stickers:
                sticker = await ctx.replied_message.stickers[0].fetch()
            else:
                raise commands.CommandError(
                    f"[**Message**]({ctx.replied_message.jump_url}) doesn't contain a sticker"
                )
        else:
            raise commands.CommandError("Please **specify** a sticker")

        if isinstance(sticker, discord.StandardSticker):
            raise commands.CommandError("Sticker **must** be a nitro sticker")
        return sticker


class PatchCore:
    def __init__(self):
        super().__init__()

    async def permissions(self):
        _permissions = list()

        if self.checks:
            for check in self.checks:
                if "has_permissions" in str(check):
                    return await check(0)

        return _permissions

    async def invoke(self, ctx: Context, /) -> None:
        await self.prepare(ctx)

        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        injected = core.hooked_wrapped_callback(self, ctx, self.callback)  # type: ignore
        await injected(*ctx.args, **ctx.kwargs)  # type: ignore


core.Command.invoke = PatchCore.invoke
core.Command.permissions = PatchCore.permissions

from discord import interactions


class PatchInteraction:
    def __init__(self):
        super().__init__()

    async def neutral(self, message: str, **kwargs):
        # embed = discord.Embed(
        #     color=Colors.neutral,
        #     description=f"{kwargs.pop('emoji', None) or ''} {message}",
        # )
        if kwargs.pop("followup", True):
            return await self.followup.send(f"{message}", ephemeral=True, **kwargs)
        else:
            return await self.response.send_message(
                f"{message}".lower(), ephemeral=True, **kwargs
            )

    async def approve(self, message: str, **kwargs):
        # embed = discord.Embed(
        #     color=Colors.approve,
        #     description=f"{kwargs.pop('emoji', None) or ''} {message}",
        # )
        if kwargs.pop("followup", True):
            return await self.followup.send(f"{message}", ephemeral=True, **kwargs)
        else:
            return await self.response.send_message(
                f"{message}".lower(), ephemeral=True, **kwargs
            )

    async def warn(self, message: str, **kwargs):
        # embed = discord.Embed(
        #     color=Colors.warn,
        #     description=f"{kwargs.pop('emoji', None) or ''} {message}",
        # )
        if kwargs.pop("followup", True):
            return await self.followup.send(f"{message}", ephemeral=True, **kwargs)
        else:
            return await self.response.send_message(
                f"{message}".lower(), ephemeral=True, **kwargs
            )


interactions.Interaction.neutral = PatchInteraction.neutral
interactions.Interaction.approve = PatchInteraction.approve
