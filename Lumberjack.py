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
    embed=discord.Embed(title='**Ping**', description=f'Pong! {round(client.latency * 1000)}ms')
    embed.set_author(name=f"{client.user.name}", icon_url=client.user.avatar_url)
    await ctx.send(embed=embed)

format_date = '%b %d, %Y'
format_time = '%I:%M %p'
format_datetime = '%b %d, %Y  %I:%M %p'

#member join event

@client.event
async def on_member_join(member):
    logs = client.get_channel(686365631217533153)
    account_age = datetime.utcnow() - member.created_at
    if (account_age.days) == 0:
        embed=discord.Embed(title=f'**User Joined**', description=f"Name: {member.mention} ({member.id})\nCreated on: {member.created_at.strftime(format_date)}\nAccount age: {account_age.days} days old\n\n**New Account**\nCreated {account_age.seconds//3600} hours {(account_age.seconds%3600)//60} minutes {((account_age.seconds%3600)%60)} seconds" , color=0xffc704)
    elif 0 < (account_age.days + 1) < 7:
        embed=discord.Embed(title=f'**User Joined**', description=f"Name: {member.mention} ({member.id})\nCreated on: {member.created_at.strftime(format_date)}\nAccount age: {account_age.days} days old\n\n**New Account**\nCreated {account_age.days +1} days {account_age.seconds//3600} hours {(account_age.seconds%3600)//60} minutes {((account_age.seconds%3600)%60)} seconds" , color=0xffc704)
    else:
        embed=discord.Embed(title=f'**User Joined**', description=f"Name: {member.mention} ({member.id})\nCreated on: {member.created_at.strftime(format_date)}\nAccount age: {account_age.days} days old", color=0x008000)
    embed.set_author(name=f'{member.name}#{member.discriminator}')
    embed.set_thumbnail(url=member.avatar_url)
    embed.set_footer(text=f'Total Members: {member.guild.member_count}')
    embed.timestamp = datetime.utcnow()
    await logs.send(embed = embed)

#member leave event

@client.event
async def on_member_remove(member):
    logs = client.get_channel(686365631217533153)
    account_age = datetime.utcnow() - member.created_at
    time_on_server = datetime.utcnow() - member.joined_at
    embed=discord.Embed(title=f'**User Left**', description=f"Name: {member.mention} ({member.id})\nCreated on: {member.created_at.strftime(format_date)}\nAccount age: {account_age.days} days old\nJoined on: {member.joined_at.strftime(format_date)} ({time_on_server.days} days ago)", color=0xd90000)
    embed.set_author(name=f'{member.name}#{member.discriminator}')
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
