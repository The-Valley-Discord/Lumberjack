import logging
import typing
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands import Context

from Helpers.database import Database
from Helpers.helpers import has_permissions, format_datetime, field_message_splitter
from Helpers.models import DBGuild, DBMessage


class Logger(commands.Cog):
    def __init__(self, bot: discord.Client, logs: logging, db: Database):
        self.bot: discord.Client = bot
        self.logs: logging = logs
        self.db: Database = db
        self._last_member = None

    @commands.command()
    @commands.check_any(has_permissions())
    async def log(
        self,
        ctx: Context,
        log_type: str,
        channel: typing.Union[discord.TextChannel, str],
    ):
        if isinstance(channel, str) and channel.lower() == "here":
            channel: discord.TextChannel = ctx.channel
        elif isinstance(channel, str):
            raise commands.BadArgument
        log_name: str = self.db.set_log_channel(
            log_type.lower(), ctx.guild.id, channel.id
        )
        await ctx.send(f"Updated {log_name} Log Channel to {channel.mention}")

    @log.error
    async def log_error(self, ctx: Context, error: Exception):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(
                "Incorrect log type. Please use one of the following. Join, Leave, "
                "Delete, Bulk_Delete, Edit, Username, Nickname, Avatar, Stats or LJLog"
            )
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                "Please enter a valid channel or 'here' to set it to this channel"
            )
        elif not isinstance(error, commands.CheckAnyFailure):
            await ctx.send("Format is `lum.log <log type> <channel name/id or 'here'>`")

    @commands.command()
    @commands.check_any(has_permissions())
    async def clear(self, ctx: Context, log_type: str):
        log_name: str = self.db.set_log_channel(log_type.lower(), ctx.guild.id, 0)
        await ctx.send(f"Disabled {log_name} logs.")

    @clear.error
    async def clear_error(self, ctx: Context, error: Exception):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(
                "Incorrect log type. Please use one of the following. Join, Leave, "
                "Delete, Bulk_Delete, Edit, Username, Nickname, Avatar, Stats or LJLog"
            )
        elif not isinstance(error, commands.CheckAnyFailure):
            await ctx.send("Format is `lum.clear <log type>")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        self.db.add_message(message)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        try:
            gld: DBGuild = self.db.get_log_by_id(payload.guild_id)
            logs: discord.TextChannel = self.bot.get_channel(gld.delete_id)
            channel: discord.TextChannel = self.bot.get_channel(payload.channel_id)
        except discord.HTTPException or ValueError as e:
            self.logs.error(f"Error in on_raw_message_delete because: {e}")
            return
        if logs is None:
            return
        try:
            msg: DBMessage = self.db.get_msg_by_id(payload.message_id)
        except ValueError as e:
            self.logs.debug(f"on_raw_message_delete: {payload.message_id} {e}")
        else:
            author: discord.User = channel.guild.get_member(msg.author.id)
            if author is None:
                author = self.bot.get_user(msg.author.id)
            polyphony_role: typing.Union[int, discord.Role] = 0
            if msg.guild.id == 539925898128785460:
                polyphony_role = self.bot.get_guild(539925898128785460).get_role(
                    732962687360827472
                )
            if author is None:
                pass
            elif isinstance(author, discord.Member) and (
                author.bot and polyphony_role not in author.roles
            ):
                pass
            else:
                embed: discord.Embed = discord.Embed(
                    title=f"**Message deleted in #{channel}**",
                    description=(
                        f"**Author:** {author.mention}\n"
                        f"**Channel:** {channel.mention} ({channel.id})\n"
                        f"**Message ID:** {payload.message_id}"
                    ),
                    color=0xD90000,
                )
                if len(msg.clean_content) > 0:
                    embed: discord.Embed = field_message_splitter(
                        embed, msg.clean_content, "Content"
                    )
                if len(msg.attachments) == 0:
                    pass
                else:
                    attachments_str: str = " ".join(msg.attachments)
                    embed.add_field(
                        name=f"**Attachments**",
                        value=f"{attachments_str}",
                        inline=False,
                    )
                    embed.set_image(url=msg.attachments[0])
                embed.set_author(
                    name=f"{author.name}#{author.discriminator} ({author.id})"
                )
                embed.set_thumbnail(url=author.avatar_url)
                embed.set_footer(text=f"")
                embed.timestamp = datetime.utcnow()
                try:
                    self.db.add_lumberjack_message(await logs.send(embed=embed))
                except discord.HTTPException as e:
                    self.logs.error(f"Error sending delete log: {e}")

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(
        self, payload: discord.RawBulkMessageDeleteEvent
    ):
        messages: typing.List[DBMessage] = []
        message_ids: typing.List[int] = sorted(payload.message_ids)
        for message_id in message_ids:
            try:
                message: DBMessage = self.db.get_msg_by_id(message_id)
            except ValueError as e:
                self.logs.debug(f"on_raw_bulk_message_delete: {message_id} {e} ")
            else:
                if self.bot.user.id == message.author.id:
                    pass
                else:
                    messages.append(message)
        if len(messages) != 0:
            try:
                logs = self.bot.get_channel(messages[0].guild.delete_bulk)
                purged_channel = self.bot.get_channel(payload.channel_id)
            except discord.HTTPException or ValueError as e:
                self.logs.error(f"Error in on_raw_bulk_message_delete because: {e}")
            else:
                if messages[0].guild.delete_bulk == 0:
                    return
                embed = discord.Embed(
                    title=f"**Bulk Message Delete**",
                    description=(
                        f"**Message Count:** {len(messages)}\n"
                        f"**Channel:** {purged_channel.mention}\n"
                        f"Full message dump attached."
                    ),
                    color=0xFF0080,
                )
                embed.timestamp = datetime.utcnow()
                with open("./log.txt", "w", encoding="utf-8") as file:
                    for message in messages:
                        file.writelines(
                            f"Author: {message.author.name} ({message.author.id})\nID:{message.id}\n"
                            f"Content: {message.clean_content}\n\n"
                        )
                try:
                    self.db.add_lumberjack_message(
                        await logs.send(
                            embed=embed,
                            file=discord.File(
                                "./log.txt",
                                filename=f"{datetime.utcnow().strftime(format_datetime)}.txt",
                            ),
                        )
                    )
                except discord.HTTPException as e:
                    self.logs.error(f"Error sending bulk delete log: {e}")

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        try:
            before = self.db.get_msg_by_id(payload.message_id)
        except ValueError as e:
            self.logs.debug(f"on_raw_message_edit: {payload.message_id} {e} ")
            return
        try:
            channel = self.bot.get_channel(payload.channel_id)
            logs = self.bot.get_channel(before.guild.edit)
        except discord.HTTPException or ValueError as e:
            self.logs.error(f"Error in on_raw_message_edit because: {e}")
            return
        if before.guild.edit == 0:
            return
        else:
            author: discord.Member = channel.guild.get_member(before.author.id)
            polyphony_role: typing.Union[int, discord.Role] = 0
            if channel.guild.id == 539925898128785460:
                try:
                    polyphony_role = self.bot.get_guild(539925898128785460).get_role(
                        732962687360827472
                    )
                except discord.HTTPException as e:
                    self.logs.error(
                        f"Error fetching polyphony role in on_raw_message_edit because: {e}"
                    )
            if "content" not in payload.data:
                payload.data["content"] = ""
            if before.clean_content == payload.data["content"]:
                pass
            elif isinstance(author, discord.Member) and (
                author.bot and polyphony_role not in author.roles
            ):
                pass
            else:
                embed = discord.Embed(
                    title=f"**Message edited in #{channel}**",
                    description=(
                        f"**Author:** <@!{author.id}>\n"
                        f"**Channel:** <#{payload.channel_id}> ({payload.channel_id})\n"
                        f"**Message ID:** {payload.message_id}\n"
                        f"**[Jump Url](https://discordapp.com/channels/"
                        f"{channel.guild.id}/{payload.channel_id}/{payload.message_id})**"
                    ),
                    color=0xFFC704,
                )
                embed.set_author(
                    name=f"{author.name}#{author.discriminator} ({author.id})"
                )
                embed = field_message_splitter(embed, before.clean_content, "Before")
                embed = field_message_splitter(embed, payload.data["content"], "After")
                embed.set_thumbnail(url=author.avatar_url)
                embed.timestamp = datetime.utcnow()
                if logs:
                    try:
                        self.db.add_lumberjack_message(await logs.send(embed=embed))
                    except discord.HTTPException as e:
                        self.logs.error(f"Error sending edit log: {e}")
                self.db.update_msg(payload.message_id, payload.data["content"])
