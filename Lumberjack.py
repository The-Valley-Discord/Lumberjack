# TODO: Delete this file when move to cogs is complete

import sqlite3
from datetime import datetime, timedelta

import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='lum.')
before_invites = []

conn = sqlite3.connect('log.db')

c = conn.cursor()


# TODO: This moves into lumberjack.tracker.Tracker
@bot.command()
@commands.check_any(has_permissions())
async def track(ctx, user, time, channel):
    strip = ['<', '>', '#', '@', '!']
    str_channel = channel.lower()
    str_user = user.lower()
    tracking_time = 0
    for item in strip:
        str_channel = str_channel.strip(item)
        str_user = str_user.strip(item)
    if time[-1].lower() == 'd':
        timelimit = timedelta(days=int(time[:-1]))
        tracking_time = datetime.utcnow() + timelimit
    elif time[-1].lower() == 'h':
        timelimit = timedelta(hours=int(time[:-1]))
        tracking_time = datetime.utcnow() + timelimit
    elif time[-1].lower() == 'm':
        timelimit = timedelta(minutes=int(time[:-1]))
        tracking_time = datetime.utcnow() + timelimit
    else:
        pass
    user = await bot.fetch_user(int(str_user))
    channel = bot.get_channel(int(str_channel))
    if user is None:
        await ctx.send(f'A Valid User was not entered\nFormat is lum.track (user mention/id) (time in d or h) (log channel mention/id)')
    elif channel is None:
        await ctx.send(f'A valid Channel was not entered\nFormat is lum.track (user mention/id) (time in d or h) (log channel mention/id)')
        await ctx.send (f'{str_channel}')
    else:
        username = f'{user.name}#{user.discriminator}'
        modname = f'{ctx.author.name}#{ctx.author.discriminator}'
        inttracker = (user.id, username, ctx.guild.id, channel.id, tracking_time, ctx.author.id, modname)
        add_tracker(conn, inttracker)
        await ctx.send(f'A Tracker has been placed on {username} for {time}')


# TODO: This moves into lumberjack.tracker.Tracker
@bot.command()
@commands.check_any(has_permissions())
async def untrack(ctx, user):
    strip = ['<', '>', '#', '@', '!']
    str_user = user
    for item in strip:
        str_user = str_user.strip(item)
    user = await bot.fetch_user(int(str_user))
    if user is None:
        await ctx.send(
            f'A Valid User was not entered\nFormat is lum.untrack (user mention/id)')
    else:
        inttracker = (ctx.guild.id, user.id)
        username = f'{user.name}#{user.discriminator}'
        remove_tracker(conn, inttracker)
        await ctx.send(f'{username} is no longer being tracked')


format_date = '%b %d, %Y'
format_time = '%I:%M %p'
format_datetime = '%b %d, %Y  %I:%M %p'


# member join event
# TODO: This moves into lumberjack.logger.Logger
@bot.event
async def on_member_join(member):
    gld = get_log_by_id(member.guild.id)
    logs = bot.get_channel(gld[1])
    account_age = datetime.utcnow() - member.created_at
    global before_invites
    after_invites = []
    invite_used = 'Vanity URL'
    invite_uses = ''
    inviter = ''
    for guild in bot.guilds:
        for invite in await guild.invites():
            x = [invite.url, invite.uses, invite.inviter]
            after_invites.append(x)
    for before_invite in before_invites:
        for after_invite in after_invites:
            if before_invite == after_invite:
                pass
            elif before_invite[0] == after_invite[0] and before_invite[1] != after_invite[1]:
                invite_used = after_invite[0]
                invite_uses = f'({after_invite[1]} uses)'
                inviter = after_invite[2]
                before_invites = after_invites
    if account_age.days < 7:
        color = 0xffc704
    else:
        color = 0x008000
    if logs is None:
        pass
    else:
        embed = discord.Embed(title=f'**User Joined**',
                              description=f'''**Name:** {member.mention}
**Created on:** {member.created_at.strftime(format_date)}
**Account age:** {account_age.days} days old
**Invite used:** {invite_used} {invite_uses}
**Created By:** {inviter}''',
                              color=color)
        if (account_age.seconds // 3600) == 0 and account_age.days == 0:
            embed.add_field(name='**New Account**',
                            value=f'Created {(account_age.seconds % 3600) // 60} minutes {((account_age.seconds % 3600) % 60)} seconds ago.',
                            inline=False)
        elif 0 < (account_age.seconds // 3600) and account_age.days == 0:
            embed.add_field(name='**New Account**',
                            value=f'Created {account_age.seconds // 3600} hours {(account_age.seconds % 3600) // 60} minutes {((account_age.seconds % 3600) % 60)} seconds ago.',
                            inline=False)
        elif 0 < account_age.days < 7:
            embed.add_field(name='**New Account**',
                            value=f'Created {account_age.days} days {account_age.seconds // 3600} hours {(account_age.seconds % 3600) // 60} minutes ago.',
                            inline=False)
        else:
            pass
        embed.set_author(name=f'{member.name}#{member.discriminator} ({member.id})')
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text=f'Total Members: {member.guild.member_count}')
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)
        stat_channel = bot.get_channel(gld[9])
        if stat_channel is None:
            pass
        else:
            await stat_channel.edit(name=f'Members: {member.guild.member_count}')


