import discord
from datetime import datetime, timedelta
from discord.ext import commands
import sqlite3

bot = commands.Bot(command_prefix="bum.")
before_invites = []
format_date = "%b %d, %Y"
format_time = "%I:%M %p"
format_datetime = "%b %d, %Y  %I:%M %p"

conn = sqlite3.connect("log.db")

c = conn.cursor()

c.execute(
    """ CREATE TABLE IF NOT EXISTS messages (
            id integer PRIMARY KEY,
            author integer NOT NULL,
            authorname text,
            authordisplayname text,
            channelid integer,
            channelname text,
            guildid integer,
            clean_content text,
            created_at timestamp,
            pfp text,
            attachments integer
            ) """
)
c.execute(
    """ CREATE TABLE IF NOT EXISTS attachment_urls (
            message_id integer,
            attachment text
            ) """
)
c.execute(
    """ CREATE TABLE IF NOT EXISTS log_channels (
            guildid integer Primary Key,
            joinid integer,
            leaveid integer,
            deleteid integer,
            delete_bulk integer,
            edit integer,
            username integer,
            nickname integer,
            avatar integer,
            stat_member integer
            ) """
)
c.execute(
    """ CREATE TABLE IF NOT EXISTS tracking (
            userid integer,
            username text,
            guildid integer,
            channelid integer,
            endtime timestamp,
            modid integer,
            modname text
            ) """
)
# c.execute(""" ALTER TABLE log_channels
#           ADD COLUMN ljid integer
#            """)
#


def add_message(conn, intmessage):
    """
    Create a new project into the projects table
    :param intmessage:
    :param conn:
    :return: message id
    """
    sql = """INSERT INTO messages (id,author,authorname,authordisplayname,channelid,channelname,guildid,
    clean_content,created_at,pfp,attachments) VALUES(?,?,?,?,?,?,?,?,?,?,?) """
    c.execute(sql, intmessage)
    conn.commit()
    return c.lastrowid


def get_msg_by_id(id):
    c.execute("SELECT * FROM messages WHERE id=:id", {"id": id})
    return c.fetchone()


def update_msg(id, content):
    with conn:
        c.execute(
            """UPDATE messages SET clean_content = :clean_content
                    WHERE id = :id""",
            {"id": id, "clean_content": content},
        )


def get_att_by_id(id):
    c.execute("SELECT * FROM attachment_urls WHERE message_id=:id", {"id": id})
    return c.fetchall()


def add_guild(conn, intguild):
    """
    Create a new project into the projects table
    :param intguild:
    :param conn:
    :return: guild id
    """
    sql = """INSERT INTO log_channels (guildid,joinid,leaveid,deleteid,delete_bulk,edit,username,nickname,
    avatar,stat_member) VALUES(?,?,?,?,?,?,?,?,?,?) """
    c.execute(sql, intguild)
    conn.commit()
    return c.lastrowid


def get_log_by_id(id):
    c.execute("SELECT * FROM log_channels WHERE guildid=:id", {"id": id})
    return c.fetchone()


def get_tracked_by_id(conn, tracked):
    sql = """SELECT * FROM tracking WHERE guildid=? AND userid=?"""
    c.execute(sql, tracked)
    return c.fetchone()


def add_tracker(conn, inttracker):
    tracked = (inttracker[2], inttracker[0])
    tracker_check = get_tracked_by_id(conn, tracked)
    if tracker_check is None:
        sql = """INSERT INTO tracking (userid,username,guildid,channelid,endtime,modid,modname) 
        VALUES(?,?,?,?,?,?,?) """
        c.execute(sql, inttracker)
        conn.commit()
    else:
        c.execute(
            """UPDATE tracking SET endtime = :endtime,
                             modid = :modid,
                             modname = :modname
                             channelid = :channelid
                            WHERE userid = :userid
                            AND guildid = :guildid""",
            {
                "endtime": inttracker[4],
                "modid": inttracker[5],
                "modname": inttracker[6],
                "channelid": inttracker[3],
                "userid": inttracker[0],
                "guildid": inttracker[2],
            },
        )
    return c.lastrowid


def remove_tracker(conn, inttracker):
    sql = """DELETE from tracking WHERE guildid = ? AND userid = ?"""
    c.execute(sql, inttracker)
    conn.commit()
    return c.lastrowid


