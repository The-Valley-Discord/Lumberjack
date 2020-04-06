import discord
from datetime import datetime
from discord.ext import commands
import pandas as pd
client = discord.Client(max_messages = 500000, fetch_offline_members = True)
bot = commands.Bot(command_prefix = 'lum.')
before_invites = []

gl = pd.read_csv('Log Channel IDs.csv')

def has_permissions():
    def predicate(ctx):
        return ctx.author.guild_permissions.manage_guild == True
    return commands.check(predicate)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="with ten thousand eyes."))
    for guild in client.guilds:
        global gl
        g_id = gl.loc[gl['Guild ID'] == guild.id]
        if g_id.empty:
            gl = gl.append(pd.Series([guild.id, 0, 0, 0, 0, 0, 0, 0, 0], index = gl.columns), ignore_index=True)
            gl.to_csv('Log Channel IDs.csv', index=False)
        else:
            pass
        for invite in await guild.invites():
            x = [invite.url, invite.uses, invite.inviter]
            before_invites.append(x)
    print('Bot is ready.')

@client.event
async def on_guild_join(guild):
    for invite in await guild.invites():
        x = [invite.url, invite.uses, invite.inviter]
        before_invites.append(x)
        global gl
        g_id = gl.loc[gl['Guild ID'] == guild.id]
        if g_id.empty:
            gl = gl.append(pd.Series([guild.id, 0, 0, 0, 0, 0, 0, 0, 0], index = gl.columns), ignore_index=True)
            gl.to_csv('Log Channel IDs.csv', index=False)
        else:
            pass

@bot.command()
@commands.check_any(has_permissions())
async def log(ctx, *, log_type):
    rows = list(gl['Guild ID'][gl['Guild ID'] == ctx.guild.id].index)
    log_type_scrub = log_type.lower()
    log_type_split = log_type_scrub.split()
    log_name = ''
    if log_type_split[0] == 'join':
        gl.iloc[rows, 1] = ctx.channel.id
        log_name = 'Join'
    elif log_type_split[0] == 'leave':
        gl.iloc[rows, 2] = ctx.channel.id
        log_name = 'Leave'
    elif log_type_split[0] == 'delete':
        gl.iloc[rows, 3] = ctx.channel.id
        log_name = 'Delete'
    elif log_type_split[0] == 'bulk_delete':
        gl.iloc[rows, 4] = ctx.channel.id
        log_name = 'Bulk Delete'
    elif log_type_split[0] == 'edit':
        gl.iloc[rows, 5] = ctx.channel.id
        log_name = 'Edit'
    elif log_type_split[0] == 'username':
        gl.iloc[rows, 6] = ctx.channel.id
        log_name = 'Username'
    elif log_type_split[0] == 'nickname':
        gl.iloc[rows, 7] = ctx.channel.id
        log_name = 'Nickname'
    elif log_type_split[0] == 'avatar':
        gl.iloc[rows, 8] = ctx.channel.id
        log_name = 'Avatar'
    if len(log_name) == 0:
        await ctx.send(f'Incorrect log type. Please use one of the folowing. Join, Leave, Delete, Bulk_Delete, Edit, Username, Nickname, or Avatar')
    else:
        await ctx.send(f'Updated {log_name} Log Channel to {ctx.channel.mention}')
        gl.to_csv('Log Channel IDs.csv', index=False)
@bot.command()
@commands.check_any(has_permissions())
async def clear(ctx, *, log_type):
    rows = list(gl['Guild ID'][gl['Guild ID'] == ctx.guild.id].index)
    log_type_scrub = log_type.lower()
    log_type_split = log_type_scrub.split()
    log_name = ''
    if log_type_split[0] == 'join':
        gl.iloc[rows, 1] = 0
        log_name = 'Join'
    elif log_type_split[0] == 'leave':
        gl.iloc[rows, 2] = 0
        log_name = 'Leave'
    elif log_type_split[0] == 'delete':
        gl.iloc[rows, 3] = 0
        log_name = 'Delete'
    elif log_type_split[0] == 'bulk_delete':
        gl.iloc[rows, 4] = 0
        log_name = 'Bulk Delete'
    elif log_type_split[0] == 'edit':
        gl.iloc[rows, 5] = 0
        log_name = 'Edit'
    elif log_type_split[0] == 'username':
        gl.iloc[rows, 6] = 0
        log_name = 'Username'
    elif log_type_split[0] == 'nickname':
        gl.iloc[rows, 7] = 0
        log_name = 'Nickname'
    elif log_type_split[0] == 'avatar':
        gl.iloc[rows, 8] = 0
        log_name = 'Avatar'
    if len(log_name) == 0:
        await ctx.send(f'Incorrect log type. Please use one of the folowing. Join, Leave, Delete, Bulk_Delete, Edit, Username, Nickname, or Avatar')
    else:
        await ctx.send(f'Disabled {log_name} logs.')
        gl.to_csv('Log Channel IDs.csv', index=False)