# member leave event
# TODO: This moves into lumberjack.logger.Logger
@bot.event
async def on_member_remove(member):
    gld = get_log_by_id(member.guild.id)
    logs = bot.get_channel(gld[2])
    if logs is None:
        pass
    else:
        account_age = datetime.utcnow() - member.created_at
        time_on_server = datetime.utcnow() - member.joined_at
        embed = discord.Embed(title=f'**User Left**',
                              description=f'''**Name:** {member.mention}
**Created on:** {member.created_at.strftime(format_date)}
**Account age:** {account_age.days} days old
**Joined on:** {member.joined_at.strftime(format_date)} ({time_on_server.days} days ago)''',
                              color=0xd90000)
        embed.set_author(name=f'{member.name}#{member.discriminator} ({member.id})')
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text=f'Total Members: {member.guild.member_count}')
        embed.timestamp = datetime.utcnow()
        roles = [f'<@&{role.id}>' for role in member.roles[1:]]
        roles_str = " ".join(roles)
        if len(roles) < 1:
            embed.add_field(name=f'**Roles[{len(roles)}]**', value="None", inline=False)
        else:
            embed.add_field(name=f'**Roles[{len(roles)}]**', value=f'{roles_str}', inline=False)
        await logs.send(embed=embed)
        stat_channel = bot.get_channel(gld[9])
        if stat_channel is None:
            pass
        else:
            await stat_channel.edit(name=f'Members: {member.guild.member_count}')


# message delete event

# TODO: This moves into lumberjack.logger.Logger
@bot.event
async def on_raw_message_delete(payload):
    gld = get_log_by_id(payload.guild_id)
    logs = bot.get_channel(gld[3])
    channel = bot.get_channel(payload.channel_id)
    msg = get_msg_by_id(payload.message_id)
    att = get_att_by_id(payload.message_id)
    author = await bot.fetch_user(msg[1])
    attachments = []
    for attachment in att:
        attachments.append(attachment[1])
    if author.bot:
        pass
    elif logs is None:
        pass
    else:
        embed = discord.Embed(title=F"**Message deleted in #{channel}**",
                              description=F'''**Author:** {author.mention}
**Channel:** {channel.mention} ({channel.id})
**Message ID:** {payload.message_id}''',
                              color=0xd90000)
        if len(msg[7]) == 0:
            embed.add_field(name=f'**Content**', value='`Blank`', inline=False)
        elif len(msg[7]) <= 1024:
            embed.add_field(name=f'**Content**', value=f'{msg[7]}', inline=False)
        else:
            prts = msg[7]
            prt_1 = prts[:1024]
            prt_2 = prts[1024:]
            embed.add_field(name=f'**Content**', value=f'{prt_1}', inline=False)
            embed.add_field(name=f'Continued', value=f'{prt_2}')
        if not msg[10]:
            embed.add_field(name=f'**Attachments**', value=f'None', inline=False)
        else:
            attachments_str = " ".join(attachments)
            embed.add_field(name=f'**Attachments**', value=f'{attachments_str}', inline=False)
            embed.set_image(url=attachments[0])
        embed.set_author(name=f'{author.name}#{author.discriminator} ({author.id})')
        embed.set_thumbnail(url=author.avatar_url)
        embed.set_footer(text=f'')
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)