def has_permissions():
    def predicate(ctx):
        return ctx.author.guild_permissions.manage_guild is True

    return commands.check(predicate)


@bot.event
async def on_message(message):
    attachments = [f"{attachment.proxy_url}" for attachment in message.attachments]
    author = f"{message.author.name}#{message.author.discriminator}"
    avatar_url = f"{message.author.avatar_url}"
    attachment_bool = False
    if len(attachments) > 0:
        attachment_bool = True
    mymessage = (
        message.id,
        message.author.id,
        author,
        message.author.display_name,
        message.channel.id,
        message.channel.name,
        message.guild.id,
        message.clean_content,
        message.created_at,
        avatar_url,
        attachment_bool,
    )
    add_message(conn, mymessage)
    if attachment_bool:
        for attachment in attachments:
            c.execute(
                "INSERT INTO attachment_urls VALUES (:message_id, :attachment)",
                {"message_id": message.id, "attachment": attachment},
            )
    tracked = (message.guild.id, message.author.id)
    tracker = get_tracked_by_id(conn, tracked)
    if tracker is None:
        pass
    else:
        end_time = datetime.strptime(tracker[4], "%Y-%m-%d %H:%M:%S.%f")
        channel = bot.get_channel(tracker[3])
        if end_time < datetime.utcnow():
            remove_tracker(conn, tracked)
            embed = discord.Embed(
                description=f"""Tracker on {tracker[1]} has expired""", color=0xFFF1D7
            )
            embed.set_author(name="Tracker Expired")
            embed.timestamp = datetime.utcnow()
            await channel.send(embed=embed)
            gld = get_log_by_id(message.channel.guild.id)
            logs = bot.get_channel(gld[10])
            await logs.send(embed=embed)
        else:
            prts = message.clean_content
            prt_1 = prts[:1900]
            prt_2 = prts[1900:]
            embed = discord.Embed(
                description=f"**[Jump URL]({message.jump_url})**\n{prt_1}",
                color=0xFFF1D7,
            )
            embed.set_footer(
                text=f"{tracker[1]}({tracker[0]}\nMessage sent",
                icon_url=f"{message.author.avatar_url}",
            )
            embed.set_author(name=f"#{message.channel.name}")
            embed.timestamp = datetime.utcnow()
            if len(message.clean_content) > 1900:
                embed.add_field(name=f"Continued", value=f"{prt_2}")
            if len(attachments) > 0:
                attachments_str = " ".join(attachments)
                embed.add_field(
                    name=f"**Attachments**", value=f"{attachments_str}", inline=False
                )
                embed.set_image(url=attachments[0])
            else:
                pass
            await channel.send(embed=embed)
    await bot.process_commands(message)


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
            newguild = (guild.id, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            add_guild(conn, newguild)
        else:
            pass
        for invite in await guild.invites():
            x = [invite.url, invite.uses, invite.inviter]
            before_invites.append(x)
    print("Bot is ready.")


@bot.event
async def on_guild_join(guild):
    for invite in await guild.invites():
        x = [invite.url, invite.uses, invite.inviter]
        before_invites.append(x)
        gld = get_log_by_id(guild.id)
        if gld is None:
            newguild = (guild.id, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            add_guild(conn, newguild)
        else:
            pass


@bot.command()
@commands.check_any(has_permissions())
async def log(ctx, arg1, arg2):
    log_name = ""
    channel_id = 0
    strip = ["<", ">", "#"]
    str_channel = arg2.lower()
    log_type = arg1.lower()
    for item in strip:
        str_channel = str_channel.strip(item)
    if str_channel == "here":
        channel_id = ctx.channel.id
    else:
        channel_id = int(str_channel)
    logs = bot.get_channel(channel_id)
    if log_type == "join":
        sql = """UPDATE log_channels SET joinid = ? WHERE guildid = ?"""
        log_name = "Join"
    elif log_type == "leave":
        sql = """UPDATE log_channels SET leaveid = ? WHERE guildid = ?"""
        log_name = "Leave"
    elif log_type == "delete":
        sql = """UPDATE log_channels SET deleteid = ? WHERE guildid = ?"""
        log_name = "Delete"
    elif log_type == "bulk_delete":
        sql = """UPDATE log_channels SET delete_bulk = ? WHERE guildid = ?"""
        log_name = "Bulk Delete"
    elif log_type == "edit":
        sql = """UPDATE log_channels SET edit = ? WHERE guildid = ?"""
        log_name = "Edit"
    elif log_type == "username":
        sql = """UPDATE log_channels SET username = ? WHERE guildid = ?"""
        log_name = "Username"
    elif log_type == "nickname":
        sql = """UPDATE log_channels SET nickname = ? WHERE guildid = ?"""
        log_name = "Nickname"
    elif log_type == "avatar":
        sql = """UPDATE log_channels SET avatar = ? WHERE guildid = ?"""
        log_name = "Avatar"
    elif log_type == "stats":
        sql = """UPDATE log_channels SET stat_member = ? WHERE guildid = ?"""
        log_name = "Stats"
        if logs is None:
            pass
        else:
            await logs.edit(name=f"Members: {logs.guild.member_count}")
    elif log_type == "ljlog":
        sql = """UPDATE log_channels SET ljid = ? WHERE guildid = ?"""
        log_name = "Lumberjack Logs"
    if len(log_name) == 0:
        await ctx.send(
            "Incorrect log type. Please use one of the following. Join, Leave, Delete, Bulk_Delete, Edit, Username, Nickname, Avatar, Stats or LJLog"
        )
    elif logs is None:
        await ctx.send("Invalid channel ID")
    else:
        await ctx.send(f"Updated {log_name} Log Channel to {logs.mention}")
        task = (logs.id, ctx.guild.id)
        c.execute(sql, task)
        conn.commit()


@bot.command()
@commands.check_any(has_permissions())
async def clear(ctx, arg1):
    log_type = arg1.lower()
    log_name = ""
    if log_type == "join":
        sql = """UPDATE log_channels SET joinid = ? WHERE guildid = ?"""
        log_name = "Join"
    elif log_type == "leave":
        sql = """UPDATE log_channels SET leaveid = ? WHERE guildid = ?"""
        log_name = "Leave"
    elif log_type == "delete":
        sql = """UPDATE log_channels SET deleteid = ? WHERE guildid = ?"""
        log_name = "Delete"
    elif log_type == "bulk_delete":
        sql = """UPDATE log_channels SET delete_bulk = ? WHERE guildid = ?"""
        log_name = "Bulk Delete"
    elif log_type == "edit":
        sql = """UPDATE log_channels SET edit = ? WHERE guildid = ?"""
        log_name = "Edit"
    elif log_type == "username":
        sql = """UPDATE log_channels SET username = ? WHERE guildid = ?"""
        log_name = "Username"
    elif log_type == "nickname":
        sql = """UPDATE log_channels SET nickname = ? WHERE guildid = ?"""
        log_name = "Nickname"
    elif log_type == "avatar":
        sql = """UPDATE log_channels SET avatar = ? WHERE guildid = ?"""
        log_name = "Avatar"
    elif log_type == "stats":
        sql = """UPDATE log_channels SET stat_member = ? WHERE guildid = ?"""
        log_name = "Stats"
    elif log_type == "ljlog":
        sql = """UPDATE log_channels SET ljid = ? WHERE guildid = ?"""
        log_name = "Lumberjack Logs"
    if len(log_name) == 0:
        await ctx.send(
            "Incorrect log type. Please use one of the following. Join, Leave, Delete, Bulk_Delete, Edit, Username, Nickname, Avatar, Stats or LJLog"
        )
    else:
        await ctx.send(f"Disabled {log_name} logs.")
        task = (0, ctx.guild.id)
        c.execute(sql, task)
        conn.commit()


@bot.event
async def on_guild_remove(guild):
    for invite in await guild.invites():
        x = [invite.url, invite.uses, invite.inviter]
        before_invites.remove(x)


@bot.event
async def on_invite_create(invite):
    x = [invite.url, invite.uses, invite.inviter]
    before_invites.append(x)


@bot.event
async def on_invite_delete(invite):
    x = [invite.url, invite.uses, invite.inviter]
    before_invites.remove(x)


@bot.command()
async def ping(ctx):
    embed = discord.Embed(
        title="**Ping**", description=f"Pong! {round(bot.latency * 1000)}ms"
    )
    embed.set_author(name=f"{bot.user.name}", icon_url=bot.user.avatar_url)
    await ctx.send(embed=embed)


@bot.command()
@commands.check_any(has_permissions())
async def track(ctx, user, time, channel):
    strip = ["<", ">", "#", "@", "!"]
    str_channel = channel.lower()
    str_user = user.lower()
    tracking_time = 0
    for item in strip:
        str_channel = str_channel.strip(item)
        str_user = str_user.strip(item)
    if time[-1].lower() == "d":
        timelimit = timedelta(days=int(time[:-1]))
        tracking_time = datetime.utcnow() + timelimit
    elif time[-1].lower() == "h":
        timelimit = timedelta(hours=int(time[:-1]))
        tracking_time = datetime.utcnow() + timelimit
    elif time[-1].lower() == "m":
        timelimit = timedelta(minutes=int(time[:-1]))
        tracking_time = datetime.utcnow() + timelimit
    else:
        pass
    user = ctx.guild.get_member(int(str_user))
    channel = bot.get_channel(int(str_channel))
    if user is None:
        await ctx.send(
            f"A Valid User was not entered\nFormat is lum.track (user mention/id) (time in d or h) (log channel "
            f"mention/id)"
        )
    # elif user.guild_permissions.manage_guild:
    # await ctx.send(
    # f'<\_<\n>\_>\nI can\'t track a mod.\n Try someone else')
    elif channel is None:
        await ctx.send(
            f"A valid Channel was not entered\nFormat is lum.track (user mention/id) (time in d or h) (log channel "
            f"mention/id)"
        )
    elif channel.guild != ctx.guild:
        await ctx.send(
            f"<\_<\n>\_>\nThat channel is not on this server.\n Try a different one."
        )
    else:
        username = f"{user.name}#{user.discriminator}"
        modname = f"{ctx.author.name}#{ctx.author.discriminator}"
        inttracker = (
            user.id,
            username,
            ctx.guild.id,
            channel.id,
            tracking_time,
            ctx.author.id,
            modname,
        )
        gld = get_log_by_id(ctx.guild.id)
        logs = bot.get_channel(gld[10])
        add_tracker(conn, inttracker)
        await ctx.send(f"A Tracker has been placed on {username} for {time}")
        await logs.send(f"{modname} placed a tracker on {username} for {time}")


@bot.command()
@commands.check_any(has_permissions())
async def untrack(ctx, user):
    strip = ["<", ">", "#", "@", "!"]
    str_user = user
    for item in strip:
        str_user = str_user.strip(item)
    user = ctx.guild.get_member(int(str_user))
    if user is None:
        await ctx.send(
            f"A Valid User was not entered\nFormat is lum.untrack (user mention/id)"
        )
    else:
        inttracker = (ctx.guild.id, user.id)
        modname = f"{ctx.author.name}#{ctx.author.discriminator}"
        username = f"{user.name}#{user.discriminator}"
        remove_tracker(conn, inttracker)
        await ctx.send(f"{username} is no longer being tracked")
        gld = get_log_by_id(ctx.guild.id)
        logs = bot.get_channel(gld[10])
        await logs.send(f"{modname} removed the tracker on {username}")


# member join event


@bot.event
async def on_member_join(member):
    gld = get_log_by_id(member.guild.id)
    logs = bot.get_channel(gld[1])
    account_age = datetime.utcnow() - member.created_at
    global before_invites
    after_invites = []
    invite_used = "Vanity URL"
    invite_uses = ""
    inviter = ""
    for guild in bot.guilds:
        for invite in await guild.invites():
            x = [invite.url, invite.uses, invite.inviter]
            after_invites.append(x)
    for before_invite in before_invites:
        for after_invite in after_invites:
            if before_invite == after_invite:
                pass
            elif (
                before_invite[0] == after_invite[0]
                and before_invite[1] != after_invite[1]
            ):
                invite_used = after_invite[0]
                invite_uses = f"({after_invite[1]} uses)"
                inviter = after_invite[2]
                before_invites = after_invites
    if account_age.days < 7:
        color = 0xFFC704
    else:
        color = 0x008000
    if logs is None:
        pass
    else:
        embed = discord.Embed(
            title=f"**User Joined**",
            description=f"""**Name:** {member.mention}
**Created on:** {member.created_at.strftime(format_date)}
**Account age:** {account_age.days} days old
**Invite used:** {invite_used} {invite_uses}
**Created By:** {inviter}""",
            color=color,
        )
        if (account_age.seconds // 3600) == 0 and account_age.days == 0:
            embed.add_field(
                name="**New Account**",
                value=f"Created {(account_age.seconds % 3600) // 60} minutes {((account_age.seconds % 3600) % 60)} seconds ago.",
                inline=False,
            )
        elif 0 < (account_age.seconds // 3600) and account_age.days == 0:
            embed.add_field(
                name="**New Account**",
                value=f"Created {account_age.seconds // 3600} hours {(account_age.seconds % 3600) // 60} minutes {((account_age.seconds % 3600) % 60)} seconds ago.",
                inline=False,
            )
        elif 0 < account_age.days < 7:
            embed.add_field(
                name="**New Account**",
                value=f"Created {account_age.days} days {account_age.seconds // 3600} hours {(account_age.seconds % 3600) // 60} minutes ago.",
                inline=False,
            )
        else:
            pass
        embed.set_author(name=f"{member.name}#{member.discriminator} ({member.id})")
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text=f"Total Members: {member.guild.member_count}")
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)
        stat_channel = bot.get_channel(gld[9])
        if stat_channel is None:
            pass
        else:
            await stat_channel.edit(name=f"Members: {member.guild.member_count}")


# member leave event


@bot.event
async def on_member_remove(member):
    gld = get_log_by_id(member.guild.id)
    logs = bot.get_channel(gld[2])
    if logs is None:
        pass
    else:
        account_age = datetime.utcnow() - member.created_at
        time_on_server = datetime.utcnow() - member.joined_at
        embed = discord.Embed(
            title=f"**User Left**",
            description=f"""**Name:** {member.mention}
**Created on:** {member.created_at.strftime(format_date)}
**Account age:** {account_age.days} days old
**Joined on:** {member.joined_at.strftime(format_date)} ({time_on_server.days} days ago)""",
            color=0xD90000,
        )
        embed.set_author(name=f"{member.name}#{member.discriminator} ({member.id})")
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text=f"Total Members: {member.guild.member_count}")
        embed.timestamp = datetime.utcnow()
        roles = [f"<@&{role.id}>" for role in member.roles[1:]]
        roles_str = " ".join(roles)
        if len(roles) < 1:
            embed.add_field(name=f"**Roles[{len(roles)}]**", value="None", inline=False)
        else:
            embed.add_field(
                name=f"**Roles[{len(roles)}]**", value=f"{roles_str}", inline=False
            )
        await logs.send(embed=embed)
        stat_channel = bot.get_channel(gld[9])
        if stat_channel is None:
            pass
        else:
            await stat_channel.edit(name=f"Members: {member.guild.member_count}")


# message delete event


@bot.event
async def on_raw_message_delete(payload):
    gld = get_log_by_id(payload.guild_id)
    logs = bot.get_channel(gld[3])
    channel = bot.get_channel(payload.channel_id)
    msg = get_msg_by_id(payload.message_id)
    att = get_att_by_id(payload.message_id)
    author = channel.guild.get_member(msg[1])
    attachments = []
    for attachment in att:
        attachments.append(attachment[1])
    if author.bot:
        pass
    elif logs is None:
        pass
    else:
        embed = discord.Embed(
            title=f"**Message deleted in #{channel}**",
            description=f"""**Author:** {author.mention}
**Channel:** {channel.mention} ({channel.id})
**Message ID:** {payload.message_id}""",
            color=0xD90000,
        )
        if len(msg[7]) == 0:
            embed.add_field(name=f"**Content**", value="`Blank`", inline=False)
        elif len(msg[7]) <= 1024:
            embed.add_field(name=f"**Content**", value=f"{msg[7]}", inline=False)
        else:
            prts = msg[7]
            prt_1 = prts[:1024]
            prt_2 = prts[1024:]
            embed.add_field(name=f"**Content**", value=f"{prt_1}", inline=False)
            embed.add_field(name=f"Continued", value=f"{prt_2}")
        if not msg[10]:
            embed.add_field(name=f"**Attachments**", value=f"None", inline=False)
        else:
            attachments_str = " ".join(attachments)
            embed.add_field(
                name=f"**Attachments**", value=f"{attachments_str}", inline=False
            )
            embed.set_image(url=attachments[0])
        embed.set_author(name=f"{author.name}#{author.discriminator} ({author.id})")
        embed.set_thumbnail(url=author.avatar_url)
        embed.set_footer(text=f"")
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)


