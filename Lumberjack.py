import discord
from datetime import datetime
from discord.ext import commands

client = commands.Bot(command_prefix = 'lum.')
@client.event
async def on_ready():
    print('Bot is ready.')

@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')

format_date = '%b %d, %Y'
format_time = '%I:%M %p'
format_datetime = '%b %d, %Y  %I:%M %p'

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
    embed.set_footer(text=f'Today at {current_time.strftime(format_time)}')
    await logs.send(embed = embed)

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
    embed.set_footer(text=f'Today at {current_time.strftime(format_time)}')
    roles = [f'<@&{role.id}>' for role in member.roles[1:]]
    roles_str = " ".join(roles)
    if len(roles) <= 1:
        embed.add_field(name=f'**Roles[{len(roles)}]**', value="None", inline=False)
    else:
        embed.add_field(name=f'**Roles[{len(roles)}]**', value=f'{roles_str}', inline=False)
    await logs.send(embed = embed)

with open("token","r") as f:
    client.run(f.readline().strip())