@client.event
async def on_guild_remove(guild):
    for invite in await guild.invites():
        x = [invite.url, invite.uses, invite.inviter]
        before_invites.remove(x)

@client.event
async def on_invite_create(invite):
    x = [invite.url, invite.uses, invite.inviter]
    before_invites.append(x)

@client.event
async def on_invite_delete(invite):
    x = [invite.url, invite.uses, invite.inviter]
    before_invites.remove(x)

@bot.command()
async def ping(ctx):
    embed=discord.Embed(title='**Ping**', description=f'Pong! {round(client.latency * 1000)}ms')
    embed.set_author(name=f"{client.user.name}", icon_url=client.user.avatar_url)
    await ctx.send(embed=embed)

format_date = '%b %d, %Y'
format_time = '%I:%M %p'
format_datetime = '%b %d, %Y  %I:%M %p'

#member join event

@client.event
async def on_member_join(member):
    g_id = gl.loc[gl['Guild ID'] == member.guild.id]
    logs = client.get_channel(g_id.iloc[0, 1])
    account_age = datetime.utcnow() - member.created_at
    global before_invites
    after_invites = []
    invite_used = 'Vanity URL'
    invite_uses = ''
    inviter = ''
    for guild in client.guilds:
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
    if logs == None:
        pass
    else:
        if (account_age.seconds//3600) == 0 and account_age.days == 0:
            embed=discord.Embed(title=f'**User Joined**', description=f"**Name:** {member.mention}\n**Created on:** {member.created_at.strftime(format_date)}\n**Account age:** {account_age.days} days old\n**Invite used:** {invite_used} {invite_uses}\n**Created By:** {inviter}\n\n**New Account**\nCreated {(account_age.seconds%3600)//60} minutes {((account_age.seconds%3600)%60)} seconds" , color=0xffc704)
        elif 0 < (account_age.seconds//3600) and account_age.days == 0:
            embed=discord.Embed(title=f'**User Joined**', description=f"**Name:** {member.mention}\n**Created on:** {member.created_at.strftime(format_date)}\n**Account age:** {account_age.days} days old\n**Invite used:** {invite_used} {invite_uses}\n**Created By:** {inviter}\n\n**New Account**\nCreated {account_age.seconds//3600} hours {(account_age.seconds%3600)//60} minutes {((account_age.seconds%3600)%60)} seconds" , color=0xffc704)
        elif 0 < account_age.days < 7:
            embed=discord.Embed(title=f'**User Joined**', description=f"**Name:** {member.mention}\n**Created on:** {member.created_at.strftime(format_date)}\n**Account age:** {account_age.days} days old\n**Invite used:** {invite_used} {invite_uses}\n**Created By:** {inviter}\n\n**New Account**\nCreated {account_age.days} days {account_age.seconds//3600} hours {(account_age.seconds%3600)//60} minutes" , color=0xffc704)
        else:
            embed=discord.Embed(title=f'**User Joined**', description=f"**Name:** {member.mention}\n**Created on:** {member.created_at.strftime(format_date)}\n**Account age:** {account_age.days} days old\n**Invite used:** {invite_used} {invite_uses}\n**Created By:** {inviter}", color=0x008000)
        embed.set_author(name=f'{member.name}#{member.discriminator} ({member.id})')
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text=f'Total Members: {member.guild.member_count}')
        embed.timestamp = datetime.utcnow()
        await logs.send(embed = embed)

#member leave event

@client.event
async def on_member_remove(member):
    g_id = gl.loc[gl['Guild ID'] == member.guild.id]
    logs = client.get_channel(g_id.iloc[0, 2])
    if logs == None:
        pass
    else:
        account_age = datetime.utcnow() - member.created_at
        time_on_server = datetime.utcnow() - member.joined_at
        embed=discord.Embed(title=f'**User Left**', description=f"Name: {member.mention}\nCreated on: {member.created_at.strftime(format_date)}\nAccount age: {account_age.days} days old\nJoined on: {member.joined_at.strftime(format_date)} ({time_on_server.days} days ago)", color=0xd90000)
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
        await logs.send(embed = embed)

#message delete event

@client.event
async def on_message_delete(message):
    g_id = gl.loc[gl['Guild ID'] == message.guild.id]
    logs = client.get_channel(g_id.iloc[0, 3])
    if message.author.bot:
        pass
    elif logs == None:
        pass
    else:
        attachments = [f"{attachment.proxy_url}" for attachment in message.attachments]
        attachments_str = " ".join(attachments)
        if len(attachments) == 0:
            embed=discord.Embed(title=F"**Message deleted in #{message.channel}**", description=F"**Author:** {message.author.mention}\n**Channel:** <#{message.channel.id}> ({message.channel.id})\n**Message ID:** {message.id}", color=0xd90000)
            embed.add_field(name=f'**Content**', value=f'{message.content}', inline=False)
            embed.add_field(name=f'**Attachments**', value=f'None', inline=False)
        else:
            embed=discord.Embed(title=F"**Message deleted in #{message.channel}**", description=F"**Author:** {message.author.mention}\n**Channel:** <#{message.channel.id}> ({message.channel.id})\n**Message ID:** {message.id}", color=0xd90000)
            embed.set_image(url=attachments[0])
            if len(message.content) == 0:
                embed.add_field(name=f'**Content**', value=f'`Blank`', inline=True)
            else:
                embed.add_field(name=f'**Content**', value=f'{message.content}', inline=True)
            embed.add_field(name=f'**Attachments**', value=f'{attachments_str}', inline=False)
        embed.set_author(name=f'{message.author.name}#{message.author.discriminator} ({message.author.id})')
        embed.set_thumbnail(url=message.author.avatar_url)
        embed.set_footer(text=f'')
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)

