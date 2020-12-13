from typing import List
import discord
from discord.ext import commands


def has_permissions():
    def predicate(ctx):
        return ctx.author.guild_permissions.manage_messages is True

    return commands.check(predicate)


before_invites = {}
format_date = "%b %d, %Y"
format_time = "%I:%M %p"
format_datetime = "%b %d, %Y  %I:%M %p"


def add_invite(invite: discord.Invite):
    before_invites[invite.id] = invite


def get_invite(invite_id: str) -> discord.Invite:
    try:
        return before_invites[invite_id]
    except KeyError:
        raise Exception("No Invite Found")


def update_invite(invite: discord.Invite):
    d = {invite.id: invite}
    before_invites.update(d)


def remove_invite(invite: discord.Invite):
    try:
        before_invites.pop(invite.id)
    except KeyError:
        raise Exception("No Invite Found")


async def add_all_invites(bot: discord.Client):
    for guild in bot.guilds:
        await add_all_guild_invites(guild)


async def add_all_guild_invites(guild: discord.Guild):
    for invite in await guild.invites():
        add_invite(invite)


async def remove_all_guild_invites(guild: discord.Guild):
    for invite in await guild.invites():
        remove_invite(invite)


def message_splitter(content: str, cap: int) -> List:
    if len(content) == 0:
        raise ValueError("Message has no contents")
    elif len(content) <= cap:
        return [content]
    else:
        prt_1 = content[:cap]
        prt_2 = content[cap:]
        return [prt_1, prt_2]


def field_message_splitter(
    embed: discord.Embed, content: str, content_type: str
) -> discord.Embed:
    if len(content) == 0:
        embed.add_field(name=f"**{content_type}**", value=f"`Blank`", inline=False)
    else:
        embed.add_field(
            name=f"**{content_type}**", value=f"{content[:1024]} ", inline=False
        )
    if len(content) > 1024:
        embed.add_field(name=f"Continued", value=f"{content[1024:]}")
    return embed
