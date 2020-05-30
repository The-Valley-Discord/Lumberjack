from discord.ext import commands

import database


def has_permissions():
    def predicate(ctx):
        return ctx.author.guild_permissions.manage_messages is True

    return commands.check(predicate)


before_invites = {}
format_date = "%b %d, %Y"
format_time = "%I:%M %p"
format_datetime = "%b %d, %Y  %I:%M %p"


def add_invite(invite):
    before_invites[invite.id] = invite


def get_invite(invite_id):
    return before_invites[invite_id]


def update_invite(invite):
    d = {invite.id: invite}
    before_invites.update(d)


def remove_invite(invite):
    before_invites.pop(invite.id)


def set_log_channel(log_type, guild_id, channel_id):
    if log_type == "join":
        database.set_join_channel(guild_id, channel_id)
        return "Join"
    elif log_type == "leave":
        database.set_leave_channel(guild_id, channel_id)
        return "Leave"
    elif log_type == "delete":
        database.set_delete_channel(guild_id, channel_id)
        return "Delete"
    elif log_type == "bulk_delete":
        database.set_bulk_delete_channel(guild_id, channel_id)
        return "Bulk Delete"
    elif log_type == "edit":
        database.set_edit_channel(guild_id, channel_id)
        return "Edit"
    elif log_type == "username":
        database.set_username_channel(guild_id, channel_id)
        return "Username"
    elif log_type == "nickname":
        database.set_nickname_channel(guild_id, channel_id)
        return "Nickname"
    elif log_type == "avatar":
        database.set_avatar_channel(guild_id, channel_id)
        return "Avatar"
    # broken member tracker
    # elif log_type == "stats":
    #    database.set_stats_channel(guild_id, channel_id)
    #    return "Stats"
    elif log_type == "ljlog":
        database.set_ljlog_channel(guild_id, channel_id)
        return "Lumberjack Logs"
    else:
        return ""


def message_splitter(content, cap):
    if len(content) == 0:
        pass
    elif len(content) <= cap:
        return [content]
    else:
        prt_1 = content[:cap]
        prt_2 = content[cap:]
        return [prt_1, prt_2]


def return_time_delta_string(account_age):
    time_string = ""
    if account_age.days > 7:
        return time_string
    if 1 < account_age.days < 7:
        time_string += f"{account_age.days} days "
    elif account_age.days == 1:
        time_string += f"{account_age.days} day "
    if 1 < (account_age.seconds // 3600):
        time_string += f"{account_age.seconds // 3600} hours "
    elif (account_age.seconds // 3600) == 1:
        time_string += f"{account_age.seconds // 3600} hour "
    if 1 < (account_age.seconds % 3600 // 60):
        time_string += f"{(account_age.seconds % 3600) // 60} minutes "
    elif 1 == (account_age.seconds % 3600 // 60):
        time_string += f"{(account_age.seconds % 3600) // 60} minute "
    if account_age.days == 0 and 1 < ((account_age.seconds % 3600) % 60):
        time_string += f"{(account_age.seconds % 3600) % 60} seconds "
    elif account_age.days == 0:
        time_string += f"{(account_age.seconds % 3600) % 60} second "
    return time_string
