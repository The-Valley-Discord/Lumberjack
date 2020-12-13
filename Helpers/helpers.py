from datetime import timedelta
from typing import List

import discord
from discord.ext import commands

from Helpers.database import Database


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


def set_log_channel(log_type: str, guild_id: int, channel_id: int, db: Database) -> str:
    logs = db.get_log_by_id(guild_id)
    log_return = ""
    if log_type == "join":
        logs.join_id = channel_id
        log_return = "Join"
    elif log_type == "leave":
        logs.leave_id = channel_id
        log_return = "Leave"
    elif log_type == "delete":
        logs.delete_id = channel_id
        log_return = "Delete"
    elif log_type == "bulk_delete":
        logs.delete_bulk = channel_id
        log_return = "Bulk Delete"
    elif log_type == "edit":
        logs.edit = channel_id
        log_return = "Edit"
    elif log_type == "username":
        logs.username = channel_id
        log_return = "Username"
    elif log_type == "nickname":
        logs.nickname = channel_id
        log_return = "Nickname"
    elif log_type == "avatar":
        logs.avatar = channel_id
        log_return = "Avatar"
    elif log_type == "ljlog":
        logs.lj_id = channel_id
        log_return = "Lumberjack Logs"
    db.update_log_channels(logs)
    if len(log_return) > 0:
        return log_return
    else:
        raise ValueError("No Log of that type.")


def message_splitter(content: str, cap: int) -> List:
    if len(content) == 0:
        raise ValueError("Message has no contents")
    elif len(content) <= cap:
        return [content]
    else:
        prt_1 = content[:cap]
        prt_2 = content[cap:]
        return [prt_1, prt_2]
