from datetime import datetime

import discord
import typing
from discord.ext import commands

from database import (
    add_message,
    add_attachment,
    get_log_by_id,
    get_att_by_id,
    get_msg_by_id,
    update_msg,
    add_lumberjack_message
)
from helpers import has_permissions, set_log_channel, format_datetime


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
    async def log(self, ctx, log_type, channel: typing.Union[discord.TextChannel, str]):
        if isinstance(channel, str) and channel == "here":
            channel = ctx.channel
        log_name = set_log_channel(log_type.lower(), ctx.guild.id, channel.id)
        if len(log_name) == 0:
            await ctx.send(
                "Incorrect log type. Please use one of the following. Join, Leave, "
                "Delete, Bulk_Delete, Edit, Username, Nickname, Avatar, Stats or LJLog"
            )
        else:
            await ctx.send(f"Updated {log_name} Log Channel to {channel.mention}")
            # broken member count tracker
            # if log_name == "Stats":
            #    await logs.edit(name=f"Members: {logs.guild.member_count}")

    @log.error
    async def log_error(self, ctx, error):
        if isinstance(error, commands.BadArgument) or isinstance(error, commands.CommandInvokeError):
            await ctx.send("Please enter a valid channel")

    @commands.command()
    @commands.check_any(has_permissions())
    async def clear(self, ctx, log_type):
        log_name = set_log_channel(log_type.lower(), ctx.guild.id, 0)
        if len(log_name) == 0:
            await ctx.send(
                "Incorrect log type. Please use one of the following. Join, Leave, "
                "Delete, Bulk_Delete, Edit, Username, Nickname, Avatar, Stats or LJLog"
            )
        else:
            await ctx.send(f"Disabled {log_name} logs.")

    @commands.Cog.listener()
    async def on_message(self, message):
        attachments = [f"{attachment.proxy_url}" for attachment in message.attachments]
        author = f"{message.author.name}#{message.author.discriminator}"
        avatar_url = f"{message.author.avatar_url}"
        attachment_bool = False
        if len(attachments) > 0:
            attachment_bool = True
        message_to_add = (
            message.id,
            message.author.id,
            author,
            message.author.display_name,
            message.channel.id,
            message.channel.name,
            message.guild.id,
            message.clean_content,
            message.created_at,
            avatar_url,
            attachment_bool,
        )
        add_message(message_to_add)
        if attachment_bool:
            add_attachment(message.id, attachments)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        gld = get_log_by_id(payload.guild_id)
        logs = self.bot.get_channel(gld[3])
        channel = self.bot.get_channel(payload.channel_id)
        msg = get_msg_by_id(payload.message_id)
        try:
            author = channel.guild.get_member(msg[1])
            polyphony_role = 0
            if author.guild.id == 539925898128785460:
                polyphony_role = self.bot.get_guild(539925898128785460).get_role(732962687360827472)
            if logs is None or author is None:
                pass
            elif author.bot and polyphony_role not in author.roles:
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
                if len(msg[7]) == 0:
                    pass
                elif len(msg[7]) <= 1024:
                    embed.add_field(name=f"**Content**", value=f"{msg[7]}", inline=False)
                else:
                    parts = msg[7]
                    prt_1 = parts[:1024]
                    prt_2 = parts[1024:]
                    embed.add_field(name=f"**Content**", value=f"{prt_1}", inline=False)
                    embed.add_field(name=f"Continued", value=f"{prt_2}")
                if not msg[10]:
                    pass
                else:
                    att = get_att_by_id(payload.message_id)
                    attachments = []
                    for attachment in att:
                        attachments.append(attachment[1])
                    attachments_str = " ".join(attachments)
                    embed.add_field(
                        name=f"**Attachments**", value=f"{attachments_str}", inline=False
                    )
                    embed.set_image(url=attachments[0])
                embed.set_author(name=f"{author.name}#{author.discriminator} ({author.id})")
                embed.set_thumbnail(url=author.avatar_url)
                embed.set_footer(text=f"")
                embed.timestamp = datetime.utcnow()
                message = await logs.send(embed=embed)
                add_lumberjack_message(message)
        except TypeError or AttributeError:
            print("Delete Message log Failed because message not in database.")

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        messages = []
        message_ids = sorted(payload.message_ids)
        for message_id in message_ids:
            message = get_msg_by_id(message_id)
            if message is None or self.bot.user.id == message[1]:
                pass
            else:
                messages.append(message)
        if len(messages) != 0:
            gld = get_log_by_id(payload.guild_id)
            logs = self.bot.get_channel(gld[4])
            current_time = datetime.utcnow()
            purged_channel = self.bot.get_channel(payload.channel_id)
            embed = discord.Embed(
                title=f"**Bulk Message Delete**",
                description=(
                    f"**Message Count:** {len(messages)}\n"
                    f"**Channel:** {purged_channel.mention}\n"
                    f"Full message dump attached below."
                ),
                color=0xFF0080,
            )
            embed.timestamp = datetime.utcnow()
            with open("./log.txt", "w", encoding="utf-8") as file:
                for message in messages:
                    file.writelines(
                        f"Author: {message[2]} ({message[1]})\nID:{message[0]}\nContent: {message[7]}\n\n"
                    )
            try:
                message1 = await logs.send(embed=embed)
                message2 = await logs.send(
                    file=discord.File(
                        "./log.txt",
                        filename=f"{current_time.strftime(format_datetime)}.txt",
                    )
                )
                add_lumberjack_message(message1)
                add_lumberjack_message(message2)
            except discord.HTTPException:
                pass

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        gld = get_log_by_id(channel.guild.id)
        logs = self.bot.get_channel(gld[5])
        before = get_msg_by_id(payload.message_id)
        try:
            author = channel.guild.get_member(before[1])
            polyphony_role = 0
            if channel.guild.id == 539925898128785460:
                polyphony_role = self.bot.get_guild(539925898128785460).get_role(732962687360827472)
            if 'content' not in payload.data:
                payload.data['content'] = ''
            if logs is None or before is None or before[7] == payload.data['content']:
                pass
            elif author.bot and polyphony_role not in author.roles:
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
                if len(before[7]) == 0:
                    embed.add_field(name=f"**Before**", value=f"`Blank`", inline=False)
                elif len(before[7]) <= 1024:
                    embed.add_field(name=f"**Before**", value=f"{before[7]} ", inline=False)
                else:
                    prts = before[7]
                    prt_1 = prts[:1024]
                    prt_2 = prts[1024:]
                    embed.add_field(name=f"**Before**", value=f"{prt_1}", inline=False)
                    embed.add_field(name=f"Continued", value=f"{prt_2}")
                if len(payload.data['content']) == 0:
                    embed.add_field(name=f"**After**", value=f"`Blank`", inline=False)
                elif len(payload.data['content']) <= 1024:
                    embed.add_field(
                        name=f"**After**", value=f"{payload.data['content']} ", inline=False
                    )
                else:
                    prts = payload.data['content']
                    prt_1 = prts[:1024]
                    prt_2 = prts[1024:]
                    embed.add_field(name=f"**After**", value=f"{prt_1}", inline=False)
                    embed.add_field(name=f"Continued", value=f"{prt_2}")
                embed.set_thumbnail(url=author.avatar_url)
                embed.timestamp = datetime.utcnow()
                message = await logs.send(embed=embed)
                add_lumberjack_message(message)
                content = payload.data['content']
                update_msg(payload.message_id, content)
        except TypeError:
            print("Edit Message log failed because message not in database.")
