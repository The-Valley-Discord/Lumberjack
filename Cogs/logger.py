import logging
from datetime import datetime

import discord
import typing
from discord.ext import commands

from Helpers.database import Database
from Helpers.helpers import has_permissions, format_datetime, field_message_splitter


class Logger(commands.Cog):
    def __init__(self, bot: discord.Client, logs: logging, db: Database):
        """
        Cog
        Handles logging system for Lumberjack
                :param bot: Discord.py Bot Object
                """
        self.bot = bot
        self.logs = logs
        self.db = db
        self._last_member = None

    @commands.command()
    @commands.check_any(has_permissions())
    async def log(self, ctx, log_type, channel: typing.Union[discord.TextChannel, str]):
        if isinstance(channel, str) and channel == "here":
            channel = ctx.channel
        elif isinstance(channel, str):
            raise commands.BadArgument
        log_name = self.db.set_log_channel(log_type.lower(), ctx.guild.id, channel.id)
        await ctx.send(f"Updated {log_name} Log Channel to {channel.mention}")

    @log.error
    async def log_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(
                "Incorrect log type. Please use one of the following. Join, Leave, "
                "Delete, Bulk_Delete, Edit, Username, Nickname, Avatar, Stats or LJLog"
            )
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                "Please enter a valid channel or 'here' to set it to this channel"
            )

    @commands.command()
    @commands.check_any(has_permissions())
    async def clear(self, ctx, log_type):
        log_name = self.db.set_log_channel(log_type.lower(), ctx.guild.id, 0)
        await ctx.send(f"Disabled {log_name} logs.")

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(
                "Incorrect log type. Please use one of the following. Join, Leave, "
                "Delete, Bulk_Delete, Edit, Username, Nickname, Avatar, Stats or LJLog"
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        self.db.add_message(message)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        try:
            gld = self.db.get_log_by_id(payload.guild_id)
            logs = self.bot.get_channel(gld.delete_id)
            channel = self.bot.get_channel(payload.channel_id)
        except discord.HTTPException or ValueError as e:
            self.logs.error(f"Error in on_raw_message_delete because: {e}")
            return
        if logs is None:
            return
        try:
            msg = self.db.get_msg_by_id(payload.message_id)
        except ValueError as e:
            self.logs.debug(f"on_raw_message_delete: {payload.message_id} {e}")
        else:
            author = channel.guild.get_member(msg.author.id)
            polyphony_role = 0
            if author.guild.id == 539925898128785460:
                polyphony_role = self.bot.get_guild(539925898128785460).get_role(
                    732962687360827472
                )
            if author is None or (author.bot and polyphony_role not in author.roles):
                pass
            else:
                embed = discord.Embed(
                    title=f"**Message deleted in #{channel}**",
                    description=(
                        f"**Author:** {author.mention}\n"
                        f"**Channel:** {channel.mention} ({channel.id})\n"
                        f"**Message ID:** {payload.message_id}"
                    ),
                    color=0xD90000,
                )
                if len(msg.clean_content) > 0:
                    embed = field_message_splitter(embed, msg.clean_content, "Content")
                if len(msg.attachments) == 0:
                    pass
                else:
                    att = self.db.get_att_by_id(payload.message_id)
                    attachments = []
                    for attachment in att:
                        attachments.append(attachment[1])
                    attachments_str = " ".join(attachments)
                    embed.add_field(
                        name=f"**Attachments**",
                        value=f"{attachments_str}",
                        inline=False,
                    )
                    embed.set_image(url=attachments[0])
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
    async def on_raw_bulk_message_delete(self, payload):
        messages = []
        message_ids = sorted(payload.message_ids)
        for message_id in message_ids:
            try:
                message = self.db.get_msg_by_id(message_id)
            except ValueError as e:
                self.logs.debug(f"on_raw_bulk_message_delete: {message_id} {e} ")
            else:
                if self.bot.user.id == message.author.id:
                    pass
                else:
                    messages.append(message)
        if len(messages) != 0:
            try:
                gld = self.db.get_log_by_id(payload.guild_id)
                logs = self.bot.get_channel(gld.delete_bulk)
                purged_channel = self.bot.get_channel(payload.channel_id)
            except discord.HTTPException or ValueError as e:
                self.logs.error(f"Error in on_raw_bulk_message_delete because: {e}")
            else:
                if gld.delete_bulk == 0:
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
                with open("../log.txt", "w", encoding="utf-8") as file:
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
    async def on_raw_message_edit(self, payload):
        try:
            channel = self.bot.get_channel(payload.channel_id)
            gld = self.db.get_log_by_id(channel.guild.id)
            logs = self.bot.get_channel(gld.edit)
        except discord.HTTPException or ValueError as e:
            self.logs.error(f"Error in on_raw_message_edit because: {e}")
            return
        if gld.edit == 0:
            return
        try:
            before = self.db.get_msg_by_id(payload.message_id)
        except ValueError as e:
            self.logs.debug(f"on_raw_message_edit: {payload.message_id} {e}")
        else:
            author = channel.guild.get_member(before.author.id)
            polyphony_role = 0
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
            if before.clean_content == payload.data["content"] or (
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
                try:
                    self.db.add_lumberjack_message(await logs.send(embed=embed))
                except discord.HTTPException as e:
                    self.logs.error(f"Error sending edit log: {e}")
                content = payload.data["content"]
                self.db.update_msg(payload.message_id, content)
