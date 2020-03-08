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
    await logs.send(f'**{member.name}#{member.discriminator}**\n**Member Joined**\n**Name:**{member.mention}({member.id})\n **Created On:**{member.created_at}\n{member.avatar_url_as(size=128)}')

@client.event
async def on_member_remove(member):
    logs = client.get_channel(639594402414854145)
    await logs.send(f'**{member.name}#{member.discriminator}**\n**Member Left**\n**Name:**{member.mention}({member.id})\n **Created On:**{member.created_at}\n{member.avatar_url_as(size=128)}')

with open("token","r") as f:
    client.run(f.readline().strip())
