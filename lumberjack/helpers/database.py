import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import List, TextIO

import discord

from lumberjack.helpers.models import (
    DBMessage,
    DBAuthor,
    DBChannel,
    DBGuild,
    Tracking,
    LJMessage,
)


class Database:
    def __init__(self, conn: sqlite3.Connection, logs: logging, schema_file: TextIO):
        self.conn = conn
        self.logs = logs
        self.schema = schema_file.read()
        try:
            conn.executescript(self.schema)
            logs.info("Database initialized from schema.sql")
        except sqlite3.Error:
            logs.error("Failed creating database from schema.sql")

    def add_message(self, message: discord.Message):
        attachments = [f"{attachment.proxy_url}" for attachment in message.attachments]
        attachment_bool = len(attachments) > 0
        if attachment_bool:
            self.add_attachment(message.id, attachments)
        values = (
            message.id,
            message.author.id,
            f"{message.author.name}#{message.author.discriminator}",
            message.author.display_name,
            message.channel.id,
            message.channel.name,
            message.guild.id,
            message.clean_content,
            message.created_at,
            f"{message.author.display_avatar.url}",
            attachment_bool,
        )
        sql = """INSERT INTO messages (id,author,authorname,authordisplayname,channelid,channelname,guildid,
        clean_content,created_at,pfp,attachments) VALUES(?,?,?,?,?,?,?,?,?,?,?) """
        try:
            self.conn.execute(sql, values)
            self.conn.commit()
        except sqlite3.Error:
            self.logs.error(
                "Error entering following message into database: " + str(values)
            )

    def get_msg_by_id(self, message_id: int) -> DBMessage:
        msg = self.conn.execute(
            "SELECT * FROM messages WHERE id=:id", {"id": message_id}
        ).fetchone()
        if msg is None:
            raise ValueError("Retrieved message not in database.")
        author = DBAuthor(msg[1], msg[2], msg[3], msg[9])
        channel = DBChannel(msg[4], msg[5])
        guild = self.get_log_by_id(msg[6])
        attachments = self.get_att_by_id(msg[0])
        return DBMessage(
            msg[0],
            author,
            channel,
            guild,
            msg[7],
            attachments,
        )

    def update_msg(self, message_id: int, content: str):
        self.conn.execute(
            """UPDATE messages SET clean_content = :clean_content
                    WHERE id = :id""",
            {"id": message_id, "clean_content": content},
        )
        self.conn.commit()

    def get_att_by_id(self, message_id: int) -> List:
        attachments_tuple: List[tuple] = self.conn.execute(
            "SELECT * FROM attachment_urls WHERE message_id=:id", {"id": message_id}
        ).fetchall()
        attachments: List[str] = []
        for attachment in attachments_tuple:
            attachments.append(attachment[1])
        return attachments

    def add_attachment(self, message_id: int, attachments: List[str]):
        for attachment in attachments:
            try:
                self.conn.execute(
                    "INSERT INTO attachment_urls VALUES (:message_id, :attachment)",
                    {"message_id": message_id, "attachment": attachment},
                )
                self.conn.commit()
            except sqlite3.Error:
                logging.error(
                    f"Failed to add attachment of id: {message_id} to the database: {attachment}"
                )

    def delete_old_db_messages(self):
        old_date = datetime.now(timezone.utc) - timedelta(days=31)
        try:
            self.conn.execute(
                "DELETE FROM messages WHERE DATETIME(created_at) < :timestamp",
                {"timestamp": old_date},
            )
            latest_message = self.conn.execute(
                "SELECT min(id) FROM messages"
            ).fetchone()
            self.conn.execute(
                "DELETE FROM attachment_urls where message_id < :id",
                {"id": latest_message[0]},
            )
            self.conn.commit()
        except sqlite3.Error:
            self.logs.error("Error deleting old messages from database")

    def add_all_guilds(self, guilds: List[discord.Guild]):
        for guild in guilds:
            try:
                self.get_log_by_id(guild.id)
            except ValueError:
                self.add_guild(guild)

    def add_guild(self, guild: discord.Guild):
        new_guild = (guild.id, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        sql = """INSERT INTO log_channels (guildid,joinid,leaveid,deleteid,delete_bulk,edit,username,nickname,
        avatar,stat_member) VALUES(?,?,?,?,?,?,?,?,?,?) """
        try:
            self.conn.execute(sql, new_guild)
            self.conn.commit()
        except sqlite3.Error:
            self.logs.error(
                "Failed to enter following guild into database: " + str(guild)
            )

    def get_log_by_id(self, guild_id: int) -> DBGuild:
        gld = self.conn.execute(
            "SELECT * FROM log_channels WHERE guildid=:id", {"id": guild_id}
        ).fetchone()
        if gld is None:
            raise ValueError("Guild not in database")
        return DBGuild(
            gld[0],
            gld[1],
            gld[2],
            gld[3],
            gld[4],
            gld[5],
            gld[6],
            gld[7],
            gld[8],
            gld[9],
            gld[10],
        )

    def update_log_channels(self, guild: DBGuild):
        try:
            self.conn.execute(
                "UPDATE log_channels "
                "SET joinid=:joinid, "
                "leaveid=:leaveid, "
                "deleteid=:deleteid, "
                "delete_bulk=:delete_bulk, "
                "edit=:edit, "
                "username=:username, "
                "nickname=:nickname, "
                "avatar=:avatar, "
                "stat_member=:stats, "
                "ljid=:ljid "
                "WHERE guildid=:guildid",
                {
                    "joinid": guild.join_id,
                    "leaveid": guild.leave_id,
                    "deleteid": guild.delete_id,
                    "delete_bulk": guild.delete_bulk,
                    "edit": guild.edit,
                    "username": guild.username,
                    "nickname": guild.nickname,
                    "avatar": guild.avatar,
                    "stats": guild.stat_member,
                    "ljid": guild.lj_id,
                    "guildid": guild.id,
                },
            )
            self.conn.commit()
        except sqlite3.Error:
            self.logs.error(f"Failed to update log channel of guild: {guild}")

    def set_log_channel(self, log_type: str, guild_id: int, channel_id: int) -> str:
        log_channels = self.get_log_by_id(guild_id)
        log_return = ""
        if log_type == "join":
            log_channels.join_id = channel_id
            log_return = "Join"
        elif log_type == "leave":
            log_channels.leave_id = channel_id
            log_return = "Leave"
        elif log_type == "delete":
            log_channels.delete_id = channel_id
            log_return = "Delete"
        elif log_type == "bulk_delete":
            log_channels.delete_bulk = channel_id
            log_return = "Bulk Delete"
        elif log_type == "edit":
            log_channels.edit = channel_id
            log_return = "Edit"
        elif log_type == "username":
            log_channels.username = channel_id
            log_return = "Username"
        elif log_type == "nickname":
            log_channels.nickname = channel_id
            log_return = "Nickname"
        elif log_type == "avatar":
            log_channels.avatar = channel_id
            log_return = "Avatar"
        elif log_type == "ljlog":
            log_channels.lj_id = channel_id
            log_return = "Lumberjack Logs"
        self.update_log_channels(log_channels)
        if len(log_return) > 0:
            return log_return
        else:
            raise ValueError("Log type not found.")

    def get_tracked_by_id(self, guild_id: int, user_id: int) -> Tracking:
        values = (guild_id, user_id)
        sql = """SELECT * FROM tracking WHERE guildid=? AND userid=?"""
        tracked = self.conn.execute(sql, values).fetchone()
        if tracked is not None:
            return Tracking(
                tracked[0],
                tracked[1],
                tracked[2],
                tracked[3],
                tracked[4],
                tracked[5],
                tracked[6],
            )
        raise ValueError("User not being tracked.")

    def get_all_expired_trackers(self) -> List[Tracking]:
        trackers = []
        try:
            trackers = self.conn.execute(
                "SELECT * FROM tracking WHERE DATETIME(endtime) < :time",
                {"time": datetime.now(timezone.utc)},
            ).fetchall()
        except sqlite3.DatabaseError:
            pass
        finally:
            objectified_trackers = []
            for tracker in trackers:
                objectified_trackers.append(
                    Tracking(
                        tracker[0],
                        tracker[1],
                        tracker[2],
                        tracker[3],
                        tracker[4],
                        tracker[5],
                        tracker[6],
                    )
                )
            return objectified_trackers

    def add_tracker(self, new_tracker: Tracking):
        tracker = (
            new_tracker.user_id,
            new_tracker.username,
            new_tracker.guild_id,
            new_tracker.channel_id,
            new_tracker.end_time,
            new_tracker.mod_id,
            new_tracker.mod_name,
        )
        try:
            self.get_tracked_by_id(new_tracker.guild_id, new_tracker.user_id)
        except ValueError:
            sql = """INSERT INTO tracking (userid,username,guildid,channelid,endtime,modid,modname) 
            VALUES(?,?,?,?,?,?,?) """
            try:
                self.conn.execute(sql, tracker)
                self.conn.commit()
            except sqlite3.Error:
                self.logs.error("Failed to enter tracker into database")
                raise Exception("Failed to enter tracker into database")
        else:
            try:
                self.conn.execute(
                    """UPDATE tracking SET endtime = :endtime,
                                     modid = :modid,
                                     modname = :modname,
                                     channelid = :channelid
                                    WHERE userid = :userid
                                    AND guildid = :guildid""",
                    {
                        "endtime": tracker[4],
                        "modid": tracker[5],
                        "modname": tracker[6],
                        "channelid": tracker[3],
                        "userid": tracker[0],
                        "guildid": tracker[2],
                    },
                )
            except sqlite3.Error:
                self.logs.error("Failed to update tracker into database")
                raise Exception("Failed to update tracker into database")

    def remove_tracker(self, guild_id: int, user_id: int):
        tracker_to_remove = (guild_id, user_id)
        sql = """DELETE from tracking WHERE guildid = ? AND userid = ?"""
        try:
            self.conn.execute(sql, tracker_to_remove)
            self.conn.commit()
        except sqlite3.Error:
            self.logs.error("Failed to remove tracker from database")
            raise Exception("Failed to remove tracker from database")

    def add_lumberjack_message(self, message: discord.Message):
        sql = """INSERT INTO lumberjack_messages (message_id, channel_id, created_at) 
               VALUES(?,?,?) """
        try:
            self.conn.execute(sql, (message.id, message.channel.id, message.created_at))
            self.conn.commit()
        except sqlite3.Error:
            self.logs.error(
                f"Failed to add following lumberjack message into database: {message}"
            )

    def get_oldest_lumberjack_message(self) -> LJMessage:
        old_date = datetime.now(timezone.utc) - timedelta(days=31)
        message = None
        try:
            message = self.conn.execute(
                "SELECT * FROM lumberjack_messages WHERE DATETIME(created_at) < :timestamp "
                "ORDER BY DATETIME(created_at) ASC Limit 1",
                {"timestamp": old_date},
            ).fetchone()
        except sqlite3.DatabaseError as e:
            print(f"get oldest lumberjack message error{e}")
        return (
            LJMessage(
                message[0],
                message[1],
                message[2],
            )
            if message
            else None
        )

    def get_lumberjack_message(self, channel_id: int, message_id: int) -> LJMessage:
        old_date = datetime.now(timezone.utc) - timedelta(days=31)
        message = None
        try:
            message = self.conn.execute(
                "SELECT * FROM lumberjack_messages WHERE DATETIME(created_at)  < :timestamp AND "
                "channel_id=:channel_id AND message_id=:message_id",
                {
                    "timestamp": old_date,
                    "channel_id": channel_id,
                    "message_id": message_id,
                },
            ).fetchone()
        except sqlite3.DatabaseError as e:
            print(f"Get Lumberjack Messages error: {e}")
        return (
            LJMessage(
                message[0],
                message[1],
                message[2],
            )
            if message
            else None
        )

    def delete_lumberjack_messages_from_db(self, message_id: int):
        try:
            self.conn.execute(
                "DELETE FROM lumberjack_messages WHERE message_id=:message_id",
                {"message_id": message_id},
            )
            self.conn.commit()
        except sqlite3.Error:
            self.logs.error("Failed to delete old LJ Messages from Database")
