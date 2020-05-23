import logging as lumberlog
import sqlite3

conn = sqlite3.connect("log.db")

c = conn.cursor()


def init_db():
    """
    Initializes database tables from schema.sql
    """
    with open('./schema.sql', 'r') as schema_file:
        schema = schema_file.read()

    c.executescript(schema)
    lumberlog.debug('Database initialized from schema.sql')


def add_message(message):
    """
    Create a new project into the projects table
    :param message:
    """
    sql = """INSERT INTO messages (id,author,authorname,authordisplayname,channelid,channelname,guildid,
    clean_content,created_at,pfp,attachments) VALUES(?,?,?,?,?,?,?,?,?,?,?) """
    c.execute(sql, message)
    conn.commit()


def get_msg_by_id(message_id):
    c.execute("SELECT * FROM messages WHERE id=:id", {"id": message_id})
    return c.fetchone()


def update_msg(message_id, content):
    with conn:
        c.execute(
            """UPDATE messages SET clean_content = :clean_content
                    WHERE id = :id""",
            {"id": message_id, "clean_content": content},
        )


def get_att_by_id(message_id):
    c.execute("SELECT * FROM attachment_urls WHERE message_id=:id", {"id": message_id})
    return c.fetchall()


def add_attachment(message_id, attachments):
    for attachment in attachments:
        c.execute(
            "INSERT INTO attachment_urls VALUES (:message_id, :attachment)",
            {"message_id": message_id, "attachment": attachment})


def add_guild(guild_id):
    """
    Create a new project into the projects table
    :param guild_id:
    """
    sql = """INSERT INTO log_channels (guildid,joinid,leaveid,deleteid,delete_bulk,edit,username,nickname,
    avatar,stat_member) VALUES(?,?,?,?,?,?,?,?,?,?) """
    c.execute(sql, guild_id)
    conn.commit()


def get_log_by_id(guild_id):
    c.execute("SELECT * FROM log_channels WHERE guildid=:id", {"id": guild_id})
    return c.fetchone()


def set_join_channel(guild_id, channel_id):
    c.execute("UPDATE log_channels SET joinid = ? WHERE guildid = ?",
              {"joinid": channel_id, "guildid": guild_id})


def set_leave_channel(guild_id, channel_id):
    c.execute("UPDATE log_channels SET leaveid = ? WHERE guildid = ?",
              {"leaveid": channel_id, "guildid": guild_id})


def set_delete_channel(guild_id, channel_id):
    c.execute("UPDATE log_channels SET deleteid = ? WHERE guildid = ?",
              {"deleteid": channel_id, "guildid": guild_id})


def set_bulk_delete_channel(guild_id, channel_id):
    c.execute("UPDATE log_channels SET delete_bulk = ? WHERE guildid = ?",
              {"delete_bulk": channel_id, "guildid": guild_id})


def set_edit_channel(guild_id, channel_id):
    c.execute("UPDATE log_channels SET edit = ? WHERE guildid = ?",
              {"edit": channel_id, "guildid": guild_id})


def set_username_channel(guild_id, channel_id):
    c.execute("UPDATE log_channels SET username = ? WHERE guildid = ?",
              {"username": channel_id, "guildid": guild_id})


def set_nickname_channel(guild_id, channel_id):
    c.execute("UPDATE log_channels SET nickname = ? WHERE guildid = ?",
              {"nickname": channel_id, "guildid": guild_id})


def set_avatar_channel(guild_id, channel_id):
    c.execute("UPDATE log_channels SET avatar = ? WHERE guildid = ?",
              {"avatar": channel_id, "guildid": guild_id})


def set_stats_channel(guild_id, channel_id):
    c.execute("UPDATE log_channels SET stats = ? WHERE guildid = ?",
              {"stats": channel_id, "guildid": guild_id})


def set_ljlog_channel(guild_id, channel_id):
    c.execute("UPDATE log_channels SET ljlog = ? WHERE guildid = ?",
              {"ljlog": channel_id, "guildid": guild_id})


def get_tracked_by_id(tracked):
    sql = """SELECT * FROM tracking WHERE guildid=? AND userid=?"""
    c.execute(sql, tracked)
    return c.fetchone()


def add_tracker(new_tracker):
    tracked = (new_tracker[2], new_tracker[0])
    tracker_check = get_tracked_by_id(tracked)
    if tracker_check is None:
        sql = """INSERT INTO tracking (userid,username,guildid,channelid,endtime,modid,modname) 
        VALUES(?,?,?,?,?,?,?) """
        c.execute(sql, new_tracker)
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
                "endtime": new_tracker[4],
                "modid": new_tracker[5],
                "modname": new_tracker[6],
                "channelid": new_tracker[3],
                "userid": new_tracker[0],
                "guildid": new_tracker[2],
            },
        )
    return c.lastrowid


def remove_tracker(tracker_to_remove):
    sql = """DELETE from tracking WHERE guildid = ? AND userid = ?"""
    c.execute(sql, tracker_to_remove)
    conn.commit()
    return c.lastrowid