# message edit event
# TODO: This moves into lumberjack.logger.Logger
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
            embed = discord.Embed(title=F"**Message edited in #{after.channel}**",
                                  description=F'''**Author:** <@!{after.author.id}>
**Channel:** <#{after.channel.id}> ({after.channel.id})
**Message ID:** {after.id}''',
                                  color=0xffc704)
            embed.set_author(name=f'{after.author.name}#{after.author.discriminator} ({after.author.id})')
            if len(before[7]) == 0:
                embed.add_field(name=f'**Before**', value=f'`Blank`', inline=False)
            elif len(before[7]) <= 1024:
                embed.add_field(name=f'**Before**', value=f'{before[7]} ', inline=False)
            else:
                prts = before[7]
                prt_1 = prts[:1024]
                prt_2 = prts[1024:]
                embed.add_field(name=f'**Before**', value=f'{prt_1}', inline=False)
                embed.add_field(name=f'Continued', value=f'{prt_2}')
            if len(after.content) <= 1024:
                embed.add_field(name=f'**After**', value=f'{after.content} ', inline=False)
            else:
                prts = after.content
                prt_1 = prts[:1024]
                prt_2 = prts[1024:]
                embed.add_field(name=f'**After**', value=f'{prt_1}', inline=False)
                embed.add_field(name=f'Continued', value=f'{prt_2}')
            embed.set_thumbnail(url=after.author.avatar_url)
            embed.set_footer(text=f'')
            embed.timestamp = datetime.utcnow()
            await logs.send(embed=embed)
            content = after.content
            update_msg(payload.message_id, content)


# member update event (nickname, roles, activity, status)
# TODO: This moves into lumberjack.logger.Logger
@bot.event
async def on_member_update(before, after):
    gld = get_log_by_id(after.guild.id)
    logs = bot.get_channel(gld[7])
    if before.nick == after.nick:
        pass
    elif logs is None:
        pass
    else:
        embed = discord.Embed(title=F"**User Nickname Updated**",
                              description=F'''**User:** <@!{after.id}>\n
**Before:** {before.nick}
**After:** {after.nick}''',
                              color=0x22ffc2)
        embed.set_author(name=f'{after.name}#{after.discriminator} ({after.id})')
        embed.set_thumbnail(url=after.avatar_url)
        embed.set_footer(text=f'')
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)


# user update event (avatar, username, discriminator)
# TODO: This moves into lumberjack.logger.Logger
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
                    embed = discord.Embed(title=F"**Username Updated**",
                                          description=F'''**User:** <@!{after.id}>\n
**Before:** {before.name}#{before.discriminator}
**After:** {after.name}#{after.discriminator}''',
                                          color=0x22ffc2)
                    embed.set_author(name=f'{after.name}#{after.discriminator} ({after.id})')
                    embed.set_thumbnail(url=after.avatar_url)
                    embed.set_footer(text=f'')
                    embed.timestamp = datetime.utcnow()
                    await logs.send(embed=embed)
            if before.avatar != after.avatar:
                logs = bot.get_channel(gld[8])
                if logs is None:
                    pass
                else:
                    embed = discord.Embed(title=F"**User avatar Updated**",
                                          description=F'''**User:** <@!{after.id}>\n
Old avatar in thumbnail. New avatar down below''',
                                          color=0x8000ff)
                    embed.set_author(name=f'{after.name}#{after.discriminator} ({after.id})')
                    embed.set_thumbnail(url=before.avatar_url)
                    embed.set_footer(text=f'')
                    embed.set_image(url=after.avatar_url_as(size=128))
                    embed.timestamp = datetime.utcnow()
                    await logs.send(embed=embed)


# TODO: This moves into lumberjack.logger.Logger
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
    embed = discord.Embed(title=F"**Bulk Message Delete**",
                          description=F'''**Message Count:** {len(messages)}
**Channel:** {purged_channel.mention}
Full message dump attached below.''',
                          color=0xff0080)
    embed.timestamp = datetime.utcnow()
    with open('./log.txt', 'w') as file:
        for message in messages:
            file.writelines(f'Author: {message[2]} ({message[1]})\nID:{message[0]}\nContent: {message[7]}\n\n')
    try:
        await logs.send(embed=embed)
        await logs.send(file=discord.File('./log.txt', filename=f'{current_time.strftime(format_datetime)}.txt'))
    except discord.HTTPException:
        pass


# TODO: This moves into lumberjack.__init__
with open("tokenbeta", "r") as f:
    bot.run(f.readline().strip())
