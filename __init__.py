import logging
import sqlite3
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands.context import Context

from Cogs.cleanup import Cleanup
from Cogs.logger import Logger
from Cogs.member_log import MemberLog
from Cogs.tracker import Tracker
from Helpers.database import Database
from Helpers.helpers import (
    add_invite,
    remove_invite,
    add_all_invites,
    add_all_guild_invites,
    remove_all_guild_invites,
    get_invite,
)

logs = logging.getLogger("Lumberjack")
logs.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="Logs/lj.log", encoding="utf-8", mode="a+")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logs.addHandler(handler)

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="lum.",
    intents=intents,
    activity=discord.Activity(
        type=discord.ActivityType.watching, name="with ten thousand eyes."
    ),
)

if __name__ == "__main__":
    with open("schema.sql", "r") as schema_file:
        db: Database = Database(
            sqlite3.connect(
                "log.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            ),
            logs,
            schema_file,
        )
    bot.add_cog(MemberLog(bot, logs, db))
    bot.add_cog(Tracker(bot, logs, db))
    bot.add_cog(Logger(bot, logs, db))
    bot.add_cog(Cleanup(bot, logs, db))
    db.add_all_guilds(bot)
    logs.info(f"Bot was started at: {datetime.utcnow()}")


@bot.event
async def on_ready():
    print("Bot is ready.")
    await add_all_invites(bot)


@bot.event
async def on_guild_join(guild: discord.Guild):
    await add_all_guild_invites(guild)
    db.add_guild(guild)


@bot.event
async def on_guild_remove(guild: discord.Guild):
    await remove_all_guild_invites(guild)


@bot.event
async def on_invite_create(invite: discord.Invite):
    add_invite(invite)


@bot.event
async def on_invite_delete(invite: discord.Invite):
    invite: discord.Invite = get_invite(invite.id)
    if invite.uses + 1 == invite.max_uses:
        gd = db.get_log_by_id(invite.guild.id)
        log = bot.get_channel(gd.join_id)
        embed = discord.Embed(
            description=f"Invite Id: {invite.id}\n" f"Created By: {invite.inviter}",
            color=0x009DFF,
        )
        embed.set_author(name="Invite Deleted", icon_url=bot.user.avatar_url)
        embed.timestamp = datetime.utcnow()
        db.add_lumberjack_message(await log.send(embed=embed))
    remove_invite(invite)


@bot.command()
async def ping(ctx: Context):
    embed: discord.Embed = discord.Embed(
        title="**Ping**", description=f"Pong! {round(bot.latency * 1000)}ms"
    )
    embed.set_author(name=f"{bot.user.name}", icon_url=bot.user.avatar_url)
    await ctx.send(embed=embed)


bot.remove_command("help")


@bot.command(aliases=["help"])
async def _help(ctx: Context):
    await ctx.send(
        "`lum.ping` to check bot responsiveness\n"
        '`lum.log <log type> <"here" or channel mention/id>` will change what channel a log appears in\n'
        "`lum.clear <log type>` will disable a log\n"
        "`lum.track <user mention/id> <time in d h or m> <channel mention/id>` "
        "to place a tracker on someone\n"
        "`lum.untrack <user mention/id>` will remove a tracker"
    )


with open("token", "r") as f:
    bot.run(f.readline().strip())