# message edit event


@bot.event
async def on_raw_message_edit(payload):
    channel = bot.get_channel(payload.channel_id)
    gld = get_log_by_id(channel.guild.id)
    logs = bot.get_channel(gld[5])
    before = get_msg_by_id(payload.message_id)
    after = await channel.fetch_message(payload.message_id)
    if before[7] == after.clean_content:
        pass
    else:
        if after.author.bot:
            pass
        elif logs is None:
            pass
        else:
            embed = discord.Embed(
                title=f"**Message edited in #{after.channel}**",
                description=f"""**Author:** <@!{after.author.id}>
**Channel:** <#{after.channel.id}> ({after.channel.id})
**Message ID:** {after.id}
[Jump Url]({after.jump_url})""",
                color=0xFFC704,
            )
            embed.set_author(
                name=f"{after.author.name}#{after.author.discriminator} ({after.author.id})"
            )
            if len(before[7]) == 0:
                embed.add_field(name=f"**Before**", value=f"`Blank`", inline=False)
            elif len(before[7]) <= 1024:
                embed.add_field(name=f"**Before**", value=f"{before[7]} ", inline=False)
            else:
                prts = before[7]
                prt_1 = prts[:1024]
                prt_2 = prts[1024:]
                embed.add_field(name=f"**Before**", value=f"{prt_1}", inline=False)
                embed.add_field(name=f"Continued", value=f"{prt_2}")
            if len(after.content) <= 1024:
                embed.add_field(
                    name=f"**After**", value=f"{after.content} ", inline=False
                )
            else:
                prts = after.content
                prt_1 = prts[:1024]
                prt_2 = prts[1024:]
                embed.add_field(name=f"**After**", value=f"{prt_1}", inline=False)
                embed.add_field(name=f"Continued", value=f"{prt_2}")
            embed.set_thumbnail(url=after.author.avatar_url)
            embed.set_footer(text=f"")
            embed.timestamp = datetime.utcnow()
            await logs.send(embed=embed)
            tracked = (after.guild.id, after.author.id)
            tracker = get_tracked_by_id(conn, tracked)
            if tracker is None:
                pass
            else:
                end_time = datetime.strptime(tracker[4], "%Y-%m-%d %H:%M:%S.%f")
                channel = bot.get_channel(tracker[3])
                embed = discord.Embed(
                    description=f"**[Jump Url]({after.jump_url})**", color=0xFFF1D7,
                )
                embed.set_author(name=f"#{after.channel.name}")
                embed.set_footer(
                    text=f"{tracker[1]}({tracker[0]})\nMessage sent",
                    icon_url=after.author.avatar_url,
                )
                embed.timestamp = datetime.utcnow()
                if len(before[7]) == 0:
                    embed.add_field(name=f"**Before**", value=f"`Blank`", inline=False)
                elif len(before[7]) <= 1024:
                    embed.add_field(
                        name=f"**Before**", value=f"{before[7]} ", inline=False
                    )
                else:
                    prts = before[7]
                    prt_1 = prts[:1024]
                    prt_2 = prts[1024:]
                    embed.add_field(name=f"**Before**", value=f"{prt_1}", inline=False)
                    embed.add_field(name=f"Continued", value=f"{prt_2}")
                if len(after.content) <= 1024:
                    embed.add_field(
                        name=f"**After**", value=f"{after.content} ", inline=False
                    )
                else:
                    prts = after.content
                    prt_1 = prts[:1024]
                    prt_2 = prts[1024:]
                    embed.add_field(name=f"**After**", value=f"{prt_1}", inline=False)
                    embed.add_field(name=f"Continued", value=f"{prt_2}")
                await channel.send(embed=embed)
            content = after.content
            update_msg(payload.message_id, content)


