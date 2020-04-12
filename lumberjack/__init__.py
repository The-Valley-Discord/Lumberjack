import logging as lumberlog
import sqlite3

import discord
from discord.ext import commands

from .database import get_log_by_id, add_guild

bot = commands.Bot(command_prefix='lum.')

conn = sqlite3.connect('log.db')
c = conn.cursor()

before_invites = []

if __name__ == "__main__":
    @bot.event
    async def on_ready():
        """
        Event
        Runs when bot starts
        """
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="with ten thousand eyes."))
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
        lumberlog.info('Bot is ready.')


    @bot.event
    async def on_guild_join(guild):
        """
        Event
        Runs when joining guild

        :param guild: API event context
        """
        for invite in await guild.invites():
            x = [invite.url, invite.uses, invite.inviter]
            before_invites.append(x)
            gld = get_log_by_id(guild.id)
            if gld is None:
                newguild = (guild.id, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                add_guild(conn, newguild)
        lumberlog.info(f'Joined guild {guild.name} ({guild.id})')


    @bot.event
    async def on_guild_remove(guild):
        """
        Event
        Runs when bot is removed from guild

        :param guild: API event context
        """
        for invite in await guild.invites():
            x = [invite.url, invite.uses, invite.inviter]
            before_invites.remove(x)
        lumberlog.info(f'Left guild {guild.name} ({guild.id})')


    @bot.event
    async def on_invite_create(invite):
        """
        Event
        Runs when invite is created on server

        :param invite: Discord API Invite passthrough
        """
        x = [invite.url, invite.uses, invite.inviter]
        before_invites.append(x)
        lumberlog.debug(f'New invite created for {invite.guild.name} ({invite.guild.id}): {invite.url}')


    @bot.event
    async def on_invite_delete(invite):
        """
        Event
        Runs when invite is deleted on server

        :param invite: API event context
        """
        x = [invite.url, invite.uses, invite.inviter]
        before_invites.remove(x)
        lumberlog.debug(f'Invite delete for {invite.guild.name} ({invite.guild.id}): {invite.url}')


    @bot.command()
    async def ping(ctx):
        """
        Command
        Sends bot ping to Discord

        :param ctx: API command context
        """
        embed = discord.Embed(title='**Ping**', description=f'Pong! {round(bot.latency * 1000)}ms')
        embed.set_author(name=f"{bot.user.name}", icon_url=bot.user.avatar_url)
        await ctx.send(embed=embed)
        lumberlog.debug(f'[PING] Latency: {bot.latency * 1000}ms')
