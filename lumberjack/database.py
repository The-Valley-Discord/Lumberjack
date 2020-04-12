import logging as lumberlog

from . import c, conn


def init_db():
    """
    Initializes database tables from schema.sql
    """
    with open('./schema.sql', 'r') as schema_file:
        schema = schema_file.read()

    c.executescript(schema)
    lumberlog.debug('Database initialized from schema.sql')


# TODO: Move to lumberjack.logger.Logger
def add_message(conn, intmessage):
    """
    Add message to the messages table

    :param intmessage: [id, author, authorname, authordisplayname, channelid, channelname, guildid, clean_content, created_at, pfp, attachments]
    :param conn: SQL Connection Object
    :return: (int) message id
    """
    # TODO: Change intmessage array members to function parameters with default values
    sql = '''INSERT INTO messages (id,author,authorname,authordisplayname,channelid,channelname,guildid,
    clean_content,created_at,pfp,attachments) VALUES(?,?,?,?,?,?,?,?,?,?,?) '''
    c.execute(sql, intmessage)
    conn.commit()
    lumberlog.debug(f'Message logged: {c.lastrowid}')
    return c.lastrowid


def get_msg_by_id(id):
    """
    Get message by ID

    :param id: (int) Message ID
    :return: (array) Message content
    """
    c.execute("SELECT * FROM messages WHERE id=:id", {"id": id})
    return c.fetchone()


def update_msg(id, content):
    """
    Update message

    :param id: (int) Message ID
    :param content: (string) Content to update
    """
    with conn:
        c.execute("""UPDATE messages SET clean_content = :clean_content
                    WHERE id = :id""",
                  {'id': id, 'clean_content': content})


def get_att_by_id(id):
    """
    Get attachment by message ID

    :param id: (int) Message ID
    :return: (array) Attachment Data
    """
    c.execute("SELECT * FROM attachment_urls WHERE message_id=:id", {"id": id})
    return c.fetchall()


def add_guild(conn, intguild):
    """
    Add guild to database

    This allows channel IDs for the various types of logging channels to be stored for the guild

    :param intguild: [guildid, joinid, leaveid, deleteid, delete_bulk, edit, username, nickname, avatar, stat_member]
    :param conn: SQL Connection Object
    :return: (int) guild id
    """
    # TODO: Change intguild array members to function parameters with default values
    sql = '''INSERT INTO log_channels (guildid,joinid,leaveid,deleteid,delete_bulk,edit,username,nickname,
    avatar,stat_member) VALUES(?,?,?,?,?,?,?,?,?,?) '''
    c.execute(sql, intguild)
    conn.commit()
    return c.lastrowid


def get_log_by_id(id):
    """
    Get log channels by guild ID

    :param id: (int) Guild ID
    :return: (array) Log channel IDs
    """
    c.execute("SELECT * FROM log_channels WHERE guildid=:id", {"id": id})
    return c.fetchone()
