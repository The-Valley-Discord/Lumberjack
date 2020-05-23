import discord
from discord.ext import commands

from database import get_log_by_id, add_guild
from helpers import add_invite, remove_invite

bot = commands.Bot(command_prefix="lum.")


@bot.event
async def on_ready():
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
            # x = [invite.url, invite.uses, invite.inviter]
            add_invite(invite=invite)
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


@bot.command()
async def ping(ctx):
    embed = discord.Embed(
        title="**Ping**", description=f"Pong! {round(bot.latency * 1000)}ms"
    )
    embed.set_author(name=f"{bot.user.name}", icon_url=bot.user.avatar_url)
    await ctx.send(embed=embed)


with open("token", "r") as f:
    bot.run(f.readline().strip())