# member update event (nickname, roles, activity, status)


@bot.event
async def on_member_update(before, after):
    gld = get_log_by_id(after.guild.id)
    logs = bot.get_channel(gld[7])
    if before.nick == after.nick:
        pass
    elif logs is None:
        pass
    else:
        embed = discord.Embed(
            title=f"**User Nickname Updated**",
            description=f"""**User:** <@!{after.id}>\n
**Before:** {before.nick}
**After:** {after.nick}""",
            color=0x22FFC2,
        )
        embed.set_author(name=f"{after.name}#{after.discriminator} ({after.id})")
        embed.set_thumbnail(url=after.avatar_url)
        embed.set_footer(text=f"")
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)


# user update event (avatar, username, discriminator)


@bot.event
async def on_user_update(before, after):
    for guild in bot.guilds:
        if after in guild.members:
            gld = get_log_by_id(guild.id)
            if before.name != after.name or before.discriminator != after.discriminator:
                logs = bot.get_channel(gld[6])
                if logs is None:
                    pass
                else:
                    embed = discord.Embed(
                        title=f"**Username Updated**",
                        description=f"""**User:** <@!{after.id}>\n
**Before:** {before.name}#{before.discriminator}
**After:** {after.name}#{after.discriminator}""",
                        color=0x22FFC2,
                    )
                    embed.set_author(
                        name=f"{after.name}#{after.discriminator} ({after.id})"
                    )
                    embed.set_thumbnail(url=after.avatar_url)
                    embed.set_footer(text=f"")
                    embed.timestamp = datetime.utcnow()
                    await logs.send(embed=embed)
            if before.avatar != after.avatar:
                logs = bot.get_channel(gld[8])
                if logs is None:
                    pass
                else:
                    embed = discord.Embed(
                        title=f"**User avatar Updated**",
                        description=f"""**User:** <@!{after.id}>\n
Old avatar in thumbnail. New avatar down below""",
                        color=0x8000FF,
                    )
                    embed.set_author(
                        name=f"{after.name}#{after.discriminator} ({after.id})"
                    )
                    embed.set_thumbnail(url=before.avatar_url)
                    embed.set_footer(text=f"")
                    embed.set_image(url=after.avatar_url_as(size=128))
                    embed.timestamp = datetime.utcnow()
                    await logs.send(embed=embed)


