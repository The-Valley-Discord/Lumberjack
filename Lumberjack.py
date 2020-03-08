import discord
import datetime
from discord.ext import commands

client = commands.Bot(command_prefix = 'lum.')
@client.event
async def on_ready():
    print('Bot is ready.')

@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')

@client.event
async def on_member_join(member):
    logs = client.get_channel(639594402414854145)
    embed=discord.Embed(title=f'**User Joined**', description=f"Name:{member.mention}({member.id})\nCreated on:{member.created_at}", color=0x008000)
    embed.set_author(name=f'{member.name}#{member.discriminator}')
    embed.set_thumbnail(url=member.avatar_url)
    await logs.send(embed = embed)

@client.event
async def on_member_remove(member):
    logs = client.get_channel(639594402414854145)
    embed=discord.Embed(title=f'**User Left**', description=f"Name:{member.mention}({member.id})\nCreated on:{member.created_at}\nJoined on:{member.joined_at}", color=0xd90000)
    embed.set_author(name=f'{member.name}#{member.discriminator}')
    embed.set_thumbnail(url=member.avatar_url)
    await logs.send(embed = embed)

with open("token","r") as f:
    client.run(f.readline().strip())
