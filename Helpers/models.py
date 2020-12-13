from datetime import datetime, timedelta
from typing import List


class DBGuild(object):
    def __init__(
        self,
        guild_id: int,
        join_id: int,
        leave_id: int,
        delete_id: int,
        delete_bulk: int,
        edit: int,
        username: int,
        nickname: int,
        avatar: int,
        stat_member: int,
        lj_id: int,
    ):
        self.id = guild_id
        self.join_id = join_id
        self.leave_id = leave_id
        self.delete_id = delete_id
        self.delete_bulk = delete_bulk
        self.edit = edit
        self.username = username
        self.nickname = nickname
        self.avatar = avatar
        self.stat_member = stat_member
        self.lj_id = lj_id

    def __str__(self) -> str:
        return str(self.id)


class DBAuthor(object):
    def __init__(self, author_id: int, name: str, display_name: str, pfp: str):
        self.id = author_id
        self.name = name
        self.display_name = display_name
        self.pfp = pfp


class DBChannel(object):
    def __init__(self, channel_id, channel_name):
        self.id = channel_id
        self.name = channel_name


class DBMessage:
    def __init__(
        self: object,
        message_id: int,
        author: DBAuthor,
        channel: DBChannel,
        guild: DBGuild,
        clean_content: str,
        created_at: datetime,
        attachments: List,
    ):
        self.id = message_id
        self.author = author
        self.channel = channel
        self.guild = guild
        self.clean_content = clean_content
        self.created_at = created_at
        self.attachments = attachments


class Tracking:
    def __init__(
        self,
        user_id: int,
        username: str,
        guild_id: int,
        channel_id: int,
        end_time: int,
        mod_id: int,
        mod_name: str,
    ):
        self.user_id = user_id
        self.username = username
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.end_time = end_time
        self.mod_id = mod_id
        self.mod_name = mod_name


class LJMessage:
    def __init__(self, message_id: int, channel_id: int, created_at: datetime):
        self.message_id = message_id
        self.channel_id = channel_id
        self.created_at = created_at


class BetterTimeDelta(timedelta):
    def __str__(self):
        time_string = ""
        if 1 < self.days:
            time_string += f"{self.days} days "
        elif self.days == 1:
            time_string += f"{self.days} day "
        if 1 < (self.seconds // 3600):
            time_string += f"{self.seconds // 3600} hours "
        elif (self.seconds // 3600) == 1:
            time_string += f"{self.seconds // 3600} hour "
        if 1 < (self.seconds % 3600 // 60):
            time_string += f"{(self.seconds % 3600) // 60} minutes "
        elif 1 == (self.seconds % 3600 // 60):
            time_string += f"{(self.seconds % 3600) // 60} minute "
        if self.days == 0 and 1 < ((self.seconds % 3600) % 60):
            time_string += f"{(self.seconds % 3600) % 60} seconds "
        elif self.days == 0:
            time_string += f"{(self.seconds % 3600) % 60} second "
        return time_string