#message edit event

@client.event
async def on_message_edit(before, after):
    g_id = gl.loc[gl['Guild ID'] == after.guild.id]
    logs = client.get_channel(g_id.iloc[0, 5])
    if after.author.bot:
        pass
    elif before.content == after.content:
        pass
    elif logs == None:
        pass
    else:
        embed=discord.Embed(title=F"**Message edited in #{after.channel}**", description=F"**Author:** <@!{after.author.id}>\n**Channel:** <#{after.channel.id}> ({after.channel.id})\n**Message ID:** {after.id}", color=0xffc704)
        embed.set_author(name=f'{after.author.name}#{after.author.discriminator} ({after.author.id})')
        if len(before.content) == 0:
            embed.add_field(name=f'**Before**', value=f'`Blank`', inline=False)
        else:
            embed.add_field(name=f'**Before**', value=f'{before.content} ', inline=False)
        embed.add_field(name=f'**After**', value=f'{after.content} ', inline=False)
        embed.set_thumbnail(url=after.author.avatar_url)
        embed.set_footer(text=f'')
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)

#member update event (nickname, roles, activity, status)

@client.event
async def on_member_update(before, after):
    g_id = gl.loc[gl['Guild ID'] == after.guild.id]
    logs = client.get_channel(g_id.iloc[0, 7])
    if before.nick == after.nick:
        pass
    elif logs == None:
        pass
    else:
        embed=discord.Embed(title=F"**User Nickname Updated**", description=F"**User:** <@!{after.id}>\n\n**Before:** {before.nick}\n**After:** {after.nick}", color=0x22ffc2)
        embed.set_author(name=f'{after.name}#{after.discriminator} ({after.id})')
        embed.set_thumbnail(url=after.avatar_url)
        embed.set_footer(text=f'')
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)

#user update event (avatar, username, discriminator)

@client.event
async def on_user_update(before, after):
    g_id = gl.loc[gl['Guild ID'] == after.guild.id]
    if before.name != after.name or before.discriminator != after.discriminator:
        logs = client.get_channel(g_id.iloc[0, 6])
        if logs == None:
            pass
        else:
            embed=discord.Embed(title=F"**Username Updated**", description=F"**User:** <@!{after.id}>\n\n**Before:** {before.name}#{before.discriminator}\n**After:** {after.name}#{after.discriminator}", color=0x22ffc2)
            embed.set_author(name=f'{after.name}#{after.discriminator} ({after.id})')
            embed.set_thumbnail(url=after.avatar_url)
            embed.set_footer(text=f'')
            embed.timestamp = datetime.utcnow()
            await logs.send(embed=embed)
    if before.avatar != after.avatar:
        logs = client.get_channel(g_id.iloc[0, 8])
        if logs == None:
            pass
        else:
            embed=discord.Embed(title=F"**User avatar Updated**", description=F"**User:** <@!{after.id}>\n\nOld avatar in thumbail. New avatar down below", color=0x8000ff)
            embed.set_author(name=f'{after.name}#{after.discriminator} ({after.id})')
            embed.set_thumbnail(url=before.avatar_url)
            embed.set_footer(text=f'')
            embed.set_image(url=after.avatar_url_as(size=128))
            embed.timestamp = datetime.utcnow()
            await logs.send(embed=embed)
@client.event
async def on_bulk_message_delete(messages):
    message = messages[0]
    g_id = gl.loc[gl['Guild ID'] == message.guild.id]
    logs = client.get_channel(g_id.iloc[0, 4])
    current_time = datetime.utcnow()
    purged_channel = message.channel.mention
    embed=discord.Embed(title=F"**Bulk Message Delete**", description=F"**Message Count:** {len(messages)}\n**Channel:** {purged_channel}\n Full message dump attached below.", color=0xff0080)
    embed.timestamp = datetime.utcnow()
    with open('./log.txt', 'w') as file:
        for message in messages:
            file.writelines(f'Author:{message.author.name}#{message.author.discriminator} ({message.author.id})\nID:{message.id}\nContent: {message.content}\n\n')
    try:
        await logs.send(embed=embed)
        await logs.send(file=discord.File('./log.txt', filename=f'{current_time.strftime(format_datetime)}.txt'))
    except discord.HTTPException:
        pass

with open("token","r") as f:
    client.run(f.readline().strip())
    bot.run(f.readline().strip())