@bot.event
async def on_raw_bulk_message_delete(payload):
    messages = []
    ids = sorted(payload.message_ids)
    for id in ids:
        messages.append(get_msg_by_id(id))
    gld = get_log_by_id(payload.guild_id)
    logs = bot.get_channel(gld[4])
    current_time = datetime.utcnow()
    purged_channel = bot.get_channel(payload.channel_id)
    embed = discord.Embed(
        title=f"**Bulk Message Delete**",
        description=f"""**Message Count:** {len(messages)}
**Channel:** {purged_channel.mention}
Full message dump attached below.""",
        color=0xFF0080,
    )
    embed.timestamp = datetime.utcnow()
    with open("./log.txt", "w") as file:
        for message in messages:
            file.writelines(
                f"Author: {message[2]} ({message[1]})\nID:{message[0]}\nContent: {message[7]}\n\n"
            )
    try:
        await logs.send(embed=embed)
        await logs.send(
            file=discord.File(
                "./log.txt", filename=f"{current_time.strftime(format_datetime)}.txt"
            )
        )
    except discord.HTTPException:
        pass


@bot.event
async def on_voice_state_update(member, before, after):
    tracked = (member.guild.id, member.id)
    tracker = get_tracked_by_id(conn, tracked)
    if tracker is None:
        pass
    else:
        channel = bot.get_channel(tracker[3])
        if before.channel == after.channel:
            pass
        elif tracker is None:
            pass
        elif before.channel is None:
            embed = discord.Embed(
                description=f"**channel:** {after.channel.name}", color=0xFF0080
            )
            embed.set_author(name="Joined Voice Channel")
            embed.set_footer(
                text=f"{tracker[1]}\n({member.id}) ", icon_url=member.avatar_url
            )
            embed.timestamp = datetime.utcnow()
            await channel.send(embed=embed)
        elif after.channel is None:
            embed = discord.Embed(
                description=f"**channel:** {before.channel.name}", color=0xFF0080
            )
            embed.set_author(name="Left Voice Channel")
            embed.set_footer(
                text=f"{tracker[1]}\n({member.id})", icon_url=member.avatar_url
            )
            embed.timestamp = datetime.utcnow()
            await channel.send(embed=embed)
        else:
            await channel.send("There was an error on VC log")


with open("token", "r") as f:
    bot.run(f.readline().strip())
