import discord
from datetime import datetime
from discord.ext import commands
import logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
client = commands.Bot(command_prefix = 'lum.')
client.max_messages = 500000


before_invites = []

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the forest."))
    for guild in client.guilds:
        for invite in await guild.invites():
            x = [invite.code, invite.uses]
            before_invites.append(x)
    print('Bot is ready.')

@client.event
async def on_invite_create(invite):
    x = [invite.code, invite.uses]
    before_invites.append(x)

@client.command()
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
    logs = client.get_channel(688877110126837766)
    account_age = datetime.utcnow() - member.created_at
    after_invites = []
    invite_used = ''
    for guild in client.guilds:
        for invite in await guild.invites():
            x = [invite.code, invite.uses]
            after_invites.append(x)
    for before_invite in before_invites:
        for after_invite in after_invites:
            if before_invite == after_invite:
                pass
            elif before_invite[0] == after_invite[0] and before_invite[1] != after_invite[1]:
                before_invite[1] += 1
                invite_used = before_invite[0]
    if (account_age.seconds//3600) == 0 and account_age.days == 0:
        embed=discord.Embed(title=f'**User Joined**', description=f"**Name:** {member.mention}\n**Created on:** {member.created_at.strftime(format_date)}\n**Account age:** {account_age.days} days old\n**Invite used:** discord.gg/{invite_used}\n\n**New Account**\nCreated {(account_age.seconds%3600)//60} minutes {((account_age.seconds%3600)%60)} seconds" , color=0xffc704)
    elif 0 < (account_age.seconds//3600) and account_age.days == 0:
        embed=discord.Embed(title=f'**User Joined**', description=f"**Name:** {member.mention}\n**Created on:** {member.created_at.strftime(format_date)}\n**Account age:** {account_age.days} days old\n**Invite used:** discord.gg/{invite_used}\n\n**New Account**\nCreated {account_age.seconds//3600} hours {(account_age.seconds%3600)//60} minutes {((account_age.seconds%3600)%60)} seconds" , color=0xffc704)
    elif 0 < account_age.days < 7:
        embed=discord.Embed(title=f'**User Joined**', description=f"**Name:** {member.mention}\n**Created on:** {member.created_at.strftime(format_date)}\n**Account age:** {account_age.days} days old\n**Invite used:** discord.gg/{invite_used}\n\n**New Account**\nCreated {account_age.days} days {account_age.seconds//3600} hours {(account_age.seconds%3600)//60} minutes" , color=0xffc704)
    else:
        embed=discord.Embed(title=f'**User Joined**', description=f"**Name:** {member.mention})\n**Created on:** {member.created_at.strftime(format_date)}\n**Account age:** {account_age.days} days old\n**Invite used:** discord.gg/{invite_used}", color=0x008000)
    embed.set_author(name=f'{member.name}#{member.discriminator} ({member.id})')
    embed.set_thumbnail(url=member.avatar_url)
    embed.set_footer(text=f'Total Members: {member.guild.member_count}')
    embed.timestamp = datetime.utcnow()
    await logs.send(embed = embed)

#member leave event

@client.event
async def on_member_remove(member):
    logs = client.get_channel(688877110126837766)
    account_age = datetime.utcnow() - member.created_at
    time_on_server = datetime.utcnow() - member.joined_at
    embed=discord.Embed(title=f'**User Left**', description=f"Name: {member.mention}\nCreated on: {member.created_at.strftime(format_date)}\nAccount age: {account_age.days} days old\nJoined on: {member.joined_at.strftime(format_date)} ({time_on_server.days} days ago)", color=0xd90000)
    embed.set_author(name=f'{member.name}#{member.discriminator} ({member.id})')
    embed.set_thumbnail(url=member.avatar_url)
    embed.set_footer(text=f'Total Members: {member.guild.member_count}')
    embed.timestamp = datetime.utcnow()
    roles = [f'<@&{role.id}>' for role in member.roles[1:]]
    roles_str = " ".join(roles)
    if len(roles) <= 1:
        embed.add_field(name=f'**Roles[{len(roles)}]**', value="None", inline=False)
    else:
        embed.add_field(name=f'**Roles[{len(roles)}]**', value=f'{roles_str}', inline=False)
    await logs.send(embed = embed)

#message delete event

@client.event
async def on_raw_message_delete(payload):
    if payload.cached_message.author.bot:
        return
    else:
        logs = client.get_channel(688877196487819268)
        attachments = [f"{attachment.proxy_url}" for attachment in payload.cached_message.attachments]
        attachments_str = " ".join(attachments)
        if len(attachments) == 0:
            embed=discord.Embed(title=F"**Message deleted in #{payload.cached_message.channel}**", description=F"**Author:** <@!{payload.cached_message.author.id}>\n**Channel:** <#{payload.channel_id}> ({payload.channel_id})\n**Message ID:** {payload.message_id}\n\n**Content**\n\n {payload.cached_message.content}\n\n**Attachments:** None")
        else:
            embed=discord.Embed(title=F"**Message deleted in #{payload.cached_message.channel}**", description=F"**Author:** <@!{payload.cached_message.author.id}>\n**Channel:** <#{payload.channel_id}> ({payload.channel_id})\n**Message ID:** {payload.message_id}\n\n**Content**\n\n {payload.cached_message.content}\n\n**Attachments:** {attachments_str}")
            embed.set_image(url=attachments[0])
        embed.set_author(name=f'{payload.cached_message.author.name}#{payload.cached_message.author.discriminator} ({payload.cached_message.author.id})')
        embed.set_thumbnail(url=payload.cached_message.author.avatar_url)
        embed.set_footer(text=f'')
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)

#message edit event

@client.event
async def on_message_edit(before, after):
    if after.author.bot:
        return
    else:
        logs = client.get_channel(688877153843937324)
        embed=discord.Embed(title=F"**Message edited in #{after.channel}**", description=F"**Author:** <@!{after.author.id}>\n**Channel:** <#{after.channel.id}> ({after.channel.id})\n**Message ID:** {after.id}\n\n**Before**\n\n {before.content}\n\n**After**\n\n{after.content}")
        embed.set_author(name=f'{after.author.name}#{after.author.discriminator} ({after.author.id})')
        embed.set_thumbnail(url=after.author.avatar_url)
        embed.set_footer(text=f'')
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)

