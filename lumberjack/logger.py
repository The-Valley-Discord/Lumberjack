import logging as lumberlog

from discord.ext import commands

from . import c, conn
from .helpers import has_permissions


class Logger(commands.Cog):
    def __init__(self, bot):
        """
        Cog
        Handles logging system for Lumberjack

        :param bot: Discord.py Bot Object
        """
        self.bot = bot
        self._last_member = None

    @commands.command()
    @commands.check_any(has_permissions())
    async def log(self, ctx, arg1, arg2):
        """
        Creates logging channel

        :param ctx: API Command Context
        :param arg1: Log Type
        :param arg2: Log Channel
        """

        # Process Arguments
        strip = ['<', '>', '#']
        str_channel = arg2.lower()
        log_type = arg1.lower()
        for item in strip:
            str_channel = str_channel.strip(item)
        if str_channel == 'here':  # If channel user wants current channel
            channel_id = ctx.channel.id
        else:
            channel_id = int(str_channel)

        # Update the logging in the database
        log_name, sql = self.update_log_channel_by_type(ctx, log_type, channel_id)

        if log_type == 'stats':
            logs = ctx.get_channel(channel_id)
            if logs is None:
                pass
            else:
                await logs.edit(name=f'Members: {logs.guild.member_count}')

        if log_name is not None:
            await ctx.send(f'Updated {log_name} Log Channel to {logs.mention}')
            lumberlog.info(
                f'Set {log_name} Log Channel to channel {logs.name} ({logs.id}) on guild {ctx.guild.name} ({ctx.guild.id})')

    @commands.command()
    @commands.check_any(has_permissions())
    async def clear(self, ctx, arg1):
        """
        Disables log type on server

        :param ctx: API Command Context
        :param arg1: Log Type
        """
        log_type = arg1.lower()
        log_name, sql = self.update_log_channel_by_type(ctx, log_type, 0)
        if log_name is not None:
            await ctx.send(f'Disabled {log_name} logs.')
            lumberlog.info(f'Disabled {log_name} logs on guild {ctx.guild.name} ({ctx.guild.id})')

    @staticmethod
    def update_log_channel_by_type(ctx, log_type, log_channel):
        """
        Update the logging channel for the specific log type

        :param log_channel: (int) Log channel ID
        :param log_type: (string) Log Type: Join, Leave, Delete, Bulk_Delete, Edit, Username, Nickname, Avatar, or Stats
        :param ctx: Command Context to send errors to
        :return: [(string) log name, (SQL) sql command] or None if type not recognized
        """

        log_type = log_type.lower()

        # Switch: find channel type
        if log_type == 'join':
            sql = """UPDATE log_channels SET joinid = ? WHERE guildid = ?"""
            log_name = 'Join'
        elif log_type == 'leave':
            sql = """UPDATE log_channels SET leaveid = ? WHERE guildid = ?"""
            log_name = 'Leave'
        elif log_type == 'delete':
            sql = """UPDATE log_channels SET deleteid = ? WHERE guildid = ?"""
            log_name = 'Delete'
        elif log_type == 'bulk_delete':
            sql = """UPDATE log_channels SET delete_bulk = ? WHERE guildid = ?"""
            log_name = 'Bulk Delete'
        elif log_type == 'edit':
            sql = """UPDATE log_channels SET edit = ? WHERE guildid = ?"""
            log_name = 'Edit'
        elif log_type == 'username':
            sql = """UPDATE log_channels SET username = ? WHERE guildid = ?"""
            log_name = 'Username'
        elif log_type == 'nickname':
            sql = """UPDATE log_channels SET nickname = ? WHERE guildid = ?"""
            log_name = 'Nickname'
        elif log_type == 'avatar':
            sql = """UPDATE log_channels SET avatar = ? WHERE guildid = ?"""
            log_name = 'Avatar'
        elif log_type == 'stats':
            sql = """UPDATE log_channels SET stat_member = ? WHERE guildid = ?"""
            log_name = 'Stats'
        else:
            await ctx.send(
                'Incorrect log type. Please use one of the following. Join, Leave, Delete, Bulk_Delete, Edit, Username, Nickname, Avatar, or Stats')
            lumberlog.debug(f'Log type {log_type} not found')
            return [None, None]

        if not log_channel:
            # Disable log type by setting channel ID to 0
            task = (0, ctx.guild.id)
        else:
            if ctx.get_channel(log_channel) is None:  # Check channel ID
                await ctx.send('Invalid channel ID')
                lumberlog.debug(f'Channel ID {log_channel} not found')
                return [None, None]
            else:
                task = (log_channel, ctx.guild.id)

        c.execute(sql, task)
        conn.commit()
        return [sql, log_name]
