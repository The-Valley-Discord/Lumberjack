import discord
from datetime import datetime
from discord.ext import commands

client = commands.Bot(command_prefix = 'lum.')
client.max_messages = 50000
@client.event
async def on_ready():
    print('Bot is ready.')

@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')

format_date = '%b %d, %Y'
format_time = '%I:%M %p'
format_datetime = '%b %d, %Y  %I:%M %p'

#member join event

@client.event
async def on_member_join(member):
    logs = client.get_channel(686365631217533153)
    current_time = datetime.now()
    account_age = current_time - member.created_at
    if (account_age.days + 1) < 7:
        embed=discord.Embed(title=f'**User Joined**', description=f"Name: {member.mention} ({member.id})\nCreated on: {member.created_at.strftime(format_date)}\nAccount age: {account_age.days + 1} days old\n\n**New Account**", color=0xffc704)
    else:
        embed=discord.Embed(title=f'**User Joined**', description=f"Name: {member.mention} ({member.id})\nCreated on: {member.created_at.strftime(format_date)}\nAccount age: {account_age.days + 1} days old", color=0x008000)
    embed.set_author(name=f'{member.name}#{member.discriminator}')
    embed.set_thumbnail(url=member.avatar_url)
    embed.set_footer(text=f'')
    embed.timestamp = datetime.utcnow()
    await logs.send(embed = embed)

#member leave event

@client.event
async def on_member_remove(member):
    logs = client.get_channel(686365631217533153)
    current_time = datetime.now()
    account_created_date = member.created_at
    account_join_date = member.joined_at
    account_age = current_time - account_created_date
    time_on_server = current_time - account_join_date
    embed=discord.Embed(title=f'**User Left**', description=f"Name: {member.mention} ({member.id})\nCreated on: {account_created_date.strftime(format_date)}\nAccount age: {account_age.days + 1} days old\nJoined on: {account_join_date.strftime(format_date)} ({time_on_server.days + 1} days ago)", color=0xd90000)
    embed.set_author(name=f'{member.name}#{member.discriminator}')
    embed.set_thumbnail(url=member.avatar_url)
    embed.set_footer(text=f'')
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
        logs = client.get_channel(686710645420589063)
        current_time = datetime.now()
        attachments = [f"{attachment.proxy_url}" for attachment in payload.cached_message.attachments]
        attachments_str = " ".join(attachments)
        if len(attachments) == 0:
            embed=discord.Embed(title=F"**Message deleted in #{payload.cached_message.channel}**", description=F"**Author:** <@!{payload.cached_message.author.id}>\n**Channel:** <#{payload.channel_id}> ({payload.channel_id})\n**Message ID:** {payload.message_id}\n\n**Content**\n\n {payload.cached_message.content}\n\n**Attachments:** None", url=payload.cached_message.jump_url)
        else:
            embed=discord.Embed(title=F"**Message deleted in #{payload.cached_message.channel}**", description=F"**Author:** <@!{payload.cached_message.author.id}>\n**Channel:** <#{payload.channel_id}> ({payload.channel_id})\n**Message ID:** {payload.message_id}\n\n**Content**\n\n {payload.cached_message.content}\n\n**Attachments:** {attachments_str}", url=payload.cached_message.jump_url)
            embed.set_image(url=attachments[0])
        embed.set_author(name=f'{payload.cached_message.author.name}#{payload.cached_message.author.discriminator} ({payload.cached_message.author.id})')
        embed.set_thumbnail(url=payload.cached_message.author.avatar_url)
        embed.set_footer(text=f'')
        embed.timestamp = datetime.utcnow()
        await logs.send(embed=embed)






with open("token","r") as f:
    client.run(f.readline().strip())