#member update event (nickname, roles, activity, status)

@client.event
async def on_member_update(before, after):
    if before.nick == after.nick:
        return
    else:
        logs = client.get_channel(688877297889312786)
        embed=discord.Embed(title=F"**User Nickname Updated**", description=F"**User:** <@!{after.id}>\n\n**Before:** {before.nick}\n**After:** {after.nick}")
        embed.set_author(name=f'{after.name}#{after.discriminator} ({after.id})')
        embed.set_thumbnail(url=after.avatar_url)
        embed.set_footer(text=f'')
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)

#user update event (avatar, username, discriminator)

@client.event
async def on_user_update(before, after):
    if before.name != after.name or before.discriminator != after.discriminator:
        logs = client.get_channel(688877297889312786)
        embed=discord.Embed(title=F"**Username Updated**", description=F"**User:** <@!{after.id}>\n\n**Before:** {before.name}#{before.discriminator}\n**After:** {after.name}#{after.discriminator}")
        embed.set_author(name=f'{after.name}#{after.discriminator} ({after.id})')
        embed.set_thumbnail(url=after.avatar_url)
        embed.set_footer(text=f'')
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)
    if before.avatar != after.avatar:
        logs = client.get_channel(688877344969981961)
        embed=discord.Embed(title=F"**User avatar Updated**", description=F"**User:** <@!{after.id}>\n\nOld avatar in thumbail. New avatar down below")
        embed.set_author(name=f'{after.name}#{after.discriminator} ({after.id})')
        embed.set_thumbnail(url=before.avatar_url)
        embed.set_footer(text=f'')
        embed.set_image(url=after.avatar_url_as(size=128))
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)
@client.event
async def on_bulk_message_delete(messages):
    logs = client.get_channel(688877252322394306)
    message = messages[0]
    current_time = datetime.utcnow()
    purged_channel = message.channel.mention
    embed=discord.Embed(title=F"**Bulk Message Delete**", description=F"**Message Count:** {len(messages)}\n**Channel:** {purged_channel}\n Full message dump attached below.")
    embed.timestamp = datetime.utcnow()
    with open('./log.txt', 'w') as file:
        for message in messages:
            file.writelines(f'Author:{message.author.name}#{message.author.discriminator} ({message.author.id})\nID:{message.id}\nContent: {message.content}\n\n')
    try:
        await logs.send(embed=embed)
        await logs.send(file=discord.File('./log.txt', filename=f'{current_time.strftime(format_datetime)}.txt'))
    except discord.HTTPException:
        return

with open("token","r") as f:
    client.run(f.readline().strip())
