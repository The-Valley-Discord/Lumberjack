import discord
from discord.ext import commands

from database import get_log_by_id, add_guild, init_db, delete_old_db_messages, get_old_lumberjack_messages, delete_lumberjack_messages_from_db
from helpers import add_invite, remove_invite
from logger import Logger
from member_log import MemberLog
from tracker import Tracker

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="lum.", intents=intents)
bot.add_cog(MemberLog(bot))
bot.add_cog(Tracker(bot))
bot.add_cog(Logger(bot))

delete_old_db_messages()

@bot.event
async def on_ready():
    init_db()
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, name="with ten thousand eyes."
        )
    )
    for guild in bot.guilds:
        gld = get_log_by_id(guild.id)
        if gld is None:
            new_guild = (guild.id, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            add_guild(new_guild)
        else:
            pass
        for invite in await guild.invites():
            add_invite(invite)
    print("Bot is ready.")


@bot.event
async def on_guild_join(guild):
    for invite in await guild.invites():
        add_invite(invite)
        gld = get_log_by_id(guild.id)
        if gld is None:
            new_guild = (guild.id, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            add_guild(new_guild)
        else:
            pass


@bot.event
async def on_guild_remove(guild):
    for invite in await guild.invites():
        remove_invite(invite)


@bot.event
async def on_invite_create(invite):
    add_invite(invite)


@bot.event
async def on_invite_delete(invite):
    remove_invite(invite)


async def delete_old_lumberjack_messages():
    messages = get_old_lumberjack_messages()
    for message_id in messages:
        message = await bot.user.fetch_message(message_id)
        await message.delete()
        delete_lumberjack_messages_from_db(message_id)


@bot.event
async def on_message_delete(payload):
    delete_old_db_messages()
    await delete_old_lumberjack_messages()



@bot.command()
async def ping(ctx):
    embed = discord.Embed(
        title="**Ping**", description=f"Pong! {round(bot.latency * 1000)}ms"
    )
    embed.set_author(name=f"{bot.user.name}", icon_url=bot.user.avatar_url)
    await ctx.send(embed=embed)


bot.remove_command("help")


@bot.command(aliases=["help"])
async def _help(ctx):
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
