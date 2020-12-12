import logging as lumberlog
import sqlite3
from datetime import datetime, timedelta
from typing import List

from discord import Message, Guild
from discord.ext.commands import Bot

from models import DBMessage, DBAuthor, DBChannel, DBGuild, Tracking, LJMessage

conn = sqlite3.connect("log.db")

c = conn.cursor()


def init_db():
    with open("./schema.sql", "r") as schema_file:
        schema = schema_file.read()

    c.executescript(schema)
    lumberlog.debug("Database initialized from schema.sql")


def add_message(message: Message):
    attachments = [f"{attachment.proxy_url}" for attachment in message.attachments]
    attachment_bool = False
    if len(attachments) > 0:
        attachment_bool = True
    if attachment_bool:
        add_attachment(message.id, attachments)
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
            f"{message.author.avatar_url}",
            attachment_bool,
        )
    sql = """INSERT INTO messages (id,author,authorname,authordisplayname,channelid,channelname,guildid,
    clean_content,created_at,pfp,attachments) VALUES(?,?,?,?,?,?,?,?,?,?,?) """
    c.execute(sql, values)
    conn.commit()


def get_msg_by_id(message_id: int) -> DBMessage:
    c.execute("SELECT * FROM messages WHERE id=:id", {"id": message_id})
    msg = c.fetchone()
    author = DBAuthor(msg[1], msg[2], msg[3], msg[9])
    channel = DBChannel(msg[4], msg[5])
    guild = get_log_by_id(msg[6])
    attachments = get_att_by_id(msg[0])
    message = DBMessage(msg[0], author, channel, guild, msg[7], msg[8], attachments)
    return message


def update_msg(message_id, content):
    with conn:
        c.execute(
            """UPDATE messages SET clean_content = :clean_content
                    WHERE id = :id""",
            {"id": message_id, "clean_content": content},
        )


def get_att_by_id(message_id: int) -> List:
    c.execute("SELECT * FROM attachment_urls WHERE message_id=:id", {"id": message_id})
    return c.fetchall()


def add_attachment(message_id, attachments):
    for attachment in attachments:
        c.execute(
            "INSERT INTO attachment_urls VALUES (:message_id, :attachment)",
            {"message_id": message_id, "attachment": attachment},
        )


def delete_old_db_messages():
    old_date = datetime.utcnow() - timedelta(days=31)
    c.execute("DELETE FROM messages WHERE DATETIME(created_at) < :timestamp",
              {"timestamp": old_date})
    c.execute("SELECT min(id) FROM messages")
    latest_message = c.fetchone()
    c.execute('DELETE FROM attachment_urls where message_id < :id', {
        "id": latest_message[0]})


def add_all_guilds(bot: Bot):
    for guild in bot.guilds:
        gld = get_log_by_id(guild.id)
        if gld is None:
            add_guild(guild)


def add_guild(guild: Guild):
    new_guild = (guild.id, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    sql = """INSERT INTO log_channels (guildid,joinid,leaveid,deleteid,delete_bulk,edit,username,nickname,
    avatar,stat_member) VALUES(?,?,?,?,?,?,?,?,?,?) """
    c.execute(sql, new_guild)
    conn.commit()


def get_log_by_id(guild_id: int) -> DBGuild:
    c.execute("SELECT * FROM log_channels WHERE guildid=:id", {"id": guild_id})
    gld = c.fetchone()
    return DBGuild(gld[0], gld[1], gld[2], gld[3], gld[4], gld[5], gld[6], gld[7], gld[8], gld[9], gld[10])


def update_log_channels(guild: DBGuild):
    c.execute(
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
        {"joinid": guild.join_id, "leaveid": guild.leave_id,
         "deleteid": guild.delete_id, "delete_bulk": guild.delete_bulk,
         "edit": guild.edit, "username": guild.username, "nickname": guild.nickname,
         "avatar": guild.avatar, "stats": guild.stat_member,
         "ljid": guild.lj_id, "guildid": guild.id},
    )


def get_tracked_by_id(guild_id: int, user_id: int) -> Tracking:
    values = (guild_id, user_id)
    sql = """SELECT * FROM tracking WHERE guildid=? AND userid=?"""
    c.execute(sql, values)
    tracked = c.fetchone()
    try:
        return Tracking(tracked[0], tracked[1], tracked[2], tracked[3],
                        tracked[4], tracked[5], tracked[6])
    except TypeError:
        return None


def add_tracker(new_tracker: Tracking):
    tracker = (new_tracker.user_id, new_tracker.username, new_tracker.guild_id,
               new_tracker.channel_id, new_tracker.end_time, new_tracker.mod_id,
               new_tracker.mod_name)
    tracker_check = get_tracked_by_id(new_tracker.guild_id, new_tracker.user_id)
    if tracker_check is None:
        sql = """INSERT INTO tracking (userid,username,guildid,channelid,endtime,modid,modname) 
        VALUES(?,?,?,?,?,?,?) """
        c.execute(sql, tracker)
        conn.commit()
    else:
        c.execute(
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
    return c.lastrowid


def remove_tracker(guild_id: int, user_id: int):
    tracker_to_remove = (guild_id, user_id)
    sql = """DELETE from tracking WHERE guildid = ? AND userid = ?"""
    c.execute(sql, tracker_to_remove)
    conn.commit()


def add_lumberjack_message(message):
    sql = """INSERT INTO lumberjack_messages (message_id, channel_id, created_at) 
           VALUES(?,?,?) """
    c.execute(sql, (message.id, message.channel.id, datetime.utcnow()))
    conn.commit()


def get_old_lumberjack_messages():
    old_date = datetime.utcnow() - timedelta(days=31)
    c.execute("SELECT * FROM lumberjack_messages WHERE DATETIME(created_at) < :timestamp",
              {"timestamp": old_date})
    messages = c.fetchall()
    lj_messages = []
    for message in messages:
        lj_messages.append(LJMessage(message[0], message[1], message[2]))
    return lj_messages


def delete_lumberjack_messages_from_db(message_id):
    c.execute("DELETE FROM lumberjack_messages WHERE message_id=:message_id",
              {"message_id": message_id})
